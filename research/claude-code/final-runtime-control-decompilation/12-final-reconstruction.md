# Final runtime-control reconstruction

Status: `PARTIAL`.

This continuation recovered the local execution relationships needed to explain
long-running sessions, but it does not meet the mission's standard for complete
decompilation of all six focused areas. The strongest result is a precise local
orchestration model with explicit provider/host gaps.

## Reconstructed session behavior

1. A model response produces tool-use blocks. Collected calls enter `Zo`, which
   partitions consecutive concurrency-safe calls and runs them through a
   bounded completion-driven pool. Unsafe calls are barriers. Every call still
   passes shared validation, hooks, permissions, and cancellation.
2. Tool messages are consumed as they are yielded, persisted/forwarded, and
   returned to the query loop. Safe-group completion order is not request order.
3. The query loop prepares the next request and may enter precomputed/reactive
   compaction on withheld overflow/error branches. Compaction returns a swap or
   reconstructed retry state; its helper does not directly run the tool batch.
   In the two recovered local callers, `rn` and deferred `Eqo` await the `Zo`
   async generator to completion before returning to that query-loop phase, so
   local batch execution and compaction have a verified caller-scoped no-overlap
   boundary (`chunk-jwmqjyrb.js@28129`, `@52813`, `@72140`). The runner is not
   exported from its defining asset; its complete export list and exact-token
   scope show no additional imported alias or callback caller
   (`chunk-jwmqjyrb.js@148486`). This does not cover detached, host/eval, or
   remote work outside the extracted JavaScript graph.
   Query iterations snapshot wake/passive folds before model preparation, so a
   later background notification is not shown entering the in-flight summary;
   its exact eligibility for the narrow passive-fold window remains open.
   Precomputed compaction is a separate asynchronous producer: `AXr` is
   launched without awaiting at both the automatic-compaction and post-response
   arm sites, then `PXr` explicitly joins its pending `settled` promise before
   admitting a swap. The `tqt` wrapper streams compact events, but the reactive
   controller's notification callback is used only for the skipped result in
   the inspected body; arbitrary background notifications are not shown being
   replayed into the active summary (`chunk-93pksqr2.js@140102`, `@174008`,
   `@182161`, `@182383`; `chunk-phacttch.js@857724`, `@2518310`,
   `@2611137`, `@2618033`).
   Precompute cleanup is explicit: the query executor aborts/removes an
   agent-owned pending entry on `subagent_exit`, and successful compaction
   invokes the same cleanup helper with `post_compact_cleanup`
   (`chunk-93pksqr2.js@127283`; `chunk-phacttch.js@2622159`, `@2622880`).
4. A detached tool persists its result, then emits a non-passive
   `task-notification`. When the local main drain is idle and input remains
   open, the queue subscriber invokes the main-loop kick. A child-agent result
   instead uses the agent wake router and delivery-commit queue consumption.
   An attached machine returning online has a separate `cd` controller that
   probes, rate-limits, and enqueues a guarded `host-return-wake` notification
    under the same queue path. The queued notification then passes through `Di`/`Ni` and the `Tbn`
    `prompt.submit` hook bridge; processing it is not equivalent to a guaranteed
    model request. Remote-served background shells are a distinct branch: the
    per-caller registry owns and settles them, and the completed result carries
    explicit non-notification guidance instead of entering the local
    task-notification queue (`chunk-bsjqfd0a.js@35653`, `@37213`, `@39490`;
    `chunk-qwgyf6qf.js@4678`, `@5543`; `chunk-0j0ezmy7.js@3077`).
   On the positive local path, after the stop/setup gates the query API loop
   invokes `I.callModel` through `Ca`; this remains conditional on queue,
   prompt-hook, stop, context, and model gates (`chunk-93pksqr2.js@153755`).
   The queue admission itself adds another conditional: under the
   `tengu_swirling_meteor` coalescing path, `xp.take` can mark a task
   notification `shouldQuery:false` and `queryHeldForNextTurn:true` when a
   qualifying follower is already admitted. `noteTurnEnded` then retains an
   empty completion's character/workload state and may synthesize a later empty
   prompt (`chunk-fzzrkchm.js@106757`, `@108084`). `kf.run` still submits the
   command to the query engine, while `Zp.route` applies the flag to result
   emission/holding (`chunk-fzzrkchm.js@137755`, `chunk-fzzrkchm.js@190435`). Thus “wake reached
   the turn runner,” “the current request was suppressed,” and “a result was
   held for a later turn” are distinct states; only the first and third are
   established by this branch.
