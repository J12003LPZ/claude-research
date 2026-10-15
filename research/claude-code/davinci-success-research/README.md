# DaVinci success research

Question: how does Claude Code 2.1.296 turn a model into something that finishes coding tasks, what is enforced by
code versus suggested by text, and what should DaVinci build to finish more tasks and claim completion less often
when it has not.

Branch `worktree-continue-daemon`. Starts from commit `92faf0a` (coding-workflow layer in
`../static-02-prompt-context-compaction.md`).

## Read in this order

| File | Content | Status |
|---|---|---|
| `01-runtime-verified-mechanisms.md` | 21 scripted runs (E50): which instruction text reaches requests per model, proactivity levels, plan mode, Explore, finishing without or after a failed test, a Stop-hook gate | Runtime evidence, no model called |
| `02-static-findings-and-unknowns.md` | What is code, what is text, what is left to the model; ranked unknowns | Static plus runtime |
| `03-coding-success-mechanism-model.md` | Eight stages: Part A observed, Part B proposed | Observed versus proposed, kept apart |
| `04-davinci-workflow-controller.md` | Requirements, state machine, interfaces, loop integration, 30 tests, failure analysis | Design plus reference implementation |
| `05-benchmark-design.md` | Six tasks, hidden acceptance tests, equal-conditions protocol, statistics fixed in advance | Built and self-checked, **not run** |
| `06-open-questions-and-next-steps.md` | Decisions needed, ranked experiments, cost | |
| `controller/davinci_controller.py` | Reference controller | Tested |
| `benchmark/` | Harness, scoring, runner, tasks | Tested |
| `tests/` | 51 tests, in the gate lane | Pass |

The request that started this directory was cut off at deliverable 3 ("Include: 1. Runtime-verified ... 2. Remaining
static-only findings and unknowns. 3."). Files 03 to 06 follow phases 3 to 5 of that request. Say if a deliverable
was meant to be different.

## Headline findings

1. **Claude Code has no default mechanism that makes a model test, retest or review.** A scripted model that skipped
   tests, and one that ran a failing test then said "Done.", both ended `success`, exit 0 (E50s, E50t).
2. **The instruction text depends on the model.** The 5-series models get a short lean body; "Doing tasks",
   "Executing actions" and "Using your tools" reach only `claude-sonnet-4-5` and `claude-opus-4-7` (E50m, E50o). This
   corrects the headline of the previous pass.
3. **The proactivity level also sets the permission mode** (E50w). `proactive` is the only level whose text mentions
   tests.
4. **Hard gates that exist:** plan-mode edit refusal, Explore and Plan tool lists (the shell stays open, E50u), the
   permission mode, and a user-configured `Stop` hook. The Stop hook is a working verification gate (E50v).
5. **Plan mode in `-p` cannot be left**: ExitPlanMode is disabled there (E50q).
6. **Success rate comparison: not available.** The benchmark is built and self-checked. No model has been run.

## Reproduce

```text
python -I research/claude-code/tools/scenarios/run_all_e50.py                           # scripted runs, about 1 minute, no model
python -I -m unittest discover -s research/claude-code/davinci-success-research/tests   # 51 tests
python -I research/claude-code/davinci-success-research/benchmark/harness.py            # task self-check
python -I research/claude-code/davinci-success-research/benchmark/runner.py plan --trials 14   # run count and worst-case cost
```

The scripted runs write raw captures to `lab/raw/` (private, not committed) and sanitized evidence to
`../runtime-logs/E50*/`. `tools/summarize_captures.py` now resolves its output folder from its own location (it used to
write to the shared checkout); `CLAUDE_REA_RUNTIME_LOGS` overrides it.

## Rules kept

Local artifacts only; the installed CLI and its binary were not modified; no authentication was bypassed; no
credential, token or private conversation was read or written into a report; test projects are disposable and
synthetic; no live model call was made; nothing was committed to a remote (the repository has none).
