#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo


MAX_BLOCK_CHARS = 12000


def clean_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content") or item.get("message")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    if isinstance(value, dict):
        text = value.get("text") or value.get("content") or value.get("message")
        return text if isinstance(text, str) else json.dumps(value, ensure_ascii=False)
    return str(value)


def truncate(text, limit):
    text = text or ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n\n...（已截断，原文 {len(text)} 字符）"


def compact_summary(text, limit=90):
    text = clean_text(text).strip()
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_>#\-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return "空内容"
    if len(text) > limit:
        return text[:limit] + "..."
    return text


def infer_code_language(code):
    sample = code.strip()
    if not sample:
        return "text"
    try:
        json.loads(sample)
        return "json"
    except Exception:
        pass
    lines = [line.strip() for line in sample.splitlines() if line.strip()]
    if lines and all(line.startswith("{") and line.endswith("}") for line in lines):
        return "jsonl"
    lower = sample.lower()
    if sample.startswith("<") and re.search(r"</?[a-zA-Z][^>]*>", sample):
        if any(tag in lower for tag in ("<!doctype html", "<html", "<div", "<span", "<body", "<script")):
            return "html"
        return "xml"
    if re.search(r"\b(select|insert|update|delete|create|alter)\b", lower) and re.search(r"\b(from|table|where|values)\b", lower):
        return "sql"
    if sample.startswith("#!/") or re.search(r"(^|\n)\s*(cd|ls|find|rg|grep|sed|awk|cp|mv|mkdir|rm|git|npm|yarn|pnpm|python3?)\b", sample):
        return "bash"
    if re.search(r"\bplugins\s*\{|\bandroid\s*\{|\bdependencies\s*\{", sample):
        return "gradle"
    if re.search(r"\bfun\s+\w+\s*\(|\bval\s+\w+\s*=|\bvar\s+\w+\s*=", sample):
        return "kotlin"
    if re.search(r"\b(public|private|protected)\s+(class|interface|void|static)\b|\bimport\s+java\.", sample):
        return "java"
    if re.search(r"\b(function|const|let|var)\s+\w+|=>|console\.log", sample):
        return "javascript"
    if re.search(r"(^|\n)\s*[-\w]+:\s+.+", sample) and not any(ch in sample for ch in "{};"):
        return "yaml"
    if re.search(r"^(graph|flowchart|sequenceDiagram|stateDiagram|erDiagram|gantt)\b", sample):
        return "mermaid"
    return "text"


def enhance_code_fences(text):
    fence_re = re.compile(r"```([A-Za-z0-9_+.-]*)[ \t]*\n(.*?)```", re.S)

    def repl(match):
        lang = match.group(1).strip()
        code = match.group(2)
        if not lang:
            lang = infer_code_language(code)
        return f"```{lang}\n{code}```"

    return fence_re.sub(repl, text)


def quote_as_callout(text, title):
    lines = enhance_code_fences(text).splitlines()
    quoted = [f"> [!note]- {title}"]
    if not lines:
        quoted.append(">")
    else:
        for line in lines:
            quoted.append(f"> {line}" if line else ">")
    return "\n".join(quoted)


def file_link(path):
    return "file://" + quote(str(path), safe="/:")


def markdown_link(label, path):
    safe_label = re.sub(r"[\[\]\n\r]+", " ", label).strip() or Path(path).name
    return f"[{safe_label}]({file_link(path)})"


def split_user_attachments(text):
    text = clean_text(text).strip()
    if not re.match(r"^#*\s*Files mentioned by the user:", text):
        return text, []

    request_match = re.search(r"(?m)^##\s+My request for Codex:\s*$", text)
    if not request_match:
        return text, []

    file_section = text[:request_match.start()]
    request = text[request_match.end():]
    attachments = []
    for line in file_section.splitlines():
        match = re.match(r"^##\s+(.+?):\s+(/.+)$", line.strip())
        if match:
            attachments.append({
                "name": match.group(1).strip(),
                "path": match.group(2).strip(),
            })
    return request.strip(), attachments


def slugify(value, fallback):
    value = clean_text(value).strip() or fallback
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"[\r\n\t]+", " ", value)
    value = re.sub(r"[\\/:\*\?\"<>\|#\^\[\]]+", "-", value)
    value = re.sub(r"\s+", " ", value).strip(" .-_")
    value = value.lstrip("/\\").strip(" .-_")
    if not value:
        value = fallback
    return value[:80]


