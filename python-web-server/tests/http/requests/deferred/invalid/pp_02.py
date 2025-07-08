from web_server.config import MessageConfig
from web_server.errors import InvalidProxyLine

cfg = MessageConfig.default()
# cfg.set("proxy_protocol", True)

request = InvalidProxyLine
