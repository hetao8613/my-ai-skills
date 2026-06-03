# 🧰 my-ai-skills

个人 Codex Skills 仓库，用于沉淀和共享可复用的 AI 工作流。

## ✨ Skills

### 📝 sync-obsidian

`sync-obsidian` 用于把本机 Codex 会话同步到 Obsidian 知识库，生成结构化的 `codex问答库`。它适合这些场景：

- 导出或重新同步本机 Codex 对话记录。
- 把 Codex 问答整理成 Obsidian 可阅读的知识库。
- 保留用户提问、助手回答和附件引用，过滤系统指令、工具调用、隐藏推理等内部信息。
- 生成 `codex问答库/项目名/对话主题.md` 的两层目录结构，并自动维护 `同步索引.md`。

同步后的笔记包含：

- YAML frontmatter 和会话元信息。
- 同步说明、目录、问答记录。
- 折叠的助手回答 callout。
- 可供后续导入脚本使用的去敏 JSONL 中间记录。
- 附件的 `file:///...` 本地引用链接。

### 📄 citizen-card-standard-doc-format

`citizen-card-standard-doc-format` 用于把市民卡上会材料、汇报材料和方案材料统一成标准 Word/DOCX 格式，适合这些场景：

- 按市民卡标准整理 `.docx` 文件版式。
- 统一页边距、页脚、标题、各级标题和正文格式。
- 处理手工编号、表格续页、表头重复和分页可读性。
- 渲染核查版面，避免文字裁切、表格溢出和尾页空白。

仓库中提供的相关文件：

- `citizen-card-standard-doc-format/SKILL.md`
- `citizen-card-standard-doc-format/references/format-requirements.md`
- `citizen-card-standard-doc-format/scripts/format_citizen_card_docx.py`
- `citizen-card-standard-doc-format/agents/openai.yaml`

## 🚀 安装

### 📦 通过 npm 安装

如果还没有发布到 npm registry，可以直接从 GitHub 安装：

```bash
npm install -g github:hetao8613/my-ai-skills
```

安装后使用全局命令：

```bash
my-ai-skills install --tool codex
my-ai-skills install --tool claude-code
my-ai-skills install --tool copilot --install-dir /path/to/your/project
my-ai-skills convert --tool cursor
my-ai-skills list-tools
```

安装单个 skill：

```bash
my-ai-skills install --tool codex --skill sync-obsidian
my-ai-skills install --tool codex --skill citizen-card-standard-doc-format
```

也可以不全局安装，直接用 `npx` 从 GitHub 运行：

```bash
npx github:hetao8613/my-ai-skills install --tool codex
```

如果后续发布到 npm registry，使用方式会变成：

```bash
npm install -g @hetao8613/my-ai-skills
my-ai-skills install --tool codex
```

本仓库不会使用 npm 的 `postinstall` 自动写入用户目录。安装 npm 包只会安装命令，真正写入 AI 工具配置需要显式执行 `my-ai-skills install ...`。

### ⚡ 一键安装到你的 AI 工具

自动检测本机已安装或已配置的直接安装工具，并安装所有 skill：

```bash
./scripts/install.sh
```

指定安装到某个工具：

```bash
./scripts/install.sh --tool codex         # Codex CLI / Codex
./scripts/install.sh --tool claude-code   # Claude Code
./scripts/install.sh --tool copilot       # GitHub Copilot repo instructions
./scripts/install.sh --tool openclaw      # OpenClaw
./scripts/install.sh --tool cursor        # Cursor
./scripts/install.sh --tool kiro          # Kiro (Amazon)
./scripts/install.sh --tool trae          # Trae
./scripts/install.sh --tool opencode      # OpenCode
./scripts/install.sh --tool aider         # Aider
./scripts/install.sh --tool windsurf      # Windsurf
./scripts/install.sh --tool antigravity   # Antigravity
./scripts/install.sh --tool gemini-cli    # Gemini CLI
./scripts/install.sh --tool qwen          # Qwen Code
./scripts/install.sh --tool deerflow      # DeerFlow 2.0 (ByteDance)
./scripts/install.sh --tool workbuddy     # WorkBuddy (Tencent)
./scripts/install.sh --tool hermes        # Hermes Agent (NousResearch)
./scripts/install.sh --tool qoder         # Qoder
```

