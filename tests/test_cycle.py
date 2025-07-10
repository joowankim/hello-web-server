import socket
from collections.abc import Callable, Iterable
from unittest import mock

import pytest

from tests import support
from tests.conftest import MockCallList
from web_server.config import Config
from web_server.connection import Connection
from web_server.cycle import Cycle
from web_server.http import Request, RequestBody, Response
from web_server.wsgi import WSGIEnviron
from web_server.types import ExcInfo


@pytest.fixture
def mock_sock() -> mock.Mock:
    return mock.Mock(spec=socket.socket)


@pytest.fixture
def request_factory() -> Callable[[tuple[int, int]], Request]:
    fake_request_body = mock.Mock(spec=RequestBody)

    def _factory(protocol_version: tuple[int, int]) -> Request:
        return Request(
            method="GET",
            path="/path/to/resource",
            query="query=string",
            fragment="fragment",
            version=protocol_version,
            headers=[],
            body=fake_request_body,
            trailers=[],
        )

    return _factory


@pytest.fixture
def cycle(
    mock_sock: mock.Mock,
    request_factory: Callable[[tuple[int, int]], Request],
    request: pytest.FixtureRequest,
) -> Cycle:
    protocol_version: tuple[int, int] = request.param
    req = request_factory(protocol_version)
    conn = Connection(sock=mock_sock)
    environ = WSGIEnviron.build(
        cfg=Config.default(), server=("localhost", "8000"), request=req
    )
    return Cycle(
        conn=conn,
        environ=environ,
        app=support.app,
    )


@pytest.mark.parametrize(
    "cycle, response_params, response_body, expected",
    [
        (
            (1, 1),
            (
                "200 OK",
                [("Content-Type", "text/plain")],
                None,
            ),
            b"Hello, World!",
            [
                mock.call(
                    b"HTTP/1.1 200 OK\r\n"
                    b"Date: Fri, 04 Jul 2025 10:00:00 GMT\r\n"
                    b"Server: hello-web-server\r\n"
                    b"Connection: close\r\n"
                    b"Content-Type: text/plain\r\n"
                    b"Content-Length: 13\r\n"
                    b"\r\n"
                ),
                mock.call(b"Hello, World!"),
            ],
        ),
        (
            (1, 0),
            (
                "404 Not Found",
                [("Content-Type", "text/html")],
                None,
            ),
            b"<h1>Not Found</h1>",
            [
                mock.call(
                    b"HTTP/1.0 404 Not Found\r\n"
                    b"Date: Fri, 04 Jul 2025 10:00:00 GMT\r\n"
                    b"Server: hello-web-server\r\n"
                    b"Connection: close\r\n"
                    b"Content-Type: text/html\r\n"
                    b"Content-Length: 18\r\n"
                    b"\r\n"
                ),
                mock.call(b"<h1>Not Found</h1>"),
            ],
        ),
        (
            (2, 0),
            (
                "500 Internal Server Error",
                [("Content-Type", "application/json")],
                None,
            ),
            b'{"error": "Internal Server Error"}',
            [
                mock.call(
                    b"HTTP/2.0 500 Internal Server Error\r\n"
                    b"Date: Fri, 04 Jul 2025 10:00:00 GMT\r\n"
                    b"Server: hello-web-server\r\n"
                    b"Connection: close\r\n"
                    b"Content-Type: application/json\r\n"
                    b"Content-Length: 34\r\n"
                    b"\r\n"
                ),
                mock.call(b'{"error": "Internal Server Error"}'),
            ],
        ),
        (
            (1, 1),
            (
                "400 Bad Request",
                [("Content-Type", "text/plain")],
                (ValueError, ValueError("Test error"), None),
            ),
            b"Hello, World!",
            [
                mock.call(
                    b"HTTP/1.1 400 Bad Request\r\n"
                    b"Date: Fri, 04 Jul 2025 10:00:00 GMT\r\n"
                    b"Server: hello-web-server\r\n"
                    b"Connection: close\r\n"
                    b"Content-Type: text/plain\r\n"
                    b"Content-Length: 13\r\n"
                    b"\r\n"
                ),
                mock.call(b"Hello, World!"),
            ],
        ),
    ],
    indirect=["cycle"],
)
def test_start_response(
    cycle: Cycle,
    response_params: tuple[str, list[tuple[str, str]], ExcInfo | None],
    response_body: bytes,
    mock_sock: mock.Mock,
    expected: MockCallList,
):
    with mock.patch(
        "email.utils.formatdate", return_value="Fri, 04 Jul 2025 10:00:00 GMT"
    ):
        write = cycle.start_response(*response_params)
        mock_sock.sendall.assert_not_called()
        write(response_body)
        mock_sock.sendall.assert_has_calls(expected)


