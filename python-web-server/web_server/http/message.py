from typing import IO, Self

from web_server.http.body import RequestBody


class Request:
    def __init__(
        self,
        method: str,
        path: str,
        query: str,
        fragment: str,
        version: tuple[int, int],
        headers: list[tuple[str, str]],
        body: RequestBody,
        trailers: list[tuple[str, str]],
    ):
        self.url_scheme = "http"
        self.method = method
        self.path = path
        self.query = query
        self.fragment = fragment
        self.version = version
        self.headers = headers
        self.body = body
        self.trailers = trailers


class Response:
    def __init__(
        self,
        version: tuple[int, int],
        status: str,
        headers: list[tuple[str, str]],
        body: IO[bytes] | None,
    ):
        self.version = version
        self.status = status
        self.headers = headers
        self.body = body

    @classmethod
    def draft(
        cls,
        protocol_version: tuple[int, int],
        status: str,
        headers: list[tuple[str, str]],
    ) -> Self:
        return cls(
            version=protocol_version,
            status=status,
            headers=headers,
            body=None,
        )
