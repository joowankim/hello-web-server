import io
import tempfile
from typing import IO


class FakeSocket:
    def __init__(self, data: io.BytesIO):
        self.tmp = tempfile.TemporaryFile()
        if data:
            self.tmp.write(data.getvalue())
            self.tmp.flush()
            self.tmp.seek(0)

    def fileno(self) -> int:
        return self.tmp.fileno()

    def recv(self, length: int | None = None) -> bytes:
        return self.tmp.read(length)

    def recv_into(self, buf: IO[bytes], length: int) -> int:
        tmp_buffer = self.tmp.read(length)
        v = len(tmp_buffer)
        for i, c in enumerate(tmp_buffer):
            buf[i] = c
        return v

    def send(self, data: IO[bytes]) -> None:
        self.tmp.write(data)
        self.tmp.flush()

    def seek(self, offset: int, whence: int = 0) -> None:
        self.tmp.seek(offset, whence)
