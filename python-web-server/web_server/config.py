import dataclasses
from typing import Self

MAX_REQUEST_LINE = 8190
MAX_HEADERS = 32768
DEFAULT_MAX_HEADERFIELD_SIZE = 8190


@dataclasses.dataclass
class MessageConfig:
    limit_request_line: int
    limit_request_fields: int
    limit_request_field_size: int
    permit_unconventional_http_method: bool
    permit_unconventional_http_version: bool

    @classmethod
    def default(cls) -> Self:
        return cls(
            limit_request_line=4094,
            limit_request_fields=100,
            limit_request_field_size=8190,
            permit_unconventional_http_method=False,
            permit_unconventional_http_version=False,
        )

    @classmethod
    def custom(
        cls,
        limit_request_line: int = 4094,
        limit_request_fields: int = 100,
        limit_request_field_size: int = 8190,
        permit_unconventional_http_method: bool = False,
        permit_unconventional_http_version: bool = False,
    ) -> Self:
        return cls(
            limit_request_line=MAX_REQUEST_LINE
            if limit_request_line == 0
            else min(limit_request_line, MAX_REQUEST_LINE),
            limit_request_fields=min(limit_request_fields, MAX_HEADERS),
            limit_request_field_size=DEFAULT_MAX_HEADERFIELD_SIZE
            if limit_request_field_size < 0
            else limit_request_field_size,
            permit_unconventional_http_method=permit_unconventional_http_method,
            permit_unconventional_http_version=permit_unconventional_http_version,
        )
