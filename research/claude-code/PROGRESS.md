# Investigation progress ledger

Resume point for this investigation after a context compaction or restart. Updated after
each stage. Evidence ids refer to `runtime-logs/<id>/` (sanitized) and `lab/raw/<id>/`
(raw, private, not committed).

## Stage status

| Stage | Status | Where |
|---|---|---|
| 1 Locate executable | done | `01-environment-and-provenance.md` |
| 2 REA audit | done | `01` section 3, `runtime-logs/rea/` |
| 3 to 12 Static architecture | done, 5 sweeps (spot-checked, not line-reviewed) | `static-0N-*.md` |
| 13 Runtime experiments | done, 171 manifest runs: 150 E, 13 C, 8 P | `03-runtime-experiments.md`, `runtime-logs/` |
| 14 Contracts | done | `04-internal-contracts.md` |
| 15, 18 Cross-validation and matrices | done | `06-verification-matrix.md` |
| 16 Repository and manifest | done, redaction check clean | `README.md`, `runtime-logs/MANIFEST.json` |
| 17 Implementation spec | done | `05-implementation-spec.md` |
| 19 Coding-workflow success research | static trace, 21 scripted runs (E50), tested DaVinci controller and benchmark; benchmark **not run** | `davinci-success-research/` |
| 20 Complete coding-workflow decompilation | static-only call graph, prompt, plan, agent, tool, recovery, context and completion reconstruction; REA unavailable in this pass | `coding-workflow-decompilation/` |
| 21 Remaining subsystem continuation | reports 01–14 added for batched tools, compaction, background delivery, plugins/MCP, Storage V5/remote mirroring, permissions, and task tools; partial by design | `remaining-subsystems-decompilation/` |
| 22 Final runtime-control continuation | reports 01–12 added; local detached-result wake, attached-host return self-wake, non-main-agent resume, query queue snapshot boundary, and passive-fold predicate recovered; permission transport/store queue, V5 provider injection/record preconditions, and MCP call abort/timeout/task cancellation/reconnect phases recovered; six focused areas remain partial | `final-runtime-control-decompilation/12-final-reconstruction.md` |
| 23 Coding-success final mission | exploration, model routing and compaction fidelity analyses plus a consolidated mechanisms report with a DaVinci gap matrix; 107 scripted-proxy runs (E90 series, no live model); 213 new source pins (312 total); live-model summary quality, the benchmark run, the plan-mode Bash rule and ToolSearch remain open | `coding-success-final/claude-code-coding-success-mechanisms.md` |

Next steps if resumed: the continuation pass recovered the central P0/P1/P2 paths but did not
meet the exhaustive-completion standard. Priority gaps now include the local interactive
permission dialog state machine, low-level Storage V5 backend/transaction semantics, remote
hydration replay/conflict policy, transport-specific MCP
pending-call races, process-exit/remote wake scheduling, and exhaustive dynamic caller enumeration.
The new reports are deliberately `PARTIAL` where those boundaries remain unresolved.
The ordinary detached and host-return notifications are now proven excluded from
the `s4` passive mid-turn fold; only other dynamic producers and their queue timing
remain open in that narrow race.
The final runtime-control pass now proves the idle, input-open local main-loop
kick for eligible detached results, recovered the attached-host `cd` return
self-wake controller, and separates both from the child-agent wake router. The
continuation also traced task notifications through `Di`/`Ni` and
the `Tbn` prompt-submit hook bridge, and separated the ordinary `Tir` failure
breaker from the query-loop rapid-refill breaker. It also recovers the local
permission transport/store boundary, the host-injected V5 backend and
record-level compare/publish contract, and the MCP call wrapper's abort,
timeout, idle-watchdog, task-cancellation, and stdio cleanup behavior. Reports
01–12 are present, but the pass remains `PARTIAL`

The latest bounded wake pass resolved an additional admission detail: `xp.take`
can rewrite an eligible task notification to `shouldQuery:false` and
`queryHeldForNextTurn:true` under `tengu_swirling_meteor` when a qualifying
follower is already admitted (`chunk-fzzrkchm.js@106757`, `@108084`). The
ordinary `Lp.run`/`turnRunner.run` handoff still occurs, while
`noteTurnEnded` can accumulate an empty completion and later synthesize an
empty prompt. This narrows the wake-to-request claim: `kf.run` still submits
the command to the query engine, and `Zp.route` applies the flag to result
emission/holding (`chunk-fzzrkchm.js@137755`, `@190435`). The flag alone does
not prove that the current API call was skipped.

