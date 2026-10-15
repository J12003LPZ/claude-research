# 01. Complete coding-workflow call graph

Target: Claude Code CLI 2.1.296, Windows x64 Bun standalone. This is a static reconstruction from the extracted JavaScript tree at `extracted/2.1.296/~BUN/root`. It describes what the code does when reached. It does not prove that every branch runs in every mode.

Evidence labels:

- **VERIFIED-STATIC**: the function body and the relevant branch were read in the shipped chunks.
- **VERIFIED-RUNTIME**: the existing E50 scripted captures observed the result. Those runs made no upstream model call.
- **INFERRED**: the call relationship follows from exports, argument shape, or adjacent code but the complete caller was not read.
- **UNKNOWN**: the inspected scope does not settle the question.

## 1. Entry and request loop

```text
host / REPL / headless runner
  -> Y0 wrapper, chunk-93pksqr2.js@126966
     -> Ad query generator, chunk-93pksqr2.js@129362
        -> memory and queued-message attachments
        -> compact-boundary message view
        -> model selection and autocompaction
        -> pre-request attachments
        -> callModel, Zvt, in chunk-phacttch.js
           -> streamResponse, pln
              -> API client and retry wrapper, Gke
              -> streamed assistant blocks
        -> StreamingToolExecutor, gs
           -> tool lookup, validation, hooks, permission, call
        -> Stop/SubagentStop hook driver, Za
        -> next_turn or terminal result
  -> session engine, chunk-jr646ga5.js@57300
  -> headless frame filter and result assembly, chunk-fzzrkchm.js
```

`Y0` is an async-generator wrapper. It delegates to `Ad`, yields loop events, and returns a terminal object. The loop state includes messages, tool-use context, transition metadata, and guards such as turn count, stop-hook blocking count, refusal retry state, malformed-tool retry state, and output-token recovery count. **VERIFIED-STATIC**, `chunk-93pksqr2.js@126966`, `@129362`, `@130200`.

The loop is a `while(true)` state machine. It does not recursively call itself for ordinary turns. Each continuation creates a new state object with a transition reason and continues. **VERIFIED-STATIC**, `chunk-93pksqr2.js@130200` and `@199381`.

## 2. Request preparation

Each iteration performs these steps before an API request:

1. Stop before the next API call if the main-thread background/shutdown predicate is set. The terminal reason is `background_requested`, `chunk-93pksqr2.js@134278`.
2. Emit `stream_request_start`, increment query tracking, and select messages after the last compact boundary, `@134900` to `@135400`.
3. Apply the tool-result replacement budget. This can shorten retained tool output before request construction, `@135400`.
4. Adopt a live model change and resolve the request model. A large-context plan-mode branch can select a different model, `@136000` to `@136400`.
5. Run the injected autocompact generator. A successful compact replaces the retained message view and emits post-compact messages. A rapid-refill breaker ends the turn with `rapid_refill_breaker`, `@136500` and `@137952`.
6. Append directory-sync, hook, model-announcement, deferred-tool, context-routing, and system-prompt snapshot attachments, `@139300` to `@142000`.
7. Build the streaming tool executor and per-attempt collections, `@142700`.
8. Enforce the hard context block before sending a request. If the estimate is blocked and this iteration did not just compact, emit a synthetic API error and return `blocking_limit`, `@149549`.

The prompt builders are upstream of this loop. The main system prompt is assembled by `H5t` in `chunk-phacttch.js@2019875`; proactivity and plan-mode content can arrive later as message attachments. The request-specific normalization, tool serialization, and provider selection happen in `pln` and its callees. See reports 02 and 05.

## 3. Model request and streaming

`Zvt` is the call-model entry used by the loop. The stream path `pln` normalizes messages, repairs tool-result pairing, applies cache markers, serializes tools, and calls the provider client. The provider client is created with the CLI retry wrapper's own retry count set to zero, so request retries are controlled by the CLI wrapper rather than by the SDK default. **VERIFIED-STATIC**, `chunk-phacttch.js@2840800`, `@2842829`, and `chunk-nfvf6nm0.js@256096`.

Conceptual request path:

```text
Ad
  -> Zvt(call-model parameters)
     -> pln(messages, system, tools, request options)
        -> normalizeForApi and pair tool results
        -> build model parameters
        -> Gke(withRetry)
           -> provider client beta.messages.create(stream=true)
           -> SSE accumulation
           -> assistant block messages
```

The stream consumer accumulates one builder per content-block index. It emits an assistant message when a content block stops, and later patches usage and stop reason when the message delta arrives. A `tool_use` block is therefore available to the executor only after its content block is complete. **VERIFIED-STATIC**, `chunk-phacttch.js@2859500` and `chunk-93pksqr2.js@173700`.

A stream failure enters an attempt-decision machine. Depending on progress and error class, it retries the stream, advances to a fallback model, switches to a non-streaming request, keeps partial output, or fails. The complete decision table is in `static-03-agent-loop-transport.md`, section Q7 and reconstructed pseudocode. **VERIFIED-STATIC**, `chunk-phacttch.js@2741900`.

## 4. Tool selection and execution

The model selects tools by emitting `tool_use` blocks. The loop does not infer a coding phase from the text of the assistant response. It sets `needsFollowUp` because an assistant message contains one or more `tool_use` blocks. **VERIFIED-STATIC**, `chunk-93pksqr2.js@173700`.

The streaming executor queues each completed block and starts `processQueue()` immediately. It can drain completed results while the model stream is still open. A tool runs when no tool is active or when the new tool and all active tools are concurrency-safe. There is no numeric limit in the streaming executor. **VERIFIED-STATIC**, `chunk-93pksqr2.js@46967`, `@47172`, `@54033`.

