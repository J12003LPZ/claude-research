"""Run the E50 `explore` scenario once per parent model and record the model each /v1/messages request carried.
usage: MODE=explore|gpmodel|gpplain|exploremodel|planplain run_matrix_e90_routing.py <tag> <model[,model...]> [ENV=VALUE ...]
Experiment ids are E90<tag>-<model>. Scripted proxy only: no upstream model call.
Writes runtime-logs/<id>/routing-probe.json: parent request model, child request model, tool counts.
"""
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
RAW = "C:/Users/sergi/Desktop/claude-rea/lab/raw"


def summarize(exp):
    reqs = []
    for f in sorted(glob.glob(f"{RAW}/{exp}/http/*-req.json")):
        d = json.load(open(f, encoding="utf-8"))
        b = d["body"] if isinstance(d.get("body"), dict) else d
        tools = [t.get("name") for t in b.get("tools", [])]
        first = b["messages"][0]["content"] if b.get("messages") else ""
        first = first if isinstance(first, str) else " ".join(x.get("text", "") for x in first if isinstance(x, dict))
        reqs.append({
            "model": b.get("model"),
            "tool_count": len(tools),
            "has_write": "Write" in tools,
            "child": "EXPLORE-CHILD" in first,
            "max_tokens": b.get("max_tokens"),
            "thinking": (b.get("thinking") or {}).get("type"),
            "effort": (b.get("output_config") or {}).get("effort"),
        })
    return reqs


tag = sys.argv[1]
models = sys.argv[2].split(",")
extra = dict(a.split("=", 1) for a in sys.argv[3:])
for model in models:
    exp = "".join(c if c.isalnum() or c in "_-" else "_" for c in f"E90{tag}-{model}")
    env = dict(os.environ, MODEL=model, E50_ENV=" ".join(f"{k}={v}" for k, v in extra.items()))
    subprocess.run(["bash", os.path.join(HERE, "run_e50.sh"), exp, os.environ.get("MODE", "explore")], cwd=ROOT, env=env,
                   capture_output=True, text=True, timeout=300)
    reqs = summarize(exp)
    out_dir = os.path.join(ROOT, "research/claude-code/runtime-logs", exp)
    os.makedirs(out_dir, exist_ok=True)
    json.dump({"exp": exp, "parent_model_flag": model, "mode": os.environ.get("MODE", "explore"), "env": extra, "requests": reqs},
              open(os.path.join(out_dir, "routing-probe.json"), "w", encoding="utf-8"), indent=1)
    print(exp, "|", " -> ".join(f"{r['model']}({r['tool_count']}t{',child' if r['child'] else ''})" for r in reqs))
