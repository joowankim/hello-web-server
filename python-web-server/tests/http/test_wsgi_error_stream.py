import tempfile
from collections.abc import Generator
from typing import IO

import pytest

from web_server.wsgi import WSGIErrorStream


@pytest.fixture
def tmp_file() -> Generator[IO[str], None, None]:
    with tempfile.TemporaryFile("w+") as f:
        yield f


@pytest.fixture
def wsgi_error_stream(tmp_file: IO[bytes]) -> WSGIErrorStream:
    return WSGIErrorStream([tmp_file])


@pytest.mark.parametrize(
    "data, expected",
    [
        ("test", "test"),
        ("test\n", "test\n"),
        ("", ""),
    ],
    ids=["no_newline", "newline_lf", "empty"],
)
def test_write(
    wsgi_error_stream: WSGIErrorStream, data: str, tmp_file: IO[bytes], expected: str
):
    wsgi_error_stream.write(data)
    wsgi_error_stream.flush()

    tmp_file.seek(0)

    assert tmp_file.read() == expected
