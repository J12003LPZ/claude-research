# Final reconstruction

Claude Code 2.1.296 combines a turn-local tool scheduler, a two-route compaction controller, queued detached work, dynamic plugin/MCP registries, local transcript persistence with optional remote mirroring, and a shared permission/task system.

The tool scheduler first partitions requests into consecutive concurrency-safe groups and unsafe barriers. Safe groups use a bounded generator pool and yield completions as they settle; unsafe tools run one at a time. Each result is matched by tool-use id, passed through shared validation/hooks/permission/call machinery, and merged into the caller's context. This is not an unrestricted Promise.all and has no recovered dependency graph beyond grouping/barriers.

Compaction has a precomputed sidecar path and a reactive fallback. Precomputation arms ahead of the threshold, stores a summary/coverage sidecar, and later swaps it only when coverage and cache conditions match. Reactive compaction checks gates, may reuse the precomputed summary, otherwise runs PreCompact hooks and a summary engine, then rebuilds preserved rows, instructions, memory/read state, and compact-boundary/session-start events. Ordinary compaction's failure breaker is not the same as the reactive failure route, explaining the prior runtime contradiction without claiming that all failure modes are safe.

Detached work is registered with an abort-linked task record. On completion, Claude persists a tool-result row, spills large output to a file when needed, and enqueues a task notification with `priority:"next"`. That queue entry can be consumed by a later admitted turn; source evidence does not prove that every completion independently starts a new API request.

Plugins load commands/skills from bounded scans and inline metadata, normalize them with plugin identity and restrictions, and reload at quiet points. Plugin MCP servers join the general pending/reconnect lifecycle. MCP tools receive aliases, deferred announcements, generation checks, live listing refresh, and ordinary permissions. A tool can become available between turns without changing the already-sent model request.

Transcript persistence routes rows to local/session/agent queues and optionally mirrors them through `internalEventWriter` or remote ingress. Storage V5 is explicit for task namespaces and high-water marks, with collision-safe IDs, per-task updates, dependency cleanup, and bounded compaction carry. Remote mirroring is an auxiliary path; the source does not establish remote canonicality.

Permissions are source-classified and recorded per tool-use id. Host/remote approval dispatch supports allow, deny, cancel, error, cancellation, and drain. Task tools use a durable schema with ownership/dependencies and separate from TodoWrite's in-memory per-agent checklist. TaskCreate hooks can roll back creation; TaskUpdate hooks can block completion; TaskStop resolves ownership and task-type killers and may cascade related agents.

The reconstruction is evidence-backed but incomplete at the dynamic boundaries: global caller exhaustiveness, local dialog UI state, the low-level Storage V5 backend, full remote hydration, transport-specific MCP failure races, and host wake policy. Those boundaries are explicitly recorded rather than filled with architectural assumptions.
