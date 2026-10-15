# Cross-subsystem concurrency and ordering

Status: `PARTIAL` — the local ordering barriers and queue serialization are
`VERIFIED-STATIC`; every race at process shutdown, remote transport, and
storage-backend boundaries is not recovered.

## Scope

This report connects the already decompiled tool runner, compaction controller,
background notification queue, dynamic tool refresh, persistence, and
permission path. It does not claim that the entire 2,586-module graph has been
resolved. No new live-model experiment was run.

## Two different kinds of concurrency

Claude Code uses two distinct concurrency mechanisms:

1. **Within a collected tool batch**, safe tool calls are placed in a bounded
   completion-driven pool. `Zo` partitions consecutive safe calls and invokes
   `uEn` with `CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY ?? 10`
   (`chunk-jwmqjyrb.js@28129`, `@28055`; scheduler
   `chunk-phacttch.js@633773`). Unsafe calls form sequential barriers. The
   shared `Qj` dispatch still performs validation, hooks, permission checks,
   cancellation, and result mapping (`chunk-phacttch.js@2268196`).
2. **Across turns and background work**, queue notifications are serialized by
   the main drain. `ow` only kicks `Em.run` when the drain is idle, input is
   open, and an eligible non-passive item is at the queue head
   (`chunk-fzzrkchm.js@224541`; setup `@559872`). `Lp.run` refuses a second
   concurrent drain (`chunk-fzzrkchm.js@118016`).

These mechanisms should not be collapsed into one global executor. A safe tool
pool can have several active `Qj` generators while the owning turn is still
inside the query generator; a queue notification can arrive during that work,
but the main queue does not launch a second main drain.

## Tool completion ordering

`uEn` starts at most the configured number of generators, races their next
values, yields the first settled value, and schedules that generator's next
step. Thus progress and terminal messages are completion-ordered within a safe
group, not request-index ordered. `Wa` drains unsafe groups one block at a
time. `Zo` carries the original group order across the barrier
(`chunk-jwmqjyrb.js@28129`).

The normal batch caller `rn` and deferred-resume caller `Eqo` consume this
stream immediately, persist messages, forward progress/attachments, and carry
permission-layer updates (`chunk-jwmqjyrb.js@52813`, `@72140`). A sibling error
is represented by an error tool result through `Qj`; no source branch in the
runner cancels all siblings merely because one sibling returned an error. Shared
abort state can still cause cooperative cancellation. The exact timing when a
hard abort races a settled `Promise.race` result is `UNKNOWN`.

## Can compaction begin while tools are running?

The inspected main query generator enters the model-preparation and compaction
phase before its API request (`chunk-93pksqr2.js@129362`). In the normal tool
turn path, the collected tool calls are consumed by the batch caller and their
messages are returned to the query loop before the loop advances to the next
model request. The reactive/precomputed compaction branch is reached from that
query loop when an API response is withheld for prompt-too-long, image, or
related context conditions (`chunk-93pksqr2.js@180652`).

Therefore the strongest source-backed statement is:

```text
current query turn
  -> collect/execute tool calls
  -> consume tool results and hook output
  -> next query-loop state
  -> model preparation / automatic compaction
  -> request or compaction retry
```

There is no recovered call from `pir`, `PXr`, or the automatic compaction
controller directly into `Zo` while the same batch is still active. This makes
“compaction starts concurrently with an active local batch” **NOT SHOWN in the
inspected local path**, not proven impossible globally. A background task can
finish while compaction is running and enqueue a notification; queue delivery is
then subject to the main-drain guard and current turn policy.

### Stronger local no-overlap bound

The two recovered local callers impose a stricter boundary than the query-loop
summary alone shows. `Zo` is an async generator: for a safe group it yields
completion-driven results from `Ka`, then does not advance past that group until
the group iterator is exhausted; unsafe blocks are consumed through `Wa`
(`chunk-jwmqjyrb.js@28129`). The ordinary caller `rn` enters `for await` over
`Zo`, persists and forwards each yielded message, and only leaves the tool-run
scope after that iteration completes (`chunk-jwmqjyrb.js@72140`). The deferred
tool-resume caller `Eqo` follows the same rule explicitly: it creates the `Zo`
async iterator, awaits successive `next()` results, and finally calls `return()`
after the batch is done (`chunk-jwmqjyrb.js@52813`).

