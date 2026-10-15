# 03. Model of the coding-success workflow

Two parts that must not be mixed. Part A is **observed Claude Code 2.1.296** behavior with its evidence class. Part B
is **proposed for DaVinci**: new mechanisms, not claims about Claude Code.

Confidence scale: **High** = seen at runtime or read in full source; **Medium** = read in source, not run; **Low** =
inferred or only partly read.

## Part A. Observed in Claude Code

Stages: Understand, Explore, Plan, Implement, Verify, Recover, Review, Complete.

| Stage | Controlling mechanism | Trigger | Tools available | State transitions | Failure path | Evidence it demands | Confidence |
|---|---|---|---|---|---|---|---|
| **Understand** | Model reads the prompt. Lean body adds "act when you have enough information" (`TBo`). Proactivity `ask` adds "confirm before changing anything, lay out a plan". | Every turn | All session tools | None. There is no state machine; the agent loop just continues while the model emits tool calls. | A wrong reading is not detected. | None | High (text), High (no state) |
| **Explore** | Model choice; optional Explore subagent (needs `tH()`, which is the negation of `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS`, `chunk-phacttch.js@143288`), read-only by tool list. Plan mode phase 1 tells the model to launch Explore agents. | Model decides; plan mode instructs | Explore child: 13 tools incl. Bash. Parent: all. | None | Child result returns as a tool result; no check that the exploration was sufficient. | None | High (E50r, E50u) |
| **Plan** | Plan mode (user or `--permission-mode plan`): reminder attachment in every request plus a hard Write refusal. Five phases in the reminder text. Approval is a permission "ask" on ExitPlanMode. | User enters plan mode, or the model calls the enter-plan tool (needs `askUserQuestion`/enter tools present) | Read-only tools plus the plan file; ExitPlanMode only if enabled | `plan` to prior mode on approval, in `call()` | User rejection returns a message asking the model to revise; headless cannot exit | The plan file's contents (shown to the user) | High (E50q, static) / Medium (approval path) |
| **Implement** | Model edits with Edit/Write/Bash under the permission mode. Todo reminder after 10 idle turns when a task tool exists. | Model | All | None | An edit that breaks the build is not detected until something runs | None | High |
| **Verify** | **Nothing mandatory.** `proactive` level text says run tests and fix failures. A Stop hook can force it if the user wrote one. Full-layout models get a UI-check sentence. | Model choice, or a configured hook | Bash | None | A failing test is a tool result; the model may ignore it (E50t) | None. The CLI never checks that a test ran | High (E50s, E50t, E50v) |
| **Recover** | Model reading tool errors. Autonomous addendum (when its predicates hold) says retry after errors and do not stop at a plan; coordinator worker text says do not retry the same failed approach more than once. Stop-hook block cap bounds a block loop (8). | Tool error or hook block | All | None | Same failure repeated is not detected. The 8-block cap ends only hook loops. | None | Medium (text), High (cap, E40) |
| **Review** | `/security-review` command (sub-task per finding, false-positive filter, confidence threshold). Coordinator mode: fresh verifier worker (prompt text). No default reviewer agent. | User command, or coordinator mode (env opt-in) | Command: read tools; workers: all | None | Findings are text | Diff and prompt | Medium (not run) |
| **Complete** | The model's last message with no tool call ends the turn; Stop hooks run first. The result event carries `subtype`, `is_error`, `terminal_reason`, `permission_denials`. | No tool call in the last assistant message | n/a | Loop ends | A completion claim is never compared with evidence (E50s, E50t) | None | High |

### What the observed system optimizes

It optimizes **latitude for the model**, with a small set of hard gates where an error is expensive and easy to
detect: edits in plan mode, which tools a subagent has, which permission mode applies, and an optional completion gate.
Success on a coding task therefore rests on the model's own habits. That is why the benchmark in file 05 measures
outcomes against hidden tests and counts false completions.

## Part B. Proposed for DaVinci (new mechanisms)

