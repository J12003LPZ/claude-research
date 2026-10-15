# Task-management tool internals

Status: VERIFIED-STATIC for TaskCreate/Get/Update/List/TodoWrite and the shared TaskStop body; PARTIAL for the deprecated TaskOutput/Continue/SendMessage naming requested in the mission.

## Tool registry and schemas

The task tools are defined in `chunk-rpwh4z9c.js` and export their names through `chunk-svt0njrf.js@2322`: `TodoWrite` (`Nx`), `TaskCreate` (`kE`), `TaskUpdate` (`$C`), and `TaskGet` (`uQ`). All four are deferred and gated by `jte()`; task-list tools are disabled when `CLAUDE_CODE_ENABLE_TASKS` is false. TaskCreate is non-concurrency-safe; Get/List are read-only and concurrency-safe; Update is concurrency-safe after its per-task persistence path.

### TodoWrite

`TodoWrite` is defined around `chunk-rpwh4z9c.js@216`. Its input is the full replacement array of `{content,status,activeForm}` where status is pending/in_progress/completed. The call stores the list per agent id (`e.agentId ?? K()`), clears it when every item is completed, and returns old/new lists. It is an in-session checklist, separate from the durable Task* task list.

### TaskCreate

`TaskCreate` is defined at `chunk-rpwh4z9c.js@140140`. Inputs are subject, description, optional activeForm, and arbitrary metadata. `Kds` allocates a durable task with status pending, no owner, and empty dependency arrays. The tool runs TaskCreated hooks; blocking hook errors delete the just-created task and return an error. On success it expands the task UI and returns the id/subject. Coercion `\$wt` accepts a small compatibility set of aliases/wrappers but explicitly rejects `tasks`/`todos` arrays and Agent-style prompt/subagent_type shapes.

### TaskGet

`TaskGet` at `chunk-rpwh4z9c.js@142348` reads the current task through `Z2` and returns only id, subject, description, status, blocks, and blockedBy. Missing tasks become `{task:null}` and serialize as `Task not found`.

### TaskUpdate

`TaskUpdate` at `chunk-rpwh4z9c.js@146660` accepts taskId, subject, description, activeForm, status (`pending`, `in_progress`, `completed`, or `deleted`), owner, metadata merge/delete, `addBlocks`, and `addBlockedBy`. It rereads the task before changing it. `in_progress` can auto-assign the current teammate when in team mode; `completed` runs TaskCompleted hooks and refuses the update if a hook blocks it; `deleted` calls `GCt` and cleans dependency references. Other field changes call `Dce`. Dependency additions call `qCt` for both sides. Team ownership changes write a mailbox assignment message. The result names updated fields and reports status changes.

### TaskList

The list tool is immediately after the TaskUpdate body in `chunk-rpwh4z9c.js` (the `Fr`/`jr` record, around `@150000`). It calls `IM`, removes tasks whose metadata has `_internal`, and filters completed dependency ids from each displayed blockedBy list. The serialized result contains id, subject, status, owner, and remaining open blockedBy ids. It does not expose descriptions.

## Durable task state

The storage implementation is `chunk-zkrrxfpr.js`: `Kds` creates, `Z2` reads, `Dce` updates under file/Storage V5 locking, `GCt` deletes and cleans edges, `IM` lists, `qCt` adds dependency edges, and `Xds` claims a task while checking owner, completion, blockers, and optional agent-busy rules. `Vot` unassigns tasks owned by a departing agent and returns a notification message.

## TaskStop and task-type dispatch

`chunk-rpwh4z9c.js@6994` builds the kill registry (`AJe`/`kn`) for local shell, local agent, workflow, MCP, monitor, memory-import, dream, and other task types. `Ive` (`@12271`) resolves an id/name, rejects ambiguous or unauthorized ownership, handles already-ended-but-live workflow loops, invokes the task-type killer, cascades to related agents where policy permits, marks user stops, and emits stopped notifications. `Ove` (`@15268`) translates expected not-found/not-running outcomes into user-level completion while preserving hard failures. `Aie` (`@15777`) performs system cleanup across eligible running tasks.

The old `TaskOutput` surface is not a normal current task-list tool in this registry. The bundle explicitly marks `taskOutputMaxChars` deprecated and says to read the output file; shell task output is represented by a task-output object in `chunk-phacttch.js@79607`. No separate TaskContinue body was found in the inspected registry. `SendMessage` in the current builtin list is a user-facing message tool, not a task continuation primitive; teammate messaging is a mailbox path (`WS` in `chunk-zkrrxfpr.js`).

## Task and transcript interaction

`chunk-fzzrkchm.js@305589` carries a bounded task snapshot into compaction, and `chunk-phacttch.js@1217506` reconstructs pending TaskCreate/TaskUpdate effects from transcript rows when needed. This provides a recovery path for a task-list state that is missing from the sidecar but present in the conversation. It is distinct from TodoWrite, which is reconstructed from the latest TodoWrite call.

## Confidence table

| Claim | Confidence | Anchor |
|---|---|---|
| TodoWrite is an in-session replacement checklist | VERIFIED-STATIC | `chunk-rpwh4z9c.js@216` |
| TaskCreate/Get/Update/List schemas and bodies | VERIFIED-STATIC | `chunk-rpwh4z9c.js@140140`, `@142348`, `@146660`, `@150000` |
| Durable task storage uses locks/V5 and dependency cleanup | VERIFIED-STATIC | `chunk-zkrrxfpr.js@9581–19185` |
| TaskStop resolves ownership/type and cascades kills | VERIFIED-STATIC | `chunk-rpwh4z9c.js@6994–15777` |
| TaskOutput and TaskContinue are current registry tools | CONTRADICTED | inspected builtin registry and task tool definitions; TaskOutput is deprecated/file-backed, Continue absent |
| Every task-related tool requested by the mission has a dedicated body | UNKNOWN | current version uses renamed/shared paths and dynamic task types |

Open: exact UI rendering for task assignment, remote MCP task continuation semantics, complete teammate `SendMessage` schema/body, and any hidden compatibility aliases that are loaded only through dynamic dispatch.