5. MCP discovery is lazy and stateful. Pending discovery waits abort-aware;
   reconnect and list-change refreshes validate identity/configuration before
   publishing. A stale call becomes a correlated tool error. The generation-
   specific client wrapper propagates abort, overall timeout, and idle
   watchdog failures; task-capable calls issue `tasks/cancel` after abort, and
   stdio cleanup escalates SIGTERM to SIGKILL. The bounded stdio subclass also
   reaps an unconnected child: Windows closes stdin before process-tree
   termination, while non-Windows escalates SIGINT/SIGTERM/SIGKILL with bounded
   waits. The CLI reconnect controller has automatic and slow retry phases with
   overlap suppression and jittered delays. The common SDK client maps
   transport `onclose` to a `ConnectionClosed` rejection for all pending
   response handlers and clears their timers/progress state; transport
   `onerror` alone is observational. The custom WebSocket path now also has a
   recovered close contract: socket close removes listeners, clears the MCP
   connection/listing caches, and reaches the common pending-call rejection;
   native socket timing remains runtime-dependent. SSE/HTTP reconnect and
   stream-retention timing remain unresolved.
   The transport split is now narrower: legacy SSE reports EventSource errors
   and relies on explicit close, while Streamable HTTP keeps a resumable SSE
   channel with `Last-Event-ID`, server retry delay, two default retries,
   bounded auth branches, 202 promotion, and terminal `onRequestStreamEnd`
   (`chunk-6y1jd448.js@314500`, @320500, @327500). Recoverable stream drops
   bypass common `onclose` settlement until terminal end; response retention
   across replay remains unverified.
   Registry settlement adds an important boundary: `mfe` closes only stale,
   superseded, or refused candidates; its normal applied path updates the
   registry without directly closing the prior active client. Transport-close
   reconnect instead owns `cleanup()` before retry, so registry publication and
   in-flight-call cancellation are not the same edge
   (`chunk-0nh75v9f.js@3225`, `@10400`, `@11641`).
   The lower-level `clearServerCache` path is the separate active-client
   closure boundary: settled clients reach `qt.cleanup()`, while pending dials
   go through `Wc`. Configuration reconciliation, plugin deduplication, late
   queued-result handling, management disable, and authentication clearing
   all invoke that boundary or an equivalent direct close
   (`chunk-9158d2ng.js@116439`, `@116861`; `chunk-exx7q64a.js@14371`,
   `@16815`; `chunk-416ekshr.js@11144`; `chunk-bpav708b.js@1415`, `@4214`;
   `chunk-9w4htdvs.js@1580387`, `@1586900`; `chunk-t680wpqf.js@105271`).

Host shutdown gating is separate from queue admission. `Lp.run` refuses a new
drain once `Ls` or the committed flag `wn` is true, and inside a running drain
`xp.take` stops taking heads, so a held task-notification completion is zeroed
by `xp.exit` rather than delivered after shutdown commit. The `end_session`
request aborts the turn with a shutdown reason; the SIGTERM handler does not
(`chunk-fzzrkchm.js@118016`, `@109230`, `@113101`, `@491913`, `@572889`;
`chunk-phacttch.js@101341`). Whether `shutdown()` waits for an in-flight turn
is answered in report 01: `shutdown()` does not wait for the turn; a
failsafe and `process.exit` can abandon unfinished flushes, and a transcript
flush that outlives the 2000 ms cleanup race is joined by nothing later
(`chunk-phacttch.js@101341`, `@98517`, `@4553723`).

