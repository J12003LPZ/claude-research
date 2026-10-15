#!/usr/bin/env bash
# usage: run_e50.sh <id> <baseline|plan|explore|notest|failtest> [proactivity: ask|default|proactive] [permission mode]
# Runs one coding-workflow scenario against the scripted proxy (no upstream model call).
cd "$(dirname "$0")/../../../.." || exit 1
set -o pipefail
ID=$1; MODE=$2; PRO=${3:-}; PERM=${4:-bypassPermissions}
case "$ID" in
  ''|*[!A-Za-z0-9_-]*) printf 'invalid experiment id: %s\n' "$ID" >&2; exit 2 ;;
esac
case "$MODE" in
  baseline|plan|explore|explorebash|stopgate|notest|failtest|gpmodel|gpplain|exploremodel|planplain) ;;
  *) printf 'invalid mode: %s\n' "$MODE" >&2; exit 2 ;;
esac
case "$MODE" in
  baseline) PROMPT='BASE-LAB start' ;;
  plan) PROMPT='PLAN-LAB start' ;;
  explore|explorebash|gpmodel|gpplain|exploremodel|planplain) PROMPT='EXPLORE-LAB start' ;;
  *) PROMPT='FIX-LAB make add correct' ;;
esac
rm -rf "C:/Users/sergi/Desktop/claude-rea/lab/raw/$ID"   # validated experiment id; this experiment's own raw dir only
PROJ=$(python -I research/claude-code/tools/scenarios/build_e50.py "$ID" "$MODE") || exit 1
F=$(cat "C:/Users/sergi/Desktop/claude-rea/lab/raw/$ID/http/fault.json")
EXTRA=()
if [ -n "$PRO" ]; then EXTRA=(--proactivity "$PRO"); fi
PERMARGS=(--permission-mode "$PERM")
if [ "$PERM" = none ]; then PERMARGS=(); fi   # leave the permission mode to the CLI default
ENVARGS=()
for kv in $E50_ENV; do ENVARGS+=(--env "$kv"); done   # space-separated NAME=value pairs for the child (run_exp.py scrubs inherited CLAUDE*/ANTHROPIC* vars)
CLAUDE_BIN='C:/Users/sergi/.local/share/claude/versions/2.1.296' MSYS_NO_PATHCONV=1 python -I research/claude-code/tools/run_exp.py \
  --id "$ID" --cwd "$PROJ" --prompt "$PROMPT" --timeout 120 \
  --env 'CLAUDE_CONFIG_DIR=C:/Users/sergi/.claude' --env 'DISABLE_AUTOUPDATER=1' --fault "$F" "${ENVARGS[@]}" \
  -- --model "${MODEL:-haiku}" --setting-sources project,local --strict-mcp-config --mcp-config 'C:/Users/sergi/cc-rea-lab/empty-mcp.json' \
  "${PERMARGS[@]}" "${EXTRA[@]}" 2>&1 | cut -c1-200
