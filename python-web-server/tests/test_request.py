import socket
from typing import cast

import pytest

from tests import fake
from web_server.config import MessageConfig
from web_server.http.parser import RequestParser
from web_server.http.reader import SocketReader
from web_server.request import Request


@pytest.fixture
def message_config() -> MessageConfig:
    return MessageConfig.custom(
        limit_request_line=4094,
        limit_request_fields=100,
        limit_request_field_size=8190,
    )


@pytest.fixture
def request_parser(
    message_config: MessageConfig, request: pytest.FixtureRequest
) -> RequestParser:
    payload = request.param
    sock = fake.FakeSocket(payload)
    sock = cast(socket.socket, sock)
    socket_reader = SocketReader(sock, max_chunk=8192)
    return RequestParser(message_config, socket_reader)


@pytest.mark.parametrize(
    "request_parser, expected",
    [
        (
            b"GET / HTTP/1.1\r\nHost: example.com\r\nContent-Length: 13\r\n\r\nHello, World!",
            (
                "GET",
                ("/", "", ""),
                [("Host", "example.com"), ("Content-Length", "13")],
                b"Hello, World!",
            ),
        ),
        (
            b"POST /submit HTTP/1.1\r\nHost: example.com\r\nContent-Length: 0\r\n\r\n",
            (
                "POST",
                ("/submit", "", ""),
                [("Host", "example.com"), ("Content-Length", "0")],
                b"",
            ),
        ),
        (
            b"PUT /update HTTP/1.0\r\nHost: example.com\r\n\r\n",
            ("PUT", ("/update", "", ""), [("Host", "example.com")], b""),
        ),
        (
            b"DELETE /delete HTTP/1.1\r\nHost: example.com\r\nContent-Length: 0\r\n\r\n",
            (
                "DELETE",
                ("/delete", "", ""),
                [("Host", "example.com"), ("Content-Length", "0")],
                b"",
            ),
        ),
        (
            b"POST /upload HTTP/1.1\r\nHost: example.com\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nHello\r\n3\r\n, W\r\n5\r\norld!\r\n0\r\n\r\n",
            (
                "POST",
                ("/upload", "", ""),
                [("Host", "example.com"), ("Transfer-Encoding", "chunked")],
                b"Hello, World!",
            ),
        ),
    ],
    indirect=["request_parser"],
)
def test_create(
    request_parser: RequestParser,
    expected: tuple[str, str, list[tuple[str, str]], bytes],
):
    req = Request.create(request_parser=request_parser)

    method, (path, query, fragment), headers, body = expected
    assert req.method == method
    assert req.path == path
    assert req.query == query
    assert req.fragment == fragment
    assert req.headers == headers
    assert req.body.read() == body