Each row names the gap it closes in Part A and the controller function in `controller/davinci_controller.py`.

| Stage | Mechanism | Trigger | Tools | Transitions | Failure path | Evidence demanded | Closes |
|---|---|---|---|---|---|---|---|
| Understand | Acceptance criteria are written before planning. Each has a kind: `executable`, `static` or `review`. | Task start | read-only | UNDERSTAND to EXPLORE | No criteria: cannot reach IMPLEMENT | The criteria list | No state, no stated goal (`set_criteria`) |
| Explore | Record the baseline: which tests fail before any change. | Before first edit | read-only plus test runner | EXPLORE to PLAN or back | Baseline never recorded: every later failure counts as new | Baseline failing-test ids and tree digest | Cannot tell new failures from old (`record_baseline`, `classify_failures`) |
| Plan | Optional plan approval gate. | `plan_approval_required` | read-only | PLAN to IMPLEMENT only when approved | Rejected plan returns to EXPLORE | Approval flag | Plan mode is user-driven only (`move`) |
| Implement | Each edit updates a tree digest. An approach is registered with strategy and files. | Every edit | edit tools | IMPLEMENT to VERIFY | Edits outside IMPLEMENT/RECOVER are illegal | Tree digest | Evidence cannot go stale unnoticed (`record_edit`, `begin_approach`) |
| Verify | Runs are recorded with command, failing ids, tree digest and the criteria they cover. Evidence is **fresh** only at the current digest. Pre-existing failures do not block; new ones do. Non-executable changes use `static` criteria and need no test. | After edits | test runner, inspection | VERIFY to REVIEW, RECOVER or REPORT | New failure: RECOVER | Fresh passing evidence per criterion | The central gap: finishing without or after failed verification (`record_verification`, `report`) |
| Recover | A diagnosis of at least 20 characters, different from the last one, is required before a new approach. A failed approach cannot be repeated. After 2 identical failures or 4 attempts the controller refuses more retries. | Failed verification | edit tools | RECOVER to IMPLEMENT, PLAN or REPORT | Budget spent: FAILED outcome | Diagnosis text, approach ledger | Blind repetition (`begin_approach`) |
| Review | Independent review only when a measurable reason exists (large diff, many files, sensitive path, recovery needed, public API). The reviewer gets criteria, fresh evidence and the diff, never the implementer's reasoning. | `should_review` non-empty | read-only | VERIFY to REVIEW to REPORT | Blocking finding: RECOVER | Review record at the current digest | Review is absent by default; avoid review cost where it adds nothing (`should_review`, `review_packet`) |
| Complete | The final message may say "verified", "tests pass" or "done" only if the report outcome is VERIFIED. Outcomes: VERIFIED, UNVERIFIED, BLOCKED, FAILED. | Before the final message | none | REPORT to DONE | A claim the evidence does not support is refused | The report | Completion claims unchecked (`may_claim`) |
| Cross-cutting | Commit, push and destructive commands need an explicit user authorization recorded in state; `sudo` is never run. State is serialized and a resume block is re-injected after compaction. | Every tool call; after compaction | all | none | Unauthorized action: needs_authorization or deny | Authorization list | Silent side effects; state lost at compaction (`evaluate_action`, `to_json`, `resume_block`) |

## Differences that matter

1. Claude Code gives the model freedom and trusts it. DaVinci's controller gives the model the same freedom to explore
   and edit, and withholds one thing: the right to **report success without fresh evidence**.
2. A failing test is information to Claude Code and a **state** to the controller (FAILED or RECOVER, with a ledger).
3. Claude Code has no memory of failed approaches beyond the transcript, which compaction can erase. The controller
   keeps them in structured state and puts them in the resume block.
4. Review is a command in Claude Code and a **conditional step** here, so its cost is paid only where a reason exists.

## What stays a model decision in DaVinci

Which files to read, what the fix is, how to write the diagnosis, how to write the criteria, and whether a change is
public API. The controller checks form and consistency, not correctness of reasoning. See file 04, section 6, for the
places it would break.
