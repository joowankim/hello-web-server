import io
import os
import socket
from collections.abc import Generator

from typing import Self, IO, ClassVar


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

    def unread(self, size: int) -> None:
        if not isinstance(size, int):
            raise TypeError("size must be an integer type")
        if size < 0:
            raise ValueError("Size must be positive.")
        if size == 0:
            return

        self._read_cursor = max(0, self._read_cursor - size)
        self.buf.seek(self._read_cursor, os.SEEK_SET)


class LengthReader:
    def __init__(self, socket_reader: SocketReader, length: int):
        self.socket_reader = socket_reader
        self.length = length

    def read(self, size: int) -> bytes:
        if not isinstance(size, int):
            raise TypeError("size must be an integer type")

        size = min(size, self.length)
        if size < 0:
            raise ValueError("Size must be positive.")
        if size == 0:
            return b""

        self.length -= size
        return self.socket_reader.read(size)


class Chunk:
    CRLF_NOT_FOUND: ClassVar[int] = -1

    def __init__(
        self, data: IO[bytes], size: int, trailers: list[tuple[str, str]] | None = None
    ):
        self.data = data
        self.size = size
        self.trailers = trailers

    @classmethod
    def from_socket_reader(
        cls, socket_reader: SocketReader
    ) -> Generator[Self, None, None]:
        buf = io.BytesIO()
        CRLF = b"\r\n"
        CRLF_LENGTH = len(CRLF)

        stream = socket_reader.read()
        buf.write(stream)
        while stream:
            buf.write(stream)
            idx = buf.getvalue().find(CRLF)
            while idx == cls.CRLF_NOT_FOUND:
                stream = socket_reader.read()
                if not stream:
                    break
                buf.write(stream)
                idx = buf.getvalue().find(CRLF)
            size_line = buf.getvalue()[:idx]
            chunk_size, *_ = size_line.split(b";", 1)
            size = int(chunk_size.rstrip(b" \t"), 16)
            chunk_start, chunk_end = idx + CRLF_LENGTH, idx + CRLF_LENGTH + size
            if size == 0:
                chunk_end = buf.getvalue().find(CRLF + CRLF)
                while chunk_end == -1:
                    stream = socket_reader.read()
                    if not stream:
                        break
                    buf.write(stream)
                    chunk_end = buf.getvalue().find(CRLF + CRLF)
            yield cls(data=io.BytesIO(buf.getvalue()[chunk_start:chunk_end]), size=size)
            if size == 0:
                break
            buf = io.BytesIO(buf.getvalue()[chunk_end + CRLF_LENGTH :])
            stream = socket_reader.read()
