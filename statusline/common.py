import json
import os
import subprocess
from pathlib import Path

from .colors import GREEN, YELLOW, RED, GRAY, RESET


def read_json_stdin():
    try:
        raw = os.read(0, 8 * 1024 * 1024)

        if not raw:
            return {}

        return json.loads(
            raw.decode("utf-8", errors="replace")
        )

    except Exception:
        return {}


def git_command(args, cwd):
    if not cwd:
        return ""

    try:
        return subprocess.check_output(
            ["git", "-C", cwd, *args],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=0.5,
        ).strip()

    except Exception:
        return ""


def git_info(cwd):
    branch = git_command(
        ["branch", "--show-current"],
        cwd,
    )

    if not branch:
        branch = git_command(
            ["rev-parse", "--short", "HEAD"],
            cwd,
        )

    if not branch:
        return ""

    dirty = bool(
        git_command(
            ["status", "--porcelain"],
            cwd,
        )
    )

    marker = (
        f"{YELLOW}●{RESET}"
        if dirty
        else f"{GREEN}✓{RESET}"
    )

    return f"{branch} {marker}"


def short_path(path):
    if not path:
        return ""

    try:
        home = str(Path.home())

        if os.path.normcase(path) == os.path.normcase(home):
            return "~"

        prefix = home + os.sep

        if path.startswith(prefix):
            path = "~" + path[len(home):]

    except Exception:
        pass

    parts = path.replace("\\", "/").split("/")

    if len(parts) > 4:
        return "…/" + "/".join(parts[-3:])

    return path


def num(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def fmt_tokens(value):
    if value is None:
        return "?"

    n = num(value, -1)

    if n < 0:
        return "?"

    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"

    if n >= 1_000:
        return f"{n / 1_000:.1f}k"

    return str(int(n))


def context_color(percent):
    percent = num(percent)

    if percent >= 85:
        return RED

    if percent >= 65:
        return YELLOW

    return GREEN


def progress_bar(percent, width=10):
    percent = max(
        0,
        min(100, num(percent)),
    )

    filled = round(
        percent / 100 * width
    )

    return (
        f"{context_color(percent)}"
        f"{'█' * filled}"
        f"{GRAY}"
        f"{'░' * (width - filled)}"
        f"{context_color(percent)}"
    )


def get_nested(obj, *paths, default=None):
    for path in paths:
        current = obj
        ok = True

        for key in path:
            if (
                isinstance(current, dict)
                and key in current
            ):
                current = current[key]
            else:
                ok = False
                break

        if ok and current is not None:
            return current

    return default


def model_name(data):
    model = data.get("model")

    if isinstance(model, dict):
        return (
            model.get("display_name")
            or model.get("name")
            or model.get("id")
            or "Claude"
        )

    return str(model or "Claude")