Therefore, **within these two statically inspected local caller paths**,
compaction cannot begin concurrently with an active `Zo` batch: control does not
return to the query-loop request/compaction phase until local batch consumption
has ended. This is `VERIFIED-STATIC` with a caller scope, not a global
impossibility claim. Detached/background execution, dynamically dispatched
callers, hard-abort timing, and host/remote work remain outside this bound. REA's
property trace seeded at `turnStartToolRun` was partial and returned no match
(`ev_26d892a6e46bafad5fde97b69ef12f1d0ec444c969e1fdea0f5c6860a2fc3cf0`), so it
does not weaken the direct source conclusion or prove additional callers.

### Precomputed compaction is an asynchronous producer

The precompute arm is not a synchronous extension of the reactive compaction
call. After automatic-compaction preparation, the query loop calls `AXr`
without awaiting its return (`chunk-93pksqr2.js@140102`). After a completed API
response it can call the same function again, also without awaiting it
(`chunk-93pksqr2.js@174008`). `AXr` creates a dedicated `AbortController`,
starts an asynchronous `d5r`/summary/hook job, and only then stores a pending
entry whose `settled` promise represents that job
(`chunk-phacttch.js@2611137`). The job can therefore overlap later query work;
the source does not support treating all compaction work as a single blocking
critical section.

The later prompt-too-long consumer has an explicit join. `PXr` checks the
pending entry and calls `Mcr` for a borrowed entry or `xXr` for the current
agent; both await the entry's `settled` promise or return a structured
turn-aborted result when the query aborts (`chunk-phacttch.js@2616746`,
`@2618033`). Thus the recovered rule is: precompute may run ahead, but a
precomputed swap is not admitted until the query joins and validates it.

### Compaction event and notification boundary

The local `tqt` adapter wraps a compaction callback in an async queue. It routes
`onCompactEvent` values directly into that queue and wraps the callback's
notification function as a `type:"notification"` queue item
(`chunk-phacttch.js@857724`). The reactive controller `pir` passes the query
notification callback through, but the complete body contains one
`onNotification` use: after `d5r` has settled with a skipped result it emits a
`compaction-skipped` notification (`chunk-phacttch.js@2518310`). The inspected
successful-summary, failed-summary, and replacement branches do not append a
newly arriving task notification to `messages` or the replacement set.

This narrows the prior race statement. Progress/status events are streamable
while compaction is active, and a skip can enqueue a user-facing notification;
there is no recovered source edge showing arbitrary background completion
notifications being replayed into an in-flight summary or swap. That remains
`UNKNOWN` at the queue/compaction boundary, while the absence of a direct live
message-queue append in the inspected `pir`/`PXr` bodies is `VERIFIED-STATIC`.

### Precompute cancellation and cleanup

The pending precompute is not left alive indiscriminately after a terminal
turn. The query executor `Y0` runs its tool/model stream in a `try/finally` and
calls `xir(..., "subagent_exit", ...)` for an agent-owned precompute when the
stream exits (`chunk-93pksqr2.js@127283`). `xir` resolves the agent key,
records a discard for a ready entry, aborts the entry's dedicated controller,
removes it from the registry, and performs the sidecar cleanup/re-hydration
bookkeeping before forgetting subagent telemetry (`chunk-phacttch.js@2622159`).
Successful compaction also invokes the same helper with
`"post_compact_cleanup"`, so a stale pending/ready precompute is cancelled or
discarded after the compaction boundary (`chunk-phacttch.js@2622880`). This is
`VERIFIED-STATIC`; it narrows the cancellation gap but does not establish the
exact interleaving when a summary promise settles at the same time as `xir`.

The manual and auto compaction helpers share a second notification boundary:
`kir` and `kZo` pass their callback to `Oon`, which only emits a notification
when the PreCompact hook reports `blockedBy`; the normal summary and cleanup
paths do not use that callback as a general task-notification subscription
(`chunk-phacttch.js@2565486`, `@2571102`, `@2597263`; `@2523831`). Thus the
available source supports compaction lifecycle/status streaming and explicit
hook-blocked/skipped notices, but not arbitrary background notification
injection into a currently running compaction generator.

## Compaction and notification interaction

Reactive compaction reconstructs a replacement message set and returns a
transition (`reactive_compact_retry` or `precomputed_compact_swap`) to the query
loop (`chunk-phacttch.js@2518325`; consumer `chunk-93pksqr2.js@180652`). The
main message queue is not directly drained by the compaction helper. A
notification arriving during the compaction request is therefore not proven to
be inserted into the in-flight summary request. The queue may instead be
consumed by the next admitted turn, or remain held if the loop is stopping or
input is closed.

