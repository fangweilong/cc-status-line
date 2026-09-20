#!/usr/bin/env python3
"""Status line entry point supporting Claude Code, Antigravity CLI, and other CLIs.

Modes:
    statusline.py main [--cli <antigravity|claude|generic>]
    statusline.py subagent [--cli <antigravity|claude|generic>]
    statusline.py agy / antigravity
    statusline.py claude
"""

import sys

from statusline.colors import BOLD, GRAY, RED, RESET, YELLOW
from statusline.main import render_main
from statusline.subagent import render_subagent

MODES = (
    "main",
    "subagent",
    "agy",
    "antigravity",
    "antigravitycli",
    "claude",
    "cc",
    "codex",
)


def error_line(message, hint=""):
    """在状态栏位置输出一行可见的错误提示。

    statusline 没有 stderr 通道，错误必须写到 stdout 才能被看到。
    """
    parts = [
        f"{BOLD}{RED}⚠ statusline: {message}{RESET}",
    ]

    if hint:
        parts.append(f"{YELLOW}{hint}{RESET}")

    parts.append(f"{GRAY}statusline.py <main|subagent|agy|claude|codex> [--cli <name>]{RESET}")

    print(" │ ".join(parts), flush=True)


def parse_args(argv):
    """解析模式参数及可选的 --cli 选项。"""
    mode = None
    cli = None
    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg.startswith("--cli="):
            cli = arg.split("=", 1)[1].strip()
        elif arg == "--cli" and i + 1 < len(argv):
            i += 1
            cli = argv[i].strip()
        elif not arg.startswith("-") and mode is None:
            mode = arg.lower()
        i += 1
    return mode, cli


def main():
    if len(sys.argv) < 2:
        error_line(
            "missing mode argument",
            "check your settings.json",
        )
        return 1

    mode, cli = parse_args(sys.argv)

    if not mode:
        error_line(
            "missing mode argument",
            "expected main, subagent, agy, claude, or codex",
        )
        return 1

    if mode not in MODES:
        error_line(
            f"unknown mode {mode!r}",
            "expected main, subagent, agy, claude, or codex",
        )
        return 1

    if mode in ("agy", "antigravity", "antigravitycli"):
        mode = "main"
        cli = "antigravity"
    elif mode in ("claude", "cc"):
        mode = "main"
        cli = "claude"
    elif mode == "codex":
        mode = "main"
        cli = "codex"

    try:
        if mode == "subagent":
            render_subagent(cli=cli)
        else:
            render_main(cli=cli)

    except Exception as exc:
        error_line(
            f"{type(exc).__name__}: {exc}",
            "render failed",
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
