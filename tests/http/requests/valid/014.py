from tests.http.treq import uri

request = {
    "method": "GET",
    "uri": uri('/with_"quotes"?foo="bar"'),
    "version": (1, 1),
    "headers": [],
    "body": b"",
}
