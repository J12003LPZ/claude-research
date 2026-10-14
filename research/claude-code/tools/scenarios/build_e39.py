"""Build one scripted background-agent scenario. usage: build_e39.py <id> <bg|fg> <interrupt|none>"""
import json
import os
import sys

exp, mode, intr = sys.argv[1], sys.argv[2], sys.argv[3]
LAB = r"C:/Users/sergi/cc-rea-lab"
RAW = r"C:/Users/sergi/Desktop/claude-rea/lab/raw"
proj = f"{LAB}/proj-{exp.lower()}"
os.makedirs(proj, exist_ok=True)
for name in ("child-done.txt",):
    p = f"{proj}/{name}"
    if os.path.exists(p):
        os.remove(p)

def text(value):
    return {"model": "claude-haiku-5-5", "stop_reason": "end_turn", "content": [{"type": "text", "text": value}]}

def tool(tool_id, name, tool_input):
    return {"model": "claude-haiku-5-5", "stop_reason": "tool_use",
            "content": [{"type": "tool_use", "id": tool_id, "name": name, "input": tool_input}]}

child_cmd = "python -c \"import time,pathlib; time.sleep(12); pathlib.Path('child-done.txt').write_text('done')\""
parent_cmd = "python -c \"import time; time.sleep(30)\""
PARENT_AGENT, PARENT_BASH, CHILD_BASH = "toolu_lab_parent_agent", "toolu_lab_parent_bash", "toolu_lab_child_bash"

sequence = [
    # The post-interrupt turn first: it matches only the request carrying this marker.
    {"body_contains": "AFTER-INTERRUPT-LAB", "response": text("after-ok")},
    {"body_contains": "START-BG-LAB", "body_not_contains": [PARENT_AGENT],
     "response": tool(PARENT_AGENT, "Agent", {
         "description": "lab background agent", "prompt": "CHILD-MARK-1 run the lab sleep script.",
         "subagent_type": "general-purpose", "run_in_background": mode == "bg"})},
    {"body_contains": "CHILD-MARK-1", "body_not_contains": [PARENT_AGENT, CHILD_BASH],
     "response": tool(CHILD_BASH, "Bash", {"command": child_cmd, "description": "child sleep then marker"})},
    {"body_contains": CHILD_BASH, "body_not_contains": [PARENT_AGENT], "response": text("CHILD-FINISHED")},
    {"body_contains": PARENT_AGENT, "body_not_contains": [PARENT_BASH],
     "response": tool(PARENT_BASH, "Bash", {"command": parent_cmd, "description": "parent long tool"})},
]
fault = {"path_contains": "/v1/messages", "sequence": sequence,
         "otherwise": {"status": 400, "body": {"type": "error", "error": {
             "type": "invalid_request_error", "message": "lab otherwise"}}}}
os.makedirs(f"{RAW}/{exp}/http", exist_ok=True)
json.dump(fault, open(f"{RAW}/{exp}/http/fault.json", "w"))

def user(content):
    return {"type": "user", "message": {"role": "user", "content": content}}

script = [{"at_s": 0, "send": user("START-BG-LAB please launch the lab agent")}]
if intr == "interrupt":
    script.append({"at_s": 6, "send": {"type": "control_request", "request_id": "lab-int-1",
                                       "request": {"subtype": "interrupt"}}})
script.append({"at_s": 10, "send": user("AFTER-INTERRUPT-LAB are you still there")})
script.append({"at_s": 34, "close": True})
sp = os.environ["TEMP"] + f"/{exp}-script.json"
json.dump(script, open(sp, "w"))
print(json.dumps({"proj": proj, "script": sp.replace("\\", "/")}))
