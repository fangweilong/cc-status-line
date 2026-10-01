"""Configuration management and TUI wizard for cc-status-line."""

import json
import os
import sys
from pathlib import Path

from .colors import BOLD, CYAN, BLUE, GREEN, GRAY, YELLOW, RED, RESET
from .common import context_color, progress_bar, short_path

DEFAULT_ORDER = [
    "model",
    "state",
    "git",
    "context",
    "tokens",
    "quota",
    "cost",
    "cwd",
]

DEFAULT_CONFIG = {
    "language": "en",
    "order": list(DEFAULT_ORDER),
    "modules": {
        "model": True,
        "state": True,
        "git": True,
        "context": True,
        "tokens": True,
        "quota": True,
        "cost": True,
        "cwd": True,
    },
}

MODULE_META = {
    "model": {
        "en": "Model Identifier",
        "zh": "模型标识",
    },
    "state": {
        "en": "Agent State (Idle / Running)",
        "zh": "运行状态 (就绪 / 运行中)",
    },
    "git": {
        "en": "Git Branch & Status (✓/●)",
        "zh": "Git 分支与状态 (✓/●)",
    },
    "context": {
        "en": "Context Usage Bar (%)",
        "zh": "上下文用量进度条 (%)",
    },
    "tokens": {
        "en": "Token Counter (↑in ↓out)",
        "zh": "Token 计数 (↑输入 ↓输出)",
    },
    "quota": {
        "en": "OAuth Quota (5h / 7d)",
        "zh": "OAuth 配额 (5h / 7d 周期限额)",
    },
    "cost": {
        "en": "Session Cost ($)",
        "zh": "会话花费 ($)",
    },
    "cwd": {
        "en": "Workspace Path",
        "zh": "工作区路径",
    },
}

I18N = {
    "en": {
        "idle": "Idle",
        "running": "Running",
        "thinking": "Thinking",
        "ctx": "ctx",
    },
    "zh": {
        "idle": "就绪",
        "running": "运行中",
        "thinking": "思考中",
        "ctx": "上下文",
    },
}


def get_config_path():
    """返回配置文件的绝对路径。"""
    return Path.home() / ".config" / "cc-status-line" / "config.json"


def load_config():
    """读取用户自定义配置，不存在或异常时回退到默认值。"""
    config_file = get_config_path()
    cfg = {
        "language": DEFAULT_CONFIG["language"],
        "order": list(DEFAULT_CONFIG["order"]),
        "modules": dict(DEFAULT_CONFIG["modules"]),
    }

    if not config_file.is_file():
        return cfg

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            if data.get("language") in ("en", "zh"):
                cfg["language"] = data["language"]

            if isinstance(data.get("order"), list) and data["order"]:
                valid_order = [x for x in data["order"] if x in DEFAULT_ORDER]
                for x in DEFAULT_ORDER:
                    if x not in valid_order:
                        valid_order.append(x)
                cfg["order"] = valid_order

            if isinstance(data.get("modules"), dict):
                for k in DEFAULT_CONFIG["modules"]:
                    if k in data["modules"]:
                        cfg["modules"][k] = bool(data["modules"][k])

    except Exception:
        pass

    return cfg


def save_config(cfg):
    """保存配置到用户目录。"""
    config_file = get_config_path()
    try:
        config_file.parent.mkdir(parents=True, exist_ok=True)
        tmp_file = config_file.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        tmp_file.replace(config_file)
        return True
    except Exception:
        return False


def render_preview(cfg):
    """根据当前配置生成终端预览行。"""
    lang = cfg.get("language", "en")
    order = cfg.get("order", DEFAULT_ORDER)
    modules_enabled = cfg.get("modules", {})

    state_str = I18N[lang]["idle"]
    ctx_label = I18N[lang]["ctx"]

    sample_parts = {
        "model": f"{BOLD}{CYAN}Opus 5{RESET}",
        "state": f"{GRAY}{state_str}{RESET}",
        "git": f"{GREEN}main ✓{RESET}",
        "context": f"{ctx_label} {progress_bar(42)} {context_color(42)}42%{RESET}",
        "tokens": f"{BLUE}↑15.0k ↓3.2k{RESET}",
        "quota": f"{GREEN}5h 76% · 2h 15m{RESET}",
        "cost": f"{GREEN}$0.37{RESET}",
        "cwd": f"{GRAY}~/Codes/project{RESET}",
    }

    active_parts = []
    for item in order:
        if modules_enabled.get(item, True) and item in sample_parts:
            active_parts.append(sample_parts[item])

    return " │ ".join(active_parts)


def _get_key_windows():
    import msvcrt

    ch = msvcrt.getch()
    if ch in (b"\x00", b"\xe0"):
        ch2 = msvcrt.getch()
        if ch2 == b"H":
            return "UP"
        if ch2 == b"P":
            return "DOWN"
        if ch2 == b"K":
            return "LEFT"
        if ch2 == b"M":
            return "RIGHT"
        return "UNKNOWN"
    if ch in (b"\r", b"\n"):
        return "ENTER"
    if ch == b" ":
        return "SPACE"
    if ch == b"\t":
        return "TAB"
    if ch in (b"q", b"Q", b"\x1b"):
        return "QUIT"
    if ch in (b"+", b"=", b"k", b"K"):
        return "MOVE_UP"
    if ch in (b"-", b"_", b"j", b"J"):
        return "MOVE_DOWN"
    if ch in (b"l", b"L"):
        return "LANG"

    return "UNKNOWN"


