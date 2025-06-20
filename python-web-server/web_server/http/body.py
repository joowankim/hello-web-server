import sys
from typing import Self

from web_server.http import reader
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
                content_length = value
            elif name == "TRANSFER-ENCODING":
                # T-E can be a list
                # https://datatracker.ietf.org/doc/html/rfc9112#name-transfer-encoding
                vals = [v.strip() for v in value.split(",")]
                for val in vals:
                    if val.lower() == "chunked":
                        # DANGER: transfer codings stack, and stacked chunking is never intended
                        if chunked:
                            raise InvalidHeader("TRANSFER-ENCODING")
                        chunked = True
                    elif val.lower() == "identity":
                        # does not do much, could still plausibly desync from what the proxy does
                        # safe option: nuke it, its never needed
                        if chunked:
                            raise InvalidHeader("TRANSFER-ENCODING")
                    elif val.lower() in ("compress", "deflate", "gzip"):
                        raise InvalidHeader("TRANSFER-ENCODING")
                    else:
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
            try:
                if str(content_length).isnumeric():
                    content_length = int(content_length)
                else:
                    raise InvalidHeader("CONTENT-LENGTH")
            except ValueError:
                raise InvalidHeader("CONTENT-LENGTH")

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
