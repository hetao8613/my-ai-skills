#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONVERT_SCRIPT="$REPO_ROOT/scripts/convert.sh"

TOOLS=(
  openclaw
  claude-code
  copilot
  cursor
  kiro
  trae
  opencode
  aider
  windsurf
  antigravity
  gemini-cli
  qwen
  codex
  deerflow
  workbuddy
  hermes
  qoder
)

usage() {
  cat <<'EOF'
Usage: ./scripts/install.sh [--tool TOOL] [--skill SKILL] [--install-dir DIR] [--dry-run]

Install or prepare skills for supported AI coding tools.

Direct installs:
  codex        -> ${CODEX_HOME:-~/.codex}/skills
  claude-code  -> ~/.claude/skills
  copilot      -> <install-dir or current directory>/.github/instructions

Other tools are converted into dist/<tool>/<skill>/ for manual import.

Options:
  --tool TOOL       Install/prepare one tool. Without this, auto-detect direct tools.
  --skill SKILL     Install/prepare one skill. Defaults to all skills.
  --install-dir DIR Override install target. For copilot, this is the target project.
  --dry-run         Print actions without writing files.
  --list-tools      Print supported tool names.
  -h, --help        Show this help.

Examples:
  ./scripts/install.sh
  ./scripts/install.sh --tool codex
  ./scripts/install.sh --tool claude-code
  ./scripts/install.sh --tool copilot --install-dir /path/to/project
  ./scripts/install.sh --tool cursor
EOF
}

is_supported_tool() {
  local tool="$1"
  local candidate
  for candidate in "${TOOLS[@]}"; do
    [[ "$candidate" == "$tool" ]] && return 0
  done
  return 1
}

list_tools() {
  printf '%s\n' "${TOOLS[@]}"
}

find_skills() {
  local skill_filter="$1"
  local skill_dir
  for skill_dir in "$REPO_ROOT"/*; do
    [[ -d "$skill_dir" ]] || continue
    [[ -f "$skill_dir/SKILL.md" ]] || continue
    if [[ -n "$skill_filter" && "$(basename "$skill_dir")" != "$skill_filter" ]]; then
      continue
    fi
    basename "$skill_dir"
  done
}

run() {
  if [[ "$DRY_RUN" == "1" ]]; then
    printf '[dry-run] %q' "$1"
    shift
    printf ' %q' "$@"
    printf '\n'
  else
    "$@"
  fi
}

backup_existing() {
  local target="$1"
  if [[ -e "$target" ]]; then
    local backup="$target.bak.$(date +%Y%m%d%H%M%S)"
    echo "Existing target found. Moving to $backup"
    run mv "$target" "$backup"
  fi
}

copy_skill_dir() {
  local skill="$1"
  local target_base="$2"
  local source="$REPO_ROOT/$skill"
  local target="$target_base/$skill"

  echo "Installing $skill -> $target"
  run mkdir -p "$target_base"
  backup_existing "$target"
  run cp -R "$source" "$target"
}

install_codex() {
  local target_base="${INSTALL_DIR:-${CODEX_HOME:-$HOME/.codex}/skills}"
  local skill
  for skill in "${skills[@]}"; do
    copy_skill_dir "$skill" "$target_base"
  done
}

install_claude_code() {
  local target_base="${INSTALL_DIR:-$HOME/.claude/skills}"
  local skill
  for skill in "${skills[@]}"; do
    copy_skill_dir "$skill" "$target_base"
  done
}

install_copilot() {
  local project_dir="${INSTALL_DIR:-$PWD}"
  local target_base="$project_dir/.github/instructions"
  local skill source

  if [[ "$DRY_RUN" == "1" ]]; then
    echo "[dry-run] $CONVERT_SCRIPT --tool copilot${SKILL_FILTER:+ --skill $SKILL_FILTER}"
  elif [[ -n "$SKILL_FILTER" ]]; then
    "$CONVERT_SCRIPT" --tool copilot --skill "$SKILL_FILTER"
  else
    "$CONVERT_SCRIPT" --tool copilot
  fi
  run mkdir -p "$target_base"

  for skill in "${skills[@]}"; do
    source="$REPO_ROOT/dist/copilot/$skill/$skill.instructions.md"
    echo "Installing $skill Copilot instructions -> $target_base/$skill.instructions.md"
    backup_existing "$target_base/$skill.instructions.md"
    run cp "$source" "$target_base/$skill.instructions.md"
  done
}

convert_only() {
  local tool="$1"
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "[dry-run] $CONVERT_SCRIPT --tool $tool${SKILL_FILTER:+ --skill $SKILL_FILTER}"
  elif [[ -n "$SKILL_FILTER" ]]; then
    "$CONVERT_SCRIPT" --tool "$tool" --skill "$SKILL_FILTER"
  else
    "$CONVERT_SCRIPT" --tool "$tool"
  fi
  echo "Converted package is ready under $REPO_ROOT/dist/$tool/"
  echo "Import that package using $tool's custom-instructions or plugin mechanism."
}

detect_direct_tools() {
  detected_tools=()
  if [[ -d "${CODEX_HOME:-$HOME/.codex}" ]] || command -v codex >/dev/null 2>&1; then
    detected_tools+=(codex)
  fi
  if [[ -d "$HOME/.claude" ]] || command -v claude >/dev/null 2>&1 || command -v claude-code >/dev/null 2>&1; then
    detected_tools+=(claude-code)
  fi
}

install_for_tool() {
  local tool="$1"
  case "$tool" in
    codex)
      install_codex
      ;;
    claude-code)
      install_claude_code
      ;;
    copilot)
      install_copilot
      ;;
    *)
      convert_only "$tool"
      ;;
  esac
}

TOOL_FILTER=""
SKILL_FILTER=""
INSTALL_DIR=""
DRY_RUN="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tool)
      TOOL_FILTER="${2:-}"
      shift 2
      ;;
    --skill)
      SKILL_FILTER="${2:-}"
      shift 2
      ;;
    --install-dir)
      INSTALL_DIR="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN="1"
      shift
      ;;
    --list-tools)
      list_tools
      exit 0
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -n "$TOOL_FILTER" ]] && ! is_supported_tool "$TOOL_FILTER"; then
  echo "Unsupported tool: $TOOL_FILTER" >&2
  echo "Supported tools:" >&2
  list_tools >&2
  exit 2
fi

skills=()
while IFS= read -r skill_name; do
  skills+=("$skill_name")
done < <(find_skills "$SKILL_FILTER")
if [[ "${#skills[@]}" -eq 0 ]]; then
  echo "No skills found${SKILL_FILTER:+ matching '$SKILL_FILTER'}." >&2
  exit 1
fi

if [[ -n "$TOOL_FILTER" ]]; then
  install_for_tool "$TOOL_FILTER"
else
  detect_direct_tools
  if [[ "${#detected_tools[@]}" -eq 0 ]]; then
    echo "No direct-install tools detected. Generating converted packages for all supported tools."
    if [[ "$DRY_RUN" == "1" ]]; then
      echo "[dry-run] $CONVERT_SCRIPT${SKILL_FILTER:+ --skill $SKILL_FILTER}"
    elif [[ -n "$SKILL_FILTER" ]]; then
      "$CONVERT_SCRIPT" --skill "$SKILL_FILTER"
    else
      "$CONVERT_SCRIPT"
    fi
  else
    for tool in "${detected_tools[@]}"; do
      install_for_tool "$tool"
    done
  fi
fi
