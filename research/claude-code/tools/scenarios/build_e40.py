"""Build the Stop-hook cap scenario. usage: build_e40.py <exp id> -> prints fault JSON path"""
import json
import os
import sys

exp = sys.argv[1]
LAB = r"C:/Users/sergi/cc-rea-lab"
RAW = r"C:/Users/sergi/Desktop/claude-rea/lab/raw"
proj = f"{LAB}/proj-{exp.lower()}"
os.makedirs(f"{proj}/.claude", exist_ok=True)
hook = f"{proj}/.claude/always_block.py"
open(hook, "w").write(
    "import json, os, sys\n"
    "d = json.loads(sys.stdin.read() or '{}')\n"
    "log = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stop_calls.jsonl')\n"
    "open(log, 'a').write(json.dumps({'stop_hook_active': d.get('stop_hook_active'), 'event': d.get('hook_event_name')}) + '\\n')\n"
    "print(json.dumps({'decision': 'block', 'reason': 'LAB_ALWAYS_BLOCK keep going'}))\n"
)
json.dump({"hooks": {"Stop": [{"hooks": [{"type": "command", "command": f"python {hook}"}]}]}},
          open(f"{proj}/.claude/settings.json", "w"))
log = f"{proj}/.claude/stop_calls.jsonl"
if os.path.exists(log):
    os.remove(log)


def text(value):
    return {"model": "claude-haiku-5-5", "stop_reason": "end_turn", "content": [{"type": "text", "text": value}]}


fault = {"path_contains": "/v1/messages",
         "sequence": [{"body_contains": "STOP-CAP-LAB", "response": text(f"reply-{i}")} for i in range(1, 16)],
         "otherwise": {"status": 400, "body": {"type": "error", "error": {
             "type": "invalid_request_error", "message": "lab otherwise"}}}}
os.makedirs(f"{RAW}/{exp}/http", exist_ok=True)
json.dump(fault, open(f"{RAW}/{exp}/http/fault.json", "w"))
print(proj)
