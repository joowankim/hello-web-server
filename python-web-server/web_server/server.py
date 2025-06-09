import socket


class Server:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self._server = None

    def run(self) -> None:
        print("Web server started.")
        new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        new_socket.bind((self.host, self.port))
        self._server = new_socket
        self._server.listen(0)
        conn, addr = self._server.accept()
        with conn:
            response_body = b"Hello, World!"
            response_headers = [
                b"HTTP/1.1 200 OK",
                b"Content-Type: text/plain; charset=utf-8",
                b"Content-Length: " + str(len(response_body)).encode(),
                b"Connection: close",
            ]
            response = b"\r\n".join(response_headers) + b"\r\n\r\n" + response_body
            conn.sendall(response)

    def shutdown(self) -> None:
        if self._server:
            print("Web server stopped.")
        else:
            print("No server to stop.")
