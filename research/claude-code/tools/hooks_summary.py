"""Sanitized timeline of lab hook invocations for one experiment.

  python -I hooks_summary.py <exp id> [--print]

Reads <lab>/raw/<id>/hooklog.jsonl (written by cc-rea-lab/hooklog.py), writes
runtime-logs/<id>/hooks-summary.json with relative times, the stdin field names per
event, and selected non-sensitive values.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from summarize_captures import LAB, OUT, mask  # noqa: E402

KEEP = ("hook_event_name", "tool_name", "permission_mode", "source", "stop_hook_active", "trigger",
        "agent_type", "reason", "notification_type", "load_reason", "memory_type", "effort")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    exp = sys.argv[1]
    p = os.path.join(LAB, "raw", exp, "hooklog.jsonl")
    recs = [json.loads(l) for l in open(p, encoding="utf-8")] if os.path.exists(p) else []
    t0 = min((r["t_in"] for r in recs), default=0)
    out = []
    for r in sorted(recs, key=lambda r: r["t_in"]):
        s = r["stdin"]
        e = {"t_in_ms": round((r["t_in"] - t0) * 1000), "t_out_ms": round((r["t_out"] - t0) * 1000),
             "tag": r["tag"], "mode": r["mode"], "pid": "<pid>", "stdin_keys": sorted(s.keys()),
             "env_names": r["env_names"], "hook_cwd_is_project": mask(r["cwd"])}
        for k in KEEP:
            if k in s:
                e[k] = mask(s[k]) if isinstance(s[k], str) else s[k]
        for k in ("tool_input", "tool_response", "tool_result"):
            if k in s:
                e[k + "_keys"] = sorted(s[k].keys()) if isinstance(s[k], dict) else type(s[k]).__name__
        if "prompt" in s:
            e["prompt_len"] = len(s["prompt"])
        if "error" in s:
            e["error_head"] = mask(str(s["error"])[:120])
        out.append(e)
    os.makedirs(os.path.join(OUT, exp), exist_ok=True)
    json.dump(out, open(os.path.join(OUT, exp, "hooks-summary.json"), "w", encoding="utf-8"), indent=1)
    if "--print" in sys.argv:
        print(f"== {exp}: {len(out)} hook invocations")
        for e in out:
            extra = {k: e[k] for k in e if k in KEEP and k != "hook_event_name"}
            print(f"  {e['t_in_ms']:>6}..{e['t_out_ms']:<6} {e['tag']:<22} {e.get('hook_event_name', ''):<18} {json.dumps(extra)[:110]}")
        if out:
            seen = {}
            for e in out:
                seen.setdefault(e.get("hook_event_name"), e)
            for ev, e in seen.items():
                print(f"  [{ev}] stdin keys: {e['stdin_keys']}")
            print("  env names (first record):", out[0]["env_names"])


if __name__ == "__main__":
    main()
