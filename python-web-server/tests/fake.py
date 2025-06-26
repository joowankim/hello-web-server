import tempfile
from collections.abc import Iterable


class FakeSocket:
    def __init__(self, data: bytes | Iterable[bytes]):
        if isinstance(data, bytes):
            self.tmp = tempfile.TemporaryFile()
            self.tmp.write(data)
            self.tmp.flush()
            self.tmp.seek(0)
        else:
            self.iter = iter(data)

    def recv(self, length: int | None = None) -> bytes:
        if hasattr(self, "tmp"):
            return self.tmp.read(length)
        elif hasattr(self, "iter"):
            if not self.iter:
                return b""
            try:
                return next(self.iter)
            except StopIteration:
                self.iter = None
                return b""
        else:
            return b""
