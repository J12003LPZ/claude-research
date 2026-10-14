"""Turn a raw experiment directory into sanitized, structural evidence.

  python -I summarize_captures.py <exp id> [--print]

Reads   <lab>/raw/<id>/{run.json, stdout.jsonl, debug.log, http/*}
Writes  research/claude-code/runtime-logs/<id>/{run.json, http-summary.json,
        stream-summary.json, debug-summary.json}

Sanitization rules:
  * prompt / message / tool text is reduced to length, sha256 and an 80-char head when safe;
    arbitrary response/error text is content-free length and sha256 metadata
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


def private_digest(text):
    """Keep prompt identity and size without publishing prompt content."""
    return {"len": len(text), "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]}


def safe_key(value):
    """Keep ordinary schema keys readable while digesting arbitrary key text."""
    text = str(value)
    if re.fullmatch(r"[a-z][a-z0-9_]*", text) or text in {"Authorization"}:
        return text
    return "<key:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16] + ">"


def safe_keys(values):
    return [safe_key(value) for value in values]


def summarize_fault(value):
    """Preserve fault controls without publishing matcher or payload values."""
    if value is None:
        return None
    if not isinstance(value, dict):
        return structural_shape(value)
    out = {}
    scalar_keys = {"status", "times", "mode", "stall_ms", "after_bytes"}
    matcher_keys = {"path_contains", "body_contains", "body_contains_all"}
    for key in sorted(value):
        item = value[key]
        if key in scalar_keys and isinstance(item, (bool, int, float, str, type(None))):
            if key == "mode" and item not in {"status", "reset", "stall", "sse_stall"}:
                out[key] = private_digest(str(item))
            else:
                out[key] = item
        elif key in matcher_keys:
            if isinstance(item, list):
                out[key] = [private_digest(str(entry)) for entry in item]
            else:
                out[key] = private_digest(str(item))
        else:
            out[key] = structural_shape(item)
    return out


def summarize_record_list(value):
    """Keep timing and event types while hiding arbitrary record payloads."""
    if not isinstance(value, list):
        return structural_shape(value)
    records = []
    for record in value:
        if not isinstance(record, dict):
            records.append(structural_shape(record))
            continue
        record_out = {}
        for key, item in sorted(record.items()):
            if key == "t_s" and isinstance(item, (int, float)):
                record_out[key] = item
            elif key == "close" and isinstance(item, bool):
                record_out[key] = item
            elif key == "type" and item in {"user", "control_response"}:
                record_out[key] = item
            elif key == "subtype" and item in {"can_use_tool", "success"}:
                record_out[key] = item
            elif isinstance(item, str):
                record_out[key] = private_digest(item)
            else:
                record_out[key] = structural_shape(item)
        records.append(record_out)
    return records


def sanitize_run(run):
    """Mask metadata and replace raw prompt/fault text with content-free summaries."""
    out = deep_mask(run)
    if isinstance(run.get("exe_sha256"), str):
        out["exe_sha256"] = run["exe_sha256"]
    if isinstance(run.get("prompt"), str):
        out["prompt"] = private_digest(run["prompt"])
    if "fault" in run:
        out["fault"] = summarize_fault(run["fault"])
    for key in ("stdin_script", "control_events"):
        if key in run:
            out[key] = summarize_record_list(run[key])
    return out


def digest(text):
    if not isinstance(text, str):
        text = json.dumps(text, sort_keys=True)
    return {"len": len(text), "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16],
            "head": mask(text[:HEAD].replace("\n", "\\n"))}


def structural_shape(value):
    """Describe a structured value without publishing any of its values."""
    if isinstance(value, dict):
        return {"type": "object", "keys": sorted(safe_keys(value.keys()))}
    if isinstance(value, list):
        return {"type": "array", "length": len(value)}
    return {"type": type(value).__name__}


def summarize_error(value):
    """Keep error shape and type while digesting arbitrary server text."""
    if not isinstance(value, dict):
        return structural_shape(value)
    out = {"keys": sorted(safe_keys(value.keys()))}
    if isinstance(value.get("type"), str):
        error_type = value["type"]
        out["type"] = error_type if error_type in {
            "api_error", "invalid_request_error", "overloaded_error", "rate_limit_error",
            "server_error", "authentication_error", "permission_error",
        } else private_digest(error_type)
    if "message" in value:
        message = value["message"]
        out["message"] = private_digest(message if isinstance(message, str) else str(message))
    return out


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


def summarize_request_field(key, value):
    """Keep known request scalars and structure-digest all other field values."""
    if key in {"max_tokens", "temperature"} and isinstance(value, (int, float)):
        return value
    if key in {"stream"} and isinstance(value, bool):
        return value
    if key == "model" and value in {
        "claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-4-1", "claude-opus-4-5",
        "claude-opus-4-6", "claude-fable-5-1", "claude-opus-5-5",
    }:
        return value
    if key in {"speed", "service_tier"} and value in {"standard", "fast", "priority"}:
        return value
    if isinstance(value, (dict, list)):
        return structural_shape(value)
    if isinstance(value, str):
        return private_digest(value)
    return structural_shape(value)


def summarize_request(req):
    body = req.get("body")
    out = {"seq": req["seq"], "t_ms": req["t_ms"], "method": req["method"],
           "url": mask(req["url"]), "body_bytes": req["body_bytes"],
           "header_order": req.get("header_order"),
           "headers": {k: mask(v) for k, v in req["headers"].items()}}
    if not isinstance(body, dict):
        out["body"] = body if body is None else "<non-json>"
        return out
    b = {"top_level_keys": safe_keys(body.keys())}
    for k in ("model", "max_tokens", "stream", "temperature", "tool_choice", "thinking", "betas",
              "context_management", "output_config", "speed", "service_tier"):
        if k in body:
            b[k] = summarize_request_field(k, body[k])
    if "container" in body:
        b["container"] = structural_shape(body["container"])
    if "mcp_servers" in body:
        servers = body["mcp_servers"]
        b["mcp_servers"] = {
            "count": len(servers),
            "items": [structural_shape(server) for server in servers],
        } if isinstance(servers, list) else structural_shape(servers)
    if "metadata" in body:
        md = body["metadata"]
        b["metadata_keys"] = sorted(safe_keys(md.keys()))
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
            "schema_props": sorted(safe_keys(((t.get("input_schema") or {}).get("properties") or {}).keys())),
            "extra_keys": sorted(safe_keys(k for k in t.keys() if k not in ("name", "description", "input_schema", "type"))),
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
    normalized = raw.replace("\r\n", "\n").replace("\r", "\n")
    for chunk in normalized.split("\n\n"):
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
                m = d.get("message")
                if isinstance(m, dict):
                    out["message_start"] = {"model": m.get("model"), "id_prefix": str(m.get("id", ""))[:8],
                                            "usage": m.get("usage"), "keys": sorted(safe_keys(m.keys()))}
                else:
                    out["message_start_keys"] = sorted(safe_keys(d.keys()))
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
                out["sse_error"] = summarize_error(d.get("error"))
        out["sse_event_runs"] = seqn
        out["content_blocks"] = blocks
        out["final_usage"] = usage
        out["final_delta"] = stop
    else:
        try:
            j = json.loads(text)
            out["json_keys"] = sorted(j.keys()) if isinstance(j, dict) else type(j).__name__
            if isinstance(j, dict) and "error" in j:
                out["error"] = summarize_error(j["error"])
            if isinstance(j, dict) and "usage" in j:
                out["usage"] = j["usage"]
            if isinstance(j, dict) and "input_tokens" in j:
                out["input_tokens"] = j["input_tokens"]
        except Exception:
            out["body_digest"] = private_digest(text)
    return out


def summarize_stream(path):
    events, init, result = [], None, None
    results = []
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
            results.append({"terminal_reason": o.get("terminal_reason"), "api_error_status": o.get("api_error_status"),
                            "is_error": o.get("is_error"), "num_turns": o.get("num_turns")})
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
    return deep_mask({"event_count": len(events), "init": init, "result": result, "results": results,
                      "events": compact})


DEBUG_PAT = re.compile(r"^(\S+)\s+\[(\w+)\]\s*(.*)$")

# Reactive-compact progress lines. Only the integers are captured, never free text.
REACTIVE_PATTERNS = [
    ("attempt_prompt_too_long", re.compile(
        r"Reactive compact: attempt (\d+) hit prompt-too-long \(gap=(\d+)\D+?step (\d+)\), next preserves (\d+)/(\d+)"),
     ("attempt", "gap", "step", "preserves", "of")),
    ("last_resort", re.compile(
        r"Reactive compact: round ladder exhausted, last resort \(keeping (\d+) trailing messages, head truncations so far: (\d+)\)"),
     ("keeping", "head_truncations")),
    ("gave_up", re.compile(
        r"Reactive compact: last-resort request still too long after (\d+) head truncations, giving up"),
     ("head_truncations",)),
    ("bail_no_assistant_messages", re.compile(
        r"Reactive compact: no assistant messages in summarize set, bailing"), ()),
]

# Autocompact progress lines. Captures are integers or short code-defined tokens, never free text.
AUTOCOMPACT_PATTERNS = [
    ("level", re.compile(r"autocompact: tokens=\S+ level=([a-z]+) effectiveWindow=(\d+)"),
     ("level", "effective_window")),
    ("routed_reactive", re.compile(r"autocompact: routing through reactive \(thresholdSource=([a-z-]+)"),
     ("threshold_source",)),
    ("pre_compact_hook_ran", re.compile(r"PreCompact:auto \[.*\] completed with status"), ()),
    ("summary_api_error", re.compile(r"Reactive compact: summarization returned API error"), ()),
    ("circuit_breaker_tripped", re.compile(r"circuit breaker tripped"), ()),
    ("failure_breaker_open", re.compile(r"failure_breaker_open"), ()),
]

# Stream watchdog progress lines; integers only, no free text.
WATCHDOG_PATTERNS = [
    ("stall_partial", re.compile(
        r"\[Stall\] stream_idle_partial lastChunkAgeMs=(\d+) bytesTotal=(\d+) idleDeadlineMs=(\d+)"),
     ("last_chunk_age_ms", "bytes_total", "idle_deadline_ms")),
    ("idle_warning", re.compile(r"Streaming idle warning: no chunks received for (\d+)s"), ("seconds",)),
    ("idle_timeout", re.compile(r"Streaming idle timeout: no chunks received for (\d+)s, aborting stream"),
     ("seconds",)),
    ("byte_watchdog_fired", re.compile(r"\[byte-watchdog\] firing: idle=(\d+)ms"), ("idle_ms",)),
    ("fallback_non_streaming", re.compile(r"falling back to non-streaming mode"), ()),
]


def summarize_debug(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    cats = {}
    signals = []
    priority_signals = []
    reactive = []
    watchdog = []
    autocompact = []
    signal_rx = re.compile(
        r"compact|source=compact|failure[_ ]breaker|circuit breaker|"
        r"tengu_auto_compact_circuit_breaker|API error",
        re.I,
    )
    priority_rx = re.compile(
        r"Reactive compact|failure[_ ]breaker|circuit breaker|"
        r"tengu_auto_compact_circuit_breaker|API error",
        re.I,
    )
    for ln in lines:
        m = DEBUG_PAT.match(ln)
        if not m:
            continue
        msg = m.group(3)
        cat = re.match(r"\[?([A-Za-z][\w .:-]{1,40}?)[\]:]", msg)
        raw_key = cat.group(1) if cat else msg.split(" ")[0][:30]
        key = "sha256:" + hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]
        cats[key] = cats.get(key, 0) + 1
        for event, rx, names in REACTIVE_PATTERNS:
            hit = rx.search(msg)
            if hit:
                reactive.append({"t": m.group(1), "event": event,
                                 **{n: int(v) for n, v in zip(names, hit.groups())}})
                break
        for event, rx, names in AUTOCOMPACT_PATTERNS:
            hit = rx.search(msg)
            if hit:
                vals = dict(zip(names, hit.groups()))
                if "effective_window" in vals:
                    vals["effective_window"] = int(vals["effective_window"])
                autocompact.append({"t": m.group(1), "event": event, **vals})
                break
        for event, rx, names in WATCHDOG_PATTERNS:
            hit = rx.search(msg)
            if hit:
                watchdog.append({"t": m.group(1), "event": event,
                                 **{n: int(v) for n, v in zip(names, hit.groups())}})
                break
        if signal_rx.search(msg):
            labels = []
            if re.search(r"Reactive compact", msg, re.I):
                labels.append("Reactive compact")
            if re.search(r"source=compact", msg, re.I):
                labels.append("source=compact")
            if re.search(r"failure_breaker_open", msg, re.I):
                labels.append("failure_breaker_open")
            elif re.search(r"failure breaker", msg, re.I):
                labels.append("failure breaker")
            if re.search(r"tengu_auto_compact_circuit_breaker", msg, re.I):
                labels.append("tengu_auto_compact_circuit_breaker")
            elif re.search(r"circuit breaker", msg, re.I):
                labels.append("circuit breaker")
            if re.search(r"API error", msg, re.I):
                labels.append("API error")
            if not labels:
                labels.append("compact")
            safe = f"{m.group(1)} [signal] {', '.join(labels)}"
            if len(signals) < 80:
                signals.append(safe)
            elif priority_rx.search(msg):
                priority_signals.append(safe)
    return {"line_count": len(lines), "top_prefixes": sorted(cats.items(), key=lambda x: -x[1])[:60],
            "signals": signals + priority_signals[:80], "reactive_compact": reactive, "watchdog": watchdog,
            "autocompact": autocompact}


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    exp = sys.argv[1]
    raw = os.path.join(LAB, "raw", exp)
    out = os.path.join(OUT, exp)
    os.makedirs(out, exist_ok=True)
    run = json.load(open(os.path.join(raw, "run.json"), encoding="utf-8"))
    run = sanitize_run(run)
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
