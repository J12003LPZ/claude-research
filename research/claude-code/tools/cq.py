"""Chunk query helper over the extracted tree + chunk index.

  python -I cq.py exp  <regex>              chunks whose export names match
  python -I cq.py grep <regex> [ctx] [max]  regex over all chunk bodies, prints ctx chars around hits
  python -I cq.py files <regex>             only chunk names + hit counts
  python -I cq.py show <chunk> <start> <len> print a slice of one chunk
  python -I cq.py info <chunk>              index entry for one chunk
  python -I cq.py who  <chunk>              chunks importing <chunk>

Environment: CQ_ROOT (extracted root), CQ_INDEX (chunk index json).
"""
import json
import os
import re
import sys

ROOT = os.environ.get("CQ_ROOT", r"C:\Users\sergi\Desktop\claude-rea\extracted\2.1.296\~BUN\root")
INDEX = os.environ.get("CQ_INDEX", r"C:\Users\sergi\Desktop\claude-rea\research\claude-code\runtime-logs\static\chunk-index-2.1.296.json")


def idx():
    with open(INDEX, "r", encoding="utf-8") as f:
        return json.load(f)


def read(rel):
    with open(os.path.join(ROOT, rel), "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def js_files():
    for dp, _dn, fns in os.walk(ROOT):
        for fn in sorted(fns):
            rel = os.path.relpath(os.path.join(dp, fn), ROOT).replace("\\", "/")
            if rel.endswith(".js") or rel == "cli" or rel.endswith(".mjs"):
                yield rel


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cmd = sys.argv[1]
    if cmd == "exp":
        rx = re.compile(sys.argv[2])
        for rel, e in sorted(idx().items()):
            hit = [x for x in e["exports"] if rx.search(x)]
            if hit:
                print(f"{rel} ({e['size']}): {', '.join(hit[:40])}")
    elif cmd in ("grep", "files"):
        rx = re.compile(sys.argv[2])
        ctx = int(sys.argv[3]) if len(sys.argv) > 3 else 200
        mx = int(sys.argv[4]) if len(sys.argv) > 4 else 40
        shown = 0
        for rel in js_files():
            src = read(rel)
            ms = list(rx.finditer(src))
            if not ms:
                continue
            if cmd == "files":
                print(f"{len(ms):5d}  {rel} ({len(src)})")
                continue
            for m in ms:
                if shown >= mx:
                    print("... (max hits reached)")
                    return
                a, b = max(0, m.start() - ctx), min(len(src), m.end() + ctx)
                print(f"--- {rel} @{m.start()}\n{src[a:b]}")
                shown += 1
    elif cmd == "show":
        src = read(sys.argv[2])
        s, n = int(sys.argv[3]), int(sys.argv[4])
        print(src[max(0, s):s + n])
    elif cmd == "info":
        e = idx()[sys.argv[2]]
        print(json.dumps(e, indent=1)[:6000])
    elif cmd == "who":
        t = sys.argv[2]
        for rel, e in sorted(idx().items()):
            kinds = [k for k in ("static_imports", "dynamic_imports", "require_imports") if t in e[k]]
            if kinds:
                print(rel, e["size"], kinds)


if __name__ == "__main__":
    main()
