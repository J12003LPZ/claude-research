# Precomputed compaction — Claude Code 2.1.296

Status: **PARTIAL / VERIFIED-STATIC**

This report reconstructs the precomputed compaction arm, its selection/consumption rules, persistence, rehydration, and invalidation. It does not claim all storage backends or all precompute callers are complete.

## Executive result

Precomputed compaction is a speculative sidecar summary maintained in `session.precompute`. It is armed before the context is blocked, computed asynchronously or ahead of the threshold, and later consumed only if its coverage still fits the current message rows. A consumer can borrow a summary from another source key, reuse it with a newly arrived tail, or discard it for explicit drift reasons. A valid precomputed swap is distinct from reactive summarization and causes the query loop to transition with `precomputed_compact_swap`.

## Feature gates and state

`sO` at `chunk-phacttch.js@~2621xxx` requires:

```text
Zp()                         // auto compaction available
&& r$()                      // reactive/precompute capability
&& feature("tengu_sepia_moth")
&& hs("precomputeCompactionEnabled", true).value
```

The sidecar/rehydration path additionally requires `tengu_amber_packet`, the precompute gate, non-diskless operation, and no excluded environment (`xke` near `chunk-phacttch.js@~2621xxx`).

## Arming predicate

`AXr` at `chunk-phacttch.js@2611146` is the precompute arming function. It:

1. returns false when precompute is disabled or the query source is excluded;
2. attempts main-session rehydration via `Jvt`;
3. refuses to arm after `consecutiveCountedFailures >= trn`, where `trn = 3`;
4. refuses when a non-failed entry already exists for the agent key;
5. requires a last message UUID;
6. refuses when the precompute manager vetoes the current message frontier;
7. applies an SDK single-prompt gate when prompt-scan metadata is available;
8. calls `Jvt`/the manager to create or update the pending precompute record.

This is a distinct counter from the ordinary `Tir` failure breaker. The source proves that the precompute manager suppresses further arming after three counted failures; it does not prove that every reactive failure increments that counter.

## Precompute consumption: `PXr`

`PXr` at `chunk-phacttch.js@2618033` is the central consumer invoked by the query loop and by the ordinary auto path. Its control flow is:

```text
G = non-excluded source && precompute enabled
    && (trigger == "threshold" || withheld413 && !hasAttemptedReactiveCompact)
if G: Jvt(...);                         // try rehydrate persisted sidecar
if not G or threshold has no pending record:
    return {outcome:{kind:"none"}, swap:undefined, emittedEarlyCompactStart:false}

record = borrowed source key ? manager.get(borrowed) : manager.get(agent key)
pending = record.status == "pending"
if pending: emit compact-start/requesting/status events
ready = borrowed ? await Mcr(...) : await xXr(...)
if borrowed result absent: fall back to own agent key
if null/aborted/failed: return structured outcome
fit = TXr(ready, sent=current rows, received=current rows, sizing model, window)
if refuse: discard/report reason and return none
return applied swap with coverage, telemetry, replacement flag, and drift data
```

`PXr` never directly edits the transcript. It returns a `swap` object to `pir` or `Tir`, which decides whether to use it. The `swap` records `compactResult`, coverage, replacement status, precompact hook display, pending/ready status, lead and total time, borrowed/rehydrated flags, drift, and fit sizes.

## Coverage and invalidation

`TXr` compares the precomputed coverage with the sent and received row UUIDs and calls `Gon` for fit. A swap is refused for causes including:

- `would_not_fit`;
- `covered_messages_changed`;
- `kept_message_missing`;
- `unseen_reply`;
- `rows_unreadable`;
- model switch or hook rewrite;
- post-compact cleanup/subagent exit;
- already-compacted or missing boundary state.

`Air` records `tengu_precomputed_compact_discarded`, including age, duration, precompact tokens, query source, and optional fit sizes. `xir` aborts and removes the agent-key record, cleans the sidecar, and forgets subagent telemetry when the reason is `subagent_exit`. `uRn` aborts a pending main record on `model_switch`.

## Interaction with reactive compaction

When `pir` receives a compatible precomputed swap, its callback `nt` calls `xxr` with the precomputed coverage and current rows. A `reuse` result appends the uncovered tail and calls `fir` with `precomputed:true`; a `refuse` result reports the reason and falls through to fresh reactive summarization. The query-loop transition is:

```text
swap applied and consumed -> transition.reason = "precomputed_compact_swap"
no swap, reactive summary succeeds -> "reactive_compact_retry"
```

This establishes that precomputed compaction is a fast path with fallback, not an independent terminal path.

## Persistence and sidecar format

The source stores versioned precompute data as `precompact.json`:

- `Yon` serializes and writes it, rejecting payloads over 8,000,000 bytes;
- disk-backed writes use the local path, while remote/storage-backed writes use `storageV5` when available;
- `Qon` and `fcr` read and validate local files;
- `pcr` reads through the storage handle;
- `Jon` tries the canonical path and the suffixed fallback;
- `Rke` deletes the local or storage-backed sidecar.

`gcr` validates the payload shape: version, session ID, main agent key, model, CLI version, creation time, precomputed boundary UUID, token count, duration, summary text/messages, preserved UUIDs, attempt/group counters, and total usage.

The persisted object is not the entire transcript. It is a summary plus a list of UUIDs to preserve and metadata needed to reattach it to the current local transcript.

## Rehydration

`Jvt` at `chunk-phacttch.js@~2625xxx` rehydrates only the main session and only when the sidecar is enabled. It rejects:

1. session mismatch;
2. invalid timestamp;
3. age over `Ecr = 604800000` ms (seven days);
4. already-compacted boundary;
5. missing precomputed boundary UUID;
6. transcript shrinking by more than half of the stored precompact token count;
7. missing preserved UUIDs;
8. unreadable rows.

On success it reconstructs a ready manager record using `Zon`, coverage, stored model/tokens, `rehydrated:true`, and a resolved promise. It emits `tengu_precomputed_compact_rehydrated`; on rejection it queues sidecar cleanup and emits `tengu_precomputed_compact_rehydrate_rejected`.

`CXr` can preload a sidecar during session resolution when the session ID/transcript path is safe and the expected session matches. It uses `Jon` and keeps a sidecar read-ahead result in the manager.

## Persisting a ready result

`xcr` serializes a ready record for the main sidecar. It stores only preserveable message UUIDs (`messagesToPreserve.filter(nS).map(uuid)`), summary text/messages, the precomputed boundary UUID, model and CLI version, token/duration and group metadata, and total usage. A successful write emits `tengu_precomputed_compact_persisted`; an oversized or failed write is reported without changing the transcript.

## Manual and subagent cleanup

The same manager is used by manual/threshold consumers, but the telemetry explicitly labels manual consumption. `Mhe` performs post-compaction cleanup and removes the precompute record; it also resets main-session caches and autonomous-loop state where applicable. Subagent exit removes the associated telemetry/record.

## Cancellation and failures

- Pending records expose an abort controller. `xir` aborts before removal.
- An aborted ready computation returns `{kind:"aborted"}`.
- A failed ready computation returns `{kind:"failed", failure, statusAtPTL}` and remains observable to telemetry.
- A stale/invalid sidecar is discarded rather than applied.
- A precompute write failure does not make the summary canonical; the normal reactive/ordinary path remains available.
- If a borrowed record cannot be applied, the code falls back to the agent’s own record before returning `none`.

## Evidence classification and limitations

All source-flow claims above are **VERIFIED-STATIC** from `chunk-phacttch.js`. Existing runtime captures verified successful rapid-refill behavior and reactive failures, but did not directly exercise sidecar persistence, rehydration, borrowing, or drift rejection; those aspects remain static-only.

REA parsed the module completely within its item view, but the application semantic graph was partial/truncated. Therefore the function bodies are source-verified while global caller exhaustiveness is **UNKNOWN**.

## Evidence anchors

| Claim | Anchor | Confidence |
|---|---|---|
| Precompute feature gate | `chunk-phacttch.js@~2621xxx` (`sO`, `xke`) | VERIFIED-STATIC |
| Arming predicate | `chunk-phacttch.js@2611146` (`AXr`) | VERIFIED-STATIC |
| Consumption/swap | `chunk-phacttch.js@2618033` (`PXr`) | VERIFIED-STATIC |
| Reactive reuse of swap | `chunk-phacttch.js@2518325` (`pir` callback) | VERIFIED-STATIC |
| Sidecar write/read/delete | `chunk-phacttch.js@~2598xxx-2625xxx` (`Yon`, `Qon`, `Jon`, `Rke`) | VERIFIED-STATIC |
| Rehydration validation | `chunk-phacttch.js@~2625xxx` (`Jvt`) | VERIFIED-STATIC |
| Rapid-refill runtime cross-check | `03-runtime-experiments.md` E17c | VERIFIED-BOTH |
| REA source artifact | retained evidence `ev_84ba937cf1929d4a0c62ebf0a747b20811040a04269d8760919ff468e7382205` | VERIFIED-STATIC |