def parse_ts(value):
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def local_time(value, tz):
    dt = parse_ts(value)
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S %Z")


def local_dir_time(value, tz):
    dt = parse_ts(value)
    if dt is None:
        return "unknown-time"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz).strftime("%Y-%m-%d_%H-%M-%S")


def load_index(path):
    index = {}
    if not path.exists():
        return index
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            session_id = row.get("id")
            if session_id:
                index[session_id] = row
    return index


def is_environment_context(text):
    text = (text or "").strip()
    return text.startswith("<environment_context>") and "</environment_context>" in text


def strip_environment_context(text):
    return re.sub(r"\n?<environment_context>.*?</environment_context>\n?", "\n", text or "", flags=re.S).strip()


def strip_memory_citation(text):
    text = text or ""
    text = re.sub(
        r"\n?(?:> ?)?<oai-mem-citation>.*?(?:> ?)?</oai-mem-citation>\n?",
        "\n",
        text,
        flags=re.S,
    )
    text = re.sub(
        r"\n?(?:> ?)?<citation_entries>.*?(?:> ?)?</oai-mem-citation>\n?",
        "\n",
        text,
        flags=re.S,
    )
    marker_re = re.compile(r"</?oai-mem-citation>|</?citation_entries>|</?rollout_ids>|\boai-mem-citation\b|\bcitation_entries\b|\brollout_ids\b")
    text = "\n".join(line for line in text.splitlines() if not marker_re.search(line))
    return text.strip()


def strip_skill_context(text):
    return re.sub(r"\n?<skill>.*?</skill>\n?", "\n", text or "", flags=re.S).strip()


def strip_system_artifacts(text):
    text = strip_environment_context(text)
    text = strip_memory_citation(text)
    text = strip_skill_context(text)
    return text


def is_approval_review_context(text):
    text = (text or "").strip()
    return text.startswith("The following is the Codex agent history")


def is_meta_context(text):
    text = (text or "").strip()
    return (
        is_environment_context(text)
        or is_approval_review_context(text)
        or text.startswith("<turn_aborted>")
        or text.startswith("<skill>")
    )


def is_external_tool_context(text):
    text = (text or "").strip()
    head = text[:500].lower()
    return (
        "[external agent tool call:" in head
        or "[external agent tool result" in head
        or "[external_agent_tool_call:" in head
        or "[external_agent_tool_result" in head
        or text == "<EXTERNAL SESSION IMPORTED>"
    )


def display_title(text, fallback):
    text = re.sub(r"[\r\n]+", " ", clean_text(text)).strip() or fallback
    if len(text) > 120:
        return text[:120] + "..."
    return text


def normalize_project_name(cwd):
    name = Path(cwd or "unknown-project").name
    slug = slugify(name, "unknown-project")
    if slug.startswith("files-mentioned-by-the-user"):
        return "临时对话"
    return slug


def read_jsonl(path):
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                yield line_no, json.loads(line)
            except json.JSONDecodeError as exc:
                yield line_no, {"type": "parse_error", "error": str(exc)}


