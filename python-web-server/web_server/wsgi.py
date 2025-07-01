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
        for stream in self.streams:
            stream.flush()

    def writelines(self, seq: Sequence[str]) -> None:
        for stream in self.streams:
            for line in seq:
                try:
                    stream.write(line)
                except UnicodeEncodeError:
                    stream.write(line.encode("UTF-8"))


@dataclasses.dataclass
class WSGIEnviron:
    request_method: str
    script_name: str
    path_info: str
    query_string: str
    server_name: str
    server_port: str
    server_protocol: str
    wsgi_version: tuple[int, int]
    wsgi_url_scheme: str
    wsgi_input: http.RequestBody
    wsgi_errors: WSGIErrorStream
    wsgi_multithread: bool
    wsgi_multiprocess: bool
    wsgi_run_once: bool

    @classmethod
    def build(
        cls, cfg: config.Config, server: tuple[str, str], request: http.Request
    ) -> Self:
        script_name, path_info = cfg.parse_path(request.path)
        return cls(
            request_method=request.method,
            script_name=script_name,
            path_info=path_info,
            query_string=request.query,
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
        )

    def dict(self) -> dict[str, Any]:
        return {
            "REQUEST_METHOD": self.request_method,
            "SCRIPT_NAME": self.script_name,
            "PATH_INFO": self.path_info,
            "QUERY_STRING": self.query_string,
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
