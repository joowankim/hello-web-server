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
