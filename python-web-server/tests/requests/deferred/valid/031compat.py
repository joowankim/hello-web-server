from tests.treq import uri
from web_server.config import MessageConfig

cfg = MessageConfig.default()
# cfg.set("permit_unconventional_http_method", True)
# cfg.set("casefold_http_method", True)

request = {
    "method": "-BLARGH",
    "uri": uri("/foo"),
    "version": (1, 1),
    "headers": [],
    "body": b"",
}
