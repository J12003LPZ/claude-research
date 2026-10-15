# Dynamic caller enumeration and source-graph limits

Status: `PARTIAL` — direct callers and cross-boundary handoffs enumerated for
the focused paths; exhaustive runtime caller enumeration is `UNKNOWN` because
the bundled graph contains minified aliases, dynamic imports, string dispatch,
and host/provider callbacks.

## Enumeration method

The inventory combined exact-token searches over the extracted 2.1.296 chunks,
bounded reading of each defining function body, import/export inspection, the
existing continuation reports, and focused REA traces. A text occurrence was
not treated as a caller unless its surrounding function body showed a call or
dispatch edge. REA's retained application analysis is
`ev_f219362e2aa64d136c19e6f408087c8cf4e07c28d12011cd2041ba7f658f85d6`.
The focused `chunk-fzzrkchm.js` trace proved module identity/import relations
but had no semantic budget for that module
(`ev_23dd97c6ca05983d50cfeadcc05997130896bf05e10383a05d8c18c52332160f`).

## Direct and resolved caller table

| Defining function/path | Caller | Anchor | Edge | Confidence |
|---|---|---|---|---|
| `Zo` batched runner | `Eqo` deferred/orphaned-tool resume | `chunk-jwmqjyrb.js@52813` | singleton `Zo` generator, manual drain | VERIFIED-STATIC |
| `Zo` batched runner | `rn` normal collected tool-use turn | `chunk-jwmqjyrb.js@72140` | mapped tool blocks, shared permission context | VERIFIED-STATIC |
| `Zo` | other modules/dynamic aliases | `chunk-jwmqjyrb.js@148486` export list plus exact-token scope | `Zo` is not exported; the defining asset contains only its definition and the `Eqo`/`rn` calls, so no imported alias or callback use is present in the extracted JS | VERIFIED-STATIC |
| `Qj` shared dispatcher | `Zo` safe/unsafe paths | `chunk-phacttch.js@2268196` | per-call validation/hooks/permission/call | VERIFIED-STATIC |
| `Qj` | streaming executor and other dispatch wrappers | `chunk-phacttch.js@2268196` | common tool dispatch contract | VERIFIED-STATIC / caller set partial |
| `pir` reactive controller | query-loop withheld-error branch | `chunk-93pksqr2.js@180652` | `tqt` adapter then `pir` | VERIFIED-STATIC |
| `PXr` precomputed consumer | same withheld-error branch and auto controller | `chunk-93pksqr2.js@180652` | returns swap/outcome to `pir`/auto route | VERIFIED-STATIC |
| `AXr` precompute arm | query-loop automatic-compaction completion | `chunk-93pksqr2.js@140102` | starts precomputed summary work without awaiting it | VERIFIED-STATIC |
| `AXr` precompute arm | query-loop post-response estimator | `chunk-93pksqr2.js@174008` | starts another pending precompute job when the response leaves enough context pressure | VERIFIED-STATIC |
| `AXr` | asynchronous precompute job | `chunk-phacttch.js@2611137` | dedicated abort controller, hook/summary job, pending entry, and settled promise | VERIFIED-STATIC |
| `PXr` | `Mcr`/`xXr` pending-precompute join | `chunk-phacttch.js@2618033` | waits for borrowed/current pending work or returns turn-aborted/failed/ready outcome | VERIFIED-STATIC |
| `tqt` compaction queue adapter | `pir` reactive compaction callback | `chunk-phacttch.js@857724`, `@2518310` | streams compact events and wraps skip notifications; no direct live-queue append recovered | VERIFIED-STATIC |
| `hge` task-result notifier | `Ejo` detached completion | `chunk-phacttch.js@2216254`, `@2217060` | persist then enqueue task notification | VERIFIED-STATIC |
| queue `enqueuePendingNotification` | `hge`, generic `LVt`, other notification producers | `chunk-phacttch.js@632678`, `@238838` | task/prompt notification insertion | VERIFIED-STATIC / producer set partial |
| `ow` queue-to-main kick | session setup | `chunk-fzzrkchm.js@224541`, `@559872` | subscriber invokes `wo` when idle/open | VERIFIED-STATIC |
| `Lp.run` main drain | `wo` kick and normal loop ownership | `chunk-fzzrkchm.js@118016` | serialized queue drain and turn | VERIFIED-STATIC |
| `Lp.run` | `xp.take` and `turnRunner.run` | `chunk-fzzrkchm.js@108084`, `@121177`, `@121518` | admitted queue command is committed, armed, and passed to the ordinary turn runner | VERIFIED-STATIC |
| `xp.take` task-notification branch | `Ju.holdsQueryForFollower` | `chunk-fzzrkchm.js@106757`, `@108084` | under the coalescing gate, rewrites the command to `shouldQuery:false` and `queryHeldForNextTurn:true` | VERIFIED-STATIC |
| `xp.noteTurnEnded` | synthetic empty prompt path in `xp.take` | `chunk-fzzrkchm.js@108084` | empty-result held completion counts/workload can be discharged on a later empty prompt | VERIFIED-STATIC |
| `kf.run` | query engine `submitMessage` | `chunk-fzzrkchm.js@190435` | the committed command is submitted with `Ck` context; no direct `shouldQuery` skip occurs in this runner body | VERIFIED-STATIC |
| `Zp.route` | result emission versus held-result path | `chunk-fzzrkchm.js@137755` | `shouldQuery:false` emits directly unless `queryHeldForNextTurn`/handback/holdback conditions retain the result | VERIFIED-STATIC |
| `Lf.route` child-agent wake | queue subscriber/stranded-resume setup | `chunk-fzzrkchm.js@229359` | `wX` target agent, consume after commit | VERIFIED-STATIC |
| attached-host self-wake controller `cd` | `gS` host-status initializer and registry callbacks | `chunk-fzzrkchm.js@97910`, `@102430` | host-return/last-word checks enqueue guarded task notification | VERIFIED-STATIC |
| remote shell executor `so` | remote-served shell dispatch | `chunk-bsjqfd0a.js@35653`, `@37213`, `@39490` | per-caller background-shell ownership/settlement; completed background shell gets non-notifying status text, not local task queue insertion | VERIFIED-STATIC (scoped) |
| remote background-shell registry `nn` | remote shell executor | `chunk-qwgyf6qf.js@4678`, `@5543` | reserve/adopt, lifetime/deadline/limit checks, per-call record and exit cleanup | VERIFIED-STATIC |
| scheduled loop controller | persisted loop schedule / queue notification | `chunk-e1qepm02.js@2208`, `@3481`, `@3775`; `chunk-zdvza25y.js@18210` | computes/re-arms loop fires and enqueues prompt or task-notification records under loading/input/kill gates | VERIFIED-STATIC |
| resume reconstruction `yft` | pending-loop reconciliation `Yi` and orphan-agent scan `Wi` | `chunk-rrep227n.js@43003`, `@49606`, `@62600` | restores transcript/task state; overdue loop is informational (`shouldQuery:false`); future loop is re-armed; recent disk-resumable agents may be returned to callback | VERIFIED-STATIC |
| session lifecycle restore | `resumeOrphanedAgents` callback | `chunk-9w4htdvs.js@365354`, `@368057` | after MCP/takeover checks, restarts eligible agents with `continueInterruptedTurn:true` and emits separate-notification guidance | VERIFIED-STATIC |
| startup/frame restore | `yft` without proven restart callback | `chunk-fzzrkchm.js@477551`; `chunk-9w4htdvs.js@352930` | invokes common reconciliation; supplied running-pool stand-ins do not prove automatic orphan restart | VERIFIED-STATIC |
| `ToolSearch` | model-emitted deferred discovery call | `chunk-phacttch.js@937427` | refresh pending MCP tools and return refs | VERIFIED-STATIC |
| `Qj` pending MCP path | model-emitted MCP tool call | `chunk-phacttch.js@2268196` | pending wait, alias/generation, shared dispatch | VERIFIED-STATIC |
| reconnect implementation | reconnect loop | `chunk-0nh75v9f.js@11641` | epoch/currentness checked publication | VERIFIED-STATIC |
| `mfe` connection settlement | app/dynamic MCP store update | `chunk-0nh75v9f.js@3225` | drops config-mismatched or account-superseded clients; reconciles tools/resources on valid settlement | VERIFIED-STATIC |
| `mfe` | `Rln` account-switch re-dial callback | `chunk-0nh75v9f.js@7555` | settles each account-switch re-dial through the registry barrier | VERIFIED-STATIC |
| `mfe` | `de` transport-close reconnect loop | `chunk-0nh75v9f.js@10400` | publishes current pending/reconnected/failed state | VERIFIED-STATIC |
| `ne` | `SDo` kept-connection refresh | `chunk-0nh75v9f.js@12046` | re-queries a kept connection's tools | VERIFIED-STATIC |
| `ne` re-queried tool-list updater | `PHt`/`Sdn` guarded store publication | `chunk-0nh75v9f.js@13379` | refuses publication when another server owns the name; retains pending-client results in a WeakMap | VERIFIED-STATIC |
| `ne` | `kDo` `tools/list_changed` handler | `chunk-0nh75v9f.js@14776` | publishes the guarded live-list refresh | VERIFIED-STATIC |
| `kDo` connected-client registration | `tools/list_changed` refresh | `chunk-0nh75v9f.js@13974` | one handler per client, config-identity check, shared refresh, keep-previous failure path | VERIFIED-STATIC |
| `mfe` | bridge server-config meta mount `L` | `chunk-2pkntkhf.js@23047` | applies or drops a reply mount based on settlement status | VERIFIED-STATIC |
| `mfe` | generic reconnect controller `tT` | `chunk-fzzrkchm.js@382970` | handles cached-adopt/retry/needs-auth settlement | VERIFIED-STATIC |
| `mfe` | local `pi` wrapper definition | `chunk-fzzrkchm.js@504690` | binds `Fr` stores and forwards to the registry barrier | VERIFIED-STATIC |
| `pi` | `Zi` reconnect-result normalizer | `chunk-fzzrkchm.js@506239` | maps registry outcomes to returned client state | VERIFIED-STATIC |
| `pi` | `Xd` needs-auth re-adoption | `chunk-fzzrkchm.js@508488` | publishes a reauthenticated listing after identity checks | VERIFIED-STATIC |
| `kDo` | MCP lifecycle setup | `chunk-fzzrkchm.js@509441` | installs the shared list-change registration callback | VERIFIED-STATIC |
| `mfe` | bridge projects reply mount `N` | `chunk-td0hhs53.js@3801` | applies or retracts the project reply mount | VERIFIED-STATIC |
| `mfe` applied settlement | `Ofe`/`se` store publication | `chunk-0nh75v9f.js@3225` | updates the current registry row; only stale/refused candidate paths call detach/close | VERIFIED-STATIC |
| `SDo` transport-close handler | row `cleanup` then `de` reconnect chain | `chunk-0nh75v9f.js@10400`, `@11641` | closes the transport-owned client before reconnect and checks current identity/configuration | VERIFIED-STATIC |
| `clearServerCache` | `qt` / `Wc` connection teardown | `chunk-9158d2ng.js@116439`, `@116861` | settles a connected client through cleanup or supersedes a pending dial before removing keyed cache state | VERIFIED-STATIC |
| `uDo` MCP config reconciliation | old-row cleanup plus `clearServerCache` | `chunk-exx7q64a.js@14371`, `@16815` | closes stale/replaced connected rows before removing their surfaces | VERIFIED-STATIC |
| plugin deduplication | connected duplicate `clearServerCache` | `chunk-416ekshr.js@11144` | closes a duplicate plugin client after disabling its close callback | VERIFIED-STATIC |
| `FXe.applyQueuedUpdates` | helper `v` / direct `detachAndCloseConnection` | `chunk-bpav708b.js@1415`, `@4214` | closes late policy/ownership results and identity-stale candidates | VERIFIED-STATIC |
| MCP management disable | connected-row `clearServerCache` | `chunk-9w4htdvs.js@1580387`, `@1586900` | closes the active server before publishing disabled state | VERIFIED-STATIC |
| authentication clear action | `clearServerCache` | `chunk-t680wpqf.js@105271` | closes the unchanged-epoch client before publishing failed state | VERIFIED-STATIC |
| `Lp.run` guard | `Ls` / `wn` shutdown flags | `chunk-fzzrkchm.js@118016` | refuses a new drain once shutdown is committed or an end-session request has no head | VERIFIED-STATIC |
| `shutdown()` | `T8` committed flag | `chunk-phacttch.js@101341` | sets shutdown state synchronously before the first await | VERIFIED-STATIC |
| print-mode SIGTERM handler | `T8`, `Yn.abort`, `Zn(143)` | `chunk-fzzrkchm.js@491913` | commits shutdown without aborting the drain controller | VERIFIED-STATIC |
| `end_session` handler | drain `abortController.abort(shutdown)` | `chunk-fzzrkchm.js@572889` | aborts the turn with a shutdown reason and stops input | VERIFIED-STATIC |
| `xp.take` | `stopping()` loop exit | `chunk-fzzrkchm.js@109230` | takes no head after shutdown commit | VERIFIED-STATIC |
| `Lf.route` | `resumesNothing` | `chunk-fzzrkchm.js@228384` | refuses child-agent wake under shutdown, end-session, or budget limit | VERIFIED-STATIC |
| shutdown() | gpt cleanup drain (We.drain, 2000 ms race) | `chunk-phacttch.js@101341` | shutdown cleanup drain | VERIFIED-STATIC |
| shutdown() | Est / FSt / eat awaited joins | `chunk-phacttch.js@51131` | shutdown awaited joins | VERIFIED-STATIC |
| exit handoff cleanup CHt | E handoff: detach shells, abort agents background, write adopt.json | `chunk-4afqvhsq.js@3677` | exit handoff | VERIFIED-STATIC |
| CHt | wYn unregister or kill unhanded running tasks | `chunk-4afqvhsq.js@5952` | exit unhanded tasks | VERIFIED-STATIC |
| project transcript writer | uNs cleanup flush + sync BJr exit re-stamp | `chunk-phacttch.js@4553723` | transcript exit flush | VERIFIED-STATIC |
| SIGTERM handler | Akn kill running shells | `chunk-phacttch.js@80961` | sigterm kill running shells | VERIFIED-STATIC |
| AXr | dedicated precompute controller Acr | `chunk-phacttch.js@2610727` | precompute independent controller | VERIFIED-STATIC |
| AXr settle | Cke guarded registry update | `chunk-phacttch.js@2616569` | precompute stale settle guard | VERIFIED-STATIC |
| PXr | Mcr / xXr join pending precompute | `chunk-phacttch.js@2618018` | precompute join | VERIFIED-STATIC |
| pir | xxr coverage validation then tail append | `chunk-phacttch.js@2519083` | precompute swap tail | VERIFIED-STATIC |
| Mhe | xir precompute discard (post_compact_cleanup) | `chunk-phacttch.js@2622774` | post compact cleanup | VERIFIED-STATIC |
| Ejo | hge -> Qa message-queue enqueue | `chunk-phacttch.js@2217054` | detached completion enqueue | VERIFIED-STATIC |
| Ejo | ledger stillHeard drop (conversation_cleared) | `chunk-phacttch.js@1909268` | detached completion drop | VERIFIED-STATIC |
| print-host rewind | BTn discardAllOutside + o6t queue removal | `chunk-fzzrkchm.js@594489` | rewind discards detached | VERIFIED-STATIC |
| interactive rewind / resume | _discardDetachedToolCallsOutside -> BTn | `chunk-9w4htdvs.js@370987` | rewind resume discards detached | VERIFIED-STATIC |
| /clear | cv.discardAll + queued detached notification removal | `chunk-p5qcgmmn.js@3661` | clear discards detached | VERIFIED-STATIC |
| `persistToRemote` | transcript append owner, normal mirror branch | `chunk-phacttch.js@4589794` | calls the remote mirror after local append/deduplication; awaits it when the internal-writer fast path is not selected | VERIFIED-STATIC |
| `persistToRemote` | transcript append owner, internal-writer branches | `chunk-phacttch.js@4589831`, `@4589897` | calls the same mirror without awaiting when the internal writer and remote mode permit fire-and-forget delivery | VERIFIED-STATIC |
| `persistToRemote` | defining body | `chunk-phacttch.js@4590886` | asynchronous remote mirror with shutdown, suppression, compaction, writer, and fallback gates | VERIFIED-STATIC |
| internal writer setup | bridge/repl persistence-ready callback | `chunk-2kr6zq6e.js@30760` | injects writer that launches `ne` and resolves adapter promise | VERIFIED-STATIC |
| internal writer setup | CCR v2 remote-IO initialization | `chunk-cest8dre.js@52700` | injects `ccrClient.writeInternalEvent` and readers | VERIFIED-STATIC |
| `x4t` writer bridge | `qFn.setInternalEventWriter` | `chunk-phacttch.js@4555224` | records callback/session and enables writer path | VERIFIED-STATIC |
| `persistToRemote` | injected internal writer | `chunk-phacttch.js@4591557` | awaits the injected writer in the body, but the append caller can intentionally discard that promise | VERIFIED-STATIC |
| `mirrorInternalEntry` | injected internal writer | `chunk-phacttch.js@4592001` | internal-event mirror with suppression/metadata guards | VERIFIED-STATIC |
| `mirrorWorkerEvent` | injected internal writer | `chunk-phacttch.js@4592424` | worker-event mirror with agent attribution | VERIFIED-STATIC |
| `CCRClient.writeInternalEvent` | `queueInternalEvents` | `chunk-a5wd77pa.js@79930` | normalizes and admits event rows into CCR queue | VERIFIED-STATIC |
| `queueInternalEvents` | `internalEventUploader.enqueue` | `chunk-a5wd77pa.js@81521` | batches related internal rows with release bookkeeping | VERIFIED-STATIC |
| internal event uploader | `/worker/internal-events` | `chunk-a5wd77pa.js@39222` | physical post, retry/drop/split policy, async batch-ack callback | VERIFIED-STATIC |
| `CCRClient.finishShutdown` | `flushInternalEvents` | `chunk-a5wd77pa.js@95811` | bounded physical-drain wait before close | VERIFIED-STATIC |
| `k3r` transport constructor | `F.writeInternalEvent` adapter | `chunk-a5wd77pa.js@125745`, `@130515` | exposes the CCR writer to the bridge transport | VERIFIED-STATIC |
| `a5o` remote bridge transport | `k3r` | `chunk-tar8k6v4.js@43925` | constructs the transport whose writer/readers are later wrapped | VERIFIED-STATIC |
| `a5o.fo` deferred-release path | `fr(...,v)` persistence callback | `chunk-tar8k6v4.js@78732`, `@79043` | passes the selected writer wrapper as `ne` | VERIFIED-STATIC |
| agent hydration reader | resume/agent transcript demand | `chunk-phacttch.js@4594002`, `@4594403` | bounded deduplicated read/materialize | VERIFIED-STATIC |
| general `hydrateRemoteSession` (`rQr`) | URL-resume branch | `chunk-phacttch.js@4614350`; caller `chunk-fzzrkchm.js@681312`; export alias `chunk-1stv0pyw.js@18425` | authenticated V1 ingress fetch, zero-content guard, local replacement | VERIFIED-STATIC |
| local permission lifecycle `Ie` | permission dispatch `lBt` | `chunk-57pw7ky5.js@47087`, `@51135` | descriptor, ask queue, resolve/teardown | VERIFIED-STATIC |
| bridge outcome mapper `$Fo` | permission decision finalization path | `chunk-phacttch.js@1880701` | host/hook/abort/recheck outcome to canonical decision/source | VERIFIED-STATIC |
| decision recorder `JQo` | `aBt` permission completion callback | `chunk-57pw7ky5.js@5939`; definition `chunk-phacttch.js@1881907` | classify, persist by tool-use id, emit `tool_decision` after the dialog result settles | VERIFIED-STATIC |
| `aBt` logDecision closure | `JQo` final decision recorder | `chunk-57pw7ky5.js@5939`; definition `@5872` | maps the per-tool logger's input, context, message id, tool-use id, and mode into `JQo` | VERIFIED-STATIC |
| `pdt` permission handler | imported permission `aBt` | `chunk-9w4htdvs.js@1506615`; import `@23579` | creates the per-request logger used by the normal local permission flow, then settles through `logDecision` | VERIFIED-STATIC |
| in-process teammate runner `Qe` | local `He` can-use-tool callback, then imported `aBt` | `chunk-tzyj6m5p.js@18175`, `@3266`; import `@2319` | custom/in-process teammate permission checks receive the same per-tool decision recorder before dialog or teammate forwarding | VERIFIED-STATIC |
| transport dispatcher `kF` | host/worker `can_use_tool` request stream | `chunk-9w4htdvs.js@218600`, `@220300` | validate, deduplicate, invoke dialog, map response, drain | VERIFIED-STATIC |
| generic permission dispatch `lBt` | `HAe` permission-prompt descriptor | `chunk-57pw7ky5.js@47087`; `chunk-cvvnq4he.js@478598` | fallback generic ask path after specialized matches fail | VERIFIED-STATIC |
| `HAe` dialog kind | `pMr` default permission renderer | `chunk-9w4htdvs.js@1292672`; `chunk-bqb9mv4b.js@54618` | registry maps `permission_prompt` to generic panel | VERIFIED-STATIC |
| `pMr` | `L9` choice/feedback controller | `chunk-bqb9mv4b.js@54618`, `@37769` | builds allow/deny/rule/auto options and maps answer | VERIFIED-STATIC |
| `L9` | shared `Ve` selector and `Uwe` feedback state | `chunk-bqb9mv4b.js@37769`, `@35151`; `chunk-75p1g95y.js@40861` | keyboard/focus, feedback editing, mouse selection, Escape | VERIFIED-STATIC |
| `Ve`/`Yi` selector | `Ci` keybinding controller, `HYn` option state, `Di` commit wrapper | `chunk-75p1g95y.js@31583`, `@38136`, `@39814`, `@40861`; focus hook `chunk-pb1e761e.js@21952` | focused-vs-selected state, boundary-aware navigation, focus reclaim, disabled/click gating | VERIFIED-STATIC |
| `Yi` selector input guards | `cb` stray-click guard and `zmt` timing helper | `chunk-cn7dpt66.js@957`, `@1312`; consumer `chunk-75p1g95y.js@40861` | drops activation/mount stray clicks and guards wheel/scroll timing | VERIFIED-STATIC |
| `pMr` | `nE` refused-answer/default-focus state | `chunk-bqb9mv4b.js@54618`; `chunk-rcjkw193.js@672` | refusal counter and temporary focus fallback | VERIFIED-STATIC |
| specialized file dispatch | `iWe` permission-file descriptor | `chunk-57pw7ky5.js@22460`, `@47087` | file branch selected after tool match and receives preview builder | VERIFIED-STATIC |
| `iWe` permission-file kind | `ort` file preview renderer | `chunk-9w4htdvs.js@1251327` | diff/tool-use preview, symlink warning, shared selector | VERIFIED-STATIC |
| `ort` | `Ont` option policy and `lho` result mapping | `chunk-9w4htdvs.js@1241629`, `@1249278` | outside-read/session-grant branches and permission updates | VERIFIED-STATIC |
| specialized web-fetch dispatch | `iBt` permission-webfetch descriptor | `chunk-57pw7ky5.js@47087`, `@33506` | web-fetch branch selected after tool-family classification | VERIFIED-STATIC |
| `iBt` permission-webfetch kind | `Vke` web-fetch renderer | `chunk-9w4htdvs.js@1292672`, `@1283914` | URL/prompt display, permission card, shared selector | VERIFIED-STATIC |
| `Vke` | `qrt` / `$rt` / `Qrt` | `chunk-9w4htdvs.js@1282875`, `@1283167`, `@1283713` | allow/deny/domain-grant mapping and safety/org/hostname gates | VERIFIED-STATIC |
| specialized skill dispatch | `sBt` permission-skill descriptor | `chunk-57pw7ky5.js@47087`, `@33238` | skill branch selected after tool-family classification | VERIFIED-STATIC |
| `sBt` permission-skill kind | `Wke` skill renderer | `chunk-9w4htdvs.js@1292672`, `@1280237` | skill display, exact/prefix grant choices, shared selector | VERIFIED-STATIC |
| `Wke` | `Mrt` / `Irt` / `Ert` / `Wrt` | `chunk-9w4htdvs.js@1278093`, `@1278805`, `@1279317`, `@1279923` | result mapping, rule construction, safety/org/prefix gates | VERIFIED-STATIC |
| specialized PowerShell dispatch | `oBt` permission-powershell descriptor | `chunk-57pw7ky5.js@47087`, `@32959` | command branch selected after tool-family classification | VERIFIED-STATIC |
| `oBt` permission-powershell kind | `Trt` PowerShell renderer | `chunk-9w4htdvs.js@1292672`, `@1271495` | command preview, sandbox/safety checks, suggestions, shared selector | VERIFIED-STATIC |
| `Trt` | `krt` / `p6` | `chunk-9w4htdvs.js@1267767`, `@1270916` | suggestion/prefix option construction and allow/deny/update mapping | VERIFIED-STATIC |
| specialized monitor dispatch | `rBt` permission-monitor descriptor | `chunk-57pw7ky5.js@47087`, `@32680` | monitor branch selected after tool-family classification | VERIFIED-STATIC |
| `rBt` permission-monitor kind | `Fke` monitor renderer | `chunk-9w4htdvs.js@1292672`, `@1260316` | command/MCP/WebSocket display, suggestion guards, shared selector | VERIFIED-STATIC |
| `Fke` | `mrt` / `prt` / `frt` / `grt` | `chunk-9w4htdvs.js@1258368`, `@1259097`, `@1259921`, `@1260091` | result mapping, bounded suggestion construction, safety/org/withheld gates | VERIFIED-STATIC |
| `ZJe` permission-bash kind | `Jtt` bash renderer | `chunk-9w4htdvs.js@1293453`, `@1200505` | command display/withholding, classifier and sandbox gates, standing grants, auto-mode option, shared selector | VERIFIED-STATIC |
| `Jtt` | `ztt` / `Yj` | `chunk-9w4htdvs.js@1198474`, `@1199853` | option construction and allow/suggestion/edited-prefix/deny result mapping | VERIFIED-STATIC |
| `eBt` permission-browser kind | `Ywe` browser/Chrome renderer | `chunk-9w4htdvs.js@1293453`, `@1206666` | URL withholding, host display, session-domain grant, allow/domain/deny mapping, cancel | VERIFIED-STATIC |
| `Ywe` | `Ztt` / `Xtt` / `eot` | `chunk-9w4htdvs.js@1206666` | domain-rule construction, result mapping, and eligibility gates | VERIFIED-STATIC |
| `tBt` permission-enter-plan kind | `oke` plan-entry renderer | `chunk-9w4htdvs.js@1293453`, `@1216982` | refusal epoch, answerability gate, mode update, plan-entry telemetry, deny path | VERIFIED-STATIC |
| `oke` | `fot` / `Zpe` | `chunk-9w4htdvs.js@1216742`, `@1216982` | yes/no result mapping and session mode transition to `plan` | VERIFIED-STATIC |
| dialog host `_v` | `rCe` buried-request filter and `iCe` mounted request | `chunk-9w4htdvs.js@1320735`, `@1323202`, `@1324180` | selects user/non-user surface, suppresses buried cards, validates current payload before answer | VERIFIED-STATIC |
| dialog host `_v` | `nCe` / `sCe` | `chunk-9w4htdvs.js@1322913`, `@1323852` | derives hidden reason and host shown/displaced timestamps | VERIFIED-STATIC |
| `iCe` | dialog-store `answer`/`dismiss` | `chunk-9w4htdvs.js@1324180` | stale-answer gate, missing-component dismissal, resolve-once answer forwarding | VERIFIED-STATIC |
| `HO` transport bridge | dialog-store `open`/`update`/`answer`/`dismiss` | `chunk-9w4htdvs.js@1326466` | subscribes requests, forwards updates, replies on closure, cancels on unmount | VERIFIED-STATIC |
| `Aee.show` local-JSX producer | typed `requestDialog` transport | `chunk-9w4htdvs.js@174417` | allocate `local-jsx-N`, retain node, settle closed/dismissed, abort on close | VERIFIED-STATIC |
| common dialog registry | `Hst` local-JSX renderer | `chunk-9w4htdvs.js@1292672`, `@1291149` | map `kg` to registry lookup by payload `nodeId` | VERIFIED-STATIC |
| main screen | `LocalJsxRegistryContext` provider | `chunk-9w4htdvs.js@1309973` | supply active `localJsx` registry to rendered dialog tree | VERIFIED-STATIC |

