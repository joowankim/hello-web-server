import multiprocessing
import os
import signal
import socket
from collections.abc import Generator

import pytest

from web_server.worker import Worker


def worker_function():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("localhost", 8000))
    worker = Worker(
        server_socket=sock,
        app=lambda environ, start_response: [b"Hello, World!"],
    )
    worker.run()


@pytest.fixture
def worker_process() -> Generator[multiprocessing.Process, None, None]:
    process = multiprocessing.Process(target=worker_function)
    process.start()
    yield process
    process.terminate()
    process.join(timeout=5)


@pytest.mark.parametrize(
    "sig", [signal.SIGABRT, signal.SIGINT, signal.SIGTERM, signal.SIGQUIT]
)
def test_graceful_shutdown(worker_process: multiprocessing.Process, sig: int):
    os.kill(worker_process.pid, sig)

    worker_process.join()

    assert worker_process.is_alive() is False
