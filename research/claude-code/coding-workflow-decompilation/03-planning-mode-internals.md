# 03. Planning-mode internals

This report follows the plan-mode prompt, permission floor, plan file, ExitPlanMode approval path, and child-agent restrictions in Claude Code 2.1.296. Source evidence is static unless marked otherwise.

## 1. Entering plan mode

Plan mode has two layers:

1. A permission context whose mode is `plan` and whose tool decisions apply a non-read-only floor.
2. A dynamic reminder that explains the workflow and the plan-file exception to the model.

The permission layer is visible in the tool-permission code around `chunk-phacttch.js@3355376`. `Lpn` identifies the plan-mode case and the surrounding algorithm can convert a passthrough non-read-only decision into `ask`; ordinary file-write validation has a separate plan-mode denial path. The reminder layer begins with `ODn`, `chunk-phacttch.js@4442619`, and is selected by `eKr`, `chunk-phacttch.js@4441599`.

The reminder says, in substance, that plan mode is active, the user does not want execution yet, edits are forbidden except for the plan file, and non-read-only tools are not available. The exact precedence of this attachment against every other prompt source is UNKNOWN. The observed ordinary file-write refusal comes from permission/tool code, not from the reminder text alone.

`EnterPlanMode` is `emn` in `chunk-3870y95r.js@7017`. Its body rejects agent contexts and calls `setToolPermissionContext` with the preserved previous context from `L_t` followed by `setMode:"plan"`, `chunk-3870y95r.js@7560` to `@8100`. `L_t` preserves the pre-plan mode and has special handling for auto mode in `chunk-kqxewm47.js@26232`. The tool prompt asks for user approval, but the entry body itself does not expose an independent approval method; the surrounding permission path supplies that boundary. **VERIFIED-STATIC**.

## 2. Reminder forms and selection

`eKr` chooses among forms based on flags and context:

- Full plan reminder `rKr`, `chunk-phacttch.js@4448210`.
- Sparse reminder `sKr`, `chunk-phacttch.js@4453126`.
- Subagent form `iKr`, `chunk-phacttch.js@4453560`.

The plan-file path is included in the full form. A workshop-document branch can add a second writable document. A custom planning instruction can replace the detailed workflow, leaving only the lead sentence, plan-file note, and exit rule. **VERIFIED-STATIC**, `chunk-phacttch.js@4441599` to `@4453560`.

## 3. Five phases in the model-facing workflow

The full reminder is a five-phase instruction sequence. It is not a separate planner program.

### Phase 1: initial understanding

The model is told to read code, ask questions, and reuse existing utilities. When `tH()` and default mode permit it, it is instructed to use Explore agents, launch up to a computed maximum in one message, and use one or several based on task scope. Otherwise it explores directly. The phase builder is `nKr`, `chunk-phacttch.js@4444446`.

The predicate `tH` is readable at `chunk-phacttch.js@143288`: it is the negation of `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS`, latched per host. The exact caller-side conditions that combine it with mode were read in the prompt builder, but the host method that governs all model layouts remains outside this pass.

### Phase 2: design

When the same Explore/Plan gate and default-mode condition hold, the model is told to launch at least one Plan agent for most tasks, skipping only trivial edits. It passes the understanding context and constraints and asks for a detailed plan. Otherwise the model produces the plan directly. This is the same plan-reminder builder region, `chunk-phacttch.js@4444446`.

### Phase 3: review

`oKr`, `chunk-phacttch.js@4447877`, tells the model to read critical files, check plans against the request, and ask remaining questions. This is review of the plan, not an independent post-edit code review.

### Phase 4: final plan

`tKr`, `chunk-phacttch.js@4441702`, tells the model to write the plan file with context, one recommended approach, critical files, reusable functions and paths, and a verification section describing end-to-end testing. The model writes this artifact with the plan-file exception.

### Phase 5: exit

`CLn`, `chunk-phacttch.js@4443342`, requires the turn to end with a question tool or the exit-plan tool, or with workshop-document publication when that mode is active. It forbids asking for approval through an ordinary prose question. This is prompt guidance for the model's final plan turn; the separate ExitPlanMode permission path is the mechanical gate.

## 4. ExitPlanMode tool

The tool is `gK`, `chunk-z3vv06zx.js@6222`.

### Availability

- `shouldDefer` is true.
- It is not read-only.
- It requires user interaction outside team mode, `chunk-z3vv06zx.js@6549` to `@6700`.
- Its `isEnabled` branch is false in headless contexts when the relevant plan-state predicates hold, including the path where `py()` has entries or `qSt(UO())` is false, `chunk-z3vv06zx.js@6564`.