The source does prove that compaction has its own abort signal and converts an
aborted summary to a structured failure, while the query loop can surface
`prompt_too_long`, `image_error`, or `blocking_limit`. It does not prove that a
notification that arrives during a failed compaction is replayed into the
replacement message set. That is an open cross-boundary race.

*Update:* the seven-scenario section below resolves this: queued items are
outside compaction input and are delivered after the boundary, and items
folded after a precompute snapshot are preserved as `tail` or the swap is
refused.

## Queue snapshot boundary inside the query loop

The query body has a more precise sequencing boundary than the high-level
compaction helper exposes. At the beginning of a query iteration it reads
`messageQueue.getTurnStartFoldCommands(...)`, registers those entries as
fold-in-flight, optionally builds `poll_events`, and delivers/settles that
fold before entering the model-preparation loop
(`chunk-93pksqr2.js@131155`, `@131354`, `@131412`). For the main thread without
an agent, it then takes a separate snapshot of the current command queue,
filters it through the passive-fold predicate, and consumes the entries only
after all generated fold messages were built successfully
(`chunk-93pksqr2.js@132165`).

This gives the following verified ordering for the inspected path:

```text
query iteration begins
  -> snapshot turn-start folds / poll events
  -> optional main-thread passive-fold snapshot and consume
  -> model preparation
  -> autocompact / reactive compaction
  -> model request or compaction retry/failure
```

`pir`/`PXr` do not receive the live message queue and do not append a newly
arrived queue notification to their current compaction input. Consequently, a
background completion that arrives after these query-iteration snapshots is
not shown being folded into the in-flight summary or replacement `P` message
set. The passive-fold predicate is now resolved: `s4(e)` requires
`e.passive === true` and current-agent ownership `Sp(e)`
(`chunk-phacttch.js@218788`). Normal `hge` detached completions and the
attached-host `cd` wake records are non-passive, so they do not satisfy `s4`
and remain subject to the outer queue/drain path. Passive auxiliary notes can
still be absorbed during the optional mid-turn fold.

## Background completion while the parent is active or idle

Detached completion persists the tool result and enqueues a non-passive task
notification (`chunk-phacttch.js@2216254`, `@2217060`). If the parent main drain
is active, no second drain starts; the existing pass or a later pass can
consume the item. If the parent is idle and input is open, `nw` causes `ow` to
invoke the main-loop kick (`chunk-fzzrkchm.js@224541`). If the parent is idle
but input is closed or shutdown is active, the local kick predicate fails.

Non-main-agent completions use `Lf.route`/`wX` and consume a queue entry after
delivery commitment (`chunk-fzzrkchm.js@229359`). That path has a wake-in-flight
guard and rechecks the queue. It is distinct from main-session resumption and
does not prove that an exited process or remote host is awakened.

## Dynamic tool refresh versus active execution

`Qj` waits for pending MCP work when the requested name indicates a pending MCP
tool and can refresh the tool pool before dispatch
(`chunk-phacttch.js@2268196`). The batch partition decision has already been
made by `ja`, so a tool that appears after partitioning cannot retroactively
change whether an existing block was scheduled safe or unsafe. A late refresh
can make a previously unresolved call executable, but the exact race between
tool-pool mutation and a concurrently executing sibling is not serialized by
`Zo` in the inspected body.

The conservative result is:

- active `Qj` calls retain their resolved dispatch context;
- pending MCP discovery may delay a specific call;
- the source does not establish atomic replacement of the complete tool set for
  all siblings in an already-running batch.

## Permissions and concurrent calls

Permission and hook logic is inside `Qj`/`RWo`, after scheduling admission. A
safe group therefore does not mean “permission-free parallel calls.” Each call
passes the same permission machinery. Concurrent permission prompts are a
separate UI/host concern; the local permission dialog queue and simultaneous
request policy are not completely decompiled in this pass. A denied call can
produce an error tool result while other safe siblings continue, subject to
shared abort state and hook behavior.

### What the local ask registry actually serializes

