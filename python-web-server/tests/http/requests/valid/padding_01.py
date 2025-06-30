from tests.treq import uri

request = {
    "method": "GET",
    "uri": uri("/"),
    "version": (1, 1),
    "headers": [("HOST", "localhost"), ("NAME", "value")],
    "body": b"",
}