def _get_key_unix():
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            ch2 = sys.stdin.read(1)
            if ch2 == "[":
                ch3 = sys.stdin.read(1)
                if ch3 == "A":
                    return "UP"
                if ch3 == "B":
                    return "DOWN"
                if ch3 == "C":
                    return "RIGHT"
                if ch3 == "D":
                    return "LEFT"
            return "QUIT"
        if ch in ("\r", "\n"):
            return "ENTER"
        if ch == " ":
            return "SPACE"
        if ch == "\t":
            return "TAB"
        if ch in ("q", "Q"):
            return "QUIT"
        if ch in ("+", "=", "k", "K"):
            return "MOVE_UP"
        if ch in ("-", "_", "j", "J"):
            return "MOVE_DOWN"
        if ch in ("l", "L"):
            return "LANG"
        return "UNKNOWN"
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def get_key():
    """跨平台捕获单个按键。"""
    try:
        return _get_key_windows()
    except ImportError:
        return _get_key_unix()


def run_tui():
    """运行终端交互配置向导。"""
    if not sys.stdin.isatty():
        cfg = load_config()
        print(json.dumps(cfg, indent=2, ensure_ascii=False))
        return 0

    cfg = load_config()
    selected_idx = 0

    # 隐藏光标
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

    try:
        while True:
            lang = cfg.get("language", "en")
            order = cfg.get("order", list(DEFAULT_ORDER))
            modules = cfg.get("modules", {})

            # 清屏并重置光标
            lines = [
                "\033[H\033[J",
                f"{BOLD}{CYAN}╔════════════════════════════════════════════════════════════════════════════════╗{RESET}",
                f"{BOLD}{CYAN}║                     cc-status-line Configuration Wizard                        ║{RESET}",
                f"{BOLD}{CYAN}║                               终端可视化配置向导                               ║{RESET}",
                f"{BOLD}{CYAN}╚════════════════════════════════════════════════════════════════════════════════╝{RESET}",
                "",
                f"{BOLD}[ Preview / 实时预览 ]:{RESET}",
                f"  {render_preview(cfg)}",
                f"{GRAY}──────────────────────────────────────────────────────────────────────────────────{RESET}",
                "",
                f"  {BOLD}Language / 语言:{RESET}  [ {BOLD}{GREEN}{'中文 (zh)' if lang == 'zh' else 'English (en)'}{RESET} ]  {GRAY}(Press L / Tab to toggle){RESET}",
                "",
                f"  {BOLD}Status Line Modules / 状态行模块排序与开关:{RESET}",
            ]

            for idx, item in enumerate(order):
                enabled = modules.get(item, True)
                box = f"{GREEN}[x]{RESET}" if enabled else f"{GRAY}[ ]{RESET}"
                cursor = f"{BOLD}{CYAN}❯{RESET}" if idx == selected_idx else " "
                meta_desc = MODULE_META.get(item, {}).get(lang, item)
                item_name = f"{BOLD}{item.ljust(8)}{RESET}" if idx == selected_idx else item.ljust(8)

                lines.append(
                    f"  {cursor} {box} {idx + 1}. {item_name}  {GRAY}│{RESET} {meta_desc}"
                )

            lines.extend([
                "",
                f"{GRAY}──────────────────────────────────────────────────────────────────────────────────{RESET}",
                f" {BOLD}Controls / 快捷键:{RESET}",
                f"   {CYAN}↑/↓{RESET}       : Move cursor / 上下移动",
                f"   {CYAN}Space{RESET}     : Toggle enabled / 启用或停用模块",
                f"   {CYAN}+ / -{RESET}     : Move module up/down / 调整模块前后顺序 (J/K)",
                f"   {CYAN}L / Tab{RESET}   : Switch language / 切换语言 (en/zh)",
                f"   {GREEN}Enter{RESET}     : Save and apply / 保存并应用配置",
                f"   {YELLOW}Q / Esc{RESET}   : Exit without saving / 放弃修改退出",
            ])

            sys.stdout.write("\n".join(lines) + "\n")
            sys.stdout.flush()

            key = get_key()

            if key == "QUIT":
                sys.stdout.write("\nCanceled.\n")
                sys.stdout.flush()
                return 0

            elif key == "UP":
                selected_idx = (selected_idx - 1) % len(order)

            elif key == "DOWN":
                selected_idx = (selected_idx + 1) % len(order)

            elif key == "SPACE":
                cur_item = order[selected_idx]
                modules[cur_item] = not modules.get(cur_item, True)

            elif key in ("MOVE_UP",):
                if selected_idx > 0:
                    order[selected_idx], order[selected_idx - 1] = (
                        order[selected_idx - 1],
                        order[selected_idx],
                    )
                    selected_idx -= 1

            elif key in ("MOVE_DOWN",):
                if selected_idx < len(order) - 1:
                    order[selected_idx], order[selected_idx + 1] = (
                        order[selected_idx + 1],
                        order[selected_idx],
                    )
                    selected_idx += 1

            elif key in ("LANG", "TAB"):
                cfg["language"] = "zh" if lang == "en" else "en"

            elif key == "ENTER":
                save_config(cfg)
                saved_lang = cfg.get("language", "en")
                msg = "配置已保存至" if saved_lang == "zh" else "Configuration saved to"
                sys.stdout.write(f"\n{BOLD}{GREEN}✓ {msg} {get_config_path()}{RESET}\n")
                sys.stdout.flush()
                return 0

    finally:
        # 恢复光标
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
