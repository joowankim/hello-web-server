import tempfile


class FakeSocket:
    def __init__(self, data: bytes):
        self.tmp = tempfile.TemporaryFile()
        if data:
            self.tmp.write(data)
            self.tmp.flush()
            self.tmp.seek(0)

    def fileno(self) -> int:
        return self.tmp.fileno()

    def recv(self, length: int | None = None) -> bytes:
        return self.tmp.read(length)

    def send(self, data: bytes) -> None:
        self.tmp.write(data)
        self.tmp.flush()

    def seek(self, offset: int, whence: int = 0) -> None:
        self.tmp.seek(offset, whence)
