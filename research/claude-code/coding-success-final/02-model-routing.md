# 02. Model selection and routing

Target: Claude Code CLI 2.1.296, extraction `extracted/2.1.296/~BUN/root`. Scope: which model answers each request, how that
choice changes prompts, tools and budgets, and what happens when the model fails. Out of scope (as briefed): authentication,
billing, entitlements and provider infrastructure. Where the model choice depends on those, the dependency is named and not followed.

## 0. Evidence base and limits

| Source | What it gives | Label |
|---|---|---|
| `chunk-x.js@offset` anchors, section 13 | Static reads of whole function bodies. Each anchor is pinned in `final-runtime-control-decompilation/13-source-pins.json`. | VERIFIED-STATIC |
| E90k to E90x runs | The pinned 2.1.296 binary against the lab proxy. The proxy replies with scripted turns, so no upstream model is called. Each run records the `model`, tool count, prompt markers, `effort` and `max_tokens` of every `/v1/messages` request. Summaries: `runtime-logs/E90[k-x]*/routing-probe.json` and `prompt-sections.json` (booleans only, no prompt text). | VERIFIED-RUNTIME |
| E50 series (earlier reports) | Layout by model, Explore child, plan mode. | VERIFIED-RUNTIME |

Limits that apply to every statement below:

* The scripted proxy shows what the CLI sends. It does not show how any model behaves with those prompts. Nothing here says one model codes better than another.
* The lab account's feature flags and per-model client data are whatever that account received. A different account can get different values for the flag-gated rules (section 9). Static facts (catalog contents, function bodies) do not depend on the account.
* Lab runs use `--model <alias or id>`. Defaults chosen by account type, organization policy or provider were not exercised.

## 1. Answer first

| Question | Answer | Label |
|---|---|---|
| Does Claude Code choose a model by task complexity? | No. No function reads the prompt, the repository or the task to pick a model. The model for each request is the product of configured inputs: session model, alias table, permission mode, agent definition, tool parameter, environment, and error-driven fallback. | VERIFIED-STATIC (bounded negative), supported by VERIFIED-RUNTIME |
| Is there any automatic switch while a session runs? | Two, both rule-based. (a) Plan mode swaps the model when the session model is the alias `opusplan` or `haiku`. (b) A failed request can move the session to a configured fallback model. | VERIFIED-BOTH |
| What does the model change besides the `model` field? | A lot. The system prompt layout (lean or full), the tool descriptions, the presence of the task-tracking tools, several coding-behavior prompt sections, the Explore nudge, the read-before-edit guard, `max_tokens`, `effort`, thinking mode and the context window. All of it is decided by a catalog and a few model lists inside the CLI. | VERIFIED-BOTH |
| Do subagents get a different model than the parent? | By default they inherit it. Explore on a parent above Opus is capped to Opus. The Agent tool's `model` parameter and `CLAUDE_CODE_SUBAGENT_MODEL` can change it. | VERIFIED-BOTH |

## 2. The model catalog

The CLI embeds a catalog (`models:[...]`, `aliases`, `latest_per_family`) at `chunk-bnqade36.js@2565`, schema at `@21516`. It is the source of context windows,
output limits, default effort, capabilities and the advisor rank. A capability is a string in a model's `capabilities` list.
The function `w_(model, capability)` answers "does this model have it" (`chunk-bnqade36.js@23782`) in this order: the environment
variable `CLAUDE_CODE_MODEL_CAPABILITIES` (`@24039`, per model, `name` or `-name`), then a server-provided lookup, then the catalog list (`@23940`).

Aliases (`chunk-bnqade36.js@18857`): first party `opus` is `claude-opus-5-5`, `sonnet` is `claude-sonnet-5-5`, `haiku` is `claude-haiku-5-5`, `fable` is
`claude-fable-5-1`; `best` is `fable`. Bedrock, Vertex, Foundry and gateway entries map the same aliases to older models. Environment variables
`ANTHROPIC_DEFAULT_{OPUS,SONNET,HAIKU,FABLE}_MODEL` override each alias (`chunk-cvvnq4he.js@363463`).

Catalog facts that matter for coding behavior (read from the catalog text, VERIFIED-STATIC):

