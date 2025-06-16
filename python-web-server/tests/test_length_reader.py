import socket
from typing import cast

import pytest

from tests import fake
from web_server.http.reader import LengthReader, SocketReader


@pytest.fixture
def length_reader(request: pytest.FixtureRequest) -> LengthReader:
    payload: bytes = request.param
    fake_sock = fake.FakeSocket(payload)
    fake_sock = cast(socket.socket, fake_sock)
    return LengthReader(
        socket_reader=SocketReader(sock=fake_sock, max_chunk=8192),
        length=len(payload),
    )


@pytest.mark.parametrize(
    "length_reader, sizes, expected_list",
    [
        (b"Hello, World!", [5, 5, 5, 5], [b"Hello", b", Wor", b"ld!", b""]),
        (b"12", [0, 5], [b"", b"12"]),
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
        (b"Hello, World!", -2),
    ],
    indirect=["length_reader"],
)
def test_read_with_invalid_size(length_reader: LengthReader, size: int):
    with pytest.raises(ValueError, match="Size must be positive."):
        length_reader.read(size)
