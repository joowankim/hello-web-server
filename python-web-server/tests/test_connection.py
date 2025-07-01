import socket
from unittest import mock

import pytest

from web_server.connection import Connection


@pytest.fixture
def mock_sock() -> mock.Mock:
    return mock.Mock(spec=socket.socket)


@pytest.fixture
def connection(mock_sock: mock.Mock) -> Connection:
    return Connection(sock=mock_sock)


@pytest.mark.parametrize(
    "response_body, expected",
    [
        (b"Hello, World!", b"Hello, World!"),
        (b"", b""),
        (b"Response with some data", b"Response with some data"),
    ],
)
def test_write(
    connection: Connection, response_body: bytes, mock_sock: mock.Mock, expected: bytes
):
    connection.write(response_body)

    mock_sock.sendall.assert_called_once_with(expected)
