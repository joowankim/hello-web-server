import io
from collections.abc import Sequence
from typing import IO


class WSGIErrorStream(io.RawIOBase):
    def __init__(self, sub_streams: list[IO[str]]):
        # There is no public __init__ method for RawIOBase so
        # we don't need to call super() in the __init__ method.
        # pylint: disable=super-init-not-called
        self.streams = sub_streams

    def write(self, data: str) -> None:
        for stream in self.streams:
            try:
                stream.write(data)
            except UnicodeError:
                stream.write(data.encode("UTF-8"))

    def flush(self) -> None:
        for stream in self.streams:
            stream.flush()

    def writelines(self, seq: Sequence[str]) -> None:
        for stream in self.streams:
            for line in seq:
                try:
                    stream.write(line)
                except UnicodeError:
                    stream.write(line.encode("UTF-8"))
