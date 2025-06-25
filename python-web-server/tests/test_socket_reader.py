import socket
from collections.abc import Callable
from typing import cast, TypeAlias

import pytest

from tests import fake
from web_server.http.reader import SocketReader


SocketReaderFactory: TypeAlias = Callable[[bytes, int], SocketReader]


@pytest.fixture
def socket_reader_factory() -> SocketReaderFactory:
    def factory(data: bytes, max_chunk: int) -> SocketReader:
        fake_sock = fake.FakeSocket(data)
        fake_sock = cast(socket.socket, fake_sock)
        return SocketReader(sock=fake_sock, max_chunk=max_chunk)

    return factory


def test_chunk(socket_reader_factory: SocketReaderFactory):
    socket_reader = socket_reader_factory(b"Lorem ipsum dolor", 5)

    assert socket_reader.chunk() == b"Lorem"
    assert socket_reader.chunk() == b" ipsu"
    assert socket_reader.chunk() == b"m dol"
    assert socket_reader.chunk() == b"or"
    assert socket_reader.chunk() == b""


def test_reader_read_when_size_is_none(socket_reader_factory: SocketReaderFactory):
    socket_reader = socket_reader_factory(b"qwerty123456", 5)

    assert socket_reader.read(size=None) == b"qwert"
    assert socket_reader.read(size=None) == b"y1234"
    assert socket_reader.read(size=None) == b"56"
    assert socket_reader.read(size=None) == b""


def test_reader_read_zero_size(socket_reader_factory: SocketReaderFactory):
    socket_reader = socket_reader_factory(b"qwertyasdfgh", 8192)

    assert socket_reader.read(size=0) == b""


def test_reader_read_with_nonzero_size(socket_reader_factory: SocketReaderFactory):
    socket_reader = socket_reader_factory(b"qwertyasdfghzxcvbn123456", 8192)

    assert socket_reader.read(size=5) == b"qwert"
    assert socket_reader.read(size=5) == b"yasdf"
    assert socket_reader.read(size=5) == b"ghzxc"
    assert socket_reader.read(size=5) == b"vbn12"
    assert socket_reader.read(size=5) == b"3456"
    assert socket_reader.read(size=5) == b""


def test_unread(socket_reader_factory: SocketReaderFactory):
    socket_reader = socket_reader_factory(b"qwertyasdfgh", 8192)
    socket_reader.read(size=5)

    socket_reader.unread(size=5)

    assert socket_reader.read(size=None) == b"qwertyasdfgh"


@pytest.mark.parametrize(
    "size, error_type, error_message",
    [
        (-2, ValueError, "Size must be positive."),
        ("foobar", TypeError, "size must be an integer type"),
        (3.14, TypeError, "size must be an integer type"),
        ([], TypeError, "size must be an integer type"),
    ],
)
def test_unread_with_invalid_size(
    socket_reader_factory: SocketReaderFactory,
    size: int | str | float | list,
    error_type: type[Exception],
    error_message: str,
):
    socket_reader = socket_reader_factory(b"qwerty", 8192)

    with pytest.raises(error_type, match=error_message):
        socket_reader.unread(size=size)


@pytest.fixture
def socket_reader(
    socket_reader_factory: SocketReaderFactory, request: pytest.FixtureRequest
) -> SocketReader:
    payload, max_chunk = request.param
    return socket_reader_factory(payload, max_chunk)


@pytest.mark.parametrize(
    "socket_reader, args, expected_list",
    [
        (
            (b"Hello, World!\r\n\r\n", 8192),
            [(b"\r\n\r\n", None), (b"\r\n\r\n", None), (b"\r\n\r\n", None)],
            [b"Hello, World!\r\n\r\n", b"", b""],
        ),
        (
            (b"Hello, World!", 8192),
            [(b"\r\n\r\n", None)],
            [b"Hello, World!"],
        ),
        ((b"", 8192), [(b"\r\n\r\n", None)], [b""]),
        (
            (b"Hello, \r\nWorld!\r\n\r\n", 8192),
            [(b"\r\n", None), (b"\r\n", None), (b"\r\n", None)],
            [b"Hello, \r\n", b"World!\r\n", b"\r\n"],
        ),
        (
            (b"Hello, \r\nWorld!\r\n\r\n", 3),
            [(b"\r\n", None), (b"\r\n", None), (b"\r\n", None)],
            [b"Hello, \r\n", b"World!\r\n", b"\r\n"],
        ),
        (
            (b"Hello, World!\r\n\r\n", 5),
            [(b"\r\n\r\n", 5), (b"\r\n\r\n", None), (b"\r\n\r\n", None)],
            [b"Hello", b", World!\r\n\r\n", b""],
        ),
    ],
    indirect=["socket_reader"],
)
def test_read_until(
    socket_reader: SocketReader,
    args: list[tuple[bytes, int | None]],
    expected_list: list[bytes],
):
    for (target, limit), expected in zip(args, expected_list):
        assert socket_reader.read_until(target=target, limit=limit) == expected
