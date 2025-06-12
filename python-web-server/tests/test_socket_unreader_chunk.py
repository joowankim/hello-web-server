import io
import socket
from typing import cast

import pytest

from tests import fake
from web_server.http.reader import SocketUnreader


@pytest.fixture
def socket_unreader() -> SocketUnreader:
    fake_sock = fake.FakeSocket(io.BytesIO(b"Lorem ipsum dolor"))
    fake_sock = cast(socket.socket, fake_sock)
    return SocketUnreader(sock=fake_sock, max_chunk=5)


def test_chunk(socket_unreader: SocketUnreader):
    assert socket_unreader.chunk() == b"Lorem"
    assert socket_unreader.chunk() == b" ipsu"
    assert socket_unreader.chunk() == b"m dol"
    assert socket_unreader.chunk() == b"or"
    assert socket_unreader.chunk() == b""
