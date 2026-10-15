# Permission UI and approval lifecycle

Status: VERIFIED-STATIC for decision recording and host/remote dispatch; PARTIAL for the terminal dialog renderer and queue-level UI details.

## Decision engine

The permission decision functions in `chunk-phacttch.js@1879000` separate telemetry, decision classification, and application. `P2t` records config/classifier/user/hook grants; `M2t` records denials; `XQo` records that a permission request was shown, including permission mode and origin. `$Fo` maps a host answer to accept/reject, including permanent-user decisions when the answer or updated permissions target a persistent destination. Abort becomes `user_abort`; hook allow/deny and a recheck/config acceptance are separate classifications. `vCn` applies the mapped result, while `JQo` records the final decision in the session's `toolDecisions` map keyed by tool-use id, with source, decision, timestamp, and surface, and emits `Us("tool_decision", ...)`.

`O2t` classifies why the result happened (rule source, permission mode, hook, classifier, subcommand, permission-prompt tool, and related reasons). This classification is not merely model-facing text: it is stored with the tool decision and drives telemetry.

## Updated permissions

The `updatedPermissions` validator at `chunk-phacttch.js@542233` caps and sanitizes returned rules/directories. It limits the update payload to 4096 entries/units as implemented, validates rule shapes, and injects the deny sentinel `EU` on malformed or oversized content. Persistent destinations are `session`, `localSettings`, `projectSettings`, and `userSettings` (`G_t` in the same region). The source distinguishes a one-call/session grant from an update intended to persist beyond the current call.

## Host and remote approval dispatcher

`TransportPermissionDispatcher` in `chunk-9w4htdvs.js@222803` handles answers arriving from a remote host/subagent surface. An allow answer sends behavior `allow`, updated input, and permission updates. A deny answer sends feedback and can interrupt the call. Cancellation becomes a user-aborted denial; exceptions become a dialog-failed denial. `cancel` aborts in-flight requests, and `drain` denies pending requests during unmount. This is the concrete pending-request lifecycle for nonlocal approval surfaces.

```text
tool call
  -> permission engine / rule + mode + hook/classifier checks
  -> ask request + XQo telemetry
  -> local UI or transport dispatcher
  -> $Fo maps answer
  -> vCn/JQo apply, persist optional rules, record tool decision
  -> allow with possibly rewritten input / deny with feedback / abort
```

## Permission modes

The mode path around `chunk-phacttch.js@3314070` and `@3196358` includes `acceptEdits` handling for recognized safe commands and routes `bypassPermissions`/`dontAsk` through the main permission flow. The broader mode set already documented in `static-04-tools-permissions-hooks.md` includes plan/default/acceptEdits/dontAsk/bypassPermissions/auto where enabled. This pass found no evidence that dynamic plugin/MCP tools bypass the same engine; they enter ordinary dispatch with their tool name and context.

## UI boundary and limitations

The source clearly records and transports the decision, but the general interactive terminal dialog body was not fully isolated from the renderer bundle. `chunk-9w4htdvs.js` contains the auto-mode confirmation surface near `@997451` and the transport approval dispatcher, but this is not a complete proof of the local dialog's component state, focus order, or simultaneous-request queue. The previous research's UI observations should therefore remain descriptive rather than treated as a complete UI decompilation.

## Race behavior

- Cancellation drains pending remote approval requests as denies.
- Hook denial is distinct from user denial.
- Persistent permission updates are applied only after validation.
- A decision is recorded per tool-use id, preventing a later result from being mistaken for an unclassified approval.
- Concurrent local approval queue ordering and replacement after compaction are not fully recovered.

## Confidence table

| Claim | Confidence | Anchor |
|---|---|---|
| Permission request/decision sources are classified and recorded | VERIFIED-STATIC | `chunk-phacttch.js@1879000` |
| Persistent permission updates are validated and bounded | VERIFIED-STATIC | `chunk-phacttch.js@542233` |
| Host/remote approval supports allow, deny, cancel, error, cancel, and drain | VERIFIED-STATIC | `chunk-9w4htdvs.js@222803` |
| Modes route through shared permission machinery | VERIFIED-STATIC | `chunk-phacttch.js@3196358`, `@3314070` |
| Complete local interactive dialog state machine recovered | UNKNOWN | inspected dispatcher and renderer references; full UI component remains unresolved |

Open: exact local prompt queue implementation, timeout policy, simultaneous approval rendering, and whether a permission decision can be replayed after resume without a new UI request.
