from collections.abc import Iterable
from unittest import mock

import pytest

from web_server.http import Response, Request, RequestBody
from web_server.http.errors import InvalidHeader


@pytest.fixture
def req(request: pytest.FixtureRequest) -> Request:
    method, version, headers = request.param
    fake_request_body = mock.Mock(spec=RequestBody)
    return Request(
        method=method,
        path="/path/to/resource",
        query="query=string",
        fragment="fragment",
        version=version,
        headers=headers,
        body=fake_request_body,
        trailers=[],
    )


@pytest.mark.parametrize(
    "req, expected",
    [
        (
            (
                "GET",
                (1, 0),
                [("Content-Type", "text/plain")],
            ),
            (
                (1, 0),
                [
                    ("Date", "Thu, 03 Jul 2025 03:10:00 -0000"),
                    ("Server", "hello-web-server"),
                    ("Connection", "close"),
                ],
            ),
        ),
        (
            (
                "GET",
                (1, 1),
                [("Content-Type", "text/plain")],
            ),
            (
                (1, 1),
                [
                    ("Date", "Thu, 03 Jul 2025 03:10:00 -0000"),
                    ("Server", "hello-web-server"),
                    ("Connection", "keep-alive"),
                ],
            ),
        ),
        (
            (
                "GET",
                (2, 0),
                [("Content-Type", "application/json")],
            ),
            (
                (2, 0),
                [
                    ("Date", "Thu, 03 Jul 2025 03:10:00 -0000"),
                    ("Server", "hello-web-server"),
                    ("Connection", "keep-alive"),
                ],
            ),
        ),
        (
            (
                "GET",
                (1, 1),
                [("Connection", "close")],
            ),
            (
                (1, 1),
                [
                    ("Date", "Thu, 03 Jul 2025 03:10:00 -0000"),
                    ("Server", "hello-web-server"),
                    ("Connection", "close"),
                ],
            ),
        ),
        (
            (
                "POST",
                (1, 1),
                [
                    ("Transfer-Encoding", "chunked"),
                    ("Content-Length", "10"),
                ],
            ),
            (
                (1, 1),
                [
                    ("Date", "Thu, 03 Jul 2025 03:10:00 -0000"),
                    ("Server", "hello-web-server"),
                    ("Connection", "close"),
                ],
            ),
        ),
        (
            (
                "GET",
                (1, 1),
                [
                    ("Connection", "upgrade"),
                    ("Upgrade", "websocket"),
                ],
            ),
            (
                (1, 1),
                [
                    ("Date", "Thu, 03 Jul 2025 03:10:00 -0000"),
                    ("Server", "hello-web-server"),
                    ("Upgrade", "websocket"),
                    ("Connection", "upgrade"),
                ],
            ),
        ),
    ],
    indirect=["req"],
)
def test_draft(
    req: Request,
    expected: tuple[tuple[int, int], list[tuple[str, str]]],
):
    with mock.patch(
        "email.utils.formatdate", return_value="Thu, 03 Jul 2025 03:10:00 -0000"
    ):
        response = Response.draft(req)

        version, headers = expected
        assert response.version == version
        assert response.status is None
        assert response.headers == headers
        assert response.body is None


@pytest.fixture
def resp(request: pytest.FixtureRequest) -> Response:
    version, status, headers = request.param
    return Response(
        version=version,
        status=status,
        headers=headers,
        body=None,
    )


@pytest.mark.parametrize(
    "resp, headers, expected_headers",
    [
        (
            (
                (1, 1),
                None,
                [
                    ("Date", "Thu, 04 Jul 2025 10:00:00 -0000"),
                    ("Server", "hello-web-server"),
                    ("Connection", "keep-alive"),
                ],
            ),
            [("Content-Type", "text/plain")],
            [
                ("Date", "Thu, 04 Jul 2025 10:00:00 -0000"),
                ("Server", "hello-web-server"),
                ("Connection", "keep-alive"),
                ("Content-Type", "text/plain"),
            ],
        ),
        (
            (
                (1, 0),
                "404 Not Found",
                [
                    ("Date", "Thu, 04 Jul 2025 10:00:00 -0000"),
                    ("Server", "hello-web-server"),
                    ("Connection", "close"),
                ],
            ),
            [("Content-Type", "text/html")],
            [
                ("Date", "Thu, 04 Jul 2025 10:00:00 -0000"),
                ("Server", "hello-web-server"),
                ("Connection", "close"),
                ("Content-Type", "text/html"),
            ],
        ),
        (
            (
                (2, 0),
                "500 Internal Server Error",
                [
                    ("Date", "Thu, 03 Jul 2025 10:00:00 -0000"),
                    ("Server", "hello-web-server"),
                    ("Connection", "keep-alive"),
                    ("Content-Type", "text/plain"),
                ],
            ),
            [
                ("Content-Type", "application/json"),
            ],
            [
                ("Date", "Thu, 03 Jul 2025 10:00:00 -0000"),
                ("Server", "hello-web-server"),
                ("Connection", "keep-alive"),
                ("Content-Type", "application/json"),
            ],
        ),
    ],
    indirect=["resp"],
)
def test_extend_headers(
    resp: Response,
    headers: list[tuple[str, str]],
    expected_headers: list[tuple[str, str]],
):
    resp.extend_headers(headers)

    assert resp.headers == expected_headers


