import re
import socket
from typing import cast

import pytest

from tests import fake
from web_server.config import MessageConfig
from web_server.http.errors import (
    InvalidRequestLine,
    InvalidRequestMethod,
    InvalidHTTPVersion,
    LimitRequestLine,
)
from web_server.http.parser import RequestParser
from web_server.http.reader import SocketReader


@pytest.fixture
def request_parser(request: pytest.FixtureRequest) -> RequestParser:
    cfg_param, payload = request.param
    cfg = MessageConfig.custom(**cfg_param)
    sock = fake.FakeSocket(payload)
    sock = cast(socket.socket, sock)
    socket_reader = SocketReader(sock, max_chunk=8192)
    return RequestParser(cfg, socket_reader)


@pytest.mark.parametrize(
    "request_parser, expected",
    [
        (
            (
                dict(),
                b"GET / HTTP/1.1\r\nHost: example.com\r\nContent-Length: 13\r\n\r\nHello, World!",
            ),
            ("GET", ("/", "", ""), (1, 1)),
        ),
        (
            (
                dict(),
                b"GET /path/to/resource?ab=123#sec1 HTTP/1.1\r\nHost: example.com\r\nContent-Length: 0\r\n\r\n",
            ),
            ("GET", ("/path/to/resource", "ab=123", "sec1"), (1, 1)),
        ),
        (
            (
                dict(),
                b"POST /submit HTTP/1.1\r\nHost: example.com\r\nContent-Length: 0\r\n\r\n",
            ),
            ("POST", ("/submit", "", ""), (1, 1)),
        ),
        (
            (
                dict(),
                b"PUT /api/data HTTP/1.0\r\nHost: api.example.com\r\nContent-Length: 5\r\n\r\nHello",
            ),
            ("PUT", ("/api/data", "", ""), (1, 0)),
        ),
        (
            (
                dict(),
                b"DELETE /resource/123 HTTP/1.0\r\nHost: example.com\r\n\r\n",
            ),
            ("DELETE", ("/resource/123", "", ""), (1, 0)),
        ),
    ],
    indirect=["request_parser"],
)
def test_parse_request_line(
    request_parser: RequestParser,
    expected: tuple[str, tuple[str, str, str], tuple[int, int]],
):
    method, uri, version = request_parser.parse_request_line()

    assert (method, uri, version) == expected


@pytest.mark.parametrize(
    "request_parser, error_type, error_message",
    [
        (
            (
                dict(),
                b"invalid / HTTP/1.1\r\nHost: example.com\r\nContent-Length: 13\r\n\r\nHello, World!",
            ),
            InvalidRequestMethod,
            "Invalid HTTP method: 'invalid'",
        ),
        (
            (
                dict(),
                b"GET /invalid_pathHTTP\r\nHost: example.com\r\nContent-Length: 13\r\n\r\nHello, World!",
            ),
            InvalidRequestLine,
            re.escape(
                r"Invalid HTTP request line: 'GET /invalid_pathHTTP\r\n'",
            ),
        ),
        (
            (
                dict(),
                b"GET / HTTP/invalid_version\r\nHost: example.com\r\nContent-Length: 13\r\n\r\nHello, World!",
            ),
            InvalidHTTPVersion,
            re.escape(r"Invalid HTTP Version: 'HTTP/invalid_version\r\n'"),
        ),
        (
            (
                dict(limit_request_line=5),
                b"GET / HTTP/1.1\r\nHost: example.com\r\nContent-Length: 13\r\n\r\n",
            ),
            LimitRequestLine,
            "Request Line is too large",
        ),
    ],
    indirect=["request_parser"],
)
def test_parse_request_line_with_invalid_stream(
    request_parser: RequestParser,
    error_type: type[Exception],
    error_message: str,
):
    with pytest.raises(error_type, match=error_message):
        request_parser.parse_request_line()
