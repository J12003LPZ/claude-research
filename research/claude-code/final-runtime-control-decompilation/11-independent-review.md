# Independent review and validation

Status: `PARTIAL` — mechanical and cold source review completed; an independent
second-agent semantic review was not available and was not delegated because
the mission explicitly prohibits subagents.

## Review performed

The authoring pass was followed by a separate read-only validation pass that:

1. reran `audit_static_citations.py` against every new Markdown report;
2. checked the JSON companion with PowerShell `ConvertFrom-Json`;
3. inspected the previous wake report and added an explicit correction rather
   than leaving the contradicted wording in place;
4. checked that every new report uses a confidence/status label and names open
   branches instead of promoting them to facts;
5. compared the wake, concurrency, MCP, Storage, permission, and callgraph
   claims against the cited extracted-module regions;
6. confirmed no installed executable, authentication store, or extracted
   proprietary source was modified.

## Review findings

| Finding | Result |
|---|---|
| New Markdown source citations | 1184/1184 resolvable across the final-runtime-control and remaining-subsystems report sets |
| Missing citation chunks | 0 |
| Out-of-bounds offsets | 0 |
| JSON syntax | valid |
| Unsupported universal wake claim | corrected; local idle/open wake is bounded and conditional |
| Runtime label applied to new static wake edge | none |
| V1 `hydrateRemoteSession` body | recovered at `chunk-phacttch.js@4614350`; dynamic/host callers remain bounded |
| Storage backend transaction guarantee | retained as UNKNOWN; injected provider boundary, default no-provider factory, and record-level preconditions are now verified (`chunk-8qnn2dw7.js@816`, `@1541`; `chunk-we7c2g4z.js@5566`, `@5810`) |
| MCP post-send cancellation | wrapper/stdio cancellation recovered; transport-specific SDK settlement retained as UNKNOWN |
| Full dynamic caller enumeration | retained as UNKNOWN/PARTIAL |
| Persistence/hydration literal caller enumeration | `rQr` has one extracted-JavaScript call site plus facade export/body; `persistToRemote` has three literal transcript-owner call sites; dynamic method/host callbacks remain UNKNOWN |
| Remote-served background-shell completion | scoped non-notifying local contract verified; broader remote/daemon wake remains UNKNOWN |
| Local JSX renderer boundary | `kg` schema, `Aee` producer, `Hst` lookup, and main-screen provider verified; dynamically supplied node/focus implementation remains UNKNOWN |
| Generic permission renderer | `HAe` schema, `QO` builder, `pMr` choices, `L9`/`Ve` selection, `Uwe` feedback, `nE` refusal state, and shared selector focus/key handling verified; specialized/cross-kind arbitration remains open |
| File permission specialization | `iWe` schema, `ort` preview, `Ont` option construction, and `lho` result mapping verified |
| Bash/browser/plan permission panels | `Yke` registry maps `ZJe→Jtt`, `eBt→Ywe`, and `tBt→oke`; bodies, option/result mapping, cancel behavior, and plan-mode transition were re-read at `chunk-9w4htdvs.js@1200505`, `@1206666`, `@1216982`, `@1199853`, `@1216742`, and `@1293453`; cross-kind focus and host arbitration remain open |
| Display-host arbitration | `_v` selects the mounted request, `rCe` suppresses buried non-user panels, `iCe` rejects missing/changed payloads before answering, and `HO` tears down transport/store state (`chunk-9w4htdvs.js@1320735`, `@1323202`, `@1324180`, `@1326466`); cross-kind focus and remote answer ordering remain open, while the shared `Ve`/`Yi` primitive is source-backed |
| MCP registry race pass | `mfe`, `ne`, and `kDo` were re-read directly: config/account-epoch mismatches close late clients, server-name ownership prevents stale list publication, and `tools/list_changed` refreshes are client/config guarded with keep-previous failure behavior (`chunk-0nh75v9f.js@3225`, `@13379`, `@13974`); in-flight call cancellation remains unproven |
| Web-fetch permission specialization | `iBt` schema, `Vke` renderer, `qrt` result mapping, `$rt` domain rule, and `Qrt` safety/org/hostname gates verified; REA literal trace remains partial |
| Local transcript drain/exit ordering | per-owner drain chain, chunk cap, store fence, multi-pass flush, and bounded exit/re-stamp windows verified; provider commit/crash durability remains UNKNOWN |
| Fallback remote ingress ordering | keyed per-session serialization, `Last-Uuid` high-water handling, duplicate-409 success, conflict adoption/refetch, bounded retry, and auth stop verified; injected writer semantics remain UNKNOWN |

