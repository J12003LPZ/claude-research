# 04. Built-in agents and agent execution

## 1. Registry boundary

`L0e` at `chunk-phacttch.js@2086295` returns the built-in registry. Its branches are:

- no built-ins when the SDK-disable setting applies in a non-interactive session;
- only the coordinator worker in coordinator mode;
- a conditional default list otherwise.

The default list read in the registry includes:

| Agent | Definition | Conditions / properties |
|---|---|---|
| `general-purpose` | `Xj`, `chunk-phacttch.js@2067564` | all tools, default model inheritance |
| `statusline-setup` | `B3t`, `@2081433` | Read/Edit, sonnet, conditional on safe mode |
| `claude` | `chunk-4vndrz3k.js@2544` | all tools, default fleet agent, conditional gate |
| `Explore` | `XT`, `chunk-phacttch.js@201330` | inherited model, read-oriented disallowed set, `tH()` gate |
| `Plan` | `ute`, `chunk-phacttch.js@204673` | inherited model, same read-oriented restrictions, `tH()` gate |
| web-fetch | `Dwt`, `@2084316` | inherited model, max turns 15, `n1()` gate |
| `claude-code-guide` | `F3t`, `@2063596` | omitted for SDK entrypoints |

This is a bounded negative. It is the complete body of `L0e` and the definitions it names. It is not a package-wide claim that no other agent definition exists. The same package contains explicitly selected or internal definitions:

- `fork`, `chunk-phacttch.js@1981657`;
- coordinator worker, `chunk-3k69rd2t.js@4093`;
- workflow-subagent, `chunk-8hbrzh7z.js@40034`;
- comment-thread-analyst, `chunk-8f1dpmg0.js@6946`;
- main-session pseudo-agent, `chunk-phacttch.js@4239986`.

Plugin and user agents are loaded outside `L0e`.

## 2. Agent definition loading and precedence

`wHo` around `chunk-phacttch.js@2090000` combines built-ins, plugin definitions, Markdown agents found by `Mte`, and flag-provided JSON. `G3t` / `Lwt` parse `--agents` JSON, and `Nwt` parses Markdown frontmatter at `chunk-phacttch.js@2095264`.

The source application order in `u2`, `chunk-phacttch.js@2088270`, is:

```text
built-in -> plugin -> user settings -> project settings -> flag settings -> policy settings
```

Later entries replace earlier entries by `agentType`. Effective precedence is therefore policy, flag, project, user, plugin, built-in. A plugin's lazy loader is resolved by `Jte`, `chunk-phacttch.js@2086771`, and can fail or return a mismatched definition. **VERIFIED-STATIC**.

The loaded Markdown body becomes the agent's prompt. Frontmatter controls tools, disallowed tools, model, effort, permission mode, MCP servers, hooks, max turns, memory, isolation, background behavior, and other launch properties. The parser rejects invalid names and invalid permission modes and can mark an agent unloadable for invalid top-level hook placement, `chunk-phacttch.js@2095264`.

## 3. Agent tool launch

The Agent tool is `aUt` in `chunk-h6wy99cb.js` and uses `xo` as its launch path, around `@15899`.

Launch order:

1. Check nesting depth. Default maximum is three unless overridden by `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` or a flag, `chunk-d1zbawpk.js@560`.
2. Refuse if the caller is stopping.
3. Enforce teammate and background restrictions.
4. Resolve explicit or default agent type, permission denies, allowed types, and fuzzy-name ambiguity.
5. Decide foreground versus asynchronous launch. Omitted `run_in_background` is eligible for background use when background tasks are enabled; explicit false can force foreground, `po`, `chunk-h6wy99cb.js@6066`.
6. Check abort and budget.
7. Wait for required MCP servers.
8. Run the plugin `agent.spawn` hook, then re-check rewritten permissions.
9. Resolve model inheritance and caps.
10. Create remote session or local execution state.
11. Build the child system prompt and initial messages.
12. Build a fresh child tool pool or reuse exact fork tools.
13. Create worktree isolation if requested.
14. Take a concurrency slot, default 20, unless a flag or ultracode branch bypasses it.
15. Dispatch foreground, background, teammate, or remote execution.

