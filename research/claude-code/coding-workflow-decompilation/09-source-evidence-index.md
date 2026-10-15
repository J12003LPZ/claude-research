# 09. Source evidence index

Target: Claude Code CLI 2.1.296 extracted tree at `extracted/2.1.296/~BUN/root`. Offsets are zero-based character offsets. `VS` means verified static source. `VR` means existing runtime capture. `SI` means strongly inferred from an inspected connection. `UNK` means not settled.

REA was requested for this pass but the REA MCP server was disconnected after session reconnect. No REA evidence IDs exist for this report. All new evidence below is from local extracted JavaScript and prior sanitized captures.

## 1. Workflow and model request path

| Function / conceptual role | Chunk and offset | Caller / callee relation | Class |
|---|---|---|---|
| `Y0` loop wrapper | `chunk-93pksqr2.js@126966` | delegates to `Ad`, yields terminal events | VS |
| `Ad` main query generator | `chunk-93pksqr2.js@129362` | prepares messages, calls model, drains tools, runs Stop checks | VS |
| loop state and guards | `chunk-93pksqr2.js@130200` | state carried across `continue` transitions | VS |
| request model selection | `chunk-93pksqr2.js@136400` | called during each `Ad` iteration | VS |
| autocompaction call site | `chunk-93pksqr2.js@136500` | calls injected `Tir` | VS |
| pre-request attachments | `chunk-93pksqr2.js@139300` | adds context/hook/tool/model records | VS |
| hard context block | `chunk-93pksqr2.js@149549` | returns `blocking_limit` before API request | VS |
| call-model seam | `chunk-phacttch.js@2840800` | constructs client with CLI retry wrapper | VS |
| streaming API call | `chunk-phacttch.js@2842829` | `beta.messages.create(... stream:true)` | VS |
| content-block accumulation | `chunk-phacttch.js@2859500` | yields assistant block messages | VS |
| tool-use recognition | `chunk-93pksqr2.js@172895` | sets `needsFollowUp`, sends block to `gs` | VS |
| next-turn transition | `chunk-93pksqr2.js@199381` | appends assistant and tool results, increments turn | VS |
| REPL input path | `chunk-9w4htdvs.js@1357077`, `@1413900` | `Tft` and `plt` queue params into engine | VS |
| headless input path | `chunk-fzzrkchm.js@343343`, `@329922` | prepares rows and queues same engine | VS |
| session engine | `chunk-jr646ga5.js@58339`, `@60500` | calls `Y0`, maps loop events | VS |

## 2. Prompt assembly and dynamic instructions

| Function / role | Anchor | Finding | Class |
|---|---|---|---|
| scoped prompt composer `jR` | `chunk-phacttch.js@2018756` | chooses `H5t` or detached `L5t`, flattens sections | VS |
| main builder `H5t` | `chunk-phacttch.js@2019875` | selects lean/full by `V4(model)` | VS |
| lean body `wBo` | `chunk-phacttch.js@2014347` | lean prompt path | VS |
| full sections | `chunk-phacttch.js@1999384`, `@2000324`, `@2001457`, `@2005523`, `@2009298` | intro, system, doing tasks, actions, tools | VS |
| lean reporting text `V0o` | `chunk-phacttch.js@1988701` | report failures/skips/verification | VS |
| end-to-end text `Y0o` | `chunk-phacttch.js@1989268` | gated by unread `xFn` | VS / UNK gate |
| act-now text `TBo` | `chunk-phacttch.js@2014981` | controlled by `vBo` and flag | VS |
| autonomous addendum `uBo` | `chunk-phacttch.js@1997648`, assembly `@2021689` | flag plus `ZH(model, canonical) || Ugs(canonical)` | VS |
| mythos mitigation lookup | `chunk-tydh8ra2.js@710` | explicitly admits mythos model | VS |
| host experiment selector | `chunk-bykygzr4.js@5072` | `Ugs` delegate | VS / branch incomplete |
| custom/coordinator prompt override `EHo` | `chunk-phacttch.js@2099229` | override and append rules | VS |
| proactivity resolver `_a` | `chunk-m44bzxs2.js@74922` | handoff, CLI, persisted stub, default | VS |
| proactivity gate `iA` | `chunk-3qrxzjv5.js@109659` | bare/attachment/selector gates | VS |
| proactivity emitter `KMe` | `chunk-phacttch.js@398302` | attachment on level/tool tuple change | VS |
| proactivity render | `chunk-phacttch.js@4477215`, body `@107269` | calls `xat` | VS |
| permission mapping `mde` | `chunk-wccxtr0h.js@1959` | level changes permission mode | VS |
| level application `OWo` | `chunk-rj7v0tgh.js@1009` to `@1959` | updates level and context | VS |
| task/subagent text `kBo` | `chunk-phacttch.js@2010614` | fork/default guidance | VS |
| imported `UH` result | `chunk-0a3kw9bb.js@33803` | returns false, short branch not reached | VS |
| plan reminder renderer | `chunk-phacttch.js@3655734` | `ZDr`, mode, plan existence, cadence | VS |
| plan attachment cadence | `chunk-phacttch.js@3653352`, `@3641208` | `Kyn`, five-turn cadence | VS |
| post-compaction plan attachment | `chunk-phacttch.js@2588668` | `OYe` | VS |