## Independent-review limitation

The requested independent reviewer could not be run in this continuation: the
user explicitly said not to use subagents, and the earlier delegated attempts
also failed with provider usage-limit errors. This report is therefore not a
claim of independent semantic approval. The mechanical validator proves only
anchor existence; it does not prove that every paragraph is semantically
correct. The final status remains `PARTIAL` for that reason as well as for the
unresolved source branches.

## Open review concerns

1. `chunk-fzzrkchm.js` function-level conclusions were read directly from the
   extracted source, but REA semantic analysis for that module was unavailable
   in the focused result.
2. The V1 `hydrateRemoteSession` body is now recovered, but remote replay,
   conflict, and any differently aliased callers remain open.
3. The Storage V5 provider may be supplied at a host boundary not represented
   in the JavaScript graph.
4. The source-level wake edge has not been re-exercised by a new runtime run,
   per the no-new-experiment constraint.
5. REA semantic tracing of `requestDialog` returned a partial graph with no seed
   match; this is recorded as a tooling limitation, not a negative source
   finding (`ev_56df6fd325aba78e6bd21f20817618ee8ffa1a6d2192ef13060ed92a0788b872`).
6. REA semantic tracing of property `JQo` likewise returned no seed match in a
   partial graph; the direct caller was then resolved independently by exact
   extracted-source token inspection to `aBt` at `chunk-57pw7ky5.js@5939`.
   The REA miss remains a tooling limitation, not a negative source finding
   (`ev_2386e849ef3ce63ea10ad45aed5b52210d46fe69893d57e0d93a154f76865fb4`).
7. A retained-analysis summary projection reconfirmed the application scope:
   2,344 JavaScript files parsed, with partial application/semantic coverage
   and explicit unknowns (`ev_9c05af955cba36c5b60e3ab4e783fca0d7bfc8c1d6370ea2d5c716777c1d2eca`).
8. The attached-host `cd` self-wake controller was independently re-read in
   the extracted module (`chunk-fzzrkchm.js@97910`); its presence narrows the
   former “external wake” gap but does not establish process-exit or
   remote-session wake.
9. The remote-served shell executor and per-caller registry were re-read in
   `chunk-bsjqfd0a.js@35653`, `@37213`, `@39490` and
   `chunk-qwgyf6qf.js@4678`, `@5543`. They settle/record the remote shell and
   append the exported `KHo` non-notification guidance rather than enqueueing
   the local task-notification path. This is a scoped static conclusion, not a
   universal claim about daemon or remote transport wake behavior.
10. The scheduled-loop and resume-reconciliation paths were re-read at
    `chunk-e1qepm02.js@2208`, `@3481`, `@3775`, `chunk-zdvza25y.js@18210`, and
    `chunk-rrep227n.js@43003`, `@49606`, `@62600`. The overdue-loop branch is
    informational (`shouldQuery:false`), and orphan-agent restart is caller-
    dependent; neither proves that a dead process is externally woken.
11. REA exact-seed tracing for `sleep-auto-resume` returned no match in the
    partial graph (`ev_97c2bc819287f6679c0f79a1886e7193dc0a3a03431d3972f0c7e4524cbe71ba`).
    This was recorded as a limitation, not as a negative source finding.
12. REA exact-seed tracing for `local_jsx` likewise returned no match in the
    partial graph (`ev_b8e1b52540bb402bb34f41c609f11e01badb1cd60a9c99e751cf9194c4c44660`).
    The extracted bundle independently resolves the schema and renderer
    handoff at `chunk-gpztfb1a.js@765`, `chunk-9w4htdvs.js@174417`,
    `@1291149`, and `@1309973`; the REA miss is only a coverage limitation.
