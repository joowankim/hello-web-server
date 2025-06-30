from web_server.config import MessageConfig
from web_server.http.errors import LimitRequestHeaders

request = LimitRequestHeaders
cfg = MessageConfig.custom(limit_request_field_size=98)
