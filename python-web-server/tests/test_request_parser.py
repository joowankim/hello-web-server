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
    LimitRequestHeaders,
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
        (
            (
                dict(),
                b"Host: example.com\r\nContent-Length: 13\r\n\r\nHello, World!",
            ),
            InvalidRequestLine,
            re.escape(r"Invalid HTTP request line: 'Host: example.com\r\n'"),
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


@pytest.mark.parametrize(
    "request_parser, expected",
    [
        (
            (
                dict(),
                b"Host: example.com\r\nContent-Length: 13\r\n\r\nHello, World!",
            ),
            [("HOST", "example.com"), ("CONTENT-LENGTH", "13")],
        ),
        (
            (
                dict(),
                b"User-Agent: TestAgent/1.0\r\nAccept: */*\r\n\r\n",
            ),
            [("USER-AGENT", "TestAgent/1.0"), ("ACCEPT", "*/*")],
        ),
        (
            (
                dict(),
                b"X-Custom-Header: Value\r\nX-Another-Header: AnotherValue\r\n\r\n",
            ),
            [("X-CUSTOM-HEADER", "Value"), ("X-ANOTHER-HEADER", "AnotherValue")],
        ),
        (
            (
                dict(limit_request_fields=3),
                b"Header1: Value1\r\nHeader2: Value2\r\nHeader3: Value3\r\n\r\n",
            ),
            [("HEADER1", "Value1"), ("HEADER2", "Value2"), ("HEADER3", "Value3")],
        ),
        (
            (
                dict(limit_request_field_size=100),
                b"Short: Value\r\nLongHeaderName: LongValueThatExceedsLimit\r\n\r\n",
            ),
            [("SHORT", "Value"), ("LONGHEADERNAME", "LongValueThatExceedsLimit")],
        ),
        (
            (
                dict(),
                b"Transfer-Encoding: identity\r\nTransfer-Encoding: chunked\r\n\r\n",
            ),
            [("TRANSFER-ENCODING", "identity"), ("TRANSFER-ENCODING", "chunked")],
        ),
        (
            (
                dict(),
                b"Host: localhost\r\nName: \t value \t \r\n\r\n",
            ),
            [("HOST", "localhost"), ("NAME", "value")],
        ),
    ],
    indirect=["request_parser"],
)
def test_parse_headers(request_parser: RequestParser, expected: list[tuple[str, str]]):
    headers = request_parser.parse_headers()

    assert headers == expected


@pytest.mark.parametrize(
    "request_parser, error_type, error_message",
    [
        (
            (
                dict(limit_request_fields=1),
                b"Header1: Value1\r\nHeader2: Value2\r\n\r\n",
            ),
            LimitRequestHeaders,
            "limit request headers fields",
        ),
        (
            (
                dict(limit_request_field_size=5),
                b"Short: Value\r\nLongHeaderName: LongValueThatExceedsLimit\r\n\r\n",
            ),
            LimitRequestHeaders,
            "limit request header field size",
        ),
    ],
    indirect=["request_parser"],
)
def test_parse_headers_with_invalid_stream(
    request_parser: RequestParser, error_type: type[Exception], error_message: str
):
    with pytest.raises(error_type, match=error_message):
        request_parser.parse_headers()


@pytest.mark.parametrize(
    "request_parser, expected_list",
    [
        (
            (
                dict(),
                b"GET / HTTP/1.1\r\nHost: example.com\r\nContent-Length: 13\r\n\r\nHello, World!",
            ),
            [
                (
                    "GET",
                    ("/", "", ""),
                    (1, 1),
                    [("HOST", "example.com"), ("CONTENT-LENGTH", "13")],
                    b"Hello, World!",
                ),
            ],
        ),
        (
            (
                dict(),
                b"POST /upload HTTP/1.1\r\nHost: example.com\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nHello\r\n3\r\n, W\r\n5\r\norld!\r\n0\r\n\r\n",
            ),
            [
                (
                    "POST",
                    ("/upload", "", ""),
                    (1, 1),
                    [("HOST", "example.com"), ("TRANSFER-ENCODING", "chunked")],
                    b"Hello, World!",
                ),
            ],
        ),
        (
            (dict(), b"PUT /update HTTP/1.0\r\nHost: example.com\r\n\r\n"),
            [
                ("PUT", ("/update", "", ""), (1, 0), [("HOST", "example.com")], b""),
            ],
        ),
        (
            (
                dict(),
                b"POST /first HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n0\r\n\r\nPOST /second HTTP/1.1\r\nContent-Length: 5\r\n\r\nHello\r\n\r\n",
            ),
            [
                (
                    "POST",
                    ("/first", "", ""),
                    (1, 1),
                    [("TRANSFER-ENCODING", "chunked")],
                    b"hello",
                ),
                (
                    "POST",
                    ("/second", "", ""),
                    (1, 1),
                    [("CONTENT-LENGTH", "5")],
                    b"Hello",
                ),
            ],
        ),
        (
            (
                dict(),
                (
                    b"POST /first HTTP/1.1\r\nTransfer-Encoding: chunked\r\nConnection: Close\r\n\r\n"
                    b"5\r\nhello\r\n0\r\n\r\n"
                    b"POST /second HTTP/1.1\r\nContent-Length: 5\r\n\r\n"
                    b"Hello\r\n\r\n"
                ),
            ),
            [
                (
                    "POST",
                    ("/first", "", ""),
                    (1, 1),
                    [("TRANSFER-ENCODING", "chunked"), ("CONNECTION", "Close")],
                    b"hello",
                ),
            ],
        ),
    ],
    indirect=["request_parser"],
)
def test_parse(
    request_parser: RequestParser,
    expected_list: list[
        tuple[str, tuple[str, str, str], str, list[tuple[int, int]], bytes]
    ],
):
    for req, expected in zip(request_parser.parse(), expected_list):
        method, (path, query, fragment), version, headers, body = expected

        assert req.method == method
        assert req.path == path
        assert req.query == query
        assert req.fragment == fragment
        assert req.version == version
        assert req.headers == headers
        assert req.body.read() == body


@pytest.mark.parametrize(
    "request_parser, expected_list",
    [
        (
            (dict(), b"POST /submit HTTP/1.1\r\nHost: example.com\r\n\r\n"),
            [
                (
                    "POST",
                    ("/submit", "", ""),
                    (1, 1),
                    [("HOST", "example.com")],
                    b"",
                ),
            ],
        ),
        (
            (dict(), b"DELETE /delete HTTP/1.1\r\nHost: example.com\r\n\r\n"),
            [
                (
                    "DELETE",
                    ("/delete", "", ""),
                    (1, 1),
                    [("HOST", "example.com")],
                    b"",
                ),
            ],
        ),
        (
            (dict(), b"GET /first HTTP/1.1\r\n\r\nGET /second HTTP/1.1\r\n\r\n"),
            [
                (
                    "GET",
                    ("/first", "", ""),
                    (1, 1),
                    [],
                    b"",
                ),
                (
                    "GET",
                    ("/second", "", ""),
                    (1, 1),
                    [],
                    b"",
                ),
            ],
        ),
    ],
    indirect=["request_parser"],
)
def test_parse_with_empty_body(
    request_parser: RequestParser,
    expected_list: list[
        tuple[str, tuple[str, str, str], str, list[tuple[int, int]], bytes]
    ],
):
    for req, expected in zip(request_parser.parse(), expected_list):
        method, (path, query, fragment), version, headers, body = expected

        assert req.method == method
        assert req.path == path
        assert req.query == query
        assert req.fragment == fragment
        assert req.version == version
        assert req.headers == headers
        assert req.body.read() == body
