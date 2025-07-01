import socket
from unittest import mock

import pytest

from tests.conftest import MockCallList
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


@pytest.mark.parametrize(
    "protocol_version, status, headers, response_body, expected",
    [
        (
            (1, 1),
            "200 OK",
            [("Content-Type", "text/plain")],
            b"Hello, World!",
            [
                mock.call(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n"),
                mock.call(b"Hello, World!"),
            ],
        ),
        (
            (1, 0),
            "404 Not Found",
            [("Content-Type", "text/html")],
            b"<h1>Not Found</h1>",
            [
                mock.call(b"HTTP/1.0 404 Not Found\r\nContent-Type: text/html\r\n\r\n"),
                mock.call(b"<h1>Not Found</h1>"),
            ],
        ),
    ],
)
def test_start_response(
    connection: Connection,
    protocol_version: tuple[int, int],
    status: str,
    headers: list[tuple[str, str]],
    response_body: bytes,
    mock_sock: mock.Mock,
    expected: MockCallList,
):
    write = connection.start_response(
        protocol_version=protocol_version,
        status=status,
        headers=headers,
    )
    mock_sock.sendall.assert_not_called()
    write(response_body)
    mock_sock.sendall.assert_has_calls(expected)
