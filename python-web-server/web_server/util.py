import urllib.parse


def split_request_uri(uri: str) -> urllib.parse.SplitResult:
    if uri.startswith("//"):
        # When the path starts with //, urlsplit considers it as a
        # relative uri while the RFC says we should consider it as abs_path
        # http://www.w3.org/Protocols/rfc2616/rfc2616-sec5.html#sec5.1.2
        # We use temporary dot prefix to workaround this behaviour
        parts = urllib.parse.urlsplit("." + uri)
        return parts._replace(path=parts.path[1:])

    return urllib.parse.urlsplit(uri)


def bytes_to_str(b: bytes) -> str:
    if isinstance(b, str):
        return b
    return str(b, "latin1")