The latest MCP race pass re-read the complete `mfe` settlement and transport
close/reconnect bodies. Normal applied registry settlement updates app/dynamic
store state without directly closing the prior active client; stale,
superseded, and refused candidates are closed. Transport-close handling owns
`cleanup()` before reconnect and performs current identity/configuration checks
(`chunk-0nh75v9f.js@3225`, `@10400`, `@11641`). A bounded caller pass then
resolved `clearServerCache` as the active-client closure boundary: settled
clients reach `qt.cleanup()`, pending dials reach `Wc`, and configuration
reconciliation, plugin deduplication, queued updates, management disable, and
authentication clearing all reach that boundary or an equivalent direct close
(`chunk-9158d2ng.js@116439`, `@116861`; `chunk-exx7q64a.js@14371`, `@16815`;
`chunk-416ekshr.js@11144`; `chunk-bpav708b.js@1415`, `@4214`;
`chunk-9w4htdvs.js@1580387`, `@1586900`; `chunk-t680wpqf.js@105271`).
Remaining MCP uncertainty is limited to dynamic/provider/host callers outside
these bounded paths.

A host-wake shutdown pass resolved the guards in `Lp.run`: `stopping` is the
shutdown controller's `shutdownInProgress` and `terminalShutdown` is a
process-global flag set only by `T8`, both committed by `shutdown()` before its
first await. After commit `xp.take` takes no head, `Xu.isHeld` releases waits,
`xp.exit` zeroes held completion counters, and the child-agent wake router
refuses to resume. `end_session` aborts the drain controller with a shutdown
reason, while the SIGTERM handler does not; `shutdown()` does not wait for an
in-flight turn (see the timeline below) (`chunk-fzzrkchm.js@118016`, `@109230`,
`@113101`, `@228384`, `@491913`, `@572889`; `chunk-phacttch.js@101341`,
`@100147`; `chunk-80kqkekd.js@150477`).

The shutdown timeline and the compaction race are now resolved to the
following scoped results. `shutdown()` does not await or cancel the model turn;
it awaits registered cleanups under a 2000 ms race, the exit-handoff write,
shell kill backstops, process sweeps, SessionEnd hooks, flushes, and a stdout
drain, and a failsafe timer calls `process.exit` regardless
(`chunk-phacttch.js@101341`, `@98517`; `chunk-j0pppawn.js@4520`). A transcript
flush that outlives the 2000 ms race is joined by nothing later
(`chunk-phacttch.js@4553723`). For compaction, detached completions go to the
message queue, not the conversation array, so compaction neither summarizes
nor drops a queued result; precomputed swaps append post-snapshot rows as
`tail` or are refused (`chunk-w3dhb84t.js@45723`;
`chunk-phacttch.js@2217054`, `@2519083`, `@2616569`). The loss path found is
rewind, resume and `/clear` discarding detached ledger entries
(`chunk-phacttch.js@1911487`). Open: whether `Zn`/`Ps` follows `end_session`
host teardown, queue crash durability, summary fidelity, and the
compaction-then-rewind sequence.

The latest permission-UI correction re-read the shared selector implementation
and narrowed an earlier open gap: `Ci`, `HYn`, `Di`, `Yi`, `Fh`, `cb`, and `zmt`
source the keyboard/focus, focus-reclaim, and mount/click timing primitives
(`chunk-75p1g95y.js@31583`, `@38136`, `@39814`, `@40861`,
`chunk-pb1e761e.js@21952`, `chunk-cn7dpt66.js@957`, `@1312`). Cross-kind host
arbitration, arbitrary `local_jsx` node behavior, and host-versus-remote answer
ordering remain unresolved, so the status stays `PARTIAL`.

The next bounded caller pass resolved the prior `JQo` caller gap. The `aBt`
`logDecision` closure invokes `JQo`; the normal `pdt` permission handler and
the in-process teammate runner's `He` callback both construct that logger
(`chunk-57pw7ky5.js@5872`, `@5939`; `chunk-9w4htdvs.js@1506615`;
`chunk-tzyj6m5p.js@18175`, `@3266`). The dynamic caller graph now has 146
structured edges; only dynamically retained host/provider logger references
remain in that branch.
because the V5 provider commit implementation, remote hydration replay/conflict
policy, transport-specific SDK settlement/retry, process-exit and other remote
wake remain unresolved. A new static pass also traced the remote-served
background-shell registry and its explicit non-notifying completion contract;
this narrows, but does not remove, the broader remote-wake gap. The
renderer/focus graph, exhaustive dynamic callers, and an independent semantic
review remain unresolved.

The latest static pass traced scheduled `/loop` wake and process-exit recovery:
`ScheduleWakeup` persists/re-arms future loop fires, while resume `yft` uses
`Yi` to turn overdue fires into informational `task-notification` events with
`shouldQuery:false` and uses `Wi` to classify orphaned background agents. Only
the session lifecycle caller supplies the guarded `resumeOrphanedAgents`
callback that can restart eligible disk-resumable agents with
`continueInterruptedTurn:true`; startup/frame restore callers do not establish
the same callback. This closes local reconciliation details but not the
external daemon/process-start wake producer. REA's exact `sleep-auto-resume`
trace had no match in the partial graph and is retained only as a limitation
record (`ev_97c2bc819287f6679c0f79a1886e7193dc0a3a03431d3972f0c7e4524cbe71ba`).

