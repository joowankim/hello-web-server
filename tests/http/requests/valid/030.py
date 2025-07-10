from tests.http.treq import uri
from web_server.config import MessageConfig

cfg = MessageConfig.default()

request = {
    "method": "GET",
    "uri": uri("/stuff/here?foo=bar"),
    "version": (1, 1),
    "headers": [("TRANSFER-ENCODING", "identity"), ("TRANSFER-ENCODING", "chunked")],
    "body": b"hello",
}
