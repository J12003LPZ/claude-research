# Remote session mirroring and hydration

Status: VERIFIED-STATIC for the recovered writer/router behavior; PARTIAL for the remote hydration entry point and conflict policy.

## Local-to-remote transcript path

`persistToRemote` is defined in `chunk-phacttch.js@4590886`. It returns after shutdown sealing, refuses a missing internal writer when the internal path is required, skips teleport-pulled rows, and has special handling for compaction pairs. Scheduled-task notes can be replaced with a `session_cron_carry` attachment containing an empty task list; history-suppressed rows are withheld. With `internalEventWriter`, it awaits `writer("transcript", row, {isCompaction,preservedEventIds,agentId})`; exceptions emit `tengu_session_persistence_failed` and a failure log. The fallback remote-ingress branch calls `fst` when the remote feature flag and ingress URL are present; failures emit persistence telemetry and increment the persistence failure path.

`mirrorInternalEntry` suppresses most internal entries for history-suppressed sessions, retaining only an explicitly permitted `last-prompt` form with the prompt removed. It requires an internal writer and propagates writer failure after telemetry. `mirrorWorkerEvent` applies analogous history suppression and writes worker events with `agentId` attribution.

Writer registration changes the flush interval to `INn`; the owner tracks `pendingWriteCount`, `writeQueues`, `activeDrain`, and `drainChain`. This indicates asynchronous queued mirroring with an explicit drain, not fire-and-forget network calls.

## Agent transcript hydration

`hydrateAgentTranscriptOnDemand`/`fetchAgentTranscriptOnce` (same `chunk-phacttch.js` mirror region near `@4592xx`) require `internalAgentEventReader`, validate a safe agent id, refuse over-bound agents, and deduplicate concurrent fetches with `agentTranscriptFetches`. They fetch events, filter by `session_agent_id`, decode them, reject encoded/unfiltered/over-bound bodies, and if no local write exists, create the local transcript with a create-only operation. Outcomes distinguish hit, empty, and superseded cases.

The exported `hydrateRemoteSession` alias is visible in `chunk-1stv0pyw.js@18425` as `rQr`, but its defining body was not recovered in this pass. It should not be conflated with on-demand agent transcript hydration: the latter is a concrete reader path, while the general session hydration entry point remains an open call-graph item.

## Source-of-truth assessment

The code makes local append routing primary for the active session: `appendEntry` chooses local/agent files, and remote persistence is an additional operation when configured. Remote failures are logged and counted rather than replacing the local append. The source therefore supports “local canonical for immediate transcript continuity, remote mirror for synchronized persistence” as a static reconstruction. It does not prove conflict resolution in a bidirectional merge or that a remote copy can become canonical after restart.

## Failure and disconnection behavior

- Internal writer failure is caught for transcript rows and reported as persistence failure.
- Worker/internal mirror failure can be rethrown after telemetry.
- Teleport-pulled and history-suppressed rows are intentionally excluded.
- Agent hydration deduplicates fetches and prevents unsafe or over-bound content from being written.
- Queued writes are drained through the owner’s chain; exact shutdown wait ordering is not fully traced.

## Confidence table

| Claim | Confidence | Anchor |
|---|---|---|
| `persistToRemote` writes transcript events through internal writer or ingress fallback | VERIFIED-STATIC | `chunk-phacttch.js@4590886` |
| Compaction/cron/history-suppressed rows receive special treatment | VERIFIED-STATIC | `chunk-phacttch.js@4590886` |
| Internal and worker events have separate mirror methods | VERIFIED-STATIC | `chunk-phacttch.js@4558167–4591xx` |
| Agent hydration is bounded, filtered, deduplicated, and create-only when needed | VERIFIED-STATIC | `chunk-phacttch.js@4592xx` |
| General `hydrateRemoteSession` body is recovered | UNKNOWN | `chunk-1stv0pyw.js@18425` export only; defining alias unresolved |
| Remote becomes canonical source of truth | HYPOTHESIS rejected | local append path and failure handling inspected; no source evidence |

Open: remote event conflict/replay ordering, retry backoff and idempotency keys, full session restoration caller graph, and crash consistency between local queue drain and remote acknowledgment.
