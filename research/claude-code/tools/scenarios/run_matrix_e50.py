"""Run the E50 baseline scenario once per model (and optionally per proactivity level) and print what each request carried.
usage: run_matrix_e50.py <tag> <model[,model...]> [level[,level...]]
Experiment ids are E50<tag>-<model>[-<level>]. Scripted proxy only: no upstream model call.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
tag = sys.argv[1]
models = sys.argv[2].split(",")
levels = sys.argv[3].split(",") if len(sys.argv) > 3 else [""]
for model in models:
    for level in levels:
        exp = f"E50{tag}-{model}" + (f"-{level}" if level else "")
        exp = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in exp)
        env = dict(os.environ, MODEL=model)
        args = ["bash", os.path.join(HERE, "run_e50.sh"), exp, "baseline"] + ([level] if level else [])
        subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True, timeout=300)
        subprocess.run([sys.executable, "-I", os.path.join(ROOT, "research/claude-code/tools/coding_workflow_probe.py"), exp],
                       cwd=ROOT, capture_output=True, text=True, timeout=60)
        p = os.path.join(ROOT, "research/claude-code/runtime-logs", exp, "coding-workflow-probe.json")
        try:
            d = json.load(open(p, encoding="utf-8"))
        except OSError:
            print(exp, "NO PROBE OUTPUT")
            continue
        for r in d["requests"]:
            print(exp, "| model", r["model"], "| system blocks", r["system_block_chars"],
                  "| system markers", [k for k, v in r["markers_in_system"].items() if v],
                  "| any-marker", [k for k, v in r["markers"].items() if v and not r["markers_in_system"][k]],
                  "| levels", r["proactivity_levels_found"], "| status", r.get("response_status"))
