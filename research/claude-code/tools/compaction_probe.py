"""Sanitized summary of what survives a compaction in a scripted lab run (E90z series).

usage: python -I compaction_probe.py <base id> [--raw-root DIR] [--out DIR] [--extract-root DIR]

A run is three invocations against one session (tools/scenarios/run_e90_compact.sh): <base>1-turn (reads files, a failing
test, an edit, a passing test), <base>2-compact (`/compact Keep the token.`; the summary request gets a canned reply) and
<base>3-after (the first request after compaction). The probe reads those raw request bodies (private, never committed)
and writes runtime-logs/<base>3-after/compaction-probe.json with booleans, counts, hashes and file names only. No prompt
or tool-result text is copied. With --extract-root and node on PATH it also rebuilds the five summary prompt arms from
the extracted chunk and reports which one the compaction request equals byte for byte (by SHA-256).
"""
import argparse
import glob
import hashlib
import json
import os
import re
import subprocess
import tempfile

RAW_ROOT = r"C:/Users/sergi/Desktop/claude-rea/lab/raw"
OUT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "runtime-logs")
CHUNK = "chunk-phacttch.js"
ARMS = ["control", "lean", "short", "short_v2", "capped"]

# scenario constants (tools/scenarios/build_e90_compact.py)
ORIGINAL_PROMPT = "COMPACT-LAB turn1"
TOOL_ID_PREFIX = "toolu_cp_"
FAILING_TEST = "FAILED: add(2, 3) != 5"
PASSING_TEST = "PASSED"
PROJECT_INSTRUCTION = "Keep failing test names when compacting."
SUMMARY_MARKER = "CANNED-SUMMARY-MARKER"
COMMAND_ARG = "Keep the token."
CRITICAL = "CRITICAL: Respond with TEXT ONLY"
TOO_LARGE = "too large to include"
SUMMARY_LEAD = "This session is being continued from a previous conversation"
CONTINUE_LINE = "Continue the conversation from where it left off"
KEPT_TAIL_NOTE = "The messages after this summary are the most recent messages from before compaction, kept verbatim."
RESUME_GUIDANCE = "Whatever is still not started, not finished, not checked"


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_requests(raw_root, exp):
    """Return ([(url, body)] for model requests, [url] for count_tokens requests) in capture order."""
    models, counts = [], []
    for path in sorted(glob.glob(os.path.join(raw_root, exp, "http", "*-req.json"))):
        with open(path, encoding="utf-8") as fh:
            row = json.load(fh)
        body = row.get("body")
        url = row.get("url", "")
        if "count_tokens" in url:
            counts.append({"url": "count_tokens", "body_bytes": row.get("body_bytes")})
        elif isinstance(body, dict) and "messages" in body:
            models.append((url, body))
    return models, counts


def blocks(message):
    content = message.get("content")
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return [b for b in (content or []) if isinstance(b, dict)]


def block_text(block):
    if block.get("type") == "text":
        return block.get("text", "")
    if block.get("type") == "tool_result":
        content = block.get("content")
        return block.get("tool_use_id", "") + " " + (content if isinstance(content, str) else json.dumps(content))
    if block.get("type") == "tool_use":
        return block.get("id", "") + " " + json.dumps(block.get("input", {}))
    return ""


def message_text(message):
    return "\n".join(block_text(b) for b in blocks(message))


def all_text(body):
    return "\n".join(message_text(m) for m in body.get("messages", []))


def system_texts(body):
    system = body.get("system")
    if isinstance(system, str):
        return [system]
    return [b.get("text", "") for b in system or [] if isinstance(b, dict)]


def cache_controls(body):
    system = body.get("system")
    if isinstance(system, str):
        return []
    return [json.dumps(b.get("cache_control"), sort_keys=True) for b in system or [] if isinstance(b, dict)]


def shape(body):
    return [{"role": m.get("role"), "blocks": len(blocks(m)), "chars": len(message_text(m))} for m in body.get("messages", [])]


