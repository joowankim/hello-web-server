import dataclasses
from typing import Self

MAX_REQUEST_LINE = 8190


@dataclasses.dataclass
class MessageConfig:
    limit_request_line: int
    limit_request_fields: int
    limit_request_field_size: int
    forwarded_allow_ips: str
    secure_scheme_headers: dict[str, str]
    forwarder_headers: str
    strip_header_spaces: bool
    permit_obsolete_folding: bool
    header_map: str
    permit_unconventional_http_method: bool
    permit_unconventional_http_version: bool
    casefold_http_method: bool

    @classmethod
    def default(cls) -> Self:
        return cls(
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
            permit_unconventional_http_method=False,
            permit_unconventional_http_version=False,
            casefold_http_method=False,
        )

    @classmethod
    def custom(
        cls,
        limit_request_line: int = 4094,
        limit_request_fields: int = 100,
        limit_request_field_size: int = 8190,
        forwarded_allow_ips: str = "127.0.0.1,::1",
        secure_scheme_headers: dict[str, str] = {
            "X-FORWARDED-PROTOCOL": "ssl",
            "X-FORWARDED-PROTO": "https",
            "X-FORWARDED-SSL": "on",
        },
        forwarder_headers: str = "SCRIPT_NAME,PATH_INFO",
        strip_header_spaces: bool = False,
        permit_obsolete_folding: bool = False,
        header_map: str = "drop",
        permit_unconventional_http_method: bool = False,
        permit_unconventional_http_version: bool = False,
        casefold_http_method: bool = False,
    ) -> Self:
        return cls(
            limit_request_line=min(limit_request_line, MAX_REQUEST_LINE),
            limit_request_fields=limit_request_fields,
            limit_request_field_size=limit_request_field_size,
            forwarded_allow_ips=forwarded_allow_ips,
            secure_scheme_headers=secure_scheme_headers,
            forwarder_headers=forwarder_headers,
            strip_header_spaces=strip_header_spaces,
            permit_obsolete_folding=permit_obsolete_folding,
            header_map=header_map,
            permit_unconventional_http_method=permit_unconventional_http_method,
            permit_unconventional_http_version=permit_unconventional_http_version,
            casefold_http_method=casefold_http_method,
        )
