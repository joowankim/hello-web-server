import collections
import dataclasses
import io
import sys
from collections.abc import Sequence
from typing import IO, Self, Any

from web_server import http, config


class WSGIErrorStream(io.RawIOBase):
    def __init__(self, sub_streams: list[IO[str]]):
        # There is no public __init__ method for RawIOBase so
        # we don't need to call super() in the __init__ method.
        # pylint: disable=super-init-not-called
        self.streams = sub_streams
        self._is_closed = False

    @classmethod
    def with_stderr(cls) -> Self:
        return cls([sys.stderr])

    def write(self, data: str) -> None:
        for stream in self.streams:
            try:
                stream.write(data)
            except UnicodeEncodeError:
                stream.write(data.encode("UTF-8"))

    def flush(self) -> None:
        if self._is_closed:
            return

        for stream in self.streams:
            try:
                if not stream.closed:
                    stream.flush()
            except (ValueError, OSError):
                pass

    def writelines(self, seq: Sequence[str]) -> None:
        if self._is_closed:
            return

        for stream in self.streams:
            for line in seq:
                try:
                    stream.write(line)
                except UnicodeEncodeError:
                    stream.write(line.encode("UTF-8"))

    def close(self) -> None:
        if not self._is_closed:
            self._is_closed = True

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass


@dataclasses.dataclass
class WSGIEnviron:
    request_method: str
    script_name: str
    path_info: str
    query_string: str
    content_type: str | None
    content_length: str | None
    server_name: str
    server_port: str
    server_protocol: str
    http_headers: list[tuple[str, str]]
    wsgi_version: tuple[int, int]
    wsgi_url_scheme: str
    wsgi_input: http.RequestBody
    wsgi_errors: WSGIErrorStream
    wsgi_multithread: bool
    wsgi_multiprocess: bool
    wsgi_run_once: bool

    @property
    def http_request(self) -> http.Request:
        headers = [
            (name[5:].replace("_", "-").title(), value)
            for name, value in self.http_headers
        ]
        if self.content_type is not None:
            headers.append(("Content-Type", self.content_type))
        if self.content_length is not None:
            headers.append(("Content-Length", self.content_length))
        return http.Request(
            method=self.request_method,
            path=f"{self.script_name}{self.path_info}",
            query=self.query_string,
            fragment="",
            version=self.wsgi_version,
            headers=headers,
            body=self.wsgi_input,
            trailers=[],
        )

    @classmethod
    def build(
        cls, cfg: config.Config, server: tuple[str, str], request: http.Request
    ) -> Self:
        script_name, path_info = cfg.parse_path(request.path)
        http_header_list = []
        content_type = None
        content_length = None
        for name, value in request.headers:
            uname = name.upper().replace("-", "_")
            if uname == "CONTENT_TYPE":
                content_type = value
                continue
            elif uname == "CONTENT_LENGTH":
                content_length = value
                continue
            http_header_list.append((f"HTTP_{uname}", value))
        http_headers_dict = collections.defaultdict(list)
        for name, value in http_header_list:
            http_headers_dict[name].append(value)
        http_headers = [
            (name, ",".join(value)) for name, value in http_headers_dict.items()
        ]
        return cls(
            request_method=request.method,
            script_name=script_name,
            path_info=path_info,
            query_string=request.query,
            http_headers=http_headers,
            server_name=server[0],
            server_port=server[1],
            server_protocol=f"HTTP/{request.version[0]}.{request.version[1]}",
            wsgi_version=request.version,
            wsgi_url_scheme=request.url_scheme,
            wsgi_input=request.body,
            wsgi_errors=WSGIErrorStream.with_stderr(),
            wsgi_multithread=False,
            wsgi_multiprocess=False,
            wsgi_run_once=False,
            content_type=content_type,
            content_length=content_length,
        )

    def dict(self) -> dict[str, Any]:
        base_environ = {
            "REQUEST_METHOD": self.request_method,
            "SCRIPT_NAME": self.script_name,
            "PATH_INFO": self.path_info,
            "QUERY_STRING": self.query_string,
            "CONTENT_TYPE": self.content_type,
            "CONTENT_LENGTH": self.content_length,
            "SERVER_NAME": self.server_name,
            "SERVER_PORT": self.server_port,
            "SERVER_PROTOCOL": self.server_protocol,
            "wsgi.version": self.wsgi_version,
            "wsgi.url_scheme": self.wsgi_url_scheme,
            "wsgi.input": self.wsgi_input,
            "wsgi.errors": self.wsgi_errors,
            "wsgi.multithread": self.wsgi_multithread,
            "wsgi.multiprocess": self.wsgi_multiprocess,
            "wsgi.run_once": self.wsgi_run_once,
        }
        return base_environ | {name: value for name, value in self.http_headers}