The local permission registry `eS` does not collapse concurrent asks into one
promise. `openAsk` increments a global open sequence and stores each request by
tool-use id in a map; `closeAsk` removes only the specified id. The selector
then publishes one visible permission block: an explicit `showAsk` id wins,
otherwise an `onTop` request wins, with opened/order tie-breaking among the
remaining entries (`chunk-phacttch.js@2931335`). This is
`VERIFIED-STATIC`: the UI surface is single-visible, but multiple asks remain
registered and can be promoted when the current one closes.

The permission caller `Ie` gives each request its own descriptor stream,
automated-recheck abort controller, dialog attempt, and teardown closure.
That closure aborts the request-local controller, clears hook-failure state,
removes only that tool-use id from `eS`, and releases its dialog resources;
parent-turn abort is wired into the request-local controller
(`chunk-57pw7ky5.js@51135`). Therefore concurrent safe tools can each reach the
permission machinery, while the local registry serializes visibility rather
than tool execution or all approval promises. Whether a host/remote dialog
surface imposes a stronger cross-request serialization remains unresolved.

## Persistence ordering

The detached path writes the tool result before enqueuing its completion
notification. Batch callers likewise persist each yielded message as they
consume it. This gives a local ordering edge:

```text
tool result representation -> storage write attempt -> notification/result delivery
```

It is not a transaction across filesystem/storage, queue memory, and remote
mirroring. A crash or remote failure between those edges can leave a persisted
result without an enqueued notification, or a queued notification whose later
hydration path cannot read the expected record. The low-level Storage V5 commit
and remote conflict behavior are covered as unresolved in reports 05–06.

## Compaction versus background notifications: seven scenarios

This section resolves the open compaction race using complete bodies of `AXr`,
`Acr`, `Cke`, `Mcr`, `xXr`, `PXr`, `pir`, `xxr`, `Mhe`, `Jvt`, `CXt`, `Ejo`,
`hge`, and the detached-call ledger `n6t`. Offsets are in the confidence ledger.

### The data model that decides the answer

* A completed detached call is not appended to the conversation array. `Ejo`
  renders the result, optionally saves an oversize result to a file, then
  `hge` calls `Qa`, which is `enqueuePendingNotification` on the **message
  queue**, as a non-passive `task-notification` with priority `next`
  (`chunk-phacttch.js@2217054`, `@2218820`, `@238822`).
* Compaction input is the conversation array. `AXr` receives `messages:r`
  and snapshots coverage as `{lastUuid, seenUuids, rowUuids}` via `yAo`
  (`chunk-phacttch.js@2611137`; `chunk-w3dhb84t.js@45615`). `pir` and `PXr`
  receive `messages:P` (`chunk-93pksqr2.js@182145`; `chunk-phacttch.js@2518310`,
  `@2618018`). None of these functions reads the message queue.
* The precomputed job runs under `Acr(toolUseContext, Te)`, which swaps in a
  **dedicated** `AbortController` `Te` (`chunk-phacttch.js@2610727`). It is not
  forwarded from the parent turn's controller.
* A precomputed result is admitted only through `xxr`
  (`chunk-w3dhb84t.js@45723`). It refuses with `boundary_uuid_missing`,
  `covered_messages_changed`, `kept_message_missing`, `unseen_reply`,
  `hook_rewrite`, or `would_not_fit`; otherwise it returns `reuse` with
  `tail`, the current messages that were not in the coverage set and are not
  `progress` rows. `pir` then builds
  `messagesToPreserve:[...compactResult.messagesToPreserve, ...tail]`
  (`chunk-phacttch.js@2519083`).

### Scenario table