E50q verified the headless result: in `-p` plan mode, ExitPlanMode was absent from the tool list and a scripted call returned `No such tool available: ExitPlanMode. ExitPlanMode is disabled for this session`. **VERIFIED-BOTH for that mode**.

### Input validation

`validateInput`, `chunk-z3vv06zx.js@6806`, refuses calls when the session is not in plan mode and refuses forked use. The model cannot invoke the tool from an ordinary mode to manufacture an approval transition.

### Permission and approval

`checkPermissions`, `chunk-z3vv06zx.js@7602`, returns an ask decision with `Exit plan mode?` outside team mode. The ordinary permission dialog and plan-exit dialog are in `chunk-9w4htdvs.js@1224601`.

In team mode, the tool sends a `plan_approval_request` to the lead inbox at `chunk-z3vv06zx.js@8226` and waits for a verdict through `Mqo`, `chunk-z3vv06zx.js@2077`. The interactive dialog offers keep-context modes, clear-context continuation, and `No, keep planning` in `chunk-9w4htdvs.js@1220500` to `@1230900`. A denial with feedback leaves planning in place; approval can carry an edited plan, permission updates, or a cleared-context implementation message. An inbox-poller branch can auto-approve lead-received requests, `chunk-9w4htdvs.js@1538650` to `@1540150`, so a universal human-approval claim is not supported across team paths.

### Transition after approval

The `call` body restores the pre-plan mode, falling back to default if no previous mode exists. If the previous mode was auto but the auto gate is now off, it falls back to default. It sets the exited-plan flags, records the transition, and calls `setToolPermissionContext` with the active mode and cleared pre-plan mode. The relevant body is `chunk-z3vv06zx.js@8810` to `@9829`.

The success result tells the model to start coding and update its todo list, `chunk-z3vv06zx.js@10953`. The mode change is application state, so a model cannot leave plan mode merely by saying that its plan is complete.

## 5. Plan file and persistence boundary

The plan path is computed by `kv`, which derives a session-slug `.md` path and an agent-suffixed path when needed. `jc` selects a configured project-contained plans directory when it is valid, otherwise the default plans directory, `chunk-sz2fxhw2.js@12600` to `@13800`. `Dco` persists plan text and updates the plan-file cache; `v4e` reads from the cache/storage backend or filesystem, `chunk-sz2fxhw2.js@14300` to `@16450`. Before tool execution, `FPt` substitutes the current plan-file content and path into ExitPlanMode input when a plan exists, `chunk-phacttch.js@818956` and caller `@2272200`.

The plan prompt gives the model a plan-file path and the permission layer permits writing that path. Existing static-05 evidence shows a `get_plan` control request and transcript/session persistence of mode and plan state. The complete alternate storage schema is **UNKNOWN**.

After compaction or session resume, plan reference and mode are among the context reattachments restored by `Ske`, `chunk-phacttch.js@2585926`, and the resume restoration path `Mpn`, `chunk-9x333bd0.js@22282`. This shows preservation of plan context, not preservation of every model-generated plan detail.

## 6. Tool restrictions and subagents

Plan mode's permission floor is independent of the Explore and Plan agent disallowed-tool lists. Explore and Plan definitions have disallowed edit/write and delegation tools at `chunk-phacttch.js@201549` and `@204673`. The child filtering path also removes plan-entry tools and other interactive tools from ordinary child agents, `chunk-jwmqjyrb.js@83520`.

Existing E50q runtime evidence showed a Write denial in headless plan mode. It did not establish an independent plan-mode Bash rule because the Bash decision went through an unavailable classifier path in the scripted lab. **VERIFIED-RUNTIME for Write, UNKNOWN for an isolated shell floor**.

## 7. State machine

```text
ordinary mode
   | EnterPlanMode path and mode transition
   v
plan mode
   | read, search, ask, Explore, Plan, plan-file edit
   | non-read-only tool -> plan floor ask or denial, depending on the tool path
   | ExitPlanMode unavailable in some headless modes
   v
approval request
   | user approval or team lead verdict
   | rejection -> remains in plan mode
   v
pre-plan permission mode restored
   | success message asks model to begin implementation
   v
implementation mode
```

The source supports the state and permission transitions. The quality of the plan, whether the model launches agents, and whether the verification section is actually executed remain model decisions.

## 8. Unresolved branches

- Every EnterPlanMode caller and alternate entry branch.
- Interactive rejection and re-prompt behavior in the UI.
- Plan-file read/write implementation and schema.
- Workshop-document approval path.
- Exact `qSt(UO())` and `py()` semantics in every session type.
- Plan-mode behavior in coordinator and remote-agent modes.
- Whether any server-side policy adds an approval or verification requirement not visible in the local CLI.
