# 06. Open questions and next steps

## Decisions needed from the user

1. **DaVinci's command line.** The benchmark can run Claude Code today. It cannot run DaVinci until there is an argv
   that takes a prompt, works in a given directory, and honors a budget cap and a wall timeout. Send that, or confirm
   the controller should first be wired into a harness of its own.
2. **Live-run approval.** Nothing has called a model. A pilot (Claude Code only, 2 trials per task) is 12 runs, worst
   case 18 USD, and shows real cost and time. The full design is 168 runs, worst case 252 USD. Approval string for the
   pilot: `12x1.50`. Say which, and which model id to use for both systems.

## Ranked next experiments (no live model unless stated)

| # | Experiment | Settles | Cost |
|---|---|---|---|
| 1 | Pilot run of the benchmark on Claude Code (live) | Real cost, time, harness fit, claim-detector error rate | up to 18 USD, needs approval |
| 2 | Scripted coordinator-mode run (`CLAUDE_CODE_COORDINATOR_MODE=1`) | Whether the verification-worker workflow exists at runtime | none |
| 3 | PTY session with scripted model: interactive plan approval, "keep context" options | Approval transition (`chunk-z3vv06zx.js@7602` onward) | none |
| 4 | Plan mode with the auto classifier scripted (E41 setup) | Plan-mode shell rule independent of the classifier | none |
| 5 | Model-id sweep of E50m (more ids, plus an unknown id) | Boundary of the lean layout | none |
| 6 | Twelve-turn scripted run without task-tool calls | Todo reminder delivery | none |
| 7 | Read `xFn`, `n1`, `ZH`, `Ugs`, `UH`, and the host method behind `V4` | Which text blocks appear under which conditions | none |
| 8 | Host adapter for the controller: parse test output (unittest, pytest, jest), map commands to criteria, claim detector | The three inputs the controller trusts | none |
| 9 | Baseline-twice rule for flaky tests | A known weakness (file 04, section 7, item 3) | none |

## What would change the design

- If the live pilot shows Claude Code with a modern model already runs tests and reports failures honestly almost
  every time, the controller's value is in the rare failures and in cross-compaction state, not in the common case.
  The false-completion rate will say which.
- If Claude Code's false-completion rate is high, the Stop-hook gate (E50v) is the cheapest first step: it needs no
  agent change and can be tried on Claude Code itself as a third benchmark arm.

## Third arm worth adding

`claude_code + stop-hook gate`: Claude Code with the project hook from E50v. It separates the effect of "a completion
gate" from the effect of the rest of the controller (freshness, baseline split, approach ledger, resume block).
