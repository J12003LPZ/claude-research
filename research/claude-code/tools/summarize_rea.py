"""Summarize saved REA diagnostics (doctor / capabilities / providers JSON).

Usage: python -I summarize_rea.py <runtime-logs/rea dir>
"""
import json
import os
import sys


def load(p):
    with open(p, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def walk_keys(obj, depth=0, maxdepth=2, prefix=""):
    if depth > maxdepth:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            t = type(v).__name__
            extra = f" len={len(v)}" if isinstance(v, (list, dict, str)) else f" = {v!r}"
            if isinstance(v, str) and len(v) < 160:
                extra = f" = {v!r}"
            print(f"{'  ' * depth}{prefix}{k}: {t}{extra}")
            walk_keys(v, depth + 1, maxdepth)
    elif isinstance(obj, list) and obj and isinstance(obj[0], dict) and depth <= maxdepth:
        print(f"{'  ' * depth}[0] keys: {sorted(obj[0].keys())}")


def main():
    d = sys.argv[1]
    doc = load(os.path.join(d, "rea-doctor.json"))
    print("=== doctor: structure ===")
    walk_keys(doc, maxdepth=1)
    prov = load(os.path.join(d, "rea-providers.json"))
    caps = prov.get("capabilities", [])
    avail = [c for c in caps if c.get("available")]
    unavail = [c for c in caps if not c.get("available")]
    print(f"\n=== providers: {len(caps)} operations, {len(avail)} available, {len(unavail)} unavailable ===")
    reasons = {}
    for c in unavail:
        reasons.setdefault((c.get("availability_code"), c.get("reason")), []).append(c["operation"])
    for (code, reason), ops in sorted(reasons.items(), key=lambda x: -len(x[1])):
        print(f"\n[{code}] {reason}  ({len(ops)})")
        print("   " + ", ".join(sorted(ops)))
    print("\n=== available operations ===")
    print(", ".join(sorted(c["operation"] for c in avail)))
    print("\n=== other top-level provider keys ===")
    for k, v in prov.items():
        if k != "capabilities":
            print(k, "=", json.dumps(v)[:600])


if __name__ == "__main__":
    main()
