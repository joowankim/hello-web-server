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
            forwarded_allow_ips="127.0.0.1,::1",
            secure_scheme_headers={
                "X-FORWARDED-PROTOCOL": "ssl",
                "X-FORWARDED-PROTO": "https",
                "X-FORWARDED-SSL": "on",
            },
            forwarder_headers="SCRIPT_NAME,PATH_INFO",
            strip_header_spaces=False,
            permit_obsolete_folding=False,
            header_map="drop",
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
                forwarded_allow_ips="127.0.0.1,::1",
                secure_scheme_headers={
                    "X-FORWARDED-PROTOCOL": "ssl",
                    "X-FORWARDED-PROTO": "https",
                    "X-FORWARDED-SSL": "on",
                },
                forwarder_headers="SCRIPT_NAME,PATH_INFO",
                strip_header_spaces=False,
                permit_obsolete_folding=False,
                header_map="drop",
            ),
        ),
        (
            dict(limit_request_line=0),
            dict(
                limit_request_line=0,
                limit_request_fields=100,
                limit_request_field_size=8190,
                forwarded_allow_ips="127.0.0.1,::1",
                secure_scheme_headers={
                    "X-FORWARDED-PROTOCOL": "ssl",
                    "X-FORWARDED-PROTO": "https",
                    "X-FORWARDED-SSL": "on",
                },
                forwarder_headers="SCRIPT_NAME,PATH_INFO",
                strip_header_spaces=False,
                permit_obsolete_folding=False,
                header_map="drop",
            ),
        ),
        (
            dict(limit_request_line=9000),
            dict(
                limit_request_line=8190,
                limit_request_fields=100,
                limit_request_field_size=8190,
                forwarded_allow_ips="127.0.0.1,::1",
                secure_scheme_headers={
                    "X-FORWARDED-PROTOCOL": "ssl",
                    "X-FORWARDED-PROTO": "https",
                    "X-FORWARDED-SSL": "on",
                },
                forwarder_headers="SCRIPT_NAME,PATH_INFO",
                strip_header_spaces=False,
                permit_obsolete_folding=False,
                header_map="drop",
            ),
        ),
        (
            dict(limit_request_line=1),
            dict(
                limit_request_line=1,
                limit_request_fields=100,
                limit_request_field_size=8190,
                forwarded_allow_ips="127.0.0.1,::1",
                secure_scheme_headers={
                    "X-FORWARDED-PROTOCOL": "ssl",
                    "X-FORWARDED-PROTO": "https",
                    "X-FORWARDED-SSL": "on",
                },
                forwarder_headers="SCRIPT_NAME,PATH_INFO",
                strip_header_spaces=False,
                permit_obsolete_folding=False,
                header_map="drop",
            ),
        ),
    ],
    indirect=["expected"],
)
def test_custom(options: dict[str, Any], expected: MessageConfig):
    assert MessageConfig.custom(**options) == expected
