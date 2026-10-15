# storageV5 and transcript persistence

Status: VERIFIED-STATIC for the session mirror/router and task-list Storage V5 use; PARTIAL for the lowest-level backend implementation and the complete `hydrateRemoteSession` body.

## Storage abstraction observed in the bundle

The session persistence owner in `chunk-phacttch.js@4558167` holds `internalEventWriter`, `internalEventReader`, `internalSubagentEventReader`, `internalAgentEventReader`, `agentWorkerEventReader`, `mirrors`, `writeQueues`, `pendingWriteCount`, a 100 ms flush interval, a drain chain, a store fence, and a 100 MiB chunk limit. These fields show a queued append/mirror abstraction rather than direct synchronous writes for all transcript events.

Task-list Storage V5 is explicit in `chunk-zkrrxfpr.js`. `Fx` (`@6323`) gates tasks with `CLAUDE_CODE_ENABLE_TASKS`; paths are namespaced by sanitized list id (`Hx`, `LN`, `D`). The V5 route uses a `storageV5` handle to read/write/list/delete namespaced task keys and a high-water-mark key. The filesystem route uses `${data}/tasks/<list>/<id>.json` plus a `.highwatermark` file.

## Task persistence contract

The task schema `Ne` at `chunk-zkrrxfpr.js@~3400` is:

```text
{ id, subject, description, activeForm?, owner?,
  status: pending|in_progress|completed,
  blocks: string[], blockedBy: string[], metadata?: object }
```

`Kds` (`@9581`) allocates the next id from the maximum of the listing and high-water mark. Under V5 it uses an if-absent write; collisions are treated as already-existing/uncertain and the allocator advances, recording skipped ids. `Yds` (`@12065`) restores/writes a specific task only if absent and raises the high-water mark. `Z2` (`@12749`) reads and schema-validates a task. `Dce` (`@14227`) updates under a lock or Storage V5 update primitive. `GCt` (`@14521`) deletes the task and removes references to it from every remaining task's `blocks` and `blockedBy`. `IM` (`@15083`) lists tasks sorted numerically. `rio` (`@15407`) returns a restorable snapshot plus highest id. `qCt` (`@15961`) adds a dependency edge to both sides.

Task V5 reads list keys, validates each JSON payload, and sorts by numeric id. Update retries up to five times for a `LockSuspect`/Unavailable condition with bounded backoff (`ye`, immediately after `@13200`). The filesystem path uses lock files and atomic/exclusive writes. This is a concrete persistence guarantee: task updates are serialized per task, but the bundle does not establish a transaction spanning multiple dependency files.

## Transcript routing

`appendEntry` (`chunk-phacttch.js@4587783`) first accounts for agent-local writes, skips when persistence is disabled, marks foreign/withheld entries, chooses the session or agent transcript file, and queues writes when the file is not ready. A policy table `rNs[e.type]` routes entries as always-write, agent-specific, or deduplicated transcript. Deduplicated transcript rows are checked against `sessionMessages`; sidechain rows go to the agent transcript path. Non-sidechain transcript rows can additionally invoke `persistToRemote` when an internal writer/remote path exists.

The router records local writes, supports per-agent mirrors, and drains through a write queue. It is not safe to infer that every internal event is part of the user-visible transcript: history-suppressed, foreign, teleport-pulled, and sidechain rows have separate policies.

## Compaction/resume interaction

The task list is carried across compaction by `chunk-fzzrkchm.js@305589` (`tg`). It reads the task snapshot, filters internal metadata, and serializes the richest representation that fits a 262,144-byte bound: tasks plus descriptions/metadata, then progressively removes metadata, descriptions, and finally task bodies, always retaining `highestId`. On restore, `XE` validates the compaction marker's preserved row UUIDs and task-list payload; malformed markers are ignored and the list is rebuilt from task calls.

This is the strongest recovered cross-subsystem persistence fact: active task state is both independently stored and opportunistically carried in the compacted transcript marker.

## Confidence and gaps

| Claim | Confidence | Anchor |
|---|---|---|
| Task storage has filesystem and V5 namespaced backends | VERIFIED-STATIC | `chunk-zkrrxfpr.js@6323–15961` |
| Task IDs use high-water mark and collision-safe allocation | VERIFIED-STATIC | `chunk-zkrrxfpr.js@9581` |
| Task deletion cleans dependency references | VERIFIED-STATIC | `chunk-zkrrxfpr.js@14521` |
| Transcript writes are queued/routed/deduplicated | VERIFIED-STATIC | `chunk-phacttch.js@4558167`, `@4587783` |
| Compaction carries task state with size fallbacks | VERIFIED-STATIC | `chunk-fzzrkchm.js@305589` |
| `storageV5` low-level backend and transaction semantics are fully recovered | UNKNOWN | inspected task and session callers; backend abstraction remains distributed |

Unresolved: the definitive Storage V5 interface declaration, backend selection feature gates, transcript durability across process crash, and the exact relationship between `storageV5` task writes and session mirror flush completion.