13. REA exact-seed tracing for `permission_prompt` likewise returned no match
    in the partial graph (`ev_3ff626107390b879aace906fd974ad13c2b4c2d7fa421575a8d5570ac1ab0826`).
    Direct bundle tracing resolves the generic descriptor and renderer at
    `chunk-cvvnq4he.js@478598`, `chunk-57pw7ky5.js@13560`, and
    `chunk-bqb9mv4b.js@54618`; the graph miss is not a negative finding.
14. REA exact-seed tracing for `yes-dont-ask-again-domain` returned no match in
    the partial graph (`ev_9841b75a43e75194beaedae36296cf50f0b4f81e0cc74b16badef1be07a49d17`).
    Direct bundle tracing resolves the web-fetch result mapper and domain-rule
    guards; the REA miss remains a coverage limitation.
15. REA exact-seed tracing for `permission_skill` returned no match in the
    partial graph (`ev_99bb7528aa36185b351542a59e417a76aaa37f7dc36dad4839702afdc36b9df8`).
    Direct bundle tracing resolves the skill renderer, exact/prefix rule
    policy, and deny-on-cancel behavior; the REA miss remains a coverage
    limitation.
16. REA exact-seed tracing for `permission_powershell` returned no match in the
    partial graph (`ev_6b171e1b7c4711338994356d61d184e1ff966beabf1dea488a8ca1b8cc8f5b7e`).
    Direct bundle tracing resolves command display/sandbox/suggestion handling,
    result mapping, and deny-on-cancel behavior; the REA miss remains a
    coverage limitation.
17. REA exact-seed tracing for `permission_monitor` returned no match in the
    partial graph (`ev_c281f7a9a5a86c6a39f997106126aac6eba2c67023d7e9effd5e0b37c4bd4da0`).
    Direct bundle tracing resolves command/MCP/WebSocket display, suggestion
    guards, result mapping, and deny-on-cancel behavior; the REA miss remains
    a coverage limitation.
18. The stop-before-request boundary was re-read in both the query loop and
    its host turn controller. `_runImpl` overrides the weaker pending-record
    callback with `Eo.stopsLoopForPending()` at
    `chunk-9w4htdvs.js@1413024`, while the query loop checks it before request
    setup at `chunk-93pksqr2.js@134246`. The pending gesture constructor and
    draft exception were checked at `chunk-9w4htdvs.js@108462` and
    `@117617`; REA's property trace returned a partial zero-match result
    (`ev_14ec941b9a0d3543307d717ce6ca928665c2094771f6a20153a130b515d0d57a`),
    so the static source read is authoritative for this claim.
19. The concurrent permission-request gap was narrowed by re-reading the
    shared `eS` registry at `chunk-phacttch.js@2931335` and its `Ie` caller at
    `chunk-57pw7ky5.js@51135`. The registry's per-tool-use map, explicit order,
    `onTop` preference, and visible-block recomputation are source-backed;
    final renderer focus remains open. REA property tracing for `openAsk`
    returned a partial zero-match result
    (`ev_5e1c0cdeb0b9a724748fe26c97dd701ded59f5e151f8e67dcf64ec752b41e993`),
    which is a graph-coverage limitation rather than a negative finding.
20. The MCP already-written-call branch was re-read at
    `chunk-9158d2ng.js@176700` and `@182461`. The wrapper records `sent` and
    `taken` request states, refuses to resend after close/no-answer, and emits
    a correlated `downstream_unreachable` error. The remaining unknown is
    transport-specific event translation, not silent duplicate retry.
21. The local batch/compaction boundary was re-read in the complete relevant
    bodies of `Zo`, `rn`, and `Eqo` at `chunk-jwmqjyrb.js@28129`, `@72140`, and
    `@52813`. Those callers await the async generator to completion before
    returning to the query-loop phase, which supports a scoped no-overlap claim;
    it does not prove a global claim for detached, dynamic, or host work. REA's
    `turnStartToolRun` property trace was partial with no match
    (`ev_26d892a6e46bafad5fde97b69ef12f1d0ec444c969e1fdea0f5c6860a2fc3cf0`),
    so it is recorded as a coverage limitation.
