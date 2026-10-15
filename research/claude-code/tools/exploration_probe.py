"""Sanitized summary of what the exploration and edit tools returned in a scripted lab run (E90 series).

usage: python -I exploration_probe.py <exp id> [--raw-root DIR] [--out DIR]

Reads the last model request of <raw root>/<id>/http/*-req.json (private, never committed; it carries the whole
conversation so far) and writes runtime-logs/<id>/exploration-probe.json with, per tool call: tool name, the input keys
and short scalar values, error flag, character and line counts, the first and last line of the result (home paths
masked, long lines cut), and fixed-string markers the CLI is known to emit. Also copies the first characters of any
`system`-role message that starts with "[Truncated". The lab projects hold synthetic data only.
"""
import argparse
import glob
import json
import os
import re

RAW_ROOT = r"C:/Users/sergi/Desktop/claude-rea/lab/raw"
OUT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "runtime-logs")

HOME_RE = re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s'\"<>|]+", re.I)
PATH_SEP_RE = re.compile(r"\\{1,2}")

MARKERS = {
    "persisted_output": "<persisted-output>",
    "pagination_note": "[Showing results with pagination",
    "glob_showing_note": "matching files;",
    "glob_truncated_note": "(Results are truncated",
    "no_files_found": "No files found",
    "no_matches_found": "No matches found",
    "file_unchanged_stub": "File unchanged since last read",
    "wasted_call_stub": "Wasted call",
    "already_in_context_stub": "This file is already in your context",
    "not_read_error": "File has not been read yet",
    "modified_since_read_error": "modified since",
    "exceeds_tokens_error": "exceeds maximum allowed tokens",
    "exceeds_size_error": "exceeds maximum allowed size",
    "binary_error": "cannot read binary files",
    "did_you_mean": "Did you mean",
    "long_line_omitted": "[Omitted long matching line]",
    "updated_successfully": "has been updated successfully",
    "plan_mode_refusal": "while in plan mode",
    "partial_view_notice": "[Truncated: PARTIAL view",
}


def scrub(text):
    """Mask home-directory names so no account name is emitted, then fold path separators."""
    return PATH_SEP_RE.sub("/", HOME_RE.sub("<home>", text))


def flat(content):
    if isinstance(content, str):
        return content
    out = []
    for block in content or []:
        if isinstance(block, dict):
            if block.get("type") == "text":
                out.append(block.get("text", ""))
            elif block.get("type") == "tool_result":
                out.append(flat(block.get("content")))
    return "\n".join(out)


def short_input(inp):
    out = {}
    for key, value in (inp or {}).items():
        if isinstance(value, (int, float, bool)) or value is None:
            out[key] = value
        elif isinstance(value, str):
            out[key] = scrub(value)[:80] if key in ("pattern", "glob", "output_mode", "type") else f"<str {len(value)} chars>"
        else:
            out[key] = f"<{type(value).__name__}>"
    return out


def summarize_conversation(body):
    """One row per tool call in the conversation carried by `body` (the last request of a run)."""
    calls = {}
    for message in body.get("messages", []):
        if isinstance(message.get("content"), list):
            for block in message["content"]:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    calls[block.get("id")] = block
    rows = []
    for message in body.get("messages", []):
        if not isinstance(message.get("content"), list):
            continue
        for block in message["content"]:
            if not (isinstance(block, dict) and block.get("type") == "tool_result"):
                continue
            text = flat(block.get("content"))
            lines = text.split("\n")
            call = calls.get(block.get("tool_use_id"), {})
            rows.append({
                "tool": call.get("name"),
                "input": short_input(call.get("input")),
                "is_error": bool(block.get("is_error")),
                "chars": len(text),
                "lines": len(lines),
                "first_line": scrub(lines[0])[:160],
                "last_line": scrub(lines[-1])[:160],
                "first_lines": [scrub(x)[:160] for x in lines[:3]],
                "last_lines": [scrub(x)[:160] for x in lines[-3:]],
                "markers": [name for name, lit in MARKERS.items() if lit in text],
            })
    notes = []
    for message in body.get("messages", []):
        if message.get("role") != "system":
            continue
        text = flat(message.get("content"))
        if text.startswith("[Truncated"):
            notes.append(scrub(text)[:420])
    return {"model": body.get("model"), "context_management": "context_management" in body, "tool_calls": rows,
            "truncation_notes": notes}


def last_messages_request(raw_dir):
    best = None
    for path in sorted(glob.glob(os.path.join(raw_dir, "http", "*-req.json"))):
        with open(path, encoding="utf-8") as fh:
            obj = json.load(fh)
        if isinstance(obj.get("body"), dict) and "/v1/messages" in obj.get("url", ""):
            best = obj
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exp")
    ap.add_argument("--raw-root", default=RAW_ROOT)
    ap.add_argument("--out", default=OUT_ROOT)
    a = ap.parse_args()
    last = last_messages_request(os.path.join(a.raw_root, a.exp))
    if last is None:
        raise SystemExit("no /v1/messages request found for " + a.exp)
    summary = summarize_conversation(last["body"])
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
                    stream["init_model"] = o.get("model")
                elif o.get("type") == "result":
                    stream.setdefault("results", []).append(
                        {k: o.get(k) for k in ("subtype", "is_error", "num_turns", "terminal_reason")}
                        | {"permission_denial_count": len(o.get("permission_denials") or [])})
    out_dir = os.path.join(a.out, a.exp)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "exploration-probe.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"exp": a.exp, "stream": stream, **summary}, fh, indent=1)
    print(path, len(summary["tool_calls"]))


if __name__ == "__main__":
    main()
