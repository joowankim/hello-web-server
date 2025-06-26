from collections.abc import Sequence

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
    ):
        self.method = method
        self.path = path
        self.query = query
        self.fragment = fragment
        self.version = version
        self.headers = headers
        self.body = body
