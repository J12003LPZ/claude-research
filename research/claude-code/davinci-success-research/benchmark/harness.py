"""Benchmark harness: materialize a task, judge a working tree against hidden acceptance tests, self-check the tasks.

The acceptance tests live outside the repo the agent sees. They run in a throwaway copy of the agent's tree, so
nothing the agent does can edit them, and the verdict never depends on what the agent said or on a CLI exit code.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TASKS_DIR = Path(__file__).resolve().parent / "tasks"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".git", ".pytest_cache")
LINE_RE = re.compile(r"^(test\w*) \(.*\) \.\.\. (.+)$")


def list_tasks() -> list[str]:
    return sorted(p.name for p in TASKS_DIR.iterdir() if (p / "task.json").exists())


def load_task(task_id: str) -> dict:
    base = TASKS_DIR / task_id
    meta = json.loads((base / "task.json").read_text(encoding="utf-8"))
    meta["prompt"] = (base / "prompt.md").read_text(encoding="utf-8")
    meta["dir"] = str(base)
    return meta


def materialize(task_id: str, dest: str) -> str:
    """Copy the agent-visible repo to dest. Acceptance tests, the reference and the wrong patch are never copied."""
    if os.path.exists(dest) and os.listdir(dest):
        raise FileExistsError(f"{dest} is not empty")
    shutil.copytree(TASKS_DIR / task_id / "repo", dest, ignore=IGNORE, dirs_exist_ok=True)
    return dest


def apply_overlay(task_id: str, workdir: str, kind: str) -> None:
    """Overwrite files in workdir with the task's 'reference' or 'wrong' files (used only by the self-check)."""
    if kind not in ("reference", "wrong"):
        raise ValueError(kind)
    src = TASKS_DIR / task_id / kind
    for path in src.rglob("*"):
        if path.is_file():
            target = Path(workdir) / path.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)


def _sha(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def protected_violations(task_id: str, workdir: str) -> list[str]:
    """Protected files must be byte-identical to the original repo (a missing file counts as a violation)."""
    task = load_task(task_id)
    original = TASKS_DIR / task_id / "repo"
    return [rel for rel in task["protected"] if _sha(original / rel) != _sha(Path(workdir) / rel)]


def evaluate(task_id: str, workdir: str, timeout_s: int = 120) -> dict:
    """Run the hidden acceptance tests against a copy of workdir. Pure judgment: no model, no CLI output involved."""
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copytree(workdir, tmp, ignore=IGNORE, dirs_exist_ok=True)
        acc = Path(tmp) / "_acceptance"
        shutil.rmtree(acc, ignore_errors=True)  # an agent-shipped folder of that name must not matter
        acc.mkdir()
        shutil.copyfile(TASKS_DIR / task_id / "acceptance" / "test_accept.py", acc / "test_accept.py")
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        env.pop("PYTHONPATH", None)
        # -I ignores cwd and PYTHONPATH; the agent's tree is appended after the standard library so it cannot shadow
        # unittest or any stdlib module the verdict depends on.
        code = ("import sys; sys.path.append(sys.argv[1]); import unittest; "
                "unittest.main(module=None, argv=['x', 'discover', '-s', '_acceptance', '-p', 'test_accept.py', '-v'])")
        try:
            p = subprocess.run([sys.executable, "-I", "-c", code, tmp],
                               cwd=tmp, env=env, capture_output=True, text=True, timeout=timeout_s)
            out, rc, timed_out = p.stdout + p.stderr, p.returncode, False
        except subprocess.TimeoutExpired:
            out, rc, timed_out = "", 1, True
    tests = {}
    for line in out.splitlines():
        m = LINE_RE.match(line)
        if m:
            tests[m.group(1)] = "ok" if m.group(2).strip() == "ok" else "fail"
    violated = protected_violations(task_id, workdir)
    passed = rc == 0 and bool(tests) and all(v == "ok" for v in tests.values()) and not timed_out
    return {"task": task_id, "acceptance_passed": passed, "protected_violations": violated,
            "resolved": passed and not violated, "tests": tests, "timed_out": timed_out}


def selfcheck(task_id: str) -> dict:
    """The task must be unsolved at the start, solved by the reference, and not solved by the plausible wrong patch."""
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        start = os.path.join(tmp, "start")
        materialize(task_id, start)
        r0 = evaluate(task_id, start)
        if r0["resolved"]:
            problems.append("starting repo already satisfies the acceptance tests")
        ref = os.path.join(tmp, "ref")
        shutil.copytree(start, ref)
        apply_overlay(task_id, ref, "reference")
        r1 = evaluate(task_id, ref)
        if not r1["resolved"]:
            problems.append(f"reference does not resolve the task: {r1['tests']} {r1['protected_violations']}")
        bad = os.path.join(tmp, "bad")
        shutil.copytree(start, bad)
        apply_overlay(task_id, bad, "wrong")
        r2 = evaluate(task_id, bad)
        if r2["resolved"]:
            problems.append("the plausible wrong patch passes")
        # the acceptance tests must be able to tell the reference from the start on at least one test
        flipped = [t for t, v in r1["tests"].items() if r0["tests"].get(t) != v]
        if not flipped:
            problems.append("no acceptance test changes between start and reference")
    return {"task": task_id, "ok": not problems, "problems": problems,
            "start_failing": sorted(t for t, v in r0["tests"].items() if v != "ok"),
            "wrong_failing": sorted(t for t, v in r2["tests"].items() if v != "ok") or r2["protected_violations"]}


if __name__ == "__main__":
    bad = 0
    for tid in list_tasks():
        res = selfcheck(tid)
        print(("OK   " if res["ok"] else "FAIL ") + tid, res["problems"] or "")
        bad += 0 if res["ok"] else 1
    sys.exit(1 if bad else 0)