22. An exact REA trace for the MCP no-resend literal returned a partial graph
    with zero matches
    (`ev_721246d2f78d0d6c5629893d4f57b837309ca22e190f4839d7193a8d1283970a`).
    The direct bundle read at `chunk-9158d2ng.js@176700` and `@182461` remains
    the source-backed basis for the settlement claim; the REA result is only a
    recorded coverage limitation.
23. The positive notification-to-model edge was re-read at
    `chunk-93pksqr2.js@153755`. The query API loop assigns `I.callModel` and
    consumes it through `Ca` only after the earlier stop/setup gates; the report
    therefore states a conditional handoff and does not claim unconditional
    automatic requests.
24. The permission dialog store was re-read at `chunk-gq0v7nj7.js@1100` and
    `@2747`. Its `ik`/`Sie` visible selectors, subscription change test, and
    same-class `shownAt`/`revealSeq` promotion are source-backed. REA's
    `closedBlockingTopBare` property trace was partial with no match
    (`ev_ece799b26112ebfed5071182c776933afe1ba05ae932dcec09dd95264e597274`).
    A subsequent direct read resolved the shared selector primitive: `Ci`,
    `HYn`, `Di`, and `Yi` implement navigation, focus state, commit, and
    focus/blur wiring (`chunk-75p1g95y.js@31583`, `@38136`, `@39814`,
    `@40861`), with focus reclamation in `Fh` (`chunk-pb1e761e.js@21952`).
    The remaining gap is cross-kind/host arbitration, not the selector's
    basic keyboard primitive.
25. The previously open `JQo` caller edge was re-read through the complete
    `aBt` body and its extracted call sites. `aBt`'s `D` closure invokes
    `JQo` (`chunk-57pw7ky5.js@5872`, `@5939`); the normal `pdt` handler creates
    it (`chunk-9w4htdvs.js@1506615`), and the in-process teammate `Qe` passes
    `He` to `vC`, where `He` creates it again
    (`chunk-tzyj6m5p.js@18175`, `@3266`). The JSON callgraph now records these
    direct edges; only dynamically retained host/provider references remain.
26. The storage continuation proves local queue and exit ordering, but not
    provider commit durability or cross-key transactions; the new report text
    keeps those as UNKNOWN (`chunk-phacttch.js@4562282`, `@4572755`,
    `@4553729`, `@4565155`).
27. The fallback remote writer's UUID conflict recovery is source-backed, but
    the injected internal-event-writer's acknowledgement/replay behavior and
    V1 replacement race remain open (`chunk-phacttch.js@42342`, `@4590886`,
    `chunk-sy9frekf.js@3491`).
28. The injected writer boundary was re-read through both setup callers. The
    bridge adapter at `chunk-2kr6zq6e.js@30760` returns an already-resolved
    promise after launching `ne(...)`; the CCR v2 adapter at
    `chunk-cest8dre.js@52700` awaits queue admission, while physical
    `/worker/internal-events` acknowledgement is later in the uploader at
    `chunk-a5wd77pa.js@39222` and the explicit drain is
    `flushInternalEvents` at `@82970`. The prior broad wording “awaits the
    remote writer” was corrected to “awaits an adapter-dependent callback
    return”; server durability and bridge-side completion remain open. REA's
    `writeInternalEvent` trace was partial with zero matches
    (`ev_b8a760d603a7f09ee2d8242fcf109f8ebf55171aa0b72146b9bba5a355064a3d`),
    so direct bundle anchors remain authoritative.