| Model | Window | Default max output | Default effort | Capabilities that change the prompt or tools | Advisor rank |
|---|---|---|---|---|---|
| claude-haiku-4-5 | 200k | 32,000 | none | context_management | 1 |
| claude-sonnet-4-5 | 200k (1m beta) | 32,000 | none | context_management | none |
| claude-sonnet-4-6 | 200k (1m beta) | 32,000 | none | effort, adaptive_thinking | 2 |
| claude-opus-4-6 | 200k (1m beta) | 64,000 | none | effort, adaptive_thinking | 3 |
| claude-opus-4-7 | 1m | 64,000 | xhigh | effort, adaptive_thinking (no lean_prompt) | 5 |
| claude-opus-4-8 | 1m | 64,000 | high | lean_prompt | 5 |
| claude-sonnet-5 | 1m | 64,000 | high | none of the prompt flags (no lean_prompt) | 4 |
| claude-sonnet-5-5 | 1m | 128,000 | medium | lean_prompt, refusal_fallback, silent_turn_reminder | 6 |
| claude-haiku-5-5 | 1m | 128,000 | medium | lean_prompt, haiku_5_5_early_stopping_guidance | 4 |
| claude-opus-5 | 1m | 64,000 | high | lean_prompt, refusal_fallback, **opus_5_prompt_bundle** | 7 |
| claude-opus-5-5 | 1m | 128,000 | medium | lean_prompt, refusal_fallback, **opus_5_5_prompt_bundle** | 7 |
| claude-fable-5 | 1m | 64,000 | high | lean_prompt, **fable_5_mitigations**, refusal_fallback | 8 |
| claude-fable-5-1 | 1m | 64,000 | high | lean_prompt, fable_5_mitigations, **fable_5_1_prompt_bundle** | 9 |
| claude-mythos-5 | 1m | 64,000 | none | no capabilities listed (handled by name in code) | 8 |
| claude-mythos-5-1 | 1m | 64,000 | high | lean_prompt, fable_5_mitigations, fable_5_1_prompt_bundle | 9 |

Catalog anchors: haiku-5-5 `@3744`, sonnet-5 `@7631`, opus-4-7 `@11966`, opus-5 `@13699`, opus-5-5 `@14669`, fable-5-1 `@16598`, mythos-5 `@17645`, mythos-5-1 `@18092`.
Names such as "prompt bundle" are the catalog's own capability strings. They are labels for sets of prompt text, not behavior claims.
"Default effort none" means the catalog has no `default_effort`. The requests still carried an effort: `high` for `claude-sonnet-4-6` and `claude-mythos-5` (E90p), none for `claude-sonnet-4-5`. The source of that fallback value was not decoded (INFERRED: a generic default for models that accept effort).

## 3. Main model selection

Function chain (VERIFIED-STATIC), highest precedence first:

1. `tt()` returns `Lt(wh())` when `wh()` is set, else `Jl()` (`chunk-cvvnq4he.js@357363`).
2. `wh()` (`@356337`): the in-session override `Xc()` (set by the model picker), else `DIt()`.
3. `DIt()` (`@356414`): the launch option `lU()` (named `initialMainLoopModel`; runtime shows `--model` is honored, so it carries that flag, INFERRED for the exact link), else `ANTHROPIC_MODEL`, else the settings `model`.
4. `Jl()` = `Lt(q_())`, where `q_()` is the `setting` of `d8()` (`@366970`): an organization-enforced setting, else a managed or built-in default. How that default depends on account type is billing and entitlement logic. Not followed (excluded).
5. `Lt(name)` (`@387332`) turns an alias into an id: `fable`, `opus`, `sonnet`, `haiku`, `best`, `opusplan` (resolves like `sonnet` outside plan mode), the `[1m]` suffix, and a deprecated-model remap described below.
6. `Yr(model)` (`@339630`) applies the organization `availableModels` allowlist. A disallowed explicit model is replaced through `jE`, which picks the newest allowed model in the same family or returns nothing.

Runtime (E90k, E90p, E90x, VERIFIED-RUNTIME): `--model haiku`, `sonnet`, `opus` sent `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`.
`--model claude-opus-4-1` sent `claude-opus-5-5`: the CLI remaps deprecated ids to the latest Opus when the remap gate is on (`Lt`, `@387332`; deprecation table at `chunk-cvvnq4he.js@319038`).
The gate function `UIt()` was not decoded. The remap happened for this account. UNKNOWN for others.

## 4. Plan mode can change the model

`fg()` (`chunk-cvvnq4he.js@364824`) runs for every request and calls `gvr` (`@364941`) with the current permission mode. When the mode is `plan`:

* If the configured model is the alias `opusplan`, planning uses the newest Opus (`g7`, `@363981`; resolved by `mvr`, `@364422`).
* If the configured model is the alias `haiku`, planning uses the newest Sonnet (the "haiku plan upgrade").
* Any other model, including a full id such as `claude-haiku-5-5`, is left alone.
* If the target model is disallowed by the organization, the next allowed model is used and a warning is recorded.

Runtime (E90x, VERIFIED-RUNTIME), request `model` by configured model and permission mode:

| `--model` | `plan` | `bypassPermissions` |
|---|---|---|
| `haiku` | claude-sonnet-5-5 | claude-haiku-5-5 |
| `opusplan` | claude-opus-5-5 | claude-sonnet-5-5 |
| `sonnet` | claude-sonnet-5-5 | claude-sonnet-5-5 |
| `opus` | claude-opus-5-5 | claude-opus-5-5 |
| `claude-haiku-5-5` | claude-haiku-5-5 | claude-haiku-5-5 |
| `claude-sonnet-4-5` | claude-sonnet-4-5 | claude-sonnet-4-5 |

The switch is by the configured alias and the mode, not by task difficulty. The messages stay the same; only the `model` field and, because the layout depends on the model (section 8), potentially the system prompt change between modes.
Whether this breaks the prompt cache is INFERRED, not measured.

## 5. Subagent model resolution

`QU(agentModel, parentModel, toolModelParam, ...)` (`chunk-phacttch.js@745395`) is called from the Agent launch (`chunk-h6wy99cb.js@27625`) as
`QU(Fge(agent, parent), parent, param, ...)`. Order (VERIFIED-STATIC):

1. `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` set: the agent definition and the tool parameter are dropped (only an Explore cap and the word `inherit` survive, `Xxt`, `@747259`), and `CLAUDE_CODE_SUBAGENT_MODEL` decides.
2. The Agent tool's `model` parameter (`sonnet`, `opus`, `haiku`, `fable`; schema `chunk-h6wy99cb.js@10543`). `inherit` gives the parent. A parameter naming the parent's family keeps the parent's exact id (`qnr`, `@747718`).
3. The agent definition's `model` (frontmatter or built-in field), unless it is `inherit`, which returns the parent model through the same plan-mode rule as section 4 (so an inheriting agent launched during plan mode with `opusplan` gets the plan model; read from `S()` in `QU`, not run).
4. `CLAUDE_CODE_SUBAGENT_MODEL` (`Gte`, `@745309`), only for agent definitions with no `model` at all.
5. The parent.

A resolved model that the allowlist rejects becomes the newest allowed model in its family, or the parent, with a warning (`ono`, `@747442`).

**Explore cap.** `Fge` (`chunk-phacttch.js@201740`): for the built-in Explore agent on a first-party provider, if the parent's family ranks above Opus
(`GWn`: haiku 0, sonnet 1, opus 2, fable and mythos 3; `chunk-eeg6qbez.js@2553`), the child gets `inheritCap: "opus"` and runs on the newest Opus. The cap is skipped on non-first-party providers and with `CLAUDE_CODE_DISABLE_EXPLORE_INHERIT_CAP` (`@201851`).
Plan and general-purpose have no cap (`ute` at `@204673` has `model:"inherit"`; general-purpose `Xj` at `@2067564` has no `model`).

Runtime (E90k to E90w, VERIFIED-RUNTIME). Child request model by parent, agent and setting:

| Agent | Parent | Setting | Child model |
|---|---|---|---|
| Explore | haiku-5-5, sonnet-5-5, opus-5-5, sonnet-4-5, opus-4-7, haiku-4-5 | none | same as parent |
| Explore | **fable-5-1, mythos-5** | none | **claude-opus-5-5** |
| Explore | fable-5-1 | `CLAUDE_CODE_DISABLE_EXPLORE_INHERIT_CAP=1` | claude-fable-5-1 |
| Explore | opus-5-5 | `CLAUDE_CODE_SUBAGENT_MODEL=haiku` | claude-opus-5-5 (env ignored: Explore defines `inherit`) |
| Explore | fable-5-1 | `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` | claude-opus-5-5 (env ignored, cap applies) |
| Explore | fable-5-1 | `..._SUBAGENT_MODEL=sonnet` and `..._FORCE=1` | claude-sonnet-5-5 |
| Explore | opus-5-5 or fable-5-1 | tool `model:"haiku"` | claude-haiku-5-5 (the cap does not apply to an explicit parameter) |
| general-purpose | opus-5-5, fable-5-1 | none | same as parent (no cap) |
| general-purpose | opus-5-5, fable-5-1 | tool `model:"haiku"` | claude-haiku-5-5 |
| general-purpose | opus-5-5 | `CLAUDE_CODE_SUBAGENT_MODEL=haiku` | claude-haiku-5-5 |
| general-purpose | opus-5-5 | tool `model:"haiku"` and env FORCE `sonnet` | claude-sonnet-5-5 |
| Plan | opus-5-5, fable-5-1 | none | same as parent |
| Plan | opus-5-5 | `CLAUDE_CODE_SUBAGENT_MODEL=haiku` | claude-opus-5-5 (env ignored: Plan defines `inherit`) |

Child tool counts in the same runs: Explore 13, Plan 13, general-purpose 17, parent 26 on the lean layout.

Consequence for coding quality: a child that explores a repository for a parent on the top tier runs on a lower tier by default. Whether that lowers exploration quality is untested (HYPOTHESIS).

