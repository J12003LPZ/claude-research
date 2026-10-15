# Remote session mirroring and hydration

Status: `PARTIAL` — local-to-remote event routing, general V1 hydration, and
bounded agent hydration are `VERIFIED-STATIC`; remote conflict/replay policy
and low-level persistence guarantees remain unresolved.

## Local transcript is the immediate source

`appendEntry` in `chunk-phacttch.js@4587783` routes a row to the session or
agent transcript, applies event-type policy, deduplicates against known
session messages, and queues the local write. The persistence owner at
`chunk-phacttch.js@4558167` maintains internal readers/writers, mirrors,
per-agent queues, pending write counts, a drain chain, and flush state.

This supports a narrow source-of-truth conclusion: local append routing is the
immediate continuity path. Remote persistence is an additional mirror operation
when configured, not a replacement for the local session row in the inspected
code.

## `persistToRemote`

The function body at `chunk-phacttch.js@4590886` applies several filters before
writing:

1. stop/shutdown sealing prevents new remote work after the session is closed;
2. teleport-pulled rows are not mirrored again;
3. history-suppressed sessions retain only explicitly allowed last-prompt
   forms, with prompt text removed where required;
4. compaction pairs carry preserved-event metadata;
5. scheduled-task rows can be represented by a `session_cron_carry` attachment
   with an empty task list;
6. with an internal writer, the function awaits the writer callback with
   transcript channel, compaction flag, preserved ids, and agent attribution;
7. when the internal path is unavailable and the remote ingress gate is
   enabled, it uses the fallback ingress path;
8. failures emit persistence telemetry and enter the persistence-failure path.

The call is therefore asynchronous and failure-aware. The source does not show
that a remote failure rolls back the local append.

## Internal and worker mirrors

`mirrorInternalEntry` and `mirrorWorkerEvent` are separate operations in the
same mirror region (`chunk-phacttch.js@4592007`, `@4592430`). Both apply
history-suppression rules and include agent/worker attribution. They should not
be conflated with a user-visible transcript append: internal events, worker
events, sidechain rows, and history-suppressed rows have different retention
policies.

## Bounded on-demand agent hydration

`hydrateAgentTranscriptOnDemand` and `fetchAgentTranscriptOnce` are concrete
reader paths at `chunk-phacttch.js@4594002` and `@4594403`. They:

- require an internal agent-event reader;
- validate the agent id and reject unsafe/over-bound requests;
- deduplicate concurrent fetches through `agentTranscriptFetches`;
- read remote events and filter them by `session_agent_id`;
- decode and bound the returned body;
- create the local agent transcript only when no local write exists;
- distinguish hit, empty, superseded, and rejected outcomes.

This is not the general session hydrator. It is a specific child-agent
transcript-on-demand path with a create-only local materialization rule.

## General `hydrateRemoteSession` (V1 session-ingress path)

The facade export at `chunk-1stv0pyw.js@18425` aliases `rQr`; the defining
function is `chunk-phacttch.js@4614350`. Its resolved direct caller is the URL
resume branch at `chunk-fzzrkchm.js@681312`. Exact-token/import inspection of
the extracted JavaScript found no second direct `rQr(...)` call; registry and
host/provider callbacks remain outside that negative result.

The recovered body is:

```text
rQr(sessionId, ingressUrl, storageV5):
  mark hydration for the session
  fetch V1 session-ingress rows with pst(sessionId, ingressUrl)
  ensure the session directory exists, using storageV5 when supplied
  if the remote set has no content-bearing rows and the local transcript does:
      emit hydrate_skip_zero_content_replace
      return true without replacing the local transcript
  replace the local transcript with the fetched rows through qUe(..., "w", ...)
  emit hydrated count
  return fetched_count > 0
  on failure: emit hydrate_remote_session_fail and return false
  always: store the ingress URL on the session context
```

The body calls `pst` at `chunk-phacttch.js@44433`, whose `Mxe` fetch helper at
`chunk-phacttch.js@47941` performs a 20-second authenticated HTTP GET, maps
`loglines`, treats 404 as an empty session, treats 401 as an expired-token
failure, and converts other/network failures to a null result. The write
helper is imported `qUe` from `chunk-sy9frekf.js`; its defining implementation
at `chunk-sy9frekf.js@3491` replaces the transcript through the V5 backend
descriptor when present, otherwise writes JSONL through a filesystem stream.

This resolves the former body gap but does not prove a bidirectional merge:
hydration is a guarded remote-to-local replacement, with a zero-content guard,
not a row-level conflict resolver. The recovered caller also shows this route
is selected only for a resumed URL session with an ingress URL and the feature
gate enabled (`chunk-fzzrkchm.js@681312`).

