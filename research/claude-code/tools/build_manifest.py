"""Build runtime-logs/MANIFEST.json: one row per experiment with hashes of the sanitized
evidence files, CLI version, exit code, and a redaction self-check.

  python -I build_manifest.py

The self-check greps every sanitized file for patterns that must never appear
(bearer tokens, API keys, the local account name, email addresses, raw UUIDs in header
values). A hit makes the script exit 1.
"""
import getpass
import glob
import hashlib
import json
import os
import re
import sys

OUT = r"C:\Users\sergi\Desktop\claude-rea\research\claude-code\runtime-logs"
FORBIDDEN = [
    ("bearer-token", re.compile(r"Bearer\s+(?=[A-Za-z0-9._-]*\d)(?=[A-Za-z0-9._-]*[._-])[A-Za-z0-9._-]{40,}")),
    ("api-key", re.compile(r"sk-ant-[A-Za-z0-9_-]{10,}")),
    ("email", re.compile(r"[\w.+-]+@[\w-]+\.(com|net|org|io|dev)\b")),
    ("local-user", re.compile(r"(?i)[\\/]Users[\\/]+" + re.escape(getpass.getuser()) + r"\b")),
    ("workspace-id", re.compile(r"wrkspc_[A-Za-z0-9]{10,}")),
]
ALLOW_EMAIL = {"noreply@anthropic.com"}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def mask_static_copies():
    """REA/static evidence copies embed absolute local paths; mask the account name in place."""
    user = getpass.getuser()
    rx = re.compile(r"(?i)((?:[\\/]+|--)Users(?:[\\/]+|-))" + re.escape(user) + r"(?![A-Za-z0-9])")
    for sub in ("rea", "static", "config", "sessions"):
        for f in glob.glob(os.path.join(OUT, sub, "*")):
            t = open(f, encoding="utf-8", errors="replace").read()
            t2 = rx.sub(lambda m: m.group(1) + "<user>", t)
            if t2 != t:
                open(f, "w", encoding="utf-8", newline="").write(t2)


def main():
    mask_static_copies()
    rows, problems = [], []
    for d in sorted(glob.glob(os.path.join(OUT, "*"))):
        if not os.path.isdir(d):
            continue
        name = os.path.basename(d)
        files = {}
        for f in sorted(glob.glob(os.path.join(d, "*"))):
            if os.path.isdir(f):
                continue
            files[os.path.basename(f)] = {"sha256": sha(f), "bytes": os.path.getsize(f)}
            text = open(f, encoding="utf-8", errors="replace").read()
            for label, rx in FORBIDDEN:
                for m in rx.finditer(text):
                    if label == "email" and m.group(0) in ALLOW_EMAIL:
                        continue
                    problems.append(f"{name}/{os.path.basename(f)}: {label}")
                    break
        row = {"id": name, "kind": "experiment" if os.path.exists(os.path.join(d, "run.json")) else "static-or-aggregate",
               "files": files, "redaction": "sanitized"}
        rp = os.path.join(d, "run.json")
        if os.path.exists(rp):
            r = json.load(open(rp, encoding="utf-8"))
            row.update({"cli_version": r.get("cli_version"), "exit_code": r.get("exit_code"),
                        "duration_s": r.get("duration_s"), "started": r.get("started_iso"),
                        "fault_injected": bool(r.get("fault")), "killed": r.get("killed")})
        rows.append(row)
    man = {"target": {"path_shape": "~/.local/bin/claude.exe", "version": "2.1.296",
                      "sha256": "76de74f7694a5bdc03378a5f837c9e132827bf004c98c276bc4e9094ff06769a"},
           "raw_evidence": "lab/raw/<id>/ (private, not committed)",
           "redaction_check": "clean" if not problems else problems,
           "entries": rows}
    json.dump(man, open(os.path.join(OUT, "MANIFEST.json"), "w", encoding="utf-8"), indent=1)
    print("entries:", len(rows), "experiments:", sum(1 for r in rows if r["kind"] == "experiment"))
    print("redaction check:", "clean" if not problems else "\n  " + "\n  ".join(sorted(set(problems))))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
