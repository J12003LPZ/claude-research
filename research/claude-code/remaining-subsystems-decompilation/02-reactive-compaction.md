# Reactive compaction — Claude Code 2.1.296

Status: **PARTIAL / VERIFIED-STATIC with VERIFIED-RUNTIME cross-checks**

This report covers the reactive compaction path in the extracted 2.1.296 bundle. It does not claim that every host-specific or dynamic caller has been recovered. The principal implementation is in `chunk-phacttch.js`; the query-loop consumer is in `chunk-93pksqr2.js`.

## Executive result

Reactive compaction is a one-shot guarded recovery operation, not an alias for ordinary automatic compaction. `pir` first applies a strict eligibility predicate (`hXr`), optionally reuses a compatible precomputed swap, runs PreCompact hooks, asks `yXr` to summarize, records failure without throwing to the caller, and returns either a replacement result or a structured failure. The query loop then either retries with reconstructed messages or surfaces `prompt_too_long` / `image_error` / `blocking_limit`.

The source also contains a separate three-failure breaker in the ordinary `Tir` automatic route. Existing E35–E37 runtime captures exercised the reactive route and repeatedly failed without that breaker. The static code explains that the reactive function itself does not update the ordinary failure counter; it does not prove which mode-specific owner omitted that update.

## Entry points and call path

```text
query loop Ad (chunk-93pksqr2.js@~182000)
  -> tqt callback adapter (chunk-phacttch.js@857724)
     -> pir (chunk-phacttch.js@2518325)
        -> hXr eligibility gate (@2518186)
        -> optional xXr reuse test / precomputed result
        -> XEe PreCompact hook
        -> yXr reactive summary request
           -> hke summary engine
        -> fir post-processing and state reconstruction
  -> retry transition reactive_compact_retry
  -> or return prompt_too_long / image_error / blocking_limit
```

The `tqt` adapter is an async generator that forwards compact progress, notifications, and response-length events while awaiting a callback (`chunk-phacttch.js@857724`). This means the compaction request is observable by the same event channel as the surrounding query loop; it is not a detached background task.

## Eligibility gate

`hXr` at `chunk-phacttch.js@2518186` returns true only when all of the following hold:

```text
!hasAttempted
&& !excludedQuerySource(querySource)
&& (hasPrecomputedSwap || !compactIsDisabledForSource(querySource))
&& autoCompactionEnabled()
&& reactiveCompactionAvailable()
&& !aborted
```

The caller passes `hasPrecomputedSwap` when a precomputed swap is available. Consequently, a prior reactive attempt normally prevents another reactive attempt in the same guard state, while a compatible precomputed swap can authorize the route even when ordinary source gating would reject it.

Confidence: **VERIFIED-STATIC**, `chunk-phacttch.js@2518186`; the exact feature-flag providers behind `Zp()` and `r$()` are outside this function body.

## `pir` state machine

`pir` at `chunk-phacttch.js@2518325` has these branches:

1. Read `hasAttempted`, query source, abort status, current messages, precomputed swap, precompute outcome, token-gap estimate, threshold source, and fallback permission.
2. Reject immediately with `{result:null, hookBlocked:false}` if `hXr` is false.
3. Emit `tengu_reactive_compact_triggered` with model-effort, query source, precomputed kind/failure cause, and threshold source.
4. Define a compaction callback `nt` used by the compaction API.
5. If a precomputed swap exists, call `xxr` to compare the precomputed coverage with the current sent/received rows.
   - `refuse`: report the reason to the precompute manager.
   - `reuse`: keep the precomputed summary, attach the newly arrived tail, emit compact progress, and either return a replacement message set or call `fir` with `precomputed:true`.
6. If the swap is not reused, emit PreCompact progress and invoke `XEe`.
   - A `blockedBy` hook result returns a skip object whose reason is prefixed by the internal hook-block marker.
   - Hook-provided instructions are merged into the summary request.
7. Call `yXr` with `trigger:"auto"`, the current messages, cache-safe parameters, initial token gap, threshold source, precomputed metadata, and `allowLastResort`.
8. On a successful summary, `dt` validates the result, extracts the compact boundary and messages, and returns the reconstructed compact result.
9. On API/summary failure, return `{result:null, hookBlocked:false, failure:{reason,detail}}`; a failure does not itself increment the ordinary `Tir` failure counter.
10. On a skipped result, mark the precompute state as skipped, optionally notify the user, clear SDK status, and return `hookBlocked:true`.
11. On final reconstruction failure, log the failure and return a structured failure rather than allowing an uncaught exception to escape.

## Summary request and failure recovery

`yXr` at `chunk-phacttch.js@2524076` calls `hke` and then `fir` at
`@2526075`. It clears the compact event callback in a `finally` block. If the
abort signal becomes set after a nominally successful summary, it converts the
result to `{ok:false, reason:"aborted"}`. It logs
`tengu_reactive_compact_failed` with attempts, group counts,
split/head-truncation data, threshold source, precompute metadata, and abort
classification.

`fir` at the following region performs the stateful commit:

- clears `readFileState` and resets memory selection;
- clears remote/main compaction caches where applicable;
- creates/updates the compact boundary metadata;
- preserves selected messages and attachments;
- runs post-compact and SessionStart(compact) hooks;
- appends hook results and reattached state;
- records pre/post token counts and summary usage;
- emits `tengu_reactive_compact_succeeded`.

The full compaction result is therefore not just a summary text. It is a boundary marker plus summary messages, preserved tail, attachments, hook results, and user display text.

## Query-loop retry and terminal branches