def extract_conversation(path, index, tz):
    meta = {}
    items = []
    first_user = ""
    last_assistant = ""
    parse_errors = 0

    def add_item(role, ts, text):
        text = clean_text(text)
        if not text:
            return
        text = strip_system_artifacts(text)
        if not text:
            return
        if is_meta_context(text):
            return
        if is_external_tool_context(text):
            return
        attachments = []
        if role == "用户":
            text, attachments = split_user_attachments(text)
            if not text:
                return
        if items and items[-1][0] == role and items[-1][2] == text:
            return
        items.append((role, ts, text, attachments))

    for line_no, row in read_jsonl(path):
        row_type = row.get("type")
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        ts = row.get("timestamp") or payload.get("timestamp")

        if row_type == "parse_error":
            parse_errors += 1
            continue

        if row_type == "session_meta":
            meta = payload
            continue

        payload_type = payload.get("type")

        if row_type == "event_msg" and payload_type == "user_message":
            text = clean_text(payload.get("message"))
            if text:
                clean_user_text, _attachments = split_user_attachments(strip_system_artifacts(text))
                if not first_user and not is_meta_context(clean_user_text):
                    first_user = clean_user_text
                add_item("用户", ts, text)
            continue

        if row_type == "response_item":
            if payload_type == "reasoning":
                continue

            if payload_type == "message":
                role = payload.get("role")
                text = clean_text(payload.get("content"))
                if role == "assistant" and text:
                    last_assistant = text
                    add_item("助手", ts, text)
                elif role == "user" and text:
                    clean_user_text, _attachments = split_user_attachments(strip_system_artifacts(text))
                    if not first_user and not is_meta_context(clean_user_text):
                        first_user = clean_user_text
                    add_item("用户", ts, text)
                continue

            if payload_type in {"function_call", "function_call_output"}:
                continue

        if row_type == "event_msg" and payload_type == "agent_message":
            text = clean_text(payload.get("message"))
            if text and text != last_assistant:
                last_assistant = text
                add_item("助手", ts, text)
            continue

        if row_type == "event_msg" and payload_type and payload_type.endswith("_end"):
            continue

    session_id = meta.get("id") or infer_session_id(path)
    indexed = index.get(session_id, {})
    indexed_name = strip_system_artifacts(indexed.get("thread_name") or "")
    indexed_name, _indexed_attachments = split_user_attachments(indexed_name)
    if indexed_name and not is_meta_context(indexed_name):
        thread_name = indexed_name
    elif first_user:
        thread_name = first_user
    elif is_approval_review_context(indexed_name or ""):
        thread_name = f"审批记录-{session_id[:8]}"
    elif (indexed_name or "").strip().startswith("<turn_aborted>"):
        thread_name = f"中断记录-{session_id[:8]}"
    else:
        thread_name = f"未命名问答-{session_id[:8]}"
    created = meta.get("timestamp") or path.stat().st_mtime
    if not isinstance(created, str):
        created_dt = datetime.fromtimestamp(created, tz=timezone.utc)
        created = created_dt.isoformat()
    project = normalize_project_name(meta.get("cwd"))
    question = slugify(thread_name, "未命名问答")

    return {
        "session_id": session_id,
        "path": path,
        "meta": meta,
        "thread_name": thread_name,
        "project": project,
        "question": question,
        "created": created,
        "created_local": local_time(created, tz),
        "created_dir": local_dir_time(created, tz),
        "updated_local": local_time(indexed.get("updated_at"), tz),
        "items": items,
        "first_user": first_user,
        "parse_errors": parse_errors,
    }


def infer_session_id(path):
    match = re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", path.name)
    return match.group(1) if match else path.stem


