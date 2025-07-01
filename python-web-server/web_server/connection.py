import socket


class Connection:
    def __init__(self, sock: socket.socket):
        self.sock = sock

    def write(self, response_body: bytes) -> None:
        self.sock.sendall(response_body)
