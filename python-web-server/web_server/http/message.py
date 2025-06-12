import re

RFC9110_5_6_2_TOKEN_SPECIALS = r"!#$%&'*+-.^_`|~"
TOKEN_PATTERN = re.compile(rf"[{re.escape(RFC9110_5_6_2_TOKEN_SPECIALS)}\w]+")
