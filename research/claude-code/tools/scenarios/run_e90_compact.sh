#!/usr/bin/env bash
# usage: [UTIL_BYTES=n UTIL_WIDTH=w COUNT_TOKENS=n] run_e90_compact.sh <base id> [arm] [model]
# Three scripted invocations against one session: turn, /compact, first turn after compaction.
# No upstream model call. Refuses to reuse an existing raw id (never deletes). Optional arm selects the
# summary prompt arm through CLAUDE_CODE_CURRIED_TRINKET (control, lean, short, short_v2, capped).
cd "$(dirname "$0")/../../../.." || exit 1
set -o pipefail
BASE=$1; ARM=${2:-}; MODEL=${3:-haiku}
case "$BASE" in ''|*[!A-Za-z0-9_-]*) printf 'invalid id: %s\n' "$BASE" >&2; exit 2 ;; esac
RAW="C:/Users/sergi/Desktop/claude-rea/lab/raw"
for s in 1-turn 2-compact 3-after; do
  if [ -e "$RAW/$BASE$s/stdout.jsonl" ]; then printf 'raw id already used: %s%s\n' "$BASE" "$s" >&2; exit 3; fi
done
PROJ=$(python -I research/claude-code/tools/scenarios/build_e90_compact.py "$BASE" "${UTIL_BYTES:-0}" "${UTIL_WIDTH:-80}" "${COUNT_TOKENS:-1000}") || exit 1
ENVARGS=(--env 'CLAUDE_CONFIG_DIR=C:/Users/sergi/.claude' --env 'DISABLE_AUTOUPDATER=1')
if [ -n "$ARM" ]; then ENVARGS+=(--env "CLAUDE_CODE_CURRIED_TRINKET=$ARM"); fi
run() { local id="$1" prompt="$2"; shift 2
  CLAUDE_BIN='C:/Users/sergi/.local/share/claude/versions/2.1.296' MSYS_NO_PATHCONV=1 python -I research/claude-code/tools/run_exp.py \
    --id "$id" --cwd "$PROJ" --prompt "$prompt" --timeout 180 --fault "$(cat "$RAW/$id/http/fault.json")" "${ENVARGS[@]}" \
    -- --model "$MODEL" --setting-sources project,local --strict-mcp-config --mcp-config 'C:/Users/sergi/cc-rea-lab/empty-mcp.json' \
    --permission-mode bypassPermissions "$@" 2>&1 | cut -c1-200; }
run "${BASE}1-turn" 'COMPACT-LAB turn1: fix add and run the tests'
SID=$(python -I -c "
import json
for l in open(r'$RAW/${BASE}1-turn/stdout.jsonl',encoding='utf-8'):
    o=json.loads(l)
    if o.get('type')=='system' and o.get('subtype')=='init': print(o['session_id']); break")
[ -n "$SID" ] || { echo 'no session id'; exit 4; }
run "${BASE}2-compact" '/compact Keep the token.' --resume "$SID"
run "${BASE}3-after" 'COMPACT-LAB after' --resume "$SID"
echo "session=$SID"
