import pytest

from web_server.http.message import TOKEN_PATTERN


@pytest.mark.parametrize(
    "method, expected",
    [
        ("GET", True),
        ("MKCALENDAR", True),
        ("GET:", False),
        ("GET;", False),
    ],
    ids=(
        "method name token must match TOKEN_PATTERN",
        "method name token which is extension-method must match TOKEN_PATTERN",
        "method name token with invalid character ':' must not match TOKEN_PATTERN",
        "method name token with invalid character ';' must not match TOKEN_PATTERN",
    ),
)
def test_method_pattern(method: str, expected: bool):
    matched = TOKEN_PATTERN.fullmatch(method)

    assert (matched is not None) is expected


@pytest.mark.parametrize(
    "field_name, expected",
    [
        ("Content-Type", True),
        ("User-Agent", True),
        ("Host", True),
        ("If-Match", True),
        ("My Header", False),
        ("Content:Type", False),
        ("MyHeader?", False),
        ('"QuotedHeader"', False),
        ("Invalid/Header", False),
    ],
    ids=(
        "'Content-Type' must match TOKEN_PATTERN",
        "'User-Agent' must match TOKEN_PATTERN",
        "'Host' must match TOKEN_PATTERN",
        "'If-Match' must match TOKEN_PATTERN",
        "field name token with invalid character ' ' must not match TOKEN_PATTERN",
        "field name token with invalid character ':' must not match TOKEN_PATTERN",
        "field name token with invalid character '?' must not match TOKEN_PATTERN",
        "field name token with invalid character '\"' must not match TOKEN_PATTERN",
        "field name token with invalid character '/' must not match TOKEN_PATTERN",
    ),
)
def test_field_name_pattern(field_name: str, expected: bool):
    matched = TOKEN_PATTERN.fullmatch(field_name)

    assert (matched is not None) is expected


@pytest.mark.parametrize(
    "contents_coding, expected",
    [
        ("gzip", True),
        ("deflate", True),
        ("br", True),
        ("identity", True),
        ("compress", True),
        ("my-coding", True),
        ("my_coding", True),
        ("my coding", False),
        ("my-coding:", False),
        ("my-coding;", False),
    ],
    ids=(
        "'gzip' must match TOKEN_PATTERN",
        "'deflate' must match TOKEN_PATTERN",
        "'br' must match TOKEN_PATTERN",
        "'identity' must match TOKEN_PATTERN",
        "'compress' must match TOKEN_PATTERN",
        "'my-coding' must match TOKEN_PATTERN",
        "'my_coding' must match TOKEN_PATTERN",
        "'my coding' must not match TOKEN_PATTERN (space)",
        "'my-coding:' must not match TOKEN_PATTERN (colon)",
        "'my-coding;' must not match TOKEN_PATTERN (semicolon)",
    ),
)
def test_contents_coding_pattern(contents_coding: str, expected: bool):
    matched = TOKEN_PATTERN.fullmatch(contents_coding)

    assert (matched is not None) is expected


@pytest.mark.parametrize(
    "media_type_component, expected",
    [
        ("text", True),
        ("plain", True),
        ("application", True),
        ("json", True),
        ("image/png", False),
        ("my type", False),
        ("my/type:", False),
        ("my/type;", False),
    ],
    ids=(
        "'text' media type must match TOKEN_PATTERN",
        "'plain' media sub type must match TOKEN_PATTERN",
        "'application' media type must match TOKEN_PATTERN",
        "'json' media sub type must match TOKEN_PATTERN",
        "'image/png' must not match TOKEN_PATTERN (slash)",
        "'my type' must not match TOKEN_PATTERN (space)",
        "'mytype:' must not match TOKEN_PATTERN (colon)",
        "'mytype;' must not match TOKEN_PATTERN (semicolon)",
    ),
)
def test_media_type_pattern(media_type_component: str, expected: bool):
    matched = TOKEN_PATTERN.fullmatch(media_type_component)

    assert (matched is not None) is expected


@pytest.mark.parametrize(
    "parameter_name, expected",
    [
        ("charset", True),
        ("boundary", True),
        ("q", True),
        ("my-parameter", True),
        ("my_parameter", True),
        ("my parameter", False),
        ("my-parameter:", False),
        ("my-parameter;", False),
    ],
    ids=(
        "'charset' must match TOKEN_PATTERN",
        "'boundary' must match TOKEN_PATTERN",
        "'q' must match TOKEN_PATTERN",
        "'my-parameter' must match TOKEN_PATTERN",
        "'my_parameter' must match TOKEN_PATTERN",
        "'my parameter' must not match TOKEN_PATTERN (space)",
        "'my-parameter:' must not match TOKEN_PATTERN (colon)",
        "'my-parameter;' must not match TOKEN_PATTERN (semicolon)",
    ),
)
def test_parameter_name_pattern(parameter_name: str, expected: bool):
    matched = TOKEN_PATTERN.fullmatch(parameter_name)

    assert (matched is not None) is expected


@pytest.mark.parametrize(
    "authentication_scheme, expected",
    [
        ("Basic", True),
        ("Bearer", True),
        ("Digest", True),
        ("Negotiate", True),
        ("my-scheme", True),
        ("my_scheme", True),
        ("my scheme", False),
        ("my-scheme:", False),
        ("my-scheme;", False),
    ],
    ids=(
        "'Basic' authentication scheme must match TOKEN_PATTERN",
        "'Bearer' authentication scheme must match TOKEN_PATTERN",
        "'Digest' authentication scheme must match TOKEN_PATTERN",
        "'Negotiate' authentication scheme must match TOKEN_PATTERN",
        "'my-scheme' authentication scheme must match TOKEN_PATTERN",
        "'my_scheme' authentication scheme must match TOKEN_PATTERN",
        "'my scheme' must not match TOKEN_PATTERN (space)",
        "'my-scheme:' must not match TOKEN_PATTERN (colon)",
        "'my-scheme;' must not match TOKEN_PATTERN (semicolon)",
    ),
)
def test_authentication_scheme_pattern(authentication_scheme: str, expected: bool):
    matched = TOKEN_PATTERN.fullmatch(authentication_scheme)

    assert (matched is not None) is expected


@pytest.mark.parametrize(
    "protocol_name_and_version, expected",
    [
        ("HTTP", True),
        ("1.1", True),
        ("2", True),
        ("MyProtocol/1.0", False),
        ("MyProtocol 1.0", False),
        ("MyProtocol/1.0:", False),
        ("MyProtocol/1.0;", False),
    ],
    ids=(
        "'HTTP' protocol name must match TOKEN_PATTERN",
        "'1.1' protocol version must match TOKEN_PATTERN",
        "'2' protocol version must match TOKEN_PATTERN",
        "'MyProtocol/1.0' must not match TOKEN_PATTERN (slash)",
        "'MyProtocol 1.0' must not match TOKEN_PATTERN (space)",
        "'MyProtocol:' must not match TOKEN_PATTERN (colon)",
        "'MyProtocol;' must not match TOKEN_PATTERN (semicolon)",
    ),
)
def test_protocol_name_and_version_pattern(
    protocol_name_and_version: str, expected: bool
):
    matched = TOKEN_PATTERN.fullmatch(protocol_name_and_version)

    assert (matched is not None) is expected


def test_token_pattern_with_invalid_characters():
    RFC9110_5_6_2_TOKEN_DELIM = '"(),/:;<=>?@[\]{}'

    for token in RFC9110_5_6_2_TOKEN_DELIM:
        matched = TOKEN_PATTERN.match(token)

        assert (matched is None) is True
