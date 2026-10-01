import os

from .common import (
    read_json_stdin,
    git_info,
    git_diff_stat,
    detect_env,
    short_path,
    fmt_tokens,
    context_color,
    progress_bar,
    model_name,
    detect_cli,
    get_nested,
    num,
    load_session_context,
    save_session_context,
)

from .colors import (
    BOLD,
    CYAN,
    BLUE,
    GREEN,
    GRAY,
    YELLOW,
    PURPLE,
    RESET,
)
from .config import load_config, DEFAULT_ORDER, I18N
from .quota import render_quota_parts


def render_main(data=None, cli=None):
    if data is None:
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
        data.get("agent_state")
        or data.get("state")
        or data.get("status")
        or ""
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

    cache_read = (
        context.get("cache_read_input_tokens")
        or context.get("cache_read_tokens")
        or data.get("cache_read_input_tokens")
        or get_nested(data, ("tokens", "cache_read"))
        or get_nested(data, ("usage", "cache_read_input_tokens"))
        or get_nested(data, ("usage", "prompt_tokens_details", "cached_tokens"))
        or get_nested(data, ("tokens", "cached"))
        or data.get("cached_content_token_count")
        or 0
    )
    cache_read = num(cache_read, 0)

    session_key = (
        data.get("session_id")
        or data.get("sessionId")
        or data.get("conversation_id")
        or (f"cwd:{os.path.normcase(os.path.abspath(cwd))}" if cwd else "")
    )

    cached = load_session_context(session_key) if session_key else None

    # 判断当前原始 payload 中是否包含实际非零的 Token 数据
    raw_token_count = (
        num(context.get("total_input_tokens"), 0)
        + num(context.get("input_tokens"), 0)
        + num(context.get("total_output_tokens"), 0)
        + num(context.get("output_tokens"), 0)
        + num(data.get("input_tokens"), 0)
        + num(data.get("output_tokens"), 0)
        + num(get_nested(data, ("tokens", "input")), 0)
        + num(get_nested(data, ("tokens", "output")), 0)
        + num(get_nested(data, ("usage", "input_tokens")), 0)
        + num(get_nested(data, ("usage", "output_tokens")), 0)
        + cache_read
    )
    raw_has_tokens = raw_token_count > 0

    if cached:
        if num(input_tokens, 0) == 0 and cached.get("input_tokens"):
            input_tokens = cached["input_tokens"]
        if num(output_tokens, 0) == 0 and cached.get("output_tokens"):
            output_tokens = cached["output_tokens"]
        if cache_read == 0 and cached.get("cache_read"):
            cache_read = num(cached["cache_read"], 0)
        if used == 0 and cached.get("used"):
            used = num(cached["used"], 0)
        if total_cost is None and cached.get("cost") is not None:
            total_cost = cached["cost"]

    if session_key and raw_has_tokens:
        save_session_context(
            session_key,
            used=used,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=total_cost,
            cache_read=cache_read,
        )

    state_lower = str(agent_state).lower()
    is_streaming = (
        state_lower in ("thinking", "running", "streaming", "busy", "working", "tool_use")
        or bool(cached and not raw_has_tokens)
    )

    if is_streaming:
        if not agent_state or state_lower in ("busy", "working", "tool_use", "streaming"):
            agent_state = "Running"
            state_lower = "running"
    else:
        if not agent_state or state_lower in ("idle", "ready"):
            agent_state = "Idle"
            state_lower = "idle"

    cfg = load_config()
    lang = cfg.get("language", "en")
    order = cfg.get("order", DEFAULT_ORDER)
    modules_enabled = cfg.get("modules", {})

    module_parts = {}
    module_parts["model"] = f"{BOLD}{CYAN}{model}{RESET}"

    if agent_state:
        state_str = str(agent_state).strip()
        if state_lower in ("thinking", "running", "streaming", "busy", "working", "tool_use"):
            state_color = CYAN
            if state_lower in ("busy", "working", "tool_use"):
                state_str = "Running"
        elif state_lower == "auth":
            state_color = YELLOW
        else:
            state_color = GRAY
            if state_lower == "idle":
                state_str = "Idle"

        state_display = state_str
        if state_str.lower() in ("idle", "ready"):
            state_display = I18N.get(lang, {}).get("idle", "Idle")
        elif state_str.lower() in ("running", "working", "busy", "streaming"):
            state_display = I18N.get(lang, {}).get("running", "Running")
        elif state_str.lower() == "thinking":
            state_display = I18N.get(lang, {}).get("thinking", "Thinking")

        module_parts["state"] = f"{state_color}{state_display}{RESET}"

    env_name = detect_env(cwd)
    if env_name:
        module_parts["env"] = f"{PURPLE}{env_name}{RESET}"

    git = git_info(cwd)
    if git:
        module_parts["git"] = f"{GREEN}{git}{RESET}"

    git_stat = git_diff_stat(cwd)
    if git_stat:
        module_parts["git_stat"] = git_stat

    ctx_label = I18N.get(lang, {}).get("ctx", "ctx")
    module_parts["context"] = (
        f"{ctx_label} "
        f"{progress_bar(used)} "
        f"{context_color(used)}"
        f"{used:.0f}%"
        f"{RESET}"
    )

    token_suffix = "…" if is_streaming else ""
    module_parts["tokens"] = (
        f"{BLUE}"
        f"↑{fmt_tokens(input_tokens)} "
        f"↓{fmt_tokens(output_tokens)}{token_suffix}"
        f"{RESET}"
    )

    if cache_read > 0:
        total_prompt = max(num(input_tokens, 0), cache_read)
        cache_label = I18N.get(lang, {}).get("cache", "cache")
        if total_prompt > 0:
            cache_pct = round((cache_read / total_prompt) * 100)
            cache_pct = max(0, min(100, cache_pct))
            module_parts["cache"] = f"{CYAN}⚡{cache_label} {cache_pct}% ({fmt_tokens(cache_read)}){RESET}"
        else:
            module_parts["cache"] = f"{CYAN}⚡{cache_label} {fmt_tokens(cache_read)}{RESET}"

    if quota_parts:
        module_parts["quota"] = " │ ".join(quota_parts)

    if total_cost is not None:
        try:
            cost_text = f"${float(total_cost):.2f}"
        except Exception:
            cost_text = "$?"
        module_parts["cost"] = f"{GREEN}{cost_text}{RESET}"

    if cwd:
        module_parts["cwd"] = f"{GRAY}{short_path(cwd)}{RESET}"

    parts = []
    for item in order:
        if modules_enabled.get(item, True) and item in module_parts:
            parts.append(module_parts[item])

    print(
        " │ ".join(parts),
        flush=True,
    )