## Queued writes and failure windows

The writer owner tracks pending counts and drains queues asynchronously
(`chunk-phacttch.js@4558167`). Thus the following windows exist:

```text
local append accepted
  -> local write queued/completed
  -> remote mirror queued/attempted
  -> remote acknowledgement or failure
```

The source proves error telemetry and local continuation, but not an idempotency
key, remote retry schedule, or conflict merge. If a process ends between queue
enqueue and drain completion, the exact persistence guarantee depends on the
unrecovered owner shutdown path.

### Fallback ingress ordering and conflict recovery (new continuation finding)

The fallback `fst` path is not an unconstrained set of concurrent PUTs. It
executes `U0n` through `H0n.run(sessionId, ...)` (`chunk-phacttch.js@44148`,
`@42342`), and `H0n` is a keyed promise serializer: calls for the same key are
chained while different keys may proceed independently (`chunk-7rd4vcyz.js@866`).
Each attempt reads the last ingress UUID remembered for that session and sends
it as `Last-Uuid`; successful 200/201 responses advance the remembered UUID
to the entry being written (`chunk-phacttch.js@42342`).

The 409 branch has three distinct outcomes. If the server's `x-last-uuid`
already equals the entry UUID, the write is treated as recovered success. If
the header names another UUID, the client adopts it and retries. If no header
exists, it refetches the session log and adopts its final UUID; if that also
fails, it records a concurrent-modification failure and stops. Non-auth
failures retry up to ten attempts with jittered backoff capped at 8 seconds;
401 stops immediately, and exhausted attempts return failure
(`chunk-phacttch.js@42342`). This is an ordered, UUID-based optimistic
recovery policy for the fallback ingress writer, not proof of a general merge
algorithm.

The internal-event-writer path is an injected boundary with adapter-dependent
completion. `persistToRemote` awaits the callback return, but the bridge adapter
installed at `chunk-2kr6zq6e.js@30760` launches the supplied `ne(...)`, catches
its failure, and returns an already-resolved promise. In the CCR v2 path, that
`ne` is now statically resolved: `a5o` obtains `S.getInternalEventWriter`,
passes its wrapped form `v` to the persistence callback, and `k3r` defines the
transport writer as `F.writeInternalEvent` (`chunk-tar8k6v4.js@78732`, `@79043`;
`chunk-a5wd77pa.js@125745`, `@130515`). The CCR writer body awaits queue
admission (`chunk-a5wd77pa.js@79930`) and the uploader enqueues batches through
`chunk-a5wd77pa.js@81521`, while physical `/worker/internal-events`
acknowledgement arrives later through the batcher at
`chunk-a5wd77pa.js@39222` and `chunk-cvvnq4he.js@414956`. The explicit
`flushInternalEvents` path is at `chunk-a5wd77pa.js@82970`, with a bounded
shutdown wait at `@95811`.

One append branch intentionally invokes `persistToRemote` without awaiting it
under the internal-writer/remote-session condition (`chunk-phacttch.js@4590886`).
Therefore local transcript queue order is stronger than the visible completion
order of all remote mirror work. The CCR v2 queue/ack path and the identity of
`ne` are now source-resolved, but the bridge does not await the callback's
returned promise; server durability, crash replay, and remote recovery remain
unresolved.

### Internal writer caller matrix and acknowledgement boundary

```text
qFn.x4t/P4t registration
  ├─ bridge/repl: x4t -> ne(...); catch/log; Promise.resolve()
  └─ CCR v2: x4t -> ccrClient.writeInternalEvent
                 -> queueInternalEvents -> internalEventUploader.enqueue
                 -> POST /worker/internal-events
                 -> onInternalBatchAcked (later)
```

This is a queue/admission graph, not a proof that a successful persistence
owner call means remote durable storage. The physical drain observation is
`flushInternalEvents`; its shutdown caller waits at most three seconds before
closing the CCR client.

The V1 hydrate replacement is similarly explicit: `qUe` uses the backend
`replaceRecords` operation with `publishDiscipline:"inPlace"` and no source
version precondition, or writes the complete JSONL body through a filesystem
stream (`chunk-sy9frekf.js@3491`). Therefore the recovered V1 path is a
guarded replacement, not a compare-and-swap merge; a concurrent local append
or crash during that replacement remains an unresolved provider/filesystem
boundary.