## Static caller boundaries

### Batched runner

The defining `Zo` asset contains two statically resolved direct callers: `Eqo`
and `rn`. Its export list does not contain `Zo`, and an exact-token inspection
of the complete defining asset found only the definition plus those two calls
(`chunk-jwmqjyrb.js@148486`). Therefore the extracted JavaScript has no
imported alias or callback-based caller for this local runner. This does not
exclude code introduced through eval/native/host injection, which is outside
the extracted static module graph.

### MCP registry callers

The exact-token pass over all extracted `chunk-*.js` files is exhaustive for
literal `mfe(` references: the definition at `chunk-0nh75v9f.js@3225` and the
six consumers at `@7555`, `@10400`, `chunk-2pkntkhf.js@23047`,
`chunk-fzzrkchm.js@382970`, `chunk-fzzrkchm.js@504690`, and
`chunk-td0hhs53.js@3801` are the complete literal set. The two literal calls to
the MCP `ne` updater are in the defining module at `chunk-0nh75v9f.js@12046`
and `@14776`; the name is too common to use a bundle-wide negative claim for
aliased imports. The local `pi` wrapper has two resolved callers at
`chunk-fzzrkchm.js@506239` and `@508488`, and `kDo` is instantiated at
`chunk-fzzrkchm.js@509441`. These are direct/resolved JavaScript edges, not a
claim that host callbacks, string-dispatched registries, or dynamic imports
have no additional runtime callers.

