import dataclasses
import sys
from typing import Self

from web_server.http.errors import ConfigurationProblem

MAX_REQUEST_LINE = 8190
MAX_HEADERS = 32768
DEFAULT_MAX_HEADERFIELD_SIZE = 8190


@dataclasses.dataclass
class MessageConfig:
    limit_request_line: int = 4094
    limit_request_fields: int = 100
    limit_request_field_size: int = 8190
    permit_unconventional_http_method: bool = False
    permit_unconventional_http_version: bool = False

    @classmethod
    def default(cls) -> Self:
        return cls()

    @classmethod
    def custom(
        cls,
        limit_request_line: int = 4094,
        limit_request_fields: int = 100,
        limit_request_field_size: int = 8190,
        permit_unconventional_http_method: bool = False,
        permit_unconventional_http_version: bool = False,
    ) -> Self:
        limit_request_line = (
            MAX_REQUEST_LINE
            if limit_request_line < 0
            else min(limit_request_line, MAX_REQUEST_LINE)
        ) or sys.maxsize
        limit_request_field_size = (
            DEFAULT_MAX_HEADERFIELD_SIZE
            if limit_request_field_size < 0
            else limit_request_field_size
        ) or sys.maxsize
        return cls(
            limit_request_line=limit_request_line,
            limit_request_fields=min(limit_request_fields, MAX_HEADERS),
            limit_request_field_size=limit_request_field_size,
            permit_unconventional_http_method=permit_unconventional_http_method,
            permit_unconventional_http_version=permit_unconventional_http_version,
        )


@dataclasses.dataclass
class EnvConfig:
    script_name: str = ""

    @classmethod
    def default(cls) -> Self:
        return cls()

    @classmethod
    def custom(cls, script_name: str = "") -> Self:
        return cls(script_name=script_name)


@dataclasses.dataclass
class Config:
    message: MessageConfig
    env: EnvConfig

    @classmethod
    def default(cls) -> Self:
        return cls(
            message=MessageConfig.default(),
            env=EnvConfig.default(),
        )

    @classmethod
    def custom(
        cls,
        message: MessageConfig = MessageConfig.default(),
        env: EnvConfig = EnvConfig.default(),
    ) -> Self:
        return cls(message=message, env=env)

    def parse_path(self, path: str) -> tuple[str, str]:
        if not path.startswith(self.env.script_name):
            raise ConfigurationProblem(
                f"Request path {path} does not start with SCRIPT_NAME {self.env.script_name}"
            )

        script_name = self.env.script_name.rstrip("/")
        path_info = path[len(script_name) :]

        return self.env.script_name, path_info
