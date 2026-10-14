"""Drive `claude -p --input-format stream-json` with a timed script (interrupt experiments).

  python -I run_stream.py --id E13 --cwd <proj> --script script.json [--timeout 120] -- <claude args>

script.json: [{"at_s": 0, "send": {...json line...}}, {"at_s": 4, "send": {...}}, {"at_s": 9, "close": true}]
Each stdout line is stored with a receive timestamp in stdout.timed.jsonl, plus the plain
stdout.jsonl that summarize_captures.py reads. Uses the same proxy and env scrubbing as
run_exp.py.
"""
import argparse
import json
import os
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_exp import KEEP, LAB, SCRUB_PREFIXES, TOOLS, free_port  # noqa: E402


CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")


def exe_info():
    """Version string and SHA-256 of the binary this run uses (CLAUDE_BIN overrides PATH)."""
    import hashlib, shutil
    path = shutil.which(CLAUDE_BIN) or CLAUDE_BIN
    try:
        digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    except OSError:
        digest = None
    ver = subprocess.run([CLAUDE_BIN, "--version"], capture_output=True, text=True).stdout.strip()
    return ver, digest


def build_auto_permission_response(request_id, subtype, behavior, message):
    """Return a host response only for a CLI can_use_tool request."""
    if subtype != "can_use_tool" or behavior is None:
        return None
    response = {"behavior": behavior}
    if behavior == "deny":
        response["message"] = message
    return {"type": "control_response", "response": {
        "subtype": "success", "request_id": request_id, "response": response,
    }}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--cwd", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--env", action="append", default=[])
    ap.add_argument("--permission-behavior", choices=["allow", "deny"],
                    help="auto-answer can_use_tool control requests")
    ap.add_argument("--permission-message", default="Denied by lab host",
                    help="message used for an auto-deny response")
    ap.add_argument("rest", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    rest = [x for x in a.rest if x != ""]
    extra = rest[1:] if rest and rest[0] == "--" else rest
    script = json.load(open(a.script, encoding="utf-8"))

    raw = os.path.join(LAB, "raw", a.id)
    os.makedirs(os.path.join(raw, "http"), exist_ok=True)
    env = dict(os.environ)
    scrubbed = sorted(k for k in env if k.upper().startswith(SCRUB_PREFIXES) and k not in KEEP)
    for k in scrubbed:
        del env[k]
    for kv in a.env:
        k, v = kv.split("=", 1)
        env[k] = v
    port = free_port()
    proxy = subprocess.Popen(["node", os.path.join(TOOLS, "capture_proxy.mjs"), str(port), os.path.join(raw, "http")],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    proxy.stdout.readline()
    env["ANTHROPIC_BASE_URL"] = f"http://127.0.0.1:{port}"

    cmd = [CLAUDE_BIN, "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
           "--include-partial-messages", "--include-hook-events", "--debug-file", os.path.join(raw, "debug.log")] + extra
    version, exe_sha256 = exe_info()
    t0 = time.time()
    p = subprocess.Popen(cmd, cwd=a.cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=open(os.path.join(raw, "stderr.txt"), "wb"))

    write_lock = threading.Lock()
    control_events = []

    def send_line(value):
        with write_lock:
            p.stdin.write((json.dumps(value) + "\n").encode("utf-8"))
            p.stdin.flush()

    def reader():
        with open(os.path.join(raw, "stdout.jsonl"), "wb") as plain, \
                open(os.path.join(raw, "stdout.timed.jsonl"), "w", encoding="utf-8") as timed:
            for line in p.stdout:
                plain.write(line)
                plain.flush()
                try:
                    o = json.loads(line)
                    tag = o.get("type", "?") + ("/" + str(o.get("subtype")) if o.get("subtype") else "")
                    if o.get("type") == "stream_event":
                        tag += "/" + o["event"].get("type", "")
                    if o.get("type") == "control_request":
                        req = o.get("request") or {}
                        entry = {"t_s": round(time.time() - t0, 3),
                                 "request_id": o.get("request_id"),
                                 "subtype": req.get("subtype")}
                        control_events.append(entry)
                        reply = build_auto_permission_response(
                            o.get("request_id"), req.get("subtype"),
                            a.permission_behavior, a.permission_message,
                        )
                        if reply:
                            try:
                                send_line(reply)
                                entry["auto_response"] = reply["response"]["response"]
                            except (BrokenPipeError, OSError) as e:
                                entry["auto_response_error"] = str(e)
                except Exception:
                    tag = "<non-json>"
                timed.write(json.dumps({"t_s": round(time.time() - t0, 3), "tag": tag}) + "\n")
                timed.flush()

    th = threading.Thread(target=reader, daemon=True)
    th.start()
    sent = []
    for step in script:
        delay = step["at_s"] - (time.time() - t0)
        if delay > 0:
            time.sleep(delay)
        if p.poll() is not None:
            break
        try:
            if step.get("close"):
                with write_lock:
                    p.stdin.close()
                sent.append({"t_s": round(time.time() - t0, 3), "close": True})
            else:
                send_line(step["send"])
                s = step["send"]
                sent.append({"t_s": round(time.time() - t0, 3), "type": s.get("type"),
                             "subtype": (s.get("request") or {}).get("subtype")})
        except (BrokenPipeError, OSError) as e:
            sent.append({"t_s": round(time.time() - t0, 3), "error": str(e)})
            break
    killed = None
    try:
        p.wait(timeout=a.timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        killed = "timeout-kill"
        p.wait()
    th.join(timeout=3)
    time.sleep(0.5)
    proxy.terminate()
    run = {"id": a.id, "cwd": a.cwd, "argv": cmd[:10] + ["<debug-file>"] + extra, "prompt": None, "stdin_script": sent,
           "control_events": control_events, "permission_behavior": a.permission_behavior,
           "extra_env_names": [kv.split("=", 1)[0] for kv in a.env], "scrubbed_env_names": scrubbed, "proxy_port": port,
           "exit_code": p.returncode, "killed": killed, "duration_s": round(time.time() - t0, 3),
           "cli_version": version, "exe_sha256": exe_sha256, "started_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0)), "fault": None}
    json.dump(run, open(os.path.join(raw, "run.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps({"id": a.id, "exit_code": p.returncode, "killed": killed, "sent": sent}))


if __name__ == "__main__":
    main()
