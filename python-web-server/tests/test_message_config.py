import sys
from typing import Any

import pytest

from web_server.config import MessageConfig


@pytest.fixture
def expected(request: pytest.FixtureRequest) -> MessageConfig:
    return MessageConfig(**request.param)


@pytest.mark.parametrize(
    "expected",
    [
        dict(
            limit_request_line=4094,
            limit_request_fields=100,
            limit_request_field_size=8190,
            permit_unconventional_http_method=False,
            permit_unconventional_http_version=False,
        ),
    ],
    indirect=["expected"],
)
def test_default(expected: MessageConfig):
    assert MessageConfig.default() == expected


@pytest.mark.parametrize(
    "options, expected",
    [
        (
            dict(),
            dict(
                limit_request_line=4094,
                limit_request_fields=100,
                limit_request_field_size=8190,
                permit_unconventional_http_method=False,
                permit_unconventional_http_version=False,
            ),
        ),
        (
            dict(limit_request_line=0),
            dict(
                limit_request_line=sys.maxsize,
                limit_request_fields=100,
                limit_request_field_size=8190,
                permit_unconventional_http_method=False,
                permit_unconventional_http_version=False,
            ),
        ),
        (
            dict(limit_request_line=9000),
            dict(
                limit_request_line=8190,
                limit_request_fields=100,
                limit_request_field_size=8190,
                permit_unconventional_http_method=False,
                permit_unconventional_http_version=False,
            ),
        ),
        (
            dict(limit_request_line=1),
            dict(
                limit_request_line=1,
                limit_request_fields=100,
                limit_request_field_size=8190,
                permit_unconventional_http_method=False,
                permit_unconventional_http_version=False,
            ),
        ),
        (
            dict(limit_request_fields=0),
            dict(
                limit_request_line=4094,
                limit_request_fields=0,
                limit_request_field_size=8190,
                permit_unconventional_http_method=False,
                permit_unconventional_http_version=False,
            ),
        ),
        (
            dict(limit_request_fields=40000),
            dict(
                limit_request_line=4094,
                limit_request_fields=32768,
                limit_request_field_size=8190,
                permit_unconventional_http_method=False,
                permit_unconventional_http_version=False,
            ),
        ),
        (
            dict(limit_request_field_size=0),
            dict(
                limit_request_line=4094,
                limit_request_fields=100,
                limit_request_field_size=sys.maxsize,
                permit_unconventional_http_method=False,
                permit_unconventional_http_version=False,
            ),
        ),
        (
            dict(limit_request_field_size=9000),
            dict(
                limit_request_line=4094,
                limit_request_fields=100,
                limit_request_field_size=9000,
                permit_unconventional_http_method=False,
                permit_unconventional_http_version=False,
            ),
        ),
    ],
    indirect=["expected"],
)
def test_custom(options: dict[str, Any], expected: MessageConfig):
    assert MessageConfig.custom(**options) == expected