The current concurrency continuation re-read the complete `tqt`, `pir`,
`AXr`, `PXr`, and query-loop bodies. It confirms that the compaction callback
queue carries lifecycle events and explicit hook-blocked/skipped notices, not
a general background-task subscription. It also recovered explicit precompute
cleanup: `Y0` aborts/removes an agent-owned entry on `subagent_exit`, and
`Mhe` invokes the same cleanup after compaction (`chunk-93pksqr2.js@127283`;
`chunk-phacttch.js@2622159`, `@2622880`). Concurrent promise-settlement
ordering, provider-side wake paths, and the remaining dynamic producers stay
open; status remains `PARTIAL`.

The permission-race continuation re-read `eS` and `Ie`: concurrent asks are
retained by tool-use id, one block is selected for visibility using explicit
show/onTop/order rules, and each caller has request-local abort/teardown. The
local registry therefore serializes presentation, not all approval promises or
tool execution (`chunk-phacttch.js@2931335`; `chunk-57pw7ky5.js@51135`).
Host/remote cross-request arbitration remains open.

The Storage V5 continuation narrowed the provider boundary: `Xmo` can only
return an injected `{backend,configHome}` pin, while its default `SSr` factory
returns no backend (`chunk-8qnn2dw7.js@816`, `@1541`). Startup validates and
publishes that optional handle (`chunk-we7c2g4z.js@5566`, `@5810`), but no
non-default provider factory or commit implementation was recovered in the
inspected JavaScript extraction. This remains a scoped `UNKNOWN` host/native
boundary, not a claim that no provider exists.

The latest storage/remote pass traced the transcript owner's local drain chain:
adjacent queued rows are chunked to 100 MiB or backend-handle changes, failures
can install a store fence, `flush()` performs multiple drain passes, and process
exit gives the project flush and V5 re-stamp bounded 500 ms windows
(`chunk-phacttch.js@4561617`, `@4562282`, `@4572755`, `@4553729`, `@4565155`).
The fallback remote ingress writer is serialized per session through `Ph().run`
and uses `Last-Uuid`/409 recovery with ten attempts and capped backoff
(`chunk-7rd4vcyz.js@866`; `chunk-phacttch.js@42342`, `@44148`). These findings
narrow local ordering and fallback conflict recovery, but provider durability,
injected internal-writer replay, and V1 replacement races remain unresolved.

The follow-up writer pass resolved the CCR v2 side of that remaining boundary.
`x4t`/`P4t` register injected writers/readers; the bridge/repl adapter launches
`ne(...)` and returns an already-resolved promise, while the CCR adapter awaits
queue admission into `internalEventUploader`. The uploader later posts
`/worker/internal-events`, schedules `onInternalBatchAcked`, and exposes
`flushInternalEvents`; shutdown waits at most three seconds for that drain
(`chunk-phacttch.js@4555224`; `chunk-2kr6zq6e.js@30760`;
`chunk-cest8dre.js@52700`; `chunk-a5wd77pa.js@79930`, `@81521`, `@82970`,
`@95811`; `chunk-cvvnq4he.js@414956`). The reports now distinguish callback
return, queue admission, and physical batch acknowledgement. Server durability,
bridge-side completion, crash replay, and V1 replacement races remain open.

The next bridge pass traced the supplied `ne` callback through the CCR v2
transport: `a5o` obtains `S.getInternalEventWriter`, `k3r` exposes that as
`F.writeInternalEvent`, and `a5o` passes its redaction/live wrapper `v` into
the bridge persistence callback (`chunk-tar8k6v4.js@43925`, `@78732`, `@79043`;
`chunk-a5wd77pa.js@125745`, `@130515`). The bridge invokes `ne` without
awaiting its returned promise (`chunk-2kr6zq6e.js@29677`, `@30760`). The
remaining issue is therefore observation/durability/replay, not an unknown CCR
writer identity. REA's incoming trace for `getInternalEventWriter` had zero
matches under the partial graph (`ev_4984b4ce6342dca35d115cba83b88938821de1a1d72b137cd406e5e2cb9b17f3`).

The latest Storage V5 pass separated caller-side mutation guarantees. Workflow
journal restoration deletes the V5 key and appends restored records without a
visible transaction; `LocalFileJournal.loadV5` rejects a non-advancing cursor
(`chunk-8hbrzh7z.js@20800`). The transcript reverse reader detects sequence/data
changes between backward pages, and V5 UUID removal uses bounded `ifMatch`
retries plus size/cursor guards (`chunk-phacttch.js@4527000`, `@4572000`). The
V1 hydration helper performs full in-place replacement without a source-version
precondition (`chunk-sy9frekf.js@3000`), so its concurrent-append/crash race is
weaker than transcript tombstone removal. Provider transaction and durability
semantics remain unresolved; status stays `PARTIAL`.

