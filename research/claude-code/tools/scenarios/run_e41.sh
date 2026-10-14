#!/usr/bin/env bash
# usage: run_e41.sh <id> <outcomes> [extra claude args...]
cd /c/Users/sergi/Desktop/claude-rea || exit 1
SP="$TEMP/claude/C--Users-sergi-Desktop-claude-rea/84e85a80-1ba0-47e3-bfd6-83e75b4abcb8/scratchpad"
ID=$1; OUT=$2; shift 2
[ -n "$ID" ] && rm -rf "lab/raw/$ID"   # only this experiment own raw dir, so reruns never mix
PROJ=$(python -I "$SP/build_e41.py" "$ID" "$OUT") || exit 1
F=$(cat "lab/raw/$ID/http/fault.json")
CLAUDE_BIN='C:/Users/sergi/.local/share/claude/versions/2.1.296' MSYS_NO_PATHCONV=1 python -I research/claude-code/tools/run_exp.py \
  --id "$ID" --cwd "$PROJ" --prompt 'AUTO-LAB please write the lab files' --timeout 120 \
  --env 'CLAUDE_CONFIG_DIR=C:/Users/sergi/.claude' --env 'DISABLE_AUTOUPDATER=1' --fault "$F" \
  -- --model haiku --setting-sources project,local --strict-mcp-config --mcp-config 'C:/Users/sergi/cc-rea-lab/empty-mcp.json' \
  --permission-mode auto "$@" 2>&1 | cut -c1-160
echo "files: $(ls "$PROJ" | tr '\n' ' ')"
python -I research/claude-code/tools/summarize_captures.py "$ID" >/dev/null
python -I - "$ID" <<'PY'
import json,sys
D='research/claude-code/runtime-logs/%s/'%sys.argv[1]
s=json.load(open(D+'stream-summary.json'))
print('results',s['results'])
print('system events',[(e.get('subtype'),e.get('decision_reason_type')) for e in s['events'] if e['type']=='system' and e.get('subtype') in('permission_denied',)])
h=json.load(open(D+'http-summary.json'))
rows=[]
for x in h:
    r=x['request'];b=r.get('body') if isinstance(r.get('body'),dict) else {}
    if b: rows.append((r['seq'],b.get('model'),'tools' if b.get('tools_count') else 'no-tools',x.get('response',{}).get('mode') or x.get('response',{}).get('status')))
print('requests',rows)
PY
grep -n -E "auto-mode\] (new action|classif)|classifier_request_(started|finished)|Auto mode|denial|too many|permission" "lab/raw/$ID/debug.log" | sed -E 's/^([0-9]+):([0-9T:.-]+)Z \[[A-Z]+\] /\1 /' | cut -c1-210 | head -${LINES_MAX:-26}
