import enum


class TransferEncoding(enum.StrEnum):
    IDENTITY = enum.auto()
    CHUNKED = enum.auto()
    COMPRESS = enum.auto()
    DEFLATE = enum.auto()
    GZIP = enum.auto()
