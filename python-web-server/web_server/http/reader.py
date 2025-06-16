import io
import os
import socket


class SocketReader:
    def __init__(self, sock: socket.socket, max_chunk: int = 8192):
        self.buf = io.BytesIO()
        self.sock = sock
        self.max_chunk = max_chunk
        self._read_cursor = 0

    def chunk(self) -> bytes:
        return self.sock.recv(self.max_chunk)

    def read(self, size: int | None = None) -> bytes:
        if size is not None and not isinstance(size, int):
            raise TypeError("size parameter must be an int or long.")

        size = self.max_chunk if size is None else size
        if chunk := self.chunk():
            self.buf.seek(0, os.SEEK_END)
            self.buf.write(chunk)
        self.buf.seek(self._read_cursor, os.SEEK_SET)
        data = self.buf.read(size)
        self._read_cursor = self.buf.tell()
        return data
