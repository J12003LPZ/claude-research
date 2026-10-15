# Source evidence index

Status: `VERIFIED-STATIC` for citation existence and report-local anchors;
semantic completeness remains `PARTIAL`.

## Retained REA evidence

| Evidence id | Use | Limitation |
|---|---|---|
| `ev_f219362e2aa64d136c19e6f408087c8cf4e07c28d12011cd2041ba7f658f85d6` | retained JavaScript application analysis | application graph partial |
| `ev_23dd97c6ca05983d50cfeadcc05997130896bf05e10383a05d8c18c52332160f` | focused `chunk-fzzrkchm.js` module trace | parse complete, semantic analysis unavailable in result budget |
| `ev_fb6fa788689ca1ad1c181cc2141ac1d1350f25d6b765be9fbc6ddd0e8f66a4cf` | exact-string `task-notification` trace | no graph match is not a negative finding because graph is partial |
| `ev_f8f010c1299fa2b52a94602fa80c55e7dd026d13865036d55aeef9e63d565520` | REA semantic trace seeded at `hydrateRemoteSession` | partial graph; no property seed match |
| `ev_57daa9ead15b190c9dc68f2508ae5f8ca5e858a0e16b6cd0ed8a9e863170d6b3` | REA application trace seeded at the exported name | no match; explicitly not evidence of absence because graph is partial |
| `ev_56df6fd325aba78e6bd21f20817618ee8ffa1a6d2192ef13060ed92a0788b872` | REA semantic trace seeded at `requestDialog` | partial graph; no property seed match, not evidence of absence |
| `ev_2386e849ef3ce63ea10ad45aed5b52210d46fe69893d57e0d93a154f76865fb4` | REA semantic trace seeded at property `JQo` | partial graph; no seed match, not evidence that the defining export has no caller |
| `ev_1bbb480b903b76dcc6315af88f79f87fab5676f6d6f0ad7561b95e0b9294f248` | REA semantic trace seeded at `loop_wakeup` | partial graph; no seed match, not evidence of absence |
| `ev_439ec0b9684bb6fcbf05bda136b6d9ff5a2345ee5fc29751069e1bae8a5849c6` | REA semantic trace seeded at `task-notification` | ambiguous partial graph; static graph only, not a replacement for source tracing |
| `ev_6693d2e216fcc195747b5fdb9c0fa70ab43c5d9c8646044db89c69ef0d5dcd0c` | REA feature trace seeded at `remote_tool_serve_background` | no graph match under partial application graph; not evidence of absence |
| `ev_9c05af955cba36c5b60e3ab4e783fca0d7bfc8c1d6370ea2d5c716777c1d2eca` | REA retained-analysis summary projection used to revalidate graph coverage | 2,344 JavaScript files parsed; application and semantic graphs remain partial with explicit unknowns |
| `ev_10b3fda277b33e7d4c103c1fe6414bd0c801fb3db87c5c08040ab9b3a51271a9` | REA feature trace seeded at exact literal `storageV5` | no graph match under partial application graph; explicitly not evidence that Storage V5 is absent |
| `ev_97c2bc819287f6679c0f79a1886e7193dc0a3a03431d3972f0c7e4524cbe71ba` | REA feature trace seeded at exact literal `sleep-auto-resume` | no graph match under partial application graph; explicitly not evidence that scheduled/process-exit recovery is absent |
| `ev_b8e1b52540bb402bb34f41c609f11e01badb1cd60a9c99e751cf9194c4c44660` | REA feature trace seeded at exact literal `local_jsx` | no graph match under partial application graph; explicitly not evidence that the local JSX boundary is absent |
| `ev_3ff626107390b879aace906fd974ad13c2b4c2d7fa421575a8d5570ac1ab0826` | REA feature trace seeded at exact literal `permission_prompt` | no graph match under partial application graph; explicitly not evidence that the permission renderer is absent |
| `ev_9841b75a43e75194beaedae36296cf50f0b4f81e0cc74b16badef1be07a49d17` | REA semantic trace seeded at exact literal `yes-dont-ask-again-domain` | partial graph with zero literal matches; not evidence that the web-fetch branch is absent |
| `ev_99bb7528aa36185b351542a59e417a76aaa37f7dc36dad4839702afdc36b9df8` | REA semantic trace seeded at exact literal `permission_skill` | partial graph with zero literal matches; not evidence that the skill branch is absent |
| `ev_6b171e1b7c4711338994356d61d184e1ff966beabf1dea488a8ca1b8cc8f5b7e` | REA semantic trace seeded at exact literal `permission_powershell` | partial graph with zero literal matches; not evidence that the PowerShell branch is absent |
| `ev_c281f7a9a5a86c6a39f997106126aac6eba2c67023d7e9effd5e0b37c4bd4da0` | REA semantic trace seeded at exact literal `permission_monitor` | partial graph with zero literal matches; not evidence that the monitor branch is absent |
| `ev_14ec941b9a0d3543307d717ce6ca928665c2094771f6a20153a130b515d0d57a` | REA semantic trace seeded at property `stopsLoopForPending` | partial graph with zero property matches; not evidence that the callback is absent |
| `ev_5e1c0cdeb0b9a724748fe26c97dd701ded59f5e151f8e67dcf64ec752b41e993` | REA semantic trace seeded at property `openAsk` | partial graph with zero property matches; not evidence that the ask registry is absent |
| `ev_26d892a6e46bafad5fde97b69ef12f1d0ec444c969e1fdea0f5c6860a2fc3cf0` | REA semantic trace seeded at property `turnStartToolRun` while checking batch/compaction overlap | partial graph with zero property matches; not evidence of a missing caller |
| `ev_721246d2f78d0d6c5629893d4f57b837309ca22e190f4839d7193a8d1283970a` | REA semantic trace seeded at literal `MCP call not sent again after connection closed` | partial graph with zero literal matches; not evidence that the v2 settlement branch is absent |
| `ev_ece799b26112ebfed5071182c776933afe1ba05ae932dcec09dd95264e597274` | REA semantic trace seeded at property `closedBlockingTopBare` while checking dialog-store promotion | partial graph with zero property matches; not evidence that the promotion state is absent |
| `ev_593d2414ff6c613465eac5d883e71e9a70469d3fbf85b162a3f01911c9974dc0` | REA semantic trace seeded at literal `ifUnchangedThrough` while checking V5 compaction preconditions | partial graph with zero literal matches; not evidence that the source precondition is absent |
| `ev_cd4f3febaef5c92c331ddf9e78c537aecf6058d257865a0af2820fe403f772b` | REA semantic trace seeded at literal `publishDiscipline` while checking V5 publish paths | partial graph with zero literal matches; not evidence that publish-discipline branches are absent |
| `ev_b8a760d603a7f09ee2d8242fcf109f8ebf55171aa0b72146b9bba5a355064a3d` | REA exact-seed trace for `writeInternalEvent` while checking injected remote-writer callers | partial source graph, zero seed matches and zero paths; not evidence that the writer is absent |
| `ev_4984b4ce6342dca35d115cba83b88938821de1a1d72b137cd406e5e2cb9b17f3` | REA incoming trace seeded at `getInternalEventWriter` | partial source graph, zero seed matches; not evidence that the writer is absent |
| `ev_90ed576fc346a740882ef69db073f7cd98efabbcd866951e0e398f3ac93ba5fa` | REA trace seeded at `/worker/internal-events` | complete retained result exceeded the MCP response budget; retained for later bounded inspection |
| `ev_e626beeb8c210f25110d3c5c1ebb8d4323c3fab70e9c23b5fd233d4d6aab7850` | REA exact-seed trace for `SIGKILL` while checking MCP stdio cleanup | partial graph with zero literal matches; not evidence that the cleanup branch is absent |
| `ev_f0321c072f61dfd1be330f00b29807c711f700ec9a18acaef711c00a1b61ad14` | REA exact-seed trace for `mcp_websocket_message_fail` while checking WebSocket closure | partial graph with zero literal matches; not evidence that the WebSocket path is absent |

