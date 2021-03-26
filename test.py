#! /usr/bin/env python
#
# Developer: YaAlex (yaalex.xyz)

import main
import os
import urllib.request as rq


# const
test_kernel = "https://raw.githubusercontent.com/YaAlex3/patcher-files/main/kernel"
kernel_fn = './kernel'
out_fn = f"{kernel_fn}-p"


def printt(msg):
    print(f"TEST: {msg}")


def download_kernel():
    printt("Downloading test kernel...")
    rq.urlretrieve(test_kernel, kernel_fn)


def fail(message):
    raise SystemExit(f"Test Failed! Error: {message}")


def test():
    if not os.path.isfile(kernel_fn):
        download_kernel()
    # Fail if patch errors
    printt("testing patch()")
    if not main.patch(kernel_fn):
        fail("patch() returned false; error msg above")
    # Fail if out file doesnt exist
    if os.path.isfile(out_fn):
        orig_size = os.path.getsize(kernel_fn)
        p_size = os.path.getsize(out_fn)
        # Fail if sizes aren't equal
        if orig_size != p_size:
            fail("Size mismatch")
    return printt("pass!")


if __name__ == "__main__":
    test()
