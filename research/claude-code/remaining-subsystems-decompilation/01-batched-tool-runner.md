# 01. Batched tool runner and caller graph

Target: Claude Code CLI 2.1.296, Windows x64 Bun extraction. This report is a
static reconstruction. Existing runtime captures are used only where called
out explicitly; no new model or billable runtime campaign was run.

Confidence labels in this report follow the investigation standard:

- **VERIFIED-STATIC**: the shipped function body and relevant branch were read.
- **VERIFIED-BOTH**: static evidence agrees with an existing capture.
- **INFERRED**: the relationship follows from exact source shape but a full
  caller or runtime path was not independently exercised.
- **UNKNOWN**: the inspected scope does not settle the question.

REA evidence: application analysis parent `ev_84ba937cf1929d4a0c62ebf0a747b20811040a04269d8760919ff468e7382205`; the selected
`chunk-jwmqjyrb.js` asset is SHA-256
`b7d77b6702a4c8339a844ee0a571043ab176fb9cd454ecda455ae93651037710`, parse
status complete, 40,406 AST nodes. REA's application graph is explicitly
partial and its semantic result budget was exhausted; the REA trace therefore
corroborates artifact identity and parse coverage, not runtime reachability.

## 1. Defining module and entry point

The batched runner is the local, non-exported generator `Zo` in
`chunk-jwmqjyrb.js@28129` (character offset; the bundled module begins at
line 11 because the source is minified onto one long line). Its signature is:

```text
async function* Zo(toolUseBlocks, assistantMessages, canUseTool, context)
```

The module imports `uEn`, `Qj`, `fM`, and `wRe` from
`chunk-phacttch.js`, `pn` from `chunk-3qrxzjv5.js`, and `wRe` from
`chunk-b8yyp6tv.js`; the import list is visible at
`chunk-jwmqjyrb.js@~2256-3569`.

`Zo` does not itself call tools. It partitions the model's tool-use blocks,
selects either the bounded-concurrent or sequential path, delegates every
individual call to `Qj`, and carries permission-layer changes forward.
**VERIFIED-STATIC**.

## 2. Exact scheduling algorithm

The partitioner is `ja` at `chunk-jwmqjyrb.js@28720`:

```text
for each block in original order:
    resolve the tool by name/alias with pn(tools, block.name, aliases)
    parse input using tool.inputSchema.safeParse(block.input)
    safe = parsed.success && Boolean(tool.isConcurrencySafe(parsed.data))
    if isConcurrencySafe throws, safe = false
    append to the current group only when both current and previous group safe
    otherwise start a new group
```

Consequences:

1. An invalid or alias-unresolved input is unsafe for scheduling purposes.
2. A throwing `isConcurrencySafe` implementation is fail-closed to the
   sequential path.
3. Safe calls are coalesced only when consecutive in the model's tool-use
   order.
4. Every unsafe call is a barrier: it is placed in a separate group and all
   later groups wait for it.
5. The runner has no separate dependency graph; dependency behavior is
   represented by the original order and the safe/unsafe barrier.

For a safe group, `Zo` calls `Ka`; for an unsafe group it calls `Wa`, both in
`chunk-jwmqjyrb.js@28129-~29400`. **VERIFIED-STATIC**.

### 2.1 Safe-group concurrency

`Ka` maps each block to an async generator that invokes `Qj`, then emits a
`set_in_progress_tool_use_ids/remove` event. It passes those generators to
`uEn` with `$a()` as the limit. `$a` is at `chunk-jwmqjyrb.js@28055` and returns
`CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY ?? 10`.

The actual scheduler `uEn` is `chunk-phacttch.js@633773`:

```text
queue all generators
start min(limit, queue.length)
while any generator is active:
    await Promise.race(active.next() promises)
    remove the settled promise
    if it yielded a value:
        immediately schedule that same generator's next() and yield the value
    else if queued generators remain:
        start the next queued generator
```

