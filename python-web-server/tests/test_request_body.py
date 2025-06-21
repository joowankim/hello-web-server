import socket
from typing import cast

import pytest

from tests import fake
from web_server.http.body import RequestBody
from web_server.http.errors import InvalidHeader, UnsupportedTransferCoding
from web_server.http.reader import SocketReader


@pytest.fixture
def socket_reader(request: pytest.FixtureRequest) -> SocketReader:
    payload: bytes = request.param
    fake_sock = fake.FakeSocket(payload)
    fake_sock = cast(socket.socket, fake_sock)
    return SocketReader(sock=fake_sock, max_chunk=8192)


@pytest.mark.parametrize(
    "protocol_version, headers, socket_reader, expected",
    [
        ((1, 1), [("Content-Length", "13")], b"Hello, World!\r\n", b"Hello, World!"),
        ((1, 0), [("Content-Length", "13")], b"Hello, World!\r\n", b"Hello, World!"),
        (
            (1, 1),
            [("Transfer-Encoding", "chunked")],
            b"5\r\nHello\r\n3\r\n, W\r\n5\r\norld!\r\n0\r\n\r\n",
            b"Hello, World!",
        ),
        ((1, 1), [("Content-Length", "0")], b"\r\n", b""),
        ((1, 0), [("Content-Length", "0")], b"\r\n", b""),
        ((1, 1), [], b"", b""),
        ((1, 0), [], b"", b""),
    ],
    indirect=["socket_reader"],
)
def test_create(
    protocol_version: tuple[int, int],
    headers: list[tuple[str, str]],
    socket_reader: SocketReader,
    expected: bytes,
):
    body = RequestBody.create(
        protocol_version=protocol_version, headers=headers, socket_reader=socket_reader
    )

    assert body.read() == expected


@pytest.mark.parametrize(
    "protocol_version, headers, socket_reader, error_type, error_message",
    [
        (
            (1, 1),
            [("Content-Length", "invalid")],
            b"Hello, World!",
            InvalidHeader,
            "Invalid HTTP Header: 'CONTENT-LENGTH'",
        ),
        (
            (1, 0),
            [("Content-Length", "invalid")],
            b"Hello, World!",
            InvalidHeader,
            "Invalid HTTP Header: 'CONTENT-LENGTH'",
        ),
        (
            (1, 1),
            [("Transfer-Encoding", "invalid")],
            b"Hello, World!",
            UnsupportedTransferCoding,
            "Unsupported transfer coding: 'invalid'",
        ),
        (
            (1, 0),
            [("Transfer-Encoding", "chunked")],
            b"Hello, World!",
            InvalidHeader,
            "Invalid HTTP Header: 'TRANSFER-ENCODING'",
        ),
        (
            (1, 1),
            [("Content-Length", "-5")],
            b"Hello, World!",
            InvalidHeader,
            "Invalid HTTP Header: 'CONTENT-LENGTH'",
        ),
        (
            (1, 0),
            [("Content-Length", "-5")],
            b"Hello, World!",
            InvalidHeader,
            "Invalid HTTP Header: 'CONTENT-LENGTH'",
        ),
        (
            (1, 1),
            [("Transfer-Encoding", "chunked"), ("Content-Length", "5")],
            b"Hello",
            InvalidHeader,
            "Invalid HTTP Header: 'CONTENT-LENGTH'",
        ),
    ],
    indirect=["socket_reader"],
)
def test_create_with_invalid_request(
    protocol_version: tuple[int, int],
    headers: list[tuple[str, str]],
    socket_reader: SocketReader,
    error_type: type[Exception],
    error_message: str,
):
    with pytest.raises(error_type, match=error_message):
        RequestBody.create(
            protocol_version=protocol_version,
            headers=headers,
            socket_reader=socket_reader,
        )


@pytest.fixture
def request_body(request: pytest.FixtureRequest) -> RequestBody:
    payload: bytes = request.param
    fake_sock = fake.FakeSocket(payload)
    fake_sock = cast(socket.socket, fake_sock)
    return RequestBody.create(
        protocol_version=(1, 1),
        headers=[("Content-Length", str(len(payload)))],
        socket_reader=SocketReader(sock=fake_sock, max_chunk=8192),
    )


@pytest.mark.parametrize(
    "request_body, size, expected",
    [
        (b"Hello, World!", None, b"Hello, World!"),
        (b"Hello, World!", 5, b"Hello"),
        (b"Hello, World!", 13, b"Hello, World!"),
        (b"Hello, World!", 0, b""),
        (b"", None, b""),
        (b"", 0, b""),
        (b"", 5, b""),
    ],
    indirect=["request_body"],
)
def test_read(request_body: RequestBody, size: int | None, expected: bytes):
    data = request_body.read(size)

    assert data == expected


@pytest.mark.parametrize(
    "request_body, sizes, expected_list",
    [
        (b"Hello, World!", [5, 5, 5, 5], [b"Hello", b", Wor", b"ld!", b""]),
        (b"", [0, 5], [b"", b""]),
    ],
    indirect=["request_body"],
)
def test_read_iteration(
    request_body: RequestBody, sizes: list[int | None], expected_list: list[bytes]
):
    for size, expected in zip(sizes, expected_list):
        assert request_body.read(size) == expected
