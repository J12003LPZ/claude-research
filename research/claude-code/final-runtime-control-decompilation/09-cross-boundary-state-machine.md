# Cross-boundary state machine

Status: `PARTIAL` — this is a consolidated static reconstruction. Each answer
labels the proven local edge separately from unresolved host/provider behavior.

## Consolidated flow

```text
model response
  -> streaming or collected tool calls
       -> Qj shared validation/hooks/permission
       -> Zo batch partition
            safe: uEn completion-driven pool
            unsafe: sequential barrier
       -> persist/forward tool results
  -> query-loop state
       -> context okay: next request
       -> overflow/withheld response: PXr precompute, pir reactive
            swap/retry or terminal context error

detached tool
  -> persist result -> task-notification queue
       -> idle/open main loop: ow -> Em.run -> Lp.run
       -> child agent: Lf.route -> wX
       -> closed/stopping: no local kick

attached host returns online
  -> cd host-status controller
       -> probe/rate/mode/turn gates
       -> host-return-wake task-notification (priority later)
       -> same main queue kick and conditional query policy

remote-served background shell
  -> per-caller nn reserve/adopt registry
  -> remote execution settles/records exit
  -> result carries KHo status guidance
  -> no local task-notification insertion in this branch

dynamic MCP
  -> pending/connected/failed state
  -> generation/config check
  -> Qj or correlated unknown/error result

all transcript/task/mirror edges
  -> local append/V5 or filesystem
  -> optional asynchronous remote mirror
```

## Required interaction questions

### 1. What happens if context compaction begins while tools are running?

**Proven:** the inspected query-loop path executes the collected tool batch
through `Zo`/`rn` before it advances to the next model-preparation and
compaction state (`chunk-jwmqjyrb.js@72140`, `chunk-93pksqr2.js@129362`,
`@180652`). The compaction helpers do not call `Zo` directly.

**Proven:** each query iteration snapshots turn-start folds and, for the main
thread, a separate passive-fold subset before model preparation. The
compaction helpers do not receive the live queue, so a notification arriving
after those snapshots is not shown entering the current summary/replacement
message set (`chunk-93pksqr2.js@131155`, `@132165`, `@180652`).

**Proven:** `s4` requires `passive === true` plus current-agent ownership, so
normal detached and attached-host return notifications are excluded from the
passive mid-turn fold and remain for the outer queue/drain
(`chunk-phacttch.js@218788`; producers `chunk-phacttch.js@2217060`,
`chunk-fzzrkchm.js@100586`).

**Unknown:** other dynamic producers may set `passive` differently, and the
exact delivery timing after the item is left for the outer queue/drain remains
dependent on the current turn state.

### 2. How does tool-result ordering interact with asynchronous execution?

**Proven:** safe-group messages are emitted in completion order by `uEn`, while
unsafe groups are sequential and group order remains a barrier
(`chunk-phacttch.js@633773`, `chunk-jwmqjyrb.js@28129`). `rn` consumes and
persists results as they arrive.

**Unknown:** whether every provider/transcript normalization step preserves
that order internally before the next request. Existing E08 runtime evidence
proves merged tool-result delivery, not every internal array mutation.

### 3. What happens when a background agent finishes after the parent becomes idle?

**Proven:** normal detached completion enqueues a non-passive task notification;
when the main drain is idle and input open, `ow` invokes the local kick. A
non-main-agent result is routed by `Lf.route`/`wX`. Separately, the attached
host-return controller can probe an online host and enqueue a guarded
`host-return-wake` task notification after its timing, mode, attestation, and
rate-limit checks (`chunk-fzzrkchm.js@224541`, `@229359`, `@97910`,
`@100586`, `@102430`).

**Proven:** a process restart performs local reconciliation through `yft`:
pending loops are checked by `Yi`, and orphaned agents are classified by `Wi`.
Only the lifecycle caller that supplies `resumeOrphanedAgents` can continue
eligible disk-resumable agents with `wX`; startup/frame callers do not by
themselves prove that callback is supplied (`chunk-rrep227n.js@43003`,
`@49606`, `@62600`; `chunk-9w4htdvs.js@365354`, `@368057`;
`chunk-fzzrkchm.js@477551`; `chunk-9w4htdvs.js@352930`).

**Unknown:** which external host or daemon starts a terminated process, and
behavior after a remote host disconnects. An overdue loop is informational only
(`shouldQuery:false`), while a future loop is re-armed. The served-shell branch
is explicitly non-notifying to its calling session.

### 4. How are background results persisted across session restarts?

**Proven:** detached completion persists the tool result before notification;
transcript/agent mirror owners queue local writes and bounded agent hydration
can create a missing local child transcript (`chunk-phacttch.js@2216254`,
`@4558167`, `@4594403`).

**Proven:** the V1 URL-resume hydrator fetches authenticated ingress rows,
ensures the local target, refuses a zero-content replacement when the local
transcript already has content, and otherwise replaces the local transcript
(`chunk-phacttch.js@4614350`; caller `chunk-fzzrkchm.js@681312`).

**Unknown:** crash consistency of queued writes, whether all detached result
classes are restored identically, and the remote service's replay/idempotency
or conflict semantics.

