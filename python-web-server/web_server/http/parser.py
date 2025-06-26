import io
import re
from collections.abc import Generator
from typing import ClassVar

from web_server import config
from web_server.http import reader, message, body
from web_server.http.errors import (
    InvalidHTTPVersion,
    InvalidRequestLine,
    InvalidRequestMethod,
    LimitRequestLine,
    InvalidHeader,
    LimitRequestHeaders,
)
from web_server.util import split_request_uri, bytes_to_str


def should_close(version: tuple[int, int], headers: list[tuple[str, str]]) -> bool:
    upper_headers = set((h.upper(), v.upper()) for h, v in headers)
    if version < (1, 1):
        if ("CONNECTION", "KEEP-ALIVE") in upper_headers:
            return False
        return True
    if ("CONNECTION", "CLOSE") in upper_headers:
        return True
    return False


class RequestParser:
    PROTOCOL_VERSION_TOKEN: ClassVar[re.Pattern] = re.compile(
        r"HTTP/(?P<major>\d+)\.(?P<minor>\d+)"
    )
    RFC9110_5_6_2_TOKEN_SPECIALS: ClassVar[str] = r"!#$%&'*+-.^_`|~"
    TOKEN_PATTERN: ClassVar[re.Pattern] = re.compile(
        rf"[{re.escape(RFC9110_5_6_2_TOKEN_SPECIALS)}\w]+"
    )
    METHOD_BADCHAR_RE: ClassVar[re.Pattern] = re.compile("[a-z#]")

    def __init__(self, cfg: config.MessageConfig, socket_reader: reader.SocketReader):
        self.cfg = cfg
        self.reader = socket_reader

    def parse(self) -> Generator[message.Request, None, None]:
        while self.reader.read(1):
            self.reader.unread(1)
            method, (path, query, fragment), version = self.parse_request_line()
            headers = self.parse_headers()
            req_body = body.RequestBody.create(version, headers, self.reader)
            if req_body is not None and isinstance(
                req_body.reader, reader.ChunkedReader
            ):
                headers += req_body.reader.trailers
            yield message.Request(
                method=method,
                path=path,
                query=query,
                fragment=fragment,
                headers=headers,
                body=req_body or body.RequestBody(io.BytesIO(b"")),
                version=version,
            )
            if should_close(version, headers):
                break

    def parse_request_line(self) -> tuple[str, tuple[str, str, str], tuple[int, int]]:
        line = self.reader.read_until(b"\r\n", self.cfg.limit_request_line)
        if not line:
            raise InvalidRequestLine(line)

        decoded_line = bytes_to_str(line)
        if not decoded_line.endswith("\r\n"):
            raise LimitRequestLine()
        tokens = decoded_line.split(" ")
        if len(tokens) < 3:
            raise InvalidRequestLine(decoded_line)

        method, uri, version = tokens

        # validate method
        if not self.cfg.permit_unconventional_http_method:
            if self.METHOD_BADCHAR_RE.search(method):
                raise InvalidRequestMethod(method)
            if not 3 <= len(method) <= 20:
                raise InvalidRequestMethod(method)
        if not self.TOKEN_PATTERN.fullmatch(method):
            raise InvalidRequestMethod(method)

        # validate uri
        if not uri:
            raise InvalidRequestLine(decoded_line)

        try:
            parts = split_request_uri(uri)
        except ValueError:
            raise InvalidRequestLine(decoded_line)
        path, query, fragment = (
            parts.path or "",
            parts.query or "",
            parts.fragment or "",
        )

        # validate http version
        matched = self.PROTOCOL_VERSION_TOKEN.match(version)
        if not matched:
            raise InvalidHTTPVersion(version)
        version = (int(matched.group("major")), int(matched.group("minor")))
        if not (1, 0) <= version < (2, 0):
            if not self.cfg.permit_unconventional_http_version:
                raise InvalidHTTPVersion(version)

        return method, (path, query, fragment), version

    def parse_headers(self) -> list[tuple[str, str]]:
        headers = []

        while True:
            if len(headers) > self.cfg.limit_request_fields:
                raise LimitRequestHeaders("limit request headers fields")
            header_line = self.reader.read_until(b"\r\n")
            if header_line == b"\r\n":
                break
            if len(header_line) > self.cfg.limit_request_field_size:
                raise LimitRequestHeaders("limit request header field size")
            header_parts = header_line.decode().strip().split(": ", 1)
            if len(header_parts) != 2:
                raise InvalidHeader(header_line)
            headers.append(
                (header_parts[0].upper().rstrip(" \t"), header_parts[1].strip(" \t"))
            )
        return headers