## 3. Plan mode

| Function / role | Anchor | Finding | Class |
|---|---|---|---|
| EnterPlanMode `emn` | `chunk-3870y95r.js@7017` | rejects agent context, sets plan mode | VS |
| EnterPlanMode body | `chunk-3870y95r.js@7560` to `@8100` | preserves prior mode through `L_t`, sets plan | VS |
| auto pre-plan preservation | `chunk-kqxewm47.js@26232` | special handling for auto | VS |
| plan prompt selector `eKr` | `chunk-phacttch.js@4441599` | full/sparse/subagent forms | VS |
| plan lead sentence `ODn` | `chunk-phacttch.js@4442619` | no execution, plan-file exception | VS |
| phase 1/2 builder `nKr` | `chunk-phacttch.js@4444446` | conditional Explore/Plan prompt | VS |
| phase 3 `oKr` | `chunk-phacttch.js@4447877` | plan review instruction | VS |
| phase 4 `tKr` | `chunk-phacttch.js@4441702` | final plan file content | VS |
| phase 5 `CLn` | `chunk-phacttch.js@4443342` | must call exit/question/publish | VS |
| full plan reminder `rKr` | `chunk-phacttch.js@4448210` | five phases and plan path | VS |
| plan path `kv` / `jc` | `chunk-sz2fxhw2.js@12600` to `@13800` | session/project plan file path | VS |
| plan write/read `Dco` / `v4e` | `chunk-sz2fxhw2.js@14300` to `@16450` | cache/storage/filesystem | VS |
| ExitPlanMode input substitution `FPt` | `chunk-phacttch.js@818956`, caller `@2272200` | injects current plan file | VS |
| plan permission floor `Lpn` | `chunk-phacttch.js@3355376` | non-read-only restrictions | VS |
| file write plan denial | `chunk-p9na5vps.js@237459` | ordinary writes refused | VS |
| ExitPlanMode `gK` | `chunk-z3vv06zx.js@6222` | availability, validation, call | VS |
| ExitPlanMode permission | `chunk-z3vv06zx.js@7602` | ask or team request | VS |
| ExitPlanMode call transition | `chunk-z3vv06zx.js@7800` to `@10000` | restore pre-plan mode | VS |
| team approval request | `chunk-z3vv06zx.js@8226`, verdict `Mqo` `@2077` | mailbox request and verdict | VS |
| interactive plan dialog | `chunk-9w4htdvs.js@1220500` to `@1230900` | reject/approve/clear context choices | VS |
| team auto-approval branch | `chunk-9w4htdvs.js@1538650` to `@1540150` | inbox poller may approve | VS |

## 4. Agents and tools

