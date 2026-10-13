"""Bounded, human-readable view of one sanitized experiment.

  python -I show_exp.py <exp id> [msgs|stream|both] [request seq or 'last']
"""
import json
import os
import sys

OUT = r"C:\Users\sergi\Desktop\claude-rea\research\claude-code\runtime-logs"


def blk(c):
    t = c.get("type")
    cc = " [cache:%s]" % json.dumps(c["cache_control"]) if "cache_control" in c else ""
    if t == "text" or t == "string":
        return f"text len={c['len']}{cc} tags={c.get('tags', '')} :: {c['head'][:70]}"
    if t == "tool_use":
        return f"tool_use {c['name']} id={c['id_prefix']} keys={c['input_keys']}{cc} :: {c['input']['head'][:70]}"
    if t == "tool_result":
        inner = c["content"]
        if isinstance(inner, list):
            inner = " | ".join(blk(x) for x in inner)
        else:
            inner = f"len={inner['len']} :: {inner['head'][:90]}"
        return f"tool_result for={c['tool_use_id_prefix']} is_error={c['is_error']}{cc} -> {inner}"
    if t in ("thinking", "redacted_thinking"):
        return f"{t} len={c['thinking_len']} sig={c['has_signature']}"
    return f"{t} keys={c.get('keys')}"


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    exp = sys.argv[1]
    what = sys.argv[2] if len(sys.argv) > 2 else "both"
    which = sys.argv[3] if len(sys.argv) > 3 else "last"
    d = os.path.join(OUT, exp)
    if what in ("msgs", "both"):
        http = json.load(open(os.path.join(d, "http-summary.json"), encoding="utf-8"))
        reqs = [h for h in http if isinstance(h["request"].get("body"), dict) and "messages" in h["request"]["body"]]
        sel = reqs if which == "all" else ([reqs[-1]] if which == "last" else [h for h in reqs if h["request"]["seq"] == which])
        for h in sel:
            r, b, s = h["request"], h["request"]["body"], h.get("response", {})
            print(f"== request {r['seq']} {r['url']} model={b.get('model')} max_tokens={b.get('max_tokens')} tools={b.get('tools_count')}")
            for i, sb in enumerate(b.get("system", [])):
                print(f"   system[{i}] {blk(sb)}")
            for i, m in enumerate(b["messages"]):
                print(f"   msg[{i}] {m['role']}")
                for c in m["content"]:
                    print(f"        - {blk(c)}")
            print(f"   -> status={s.get('status')} blocks={[(x['type'], x.get('name'), x['delta_types']) for x in s.get('content_blocks', [])]}")
            print(f"   -> stop={s.get('final_delta')} usage={json.dumps(s.get('final_usage'))[:260]}")
    if what in ("stream", "both"):
        st = json.load(open(os.path.join(d, "stream-summary.json"), encoding="utf-8"))
        print("== stream events")
        for e in st["events"]:
            line = e["type"]
            if e.get("subtype"):
                line += "/" + e["subtype"]
            if e.get("event"):
                line += "/" + e["event"]
            if e.get("repeat"):
                line += f" x{e['repeat']}"
            for k in ("block", "delta", "stop_reason", "hook_event", "hook_name", "exit_code", "outcome", "status",
                      "parent_tool_use_id", "tool_use_result_keys", "isSynthetic", "error"):
                if e.get(k) is not None:
                    line += f" {k}={e[k]}"
            print("  " + line[:230])
            for c in e.get("content", []):
                print("      - " + blk(c)[:230])
            if e["type"] not in ("stream_event", "assistant", "user", "result") and not str(e.get("subtype", "")).startswith("hook"):
                extra = {k: v for k, v in e.items() if k not in ("type", "subtype", "keys", "status")}
                if extra:
                    print("      " + json.dumps(extra)[:300])
                print("      keys=" + ",".join(e["keys"]))
        r = st.get("result") or {}
        print("== result:", json.dumps({k: r.get(k) for k in ("subtype", "is_error", "num_turns", "duration_ms", "duration_api_ms",
                                                              "total_cost_usd", "stop_reason", "terminal_reason", "permission_denials", "api_error_status")})[:900])


if __name__ == "__main__":
    main()
