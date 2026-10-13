"""Index the extracted Bun chunks: static imports, dynamic imports, export names, size.

Usage: python -I chunk_index.py <extracted root dir> <out index.json>

Regex-based on minified ESM emitted by Bun's bundler. It reads module specifiers and
export clauses only; it does not parse function bodies. Export names survive
minification because dynamic `import()` call sites destructure them by name, so they are
real identifiers from the shipped artifact (not invented).
"""
import json
import os
import re
import sys

IMP = re.compile(r'import\s*(?:\{([^}]*)\}|\*\s*as\s+[\w$]+|[\w$]+)?\s*(?:from)?\s*"(B:/~BUN/root/[^"]+|[\w@/.:-]+)"')
DYN = re.compile(r'import\("([^"]+)"\)')
REQ = re.compile(r'import\.meta\.require\("([^"]+)"\)')
EXP = re.compile(r'export\s*\{([^}]*)\}')


def names(clause):
    out = []
    for part in clause.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.match(r'([\w$]+)(?:\s+as\s+([\w$]+))?$', part)
        if m:
            out.append(m.group(2) or m.group(1))
    return out


def short(spec):
    return spec.replace("B:/~BUN/root/", "")


def main():
    root, outp = sys.argv[1], sys.argv[2]
    idx = {}
    for dp, _dn, fns in os.walk(root):
        for fn in fns:
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, root).replace("\\", "/")
            if not (rel.endswith(".js") or rel == "cli" or rel.endswith(".mjs")):
                continue
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                src = f.read()
            head = src[:400000]
            static, ext = [], []
            for m in IMP.finditer(head):
                spec = m.group(2)
                (static if spec.startswith("B:/") else ext).append(short(spec))
            exports = []
            for m in EXP.finditer(src):
                exports.extend(names(m.group(1)))
            idx[rel] = {
                "size": len(src),
                "static_imports": sorted(set(static)),
                "external_imports": sorted(set(ext)),
                "dynamic_imports": sorted(set(short(s) for s in DYN.findall(src) if s.startswith("B:/"))),
                "require_imports": sorted(set(short(s) for s in REQ.findall(src))),
                "exports": sorted(set(exports)),
            }
    # reverse edges
    for rel, e in idx.items():
        e["imported_by_count"] = 0
    for rel, e in idx.items():
        for t in set(e["static_imports"]) | set(e["dynamic_imports"]) | set(e["require_imports"]):
            if t in idx:
                idx[t]["imported_by_count"] += 1
    with open(outp, "w", encoding="utf-8") as g:
        json.dump(idx, g, indent=0)
    readable = [(r, e) for r, e in idx.items() if any(len(x) > 3 for x in e["exports"])]
    print("chunks indexed:", len(idx))
    print("chunks with readable (>3 char) export names:", len(readable))
    print("total exports:", sum(len(e["exports"]) for e in idx.values()))
    print("static edges:", sum(len(e["static_imports"]) for e in idx.values()),
          "dynamic edges:", sum(len(e["dynamic_imports"]) for e in idx.values()))


if __name__ == "__main__":
    main()
