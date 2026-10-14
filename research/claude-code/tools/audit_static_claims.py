"""Create a reproducible paragraph-level evidence ledger for static reports.

Each non-heading Markdown unit receives its section, line range, text digest and cited
chunk anchors. Source text is not copied to the ledger. An anchor is mechanically
resolvable only when it names an extracted chunk and lies inside that chunk's decoded
UTF-8 text.

Usage:
  python -I audit_static_claims.py --root <extracted root> --output ledger.json report.md [...]
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_static_citations import extract_anchors  # noqa: E402

HEADING = re.compile(r"^#{1,6}\s+(.*)$")


def heading_at(lines, line_number):
    """Return the closest preceding Markdown heading, without its hashes."""
    for line in reversed(lines[:line_number - 1]):
        match = HEADING.match(line)
        if match:
            return match.group(1).strip()
    return "<preamble>"


def units_from_report(report_path):
    """Split report prose into blank-line-delimited auditable units."""
    lines = Path(report_path).read_text(encoding="utf-8").splitlines()
    units = []
    start = None
    current = []

    def finish():
        nonlocal start, current
        if current:
            text = "\n".join(current).strip()
            if text and not all(HEADING.match(line) for line in current):
                units.append((start, start + len(current) - 1, text))
        start, current = None, []

    for number, line in enumerate(lines, start=1):
        if not line.strip():
            finish()
        elif HEADING.match(line):
            finish()
        else:
            if start is None:
                start = number
            current.append(line)
    finish()
    return lines, units


def anchor_statuses(anchors, extract_root, source_lengths):
    statuses = []
    for anchor in anchors:
        source = Path(extract_root) / anchor["chunk"]
        if not source.is_file():
            status = "missing_file"
        else:
            length = source_lengths.get(source)
            if length is None:
                length = len(source.read_text(encoding="utf-8", errors="replace"))
                source_lengths[source] = length
            status = "resolvable" if anchor["offset"] < length else "out_of_bounds"
        statuses.append({**anchor, "status": status})
    return statuses


def inventory_report(report_path, extract_root):
    """Build paragraph-level source-anchor inventory for one static report."""
    report_path = Path(report_path)
    extract_root = Path(extract_root)
    lines, raw_units = units_from_report(report_path)
    source_lengths = {}
    units = []
    for start, end, text in raw_units:
        anchors = anchor_statuses(extract_anchors(text), extract_root, source_lengths)
        units.append({
            "heading": heading_at(lines, start),
            "line_start": start,
            "line_end": end,
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16],
            "text_chars": len(text),
            "anchors": anchors,
            "anchor_status": (
                "without_anchors" if not anchors
                else "all_resolvable" if all(anchor["status"] == "resolvable" for anchor in anchors)
                else "has_invalid_anchor"
            ),
        })
    return {
        "report": report_path.name,
        "units_total": len(units),
        "units_all_anchors_resolvable": sum(unit["anchor_status"] == "all_resolvable" for unit in units),
        "units_without_anchors": sum(unit["anchor_status"] == "without_anchors" for unit in units),
        "units_has_invalid_anchor": sum(unit["anchor_status"] == "has_invalid_anchor" for unit in units),
        "units": units,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("reports", nargs="+", type=Path)
    args = parser.parse_args()
    payload = {"reports": [inventory_report(report, args.root) for report in args.reports]}
    payload["summary"] = {
        key: sum(report[key] for report in payload["reports"])
        for key in ("units_total", "units_all_anchors_resolvable", "units_without_anchors", "units_has_invalid_anchor")
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
