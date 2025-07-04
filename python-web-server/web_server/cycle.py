from collections.abc import Callable, Iterable
from types import TracebackType
from typing import Any

from web_server import wsgi, connection


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

        status_line = f"{self.environ.server_protocol} {status}\r\n"
        header_fields = "".join(f"{name}: {value}\r\n" for name, value in headers)

        def _write(data: bytes) -> None:
            headers = (status_line + header_fields).encode("latin-1") + b"\r\n"
            self.conn.sock.sendall(headers)
            self._sent_headers.append(headers)
            self.conn.sock.sendall(data)

        return _write