Compaction does not interact with queued background results: they live on the
message queue, outside the compaction input. A precomputed swap keeps rows
that arrived after its snapshot or is refused, and a stale settle is rejected
(`chunk-phacttch.js@2217054`, `@2519083`, `@2616569`;
`chunk-w3dhb84t.js@45723`). Detached results are discarded only by rewind,
resume and `/clear` (`chunk-phacttch.js@1911487`).
6. Permission asks are per tool-use id. The local UI assigns order and queue
   placement, supports async descriptor updates and reprompt, and resolves
   allow/deny/cancel through a single teardown path. `$Fo` classifies bridge
   outcomes, `JQo` persists the final decision by tool-use id and emits the
   normalized decision event, while the transport dispatcher validates and
   deduplicates `can_use_tool` requests before mapping dialog outcomes back to
   the host. The dialog store's visible top selectors and same-class reveal
   promotion are verified; cross-kind host focus arbitration remains open, while
   the shared selector keyboard/focus primitive is source-backed
   (`chunk-gq0v7nj7.js@1100`, `@2747`; selector `chunk-75p1g95y.js@31583`,
   `@38136`, `@39814`, `@40861`).
    The underlying ask registry retains multiple concurrent requests but
    publishes one selected visible block at a time; it serializes presentation,
    not the approval promises or tool execution (`chunk-phacttch.js@2931335`,
    `chunk-57pw7ky5.js@51135`).
   The local-JSX branch is also source-resolved through its dialog-loader and
   panel-host gates: interactive sessions mount the returned node through
   `localJsx.show`, while headless or hostless sessions take the command
   fallback. `Aee.show` owns the retained `local-jsx-N` node and maps abort to
   `closed` versus request dismissal to `dismissed`; the `Yke` literal covers
   the statically bundled renderer kinds (`chunk-qqv1hedf.js@27800`, `@29100`;
   `chunk-9w4htdvs.js@174423`, `@1292300`). Arbitrary loader/node bodies and
   cross-kind focus arbitration remain open.
7. Storage V5 is a structured handle used by task, transcript, sidecar, daemon,
   and other callers. Startup validates a pinned, host-supplied backend and
   publishes the resulting handle. Task persistence has conditional allocation
   and bounded retries. Transcript streams support cursor reads plus atomic or
   in-place compare-and-publish rewrites. Transcript writes are
   queued/routed. The default JavaScript pin factory returns no backend, so the
   provider construction is outside the inspected bundle or supplied by a host
boundary (`chunk-8qnn2dw7.js@816`, `@1541`; `chunk-we7c2g4z.js@5566`,
   `@5810`). The transcript owner adds a per-owner drain chain, 100 MiB/handle-
   change chunking, store-fence failure state, multi-pass `flush()`, and bounded
   exit/re-stamp windows (`chunk-phacttch.js@4561617`, `@4562282`, `@4572755`,
   `@4553729`, `@4565155`). The provider's commit implementation, crash
   durability, and cross-key transaction semantics remain unresolved.
8. Remote mirroring is additional asynchronous persistence. Local append is the
   immediate continuity path. Agent hydration is bounded/deduplicated/create-only
   when needed. The V1 URL-resume hydrator fetches authenticated ingress rows,
   applies a zero-content replacement guard, and otherwise replaces the local
   transcript. The fallback mirror is serialized per session and uses a
   `Last-Uuid` high-water plus duplicate-409 success, conflict adoption/refetch,
   and bounded retry policy (`chunk-7rd4vcyz.js@866`; `chunk-phacttch.js@42342`,
   `@44148`). The injected writer has two recovered adapter modes: bridge setup
   resolves after launching its host write, while CCR v2 admits rows to a
   batched uploader and later observes `/worker/internal-events` acknowledgement;
   `flushInternalEvents` is the explicit physical-drain point
   (`chunk-phacttch.js@4555224`; `chunk-2kr6zq6e.js@30760`;
   `chunk-cest8dre.js@52700`; `chunk-a5wd77pa.js@79930`, `@81521`, `@82970`,
   `@95811`). In CCR v2, the bridge's `ne` argument resolves through `a5o` and
   `k3r` to `F.writeInternalEvent`, but the bridge adapter does not await that
   callback. Server durability, bridge-side observation, replay, and the V1
   in-place replacement's concurrent-append/crash behavior remain open.

   The storage callers are not uniform: workflow-journal restoration performs
   V5 delete-then-append, reverse transcript scans detect page-overlap
   mutation, and transcript UUID removal uses bounded `ifMatch` retries,
   whereas V1 hydration's full-stream replacement has no source-version
   precondition (`chunk-8hbrzh7z.js@20800`; `chunk-phacttch.js@4527000`,
   `@4572000`; `chunk-sy9frekf.js@3000`).

