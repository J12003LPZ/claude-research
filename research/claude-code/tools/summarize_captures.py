"""Turn a raw experiment directory into sanitized, structural evidence.

  python -I summarize_captures.py <exp id> [--print]

Reads   <lab>/raw/<id>/{run.json, stdout.jsonl, debug.log, http/*}
Writes  research/claude-code/runtime-logs/<id>/{run.json, http-summary.json,
        stream-summary.json, debug-summary.json}

Sanitization rules:
  * prompt / message / tool text is reduced to length, sha256 and an 80-char head
  * header values for credentials were already dropped by the proxy; ids are masked here
  * emails, UUIDs, long hex ids, home-directory names are masked in every emitted string
"""
import glob
import hashlib
import json
import os
import re
import sys

LAB = r"C:\Users\sergi\Desktop\claude-rea\lab"
OUT = r"C:\Users\sergi\Desktop\claude-rea\research\claude-code\runtime-logs"
HEAD = 80

MASKS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "<email>"),
    (re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I), "<uuid>"),
    (re.compile(r"\b[0-9a-f]{32,}\b", re.I), "<hex>"),
    (re.compile(r"\b(wrkspc|req|msg|org|toolu|srvtoolu)_[A-Za-z0-9]{6,}"), r"\1_<id>"),
    (re.compile(r"(?i)([A-Z]:[\\/]+Users[\\/]+)[^\\/\"'\s]+"), r"\1<user>"),
    (re.compile(r"(?i)(/home/|/Users/)[^/\"'\s]+"), r"\1<user>"),
]


def mask(s):
    if not isinstance(s, str):
        return s
    for rx, rep in MASKS:
        s = rx.sub(rep, s)
    return s


def deep_mask(o):
    if isinstance(o, str):
        return mask(o)
    if isinstance(o, list):
        return [deep_mask(x) for x in o]
    if isinstance(o, dict):
        return {k: deep_mask(v) for k, v in o.items()}
    return o


def digest(text):
    if not isinstance(text, str):
        text = json.dumps(text, sort_keys=True)
    return {"len": len(text), "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16],
            "head": mask(text[:HEAD].replace("\n", "\\n"))}


def block(b):
    if isinstance(b, str):
        return {"type": "string", **digest(b)}
    out = {"type": b.get("type")}
    if "cache_control" in b:
        out["cache_control"] = b["cache_control"]
    t = b.get("type")
    if t == "text":
        out.update(digest(b.get("text", "")))
        # reminder-tag inventory without content
        tags = re.findall(r"<([a-zA-Z][\w-]*)>", b.get("text", ""))
        if tags:
            seen = []
            for x in tags:
                if x not in seen:
                    seen.append(x)
            out["tags"] = seen[:12]
    elif t == "tool_use":
        out.update({"id_prefix": str(b.get("id", ""))[:6], "name": b.get("name"),
                    "input_keys": sorted((b.get("input") or {}).keys()),
                    "input": digest(b.get("input"))})
    elif t == "tool_result":
        c = b.get("content")
        out.update({"tool_use_id_prefix": str(b.get("tool_use_id", ""))[:6], "is_error": b.get("is_error"),
                    "content": [block(x) for x in c] if isinstance(c, list) else digest(c or "")})
    elif t in ("thinking", "redacted_thinking"):
        out.update({"thinking_len": len(b.get("thinking", "") or b.get("data", "")),
                    "has_signature": bool(b.get("signature"))})
    else:
        out["keys"] = sorted(b.keys())
    return out