The next local-permission pass resolved the bundled local-JSX caller boundary.
The slash-command dispatcher rejects headless execution, selects `s.load` or
`resolveCommandDialog`, falls back when no loader or panel host exists, and
mounts the resolved node through `localJsx.show`; dismissal completes the
command without another model query (`chunk-qqv1hedf.js@27800`, `@29100`).
`Aee.show` owns monotonic `local-jsx-N` retention, turn-boundary abort
retirement, typed `kg` transport, and `closed` versus `dismissed` settlement
(`chunk-9w4htdvs.js@174423`). The `Yke` literal enumerates the statically
bundled renderer kinds, including conditional and list-expanded entries
(`chunk-9w4htdvs.js@1292300`). Arbitrary loader/node bodies and cross-kind
focus/answer ordering remain open; status stays `PARTIAL`.

The next MCP pass resolved the remaining transport-level reconnect distinction.
Legacy `Lgn` SSE uses EventSource error/explicit-close handling without an
automatic reconnect loop (`chunk-6y1jd448.js@314500`, `@315922`). Modern
Streamable HTTP `_1t` maintains a resumable SSE channel with `Last-Event-ID`,
server retry delays, two default retries, 401/403 auth branches, 405 terminal
end, and 202-to-stream promotion (`chunk-6y1jd448.js@320500`, `@327500`).
Recoverable stream drops bypass common `Client.onclose` until terminal end;
server replay and pending-response retention across reconnect remain unresolved
or inferred. Status stays `PARTIAL`.

The local permission continuation also resolved the terminal local-JSX handoff:
`kg` is the `local_jsx` schema, `Aee.show()` allocates and retains
`local-jsx-N` nodes, `Hst` looks them up through `LocalJsxRegistryContext`,
and the main screen supplies the active registry (`chunk-gpztfb1a.js@765`,
`chunk-9w4htdvs.js@174417`, `@1291149`, `@1309973`). The dynamically supplied
node implementation and focus/keyboard behavior remain unknown. REA's exact
`local_jsx` trace returned no match in its partial graph and is retained only as
a tooling limitation (`ev_b8e1b52540bb402bb34f41c609f11e01badb1cd60a9c99e751cf9194c4c44660`).

The next permission pass resolved the generic interactive approval renderer:
`HAe` defines the `permission_prompt` contract, `QO` builds its payload,
`pMr` constructs allow/deny/rule/auto choices, `L9` and the shared `Ve` selector
handle focus, keyboard, feedback editing, and Escape, and `nE` tracks refused
answers/default focus (`chunk-cvvnq4he.js@478598`,
`chunk-57pw7ky5.js@13560`, `chunk-bqb9mv4b.js@35151`, `@37769`, `@54618`,
`chunk-75p1g95y.js@40861`, `chunk-rcjkw193.js@672`). Specialized dialog bodies
and cross-kind focus arbitration remain open. REA's exact `permission_prompt`
trace returned no match in the partial graph and is retained only as a
limitation (`ev_3ff626107390b879aace906fd974ad13c2b4c2d7fa421575a8d5570ac1ab0826`).

The file-operation specialization was then traced through `iWe` and `ort`:
`Ont` constructs accept-once/session-grant/reject/outside-read options and
`lho` maps them to allow, deny, permission updates, and outside-read flags
while reusing the shared selector (`chunk-57pw7ky5.js@22460`,
`chunk-9w4htdvs.js@1241629`, `@1249278`, `@1251327`). Other specialized
permission families remain at registry/dispatch depth only.

The web-fetch specialization is now resolved through `iBt` and `Vke`:
`qrt` maps yes/no/domain-grant selections, `$rt` constructs the
`domain:<hostname>` rule, and `Qrt` applies safety/classifier, organization-cap,
hostname, and withheld-URL gates (`chunk-57pw7ky5.js@33506`,
`chunk-9w4htdvs.js@1282875`, `@1283167`, `@1283713`, `@1283914`). Remaining
specialized permission families are still only partially traced.

The skill specialization is also source-resolved through `sBt` and `Wke`:
`Mrt` maps yes/no/exact/prefix choices, `Irt` and `Ert` construct exact and
validated `${prefix}:*` rules, and cancel maps to deny. The branch reuses `L9`
feedback and the common permission transport (`chunk-57pw7ky5.js@33238`,
`chunk-9w4htdvs.js@1278093`, `@1278805`, `@1279317`, `@1280237`).

The PowerShell branch is now source-resolved through `oBt` and `Trt`:
`krt` constructs normal/suggestion/edited-prefix options, `p6` maps them to
allow/deny/update results with feedback, command parsing refines prefix
suggestions, and Escape maps to deny (`chunk-57pw7ky5.js@32959`,
`chunk-9w4htdvs.js@1267767`, `@1270916`, `@1271495`).