**Prompt steer for delegation.** A per-session value `b$()` (`chunk-cvvnq4he.js@116420`) is one of `default`, `no_nudges`, `counter_steer`. Resolution order: `CLAUDE_CODE_THISTLE_GREBE`, per-model client data, GrowthBook flag `tengu_thistle_grebe`, a model floor, then `default` (`YR`, `@116026`).
It is latched for the session. `counter_steer` adds a "Delegating to subagents" section (`@116645`) that tells the model to do small work inline, not fan out on small tasks, not spawn agents to re-verify, and keep spawn counts low.
For `claude-opus-5` the registered model floor is `no_nudges` (`chunk-phacttch.js@2019690`), and a separate section tells that model: "Do not use the Agent tool, workflows, or deep-research unless the user, a CLAUDE.md file, or a skill asks for it" (`@2021102`, text `@1997316`; flag `tengu_slate_bittern`).
Runtime: that sentence is in the `claude-opus-5` system prompt and in none of the 12 other models tried. VERIFIED-BOTH. The server-side values of `tengu_thistle_grebe` for other models are UNKNOWN.

## 6. Fallback and escalation

Fallback replaces the failing model for the rest of the turn chain. There is no "escalate to a stronger model when stuck" logic.

**Triggers** (all throw `FallbackTriggeredError`, class `gM`, `chunk-phacttch.js@2551755`; VERIFIED-STATIC):

| Trigger | Condition | Anchor |
|---|---|---|
| Repeated overload | HTTP 529 counted consecutively, 3 in a row (`J8=3`), with an explicit fallback model, or `FALLBACK_FOR_ALL_PRIMARY_MODELS`, or a primary model from a short list | `@2730240`, `@2721070` |
| Model not found, permission denied, or server error | Status classification, with an explicit fallback or an implicit first-party one | `@2728628` |
| Last resort | Non-retryable status with a fallback configured | `@2732473` |
| Mid-stream failure | Server error or timeout during streaming, fallback present | `@2873232` |
| Per-model block | A remote block message for the model, fallback present | in the same function family |

Configuration: `--fallback-model`, settings `fallbackModel` (array, tried in order, `"default"` expands to the default model; schema `chunk-ff982hys.js@218750`), built by `oue` (`chunk-cvvnq4he.js@379253`).
Fallback models equal to the failing one are removed. On Bedrock and Vertex a derived fallback can be added for known models (`uBn`). Refusal-based fallback (`refusal_fallback` capability) is a separate path involving user consent and credits and is not followed.

