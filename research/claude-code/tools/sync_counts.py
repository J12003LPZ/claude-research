"""Rewrite the run counts quoted in the prose reports from runtime-logs/MANIFEST.json.

  python -I sync_counts.py            # rewrite in place
  python -I sync_counts.py --check    # exit 1 when any quoted count is stale

The manifest is the single source of truth: experiment entries counted by id family
(E, C, P). Only the sentences listed in PATTERNS are touched.
"""
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PATTERNS = [
    ("PROGRESS.md", r"\d+ manifest runs: \d+ E, \d+ C, \d+ P", "{n} manifest runs: {E} E, {C} C, {P} P"),
    ("README.md", r"\d+ instrumented lab runs against disposable projects \(\d+ E-runs, \d+ C-probes, and \d+ P-mode probes\)",
     "{n} instrumented lab runs against disposable projects ({E} E-runs, {C} C-probes, and {P} P-mode probes)"),
    ("01-environment-and-provenance.md", r"across the \d+ manifest runs", "across the {n} manifest runs"),
    ("06-verification-matrix.md", r"The \d+ manifest runs include scoped", "The {n} manifest runs include scoped"),
]


def family_counts(manifest_path):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    ids = [row["id"] for row in manifest["entries"] if row["kind"] == "experiment"]
    counts = collections.Counter(re.match(r"[A-Z]", i).group(0) for i in ids)
    return {"n": len(ids), "E": counts["E"], "C": counts["C"], "P": counts["P"]}


def sync(text, regex, template, counts):
    """Return (new_text, replacements). Exactly one match is required."""
    matches = re.findall(regex, text)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one match for {regex!r}, found {len(matches)}")
    return re.sub(regex, template.format(**counts), text), 1


def main(argv):
    check = "--check" in argv
    counts = family_counts(ROOT / "runtime-logs" / "MANIFEST.json")
    stale = []
    for name, regex, template in PATTERNS:
        path = ROOT / name
        raw = path.read_bytes().decode("utf-8")
        new, _ = sync(raw, regex, template, counts)
        if new != raw:
            stale.append(name)
            if not check:
                path.write_bytes(new.encode("utf-8"))
    print(f"counts {counts}; {'stale' if check else 'updated'}: {sorted(set(stale)) or 'none'}")
    return 1 if (check and stale) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
