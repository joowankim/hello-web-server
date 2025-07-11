import glob
import os

import pytest

from tests.http import treq

dirname = os.path.dirname(__file__)
reqdir = os.path.join(dirname, "requests", "valid")
httpfiles = glob.glob(os.path.join(reqdir, "*.http"))


@pytest.mark.parametrize("fname", httpfiles)
def test_http_parser(fname):
    env = treq.load_py(os.path.splitext(fname)[0] + ".py")

    expect = env["request"]
    cfg = env["cfg"]
    req = treq.request(fname, expect)

    for case in req.gen_cases(cfg):
        case[0](*case[1:])
