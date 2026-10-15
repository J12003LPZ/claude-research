#!/usr/bin/env bash
# usage: [AFTER_EDITS=1 UTIL_BYTES=n COUNT_TOKENS=n] run_e90_compact_1p.sh <base id> [arm] [model]
# The same scenario as run_e90_compact.sh in ONE process (stream-json input): turn, /compact, turn.
# That keeps the in-memory state a separate --resume process would lose. No upstream model call.
cd "$(dirname "$0")/../../../.." || exit 1
set -o pipefail
BASE=$1; ARM=${2:-}; MODEL=${3:-haiku}
case "$BASE" in ''|*[!A-Za-z0-9_-]*) printf 'invalid id: %s\n' "$BASE" >&2; exit 2 ;; esac
RAW="C:/Users/sergi/Desktop/claude-rea/lab/raw"
if [ -e "$RAW/${BASE}0-single/stdout.jsonl" ]; then printf 'raw id already used: %s0-single\n' "$BASE" >&2; exit 3; fi
PROJ=$(python -I research/claude-code/tools/scenarios/build_e90_compact.py "$BASE" "${UTIL_BYTES:-0}" "${UTIL_WIDTH:-80}" "${COUNT_TOKENS:-1000}") || exit 1
ENVARGS=(--env 'CLAUDE_CONFIG_DIR=C:/Users/sergi/.claude' --env 'DISABLE_AUTOUPDATER=1')
if [ -n "$ARM" ]; then ENVARGS+=(--env "CLAUDE_CODE_CURRIED_TRINKET=$ARM"); fi
SCRIPT="$RAW/${BASE}0-single/script.json"
python -I - "$SCRIPT" <<'PY'
import json, sys
def user(text):
    return {"type": "user", "message": {"role": "user", "content": text}}
steps = [{"at_s": 0, "send": user("COMPACT-LAB turn1: fix add and run the tests")},
         {"at_s": 8, "send": user("/compact Keep the token.")},
         {"at_s": 14, "send": user("COMPACT-LAB after")},
         {"at_s": 24, "close": True}]
json.dump(steps, open(sys.argv[1], "w"))
PY
CLAUDE_BIN='C:/Users/sergi/.local/share/claude/versions/2.1.296' MSYS_NO_PATHCONV=1 python -I research/claude-code/tools/run_stream.py \
  --id "${BASE}0-single" --cwd "$PROJ" --script "$SCRIPT" --timeout 120 "${ENVARGS[@]}" \
  -- --model "$MODEL" --setting-sources project,local --strict-mcp-config --mcp-config 'C:/Users/sergi/cc-rea-lab/empty-mcp.json' \
  --permission-mode bypassPermissions 2>&1 | cut -c1-200
