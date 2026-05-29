#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_ROOT="$REPO_ROOT/dist"

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
Usage: ./scripts/convert.sh [--tool TOOL] [--skill SKILL]

Convert repository skills into tool-specific instruction packages under dist/.

Options:
  --tool TOOL     Convert for one tool. Defaults to all supported tools.
  --skill SKILL   Convert one skill directory. Defaults to all skills.
  --list-tools    Print supported tool names.
  -h, --help      Show this help.

Examples:
  ./scripts/convert.sh
  ./scripts/convert.sh --tool codex
  ./scripts/convert.sh --tool copilot --skill sync-obsidian
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

frontmatter_value() {
  local file="$1"
  local key="$2"
  awk -v key="$key" '
    BEGIN { in_frontmatter=0 }
    NR == 1 && $0 == "---" { in_frontmatter=1; next }
    in_frontmatter && $0 == "---" { exit }
    in_frontmatter && index($0, key ":") == 1 {
      sub(key ":[[:space:]]*", "", $0)
      gsub(/^"|"$/, "", $0)
      print
      exit
    }
  ' "$file"
}

copy_skill_native() {
  local tool="$1"
  local skill="$2"
  local source="$REPO_ROOT/$skill"
  local target="$DIST_ROOT/$tool/$skill"

  rm -rf "$target"
  mkdir -p "$(dirname "$target")"
  cp -R "$source" "$target"
}

write_copilot_package() {
  local skill="$1"
  local source="$REPO_ROOT/$skill"
  local target="$DIST_ROOT/copilot/$skill"
  local name description

  name="$(frontmatter_value "$source/SKILL.md" name)"
  description="$(frontmatter_value "$source/SKILL.md" description)"

  rm -rf "$target"
  mkdir -p "$target"
  cp -R "$source/scripts" "$target/scripts" 2>/dev/null || true

  {
    printf -- "---\n"
    printf "applyTo: \"**\"\n"
    printf -- "---\n\n"
    printf "# %s\n\n" "${name:-$skill}"
    printf "%s\n\n" "${description:-Converted skill instructions.}"
    printf "Use these instructions when the user asks for this workflow. If bundled scripts are present, prefer running or adapting them instead of rewriting large logic.\n\n"
    printf "Original skill instructions follow.\n\n"
    cat "$source/SKILL.md"
  } > "$target/$skill.instructions.md"
}

write_generic_package() {
  local tool="$1"
  local skill="$2"
  local source="$REPO_ROOT/$skill"
  local target="$DIST_ROOT/$tool/$skill"
  local name description

  name="$(frontmatter_value "$source/SKILL.md" name)"
  description="$(frontmatter_value "$source/SKILL.md" description)"

  rm -rf "$target"
  mkdir -p "$target"
  cp -R "$source/scripts" "$target/scripts" 2>/dev/null || true

  {
    printf "# %s\n\n" "${name:-$skill}"
    printf "%s\n\n" "${description:-Converted skill instructions.}"
    printf "This package was generated from a Codex skill for %s. Import or paste the instructions into the target tool according to that tool's custom-instructions mechanism.\n\n" "$tool"
    printf "## Original Skill\n\n"
    cat "$source/SKILL.md"
  } > "$target/INSTRUCTIONS.md"
}

convert_skill() {
  local tool="$1"
  local skill="$2"

  case "$tool" in
    codex|claude-code)
      copy_skill_native "$tool" "$skill"
      ;;
    copilot)
      write_copilot_package "$skill"
      ;;
    *)
      write_generic_package "$tool" "$skill"
      ;;
  esac
}

tool_filter=""
skill_filter=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tool)
      tool_filter="${2:-}"
      shift 2
      ;;
    --skill)
      skill_filter="${2:-}"
      shift 2
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

if [[ -n "$tool_filter" ]] && ! is_supported_tool "$tool_filter"; then
  echo "Unsupported tool: $tool_filter" >&2
  echo "Supported tools:" >&2
  list_tools >&2
  exit 2
fi

skills=()
while IFS= read -r skill_name; do
  skills+=("$skill_name")
done < <(find_skills "$skill_filter")
if [[ "${#skills[@]}" -eq 0 ]]; then
  echo "No skills found${skill_filter:+ matching '$skill_filter'}." >&2
  exit 1
fi

if [[ -n "$tool_filter" ]]; then
  selected_tools=("$tool_filter")
else
  selected_tools=("${TOOLS[@]}")
fi

for tool in "${selected_tools[@]}"; do
  for skill in "${skills[@]}"; do
    convert_skill "$tool" "$skill"
    echo "Converted $skill for $tool -> $DIST_ROOT/$tool/$skill"
  done
done
