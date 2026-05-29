---
name: sync-obsidian
description: Sync local Codex conversation sessions into an Obsidian vault as a structured Codex Q&A knowledge base. Use when the user asks to export, resync, clean, format, update, incrementally sync, or archive Codex chat history into Obsidian; when they mention Obsidian knowledge base, codex问答库, conversation archive, chat history export, attachment references, or automatic post-answer sync to Obsidian.
---

# Sync Obsidian

## Purpose

Sync locally available Codex session JSONL files into an Obsidian knowledge base named `codex问答库`, using the user's vault rather than hard-coded local paths.

Use the bundled script whenever possible:

```bash
python scripts/export_codex_sessions_to_obsidian.py --sync
```

For a dry run in the current workspace:

```bash
python scripts/export_codex_sessions_to_obsidian.py
```

## Trigger Policy

Run this skill only when the user explicitly asks for Obsidian/Codex conversation synchronization, export, cleanup, reformatting, attachment linking, or importable conversation records.

Do not implicitly sync after ordinary answers, coding tasks, document edits, reviews, or analysis. Automatic post-answer sync is opt-in only. If the user asks to enable automatic sync, confirm:

- Target Obsidian vault.
- Whether to sync all local sessions first.
- Whether each future answer should sync only the current changed session.
- Whether generated files under `codex问答库` may be overwritten.

## Vault Discovery

Do not hard-code the user's vault path.

1. Prefer the script's automatic discovery of Obsidian vaults from the local Obsidian config.
2. On macOS, the script reads `~/Library/Application Support/obsidian/obsidian.json`.
3. If exactly one vault exists, use it.
4. If multiple vaults exist, ask the user to choose one or pass `--vault /path/to/vault`.
5. If no vault is detected, tell the user to install/open Obsidian and create a vault, or provide `--vault /path/to/vault`.

Codex sessions are discovered from `$CODEX_HOME/sessions` and `$CODEX_HOME/session_index.jsonl`; if `$CODEX_HOME` is unset, fall back to `~/.codex/sessions` and `~/.codex/session_index.jsonl`.

## Knowledge Base Shape

Write into:

```text
<vault>/codex问答库
```

Use this structure:

```text
codex问答库/
├── 同步索引.md
└── 项目名/
    └── 对话主题.md
```

Never use the older `项目名/对话时间/对话主题.md` structure.

If the source project name is a temporary Codex directory such as `files-mentioned-by-the-user-*`, put the note under `临时对话`.

## Note Format

Each generated note must contain:

- YAML frontmatter with title, created time, project, session id, source.
- `元信息`
- `同步说明`
- `目录`
- `问答记录`
- `Codex 可导入记录`

Only include visible user questions and assistant answers.

Render assistant answers as folded Obsidian callouts:

```md
> [!note]- 助手回答 · 时间
```

Add code fence languages when inferable, including `json`, `jsonl`, `bash`, `java`, `kotlin`, `xml`, `html`, `sql`, and `mermaid`.

## Attachment Links

When a user message contains Codex attachment wrappers like:

```md
Files mentioned by the user:

## filename.docx: /absolute/path/filename.docx

## My request for Codex:
...
```

Remove the wrapper from the visible question, keep only the actual request, and add an attachment section under that question:

```md
附件：
- [filename.docx](file:///absolute/path/filename.docx)
```

Only reference attachments. Do not read, copy, move, edit, or rewrite attachment files unless the user separately asks for file editing.

## Required Filtering

Remove these from exported notes and importable records:

- Hidden reasoning.
- System and developer instructions.
- Tool calls, tool outputs, command output, and tool role records.
- `<environment_context>...</environment_context>`.
- `<oai-mem-citation>...</oai-mem-citation>`.
- `<citation_entries>...</citation_entries>`.
- `<rollout_ids>...</rollout_ids>`.
- Standalone marker lines containing `oai-mem-citation`, `citation_entries`, or `rollout_ids`.
- `<turn_aborted>`.
- Approval-review transcripts beginning with `The following is the Codex agent history`.
- External agent tool transcript blocks.

## Sync Behavior

Export to a temporary or workspace directory first, then verify, then write to the vault.

When syncing to the vault:

- Replace generated notes under `codex问答库`.
- Preserve non-generated/manual files when possible.
- Write `.sync-state.json` under `codex问答库`.
- Do not delete files outside `codex问答库`.

For incremental sync requests, prefer rebuilding only changed sessions when the script supports it. If incremental state is incomplete or stale, run a full export and say so.

## Verification

Before reporting success, verify:

- No `environment_context` raw block remains.
- No `oai-mem-citation`, `citation_entries`, or `rollout_ids` remains.
- No `Files mentioned by the user` wrapper remains.
- No obvious tool-call or tool-output records remain.
- Markdown files are two levels deep under `codex问答库/项目名/对话主题.md`.
- Attachment links are present as `file:///...` links and attachment files were not modified.

Report the vault path, target knowledge base path, number of exported sessions, and any preserved manual files.
