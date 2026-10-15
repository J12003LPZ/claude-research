"""Scoring for the coding-task benchmark. Pure functions over run records; no model and no I/O.

A record is {"task", "system", "trial", "resolved", "claimed_done", "cost_usd", "wall_s"}.
`resolved` comes only from harness.evaluate (hidden acceptance tests), never from a CLI exit code or the final message.
"""
from __future__ import annotations

import math
import re
import statistics
from collections import defaultdict


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for k successes in n trials."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def mcnemar_exact(only_a: int, only_b: int) -> float:
    """Two-sided exact p-value for paired outcomes where only_a / only_b count the discordant pairs."""
    n = only_a + only_b
    if n == 0:
        return 1.0
    k = min(only_a, only_b)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def fisher_exact(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact p-value for the 2x2 table [[a, b], [c, d]] (sum of tables no more likely than observed)."""
    r1, r2, c1, n = a + b, c + d, a + c, a + b + c + d
    if n == 0:
        return 1.0

    def prob(x):
        return math.comb(r1, x) * math.comb(r2, c1 - x) / math.comb(n, c1)

    observed = prob(a)
    lo, hi = max(0, c1 - r2), min(r1, c1)
    return min(1.0, sum(prob(x) for x in range(lo, hi + 1) if prob(x) <= observed * (1 + 1e-9)))


def compare_false_completion(records: list[dict], system_a: str, system_b: str) -> dict:
    """Unpaired test on completion claims: among runs that claimed done, did one system fail the acceptance tests more often."""
    def counts(system):
        claims = [r for r in records if r["system"] == system and r["claimed_done"]]
        bad = sum(1 for r in claims if not r["resolved"])
        return bad, len(claims) - bad
    (a_bad, a_ok), (b_bad, b_ok) = counts(system_a), counts(system_b)
    return {f"{system_a}_false": a_bad, f"{system_a}_true": a_ok, f"{system_b}_false": b_bad, f"{system_b}_true": b_ok,
            "fisher_exact_p": fisher_exact(a_bad, a_ok, b_bad, b_ok)}


NEG = re.compile(r"\b(not|n't|cannot|can't|unable|couldn't|did not|didn't|failed|still fail\w*)\b", re.I)
POS = re.compile(r"\b(done|fixed|resolved|complete[d]?|implemented|all tests pass\w*|tests pass\w*|works now)\b", re.I)


def detect_claim(final_text: str) -> bool:
    """True when the final message claims the work is done. A negation in the same sentence cancels a claim."""
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", final_text or ""):
        if POS.search(sentence) and not NEG.search(sentence):
            return True
    return False


def summarize(records: list[dict]) -> dict:
    by_system: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_system[r["system"]].append(r)
    out = {}
    for system, rows in sorted(by_system.items()):
        n = len(rows)
        k = sum(1 for r in rows if r["resolved"])
        claims = [r for r in rows if r["claimed_done"]]
        false_claims = [r for r in claims if not r["resolved"]]
        costs = [r["cost_usd"] for r in rows if r.get("cost_usd") is not None]
        walls = [r["wall_s"] for r in rows if r.get("wall_s") is not None]
        lo, hi = wilson(k, n)
        flo, fhi = wilson(len(false_claims), len(claims))
        per_task = defaultdict(lambda: [0, 0])
        for r in rows:
            per_task[r["task"]][1] += 1
            per_task[r["task"]][0] += 1 if r["resolved"] else 0
        out[system] = {
            "runs": n, "resolved": k, "resolve_rate": k / n if n else 0.0, "resolve_ci95": [round(lo, 4), round(hi, 4)],
            "claimed_done": len(claims), "false_completions": len(false_claims),
            "false_completion_rate": len(false_claims) / len(claims) if claims else 0.0,
            "false_completion_ci95": [round(flo, 4), round(fhi, 4)],
            "median_cost_usd": statistics.median(costs) if costs else None,
            "median_wall_s": statistics.median(walls) if walls else None,
            "per_task": {t: {"resolved": v[0], "runs": v[1]} for t, v in sorted(per_task.items())},
        }
    return out


def compare(records: list[dict], system_a: str, system_b: str) -> dict:
    """Paired comparison on (task, trial) pairs both systems completed."""
    a = {(r["task"], r["trial"]): r["resolved"] for r in records if r["system"] == system_a}
    b = {(r["task"], r["trial"]): r["resolved"] for r in records if r["system"] == system_b}
    keys = sorted(set(a) & set(b))
    only_a = sum(1 for k in keys if a[k] and not b[k])
    only_b = sum(1 for k in keys if b[k] and not a[k])
    both = sum(1 for k in keys if a[k] and b[k])
    neither = sum(1 for k in keys if not a[k] and not b[k])
    return {"pairs": len(keys), "both": both, "neither": neither, f"only_{system_a}": only_a, f"only_{system_b}": only_b,
            "mcnemar_exact_p": mcnemar_exact(only_a, only_b)}


def trials_needed(p_a: float, p_b: float, power: float = 0.8, alpha: float = 0.05) -> int:
    """Rough number of paired runs for a two-proportion difference (normal approximation, independent samples)."""
    z = {0.05: 1.959964}[alpha]
    zb = {0.8: 0.841621, 0.9: 1.281552}[power]
    pbar = (p_a + p_b) / 2
    num = (z * math.sqrt(2 * pbar * (1 - pbar)) + zb * math.sqrt(p_a * (1 - p_a) + p_b * (1 - p_b))) ** 2
    return math.ceil(num / (p_a - p_b) ** 2)
