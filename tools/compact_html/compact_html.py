#!/bin/env python3

import sys

from sdk.common.utils.string_utils import compact_html


def convert(in_path, out_path):
    with open(in_path) as f:
        html = compact_html(f.read())
        with open(out_path, "w") as fw:
            fw.write(html)


if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2])

    """$ ./compact_html.py in_file.html out_file.html"""