| # | Scenario | Outcome | Evidence |
|---|---|---|---|
| 1 | Background task completes while a precomputed summary is generating | **Deferred, not lost.** The notification goes to the queue; the summary was computed from the snapshot `r` and never sees it. The notification is taken by the next drain (`xp.take`); non-passive items are not absorbed by the passive fold | `AXr` has no queue access; `Qa` target above; drain behavior in this report |
| 2 | Notification arrives during reactive compaction | **Deferred.** `pir` and `PXr` do not read the queue. Only `compaction-skipped` emits a notification from inside `pir` (`@2518310`) | `pir` body read in full |
| 3 | Notification queued after the snapshot but before the swap | Two sub-cases. Still in the queue: **deferred**. Already folded into the array before the swap: it is unseen by coverage, so `xxr` puts it in `tail` and it is **preserved verbatim after the kept messages**. If an unseen assistant row sits before the last seen row, the swap is refused (`unseen_reply`) and a fresh summary is built from the current messages | `xxr` body; `pir@2519083`; only `progress` rows are excluded from `tail` |
| 4 | Compaction completes before the queued result is delivered | **Delivered after the boundary.** Post-compact cleanup `Mhe` resets caches and discards the precompute entry; its body has no queue or ledger operation. A literal pass over every chunk found no compaction caller of `discardAll`, `discardAllOutside`, or `discardAllExcept` | `Mhe@2622774`; caller pass below |
| 5 | Shutdown begins during compaction | **Abandoned.** `shutdown()` does not join the turn (see report 01), so the in-flight summary request is cut at `process.exit`. Whether queued notifications survive a crash was not traced. The precompute sidecar queue `enqueueSidecarIo` has a settle accessor `sidecarIoSettled` with no caller in any chunk, so a pending sidecar write is not joined | `chunk-w3dhb84t.js@44732`; report 01 timeline |
| 6 | Precomputed summary settles after its parent turn was cancelled | **Settles into the registry; consumed later or discarded.** `Te` is independent of the parent controller. `xXr`/`Mcr` return `turn_aborted` and leave the entry. `Cke` accepts the settle only while the entry is still `pending` with the same controller. A later turn revalidates through `xxr` against the then-current messages. `xir` removes and aborts it on `post_compact_cleanup`, `subagent_exit`, and `uRn` on model switch | `Cke@2616569`, `Mcr@2616746`, `xXr@2617315`, `xir@2622150`, `uRn@2622478` |
| 7 | A detached call finishes after the delivery state was cleared | **Discarded by design.** `Y.settled` returns false when the ledger no longer holds the id, and `Ejo` checks `stillHeard()` after rendering and again after the oversize save, then returns without enqueueing (`conversation_cleared`). `/clear` also removes queued detached-call notifications | `n6t@1909268`; `CXt@2214983`; `Ejo@2217054`; `chunk-p5qcgmmn.js@3661` |

### Critical question: can a background result be omitted from the compacted
conversation and lost from effective context?

**Compaction alone: no path found that drops it (`VERIFIED-STATIC`, scoped).**

1. A result still in the queue is outside compaction's input and outside
   `Mhe`'s effects, so it is delivered after the boundary.
2. A result already in the array is either inside the summarized region (its
   content survives only as summary content) or kept, or, if newer than the
   snapshot, appended as `tail`. The array is not truncated without one of
   those three outcomes.
3. A swap that cannot prove coverage is refused and replaced by a fresh
   summary from the current messages.

**What is lossy, not lost (`INFERRED`).** A notification already folded into
the array and older than the preserved window is represented only by the
summary text. Whether the summary retains the result body or the saved-file
path was not decompiled. An oversize result is saved to a file before the
notification is built (`Ejo`), so the file exists even if the summary drops the
path.

**The real loss path is rewind, resume, and `/clear`, not compaction
(`VERIFIED-STATIC` for the mechanism).** `discardAllOutside(messages)` keeps only
ledger entries whose `tool_use` block appears in the given messages, aborts the
others with `conversation-cleared`, and `o6t` removes their queued
notifications (`chunk-phacttch.js@1909268`, `@1911487`). Its callers are the
print-host rewind (`chunk-fzzrkchm.js@594489`, and `bQo` at `@592535`), the
interactive rewind and resume (`chunk-9w4htdvs.js@370987`, `@354074`), and
`/clear` (`chunk-p5qcgmmn.js@3661`). `INFERRED`: because compaction replaces
older assistant rows with a summary, a later rewind or resume that passes the
compacted array would find no `tool_use` for an older detached call and discard
it. This sequence was not exercised and the rewind cut-index rules (`$l`) were
not decompiled, so it is recorded as a hypothesis with a proven mechanism.

### What prevents a stale precomputed summary from overwriting newer state

All `VERIFIED-STATIC`:

1. `Cke` drops a settle whose entry was removed, replaced, or already settled,
   or whose controller differs (`chunk-phacttch.js@2616569`).
2. The entry is single-use for the owning agent: `xXr` removes it before
   returning (`@2617315`); a borrowed entry (`Mcr`) is not removed.
3. `xir` and `uRn` abort and remove it on post-compact cleanup, subagent exit
   and model switch (`@2622150`, `@2622478`, `@2622774`).
4. `xxr` revalidates against the current messages on every consumption
   (`chunk-w3dhb84t.js@45723`), and the size check `ji` can refuse with
   `would_not_fit` (`@46800`).
