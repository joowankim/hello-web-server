def app(environ, start_response):
    """Simplest possible application object"""

    status = "200 OK"
    content = b"Hello, World!"

    response_headers = [
        ("Content-type", "text/plain"),
        ("Content-Length", len(content)),
    ]
    start_response(status, response_headers)
    return iter([content])