The query loop in `chunk-93pksqr2.js` calls the reactive route after a withheld prompt-too-long/media response. If compaction returns a usable result, it rebuilds `Q` with:

```text
hasAttemptedReactiveCompact = (precomputedSwap === undefined)
reactiveCompactDeeperPass = next deeper-pass state
transition.reason = precomputed_compact_swap | reactive_compact_retry
```

It then continues the model loop. If no usable result exists, it emits the prompt-too-long or image error to the user. If the token state is already blocked after a failed attempt, it returns `blocking_limit` without sending another model request (`chunk-93pksqr2.js@149346`).

The reactive path has a special deeper-pass rule. On a retry after a prior reactive compact, it may proceed when `reactiveCompactDeeperPass === "available"`; the source allows the rapid-refill calculation to proceed in that case rather than immediately treating the repeated attempt as an ordinary new compact.

## Failure-breaker contradiction

The ordinary automatic path `Tir` at `chunk-phacttch.js@2594742` contains:

```text
if (precomputeCandidate === undefined && tracking.consecutiveFailures >= Won)
    return {kind:"failure_breaker_open"}
```

`Won` is three. The ordinary failure updater `Uon` is at
`chunk-phacttch.js@2591982`; it increments the tracking field and emits
`tengu_auto_compact_circuit_breaker`. Successful compaction resets it through
`v5r` near `@864500`.

There is a second, different breaker on the query-loop response path. The
loop computes `vrr(et)` after a withheld prompt-too-long or request-too-large
response and trips only when the prior compact was followed by three rapid
refills; it then returns an API-error-shaped `autocompact_thrashing` result
with terminal reason `rapid_refill_breaker`
(`chunk-93pksqr2.js@180300`). This is not the ordinary failed-summary counter.
The query loop also sets `hasAttemptedReactiveCompact` and the deeper-pass
state when rebuilding `Q` after compaction (`chunk-93pksqr2.js@183991`).

However, `Tir` routes to `pir` whenever a reactive handler exists and the threshold source is not `auto`, or when classifier overflow/model override conditions select that route (`chunk-phacttch.js@2594742`). The reactive `pir` body returns structured failure but contains no call to `Uon`. The query-loop state instead controls repeated reactive attempts through `hasAttemptedReactiveCompact`, deeper-pass state, and the blocking-limit branch.

Existing E35–E37 captures are **VERIFIED-RUNTIME** evidence that 5/25 reactive failures were retried without `failure_breaker_open`, ending in `blocking_limit`. The combined conclusion is:

- **VERIFIED-BOTH:** the ordinary failure breaker exists and the observed runs were on the reactive route;
- **CONTRADICTED:** “three failed reactive summaries always open the ordinary failure breaker”;
- **UNKNOWN:** whether the reactive counter is intentionally absent, maintained by an unobserved host/stream-json wrapper, or only updated on the non-reactive route.

No source evidence justifies claiming the discrepancy is caused by a feature flag alone.

## Context and thresholds

`Tir` delegates threshold calculation to `scr`, `Jae`, and related helpers. The previously verified threshold contract remains: effective model window minus output reservation, auto-compact threshold, warning level, and a hard blocking level. The reactive call receives `initialTokenGap` when the server supplied a parsable overflow amount; this is used by the summary request and later gap-guided retry logic.

## Cancellation and errors

- Abort before eligibility: no compaction request.
- Abort during summary: result converted to `reason:"aborted"`.
- PreCompact hook block: surfaced as `hookBlocked`, and the enclosing loop can skip or surface the original error.
- Summary/API failure: structured failure with reason/detail; no uncaught throw at the `pir` boundary.
- Failure after result creation: reconstruction failure is recorded and returned as a structured failure.
- Query-loop failure after no recovery: the original withheld error is yielded and the turn terminates locally.

## Open gaps

1. The exact body and all callers of `Uon` were not exhaustively recovered in this pass.
2. The source of the `r$()` reactive availability predicate and its host-mode differences is not fully decompiled.
3. The detailed `hke` group-selection algorithm is shared with the broader compaction engine and only partially covered by the earlier report.
4. The precise stream-json state owner for `consecutiveFailures` remains unresolved; existing runtime evidence only scopes the contradiction to the reactive route.
5. Concurrent tool execution versus a reactive compaction trigger is not proven to serialize at this layer.

## Evidence anchors

| Claim | Anchor | Confidence |
|---|---|---|
| Reactive eligibility gate | `chunk-phacttch.js@2518186` | VERIFIED-STATIC |
| Reactive controller `pir` | `chunk-phacttch.js@2518325` | VERIFIED-STATIC |
| Summary/reconstruction helper `yXr`/`fir` | `chunk-phacttch.js@2524076`, `@2526075` | VERIFIED-STATIC |
| Ordinary failure updater | `chunk-phacttch.js@2591982` | VERIFIED-STATIC |
| Query-loop rapid-refill breaker and guard update | `chunk-93pksqr2.js@180300`, `@183991` | VERIFIED-STATIC |
| Auto route and reactive routing | `chunk-phacttch.js@2594742` | VERIFIED-STATIC |
| Query-loop retry/terminal handling | `chunk-93pksqr2.js@~180652-184635` | VERIFIED-STATIC |
| Repeated reactive failures without breaker | `03-runtime-experiments.md`, E35–E37 | VERIFIED-RUNTIME |
| REA parsed `chunk-phacttch.js` completely | retained REA evidence `ev_84ba937cf1929d4a0c62ebf0a747b20811040a04269d8760919ff468e7382205`, module view `ev_6ef760e9fa05ba3251bfe53f0d4eb6c030dd0a185fe6dda532fb54900fa7ea56` | VERIFIED-STATIC |

