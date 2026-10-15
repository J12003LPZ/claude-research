"""Run the whole E50 coding-workflow series against the scripted proxy and write the sanitized evidence.
usage: run_all_e50.py            (no upstream model call; about 1 to 2 seconds per run)
For each run: run_e50.sh, then coding_workflow_probe.py and summarize_captures.py.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
TOOLS = os.path.join(ROOT, "research", "claude-code", "tools")

# (experiment id, mode, model, proactivity, permission mode)
RUNS = [("E50a-baseline-default", "baseline", "haiku", "default", "bypassPermissions")]
for tag, models in (("m", ["sonnet", "opus", "claude-opus-5-5", "claude-fable-5-1"]),
                    ("o", ["claude-opus-4-1", "claude-sonnet-4-5", "claude-opus-4-7", "claude-mythos-5"])):
    for m in models:
        RUNS.append((f"E50{tag}-{m}-default", "baseline", m, "default", "bypassPermissions"))
for level in ("ask", "default", "proactive"):
    RUNS.append((f"E50p-haiku-{level}", "baseline", "haiku", level, "bypassPermissions"))
for level in ("ask", "default", "proactive"):
    RUNS.append((f"E50w-mode-{level}", "baseline", "haiku", level, "none"))
RUNS += [
    ("E50q-plan", "plan", "haiku", "default", "plan"),
    ("E50r-explore", "explore", "haiku", "default", "bypassPermissions"),
    ("E50u-explore-bash", "explorebash", "haiku", "default", "bypassPermissions"),
    ("E50s-notest", "notest", "haiku", "default", "bypassPermissions"),
    ("E50t-failtest", "failtest", "haiku", "default", "bypassPermissions"),
    ("E50v-stopgate", "stopgate", "haiku", "default", "bypassPermissions"),
]

only = sys.argv[1] if len(sys.argv) > 1 else ""
for exp, mode, model, level, perm in RUNS:
    if not exp.startswith(only):
        continue
    env = dict(os.environ, MODEL=model)
    r = subprocess.run(["bash", os.path.join(HERE, "run_e50.sh"), exp, mode, level, perm],
                       cwd=ROOT, env=env, capture_output=True, text=True, timeout=300)
    for cmd in (["coding_workflow_probe.py", exp], ["summarize_captures.py", exp]):
        subprocess.run([sys.executable, "-I", os.path.join(TOOLS, cmd[0]), cmd[1]], cwd=ROOT,
                       capture_output=True, text=True, timeout=120)
    print(exp, "->", (r.stdout.strip().splitlines() or ["(no output)"])[-1][:150])