Each tool call passes through this application-controlled pipeline:

```text
name lookup and alias resolution
  -> abort and routing gates
  -> input JSON parse
  -> schema validation
  -> tool validateInput
  -> PreToolUse hooks
  -> permission resolution
  -> revalidate permission-updated input
  -> write-lock and abort checks
  -> tool.call
  -> result mapping
  -> PostToolUse or PostToolUseFailure hooks
  -> size cap / persistence
  -> user tool_result message
```

**VERIFIED-STATIC**, `Qj`, `RWo`, and `AWo` in `chunk-phacttch.js@2268196`, `@2272882`, and `@2275985`. Validation errors and unknown-tool errors become `tool_result` messages with `is_error:true`; normal tool errors are returned to the model as user messages and can cause another turn. A tool result is not a successful verification result by itself.

The tool pool is assembled separately from model selection. `rv` in `chunk-rpwh4z9c.js@155896` builds base tools. `ZL` filters the pool for mode and settings. `iUt` concatenates sorted built-ins with sorted, deny-filtered MCP tools and de-duplicates by name. Agent-specific filtering occurs later in `LR` in `chunk-jwmqjyrb.js`. **VERIFIED-STATIC** from static-04 and static-05.

## 5. Continuation after tools

After the stream ends, the loop drains remaining tool results. It then checks, in order, abort state, deferred-tool state, hook-requested stop, a tool-requested end of turn, PostToolBatch hooks, tool-pool refresh, queued commands, and max turns. If none ends the turn, it appends the assistant messages and tool-result messages, increments the turn count, records `transition:"next_turn"`, and loops. **VERIFIED-STATIC**, `chunk-93pksqr2.js@190900` to `@199381`.

The application therefore continues after a tool result because the tool-use state requires a follow-up. It does not continue because it has independently decided that a test or review is required.

## 6. No-tool completion path

When the assistant response contains no tool calls, the loop first handles recoverable output and model errors. It then runs Stop and SubagentStop hooks through `Za` if the skip conditions do not apply. The hook result has `blockingErrors`, `preventContinuation`, and `goalPass` fields. **VERIFIED-STATIC**, `chunk-93pksqr2.js@187700` to `@189300`.

- `preventContinuation` returns `stop_hook_prevented`.
- Blocking errors continue the loop with the blocking messages appended as user messages, unless max turns or the stop-hook block cap ends the loop.
- A clean hook result returns `completed`.
- The default stop-hook block cap is eight consecutive blocks. At the cap, the loop returns `completed` with a warning instead of forcing an infinite loop. `@188500`.

A Stop hook is user configuration. The static scope found no default hook that requires tests for ordinary coding tasks. Existing E50v runtime evidence confirms that a project Stop hook can force another model turn, while E50s and E50t show that the CLI permits completion without a test and after a failing test when no such hook blocks it. **VERIFIED-RUNTIME**, E50s, E50t, E50v.

## 7. Terminal reasons

The loop's application-level terminal reasons include:

`blocking_limit`, `rapid_refill_breaker`, `prompt_too_long`, `image_error`, `model_error`, `api_error`, `malformed_tool_use_exhausted`, `aborted_streaming`, `aborted_tools`, `stop_hook_prevented`, `hook_stopped`, `tool_deferred`, `max_turns`, `background_requested`, and `completed`. Engine-level mappings add budget, structured-output retry, deferred-tool-unavailable, and turn-setup failures. **VERIFIED-STATIC**, `chunk-80kqkekd.js@168400` and `chunk-93pksqr2.js` termination sites.

Headless result assembly maps a normal completed loop to subtype `success`, max-turn attachment to `error_max_turns`, and thrown or aborted execution to `error_during_execution`. An API error can still be surfaced as subtype `success` with `is_error:true`. **VERIFIED-STATIC**, `chunk-fzzrkchm.js@483134`, `chunk-jr646ga5.js@63800` to `@68300`. This is why process exit success is not evidence that the coding task passed its acceptance criteria.

## 8. Stage classification

| Coding stage | Mechanism found | Classification |
|---|---|---|
| Understand | Prompt text in plan mode and model conversation state | Prompt guidance; model decides |
| Explore | Explore/Plan tool filtering and prompt text | Tool availability is code; exploration choice is model-driven |
| Plan | Plan mode, plan-file path, ExitPlanMode permission and mode transition | Plan-mode restrictions and exit approval are code; plan content is model-driven |
| Implement | Edit/Write availability and normal tool pipeline | Tool execution and permissions are code; edit choice is model-driven |
| Test | Bash/tool execution only | No default test-enforcement path found in inspected scope |
| Diagnose | Error text, tool-result continuation, prompt guidance | Error delivery is code; diagnosis and next approach are model-driven |
| Recover | Bounded transport/output/compaction retries and Stop-hook re-entry | Transport recovery is code; coding failure recovery is mostly model-driven |
| Review | Plan phase review and optional review command | No default mandatory reviewer in inspected registry scope |
| Complete | No-tool path, hooks, max turns, abort/error terminal reasons | Completion is code-gated by engine conditions, not by acceptance verification |

## 9. Bounded limits

The main loop coverage above is based on the complete `Ad` region read in static-03, the tool executor and dispatch regions named in static-04, and the headless result path. Compaction internals, some provider fallback handlers, several control-request bodies, and the interactive permission dialog remain outside this pass. The absence claim about mandatory testing is therefore bounded to those inspected loop, tool, hook, prompt, registry, and headless-result scopes. It is not a claim about unavailable server-side behavior or every plugin.