5. A summary rehydrated from the on-disk sidecar is validated by `Jvt` for
   session id, timestamp, age (at most 604800000 ms), boundary presence,
   preserved-row presence, token shrink, and prior compaction
   (`chunk-phacttch.js@2607044`).
6. The swap is returned to the query loop as a new message set with transition
   `precomputed_compact_swap`; it is not applied by mutating shared session
   state in place (`chunk-93pksqr2.js@180652`, `@182145`).

### Race verdicts

| Race | Verdict |
|---|---|
| Notification versus in-flight summary input | Prevented: separate stores (queue versus array) |
| Notification folded after snapshot, before swap | Prevented from being lost: `tail` preserves it, or the swap is refused |
| Stale precompute settling over a newer entry | Prevented by the `Cke` identity guard |
| Precompute outliving a cancelled parent turn | Proven to occur; bounded by cleanup triggers and `xxr` revalidation |
| Shutdown during compaction | Proven to abandon the summary and unjoined sidecar writes |
| Detached result after `/clear`, rewind, resume | Proven to be discarded by design |
| Compaction followed by rewind or resume discarding a live detached call | Unresolved (mechanism proven, sequence not traced) |
| Fidelity of a summarized notification | Unresolved |
| Crash durability of the in-memory queue | Unresolved (queue persistence not traced) |

## State machine for the recovered local path

```text
tool-use blocks
  -> ja partition
       safe group -> uEn/Qj pool
       unsafe group -> Wa/Qj sequence
  -> rn/Eqo consume + persist
  -> query-loop turn state
       context okay -> next model request
       overflow/withheld response -> PXr/pir compaction
          swap/retry -> reconstructed query state
          failure -> prompt-too-long/image/blocking branch

background completion at any point
  -> persist -> task notification queue
       active main drain -> existing drain owns delivery
       idle/open -> ow kicks main drain
       child agent -> Lf.route/wX
       closed/stopping -> no new local drain
```

## Confidence ledger

