# 02. System-prompt internals

Target: Claude Code CLI 2.1.296 extracted JavaScript. This report traces prompt assembly and dynamic coding-workflow instructions. It separates text construction from code that controls whether a tool or turn can proceed.

## 1. Assembly boundary

The main builder is `H5t` at `chunk-phacttch.js@2019875`. It receives the model and prompt inputs, computes `h=V4(model)`, and selects the lean or full layout at `chunk-phacttch.js@2021689`.

```text
model and host prompt inputs
  -> V4(model), chunk-bykygzr4.js@6140
  -> H5t, chunk-phacttch.js@2019875
       -> lean: wBo, chunk-phacttch.js@2014347
       -> full: cBo, mBo, gBo, hBo, _Bo, bBo
  -> system blocks and session-message additions
  -> request normalizer / tool serializer
  -> provider request
```

`V4` delegates the model table to a host method named `leanPrompt(model)`. That host table was not read. The E50 captures are runtime evidence for the tested model ids only, not a complete model policy.

`jR` at `chunk-phacttch.js@2018756` composes scoped prompt sections through `aYn` and chooses `H5t` or a detached-section reconstruction `L5t` before flattening and filtering. `SBo` calls `kBo` only when the Agent tool is present, `chunk-phacttch.js@2012400`. The standard prompt can be replaced or extended by `EHo` at `chunk-phacttch.js@2099229`, which accepts coordinator, custom system, or main-agent prompt sources and applies append rules. The `jR` caller at `@2110541` is an analysis-only context calculation, so that caller alone does not prove request reachability.

## 2. Lean and full layouts

The full layout is assembled from these sections:

| Section | Builder | Evidence |
|---|---|---|
| Intro | `cBo` | `chunk-phacttch.js@1999384` |
| System | `mBo` | `chunk-phacttch.js@2000324` |
| Doing tasks | `gBo` | `chunk-phacttch.js@2001457` |
| Executing actions with care | `hBo` | `chunk-phacttch.js@2005523` |
| Using your tools | `_Bo` | `chunk-phacttch.js@2009298` |
| Tone and output | `bBo` and related sections | nearby `H5t` assembly |

The lean layout uses `wBo` and the shared session sections. It does not include the full-layout `Doing tasks`, `Executing actions with care`, or `Using your tools` blocks. E50m and E50o showed the lean layout for the tested 5-series ids and the full layout for `claude-sonnet-4-5` and `claude-opus-4-7`. `claude-opus-4-1` was rewritten to `claude-opus-5-5` in the request. **VERIFIED-BOTH**, limited to those captures and source builder.

The body-size comparison must include the separate session `system` message present in the lean request. Comparing only the system-block body with the full layout is not a like-for-like instruction-volume comparison. **VERIFIED-RUNTIME**, E50 captures.

## 3. Full-layout coding text

`gBo` contains the principal coding rules. The body says, in substance:

- Treat unclear instructions as software-engineering work in the working directory.
- Prefer editing existing files and avoid unrelated refactors, speculative compatibility, and unnecessary comments.
- Treat security issues as part of the requested fix.
- For UI work, start the server, use the feature, test the golden path and edge cases, and say when UI testing was not possible.
- Report what was verified and what was assumed only when the feature flag for that sentence is enabled.

The UI verification sentence is anchored at `chunk-phacttch.js@2002646`. The verified-versus-assumed sentence is controlled by `tengu_verified_vs_assumed`, with the default branch off, at `chunk-phacttch.js@2005129`. **VERIFIED-STATIC**.

There is no equivalent unconditional sentence in this builder requiring tests for all non-UI code. This is a bounded source finding, not a claim about server-side evaluation.

`hBo` contains action-safety text. Reversible local edits and test commands do not require the same confirmation as destructive or shared-state actions. Approval does not automatically transfer to another context. It tells the model to investigate obstacles rather than bypass checks, to inspect unfamiliar files before deleting, and to check status before discard-prone Git operations. **VERIFIED-STATIC**, `chunk-phacttch.js@2005523`.

`_Bo` has two paths:

1. With a task-tracking predicate, it emits task-tool guidance to mark items complete.
2. Otherwise it emits dedicated-tool, parallel-tool, task-tool, and subagent guidance according to the mode and fork predicates.

`kBo` returns no text for one branch, fork-specific text for another, and default-mode subagent guidance otherwise. Its relevant source is around `chunk-phacttch.js@2010614`. The exact predicates were not all read, so inclusion of each sentence in every request is **UNKNOWN**.

## 4. Lean-layout coding text

`V0o` at `chunk-phacttch.js@1988701` supplies the lean body's explicit test-related sentence: report failures with their output, report skipped steps, and state verification plainly. This is reporting guidance. It does not itself schedule a test.

`Y0o` at `chunk-phacttch.js@1989268` contains an end-to-end approval sentence behind `xFn`. `xFn` was not read and was false in the E50 requests, so runtime inclusion is not established outside those captures.

`TBo` is the "act when enough information is available" text. `vBo` at `chunk-phacttch.js@2014981` controls its inclusion, with the `tengu_cedar_lantern` flag defaulting true in the inspected source. **VERIFIED-STATIC**.