### General remote hydration

The former `hydrateRemoteSession` body gap is closed for the V1 path. The
defining `rQr` body is in `chunk-phacttch.js@4614350`; its direct URL-resume
caller is `chunk-fzzrkchm.js@681312`. Exact-token/import inspection found the
facade export (`chunk-1stv0pyw.js@18425`), that one direct call, the defining
body, and the defining module's export footer—no second extracted-JavaScript
call site. The same scan found three literal `this.persistToRemote(...)`
call sites in the transcript owner (`chunk-phacttch.js@4589794`, `@4589831`,
`@4589897`) and no imported alias of the method. This is exhaustive for the
literal references and call syntax in the inspected extraction, not a proof
that no dynamically selected or differently aliased host callback can reach
either exported or instance-bound path.

### Wake path

The local main wake has a resolved edge from queue subscription (`ow`) to the
main drain kick (`wo`), with `Lf.route` as the separate child-agent route. A
queue event can have other producers; detached completion, the generic
notification helper, and the attached-host `cd` self-wake producer are now
traced. The remote-served background-shell path is separately traced through
its per-caller registry and explicitly does not use the local task queue for
completion notification. Process-exit reconciliation is now traced through
`yft`, `Yi`, and `Wi`; only the session lifecycle caller supplies the callback
that can restart eligible returned agents. The external daemon/process-start
wake producer and other remote process boundaries remain unresolved.

