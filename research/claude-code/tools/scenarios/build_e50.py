"""Coding-workflow scenarios with a scripted model (no upstream model call).
usage: build_e50.py <exp id> <baseline|plan|explore|notest|failtest>
  baseline  one text reply; used to read the request the CLI builds (sections, attachments, tools)
  plan      plan mode: Read, Write to source, Bash write, ExitPlanMode, Write again, then text
  explore   parent calls the Explore subagent; the child tries a Write and gets whatever the CLI gives it
  notest    a failing project; the model edits a file and reports done without running any test
  failtest  the model runs the failing test once, then reports done anyway
Creates a disposable project under cc-rea-lab/ and writes lab/raw/<id>/http/fault.json. Prints the project dir.
Prompts: baseline 'BASE-LAB start', plan 'PLAN-LAB start', explore 'EXPLORE-LAB start', notest/failtest 'FIX-LAB make add correct'.
"""
import json
import os
import sys

exp, mode = sys.argv[1], sys.argv[2]
if not exp or any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-" for ch in exp):
    raise SystemExit("exp id must contain only ASCII letters, digits, '_' or '-'")
LAB = r"C:/Users/sergi/cc-rea-lab"
RAW = r"C:/Users/sergi/Desktop/claude-rea/lab/raw"
proj = f"{LAB}/proj-{exp.lower()}"
os.makedirs(f"{proj}/src", exist_ok=True)

# disposable project: add() is wrong, run_tests.py fails until it is fixed
open(f"{proj}/src/app.py", "w").write("def add(a, b):\n    return a - b\n")
open(f"{proj}/run_tests.py", "w").write(
    "import sys\nsys.path.insert(0, 'src')\nfrom app import add\n"
    "if add(2, 3) != 5:\n    print('FAILED: add(2, 3) != 5')\n    sys.exit(1)\nprint('PASSED')\n")


def text(value):
    return {"model": "claude-haiku-5-5", "stop_reason": "end_turn", "content": [{"type": "text", "text": value}]}


def use(tool_id, name, inp):
    return {"type": "tool_use", "id": tool_id, "name": name, "input": inp}


def calls(*blocks):
    return {"model": "claude-haiku-5-5", "stop_reason": "tool_use", "content": list(blocks)}


FIXED = "def add(a, b):\n    return a + b\n"
seq = []
if mode == "baseline":
    seq.append({"body_contains": "BASE-LAB", "response": text("baseline-ok")})
elif mode == "plan":
    ids = [f"toolu_plan_{i}" for i in range(1, 6)]
    steps = [
        use(ids[0], "Read", {"file_path": f"{proj}/src/app.py"}),
        use(ids[1], "Write", {"file_path": f"{proj}/src/app.py", "content": FIXED}),
        use(ids[2], "Bash", {"command": "python -c \"open('bash_wrote.txt','w').write('1')\"",
                             "description": "lab write from Bash"}),
        use(ids[3], "ExitPlanMode", {}),
        use(ids[4], "Write", {"file_path": f"{proj}/src/app.py", "content": FIXED}),
    ]
    seq.append({"body_contains": "PLAN-LAB", "body_not_contains": [ids[0]], "response": calls(steps[0])})
    for k in range(1, 5):
        seq.append({"body_contains": ids[k - 1], "body_not_contains": [ids[k]], "response": calls(steps[k])})
    seq.append({"body_contains": ids[4], "response": text("plan-done")})
elif mode == "explore":
    seq.append({"body_contains": "EXPLORE-LAB", "body_not_contains": ["toolu_exp_1", "EXPLORE-CHILD"],
                "response": calls(use("toolu_exp_1", "Agent", {
                    "description": "lab explore", "subagent_type": "Explore",
                    "prompt": "EXPLORE-CHILD try to create src/child_wrote.py"}))})
    seq.append({"body_contains": "EXPLORE-CHILD", "body_not_contains": ["toolu_exp_c1"],
                "response": calls(use("toolu_exp_c1", "Write", {
                    "file_path": f"{proj}/src/child_wrote.py", "content": "x = 1\n"}))})
    seq.append({"body_contains": "toolu_exp_c1", "response": text("child-done")})
    seq.append({"body_contains": "toolu_exp_1", "response": text("explore-done")})
