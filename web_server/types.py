from types import TracebackType

ExcInfo = tuple[type[BaseException] | None, BaseException | None, TracebackType | None]
