from collections.abc import Sequence
from typing import Self

from web_server.http import reader, parser
from web_server.http.body import RequestBody


class Request:
    def __init__(
        self,
        method: str,
        path: str,
        query: str,
        fragment: str,
        headers: Sequence[tuple[str, str]],
        body: RequestBody,
    ):
        self.method = method
        self.path = path
        self.query = query
        self.fragment = fragment
        self.headers = headers
        self.body = body

    @classmethod
    def create(cls, request_parser: parser.RequestParser) -> Self:
        method, (path, query, fragment), version = request_parser.parse_request_line()
        headers = request_parser.parse_headers()

        body = RequestBody.create(version, headers, request_parser.reader)
        if isinstance(body.reader, reader.ChunkedReader):
            headers += body.reader.trailers
        return cls(
            method=method,
            path=path,
            query=query,
            fragment=fragment,
            headers=headers,
            body=body,
        )
