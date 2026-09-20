# AGENTS.md — Universal AI Agent Installation & Execution Guide

This document is designed for AI Coding Assistants (including **Claude Code**, **Codex CLI**, **Antigravity CLI**, **Cursor**, and others) to read and automatically configure `cc-status-line` on behalf of the user.

---

## 1. Quick Overview

`cc-status-line` is a fast, dependency-free status line written in pure Python 3. It renders:
- **Main Session Status Line**: Model, agent state, Git branch & status (`✓`/`●`), context tokens (`↑` input, `↓` output), official OAuth quotas (`5h`, `7d`, `1m`) or API cost (`$0.XX`), and shortened workspace path.
- **Subagent Status Line**: Formatted JSON (`{"id": "...", "content": "..."}`) for each running subagent.

Entry point: `statusline.py`

---

## 2. Automated Installation & Setup by Target CLI

When the user asks you to configure or install `cc-status-line`, identify the user's active environment and follow the corresponding section below.

### Target A: Claude Code (`cc`)
- **Config file**: `~/.claude/settings.json`
- **Action**:
  1. Determine the absolute path to `statusline.py` using **forward slashes** (e.g. `C:/path/to/cc-status-line/statusline.py`).
  2. Read existing `~/.claude/settings.json` (or create if absent).
  3. Set or update the following keys:
     ```json
     {
       "statusLine": {
         "type": "command",
         "command": "python <ABSOLUTE_PATH>/statusline.py main",
         "padding": 0
       },
       "subagentStatusLine": {
         "type": "command",
         "command": "python <ABSOLUTE_PATH>/statusline.py subagent"
       }
     }
     ```
  4. Ensure `main` and `subagent` parameters are explicitly present at the end of each command.

### Target B: Antigravity CLI (`agy`)
- **Config file**: `~/.gemini/antigravity-cli/settings.json`
- **Action**:
  1. Determine the absolute path to `statusline.py` using forward slashes.
  2. Read or create `~/.gemini/antigravity-cli/settings.json`.
  3. Add or update:
     ```json
     {
       "statusLine": {
         "type": "command",
         "command": "python <ABSOLUTE_PATH>/statusline.py main",
         "enabled": true,
         "padding": 0,
         "stack_with_default": false
       }
     }
     ```
  4. Alternatively, execute inside `agy`: `/statusline python <ABSOLUTE_PATH>/statusline.py main`.

### Target C: OpenAI Codex CLI (`codex`)
- **Config file**: `~/.codex/config.toml` (or `$CODEX_HOME/config.toml`)
- **Action**:
  1. Codex CLI natively configures status lines via built-in item identifiers in `~/.codex/config.toml`.
  2. Read or create `~/.codex/config.toml` and configure the `[tui]` section:
     ```toml
     [tui]
     status_line = [
         "model-with-reasoning",
         "project-root",
         "current-dir",
         "git-branch",
         "five-hour-limit",
         "weekly-limit",
         "context-used",
         "context-window-size",
         "used-tokens"
     ]
     status_line_use_colors = true
     ```
  3. If the user uses a wrapper, tmux, or shell prompt integration with Codex, they can run `cc-status-line` directly:
     ```bash
     python <ABSOLUTE_PATH>/statusline.py codex
     ```

---

## 3. Verification & Testing

Verify that the script runs properly before completing the task:

```bash
# Test main line (Claude)
echo '{"model": "Claude 3.7 Sonnet", "cwd": "."}' | python statusline.py main

# Test main line (Antigravity)
echo '{"product": "antigravity", "tokens": {"input": 1000, "output": 200}}' | python statusline.py agy

# Test main line (Codex)
echo '{"model": "gpt-4o", "cwd": "."}' | python statusline.py codex

# Test subagents
echo '{"subagents": [{"id": "1", "name": "Task", "prompt": "test"}]}' | python statusline.py subagent
```

All invocations should exit with code 0 and output ANSI truecolor status lines.