### 5. How does an MCP tool become available during an active conversation?

**Proven:** `ToolSearch` refreshes pending MCP clients and deferred tools,
waits abort-aware, then returns references for later direct calls
(`chunk-phacttch.js@937427`). Client list changes also trigger a refreshed
listing when identity/configuration still match (`chunk-0nh75v9f.js@11641`).

**Unknown:** an already serialized model request is not retroactively changed;
the exact next-turn schema injection path for every host mode is not globally
enumerated.

### 6. What happens when an MCP tool disappears while a call is pending?

**Proven:** generation/owner checks and `Qj` can reject a stale call with a
correlated tool error; stale list refreshes are not applied over a replacement
server (`chunk-phacttch.js@456210`, `@2268196`; `chunk-0nh75v9f.js@11641`).

**Unknown:** whether stdio/SSE/HTTP/WS/SDK transports actively cancel a remote
call after bytes have been sent, or merely return timeout/disconnect errors.

### 7. How do subagent tool restrictions interact with plugin tools?

**Proven:** plugin/MCP tools enter shared dispatch and permission context; the
tool record carries ownership/MCP metadata and the target agent context is
passed through `Qj`/wake paths (`chunk-phacttch.js@2268196`,
`chunk-phacttch.js@1826026`).

**Unknown:** exhaustive dynamic caller coverage for every plugin-defined agent
and the host-side policy merge at every subagent entry point.

### 8. How are interrupted tool calls represented after restoration?

**Proven:** tool results and notifications retain tool-use/task ids; persisted
transcript routing and task snapshots carry structured state. Permission
cancel/abort is distinct from deny and is recorded per tool-use id
(`chunk-57pw7ky5.js@51135`; `chunk-phacttch.js@4587783`).

**Unknown:** complete restore replay for every interrupted detached task and
the unresolved general remote hydrator.

### 9. How do interactive permissions interact with concurrent tool execution?

**Proven:** permission checks occur inside shared per-call dispatch, so safe
batch admission does not bypass permissions. Each local ask has a tool-use id,
ordering, queue placement, resolve-once claim, and abort teardown. The
host/worker `can_use_tool` dispatcher validates requests, deduplicates active
request ids, invokes the same dialog boundary, and maps allow/deny/cancel or
drain outcomes back to the transport. Settled bridge outcomes are normalized
by `$Fo` and persisted/emitted by `JQo` with tool-use and MCP metadata
(`chunk-phacttch.js@2268196`; `chunk-57pw7ky5.js@51135`;
`chunk-9w4htdvs.js@218600`, `@220300`; `chunk-phacttch.js@1880701`,
`@1881907`).

**Unknown:** visible focus/promotion policy for multiple simultaneously pending
local dialogs.

### 10. What if compaction fails during a long-running multi-agent task?

**Proven:** reactive failure returns structured failure; the query loop can
surface prompt-too-long/image/blocking outcomes. Background completion remains
an independent persisted queue event; child-agent wake has its own in-flight
guard (`chunk-phacttch.js@2518325`, `chunk-93pksqr2.js@180652`,
`chunk-fzzrkchm.js@229359`).

**Unknown:** whether a notification arriving during failed compaction is folded
into the next reconstructed message set or waits for a later queue pass.

### 11. How do task notifications interact with stored conversation history?

**Proven:** detached completion persists result content first and enqueues a
task notification with task/tool ids; local transcript and task storage are
separate but both can be carried through compaction/task markers
(`chunk-phacttch.js@2217060`, `chunk-zkrrxfpr.js@15407`).

**Unknown:** exact deduplication when a persisted notification is replayed after
resume and how remote replay/idempotency interacts with the V1 hydrator's
whole-transcript replacement.

### 12. When can asynchronous work cause another model request without a new user message?

**Proven:** an eligible non-passive detached completion can kick an idle,
input-open local main drain; non-main agent results can resume their target
agent (`chunk-fzzrkchm.js@224541`, `@229359`). A scheduled future loop also
enqueues a prompt event through the scheduler, whereas an overdue loop after
restart explicitly uses `shouldQuery:false` (`chunk-zdvza25y.js@18210`,
`chunk-rrep227n.js@62600`). The notification is then folded
through queue selection and the `prompt.submit` hook bridge (`Di`/`Ni`/`Tbn`),
which can surface, wait, drop, or leave it before normal query policy decides
whether to call the model (`chunk-93pksqr2.js@11147`, `@11874`,
`chunk-kgekdqv3.js@7480`). The query loop can still stop before an API call
(`chunk-93pksqr2.js@129362`).

**Unknown:** host/remote process start/wake after exit, and whether all queued prompt
or check-in classes have the same policy. The remote-served background-shell
branch itself does not enqueue the local task-notification path; its broader
transport/host behavior remains unknown. Goal check-in scheduling is a
separate path and must not be generalized from task notifications.

## Cross-boundary confidence

The most reliable reconstructed edges are local queue serialization, shared
tool dispatch, completion-driven batch ordering, permission resolve-once
teardown, MCP generation checks, and local-before-remote persistence ordering.
The least resolved edges are provider/host wake, Storage V5 transactionality,
general remote hydration, transport-specific MCP cancellation, and exhaustive
dynamic caller discovery.
