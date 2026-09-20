from .common import (
    read_json_stdin,
    git_info,
    short_path,
    fmt_tokens,
    context_color,
    progress_bar,
    model_name,
    detect_cli,
    get_nested,
    num,
)

from .colors import (
    BOLD,
    CYAN,
    BLUE,
    GREEN,
    GRAY,
    YELLOW,
    RESET,
)
from .quota import render_quota_parts


def render_main(cli=None):
    data = read_json_stdin()
    active_cli = detect_cli(data, explicit_cli=cli)

    workspace = data.get("workspace") or {}

    cwd = (
        workspace.get("current_dir")
        or workspace.get("project_dir")
        or data.get("cwd")
        or ""
    )

    context = data.get("context_window") or {}

    used = num(
        context.get("used_percentage"),
        0,
    )

    model = model_name(data, cli=active_cli)
    agent_state = (
        data.get("agent_state") or data.get("state") or ""
        if active_cli == "antigravity"
        else ""
    )

    cost = data.get("cost") or {}
    total_cost = cost.get("total_cost_usd") if isinstance(cost, dict) else None

    quota_parts = render_quota_parts(data, active_model=model, cli=active_cli)

    input_tokens = (
        context.get("total_input_tokens")
        or context.get("input_tokens")
        or data.get("input_tokens")
        or get_nested(data, ("tokens", "input"))
        or get_nested(data, ("usage", "input_tokens"))
        or 0
    )

    output_tokens = (
        context.get("total_output_tokens")
        or context.get("output_tokens")
        or data.get("output_tokens")
        or get_nested(data, ("tokens", "output"))
        or get_nested(data, ("usage", "output_tokens"))
        or 0
    )

    parts = [
        f"{BOLD}"
        f"{CYAN}"
        f"{model}"
        f"{RESET}"
    ]

    if agent_state:
        state_str = str(agent_state).strip()
        state_lower = state_str.lower()
        if state_lower in ("thinking", "running"):
            state_color = CYAN
        elif state_lower == "auth":
            state_color = YELLOW
        else:
            state_color = GRAY

        parts.append(
            f"{state_color}{state_str}{RESET}"
        )

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

    # 上下文 token 计数始终显示
    parts.append(
        f"{BLUE}"
        f"↑{fmt_tokens(input_tokens)} "
        f"↓{fmt_tokens(output_tokens)}"
        f"{RESET}"
    )

    # 官方 OAuth 额度（5h、7d、1m等）优先显示；否则若有花费则显示花费
    if quota_parts:
        for qp in quota_parts:
            parts.append(qp)
    elif total_cost is not None:
        try:
            cost_text = (
                f"${float(total_cost):.2f}"
            )
        except Exception:
            cost_text = "$?"

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