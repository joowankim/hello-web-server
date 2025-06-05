from collections.abc import Generator

import httpx
import pytest

from web_server.main import WebServer


@pytest.fixture
def start_server() -> Generator[None, None, None]:
    web_server = WebServer()
    web_server.start()
    yield
    web_server.stop()


@pytest.fixture
def expected() -> bytes:
    return b"Hello, World!"


@pytest.mark.usefixtures("start_server")
def test_hello_world(expected: bytes):
    with httpx.Client() as client:
        response = client.get("http://localhost:8000/hello")

    assert response.content == expected
