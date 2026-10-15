# 07. Context and session internals

This report traces the information that survives a long coding session, compaction, interruption, background work, and resume. It distinguishes message preservation from model-generated summaries.

## 1. Loop-side retained context

`Ad` keeps a message list plus compact tracking and tool-use context. At the beginning of each iteration it selects the segment after the last compact boundary, applies tool-result replacement budgeting, and appends queued command or poll-event attachments. **VERIFIED-STATIC**, `chunk-93pksqr2.js@130200` to `@135400`.

The loop yields pre-request attachments for directory sync, post-model-switch hook context, routing records, model announcements, deferred-tool state, and system-prompt snapshots. These are application-generated rows, not model summaries, `chunk-93pksqr2.js@139300` to `@142000`.

Tool result messages are retained as user-role rows paired with the assistant tool-use blocks. If a tool result is too large, the tool-result persistence path writes the full content to a file and sends a bounded preview. **VERIFIED-STATIC**, `chunk-ghf2w5kp.js@1900`, `@5225`; `chunk-fd5j6erd.js@1312` and `@1370`.

## 2. Compaction trigger and boundary

Every loop iteration calls the injected autocompact path before the request, `chunk-93pksqr2.js@136500`. The compaction implementation is `Tir` and its prompt/fallback functions are in `chunk-phacttch.js` around `@2565344`, `@2575000`, `@2578200`, and `@2592000`.

The compaction path can:

1. Determine that compaction is not needed.
2. Request a summary through a cache-sharing fork or direct fallback.
3. Retry a prompt-too-long summary while discarding older round groups, with a bounded retry count.
4. Create a compact boundary and synthetic user summary.
5. Reattach recent file contents, background-task state, plan reference, invoked skills, environment changes, and tool deltas.
6. Return the replacement message list to `Ad`.

`Ske`, `chunk-phacttch.js@2585926`, builds the bounded reattachments. A successful compact yields `compact_progress` and post-compact messages, then the next request uses the compacted history. **VERIFIED-STATIC**.

The compaction summary is model-generated. The boundary, preserved segment, dropped-token counts, and reattachments are application state. The CLI cannot guarantee that the summary faithfully preserves every code fact.

## 3. Context exhaustion and breakers

If compaction succeeds, the loop proceeds with the replacement history. If compaction is not just completed and the context estimator reports a hard blocked level, `Ad` emits a synthetic API error and returns `blocking_limit` before sending the request, `chunk-93pksqr2.js@149549`.

`Tir` has bounded failure handling and a rapid-refill breaker in the `chunk-phacttch.js@2598800` region. A rapid-refill terminal result is `rapid_refill_breaker`, while a hard pre-request block is `blocking_limit`. These are engine protections, not coding-task failure recovery.

## 4. Transcript persistence

The plain-filesystem transcript path uses `_E`, `insertMessageChain`, and `appendEntry`:

- `_E` at `chunk-phacttch.js@4595820` prepares transcript writes.
- `insertMessageChain` at `@4582928` builds the chain.
- `appendEntry` at `@4539653` queues JSONL entries.

The load path `Ole -> S$n -> TNs -> Akt`, `chunk-phacttch.js@4694390`, `@4685423`, `@4700746`, `@4627113`, loads rows, selects a leaf, and walks `parentUuid` to rebuild a branch. The write and load paths deduplicate main-chain UUIDs and preserve sidechain metadata where available.

A `storageV5` backend branch exists but was not read. Remote mirroring functions exist but their protocol was not read. Any statement below about persistence refers to the plain-filesystem path only.

## 5. Interrupted-turn resume

Resume repair classifies an unanswered user prompt separately from an interrupted tool or notification turn in the `chunk-phacttch.js@1288300` to `@1294400` region. For an interrupted turn it can append a `Continue from where you left off.` message.

Automatic resubmission requires `CLAUDE_CODE_RESUME_INTERRUPTED_TURN`. Loading a transcript alone does not automatically rerun the interrupted work. `Mpn` at `chunk-9x333bd0.js@22282` restores mode, model, worktree state, file history, and todo state derived from messages.

This means session restore is not the same as workflow-state restoration. The transcript and derived state return, but the model must still decide what to do on the resumed turn unless the explicit interrupted-turn resubmission feature is enabled.

## 6. Subagent context

`createSubagentContext`, `gir`, `chunk-phacttch.js@2539713`, shares message queues, task registry, session hooks, tool state, credentials, storage, and permission relays by reference. It isolates file-state cache, tool decisions, denial tracking, query tracking, and nested-memory triggers. Parent abort signals create linked child controllers.

Normal agents receive selected parent context copies, their own system prompt, and a filtered tool pool. Forks reuse the parent's rendered system prompt, exact tools, message prefix, sticky betas, and fork point. The fork context is represented by `forkPointUuid` and related metadata. **VERIFIED-STATIC**, static-05 A2.

Sidechain agent transcripts are written separately under the session's `subagents` directory with agent metadata. The main transcript does not need to contain every child row to resume the child.

## 7. Reminders and re-injection

The plan-mode reminder is regenerated from mode and context. `ZDr` at `chunk-phacttch.js@3655734` checks the actual permission mode, reads plan existence, carries `options.planModeInstructions`, and selects a full or sparse reminder. `Kyn` at `chunk-phacttch.js@3653352` counts non-meta user turns since the prior plan attachment or exit. Cadence constants are five turns between reminders and one full reminder per five attachments, `chunk-phacttch.js@3641208`. After compaction, `OYe` creates a full plan attachment at `chunk-phacttch.js@2588668`.

Todo/task reminders count turns since the relevant tool was last used and can produce an attachment at ten turns, `ULr`, `BLr`, and `Wwe` at `chunk-phacttch.js@3699177`, `@3699784`, `@3641002`. The reminder lists current items but does not verify that an item was completed, that tests ran, or that a failed approach changed. Its effect is a prompt nudge. A separate task-reminder path exists for task tools; the exact attachment enumeration is incomplete.

After compaction, the next request re-announces session sections and current environment/tool deltas. This is code-generated context restoration. The model-generated compact summary remains the weak link.

## 8. Continuity failure modes

| Event | Preserved mechanically | Model-dependent |
|---|---|---|
| Tool result | tool-result row, error flag, side fields | understanding the error and next action |
| Large output | full file path and bounded preview | deciding to read the full file |
| Compaction | boundary, summary row, reattachments | summary accuracy |
| Plan mode | mode, reminder, plan reference | plan quality and execution |
| Todo reminder | current items and reminder text | updating and completing items |
| Background agent | task record, transcript, notification | interpreting child result |
| Resume | transcript branch, mode/worktree/file state | continuing the task correctly |
| Failed tool | error row and next turn | diagnosis and changed approach |

## 9. Unresolved branches

- Full reactive and precomputed compaction internals.
- Exact summary prompt and model choice for every compaction arm.
- `storageV5` implementation and remote session mirroring.
- Complete `SendMessage`, `TaskOutput`, and `TaskStop` bodies.
- Full transcript schema for all `parentUuid` and sidechain fields.
- Whether server-side conversation state adds preservation not visible in local code.
