# 06. Failure recovery and continued execution

This report covers failures that are mechanically recovered, failures that are returned to the model, and failures that terminate the turn. It does not infer a general coding-failure controller from prompt text.

## 1. Tool failures

The tool dispatcher is `Qj` with validation and execution helpers `RWo` and `AWo`, `chunk-phacttch.js@2268196`, `@2272882`, and `@2275985`.

The sequence is:

```text
lookup
  -> abort/routing checks
  -> input parsing
  -> schema validation
  -> validateInput
  -> PreToolUse hooks
  -> permission resolution
  -> updated-input revalidation
  -> lock and abort checks
  -> call
  -> result mapping
  -> PostToolUse or PostToolUseFailure
  -> size handling
  -> tool_result user message
```

Invalid input, unknown tools, permission denials, and thrown tool calls become user messages containing a `tool_result` with `is_error:true`. A thrown call also runs PostToolUseFailure hooks, `chunk-phacttch.js@2235023` and `@2287500`.

The main loop receives the tool-result message and continues with `transition.reason:"next_turn"`, `chunk-93pksqr2.js@199381`. This is continuation, not an automatic retry of the same tool call. The model sees the error and chooses whether to retry, change the command, inspect more files, or stop.

A permission decision marked as ending the turn aborts with `permission-stop`, `chunk-phacttch.js@2289304`. This differs from an ordinary denied tool result.

## 2. Permission-denial recovery

Permission decisions are computed in two layers:

- `Hpn`, `chunk-phacttch.js@3360889`, applies deny rules, ask rules, tool checks, mode floors, safety checks, bypass rules, and allow rules.
- `jxr`, `chunk-phacttch.js@3321594`, resolves `ask` through auto-mode fast paths, the classifier, permission hooks, or a user dialog.

Auto-mode classification tracks three consecutive or twenty total denials, `chunk-phacttch.js@2533539`. At denial limits, the system changes from classifier handling to a prompt or a headless error path. A PermissionRequest hook can provide an answer. This is a denial budget, not a counter for failed coding approaches.

Bash safety checks parse commands, inspect compound commands and substitutions, and return a passthrough when the read-only fast path cannot prove safety. The exact compound splitter and tree-sitter parser were not read, `static-04` scope note. This leaves a static unknown about the parser's full grammar, not about the permission pipeline around it.

## 3. Stream and API failures

`Ad` calls `Zvt` and `pln`; `Gke` provides the CLI retry wrapper. The provider SDK is constructed with `maxRetries:0`, so retry policy is in the CLI. **VERIFIED-STATIC**, `chunk-phacttch.js@2840800`, `@2842829`.

`Gke` retries eligible statuses and connection failures with bounded attempts, backoff, retry-after handling, credential refresh limits, and fallback-model transitions. The stream decision machine `Q6e` / `Wan` in `chunk-phacttch.js@2741300` and `@2870500` chooses among:

- retry the stream
- switch to a fallback model
- retry without streaming
- keep partial output
- fail

The choice depends on error cause and whether the stream produced no output, thinking only, partial output, or completed visible output. It is transport recovery, not coding-task recovery.

Ordinary API failures become synthetic assistant API-error rows through `s6` / `dao` at `chunk-phacttch.js@900073` and the outer stream catch at `@2885300`. The normalizer does not send these synthetic rows to the API. The loop returns `api_error` unless a bounded recovery branch claims the error.

## 4. Output and malformed-response recovery

The loop has bounded recovery for malformed or incomplete model output:

| Failure | Mechanism | Limit / result |
|---|---|---|
| Max output tokens | append a meta nudge | up to three attempts, `chunk-93pksqr2.js@185383` |
| Truncated response | append a recovery nudge | bounded retry, `@185951` |
| Tool-use stop with no tool blocks | tombstone attempt and nudge | once, then `malformed_tool_use_exhausted`, `@186524` |
| Thinking-only answer | nudge the model | once, `@187227` |
| Model refusal | fallback or same-model retry | refusal retry state, `@179858` |
| Prompt too long/media error | reactive compact and retry | ends if compaction cannot recover, `@183900` |
| Unmatched tool-use history | repair pairing before request | synthetic error rows / orphan removal, `chunk-phacttch.js@4516900` |

