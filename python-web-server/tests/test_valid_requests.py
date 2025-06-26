import glob
import os

import pytest

from tests import treq

dirname = os.path.dirname(__file__)
reqdir = os.path.join(dirname, "requests", "valid")
httpfiles = glob.glob(os.path.join(reqdir, "*.http"))


@pytest.mark.parametrize("fname", httpfiles)
def test_http_parser(fname):
    # if fname == "/Users/kimjoowan/projects/hello-web-server/python-web-server/tests/requests/valid/018.http":
    env = treq.load_py(os.path.splitext(fname)[0] + ".py")

    expect = env["request"]
    cfg = env["cfg"]
    req = treq.request(fname, expect)

    print(fname)
    for case in req.gen_cases(cfg):
        print(case[0].description)
        case[0](*case[1:])
