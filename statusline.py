#!/usr/bin/env python3

import sys

from statusline.main import render_main
from statusline.subagent import render_subagent


def main():
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "main"

    if mode == "subagent":
        render_subagent()
    else:
        render_main()


if __name__ == "__main__":
    main()