## Most important newly recovered mechanisms

- `Zf` accepts owned non-passive queue work, not only human prompts.
- `ow`/`nw`/`wo` is the concrete local detached-result-to-main-drain kick.
- `Lf.route` is a separate child-agent wake/resume path with in-flight guarding.
- `Di`/`Ni`/`Tbn` is the queue-to-prompt hook boundary for task notifications;
  it can settle a notification before query policy reaches the model.
- `Tir`'s ordinary failed-summary breaker is distinct from the query-loop
  rapid-refill breaker; the former is not updated by the reactive `pir` body.
- Precompute is deliberately ahead-of-demand rather than a blocking compaction
  lock: its abort controller and settled promise are stored first, and the
  prompt-too-long path joins that entry only when it needs the swap.
- Permission dialogs use explicit ask ordering, queue placement, descriptor
  streams, resolve-once claims, reprompt aborts, and auto-deny deadlines.
- Local JSX dialogs use a typed `kg` schema, producer-side ID registry, and a
  provider-backed renderer lookup; this is the recovered terminal boundary,
  not proof of one universal permission-panel implementation.
- The generic permission approval path is now concrete: `HAe` validates the
  `permission_prompt` payload, `pMr` builds the allow/deny/rule/auto choices,
  `L9` and `Ve` provide selection/focus/feedback editing, and `nE` tracks a
  refused answer before the next focus decision. Specialized dialog kinds
  still have separate renderer bodies.
- The shared selector's keyboard/focus primitive is also recovered: `Ci`
  handles boundary-aware navigation and acceptance, `HYn` maintains the
  focused option/window, `Di` separates committed selection from focus, and
  `Yi`/`Fh` install and reclaim terminal focus. `cb` and `zmt` add mount/click
  and timing guards. The unresolved focus question is cross-kind host
  arbitration and arbitrary `local_jsx` content, not the common selector
  implementation (`chunk-75p1g95y.js@31583`, `@38136`, `@39814`, `@40861`,
  `chunk-pb1e761e.js@21952`, `chunk-cn7dpt66.js@957`, `@1312`).
- The file-permission specialization is also resolved through `iWe` → `ort`:
  `Ont` builds accept-once/session-grant/reject/outside-read choices and
  `lho` maps them to permission updates, denial, or outside-read flags while
  reusing the shared selector and feedback path.
- The web-fetch specialization is resolved through `iBt` → `Vke`:
  `qrt` maps yes/no/domain-grant selections to allow, deny, cancellation, or
  allow-plus-updates; `$rt` constructs the domain rule and `Qrt` gates it on
  safety classification, organization caps, hostname shape, and URL display
  state. The registered specialized dialog bodies are now resolved through the
  bash, browser, and plan-entry panels as well; cross-kind focus policy,
  dynamically supplied nodes, and host/local races are still open.
- The skill specialization is resolved through `sBt` → `Wke`: it offers exact
  and validated prefix grants, maps those choices through `Mrt` to persisted
  permission updates, and treats cancel as deny. It reuses the shared feedback
  selector, so its special behavior is in policy/result mapping rather than a
  separate transport.
- The PowerShell specialization is resolved through `oBt` → `Trt`: command
  text may be withheld or refined asynchronously, sandbox and destructive
  warnings are computed before display, and `p6` maps normal, suggestion, and
  edited-prefix choices to allow/deny/update results. Escape is deny in this
  branch, while the common transport remains shared.
- The monitor specialization is resolved through `rBt` → `Fke`: it renders
  command, MCP-poll, and WebSocket actions, suppresses standing grants for
  withheld/unsafe/capped cases, and maps suggestion acceptance through `mrt`
  to permission updates. Its cancellation path is deny.
