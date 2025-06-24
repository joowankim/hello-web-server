import socket
from typing import cast

import pytest

from tests import fake
from web_server.http.reader import SocketReader
from web_server.request import Request


@pytest.fixture
def socket_reader(request: pytest.FixtureRequest) -> SocketReader:
    payload: bytes = request.param
    fake_sock = fake.FakeSocket(payload)
    fake_sock = cast(socket.socket, fake_sock)
    return SocketReader(sock=fake_sock, max_chunk=8192)


@pytest.mark.parametrize(
    "socket_reader, expected",
    [
        (
            b"GET / HTTP/1.1\r\nHost: example.com\r\nContent-Length: 13\r\n\r\nHello, World!",
            (
                "GET",
                "/",
                [("Host", "example.com"), ("Content-Length", "13")],
                b"Hello, World!",
            ),
        ),
        (
            b"POST /submit HTTP/1.1\r\nHost: example.com\r\nContent-Length: 0\r\n\r\n",
            (
                "POST",
                "/submit",
                [("Host", "example.com"), ("Content-Length", "0")],
                b"",
            ),
        ),
        (
            b"PUT /update HTTP/1.0\r\nHost: example.com\r\n\r\n",
            ("PUT", "/update", [("Host", "example.com")], b""),
        ),
        (
            b"DELETE /delete HTTP/1.1\r\nHost: example.com\r\nContent-Length: 0\r\n\r\n",
            (
                "DELETE",
                "/delete",
                [("Host", "example.com"), ("Content-Length", "0")],
                b"",
            ),
        ),
        (
            b"POST /upload HTTP/1.1\r\nHost: example.com\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nHello\r\n3\r\n, W\r\n5\r\norld!\r\n0\r\n\r\n",
            (
                "POST",
                "/upload",
                [("Host", "example.com"), ("Transfer-Encoding", "chunked")],
                b"Hello, World!",
            ),
        ),
    ],
    indirect=["socket_reader"],
)
def test_create(
    socket_reader: SocketReader, expected: tuple[str, str, list[tuple[str, str]], bytes]
):
    req = Request.create(socket_reader)

    method, url, headers, body = expected
    assert req.method == method
    assert req.url == url
    assert req.headers == headers
    assert req.body.read() == body
