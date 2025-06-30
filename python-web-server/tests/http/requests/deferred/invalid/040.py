from web_server.http.errors import InvalidHeaderName
from web_server.config import MessageConfig

cfg = MessageConfig.default()
# cfg.set("header_map", "refuse")

request = InvalidHeaderName