29. The bridge callback was traced one level farther. `a5o` constructs `S` via
    `k3r`, obtains `S.getInternalEventWriter`, and passes the wrapper `v` into
    the persistence callback; `k3r` exposes `F.writeInternalEvent`
    (`chunk-tar8k6v4.js@43925`, `@78732`, `@79043`;
    `chunk-a5wd77pa.js@125745`, `@130515`). The bridge adapter still invokes
    `ne` without awaiting it (`chunk-2kr6zq6e.js@29677`, `@30760`), so the
    correction is to narrow the unresolved issue to caller observation and
    server durability, not to claim that CCR v2's writer identity is unknown.
    REA's incoming `getInternalEventWriter` trace returned a partial zero-match
    result (`ev_4984b4ce6342dca35d115cba83b88938821de1a1d72b137cd406e5e2cb9b17f3`),
    which remains a graph-coverage limitation.
30. The MCP stdio transport and bounded subclass were re-read directly. The
    base transport's `close()` and `_dispose()` have distinct escalation
    timings and both clear the read buffer; stderr is only exposed through a
    PassThrough, not converted here into a tool result
    (`chunk-9158d2ng.js@19308`, `@20196`). The bounded subclass arms a
    one-shot exit reaper, with Windows stdin-close/process-tree cleanup and
    non-Windows SIGINT/SIGTERM/SIGKILL escalation
    (`chunk-9158d2ng.js@26410`; `chunk-tem5x312.js@6146`, `@6251`, `@6379`,
    `@6840`). An exact REA `SIGKILL` trace returned a partial zero-match result
    (`ev_e626beeb8c210f25110d3c5c1ebb8d4323c3fab70e9c23b5fd233d4d6aab7850`),
    so it is recorded as a coverage limitation and not as a negative finding.
31. The SDK client boundary was re-read in `chunk-6y1jd448.js`. `connect()`
    wraps transport callbacks; `_onclose()` rejects all pending response
    handlers with `ConnectionClosed`, clears timers/progress, aborts inbound
    handlers, and invalidates the transport, while `_onerror()` only forwards
    errors (`@100162`, `@100736`, `@101233`). SSE and Streamable HTTP close
    paths were checked for controller abort and `onclose` dispatch
    (`@315922`, `@319109`, `@320990`, `@328757`, `@328935`). This closes the
    common SDK settlement gap but leaves reconnect timing and WebSocket-specific
    behavior open.
32. The custom WebSocket transport and its connection-manager caller were
    re-read. `yQe` forwards parse/socket errors without settling pending calls,
    but invokes `onclose` and removes listeners on close; the manager then
    removes connection/listing caches and calls the SDK client's close path
    (`chunk-tem5x312.js@2933`, `@3539`, `@4021`, `@4613`, `@4720`;
    `chunk-9158d2ng.js@79789`, `@80238`, `@103774`, `@107057`, `@107564`).
    This closes the custom WebSocket control-flow gap while retaining native
    socket timing as runtime-dependent. REA's exact
    `mcp_websocket_message_fail` trace returned a partial zero-match result
    (`ev_f0321c072f61dfd1be330f00b29807c711f700ec9a18acaef711c00a1b61ad14`),
    so it is recorded as a coverage limitation.
33. The batched-runner caller enumeration was tightened by inspecting the
    complete `chunk-jwmqjyrb.js` export list and all exact `Zo` occurrences.
    `Zo` is not exported and occurs only at its definition and the `Eqo` and
    `rn` calls, so imported aliases and callback callers are absent from the
    extracted JavaScript (`chunk-jwmqjyrb.js@148486`). The report now limits
    the remaining uncertainty to eval/native/host injection rather than an
    unsearched bundled alias.
34. The MCP registry caller enumeration was independently re-read against the
    complete extracted-chunk literal scan and the full bodies of `Rln`, `SDo`,
    `de`, `tT`, `pi`, `Zi`, `Xd`, bridge `L`, and bridge `N`. The six literal
    `mfe` consumers, two MCP `ne` calls, two `pi` callers, and `kDo` setup are
    correctly anchored (`chunk-0nh75v9f.js@7555`, `@10400`, `@12046`,
    `@14776`, `chunk-2pkntkhf.js@23047`, `chunk-fzzrkchm.js@382970`,
    `@504690`, `@506239`, `@508488`, `@509441`,
    `chunk-td0hhs53.js@3801`). The review intentionally does not promote this
    literal scan to exhaustive coverage of aliased, string-dispatched, or
    host-injected callers; the MCP report and JSON retain that open boundary.
