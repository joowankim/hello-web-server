import socket
from collections.abc import Callable
from types import TracebackType

ExcInfo = tuple[type[BaseException] | None, BaseException | None, TracebackType | None]


class Connection:
    def __init__(self, sock: socket.socket):
        self.sock = sock

    def write(self, response_body: bytes) -> None:
        self.sock.sendall(response_body)

    def start_response(
        self,
        protocol_version: tuple[int, int],
        status: str,
        headers: list[tuple[str, str]],
        exc_info: ExcInfo | None = None,
    ) -> Callable[[bytes], None]:
        status_line = f"HTTP/{protocol_version[0]}.{protocol_version[1]} {status}\r\n"
        header_fields = "".join(f"{name}: {value}\r\n" for name, value in headers)

        def _write(data: bytes) -> None:
            pre_body = (status_line + header_fields).encode("latin-1") + b"\r\n"
            self.sock.sendall(pre_body)
            self.write(data)

        return _write
