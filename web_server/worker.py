import socket
from collections.abc import Callable, Iterable
from typing import Any

from web_server import config, http, wsgi, connection
from web_server.cycle import Cycle
from web_server.errors import ParseException


class Worker:
    def __init__(
        self,
        server_socket: socket.socket,
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
        self.app = app
        self.alive = True
        self.server_socket = server_socket
        self.server_socket.listen(socket.SOMAXCONN)

    def shutdown(self) -> None:
        self.alive = False
        self.server_socket.close()

    def run(self) -> None:
        print("Worker started.")
        while self.alive:
            self.listen()

    def listen(self) -> None:
        conn, addr = self.server_socket.accept()
        conn.setblocking(False)
        with conn:
            cfg = config.Config.default()
            parser = http.RequestParser(
                cfg=cfg.message, socket_reader=http.SocketReader(sock=conn)
            )
            try:
                req = next(parser.parse())
                environ = wsgi.WSGIEnviron.build(
                    cfg=cfg, server=conn.getsockname(), request=req
                )
                cycle = Cycle(
                    conn=connection.Connection(sock=conn),
                    environ=environ,
                    app=self.app,
                )
                resp = cycle.handle_request()
            except ParseException as exc:
                resp = http.Response.bad_request(exc)
            except BaseException as exc:
                resp = http.Response.internal_server_error(exc)
            finally:
                if not cycle.headers_sent:
                    conn.sendall(resp.headers_data())
                    for chunk in resp.body_stream():
                        conn.sendall(chunk)
