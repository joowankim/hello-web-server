import pytest

from web_server.config import EnvConfig


@pytest.fixture
def expected(request: pytest.FixtureRequest) -> EnvConfig:
    return EnvConfig(**request.param)


@pytest.mark.parametrize(
    "expected",
    [dict(script_name="")],
    indirect=["expected"],
)
def test_default(expected: EnvConfig):
    cfg = EnvConfig.default()

    assert cfg == expected


@pytest.mark.parametrize(
    "options, expected",
    [
        (dict(script_name=""), dict(script_name="")),
        (dict(script_name="/app"), dict(script_name="/app")),
        (dict(script_name="/app/subdir"), dict(script_name="/app/subdir")),
    ],
    indirect=["expected"],
)
def test_custom(options: dict[str, str], expected: EnvConfig):
    cfg = EnvConfig(**options)

    assert cfg == expected