The monitor branch is now source-resolved through `rBt` and `Fke`: command,
MCP-poll, and WebSocket action shapes are rendered with withheld-content
guards; `prt` builds bounded suggestions, `mrt` maps allow/deny/update results,
and cancellation maps to deny (`chunk-57pw7ky5.js@32680`,
`chunk-9w4htdvs.js@1258368`, `@1259097`, `@1259921`, `@1260091`,
`@1260316`).

The registered permission-panel pass now closes three additional renderer
bodies. `Yke` maps `ZJe` to the bash panel `Jtt`, `eBt` to the browser/Chrome
panel `Ywe`, and `tBt` to the plan-entry panel `oke`
(`chunk-9w4htdvs.js@1293453`). `Jtt` combines command withholding, sandbox
and destructive-warning state, standing-prefix/backend suggestions, and
optional auto-mode enablement; `Ywe` supports withheld URLs and an eligible
session host grant, with Escape returning cancelled; `oke` checks the refusal
epoch and answerability, records `tengu_plan_enter`, changes the mode to
`plan`, and maps its implementation-now choice to deny
(`chunk-9w4htdvs.js@1200505`, `@1206666`, `@1216982`, `@1199853`,
`@1216742`). Cross-kind focus/host arbitration and dynamically supplied
local-JSX node behavior remain unresolved.

The permission UI gap is narrowed again at the display-host layer. `_v`
selects the user/non-user request for the active surface; `nCe` derives hidden
reasons; `rCe` suppresses buried non-user panels while a user-invoked request
is present; `sCe` tracks shown/displaced timestamps; and `iCe` verifies the
request id and payload before allowing an answer or dismissing an unavailable
component. `HO` bridges transport subscription, updates, cancellation, store
closure replies, and unmount cleanup (`chunk-9w4htdvs.js@1320735`,
`@1322913`, `@1323202`, `@1323852`, `@1324180`, `@1326466`). Final keyboard
focus selection and host-versus-remote answer ordering remain UNKNOWN.

The MCP race pass now resolves the registry-side replacement boundary. `mfe`
closes and drops late connection settlements when app/dynamic config identity
or account-switch epoch no longer matches; `ne` refuses a re-queried tool list
when another server owns the name and retains pending-client results in a
WeakMap; `kDo` registers one guarded `tools/list_changed` handler per connected
client and keeps the previous listing after a failed refresh
(`chunk-0nh75v9f.js@3225`, `@13379`, `@13974`). This still does not prove that
registry removal aborts an already-running MCP call.

The follow-up MCP caller pass exact-scanned every extracted `chunk-*.js` file.
It resolves six literal `mfe` consumers (account-switch, reconnect, generic
controller, two bridge mounts, and the local wrapper), two MCP `ne` refresh
calls, two `pi` wrapper consumers, and the `kDo` lifecycle setup
(`chunk-0nh75v9f.js@7555`, `@10400`, `@12046`, `@14776`,
`chunk-2pkntkhf.js@23047`, `chunk-fzzrkchm.js@382970`, `@504690`, `@506239`,
`@508488`, `@509441`, `chunk-td0hhs53.js@3801`). The result is exhaustive for
literal token references in the extracted chunks, not for aliases, string
dispatch, host callbacks, or dynamic imports; the dynamic-caller area remains
`PARTIAL`.

The next concurrency pass resolved the precompute overlap boundary. `AXr` is
called without awaiting after automatic-compaction preparation and after an API
response (`chunk-93pksqr2.js@140102`, `@174008`); it creates a separate abortable
summary/hook job and stores a pending `settled` promise
(`chunk-phacttch.js@2611137`). `PXr` later joins that promise through
`Mcr`/`xXr` or returns a structured abort outcome (`@2616746`, `@2618033`).
The `tqt` compaction adapter streams compact events, but the complete `pir`
body uses its notification callback only after a skipped result
(`chunk-phacttch.js@857724`, `@2518310`). This narrows the notification-during-
compaction race while leaving arbitrary host/queue callback injection open.

The notification-to-next-request boundary is now source-resolved. The main
turn `_runImpl` overrides the ordinary pending-record callback with
`Eo.stopsLoopForPending()`, the query loop checks it before request setup, and
a pending `defer-then-fork` gesture returns `background_requested` so the
background fork can take ownership. A non-empty draft cancels the suppression
under `tengu_keen_sloth`; normal turn cleanup clears the pending gesture
(`chunk-9w4htdvs.js@108462`, `@117617`, `@1395543`, `@1408892`, `@1413024`,
`chunk-93pksqr2.js@134246`). REA property tracing returned a partial zero-match
cross-check (`ev_14ec941b9a0d3543307d717ce6ca928665c2094771f6a20153a130b515d0d57a`),
which is recorded as a graph-coverage limitation rather than a negative source
finding.