**What happens.** The turn loop catches the error, moves to the next entry of the chain, sets `mainLoopModel` to it, records `availabilityFallback:{primaryModel, fallbackModel}`, abandons the partial attempt,
emits a `model_fallback` system message and event `tengu_model_fallback_triggered`, and retries (`chunk-93pksqr2.js@172400` to `@175900`).
The loop continues with the same message array and an `abandonAttempt` call; the next request in E20 carried the same conversation on the new model (INFERRED from the loop structure plus E20's successful fourth request; the exact message contents were not diffed).
A window change notice is produced when the fallback model has a different context window (`td`, INFERRED from its use). If no usable fallback remains, the original error is thrown.

Runtime (earlier runs E20 and E21, `03-runtime-experiments.md` lines 736 and 737, not repeated; VERIFIED-RUNTIME):

* E20: `--model haiku --fallback-model sonnet`, three injected 529s. Two retries, then on the third 529 a `model_fallback` frame (`trigger: "overloaded"`, `claude-haiku-5-5` to `claude-sonnet-5-5`), then a request on the new model that succeeded. Matches `J8=3`.
* E21: `--model haiku`, four injected 529s, **no** fallback model. Four retries on the same model, then success. No switch and no error. The repeated-overload branch needs either a configured fallback, the environment switch `FALLBACK_FOR_ALL_PRIMARY_MODELS`, or a primary model from a short built-in list (`@2730240`); haiku is not on that list for this account. The list members were not decoded (UNKNOWN).

So the fallback only fires when the user, a setting or the short list asks for it. By default a 529 storm is retried on the same model.

## 7. Advisor (a configured stronger model, not routing)

`/advisor`, `--advisor <model>` and the settings key `advisorModel` enable a server-side `advisor_20260301` tool that lets the main model consult a stronger model (`chunk-phacttch.js@867425`, command `@1644901`).
Gates: first-party provider, not disabled by `CLAUDE_CODE_DISABLE_ADVISOR_TOOL`, and either `CLAUDE_CODE_ENABLE_EXPERIMENTAL_ADVISOR_TOOL` or flag `tengu_sage_compass2` (`chunk-zdd7h7by.js@329457`, `@329558`).
The advisor's catalog rank must be at least 2 (`Gw`, `@330161`), and at launch the CLI rejects an advisor that is "not at least as capable as the main model" (message at `chunk-m44bzxs2.js@134165` region). Fork helper agents (compaction and similar) receive "Never consult the advisor tool." (`chunk-phacttch.js@2533994`).
The user chooses the advisor. Whether the main model calls it at useful moments is model behavior. Not tested (no live model).

## 8. What else the model changes

### 8.1 Prompt layout and tools

Layout (lean or full) is decided by `de(model)` (`chunk-bykygzr4.js@5818`): the capability `lean_prompt` wins if the catalog or the environment sets it; otherwise `claude-mythos-5` is lean;
otherwise ids containing `claude-3-`, `haiku`, `sonnet`, or equal to opus 4.0, 4.1, 4.5, 4.6, 4.7 get the full layout; unknown models follow a provider check. `CLAUDE_CODE_SIMPLE_SYSTEM_PROMPT` forces lean.
Result: current models are lean through the catalog, and **`claude-sonnet-5` is full** because its catalog entry has no `lean_prompt` and its name contains `sonnet`.

The task-tracking tools `TaskCreate`, `TaskGet`, `TaskList`, `TaskUpdate` are enabled by `s2()` (`chunk-phacttch.js@3579584`): always in background sessions or on host opt-in, else only when the main model is in a fixed list of
older ids (`EOr`, `@3579168`: claude-3 models, opus 4.0 to 4.7, sonnet 4.0, 4.5, 4.6, haiku 4.5), or with `CLAUDE_CODE_ENABLE_TODO_TOOLS`. `CLAUDE_CODE_ENABLE_TASKS=false` disables them (`chunk-zkrrxfpr.js@6323`).

### 8.2 Prompt sections gated by capability

The helper `JH(name, canonicalModel, model, envOverride)` (`chunk-bykygzr4.js@1942`) decides a flag in this order: the environment override; the capability lookup `w_` (environment, server lookup, catalog);
three built-in defaults; then a per-model remote client-data value, which can switch a default off or an unlisted flag on (`Qkr`). The built-in defaults (`@1636`):

* Group Q (`turn_updates`, `bash_output_audience_note`, `silent_turn_reminder`, `thinking_display_updates`): on when the model has `fable_5_1_prompt_bundle` (`RRe`, `chunk-tydh8ra2.js@829`).
* Group X (`bison_cairn`, `larch_cistern`): on when the model has `opus_5_prompt_bundle` and flag `tengu_fennel_godwit` is off (`YNn`, `@1466`).
* Group J (`silent_turn_reminder`, `quizzical_shore`): on when the model has `opus_5_5_prompt_bundle` (`y`, `@1572`).

**Resolution of the inherited unknowns.**

* Section `delivering_work_max` (`chunk-phacttch.js@2020899`, text `@2015444`): included when `CLAUDE_CODE_BISON_CAIRN` decides it, else when `RRe(model)` (the `fable_5_1_prompt_bundle` models) or `bison_cairn` holds (the `claude-opus-5` default, or client data).
  The text says, among other things: do the requested scope, "Finish the whole task, not just easy parts - report completion only when fully done", "If part of the scope turns out to be blocked ... finish every other part in full and say explicitly what you left out and why", and treat a repeated user request as a decision.
* Section `overcorrection` ("# Corrections", `@2020982`, text `@2017493`): included when `larch_cistern` holds, so by default only `claude-opus-5`.
* Autonomy block from `uBo` (`@1997648`): requires flag `tengu_amber_sextant` (default on) and either `fable_5_mitigations` (`ZH`, `chunk-tydh8ra2.js@710`: catalog fable-5, fable-5-1, mythos-5-1, or the exact id `claude-mythos-5`) or `amber_astrolabe`.
  The text tells the model it operates autonomously, not to ask "Want me to...?" for reversible actions that follow from the request, to report findings and stop when the user is only asking a question, and: "Before ending your turn, check your last paragraph. If it is a plan, an analysis, a question, a list of next steps, or a promise about work you have not done ... do that work now with tool calls." It also asks for evidence before state-changing commands.
  Registered as `autonomy_append` (`@2021385`).

Runtime confirmation (E90p; 1 means the marker was in the main request's system prompt; VERIFIED-RUNTIME):

| Model | Layout | Tools | Delivering work | Corrections | Autonomy block | Explore nudge | Effort | max_tokens |
|---|---|---|---|---|---|---|---|---|
| claude-opus-5 | lean | 26 | 1 | 1 | 0 | 0 | high | 64,000 |
| claude-opus-5-5 | lean | 26 | 0 | 0 | 0 | 0 | medium | 128,000 |
| claude-sonnet-5-5 | lean | 26 | 0 | 0 | 0 | 0 | medium | 128,000 |
| claude-haiku-5-5 | lean | 26 | 0 | 0 | 0 | 0 | medium | 128,000 |
| claude-opus-4-8 | lean | 26 | 0 | 0 | 0 | 0 | high | 64,000 |
| claude-fable-5 | lean | 26 | 0 | 0 | 1 | 0 | high | 64,000 |
| claude-fable-5-1 | lean | 26 | 1 | 0 | 1 | 0 | high | 64,000 |
| claude-mythos-5 | lean | 26 | 0 | 0 | 1 | 0 | high | 64,000 |
| claude-mythos-5-1 | lean | 26 | 1 | 0 | 1 | 0 | high | 64,000 |
| claude-sonnet-5 | **full** | 26 | 0 | 0 | 0 | 1 | high | 64,000 |
| claude-sonnet-4-6 | full | 30 | 0 | 0 | 0 | 1 | high | 32,000 |
| claude-opus-4-7 | full | 30 | 0 | 0 | 0 | 1 | xhigh | 64,000 |
| claude-sonnet-4-5 | full | 30 | 0 | 0 | 0 | 1 | none (thinking enabled) | 32,000 |

Every cell matches the static prediction. The 4 extra tools on the 30-tool rows are the Task family. Tool schema text sent per request was 106 KB for `claude-opus-4-7` and 78 KB for `claude-opus-5-5` (measured on the request bodies; part of the gap is the four Task tools, the rest is longer descriptions in the full layout).
All nine lean models and `claude-sonnet-5` carry the same 26 tools; none has the task-tracking tools in this headless setup. The lab runs are `-p` (non-interactive) sessions without the host opt-in; an interactive session that sets `todoToolsOptIn` was not run.

### 8.3 Guards that depend on the model

The read-before-edit guard is enforced only for a fixed list of ten older model ids (`chunk-bykygzr4.js@2857`). Details and runtime matrix are in report 01, section 10.
`max_tokens` and `effort` follow the catalog defaults shown above (clamped by `CLAUDE_CODE_MAX_OUTPUT_TOKENS`, `chunk-cvvnq4he.js@396606`).

### 8.4 Context and token budgets

* Window: `zv` (`chunk-cvvnq4he.js@395055`) returns 1,000,000 for models native at 1m or with an honored `[1m]` suffix, else the catalog window (200,000 default constants at `@393371`). `CLAUDE_CODE_DISABLE_1M_CONTEXT` turns the 1m path off.
* Auto-compaction window: `lv` (`chunk-phacttch.js@860717`) takes the first of: `CLAUDE_CODE_AUTO_COMPACT_WINDOW` (100k to 1m), the `autoCompactWindow` setting (global or per model), per-model client data, an experiment value, a model default, then the full window. Details in report 03.
* Blocking limit: window minus the smaller of max output and 20,000 (`wrr`, `@862702`).
* Bytes per token for context estimates: 4 for the older ids listed in `jN` (`chunk-cvvnq4he.js@383174`), 3 for every other model (`vh`, `@383453`). So newer models are counted conservatively.
  Read's own size check uses a separate file-type estimate (report 01 section 5), not `vh`.
* Output limit: catalog default, upper bound from the catalog, clamped by `CLAUDE_CODE_MAX_OUTPUT_TOKENS`.

## 9. Decision tree

```
request for model M
 1. M0 = session override (/model picker)
        else --model value
        else ANTHROPIC_MODEL
        else settings.model
        else account default (not followed)               tt(), wh(), DIt(), Jl()
 2. M1 = resolve alias / deprecated remap in M0; apply availableModels allowlist
 3. if permission mode == plan and configured name is "opusplan": M1 = newest Opus
    if permission mode == plan and configured name is "haiku":    M1 = newest Sonnet     fg(), gvr()
 4. request layout, tools, prompt sections, max_tokens, effort, thinking, window, guards
    are read from M1 (catalog + lists)                                                     section 8
 5. on 529 x3, not found, permission denied, server error, mid-stream failure, block:
       if a fallback model is configured (or implicit on first party): M1 = next in chain
       keep messages; abandon partial attempt; emit model_fallback                         section 6
 subagent launch from parent model P:
    P1 = FORCE env ? env model
         : tool "model" param ? resolve(param)
         : definition model (not "inherit") ? resolve(definition)
         : SUBAGENT_MODEL env set and definition has no model ? env model
         : P
    Explore, first party, P above Opus, no explicit param: P1 = newest Opus                section 5
```

Static, configurable, gated:

| Item | Static in code | User-configurable | Remote or account-gated |
|---|---|---|---|
| Catalog of models, windows, defaults | yes | `CLAUDE_CODE_MODEL_CAPABILITIES` | server capability lookup, per-model client data |
| Plan-mode swap | yes | the alias in `--model` / settings | org model restrictions |
| Explore cap | yes | `..._DISABLE_EXPLORE_INHERIT_CAP`, tool param | provider |
| Delivering work, corrections, autonomy | the model lists | env overrides per section | flags and client data (`tengu_amber_sextant`, `tengu_fennel_godwit`, ...) |
| Delegation steer | opus-5 floor | `CLAUDE_CODE_THISTLE_GREBE` | `tengu_thistle_grebe`, `tengu_slate_bittern` |
| Fallback chain | triggers and counts | `--fallback-model`, settings | implicit first-party fallback |
| Advisor | gate logic | `--advisor`, `/advisor` | `tengu_sage_compass2` |
| Task-tracking tools | model list | `CLAUDE_CODE_ENABLE_TODO_TOOLS`, `..._ENABLE_TASKS` | none found |

## 10. What this means for the coding workflow

1. The CLI has no quality router. Any claim that Claude Code "picks the right model for the job" is false for this build (VERIFIED-STATIC bounded negative: the model inputs listed in section 9 are exhaustive for the request path read; helper calls that use a small fast model (`Ow`, `chunk-cvvnq4he.js@354918`) were not enumerated).
2. Behavior differences between models come from different prompts and tool sets, not from different code paths. The most coding-relevant differences are: completion discipline text (Delivering work, autonomy block) only on fable, mythos and opus-5; read-before-edit enforced only on older models; task tools only on older models; delegation nudges only on the full layout, and suppressed for opus-5.
3. A session on `claude-opus-5-5`, `claude-sonnet-5-5` or `claude-haiku-5-5` (what the aliases `opus`, `sonnet`, `haiku` resolve to) receives none of the completion-discipline sections. Whether that matters for task success is untested.
4. Model choice is not part of the saved plan or the compaction state beyond the session setting. A fallback keeps the messages but changes the model, and so potentially the prompt layout and tool set, mid-session. The effect of that on behavior is untested (HYPOTHESIS).

## 11. Lessons for DaVinci (HYPOTHESES, none tested)

* HYPOTHESIS: explicit per-role model slots (explorer, planner, implementer, verifier) with a visible resolution order are clearer than Claude Code's implicit inheritance plus caps. They also make it testable which tier did which step.
* HYPOTHESIS: a router that uses measured signals (files touched, failing test count, retry count) to escalate model tier could beat static configuration. Claude Code gives no evidence either way; it has no such router.
* HYPOTHESIS: prompt sections that enforce completion discipline ("report completion only when fully done", "do the deferred work now") are cheap to port as a mandatory section for every model instead of a few. Their effect is unmeasured.
* HYPOTHESIS: pairing every guard with a model-independent code check (for example read-before-edit as code for all models) removes a silent difference between models.
* Observed design to avoid: the same session can silently switch layout and tool set when fallback or plan mode changes the model, and nothing records that in a user-visible state beyond a system message.

## 12. Unknowns and what would settle them

| Unknown | Would be settled by |
|---|---|
| Server-side values of `tengu_thistle_grebe`, `tengu_slate_bittern`, `tengu_fennel_godwit`, per-model client data | Reading a live account's feature data. Not read. |
| The deprecated-model remap gate `UIt()` | Decoding it and its inputs. It is entitlement-related, so left out. |
| Account default model (`d8`, `Av`) | Out of scope (billing, auth). |
| Whether the Explore cap helps or hurts exploration | A model experiment. Excluded by the brief. |
| Behavior of refusal-based fallback (`refusal_fallback`) | It involves consent and credits. Excluded. |
| Callers of the small fast model `Ow` | Enumeration. Excluded as exhaustive caller enumeration. |

## 13. Reproduce

```
python -I research/claude-code/tools/scenarios/run_matrix_e90_routing.py k haiku,claude-fable-5-1,claude-opus-5-5          # explore child by parent
MODE=gpmodel python -I .../run_matrix_e90_routing.py q claude-opus-5-5                                                       # tool model param
python -I .../run_matrix_e90_routing.py n claude-fable-5-1 CLAUDE_CODE_SUBAGENT_MODEL=sonnet CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1
MODEL=<model> bash .../run_e50.sh <id> baseline "" plan ; python -I research/claude-code/tools/prompt_sections_probe.py <id>
```

Modes added to `build_e50.py` and `run_e50.sh`: `gpmodel`, `gpplain`, `exploremodel`, `planplain`, and `E50_ENV` for child environment variables
(the lab runner scrubs inherited `CLAUDE*` and `ANTHROPIC*` variables, so env settings must be passed with `--env`; a first attempt without that was invalid and its runs were discarded).
Runs: E90k explore child by parent (9 models), E90l to E90o env and cap variants, E90p prompt sections (13 models), E90q to E90w agent model parameter and env, E90x plan-mode alias matrix (6 models by 2 modes).

## 14. Anchors

All anchors in this report are listed with their literal in `final-runtime-control-decompilation/13-source-pins.json` .

### Pinned anchors by name

Each anchor starts at the literal recorded in `13-source-pins.json`.

| Name | Anchor |
|---|---|
| `catalog_latest` | `chunk-bnqade36.js@19657` |
| `catalog_haiku55` | `chunk-bnqade36.js@3744` |
| `catalog_sonnet5` | `chunk-bnqade36.js@7631` |
| `catalog_opus47` | `chunk-bnqade36.js@11966` |
| `catalog_opus5` | `chunk-bnqade36.js@13699` |
| `catalog_opus55` | `chunk-bnqade36.js@14669` |
| `catalog_fable51` | `chunk-bnqade36.js@16598` |
| `catalog_mythos5` | `chunk-bnqade36.js@17645` |
| `catalog_mythos51` | `chunk-bnqade36.js@18092` |
| `cap_env` | `chunk-bnqade36.js@24039` |
| `cap_catalog` | `chunk-bnqade36.js@23940` |
| `third_party` | `chunk-bnqade36.js@30664` |
| `jh_sets` | `chunk-bykygzr4.js@1636` |
| `jh_opus5_bundle` | `chunk-bykygzr4.js@1466` |
| `jh_opus55_bundle` | `chunk-bykygzr4.js@1572` |
| `jh_bison` | `chunk-bykygzr4.js@5163` |
| `jh_larch` | `chunk-bykygzr4.js@5238` |
| `jh_amber` | `chunk-bykygzr4.js@5072` |
| `sec_corrections` | `chunk-phacttch.js@2020982` |
| `sec_delivering_text` | `chunk-phacttch.js@2015444` |
| `sec_corrections_text` | `chunk-phacttch.js@2017493` |
| `sec_autonomy_fn` | `chunk-phacttch.js@1997648` |
| `sec_autonomy_reg` | `chunk-phacttch.js@2021385` |
| `sec_opus5_delegation` | `chunk-phacttch.js@2021102` |
| `sec_opus5_delegation_text` | `chunk-phacttch.js@1997316` |
| `sec_counter_steer` | `chunk-phacttch.js@2021023` |
| `steer_resolve` | `chunk-cvvnq4he.js@116026` |
| `steer_text` | `chunk-cvvnq4he.js@116645` |
| `main_explicit` | `chunk-cvvnq4he.js@356337` |
| `main_env` | `chunk-cvvnq4he.js@356414` |
| `main_alias` | `chunk-cvvnq4he.js@387332` |
| `main_default` | `chunk-cvvnq4he.js@378555` |
| `main_default_setting` | `chunk-cvvnq4he.js@366970` |
| `plan_clamp` | `chunk-cvvnq4he.js@364941` |
| `plan_map` | `chunk-cvvnq4he.js@363981` |
| `plan_resolve` | `chunk-cvvnq4he.js@364422` |
| `allowlist` | `chunk-cvvnq4he.js@339630` |
| `allowlist_sub` | `chunk-phacttch.js@747442` |
| `sub_env` | `chunk-phacttch.js@745309` |
| `sub_force` | `chunk-phacttch.js@747259` |
| `sub_family_match` | `chunk-phacttch.js@747718` |
| `explore_cap_rank` | `chunk-phacttch.js@201953` |
| `plan_agent` | `chunk-phacttch.js@204673` |
| `gp_agent` | `chunk-phacttch.js@2067564` |
| `fallback_529` | `chunk-phacttch.js@2730240` |
| `fallback_529_thr` | `chunk-phacttch.js@2721070` |
| `fallback_notfound` | `chunk-phacttch.js@2728628` |
| `fallback_last_resort` | `chunk-phacttch.js@2732473` |
| `fallback_apply` | `chunk-phacttch.js@2585401` |
| `fallback_midstream` | `chunk-phacttch.js@2873232` |
| `advisor_flag` | `chunk-zdd7h7by.js@329558` |
| `advisor_rank_gate` | `chunk-zdd7h7by.js@330161` |
| `advisor_cmd` | `chunk-phacttch.js@1644901` |
| `task_models` | `chunk-phacttch.js@3579168` |
| `task_enabled` | `chunk-phacttch.js@3579717` |
| `window_consts` | `chunk-cvvnq4he.js@393371` |
| `bytes_per_token` | `chunk-cvvnq4he.js@383453` |
| `model_facts` | `chunk-phacttch.js@405864` |
| `blocking_limit` | `chunk-phacttch.js@862702` |
| `explore_inherit_env` | `chunk-phacttch.js@201851` |
