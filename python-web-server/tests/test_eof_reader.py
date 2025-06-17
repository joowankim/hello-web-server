import socket
from typing import cast
from unittest import mock

import pytest

from tests import fake
from web_server.http.reader import EOFReader, SocketReader


@pytest.fixture
def eof_reader(request: pytest.FixtureRequest) -> EOFReader:
    payload: bytes = request.param
    fake_sock = fake.FakeSocket(payload)
    fake_sock.recv = mock.Mock(side_effect=iter(payload.split(b" ")))
    fake_sock = cast(socket.socket, fake_sock)
    return EOFReader(socket_reader=SocketReader(fake_sock))


@pytest.mark.parametrize(
    "eof_reader, sizes, expected_list",
    [
        (
            b"Lorem ipsum dolor sit amet",
            [5, 5, 3, 3, 100],
            [b"Lorem", b"ipsum", b"dol", b"ors", b"itamet"],
        ),
        (b"12", [0, 5], [b"", b"12"]),
    ],
    indirect=["eof_reader"],
)
def test_read(eof_reader: EOFReader, sizes: list[int], expected_list: list[bytes]):
    for size, expected in zip(sizes, expected_list):
        assert eof_reader.read(size) == expected