The final local query gate is also resolved: `_buildToolUseContextWith` first
provides a pending-record predicate, and the main turn `_runImpl` overrides it
with `Eo.stopsLoopForPending()` before invoking the query engine
(`chunk-9w4htdvs.js@1395543`, `@1413024`). The query loop checks it only for a
main query before request setup (`chunk-93pksqr2.js@134246`) and returns
`background_requested`; this is the local handoff point for a deferred
background fork. The exact pending-record creation and draft exception are in
the background gesture class (`chunk-9w4htdvs.js@108462`, `@117617`).

### Process-exit and scheduled wake paths

The common resume function `yft` is now traced through its direct callers. It
does not itself wake a dead process. It reconstructs transcript/task state,
reconciles pending loop records, and scans orphaned agents. The only inspected
caller that supplies a callback capable of restarting returned agents is the
session lifecycle path at `chunk-9w4htdvs.js@365354`; the startup and frame
restore callers supply pool descriptions or no callback
(`chunk-fzzrkchm.js@477551`, `chunk-9w4htdvs.js@352930`). Thus process-exit
recovery is a verified local reconciliation/resume path with a caller-dependent
restart callback, not proof of an external daemon wake producer.

### Permission path

The local `Ie` lifecycle and its `lBt` dispatcher are resolved, and the
transport-side `kF` body is resolved through validation, in-flight
deduplication, dialog invocation, response mapping, and drain. The `$Fo` and
`JQo` bodies establish how a settled bridge result becomes a canonical
decision and persisted `toolUseID` record. Exact-token inspection resolves its
direct extracted-JavaScript caller to `aBt` at `chunk-57pw7ky5.js@5939`; the
registered bash, browser, and plan-entry panel bodies are also now resolved
through `Yke` at `chunk-9w4htdvs.js@1293453` (`Jtt` at `@1200505`, `Ywe` at
`@1206666`, and `oke` at `@1216982`). The display-host selection,
buried-request suppression, stale-answer gate, and transport/store bridge are
resolved through `_v`, `rCe`, `iCe`, and `HO`
(`chunk-9w4htdvs.js@1320735`, `@1323202`, `@1324180`, `@1326466`). Remaining
open permission edges are cross-kind focus arbitration after host promotion,
dynamically supplied local-JSX node implementations, host-versus-remote
answer ordering, and dialog kinds supplied outside the inspected registry. The
shared selector's keyboard/focus primitive itself is resolved at
`chunk-75p1g95y.js@31583`, `@38136`, `@39814`, and `@40861`.
The generic `permission_prompt` path, the `kg` producer/provider/lookup
handoff, and the web-fetch descriptor/renderer/result mapping are resolved
statically.

