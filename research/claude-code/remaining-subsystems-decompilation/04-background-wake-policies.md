# Background results, notifications, and wake policies

Status: PARTIAL / VERIFIED-BOTH where noted. The detached-tool path is statically reconstructed. Audit correction: an eligible detached completion is proven to kick an idle, input-open local main loop; universal host/remote wake is not proven.

## Audit correction

The earlier wording below was too broad. `hge` enqueues a normal completion as
non-passive `mode: "task-notification"`, and `Zf` accepts owned, non-passive
queue items without requiring prompt mode (`chunk-phacttch.js@218545`,
`chunk-phacttch.js@2217060`). The queue subscriber's `nw` predicate checks that
the main drain is idle, input remains open, and `peek(Zf)` succeeds; `ow` then
invokes the local `Em.run` kick (`chunk-fzzrkchm.js@224541`, setup at
`chunk-fzzrkchm.js@559872`). Thus detached completion does automatically start
the local main drain under those conditions. The query policy can still stop
before an API request (`chunk-93pksqr2.js@134303`), and external/remote wake
behavior remains unresolved. The more complete reconstruction is in
`research/claude-code/final-runtime-control-decompilation/01-host-wake-and-resumption.md`.

## Scope and evidence

The defining detached execution path is in `chunk-phacttch.js@2216254` (`aqe`, `CXt`, `Ejo`, and the notification helper `hge`). The normal turn loop and result routing are in `chunk-93pksqr2.js@134303` and `chunk-fzzrkchm.js@137755`. The reported offsets are character offsets in the extracted 2.1.296 bundle, not source-map line numbers.

## Detached task lifecycle

`aqe(tool, context, options)` is the admission gate. It returns true only when the tool's backgrounding policy is `detach`, the call is not an agent/inner/remote call, the session is allowed to detach, no stop condition is pending, and `tengu_tool_detach` is enabled. It refuses detachment when PostToolUse/PostToolUseFailure/PostToolBatch hooks or a `tool.call` hook are active. Thus detachment is not merely a property of the tool; it is a property of the tool plus the current hook and execution context.

`CXt({tool,input,toolUseID,toolUseContext,onProgress,run})` creates a child abort controller and links the parent signal. It starts `run` and records the task in the session task registry. A `backgroundNow()` callback calls the registry's `letGo` operation and resolves the foreground promise early. Once detached, it records a detach timestamp, emits `tengu_tool_call_detached`, registers a ceiling timer (`Xme`), and returns control without an inline tool result.

The completion path settles the registry record as completed and calls `Ejo`. Exceptions mark the task stopped/failed, emit the failure notification path, and do not become a normal synchronous tool result. Parent cancellation propagates to the child controller; the ceiling timer is a separate upper-bound termination path. Exact timer cleanup is present in the implementation, but the full task-type-specific kill matrix is in the task registry and remains only partly resolved here.

## Result persistence and notification

`Ejo` converts the completed result into a tool-result block using `sCe`, persists it through the session storage path, and checks `stillHeard` before delivery. If the conversation has been cleared, the result is dropped rather than injected into a different conversation. Long textual output is redirected through `_4` when it exceeds `lMt - 2000` (`RXt`); the notification then points to the saved file. A failed save produces a failed notification.

The notification helper `hge` calls `Qa` with a `Hi(...)` task notification carrying task id, tool-use id, task type, status, summary, and body/output metadata. It sets `mode: "task-notification"`, `priority: "next"`, `skipAttachments: true`, and inherits turn attribution. `Y.resultQueued(...)` records that the result has entered the delivery path. This is the concrete local completion-to-message bridge.

```text
tool call
  -> aqe admission
  -> CXt child run + registry record
       | foreground continuation (backgroundNow)
       | detached execution
       v
  completion/failure
  -> Ejo persist tool result / spill large output
  -> hge -> Qa(task-notification, priority=next)
  -> message/result routing and a later turn if the host/loop admits one
```

## Wake and resume behavior

`priority: "next"` proves queue priority, not that a new API request is unconditionally created. `chunk-93pksqr2.js@134303` has a `background_requested` stop-before-next-api-call branch; the loop checks `shouldStopBeforeNextApiCall()` and can return that reason before another request. The message input path recognizes `mode === "task-notification"` in `chunk-93pksqr2.js@11011` and attaches task delivery provenance. `chunk-phacttch.js@4524558` classifies task notifications separately from human prompts and uses task snapshots for delivery attachments.

The source also contains an explicit user-facing wake limitation near `chunk-93pksqr2.js@56010`: the session will not wake for another check-in until the user sends a message. Separately, hook provenance supports `loop_wakeup`, `schedule_wakeup`, `system`, and `poll_event` (`chunk-80kqkekd.js@194279`). Those are distinct host/loop wake sources; they are not evidence that every detached result itself schedules an autonomous model request.

Therefore the proven local policy is: completion is queued as a high-priority task notification and may be consumed by the next admitted turn. Automatic resumption is conditional on the surrounding loop/host policy. A universal local wake, an external remote wake, and the exact interactive-versus-headless differences remain unresolved.

## Cancellation and races

- Parent abort is forwarded to the detached child controller.
- A ceiling timer can terminate an overlong detached task.
- A completion after conversation clearing is discarded by `stillHeard`.
- Multiple completions are independently registered and queued; deduplication beyond registry/result bookkeeping was not established.
- Persistence occurs before notification, so the result can survive as stored state even when notification delivery is dropped; exact crash ordering across storage and queue is not proven.
- Existing runtime E35/E37 evidence showed background/foreground interruption behavior, but no new runtime campaign was performed. Those captures are cross-checks only, not proof of additional wake behavior.

## Confidence and open gaps

| Claim | Confidence | Anchor |
|---|---|---|
| Detach admission depends on tool policy, context, hooks, and feature gate | VERIFIED-STATIC | `chunk-phacttch.js@2216254` |
| Detached completion persists/spills output and emits a task notification | VERIFIED-STATIC | `chunk-phacttch.js@2217060` |
| Notification is queued with `priority: "next"` | VERIFIED-STATIC | `chunk-phacttch.js@2217060` |
| Queue input is recognized as `task-notification` | VERIFIED-STATIC | `chunk-93pksqr2.js@11011` |
| A runtime batch produced merged tool delivery | VERIFIED-BOTH | E08; runner report and `chunk-jwmqjyrb.js@52813` |
| Every detached completion automatically starts a model request | UNKNOWN | inspected local queue, turn-loop, and wake-source paths; no unconditional edge found |

Unresolved: the complete registry state transition table for every task type, host-triggered wake scheduling, shutdown races after `Ejo`, notification deduplication across resume, and remote-session wake behavior.
