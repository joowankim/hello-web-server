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
        self.resp.set_body([data])
        self.conn.sock.sendall(self.resp.headers_data())
        self.headers_sent = True
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
