import tempfile
from collections.abc import Generator, Sequence
from typing import IO

import pytest

from web_server.wsgi import WSGIErrorStream


@pytest.fixture
def tmp_file() -> Generator[IO[str], None, None]:
    with tempfile.TemporaryFile("w+") as f:
        yield f


@pytest.fixture
def wsgi_error_stream(tmp_file: IO[str]) -> WSGIErrorStream:
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
    wsgi_error_stream: WSGIErrorStream, data: str, tmp_file: IO[str], expected: str
):
    wsgi_error_stream.write(data)
    wsgi_error_stream.flush()

    tmp_file.seek(0)

    assert tmp_file.read() == expected


@pytest.mark.parametrize(
    "data, expected",
    [
        (["line1", "line2\n", "line3"], "line1line2\nline3"),
        (["line1", "line2\n"], "line1line2\n"),
        ([], ""),
    ],
    ids=["multiple_lines", "two_lines", "empty"],
)
def test_writelines(
    wsgi_error_stream: WSGIErrorStream,
    data: Sequence[str],
    tmp_file: IO[str],
    expected: str,
):
    wsgi_error_stream.writelines(data)
    wsgi_error_stream.flush()

    tmp_file.seek(0)

    assert tmp_file.read() == expected
