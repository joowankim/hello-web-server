import inspect
import importlib.machinery
import os
import random
import socket
import types
from collections.abc import Generator
from typing import cast

from tests import fake
from web_server.config import MessageConfig
from web_server.http.parser import RequestParser
from web_server.http.reader import SocketReader
from web_server.util import split_request_uri

dirname = os.path.dirname(__file__)
random.seed()


def uri(data):
    ret = {"raw": data}
    parts = split_request_uri(data)
    ret["scheme"] = parts.scheme or ""
    ret["host"] = parts.netloc.rsplit(":", 1)[0] or None
    ret["port"] = parts.port or 80
    ret["path"] = parts.path or ""
    ret["query"] = parts.query or ""
    ret["fragment"] = parts.fragment or ""
    return ret


def load_py(fname):
    module_name = "__config__"
    mod = types.ModuleType(module_name)
    setattr(mod, "uri", uri)
    setattr(mod, "cfg", MessageConfig.default())
    loader = importlib.machinery.SourceFileLoader(module_name, fname)
    loader.exec_module(mod)
    return vars(mod)


class request:
    def __init__(self, fname, expect):
        self.fname = fname
        self.name = os.path.basename(fname)

        self.expect = expect
        if not isinstance(self.expect, list):
            self.expect = [self.expect]

        with open(self.fname, "rb") as handle:
            self.data = handle.read()
        self.data = self.data.replace(b"\n", b"").replace(b"\\r\\n", b"\r\n")
        self.data = (
            self.data.replace(b"\\0", b"\000")
            .replace(b"\\n", b"\n")
            .replace(b"\\t", b"\t")
        )
        if b"\\" in self.data:
            raise AssertionError(
                "Unexpected backslash in test data - only handling HTAB, NUL and CRLF"
            )

    # Functions for sending data to the parser.
    # These functions mock out reading from a
    # socket or other data source that might
    # be used in real life.

    def send_all(self) -> Generator[bytes, None, None]:
        yield self.data

    def send_lines(self) -> Generator[bytes, None, None]:
        lines = self.data
        pos = lines.find(b"\r\n")
        while pos > 0:
            yield lines[: pos + 2]
            lines = lines[pos + 2 :]
            pos = lines.find(b"\r\n")
        if lines:
            yield lines

    def send_bytes(self) -> Generator[bytes, None, None]:
        for d in self.data:
            yield bytes([d])

    def send_random(self) -> Generator[bytes, None, None]:
        maxs = round(len(self.data) / 10)
        read = 0
        while read < len(self.data):
            chunk = random.randint(1, maxs)
            yield self.data[read : read + chunk]
            read += chunk

    def send_special_chunks(self) -> Generator[bytes, None, None]:
        """Meant to test the request line length check.

        Sends the request data in two chunks, one having a
        length of 1 byte, which ensures that no CRLF is included,
        and a second chunk containing the rest of the request data.

        If the request line length check is not done properly,
        testing the ``tests/requests/valid/099.http`` request
        fails with a ``LimitRequestLine`` exception.

        """
        chunk = self.data[:1]
        read = 0
        while read < len(self.data):
            yield self.data[read : read + len(chunk)]
            read += len(chunk)
            chunk = self.data[read:]

    # These functions define the sizes that the
    # read functions will read with.

    def size_all(self):
        return -1

    def size_bytes(self):
        return 1

    def size_small_random(self):
        return random.randint(1, 4)

    def size_random(self):
        return random.randint(1, 4096)

    # Match a body against various ways of reading
    # a message. Pass in the request, expected body
    # and one of the size functions.

    def szread(self, func, sizes):
        sz = sizes()
        data = func(sz)
        if 0 <= sz < len(data):
            raise AssertionError("Read more than %d bytes: %s" % (sz, data))
        return data

    def match_read(self, req, body, sizes):
        data = self.szread(req.body.read, sizes)
        count = 1000
        while body:
            if body[: len(data)] != data:
                raise AssertionError(
                    "Invalid body data read: %r != %r" % (data, body[: len(data)])
                )
            body = body[len(data) :]
            data = self.szread(req.body.read, sizes)
            if not data:
                count -= 1
            if count <= 0:
                raise AssertionError("Unexpected apparent EOF")

        if body:
            raise AssertionError("Failed to read entire body: %r" % body)
        elif data:
            raise AssertionError("Read beyond expected body: %r" % data)
        data = req.body.read(sizes())
        if data:
            raise AssertionError("Read after body finished: %r" % data)

    def match_readline(self, req, body, sizes):
        data = self.szread(req.body.readline, sizes)
        count = 1000
        while body:
            if body[: len(data)] != data:
                raise AssertionError("Invalid data read: %r" % data)
            if b"\n" in data[:-1]:
                raise AssertionError("Embedded new line: %r" % data)
            body = body[len(data) :]
            data = self.szread(req.body.readline, sizes)
            if not data:
                count -= 1
            if count <= 0:
                raise AssertionError("Apparent unexpected EOF")
        if body:
            raise AssertionError("Failed to read entire body: %r" % body)
        elif data:
            raise AssertionError("Read beyond expected body: %r" % data)
        data = req.body.readline(sizes())
        if data:
            raise AssertionError("Read data after body finished: %r" % data)

    def match_readlines(self, req, body, sizes):
        """\
        This skips the sizes checks as we don't implement it.
        """
        data = req.body.readlines()
        for line in data:
            if b"\n" in line[:-1]:
                raise AssertionError("Embedded new line: %r" % line)
            if line != body[: len(line)]:
                raise AssertionError(
                    "Invalid body data read: %r != %r" % (line, body[: len(line)])
                )
            body = body[len(line) :]
        if body:
            raise AssertionError("Failed to read entire body: %r" % body)
        data = req.body.readlines(sizes())
        if data:
            raise AssertionError("Read data after body finished: %r" % data)

    def match_iter(self, req, body, sizes):
        """\
        This skips sizes because there's its not part of the iter api.
        """
        for line in req.body:
            if b"\n" in line[:-1]:
                raise AssertionError("Embedded new line: %r" % line)
            if line != body[: len(line)]:
                raise AssertionError(
                    "Invalid body data read: %r != %r" % (line, body[: len(line)])
                )
            body = body[len(line) :]
        if body:
            raise AssertionError("Failed to read entire body: %r" % body)
        try:
            data = next(iter(req.body))
            raise AssertionError("Read data after body finished: %r" % data)
        except StopIteration:
            pass

    # Construct a series of test cases from the permutations of
    # send, size, and match functions.

    def gen_cases(self, cfg):
        def get_funs(p):
            return [v for k, v in inspect.getmembers(self) if k.startswith(p)]

        senders = get_funs("send_")
        sizers = get_funs("size_")
        matchers = get_funs("match_")
        cfgs = [(mt, sz, sn) for mt in matchers for sz in sizers for sn in senders]

        ret = []
        for mt, sz, sn in cfgs:
            if hasattr(mt, "funcname"):
                mtn = mt.func_name[6:]
                szn = sz.func_name[5:]
                snn = sn.func_name[5:]
            else:
                mtn = mt.__name__[6:]
                szn = sz.__name__[5:]
                snn = sn.__name__[5:]

            def test_req(sn, sz, mt):
                self.check(cfg, sn, sz, mt)

            desc = "%s: MT: %s SZ: %s SN: %s" % (self.name, mtn, szn, snn)
            test_req.description = desc
            ret.append((test_req, sn, sz, mt))
        return ret

    def check(self, cfg, sender, sizer, matcher):
        cases = self.expect[:]
        fake_sock = fake.FakeSocket(sender())
        fake_sock = cast(socket.socket, fake_sock)
        socket_reader = SocketReader(sock=fake_sock, max_chunk=8192)
        p = RequestParser(cfg=cfg, socket_reader=socket_reader)
        parsed_request_idx = -1
        for parsed_request_idx, req in enumerate(p.parse()):
            self.same(req, sizer, matcher, cases.pop(0))
        assert len(self.expect) == parsed_request_idx + 1
        assert not cases

    def same(self, req, sizer, matcher, exp):
        assert req.method == exp["method"]
        assert req.path == exp["uri"]["path"]
        assert req.query == exp["uri"]["query"]
        assert req.fragment == exp["uri"]["fragment"]
        assert req.version == exp["version"]
        assert req.headers == exp["headers"]
        matcher(req, exp["body"], sizer)
        assert req.trailers == exp.get("trailers", [])


class badrequest:
    # FIXME: no good reason why this cannot match what the more extensive mechanism above
    def __init__(self, fname):
        self.fname = fname
        self.name = os.path.basename(fname)

        with open(self.fname) as handle:
            self.data = handle.read()
        self.data = self.data.replace("\n", "").replace("\\r\\n", "\r\n")
        self.data = (
            self.data.replace("\\0", "\000").replace("\\n", "\n").replace("\\t", "\t")
        )
        if "\\" in self.data:
            raise AssertionError(
                "Unexpected backslash in test data - only handling HTAB, NUL and CRLF"
            )
        self.data = self.data.encode("latin1")

    def send(self):
        maxs = round(len(self.data) / 10)
        read = 0
        while read < len(self.data):
            chunk = random.randint(1, maxs)
            yield self.data[read : read + chunk]
            read += chunk

    def check(self, cfg):
        fake_sock = fake.FakeSocket(self.send())
        fake_sock = cast(socket.socket, fake_sock)
        socket_reader = SocketReader(sock=fake_sock, max_chunk=8192)
        p = RequestParser(cfg=cfg, socket_reader=socket_reader)
        # must fully consume iterator, otherwise EOF errors could go unnoticed
        for _ in p.parse():
            pass
