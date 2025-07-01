import socket
from typing import cast
from unittest import mock

import pytest

from tests import support, fake
from web_server.config import Config
from web_server.connection import Connection
from web_server.http import Request, RequestBody
from web_server.http.reader import SocketReader
from web_server.wsgi import WSGIEnviron


@pytest.fixture
def request_body(request: pytest.FixtureRequest) -> RequestBody:
    payload: bytes = b"hello"
    fake_sock = fake.FakeSocket(payload)
    fake_sock = cast(socket.socket, fake_sock)
    return RequestBody.create(
        protocol_version=(1, 1),
        headers=[("Content-Length", str(len(payload)))],
        socket_reader=SocketReader(sock=fake_sock, max_chunk=8190),
    )


@pytest.fixture
def req(request_body: RequestBody) -> Request:
    return Request(
        method="GET",
        path="/path/to/resource",
        query="query=string",
        fragment="fragment",
        version=(1, 1),
        headers=[("Host", "localhost:8000")],
        body=request_body,
        trailers=[],
    )


@pytest.fixture
def connection() -> Connection:
    return Connection(sock=mock.Mock(spec=socket.socket))


@pytest.fixture
def wsgi_environ(req: Request) -> WSGIEnviron:
    cfg = Config.default()
    server = ("localhost", "8000")
    return WSGIEnviron.build(cfg=cfg, server=server, request=req)


def test_hello_wsgiref(wsgi_environ: WSGIEnviron, connection: Connection):
    def start_response(status, headers, exc_info=None):
        return connection.start_response(
            protocol_version=(1, 1), status=status, headers=headers, exc_info=exc_info
        )

    support.app(wsgi_environ.dict(), start_response)
