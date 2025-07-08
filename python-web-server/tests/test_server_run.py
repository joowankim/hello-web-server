import multiprocessing
import time
from collections.abc import Generator

import httpx
import pytest

from tests import support
from web_server.worker import Worker


@pytest.fixture
def running_worker() -> Generator[None, None, None]:
    worker = Worker(host="localhost", port=8000, app=support.app)
    worker_process = multiprocessing.Process(target=worker.run)
    worker_process.start()
    time.sleep(1)
    try:
        yield
    finally:
        worker_process.terminate()
        worker_process.join()


@pytest.fixture
def expected() -> bytes:
    return b"Hello, World!"


@pytest.mark.usefixtures("running_worker")
def test_run(expected: bytes):
    with httpx.Client() as client:
        response = client.get("http://localhost:8000")

    assert response.content == expected
