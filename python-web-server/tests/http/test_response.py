from unittest import mock

import pytest

from web_server.http import Response, Request, RequestBody


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
