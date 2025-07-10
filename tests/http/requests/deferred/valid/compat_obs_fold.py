from tests.http.treq import uri
from web_server.config import MessageConfig

cfg = MessageConfig.default()
# cfg.set('permit_obsolete_folding', True)

request = {
    "method": "GET",
    "uri": uri("/"),
    "version": (1, 1),
    "headers": [
        ("LONG", "one two"),
        ("HOST", "localhost"),
    ],
    "body": b"",
}
