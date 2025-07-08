from collections.abc import Callable, Iterable
from types import TracebackType
from typing import Any

from web_server import wsgi, connection, http

ExcInfo = tuple[type[BaseException] | None, BaseException | None, TracebackType | None]


class Cycle:
    def __init__(
        self,
        conn: connection.Connection,
        environ: wsgi.WSGIEnviron,
        app: Callable[
            [
                dict[str, Any],
                Callable[
                    [str, list[tuple[str, str]], ExcInfo], Callable[[bytes], None]
                ],
            ],
            Iterable[bytes],
        ],
    ):
        self.conn = conn
        self.environ = environ
        self.app = app
        self.headers_sent = False
        self.resp: http.Response | None = None

    def write(self, data: bytes) -> None:
        if self.resp is None:
            raise AssertionError("Response headers not set!")
        if self.resp.body is None:
            self.resp.set_body([data])
        if not self.headers_sent:
            self.conn.sock.sendall(self.resp.headers_data())
            self.headers_sent = True
        if self.resp.is_chunked:
            if isinstance(data, str):
                data = data.encode("utf-8")
            chunk_size = f"{len(data)}\r\n"
            chunk = b"".join([chunk_size.encode("utf-8"), data, b"\r\n"])
            self.conn.sock.sendall(chunk)
        else:
            self.conn.sock.sendall(data)

    def start_response(
        self,
        status: str,
        headers: list[tuple[str, str]],
        exc_info: connection.ExcInfo | None = None,
    ) -> Callable[[bytes], None]:
        if self.headers_sent:
            if exc_info is None:
                raise AssertionError("Response headers already set!")
            raise exc_info[1].with_traceback(exc_info[2])

        self.resp = http.Response.draft(self.environ.http_request)
        self.resp.set_status(status)
        self.resp.extend_headers(headers)
        return self.write

    def handle_request(self) -> None:
        response_body = self.app(self.environ.dict(), self.start_response)
        self.resp.set_body(response_body)
        for data in self.resp.body:
            self.write(data)