@pytest.mark.parametrize(
    "cycle, response_params, response_body, expected",
    [
        (
            (1, 1),
            [
                ("200 OK", [("Content-Type", "text/plain")], None),
                (
                    "404 Not Found",
                    [("Content-Type", "text/html")],
                    (ValueError, ValueError("Test error"), None),
                ),
            ],
            b"<h1>Not Found</h1>",
            [
                mock.call(
                    b"HTTP/1.1 404 Not Found\r\n"
                    b"Date: Fri, 04 Jul 2025 10:00:00 GMT\r\n"
                    b"Server: hello-web-server\r\n"
                    b"Connection: close\r\n"
                    b"Content-Type: text/html\r\n"
                    b"Content-Length: 18\r\n"
                    b"\r\n"
                ),
                mock.call(b"<h1>Not Found</h1>"),
            ],
        ),
        (
            (1, 1),
            [
                (
                    "400 Bad Request",
                    [("Content-Type", "text/plain")],
                    (ValueError, ValueError("Test error"), None),
                ),
                (
                    "500 Internal Server Error",
                    [("Content-Type", "application/json")],
                    (TypeError, TypeError("Test error"), None),
                ),
            ],
            b"{'error': 'Internal Server Error'}",
            [
                mock.call(
                    b"HTTP/1.1 500 Internal Server Error\r\n"
                    b"Date: Fri, 04 Jul 2025 10:00:00 GMT\r\n"
                    b"Server: hello-web-server\r\n"
                    b"Connection: close\r\n"
                    b"Content-Type: application/json\r\n"
                    b"Content-Length: 34\r\n"
                    b"\r\n"
                ),
                mock.call(b"{'error': 'Internal Server Error'}"),
            ],
        ),
    ],
    indirect=["cycle"],
)
def test_start_response_duplication_called(
    cycle: Cycle,
    response_params: tuple[tuple[int, int], str, list[tuple[str, str]], ExcInfo | None],
    response_body: bytes,
    mock_sock: mock.Mock,
    expected: MockCallList,
):
    write = lambda *args: None  # noqa: E731, dummy write function to avoid TypeError

    with mock.patch(
        "email.utils.formatdate", return_value="Fri, 04 Jul 2025 10:00:00 GMT"
    ):
        for status, headers, exc_info in response_params:
            write = cycle.start_response(
                status=status,
                headers=headers,
                exc_info=exc_info,
            )
            mock_sock.sendall.assert_not_called()
            mock_sock.sendall.assert_has_calls(b"")
        write(response_body)
        mock_sock.sendall.assert_has_calls(expected)