### Compaction

The query-loop branch is a resolved caller for `PXr` and `pir`. The ordinary
automatic route and precompute manager also call into the same controller, but
the full dynamically selected source/host matrix remains outside the bounded
enumeration.

### MCP and Storage

MCP calls are reached through model tool dispatch, ToolSearch, pending-client
waits, list-change callbacks, reconnect, and plugin hooks. Storage V5 is passed
as a handle to many modules; the default pin helper has no recovered provider
factory, so exact host/provider construction remains outside the inspected JS
path (`chunk-8qnn2dw7.js@816`, `@1541`; `chunk-we7c2g4z.js@5566`, `@5810`).
The local transcript owner is nevertheless statically resolved through its
per-owner drain chain, 100 MiB/handle-change chunking, store-fence failure
state, and multi-pass flush (`chunk-phacttch.js@4561617`, `@4562282`,
`@4572755`). The fallback remote mirror is serialized per session by a keyed
promise chain and its UUID high-water/409 retry policy is resolved through
`fst`/`U0n` (`chunk-phacttch.js@44148`, `@42342`; `chunk-7rd4vcyz.js@866`).
These are local caller/callee edges, not proof of provider commit durability or
of the injected internal-event-writer's queue semantics.

The local-JSX permission boundary now has direct caller edges. The
`local-jsx` slash-command branch selects a loader, checks the interactive and
panel-host gates, and calls the session's `localJsx.show` method on the loader
result (`chunk-qqv1hedf.js@27800`, `@29100`). That method resolves to the
`Aee.show` implementation, which stores the node, emits the `kg` request, and
maps abort/dismissal to the returned `closed` promise
(`chunk-9w4htdvs.js@174423`). The common renderer's `Yke` literal supplies the
static kind-to-component registry, including conditional and list-expanded
entries (`chunk-9w4htdvs.js@1292300`). The unresolved edge is the loader's
arbitrary implementation, not the bundled retention/dispatch handoff.