def summarize_request(req):
    body = req.get("body")
    out = {"seq": req["seq"], "t_ms": req["t_ms"], "method": req["method"],
           "url": mask(req["url"]), "body_bytes": req["body_bytes"],
           "header_order": req.get("header_order"),
           "headers": {k: mask(v) for k, v in req["headers"].items()}}
    if not isinstance(body, dict):
        out["body"] = body if body is None else "<non-json>"
        return out
    b = {"top_level_keys": list(body.keys())}
    for k in ("model", "max_tokens", "stream", "temperature", "tool_choice", "thinking", "betas",
              "context_management", "output_config", "speed", "service_tier", "container", "mcp_servers"):
        if k in body:
            b[k] = body[k]
    if "metadata" in body:
        md = body["metadata"]
        b["metadata_keys"] = sorted(md.keys())
        uid = md.get("user_id")
        if isinstance(uid, str):
            try:
                b["metadata_user_id_json_keys"] = sorted(json.loads(uid).keys())
            except Exception:
                b["metadata_user_id_shape"] = re.sub(r"[0-9a-f]{8,}", "<hex>", mask(uid))[:120]
    sysm = body.get("system")
    if isinstance(sysm, str):
        b["system"] = [{"type": "string", **digest(sysm)}]
    elif isinstance(sysm, list):
        b["system"] = [block(x) for x in sysm]
    tools = body.get("tools")
    if isinstance(tools, list):
        b["tools_count"] = len(tools)
        b["tools"] = [{
            "name": t.get("name"), "type": t.get("type"),
            "description_len": len(t.get("description") or ""),
            "schema_len": len(json.dumps(t.get("input_schema"))) if "input_schema" in t else None,
            "schema_props": sorted(((t.get("input_schema") or {}).get("properties") or {}).keys()),
            "extra_keys": sorted(k for k in t.keys() if k not in ("name", "description", "input_schema", "type")),
            **({"cache_control": t["cache_control"]} if "cache_control" in t else {}),
            **({"defer_loading": t["defer_loading"]} if "defer_loading" in t else {}),
        } for t in tools]
        b["tools_total_bytes"] = len(json.dumps(tools))
    msgs = body.get("messages")
    if isinstance(msgs, list):
        b["messages_count"] = len(msgs)
        b["messages"] = [{"role": m.get("role"),
                          "content": [block(x) for x in m["content"]] if isinstance(m.get("content"), list)
                          else [block(m.get("content", ""))]} for m in msgs]
    out["body"] = b
    return out


def parse_sse(raw):
    events = []
    for chunk in raw.split("\n\n"):
        ev, data = None, []
        for line in chunk.split("\n"):
            if line.startswith("event:"):
                ev = line[6:].strip()
            elif line.startswith("data:"):
                data.append(line[5:].strip())
        if ev or data:
            try:
                d = json.loads("\n".join(data)) if data else None
            except Exception:
                d = None
            events.append((ev, d))
    return events


def summarize_response(meta, raw, chunks):
    out = dict(meta)
    if "headers" in out:
        out["headers"] = {k: mask(v) for k, v in out["headers"].items()}
    out["body_bytes"] = len(raw)
    out["chunk_count"] = sum(1 for c in chunks if "bytes" in c)
    out["chunk_times_ms"] = [c["t_ms"] for c in chunks if "bytes" in c][:40]
    out["client_closed_early"] = any(c.get("client_closed_early") for c in chunks)
    ct = (meta.get("headers") or {}).get("content-type", "")
    text = raw.decode("utf-8", "replace")
    if "event-stream" in ct:
        evs = parse_sse(text)
        seqn, blocks, usage, stop = [], [], None, None
        for ev, d in evs:
            if seqn and seqn[-1][0] == ev:
                seqn[-1][1] += 1
            else:
                seqn.append([ev, 1])
            if not isinstance(d, dict):
                continue
            if d.get("type") == "message_start":
                m = d["message"]
                out["message_start"] = {"model": m.get("model"), "id_prefix": str(m.get("id", ""))[:8],
                                        "usage": m.get("usage"), "keys": sorted(m.keys())}
            elif d.get("type") == "content_block_start":
                cb = d["content_block"]
                blocks.append({"index": d.get("index"), "type": cb.get("type"), "name": cb.get("name"),
                               "delta_types": {}, "delta_count": 0})
            elif d.get("type") == "content_block_delta" and blocks:
                dt = d["delta"].get("type")
                blocks[-1]["delta_types"][dt] = blocks[-1]["delta_types"].get(dt, 0) + 1
                blocks[-1]["delta_count"] += 1
            elif d.get("type") == "message_delta":
                usage = d.get("usage")
                stop = d.get("delta")
                out["message_delta_keys"] = sorted(d.keys())
            elif d.get("type") == "error":
                out["sse_error"] = d.get("error")
        out["sse_event_runs"] = seqn
        out["content_blocks"] = blocks
        out["final_usage"] = usage
        out["final_delta"] = stop
    else:
        try:
            j = json.loads(text)
            out["json_keys"] = sorted(j.keys()) if isinstance(j, dict) else type(j).__name__
            if isinstance(j, dict) and "error" in j:
                out["error"] = j["error"]
            if isinstance(j, dict) and "usage" in j:
                out["usage"] = j["usage"]
            if isinstance(j, dict) and "input_tokens" in j:
                out["input_tokens"] = j["input_tokens"]
        except Exception:
            out["body_head"] = mask(text[:160])
    return out


