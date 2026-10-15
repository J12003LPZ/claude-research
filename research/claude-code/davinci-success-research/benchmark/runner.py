"""Plan and (only with explicit approval) run benchmark trials against Claude Code or another agent command.

Nothing here calls a model unless run_trial is invoked with an approval token that matches the scope the user approved.
The default entry point only prints the plan and the worst-case cost.

usage:
  python -I runner.py plan --systems claude_code,davinci --trials 5 --budget-usd 1.5 --seed 7
"""
from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness  # noqa: E402
import score  # noqa: E402


class NotApproved(Exception):
    pass


def claude_code_command(prompt: str, model: str, budget_usd: float, claude_bin: str = "claude") -> list[str]:
    """Headless run with the same permission posture inside the disposable workdir for every system."""
    return [claude_bin, "-p", prompt, "--model", model, "--output-format", "stream-json", "--verbose",
            "--permission-mode", "bypassPermissions", "--max-budget-usd", f"{budget_usd:.2f}",
            "--no-session-persistence", "--setting-sources", "project,local", "--strict-mcp-config"]


def extract_run_facts(stdout_text: str) -> dict:
    """Facts from a stream-json transcript. The final text is only used to detect a completion claim."""
    final, cost, wall, turns = "", None, None, None
    for line in stdout_text.splitlines():
        try:
            o = json.loads(line)
        except ValueError:
            continue
        if o.get("type") == "result":
            final = o.get("result") or ""
            cost = o.get("total_cost_usd", o.get("cost_usd"))
            wall = (o.get("duration_ms") or 0) / 1000 or None
            turns = o.get("num_turns")
    return {"claimed_done": score.detect_claim(final), "cost_usd": cost, "wall_s": wall, "turns": turns}


def plan_matrix(systems: list[str], tasks: list[str], trials: int, seed: int) -> list[dict]:
    """Every (system, task, trial) once, in a seeded shuffled order so no system always runs first or last."""
    runs = [{"system": s, "task": t, "trial": k} for s in systems for t in tasks for k in range(trials)]
    random.Random(seed).shuffle(runs)
    return runs


def worst_case_cost(runs: list[dict], budget_usd: float) -> float:
    return round(len(runs) * budget_usd, 2)


def approval_scope(runs: list[dict], budget_usd: float) -> str:
    return f"{len(runs)}x{budget_usd:.2f}"


def run_trial(run: dict, command_for: dict, model: str, budget_usd: float, approval: str | None, all_runs: list[dict],
              timeout_s: int = 1800) -> dict:
    """Execute one trial in a fresh disposable copy and judge it with the hidden acceptance tests."""
    if approval != approval_scope(all_runs, budget_usd):
        raise NotApproved(f"live runs need approval for exactly this scope: {approval_scope(all_runs, budget_usd)}")
    task = harness.load_task(run["task"])
    with tempfile.TemporaryDirectory() as tmp:
        work = os.path.join(tmp, "work")
        harness.materialize(run["task"], work)
        argv = command_for[run["system"]](task["prompt"], model, budget_usd)
        t0 = time.time()
        try:
            p = subprocess.run(argv, cwd=work, capture_output=True, text=True, timeout=timeout_s)
            stdout = p.stdout
        except subprocess.TimeoutExpired as e:
            stdout = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        facts = extract_run_facts(stdout)
        verdict = harness.evaluate(run["task"], work)
        facts["wall_s"] = facts["wall_s"] or round(time.time() - t0, 1)
        return {**run, "resolved": verdict["resolved"], "protected_violations": verdict["protected_violations"],
                "claimed_done": facts["claimed_done"], "cost_usd": facts["cost_usd"], "wall_s": facts["wall_s"]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    pl = sub.add_parser("plan")
    pl.add_argument("--systems", default="claude_code,davinci")
    pl.add_argument("--trials", type=int, default=5)
    pl.add_argument("--budget-usd", type=float, default=1.5)
    pl.add_argument("--seed", type=int, default=7)
    a = ap.parse_args(argv)
    runs = plan_matrix(a.systems.split(","), harness.list_tasks(), a.trials, a.seed)
    print(json.dumps({"runs": len(runs), "worst_case_cost_usd": worst_case_cost(runs, a.budget_usd),
                      "approval_scope": approval_scope(runs, a.budget_usd), "first_five": runs[:5]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
