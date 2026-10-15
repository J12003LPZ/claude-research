# 10. Complete coding-workflow reconstruction

## Executive conclusion

Claude Code 2.1.296 is an event-driven model loop surrounded by strong transport, tool, permission, context, and lifecycle machinery. The model supplies the coding strategy. The application supplies the available tools, validates and authorizes calls, runs tools, returns failures, manages context, and decides whether the conversation can continue or terminate.

The inspected implementation does not contain a general acceptance controller that requires an ordinary coding task to run tests, pass tests, retest after a failure, or receive an independent review before completion. Prompt branches can request those actions. A user-configured Stop hook can enforce them. A specialized tool, goal, plugin, or server-side policy can add another gate. Without such a gate, the ordinary no-tool path can return `completed` after the model says it is done.

That conclusion is **VERIFIED-STATIC** for the indexed source scope and **VERIFIED-RUNTIME** for the existing scripted E50 captures. It is not a claim about hidden server-side behavior or every plugin.

## 1. End-to-end call graph

```text
user prompt
  -> REPL or headless input parser
     Tft / plt
  -> session engine x9e
     -> upstream prompt sections H5t / jR
     -> upstream tool pool rv / ZL / iUt
     -> Y0 wrapper
        -> Ad query loop
           -> prompt/context attachments
           -> autocompaction
           -> model selection
           -> Zvt / pln request normalization
           -> Gke retry wrapper
           -> provider Messages API stream
              -> assistant text/tool blocks
           -> gs streaming executor
              -> Qj / RWo / AWo
                 -> validation
                 -> hooks
                 -> permissions
                 -> tool.call
                 -> result mapping
           -> Stop/SubagentStop Za
           -> next_turn or terminal reason
     -> SDK/headless result builder
```

The REPL and headless paths converge before the shared model loop. **VERIFIED-STATIC**, `chunk-9w4htdvs.js@1357077`, `@1413900`, `chunk-fzzrkchm.js@343343`, `chunk-jr646ga5.js@58339`, and `chunk-93pksqr2.js@126966`.

## 2. Understand and Explore

Plan mode supplies the model with a five-phase workflow. The phases are instructions, not five application states:

1. initial understanding;
2. design, with a conditional Plan-agent recommendation;
3. plan review;
4. final plan file;
5. ExitPlanMode or the corresponding workshop action.

`nKr`, `oKr`, `tKr`, and `CLn` implement the text, `chunk-phacttch.js@4444446`, `@4447877`, `@4441702`, and `@4443342`. `EnterPlanMode` sets the actual mode through `emn`, `chunk-3870y95r.js@7017`; the plan permission floor can ask or deny non-read-only calls, while ordinary file-write validation has a denial path, `chunk-phacttch.js@3355376`.

Explore and Plan agents are real built-in definitions with filtered tools. The main model is not forced to call either one. The source shows a prompt-level recommendation and an application-level tool boundary, not a planner scheduler.

## 3. Plan and approval

The plan has a real path and a persistence abstraction. `kv` and `jc` compute its path, `Dco` writes it, `v4e` reads it, and `FPt` supplies its current content to ExitPlanMode input when present. The plain-filesystem branch is verified, but `storageV5` can back these operations in other modes, so filesystem backing is not universal. **VERIFIED-STATIC**, `chunk-sz2fxhw2.js@12600` to `@16450`, `chunk-phacttch.js@818956`.

ExitPlanMode performs validation, permission, and transition. Outside team mode it requests approval and offers keep-context, clear-context, and continue-planning choices. In team mode it sends a plan approval request to a lead inbox. A team inbox-poller branch can auto-approve a lead-received request, so the approval behavior is not one universal human-only path. `gK`, `Mqo`, and the interactive dialog are at the anchors in report 09.

After approval the application restores the pre-plan permission mode and emits a message instructing the model to begin coding. The model still chooses which files to edit and which tools to run.

## 4. Execute and edit

The model emits tool-use blocks. The stream loop recognizes them independent of the API stop reason and sends them to the streaming executor. Safe tools can overlap; unsafe tools queue behind active work. The executor returns tool results as user messages. The application validates inputs, applies hooks and permissions, executes the tool, persists large output when needed, and maps the result back into the conversation.

An ordinary error becomes an error tool-result and another model turn. There is no automatic rerun of the same failed command. A tool contract can request end of turn, including the MCP end-turn metadata path, which is a separate completion route.

## 5. Test, diagnose, and recover

