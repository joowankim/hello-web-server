from web_server.config import MessageConfig
from web_server.http.errors import InvalidProxyLine

cfg = MessageConfig.default()
# cfg.set("proxy_protocol", True)

request = InvalidProxyLine
