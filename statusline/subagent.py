import json

from .common import (
    read_json_stdin,
    fmt_tokens,
    num,
    context_color,
    progress_bar,
    get_nested,
    detect_cli,
)

from .colors import (
    CYAN,
    BLUE,
    GREEN,
    GRAY,
    RESET,
)


def task_model(task, cli=None):
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
    return (
        task.get("description")
        or task.get("prompt")
        or task.get("content")
        or task.get("subject")
        or task.get("title")
        or ""
    )


def render_subagent(cli=None):
    data = read_json_stdin()
    active_cli = detect_cli(data, explicit_cli=cli)

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

        model = task_model(task, cli=active_cli)
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

        pieces = [
            f"{CYAN}↳ {model}{RESET}",
            f"{GREEN}{name}{RESET}",
        ]

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

        content_out = (
            " │ ".join(pieces)
        )

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