def render_markdown(conv):
    title = display_title(conv["thread_name"], f"未命名问答-{conv['session_id'][:8]}")
    toc_items = [(idx, role, ts, text) for idx, (role, ts, text, _attachments) in enumerate(conv["items"], 1)]
    lines = [
        "---",
        f"title: {title}",
        f"created: {conv['created_local']}",
        f"project: {conv['project']}",
        f"session_id: {conv['session_id']}",
        "source: Codex 本地会话 JSONL",
        "tags:",
        "  - codex",
        "  - 问答库",
        "  - obsidian",
        "---",
        "",
        f"# {title}",
        "",
        "## 元信息",
        "",
        f"- 项目名：`{conv['project']}`",
        f"- 问答创建时间：`{conv['created_local']}`",
        f"- 最近更新时间：`{conv['updated_local'] or '未知'}`",
        f"- 会话 ID：`{conv['session_id']}`",
        f"- 原始会话文件：`{conv['path']}`",
        f"- 工作目录：`{conv['meta'].get('cwd', '未知')}`",
        "",
        "## 同步说明",
        "",
        "本记录来自本机 Codex 会话 JSONL。隐藏内部推理、系统指令和开发者指令已排除；仅同步可见用户提问和助手回答。",
        "",
        "## 目录",
        "",
    ]

    if not toc_items:
        lines.append("- 无可同步问答")
    else:
        for idx, role, _ts, text in toc_items:
            label = "用户提问" if role == "用户" else "助手回答"
            lines.append(f"- [[#{idx}. {label}|{idx}. {label}]]：{compact_summary(text)}")

    lines.extend([
        "",
        "## 问答记录",
        "",
    ])

    if not conv["items"]:
        lines.append("> 该会话没有可同步的可见问答内容。")
        lines.append("")
    else:
        for idx, (role, ts, text, attachments) in enumerate(conv["items"], 1):
            label = "用户提问" if role == "用户" else "助手回答"
            lines.append(f"### {idx}. {label}")
            time_text = local_time(ts, ZoneInfo("Asia/Shanghai"))
            if time_text and role != "助手":
                lines.append(f"时间：`{time_text}`")
                lines.append("")
            body = enhance_code_fences(truncate(text.strip(), MAX_BLOCK_CHARS))
            if role == "助手":
                callout_title = f"助手回答"
                if time_text:
                    callout_title += f" · {time_text}"
                lines.append(quote_as_callout(body, callout_title))
            else:
                lines.append(body)
                if attachments:
                    lines.append("")
                    lines.append("附件：")
                    for attachment in attachments:
                        lines.append(f"- {markdown_link(attachment['name'], attachment['path'])}")
            lines.append("")

    if conv["parse_errors"]:
        lines.extend([
            "## 解析警告",
            "",
            f"- 有 {conv['parse_errors']} 行 JSONL 解析失败，已跳过。",
            "",
        ])

    lines.extend([
        "## Codex 可导入记录",
        "",
        "说明：当前未检测到公开稳定的 Codex 会话导入命令。本段提供去敏后的 JSONL 中间格式，保留可见用户提问和助手回答，可供后续导入脚本或人工恢复上下文使用。",
        "",
        "```jsonl",
    ])
    for row in importable_rows(conv):
        lines.append(json.dumps(row, ensure_ascii=False))
    lines.append("```")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def importable_rows(conv):
    yield {
        "schema": "codex-visible-conversation-v1",
        "type": "session",
        "session_id": conv["session_id"],
        "thread_name": conv["thread_name"],
        "project": conv["project"],
        "created": conv["created_local"],
        "source_jsonl": str(conv["path"]),
    }
    for role, ts, text, attachments in conv["items"]:
        if role == "用户":
            item_type = "message"
            mapped_role = "user"
            content = text
        elif role == "助手":
            item_type = "message"
            mapped_role = "assistant"
            content = text
        else:
            continue
        yield {
            "schema": "codex-visible-conversation-v1",
            "type": item_type,
            "role": mapped_role,
            "time": local_time(ts, ZoneInfo("Asia/Shanghai")) if ts else "",
            "content": truncate(content, MAX_BLOCK_CHARS),
            "attachments": attachments if role == "用户" and attachments else [],
        }


def export_all(sessions_root, index_path, output_root):
    tz = ZoneInfo("Asia/Shanghai")
    index = load_index(index_path)
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    conversations = []
    for path in sorted(sessions_root.rglob("*.jsonl")):
        conv = extract_conversation(path, index, tz)
        conversations.append(conv)
        target_dir = output_root / conv["project"]
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{conv['question']}.md"
        suffix = 2
        while target.exists():
            target = target_dir / f"{conv['question']}-{suffix}.md"
            suffix += 1
        target.write_text(render_markdown(conv), encoding="utf-8")
        conv["target"] = target

    index_lines = [
        "---",
        "title: Codex 问答库同步索引",
        f"created: {datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S %Z')}",
        "tags:",
        "  - codex",
        "  - 问答库",
        "  - 索引",
        "---",
        "",
        "# Codex 问答库同步索引",
        "",
        f"- 本次导出会话数：{len(conversations)}",
        f"- 本地会话目录：`{sessions_root}`",
        f"- 同步范围：本机当前账号可访问的 Codex 本地会话 JSONL",
        f"- 内容边界：不包含隐藏内部推理、系统指令、开发者指令",
        "",
        "## 会话列表",
        "",
    ]
    for conv in conversations:
        rel = conv["target"].relative_to(output_root)
        label = display_title(conv["thread_name"], f"未命名问答-{conv['session_id'][:8]}")
        index_lines.append(f"- [[{rel.with_suffix('').as_posix()}|{label}]] - `{conv['created_local']}` - `{conv['project']}`")
    (output_root / "同步索引.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    return conversations


def codex_home():
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex").expanduser()


def default_sessions_root():
    return codex_home() / "sessions"


def default_index_path():
    return codex_home() / "session_index.jsonl"


def obsidian_config_path():
    return Path.home() / "Library" / "Application Support" / "obsidian" / "obsidian.json"


def discover_obsidian_vaults():
    config_path = obsidian_config_path()
    if not config_path.exists():
        return []
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    vaults = []
    for key, value in (config.get("vaults") or {}).items():
        if not isinstance(value, dict):
            continue
        path = value.get("path")
        if not path:
            continue
        vault_path = Path(path).expanduser()
        if vault_path.exists():
            vaults.append({
                "id": key,
                "name": value.get("name") or vault_path.name,
                "path": str(vault_path),
            })
    return vaults


def resolve_vault(vault_arg=None, vault_name=None):
    if vault_arg:
        vault = Path(vault_arg).expanduser()
        if not vault.exists():
            raise SystemExit(f"Obsidian vault path does not exist: {vault}")
        return vault

    vaults = discover_obsidian_vaults()
    if vault_name:
        matches = [v for v in vaults if v["name"] == vault_name or Path(v["path"]).name == vault_name]
        if len(matches) == 1:
            return Path(matches[0]["path"])
        raise SystemExit(json.dumps({
            "error": f"Obsidian vault not found or not unique: {vault_name}",
            "candidates": vaults,
        }, ensure_ascii=False, indent=2))

    if len(vaults) == 1:
        return Path(vaults[0]["path"])
    if not vaults:
        raise SystemExit(
            "No Obsidian vault was detected. Install/open Obsidian and create a vault, "
            "or rerun with --vault /path/to/vault."
        )
    raise SystemExit(json.dumps({
        "error": "Multiple Obsidian vaults detected. Rerun with --vault /path/to/vault or --vault-name NAME.",
        "candidates": vaults,
    }, ensure_ascii=False, indent=2))


def is_generated_markdown(path):
    if path.name == "同步索引.md":
        return True
    try:
        head = path.read_text(encoding="utf-8", errors="ignore")[:1200]
    except OSError:
        return False
    return "source: Codex 本地会话 JSONL" in head


def copy_tree_contents(source, target):
    target.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        dest = target / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)


