import socket
from collections.abc import Callable
from types import TracebackType

ExcInfo = tuple[type[BaseException] | None, BaseException | None, TracebackType | None]


class Connection:
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self._sent_headers = []

    def write(self, response_body: bytes) -> None:
        self.sock.sendall(response_body)

    def start_response(
        self,
        protocol_version: tuple[int, int],
        status: str,
        headers: list[tuple[str, str]],
        exc_info: ExcInfo | None = None,
    ) -> Callable[[bytes], None]:
        if self._sent_headers:
            if exc_info is None:
                raise AssertionError("Response headers already set!")
            raise exc_info[1].with_traceback(exc_info[2])

        status_line = f"HTTP/{protocol_version[0]}.{protocol_version[1]} {status}\r\n"
        header_fields = "".join(f"{name}: {value}\r\n" for name, value in headers)

        def _write(data: bytes) -> None:
            pre_body = (status_line + header_fields).encode("latin-1") + b"\r\n"
            self.sock.sendall(pre_body)
            self._sent_headers.append(headers)
            self.write(data)

        return _write
