import multiprocessing
import time
from collections.abc import Generator

import httpx
import pytest

from web_server.server import Server


@pytest.fixture
def running_server() -> Generator[None, None, None]:
    server = Server(host="localhost", port=8000)
    server_process = multiprocessing.Process(target=server.run)
    server_process.start()
    time.sleep(1)
    try:
        yield
    finally:
        server_process.terminate()
        server_process.join()


@pytest.fixture
def expected() -> bytes:
    return b"Hello, World!"


@pytest.mark.usefixtures("running_server")
def test_run(expected: bytes):
    with httpx.Client() as client:
        response = client.get("http://localhost:8000")

    assert response.content == expected