This is a completion-driven worker pool. It is not `Promise.all`, does not
wait for the slowest member before emitting earlier completions, and does not
reorder yielded values by input index. **VERIFIED-STATIC**.

### 2.2 Unsafe-group execution

`Wa` at `chunk-jwmqjyrb.js@~29000` iterates one block at a time and fully drains
`Qj` before yielding the next block. It carries `S.contextLayers` into
`wRe(context, layers)`, emits the message, and then emits the in-progress-id
removal for that block. **VERIFIED-STATIC**.

## 3. The individual dispatch contract

`Qj` is defined in `chunk-phacttch.js@2268196` and is the shared dispatch
pipeline for both paths. It performs, in order:

1. Activity and pending-session gates; it waits for pending MCP work when the
   tool name looks like a pending MCP tool.
2. Alias resolution and late tool-pool refresh through `vtt` when a matching
   MCP server is still connecting.
3. Unknown-tool result construction with the original tool-use id.
4. Abort check, isolation-latch check, remote/elsewhere routing, and tool
   metadata resolution.
5. `RWo` execution at `chunk-phacttch.js@2272882`, which performs coercion,
   JSON/schema validation, tool validation, PreToolUse hooks, permission
   resolution, updated-input validation, abort/lock checks, the actual
   `tool.call`, result mapping, and PostToolUse/PostToolUseFailure behavior.
6. Catch-all conversion of unexpected errors into an `is_error:true`
   `tool_result`, retaining `tool_use_id` and the source assistant UUID.

`Qj` also emits an explicit cancellation result when the context signal is
already aborted or becomes aborted during dispatch. **VERIFIED-STATIC**.

The shared dispatch means the batched runner and the streaming executor use the
same permission and hook machinery; `Zo` changes only admission and ordering,
not authorization. This corrects any interpretation of `Zo` as a bypass path.
**VERIFIED-STATIC**.

## 4. All statically resolved callers found

The exact token `Zo` occurs three times in the defining module: one definition
and two calls. The two calls are:

| Caller | Anchor | Inputs | Purpose | Consumption |
|---|---|---|---|---|
| `Eqo` | `chunk-jwmqjyrb.js@52813` | `[M]`, `[A]`, `s`, `r` | Re-execute one deferred/orphaned tool after the permission answer is recovered on resume | Manually drains the generator; persists each message; forwards progress/user messages; returns a deferred-hook attachment when present |
| `rn` | `chunk-jwmqjyrb.js@72140` | `e.map(D => D.block)`, assistant-message list `M`, `canUseTool`, execution context | Execute the collected tool-use calls for a turn | Persists and forwards each result; updates permission layers from `P.newContext`; returns the final permission context |

`Eqo` is the deferred-permission resume path. It re-finds the matching
assistant/tool-use block in the transcript, resets the permission context to
the resume mode, calls `Zo` with a singleton list, and drains it through a
traceparent-aware `next()` wrapper. If a message is progress or user content,
it is routed through `ste`; a `hook_deferred_tool` attachment is retained for
the caller. **VERIFIED-STATIC**.

`rn` is the normal turn-level batch caller. Before `Zo`, it restores assistant
rows that are not already present in the mutable transcript and answers calls
that were never sent. It then runs an optional `beforeRun` callback, calls
`Zo`, persists each emitted message, forwards progress/user messages through
`ste`, forwards attachments through `ll`, and wraps ordinary messages with a
fresh session id and `parent_tool_use_id:null`. **VERIFIED-STATIC**.

The exact source contains no additional direct `Zo(` call in
`chunk-jwmqjyrb.js`; the REA module inventory confirms the defining asset is
parse-complete but its global relationship graph is partial. Therefore the
following caller boundary is precise but not a proof about dynamically
constructed references:

