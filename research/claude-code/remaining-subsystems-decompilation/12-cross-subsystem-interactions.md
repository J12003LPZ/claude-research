# Cross-subsystem interactions

## 1. Compaction while tools are running

Proven: the normal tool batch yields results into the turn context, while compaction is selected by the query loop and can be reactive/precomputed. The detached path persists a result and queues a notification. Not proven: a single global lock that prevents compaction from starting while an arbitrary foreground tool is still running. The result router has held/late-result state (`Zp` in `chunk-fzzrkchm.js@137755`), so a result can be retained while input is closed or tasks remain, but the exact interaction with `pir` is unresolved.

## 2. Tool-result ordering and asynchronous execution

Safe tools are grouped consecutively; `uEn` yields generator completion order within a safe group, while unsafe tools form sequential barriers. The outer runner merges context layers after the group and the caller persists/forwards results. This means completion order can differ from request order inside a safe group, but groups and unsafe barriers preserve dependency-like sequencing. Runtime E08 observed one merged user message with three tool results, confirming the static delivery shape.

## 3. Background completion after parent idle

Proven: detached completion is persisted and enqueued as `task-notification` with priority `next`. Whether that queue entry immediately causes another model request depends on the loop/host wake policy; the source includes explicit user-wake limitations and separate loop/schedule wake sources. Automatic local resumption is therefore conditional, not universally established.

## 4. Background results across restart

Proven: completion results are routed through session persistence before notification, and remote/agent transcript hydration is bounded and create-only when no local write exists. Exact restart recovery of every detached result, especially after a crash between persistence and notification, is unknown.

## 5. MCP availability during a conversation

Proven: deferred tools are announced by records/deltas; ToolSearch waits for pending/changed MCP servers, refreshes the active registry, and returns `tool_reference` blocks. Availability can change between turns. An in-flight model request is not statically rewritten; a newly selected tool enters later dispatch.

## 6. MCP disappearance during a pending call

Proven: pending/failed/generation checks exist and stale listings are removed. The exact post-send transport behavior is unknown; the common invocation/result path supplies the best evidence-backed failure boundary.

## 7. Subagent restrictions and plugin tools

Proven: plugin/MCP tools are normalized into ordinary tool records and enter shared permission/validation/hooks dispatch. `CXt` explicitly refuses detachment for agent/inner/remote calls. Complete propagation of plugin restrictions into every subagent flavor remains open.

## 8. Interrupted tool calls after restoration

Proven: tool-result reconstruction code marks missing tool results as interrupted in `chunk-phacttch.js@...` and the persistence layer stores transcript rows/compaction boundaries. The exact restore presentation for every tool type is not fully traced.

## 9. Interactive permission with concurrent tools

Proven: permission decisions are keyed by tool-use id and safe grouping only begins after concurrency classification; dynamic tool calls use the same permission engine. The local UI's concurrent approval queue/order is unknown, so no stronger claim is made.

## 10. Compaction failure during multi-agent work

Proven: reactive failure returns structured failure and the ordinary compaction path has a failure breaker for its own route; query-loop retry and precomputed swap are separate. Background/task state is independently persisted and task snapshots may be carried through compaction. Exact behavior when several detached agents complete while compaction is failing remains open.

## 11. Task notifications and conversation history

Proven: notifications are queued as task-notification messages, with task snapshots/attachments and transcript persistence. The source distinguishes task notification provenance from human prompts. Whether every notification is durably inserted before a compaction boundary is unresolved.

## 12. When asynchronous work causes another request

Proven: `priority:"next"`, `background_requested`, loop/schedule wake sources, and queued message routing can make another turn possible. Not proven: detached completion alone is sufficient in all interactive/headless modes. External host initiators and idle-session policy remain part of the unresolved boundary.