The concurrent permission-request gap is narrowed at the registry level. The
shared `eS` ask registry retains one block per `toolUseID`, assigns an
`opened` sequence, honors explicit `order`, prefers `onTop` requests, and
recomputes the visible block after open/close (`chunk-phacttch.js@2931335`,
caller `chunk-57pw7ky5.js@51135`). Final renderer focus remains unresolved;
REA's `openAsk` property trace was partial with zero matches and is recorded as
a tooling limitation (`ev_5e1c0cdeb0b9a724748fe26c97dd701ded59f5e151f8e67dcf64ec752b41e993`).

The MCP pending-call branch is narrowed: the v2 `ao` wrapper records request
ids as `sent`/`taken`, refuses to resend after a connection close or ambiguous
sent-POST failure, and returns a correlated `downstream_unreachable` error;
task-capable calls separately send `tasks/cancel` after abort
(`chunk-9158d2ng.js@176700`, `@182461`). The SDK client closure boundary is
also recovered: `connect()` wraps transport callbacks and `_onclose()` rejects
all pending response handlers with `ConnectionClosed`, clears timers/progress,
and aborts inbound handlers (`chunk-6y1jd448.js@100162`, `@100736`, `@101233`).
The base stdio close/dispose timings and the bounded unconnected-child reaper
are recovered (`chunk-9158d2ng.js@19308`, `@20196`, `@26410`;
`chunk-tem5x312.js@6146`, `@6251`, `@6379`, `@6840`). The custom WebSocket
transport and manager are now also traced: socket close reaches the SDK
pending-call settlement and removes the connection/listing caches, while a
socket error alone is forwarded without settlement
(`chunk-tem5x312.js@2933`, `@3539`, `@4021`, `@4613`, `@4720`;
`chunk-9158d2ng.js@79789`, `@80238`, `@103774`, `@107057`). SSE/HTTP
reconnect/stream-retention timing, native WebSocket timing, and pre-dispatch
disappearance coupling remain open. REA's exact `SIGKILL` and
`mcp_websocket_message_fail` traces had no matches on the partial graph
(`ev_e626beeb8c210f25110d3c5c1ebb8d4323c3fab70e9c23b5fd233d4d6aab7850`,
`ev_f0321c072f61dfd1be330f00b29807c711f700ec9a18acaef711c00a1b61ad14`),
which are recorded as coverage limitations rather than negative findings.

The local batch/compaction boundary is narrower than the global race question:
`Zo` is consumed to completion by both the ordinary `rn` caller and deferred
`Eqo` before either returns to the query-loop request/compaction phase
(`chunk-jwmqjyrb.js@28129`, `@52813`, `@72140`). Its defining asset does not
export `Zo`, and the complete export list/exact-token scope contains no other
alias or callback caller (`chunk-jwmqjyrb.js@148486`). This is a caller-scoped
`VERIFIED-STATIC` no-overlap bound for extracted JavaScript; detached, host/eval,
and remote paths remain unresolved. REA's `turnStartToolRun` trace was partial with no property
match and is retained only as a tooling limitation
(`ev_26d892a6e46bafad5fde97b69ef12f1d0ec444c969e1fdea0f5c6860a2fc3cf0`).

The notification-to-model path now has a verified positive edge as well as the
stop edge: after the main query gate and setup/context checks, the API loop
assigns `I.callModel` and consumes `Ca(...)` (`chunk-93pksqr2.js@153755`). This
shows when an admitted detached notification can produce another model request;
it remains conditional and does not prove that every task notification requests
the model.

The persistence/hydration caller boundary was tightened by an exact-token pass:
`rQr` has one extracted-JavaScript call site (`chunk-fzzrkchm.js@681312`), one
facade export (`chunk-1stv0pyw.js@18425`), and its defining body
(`chunk-phacttch.js@4614350`). The transcript owner has three literal
`this.persistToRemote(...)` call sites (`chunk-phacttch.js@4589794`, `@4589831`,
`@4589897`); the internal-writer body invocation is at `@4591557`. This is
exhaustive for literal references in the extraction, not for dynamic method
references or host/provider callbacks.

The final permission-decision caller was also narrowed: exact-token inspection
finds `aBt` invoking `JQo` at `chunk-57pw7ky5.js@5939`; `JQo` remains defined
and records the normalized decision at `chunk-phacttch.js@1881907`. Specialized
dialog/focus and host-versus-terminal arbitration remain separate open edges.

The local permission store is now narrowed at the visible-state boundary:
`ik` selects the latest non-user dialog, `Sie` selects the latest user-invoked
dialog, and `PLr` publishes only when either visible selector changes. Closing a
top same-class request marks the predecessor with `shownAt` and increments
`revealSeq` (`chunk-gq0v7nj7.js@1100`, `@2747`). REA's property trace for
`closedBlockingTopBare` was partial with no match and is recorded as a tooling
limitation (`ev_ece799b26112ebfed5071182c776933afe1ba05ae932dcec09dd95264e597274`).