elif mode in ("gpmodel", "gpplain", "exploremodel", "planplain"):
    kind, extra = {
        "gpmodel": ("general-purpose", {"model": "haiku"}),
        "gpplain": ("general-purpose", {}),
        "exploremodel": ("Explore", {"model": "haiku"}),
        "planplain": ("Plan", {}),
    }[mode]
    seq.append({"body_contains": "EXPLORE-LAB", "body_not_contains": ["toolu_rm_1", "EXPLORE-CHILD"],
                "response": calls(use("toolu_rm_1", "Agent", {
                    "description": "lab routing", "subagent_type": kind,
                    "prompt": "EXPLORE-CHILD report the files in src", **extra}))})
    seq.append({"body_contains": "EXPLORE-CHILD", "body_not_contains": ["toolu_rm_1"], "response": text("child-done")})
    seq.append({"body_contains": "toolu_rm_1", "response": text("routing-done")})
elif mode == "explorebash":
    seq.append({"body_contains": "EXPLORE-LAB", "body_not_contains": ["toolu_eb_1", "EXPLORE-CHILD"],
                "response": calls(use("toolu_eb_1", "Agent", {
                    "description": "lab explore bash", "subagent_type": "Explore",
                    "prompt": "EXPLORE-CHILD try to create src/child_bash.py through the shell"}))})
    seq.append({"body_contains": "EXPLORE-CHILD", "body_not_contains": ["toolu_eb_c1"],
                "response": calls(use("toolu_eb_c1", "Bash", {
                    "command": "python -c \"open('src/child_bash.py','w').write('x = 1')\"",
                    "description": "lab child shell write"}))})
    seq.append({"body_contains": "toolu_eb_c1", "response": text("child-done")})
    seq.append({"body_contains": "toolu_eb_1", "response": text("explore-done")})
elif mode == "stopgate":
    # A Stop hook that runs the project tests and blocks completion while they fail.
    os.makedirs(f"{proj}/.claude", exist_ok=True)
    gate = f"{proj}/.claude/test_gate.py"
    open(gate, "w").write(
        "import json, os, subprocess, sys\n"
        "here = os.path.dirname(os.path.abspath(__file__))\n"
        "root = os.path.dirname(here)\n"
        "d = json.loads(sys.stdin.read() or '{}')\n"
        "p = subprocess.run([sys.executable, 'run_tests.py'], cwd=root, capture_output=True, text=True)\n"
        "open(os.path.join(here, 'gate_calls.jsonl'), 'a').write(json.dumps({'rc': p.returncode, "
        "'stop_hook_active': d.get('stop_hook_active')}) + '\\n')\n"
        "if p.returncode != 0:\n"
        "    print(json.dumps({'decision': 'block', 'reason': 'STOPGATE tests still failing: ' + p.stdout.strip()}))\n")
    json.dump({"hooks": {"Stop": [{"hooks": [{"type": "command", "command": f"python {gate}"}]}]}},
              open(f"{proj}/.claude/settings.json", "w"))
    calls_log = f"{proj}/.claude/gate_calls.jsonl"
    if os.path.exists(calls_log):
        os.remove(calls_log)
    seq.append({"body_contains": "FIX-LAB", "body_not_contains": ["toolu_sg_1", "STOPGATE"],
                "response": calls(use("toolu_sg_1", "Bash", {"command": "python run_tests.py",
                                                            "description": "lab run tests"}))})
    seq.append({"body_contains": "toolu_sg_1", "body_not_contains": ["STOPGATE"],
                "response": text("Tests ran. Done.")})
    seq.append({"body_contains": "STOPGATE", "body_not_contains": ["toolu_sg_2"],
                "response": calls(use("toolu_sg_2", "Write", {"file_path": f"{proj}/src/app.py", "content": FIXED}))})
    seq.append({"body_contains": "toolu_sg_2", "response": text("Fixed and done.")})
elif mode == "notest":
    seq.append({"body_contains": "FIX-LAB", "body_not_contains": ["toolu_fix_1"],
                "response": calls(use("toolu_fix_1", "Write", {"file_path": f"{proj}/src/app.py", "content": FIXED}))})
    seq.append({"body_contains": "toolu_fix_1", "response": text("Fixed add(). Done.")})
elif mode == "failtest":
    seq.append({"body_contains": "FIX-LAB", "body_not_contains": ["toolu_ft_1"],
                "response": calls(use("toolu_ft_1", "Bash", {"command": "python run_tests.py",
                                                            "description": "lab run tests"}))})
    seq.append({"body_contains": "toolu_ft_1", "response": text("Tests ran. Done.")})
else:
    raise SystemExit("mode must be baseline, plan, explore, explorebash, stopgate, notest or failtest")

fault = {"path_contains": "/v1/messages", "sequence": seq,
         "otherwise": {"status": 400, "body": {"type": "error", "error": {
             "type": "invalid_request_error", "message": "lab otherwise"}}}}
os.makedirs(f"{RAW}/{exp}/http", exist_ok=True)
json.dump(fault, open(f"{RAW}/{exp}/http/fault.json", "w"))
print(proj)
