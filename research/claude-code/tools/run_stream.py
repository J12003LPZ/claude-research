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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--cwd", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--env", action="append", default=[])
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

    cmd = ["claude", "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
           "--include-partial-messages", "--include-hook-events", "--debug-file", os.path.join(raw, "debug.log")] + extra
    t0 = time.time()
    p = subprocess.Popen(cmd, cwd=a.cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=open(os.path.join(raw, "stderr.txt"), "wb"))

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
                except Exception:
                    tag = "<non-json>"
                timed.write(json.dumps({"t_s": round(time.time() - t0, 3), "tag": tag}) + "\n")

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
                p.stdin.close()
                sent.append({"t_s": round(time.time() - t0, 3), "close": True})
            else:
                p.stdin.write((json.dumps(step["send"]) + "\n").encode("utf-8"))
                p.stdin.flush()
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
           "extra_env_names": [kv.split("=", 1)[0] for kv in a.env], "scrubbed_env_names": scrubbed, "proxy_port": port,
           "exit_code": p.returncode, "killed": killed, "duration_s": round(time.time() - t0, 3),
           "cli_version": "2.1.296 (Claude Code)", "started_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0)), "fault": None}
    json.dump(run, open(os.path.join(raw, "run.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps({"id": a.id, "exit_code": p.returncode, "killed": killed, "sent": sent}))


if __name__ == "__main__":
    main()