The application has many recovery mechanisms:

- transport retries and fallback models;
- output-token and truncated-response nudges;
- malformed-tool-use retry;
- thinking-only retry;
- refusal retry;
- prompt-too-long reactive compaction;
- tool-error delivery;
- permission-denial budgets;
- Stop-hook blocking;
- max-turn and context breakers.

These mechanisms maintain a valid conversation and keep the process from hanging. They are not a test-result controller. The inspected loop does not parse a failed test into a required diagnosis, track failed coding approaches, or prevent repeating the same edit strategy. Those behaviors exist in prompt text and coordinator instructions, not as a general local state machine.

## 6. Finish

The no-tool finish path is:

```text
no tool_use blocks
  -> recover output/API conditions
  -> Stop/SubagentStop/internal checks
     -> preventContinuation: stop_hook_prevented
     -> blocking errors: another turn, until max/cap
     -> clean: completed
```

The tool path is:

```text
tool_use blocks
  -> drain executor
  -> abort/deferred/hook/tool-end checks
  -> PostToolBatch hooks and tool refresh
  -> max-turn check
  -> next_turn with tool results
```

A background Agent launch returns before the child finishes. Completion and failure are later task notifications. The ordinary parent completion path does not unconditionally wait for every background task, although active goal evaluation has a narrower task-aware check-in path.

The headless result builder maps terminal state to `success`, `error_max_turns`, or `error_during_execution`. API errors can appear as `success` with `is_error:true`. Exit code, subtype, and model prose are therefore not acceptance evidence.

## 7. State machine

```text
INPUT
  -> PREPARE
     -> COMPACT
        -> REQUEST
           -> STREAM
              -> RECOVER_STREAM
              -> TOOL_DRAIN
                 -> POST_TOOL
                    -> NEXT_TURN
           -> NO_TOOL_RECOVERY
              -> STOP_CHECK
                 -> STOP_BLOCK -> REQUEST
                 -> COMPLETE

Any state:
  -> ABORTED_STREAMING / ABORTED_TOOLS
  -> MODEL_ERROR / API_ERROR
  -> CONTEXT_BLOCKED / COMPACTION_BREAKER
  -> MAX_TURNS
  -> BACKGROUND_REQUESTED
  -> HOOK_STOPPED / TOOL_DEFERRED
```

The state machine is application-controlled. The content of the plan, the decision to search, the choice of test command, the diagnosis of failure, and the decision to stop are model-controlled unless a tool, hook, mode, or host policy intervenes.

## 8. Mechanism classification

| Behavior | Code | Prompt | Model | External / unknown |
|---|---:|---:|---:|---:|
| Build prompt layout | yes | contributes text | no | model table partly unknown |
| Choose Explore or Plan | availability only | recommends | yes | coordinator/server may alter |
| Write plan file | path, cache, permission | instructs format | supplies content | storage backend partly unknown |
| Exit plan mode | validation, approval, transition | tells model to call tool | chooses timing | team inbox behavior |
| Execute tools | validation, hooks, permissions, call | descriptions | chooses calls | MCP/plugin bodies |
| Continue after tool result | loop and executor | error text | chooses response | host queues |
| Retry API/output failure | bounded code | recovery nudge | responds to nudge | provider behavior |
| Test ordinary code | no generic gate found | branch-dependent guidance | decides | Stop hook/plugin/server |
| Diagnose failed test | no general ledger found | autonomous/coordinator text | decides | tool/goal extensions |
| Review | optional plan review/security command/coordinator | prompt | decides | plugin/remote review |
| Finish | terminal state and hooks | completion/reporting guidance | supplies final text | server policies unknown |

## 9. Evidence and limits

This reconstruction combines existing static passes 02 to 05, the new indexed source reads in reports 01 to 09, and existing E50 scripted captures. It does not copy shipped implementation code. Pseudocode is conceptual.

REA was requested but unavailable after reconnect. No new runtime or billable model experiment was run. The remaining unknowns are the model table behind `V4`, server-side behavior, complete plugin and MCP paths, full reactive/precomputed compaction, storageV5, the full permission UI, all batched tool-runner callers, and host-level wake policies after results.

The correct completion claim is therefore: **the local coding workflow has been statically reconstructed across the shared loop, prompt assembly, plan mode, registry, tool dispatch, recovery, context, and result boundaries, with the listed branches still open.** It is not a claim that every function in the 2,586-module extraction has been decompiled.
