import socket
from typing import cast

import pytest

from tests import fake
from web_server.http.reader import LengthReader, SocketReader


@pytest.fixture(params=[3, 8192])
def socket_chunk_size(request: pytest.FixtureRequest) -> int:
    return request.param


@pytest.fixture
def socket_reader(
    socket_chunk_size: int, request: pytest.FixtureRequest
) -> SocketReader:
    payload: bytes = request.param
    fake_sock = fake.FakeSocket(payload)
    fake_sock = cast(socket.socket, fake_sock)
    return SocketReader(sock=fake_sock, max_chunk=socket_chunk_size)


@pytest.mark.parametrize(
    "socket_reader, length, expected",
    [
        (b"hello world!\r\n\r\n", 12, (b"hello world!", 12)),
        (
            b"hello world!\r\n\r\nGET /second HTTP/1.1\r\n\r\n",
            12,
            (b"hello world!", 12),
        ),
    ],
    indirect=["socket_reader"],
)
def test_parse_content(
    socket_reader: SocketReader, length: int, expected: tuple[bytes, int]
):
    reader = LengthReader.parse_content(socket_reader=socket_reader, length=length)

    assert (reader.buf.read(), reader.length) == expected


@pytest.fixture
def length_reader(
    socket_chunk_size: int, request: pytest.FixtureRequest
) -> LengthReader:
    payload: bytes = request.param
    fake_sock = fake.FakeSocket(payload)
    fake_sock = cast(socket.socket, fake_sock)
    socket_reader = SocketReader(sock=fake_sock, max_chunk=socket_chunk_size)
    return LengthReader.parse_content(
        socket_reader=socket_reader, length=len(payload.replace(b"\r\n\r\n", b""))
    )


@pytest.mark.parametrize(
    "length_reader, sizes, expected_list",
    [
        (b"Hello, World!\r\n\r\n", [5, 5, 5, 5], [b"Hello", b", Wor", b"ld!", b""]),
        (b"12\r\n\r\n", [0, 5], [b"", b"12"]),
    ],
    indirect=["length_reader"],
)
def test_read(
    length_reader: LengthReader, sizes: list[int | None], expected_list: list[bytes]
):
    for size, expected in zip(sizes, expected_list):
        assert length_reader.read(size) == expected


@pytest.mark.parametrize(
    "length_reader, size",
    [
        (b"Hello, World!\r\n\r\n", -2),
    ],
    indirect=["length_reader"],
)
def test_read_with_invalid_size(length_reader: LengthReader, size: int):
    with pytest.raises(ValueError, match="Size must be positive."):
        length_reader.read(size)
