from urllib.parse import SplitResult

import pytest

from web_server import util


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (
            "https://example.org/a/b?c=1#d",
            SplitResult(
                scheme="https",
                netloc="example.org",
                path="/a/b",
                query="c=1",
                fragment="d",
            ),
        ),
        (
            "a/b?c=1#d",
            SplitResult(scheme="", netloc="", path="a/b", query="c=1", fragment="d"),
        ),
        (
            "/a/b?c=1#d",
            SplitResult(scheme="", netloc="", path="/a/b", query="c=1", fragment="d"),
        ),
        (
            "//a/b?c=1#d",
            SplitResult(scheme="", netloc="", path="//a/b", query="c=1", fragment="d"),
        ),
        (
            "///a/b?c=1#d",
            SplitResult(scheme="", netloc="", path="///a/b", query="c=1", fragment="d"),
        ),
    ],
)
def test_split_request_uri(test_input, expected):
    assert util.split_request_uri(test_input) == expected