def summarize_stream(path):
    events, init, result = [], None, None
    if not os.path.exists(path):
        return {"events": []}
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except Exception:
            events.append({"type": "<non-json>", "head": mask(line[:120])})
            continue
        t = o.get("type")
        e = {"type": t}
        if o.get("subtype"):
            e["subtype"] = o["subtype"]
        e["keys"] = sorted(o.keys())
        if t == "system" and o.get("subtype") == "init":
            init = {k: (v if k in ("tools", "model", "permissionMode", "apiKeySource", "output_style",
                                    "claude_code_version", "slash_commands", "agents", "skills", "fast_mode_state")
                        else (len(v) if isinstance(v, (list, dict)) else mask(v) if isinstance(v, str) else v))
                    for k, v in o.items()}
            for k in ("slash_commands", "skills", "agents"):
                if isinstance(init.get(k), list):
                    init[k + "_count"] = len(init[k])
                    init[k] = init[k][:8]
            if isinstance(o.get("mcp_servers"), list):
                init["mcp_servers"] = [{"status": s.get("status")} for s in o["mcp_servers"]]
            if isinstance(o.get("plugins"), list):
                init["plugins"] = len(o["plugins"])
        elif t == "system" and str(o.get("subtype", "")).startswith("hook"):
            e.update({k: mask(o.get(k)) for k in ("hook_event", "hook_name", "exit_code", "outcome") if k in o})
        elif t == "system":
            for k in ("status", "compact_metadata", "content", "level"):
                if k in o:
                    e[k] = mask(o[k]) if isinstance(o[k], str) else o[k]
        elif t == "stream_event":
            ev = o["event"]
            e["event"] = ev.get("type")
            if ev.get("type") == "content_block_start":
                e["block"] = {"type": ev["content_block"].get("type"), "name": ev["content_block"].get("name")}
            if ev.get("type") == "content_block_delta":
                e["delta"] = ev["delta"].get("type")
            if ev.get("type") == "message_delta":
                e["stop_reason"] = ev["delta"].get("stop_reason")
            e["parent_tool_use_id"] = o.get("parent_tool_use_id")
        elif t in ("assistant", "user"):
            m = o.get("message", {})
            c = m.get("content")
            e["content"] = [block(x) for x in c] if isinstance(c, list) else [block(c or "")]
            e["parent_tool_use_id"] = o.get("parent_tool_use_id")
            if t == "assistant":
                e["stop_reason"] = m.get("stop_reason")
                e["usage_keys"] = sorted((m.get("usage") or {}).keys())
            if "tool_use_result" in o:
                r = o["tool_use_result"]
                e["tool_use_result_keys"] = sorted(r.keys()) if isinstance(r, dict) else type(r).__name__
            for k in ("isSynthetic", "isReplay", "error"):
                if k in o:
                    e[k] = o[k]
        elif t == "result":
            result = {k: deep_mask(v) for k, v in o.items() if k not in ("result",)}
            result["result"] = digest(o.get("result") or "")
            if isinstance(result.get("modelUsage"), dict):
                result["modelUsage"] = {m: sorted(u.keys()) for m, u in result["modelUsage"].items()}
            e["subtype"] = o.get("subtype")
        else:
            for k, v in o.items():
                if k not in ("type", "uuid", "session_id") and not isinstance(v, (dict, list)):
                    e[k] = mask(v) if isinstance(v, str) else v
        events.append(e)
    # collapse runs of identical stream_event deltas
    compact, i = [], 0
    for e in events:
        key = (e["type"], e.get("event"), e.get("delta"), e.get("subtype"), e.get("hook_event"))
        if compact and compact[-1].get("_key") == key and e["type"] in ("stream_event",):
            compact[-1]["repeat"] = compact[-1].get("repeat", 1) + 1
        else:
            e2 = dict(e)
            e2["_key"] = key
            compact.append(e2)
    for e in compact:
        e.pop("_key", None)
    return deep_mask({"event_count": len(events), "init": init, "result": result, "events": compact})


