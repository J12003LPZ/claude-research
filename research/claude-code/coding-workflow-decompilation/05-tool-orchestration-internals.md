# 05. Tool orchestration internals

## 1. Tool registration and model-facing schema

Base built-in tools are assembled by `rv` at `chunk-rpwh4z9c.js@155896`. `ZL` filters them for simple mode, enabled state, session conditions, REPL mode, and delegation. `iUt` at `chunk-rpwh4z9c.js@157860` combines sorted built-ins with deny-filtered MCP tools and de-duplicates by name. Built-ins win a name collision because they are concatenated first.

The model-facing wire definition is built by `tN` at `chunk-phacttch.js@824746`. It contains the tool name, description, and JSON input schema, plus conditional strictness, eager-input streaming, deferred-loading, cache-control, and WebSearch citation fields. Descriptions come from each tool's prompt builder and can pass through tool-description hooks. MCP tools can supply a raw JSON schema.

The final model-facing pool is not simply the base registry:

```text
base built-ins
  -> session / simple-mode / enabled filters
  -> permission deny filters
  -> REPL and delegation filters
  -> MCP assembly and name deduplication
  -> child-agent Cl/LR filtering when applicable
  -> provider-specific schema shaping
  -> wire request
```

## 2. Deferred tools

`tNe` at `chunk-tgmspsjh.js@3646` decides which tools are always loaded and which can be deferred. The request builder around `chunk-phacttch.js@2771900` to `@2779950` chooses among a tool-search schema, tool-addition schema, or no search. It derives discovered tools from transcript tool-reference blocks and compact-boundary records, including `bJ` at `@2119022`.

Deferral is primarily a wire/schema availability feature. It does not automatically make a tool impossible to dispatch if the current executor pool has it. A missing pending MCP tool receives a bounded refresh/wait path through `Svt` / `vtt`, `chunk-phacttch.js@2142723`, `@2268202`; otherwise the executor returns a no-such-tool error.

The exact caller set for deferred discovery and the full ToolSearch body remain **UNKNOWN**.

## 3. Model tool-call recognition

The stream consumer emits one assistant message per completed content block. At `chunk-93pksqr2.js@172895`, the loop filters assistant content for `tool_use`, records those blocks, sets `needsFollowUp`, and calls `gs.addTool`. This means the model chooses tools by emitting the API tool-use block. The CLI does not infer a coding stage from natural-language text.

`gs.addTool` starts queue processing immediately. `chunk-93pksqr2.js@54033` interleaves model-stream consumption with executor drain ticks. The tool call is dispatched only after its input block has completed, even though execution can overlap the remaining response stream.

## 4. Concurrency

`canExecuteTool` at `chunk-93pksqr2.js@47172` applies the streaming rule:

- if no tool is executing, start;
- if the new tool is concurrency-safe and every active tool is concurrency-safe, start;
- otherwise wait.

An invalid input or exception in `isConcurrencySafe` counts as unsafe. The streaming executor has no numeric concurrency cap in the inspected class. A separate batched runner `Zo` at `chunk-jwmqjyrb.js@28129` groups safe calls and uses `CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY ?? 10`; its caller set was not traced. **VERIFIED-STATIC with one unresolved caller branch**.

Results are emitted in request order subject to the unsafe-tool barrier. `getCompletedResults` walks arrival order, emits progress and completed results, and removes in-progress ids. `getRemainingResults` waits for all unfinished entries, `chunk-93pksqr2.js@52211`.

## 5. Dispatch pipeline

`Qj` at `chunk-phacttch.js@2268202` resolves the tool and handles late MCP and isolation paths. `RWo` / `AWo` perform the execution stages:

1. Name lookup and alias resolution.
2. Abort and remote-routing checks.
3. JSON input parsing and optional coercion, `W9t`, `chunk-phacttch.js@2145160`.
4. Schema `safeParse`.
5. Tool-specific `validateInput`, `gsr`, `@2145597`.
6. PreToolUse hooks.
7. Permission decision.
8. Revalidation of permission-updated input.
9. Lock, heartbeat, and abort checks.
10. `tool.call`.
11. Result mapping.
12. PostToolUse or PostToolUseFailure hooks.
13. Size cap and persistence.
14. User-role tool-result message.

Parse, schema, validation, and permission failures become `tool_result` blocks with `is_error:true`. Unexpected calls are caught by `Qj` and also become an error result, preserving the tool-use id. **VERIFIED-STATIC**, `chunk-phacttch.js@2269600`, `@2276500`, `@2284600`, `@2290250`, and `@2297800`.

## 6. Permissions and modes

The primary permission algorithm is `Hpn` at `chunk-phacttch.js@3360889`. It applies deny rules, ask rules, tool checks, mode floors, safety checks, bypass rules, allow rules, and tool-specific interaction requirements. `jxr` at `@3321594` converts `ask` decisions through auto-mode fast paths, classifier calls, hooks, or an interactive prompt.

Relevant modes are `default`, `acceptEdits`, `plan`, `bypassPermissions`, `dontAsk`, `auto`, and internal `bubble`. The plan mode floor changes non-read-only tool decisions to ask or denial paths. Subagent `bubble` forwards permission prompts to the parent rather than widening permissions.

The classifier has a denial budget of three consecutive or twenty total blocks, `chunk-phacttch.js@2533539`. These limits are permission safety controls, not test or failure-recovery counters.

## 7. Tool result shape and output handling

A mapped tool result is a user message containing a `tool_result` block, optional `toolUseResult`, permission decision metadata, hook attachments, and new messages. Empty output is replaced by a named completion string. Large output is persisted to a tool-results file and sent as a bounded preview, `chunk-ghf2w5kp.js@1900`, `@5225`.

The per-message aggregate output budget is 200,000 characters under a remote flag, `chunk-fd5j6erd.js@1381`. Persistence avoids putting the whole command output into the next model request, but the model must choose to read the persisted file.

## 8. Continuation

`Ad` drains completed results while streaming and remaining results after the stream. It appends assistant messages followed by user tool-result messages and, unless a hook or tool requests an end, continues with `transition.reason:"next_turn"`, `chunk-93pksqr2.js@190600` to `@199381`.

A normal tool error therefore re-enters the model. The CLI does not automatically rerun the failed command or compare it with an earlier failed approach. A tool result marked `toolEndsTurn`, including the MCP end-turn metadata path, can terminate the turn after reaction hooks. This is a tool contract, not a verification gate.

## 9. Agent-specific orchestration

Child agents use `Cl` then `LR`, `chunk-jwmqjyrb.js@83520`, `@87492`, to remove globally forbidden tools, enforce depth and async allowlists, and apply the agent's `tools` and `disallowedTools`. A fork takes an exact parent tool array; a normal child gets a freshly assembled pool.

Explore and Plan are read-oriented by definition. The parent model still decides whether and when to invoke them. Async agents can retain Bash, Edit, Write, and other tools under their allowlist; actual permission mode and tool checks still apply.

## 10. Unresolved branches

- Full tree-sitter and compound-command parser bodies for Bash.
- Interactive permission dialog implementation and all `--permission-prompt-tool` paths.
- All callers of the batched `Zo` runner.
- Complete deferred ToolSearch discovery and server refresh race.
- Plugin tool-description and tool-call hook bodies.
- MCP lifecycle and remote execution details.
- Provider-specific tool serialization variants.
