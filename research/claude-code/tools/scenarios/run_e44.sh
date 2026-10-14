#!/usr/bin/env bash
# usage: run_e44.sh <id> <depth|conc|fail> [n]
# Runs one subagent-limit scenario against the scripted proxy and prints the facts that matter.
cd "$(dirname "$0")/../../../.." || exit 1
ID=$1; MODE=$2; N=${3:-22}
[ -n "$ID" ] && rm -rf "lab/raw/$ID"   # this experiment's own raw dir only, so reruns never mix
PROJ=$(python -I research/claude-code/tools/scenarios/build_e44.py "$ID" "$MODE" "$N") || exit 1
F=$(cat "lab/raw/$ID/http/fault.json")
CLAUDE_BIN='C:/Users/sergi/.local/share/claude/versions/2.1.296' MSYS_NO_PATHCONV=1 python -I research/claude-code/tools/run_exp.py \
  --id "$ID" --cwd "$PROJ" --prompt 'ROOT-LAB start' --timeout 120 \
  --env 'CLAUDE_CONFIG_DIR=C:/Users/sergi/.claude' --env 'DISABLE_AUTOUPDATER=1' --fault "$F" \
  -- --model haiku --setting-sources project,local --strict-mcp-config --mcp-config 'C:/Users/sergi/cc-rea-lab/empty-mcp.json' \
  --permission-mode bypassPermissions 2>&1 | cut -c1-160
python -I research/claude-code/tools/summarize_captures.py "$ID" >/dev/null
python -I - "$ID" <<'PY'
import json,sys
I=sys.argv[1]
D='research/claude-code/runtime-logs/%s/'%I
s=json.load(open(D+'stream-summary.json'))
print('results',s['results'])
print('result subagent_stats',json.dumps((s['result'] or {}).get('subagent_stats')))
h=json.load(open(D+'http-summary.json'))
rows=[x for x in h if isinstance(x['request'].get('body'),dict)]
mode=[x.get('response',{}).get('mode') or x.get('response',{}).get('status') for x in rows]
print('POST requests',len(rows),'respond',mode.count('respond'),'other',[m for m in mode if m!='respond'])
# raw: text of tool_result blocks that came back for Agent calls (lab strings only)
seen=0
for l in open('lab/raw/%s/stdout.jsonl'%I,encoding='utf-8'):
    try:o=json.loads(l)
    except: continue
    if o.get('type')=='user':
        for b in (o.get('message',{}).get('content') or []):
            if isinstance(b,dict) and b.get('type')=='tool_result' and (b.get('is_error') or seen<3):
                c=b.get('content'); c=c if isinstance(c,str) else ' '.join(x.get('text','') for x in c)
                print(' tool_result is_error=%s: %s'%(b.get('is_error'),c[:170].replace('\n',' '))); seen+=1
PY
