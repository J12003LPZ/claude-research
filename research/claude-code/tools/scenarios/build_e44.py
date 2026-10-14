"""Subagent limit scenarios with a scripted model.
usage: build_e44.py <exp id> <depth|conc|fail|maxtok> [n]
  depth  root -> L1 -> L2 -> L3 -> (L4 attempted): the depth cap
  conc   one assistant message with n parallel Agent calls (default 22): the concurrency cap
  fail   the child's first request gets no scripted reply (400): a child failing mid-run
  maxtok replies cut by max_tokens with real text: output-token recovery replay
Prints the project dir. Run with run_exp.py, bypassPermissions, prompt 'ROOT-LAB start'.
"""
import json
import os
import sys

exp, mode = sys.argv[1], sys.argv[2]
if not exp or any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-" for ch in exp):
    raise SystemExit("exp id must contain only ASCII letters, digits, '_' or '-'")
n = int(sys.argv[3]) if len(sys.argv) > 3 else 22
LAB = r"C:/Users/sergi/cc-rea-lab"
RAW = r"C:/Users/sergi/Desktop/claude-rea/lab/raw"
proj = f"{LAB}/proj-{exp.lower()}"
os.makedirs(proj, exist_ok=True)


def text(value):
    return {"model": "claude-haiku-5-5", "stop_reason": "end_turn", "content": [{"type": "text", "text": value}]}


def agent(tool_id, prompt, background=False):
    return {"type": "tool_use", "id": tool_id, "name": "Agent",
            "input": {"description": f"lab {prompt}", "prompt": prompt, "subagent_type": "general-purpose",
                      "run_in_background": background}}


def calls(*blocks):
    return {"model": "claude-haiku-5-5", "stop_reason": "tool_use", "content": list(blocks)}


seq = []
if mode == "depth":
    c = {k: f"toolu_dep_{k}" for k in range(1, 5)}
    # level k (0 = root) asks level k+1; levels 1..3 also ask one deeper, level 3's ask (L4) must be refused
    for k in range(0, 4):
        marker = "ROOT-LAB" if k == 0 else f"LEVEL-{k}"
        not_in = [c[k + 1]] + ([c[k]] if k >= 1 else [])
        seq.append({"body_contains": marker, "body_not_contains": not_in,
                    "response": calls(agent(c[k + 1], f"LEVEL-{k + 1}"))})
        seq.append({"body_contains": c[k + 1], "body_not_contains": ([c[k]] if k >= 1 else []),
                    "response": text(f"level-{k}-done")})
elif mode == "conc":
    ids = [f"toolu_par_{i}" for i in range(1, n + 1)]
    seq.append({"body_contains": "ROOT-LAB", "body_not_contains": [ids[0]],
                "response": calls(*[agent(i, f"PAR-CHILD-{j}") for j, i in enumerate(ids, 1)])})
    for _ in ids:
        seq.append({"body_contains": "PAR-CHILD", "body_not_contains": [ids[0]], "response": text("child-done")})
    seq.append({"body_contains": ids[0], "response": text("root-done")})
elif mode == "fail":
    seq.append({"body_contains": "ROOT-LAB", "body_not_contains": ["toolu_fail_1"],
                "response": calls(agent("toolu_fail_1", "FAIL-CHILD run"))})
    seq.append({"body_contains": "toolu_fail_1", "response": text("root-saw-failure")})
    # no entry for the child's own first request: it falls to `otherwise` (HTTP 400)
elif mode == "maxtok":
    # Three replies cut by max_tokens with real text, then a normal end: does partial text replay?
    for part in ("PARTIAL-ONE", "PARTIAL-TWO", "PARTIAL-THREE"):
        seq.append({"body_contains": "ROOT-LAB",
                    "response": {"model": "claude-haiku-5-5", "stop_reason": "max_tokens",
                                 "content": [{"type": "text", "text": f"{part} words words words"}]}})
    seq.append({"body_contains": "ROOT-LAB", "response": text("FINAL-DONE")})
else:
    raise SystemExit("mode must be depth, conc, fail or maxtok")

fault = {"path_contains": "/v1/messages", "sequence": seq,
         "otherwise": {"status": 400, "body": {"type": "error", "error": {
             "type": "invalid_request_error", "message": "lab otherwise"}}}}
os.makedirs(f"{RAW}/{exp}/http", exist_ok=True)
json.dump(fault, open(f"{RAW}/{exp}/http/fault.json", "w"))
print(proj)
