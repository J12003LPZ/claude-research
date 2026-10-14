"""Check that the behaviour table in 06-verification-matrix.md agrees with its own `Counts:` footer.

  python -I check_matrix.py

Rows are the numbered lines of section 2 (`| 30a |`, `| 44 |`, ...). The status is the first of
Verified / Partially verified / Untested / Blocked that starts the last table cell. Exit 1 on mismatch.
"""
import collections
import re
import sys
from pathlib import Path

MATRIX = Path(__file__).resolve().parent.parent / "06-verification-matrix.md"
ROW = re.compile(r"^\| \d+[a-z]? \|")
STATUS = re.compile(r"\|\s*(Verified|Partially verified|Untested|Blocked)\b[^|]*\|?\s*$")
FOOTER = re.compile(
    r"Counts: (\d+) behaviours enumerated\. Verified (\d+), partially verified (\d+), untested (\d+), blocked (\d+)\."
)


SECTION = re.compile(r"^## 2\.[^\n]*\n(.*?)(?=^## \d+\.|\Z)", re.S | re.M)


def tally(text):
    counts = collections.Counter()
    rows = 0
    section = SECTION.search(text)
    # Only the behaviour table counts; other tables have numbered rows with status-like cells.
    for line in (section.group(1) if section else text).splitlines():
        if not ROW.match(line):
            continue
        match = STATUS.search(line)
        if match:
            rows += 1
            counts[match.group(1)] += 1
    return rows, counts


def footer(text):
    match = FOOTER.search(text)
    if not match:
        raise ValueError("no Counts footer found")
    n, verified, partial, untested, blocked = map(int, match.groups())
    return n, {"Verified": verified, "Partially verified": partial, "Untested": untested, "Blocked": blocked}


def main():
    text = MATRIX.read_text(encoding="utf-8")
    rows, counts = tally(text)
    want_rows, want = footer(text)
    got = {k: counts.get(k, 0) for k in want}
    ok = rows == want_rows and got == want
    print(f"rows {rows} {got} | footer {want_rows} {want} | {'OK' if ok else 'MISMATCH'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
