from tests.http.treq import uri

request = {
    "method": "GET",
    "uri": uri("/stuff/here?foo=bar"),
    "version": (1, 0),
    "headers": [("IF-MATCH", "bazinga!"), ("IF-MATCH", "large-sound")],
    "body": b"",
}