The launch path is application code. The agent's choice to use a child, its prompt, and its task strategy remain model-driven unless a host or plugin hook changes them.

## 4. Normal child versus fork

A normal child gets a fresh prompt from its agent definition, selected parent context copies, a newly assembled tool pool, and a linked abort controller. The child context shares queues, task registry, session hooks, tool state, credentials, storage, permission relays, and root tool surface, while isolating read state, tool decisions, denial tracking, and query tracking. **VERIFIED-STATIC**, `gir`, `chunk-phacttch.js@2539713`.

A fork gets the parent's rendered system prompt, exact tool array, parent message prefix, sticky betas, and fork point. The fork path uses `useExactTools` and preserves cache-relevant prefix state. Recursive forks and remote forks are refused. **VERIFIED-STATIC**, `chunk-h6wy99cb.js@17700` to `@27500`, `chunk-jwmqjyrb.js@121161`.

## 5. Explore and Plan

Explore is described as a file-search specialist. Its prompt says it should read and search without changing state. Its disallowed set includes Agent, plan-entry tools, Edit, Write, NotebookEdit, and related interactive tools, `chunk-phacttch.js@201330` and the prompt builder around `@198147`.

Plan has the same read-oriented restrictions and a planning-specialist prompt requiring understanding, exploration, design, a detailed plan, and a critical-file list, `chunk-phacttch.js@204673` and `@202087`.

The tool restrictions are code. The plan-mode prompt tells the main model when to launch Explore and Plan, but the source does not show a host predicate that requires those calls. **VERIFIED-STATIC**.

## 6. Child tool filtering

`Cl` and `LR` in `chunk-jwmqjyrb.js@83520` and `@87492` filter child tools in this order:

1. MCP tools, subject to memory mode.
2. ExitPlanMode only for a child in plan mode.
3. Globally removed interactive and session tools, including EnterPlanMode, AskUserQuestion, memory tools, Workflow, scheduling, onboarding, and refresh tools.
4. Headless-only removals.
5. Agent removal at the depth limit.
6. Async-agent allowlist and teammate additions.
7. Agent definition `disallowedTools` and `tools` allowlist.
8. `Agent(type)` entries become allowed agent types.

Explore and Plan therefore have fewer tools than the parent by construction. A child that retains Bash can still run shell commands unless its permission context or a tool-specific check blocks them. Existing E50u demonstrated this boundary under bypass permissions.

## 7. Result and failure delivery

Foreground results contain status, content, usage, duration, tool count, and agent metadata. Background and remote launches return a receipt first and deliver completion or failure through task notifications. The result text can include a continuation hint for `SendMessage`.

Foreground exceptions other than user abort can be turned into partial history plus a harness note, `chunk-h6wy99cb.js@42800`. Background exceptions mark the task failed and enqueue a notification through `avt`, `chunk-phacttch.js@4226700`. A launch receipt is not a prediction of the child result.

## 8. No default verifier claim

Within the full `L0e` registry body and the definitions it directly names, no separate reviewer, verifier, debugger, or test-runner built-in appears. The package does contain review commands, coordinator prompts, plugins, user agents, workflow agents, and internal analysts. Therefore the accurate claim is:

> No default reviewer or verifier was found in the inspected built-in registry body. Plugin, user, policy, workflow, and coordinator definitions are separate loading paths and were not treated as absent.

## 9. Unresolved branches

- Complete plugin lazy-loader behavior and failure handling.
- All callers of the batched tool runner `Zo`.
- Full `SendMessage`, `TaskOutput`, and `TaskStop` schemas and call bodies.
- Remote agent service behavior.
- Host-level parked-agent and idle-wake policy after a parent turn ends.