35. The cross-subsystem concurrency addition was checked against the complete
    `AXr`, `PXr`, `pir`, and `tqt` bodies. `AXr` is invoked without awaiting at
    `chunk-93pksqr2.js@140102` and `@174008`, creates an independent pending
    job at `chunk-phacttch.js@2611137`, and `PXr` joins it through `Mcr`/`xXr`
    (`@2616746`, `@2618033`). The `tqt` queue adapter is real, but `pir` has
    only one `onNotification` use, on the skipped-result branch
    (`chunk-phacttch.js@857724`, `@2518310`). The report therefore narrows the
    notification race without claiming that all queue or host paths are
    exhausted.
37. The local-JSX continuation was checked against the complete `Aee.show`
    body, the `local-jsx` slash-command branch, and the `Yke` renderer registry.
    The dispatcher’s headless/no-loader/no-host fallbacks and dismissal result
    are source-backed (`chunk-qqv1hedf.js@27800`, `@29100`); retained node ids,
    abort retirement, and `closed`/`dismissed` mapping are source-backed at
    `chunk-9w4htdvs.js@174423`; and the static registry literal is anchored at
    `@1292300`. The review retains arbitrary loader/node behavior and
    cross-kind focus ordering as unresolved rather than calling the dynamic
    boundary complete.
36. The Storage V5 continuation was checked against the complete journal,
    reverse-reader, tombstone-removal, and V1 hydration helper bodies. The
    journal restore sequence is delete-then-append and its cursor must advance
    (`chunk-8hbrzh7z.js@20800`); `Ktr` rejects changed sequence/data overlap
    (`chunk-phacttch.js@4527000`); `removeByUuidV5` uses bounded `ifMatch`
    retries (`@4572000`); and `qUe`/`me` performs in-place full replacement
    without a source precondition (`chunk-sy9frekf.js@3000`). The wording was
    kept caller-scoped: provider atomicity, crash durability, and remote
    hydration conflict resolution remain open.
38. The MCP transport continuation was checked against the legacy `Lgn` body,
    the modern `_1t` stream-open/reconnect body, and its `_send` path. Legacy
    SSE has explicit-close and error handling without an automatic reconnect
    loop (`chunk-6y1jd448.js@314500`, `@315922`); Streamable HTTP combines
    resumption tokens, auth/step-up, bounded retry scheduling, terminal stream
    end, and 202/POST promotion (`@320500`, `@327500`). The review keeps native
    timing, server replay semantics, and pending-response retention across
    reconnects as unresolved or inferred rather than claiming runtime proof.
39. The precompute cancellation continuation was checked against the complete
    `Y0` `finally` path and the `Mhe` post-compaction cleanup call. `Y0` invokes
    `xir` with `subagent_exit`, while `Mhe` invokes it with
    `post_compact_cleanup`; `xir` aborts/removes the registry entry and performs
    the associated sidecar bookkeeping (`chunk-93pksqr2.js@127283`,
    `chunk-phacttch.js@2622159`, `@2622880`). The report keeps simultaneous
    promise-settlement ordering and host/provider aliases unresolved.
40. The concurrent permission continuation was checked against the complete
    `eS` registry and `Ie` caller. `openAsk` retains requests per tool-use id,
    selects one visible block using explicit show/onTop/order rules, and
    `Ie` tears down only the completed request's controller and registry entry
    (`chunk-phacttch.js@2931335`, `chunk-57pw7ky5.js@51135`). The wording now
    says “one-visible/many-open” and does not claim that host/remote surfaces
    serialize all approval promises.
41. The host-wake continuation was checked against the complete `Ju`/`xp`
    queue-selector bodies and the `Lp.run` handoff. A task notification can be
    admitted while explicitly setting `shouldQuery:false` when the
    coalescing/follower predicate succeeds; `noteTurnEnded` retains the empty
    result's character/workload state for a later synthetic prompt
    (`chunk-fzzrkchm.js@106757`, `@108084`, `@121518`). The review keeps the
    downstream per-mode interpretation of `shouldQuery:false` unresolved.
