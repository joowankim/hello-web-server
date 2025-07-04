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
        self._sent_headers: list[bytes] = []

    def start_response(
        self,
        status: str,
        headers: list[tuple[str, str]],
        exc_info: connection.ExcInfo | None = None,
    ) -> Callable[[bytes], None]:
        if self._sent_headers:
            if exc_info is None:
                raise AssertionError("Response headers already set!")
            raise exc_info[1].with_traceback(exc_info[2])

        resp = http.Response.draft(self.environ.http_request)
        resp.set_status(status)
        resp.extend_headers(headers)

        def _write(data: bytes) -> None:
            resp.set_body([data])
            sent_headers = resp.headers_data()
            self.conn.sock.sendall(sent_headers)
            self._sent_headers.append(sent_headers)
            self.conn.sock.sendall(data)

        return _write