| Claim | Confidence | Anchor |
|---|---|---|
| Safe tool calls use bounded completion-driven scheduling | VERIFIED-STATIC | `chunk-jwmqjyrb.js@28129`, `chunk-phacttch.js@633773` |
| Unsafe calls are sequential barriers | VERIFIED-STATIC | `chunk-jwmqjyrb.js@28129` |
| Tool results pass shared permissions/hooks | VERIFIED-STATIC | `chunk-phacttch.js@2268196`, `@2272882` |
| Main queue does not start a second drain while one runs | VERIFIED-STATIC | `chunk-fzzrkchm.js@118016` |
| Eligible detached completion can kick an idle local drain | VERIFIED-STATIC | `chunk-fzzrkchm.js@224541`, `@559872` |
| Compaction is entered by the query loop after tool-result consumption | VERIFIED-STATIC | `chunk-93pksqr2.js@129362`, `@180652` |
| Query iterations snapshot turn-start folds before model preparation | VERIFIED-STATIC | `chunk-93pksqr2.js@131155`, `@131354`, `@131412` |
| Detached completion is queued as a non-passive `task-notification` on the message queue, not appended to the conversation array | VERIFIED-STATIC | `chunk-phacttch.js@2217054`, `@2218820`, `@238822` |
| `AXr`/`pir`/`PXr` take the conversation array and never read the message queue | VERIFIED-STATIC | `chunk-phacttch.js@2611137`, `@2518310`, `@2618018` |
| Precompute runs under a dedicated controller not forwarded from the parent turn | VERIFIED-STATIC | `chunk-phacttch.js@2610727`, `@2611137` |
| `xxr` admits a precomputed swap only after coverage checks and appends unseen non-progress rows as `tail` | VERIFIED-STATIC | `chunk-w3dhb84t.js@45723`; `chunk-phacttch.js@2519083` |
| `Cke` rejects a stale settle (entry gone, replaced, or controller differs) | VERIFIED-STATIC | `chunk-phacttch.js@2616569` |
| Turn abort while awaiting a precompute leaves the entry registered | VERIFIED-STATIC | `chunk-phacttch.js@2616746`, `@2617315` |
| `Mhe` post-compact cleanup touches neither queue nor detached ledger | VERIFIED-STATIC | `chunk-phacttch.js@2622774` |
| No compaction path calls the ledger discard APIs; callers are rewind, resume, and `/clear` | VERIFIED-STATIC (literal pass over all chunks) | `chunk-fzzrkchm.js@594489`, `@592535`; `chunk-9w4htdvs.js@370987`, `@354074`; `chunk-p5qcgmmn.js@3661` |
| A detached result finishing after its ledger entry was cleared is dropped without enqueue | VERIFIED-STATIC | `chunk-phacttch.js@1909268`, `@2217054` |
| Precompute sidecar write queue has no joining caller at exit | VERIFIED-STATIC (literal pass) | `chunk-w3dhb84t.js@44732` |
| Compaction then rewind/resume discards a live detached call whose `tool_use` was summarized away | HYPOTHESIS (mechanism proven, sequence not traced) | `chunk-phacttch.js@1911487`, `@1909268` |
| Summary retains a summarized notification's result body or file path | UNKNOWN | summary prompt not decompiled |
| Queued notifications survive a process crash | UNKNOWN | queue persistence not traced |
| Main-thread passive-fold entries are consumed only after fold construction succeeds | VERIFIED-STATIC | `chunk-93pksqr2.js@132165` |
| Compaction helpers do not directly append a live queue notification to their current input | VERIFIED-STATIC | inspected `chunk-93pksqr2.js@131155`, `@132165`, `@180652` scope |
| `rn` and deferred `Eqo` hold their `Zo` async iteration until local batch completion before returning to the query loop | VERIFIED-STATIC | `chunk-jwmqjyrb.js@28129`, `@52813`, `@72140` |
| Precomputed compaction is launched without awaiting at the two query-loop arm sites | VERIFIED-STATIC | `chunk-93pksqr2.js@140102`, `@174008`; body `chunk-phacttch.js@2611137` |
| Precomputed swap consumption joins the pending job or aborts with a structured turn-aborted result | VERIFIED-STATIC | `chunk-phacttch.js@2616746`, `@2618033` |
| Compaction progress/status and notification values are routed through the async queue adapter | VERIFIED-STATIC | `chunk-phacttch.js@857724` |
| Reactive compaction emits its notification callback only on the skipped-result branch in the inspected body | VERIFIED-STATIC | `chunk-phacttch.js@2518310` |
| Agent stream exit aborts/removes its pending precompute entry | VERIFIED-STATIC | `chunk-93pksqr2.js@127283`; `chunk-phacttch.js@2622159` |
| Successful compaction invokes precompute post-boundary cleanup | VERIFIED-STATIC | `chunk-phacttch.js@2622880` |
| Manual/auto hook-block notices use the compaction callback, not a general task-notification subscription | VERIFIED-STATIC | `chunk-phacttch.js@2523831`, `@2565486`, `@2571102`, `@2597263` |
| `s4` passive mid-turn fold excludes non-passive detached/host-return wakes | VERIFIED-STATIC | `chunk-phacttch.js@218788`; producers `chunk-phacttch.js@2217060`, `chunk-fzzrkchm.js@100586` |
| Concurrent permission asks are retained per tool-use id with one selected visible block | VERIFIED-STATIC | `chunk-phacttch.js@2931335` |
| Permission teardown is request-local and removes only the completed ask | VERIFIED-STATIC | `chunk-57pw7ky5.js@51135` |
| Compaction and active safe-tool execution are globally impossible to overlap | UNKNOWN | inspected local turn/batch path; dynamic/background boundaries remain |
| Queue/storage/remote delivery is one atomic transaction | UNKNOWN | inspected local persistence and queue edges; Storage V5/remote commit body open |
| All permission UI races are serialized | UNKNOWN | local UI queue body not yet fully recovered |

## Open gaps

1. Whether any other dynamic queue producer changes its passive flag or enters
   the mid-turn fold while the queue is suspended; the ordinary detached and
   host-return producers are resolved as non-passive.
2. Whether a background completion notification can be routed into the active
   `tqt`/`pir` compaction queue through a callback path not visible in the
   inspected `pir` body.
3. The exact interleaving when a sibling tool or precompute promise settles
   concurrently with query cancellation; the explicit `Y0`/`Mhe` cleanup
   callers are recovered, but every competing producer/consumer path is not.
4. Atomicity, retry, and conflict behavior across Storage V5 and remote
   mirroring.
5. Host/remote dialog arbitration and the exact behavior when multiple safe
   calls reach `Ie` concurrently; the local registry's one-visible/many-open
   rule is recovered, but stronger host serialization is not.
6. Whether any host daemon can restart or wake a process after the local main
   loop has closed.