直接安装支持：

- `codex`：复制到 `${CODEX_HOME:-~/.codex}/skills`
- `claude-code`：复制到 `~/.claude/skills`
- `copilot`：写入目标项目的 `.github/instructions/<skill>.instructions.md`
- 当前仓库中的 skill 会按目录名自动发现并分发，包括 `sync-obsidian` 和 `citizen-card-standard-doc-format`

GitHub Copilot 是项目级指令，不是全局 skill 目录。建议指定目标项目：

```bash
./scripts/install.sh --tool copilot --install-dir /path/to/your/project
```

其他工具会生成转换后的导入包：

```bash
./scripts/convert.sh --tool cursor
./scripts/convert.sh --tool gemini-cli
```

转换产物位于：

```text
dist/<tool>/<skill>/
```

然后按对应工具的自定义指令、插件或 agent 导入机制使用。

查看支持的工具：

```bash
./scripts/install.sh --list-tools
```

只安装某一个 skill：

```bash
./scripts/install.sh --tool codex --skill sync-obsidian
./scripts/install.sh --tool codex --skill citizen-card-standard-doc-format
```

预览安装动作，不写文件：

```bash
./scripts/install.sh --tool codex --dry-run
```

### 🛠️ 手动安装到 Codex

把仓库中的 skill 目录复制到 Codex skills 目录：

```bash
mkdir -p ~/.codex/skills
cp -R sync-obsidian ~/.codex/skills/sync-obsidian
cp -R citizen-card-standard-doc-format ~/.codex/skills/citizen-card-standard-doc-format
```

如果本地已经安装过同名 skill，先确认不需要保留本地改动，再覆盖更新：

```bash
rm -rf ~/.codex/skills/sync-obsidian
cp -R sync-obsidian ~/.codex/skills/sync-obsidian
rm -rf ~/.codex/skills/citizen-card-standard-doc-format
cp -R citizen-card-standard-doc-format ~/.codex/skills/citizen-card-standard-doc-format
```

## 📖 使用

在 Codex 中直接请求：

```text
$sync-obsidian 把本机 Codex 对话同步到 Obsidian
$citizen-card-standard-doc-format 把这份 DOCX 调整成市民卡标准格式
```

也可以在 skill 目录中手动运行脚本。

干运行，只导出到临时或指定目录，不写 Obsidian：

```bash
python scripts/export_codex_sessions_to_obsidian.py
```

正式同步到自动发现的 Obsidian vault：

```bash
python scripts/export_codex_sessions_to_obsidian.py --sync
```

指定 Obsidian vault：

```bash
python scripts/export_codex_sessions_to_obsidian.py --sync --vault /path/to/your/vault
```

指定 Codex 会话目录和索引：

```bash
python scripts/export_codex_sessions_to_obsidian.py \
  --sessions-root ~/.codex/sessions \
  --index ~/.codex/session_index.jsonl \
  --sync
```

市民卡标准格式调整的脚本示例：

```bash
python3 citizen-card-standard-doc-format/scripts/format_citizen_card_docx.py input.docx --output output.docx
```

## 🔍 工作方式

`sync-obsidian` 默认从 `$CODEX_HOME/sessions` 和 `$CODEX_HOME/session_index.jsonl` 读取会话；如果没有设置 `$CODEX_HOME`，会回退到 `~/.codex/sessions` 和 `~/.codex/session_index.jsonl`。

Obsidian vault 会优先从 macOS Obsidian 配置中自动发现。同步目标固定为：

```text
<vault>/codex问答库
```

正式同步前，脚本会先生成临时导出结果并完成校验，然后再写入 vault。生成内容会过滤：

- 系统和开发者指令。
- 工具调用、工具输出、命令输出。
- 隐藏推理。
- `environment_context`、记忆引用块和审批审查转录。
- Codex 附件包装文本。

附件只会以本地 `file:///...` 链接引用，不会读取、复制或修改附件文件。

`citizen-card-standard-doc-format` 会先把源文件复制成 `原文件名-格式调整版.docx`，再按市民卡标准统一页边距、字体、段落、编号和页脚，并通过渲染结果检查表格裁切、分页和尾页空白问题。
