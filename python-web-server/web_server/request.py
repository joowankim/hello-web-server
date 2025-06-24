import re
from collections.abc import Sequence
from typing import Self, ClassVar

from web_server.http import reader
from web_server.http.body import RequestBody
from web_server.http.errors import InvalidHTTPVersion


class Request:
    PROTOCOL_VERSION_TOKEN: ClassVar[re.Pattern] = re.compile(
        r"HTTP/(?P<major>\d+)\.(?P<minor>\d+)"
    )

    def __init__(
        self,
        method: str,
        url: str,
        headers: Sequence[tuple[str, str]],
        body: RequestBody,
    ):
        self.method = method
        self.url = url
        self.headers = headers
        self.body = body

    @classmethod
    def create(cls, socket_reader: reader.SocketReader) -> Self:
        line = socket_reader.read_until(b"\r\n")
        if not line:
            raise ValueError("Empty request line")

        parts = line.decode().split(" ")
        if len(parts) < 3:
            raise ValueError("Invalid request line")

        method, url, version = parts[0], parts[1], parts[2]
        matched = cls.PROTOCOL_VERSION_TOKEN.match(version)
        if not matched:
            raise InvalidHTTPVersion(version)
        version = (int(matched.group("major")), int(matched.group("minor")))
        headers = []

        while True:
            header_line = socket_reader.read_until(b"\r\n")
            if header_line == b"\r\n":
                break
            header_parts = header_line.decode().strip().split(": ", 1)
            if len(header_parts) != 2:
                raise ValueError("Invalid header format")
            headers.append((header_parts[0], header_parts[1]))

        body = RequestBody.create(version, headers, socket_reader)

        return cls(method=method, url=url, headers=headers, body=body)
