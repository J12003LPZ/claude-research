# 01. Runtime-verified coding-workflow mechanisms

Target: Claude Code 2.1.296 (`C:\Users\...\versions\2.1.296`, SHA-256 `76de74f7...06769a`), Windows 11.
Method: the real CLI ran against the local capture proxy in **scripted mode** (`tools/capture_proxy.mjs`,
`tools/scripted_response.mjs`). The proxy answered every `/v1/messages` request with a canned reply, so no model
was called, no account was billed, and no credential left the machine. The CLI built its real requests, ran its real
tools, hooks and permission checks. The project directories are disposable and hold synthetic code.

What this shows: what the **CLI** puts in a request and what it **permits or forces**. What it does not show: what a
real model chooses to do. Every behavior below that depends on model choice is marked as such.

Label used throughout: **VERIFIED-RUNTIME** = seen in a captured request, event stream or file of the named run.
Raw captures stay in the private `lab/raw/<id>/`; the sanitized evidence is `runtime-logs/<id>/` (the
`coding-workflow-probe.json` file in each folder is produced by `tools/coding_workflow_probe.py` and holds booleans,
tool names, sizes and the first 240 characters of tool results, never prompt text).

Reproduce everything: `python -I research/claude-code/tools/scenarios/run_all_e50.py` (about 2 seconds per run).

## 1. Which instruction text reaches a request depends on the model (E50a, E50m, E50o)

One trivial prompt, default proactivity, `-p`, scripted reply. Headings are the `# ` lines seen in the raw captures (private, not committed; the committed probe JSON stores sizes and marker booleans, not headings).

**Size caveat.** "System body" is the `system` blocks of the request only. For the lean layout a separate `system`-role message in `messages` carries the session sections (it starts with `# Environment`): about 9,700 characters for sonnet-5-5, 10,072 for fable-5-1, 11,597 for haiku with proactive. The full layout has no such message. Compare instruction volume with both parts, not the body column alone.

| Requested model | Model sent | System body (chars) | Layout | "Doing tasks" / "Executing actions" / "Using your tools" | Notes |
|---|---|---|---|---|---|
| `haiku` | claude-haiku-5-5 | 8,780 to 8,790 | lean | absent | adds early-stopping guidance (text about finishing a request in one turn) |
| `sonnet` | claude-sonnet-5-5 | 5,996 | lean | absent | |
| `opus` | claude-opus-5-5 | 5,994 | lean | absent | |
| `claude-opus-5-5` | claude-opus-5-5 | 6,005 | lean | absent | |
| `claude-opus-4-1` | claude-opus-5-5 | 6,005 | lean | absent | request was rewritten to 5-5 |
| `claude-fable-5-1` | claude-fable-5-1 | 12,078 | lean + "Delivering work" + "Writing for the user" | absent | |
| `claude-mythos-5` | claude-mythos-5 | 9,720 | lean + "Communicating with the user" | absent | |
| `claude-sonnet-4-5` | claude-sonnet-4-5 | 27,560 | **full** | **present** | headings System, Doing tasks, Executing actions with care, Using your tools, Tone and style, Text output |
| `claude-opus-4-7` | claude-opus-4-7 | 27,558 | **full** | **present** | same headings |

Consequences:

- The coding-workflow text that earlier research reported as "the CLI's system instructions" reached only the two
  older models tested here (`claude-sonnet-4-5`, `claude-opus-4-7`); other older ids were not run (`claude-opus-4-1` was rewritten to 5-5). For the 5-series the lean body is the whole instruction set, and its test-related content is one
  sentence about reporting: *if tests fail, say so with the output; when something is done and verified, state it
  plainly*. It tells the model how to report, not when to run tests.
- STRONGLY INFERRED: the lean body is the same family of text that governs this session's own system prompt (same headings; not compared byte for byte).
- Statically the choice is made by `V4(model)` (`chunk-bykygzr4.js@6140`) and a host table that was not read, so the
  boundary for models not tested here is unknown.

## 2. Proactivity levels (E50p, E50w)

`--proactivity ask|default|proactive` is a hidden option (accepted, not in `--help`).

| Level | Block heading word | Block size (raw captures; the committed evidence has the whole `system`-role message: 9,944 / 9,688 / 11,597 chars) | Delivered as | Mentions of "test" | Initial permission mode with no `--permission-mode` (E50w) |
|---|---|---|---|---|---|
| `ask` | low | 1,009 chars | `system`-role message inside `messages` | 0 | `auto` |
| `default` | medium | 749 chars | same | 0 | `default` |
| `proactive` | high | 2,656 chars | same | 5 (raw captures; the static source shows the "tests" lines are code tests, the rest concern experiments) | `auto` (bypass was not available here) |

- The level is not only prompt text. It also picks the permission mode (`mde`, static-02 section 26). On this machine
  `ask` and `proactive` started in `auto`, but `default` started in `default`, although the static reading of `mde`
  says `default` also maps to auto when available. The two disagree and the reason is UNKNOWN (an availability check
  in the caller that was not traced, or a startup path that bypasses it).
- Only the `proactive` block mentions tests. `default` says to run the checks the task needs and gives no rule about
  failures. This confirms the static reading of the twenty-fifth pass.
- Depends on this machine: auto-mode availability. Another account could see `ask` start in `default`.

## 3. Plan mode (E50q, `--permission-mode plan`)

Scripted sequence: Read a source file; Write the source file; Bash that writes a file; ExitPlanMode; Write again.

