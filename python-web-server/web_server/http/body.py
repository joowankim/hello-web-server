import sys
from typing import Self

from web_server.http import reader, header
from web_server.http.errors import InvalidHeader, UnsupportedTransferCoding


class RequestBody:
    def __init__(self, body_reader: reader.BodyReader):
        self.reader = body_reader

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
                if vals == (header.TransferEncoding.CHUNKED,):
                    chunked = True
                if len(vals) > 1 and {header.TransferEncoding.CHUNKED}.issubset(
                    set(vals)
                ):
                    raise InvalidHeader("TRANSFER-ENCODING")
                if not set(vals).issubset(set(header.TransferEncoding)):
                    raise UnsupportedTransferCoding(value)

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
            return cls(body_reader=reader.LengthReader(socket_reader, content_length))
        else:
            return cls(body_reader=reader.EOFReader(socket_reader))

    def read(self, size: int | None = None) -> bytes:
        if size is not None and not isinstance(size, int):
            raise TypeError("size parameter must be an int or long.")

        if size is None:
            size = sys.maxsize
        elif not isinstance(size, int):
            raise TypeError("size must be an integer type")
        elif size < 0:
            size = sys.maxsize

        return self.reader.read(size)