The contrast with transcript tombstone removal matters for hydration races.
`qUe` delegates directly to `me`, which maps a full replacement to
`replaceRecords(key, rows, {publishDiscipline:"inPlace", mode:384})`; the
hydration caller supplies no `ifMatch`, stream version, or `ifUnchangedThrough`
token (`chunk-sy9frekf.js@3000`). By comparison, the transcript owner's
`removeByUuidV5` obtains a version and retries conditional in-place rewrites
(`chunk-phacttch.js@4572000`). Thus the source proves a zero-content guard plus
whole-stream replacement for V1 hydration, but not protection against a
concurrent local append or a stale remote snapshot. No row-level merge or
conflict resolver is visible in this caller path.

## Hydration state machine

```text
session resume/request
  -> local transcript available?
       yes -> use local path; optional remote mirror/hydration side work
       no/agent child -> bounded reader and deduplicated fetch
           filtered/valid -> create-only local materialization
           empty -> no local transcript
           stale/unsafe/over-bound -> reject
  -> general hydrateRemoteSession
       fetch authenticated V1 ingress rows
       ensure local transcript directory/backend
       zero-content guard? return without replacement
       otherwise replace local transcript
       record ingress URL; return success/failure
```

## Confidence ledger

| Finding | Confidence | Anchor |
|---|---|---|
| Local transcript append routes and queues rows | VERIFIED-STATIC | `chunk-phacttch.js@4587783` |
| Mirror owner tracks queues/readers/writers | VERIFIED-STATIC | `chunk-phacttch.js@4558167` |
| `persistToRemote` filters and writes supported event classes | VERIFIED-STATIC | `chunk-phacttch.js@4590886` |
| Internal and worker mirror operations are separate | VERIFIED-STATIC | `chunk-phacttch.js@4592007`, `@4592430` |
| Agent transcript hydration is bounded/deduplicated/create-only | VERIFIED-STATIC | `chunk-phacttch.js@4594002`, `@4594403` |
| General V1 `hydrateRemoteSession` body and URL-resume caller | VERIFIED-STATIC | `chunk-phacttch.js@4614350`; `chunk-fzzrkchm.js@681312`; alias `chunk-1stv0pyw.js@18425` |
| Fallback remote persistence is serialized per session and carries UUID conflict recovery | VERIFIED-STATIC | `chunk-7rd4vcyz.js@866`; `chunk-phacttch.js@42342`, `@44148` |
| Fallback remote persistence retries ten times with 8-second cap and stops on auth/unrecoverable conflict | VERIFIED-STATIC | `chunk-phacttch.js@42342` |
| Internal writer registration and bridge/CCR adapters are distinct | VERIFIED-STATIC | `chunk-phacttch.js@4555224`; `chunk-2kr6zq6e.js@29677`, `@30760`; `chunk-cest8dre.js@52700` |
| CCR v2 internal events have queue, batch-post, ack, and bounded shutdown paths | VERIFIED-STATIC | `chunk-a5wd77pa.js@79930`, `@81521`, `@82970`, `@95811`; `chunk-cvvnq4he.js@414956` |
| CCR v2 bridge `ne` resolves to `F.writeInternalEvent` through transport construction and wrapper selection | VERIFIED-STATIC | `chunk-a5wd77pa.js@125745`, `@130515`; `chunk-tar8k6v4.js@43925`, `@78732`, `@79043` |
| V1 hydration replacement uses in-place `replaceRecords` without a source-version precondition | VERIFIED-STATIC | `chunk-sy9frekf.js@3491`; caller `chunk-phacttch.js@4614350` |
| V1 hydration helper maps full replacement to in-place V5 replacement without `ifMatch`/stream precondition | VERIFIED-STATIC | `chunk-sy9frekf.js@3000` |
| Transcript UUID removal has stronger caller-side version/retry guards than V1 hydration | VERIFIED-STATIC | `chunk-phacttch.js@4572000`; `chunk-sy9frekf.js@3000` |
| Remote is bidirectionally conflict-resolved and canonical on resume | UNKNOWN | inspected local append/mirror and agent hydration scope |

## Open gaps

1. Additional registry/host callers of `rQr` beyond the direct URL-resume call.
2. Bridge-side observation of the callback's returned promise, server
   durability, crash replay, and remote conflict handling. CCR v2 writer
   identity, queue admission, and HTTP batch settlement are recovered, but do
   not prove that the bridge waits for them or that the server is durable.
3. Shutdown drain and crash consistency for pending mirror queues and V1
   in-place replacement.
4. Exact remote restoration of interrupted turns, compaction boundaries, and
   task state.
5. Whether a failed remote hydrate can trigger local rehydration retries.
