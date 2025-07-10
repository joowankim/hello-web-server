import errno
import signal
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
        self._setup_signals()

    def _setup_signals(self) -> None:
        def shutdown_signal_handler(signum, frame):
            print(f"Received signal {signum}, shutting down gracefully.")
            self.shutdown()

        signal.signal(signal.SIGINT, shutdown_signal_handler)
        signal.signal(signal.SIGTERM, shutdown_signal_handler)
        signal.signal(signal.SIGQUIT, shutdown_signal_handler)
        signal.signal(signal.SIGABRT, shutdown_signal_handler)

    def shutdown(self) -> None:
        print("Worker shutting down...")
        self.alive = False
        self.server_socket.close()

    def run(self) -> None:
        print("Worker started.")
        try:
            while self.alive:
                self.listen()
        except OSError as exc:
            if exc.errno in (errno.EINTR, errno.EBADF):
                print("Server socket closed, shutting down gracefully.")
            else:
                raise exc

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
