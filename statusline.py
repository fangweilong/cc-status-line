#!/usr/bin/env python3
"""Claude Code status line entry point.

Claude Code 调用本脚本时必须显式传入模式参数，配置中不可省略：

    statusLine.command          → statusline.py main
    subagentStatusLine.command  → statusline.py subagent
"""

import sys

from statusline.colors import BOLD, GRAY, RED, RESET, YELLOW
from statusline.main import render_main
from statusline.subagent import render_subagent

MODES = ("main", "subagent")


def error_line(message, hint=""):
    """在状态栏位置输出一行可见的错误提示。

    statusline 没有 stderr 通道，错误必须写到 stdout 才能被看到。
    """
    parts = [
        f"{BOLD}{RED}⚠ statusline: {message}{RESET}",
    ]

    if hint:
        parts.append(f"{YELLOW}{hint}{RESET}")

    parts.append(f"{GRAY}statusline.py <main|subagent>{RESET}")

    print(" │ ".join(parts), flush=True)


def main():
    if len(sys.argv) < 2:
        error_line(
            "missing mode argument",
            "check your settings.json",
        )
        return 1

    mode = sys.argv[1].lower()

    if mode not in MODES:
        error_line(
            f"unknown mode {sys.argv[1]!r}",
            "expected main or subagent",
        )
        return 1

    try:
        if mode == "subagent":
            render_subagent()
        else:
            render_main()

    except Exception as exc:
        error_line(
            f"{type(exc).__name__}: {exc}",
            "render failed",
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
