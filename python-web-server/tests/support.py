from wsgiref.validate import validator


def create_app(name="World", count=1):
    message = (("Hello, %s!\n" % name) * count).encode("utf8")
    length = str(len(message))

    @validator
    def app(environ, start_response):
        """Simplest possible application object"""

        status = "200 OK"

        response_headers = [
            ("Content-type", "text/plain"),
            ("Content-Length", length),
        ]
        start_response(status, response_headers)
        return iter([message])

    return app


app = application = create_app()