Earlier priority gaps include the failure breaker on the non-reactive route,
non-reactive prompt-too-long handling and partial compaction, `auto` permission mode with a real classifier
(the flow is verified with a scripted classifier), background-agent survival under TUI Esc, supervisor worker
respawn execution, authenticated PTY success and independent input-forwarding rejection, sandbox enforcement
(blocked: `sandbox status` reports unsupported on this host), and a direct-path request dump. Other partially
verified rows still have narrower gaps, including the single-variable `availableModels` check, external-include
approval, retry caps, cross-directory resume, and the complete renderer/dialog harness. The heartbeat
worker lifecycle and parent-watchdog message are runtime-verified in `runtime-logs/worker-lifecycle/summary.json`;
the watchdog worker exit status was not captured. A daemon-managed unauthenticated PTY client produced an
`auth-required` response, recorded in `runtime-logs/pty-auth/summary.json`; marker absence is not independent
proof of input rejection. E92 attempted one model POST and received 401, so no model turn completed. Scheduled
and remoteControl workers remain OAuth-gated. E35 to E37 ran 25 failed compaction operations in one process on
the reactive route with no breaker; the non-reactive route was never reached.

## Tooling (all under `tools/`)

- `pe_inventory.py`, `bun_probe.py`, `bun_extract.py`: PE + Bun module-graph extraction.
- `chunk_index.py`, `cq.py`: export/import index and bounded search over extracted chunks.
- `capture_proxy.mjs`: logging forward proxy (`ANTHROPIC_BASE_URL`), credential values never stored, fault injection via `fault.json`, and scripted model replies (`sequence`, `scripted_response.mjs`) that need no upstream call.
- `run_gates.sh`: the whole local gate lane in one command. `sync_counts.py` rewrites run counts quoted in the prose from the manifest; `check_matrix.py` checks the matrix footer against its rows.
- `run_exp.py`: one instrumented `claude -p` run. `summarize_captures.py`, `hooks_summary.py`, `show_exp.py`: sanitized evidence + views.
- `lab_batch1.sh`, `lab_batch2.sh`: experiment batches. Lab projects live in `C:\Users\<user>\cc-rea-lab\`.

## Slim experiment profile (cost control)

Default config on this machine sends 206 tools and ~258k cached tokens per first request
(E01: one word answer, notional cost 2.06 USD on Opus). Experiments therefore run with
`--model haiku --setting-sources project,local --strict-mcp-config --mcp-config empty-mcp.json`
(26 tools, ~36k tokens, ~0.002 to 0.008 USD per run). `--model haiku` alone was ignored under
user settings (E01: `availableModels` in user settings does not list a haiku id; the request
used the settings model). Status: partially verified (E01 vs E01b, not a single-variable run); see `06-verification-matrix.md` row 17.

## Verified runtime findings so far

1. Artifact: `claude` resolves to one PE, Bun standalone, `.bun` section holds 2,586 modules; entry `cli`. (static)
2. Transport: `POST /v1/messages?beta=true`, streamed SSE, preceded by `HEAD /api/hello`. Headers and body keys in `E01-simple/http-summary.json`.
3. Request body keys: model, messages, system, tools, metadata, max_tokens, thinking, context_management, output_config, stream. `metadata.user_id` is a JSON string with keys account_uuid, device_id, session_id.
4. System is 3 text blocks: billing header line (uncached), identity line (cache 1h), main prompt (cache 1h).
5. First user message carries reminder blocks ahead of the prompt: instruction files, context (date etc.), attribution, then the user text.
6. `messages` contains `role: "system"` entries mid-conversation (environment block after the first user message; lazily loaded nested CLAUDE.md after a Read in that subdirectory, E08).
7. Cache breakpoints move: the last block of the newest message carries `cache_control` (E08 msg[2] last tool_use, msg[4]).
8. Streaming tool execution: tool results are produced while the assistant stream is still open (E08: `user` tool_result events interleave with later `content_block_start`).
9. SDK stream emits one `assistant` message per content block, before `content_block_stop`.
10. Parallel tool calls: three tool_use blocks in one assistant message, three tool_results merged into one user message (E08).
11. Headless default mode: an `ask` decision becomes a denial with `is_error: true` tool_result, a `system/permission_denied` event, and an entry in `result.permission_denials`; the loop continues and the run still ends `success` (E06, E06b).
12. Bash path safety: `ls /outside` denied even with `Bash(ls:*)` allowed (E05).
13. Hook order for a tool: all matching PreToolUse hooks start in parallel (same ms), tool waits for the slowest, then PostToolUse, then result (E07a). Session order: SessionStart, InstructionsLoaded, UserPromptSubmit, [PreToolUse, PostToolUse]*, Stop, SessionEnd.
14. PreToolUse `permissionDecision: deny` blocks the tool, counted in permission_denials (E07b). Exit 2 blocks with stderr fed to the model (E07c). Exit 1 is non-blocking (E07d).
15. PreToolUse `allow` skips the permission prompt in default mode (E07e) but a `deny` rule wins: the denied tool is removed from the session entirely ("No such tool available", E07f).
16. PreToolUse `updatedInput` rewrites the command that runs; the model still sees its original tool_use (E07g).
17. Stop hook `decision: block` re-enters the loop with a synthetic user message "Stop hook feedback: ..." and the second Stop has `stop_hook_active` (E07h).
18. Rule precedence observed: deny > ask > allow for Bash prefix rules; Read deny rule on a path blocks via tool validation (E08b).
19. Real API failure captured: 429 session limit ends the run with `is_error: true`, `terminal_reason: api_error`, exit code 1, and a synthetic assistant text (E08b tail).
20. Compaction fault targeting: a literal request-body marker distinguishes summary calls from normal `/v1/messages` turns in the lab proxy (E28b, E30, E31).
21. Automatic summary failure: eleven injected 529 HTTP attempts (one initial attempt plus ten retries) exhaust one `source=compact` operation, then `Reactive compact: summarization returned API error` and `session.compact` hook failure occur; no failure-breaker event was observed (E31).
22. Evidence tooling now digests arbitrary error/non-JSON/SSE error text, structurally summarizes request and run metadata, accepts mixed SSE line endings, tolerates incomplete frames, retains explicit late breaker signals without raw message text, preserves injected SSE capture metadata/body, validates malformed fault matcher fields, and closes capture streams on cancellation.
23. E32b used the local OAuth store and reached a real upstream 429 after `HEAD /api/hello`; the account was still rate-limited, so no further live breaker experiments were run.
24. E46 covered 13 hook event types in one scripted session and accepted a default-mode `PermissionRequest` allow; E47 showed that a non-deciding PermissionRequest hook leaves a dangerous headless Bash call denied. Across sanitized hook logs, 17 of 33 event types have been observed.
25. A pinned 2.1.296 daemon help/status probe verified the on-demand lifecycle text and the disabled service-install path; status showed no running daemon and zero workers. `claude --bg --help` unexpectedly started a background session and was stopped immediately; later direct `--bg` attempts were blocked first by `--print` incompatibility and then by workspace trust. E82 then launched a trusted disposable background session, observed one `background` row in `blocked/idle`, and removed it with `stop` plus `rm`; E83 started `claude attach` against a live registry entry, observed attach output, and cleaned it; E84 stopped and respawned a session successfully, observing `working/idle`, then cleaned it; E85 received 7,303 PTY bytes including ANSI control bytes through attach. The spare pool is statically disabled on Windows. A heartbeat worker was launched with valid stdin and a Node IPC channel, emitted startup and heartbeat output, accepted `shutdown`, and exited 0; a second worker reached the parent-watchdog path and emitted `parent supervisor gone - exiting`. A daemon-managed unauthenticated PTY client then connected, received `auth-required`, and did not reflect its marker in host-to-client terminal frames. Valid worker kinds and invalid-kind handling remain recorded. A direct scheduled-unavailable worker probe returned exit 78; supervisor respawn execution remains untested. E92 attempted one model POST and received 401; no model turn completed.
27. A second source-level pass read the daemon supervisor loop `Mt`, bg manager `Pt`, worker class `Ke`, auth manager `Y$o`, the stubbed Windows service module, the renderer diff engine `Zd` and patch optimizer, the kept-bytes path, the `transcriptFrontCutRows` producer (message list `$w` in `chunk-f0h0v7h4.js`), and the key/kitty decoder tables. Everything is `VERIFIED-STATIC`; none was executed. A cold review of that pass found 13 defects (mostly wording and offsets), all checked against source and fixed. A third pass then read tokenizer `KSe`, the terminal reply classifier `By` and startup probe `Vv`, and the print-mode output path (`runHeadless` output formats, text writer `Ig`, exit code), in the last section of `static-05-subagents-sessions-rendering.md`. Still unread: macOS aqua wrap internals, the `json` stringify helper, the `VL` generator body beyond the existing loop notes, much of the unread minified module graph, and macOS/Linux service install bodies (absent from this build).
26. A fresh source-level pass read the daemon supervisor, worker registry, worker entrypoints, PTY framing/host/client, spare guards, renderer pacer, raw-input dispatch, Escape routing, and local/remote permission cancellation. The new static contracts and exact anchors are in `static-05-subagents-sessions-rendering.md` and `04-internal-contracts.md`; runtime reachability, OS signal timing, native terminal behavior, and end-to-end Esc cancellation remain unverified.

## Incidents

- Five parallel Opus static-sweep agents exhausted the account's 5-hour session limit. Four had
  already written complete reports; the fifth was resumed after the reset.