The transport callgraph now also separates legacy SSE from modern Streamable
HTTP. `Lgn` owns an EventSource and explicit-close/error path without a
transport reconnect loop (`chunk-6y1jd448.js@314500`). `_1t` owns resumable SSE
opening, auth/step-up handling, bounded reconnect scheduling, and terminal
`onRequestStreamEnd` (`chunk-6y1jd448.js@320500`); its `_send` body couples
202/resumption responses to that channel and combines request/transport abort
signals (`chunk-6y1jd448.js@327500`). Recoverable stream drops therefore do not
call the common client's `onclose` until the terminal path; the report marks
the pending-call consequence `INFERRED` rather than runtime-verified.

The storage callgraph also distinguishes the concrete mutation helpers. The
workflow `LocalFileJournal` calls V5 `delete` followed by `append` during
restoration and calls paged `readRecords` during load
(`chunk-8hbrzh7z.js@20800`). The transcript reverse reader `Ktr` calls
backward `readRecords` and validates the overlap between pages
(`chunk-phacttch.js@4527000`). `removeByUuidV5` calls the bounded slow path and
then in-place `replaceRecords` with an `ifMatch` version when removing a UUID
(`chunk-phacttch.js@4572000`). Finally, the URL hydrator's `qUe`/`me` path calls
in-place `replaceRecords` without a source version (`chunk-sy9frekf.js@3000`).
These are direct bundled edges; the backend's internal commit and transaction
edges remain outside the extracted JavaScript.