def sync_to_vault(export_root, vault, knowledge_root_name):
    target = vault / knowledge_root_name
    manual_backup = Path(tempfile.mkdtemp(prefix="sync-obsidian-manual-"))
    preserved = []

    if target.exists():
        for path in target.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix == ".md" and is_generated_markdown(path):
                continue
            rel = path.relative_to(target)
            backup_path = manual_backup / rel
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup_path)
            preserved.append(rel.as_posix())
        shutil.rmtree(target)

    shutil.copytree(export_root, target)
    for backup_file in manual_backup.rglob("*"):
        if not backup_file.is_file():
            continue
        rel = backup_file.relative_to(manual_backup)
        restore_path = target / rel
        if restore_path.exists():
            restore_path = target / "_手工保留" / rel
        restore_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_file, restore_path)

    state = {
        "synced_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
        "knowledge_root": str(target),
        "preserved_manual_files": preserved,
    }
    (target / ".sync-state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.rmtree(manual_backup, ignore_errors=True)
    return target, preserved


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sessions-root", type=Path, default=default_sessions_root())
    parser.add_argument("--index", type=Path, default=default_index_path())
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--sync", action="store_true", help="Write the verified export into an Obsidian vault.")
    parser.add_argument("--vault", type=Path, help="Obsidian vault path. If omitted, the script discovers local vaults.")
    parser.add_argument("--vault-name", help="Obsidian vault name to select when multiple vaults exist.")
    parser.add_argument("--knowledge-root-name", default="codex问答库")
    args = parser.parse_args()

    if not args.sessions_root.exists():
        print(f"Codex session directory was not found: {args.sessions_root}", file=sys.stderr)
        sys.exit(2)

    vault = resolve_vault(args.vault, args.vault_name) if args.sync else None
    output_root = args.output_root
    temp_dir = None
    if output_root is None:
        if args.sync:
            temp_dir = Path(tempfile.mkdtemp(prefix="sync-obsidian-export-"))
            output_root = temp_dir / args.knowledge_root_name
        else:
            output_root = Path.cwd() / "obsidian_export" / args.knowledge_root_name

    conversations = export_all(args.sessions_root, args.index, output_root)
    result = {
        "exported": len(conversations),
        "output_root": str(args.output_root),
        "actual_output_root": str(output_root),
        "projects": len({conv["project"] for conv in conversations}),
        "empty": sum(1 for conv in conversations if not conv["items"]),
        "synced": False,
    }
    if args.sync:
        target, preserved = sync_to_vault(output_root, vault, args.knowledge_root_name)
        result.update({
            "synced": True,
            "vault": str(vault),
            "target": str(target),
            "preserved_manual_files": preserved,
        })

    if temp_dir:
        shutil.rmtree(temp_dir, ignore_errors=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
