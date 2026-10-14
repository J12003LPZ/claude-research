#!/usr/bin/env bash
# usage: run_e46.sh <id> <hooks|permreq> [extra claude args...]
# Hook-event coverage with a scripted model. Prints the events that fired.
cd "$(dirname "$0")/../../../.." || exit 1
set -o pipefail
ID=$1; MODE=$2; shift 2
case "$ID" in
  ''|*[!A-Za-z0-9_-]*) printf 'invalid experiment id: %s\n' "$ID" >&2; exit 2 ;;
esac
case "$MODE" in
  hooks|permreq) ;;
  *) printf 'invalid mode: %s\n' "$MODE" >&2; exit 2 ;;
esac
rm -rf "lab/raw/$ID"   # validated experiment id; this experiment's own raw dir only
PROJ=$(python -I research/claude-code/tools/scenarios/build_e46.py "$ID" "$MODE") || exit 1
F=$(cat "lab/raw/$ID/http/fault.json")
if [ "$MODE" = hooks ]; then PROMPT='/lab ROOT-LAB go'; PM=(--permission-mode bypassPermissions); else PROMPT='ROOT-LAB write the file'; PM=(); fi
CLAUDE_BIN='C:/Users/sergi/.local/share/claude/versions/2.1.296' MSYS_NO_PATHCONV=1 python -I research/claude-code/tools/run_exp.py \
  --id "$ID" --cwd "$PROJ" --prompt "$PROMPT" --timeout 120 \
  --env 'CLAUDE_CONFIG_DIR=C:/Users/sergi/.claude' --env 'DISABLE_AUTOUPDATER=1' \
  --env "LAB_HOOK_LOG_DIR=C:/Users/sergi/Desktop/claude-rea/lab/raw/$ID" --fault "$F" \
  -- --model haiku --setting-sources project,local --strict-mcp-config --mcp-config 'C:/Users/sergi/cc-rea-lab/empty-mcp.json' \
  "${PM[@]}" "$@" 2>&1 | cut -c1-160 || exit $?
python -I research/claude-code/tools/summarize_captures.py "$ID" >/dev/null
python -I research/claude-code/tools/hooks_summary.py "$ID" >/dev/null
python -I - "$ID" <<'PY'
import collections,json,sys
I=sys.argv[1]
h=json.load(open('research/claude-code/runtime-logs/%s/hooks-summary.json'%I))
c=collections.Counter(e.get('hook_event_name') or e['tag'] for e in h)
print('hook invocations',len(h),'distinct events',len(c))
print(dict(c))
s=json.load(open('research/claude-code/runtime-logs/%s/stream-summary.json'%I))
print('results',s['results'])
PY