- The central dialog registry is also resolved for bash, browser/Chrome, and
  plan-entry approval: `Yke` maps `ZJe` → `Jtt`, `eBt` → `Ywe`, and `tBt` →
  `oke`. Bash combines command withholding, sandbox/destructive warnings,
  standing-prefix suggestions, and optional auto-mode enablement; browser
  approval can add a session-scoped host rule and treats Escape as cancelled;
  plan entry checks answerability, records `tengu_plan_enter`, changes the
  session mode to `plan`, and maps “start implementing now” to deny. These
  are renderer-level facts; focus arbitration and host/local races remain
  unresolved (`chunk-9w4htdvs.js@1200505`, `@1206666`, `@1216982`,
  `@1293453`).
- The local permission host has a distinct display-arbitration layer above the
  store. `_v` chooses the user/non-user request for the current surface,
  `rCe` suppresses buried non-user cards while a user dialog is active, and
  `iCe` verifies request identity/payload and rejects stale answers before
  calling the store. `HO` bridges transport subscription, updates,
  cancellation, closure replies, and unmount cleanup. This proves local
  display selection and stale-answer prevention, but not the selector's final
  cross-kind focus arbitration or host-versus-remote answer ordering
  (`chunk-9w4htdvs.js@1320735`, `@1323202`, `@1324180`, `@1326466`).
- The former unresolved `JQo` caller edge is narrowed to a concrete chain:
  `aBt`'s `logDecision` closure invokes `JQo`; the normal `pdt` permission
  handler constructs that logger, and the in-process teammate runner's `He`
  callback constructs the same logger before passing it to `vC`. The remaining
  gap is only dynamically retained host/provider references
  (`chunk-57pw7ky5.js@5872`, `@5939`; `chunk-9w4htdvs.js@1506615`, `@23579`;
  `chunk-tzyj6m5p.js@18175`, `@3266`).
- Permission decision classification and persistence are separate from the
  dialog renderer: host, hook, abort, and config outcomes are normalized, then
  stored/emitted with tool-use and MCP metadata; the host/worker dispatcher
  also has request-id deduplication and explicit drain denial. The standard
  `kg` kind is a `local_jsx` command-panel descriptor: `Aee.show()` allocates
  `local-jsx-N`, the common registry maps it to `Hst`, and `Hst` resolves the
  node through the main screen's `LocalJsxRegistryContext`. The final node
  implementation and focus policy remain dynamic.
- Concurrent permission requests have a verified registry-level ordering:
  `eS` retains one ask block per `toolUseID`, honors explicit ask order,
  prefers `onTop` requests, and recomputes the visible block after open/close.
  This prevents sibling permission records from overwriting each other, but
  does not prove final cross-kind terminal focus arbitration (`chunk-phacttch.js@2931335`,
  caller `chunk-57pw7ky5.js@51135`); the shared selector focus primitive is
  independently source-backed as cited above.
- Local batch/compaction overlap is bounded in the inspected callers: `rn` and
  deferred `Eqo` consume `Zo` to completion before control returns to the query
  loop. The global overlap question remains open for detached or dynamic paths
  (`chunk-jwmqjyrb.js@28129`, `@52813`, `@72140`).
- MCP refresh/reconnect publication is guarded by server identity/configuration
  and reconnect epoch checks; call wrappers separately enforce abort, timeout,
  idle-watchdog, and task-cancellation policy.
- The v2 MCP call wrapper also records request states and refuses to resend a
  call after a close/no-answer race once it has been written; it returns a
  correlated `downstream_unreachable` error. Transport-specific close/abort
  event translation remains open (`chunk-9158d2ng.js@176700`, `@182461`).
- The MCP registry independently guards publication races: `mfe` drops and
  closes late settlements whose config or account epoch is stale, `ne` refuses
  a re-queried list when another server owns the name, and `kDo` registers one
  guarded `tools/list_changed` handler per connected client while retaining
  the previous listing after a failed refresh. This protects registry state
  but does not itself abort an already-running tool call
  (`chunk-0nh75v9f.js@3225`, `@13379`, `@13974`).
- The registry caller boundary is now tighter: exact literal scanning resolves
  the six `mfe` consumers, two MCP `ne` refresh callers, the `pi` wrapper's two
  consumers, and the `kDo` setup path across the bridge, reconnect, account-
  switch, and project-mount modules. Aliased/string/host callers remain an
  explicit dynamic-graph gap (`chunk-0nh75v9f.js@7555`, `@10400`, `@12046`,
  `@14776`; `chunk-2pkntkhf.js@23047`; `chunk-fzzrkchm.js@382970`,
  `@504690`, `@506239`, `@508488`, `@509441`; `chunk-td0hhs53.js@3801`).
