from tests.http.treq import uri

request = {
    "method": "GET",
    "uri": uri("/silly"),
    "version": (1, 1),
    "headers": [("AAAAAAAAAAAAA", "++++++++++")],
    "body": b"",
}
