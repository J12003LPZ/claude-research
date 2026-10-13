"""Field-level schema of session transcripts written for the LAB projects only.

  python -I transcript_schema.py [--print]

Refuses any project directory whose sanitized name does not contain "cc-rea-lab", so
real conversations are never opened. Emits structure (entry types, keys, value types,
parent links) and no message text.
"""
import collections
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from summarize_captures import OUT  # noqa: E402

PROJECTS = os.path.join(os.path.expanduser("~"), ".claude", "projects")


def tname(v):
    if isinstance(v, dict):
        return "object{" + ",".join(sorted({("toolu_<id>" if k.startswith("toolu_") else k) for k in v.keys()})[:14]) + "}"
    if isinstance(v, list):
        return "array<" + (tname(v[0]) if v else "") + ">"
    return type(v).__name__


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    dirs = [d for d in glob.glob(os.path.join(PROJECTS, "*")) if "cc-rea-lab" in os.path.basename(d)]
    layout, types, chains = [], {}, []
    for d in dirs:
        proj = os.path.basename(d)
        files = []
        for dp, _dn, fns in os.walk(d):
            for fn in fns:
                rel = os.path.relpath(os.path.join(dp, fn), d).replace("\\", "/")
                parts = rel.split("/")
                shape = "/".join("<session-uuid>" + os.path.splitext(p)[1] if len(p) >= 36 and p[8:9] == "-" else
                                 ("agent-<id>" + os.path.splitext(p)[1] if p.startswith("agent-") else p) for p in parts)
                shape = shape.replace("<session-uuid>.jsonl", "<session-uuid>.jsonl")
                files.append(shape)
        layout.append({"project_dir": proj, "file_shapes": dict(collections.Counter(files))})
        for f in glob.glob(os.path.join(d, "**", "*.jsonl"), recursive=True):
            entries = []
            for line in open(f, encoding="utf-8", errors="replace"):
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except Exception:
                    continue
            kind = "subagent" if os.sep + "subagents" + os.sep in f or os.path.basename(f).startswith("agent-") else "main"
            seq = []
            uuids = {e.get("uuid") for e in entries if e.get("uuid")}
            for e in entries:
                t = e.get("type")
                key = f"{kind}:{t}" + (f"/{e.get('subtype')}" if e.get("subtype") else "")
                slot = types.setdefault(key, {"count": 0, "fields": {}})
                slot["count"] += 1
                for k, v in e.items():
                    slot["fields"].setdefault(k, set()).add(tname(v)[:160])
                if t in ("user", "assistant"):
                    m = e.get("message", {})
                    c = m.get("content")
                    blocks = [b.get("type") for b in c] if isinstance(c, list) else ["string"]
                    slot.setdefault("message_fields", set()).update(m.keys())
                    slot.setdefault("block_types", set()).update(blocks)
                seq.append({"type": t, "subtype": e.get("subtype"),
                            "has_uuid": "uuid" in e, "parent": ("null" if e.get("parentUuid") is None else
                                                               ("resolves" if e.get("parentUuid") in uuids else "dangling")) if "parentUuid" in e else "absent",
                            "isSidechain": e.get("isSidechain"), "isMeta": e.get("isMeta"),
                            "isCompactSummary": e.get("isCompactSummary")})
            chains.append({"project_dir": proj, "kind": kind, "entries": len(entries),
                           "sequence": [f"{s['type']}{'/' + s['subtype'] if s['subtype'] else ''}"
                                        f"{'[meta]' if s['isMeta'] else ''}{'[compactSummary]' if s['isCompactSummary'] else ''}"
                                        f"{'' if s['parent'] in ('resolves', 'absent') else '(parent:' + s['parent'] + ')'}"
                                        for s in seq][:120]})
    for slot in types.values():
        slot["fields"] = {k: sorted(v) for k, v in sorted(slot["fields"].items())}
        for k in ("message_fields", "block_types"):
            if k in slot:
                slot[k] = sorted(x for x in slot[k] if x)
    out = {"projects_root_shape": "~/.claude/projects/<sanitized-cwd>/", "layout": layout, "entry_types": types, "files": chains}
    os.makedirs(os.path.join(OUT, "sessions"), exist_ok=True)
    json.dump(out, open(os.path.join(OUT, "sessions", "transcript-schema.json"), "w", encoding="utf-8"), indent=1)
    if "--print" in sys.argv:
        for l in layout:
            print("PROJECT", l["project_dir"]); [print("   ", n, s) for s, n in sorted(l["file_shapes"].items())]
        for k, s in sorted(types.items()):
            print(f"\n[{k}] x{s['count']}")
            print("   fields:", ", ".join(f"{f}:{'|'.join(t)[:60]}" for f, t in s["fields"].items()))
            if "block_types" in s:
                print("   message_fields:", s["message_fields"], " block_types:", s["block_types"])


if __name__ == "__main__":
    main()