@pytest.mark.parametrize(
    "cycle, response_params, error_type, error_message",
    [
        (
            (1, 1),
            [
                ("200 OK", [("Content-Type", "text/plain")], None),
                (
                    "400 Bad Request",
                    [("Content-Type", "text/plain")],
                    (ValueError, ValueError("Test error"), None),
                ),
            ],
            ValueError,
            "Test error",
        ),
        (
            (1, 1),
            [
                (
                    "400 Bad Request",
                    [("Content-Type", "text/plain")],
                    (ValueError, ValueError("Test error"), None),
                ),
                (
                    "400 Bad Request",
                    [("Content-Type", "text/plain")],
                    (ValueError, ValueError("Test error2"), None),
                ),
            ],
            ValueError,
            "Test error2",
        ),
        (
            (1, 1),
            [
                (
                    "400 Bad Request",
                    [("Content-Type", "text/plain")],
                    (ValueError, ValueError("Test error"), None),
                ),
                ("200 OK", [("Content-Type", "text/plain")], None),
            ],
            AssertionError,
            "Response headers already set!",
        ),
        (
            (1, 1),
            [
                (
                    "400 Bad Request",
                    [("Content-Type", "text/plain")],
                    (ValueError, ValueError("Test error"), None),
                ),
                ("400 Bad Request", [("Content-Type", "text/plain")], None),
            ],
            AssertionError,
            "Response headers already set!",
        ),
        (
            (1, 1),
            [
                ("200 OK", [("Content-Type", "text/plain")], None),
                ("200 OK", [("Content-Type", "text/plain")], None),
            ],
            AssertionError,
            "Response headers already set!",
        ),
    ],
    indirect=["cycle"],
)
def test_start_response_raise_error(
    cycle: Cycle,
    response_params: tuple[tuple[int, int], str, list[tuple[str, str]], ExcInfo | None],
    error_type: type[Exception],
    error_message: str,
):
    with pytest.raises(error_type, match=error_message):
        for status, headers, exc_info in response_params:
            write = cycle.start_response(
                status=status,
                headers=headers,
                exc_info=exc_info,
            )
            write(b"")


@pytest.fixture
def response_ready_cycle(
    mock_sock: mock.Mock,
    request_factory: Callable[[tuple[int, int]], Request],
    request: pytest.FixtureRequest,
) -> Cycle:
    protocol_version, status, headers, resp_body = request.param
    req = request_factory(protocol_version)
    conn = Connection(sock=mock_sock)
    environ = WSGIEnviron.build(
        cfg=Config.default(), server=("localhost", "8000"), request=req
    )
    cycle = Cycle(
        conn=conn,
        environ=environ,
        app=support.app,
    )
    cycle.resp = Response(
        version=protocol_version,
        status=status,
        headers=headers,
        body=resp_body,
    )
    return cycle


@pytest.mark.parametrize(
    "response_ready_cycle, response_body, expected",
    [
        (
            (
                (1, 1),
                "200 OK",
                [
                    ("Date", "Fri, 07 Jul 2025 10:00:00 GMT"),
                    ("Server", "hello-web-server"),
                    ("Connection", "keep-alive"),
                    ("Content-Type", "text/plain"),
                    ("Content-Length", "13"),
                ],
                [b"Hello, World!"],
            ),
            [b"Hello, World!"],
            [
                mock.call(
                    b"HTTP/1.1 200 OK\r\n"
                    b"Date: Fri, 07 Jul 2025 10:00:00 GMT\r\n"
                    b"Server: hello-web-server\r\n"
                    b"Connection: keep-alive\r\n"
                    b"Content-Type: text/plain\r\n"
                    b"Content-Length: 13\r\n"
                    b"\r\n"
                ),
                mock.call(b"Hello, World!"),
            ],
        ),
        (
            (
                (1, 1),
                "200 OK",
                [
                    ("Date", "Fri, 07 Jul 2025 10:00:00 GMT"),
                    ("Server", "hello-web-server"),
                    ("Connection", "keep-alive"),
                    ("Content-Type", "text/plain"),
                    ("Transfer-Encoding", "chunked"),
                ],
                [b"Hello, ", b"World!", b""],
            ),
            [b"Hello, ", b"World!", b""],
            [
                mock.call(
                    b"HTTP/1.1 200 OK\r\n"
                    b"Date: Fri, 07 Jul 2025 10:00:00 GMT\r\n"
                    b"Server: hello-web-server\r\n"
                    b"Connection: keep-alive\r\n"
                    b"Content-Type: text/plain\r\n"
                    b"Transfer-Encoding: chunked\r\n"
                    b"\r\n"
                ),
                mock.call(b"7\r\nHello, \r\n"),
                mock.call(b"6\r\nWorld!\r\n"),
                mock.call(b"0\r\n\r\n"),
            ],
        ),
    ],
    indirect=["response_ready_cycle"],
)
def test_write(
    response_ready_cycle: Cycle,
    response_body: Iterable[bytes],
    mock_sock: mock.Mock,
    expected: MockCallList,
):
    for data in response_body:
        response_ready_cycle.write(data)

    mock_sock.sendall.assert_has_calls(expected)
