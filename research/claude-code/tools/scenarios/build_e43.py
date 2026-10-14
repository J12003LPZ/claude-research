"""Background agent whose Bash calls are all denied by a scripted classifier (auto mode).
usage: build_e43.py <exp id> <n_denied_calls>
"""
import json
import os
import sys

exp, n = sys.argv[1], int(sys.argv[2])
LAB = r"C:/Users/sergi/cc-rea-lab"
RAW = r"C:/Users/sergi/Desktop/claude-rea/lab/raw"
proj = f"{LAB}/proj-{exp.lower()}"
os.makedirs(proj, exist_ok=True)
CLF1 = '"stop_sequences":["</severity>"]'
CLF2 = '"max_tokens":8192'
PA = "toolu_lab_p_agent"


def text(value, stop="end_turn"):
    return {"model": "claude-haiku-5-5", "stop_reason": stop, "content": [{"type": "text", "text": value}]}


def tool(tool_id, name, tool_input):
    return {"model": "claude-haiku-5-5", "stop_reason": "tool_use",
            "content": [{"type": "tool_use", "id": tool_id, "name": name, "input": tool_input}]}


cmd = "python -c \"print('lab')\""
cids = [f"toolu_lab_c{i}" for i in range(1, n + 1)]
seq = [{"body_contains": CLF1, "response": text("<severity>0", "stop_sequence")}]   # allow the Agent launch itself
for _ in range(n):
    seq.append({"body_contains": CLF1, "response": text("<severity>30", "stop_sequence")})
    seq.append({"body_contains": CLF2, "body_not_contains": [CLF1], "response": text("<severity>90</severity>")})
nc = [CLF1, CLF2]
seq.append({"body_contains": "AUTO-LAB", "body_not_contains": nc + [PA],
            "response": tool(PA, "Agent", {"description": "lab denied agent", "prompt": "CHILD-MARK-1 run the lab command",
                                            "subagent_type": "general-purpose", "run_in_background": True})})
seq.append({"body_contains": PA, "body_not_contains": nc, "response": text("parent-launched")})
seq.append({"body_contains": "CHILD-MARK-1", "body_not_contains": nc + [PA, cids[0]],
            "response": tool(cids[0], "Bash", {"command": cmd, "description": "lab"})})
for k in range(1, n):
    seq.append({"body_contains": cids[k - 1], "body_not_contains": nc + [PA, cids[k]],
                "response": tool(cids[k], "Bash", {"command": cmd, "description": "lab"})})
seq.append({"body_contains": cids[-1], "body_not_contains": nc + [PA], "response": text("CHILD-GAVE-UP")})
fault = {"path_contains": "/v1/messages", "sequence": seq,
         "otherwise": {"status": 400, "body": {"type": "error", "error": {
             "type": "invalid_request_error", "message": "lab otherwise"}}}}
os.makedirs(f"{RAW}/{exp}/http", exist_ok=True)
json.dump(fault, open(f"{RAW}/{exp}/http/fault.json", "w"))

def user(content):
    return {"type": "user", "message": {"role": "user", "content": content}}

script = [{"at_s": 0, "send": user("AUTO-LAB launch the lab agent")}, {"at_s": 12, "close": True}]
sp = os.environ["TEMP"] + f"/{exp}-script.json"
json.dump(script, open(sp, "w"))
print(json.dumps({"proj": proj, "script": sp.replace("\\", "/")}))
