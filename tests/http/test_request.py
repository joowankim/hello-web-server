from unittest import mock

import pytest

from web_server.http import Request, RequestBody


@pytest.fixture
def req(request: pytest.FixtureRequest) -> Request:
    headers: list[tuple[str, str]] = request.param
    fake_request_body = mock.Mock(spec=RequestBody)
    return Request(
        method="GET",
        path="/path/to/resource",
        query="query=string",
        fragment="fragment",
        version=(1, 1),
        headers=headers,
        body=fake_request_body,
        trailers=[],
    )


@pytest.mark.parametrize(
    "req, expected",
    [
        (
            [("Connection", "close")],
            True,
        ),
        (
            [("Connection", "keep-alive")],
            False,
        ),
        (
            [("Content-Type", "text/plain")],
            False,
        ),
        (
            [("Connection", "Keep-Alive")],
            False,
        ),
        (
            [("Connection", "close"), ("Content-Type", "text/plain")],
            True,
        ),
        (
            [("Content-Type", "text/plain"), ("Connection", "close")],
            True,
        ),
        (
            [("Content-Type", "text/plain"), ("Connection", "keep-alive")],
            False,
        ),
        (
            [("Connection", "upgrade")],
            False,
        ),
    ],
    indirect=["req"],
)
def test_has_connection_close_header(req: Request, expected: bool):
    assert req.has_connection_close_header is expected


@pytest.mark.parametrize(
    "req, expected",
    [
        (
            [("Upgrade", "websocket")],
            None,
        ),
        (
            [("Connection", "upgrade")],
            None,
        ),
        (
            [("Content-Type", "text/plain")],
            None,
        ),
        (
            [("Upgrade", "WebSocket")],
            None,
        ),
        (
            [("Upgrade", "websocket"), ("Connection", "upgrade")],
            ("Upgrade", "websocket"),
        ),
        (
            [("Connection", "upgrade"), ("Upgrade", "websocket")],
            ("Upgrade", "websocket"),
        ),
        (
            [("Content-Type", "text/plain"), ("Connection", "upgrade")],
            None,
        ),
    ],
    indirect=["req"],
)
def test_upgrade_header(req: Request, expected: tuple[str, str] | None):
    assert req.upgrade_header == expected


@pytest.mark.parametrize(
    "req, expected",
    [
        (
            [("Transfer-Encoding", "chunked"), ("Content-Length", "123")],
            True,
        ),
        (
            [("Transfer-Encoding", "chunked")],
            False,
        ),
        (
            [("Content-Length", "123")],
            False,
        ),
        (
            [("Content-Type", "text/plain")],
            False,
        ),
        (
            [("Transfer-Encoding", "chunked"), ("Content-Type", "text/plain")],
            False,
        ),
        (
            [("Content-Type", "text/plain"), ("Transfer-Encoding", "chunked")],
            False,
        ),
        (
            [("Content-Type", "text/plain"), ("Content-Length", "123")],
            False,
        ),
    ],
    indirect=["req"],
)
def test_has_transfer_encoding_and_content_length_headers(req: Request, expected: bool):
    assert req.has_transfer_encoding_and_content_length_headers is expected