@pytest.mark.parametrize(
    "resp, headers, error_message",
    [
        (
            (
                (1, 1),
                None,
                [
                    ("Date", "Thu, 04 Jul 2025 10:00:00 -0000"),
                    ("Server", "hello-web-server"),
                    ("Connection", "keep-alive"),
                ],
            ),
            [
                ("Connection", "close"),
            ],
            "Invalid HTTP Header: 'Connection'",
        ),
        (
            (
                (1, 0),
                "404 Not Found",
                [
                    ("Date", "Thu, 04 Jul 2025 10:00:00 -0000"),
                    ("Server", "hello-web-server"),
                    ("Connection", "close"),
                ],
            ),
            [("Transfer-Encoding", "chunked")],
            "Invalid HTTP Header: 'Transfer-Encoding'",
        ),
    ],
    indirect=["resp"],
)
def test_extend_headers_with_invalid_header(
    resp: Response, headers: list[tuple[str, str]], error_message: str
):
    with pytest.raises(InvalidHeader, match=error_message):
        resp.extend_headers(headers)


@pytest.mark.parametrize(
    "resp, status, expected_status",
    [
        (
            (
                (1, 1),
                None,
                [
                    ("Date", "Thu, 04 Jul 2025 10:00:00 -0000"),
                    ("Server", "hello-web-server"),
                    ("Connection", "keep-alive"),
                ],
            ),
            "200 OK",
            "200 OK",
        ),
        (
            (
                (1, 0),
                None,
                [
                    ("Date", "Thu, 04 Jul 2025 10:00:00 -0000"),
                    ("Server", "hello-web-server"),
                    ("Connection", "close"),
                ],
            ),
            "404 Not Found",
            "404 Not Found",
        ),
    ],
    indirect=["resp"],
)
def test_set_status(resp: Response, status: str, expected_status: str):
    resp.set_status(status)

    assert resp.status == expected_status


@pytest.mark.parametrize(
    "resp",
    [
        (
            (1, 1),
            "200 OK",
            [
                ("Date", "Thu, 04 Jul 2025 10:00:00 -0000"),
                ("Server", "hello-web-server"),
                ("Connection", "keep-alive"),
            ],
        ),
    ],
    indirect=["resp"],
)
def test_set_status_with_already_set_status(resp: Response):
    with pytest.raises(AssertionError, match="Response status already set!"):
        resp.set_status("404 Not Found")


@pytest.mark.parametrize(
    "resp, response_body, expected",
    [
        (
            (
                (1, 1),
                "200 OK",
                [
                    ("Date", "Thu, 04 Jul 2025 10:00:00 -0000"),
                    ("Server", "hello-web-server"),
                    ("Connection", "keep-alive"),
                ],
            ),
            [b"Hello, ", b"World!"],
            (
                [
                    ("Date", "Thu, 04 Jul 2025 10:00:00 -0000"),
                    ("Server", "hello-web-server"),
                    ("Connection", "keep-alive"),
                    ("Content-Length", "13"),
                ],
                [b"Hello, ", b"World!"],
            ),
        ),
        (
            (
                (1, 0),
                "404 Not Found",
                [
                    ("Date", "Thu, 04 Jul 2025 10:00:00 -0000"),
                    ("Server", "hello-web-server"),
                    ("Connection", "close"),
                ],
            ),
            [b"<h1>Not Found</h1>"],
            (
                [
                    ("Date", "Thu, 04 Jul 2025 10:00:00 -0000"),
                    ("Server", "hello-web-server"),
                    ("Connection", "close"),
                    ("Content-Length", "18"),
                ],
                [b"<h1>Not Found</h1>"],
            ),
        ),
    ],
    indirect=["resp"],
)
def test_set_body(
    resp: Response,
    response_body: Iterable[bytes],
    expected: tuple[list[tuple[str, str]], list[bytes]],
):
    resp.set_body(response_body)

    assert (resp.headers, list(resp.body)) == expected


