from web_server.config import MessageConfig
from web_server.errors import LimitRequestHeaders

request = LimitRequestHeaders
cfg = MessageConfig.custom(limit_request_field_size=14)

# once this option is removed, this test should not be dropped;
#  rather, add something involving unnessessary padding
# cfg.set("permit_obsolete_folding", True)
