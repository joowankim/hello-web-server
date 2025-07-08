from collections.abc import Iterable

from web_server.worker import Worker


def app(environ, start_response) -> Iterable[bytes]:
    """Simplest possible application object"""

    status = "200 OK"
    content = b"Hello, World!"

    response_headers = [
        ("Content-type", "text/plain"),
        ("Content-Length", len(content)),
    ]
    start_response(status, response_headers)
    return [content]


def main():
    worker = Worker(host="localhost", port=8000, app=app)
    worker.run()


if __name__ == "__main__":
    main()
