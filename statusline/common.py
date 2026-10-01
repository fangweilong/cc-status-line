"""Common utilities, formatting helpers, and environment detection."""

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from .colors import GREEN, YELLOW, RED, GRAY, PURPLE, RESET


def read_json_stdin():
    """读取并解析 stdin 传入的 JSON 数据。

    终端直接交互执行（无管道）时回退到当前工作目录，避免键盘阻塞。
    """
    try:
        if sys.stdin.isatty():
            return {"cwd": os.getcwd()}

        raw = os.read(0, 8 * 1024 * 1024)

        if not raw:
            return {"cwd": os.getcwd()}

        parsed = json.loads(
            raw.decode("utf-8", errors="replace")
        )
        if isinstance(parsed, dict):
            if "cwd" not in parsed and "workspace" not in parsed:
                parsed["cwd"] = os.getcwd()
            return parsed
        return {}

    except Exception:
        return {"cwd": os.getcwd()}


def git_command(args, cwd):
    """Execute a git command in cwd and return stripped stdout."""
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
    """Return current git branch and dirty status marker (✓ or ●)."""
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


def git_diff_stat(cwd):
    """返回 Git 增删行统计（如 +12 -4），无改动或异常时返回空字符串。"""
    if not cwd:
        return ""

    out = git_command(["diff", "HEAD", "--shortstat"], cwd)
    if not out:
        out = git_command(["diff", "--shortstat"], cwd)

    if not out:
        return ""

    ins = 0
    dels = 0
    m_ins = re.search(r"(\d+)\s+insertion", out)
    if m_ins:
        ins = int(m_ins.group(1))
    m_del = re.search(r"(\d+)\s+deletion", out)
    if m_del:
        dels = int(m_del.group(1))

    if ins == 0 and dels == 0:
        return ""

    parts = []
    if ins > 0:
        parts.append(f"{GREEN}+{ins}{RESET}")
    if dels > 0:
        parts.append(f"{RED}-{dels}{RESET}")

    return " ".join(parts)


def detect_env(cwd):
    """检测当前激活的虚拟环境与项目运行时（支持 Python, Node, Go, Rust, Java 等）。"""
    # 优先检测当前进程环境变量（真实激活的运行时环境）
    venv = os.environ.get("VIRTUAL_ENV")
    if venv:
        return f"({Path(venv).name})"

    conda = os.environ.get("CONDA_DEFAULT_ENV")
    if conda:
        return f"conda:{conda}"

    if os.environ.get("REMOTE_CONTAINERS") or os.environ.get("CODESPACES"):
        return "devcontainer"
    if os.environ.get("WSL_DISTRO_NAME"):
        return "wsl"

    if not cwd:
        return ""

    try:
        p = Path(cwd)
        # 检测工作区根目录的 Python 虚拟环境
        for venv_name in (".venv", "venv", "env"):
            if (p / venv_name).is_dir():
                return f"({venv_name})"

        # 检测 Node.js 运行时与包管理器
        for node_ver_file in (".nvmrc", ".node-version"):
            nv = p / node_ver_file
            if nv.is_file():
                try:
                    ver = nv.read_text(encoding="utf-8", errors="replace").strip()
                    if ver:
                        if not ver.startswith("v") and not ver.startswith("node"):
                            ver = f"v{ver}"
                        return f"node:{ver}"
                except Exception:
                    pass

        if (p / "bun.lockb").is_file() or (p / "bun.lock").is_file():
            return "bun"
        if (p / "pnpm-lock.yaml").is_file():
            return "pnpm"
        if (p / "yarn.lock").is_file():
            return "yarn"
        if (p / "package-lock.json").is_file():
            return "npm"
        if (p / "package.json").is_file():
            return "node"

        # 检测 Rust
        if (p / "Cargo.toml").is_file():
            for tc_file in ("rust-toolchain.toml", "rust-toolchain"):
                tc = p / tc_file
                if tc.is_file():
                    try:
                        content = tc.read_text(encoding="utf-8", errors="replace")
                        m = re.search(r'channel\s*=\s*["\']([^"\']+)["\']', content)
                        if m:
                            return f"rust:{m.group(1)}"
                        lines = [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith("#")]
                        if lines:
                            return f"rust:{lines[0]}"
                    except Exception:
                        pass
            return "cargo"

        # 检测 Go
        go_mod = p / "go.mod"
        if go_mod.is_file():
            try:
                content = go_mod.read_text(encoding="utf-8", errors="replace")
                m = re.search(r"^go\s+([0-9.]+)", content, re.MULTILINE)
                if m:
                    return f"go:{m.group(1)}"
            except Exception:
                pass
            return "go"

        # 检测 Java
        if (p / "pom.xml").is_file():
            return "maven"
        if (p / "build.gradle").is_file() or (p / "build.gradle.kts").is_file():
            return "gradle"

        # 检测 Ruby
        for rb_file in (".ruby-version", "Gemfile"):
            if (p / rb_file).is_file():
                if rb_file == ".ruby-version":
                    try:
                        ver = (p / rb_file).read_text(encoding="utf-8", errors="replace").strip()
                        if ver:
                            return f"ruby:{ver}"
                    except Exception:
                        pass
                return "ruby"

        # 检测 Python 项目文件（未建立虚拟环境时）
        if (p / "pyproject.toml").is_file() or (p / "requirements.txt").is_file():
            return "python"

    except Exception:
        pass

    return ""


