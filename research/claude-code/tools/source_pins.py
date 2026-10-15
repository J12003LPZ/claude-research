"""Verify that cited `chunk@offset` anchors still point at the construct a report names.

`audit_static_citations.py` only proves an offset lies inside a chunk. A pin goes one
step further: it records the literal text that must start at that offset, so a changed
extraction, a miscounted offset, or a drifted report is caught mechanically. A pin does
not prove the prose claim; it proves the anchor lands on the named construct.

Usage:
  python -I source_pins.py --root <extracted root> --pins pins.json [--reports a.md ...]

pins.json: {"pins": [{"anchor": "chunk-x.js@123", "expect": "function foo("}, ...]}
With --reports, every pinned anchor must also be cited by at least one report.
Exit status 1 when any pin fails.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_static_citations import extract_anchors  # noqa: E402


def split_anchor(anchor):
    chunk, _, offset = anchor.partition("@")
    return chunk, int(offset)


def check_pins(pins, extract_root):
    """Return one result per pin: status is ok, mismatch, missing_file or out_of_bounds."""
    root = Path(extract_root)
    cache = {}
    results = []
    for pin in pins:
        chunk, offset = split_anchor(pin["anchor"])
        path = root / chunk
        if not path.is_file():
            results.append({**pin, "status": "missing_file"})
            continue
        if chunk not in cache:
            cache[chunk] = path.read_text(encoding="utf-8")
        text = cache[chunk]
        if offset >= len(text):
            results.append({**pin, "status": "out_of_bounds"})
            continue
        found = text[offset:offset + len(pin["expect"])]
        results.append({**pin, "status": "ok" if found == pin["expect"] else "mismatch", "found": found})
    return results


def uncited(pins, report_paths):
    """Return pinned anchors that no report cites as `chunk@offset`."""
    cited = set()
    for report in report_paths:
        for anchor in extract_anchors(Path(report).read_text(encoding="utf-8")):
            cited.add((anchor["chunk"], anchor["offset"]))
    return [p["anchor"] for p in pins if split_anchor(p["anchor"]) not in cited]


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--pins", required=True)
    parser.add_argument("--reports", nargs="*", default=[])
    args = parser.parse_args(argv)
    pins = json.loads(Path(args.pins).read_text(encoding="utf-8"))["pins"]
    results = check_pins(pins, args.root)
    bad = [r for r in results if r["status"] != "ok"]
    for r in bad:
        print("FAIL %s %s expect=%r found=%r" % (r["status"], r["anchor"], r["expect"], r.get("found")))
    missing = uncited(pins, args.reports) if args.reports else []
    for anchor in missing:
        print("UNCITED %s" % anchor)
    print("pins=%d ok=%d failed=%d uncited=%d" % (len(results), len(results) - len(bad), len(bad), len(missing)))
    return 1 if bad or missing else 0


if __name__ == "__main__":
    sys.exit(main())