DEBUG_PAT = re.compile(r"^(\S+)\s+\[(\w+)\]\s*(.*)$")


def summarize_debug(path):
    if not os.path.exists(path):
        return None
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    cats = {}
    first = []
    for ln in lines:
        m = DEBUG_PAT.match(ln)
        if not m:
            continue
        msg = m.group(3)
        cat = re.match(r"\[?([A-Za-z][\w .:-]{1,40}?)[\]:]", msg)
        key = cat.group(1) if cat else msg.split(" ")[0][:30]
        cats[key] = cats.get(key, 0) + 1
    return {"line_count": len(lines), "top_prefixes": sorted(cats.items(), key=lambda x: -x[1])[:60]}


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    exp = sys.argv[1]
    raw = os.path.join(LAB, "raw", exp)
    out = os.path.join(OUT, exp)
    os.makedirs(out, exist_ok=True)
    run = json.load(open(os.path.join(raw, "run.json"), encoding="utf-8"))
    run["cwd"] = mask(run["cwd"])
    run["argv"] = [mask(x) for x in run["argv"]]
    json.dump(run, open(os.path.join(out, "run.json"), "w", encoding="utf-8"), indent=1)

    http = []
    for rq in sorted(glob.glob(os.path.join(raw, "http", "*-req.json"))):
        seq = os.path.basename(rq)[:4]
        req = json.load(open(rq, encoding="utf-8"))
        entry = {"request": summarize_request(req)}
        mp = os.path.join(raw, "http", f"{seq}-res.json")
        if os.path.exists(mp):
            meta = json.load(open(mp, encoding="utf-8"))
            body = open(os.path.join(raw, "http", f"{seq}-res.body"), "rb").read()
            ch = [json.loads(l) for l in open(os.path.join(raw, "http", f"{seq}-res.chunks.jsonl"), encoding="utf-8") if l.strip()]
            entry["response"] = summarize_response(meta, body, ch)
        http.append(entry)
    json.dump(http, open(os.path.join(out, "http-summary.json"), "w", encoding="utf-8"), indent=1)
    stream = summarize_stream(os.path.join(raw, "stdout.jsonl"))
    json.dump(stream, open(os.path.join(out, "stream-summary.json"), "w", encoding="utf-8"), indent=1)
    dbg = summarize_debug(os.path.join(raw, "debug.log"))
    json.dump(dbg, open(os.path.join(out, "debug-summary.json"), "w", encoding="utf-8"), indent=1)

    if "--print" in sys.argv:
        print(f"== {exp}: exit={run['exit_code']} dur={run['duration_s']}s http_requests={len(http)} stream_events={stream['event_count']}")
        for h in http:
            r, s = h["request"], h.get("response", {})
            b = r.get("body") if isinstance(r.get("body"), dict) else {}
            print(f"  [{r['seq']}] {r['method']} {r['url'][:70]} bytes={r['body_bytes']} -> {s.get('status')} "
                  f"model={b.get('model')} msgs={b.get('messages_count')} tools={b.get('tools_count')} "
                  f"sys_blocks={len(b.get('system', []))} stop={(s.get('final_delta') or {}).get('stop_reason')}")
        print("  stream:", " > ".join(
            (e["type"] + ("/" + e["subtype"] if e.get("subtype") else "") + ("/" + e["event"] if e.get("event") else "")
             + (f"x{e['repeat']}" if e.get("repeat") else "")) for e in stream["events"])[:1800])


if __name__ == "__main__":
    main()
