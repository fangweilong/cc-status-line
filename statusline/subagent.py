"""Subagent status line rendering for Claude Code and Antigravity CLI."""

import json

from .colors import BLUE, CYAN, GRAY, GREEN, RED, RESET
from .common import (
    context_color,
    detect_cli,
    fmt_tokens,
    get_nested,
    num,
    progress_bar,
    read_json_stdin,
)
from .config import load_config

STATUS_I18N = {
    "en": {
        "completed": "done",
        "done": "done",
        "running": "running",
        "working": "running",
        "in_progress": "running",
        "pending": "pending",
        "failed": "failed",
        "error": "error",
        "idle": "idle",
    },
    "zh": {
        "completed": "已完成",
        "done": "已完成",
        "running": "运行中",
        "working": "运行中",
        "in_progress": "进行中",
        "pending": "等待中",
        "failed": "失败",
        "error": "错误",
        "idle": "空闲",
    },
}

STATUS_COLOR = {
    "completed": GREEN,
    "done": GREEN,
    "running": CYAN,
    "working": CYAN,
    "in_progress": CYAN,
    "pending": GRAY,
    "failed": RED,
    "error": RED,
    "idle": GRAY,
}


def task_model(task, cli=None):
    """Extract subagent model name from task dictionary."""
    model = task.get("model")

    if isinstance(model, dict):
        return (
            model.get("display_name")
            or model.get("name")
            or model.get("id")
            or ("Gemini" if cli == "antigravity" else "Claude")
        )

    if model:
        return str(model)

    if cli == "antigravity":
        return "Gemini"
    if cli == "codex":
        return "Codex"
    return "Claude"


def task_name(task):
    """Extract subagent display name or role."""
    return (
        task.get("name")
        or task.get("role")
        or task.get("type_name")
        or task.get("agent_type")
        or task.get("subagent_type")
        or task.get("type")
        or "agent"
    )


def task_context(task):
    """Extract subagent context window usage percentage."""
    context = task.get("context_window")

    if isinstance(context, dict):
        value = context.get("used_percentage")
        if value is not None:
            return value

    for key in (
        "used_percentage",
        "context_used_percentage",
        "contextPercentage",
    ):
        if key in task:
            return task[key]

    return None


def task_tokens(task):
    """Extract subagent token usage formatted string."""
    tokens = (
        task.get("tokenCount")
        or task.get("token_count")
        or task.get("tokens")
        or get_nested(task, ("usage", "total_tokens"))
        or get_nested(task, ("usage", "totalTokens"))
    )

    if tokens is not None:
        return fmt_tokens(tokens)

    input_tokens = (
        task.get("input_tokens")
        or get_nested(task, ("usage", "input_tokens"))
        or get_nested(task, ("usage", "inputTokens"))
    )

    output_tokens = (
        task.get("output_tokens")
        or get_nested(task, ("usage", "output_tokens"))
        or get_nested(task, ("usage", "outputTokens"))
    )

    if (
        input_tokens is not None
        or output_tokens is not None
    ):
        return (
            f"↑{fmt_tokens(input_tokens or 0)} "
            f"↓{fmt_tokens(output_tokens or 0)}"
        )

    return ""


def task_content(task):
    """Extract subagent task description or prompt."""
    content = (
        task.get("description")
        or task.get("prompt")
        or task.get("content")
        or task.get("subject")
        or task.get("title")
        or ""
    )
    if not content and task.get("role") and task.get("name"):
        content = task.get("role")
    return content or ""


def format_subagent_line(task, cli=None, lang="en"):
    """Format a single subagent task dictionary into a styled statusline string."""
    model = task_model(task, cli=cli)
    name = task_name(task)

    content = (
        task_content(task)
        .replace("\r", " ")
        .replace("\n", " ")
        .strip()
    )

    if len(content) > 70:
        content = content[:67] + "..."

    used = task_context(task)
    tokens = task_tokens(task)
    status = task.get("status")

    pieces = [
        f"{CYAN}↳ {model}{RESET}",
        f"{GREEN}{name}{RESET}",
    ]

    if status:
        status_key = str(status).strip().lower()
        status_text = STATUS_I18N.get(lang, STATUS_I18N["en"]).get(status_key, status)
        status_color = STATUS_COLOR.get(status_key, GRAY)
        pieces.append(f"{status_color}{status_text}{RESET}")

    if used is not None:
        used = num(used, 0)
        pieces.append(
            f"ctx "
            f"{progress_bar(used)} "
            f"{context_color(used)}"
            f"{used:.0f}%"
            f"{RESET}"
        )

    if tokens:
        token_display = (
            tokens
            if (tokens.startswith("↑") or tokens.startswith("↓"))
            else f"↓{tokens}"
        )
        pieces.append(
            f"{BLUE}"
            f"{token_display}"
            f"{RESET}"
        )

    if content:
        pieces.append(
            f"{GRAY}"
            f"{content}"
            f"{RESET}"
        )

    return " │ ".join(pieces)


def render_subagent(data=None, cli=None):
    """Render subagent lines from payload (JSON for Claude Code, ANSI for Antigravity)."""
    if data is None:
        data = read_json_stdin()
    active_cli = detect_cli(data, explicit_cli=cli)
    cfg = load_config()
    lang = cfg.get("language", "en")

    tasks = (
        data.get("tasks")
        or data.get("subagents")
        or get_nested(data, ("subagent_info", "subagents"))
        or get_nested(data, ("subagentInfo", "subagents"))
        or []
    )

    if isinstance(tasks, dict):
        tasks = list(tasks.values())

    for task in tasks:
        if not isinstance(task, dict):
            continue

        task_id = str(
            task.get("id")
            or task.get("conversation_id")
            or task.get("task_id")
            or task.get("session_id")
            or task_name(task)
        )

        content_out = format_subagent_line(task, cli=active_cli, lang=lang)

        if active_cli == "antigravity":
            print(content_out, flush=True)
        else:
            print(
                json.dumps(
                    {
                        "id": task_id,
                        "content": content_out,
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )