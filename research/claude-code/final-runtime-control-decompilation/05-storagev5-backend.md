# Storage V5 backend contract

Status: `PARTIAL` — the caller-visible V5 contract, provider injection boundary,
record-stream operations, precondition forms, publish disciplines, listing
semantics, and task persistence are `VERIFIED-STATIC`; the provider's own
commit implementation and cross-operation transaction guarantees remain
`UNKNOWN`.

## What was actually recovered

The extracted application does not expose one obvious `StorageV5` class whose
body defines all behavior. Instead, many callers receive a `storageV5` handle
and use a common result-shaped interface. The inspected contract includes:

```text
read(keys[, options])
write(key, bytes/text, {precondition, mode})
delete(key[, expected/precondition])
listEntries(scope, {cursor, skipKeyStats, skipScopeStats, includeValue, ...})
ensureScope(scope)
deleteScope(scope)
update(key, callback/options) in selected callers
```

Operations commonly return `{ok:true,value}` or `{ok:false,error}` rather than
throwing for ordinary backend failures. Callers validate `error.code`, page
cursors, and `found` flags. Some higher-level wrappers convert an unsuccessful
result into a warning/skip; others retry or throw.

The absence of a single recovered implementation is a negative finding about
the inspected application graph, not evidence that no backend exists. The
backend may be supplied by a host/provider boundary or split across imported
modules.

## Namespaces and key scope

Observed key namespaces include `task`, `transcript`, `sidecar`, `session`,
`daemon`, `job`, `plan`, `userConfigDir`, and `log`. Keys carry structured
scope such as project, session, agent id/relative path, list id, run id, and
relative path. Callers do not generally concatenate user strings directly;
they sanitize identifiers before constructing V5 keys.

The task backend is the clearest complete caller contract. `chunk-zkrrxfpr.js`
uses task-list/list-id scope around `@6323`, validates task payloads around
`@3400`, allocates ids around `@9581`, restores specific tasks around
`@12065`, reads/validates around `@12749`, updates around `@14227`, deletes and
cleans dependency references around `@14521`, lists around `@15083`, and
creates restorable snapshots around `@15407`/`@15961`.

## Conditional writes and task consistency

Task id allocation uses a high-water-mark key plus an if-absent write. A
collision is treated as an already-existing/uncertain id and the allocator
advances. Restoring a task raises the high-water mark. Task updates retry
bounded lock/unavailable conditions; deletion rewrites remaining dependency
references. These are per-task/list consistency rules, not proof of an atomic
transaction over the whole list.

The V5 task path can list values in one operation and otherwise performs
individual reads. It schema-validates each decoded task and sorts by numeric id.
Malformed or missing entries can be skipped. A dependency update touches more
than one task record, but the inspected source does not show a multi-key
transaction primitive around that operation.

## Transcript and sidecar callers

Transcript persistence routes events through an owner with internal event
readers/writers, per-agent mirrors, write queues, pending-write accounting, a
drain chain, and a chunk-size cap (`chunk-phacttch.js@4558167`). The append
router chooses the session/agent transcript, applies event-type policy and
deduplication, and queues the actual write (`chunk-phacttch.js@4587783`).

Precomputed compaction uses V5 for its sidecar when storage-backed mode is
available. The sidecar write/read/delete path validates version, session,
boundary UUIDs, preserved message UUIDs, model and CLI version, token/usage
metadata, and age before applying it. A sidecar write failure leaves the
ordinary local compaction path available; it does not make the sidecar
canonical.

Transcript listings are paged with cursors and bounded budgets. The persistence
sync reader lists transcript scopes and keys and skips/caps work when the
listing is incomplete (`chunk-2kr6zq6e.js@23457`). This is an explicit
availability policy: a capped listing is not silently treated as an exhaustive
snapshot.

## Durability and ordering

The caller-visible local order is generally:

```text
construct validated row/payload
  -> enqueue or issue V5 write
  -> observe {ok/error}
  -> update in-memory/session bookkeeping
  -> optional remote mirror or notification
```

The source does not establish that a successful `write` is fsynced, replicated,
or durable across process crash before the promise resolves. It also does not
establish a transaction that atomically couples a transcript write, a task
write, a sidecar write, and a remote mirror.

### Transcript queue and shutdown ordering (new continuation finding)

The transcript owner adds a more precise local ordering boundary than the
caller-visible V5 contract alone. `appendToFile` refuses new appends after a
`storeFence`, increments `directAppendsInFlight`, and records whether the
append used the V5 backend (`chunk-phacttch.js@4561617`). `drainQueuesOnce`
splices each per-path queue, concatenates adjacent rows until the 100 MiB
chunk cap or a backend-handle change, awaits `appendToFile`, then resolves the
queued entry promises and emits mirrors for the written chunk
(`chunk-phacttch.js@4562282`). A `drainChain` serializes successive drains, so
two scheduled drains do not concurrently write the same owner; this is local
queue sequencing, not a provider transaction.

The error branch logs the write failure, marks writer health, restarts replay
index state, clears queued tool-result digests, resolves the remaining queue
items, and promotes selected wrapped backend errors to `storeFence`
(`chunk-phacttch.js@4562282`). Consequently, an `appendEntry` caller can have
queued a row without receiving a direct rejection from the queue; `flush()` is
the stronger observation point. `flush()` cancels the timer, waits the active
drain, runs another drain, waits tracked writes, drains again, and only then
throws an installed store fence (`chunk-phacttch.js@4572755`).

The process-exit path gives this sequence a bounded finalization window:
`uNs` waits exit-drain callbacks for at most 500 ms, calls the project flush,
performs ancillary cleanup, and on a pinned V5 path gives
`reStampAtExitAsync` another 500 ms before falling back to synchronous
re-stamping (`chunk-phacttch.js@4553729`, `@4565155`). This proves a bounded
best-effort shutdown protocol, not crash durability: timeout or process loss
can still leave queued or remote work absent, and the provider's commit
semantics remain outside the inspected JavaScript.

### Injected remote writer and remote-IO batch boundary

The remote mirror has a second, distinct completion boundary. The persistence
owner registers an injected writer through `x4t`, which delegates to
`setInternalEventWriter`, and registers readers through `P4t`
(`chunk-phacttch.js@4555224`). The bridge/repl setup at
`chunk-2kr6zq6e.js@30760` supplies an adapter that starts `ne(...)`, catches
and logs its failure, and then returns `Promise.resolve()`. Therefore an
`await this.internalEventWriter(...)` in the persistence owner means only that
the adapter returned; on this bridge path it is not an await of the physical
remote write.

The CCR v2 setup at `chunk-cest8dre.js@52700` supplies the corresponding
`ccrClient.writeInternalEvent` adapter. Its body normalizes the event, applies
compaction/preserved-event metadata, and awaits `queueInternalEvents`
(`chunk-a5wd77pa.js@79930`). That method enqueues through the internal uploader
with `together:true` and release bookkeeping (`chunk-a5wd77pa.js@81521`). The
uploader later POSTs `/worker/internal-events`; successful HTTP responses mark
the batch stored and schedule `onInternalBatchAcked`, while retryable failures,
partial-batch splitting, permanent 4xx drops, and ordinary retry errors are
handled by the uploader policy (`chunk-a5wd77pa.js@39222`; batcher
`chunk-cvvnq4he.js@414956`). The CCR client's `flushInternalEvents` exposes a
stronger physical-drain observation point (`chunk-a5wd77pa.js@82970`), and
`finishShutdown` waits for that drain only within a bounded 3-second shutdown
window before closing and signalling the lane (`chunk-a5wd77pa.js@95811`).

Thus the recovered order is: local append/queue, adapter-dependent writer
return, CCR queue admission where applicable, and later HTTP batch settlement.
The source still does not establish server-side durability, replay after a
process crash, or that the bridge adapter's `ne` operation has completed when
its callback promise resolves. This narrows the remote guarantee without
turning the host/provider boundary into an unsupported negative finding.

### CCR v2 bridge callback resolution

The CCR v2 bridge path resolves more of the apparent callback boundary. The
transport constructor `k3r` creates the `GU` worker transport and returns
`getInternalEventWriter(){return(A,W,j)=>F.writeInternalEvent(A,W,j)}`
(`chunk-a5wd77pa.js@125745`, `@130515`). The remote bridge stores that object as
`S` after `await k3r(...)` (`chunk-tar8k6v4.js@43925`). When deferred transcript
work is released, `fo` obtains `S.getInternalEventWriter`, wraps it for event
redaction/live classification, and passes the selected wrapper `v` as the
seventh argument to `fr` (`chunk-tar8k6v4.js@78732`, `@79043`). The
`initReplBridge` callback receives that argument as `ne=e` and invokes
`ne(st,at,$e)` inside the adapter, but returns `Promise.resolve()` immediately
after attaching a rejection handler (`chunk-2kr6zq6e.js@29677`, `@30760`).

Therefore the CCR v2 physical implementation is source-resolved through
`F.writeInternalEvent` and the uploader chain; what remains unresolved is not
the identity of `ne` on this path, but whether the bridge caller observes its
returned promise. Other transport/provider modes and server-side durability
remain outside this conclusion.

## Backend selection

Callers consistently branch on whether `storageV5` exists and otherwise use the
filesystem path. Task persistence, daemon dispatch, plugin/marketplace state,
themes, transcripts, and sidecars each have examples of this selection. The
startup pin carries `backend` plus the config-home identity, rejects a pin when
`CLAUDE_CONFIG_DIR` no longer matches the home used to build it, and hands the
backend into initialization (`chunk-we7c2g4z.js@5566`). The initialization path
passes that backend through credential/config priming and publishes the
resulting V5 handle to host services (`chunk-we7c2g4z.js@5810`). The pin helper
returns `{backend: ... , configHome: ...}` only for the selected host mode
(`chunk-8qnn2dw7.js@816`), while the public facade exposes pin/adopt/try creation
as separate operations (`chunk-bvf52rcv.js@622`). The provider is therefore
handed in at the startup/host boundary rather than constructed by the recovered
caller modules.

### Provider-construction boundary (new continuation finding)

The pin helper makes the boundary narrower than the earlier report stated.
`Xmo` (`pinStorageV5FromEnv`) reads `CLAUDE_CODE_HOVER_REST`, records the
one-time feature decision, and returns `{backend: j()?e():void 0,
configHome: ve()}` only when the process has been pinned into the selected host
mode (`chunk-8qnn2dw7.js@816`). Its default callback is `SSr`; that callback is
an empty provider factory which returns `undefined` even when the mode predicate
is true (`chunk-8qnn2dw7.js@1541`). The mode predicate itself is a one-time
boolean pin (`chunk-xg6d4cp3.js@1137`). The public facade only re-exports these
helpers; it does not add a backend implementation (`chunk-bvf52rcv.js@622`).

The normal CLI initialization call is `i??=Xmo()` followed by config and
credential priming, and later `MG(i)`/`Ufo({storageV5:n,...})` publishes the
selected handle (`chunk-we7c2g4z.js@5566`, `@5810`). The daemon path likewise
calls `MG(e)` before using the returned handle (`chunk-39q3j8sd.js@72433`).
Exact token/import inspection found no extracted JavaScript call that supplies a
non-default `Xmo` factory, and no provider class body behind `SSr`. This is a
`VERIFIED-STATIC` boundary finding within the inspected `~BUN/root` extraction,
not proof that a native/host provider does not exist. The provider constructor,
commit protocol, and host-to-bundle injection remain `UNKNOWN`.

## Recovered record-stream and publish contract

The backend is not limited to byte-file CRUD. A V5 key can be wrapped as
`{backend, key}` and consumed through record operations: `append`, paged
`readRecords` with forward/backward order and sequence cursors, `statStream`,
and `replaceRecords` (`chunk-8hbrzh7z.js@21826`; `chunk-phacttch.js@4530864`).
Transcript compaction requests an atomic replacement with
`precondition:{type:"ifUnchangedThrough",seq,version}`, `preserveFrom`,
`publishDiscipline:"atomic"`, and `parent:"mustExist"`
(`chunk-phacttch.js@4580562`). Tombstone removal uses the weaker in-place
discipline with `keepBefore`/`preserveFrom` and an `ifMatch` or stream version
precondition (`chunk-phacttch.js@4532863`; `chunk-phacttch.js@4575098`). A
precondition failure causes the caller to report `source_changed` or abandon
the rewrite, rather than silently retrying indefinitely. These call sites prove
the requested compare-and-publish contract and caller behavior; they do not
prove how the injected provider implements atomicity, fencing, or durability.

The same provider boundary supports metadata/stat and file-like operations.
For example, session code uses `statMeta` to distinguish a missing artifact
before falling back (`chunk-phacttch.js@4590675`), and other callers use
`ensureScope`, `listEntries`, `read`, `write`, `touch`, `delete`, and
`deleteScope`. The visible error vocabulary includes `NotFound`,
`PreconditionFailed`, `Unavailable`, `InvalidArgument`, and `Failed`, with
optional phase/telemetry and retry information. The provider owns final error
mapping; callers implement policy around it.

### V5 stream mutation and restoration guards (new continuation finding)

The extracted callers do not all use the same replacement discipline. The
workflow journal's V5 implementation reads paginated records with a forward
sequence cursor and rejects a non-advancing cursor. Its restore operation first
deletes the old journal key and then appends the `restoring`/payload/`restored`
records; no transaction or precondition is passed at this caller boundary
(`chunk-8hbrzh7z.js@20800`). A failure between those two provider calls is
therefore not shown as an atomic restore by the JavaScript caller.

Transcript reverse scans are more defensive. `Ktr` reads backward pages,
retains the last record from the prior page, and compares both sequence and
bytes when the overlap is returned. If the stream changed between pages it
throws and abandons the scan (`chunk-phacttch.js@4527000`). The fast
`removeByUuidV5` path supplies the observed stream version as an `ifMatch`
precondition to an in-place `replaceRecords`; it retries at most three times on
`PreconditionFailed` or `Unavailable`, and delegates tail misses to the slow
path. The slow path forward-scans to the target sequence, checks cursor
advancement and a maximum-read budget, and updates the `ifMatch` version after
each paged replacement (`chunk-phacttch.js@4572000`). These are optimistic
caller-side race guards, not proof that the provider's replace is transactional
or that a failed retry leaves no partial publication.

This separates three superficially similar operations: transcript compaction
requests atomic publish with `ifUnchangedThrough`; transcript UUID removal
requests in-place publish with `ifMatch`; workflow-journal restoration does
delete-then-append without a visible precondition. The distinction is
source-backed and should not be collapsed into a single generic “V5 write”
guarantee.

## State machine

```text
caller selects V5 or filesystem
  -> build sanitized namespace/key
  -> read/list/write/delete with result object
       success -> validate/decode -> update local state
       not found -> caller-specific miss/rebuild
       conflict/lock/unavailable -> retry, skip, or surface failure
       capped listing -> partial result policy
  -> optional queue drain / remote mirror
```

## Confidence ledger

| Finding | Confidence | Anchor |
|---|---|---|
| V5 task namespace and CRUD caller contract | VERIFIED-STATIC | `chunk-zkrrxfpr.js@6323`, `@9581`, `@12065`, `@12749`, `@14227`, `@14521`, `@15083`, `@15407` |
| Task id allocation uses high-water mark and conditional creation | VERIFIED-STATIC | `chunk-zkrrxfpr.js@9581` |
| Transcript writes are queued/routed/deduplicated | VERIFIED-STATIC | `chunk-phacttch.js@4558167`, `@4587783` |
| V5 listings are cursor/budget bounded in persistence sync | VERIFIED-STATIC | `chunk-2kr6zq6e.js@23457` |
| V5 can be replaced by filesystem callers | VERIFIED-STATIC | `chunk-zkrrxfpr.js@12749`, `@15083` |
| Startup pins/adopts an injected backend and publishes the V5 handle | VERIFIED-STATIC | `chunk-we7c2g4z.js@5566`, `@5810`; `chunk-8qnn2dw7.js@816`; `chunk-bvf52rcv.js@622` |
| Default pin path has no recovered provider factory; backend construction is outside the inspected JS path | VERIFIED-STATIC / UNKNOWN at boundary | `chunk-8qnn2dw7.js@816`, `@1541`; `chunk-xg6d4cp3.js@1137`; exact-token scope over `~BUN/root` |
| V5 supports record streams, cursors, preconditions, and publish disciplines | VERIFIED-STATIC | `chunk-8hbrzh7z.js@21826`; `chunk-phacttch.js@4532863`, `@4580562` |
| Workflow-journal V5 restoration is delete-then-append; paged reads reject a non-advancing cursor | VERIFIED-STATIC | `chunk-8hbrzh7z.js@20800` |
| Reverse transcript scans detect mutation between pages by sequence/data overlap | VERIFIED-STATIC | `chunk-phacttch.js@4527000` |
| V5 UUID removal uses bounded optimistic `ifMatch` retries and a size/cursor-guarded slow path | VERIFIED-STATIC | `chunk-phacttch.js@4572000` |
| Transcript appends use a per-owner drain chain and chunked queue; queue failures install a store fence | VERIFIED-STATIC | `chunk-phacttch.js@4561617`, `@4562282` |
| `flush()` is the stronger local write-completion observation point | VERIFIED-STATIC | `chunk-phacttch.js@4572755` |
| Exit flush and V5 re-stamp are bounded to 500 ms each | VERIFIED-STATIC | `chunk-phacttch.js@4553729`, `@4565155` |
| Internal writer registration is injected through bridge/setup functions | VERIFIED-STATIC | `chunk-phacttch.js@4555224` |
| Bridge writer callback resolves before its launched `ne` operation is proven complete | VERIFIED-STATIC | `chunk-2kr6zq6e.js@30760` |
| CCR writer awaits queue admission and batches internal events | VERIFIED-STATIC | `chunk-cest8dre.js@52700`; `chunk-a5wd77pa.js@79930`, `@81521` |
| Physical internal-event POST, batch acknowledgement, and bounded shutdown flush are implemented | VERIFIED-STATIC | `chunk-a5wd77pa.js@39222`, `@82970`, `@95811`; `chunk-cvvnq4he.js@414956` |
| CCR v2 `ne` resolves to the transport's `F.writeInternalEvent` through `k3r` and `a5o` | VERIFIED-STATIC | `chunk-a5wd77pa.js@125745`, `@130515`; `chunk-tar8k6v4.js@43925`, `@78732`, `@79043`; `chunk-2kr6zq6e.js@29677` |
| One low-level backend class defines all V5 semantics | UNKNOWN | provider is injected at the startup/host boundary; no implementation body is present in the inspected JS scope |
| Successful V5 write is crash-durable and cross-key transactional | UNKNOWN | no provider commit/transaction body recovered |

## Open gaps

1. Definitive provider/backend implementation behind the startup/host injection (including any native or host-side factory).
2. Transaction, fencing, and write-queue flush semantics.
3. Crash consistency and process-exit drain guarantees.
4. Full feature-gate path selecting V5 versus filesystem per namespace.
5. Conflict behavior for multi-key task/dependency updates.
