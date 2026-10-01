# cc-status-line

A fast, dependency-free status line for [Claude Code](https://claude.com/claude-code), [Antigravity CLI (`agy`)](https://antigravity.google), [OpenAI Codex CLI](https://github.com/openai), and other AI coding CLIs — a single line of context for your main session, plus a compact line per running subagent.

[English](README.md) | [中文](README_zh.md)

---

### Preview

<!-- Screenshot goes to assets/preview.png — drop the file in, no other change needed. -->
![cc-status-line in a terminal: main session line and one line per running subagent](assets/preview.png)

```text
# Claude Code session (with cache, git diff, and OAuth rate limits):
Opus 5 │ Idle │ (.venv) │ main ● │ +42 -12 │ ctx ████░░░░░░ 42% │ ↑15.0k ↓3.2k │ ⚡cache 80% (12.0k) │ 5h 76% · 2h 15m │ ~/Codes/my-project

# Antigravity CLI session (with official Google OAuth quota):
Gemini 2.5 Pro │ Idle │ pnpm │ main ✓ │ ctx ████░░░░░░ 42% │ ↑85.0k ↓15.0k │ ⚡cache 71% (60.0k) │ 5h 80% · 1h │ 7d 94% · 6d │ ~/Codes/my-project

# OpenAI Codex CLI / GPT session:
GPT-4o │ main ✓ │ ctx ███░░░░░░░ 26% │ ↑12.0k ↓3.5k │ 5h 85% · 3h │ ~/Codes/my-project

# Subagent line (Claude Code / Antigravity CLI):
↳ Opus 5 │ Explore │ ctx ███████░░░ 68% │ ↓12.4k │ find all status line configs
↳ Gemini 2.5 Flash │ Researcher │ ctx ███░░░░░░░ 30% │ ↓5.4k │ search codebase
```

### Subagent states

A subagent line is built up in stages. These two screenshots show the same agent at each stage:

<!-- Screenshots go to assets/subagent_new.png and assets/subagent_token.png — drop the files in, no other change needed. -->
![A subagent line right after opening, before token counts arrive](assets/subagent_new.png)
![The same subagent line once token counts are populated](assets/subagent_token.png)

- **Just opened** — the line renders from model, agent type/role, task description/prompt and, when the context window is already known, the context bar. Token counts have not arrived yet.
- **With token data** — the `↓` token segment fills in as the agent runs.

Either stage degrades cleanly: a segment whose data is missing is omitted rather than rendered as a placeholder.

### Features

- **Multi-CLI compatibility** — seamless support for Claude Code, Antigravity CLI (`agy`), OpenAI Codex CLI (`codex`), and generic AI coding assistants with automatic CLI detection.
- **Prompt cache hit rate** — automatically detects and displays prompt cache hits and savings (`⚡cache 80% (12.0k)`).
- **Virtual environment & runtime detection** — automatically detects active environments (Python `.venv`/`conda`, Node `pnpm`/`bun`/`yarn`/`.nvmrc`, Go `go.mod`, Rust `cargo`/`rust-toolchain`, etc.).
- **Git diff stat** — real-time additions and deletions (`+42 -12`) alongside branch status.
- **Always-on context tokens** — context token usage (`↑` input and `↓` output) is always visible across all sessions.
- **Official OAuth quota detection** — automatically detects official OAuth subscriptions and displays standard buckets (`5h`, `7d`, `1m`) with remaining percentage and reset countdown (e.g. `5h 76% · 2h 15m │ 7d 59%`).
- **Context usage bar** — color-coded green / yellow / red at 65% and 85% thresholds.
- **Git state** — current branch (falls back to short SHA on detached HEAD) with a `✓` / `●` clean-or-dirty marker.
- **Session cost / Quota** — total USD for API token-billed sessions, or official OAuth quotas for subscription sessions.
- **Interactive TUI configuration** — visual module reordering, toggling, and bilingual switching via `python statusline.py config`.
- **Shortened workspace path** — `$HOME` collapses to `~`, deep paths to `…/last/three/segments`.
- **Per-subagent lines** — each running subagent gets its own line with model, role/type, context usage and task description, fully compatible with Antigravity subagents and Claude Code.
- **Zero dependencies** — Python 3 standard library only. No install step, no virtualenv, no build.
- **Never blocks your prompt** — git calls are capped at a 0.5s timeout, and any failure degrades to a blank field instead of an error.

### Requirements

- Python 3.8+
- `git` on `PATH` (optional — the git segment is simply omitted without it)
- A terminal with truecolor support for the RGB palette

### Installation & Configuration

#### Quick Setup via AI Coding Assistants (Claude Code, Codex, etc.)

You can let your AI agent configure `cc-status-line` automatically. Copy and send the following instruction to your assistant (**Claude Code**, **OpenAI Codex**, **Antigravity**, etc.):

```text
Please configure cc-status-line for my environment by following the instructions in AGENTS.md in this repository. Automatically determine the absolute path to statusline.py and safely update my CLI settings.
```

The repository includes [AGENTS.md](AGENTS.md) as the standard universal guide for AI agents to inspect and configure automatically.

---

#### Manual Setup

1. Clone the repository anywhere you like:

   ```bash
   git clone https://github.com/fangweilong/cc-status-line.git
   ```

2. Configure according to your CLI:

   #### Option A: Claude Code (`~/.claude/settings.json`)

   ```json
   {
     "statusLine": {
       "type": "command",
       "command": "python /absolute/path/to/cc-status-line/statusline.py main",
       "padding": 0
     },
     "subagentStatusLine": {
       "type": "command",
       "command": "python /absolute/path/to/cc-status-line/statusline.py subagent"
     }
   }
   ```

   See [examples/settings.json](examples/settings.json).

   #### Option B: Antigravity CLI (`~/.gemini/antigravity-cli/settings.json`)

   ```json
   {
     "statusLine": {
       "type": "command",
       "command": "python /absolute/path/to/cc-status-line/statusline.py main",
       "enabled": true,
       "padding": 0,
       "stack_with_default": false
     }
   }
   ```

   See [examples/antigravity-settings.json](examples/antigravity-settings.json). You can also run `/statusline python /path/to/statusline.py main` inside `agy`.

   #### Option C: OpenAI Codex CLI (`~/.codex/config.toml`)

   Codex CLI natively manages its footer status line via built-in item identifiers in `~/.codex/config.toml`:

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

   See [examples/codex-config.toml](examples/codex-config.toml).
   If you invoke Codex inside custom terminal scripts, tmux, or shell wrappers, you can call `cc-status-line` directly:
   `python /path/to/cc-status-line/statusline.py codex`

3. Restart your CLI, or run `/statusline` to confirm the setting was picked up.

#### Path notes

- Use **forward slashes**, even on Windows (`python C:/tools/cc-status-line/statusline.py main`).
- Quote the path if it contains spaces.
- On Windows, `python` must resolve to a real interpreter. If you rely on the `py` launcher, use `py` in the command instead.
- On macOS / Linux, make the entry executable and use the shebang if you prefer:

  ```bash
  chmod +x statusline.py
  ```

### Usage & Modes

```bash
# Main session line (auto-detects Claude Code, Antigravity CLI, Codex, or generic)
python statusline.py main

# Explicit CLI selection:
python statusline.py main --cli antigravity
python statusline.py main --cli claude
python statusline.py main --cli codex

# Direct shorthand aliases:
python statusline.py agy
python statusline.py antigravity
python statusline.py claude
python statusline.py cc
python statusline.py codex

# Interactive TUI configuration wizard (modules, ordering, language):
python statusline.py config

# Subagent lines (outputs {"id", "content"} JSON per task):
python statusline.py subagent
```

### Standalone Binary (Optional)

If you prefer not having Python installed or want a single executable:
- Prebuilt standalone executables are automatically generated via GitHub Actions for **Windows (`x86_64` / `arm64`)**, **macOS (`Apple Silicon arm64`)**, and **Linux (`x86_64` / `arm64`)** on every release.
- Download the binary for your platform from GitHub Releases, put it in your `PATH`, and run directly:
  ```bash
  # Windows
  statusline.exe main
  statusline.exe config

  # Linux / macOS
  statusline main
  statusline config
  ```
- Or build locally using PyInstaller:
  ```bash
  pip install pyinstaller
  pyinstaller --onefile --clean --name statusline statusline.py
  ```


### Errors

The entry point validates its mode argument and never fails silently. Because a status line has no stderr channel, every error is printed to **stdout** as a single visible line:

```text
⚠ statusline: missing mode argument │ check your settings.json │ statusline.py <main|subagent|agy|claude|codex> [--cli <name>]
⚠ statusline: unknown mode 'mian' │ expected main, subagent, agy, claude, or codex │ statusline.py <main|subagent|agy|claude|codex> [--cli <name>]
⚠ statusline: KeyError: 'foo' │ render failed │ statusline.py <main|subagent|agy|claude|codex> [--cli <name>]
```

| Case | Behavior | Exit code |
| --- | --- | --- |
| No argument | `missing mode argument` line | 1 |
| Unrecognized argument | `unknown mode '...'` line | 1 |
| Unexpected exception during rendering | `ExceptionType: message` line | 1 |
| Empty or malformed stdin JSON | No error — renders a minimal line (by design) | 0 |

### Input fields & OAuth Quota

The renderer reads defensively and tolerates missing keys — each field below is tried in order, and anything absent is skipped.

| Segment | Fields read (first match wins) |
| --- | --- |
| Model | `model.display_name` → `model.name` → `model.id` → CLI default (`Gemini` / `Claude` / `Codex` / `Agent`) |
| State | `agent_state` → `state` (e.g., `Idle`, `Thinking`, `Auth`) |
| Env | `VIRTUAL_ENV` / `CONDA_DEFAULT_ENV` or project files (`.venv`, `pnpm-lock.yaml`, `go.mod`, etc.) |
| Git | Current branch with `✓` / `●` |
| Git Stat | `git diff HEAD --shortstat` (`+X -Y`) |
| Workspace | `workspace.current_dir` → `workspace.project_dir` → `cwd` |
| Context | `context_window.used_percentage` → `100 - context_window.remaining_percentage` |
| Tokens | `context_window.total_input_tokens` → `context_window.input_tokens` → `input_tokens` → `tokens.input`, same for output |
| Cache | `cache_read_input_tokens` → `tokens.cached` → `prompt_tokens_details.cached_tokens` |
| Cost | `cost.total_cost_usd` |
| Quota | `quota.remaining_fraction` / `quota.<model>.remaining_fraction` (with `reset_in_seconds` or `reset_time` countdown) |

#### Quota Detection Rules

1. Checks payload for explicit OAuth auth type (`auth.type` or `auth_type`).
2. Checks payload for `quota` metrics.
3. Checks local Google OAuth credentials (`~/.gemini/oauth_creds.json`, `~/.gemini/google_accounts.json`, etc.).
4. If an explicit API key (`GEMINI_API_KEY` / `GOOGLE_API_KEY` / `OPENAI_API_KEY`) is active, OAuth quota is bypassed.
5. Quota color-codes automatically: **green** (>= 50%), **yellow** (20% ~ 50%), **red** (< 20%).

### Project layout

```text
statusline.py            # CLI entry point (main | subagent | agy | claude | codex)
AGENTS.md                # Universal AI Agent reading and installation guide
statusline/
  main.py                # main session status line renderer
  subagent.py            # per-subagent lines renderer
  quota.py               # official OAuth detection and quota formatting
  common.py              # stdin parsing, CLI detection, git, path, progress bar
  colors.py              # ANSI truecolor palette
examples/
  settings.json              # Claude Code configuration example
  antigravity-settings.json  # Antigravity CLI configuration example
  codex-config.toml          # OpenAI Codex CLI configuration example
```

### License

[MIT](LICENSE)
