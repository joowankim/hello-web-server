from tests.http.treq import uri

request = {
    "method": "-BLARGH",
    "uri": uri("/foo"),
    "version": (1, 1),
    "headers": [],
    "body": b"",
}
