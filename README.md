# cc-status-line

A fast, dependency-free status line for [Claude Code](https://claude.com/claude-code) — a single line of context for your main session, plus a compact line per running subagent.

[English](#english) | [中文](#中文)

---

## English

### Preview

<!-- Screenshot goes to assets/preview.png — drop the file in, no other change needed. -->
![cc-status-line in a terminal: main session line and one line per running subagent](assets/preview.png)

```text
Opus 5 │ main ✓ │ ctx ████░░░░░░ 42% │ ↑15.0k ↓3.2k │ $0.37 │ ~/Codes/my-project
↳ Opus 5 │ Explore │ ctx ███████░░░ 68% │ ↓12.4k │ find all status line configs
```

### Subagent states

A subagent line is built up in stages. These two screenshots show the same agent at each stage:

<!-- Screenshots go to assets/subagent_new.png and assets/subagent_token.png — drop the files in, no other change needed. -->
![A subagent line right after opening, before token counts arrive](assets/subagent_new.png)
![The same subagent line once token counts are populated](assets/subagent_token.png)

- **Just opened** — the line renders from model, agent type, task description and, when the context window is already known, the context bar. Token counts have not arrived yet.
- **With token data** — the `↓` token segment fills in as the agent runs.

Either stage degrades cleanly: a segment whose data is missing is omitted rather than rendered as a placeholder.

### Features

- **Context usage bar** — color-coded green / yellow / red at 65% and 85% thresholds.
- **Git state** — current branch (falls back to short SHA on detached HEAD) with a `✓` / `●` clean-or-dirty marker.
- **Token counts** — `↑` input and `↓` output, abbreviated as `k` / `M`.
- **Session cost** — total USD for the session.
- **Shortened workspace path** — `$HOME` collapses to `~`, deep paths to `…/last/three/segments`.
- **Per-subagent lines** — each running subagent gets its own line with model, agent type, context usage and task description.
- **Zero dependencies** — Python 3 standard library only. No install step, no virtualenv, no build.
- **Never blocks your prompt** — git calls are capped at a 0.5s timeout, and any failure degrades to a blank field instead of an error.

### Requirements

- Python 3.8+
- `git` on `PATH` (optional — the git segment is simply omitted without it)
- A terminal with truecolor support for the RGB palette

### Installation

1. Clone the repository anywhere you like:

   ```bash
   git clone https://github.com/fangweilong/cc-status-line.git
   ```

2. Point Claude Code at the entry script. Add to `~/.claude/settings.json`:

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

   ⚠️ **The `main` / `subagent` argument is mandatory — do not drop it.**

   > `statusLine` **must** end with `main`, and `subagentStatusLine` **must** end with `subagent`.
   > The two keys are not interchangeable, and neither command works without its argument.
   >
   > - `"command": "... statusline.py"` ❌ — missing argument, renders an error line
   > - `"command": "... statusline.py subagent"` under `statusLine` ❌ — wrong mode, subagent JSON is not a valid main status line
   > - `"command": "... statusline.py main"` under `statusLine` ✅
   >
   > A wrong or missing argument is reported visibly in the status line itself — see [Errors](#errors).

   See [examples/settings.json](examples/settings.json) for a copy-paste version.

3. Restart Claude Code, or run `/statusline` to confirm the setting was picked up.

#### Path notes

- Use **forward slashes**, even on Windows (`python C:/tools/cc-status-line/statusline.py main`).
- Quote the path if it contains spaces.
- On Windows, `python` must resolve to a real interpreter. If you rely on the `py` launcher, use `py` in the command instead.
- On macOS / Linux, make the entry executable and use the shebang if you prefer:

  ```bash
  chmod +x statusline.py
  ```

  ```json
  { "statusLine": { "type": "command", "command": "/absolute/path/to/cc-status-line/statusline.py main" } }
  ```

### Usage

```bash
# main session line — reads the status JSON on stdin
python statusline.py main

# one line per subagent — prints {"id", "content"} JSON objects
python statusline.py subagent
```

Both modes read Claude Code's status JSON from **stdin**. The mode argument is required — see [Errors](#errors) for what happens when it is missing.

### Errors

The entry point validates its mode argument and never fails silently. Because a status line has no stderr channel, every error is printed to **stdout** as a single visible line:

```text
⚠ statusline: missing mode argument │ check your settings.json │ statusline.py <main|subagent>
⚠ statusline: unknown mode 'mian' │ expected main or subagent │ statusline.py <main|subagent>
⚠ statusline: KeyError: 'foo' │ render failed │ statusline.py <main|subagent>
```

| Case | Behavior | Exit code |
| --- | --- | --- |
| No argument | `missing mode argument` line | 1 |
| Argument not `main` / `subagent` (case-insensitive) | `unknown mode '...'` line | 1 |
| Unexpected exception during rendering | `ExceptionType: message` line | 1 |
| Empty or malformed stdin JSON | No error — renders a minimal line (by design) | 0 |

If you see a `⚠ statusline:` line, the cause is almost always the `command` in your `settings.json` — re-check the argument at the end of it.

### Input fields

The renderer reads defensively and tolerates missing keys — each field below is tried in order, and anything absent is skipped.

| Segment | Fields read (first match wins) |
| --- | --- |
| Model | `model.display_name` → `model.name` → `model.id` → `"Claude"` |
| Workspace | `workspace.current_dir` → `cwd` |
| Context | `context_window.used_percentage` |
| Tokens | `context_window.total_input_tokens` → `context_window.input_tokens` → `input_tokens`, same shape for output |
| Cost | `cost.total_cost_usd` |

Subagent mode additionally reads `tasks` (or `subagents`), and per task: `id` / `task_id` / `session_id`, `model`, `name` / `agent_type` / `subagent_type` / `type`, `context_window.used_percentage`, token counts, and `description` / `content` / `subject` / `title` for the text label. Description text longer than 70 characters is truncated with an ellipsis.

### Customization

- **Colors** — every color is a truecolor escape in [statusline/colors.py](statusline/colors.py). Edit the RGB values there; `DIM`, `PURPLE` and `WHITE` are defined but currently unused, ready for your own segments.
- **Thresholds** — the green / yellow / red cutoffs (65% / 85%) live in `context_color()` in [statusline/common.py](statusline/common.py).
- **Bar width** — pass `width` to `progress_bar()`; the default is 10 cells.
- **Segment order** — the `parts` list in [statusline/main.py](statusline/main.py) is joined with `" │ "`. Reorder, add or drop entries there.

### Project layout

```text
statusline.py            # entry point; requires argv[1]: main | subagent
statusline/
  main.py                # main session line
  subagent.py            # per-subagent lines
  common.py              # stdin parsing, git, path, formatting, progress bar
  colors.py              # ANSI truecolor palette
```

### License

[MIT](LICENSE)

---

## 中文

### 效果预览

<!-- 截图放到 assets/preview.png，放进去即可，无需改其他内容。 -->
![cc-status-line 终端实际效果：主会话状态行，以及每个运行中的 subagent 各一行](assets/preview.png)

```text
Opus 5 │ main ✓ │ ctx ████░░░░░░ 42% │ ↑15.0k ↓3.2k │ $0.37 │ ~/Codes/my-project
↳ Opus 5 │ Explore │ ctx ███████░░░ 68% │ ↓12.4k │ 查找所有 status line 配置
```

### Subagent 状态

subagent 状态行是分阶段拼出来的。下面两张截图是同一个 agent 在不同阶段的样子：

<!-- 截图放到 assets/subagent_new.png 和 assets/subagent_token.png，放进去即可，无需改其他内容。 -->
![Subagent 刚打开、token 计数尚未到来时的状态行](assets/subagent_new.png)
![同一个 subagent 状态行在 token 计数填充后的样子](assets/subagent_token.png)

- **刚打开** —— 状态行由模型、agent 类型、任务描述，以及已知上下文窗口时的进度条拼出，此时还没有 token 计数。
- **有 token 数据时** —— 随着 agent 运行，`↓` token 片段会填充进来。

两种阶段都做了降级：某个片段的数据缺失时会被直接省略，而不是渲染成占位符。

### 特性

- **上下文用量进度条** —— 按阈值着色，65% 转黄、85% 转红。
- **Git 状态** —— 显示当前分支（detached HEAD 时回退到短 SHA），并用 `✓` / `●` 标记工作区是否干净。
- **Token 统计** —— `↑` 输入、`↓` 输出，超过千 / 百万自动缩写为 `k` / `M`。
- **会话花费** —— 当前会话累计美元金额。
- **路径缩写** —— `$HOME` 折叠为 `~`，过深的路径折叠为 `…/最后/三级/目录`。
- **Subagent 逐行显示** —— 每个运行中的 subagent 单独一行，包含模型、agent 类型、上下文用量和任务描述。
- **零依赖** —— 只用 Python 3 标准库。无需安装、无需虚拟环境、无需构建。
- **不阻塞输入** —— git 调用最长 0.5 秒超时，任何异常都降级为空字段而不是报错。

### 环境要求

- Python 3.8+
- `PATH` 中有 `git`（可选，缺失时整段 git 信息不显示）
- 终端支持 truecolor，否则 RGB 配色会失真

### 安装

1. 克隆仓库到任意位置：

   ```bash
   git clone https://github.com/fangweilong/cc-status-line.git
   ```

2. 在 `~/.claude/settings.json` 中指向入口脚本：

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

   ⚠️ **`main` / `subagent` 这两个参数必须保留，不能省略。**

   > `statusLine` 的命令**必须**以 `main` 结尾，`subagentStatusLine` 的命令**必须**以 `subagent` 结尾。
   > 两个配置项不能互换，任何一条命令少了参数都不工作。
   >
   > - `"command": "... statusline.py"` ❌ —— 缺少参数，状态栏会显示错误提示
   > - `statusLine` 下写 `"command": "... statusline.py subagent"` ❌ —— 模式错误，subagent 的 JSON 不是合法的主状态行
   > - `statusLine` 下写 `"command": "... statusline.py main"` ✅
   >
   > 参数缺失或写错时，错误会直接显示在状态栏上，详见[错误提示](#错误提示)。

   可直接复制 [examples/settings.json](examples/settings.json)。

3. 重启 Claude Code，或执行 `/statusline` 确认配置已生效。

#### 路径注意事项

- 即使在 Windows 上也请使用**正斜杠**：`python C:/tools/cc-status-line/statusline.py main`。
- 路径含空格时请加引号。
- Windows 上 `python` 必须能解析到真实解释器。若你依赖 `py` 启动器，请把命令里的 `python` 换成 `py`。
- macOS / Linux 下也可以加执行权限后直接用 shebang：

  ```bash
  chmod +x statusline.py
  ```

  ```json
  { "statusLine": { "type": "command", "command": "/absolute/path/to/cc-status-line/statusline.py main" } }
  ```

### 用法

```bash
# 主会话状态行 —— 从 stdin 读取状态 JSON
python statusline.py main

# 每个 subagent 一行 —— 输出 {"id", "content"} 结构的多行 JSON
python statusline.py subagent
```

两种模式都从 **stdin** 读取 Claude Code 传入的状态 JSON。模式参数是必填的，缺失时的表现见[错误提示](#错误提示)。

### 错误提示

入口脚本会校验模式参数，不会静默失败。由于状态栏没有 stderr 通道，所有错误都打印到 **stdout**，输出为一行可见的提示：

```text
⚠ statusline: missing mode argument │ check your settings.json │ statusline.py <main|subagent>
⚠ statusline: unknown mode 'mian' │ expected main or subagent │ statusline.py <main|subagent>
⚠ statusline: KeyError: 'foo' │ render failed │ statusline.py <main|subagent>
```

| 情况 | 行为 | 退出码 |
| --- | --- | --- |
| 未传参数 | 输出 `missing mode argument` 提示行 | 1 |
| 参数不是 `main` / `subagent`（不区分大小写） | 输出 `unknown mode '...'` 提示行 | 1 |
| 渲染过程中出现未预期异常 | 输出 `异常类型: 消息` 提示行 | 1 |
| stdin JSON 为空或格式错误 | 不报错，输出最小可用内容（有意为之） | 0 |

只要看到 `⚠ statusline:` 开头的行，问题基本都在 `settings.json` 的 `command` 上 —— 回头检查一下命令末尾的参数。

### 输入字段

渲染逻辑做了充分的容错，下表字段按顺序逐个尝试，缺失即跳过。

| 片段 | 读取字段（命中即用） |
| --- | --- |
| 模型 | `model.display_name` → `model.name` → `model.id` → `"Claude"` |
| 工作目录 | `workspace.current_dir` → `cwd` |
| 上下文 | `context_window.used_percentage` |
| Token | `context_window.total_input_tokens` → `context_window.input_tokens` → `input_tokens`，输出同理 |
| 花费 | `cost.total_cost_usd` |

Subagent 模式额外读取 `tasks`（或 `subagents`），每个任务内读取：`id` / `task_id` / `session_id`、`model`、`name` / `agent_type` / `subagent_type` / `type`、`context_window.used_percentage`、token 计数，以及作为文本标签的 `description` / `content` / `subject` / `title`。描述超过 70 字符会被截断并加省略号。

### 自定义

- **配色** —— 所有颜色都是 [statusline/colors.py](statusline/colors.py) 中的 truecolor 转义码。直接改 RGB 值即可；`DIM`、`PURPLE`、`WHITE` 已定义但当前未使用，可留给你新增片段。
- **阈值** —— 绿 / 黄 / 红的分界（65% / 85%）在 [statusline/common.py](statusline/common.py) 的 `context_color()` 中。
- **进度条宽度** —— 给 `progress_bar()` 传 `width`，默认 10 格。
- **片段顺序** —— [statusline/main.py](statusline/main.py) 中的 `parts` 列表以 `" │ "` 拼接，在这里增删或调序。

### 项目结构

```text
statusline.py            # 入口，必须传 argv[1]：main | subagent
statusline/
  main.py                # 主会话状态行
  subagent.py            # 各 subagent 状态行
  common.py              # stdin 解析、git、路径、格式化、进度条
  colors.py              # ANSI truecolor 调色板
```

### 许可证

[MIT](LICENSE)
