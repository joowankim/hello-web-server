import socket
from typing import cast

import pytest

from tests import fake
from web_server.http.reader import ChunkedReader, SocketReader


@pytest.fixture
def socket_reader(request: pytest.FixtureRequest) -> SocketReader:
    payload: bytes = request.param
    fake_sock = fake.FakeSocket(payload)
    fake_sock = cast(socket.socket, fake_sock)
    return SocketReader(sock=fake_sock, max_chunk=8192)


@pytest.mark.parametrize(
    "socket_reader, expected_data, expected_trailers",
    [
        (
            (b"5\r\nhello\r\n6\r\n world\r\n0\r\n\r\n"),
            b"hello world",
            [],
        ),
        (
            (
                b"5\r\nhello\r\n6\r\n world\r\n0\r\n"
                b"Vary: *\r\nContent-Type: text/plain\r\n\r\n"
            ),
            b"hello world",
            [("Vary", "*"), ("Content-Type", "text/plain")],
        ),
        (
            (
                b"5; some; parameters=stuff\r\nhello\r\n"
                b"6; blahblah; blah\r\n world\r\n"
                b"0\r\n\r\n"
            ),
            b"hello world",
            [],
        ),
    ],
    indirect=["socket_reader"],
)
def test_parse_chunked(
    socket_reader: SocketReader,
    expected_data: bytes,
    expected_trailers: list[tuple[str, str]],
):
    reader = ChunkedReader.parse_chunked(socket_reader)

    assert reader.buf.read() == expected_data
    assert reader.trailers == expected_trailers


@pytest.fixture
def chunked_reader(request: pytest.FixtureRequest) -> ChunkedReader:
    payload: bytes = request.param
    fake_sock = fake.FakeSocket(payload)
    fake_sock = cast(socket.socket, fake_sock)
    return ChunkedReader.parse_chunked(socket_reader=SocketReader(fake_sock))


@pytest.mark.parametrize(
    "chunked_reader, sizes, expected_list",
    [
        (
            b"6\r\nhello,\r\n7\r\n world!\r\n0\r\n\r\n",
            [5, 5, 5, 5],
            [b"hello", b", wor", b"ld!", b""],
        ),
        (
            (
                b"5\r\nhello\r\n6\r\n world\r\n0\r\n"
                b"Vary: *\r\nContent-Type: text/plain\r\n\r\n"
            ),
            [0, 6, 7, 5],
            [b"", b"hello ", b"world", b""],
        ),
        (
            (
                b"5; some; parameters=stuff\r\nhello\r\n"
                b"6; blahblah; blah\r\n world\r\n"
                b"0\r\n\r\n"
            ),
            [5, 5, 5, 5],
            [b"hello", b" worl", b"d", b""],
        ),
    ],
    indirect=["chunked_reader"],
)
def test_read(
    chunked_reader: ChunkedReader, sizes: list[int | None], expected_list: list[bytes]
):
    for size, expected in zip(sizes, expected_list):
        assert chunked_reader.read(size) == expected