42. The follow-up checked the `kf.run` and `Zp.route` bodies rather than
    treating the queue flag as a model-call gate. `kf.run` submits the command
    to the engine; `Zp.route` handles the concrete direct-emission versus
    held-result behavior, while the query loop's explicit pre-request stop
    predicate remains separate (`chunk-fzzrkchm.js@137755`, `@190435`;
    `chunk-93pksqr2.js@134246`). The report now states that
    `shouldQuery:false` alone does not prove the current API call is skipped.
43. The MCP continuation re-read the complete `mfe` settlement body and the
    transport-close reconnect entry. Normal applied settlement publishes store
    state without directly closing the prior active client; stale/refused
    candidates are closed, while `SDo` owns cleanup before reconnect
    (`chunk-0nh75v9f.js@3225`, `@10400`, `@11641`). The remaining gap is now
    limited to uninspected removal/replacement callers that might close an
    active client and settle its in-flight calls.
44. A bounded caller pass resolved the cache-closure edge that was previously
    left broad. `clearServerCache` calls `qt` for a settled connected client
    and `Wc` for an unsettled dial; configuration reconciliation, plugin
    deduplication, queued updates, management disable, and authentication
    clearing all reach that boundary or an equivalent direct close
    (`chunk-9158d2ng.js@116439`, `@116861`; `chunk-exx7q64a.js@14371`,
    `@16815`; `chunk-416ekshr.js@11144`; `chunk-bpav708b.js@1415`, `@4214`;
    `chunk-9w4htdvs.js@1580387`, `@1586900`; `chunk-t680wpqf.js@105271`).
    The remaining unknown is now the uninspected dynamic/provider/host caller
    set, not the semantics of these bounded removal paths.


45. The shutdown guards on the host wake path are now bound. `Lp.run` receives
    `Ls` (`shutdownInProgress`) and `wn` (process-global flag written only by
    `T8`); `shutdown()` commits both before its first await, after which
    `xp.take` returns no head, `Xu.isHeld` releases waits, `xp.exit` zeroes held
    completion counters, and `Lf.route` refuses child-agent resume. SIGTERM
    does not abort the drain controller while `end_session` does, so an
    in-flight turn can outlive the SIGTERM handler, and `shutdown()` does not wait
    for it (item 46) (`chunk-fzzrkchm.js@118016`, `@109230`, `@113101`,
    `@228384`, `@491913`, `@572889`; `chunk-phacttch.js@101341`,
    `chunk-80kqkekd.js@150477`).

46. `shutdown()` does not wait for the model turn. It awaits `gpt` (registered
    cleanups, raced for 2000 ms), `Est` (exit-handoff write only), `FSt`
    (shell kill backstops), `eat` (process sweeps), SessionEnd hooks bounded by
    `JEe()`, `mL`, `PDe`, `rPe`, `pwe`, `g2n`, and a scaled stdout drain, then
    calls `process.exit`; the failsafe timer can cut any of these. SIGTERM
    does not abort the turn controller (`Yn` is the control-request
    controller). A transcript flush still running after the 2000 ms race is
    not joined by any later step (`chunk-phacttch.js@101341`, `@98517`,
    `@4553723`; `chunk-j0pppawn.js@4520`; `chunk-fzzrkchm.js@491913`).
47. The compaction race is resolved for the inspected paths. Detached results
    are queued, not in the compaction input; `Mhe` and the compaction functions
    do not touch the queue or the detached ledger; precomputed swaps keep
    post-snapshot rows as `tail` or are refused; stale settles are rejected by
    `Cke`. The only discard paths found are rewind, resume and `/clear`
    (`chunk-phacttch.js@2217054`, `@2519083`, `@2616569`, `@1911487`;
    `chunk-w3dhb84t.js@45723`). Summary fidelity and the compaction-then-rewind
    sequence remain open.