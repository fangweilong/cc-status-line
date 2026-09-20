"""Quota and rate limit detection for official OAuth sessions (5h, 7d, 1m, etc.)."""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from .colors import GREEN, RED, RESET, YELLOW
from .common import num

BUCKET_ORDER = {"5h": 1, "1d": 2, "7d": 3, "1m": 4}


def normalize_bucket_label(key, reset_seconds=None):
    """将配额或速率限制项映射为标准标识（5h、7d、1m、1d等）。"""
    k = str(key).lower().replace("-", "_").replace(" ", "_")
    if "5h" in k or "five_hour" in k or "5_hour" in k or "5hour" in k:
        return "5h"
    if "7d" in k or "seven_day" in k or "7_day" in k or "7day" in k or "week" in k:
        return "7d"
    if "1m" in k or "month" in k or "30d" in k or "monthly" in k:
        return "1m"
    if "1d" in k or "daily" in k or "day" in k:
        return "1d"

    if reset_seconds is not None and reset_seconds > 0:
        if reset_seconds <= 21600:
            return "5h"
        if reset_seconds <= 90000:
            return "1d"
        if reset_seconds <= 691200:
            return "7d"
        return "1m"

    return key or "quota"


def is_official_oauth(data, cli=None):
    """判断当前会话是否为官方 OAuth（支持 Claude Code rate_limits 与 Antigravity quota）。"""
    if cli == "claude" and os.environ.get("ANTHROPIC_API_KEY"):
        return False
    if cli == "antigravity" and (
        os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    ):
        return False
    if cli == "codex" and os.environ.get("OPENAI_API_KEY"):
        return False

    # Claude Code OAuth 特征：携带 rate_limits
    if data.get("rate_limits"):
        return True

    # Antigravity CLI 特征：携带 quota
    if data.get("quota"):
        return True

    # 显式声明的鉴权类型
    auth = data.get("auth") or {}
    if isinstance(auth, dict):
        auth_type = str(auth.get("type") or auth.get("auth_type") or "").lower()
        if "oauth" in auth_type or "google" in auth_type:
            return True

    auth_type = str(
        data.get("auth_type")
        or data.get("account_type")
        or ""
    ).lower()
    if "oauth" in auth_type or "google" in auth_type:
        return True

    # 本地凭据文件检查（仅在 Antigravity 模式生效）
    if cli == "antigravity":
        home = Path.home()
        oauth_paths = (
            home / ".gemini" / "oauth_creds.json",
            home / ".gemini" / "google_accounts.json",
            home / ".antigravity" / "oauth_creds.json",
        )
        for p in oauth_paths:
            try:
                if p.is_file() and p.stat().st_size > 0:
                    return True
            except Exception:
                pass

    return False


def get_cached_quota():
    """读取本地配额缓存文件（当 payload 中未携带时降级读取）。"""
    home = Path.home()
    cache_paths = (
        home / ".antigravity" / "quota-cache.json",
        home / ".gemini" / "antigravity-cli" / "quota-cache.json",
        home / ".gemini" / "quota-cache.json",
    )
    for p in cache_paths:
        try:
            if p.is_file() and p.stat().st_size > 0:
                with open(p, "r", encoding="utf-8") as f:
                    cdata = json.load(f)
                    if isinstance(cdata, dict):
                        return cdata.get("quota") or cdata
        except Exception:
            pass
    return None


def parse_reset_time(value):
    """统一解析重置时间（支持时间戳或 ISO 字符串），返回剩余秒数。"""
    if value is None:
        return None

    try:
        val_f = float(value)
        if val_f > 1_000_000_000:
            diff = val_f - time.time()
            return max(0, int(diff))
        return max(0, int(val_f))
    except (ValueError, TypeError):
        pass

    try:
        ts = str(value).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts)
        now = datetime.now(timezone.utc)
        diff = (dt - now).total_seconds()
        return max(0, int(diff))
    except Exception:
        return None


def fmt_duration(seconds):
    """格式化重置倒计时（例如 1h 21m、5d 2h、45m、30s）。"""
    if seconds is None:
        return ""

    try:
        s = int(seconds)
    except Exception:
        return ""

    if s <= 0:
        return ""

    days = s // 86400
    hours = (s % 86400) // 3600
    minutes = (s % 3600) // 60

    if days > 0:
        return f"{days}d {hours}h" if hours > 0 else f"{days}d"
    if hours > 0:
        return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
    if minutes > 0:
        return f"{minutes}m"
    return f"{s}s"