The compaction cleanup edges are now explicit. The query executor `Y0` invokes
`xir` from its `finally` path with `subagent_exit`, aborting/removing an
agent-owned pending precompute when the stream exits
(`chunk-93pksqr2.js@127283`; `chunk-phacttch.js@2622159`). The common
post-compaction cleanup helper `Mhe` invokes the same `xir` with
`post_compact_cleanup` (`chunk-phacttch.js@2622880`). These edges prove the
local cleanup callers, but not every external/provider path that might retain
an alias to the exported `xir` helper.

## Dynamic-boundary categories

| Category | Inspected evidence | Remaining limit |
|---|---|---|
| Imported alias/re-export | chunk import/export catalogs and focused module reads | minified imported binding may have no literal callee name |
| String/tool registry dispatch | tool registries, ToolSearch, MCP aliases | runtime tool names can select functions without static call syntax |
| Async callbacks/events | queue subscriptions, `tools/list_changed`, hooks | registration and firing can be in different assets |
| Host/provider boundary | `storageV5`, `requestDialog`, remote writer | provider may be supplied outside the JS semantic graph |
| Dynamic imports | plugin/MCP loading paths | loaded module set depends on settings/runtime state |

## Negative findings

The following claims are intentionally not made:

- no claim that the two `Zo` callers cover code injected through eval/native/host
  boundaries; they are exhaustive for the extracted JavaScript asset because
  `Zo` is not exported and has no other token uses;
