import email.utils
import time
from collections.abc import Iterable, Generator
from typing import Self, ClassVar

from web_server import constants
from web_server.http.body import RequestBody
from web_server.errors import InvalidHeader, ParseException


class Request:
    def __init__(
        self,
        method: str,
        path: str,
        query: str,
        fragment: str,
        version: tuple[int, int],
        headers: list[tuple[str, str]],
        body: RequestBody,
        trailers: list[tuple[str, str]],
    ):
        self.url_scheme = "http"
        self.method = method
        self.path = path
        self.query = query
        self.fragment = fragment
        self.version = version
        self.headers = headers
        self.body = body
        self.trailers = trailers

    @property
    def has_connection_close_header(self) -> bool:
        for name, value in self.headers:
            if name.lower() == "connection" and value.lower() == "close":
                return True
        return False

    @property
    def upgrade_header(self) -> tuple[str, str] | None:
        upgrade_header = None
        has_connection_upgrade_header = False
        for name, value in self.headers:
            if name.lower() == "upgrade":
                upgrade_header = (name, value)
            elif name.lower() == "connection" and value.lower() == "upgrade":
                has_connection_upgrade_header = True
        return upgrade_header if has_connection_upgrade_header else None

    @property
    def has_transfer_encoding_and_content_length_headers(self) -> bool:
        has_transfer_encoding = False
        has_content_length = False
        for name, value in self.headers:
            if name.lower() == "transfer-encoding":
                has_transfer_encoding = True
            elif name.lower() == "content-length":
                has_content_length = True
        return has_transfer_encoding and has_content_length


class Response:
    hob_by_hob_headers: ClassVar[set[str]] = {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "server",
        "date",
    }

    def __init__(
        self,
        version: tuple[int, int],
        status: str | None,
        headers: list[tuple[str, str]],
        body: Iterable[bytes] | None,
    ):
        self.version = version
        self.status = status
        self.headers = headers
        self.body = body

    @property
    def is_chunked(self) -> bool:
        return any(
            name.upper().replace("_", "-") == "TRANSFER-ENCODING"
            and value.lower() == "chunked"
            for name, value in self.headers
        )

    @property
    def status_code(self) -> int | None:
        if self.status is None:
            return None
        return int(self.status[:3])

    @classmethod
    def draft(cls, request: Request) -> Self:
        http_date = email.utils.formatdate(time.time(), localtime=False, usegmt=True)
        headers = [
            ("Date", http_date),
            ("Server", constants.SERVER),
        ]
        connection = (
            "close"
            if (
                request.has_connection_close_header
                or request.version == (1, 0)
                or request.has_transfer_encoding_and_content_length_headers
            )
            else "keep-alive"
        )
        if (upgrade_header := request.upgrade_header) is not None:
            connection = "upgrade"
            headers.append(upgrade_header)
        headers.append(("Connection", connection))

        return cls(
            version=request.version,
            status=None,
            headers=headers,
            body=None,
        )

    @classmethod
    def bad_request(cls, exc: ParseException) -> Self:
        content = f"<h1>400 Bad Request</h1><p>{exc}</p>".encode("utf-8")
        headers = [
            ("Content-Type", "text/html"),
            ("Connection", "close"),
            ("Content-Length", f"{len(content)}"),
        ]
        return cls(
            version=(1, 1),
            status="400 Bad Request",
            headers=headers,
            body=[content],
        )

    @classmethod
    def internal_server_error(cls, exc: BaseException) -> Self:
        content = f"<h1>500 Internal Server Error</h1><p>{exc}</p>".encode("utf-8")
        headers = [
            ("Content-Type", "text/html"),
            ("Connection", "close"),
            ("Content-Length", f"{len(content)}"),
        ]
        return cls(
            version=(1, 1),
            status="500 Internal Server Error",
            headers=headers,
            body=[content],
        )

    def extend_headers(self, headers: list[tuple[str, str]]) -> None:
        new_headers = {
            name.upper().replace("_", "-"): value for name, value in self.headers
        }
        for name, value in headers:
            if name.lower().replace("_", "-") in self.hob_by_hob_headers:
                raise InvalidHeader(name)
            new_headers[name.upper().replace("_", "-")] = value
        for idx, (name, value) in enumerate(new_headers.items()):
            if name.upper() == "CONNECTION" and self.should_conn_close():
                new_headers[name.upper().replace("_", "-")] = "close"
        self.headers = [(name.title(), value) for name, value in new_headers.items()]

    def set_status(self, status: str) -> None:
        if self.status is not None:
            raise AssertionError("Response status already set!")
        self.status = status

    def set_body(self, body: Iterable[bytes]) -> None:
        content_length = next(
            (
                value
                for name, value in self.headers
                if name.upper().replace("_", "-") == "CONTENT-LENGTH"
            ),
            None,
        )
        transfer_encoding = next(
            (
                value
                for name, value in self.headers
                if name.upper().replace("_", "-") == "TRANSFER-ENCODING"
            ),
            None,
        )
        body_iter = iter(body)
        body_length = len(next(body_iter))
        if content_length is not None and int(content_length) != body_length:
            raise ValueError(
                f"Content-Length is wrong: expected {body_length}, got {content_length}"
            )
        if transfer_encoding is None and content_length is None:
            content_length = body_length
            self.headers.append(("Content-Length", str(body_length)))

        if content_length is not None and next(body_iter, None) is not None:
            raise ValueError(
                "Content-Length data must be a single byte string, not multiple chunks"
            )
        self.body = body

    def headers_data(self) -> bytes:
        if self.status is None:
            raise AssertionError("Response status not set!")
        if self.body is None:
            raise AssertionError("Response body not set!")
        status_line = f"HTTP/{self.version[0]}.{self.version[1]} {self.status}\r\n"
        header_fields = "".join(f"{name}: {value}\r\n" for name, value in self.headers)
        return (status_line + header_fields).encode("latin-1") + b"\r\n"

    def body_stream(self) -> Generator[bytes, None, None]:
        is_chunked = self.is_chunked
        last_chunk = b"0\r\n\r\n"
        for data in self.body:
            if is_chunked:
                chunk_size = f"{len(data)}\r\n"
                last_chunk = b"".join([chunk_size.encode("utf-8"), data, b"\r\n"])
                yield last_chunk
            else:
                yield data
        if is_chunked and last_chunk != b"0\r\n\r\n":
            yield b"0\r\n\r\n"

    def should_conn_close(self) -> bool:
        if self.status is None:
            raise AssertionError("Response status not set!")
        if self.is_chunked:
            return False
        if self.status_code < 200 or self.status_code in (204, 304):
            return False
        return True
