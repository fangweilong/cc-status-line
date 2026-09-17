from .common import (
    read_json_stdin,
    git_info,
    short_path,
    fmt_tokens,
    context_color,
    progress_bar,
    model_name,
    num,
)

from .colors import (
    BOLD,
    CYAN,
    BLUE,
    GREEN,
    GRAY,
    RESET,
)


def render_main():
    data = read_json_stdin()

    workspace = data.get("workspace") or {}

    cwd = (
        workspace.get("current_dir")
        or data.get("cwd")
        or ""
    )

    context = data.get("context_window") or {}

    used = num(
        context.get("used_percentage"),
        0,
    )

    cost = data.get("cost") or {}

    total_cost = cost.get(
        "total_cost_usd"
    )

    try:
        cost_text = (
            f"${float(total_cost):.2f}"
            if total_cost is not None
            else "$?"
        )

    except Exception:
        cost_text = "$?"

    input_tokens = (
        context.get("total_input_tokens")
        or context.get("input_tokens")
        or data.get("input_tokens")
    )

    output_tokens = (
        context.get("total_output_tokens")
        or context.get("output_tokens")
        or data.get("output_tokens")
    )

    parts = [
        f"{BOLD}"
        f"{CYAN}"
        f"{model_name(data)}"
        f"{RESET}"
    ]

    git = git_info(cwd)

    if git:
        parts.append(
            f"{GREEN}{git}{RESET}"
        )

    parts.append(
        f"ctx "
        f"{progress_bar(used)} "
        f"{context_color(used)}"
        f"{used:.0f}%"
        f"{RESET}"
    )

    if (
        input_tokens is not None
        or output_tokens is not None
    ):
        parts.append(
            f"{BLUE}"
            f"↑{fmt_tokens(input_tokens)} "
            f"↓{fmt_tokens(output_tokens)}"
            f"{RESET}"
        )

    parts.append(
        f"{GREEN}{cost_text}{RESET}"
    )

    if cwd:
        parts.append(
            f"{GRAY}"
            f"{short_path(cwd)}"
            f"{RESET}"
        )

    print(
        " │ ".join(parts),
        flush=True,
    )