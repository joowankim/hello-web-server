from tests.treq import uri

request = {
    "method": "GET",
    "uri": uri("/first"),
    "version": (1, 1),
    "headers": [("CONNECTION", "Close")],
    "body": b"",
}
