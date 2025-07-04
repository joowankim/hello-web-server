import email.utils
import time
from collections.abc import Iterable
from typing import Self, ClassVar

from web_server import constants
from web_server.http.body import RequestBody
from web_server.http.errors import InvalidHeader


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

    def extend_headers(self, headers: list[tuple[str, str]]) -> None:
        new_headers = {
            name.upper().replace("_", "-"): value for name, value in self.headers
        }
        for name, value in headers:
            if name.lower().replace("_", "-") in self.hob_by_hob_headers:
                raise InvalidHeader(name)
            new_headers[name.upper().replace("_", "-")] = value
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
        body_length = sum(len(chunk) for chunk in body)
        if content_length is None:
            self.headers.append(("Content-Length", str(body_length)))
        elif int(content_length) != body_length:
            raise ValueError(
                f"Content-Length is wrong: expected {body_length}, got {content_length}"
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
