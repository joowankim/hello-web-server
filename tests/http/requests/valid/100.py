from tests.http.treq import uri

request = {
    "method": "GET",
    "uri": uri("///keeping_slashes"),
    "version": (1, 1),
    "headers": [],
    "body": b"",
}
