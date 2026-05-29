# my-ai-skills

个人 Codex Skills 仓库，用于沉淀和共享可复用的 AI 工作流。

## Skills

### sync-obsidian

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

## 安装

把仓库中的 skill 目录复制到 Codex skills 目录：

```bash
mkdir -p ~/.codex/skills
cp -R sync-obsidian ~/.codex/skills/sync-obsidian
```

如果本地已经安装过同名 skill，先确认不需要保留本地改动，再覆盖更新：

```bash
rm -rf ~/.codex/skills/sync-obsidian
cp -R sync-obsidian ~/.codex/skills/sync-obsidian
```

## 使用

在 Codex 中直接请求：

```text
$sync-obsidian 把本机 Codex 对话同步到 Obsidian
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

## 工作方式

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