## New report citation counts

Counts are produced by `research/claude-code/tools/audit_static_citations.py`.
The validator checks that a chunk exists and the offset is within decoded text;
it does not establish semantic correctness.

| Report | Anchors | Resolvable | Missing/out-of-bounds |
|---|---:|---:|---:|
| 01-host-wake-and-resumption | 134 | 134 | 0 |
| 02-cross-subsystem-concurrency | 90 | 90 | 0 |
| 03-local-permission-ui | 128 | 128 | 0 |
| 04-mcp-connection-races | 95 | 95 | 0 |
| 05-storagev5-backend | 67 | 67 | 0 |
| 06-remote-session-hydration | 52 | 52 | 0 |
| 07-dynamic-callgraph | 189 | 189 | 0 |
| 09-cross-boundary-state-machine | 39 | 39 | 0 |
| **reports 01–09 total** | **794** | **794** | **0** |

`13-source-pins.json` pins 78 of these anchors to the literal construct that must start at the offset; `tools/source_pins.py` and `tools/test_source_pins.py` re-check them against the extraction.

The JSON callgraph contains 201 structured source edges with module/offset
fields. It is validated separately as JSON and is not counted as Markdown
`chunk@offset` citations.

Including this evidence-index report, the independent-review report, and the
final reconstruction report, the final-runtime-control report set has 1050
resolvable anchor occurrences; the 794-row total above intentionally excludes
the index/review/final-reconstruction citations. The companion
`remaining-subsystems-decompilation` set contributes 134 additional
resolvable anchor occurrences, for 1184 across both current report sets.

