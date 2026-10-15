"""Run the read-guard scenarios once per model and permission mode, then write the sanitized probe for each run.
usage: run_matrix_e90.py <tag> <scenario[,scenario...]> <model[,model...]> <perm[,perm...]>
Experiment ids are E90<tag>-<scenario>-<model>-<perm>. Scripted proxy only: no upstream model call.
Prints one line per run: the Write/Edit result (error flag, markers, first line).
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
tag = sys.argv[1]
scenarios = sys.argv[2].split(",")
models = sys.argv[3].split(",")
perms = sys.argv[4].split(",")
for scenario in scenarios:
    for model in models:
        for perm in perms:
            exp = f"E90{tag}-{scenario}-{model}-{perm}"
            exp = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in exp)
            env = dict(os.environ, MODEL=model)
            subprocess.run(["bash", os.path.join(HERE, "run_e90.sh"), exp, scenario, perm], cwd=ROOT, env=env,
                           capture_output=True, text=True, timeout=300)
            subprocess.run([sys.executable, "-I", os.path.join(ROOT, "research/claude-code/tools/exploration_probe.py"), exp],
                           cwd=ROOT, capture_output=True, text=True, timeout=60)
            p = os.path.join(ROOT, "research/claude-code/runtime-logs", exp, "exploration-probe.json")
            try:
                d = json.load(open(p, encoding="utf-8"))
            except OSError:
                print(exp, "NO PROBE OUTPUT")
                continue
            last = d["tool_calls"][-1] if d["tool_calls"] else {}
            print(exp, "| model", d.get("model"), "| mode", d["stream"].get("init_permission_mode"),
                  "| tools", [c["tool"] for c in d["tool_calls"]], "| last err", last.get("is_error"),
                  "| markers", last.get("markers"), "|", last.get("first_line", "")[:90])
