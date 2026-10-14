"""Inventory and validate `chunk-*.js@offset` citations in static reports.

This validates that an anchor names an extracted chunk and points within its decoded
UTF-8 text. It does not establish the prose claim at that anchor; semantic review is
recorded separately in static-audit.md.

Usage:
  python -I audit_static_citations.py --root <extracted root> --output audit.json report1.md [...]
"""
import argparse
import json
import re
from pathlib import Path

ANCHOR = re.compile(r"\b(chunk-[A-Za-z0-9_-]+\.js)@(~?)(\d+)\b")


def extract_anchors(text):
    """Return ordered citation anchors from one report body."""
    return [
        {"chunk": match.group(1), "offset": int(match.group(3)), "approximate": bool(match.group(2))}
        for match in ANCHOR.finditer(text)
    ]


def audit_report(report_path, extract_root):
    """Check every parsed citation in one report against its extracted source file."""
    report_path = Path(report_path)
    extract_root = Path(extract_root)
    anchors = extract_anchors(report_path.read_text(encoding="utf-8"))
    entries = []
    resolvable = missing_file = out_of_bounds = 0
    source_cache = {}

    for anchor in anchors:
        source = extract_root / anchor["chunk"]
        if not source.is_file():
            status = "missing_file"
            missing_file += 1
        else:
            size = source_cache.get(source)
            if size is None:
                size = len(source.read_text(encoding="utf-8", errors="replace"))
                source_cache[source] = size
            if anchor["offset"] >= size:
                status = "out_of_bounds"
                out_of_bounds += 1
            else:
                status = "resolvable"
                resolvable += 1
        entries.append({**anchor, "status": status})

    return {
        "report": report_path.name,
        "anchors_total": len(anchors),
        "anchors_unique": len({(e["chunk"], e["offset"]) for e in entries}),
        "anchors_resolvable": resolvable,
        "anchors_missing_file": missing_file,
        "anchors_out_of_bounds": out_of_bounds,
        "entries": entries,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="extracted ~BUN/root directory")
    parser.add_argument("--output", type=Path, help="write JSON inventory here")
    parser.add_argument("reports", nargs="+", type=Path)
    args = parser.parse_args()

    reports = [audit_report(report, args.root) for report in args.reports]
    total = {
        "reports": reports,
        "summary": {
            key: sum(report[key] for report in reports)
            for key in ("anchors_total", "anchors_resolvable", "anchors_missing_file", "anchors_out_of_bounds")
        },
    }
    text = json.dumps(total, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
