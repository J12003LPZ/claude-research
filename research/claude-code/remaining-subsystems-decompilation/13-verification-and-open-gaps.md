# Verification, corrections, and open gaps

## Review performed

This was a read-only independent self-review of all reports 01–12 against the extracted 2.1.296 files, the prior coding-workflow reports, the retained runtime captures, and the REA analysis metadata. It specifically checked that each major claim has a module/offset anchor, that runtime claims cite existing captures, and that partial semantic-graph coverage is not described as exhaustive.

Corrections made during review:

1. The batched runner's safe-group result order is completion order from `Promise.race`, not request order. The report now distinguishes group/barrier order from completion order.
2. Reactive compaction's failure behavior is not contradicted by the ordinary compaction breaker: the breaker is in `Tir`'s ordinary route, while the reactive `pir` route returns structured failure without calling that breaker. The runtime contradiction remains scoped to the reactive route.
3. A task notification's `priority:"next"` is a queue priority, not proof of an unconditional new API call.
4. `TaskOutput` is deprecated/file-backed in this build and `TaskContinue` was not found as a current registry body; these are documented as a contradiction/unknown rather than invented tools.
5. Remote persistence is an additional mirror path from local append routing; no source evidence establishes remote canonicality or bidirectional conflict resolution.

## Citation audit

New reports use `module@character-offset` anchors. The current report set contains 122 anchored source references (82 unique `(module,offset)` pairs); all 122 resolve to an extracted file and in-bounds character offset. Anchors are not all independently resolvable by the partial REA graph, so the audit checks file existence and offset bounds against the extracted files, not semantic completeness.

## Verification matrix

| Area | Static source | Existing runtime cross-check | Result |
|---|---|---|---|
| Batched runner | `chunk-jwmqjyrb.js@28129`, `chunk-phacttch.js@633773` | E08 merged results | VERIFIED-BOTH |
| Reactive compaction | `chunk-phacttch.js@2518325`, `chunk-93pksqr2.js@184160` | E35–E37 repeated failures | VERIFIED-BOTH with scoped contradiction |
| Precomputed compaction | `chunk-phacttch.js@2611146`, `@2618033` | rapid-refill evidence only | VERIFIED-STATIC / partial runtime |
| Background delivery | `chunk-phacttch.js@2216254`, `@2217060` | prior interruption captures | VERIFIED-BOTH for interruption boundary |
| Plugin/MCP | `chunk-phacttch.js@964054`, `@937427`, MCP reconnect modules | none newly run | VERIFIED-STATIC |
| Storage/remote | `chunk-phacttch.js@4587783`, `@4590886`, `chunk-zkrrxfpr.js@9581` | prior persistence evidence | VERIFIED-STATIC / runtime limited |
| Permissions/tasks | `chunk-phacttch.js@1879000`, `chunk-rpwh4z9c.js@140140` | prior permission/task observations | VERIFIED-STATIC / UI partial |

## Remaining unresolved branches

- Global caller exhaustiveness is unavailable because the REA semantic graph is partial/truncated and dynamic imports/configuration dispatch remain.
- Local interactive permission dialog component state, timeout, and multi-request ordering.
- Full `hydrateRemoteSession` defining body and bidirectional remote conflict policy.
- Lowest-level storageV5 backend/transaction contract and crash ordering.
- Complete MCP transport-specific reconnect and pending-call cancellation semantics.
- Host/external wake behavior that turns a queued notification into a model request.
- Full task-tool compatibility/remote continuation surface and exact TaskStop registry aliases.
- Cross-boundary lock ordering when compaction, foreground tools, detached tasks, and transcript flushes overlap.

## Assessment

The six target areas are materially advanced and several central mechanisms are verified statically or against existing captures, but the mission's “complete” standard is not met for all six because UI, remote hydration, backend transactions, transport-specific failures, and global dynamic caller enumeration remain unresolved. Recommended final status: `PARTIAL`.