| Function / role | Anchor | Finding | Class |
|---|---|---|---|
| built-in registry `L0e` | `chunk-phacttch.js@2086295` | conditional default registry | VS |
| general-purpose | `chunk-phacttch.js@2067564` | all tools | VS |
| Explore / Plan | `chunk-phacttch.js@201330`, `@204673` | read-oriented definitions | VS |
| registry loader | `chunk-phacttch.js@2090000` | built-ins/plugins/files/flags | VS |
| precedence `u2` | `chunk-phacttch.js@2088270` | policy > flag > project > user > plugin > built-in | VS |
| plugin loader `Jte` | `chunk-phacttch.js@2086771` | lazy definition validation | VS |
| Agent launch `xo` | `chunk-h6wy99cb.js@15899` | depth, permission, model, pool, dispatch | VS |
| async decision `po` | `chunk-h6wy99cb.js@6066` | background default logic | VS |
| child context `gir` | `chunk-phacttch.js@2539713` | shared/isolated state | VS |
| child filter `Cl` / `LR` | `chunk-jwmqjyrb.js@83520`, `@87492` | remove and allow/disallow tools | VS |
| base tools `rv` | `chunk-rpwh4z9c.js@155896` | registry array | VS |
| tool pool `ZL` / `iUt` | `chunk-rpwh4z9c.js@156500`, `@157860` | filters and MCP assembly | VS |
| wire tool builder `tN` | `chunk-phacttch.js@824746` | API tool schema | VS |
| deferred tool builder `tNe` | `chunk-tgmspsjh.js@3646` | defer decision | VS |
| tool search request path | `chunk-phacttch.js@2771900` to `@2779950` | tool_search/tool_addition | VS |
| streaming executor `gs` | `chunk-93pksqr2.js@46967`, `@47172` | queue/concurrency | VS |
| batched runner `Zo` | `chunk-jwmqjyrb.js@28129` | group cap 10 | VS; caller UNK |
| dispatch `Qj` | `chunk-phacttch.js@2268202` | late MCP/isolation/exception path | VS |
| parse/coerce `W9t` | `chunk-phacttch.js@2145160` | JSON input | VS |
| validation `gsr` | `chunk-phacttch.js@2145597` | tool validation | VS |
| mapped result | `chunk-phacttch.js@2297800` | user tool_result | VS |

## 5. Recovery, completion, persistence

| Function / role | Anchor | Finding | Class |
|---|---|---|---|
| Stop driver `Za` | `chunk-93pksqr2.js@187700` to `@189300` | block/prevent/pass and internal nudges | VS |
| stop cap | `chunk-93pksqr2.js@188500` | default eight | VS |
| tool-end-turn path | `chunk-phacttch.js@1243393`, `chunk-93pksqr2.js@192949` | tool can end turn | VS |
| max turns | `chunk-93pksqr2.js@188345`, `@199183` | pre-next-turn checks | VS |
| terminal list | `chunk-80kqkekd.js@168441` | terminal reasons | VS |
| result assembly | `chunk-jr646ga5.js@66500` to `@69500` | subtype and is_error | VS |
| API retry | `chunk-phacttch.js@2723307`, `@2741300` | retry/fallback/stream choice | VS |
| output recovery | `chunk-93pksqr2.js@185383`, `@186524`, `@187227` | bounded nudges | VS |
| tool failure | `chunk-phacttch.js@2287500`, `@2235023` | error result and failure hooks | VS |
| compaction call | `chunk-93pksqr2.js@136500` | `Tir` before request | VS |
| compaction summary | `chunk-phacttch.js@2565344`, `@2578200` | summary/fallback retries | VS |
| reattachment | `chunk-phacttch.js@2585926` | recent files/status/plan/skills | VS |
| transcript write | `chunk-phacttch.js@4595820`, `@4582928`, `@4539653` | JSONL append/dedup | VS |
| transcript load | `chunk-phacttch.js@4694390`, `@4685423`, `@4700746`, `@4627113` | leaf/parent branch restore | VS |
| interrupted resume | `chunk-phacttch.js@1288300` to `@1294400` | continue message and env gate | VS |
| mode/state restore | `chunk-9x333bd0.js@22282` | mode/model/worktree/file/todo state | VS |
| task notification | `chunk-phacttch.js@4226700` | background completion/failure | VS |
| agent resume | `chunk-r06rdesa.js@9390` | guarded continuation | VS |

## 6. Known limits and unverified claims

1. REA MCP was disconnected, so there are no retained REA Evidence IDs in this pass.
2. Static source existence does not prove runtime reachability. Runtime classifications refer only to the existing E50 captures.
3. The model table behind `V4`, host experiment predicates, server-side policy, and provider-specific request branches remain partly unknown.
4. Full reactive/precomputed compaction, `storageV5`, remote mirroring, plugin lazy loaders, compound-command parser internals, all `Zo` callers, full permission UI, and full task-tool bodies remain outside the inspected scope.
5. No source path in the inspected coding loop requires an ordinary coding task to run or pass tests before completion. This is bounded to the indexed loop, tool, hook, prompt, agent, persistence, and result-builder scopes.
