from typing import Any
from unittest import mock

import pytest

from web_server.http import RequestBody
from web_server.wsgi import WSGIEnviron, WSGIErrorStream


@pytest.fixture
def fake_request_body() -> RequestBody:
    return mock.Mock(spec=RequestBody)


@pytest.fixture
def wsgi_environ(
    fake_request_body: RequestBody, request: pytest.FixtureRequest
) -> WSGIEnviron:
    environ_params: dict[str, Any] = request.param
    return WSGIEnviron(
        request_method="GET",
        script_name=environ_params["script_name"],
        path_info=environ_params["path_info"],
        query_string="query=string",
        content_type=environ_params["content_type"],
        content_length=environ_params["content_length"],
        server_name="localhost",
        server_port="8000",
        server_protocol="HTTP/1.1",
        http_headers=environ_params["http_headers"],
        wsgi_version=(1, 1),
        wsgi_url_scheme="http",
        wsgi_input=fake_request_body,
        wsgi_errors=mock.Mock(spec=WSGIErrorStream),
        wsgi_multithread=False,
        wsgi_multiprocess=False,
        wsgi_run_once=False,
    )


@pytest.mark.parametrize(
    "wsgi_environ, expected",
    [
        (
            dict(
                script_name="/app",
                path_info="/path/to/resource",
                content_type="text/plain",
                content_length="123",
                http_headers=[
                    ("HTTP_HOST", "localhost:8000"),
                    ("HTTP_USER_AGENT", "TestClient/1.0"),
                    ("HTTP_ACCEPT", "*/*"),
                ],
            ),
            (
                "/app/path/to/resource",
                [
                    ("Host", "localhost:8000"),
                    ("User-Agent", "TestClient/1.0"),
                    ("Accept", "*/*"),
                    ("Content-Type", "text/plain"),
                    ("Content-Length", "123"),
                ],
            ),
        )
    ],
    indirect=["wsgi_environ"],
)
def test_http_request(
    wsgi_environ: WSGIEnviron,
    fake_request_body: RequestBody,
    expected: tuple[str, list[tuple[str, str]]],
):
    req = wsgi_environ.http_request

    path, headers = expected
    assert req.method == "GET"
    assert req.path == path
    assert req.query == "query=string"
    assert req.fragment == ""
    assert req.version == (1, 1)
    assert req.headers == headers
    assert req.body == fake_request_body
    assert req.trailers == []
