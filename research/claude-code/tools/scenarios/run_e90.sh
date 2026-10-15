#!/usr/bin/env bash
# usage: run_e90.sh <id> <glob|grep|grepsize|grepslow|read|guardw|guarde|guardr> [permission mode|none]
# Runs one exploration-tool or read-guard scenario against the scripted proxy (no upstream model call).
# The model comes from $MODEL (default haiku). Refuses to reuse an experiment id: it never deletes a raw directory.
cd "$(dirname "$0")/../../../.." || exit 1
set -o pipefail
ID=$1; MODE=$2; PERM=${3:-bypassPermissions}
case "$ID" in
  ''|*[!A-Za-z0-9_-]*) printf 'invalid experiment id: %s\n' "$ID" >&2; exit 2 ;;
esac
case "$MODE" in
  glob|grep|grepsize|grepslow|read|guardw|guarde|guardr) ;;
  *) printf 'invalid mode: %s\n' "$MODE" >&2; exit 2 ;;
esac
if [ -e "C:/Users/sergi/Desktop/claude-rea/lab/raw/$ID" ]; then
  printf 'raw directory for %s already exists; pick a new id\n' "$ID" >&2; exit 3
fi
PROJ=$(python -I research/claude-code/tools/scenarios/build_e90.py "$ID" "$MODE") || exit 1
F=$(cat "C:/Users/sergi/Desktop/claude-rea/lab/raw/$ID/http/fault.json")
ENVARGS=()
if [ -n "$E90_ENV" ]; then ENVARGS=(--env "$E90_ENV"); fi   # one extra NAME=value for the child, e.g. CLAUDE_CODE_GLOB_TIMEOUT_SECONDS=1
PERMARGS=(--permission-mode "$PERM")
if [ "$PERM" = none ]; then PERMARGS=(); fi   # leave the permission mode to the CLI default
CLAUDE_BIN='C:/Users/sergi/.local/share/claude/versions/2.1.296' MSYS_NO_PATHCONV=1 python -I research/claude-code/tools/run_exp.py \
  --id "$ID" --cwd "$PROJ" --prompt 'E90-LAB start' --timeout 120 \
  --env 'CLAUDE_CONFIG_DIR=C:/Users/sergi/.claude' --env 'DISABLE_AUTOUPDATER=1' "${ENVARGS[@]}" --fault "$F" \
  -- --model "${MODEL:-haiku}" --setting-sources project,local --strict-mcp-config --mcp-config 'C:/Users/sergi/cc-rea-lab/empty-mcp.json' \
  "${PERMARGS[@]}" 2>&1 | cut -c1-200