def static_prompts(extract_root, custom=COMMAND_ARG):
    """Evaluate the summary prompt builders from the extracted chunk in node; returns {arm: prompt} or None."""
    try:
        src = open(os.path.join(extract_root, CHUNK), encoding="utf-8").read()
        start = src.index('var TYe="an <analysis> block')
        end = src.index("var Mnn=/<analysis>")
    except (OSError, ValueError):
        return None
    js = src[start:end] + (
        "\nconst out={};\nfor (const arm of %s) out[arm]=cke(%s, arm, true);\n"
        "require('fs').writeFileSync(process.argv[2], JSON.stringify(out));\n" % (json.dumps(ARMS), json.dumps(custom)))
    with tempfile.TemporaryDirectory() as tmp:
        script = os.path.join(tmp, "eval.js")
        target = os.path.join(tmp, "out.json")
        with open(script, "w", encoding="utf-8") as fh:
            fh.write(js)
        try:
            done = subprocess.run(["node", script, target], capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            return None
        if done.returncode != 0:
            return None
        with open(target, encoding="utf-8") as fh:
            return json.load(fh)


def restored_files(text):
    """Files named in the post-compaction attachment: restored with content, or replaced by a pointer note."""
    rows = []
    for match in re.finditer(r'Called the Read tool with the following input: \{"file_path":"((?:[^"\\]|\\.)*)"\}', text):
        name = re.split(r"[\\/]+", match.group(1).replace("\\\\", "/"))[-1]
        rows.append({"name": name, "status": "content", "pos": match.start()})
    for match in re.finditer(r"Note: (\S+?) was read before the last conversation was summarized, but the contents are too large", text):
        name = re.split(r"[\\/]+", match.group(1))[-1]
        rows.append({"name": name, "status": "note_too_large", "pos": match.start()})
    rows.sort(key=lambda r: r["pos"])
    for r in rows:
        del r["pos"]
    return rows


def is_compaction_request(body):
    return any(CRITICAL in block_text(x) for x in blocks(body["messages"][-1]))


def load_phases(base, raw_root):
    """(turn requests, compaction requests, its count_tokens calls, after requests, their count_tokens calls, out dir name).

    Two layouts: three invocations (<base>1-turn, 2-compact, 3-after) or one process (<base>0-single)."""
    def has_requests(exp):
        return bool(glob.glob(os.path.join(raw_root, exp, "http", "*-req.json")))

    if has_requests(base + "0-single") and not has_requests(base + "1-turn"):
        models, counts = read_requests(raw_root, base + "0-single")
        cut = next((i for i, (_, b) in enumerate(models) if is_compaction_request(b)), None)
        if cut is None:
            raise SystemExit("no compaction request in " + base + "0-single")
        # count_tokens requests are not split by phase in one process; all are attributed to the compaction step
        return models[:cut], models[cut:cut + 1], counts, models[cut + 1:], [], base + "0-single"
    turn_reqs, _ = read_requests(raw_root, base + "1-turn")
    comp_reqs, comp_counts = read_requests(raw_root, base + "2-compact")
    after_reqs, after_counts = read_requests(raw_root, base + "3-after")
    return turn_reqs, comp_reqs, comp_counts, after_reqs, after_counts, base + "3-after"


def attachment_text(body):
    """The re-attached files: every message after the summary that names a restore marker, joined in order.

    Lean-layout models get them in one message; full-layout models can get one message per file."""
    parts = []
    for message in body.get("messages", [])[1:]:
        text = message_text(message)
        if "Called the Read tool with the following input" in text or "was read before the last conversation" in text:
            parts.append(text)
    return "\n".join(parts)


def edit_results(body):
    """Outcome of the Edit calls the after-turn scenario issues (ids toolu_cp_x1..3), by tool_use id."""
    out = {}
    for message in body.get("messages", []):
        for block in blocks(message):
            if block.get("type") == "tool_result" and str(block.get("tool_use_id", "")).startswith("toolu_cp_x"):
                text = block_text(block)
                if "File has not been read yet" in text:
                    out[block["tool_use_id"]] = "refused_not_read"
                elif "has been updated" in text:
                    out[block["tool_use_id"]] = "applied"
                else:
                    out[block["tool_use_id"]] = "other"
    return out


def summarize(base, raw_root=RAW_ROOT, extract_root=None):
    turn_reqs, comp_reqs, comp_counts, after_reqs, after_counts, out_name = load_phases(base, raw_root)
    if not turn_reqs or not comp_reqs or not after_reqs:
        raise SystemExit("missing requests for " + base)
    turn_last = turn_reqs[-1][1]
    comp = next(((u, b) for u, b in comp_reqs if is_compaction_request(b)), None)
    if comp is None:
        raise SystemExit("no compaction request in " + base + "2-compact")
    comp_body = comp[1]
    instruction = next(block_text(x) for x in blocks(comp_body["messages"][-1]) if CRITICAL in block_text(x))
    after = after_reqs[-1][1]
    after_text = all_text(after)
    first = message_text(after["messages"][0])
    last = attachment_text(after)
    arm_hits = []
    prompts = static_prompts(extract_root) if extract_root else None
    if prompts:
        arm_hits = [arm for arm, text in prompts.items() if sha(text) == sha(instruction)]
    turn_text = all_text(turn_last)
    return {
        "base": base,
        "out_dir": out_name,
        "model": after.get("model"),
        "turn_final_request": {"messages": len(turn_last["messages"]), "shape": shape(turn_last)},
        "compact_request": {
            "messages": len(comp_body["messages"]),
            "instruction_chars": len(instruction),
            "instruction_sha256": sha(instruction),
            "arms_equal_by_sha256": arm_hits,
            "static_prompts_checked": prompts is not None,
            "carries_custom_instruction": ("Additional Instructions:\n" + COMMAND_ARG) in instruction,
            "same_system_text_as_turn": system_texts(comp_body) == system_texts(turn_last),
            "cache_control_differs_from_turn": cache_controls(comp_body) != cache_controls(turn_last),
            "same_tools_as_turn": comp_body.get("tools") == turn_last.get("tools"),
            "history_contains_turn_tool_ids": TOOL_ID_PREFIX in all_text(comp_body),
            "count_tokens_calls": len(comp_counts),
        },
        "after_request": {
            "messages": len(after["messages"]),
            "shape": shape(after),
            "count_tokens_calls": len(after_counts),
            "summary_message": {
                "is_first_message": first.startswith(SUMMARY_LEAD) or SUMMARY_LEAD in first,
                "has_canned_summary": SUMMARY_MARKER in first,
                "analysis_stripped": "<analysis>" not in first,
                "summary_tag_rewritten": "Summary:\n" in first and "<summary>" not in first,
                "has_transcript_pointer": "read the full transcript at:" in first,
                "has_continue_guidance": CONTINUE_LINE in first,
                "has_kept_tail_note": KEPT_TAIL_NOTE in first,
                "has_arm_resume_guidance": RESUME_GUIDANCE in first,
            },
            "restored_files": restored_files(last),
            "edit_results_after": edit_results(after),
            "attachment_message_chars": len(last),
            "present": {
                "canned_summary": SUMMARY_MARKER in after_text,
                "project_instruction_file": PROJECT_INSTRUCTION in after_text,
                "compact_command_argument": COMMAND_ARG in after_text,
                "new_user_prompt": "COMPACT-LAB after" in after_text,
            },
            "absent_after_compaction": {
                "original_user_prompt": ORIGINAL_PROMPT not in after_text,
                "turn_tool_use_ids": TOOL_ID_PREFIX not in after_text,
                "failing_test_output": FAILING_TEST not in after_text,
                "tool_result_blocks": not any(b.get("type") == "tool_result" for m in after["messages"] for b in blocks(m)),
                "tool_use_blocks": not any(b.get("type") == "tool_use" for m in after["messages"] for b in blocks(m)),
            },
        },
        "turn_text_had": {
            "failing_test_output": FAILING_TEST in turn_text,
            "original_user_prompt": ORIGINAL_PROMPT in turn_text,
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("--raw-root", default=RAW_ROOT)
    ap.add_argument("--out", default=OUT_ROOT)
    ap.add_argument("--extract-root", default=None)
    args = ap.parse_args()
    result = summarize(args.base, args.raw_root, args.extract_root)
    out_dir = os.path.join(args.out, result["out_dir"])
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "compaction-probe.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
    print(json.dumps({k: result[k] for k in ("base", "model")}), result["compact_request"]["arms_equal_by_sha256"],
          [(r["name"], r["status"]) for r in result["after_request"]["restored_files"]])


if __name__ == "__main__":
    main()
