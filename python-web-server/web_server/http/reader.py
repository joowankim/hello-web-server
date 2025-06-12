import io
import socket


class SocketUnreader:
    def __init__(self, sock: socket.socket, max_chunk: int = 8192):
        self.buf = io.BytesIO()
        self.sock = sock
        self.max_chunk = max_chunk

    def chunk(self) -> bytes:
        return self.sock.recv(self.max_chunk)

    def read(self) -> bytes: ...

    def unread(self) -> None: ...
