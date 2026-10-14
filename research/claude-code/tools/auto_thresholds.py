"""Derive the auto-mode classifier thresholds from the scripted bisect runs (E41b/c/d, E41t-*, E41u-*).

  python -I auto_thresholds.py            # writes runtime-logs/auto-mode-thresholds/summary.json

Each run scripted the classifier's stage-1 severity, optionally a stage-2 severity, and the harness
recorded how many classifier requests were made and whether the tool call ran (a file was written).
Stage 1 is the fast score: allowed in one request, or escalated to stage 2 (two requests).
Stage 2 is allowed (tool ran) or denied (no tool).
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAB = Path(r"C:/Users/sergi/cc-rea-lab")


def parse_run_id(run_id):
    """Return (stage1, stage2 or None) encoded in a bisect run id, else None."""
    match = re.fullmatch(r"E41t-sev([0-9_]+)", run_id)
    if match:
        return float(match.group(1).replace("_", ".")), None
    match = re.fullmatch(r"E41u-s2-([0-9_]+)", run_id)
    if match:
        return 30.0, float(match.group(1).replace("_", "."))
    match = re.fullmatch(r"E41[bcd]-auto-sev([0-9_]+)", run_id)
    if match:
        return float(match.group(1).replace("_", ".")), None
    return None


def bounds(points):
    """points: [(score, bool)]; True means 'passes' (allowed / not escalated).

    Returns (highest passing score, lowest failing score). A strict `>` threshold T gives
    (T, next value above T).
    """
    passing = [s for s, ok in points if ok]
    failing = [s for s, ok in points if not ok]
    if passing and failing and max(passing) >= min(failing):
        raise ValueError("scores are not monotonic: a passing score is not below every failing score")
    return (max(passing) if passing else None, min(failing) if failing else None)


def derive(rows):
    stage1 = [(r["stage1"], r["classifier_requests"] == 1) for r in rows if r["stage2"] is None]
    stage2 = [(r["stage2"], r["tool_ran"]) for r in rows if r["stage2"] is not None]
    return {"t1": dict(zip(("highest_allowed", "lowest_escalated"), bounds(stage1))),
            "t2": dict(zip(("highest_allowed", "lowest_denied"), bounds(stage2)))}


def collect(runtime_logs):
    rows = []
    for d in sorted(Path(runtime_logs).iterdir()):
        parsed = parse_run_id(d.name)
        if not parsed or not (d / "http-summary.json").exists():
            continue
        http = json.loads((d / "http-summary.json").read_text(encoding="utf-8"))
        classifier = [h for h in http if isinstance(h["request"].get("body"), dict)
                      and not h["request"]["body"].get("tools_count")]
        ran = (LAB / f"proj-{d.name.lower()}" / "auto-made-1.txt").exists()
        rows.append({"run": d.name, "stage1": parsed[0], "stage2": parsed[1],
                     "classifier_requests": len(classifier), "tool_ran": ran})
    return rows


def main():
    logs = ROOT / "runtime-logs"
    rows = collect(logs)
    out = {"id": "auto-mode-thresholds", "cli_version": "2.1.296",
           "method": "scripted classifier replies through the lab proxy; no upstream model call",
           "rule": "block when severity > threshold (strict)", "derived": derive(rows), "runs": rows}
    target = logs / "auto-mode-thresholds"
    target.mkdir(exist_ok=True)
    (target / "summary.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out["derived"]))


if __name__ == "__main__":
    sys.exit(main())
