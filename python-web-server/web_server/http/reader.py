import io
import os
import socket
from collections.abc import Generator

from typing import Self, IO, ClassVar

from web_server.http.errors import InvalidChunkSize


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
    CRLF: ClassVar[bytes] = b"\r\n"

    def __init__(self, data: IO[bytes], size: int):
        self.data = data
        self.size = size

    @property
    def is_last(self) -> bool:
        return self.size == 0

    @property
    def trailers(self) -> list[tuple[str, str]]:
        if not self.is_last:
            return []
        return [
            tuple(
                [
                    value.replace(b"\r\n", b"").decode("utf-8").strip()
                    for value in line.split(b":")
                ]
            )
            for line in self.data.readlines()
        ]

    @classmethod
    def from_socket_reader(
        cls, socket_reader: SocketReader
    ) -> Generator[Self, None, None]:
        buf = io.BytesIO()
        crlf_length = len(cls.CRLF)

        while True:
            stream = socket_reader.read()
            buf.write(stream)
            size_end_idx = buf.getvalue().find(cls.CRLF)
            while size_end_idx == cls.CRLF_NOT_FOUND:
                stream = socket_reader.read()
                if not stream:
                    break
                buf.write(stream)
                size_end_idx = buf.getvalue().find(cls.CRLF)
            size_line = buf.getvalue()[:size_end_idx]
            chunk_size, *_ = size_line.split(b";", 1)
            if not chunk_size or any(
                n not in b"0123456789abcdefABCDEF" for n in chunk_size
            ):
                raise InvalidChunkSize(chunk_size)
            size = int(chunk_size.rstrip(b" \t"), 16)
            chunk_start = size_end_idx + crlf_length
            chunk_end = size_end_idx + crlf_length + size
            while chunk_end + crlf_length > buf.tell():
                buf.write(socket_reader.read())
            if size == 0:
                chunk_end = buf.getvalue().find(cls.CRLF + cls.CRLF)
                while chunk_end == cls.CRLF_NOT_FOUND:
                    stream = socket_reader.read()
                    if not stream:
                        break
                    buf.write(stream)
                    chunk_end = buf.getvalue().find(cls.CRLF + cls.CRLF)
            yield cls(data=io.BytesIO(buf.getvalue()[chunk_start:chunk_end]), size=size)
            if size == 0:
                break
            buf = io.BytesIO(buf.getvalue()[chunk_end + crlf_length :])
            buf.seek(0, os.SEEK_END)


class ChunkedReader:
    def __init__(self, buf: IO[bytes], trailers: list[tuple[str, str]]):
        self.buf = buf
        self.trailers = trailers
        self._read_cursor = 0

    @classmethod
    def parse_chunked(cls, socket_reader: SocketReader) -> Self:
        buf = io.BytesIO()
        trailers = []

        chunks = Chunk.from_socket_reader(socket_reader)
        for chunk in chunks:
            if chunk.is_last:
                trailers = chunk.trailers
                break
            chunk.data.seek(0, os.SEEK_SET)
            buf.write(chunk.data.read())
        buf.seek(0, os.SEEK_SET)
        return cls(buf, trailers)

    def read(self, size: int) -> bytes:
        if size is not None and not isinstance(size, int):
            raise TypeError("size must be an integer type")

        if size < 0:
            raise ValueError("Size must be positive.")
        if size == 0:
            return b""

        return self.buf.read(size)
