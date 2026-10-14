"""Auto-mode scenario builder (severity classifier).
usage: build_e41.py <exp id> <outcomes>   e.g. "0", "18", "50,50,50,50"
Each outcome is the classifier verdict for one Bash tool call the scripted parent requests, in order.
"""
import json
import os
import sys

exp, outcomes = sys.argv[1], sys.argv[2].split(",")
LAB = r"C:/Users/sergi/cc-rea-lab"
RAW = r"C:/Users/sergi/Desktop/claude-rea/lab/raw"
proj = f"{LAB}/proj-{exp.lower()}"
os.makedirs(proj, exist_ok=True)
for i in range(1, len(outcomes) + 1):
    p = f"{proj}/auto-made-{i}.txt"
    if os.path.exists(p):
        os.remove(p)

CLASSIFIER = '"stop_sequences":["</severity>"]'


def text(value, stop="end_turn"):
    return {"model": "claude-haiku-5-5", "stop_reason": stop, "content": [{"type": "text", "text": value}]}


def tool(tool_id, command):
    return {"model": "claude-haiku-5-5", "stop_reason": "tool_use",
            "content": [{"type": "tool_use", "id": tool_id, "name": "Bash",
                         "input": {"command": command, "description": "lab write"}}]}


def cmd(i):
    return f"python -c \"open('auto-made-{i}.txt','w').write('x')\""


ids = [f"toolu_lab_auto_{i}" for i in range(1, len(outcomes) + 1)]
sequence = []
# Classifier verdicts first: they are the only requests that carry the stop sequence.
STAGE2 = '"max_tokens":8192'
for outcome in outcomes:
    if outcome == "none":      # no scripted classifier reply: the proxy answers it with the otherwise 400
        continue
    s1, _, s2 = outcome.partition(">")
    sequence.append({"body_contains": CLASSIFIER, "response": text(f"<severity>{float(s1):g}", "stop_sequence")})
    if s2:
        sequence.append({"body_contains": STAGE2, "body_not_contains": [CLASSIFIER],
                         "response": text(f"<severity>{float(s2):g}</severity>")})
# Parent turns.
sequence.append({"body_contains": "AUTO-LAB", "body_not_contains": [CLASSIFIER, ids[0]],
                 "response": tool(ids[0], cmd(1))})
for k in range(1, len(ids)):
    sequence.append({"body_contains": ids[k - 1], "body_not_contains": [CLASSIFIER, ids[k]],
                     "response": tool(ids[k], cmd(k + 1))})
sequence.append({"body_contains": ids[-1], "body_not_contains": [CLASSIFIER], "response": text("AUTO-DONE")})
fault = {"path_contains": "/v1/messages", "sequence": sequence,
         "otherwise": {"status": 400, "body": {"type": "error", "error": {
             "type": "invalid_request_error", "message": "lab otherwise"}}}}
os.makedirs(f"{RAW}/{exp}/http", exist_ok=True)
json.dump(fault, open(f"{RAW}/{exp}/http/fault.json", "w"))
print(proj)
