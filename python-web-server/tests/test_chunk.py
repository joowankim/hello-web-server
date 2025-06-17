import socket
from typing import cast

import pytest

from tests import fake
from web_server.http.errors import InvalidChunkSize
from web_server.http.reader import Chunk, SocketReader


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
            (b"5\r\nhello\r\n6\r\n world\r\n0\r\n\r\n"),
            [(b"hello", 5), (b" world", 6), (b"", 0)],
        ),
        (
            (
                b"5\r\nhello\r\n6\r\n world\r\n0\r\n"
                b"Vary: *\r\nContent-Type: text/plain\r\n\r\n"
            ),
            [
                (b"hello", 5),
                (b" world", 6),
                (b"Vary: *\r\nContent-Type: text/plain", 0),
            ],
        ),
        (
            (
                b"5; some; parameters=stuff\r\nhello\r\n"
                b"6; blahblah; blah\r\n world\r\n"
                b"0\r\n\r\n"
            ),
            [(b"hello", 5), (b" world", 6), (b"", 0)],
        ),
        (
            (b"5\r\nhello\r\n6\r\n world\r\n000\r\n\r\nGET /second HTTP/1.1\r\n\r\n"),
            [(b"hello", 5), (b" world", 6), (b"", 0)],
        ),
        (
            b"b\r\nhello world\r\n\r\n",
            [(b"hello world", 11)],
        ),
    ],
    indirect=["socket_reader"],
    ids=(
        "basic_chunks",
        "chunks_with_trailers",
        "chunks_with_chunk_extensions",
        "chunks_with_next_request",
        "single_chunk_with_hexadecimal_size",
    ),
)
def test_from_socket_reader(
    socket_reader: SocketReader, expected: list[tuple[bytes, int]]
):
    chunks = Chunk.from_socket_reader(socket_reader)

    for chunk, (data, size) in zip(chunks, expected):
        assert chunk.data.read() == data
        assert chunk.size == size


@pytest.mark.parametrize(
    "socket_reader, error_type, error_message",
    [
        (
            b"-5\r\nhello\r\n6\r\n world\r\n0\r\n\r\n",
            InvalidChunkSize,
            "Invalid chunk size: b'-5'",
        ),
        (
            b"t\r\nhello\r\n6\r\n world\r\n0\r\n",
            InvalidChunkSize,
            "Invalid chunk size: b't'",
        ),
        (
            b"\r\nhello\r\n6\r\n world\r\n0\r\n\r\n",
            InvalidChunkSize,
            "Invalid chunk size: b''",
        ),
    ],
    indirect=["socket_reader"],
)
def test_from_socket_reader_with_invalid_chunk_data(
    socket_reader: SocketReader, error_type: type[Exception], error_message: str
):
    with pytest.raises(error_type, match=error_message):
        list(Chunk.from_socket_reader(socket_reader))
