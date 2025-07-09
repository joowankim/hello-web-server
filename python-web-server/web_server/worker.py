import socket
from collections.abc import Callable, Iterable
from typing import Any

from web_server import config, http, wsgi, connection
from web_server.cycle import Cycle
from web_server.errors import ParseException


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

    def run(self) -> None:
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
