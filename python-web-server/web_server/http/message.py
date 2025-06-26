from collections.abc import Sequence

from web_server.http.body import RequestBody


class Request:
    def __init__(
        self,
        method: str,
        path: str,
        query: str,
        fragment: str,
        headers: Sequence[tuple[str, str]],
        body: RequestBody | None,
    ):
        self.method = method
        self.path = path
        self.query = query
        self.fragment = fragment
        self.headers = headers
        self.body = body
