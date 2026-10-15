# 08. Completion and verification internals

## 1. The completion boundary

Claude Code's ordinary completion boundary is in the shared async-generator loop `Ad`, wrapped by `Y0` in `chunk-93pksqr2.js@126966` and `@129362`. The loop returns a terminal reason after request recovery, tool draining, end-of-turn hooks, and max-turn checks. The API's `end_turn` stop reason is one input to this logic, not the entire completion decision.

At stream block completion, the provider stop reason is attached to the assistant message. The loop independently sets `needsFollowUp` when parsed `tool_use` blocks exist, `chunk-phacttch.js@2859082`, `@2860683`, and `chunk-93pksqr2.js@172895`.

Conceptually:

```text
assistant stream ends
  -> recover malformed/output/context conditions
  -> if tool_use blocks:
       drain tools
       run post-tool checks and hooks
       continue with assistant + tool_result messages
     else:
       run Stop/SubagentStop and internal end-of-turn checks
       block -> append feedback and continue, subject to cap/maxTurns
       pass -> completed
```

This is **VERIFIED-STATIC**. It is not a final-answer acceptance checker.

## 2. Ordinary no-tool path

The no-tool path handles max-output recovery, truncated output, malformed tool use, thinking-only output, refusal/API errors, and reactive compact before Stop hooks. Relevant loop regions are `chunk-93pksqr2.js@185000` to `@187573`.

`Za` then runs Stop/SubagentStop and internal end-of-turn checks, `chunk-93pksqr2.js@67408` to `@70600`. It returns:

- `preventContinuation`, which ends with `stop_hook_prevented`;
- blocking errors, which are appended as user messages and cause `stop_hook_blocking` re-entry;
- a clean result, which permits `completed`.

The default consecutive block cap is eight, `chunk-93pksqr2.js@188500`. When the cap is exceeded, the loop emits a warning and returns `completed` rather than continuing forever. Max turns can end the blocked retry before the cap.

Stop hooks are configuration-driven. Existing E50v evidence showed that a user Stop hook can run tests and block a false completion. E50s and E50t showed that, without such a hook, the CLI accepts a scripted completion without tests and after a failing test. **VERIFIED-BOTH for those observed modes**.

## 3. Tool-driven completion

With tool calls, the loop drains the executor using `getRemainingResults`, `chunk-93pksqr2.js@52900` and `@190576`. Failed tools normally return `tool_result.is_error:true` to the model, and the loop continues. The tool dispatcher is `Qj/RWo/AWo`, `chunk-phacttch.js@2268196`, `@2272882`, `@2275985`.

A special tool result can request end of turn. A successful tool result marked `toolEndsTurn`, including the MCP `_meta["claude/endTurn"]` path, can end the turn after its reactions. The loop does not necessarily give a Stop-hook block another model invocation on that path. Relevant evidence is `chunk-phacttch.js@1243393`, `chunk-93pksqr2.js@192949`, `@124625`, and `@62582`.

This is a tool-contract boundary, not a test-verification boundary. A tool can end the turn because its own contract says so.

## 4. Pending background work

Foreground tool and subagent calls remain in the executor drain. A background Agent launch returns `async_launched`, registers a task, and later queues a task notification. The ordinary completion path does not unconditionally wait for every background task. **VERIFIED-STATIC**, `chunk-h6wy99cb.js@6066`, `chunk-phacttch.js@4226700`, and `chunk-93pksqr2.js@52900`.

An active goal has a narrower exception: `Za` can defer a matching goal-evaluation Stop hook when agent or shell tasks are running and queue a check-in, `chunk-93pksqr2.js@70600`. Other parked-agent, idle-wake, and host-level policies were not fully traced. **UNKNOWN outside this branch**.

## 5. Max turns and terminal reasons

`maxTurns` is checked before another tool-result turn and before another Stop-hook-blocked turn, `chunk-93pksqr2.js@188345` and `@199183`. It is not the same as API retry budget.

The terminal-reason list includes:

`completed`, `max_turns`, `blocking_limit`, `rapid_refill_breaker`, `prompt_too_long`, `image_error`, `model_error`, `api_error`, `malformed_tool_use_exhausted`, `aborted_streaming`, `aborted_tools`, `stop_hook_prevented`, `hook_stopped`, `tool_deferred`, and `background_requested`, `chunk-80kqkekd.js@168441`.

The session engine separately maps terminal state and the trailing message to SDK result subtypes. `chunk-jr646ga5.js@66500` to `@69500` constructs budget, max-turn, execution-error, and success variants. An API-error assistant row can still result in subtype `success` with `is_error:true`, `@68300`. Exit status and subtype therefore do not prove that the requested code is correct.

## 6. What is and is not verified

The inspected completion paths do not contain a generic predicate equivalent to:

```text
changed executable files -> require a test command
last test failed -> prohibit completion
changed files -> require fresh acceptance evidence
```

The inline skill-command check records `not_run` telemetry rather than blocking completion, `chunk-93pksqr2.js@70000` and `chunk-phacttch.js@3368122`. Tests can still be enforced by:

- a user-configured Stop hook;
- a specialized tool or plugin contract;
- an active goal's Stop logic;
- permission or plan-mode restrictions;
- model instructions and the model's own tool selection.

This is a bounded static negative over the loop, executor, Stop hook, engine result, prompt, and built-in registry regions inspected. It does not cover server-side policies, all plugins, or every host wake path.

## 7. Verification mechanism table

| Mechanism | Enforced by local code | What it proves |
|---|---:|---|
| Tool schema and input validation | yes | input shape |
| Tool exit/error returned to model | yes | command/tool outcome was delivered |
| Stop hook block | yes, when configured | hook condition blocked this stop attempt |
| Stop-hook block cap | yes | prevents infinite hook loop |
| Plan-mode write refusal | yes | write was not permitted in plan mode |
| Max turns | yes | execution budget ended |
| API/stream retry | yes | transport recovery attempted |
| Test command after edit | not generic | nothing without a hook/tool rule |
| Re-test after failure | not generic | nothing without a hook/tool rule |
| Acceptance test pass | not generic | no local final-answer gate found |
| Review pass | optional prompt/command/goal | no default mandatory reviewer in inspected registry |

## 8. Answer to the central question

For ordinary coding tasks in the inspected CLI path, the application enforces tool permissions, plan-mode restrictions, transport recovery, turn budgets, Stop-hook behavior, and valid message/tool sequencing. It does not itself require that code be tested and verified before `completed`.

The model is instructed to test in some prompt branches and can be forced to test by a user Stop hook. The existing scripted runtime captures show both sides: completion without a test and completion after a failed test are permitted without a hook; a configured Stop hook can force another turn. **VERIFIED-BOTH, with runtime coverage limited to the existing scripted captures**.
