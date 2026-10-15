# Consolidated source call graph

This is an evidence-indexed graph of the recovered paths, not a claim that the partial REA semantic graph enumerates every dynamic caller.

## Core edges

```text
rn (normal turn, chunk-jwmqjyrb.js@72140)
  -> Zo (same module @28129)
     -> ja (safe/unsafe grouping @28720)
     -> Ka -> uEn (chunk-phacttch.js@633773)
     -> Wa (sequential unsafe path)
     -> Qj (shared dispatch @2268196)
        -> AWo (validation/hooks/permission/call @2275985)
  -> persistence/forwarding -> next model context

Eqo (deferred permission resume, chunk-jwmqjyrb.js@52813)
  -> Zo -> persistence/forwarding -> deferred hook attachment

query loop (chunk-93pksqr2.js@182145)
  -> PXr precompute -> pir reactive compaction
  -> retry / precomputed swap / prompt-too-long handling

CXt (detached tool, chunk-phacttch.js@2216254)
  -> Ejo persist/spill (@2217060)
  -> hge -> Qa(task-notification, priority=next)
  -> input/result routing (chunk-93pksqr2.js@11011; chunk-fzzrkchm.js@137755)

nle plugin commands (@964054)
  -> TDt/Tj scan (@955000) -> z6 normalize (@960000)
  -> command registry / permissions

Rrr ToolSearch (@937427)
  -> refresh deferred tools/MCP clients -> tool_reference result
  -> MCP aliases/generation checks (mre @456210; Tht)

appendEntry (@4587783)
  -> local/agent write queues -> persistToRemote (@4590886)
  -> internal writer / ingress fallback

TaskCreate (@140140) -> Kds (chunk-zkrrxfpr.js@9581)
TaskGet (@142348) -> Z2 (@12749)
TaskUpdate (@146660) -> Dce (@14227), GCt (@14521), qCt (@15961)
TaskList (~@150000) -> IM (@15083)
TaskStop -> Ive (@12271) -> AJe/kn task-type killer registry (@6994)
TodoWrite (@216) -> per-agent in-memory checklist
```

## Caller classification

| Node | Resolved callers | Dynamic/unknown boundary |
|---|---|---|
| `Zo` | `Eqo`, `rn` in `chunk-jwmqjyrb.js` | Runtime aliases and imported/re-exported references outside the defining module; REA graph partial |
| `pir` | Query-loop compaction route | Other entry paths may be indirect through settings/host orchestration |
| `PXr` | Query loop and reactive controller | Precompute scheduling callers outside the inspected query path |
| `CXt` | Tool dispatch/detach path | Other detached task producers and dynamic tool calls |
| `Qa` task notification | `hge`, remote-agent completion paths, other task producers | Host/UI consumers and external wake handlers |
| `nle` | Plugin command initialization/reload | Manifest/configuration-driven plugin imports |
| `Rrr` | Normal ToolSearch dispatch | Dynamic model tool calls |
| `persistToRemote` | `appendEntry` and mirror callers | Remote/session restore paths; `hydrateRemoteSession` alias body unresolved |
| `Kds/Z2/Dce/GCt/IM/qCt` | Task tools, compaction carry/restore, team logic | Dynamic task types and compatibility callers |
| `$Fo/JQo/TransportPermissionDispatcher` | Permission dispatch and remote transport | Local renderer event wiring |

## Evidence discipline

The extraction contains 2,344 parsed JavaScript files and zero parse failures in the retained REA analysis, but its semantic graph is partial/truncated. A text occurrence or a single graph edge therefore cannot prove an exhaustive global caller set. The reports label module-local exhaustive occurrences separately from indirect/dynamic unknowns. No installed executable was modified and no new live-model experiment was run.
