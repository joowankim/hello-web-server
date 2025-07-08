import pytest

from web_server.config import Config, EnvConfig
from web_server.errors import ConfigurationProblem


@pytest.fixture
def cfg(request: pytest.FixtureRequest) -> Config:
    return Config.custom(env=EnvConfig.custom(script_name=request.param))


@pytest.mark.parametrize(
    "cfg, path, expected",
    [
        ("", "/path/to/resource", ("", "/path/to/resource")),
        ("/app", "/app/path/to/resource", ("/app", "/path/to/resource")),
        (
            "/app/subdir",
            "/app/subdir/path/to/resource",
            ("/app/subdir", "/path/to/resource"),
        ),
    ],
    indirect=["cfg"],
)
def test_parse_path(cfg: Config, path: str, expected: tuple[str, str]):
    script_name, path_info = cfg.parse_path(path)

    assert (script_name, path_info) == expected


@pytest.mark.parametrize(
    "cfg, path",
    [
        ("/app", "/subdir"),
        ("/app/", "/subdir/"),
        ("/app/subdir1", "/app/subdir2/another"),
        ("/app/subdir1/", "/app/subdir2/another/"),
    ],
    indirect=["cfg"],
)
def test_parse_path_with_non_subset_path(cfg: Config, path: str):
    with pytest.raises(
        ConfigurationProblem,
        match=f"Request path {path} does not start with SCRIPT_NAME {cfg.env.script_name}",
    ):
        cfg.parse_path(path)
