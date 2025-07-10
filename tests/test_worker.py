import socket
from unittest import mock

import pytest

from web_server.worker import Worker


@pytest.fixture
def mock_sock() -> mock.Mock:
    return mock.Mock(spec=socket.socket)


@pytest.fixture
def worker(mock_sock: mock.Mock, request: pytest.FixtureRequest) -> Worker:
    is_alive: bool = request.param
    _worker = Worker(
        server_socket=mock_sock,
        app=lambda environ, start_response: [b"Hello, World!"],
    )
    _worker.alive = is_alive
    return _worker


@pytest.mark.parametrize(
    "worker",
    [True, False],
    indirect=["worker"],
)
def test_shutdown(worker: Worker, mock_sock: mock.Mock):
    worker.shutdown()

    assert worker.alive is False
    mock_sock.close.assert_called_once()