def quota_color(pct):
    """根据剩余额度百分比着色：充足为绿，警戒为黄，即将耗尽为红。"""
    if pct >= 50:
        return GREEN
    if pct >= 20:
        return YELLOW
    return RED


def extract_pct(item):
    """从项中提取剩余百分比（0-100）。"""
    fraction = item.get("remaining_fraction")
    if fraction is not None:
        val = num(fraction, -1)
        if 0 <= val <= 1.0:
            return val * 100
        if val > 1.0:
            return val

    rem_pct = item.get("remaining_percentage") or item.get("remainingPercentage")
    if rem_pct is not None:
        return num(rem_pct)

    used_pct = item.get("used_percentage") or item.get("usedPercentage")
    if used_pct is not None:
        return max(0.0, 100.0 - num(used_pct))

    return None


def render_quota_parts(data, active_model="", cli=None):
    """渲染官方 OAuth 配额（5h、7d、1m等），按当前模型匹配并对周期窗口去重。"""
    if not is_official_oauth(data, cli=cli):
        return []

    model_str = str(active_model or "").lower()
    is_gemini = "gemini" in model_str
    is_3p = any(x in model_str for x in ("claude", "gpt", "opus", "sonnet", "haiku"))

    raw_buckets = []

    # 1. Claude Code rate_limits (five_hour, seven_day 等)
    rate_limits = data.get("rate_limits")
    if isinstance(rate_limits, dict) and rate_limits:
        for raw_key, item in rate_limits.items():
            if isinstance(item, dict):
                raw_buckets.append((raw_key, item))

    # 2. Antigravity CLI quota
    quota_data = data.get("quota") or (get_cached_quota() if cli == "antigravity" else None)
    if isinstance(quota_data, dict) and quota_data:
        # 结构 A: 包含 groups 列表
        if "groups" in quota_data and isinstance(quota_data["groups"], list):
            matched_group = None
            fallback_group = None
            for g in quota_data["groups"]:
                if not isinstance(g, dict):
                    continue
                if fallback_group is None:
                    fallback_group = g
                g_name = str(g.get("name") or "").lower()
                g_desc = str(g.get("description") or "").lower()

                if is_gemini and ("gemini" in g_name or "gemini" in g_desc):
                    matched_group = g
                    break
                if is_3p and any(x in g_name or x in g_desc for x in ("claude", "gpt", "3p")):
                    matched_group = g
                    break

            target_group = matched_group or fallback_group
            if target_group and isinstance(target_group.get("buckets"), list):
                for b in target_group["buckets"]:
                    if isinstance(b, dict):
                        raw_buckets.append((b.get("id") or b.get("window") or "", b))

        # 结构 B: 单项直接配额
        elif "remaining_fraction" in quota_data or "remaining_percentage" in quota_data:
            raw_buckets.append(("quota", quota_data))

        # 结构 C: 扁平字典或嵌套在 models/buckets/quotas
        else:
            q_dict = quota_data
            for subkey in ("models", "buckets", "quotas"):
                if isinstance(quota_data.get(subkey), dict):
                    q_dict = quota_data[subkey]
                    break

            for k, v in q_dict.items():
                if isinstance(v, dict):
                    raw_buckets.append((k, v))

    if not raw_buckets:
        return []

    # 按 label（5h、7d、1m等）严格去重，优先选取与当前模型相关的桶
    by_label = {}

    for key, item in raw_buckets:
        reset_sec = parse_reset_time(
            item.get("reset_in_seconds") or item.get("reset_time") or item.get("resets_at")
        )
        window = item.get("window") or key
        label = normalize_bucket_label(window, reset_sec)
        pct = extract_pct(item)
        if pct is None:
            continue

        key_lower = str(key).lower()
        score = 0
        if is_gemini and "gemini" in key_lower:
            score += 10
        elif is_3p and any(x in key_lower for x in ("3p", "claude", "gpt")):
            score += 10
        elif not is_gemini and not is_3p:
            score += 1

        existing = by_label.get(label)
        if existing is None or score > existing[0] or (score == existing[0] and pct < existing[4]):
            dur_str = fmt_duration(reset_sec) if reset_sec is not None else ""
            by_label[label] = (score, item, reset_sec, dur_str, pct)

    sorted_labels = sorted(by_label.keys(), key=lambda l: BUCKET_ORDER.get(l, 99))
    result = []
    for l in sorted_labels:
        _, _, _, dur_str, pct = by_label[l]
        color = quota_color(pct)
        reset_part = f" · {dur_str}" if dur_str else ""
        result.append(f"{color}{l} {pct:.0f}%{reset_part}{RESET}")

    return result