| Step | Observed |
|---|---|
| Request content | Every request carried the plan-mode reminder ("Plan mode is active" and the Phase 4 final-plan text). |
| Read | Allowed; returned the file. |
| Write to source | `is_error`, text `Cannot write to <path> while in plan mode.` Listed in the result's `permission_denials`. File unchanged. |
| Bash that writes a file | Denied; the file was not created. **Caveat:** the denial text was `claude-haiku-5-5 is temporarily unavailable, so auto mode cannot determine the safety of Bash right now`. The shell went through the auto-mode classifier, which the lab proxy cannot answer (HTTP 400). This run does not isolate a plan-mode shell rule. |
| ExitPlanMode | Not in the tool list. A call returned `No such tool available: ExitPlanMode. ExitPlanMode is disabled for this session, in subagents as well as here.` |
| Write after the ExitPlanMode attempt | Refused again. The mode never left `plan`. |
| End | `subtype success`, `terminal_reason completed`, exit 0, three denials recorded. |

So in headless mode plan mode refuses the Write tool outright and the model cannot leave it.
The approval transition (the ask dialog, the mode restore) was **not** exercised: it needs an interactive session or a
channel. Static reading only (static-02 section 26, item 3).

Unexplained: with `--model haiku` the plan-mode requests were sent as `claude-sonnet-5-5`. Not traced.

## 4. Explore subagent (E50r, E50u)

Parent: 26 tools. Explore child: 13.

- Removed for the child: Agent, Edit, Write, NotebookEdit, CronCreate, CronDelete, CronList, ScheduleWakeup,
  ListAgents, RemoteTrigger, PushNotification, DesignSync, ReportFindings.
- Kept: Bash, PowerShell, Read, Glob, Grep, Skill, SendMessage, TaskStop, Monitor, WebFetch, WebSearch,
  EnterWorktree, ExitWorktree.
- A scripted child `Write` returned `No such tool available: Write. Write is not among the tools available here.`
- A scripted child `Bash` command writing `src/child_bash.py` returned "(Bash completed with no output)" with no error
  (bypassPermissions). The file's existence was not captured, so STRONGLY INFERRED that the write happened. Explore's
  read-only guarantee is the missing edit tools plus prompt text. The shell is an open path unless the permission mode closes it.
- The Agent tool description in the parent request (1,628 chars) does not name Explore, but `subagent_type: "Explore"`
  was accepted and applied.
- The call launched asynchronously ("Async agent launched successfully"). Exit code 1 in both runs comes from the
  script: the completion notification caused one more parent turn that the scripted sequence did not cover (HTTP 400
  `lab otherwise`). It is not a CLI behavior.

## 5. Finishing without verification (E50s, E50t)

Project: `add(a, b)` returns `a - b`; `run_tests.py` exits 1 until it is fixed.

| Run | Scripted model | CLI outcome |
|---|---|---|
| E50s | Write the fix, then "Fixed add(). Done." (no test run) | `subtype success`, `is_error` false, exit 0, 2 requests, file fixed |
| E50t | Run `python run_tests.py` (exit 1, `FAILED: add(2, 3) != 5`), then "Tests ran. Done." | `subtype success`, `is_error` false, exit 0, 2 requests, file **unchanged** |

The CLI does not require a test run before the turn ends, and it does not react to a failing test run. No extra
request, reminder, refusal or flag followed in either run. The result event has no field that says a test failed. A
caller reading exit code or `is_error` sees success in both. HYPOTHESIS: the DaVinci controller (file 04) closes this gap; no model has been run against it.

## 6. A Stop hook is the one code path that can force verification (E50v)

Project hook (`.claude/settings.json`, `Stop`): run `run_tests.py`; if it fails, print `{"decision":"block", "reason": ...}`.

Scripted model: run tests (fail), say "Done.", then, only if a block reason arrives, fix the file and say "Fixed and done."

Result: 4 model requests instead of 2. The first "Done." was blocked; the block reason arrived as a `system`-role
message; the model fixed the file; the second stop passed. The lab hook log (raw, private) showed call 1 `rc 1, stop_hook_active false` and call 2 `rc 0, stop_hook_active true`;
the committed `stream-summary.json` records only two Stop `hook_response` events with exit code 0, so the `rc` values
are of the test command and the `stop_hook_active` values are not in committed evidence. Final file fixed, `subtype success`.

So "do not finish while the tests fail" is implementable today as a hook, and Claude Code ships none by default. The
block cap (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`, default 8, E40) bounds the loop.

## 7. What was not run

- Interactive ExitPlanMode approval and the permission dialog.
- The autonomous addendum, coordinator mode, the todo reminder, proactivity-driven behavior of a real model.
- Explore under default (non-bypass) permissions.
- Any real-model run. Whether a real model runs tests unprompted, and how often it claims done after a failure, is
  UNKNOWN until the benchmark in `05-benchmark-design.md` runs.

## Run index

| Id | Question | Mode |
|---|---|---|
| E50a-baseline-default | baseline request | haiku, default |
| E50m-sonnet / opus / claude-opus-5-5 / claude-fable-5-1 | layout per model | default |
| E50o-claude-opus-4-1 / sonnet-4-5 / opus-4-7 / mythos-5 | layout per older model | default |
| E50p-haiku-ask / default / proactive | proactivity block | explicit permission mode |
| E50w-mode-ask / default / proactive | permission mode per level | no permission flag |
| E50q-plan | plan mode edit refusal, ExitPlanMode headless | plan |
| E50r-explore, E50u-explore-bash | Explore tool restriction, shell path | bypassPermissions |
| E50s-notest, E50t-failtest | completion without or after a failed test | bypassPermissions |
| E50v-stopgate | Stop-hook test gate | bypassPermissions |
