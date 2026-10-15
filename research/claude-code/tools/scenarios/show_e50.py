"""Print the facts that matter for one E50 run: requests, tool results, result event, project file state.
usage: show_e50.py <exp id>   (run coding_workflow_probe.py first)
"""
import json
import os
import subprocess
import sys

exp = sys.argv[1]
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
RAW = r"C:/Users/sergi/Desktop/claude-rea/lab/raw"
subprocess.run([sys.executable, "-I", os.path.join(ROOT, "research/claude-code/tools/coding_workflow_probe.py"), exp],
               cwd=ROOT, capture_output=True, text=True, timeout=60)
d = json.load(open(os.path.join(ROOT, "research/claude-code/runtime-logs", exp, "coding-workflow-probe.json"), encoding="utf-8"))
print("message requests:", d["message_requests"])
for r in d["requests"]:
    print(f" req seq={r['seq']} model={r['model']} tools={len(r['tool_names'])} roles={r['message_roles']} "
          f"plan_active={r['markers']['plan_mode_active']} phase4={r['markers']['plan_phase4']} status={r.get('response_status')}")
    for tr in r["tool_results"]:
        print(f"   tool_result id={tr['tool_use_id']} err={tr['is_error']} :: {tr['text_head'][:200]!r}")
run = json.load(open(os.path.join(RAW, exp, "run.json")))
print("exit_code", run["exit_code"], "duration_s", run["duration_s"])
for line in open(os.path.join(RAW, exp, "stdout.jsonl"), encoding="utf-8"):
    try:
        o = json.loads(line)
    except ValueError:
        continue
    if o.get("type") == "result":
        keep = {k: o.get(k) for k in ("subtype", "is_error", "num_turns", "stop_reason", "permission_denials", "terminal_reason")}
        keep["result_head"] = (o.get("result") or "")[:120]
        print("result:", json.dumps(keep))
proj = f"C:/Users/sergi/cc-rea-lab/proj-{exp.lower()}"
for rel in ("src/app.py", "src/child_wrote.py", "src/child_bash.py", "bash_wrote.txt"):
    p = os.path.join(proj, rel)
    print(" file", rel, "->", repr(open(p).read()) if os.path.exists(p) else "ABSENT")
