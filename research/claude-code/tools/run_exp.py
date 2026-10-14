"""Run one controlled Claude Code experiment with instrumentation.

  python -I run_exp.py --id E01 --cwd <lab project> --prompt "..." [--no-proxy]
                       [--timeout 300] [--stdin-file f] [--kill-after SEC] [--interactive-off]
                       -- <extra claude args>

What it does:
  * starts tools/capture_proxy.mjs on a free port (unless --no-proxy) and points the CLI
    at it with ANTHROPIC_BASE_URL
  * scrubs the parent agent session's CLAUDE*/ANTHROPIC* env vars so the child is not a
    nested session (names of scrubbed vars are recorded, values never are)
  * runs `claude -p` with stream-json output, verbose, partial messages, hook events and a
    debug file, capturing stdout/stderr/exit code/timing
  * writes everything under <lab>/raw/<id>/ (raw, private, NOT committed)

Sanitized evidence is produced afterwards by summarize_captures.py.
"""
import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time

LAB = r"C:\Users\sergi\Desktop\claude-rea\lab"
TOOLS = os.path.dirname(os.path.abspath(__file__))
SCRUB_PREFIXES = ("CLAUDE", "ANTHROPIC", "MCP_", "OTEL_")
KEEP = {"CLAUDE_CONFIG_DIR"}


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


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--cwd", required=True)
    ap.add_argument("--prompt")
    ap.add_argument("--stdin-file")
    ap.add_argument("--no-proxy", action="store_true")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--kill-after", type=float, default=0, help="terminate the CLI after N seconds (interrupt experiments)")
    ap.add_argument("--kill-signal", default="break", choices=["break", "terminate", "kill"])
    ap.add_argument("--no-default-flags", action="store_true")
    ap.add_argument("--env", action="append", default=[], help="KEY=VALUE for the child")
    ap.add_argument("--fault", help="JSON written to fault.json before the run")
    ap.add_argument("rest", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    rest = [x for x in a.rest if x != ""]
    extra = rest[1:] if rest and rest[0] == "--" else rest
    if "--" in extra:
        raise SystemExit("refusing to run: stray -- in claude args would turn flags into positionals")

    raw = os.path.join(LAB, "raw", a.id)
    os.makedirs(raw, exist_ok=True)
    env = dict(os.environ)
    scrubbed = sorted(k for k in env if k.upper().startswith(SCRUB_PREFIXES) and k not in KEEP)
    for k in scrubbed:
        del env[k]
    for kv in a.env:
        k, v = kv.split("=", 1)
        env[k] = v

    proxy = None
    port = None
    if not a.no_proxy:
        port = free_port()
        cap = os.path.join(raw, "http")
        os.makedirs(cap, exist_ok=True)
        if a.fault:
            with open(os.path.join(cap, "fault.json"), "w") as f:
                f.write(a.fault)
        proxy = subprocess.Popen(["node", os.path.join(TOOLS, "capture_proxy.mjs"), str(port), cap],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        proxy.stdout.readline()
        env["ANTHROPIC_BASE_URL"] = f"http://127.0.0.1:{port}"

    cmd = [CLAUDE_BIN]
    if a.prompt is not None:
        cmd += ["-p", a.prompt]
    if not a.no_default_flags:
        cmd += ["--output-format", "stream-json", "--verbose", "--include-partial-messages",
                "--include-hook-events", "--debug-file", os.path.join(raw, "debug.log")]
    cmd += extra

    stdin = open(a.stdin_file, "rb") if a.stdin_file else subprocess.DEVNULL
    t0 = time.time()
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    with open(os.path.join(raw, "stdout.jsonl"), "wb") as so, open(os.path.join(raw, "stderr.txt"), "wb") as se:
        p = subprocess.Popen(cmd, cwd=a.cwd, env=env, stdin=stdin, stdout=so, stderr=se,
                             creationflags=flags, shell=False)
        killed = None
        try:
            if a.kill_after:
                try:
                    p.wait(timeout=a.kill_after)
                except subprocess.TimeoutExpired:
                    if a.kill_signal == "break":
                        p.send_signal(signal.CTRL_BREAK_EVENT)
                    elif a.kill_signal == "terminate":
                        p.terminate()
                    else:
                        p.kill()
                    killed = {"signal": a.kill_signal, "at_s": round(time.time() - t0, 3)}
            p.wait(timeout=a.timeout)
        except subprocess.TimeoutExpired:
            p.kill()
            killed = {"signal": "timeout-kill", "at_s": round(time.time() - t0, 3)}
            p.wait()
    dur = time.time() - t0
    time.sleep(0.5)
    if proxy:
        proxy.terminate()
    version, exe_sha256 = exe_info()
    run = {
        "id": a.id,
        "exe_sha256": exe_sha256,
        "cwd": a.cwd,
        "argv": ["claude"] + [x if x != a.prompt else "<prompt>" for x in cmd[1:]],
        "prompt": a.prompt,
        "stdin_file": a.stdin_file,
        "extra_env_names": [kv.split("=", 1)[0] for kv in a.env],
        "scrubbed_env_names": scrubbed,
        "proxy_port": port,
        "exit_code": p.returncode,
        "killed": killed,
        "duration_s": round(dur, 3),
        "cli_version": version,
        "started_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0)),
        "fault": json.loads(a.fault) if a.fault else None,
    }
    with open(os.path.join(raw, "run.json"), "w", encoding="utf-8") as f:
        json.dump(run, f, indent=1)
    print(json.dumps({k: run[k] for k in ("id", "exit_code", "killed", "duration_s", "cli_version")}))


if __name__ == "__main__":
    main()
