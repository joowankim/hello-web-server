import io
import socket
from typing import cast

import pytest

from tests import fake
from web_server.http.errors import InvalidChunkSize
from web_server.http.reader import Chunk, SocketReader


@pytest.fixture(params=[3, 8192])
def socket_chunk_size(request: pytest.FixtureRequest) -> int:
    return request.param


@pytest.fixture
def socket_reader(
    socket_chunk_size: int, request: pytest.FixtureRequest
) -> SocketReader:
    payload = request.param
    fake_sock = fake.FakeSocket(payload)
    fake_sock = cast(socket.socket, fake_sock)
    return SocketReader(sock=fake_sock, max_chunk=socket_chunk_size)


@pytest.mark.parametrize(
    "socket_reader, expected, expected_rest",
    [
        (
            b"5\r\nhello\r\n6\r\n world\r\n0\r\n\r\n",
            [(b"hello", 5), (b" world", 6), (b"", 0)],
            b"",
        ),
        (
            (
                b"5\r\nhello\r\n6\r\n world\r\n0\r\n"
                b"Vary: *\r\nContent-Type: text/plain\r\n\r\n"
            ),
            [
                (b"hello", 5),
                (b" world", 6),
                (b"Vary: *\r\nContent-Type: text/plain\r\n", 0),
            ],
            b"",
        ),
        (
            (
                b"5; some; parameters=stuff\r\nhello\r\n"
                b"6; blahblah; blah\r\n world\r\n"
                b"0\r\n\r\n"
            ),
            [(b"hello", 5), (b" world", 6), (b"", 0)],
            b"",
        ),
        (
            b"5\r\nhello\r\n6\r\n world\r\n000\r\n\r\nGET /second HTTP/1.1\r\n\r\n",
            [(b"hello", 5), (b" world", 6), (b"", 0)],
            b"GET /second HTTP/1.1\r\n\r\n",
        ),
        (
            b"b\r\nhello world\r\n0\r\n\r\n",
            [(b"hello world", 11), (b"", 0)],
            b"",
        ),
        (
            b"5\r\nhello\r\n000\r\n",
            [(b"hello", 5), (b"", 0)],
            b"",
        ),
    ],
    indirect=["socket_reader"],
    ids=(
        "basic_chunks",
        "chunks_with_trailers",
        "chunks_with_chunk_extensions",
        "chunks_with_next_request",
        "single_chunk_with_hexadecimal_size",
        "chunk_end_without_duplicated_crlf",
    ),
)
def test_from_socket_reader(
    socket_reader: SocketReader, expected: list[tuple[bytes, int]], expected_rest: bytes
):
    chunks = Chunk.from_socket_reader(socket_reader)

    for chunk, (data, size) in zip(chunks, expected):
        assert chunk.data.read() == data
        assert chunk.size == size
    assert socket_reader.read() == expected_rest[: socket_reader.max_chunk]


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


def test_is_last():
    chunk = Chunk(data=io.BytesIO(b"test"), size=4)
    assert chunk.is_last is False

    last_chunk = Chunk(data=io.BytesIO(b""), size=0)
    assert last_chunk.is_last is True


@pytest.mark.parametrize(
    "chunk, expected",
    [
        (Chunk(data=io.BytesIO(b"hello"), size=5), []),
        (
            Chunk(
                data=io.BytesIO(b"Vary: *\r\nContent-Type: text/plain\r\n"),
                size=0,
            ),
            [("VARY", "*"), ("CONTENT-TYPE", "text/plain")],
        ),
        (
            Chunk(
                data=io.BytesIO(b"Trailer-Name: value\r\nAnother-Header: value2\r\n"),
                size=0,
            ),
            [("TRAILER-NAME", "value"), ("ANOTHER-HEADER", "value2")],
        ),
        (
            Chunk(data=io.BytesIO(b""), size=0),
            [],
        ),
    ],
)
def test_trailers(chunk: Chunk, expected: list[tuple[str, str]]):
    assert chunk.trailers == expected