These paths make the message sequence valid or give the model a chance to produce a structurally valid answer. They do not assert that the requested code change is correct.

## 5. Interruptions and cancellation

Abort reasons include user cancel, remote cancel, shutdown, interrupt, turn-abort, background, refusal-fallback-edit, recovery-timeout, permission-stop, server-fallback-tombstone, and subagent-park, `chunk-wns1g1rg.js@2700`.

The same signal reaches the provider request and child tools. On abort, the loop drains started tools and creates synthetic tool results for unanswered calls. An interrupt user message is emitted except for quiet reasons such as interrupt, turn-abort, refusal-fallback-edit, and permission-stop, `chunk-93pksqr2.js@177100` and `@192000`.

Interactive cancel reaches the turn controller through the REPL controller, `chunk-9w4htdvs.js@1393150`. Headless SIGINT and SDK interrupt/end-session controls map to different abort reasons in `chunk-fzzrkchm.js`. The exact keyboard binding that invokes the REPL method was not read.

## 6. Context and tool-output failures

Large tool results are persisted to a file with a bounded preview. The model receives a path and a preview, not the entire output. The per-message aggregate budget is 200,000 characters under a feature gate. **VERIFIED-STATIC**, `chunk-ghf2w5kp.js@1900`, `@8600`, and `chunk-fd5j6erd.js@1312` to `@1381`.

Before each request, autocompact can replace the history. If the context remains blocked after compaction, the loop returns `blocking_limit` without sending the request, `chunk-93pksqr2.js@149549`. Compaction has a failure count and a rapid-refill breaker in `chunk-phacttch.js@2598800`.

## 7. Stop-hook recovery

When there are no tool calls and no API error, `Za` runs Stop and SubagentStop hooks unless its skip conditions apply. A hook can return:

- `preventContinuation`, which ends with `stop_hook_prevented`;
- blocking errors, which become user messages and cause `stop_hook_blocking` re-entry;
- no block, which permits `completed`.

The consecutive block count is capped by `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`, default eight, `chunk-93pksqr2.js@188500`. A cap of zero or less disables the check. At the cap, the loop ends `completed` with a warning rather than continuing forever.

Existing E50v runtime evidence showed a user-configured Stop hook forcing another turn after a failed test. This is the one observed code path that can make test success a completion precondition. No default hook was found in the inspected source.

## 8. Subagent failures

A foreground agent exception is turned into recovered partial history and a harness note in the `runAgent` path around `chunk-h6wy99cb.js@42800`. An asynchronous agent failure marks its task failed and enqueues a failed task notification through `avt`, `chunk-phacttch.js@4226700`.

The parent receives child progress and final result messages. It may continue a child through `SendMessage`; the resume path `kn` at `chunk-r06rdesa.js@9390` refuses concurrent or stopping agents and uses recorded identifiers to avoid rewriting old transcript rows.

The source establishes failure delivery and lifecycle state. It does not show a parent-level policy that automatically launches a replacement worker after every child failure.

## 9. Coding-failure question

The inspected code has retry counters for transport, malformed output, context, stop hooks, classifier denials, and model fallback. It has no located general state machine that:

1. parses a failed test;
2. records a failed coding approach;
3. prohibits the same approach;
4. requires a diagnosis;
5. reruns a test after a changed approach.

That negative is bounded to the query loop, tool dispatch, permission, hook, subagent, prompt, and persistence regions read in this investigation. Prompt text in `uBo`, Bash guidance, proactivity, and coordinator mode may encourage recovery, but prompt text is not a mechanical counter.
