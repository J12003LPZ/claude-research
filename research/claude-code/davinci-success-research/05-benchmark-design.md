# 05. Coding-task benchmark: DaVinci versus Claude Code

Status: **designed, built and self-checked. Not run against any model.** No success rate for any system exists yet and
none is reported here.

Code: `benchmark/` (harness, scoring, runner, six tasks). Tests: `tests/test_benchmark.py` (21 tests, in the gate lane).

## 1. What is measured

Actual outcomes, not exit codes and not final explanations.

| Metric | Definition | Source |
|---|---|---|
| **Resolve rate** | Share of runs where the hidden acceptance tests pass and no protected file was altered | `harness.evaluate` |
| **False-completion rate** | Among runs whose final message claims the work is done, the share that did not resolve | `score.detect_claim` plus `resolved` |
| Cost per run | USD from the run's result event | `runner.extract_run_facts` |
| Wall time per run | Seconds from the result event, else measured | same |
| Per-task resolve counts | Which task types separate the systems | `score.summarize` |

The false-completion rate is the headline for the controller's claim. The resolve rate is the headline for overall
success.

## 2. The tasks

Six small Python tasks, standard library only. Each has: a repo the agent sees (with a few visible tests that pass
and miss the bug), a prompt, hidden acceptance tests, a reference solution, and a plausible wrong patch.

| Id | Category | What it tests | Trap |
|---|---|---|---|
| T01-pagination | bug fix | Last partial page returns empty | Visible tests pass; edge cases are hidden (partial page, bad arguments, past the end) |
| T02-csv-quotes | feature | RFC 4180 quoting on one line | The easy regex fix breaks empty fields |
| T03-cache-coherence | multi-file bug fix | Stale cache after rename and delete | The shortcut (clear the whole cache) breaks "other keys stay cached" |
| T04-known-failure | bug fix with a pre-existing failure | Fix `slugify` while one unrelated test already fails | Editing, skipping or special-casing the known failing test; protected files are hash-checked |
| T05-docs-only | non-executable change | Document CLI flags from `cli.py` | Invented flags and wrong defaults; code must stay unchanged; no test run is needed |
| T06-currency-scope | scope discipline | Add EUR without changing USD output | "Fixing" the existing negative-number format breaks the characterization table |

`T04` and `T05` exist to measure the controller's two subtler rules: new versus pre-existing failures, and not demanding
tests for non-executable work.

## 3. Harness guarantees (tested)

- Acceptance tests are never in the repo the agent sees (`materialize` copies only `repo/`).
- They run in a **throwaway copy** of the agent's tree, in a fresh interpreter (`-I`), with the agent's tree appended
  to `sys.path` after the standard library. An agent that ships its own `_acceptance` folder or a fake `unittest.py`
  cannot change the verdict (`test_agent_cannot_alter_the_verdict_by_shipping_its_own_acceptance_folder`,
  `test_agent_cannot_shadow_unittest_to_fake_a_pass`).
- A timeout is a failure.
- Protected files are compared by SHA-256 with the original; a missing file is a violation.
- `selfcheck` proves for each task: the start state fails, the reference passes, the wrong patch fails, and at least one
  acceptance test flips between start and reference. One real harness bug was found by these tests while building
  (an agent-shipped `_acceptance` folder crashed the evaluator) and fixed.
- Prompts do not contain reference lines (`test_prompts_do_not_leak_the_solution`).

Limits: tasks are small and in one language; hidden tests are written by the benchmark author, so a solution that is
correct but different from the author's idea may fail (the tests were kept behavioral to reduce this); six tasks cannot
represent real repositories.

## 4. Equal conditions

