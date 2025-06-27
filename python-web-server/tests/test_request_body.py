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
        ((1, 1), [], b"\r\n", b""),
        ((1, 1), [], b"\r\n\r\n", b""),
        ((1, 1), [], b"\r\n\r\nGET / HTTP/1.1\r\nHost: example.com\r\n\r\n", b""),
        ((1, 0), [("CONNECTION", "Keep-Alive")], b"GET /second HTTP/1.1\r\n\r\n", b""),
        (
            (1, 1),
            [("Transfer-Encoding", "gzip,chunked")],
            b"5\r\nHello\r\n0\r\n\r\n",
            b"Hello",
        ),
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
        (
            (1, 1),
            [("Transfer-Encoding", "chunked,gzip")],
            b"Hello, World!",
            InvalidHeader,
            "Invalid HTTP Header: 'TRANSFER-ENCODING'",
        ),
        (
            (1, 1),
            [("Transfer-Encoding", "identity,chunked,identity,chunked")],
            b"Hello, World!",
            InvalidHeader,
            "Invalid HTTP Header: 'TRANSFER-ENCODING'",
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


@pytest.fixture(params=[3, 8192])
def socket_chunk_size(request: pytest.FixtureRequest) -> int:
    return request.param


@pytest.fixture
def request_body(socket_chunk_size: int, request: pytest.FixtureRequest) -> RequestBody:
    payload: bytes = request.param
    fake_sock = fake.FakeSocket(payload)
    fake_sock = cast(socket.socket, fake_sock)
    return RequestBody.create(
        protocol_version=(1, 1),
        headers=[("Content-Length", str(len(payload)))],
        socket_reader=SocketReader(sock=fake_sock, max_chunk=socket_chunk_size),
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
        (b"GET /second HTTP/1.1\r\n\r\n", 22, b"GET /second HTTP/1.1\r\n"),
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


@pytest.mark.parametrize(
    "request_body, sizes, expected_list",
    [
        (b"", [None], [b""]),
        (b"", [1], [b""]),
        (b"abc", [0], [b""]),
        (b"\n", [0], [b""]),
        (b"abc\ndef", [4, None], [b"abc\n", b"def"]),
        (b"abc\ndef", [2, 2, None], [b"ab", b"c\n", b"def"]),
        (b"abcdef", [None], [b"abcdef"]),
        (b"abcdef", [2, 2, 2], [b"ab", b"cd", b"ef"]),
        (b"abc\ndefg\nhi", [1, None, None, None], [b"a", b"bc\n", b"defg\n", b"hi"]),
        (b"abc\ndef", [1, 2, 2, 2, 2], [b"a", b"bc", b"\n", b"de", b"f"]),
        (
            b"GET /second HTTP/1.1\r\n\r\n",
            [None, None],
            [b"GET /second HTTP/1.1\r\n", b"\r\n"],
        ),
    ],
    indirect=["request_body"],
)
def test_readline(
    request_body: RequestBody, sizes: list[int | None], expected_list: list[bytes]
):
    for size, expected in zip(sizes, expected_list):
        assert request_body.readline(size) == expected


@pytest.mark.parametrize(
    "request_body, hint, expected",
    [
        (b"Hello, \nWorld!", None, [b"Hello, \n", b"World!"]),
        (b"Hello, \nWorld!", 5, [b"Hello, \n"]),
        (b"Hello, \nWorld!", 10, [b"Hello, \n", b"World!"]),
        (b"", None, []),
        (b"", 5, []),
        (b"\n", None, [b"\n"]),
        (b"\na", 1, [b"\n"]),
        (b"\na", 2, [b"\n", b"a"]),
    ],
    indirect=["request_body"],
)
def test_readlines(request_body: RequestBody, hint: int | None, expected: list[bytes]):
    lines = request_body.readlines(hint)

    assert lines == expected
