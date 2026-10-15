"""Summarize which model-gated prompt sections a lab run's main request carried.
usage: python -I prompt_sections_probe.py EXPID [EXPID ...]
Reads lab/raw/<id>/http/*-req.json (private, uncommitted) and writes runtime-logs/<id>/prompt-sections.json
with booleans only: no prompt text is copied. Markers are short literals from the 2.1.296 prompt sections.
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_ROOT = os.path.abspath(os.path.join(HERE, "..", "runtime-logs"))
RAW = os.environ.get("LAB_RAW", "C:/Users/sergi/Desktop/claude-rea/lab/raw")

MARKERS = {
    "delivering_work": "# Delivering work",
    "corrections": "# Corrections",
    "autonomy_block": "You are operating autonomously",
    "explore_nudge": "more than 3 queries",
    "prefer_dedicated_tools_full": "Prefer dedicated tools over Bash",
    "prefer_dedicated_tools_lean": "Prefer the dedicated file/search tools over shell commands",
    "read_before_edit_text": "Read it first",
}


def flatten(system):
    if isinstance(system, str):
        return system
    return "\n".join(x.get("text", "") for x in system or [] if isinstance(x, dict))


def summarize(exp):
    files = sorted(glob.glob(f"{RAW}/{exp}/http/*-req.json"))
    best = None
    for f in files:
        d = json.load(open(f, encoding="utf-8"))
        b = d["body"] if isinstance(d.get("body"), dict) else d
        if len(b.get("tools", [])) >= 20 and b.get("system"):
            best = b
            break
    if best is None:
        return None
    text = flatten(best.get("system"))
    return {
        "exp": exp,
        "model": best.get("model"),
        "tool_count": len(best.get("tools", [])),
        "system_chars": len(text),
        "markers": {k: (v in text) for k, v in MARKERS.items()},
        "thinking": (best.get("thinking") or {}).get("type"),
        "effort": (best.get("output_config") or {}).get("effort"),
        "max_tokens": best.get("max_tokens"),
    }


if __name__ == "__main__":
    for exp in sys.argv[1:]:
        r = summarize(exp)
        if r is None:
            print(exp, "NO MAIN REQUEST")
            continue
        out = os.path.join(OUT_ROOT, exp)
        os.makedirs(out, exist_ok=True)
        json.dump(r, open(os.path.join(out, "prompt-sections.json"), "w", encoding="utf-8"), indent=1)
        print(exp, r["model"], r["tool_count"], "tools", {k: int(v) for k, v in r["markers"].items()},
              "effort", r["effort"], "thinking", r["thinking"], "max_tokens", r["max_tokens"])