- no claim that the V1 `hydrateRemoteSession` body is absent; it is recovered
  at `chunk-phacttch.js@4614350`;
- no claim that literal `rQr` reference enumeration excludes dynamic or
  differently aliased host callbacks;
- no claim that the three `persistToRemote` call sites exclude calls through a
  dynamically retained method reference or host/provider callback; they are
  exhaustive for literal method-call syntax in the extracted JavaScript;
- no claim that every Storage V5 backend operation is represented in the
  application bundle;
- no claim that `SSr` proves a provider is absent from native or host code; it
  only proves that the extracted default JavaScript factory returns no backend;
- no claim that every wake producer or MCP transport is statically reachable
  from one root;
- no claim that the scoped remote-served-shell non-notification contract
  describes every remote or daemon-managed wake protocol;
- no claim that `yft` restarts every orphan: restart requires the inspected
  lifecycle callback and its MCP/takeover gates;
- no claim that an overdue `/loop` fire triggers a model request: `Yi` emits
  `shouldQuery:false` for that restart case;
- no claim that every dynamically supplied permission dialog is represented by
  the inspected `Yke` registry or is a direct `Ie` caller.

## Bottom line

The graph is complete enough to establish the local orchestration edges used in
the six reports, but not complete enough to satisfy an exhaustive dynamic
caller standard. The unresolved edges are structural and are recorded in the
JSON companion rather than silently promoted to facts.