The fable request included additional "Delivering work" and "Writing for the user" sections. The predicate that admits other models to those sections was not traced. The mythos-related "Communicating with the user" section is at `K0o`, `chunk-phacttch.js@1984482`; its gating predicate was not established. **VERIFIED-RUNTIME for tested captures, UNKNOWN for general model policy**.

## 5. Proactivity attachment

The proactivity resolver `_a` at `chunk-m44bzxs2.js@74922` chooses, in order:

1. Relaunch handoff from environment, `T4o`, `chunk-9f9fftqe.js@1857`.
2. CLI value.
3. Persisted value `wmn`, a stub returning no value in this build, `chunk-dvydyt6t.js@654`.
4. Default `default`, from `chunk-zdd7h7by.js@327930`.

The hidden `--proactivity <level>` option is at `chunk-jzzwheky.js@66125`; it is hidden because `Gre()` returns false at `chunk-3qrxzjv5.js@109692`. The attachment gate `iA` is at `chunk-3qrxzjv5.js@109659`. `Cpn` and `Gu` set the selector gate from `CLAUDE_CODE_DISABLE_PROACTIVITY` and `tengu_proactivity_selector`, `chunk-m44bzxs2.js@75356`, `@75491`.

`KMe` at `chunk-phacttch.js@398302` emits a `proactivity` attachment when the level or relevant tool set changes. The render case is at `chunk-phacttch.js@4477215` and calls `xat` at `chunk-phacttch.js@107269`. `hAe` at `chunk-phacttch.js@106850` retracts it.

The three text branches are:

- `ask` / low: confirm before changes, use plan mode for non-trivial work, and confirm before commit or push.
- `default` / medium: ask only for decisions the user must make, make edits, and run needed checks.
- `proactive` / high: act without unnecessary questions, run tests and fix failures, fix lint and type errors, update affected docs, and tie off loose ends.

These are prompt instructions. The same level also feeds `mde` at `chunk-wccxtr0h.js@1959`, which selects a permission mode. E50w observed `auto`, `default`, and `auto` as the initial modes for ask, default, and proactive on that machine. The static mapping and the runtime default-level result disagree; the caller or availability predicate responsible was not traced. **CONTRADICTED between static interpretation and runtime observation**, not resolved.

## 6. Autonomous addendum

`uBo` at `chunk-phacttch.js@1997648` adds an autonomous-working block when `tengu_amber_sextant` is enabled and `ZH(model, canonicalModel) || Ugs(canonicalModel)` holds, as shown in the `H5t` assembly at `chunk-phacttch.js@2021689`. `ZH` uses a model-mitigation lookup and explicitly admits `claude-mythos-5`, `chunk-tydh8ra2.js@710`; `Ugs` delegates to host experiment selection, `chunk-bykygzr4.js@5072`. The code text tells the model not to ask whether it should continue on reversible work, to stop for destructive actions or real scope changes, and to inspect its last paragraph before ending a turn. It also says to retry after errors when the last paragraph describes unfinished work. The flag default is visible, but the host experiment selection and every model result are not. **VERIFIED-STATIC for the builder and gates; UNKNOWN for general runtime reachability**.

`UH()`'s task-tracking short branch is not reached through the imported implementation, which returns false at `chunk-0a3kw9bb.js@33803`. This narrows the task-tool text path: the ordinary `_Bo` branch, not the short `UH()` branch, is the relevant path in this build. **VERIFIED-STATIC**.

## 7. Plan-mode reminder as a dynamic prompt

The plan-mode lead sentence is `ODn` at `chunk-phacttch.js@4442619`. It says that plan mode is active, execution is not wanted, the plan file is the only writable exception, and non-read-only tools are forbidden. `eKr` at `chunk-phacttch.js@4441599` selects the full, sparse, or subagent form. The full form includes the plan path and five phases.

The plan-mode reminder is not the enforcement boundary by itself. Permission code refuses non-read-only calls in plan mode, while the reminder explains what the model should do. Existing E50q captures showed a Write denial and an absent ExitPlanMode in headless plan mode. **VERIFIED-BOTH for those tested paths**.

## 8. Prompt inclusion, caching, and precedence

The prompt system has several distinct channels:

1. Base system blocks assembled by `H5t`.
2. Session guidance and environment/memory sections in the lean request's system-role message.
3. Tool descriptions serialized from the current tool pool.
4. Dynamic attachments for proactivity, plan mode, todo/task reminders, hooks, model changes, and queued commands.
5. User and assistant messages retained by the loop and normalized for the provider.

The source shows cache markers and request normalization in `pln`, but this pass did not read every cache key or all provider-specific cache branches. Prompt inclusion for `Y0o`, autonomous predicates, host model table, task reminder render predicates, and custom prompt overrides remains partly unknown.

## 9. What is enforced versus suggested

| Mechanism | Application code | Prompt text | Model choice |
|---|---:|---:|---:|
| Prompt layout selection | yes | no | no |
| Proactivity level resolution | yes | injected text | no |
| Permission mode associated with level | yes | explanatory text | no |
| Plan-mode edit refusal | yes | reminder | model still chooses allowed reads |
| Test after ordinary code edit | not found in inspected scope | default/proactive text varies | yes |
| Retry a failed coding approach | no counter found | autonomous addendum and Bash guidance | yes |
| Report verified versus assumed | conditional text | yes | wording choice |
| Stop-hook response | yes | blocking text delivered to model | model chooses repair |

The source scope and unknown branches are indexed in report 09.