@pytest.mark.parametrize(
    "resp, response_body, error_type, error_message",
    [
        (
            (
                (1, 1),
                "200 OK",
                [
                    ("Date", "Thu, 04 Jul 2025 10:00:00 -0000"),
                    ("Server", "hello-web-server"),
                    ("Connection", "keep-alive"),
                    ("Content-Length", "11"),
                ],
            ),
            [b"Hello, ", b"World!"],
            ValueError,
            "Content-Length is wrong: expected 13, got 11",
        ),
    ],
    indirect=["resp"],
)
def test_set_body_with_invalid_body(
    resp: Response,
    response_body: Iterable[bytes],
    error_type: type[Exception],
    error_message: str,
):
    with pytest.raises(error_type, match=error_message):
        resp.set_body(response_body)


@pytest.fixture
def body_written_response(request: pytest.FixtureRequest) -> Response:
    version, status, headers, body = request.param
    return Response(
        version=version,
        status=status,
        headers=headers,
        body=body,
    )


@pytest.mark.parametrize(
    "body_written_response, expected",
    [
        (
            (
                (1, 1),
                "200 OK",
                [
                    ("Date", "Thu, 04 Jul 2025 10:00:00 -0000"),
                    ("Server", "hello-web-server"),
                    ("Connection", "keep-alive"),
                    ("Content-Length", "13"),
                ],
                [b"Hello, world!"],
            ),
            b"HTTP/1.1 200 OK\r\nDate: Thu, 04 Jul 2025 10:00:00 -0000\r\n"
            b"Server: hello-web-server\r\nConnection: keep-alive\r\n"
            b"Content-Length: 13\r\n\r\n",
        ),
        (
            (
                (1, 0),
                "404 Not Found",
                [
                    ("Date", "Thu, 04 Jul 2025 10:00:00 -0000"),
                    ("Server", "hello-web-server"),
                    ("Connection", "close"),
                    ("Content-Length", "18"),
                ],
                [b"<h1>Not Found</h1>"],
            ),
            b"HTTP/1.0 404 Not Found\r\nDate: Thu, 04 Jul 2025 10:00:00 -0000\r\n"
            b"Server: hello-web-server\r\nConnection: close\r\n"
            b"Content-Length: 18\r\n\r\n",
        ),
        (
            (
                (2, 0),
                "500 Internal Server Error",
                [
                    ("Date", "Thu, 03 Jul 2025 10:00:00 -0000"),
                    ("Server", "hello-web-server"),
                    ("Connection", "keep-alive"),
                    ("Content-Type", "application/json"),
                    ("Content-Length", "34"),
                ],
                [b"{'error': 'Internal Server Error'}"],
            ),
            b"HTTP/2.0 500 Internal Server Error\r\nDate: Thu, 03 Jul 2025 "
            b"10:00:00 -0000\r\nServer: hello-web-server\r\n"
            b"Connection: keep-alive\r\nContent-Type: application/json\r\n"
            b"Content-Length: 34\r\n\r\n",
        ),
    ],
    indirect=["body_written_response"],
)
def test_headers_data(body_written_response: Response, expected: bytes):
    assert body_written_response.headers_data() == expected


@pytest.mark.parametrize(
    "body_written_response, error_message",
    [
        (
            (
                (1, 1),
                None,
                [
                    ("Date", "Thu, 04 Jul 2025 10:00:00 -0000"),
                    ("Server", "hello-web-server"),
                    ("Connection", "keep-alive"),
                ],
                [b"Hello, world!"],
            ),
            "Response status not set!",
        ),
        (
            (
                (1, 0),
                "404 Not Found",
                [
                    ("Date", "Thu, 04 Jul 2025 10:00:00 -0000"),
                    ("Server", "hello-web-server"),
                    ("Connection", "close"),
                ],
                None,
            ),
            "Response body not set!",
        ),
    ],
    indirect=["body_written_response"],
)
def test_headers_data_with_invalid_response(
    body_written_response: Response,
    error_message: str,
):
    with pytest.raises(AssertionError, match=error_message):
        body_written_response.headers_data()
