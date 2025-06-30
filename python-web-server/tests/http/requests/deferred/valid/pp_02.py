from tests.treq import uri
from web_server.config import MessageConfig

cfg = MessageConfig.default()
# cfg.set("proxy_protocol", True)

req1 = {
    "method": "GET",
    "uri": uri("/stuff/here?foo=bar"),
    "version": (1, 1),
    "headers": [
        ("SERVER", "http://127.0.0.1:5984"),
        ("CONTENT-TYPE", "application/json"),
        ("CONTENT-LENGTH", "14"),
        ("CONNECTION", "keep-alive"),
    ],
    "body": b'{"nom": "nom"}',
}


req2 = {
    "method": "POST",
    "uri": uri("/post_chunked_all_your_base"),
    "version": (1, 1),
    "headers": [
        ("TRANSFER-ENCODING", "chunked"),
    ],
    "body": b"all your base are belong to us",
}

request = [req1, req2]
