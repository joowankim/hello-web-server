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
                ],
            ),
            [
                ("Date", "Thu, 04 Jul 2025 12:00:00 -0000"),
                ("Content-Type", "application/json"),
            ],
            [
                ("Date", "Thu, 04 Jul 2025 12:00:00 -0000"),
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
