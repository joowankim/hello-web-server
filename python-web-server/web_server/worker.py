import socket
from collections.abc import Callable, Iterable
from typing import Any

from web_server import config, http, wsgi, connection
from web_server.cycle import Cycle


class Worker:
    def __init__(
        self,
        host: str,
        port: int,
        app: Callable[
            [
                dict[str, Any],
                Callable[
                    [str, list[tuple[str, str]], connection.ExcInfo],
                    Callable[[bytes], None],
                ],
            ],
            Iterable[bytes],
        ],
    ):
        self.host = host
        self.port = port
        self.app = app
        self._server = None

    def run(self):
        print("Worker started.")
        new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        new_socket.bind((self.host, self.port))
        self._server = new_socket
        self._server.listen(0)
        conn, addr = self._server.accept()
        conn.setblocking(False)
        with conn:
            cfg = config.Config.default()
            parser = http.RequestParser(
                cfg=cfg.message, socket_reader=http.SocketReader(sock=conn)
            )
            for req in parser.parse():
                environ = wsgi.WSGIEnviron.build(
                    cfg=cfg, server=conn.getsockname(), request=req
                )
                cycle = Cycle(
                    conn=connection.Connection(sock=conn),
                    environ=environ,
                    app=self.app,
                )
                cycle.handle_request()