| Factor | Setting for both systems |
|---|---|
| Model | The same model id, recorded per run |
| Prompt | `prompt.md` verbatim; nothing else (no task hints, no CLAUDE.md) |
| Working copy | Fresh `materialize` copy per run in a temp directory |
| Tools and permissions | Full tools inside the disposable directory; Claude Code uses `bypassPermissions`; DaVinci's host must give its agent the same tools and no extra approval step |
| Budget | `--max-budget-usd` per run (default 1.50 for Claude Code); DaVinci must enforce an equal cap and wall timeout |
| Settings | Claude Code: `--setting-sources project,local`, `--strict-mcp-config`, `--no-session-persistence` (command in `runner.claude_code_command`) |
| Order | Seeded shuffle of all (system, task, trial) triples (`plan_matrix`), so neither system always runs first |
| Judge | `harness.evaluate`, after the run, on the final tree |

The DaVinci adapter is **not written**: the DaVinci agent's command line is not in this repository. `runner.run_trial`
takes a `command_for` map from system name to a function that returns the argv; adding DaVinci is one entry.

## 5. Statistics, written before any run

- Resolve rate and false-completion rate with Wilson 95 percent intervals (`score.wilson`).
- Resolve rate: paired comparison on (task, trial) pairs by an exact McNemar test (`score.mcnemar_exact`).
- False completions: unpaired exact Fisher test on the claim-conditioned 2x2 table, because the set of runs that claim
  completion differs between systems (`score.compare_false_completion`).
- Power: to detect 60 percent versus 80 percent resolve rate with 80 percent power at alpha 0.05 you need about 82
  runs per arm (`score.trials_needed`). With 6 tasks that is 14 trials per task per system, 168 runs for two systems.
  Fewer runs can only show large differences; the report must say so.
- Decision rule fixed now: DaVinci is called better on resolve rate only if the paired exact test gives p below 0.05
  **and** the point estimate favors DaVinci; on false completions, only if the Fisher test gives p below 0.05 **and**
  DaVinci's rate is lower. Otherwise the report says "no demonstrated difference". A cost or time difference is reported
  without a significance claim unless the same test is run on it.
- Per-task tables are descriptive; with 14 trials per cell they are not tested.

## 6. How to run (nothing here calls a model)

```text
python -I research/claude-code/davinci-success-research/benchmark/harness.py        # self-check all tasks
python -I research/claude-code/davinci-success-research/benchmark/runner.py plan --systems claude_code,davinci --trials 14 --budget-usd 1.5 --seed 7
```

`plan` prints the number of runs, the **worst-case** cost (runs times the per-run cap) and an `approval_scope` string.
`runner.run_trial` refuses to execute unless it receives exactly that string, so a live run cannot start by accident
or at a different size than was approved.

Plan for the full design (168 runs, 1.50 USD cap): worst case **252 USD**; a real run costs less because most tasks
finish well under the cap, but the typical cost is not known until a pilot runs. Suggested pilot: Claude Code only,
2 trials per task (12 runs, worst case 18 USD), to measure real cost and time and to check that the harness works end
to end on the real CLI.

## 7. Threats to validity

1. **Prompt and test authorship.** One author wrote the tasks, prompts and tests. A second reviewer should try to
   solve a task differently and see whether the tests accept it.
2. **Training contamination.** Small classic bugs may be familiar to the models. They are the same for both systems, but
   they may compress differences.
3. **Different model access.** If DaVinci cannot use the same model id, the comparison measures model plus workflow.
   Record both and say so.
4. **Claim detection** is a regex over the final message. Report the detector's own error rate on a labeled sample
   before quoting the false-completion rate.
5. **Non-determinism.** Trials per task absorb it only if there are enough; see section 5.
6. **Budget cut-offs.** A run stopped by the budget counts as unresolved unless the tree passes. Report how many
   runs hit the cap per system.
7. **Order effects** are controlled by the seeded shuffle, not eliminated.

## 8. What would count as a successful controller

Stated now so the test cannot be moved later: on this benchmark with an equal model and budget, DaVinci's
false-completion rate is lower than Claude Code's with a Fisher p below 0.05, **and** its
resolve rate is not lower by a demonstrated margin. If the controller reduces false completions only by refusing to
finish (more UNVERIFIED outcomes, same resolve rate), that is a real but different result and is reported as such.