## Principal source anchors

| Mechanism | Anchors |
|---|---|
| Batched runner and callers | `chunk-jwmqjyrb.js@28129`, `@52813`, `@72140`, `@148486`; `chunk-phacttch.js@633773`, `@2268196` |
| Local batch/compaction return boundary | `chunk-jwmqjyrb.js@28129`, `@52813`, `@72140` |
| Reactive/precomputed compaction | `chunk-phacttch.js@857724`, `@2518310`, `@2518325`, `@2524076`, `@2526075`, `@2591982`, `@2611137`, `@2616746`, `@2618033`; `chunk-93pksqr2.js@131155`, `@132165`, `@140102`, `@174008`, `@180300`, `@180652`, `@182161`, `@182383`, `@183991` |
| Precompute cancellation and compaction cleanup | `chunk-93pksqr2.js@127283`; `chunk-phacttch.js@2518310`, `@2523831`, `@2565486`, `@2571102`, `@2597263`, `@2622159`, `@2622880` |
| Detached completion and queue | `chunk-phacttch.js@218788`, `@2216254`, `@2217060`, `@238838`; `chunk-fzzrkchm.js@224541`, `@559872`, `@118016`, `@121177`, `@121518`, `@229359` |
| Task-notification coalescing and held completion | `chunk-fzzrkchm.js@106757`, `@108084`, `@137755`, `@190435`; `chunk-93pksqr2.js@134246` |
| Attached-host self-wake | `chunk-fzzrkchm.js@97910`, `@100586`, `@101196`, `@102333`, `@102430` |
| Stop-before-request background handoff | `chunk-9w4htdvs.js@108462`, `@117617`, `@1395543`, `@1408892`, `@1413024`; `chunk-93pksqr2.js@134246` |
| Conditional positive model-request handoff | `chunk-93pksqr2.js@153755` |
| Remote-served background shell non-notification branch | `chunk-bsjqfd0a.js@35653`, `@37213`, `@39490`; `chunk-qwgyf6qf.js@4678`, `@5543`; `chunk-0j0ezmy7.js@3077` |
| Scheduled loop and process-exit recovery | `chunk-e1qepm02.js@2208`, `@3481`, `@3775`, `@4928`; `chunk-zdvza25y.js@18210`; `chunk-rrep227n.js@43003`, `@49606`, `@53530`, `@62600`; `chunk-fzzrkchm.js@477551`; `chunk-9w4htdvs.js@352930`, `@365354`, `@368057` |
| Queue-to-prompt submission bridge | `chunk-93pksqr2.js@11147`, `@11874`; `chunk-kgekdqv3.js@7480` |
| Local permission UI | `chunk-57pw7ky5.js@5872`, `@5939`, `@13560`, `@22460`, `@47087`, `@45577`, `@51135`, `@33506`, `@33238`; `chunk-cvvnq4he.js@478598`; `chunk-bqb9mv4b.js@35151`, `@37769`, `@53100`, `@54618`; `chunk-75p1g95y.js@31583`, `@38136`, `@39814`, `@40861`; `chunk-v44rfc3q.js@184129`; `chunk-pb1e761e.js@21952`; `chunk-cn7dpt66.js@957`, `@1312`; `chunk-rcjkw193.js@672`; `chunk-phacttch.js@1880701`, `@1881636`, `@1881907`; `chunk-9w4htdvs.js@1506615`, `@23579`, `@1198474`, `@1199853`, `@1200505`, `@1206666`, `@1216742`, `@1216982`, `@1241629`, `@1249278`, `@1251327`, `@1278093`, `@1278625`, `@1278805`, `@1279317`, `@1279923`, `@1280080`, `@1280174`, `@1280237`, `@1282875`, `@1283167`, `@1283713`, `@1283914`, `@1291149`, `@1291712`, `@1291863`, `@1292189`, `@1292512`, `@1292672`, `@1293453`, `@1309973`, `@1320735`, `@1322913`, `@1323202`, `@1323852`, `@1324180`, `@1326466`, `@173347`, `@218600`, `@220300`; `chunk-tzyj6m5p.js@2319`, `@3266`, `@18175`; `chunk-gpztfb1a.js@765`, `@1043`; `chunk-s46d15s3.js@2725`; `chunk-gq0v7nj7.js@1100`, `@2747`; `chunk-fzzrkchm.js@61693` |
| Local-JSX loader, retention, and static renderer registry | `chunk-qqv1hedf.js@27800`, `@29100`; `chunk-9w4htdvs.js@174423`, `@1292300` |
| Concurrent permission ask registry | `chunk-phacttch.js@2931335`; caller `chunk-57pw7ky5.js@51135` |
| MCP races | `chunk-phacttch.js@1826026`, `@456210`, `@937427`, `@2268196`; `chunk-0nh75v9f.js@3225`, `@7555`, `@10400`, `@11641`, `@12046`, `@13379`, `@13974`, `@14776`; `chunk-2pkntkhf.js@23047`; `chunk-fzzrkchm.js@382970`, `@504690`, `@506239`, `@508488`, `@509441`; `chunk-td0hhs53.js@3801`; `chunk-drrbp3n4.js@4838`; `chunk-9158d2ng.js@175589`, `@182461`, `@19308`, `@19724`, `@20196`, `@21315`, `@21768`, `@26410`, `@79789`, `@80238`, `@103774`, `@107057`, `@107564`, `@108930`; `chunk-tem5x312.js@2933`, `@3539`, `@4021`, `@4613`, `@4720`, `@6146`, `@6251`, `@6379`, `@6840`; `chunk-6y1jd448.js@100162`, `@100736`, `@101233`, `@315922`, `@319109`, `@320990`, `@328757`, `@328935` |
| MCP already-written call settlement | `chunk-9158d2ng.js@176700`, `@182461` |
| MCP registry settlement versus active-client closure | `chunk-0nh75v9f.js@3225`, `@10400`, `@11641`; `chunk-9158d2ng.js@116439`, `@116861`; `chunk-exx7q64a.js@14371`, `@16815`; `chunk-416ekshr.js@11144`; `chunk-bpav708b.js@1415`, `@4214`; `chunk-9w4htdvs.js@1580387`, `@1586900`; `chunk-t680wpqf.js@105271` |
| Host shutdown gating of the wake path | `chunk-fzzrkchm.js@118016`, `@109230`, `@113101`, `@228384`, `@491913`, `@572889`; `chunk-phacttch.js@101341`, `@100147`; `chunk-80kqkekd.js@150477` |
| Shutdown execution timeline | `chunk-phacttch.js@101341`, `@98517`, `@4553723`, `@80961`, `@51131`; `chunk-j0pppawn.js@4520`; `chunk-4afqvhsq.js@3677`, `@5952`; `chunk-fzzrkchm.js@491913` |
| Compaction versus background notifications | `chunk-phacttch.js@2217054`, `@2519083`, `@2616569`, `@1911487`; `chunk-w3dhb84t.js@45723`; `chunk-fzzrkchm.js@594489` |
| MCP transport reconnect and stream retention | `chunk-6y1jd448.js@314500`, `@315922`, `@320500`, `@327500`; common close settlement `@100736` |
| Storage/remote | `chunk-zkrrxfpr.js@6323`, `@9581`, `@12749`, `@14227`, `@15407`; `chunk-xg6d4cp3.js@1137`; `chunk-8qnn2dw7.js@816`, `@1541`; `chunk-8hbrzh7z.js@21826`; `chunk-we7c2g4z.js@5566`, `@5810`; `chunk-39q3j8sd.js@72433`; `chunk-bvf52rcv.js@622`; `chunk-7rd4vcyz.js@866`; `chunk-phacttch.js@42342`, `@44148`, `@4553729`, `@4555224`, `@4558167`, `@4561617`, `@4562282`, `@4572755`, `@4579334`, `@4587783`, `@4590886`, `@4592001`, `@4592424`, `@4594002`, `@4594403`, `@4614350`, `@4532863`, `@4580562`, `@47941`; `chunk-2kr6zq6e.js@29677`, `@30760`; `chunk-a5wd77pa.js@125745`, `@130515`, `@39222`, `@79930`, `@81521`, `@82970`, `@95811`; `chunk-cest8dre.js@52700`; `chunk-cvvnq4he.js@414956`; `chunk-tar8k6v4.js@43925`, `@78732`, `@79043`; `chunk-sy9frekf.js@3491` |
| Storage mutation and hydration guards | `chunk-8hbrzh7z.js@20800`; `chunk-phacttch.js@4527000`, `@4572000`; `chunk-sy9frekf.js@3000` |

## Runtime cross-checks retained from prior work

No new runtime campaign was run. Existing captures still support only the
claims previously marked runtime-backed: E08 merged parallel tool delivery,
E35–E37 repeated reactive compaction failures without the ordinary breaker,
and the prior daemon/worker/attach observations. The new local wake edge is
static-only in this continuation and is not relabeled `VERIFIED-RUNTIME`.