def short_path(path):
    """Shorten a filesystem path for display, substituting ~ for home directory."""
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
    """Safely cast value to float or return default."""
    try:
        return float(value)
    except Exception:
        return default


def fmt_tokens(value):
    """Format token count into human-readable string (e.g. 1.2k, 3.4M)."""
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
    """Return ANSI color code corresponding to context usage percentage."""
    percent = num(percent)

    if percent >= 85:
        return RED

    if percent >= 65:
        return YELLOW

    return GREEN


def progress_bar(percent, width=10):
    """Render a colored ANSI progress bar for context percentage."""
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
    """Safely retrieve nested dictionary value using fallback key sequences."""
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


def detect_cli(data=None, explicit_cli=None):
    """Detect active CLI environment (antigravity, claude, codex, or generic)."""
    if explicit_cli:
        cli = explicit_cli.lower().strip()
        if cli in ("agy", "antigravity", "antigravitycli", "antigravity-cli"):
            return "antigravity"
        if cli in ("claude", "claudecode", "claude-code", "cc"):
            return "claude"
        if cli in ("codex", "codex-cli", "openai-codex"):
            return "codex"
        return cli

    env_cli = os.environ.get("STATUSLINE_CLI")
    if env_cli:
        return detect_cli(data, explicit_cli=env_cli)

    if not data or not isinstance(data, dict):
        return "claude"

    # 1. Check model identifier
    model_id = ""
    model = data.get("model")
    if isinstance(model, dict):
        model_id = str(
            model.get("id")
            or model.get("name")
            or model.get("display_name")
            or ""
        ).lower()
    elif model:
        model_id = str(model).lower()

    if "claude" in model_id:
        return "claude"
    if "gemini" in model_id:
        return "antigravity"
    if any(x in model_id for x in ("codex", "gpt", "o1", "o3", "o4")):
        return "codex"

    # 2. Antigravity-specific indicators
    product = str(data.get("product") or "").lower()
    if product in ("antigravity", "agy", "gemini"):
        return "antigravity"

    if "quota" in data or "exceeds_200k_tokens" in data:
        return "antigravity"

    # 3. Claude Code-specific indicators
    if "cost" in data or "rate_limits" in data:
        return "claude"

    # 4. Default to claude (preserves original cc-status-line behavior)
    return "claude"


def model_name(data, cli=None):
    """Extract and format model name from input payload."""
    model = data.get("model")

    if isinstance(model, dict):
        name = (
            model.get("display_name")
            or model.get("name")
            or model.get("id")
        )
        if name:
            return str(name)

    if model:
        return str(model)

    if cli == "antigravity":
        return "Gemini"
    if cli == "claude":
        return "Claude"
    if cli == "codex":
        return "Codex"

    return "Agent"


def _session_cache_dir():
    """Return Path to local statusline session cache directory."""
    d = Path(tempfile.gettempdir()) / "cc_statusline"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return d



def load_session_context(session_key, max_age_seconds=86400):
    """读取指定会话的上下文与 Token 缓存，避免 SSE 流式期间数据归零。"""
    if not session_key:
        return None

    try:
        h = hashlib.sha256(
            session_key.encode("utf-8", errors="replace")
        ).hexdigest()[:16]
        cache_file = _session_cache_dir() / f"ctx_{h}.json"
        if not cache_file.is_file():
            return None

        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            if time.time() - data.get("time", 0) <= max_age_seconds:
                return data
    except Exception:
        pass

    return None


def save_session_context(session_key, used, input_tokens, output_tokens, cost=None, cache_read=None):
    """保存当前会话有效的上下文与 Token 统计。"""
    if not session_key:
        return

    try:
        h = hashlib.sha256(
            session_key.encode("utf-8", errors="replace")
        ).hexdigest()[:16]
        cache_file = _session_cache_dir() / f"ctx_{h}.json"
        tmp_file = cache_file.with_suffix(".tmp")

        payload = {
            "used": used,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost,
            "cache_read": cache_read,
            "time": time.time(),
        }

        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        tmp_file.replace(cache_file)
    except Exception:
        pass