- **VERIFIED-STATIC:** two direct same-module callers (`Eqo`, `rn`).
- **UNKNOWN:** dynamically aliased or generated callers outside the inspected
  static binding graph. The REA incoming module trace reached only the artifact
  root and reported partial source coverage; it did not prove global caller
  exhaustiveness (`ev_240d480a32c09e73544419c2886f39d36bdd276846e0babdc3710e08a17f638b`).

## 5. Result ordering and delivery

Within a safe group, results are yielded in the order in which each `Qj`
generator produces its next value. This includes progress events and terminal
messages. The per-generator in-progress removal is emitted only after that
generator finishes. Thus a fast later tool can produce progress/result output
before a slower earlier tool.

Across groups, `Zo` drains the entire group before entering the next group, so
the safe-group completion ordering is bounded by the unsafe barriers.

`rn` consumes this stream immediately. For each yielded `P`:

```text
if P is an internal control event: skip/handle it
permissionLayers = P.newContext.permissionLayers when present
if P.message: append it to the mutable transcript
                 persist it when storage is enabled
                 progress/user -> ste(...)
                 attachment -> ll(...)
                 ordinary -> yield session-wrapped message
```

The model-facing result is still a `user` message containing a
`tool_result` block with the original `tool_use_id`; later loop code merges the
assistant tool-use row and user tool-result messages before the next request.
The existing E08 capture independently observed three parallel tool uses
followed by one merged user message containing three tool results. This is
**VERIFIED-BOTH** for merged delivery, while completion-order emission is
**VERIFIED-STATIC**.

The previous report stated that batched results followed request order. That
claim is corrected here: the `uEn` implementation proves completion-order
emission within a safe group. Any later request-order appearance is a
transcript-normalization or capture presentation effect, not the scheduler's
yield order.

## 6. Failure, cancellation, and output handling

- A schema/validation/permission failure becomes an `is_error:true` result for
  the same tool-use id; it does not abort the entire safe group by itself.
- An unexpected `Qj` exception is converted to an error result unless the
  exception is a recognized control/cancellation condition.
- Abort state is carried by `context.abortController.signal` into every
  `Qj` generator. The scheduler itself has no independent cancellation
  protocol; cancellation is cooperative through the shared context.
- The runner does not cancel sibling generators merely because one sibling
  returned an error result. A shared abort or a tool-specific abort can cause
  other generators to return cancellation results; the exact race is
  **UNKNOWN** without a controlled runtime execution, which is out of scope.
- Large output truncation/persistence happens downstream in the shared
  `RWo/AWo` result path, not in `Zo`. The user message may carry a bounded
  preview plus a persisted tool-results reference.
- After normal batch completion the main query loop can run PostToolBatch hooks,
  refresh the tool pool/MCP clients, absorb queued notifications, and either
  continue with `next_turn` or terminate. Existing source anchors are
  `chunk-93pksqr2.js@190900-199381`.

## 7. State machine

```text
tool-use blocks
    |
    v
ja: resolve + safeParse + isConcurrencySafe
    |
    +-- safe group -- Ka -- uEn(limit=env ?? 10) -- Qj generators
    |                                      |
    |                                      +-- completion-order messages
    |
    +-- unsafe group -- Wa -- Qj one at a time
    |
    v
Zo carries contextLayers -> wRe and yields newContext
    |
    v
rn/Eqo persist, forward, and normalize results
    |
    v
PostToolBatch / tool-pool refresh / next_turn or terminal branch
```

## 8. Open gaps

1. The global indirect caller set remains **UNKNOWN** because the REA semantic
   graph is partial and the source uses minified imported bindings.
2. The exact interaction between a sibling's hard abort and already-running
   safe generators is **UNKNOWN**.
3. Whether any provider-specific transcript normalization reorders completed
   tool results before the next API request is not fully settled; E08 proves
   merged same-message delivery, not every internal array mutation.
4. The streaming executor's separate no-cap admission rule remains distinct
   from `Zo`'s numeric limit; callers may use either path depending on whether
   calls arrived during the stream or were collected for the batch.

