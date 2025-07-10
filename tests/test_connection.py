import socket
from unittest import mock

import pytest

from tests.conftest import MockCallList
from web_server.connection import Connection
from web_server.types import ExcInfo


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
    "protocol_version, status, headers, exc_info, response_body, expected",
    [
        (
            (1, 1),
            "200 OK",
            [("Content-Type", "text/plain")],
            None,
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
            None,
            b"<h1>Not Found</h1>",
            [
                mock.call(b"HTTP/1.0 404 Not Found\r\nContent-Type: text/html\r\n\r\n"),
                mock.call(b"<h1>Not Found</h1>"),
            ],
        ),
        (
            (2, 0),
            "500 Internal Server Error",
            [("Content-Type", "application/json")],
            None,
            b'{"error": "Internal Server Error"}',
            [
                mock.call(
                    b"HTTP/2.0 500 Internal Server Error\r\nContent-Type: application/json\r\n\r\n"
                ),
                mock.call(b'{"error": "Internal Server Error"}'),
            ],
        ),
        (
            (1, 1),
            "400 Bad Request",
            [("Content-Type", "text/plain")],
            (ValueError, ValueError("Test error"), None),
            b"Hello, World!",
            [
                mock.call(
                    b"HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\n"
                ),
                mock.call(b"Hello, World!"),
            ],
        ),
    ],
)
def test_start_response(
    connection: Connection,
    protocol_version: tuple[int, int],
    status: str,
    headers: list[tuple[str, str]],
    exc_info: ExcInfo | None,
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


@pytest.mark.parametrize(
    "response_params, response_body, expected",
    [
        (
            [
                ((1, 1), "200 OK", [("Content-Type", "text/plain")], None),
                (
                    (1, 1),
                    "404 Not Found",
                    [("Content-Type", "text/html")],
                    (ValueError, ValueError("Test error"), None),
                ),
            ],
            b"<h1>Not Found</h1>",
            [
                mock.call(b"HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n"),
                mock.call(b"<h1>Not Found</h1>"),
            ],
        ),
        (
            [
                (
                    (1, 1),
                    "400 Bad Request",
                    [("Content-Type", "text/plain")],
                    (ValueError, ValueError("Test error"), None),
                ),
                (
                    (1, 1),
                    "500 Internal Server Error",
                    [("Content-Type", "application/json")],
                    (TypeError, TypeError("Test error"), None),
                ),
            ],
            b"{'error': 'Internal Server Error'}",
            [
                mock.call(
                    b"HTTP/1.1 500 Internal Server Error\r\nContent-Type: application/json\r\n\r\n"
                ),
                mock.call(b"{'error': 'Internal Server Error'}"),
            ],
        ),
    ],
)
def test_start_response_duplication_called(
    connection: Connection,
    response_params: tuple[tuple[int, int], str, list[tuple[str, str]], ExcInfo | None],
    response_body: bytes,
    mock_sock: mock.Mock,
    expected: MockCallList,
):
    write = lambda *args: None  # noqa: E731, dummy write function to avoid TypeError

    for protocol_version, status, headers, exc_info in response_params:
        write = connection.start_response(
            protocol_version=protocol_version,
            status=status,
            headers=headers,
            exc_info=exc_info,
        )
        mock_sock.sendall.assert_not_called()
        mock_sock.sendall.assert_has_calls(b"")
    write(response_body)
    mock_sock.sendall.assert_has_calls(expected)


@pytest.mark.parametrize(
    "response_params, error_type, error_message",
    [
        (
            [
                ((1, 1), "200 OK", [("Content-Type", "text/plain")], None),
                (
                    (1, 1),
                    "400 Bad Request",
                    [("Content-Type", "text/plain")],
                    (ValueError, ValueError("Test error"), None),
                ),
            ],
            ValueError,
            "Test error",
        ),
        (
            [
                (
                    (1, 1),
                    "400 Bad Request",
                    [("Content-Type", "text/plain")],
                    (ValueError, ValueError("Test error"), None),
                ),
                (
                    (1, 1),
                    "400 Bad Request",
                    [("Content-Type", "text/plain")],
                    (ValueError, ValueError("Test error2"), None),
                ),
            ],
            ValueError,
            "Test error2",
        ),
        (
            [
                (
                    (1, 1),
                    "400 Bad Request",
                    [("Content-Type", "text/plain")],
                    (ValueError, ValueError("Test error"), None),
                ),
                ((1, 1), "200 OK", [("Content-Type", "text/plain")], None),
            ],
            AssertionError,
            "Response headers already set!",
        ),
        (
            [
                (
                    (1, 1),
                    "400 Bad Request",
                    [("Content-Type", "text/plain")],
                    (ValueError, ValueError("Test error"), None),
                ),
                ((1, 1), "400 Bad Request", [("Content-Type", "text/plain")], None),
            ],
            AssertionError,
            "Response headers already set!",
        ),
        (
            [
                ((1, 1), "200 OK", [("Content-Type", "text/plain")], None),
                ((1, 1), "200 OK", [("Content-Type", "text/plain")], None),
            ],
            AssertionError,
            "Response headers already set!",
        ),
    ],
)
def test_start_response_raise_error(
    connection: Connection,
    response_params: tuple[tuple[int, int], str, list[tuple[str, str]], ExcInfo | None],
    error_type: type[Exception],
    error_message: str,
):
    with pytest.raises(error_type, match=error_message):
        for protocol_version, status, headers, exc_info in response_params:
            write = connection.start_response(
                protocol_version=protocol_version,
                status=status,
                headers=headers,
                exc_info=exc_info,
            )
            write(b"")
