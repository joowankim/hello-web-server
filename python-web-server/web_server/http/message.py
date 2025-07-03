from collections.abc import Sequence
from typing import IO

from web_server.http.body import RequestBody


class Request:
    def __init__(
        self,
        method: str,
        path: str,
        query: str,
        fragment: str,
        version: tuple[int, int],
        headers: Sequence[tuple[str, str]],
        body: RequestBody,
        trailers: Sequence[tuple[str, str]],
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
        headers: Sequence[tuple[str, str]],
        body: IO[bytes],
    ):
        self.version = version
        self.status = status
        self.headers = headers
        self.body = body
