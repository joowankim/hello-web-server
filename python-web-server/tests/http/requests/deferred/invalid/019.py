from web_server.config import MessageConfig
from web_server.errors import InvalidSchemeHeaders

request = InvalidSchemeHeaders
cfg = MessageConfig.default()
# cfg.set("forwarded_allow_ips", "*")
