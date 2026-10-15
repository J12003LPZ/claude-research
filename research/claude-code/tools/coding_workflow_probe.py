"""Sanitized summary of the model requests a scripted coding-workflow run produced.

usage: python -I coding_workflow_probe.py <exp id> [--raw-root DIR] [--out DIR]

Reads <raw root>/<id>/http/*-req.json (private, never committed) and writes
runtime-logs/<id>/coding-workflow-probe.json with only: marker presence booleans, tool names, block counts,
byte sizes, and the first characters of tool_result blocks (the lab projects hold synthetic data only).
No prompt text, header, or credential is copied. Markers are fixed strings taken from the extracted 2.1.296 modules
(see static-02 "Coding-workflow layer"), so a True means that exact string was in the request body.
"""
import argparse
import glob
import json
import os
import re

RAW_ROOT = r"C:/Users/sergi/Desktop/claude-rea/lab/raw"
OUT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "runtime-logs")

MARKERS = {
    "doing_tasks_text": "Don't add features, refactor, or introduce abstractions beyond what the task requires",
    "executing_actions_heading": "# Executing actions with care",
    "using_tools_heading": "# Using your tools",
    "proactivity_heading": "## Proactivity: ",
    "plan_mode_active": "Plan mode is active",
    "plan_phase4": "### Phase 4: Final Plan",
    "plan_file_info": "## Plan File Info:",
}
LEVEL_RE = re.compile(r"## Proactivity: (low|medium|high)")


HOME_RE = re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s'\"<>|]+", re.I)
PATH_SEP_RE = re.compile(r"\\{1,2}")


def scrub(text):
    """Mask home-directory names so no account name is emitted, then fold path separators."""
    return PATH_SEP_RE.sub("/", HOME_RE.sub("<home>", text))


def _flat(content):
    if isinstance(content, str):
        return content
    out = []
    for block in content or []:
        if isinstance(block, dict):
            if block.get("type") == "text":
                out.append(block.get("text", ""))
            elif block.get("type") == "tool_result":
                out.append(_flat(block.get("content")))
    return "\n".join(out)


def summarize_request(body):
    system = body.get("system")
    system_text = system if isinstance(system, str) else "\n".join(b.get("text", "") for b in (system or []))
    message_text = "\n".join(_flat(m.get("content")) for m in body.get("messages", []))
    whole = system_text + "\n" + message_text
    levels = sorted(set(LEVEL_RE.findall(whole)))
    results = []
    for m in body.get("messages", []):
        if isinstance(m.get("content"), list):
            for b in m["content"]:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    results.append({"tool_use_id": b.get("tool_use_id"), "is_error": bool(b.get("is_error")),
                                    "text_head": scrub(_flat(b.get("content")))[:240]})
    return {
        "model": body.get("model"),
        "tool_names": [t.get("name") for t in body.get("tools", [])],
        "system_block_chars": [len(b.get("text", "")) for b in system] if isinstance(system, list) else [len(system_text)],
        "message_roles": [m.get("role") for m in body.get("messages", [])],
        "markers": {k: (v in whole) for k, v in MARKERS.items()},
        "markers_in_system": {k: (v in system_text) for k, v in MARKERS.items()},
        "proactivity_levels_found": levels,
        "tool_results": results,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exp")
    ap.add_argument("--raw-root", default=RAW_ROOT)
    ap.add_argument("--out", default=OUT_ROOT)
    a = ap.parse_args()
    rows = []
    for f in sorted(glob.glob(os.path.join(a.raw_root, a.exp, "http", "*-req.json"))):
        with open(f, encoding="utf-8") as fh:
            o = json.load(fh)
        if not isinstance(o.get("body"), dict) or "/v1/messages" not in o.get("url", ""):
            continue
        row = summarize_request(o["body"])
        row["seq"] = o.get("seq")
        res = f.replace("-req.json", "-res.json")
        if os.path.exists(res):
            try:
                with open(res, encoding="utf-8") as fh:
                    row["response_status"] = json.load(fh).get("status")
            except (OSError, ValueError):
                pass
        rows.append(row)
    stream = {}
    sp = os.path.join(a.raw_root, a.exp, "stdout.jsonl")
    if os.path.exists(sp):
        with open(sp, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                if o.get("type") == "system" and o.get("subtype") == "init":
                    stream["init_permission_mode"] = o.get("permissionMode")
                elif o.get("type") == "result":
                    stream.setdefault("results", []).append(
                        {k: o.get(k) for k in ("subtype", "is_error", "num_turns", "terminal_reason")}
                        | {"permission_denial_count": len(o.get("permission_denials") or [])})
    out_dir = os.path.join(a.out, a.exp)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "coding-workflow-probe.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"exp": a.exp, "message_requests": len(rows), "stream": stream, "requests": rows}, fh, indent=1)
    print(path, len(rows))


if __name__ == "__main__":
    main()