- Storage/remote ordering is local append/write first, asynchronous mirror next;
  the local queue and fallback mirror have concrete sequencing boundaries, and
  V5 record rewrites have explicit preconditions and publish disciplines, but no
  provider-level crash guarantee or atomic cross-key/cross-backend transaction
  was established. The remote-writer correction is important: awaiting the
  persistence owner’s callback is adapter-dependent, and CCR queue admission is
  earlier than physical HTTP batch acknowledgement. The CCR v2 bridge writer
  identity is now resolved through `a5o`/`k3r`, but its returned promise is not
  awaited by the bridge adapter.
- Scheduled `/loop` wake is a separate queue producer: future fires enqueue
  prompt events, while restart reconciliation reports overdue fires with
  `shouldQuery:false`. Resume reconstruction scans orphaned agents and only
  restarts eligible disk-resumable agents when the session lifecycle supplies
  the guarded `resumeOrphanedAgents` callback.
- The local notification-to-request boundary is now exact: the main turn
  controller installs `Eo.stopsLoopForPending()`, the query loop checks it
  before request preparation, and a pending `defer-then-fork` gesture returns
  `background_requested` to suppress the next API call while the background
  fork takes ownership. A non-empty draft cancels this suppression when
  `tengu_keen_sloth` is enabled. This is a main-query handoff policy, not a
  universal background-result guarantee (`chunk-9w4htdvs.js@108462`,
  `@117617`, `@1413024`; `chunk-93pksqr2.js@134246`).

## Corrections to prior research

The previous background-wake report understated local automatic wake. It is now
corrected: an eligible detached completion does kick an idle, input-open local
main drain. This does not imply a guaranteed API request because the query loop
can stop before the next API call, and it does not establish external/remote
process wake.

The remote wake boundary is narrowed, not closed: the served-shell branch is
statically non-notifying to its calling session. Process-exit reconciliation is
now recovered locally, but the external process-start/daemon wake producer and
other remote transport wake producers remain unresolved.

The previous result-order wording is also preserved as corrected in the batch
report: safe-group delivery is completion-driven, while later transcript
normalization may make a capture appear request-ordered.

## Completion assessment by focused area

| Area | Assessment |
|---|---|
| Host wake/background resumption | PARTIAL: local main/child-agent, attached-host return, scheduled-loop, caller-dependent process-exit recovery, shutdown gating, and the full `shutdown()` timeline recovered; external process-start/remote wake and the `end_session` to process-exit caller open |
| Cross-subsystem concurrency | PARTIAL: local barriers/serialization and the compaction versus background-notification scenarios recovered; summary fidelity, compaction-then-rewind, queue crash durability, and storage races open |
| Local permission UI | PARTIAL: transport/store/queue, registered panels, display-host arbitration, stale-answer gating, teardown, and the shared selector keyboard/focus primitive recovered; cross-kind arbitration, dynamic nodes, and host/remote ordering remain open |
| MCP connection races | PARTIAL: pending/reconnect/stale-settlement/name-ownership/list-refresh guards and call-level abort/timeout/task cancellation recovered; transport timing and in-flight removal coupling open |
| Storage V5 backend | PARTIAL: injected provider, record-level compare/publish contract, local drain/fence/flush, and bounded exit path recovered; provider commit and cross-key transactions open |
| Remote session hydration | PARTIAL: V1 hydrator, keyed fallback mirror conflict recovery, child hydration, CCR v2 writer identity/batching, and callback non-await recovered; server durability/replay and replacement races open |
| Dynamic caller enumeration | PARTIAL: focused direct/resolved edges enumerated; dynamic graph incomplete |

## Final status

`PARTIAL` is required. Selecting `DONE` would contradict the unresolved
backend, hydration, transport, external-wake, renderer, and dynamic-graph
branches and the absence of an independent semantic reviewer. The reports are
usable as an evidence-backed reconstruction of the local orchestration core,
not as a complete decompilation of every runtime boundary.
