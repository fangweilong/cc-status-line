import json

from .common import (
    read_json_stdin,
    fmt_tokens,
    num,
    context_color,
    progress_bar,
    get_nested,
)

from .colors import (
    CYAN,
    BLUE,
    GREEN,
    GRAY,
    RESET,
)


def task_model(task):
    model = task.get("model")

    if isinstance(model, dict):
        return (
            model.get("display_name")
            or model.get("name")
            or model.get("id")
            or "Claude"
        )

    return str(model or "Claude")


def task_name(task):
    return (
        task.get("name")
        or task.get("agent_type")
        or task.get("subagent_type")
        or task.get("type")
        or "agent"
    )


def task_context(task):
    context = task.get(
        "context_window"
    )

    if isinstance(context, dict):
        value = context.get(
            "used_percentage"
        )

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
        or get_nested(
            task,
            ("usage", "total_tokens"),
        )
    )

    if tokens is not None:
        return fmt_tokens(tokens)

    input_tokens = (
        task.get("input_tokens")
        or get_nested(
            task,
            ("usage", "input_tokens"),
        )
    )

    output_tokens = (
        task.get("output_tokens")
        or get_nested(
            task,
            ("usage", "output_tokens"),
        )
    )

    if (
        input_tokens is not None
        or output_tokens is not None
    ):
        return (
            f"↑{fmt_tokens(input_tokens)} "
            f"↓{fmt_tokens(output_tokens)}"
        )

    return ""


def task_content(task):
    return (
        task.get("description")
        or task.get("content")
        or task.get("subject")
        or task.get("title")
        or ""
    )


def render_subagent():
    data = read_json_stdin()

    tasks = (
        data.get("tasks")
        or data.get("subagents")
        or []
    )

    if isinstance(tasks, dict):
        tasks = list(tasks.values())

    for task in tasks:
        if not isinstance(task, dict):
            continue

        task_id = str(
            task.get("id")
            or task.get("task_id")
            or task.get("session_id")
            or task_name(task)
        )

        model = task_model(task)
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
            pieces.append(
                f"{BLUE}"
                f"↓{tokens}"
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