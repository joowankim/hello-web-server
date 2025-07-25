import abc
import io
import os
import socket
from collections.abc import Generator

from typing import Self, IO, ClassVar

from web_server.errors import InvalidChunkSize, InvalidHeader


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

    def read_until(self, target: bytes, limit: int | None = None) -> bytes:
        if not isinstance(target, bytes):
            raise TypeError("target must be of type bytes")
        if not target:
            raise ValueError("target must be non-empty")

        read_length = 0
        while True:
            self.buf.seek(self._read_cursor, os.SEEK_SET)
            data = self.buf.read()
            read_length += len(data)

            search_data = data
            if limit is not None:
                search_data = data[:limit]

            if (target_index := search_data.find(target)) != -1:
                target_next_index = target_index + len(target)
                self._read_cursor += target_next_index
                return data[:target_next_index]

            if limit is not None and read_length >= limit:
                self._read_cursor += limit
                return data[:limit]

            self.buf.seek(0, io.SEEK_END)
            chunk = self.chunk()
            if not chunk:
                self._read_cursor = self.buf.tell()
                return data

            self.buf.write(chunk)


class BodyReader(abc.ABC):
    @abc.abstractmethod
    def read(self, size: int) -> bytes:
        raise NotImplementedError


class LengthReader(BodyReader):
    def __init__(self, buf: IO[bytes], length: int):
        self.buf = buf
        self.length = length

    @classmethod
    def parse_content(cls, socket_reader: SocketReader, length: int) -> Self:
        buf = io.BytesIO()
        size = length
        data = socket_reader.read(size)
        while data:
            buf.write(data)
            if buf.tell() == length:
                break
            size -= len(data)
            data = socket_reader.read(size)
        if (d := socket_reader.read_until(b"\r\n\r\n")) != b"\r\n\r\n":
            socket_reader.unread(len(d))
        buf.seek(0, os.SEEK_SET)
        return cls(buf=buf, length=length)

    def read(self, size: int) -> bytes:
        if not isinstance(size, int):
            raise TypeError("size must be an integer type")

        size = min(size, self.length)
        if size < 0:
            raise ValueError("Size must be positive.")
        if size == 0:
            return b""

        self.length -= size
        return self.buf.read(size)


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
        headers = [
            tuple(
                [
                    value.replace(b"\r\n", b"").decode("utf-8").strip()
                    for value in line.split(b":")
                ]
            )
            for line in self.data.readlines()
        ]
        return [(key.upper(), value) for key, value in headers]

    @classmethod
    def from_socket_reader(
        cls, socket_reader: SocketReader
    ) -> Generator[Self, None, None]:
        while True:
            buf = io.BytesIO()
            chunk_size_line = socket_reader.read_until(cls.CRLF).replace(cls.CRLF, b"")
            chunk_size, *_ = chunk_size_line.split(b";", 1)
            if not chunk_size or any(
                n not in b"0123456789abcdefABCDEF" for n in chunk_size
            ):
                raise InvalidChunkSize(chunk_size)
            size = int(chunk_size.rstrip(b" \t"), 16)
            if size == 0:
                content = b""
                data = socket_reader.read_until(cls.CRLF)
                while data != cls.CRLF:
                    if data == b"":
                        break
                    content += data
                    data = socket_reader.read_until(cls.CRLF)
            else:
                content = socket_reader.read_until(cls.CRLF).replace(cls.CRLF, b"")
                if size != len(content):
                    raise InvalidHeader(
                        f"Chunk size {size} does not match content length {len(content)}"
                    )
            buf.write(content)
            buf.seek(0, io.SEEK_SET)
            yield cls(data=buf, size=size)
            if size == 0:
                break


class ChunkedReader(BodyReader):
    def __init__(self, buf: IO[bytes], trailers: list[tuple[str, str]]):
        self.buf = buf
        self.trailers = trailers

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


class EOFReader(BodyReader):
    def __init__(self, buf: IO[bytes]):
        self.buf = buf

    @classmethod
    def parse_content(cls, socket_reader: SocketReader) -> Self:
        buf = io.BytesIO()
        data = socket_reader.read_until(b"\r\n\r\n")
        buf.write(data[: -len(b"\r\n\r\n")])
        buf.seek(0, os.SEEK_SET)
        return cls(buf=buf)

    def read(self, size: int) -> bytes:
        if not isinstance(size, int):
            raise TypeError("size must be an integer type")
        if size < 0:
            raise ValueError("Size must be positive.")
        if size == 0:
            return b""

        return self.buf.read(size)
