#!/usr/bin/env python3
"""Status line entry point supporting Claude Code, Antigravity CLI, and other CLIs.

Modes:
    statusline.py main [--cli <antigravity|claude|generic>]
    statusline.py subagent [--cli <antigravity|claude|generic>]
    statusline.py agy / antigravity
    statusline.py claude
    statusline.py config / tui
"""

import sys

from statusline.colors import BOLD, GRAY, RED, RESET, YELLOW
from statusline.common import read_json_stdin
from statusline.config import run_tui
from statusline.main import render_main
from statusline.subagent import render_subagent

MODES = (
    "main",
    "subagent",
    "auto",
    "agy",
    "antigravity",
    "antigravitycli",
    "claude",
    "cc",
    "codex",
    "config",
    "tui",
)


def is_subagent_payload(data):
    """检测输入数据是否属于 Subagent 任务列表结构。"""
    if not isinstance(data, dict):
        return False
    return any(
        k in data
        for k in ("tasks", "subagents", "subagent_info", "subagentInfo")
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

    parts.append(f"{GRAY}statusline.py [main|subagent|config] [--cli <name>]{RESET}")

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
    mode, cli = parse_args(sys.argv)

    if mode is not None and mode not in MODES:
        error_line(
            f"unknown mode {mode!r}",
            "expected main, subagent, auto, config, agy, claude, or codex",
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

    if mode in ("config", "tui"):
        return run_tui()

    try:
        # 当未显式指定模式或传 auto 时，通过 stdin payload 结构自动识别
        if mode in (None, "auto"):
            data = read_json_stdin()
            if is_subagent_payload(data):
                render_subagent(data=data, cli=cli)
            else:
                render_main(data=data, cli=cli)
        elif mode == "subagent":
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
