import io
import sys
from typing import Self

from web_server.http import reader, header
from web_server.http.errors import InvalidHeader, UnsupportedTransferCoding


class RequestBody:
    def __init__(self, body_reader: reader.BodyReader):
        self.reader = body_reader
        self.buf = io.BytesIO()
        self._read_cursor = 0

    def __iter__(self):
        return self

    def __next__(self):
        ret = self.readline()
        if not ret:
            raise StopIteration()
        return ret

    @classmethod
    def create(
        cls,
        protocol_version: tuple[int, int],
        headers: list[tuple[str, str]],
        socket_reader: reader.SocketReader,
    ) -> Self:
        chunked = False
        content_length = None

        for name, value in headers:
            name = name.upper()
            if name == "CONTENT-LENGTH":
                if content_length is not None:
                    raise InvalidHeader("CONTENT-LENGTH")
                if not str(value).isnumeric():
                    raise InvalidHeader("CONTENT-LENGTH")
                content_length = int(value)
            elif name == "TRANSFER-ENCODING":
                # T-E can be a list
                # https://datatracker.ietf.org/doc/html/rfc9112#name-transfer-encoding
                vals = tuple(v.strip().lower() for v in value.split(","))
                if len(vals) == 1:
                    if vals != (header.TransferEncoding.CHUNKED,):
                        raise InvalidHeader("TRANSFER-ENCODING")
                    chunked = True
                elif len(vals) > 1:
                    if vals[-1] != header.TransferEncoding.CHUNKED:
                        raise InvalidHeader("TRANSFER-ENCODING")
                    chunked = True
                if not set(vals).issubset(set(header.TransferEncoding)):
                    raise UnsupportedTransferCoding(value)

        if not chunked and content_length is None:
            # RFC 9112 Section 6.1: If no Transfer-Encoding or Content-Length header is present,
            # the message body is considered to be empty.
            return cls(body_reader=reader.EOFReader(io.BytesIO(b"")))

        if chunked:
            # two potentially dangerous cases:
            #  a) CL + TE (TE overrides CL.. only safe if the recipient sees it that way too)
            #  b) chunked HTTP/1.0 (always faulty)
            if protocol_version < (1, 1):
                # framing wonky, see RFC 9112 Section 6.1
                raise InvalidHeader("TRANSFER-ENCODING")
            if content_length is not None:
                # we cannot be certain the message framing we understood matches proxy intent
                #  -> whatever happens next, remaining input must not be trusted
                raise InvalidHeader("CONTENT-LENGTH")
            return cls(body_reader=reader.ChunkedReader.parse_chunked(socket_reader))
        elif content_length is not None:
            if content_length < 0:
                raise InvalidHeader("CONTENT-LENGTH")
            return cls(
                body_reader=reader.LengthReader.parse_content(
                    socket_reader, content_length
                )
            )
        else:
            return cls(body_reader=reader.EOFReader.parse_content(socket_reader))

    def read(self, size: int | None = None) -> bytes:
        if size is not None and not isinstance(size, int):
            raise TypeError("size parameter must be an int or long.")

        new_size = sys.maxsize if size is None or size < 0 else size

        self.buf.write(self.reader.read(new_size))
        self.buf.seek(self._read_cursor, io.SEEK_SET)
        data = self.buf.read(new_size)
        self._read_cursor = self.buf.tell()
        return data

    def readline(self, size: int | None = None) -> bytes:
        if size is not None and not isinstance(size, int):
            raise TypeError("size parameter must be an int or long.")

        new_size = sys.maxsize if size is None or size < 0 else size

        self.buf.seek(0, io.SEEK_END)
        chunk_size = 1024
        while self.buf.tell() < self._read_cursor + new_size:
            data = self.reader.read(chunk_size)
            if not data:
                break
            self.buf.write(data)
        self.buf.seek(self._read_cursor, io.SEEK_SET)
        data = self.buf.read(new_size)
        new_line_index = data.find(b"\n")
        if new_line_index != -1:
            self._read_cursor += new_line_index + 1
            return data[: new_line_index + 1]
        self._read_cursor = self.buf.tell()
        return data

    def readlines(self, hint: int | None = None) -> list[bytes]:
        if hint is not None and not isinstance(hint, int):
            raise TypeError("hint parameter must be an int or long.")

        if hint is None or hint < 0:
            return [line for line in self]

        lines = []
        while sum(len(line) for line in lines) < hint:
            line = self.readline()
            if not line:
                break
            lines.append(line)
        return lines
