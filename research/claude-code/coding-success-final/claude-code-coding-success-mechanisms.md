# Claude Code coding-success mechanisms (final consolidated report)

Target: Claude Code CLI 2.1.296, extraction `extracted/2.1.296/~BUN/root`. This report stands alone. It states what the local code
enforces, what prompt text asks for, what the model decides, and what could not be seen. Detail lives in
`01-repository-exploration.md`, `02-model-routing.md` and `03-compaction-fidelity.md` in this directory and in
`../coding-workflow-decompilation/`. Anchors in this report are pinned in `../final-runtime-control-decompilation/13-source-pins.json`.

## 0. Scope, labels and limits

Labels: VERIFIED-STATIC (function bodies read), VERIFIED-RUNTIME (observed in a pinned-binary run), VERIFIED-BOTH, INFERRED, HYPOTHESIS, UNKNOWN, CONTRADICTED.

Limits that apply to everything below:

* **No live-model run was made in this mission.** Runtime evidence comes from the lab proxy, which replies with scripted turns. It proves what the CLI sends, accepts, refuses and ends with. It does not show how any model behaves.
* Server-side behavior (what the API or a feature flag does on the other side) is not visible. Flag-gated rules were read with the lab account's flag values.
* Negative findings are scoped: "not found" means not found in the regions named.
* Nothing here says Claude Code finishes more tasks than another agent. Every advantage claimed for DaVinci is a HYPOTHESIS.

## 1. Answers to the six enforcement questions

| Question | Answer | Who decides | Label |
|---|---|---|---|
| Is exploration forced before implementation? | No. No code path requires a search or read before the first edit. The Explore agent exists and prompts nudge toward it, but the model chooses. The only read gate is the read-before-edit check, and it is active only for four legacy model ids (section 4.2). | Model | VERIFIED-BOTH (E50s edited without exploring; report 01) |
| Is planning mandatory? | No, with one exception. Plan mode is entered by the model through EnterPlanMode, by `--permission-mode plan`, or by the user. A spawned teammate with `planModeRequired` is launched in plan mode by code (`chunk-b6yrqcs2.js@17997`). | Model or user; code only for that teammate flag | VERIFIED-STATIC |
| Must tests run before completion? | No. A turn with no tool call ends as `completed` unless a Stop hook blocks it (`chunk-93pksqr2.js@188920`). E50s finished with no test run: `success`, exit 0. | Model, unless a user hook | VERIFIED-BOTH |
| Must failing tests be corrected? | No. E50t ran a test that exited 1, then said "Done.", and finished `success`, exit 0, with the file unchanged. | Model, unless a user hook | VERIFIED-RUNTIME |
| Is an independent reviewer mandatory? | No. No built-in verifier or reviewer agent is registered (`chunk-phacttch.js@2086295`; report 04 section 8). Review exists as optional commands, plugins and a hook type. | Model or user | VERIFIED-STATIC |
| Is there a code-enforced acceptance gate? | Only a gate the user configures: a `Stop` hook (command, or an agent-type hook whose prompt says "verify that the agent completed the given plan", `chunk-phacttch.js@2911347`). E50v: a Stop hook that blocks while tests fail turned a false "Done." into another turn. The block count is capped at 8 by default (`chunk-93pksqr2.js@188378`, E40). | User configuration | VERIFIED-BOTH |

**Retained finding:** no universal local testing or acceptance controller was found in the loop, executor, Stop-hook path, result builder, prompts or the built-in agent registry. No new evidence contradicted it.

## 2. Reconstructed workflow

Each stage lists what code does, what the model decides, the state passed on, whether it is enforced or recommended, failure modes and the lesson for DaVinci.

| Stage | Local code | Model decides | State passed | Enforced or recommended | Failure modes | Lesson (HYPOTHESIS) |
|---|---|---|---|---|---|---|
| 1. User request | Parses input, builds the first request: system prompt (lean or full by model), tools, CLAUDE.md and reminders (`02`) | Nothing yet | Prompt text, attachments | Enforced layout; content depends on model capability flags | Model-dependent prompt sections change behavior silently (section 5) | Make layout and coding sections an explicit, logged function of the model |
| 2. Repository exploration | Provides Glob, Grep, Read, Agent (Explore). Applies limits: Glob 100 files, Grep 250 lines, Read 256 KB and 25,000 tokens (`01`) | Whether to search at all, which tool, when to delegate | Tool results in history | Recommended only (prompt nudge, "more than 3 queries", full layout only) | Glob drops the newest files; Grep returns a partial result without warning on timeout; the Read "2000 lines" text is not enforced | Surface truncation and timeouts to the model; a deterministic index can beat repeated greps |
| 3. Context gathering | Reads, attachments, CLAUDE.md, memory, microcompaction of old tool results | What to read and keep | `readFileState` (used by the read-before-edit check on legacy models) | Enforced limits, model-chosen content | Read state is lost at compaction (`03`) | Track what was read as explicit state |
| 4. Planning | Plan mode: reminder text, permission floor `Lpn` (`chunk-phacttch.js@3355376`) turns non-read-only calls into an ask, ExitPlanMode needs approval | Whether to plan, plan content, when to exit | Plan file, mode | Enforced only when plan mode is on; entering it is the model's or user's choice | `-p` runs cannot leave plan mode (E50q) | Plan mode as a state with enforced write refusal is cheap and worth copying |
| 5. Implementation | Edit/Write tools validate inputs; read-before-edit check on 4 legacy models | What to change | File system | Enforced validation; strategy is the model's | Edits without reading on current models are allowed | Keep DaVinci's own stale-edit checks |
| 6. Tool execution | Validation, hooks, permissions, call, result mapping; safe tools run in parallel | Which calls | Tool results as user messages | Enforced | An error becomes a tool result and another turn; no automatic rerun | Fine as is |
| 7. Testing | None generic. The plan prompt asks for a verification section (`chunk-phacttch.js@4442498`); a full-layout line asks UI work to be tried in a browser (`@2002645`); an autonomous block asks the model to "run the tests and fix what fails" (gated, section 5) | Whether, what and when to test | Nothing | Recommended, model-gated, not enforced | A model can finish with no test run (E50s) | A test gate is a code feature, not a prompt feature |
| 8. Debugging and recovery | Transport retries, fallback model on repeated overload, output-token nudges, malformed-tool retry, compaction on overflow (`02`, `../coding-workflow-decompilation/06`) | Diagnosis and next attempt | Error text in history | Enforced for transport and context; none for test failures | No ledger of failed approaches; a failed test can be ignored (E50t) | Track failed approaches and last test result outside the prompt |
| 9. Verification | A configured Stop hook | Whether to verify | Hook output as a blocking reason | Enforced only if configured | Without a hook, nothing checks | Ship a default acceptance gate |
| 10. Completion | `completed` when no tools remain and no hook blocks (`chunk-93pksqr2.js@188920`); terminal reasons list (`chunk-80kqkekd.js@168441`) | The final text | Result subtype, exit code | Enforced termination; honesty of the claim is prompt-only | API errors can end as `success` with `is_error:true`, so exit status is not acceptance evidence | Never treat model prose or exit code as proof |

## 3. Verified mechanisms (summary)

| Mechanism | Finding | Source | Label |
|---|---|---|---|
| Search tools | Section 2 stage 2; details and runtime tables in `01` | `01` | VERIFIED-BOTH |
| Explore | Model `inherit`, capped to Opus when the parent ranks above it; Edit, Write, NotebookEdit and Agent removed by code; Bash only prompt-restricted; never invoked by code | `01`, `02`, `chunk-phacttch.js@2086295`, `chunk-jwmqjyrb.js@83520`, `chunk-jwmqjyrb.js@87492` | VERIFIED-BOTH |
| Code graph or symbol index | None found locally (bounded negative over search tools, registry and attachments); a LSP tool exists but no language server is bundled | `01` | VERIFIED-STATIC |
| Model choice | Configured defaults and rules, not task complexity | `02` | VERIFIED-BOTH |
| Prompt sections per model | Capability flags select the layout and several coding sections | `02` | VERIFIED-BOTH |
| Fallback | 3 consecutive 529s with a configured fallback switch the model and keep the messages | `02` (E20, E21) | VERIFIED-RUNTIME |
| Compaction | The model writes the summary; code re-attaches up to 5 small files, plan, skills, status and CLAUDE.md | `03` | VERIFIED-BOTH |
| Stop hook gate | Works and is capped | E40, E50v | VERIFIED-RUNTIME |
| Plan-mode write refusal | Observed in E50q (`Cannot write to <path> while in plan mode.`) | E50q | VERIFIED-RUNTIME |

## 4. Corrections to earlier findings

### 4.1 Corrections made in this mission

| Earlier statement | Where | Correction | Label |
|---|---|---|---|
| "Doing tasks", "Executing actions", "Using your tools" reach only claude-sonnet-4-5 and claude-opus-4-7 | `davinci-success-research/README.md` headline 2 | The full layout also reaches claude-sonnet-4-6 and claude-sonnet-5 (E90p, 13 models). The layout comes from the catalog `lean_prompt` capability. | CONTRADICTED, VERIFIED-RUNTIME |
| Read-before-edit is enforced ("File has not been read yet") | `static-04-tools-permissions-hooks.md` lines 385 and 1240 | Enforced only for claude-sonnet-4-5, claude-opus-4-5, claude-haiku-4-5 and claude-opus-4-6. Not applied for haiku-5-5, sonnet-5-5, opus-5-5, fable-5-1, mythos-5 or opus-4-7. | VERIFIED-RUNTIME (E90 matrix, `01`) |
| The Read tool text says 2,000 lines | tool description | Not enforced; a 3,000-line file was returned whole. Caps are 256 KB and 25,000 tokens. | CONTRADICTED, VERIFIED-RUNTIME |
| Compaction re-attached files "truncated" | `03-runtime-experiments.md` E17c | A restored file is whole (5,000 tokens or less) or replaced by a one-line pointer. Selection is by file mtime, not read recency. | CONTRADICTED, VERIFIED-RUNTIME |
| The 4 task-tracking tools are part of the standard toolset | implied by `static-04` | They exist only for an old-model list, background sessions, `todoToolsOptIn` or `CLAUDE_CODE_ENABLE_TODO_TOOLS` (30 versus 26 tools) | VERIFIED-BOTH |
| The model table behind `V4` is unknown | `coding-workflow-decompilation/10`, section 9 | `V4` is the catalog `lean_prompt` capability (`chunk-bykygzr4.js@6140`), so the lean-layout sections ("Report outcomes faithfully: if tests fail, say so with the output", `chunk-phacttch.js@1988701`) reach lean-layout models only | VERIFIED-STATIC |
| Predicate for "Delivering work" and the autonomy block unknown | `coding-workflow-decompilation/02` | Resolved in `02` of this directory | VERIFIED-STATIC |
| Plan-mode reminder role of `OYe` unknown | remaining-subsystems | Plan-mode reminder attachment re-added after compaction | VERIFIED-STATIC |

### 4.2 Claims revalidated without change

| Claim | Evidence | Label |
|---|---|---|
| The ordinary no-tool path ends `completed` unless a Stop hook blocks | `chunk-93pksqr2.js@187906` (`stop_hook_prevented`), `chunk-93pksqr2.js@188920` (`completed`), E50s, E50t | VERIFIED-BOTH |
| The Stop-hook block cap is 8 by default | `chunk-93pksqr2.js@188378`, E40 | VERIFIED-BOTH |
| Tool-using turns continue until no tools remain or a limit is hit | `chunk-93pksqr2.js@199182` | VERIFIED-STATIC |
| API errors can appear as `success` with `is_error:true` | `chunk-80kqkekd.js@168441` terminal list, existing report 08 | VERIFIED-STATIC |
| No default verifier or reviewer agent | `chunk-phacttch.js@2086295` | VERIFIED-STATIC |
| Plan mode requires approval to leave; `-p` runs cannot leave it | E50q | VERIFIED-RUNTIME |

### 4.3 Earlier unknowns, closed or downgraded

| Unknown | Status now |
|---|---|
| Predicate for "Delivering work" and the `uBo` autonomy block | Closed (`02`). Needs `tengu_amber_sextant` and either fable-5 family mitigations or `amber_astrolabe`. |
| Goal-evaluation Stop hook `Za` | Located: `chunk-93pksqr2.js@67408`. An agent-type hook runs a verification prompt (`chunk-phacttch.js@2911347`). Server flag details stay UNKNOWN; not coding-critical. |
| Plan-mode Bash rule | **Still UNKNOWN.** The floor `Lpn` (`chunk-phacttch.js@3355376`) makes a non-read-only passthrough decision ask with the message "Cannot call <tool> while in plan mode" (`chunk-phacttch.js@3361916`), but `Vxr` exempts some tools and was not fully decoded, so whether Bash falls under it was not settled. The plan prompt separately forbids non-read-only tools. |
| ToolSearch body and caller set | **Still UNKNOWN.** Not coding-critical. |
| Model table behind `V4` | Closed above. |

## 5. Code-enforced versus prompt or model

| Behavior | Enforced by code | Prompt guidance | Model choice | Unknown or external |
|---|---|---|---|---|
| Layout, tool set, effort, max tokens | Yes, as a function of model and flags | No | No | Account flags |
| Search limits and truncation | Yes (Glob 100, Grep 250, Read caps) | Partly wrong (Read lines) | No | No |
| Whether to explore | No | Nudge (full layout) | Yes | No |
| Read before edit | Legacy models only | Some prompts | Yes | No |
| Plan mode write refusal | Yes when on | Reminder text | Entering it | Team inbox paths |
| Run tests | No | Some model-gated sections | Yes | User Stop hook |
| Fix failing tests | No | Autonomous block (gated) | Yes | User Stop hook |
| Review by another agent | No | Optional | Yes | Plugins |
| Honest completion report | No | "Report outcomes faithfully" (lean layout only), "Delivering work" (some models) | Yes | No |
| End of the turn | Yes | No | The final text | Hooks |
| Summary content after compaction | No (a `<summary>` block must exist) | 9 requested sections | Yes | No |
| Model fallback on overload | Yes, rule-based | No | No | Server errors |

Model-dependent coding sections (from `02`): `delivering_work_max` for claude-opus-5, claude-fable-5-1 and claude-mythos-5-1; `# Corrections` for claude-opus-5 only; the autonomy block for the fable-5 family or `amber_astrolabe`; reduced delegation text for claude-opus-5 ("Do not use the Agent tool, workflows, or deep-research unless the user, a CLAUDE.md file, or a skill asks for it"); the "Delegating to subagents" section only under the `counter_steer` steer value, whose server values are UNKNOWN.

## 6. DaVinci capability gap matrix

DaVinci was inspected read-only: `README` files, `docs/repo-intelligence.md`, `crates/davinci-agent/src/{completion,compaction,delegation,lib}.rs`, `verification/README.md`, the token governor header and the coding prompt text. It was not modified. A symbol search that finds nothing is reported as "not found in <scope>", not as proof of absence.

| Mechanism | Claude Code evidence | DaVinci status | Potential improvement | Priority |
|---|---|---|---|---|
| Repository search with explicit truncation signals | Glob 100 oldest files, Grep silent partial on timeout (`01`) | PRESENT: `docs/repo-intelligence.md` says results carry `truncated`, `total`, and `text_search_partial` | Keep. Add a test that a timeout never returns an unmarked partial result | P2 |
| Persistent code graph and symbol index | None locally (`01`) | PRESENT for TypeScript and JavaScript (`repo_map`, `symbol_search`, `file_dependencies`, `related_files`, `code_query`); Rust and other languages not covered by that doc | Extend language coverage; HYPOTHESIS: an index cuts exploration turns, untested | P1 |
| Explore as a read-only agent with write tools removed by code | `chunk-phacttch.js@2086295`, `chunk-jwmqjyrb.js@87492` | UNKNOWN: `delegation.rs` is a code backstop for the user's "don't use subagents" instruction (which Claude Code leaves to the model); per-agent tool filtering for a read-only agent was not traced | Confirm that read-only agents lose write tools in code, not in prompt. Keep the delegation backstop: Claude Code has no equivalent | P2 |
| Graph engine (task-graph executor with scoped workers) | No equivalent; subagents are model-invoked | PRESENT (`native_extensions/graph`, controller attempts and continuation) | Run the existing benchmark before claiming gain; HYPOTHESIS | P1 |
| Token governor | Read caps, microcompaction of old tool results (`03`) | PRESENT: digest, offload and read dedupe (`token_governor.rs`). CC showed no read dedupe on 5 models | Keep; report digest events so the model knows output was digested | P2 |
| Model router | None by complexity; configured rules only (`02`) | UNKNOWN: no `ModelRouter` or routing symbol found in `crates/**/*.rs` by name; routing through provider configuration not traced | State the policy: a configured table plus an explicit per-task override, logged per request | P1 |
| Model fallback on repeated overload | 3 consecutive 529s switch model and keep messages (`02`) | UNKNOWN: no `fallback_model` setting found in `crates/**/*.rs` outside tests | Add a configured fallback model with state kept; HYPOTHESIS: fewer aborted tasks | P1 |
| Model-aware prompt layout and sections | Layout, task tools and coding sections vary by model capability (`02`) | UNKNOWN: prompt modules exist per model family (`prompt/gpt6.rs`, `prompt/astra.rs`); capability-table selection not traced | Log which sections reach each model so behavior differences are explainable | P2 |
| Plan mode with enforced write refusal | `Lpn`, E50q | PRESENT: `permission.rs` parses a plan, read-only mode and `completion.rs` checks `is_plan_mode()` | Verify write refusal is in code, not only in the prompt | P2 |
| Test, retest and acceptance gate | None by default; Stop hook only (section 1) | PRESENT and stronger: `CompletionEvidence` (Verified, Partial, Unverified, VerificationFailed, NotRequired), workspace snapshots, scoped fresh checks, a requirement review before finishing | Run the existing benchmark (built, not run) to measure it | P0 |
| Completion hook with block cap | Cap of 8 (E40) | PRESENT: `MAX_HOOK_BLOCKS = 3` | Document why 3 | P2 |
| Independent reviewer | None by default | PARTIAL: a requirement-coverage review prompt exists in `completion.rs` and it runs in the same agent; an independent agent was not found | HYPOTHESIS: a separate critic improves detection of missed requirements; untested | P1 |
| Read-before-edit | Enforced on 4 legacy models only (`01`) | PARTIAL: prompt text only ("Read and understand relevant code before editing it", `prompt/coding.rs:14`); a code check was not found by name | Add a code-level stale-read check that survives compaction | P1 |
| Summary instructions | 9 sections, no explicit test outcomes or ruled-out approaches (`03`) | PARTIAL: `SUMMARIZATION_PROMPT` has Goal, Constraints, Progress, Key Decisions, Next Steps, Critical Context, and keeps exact paths and errors; no test-outcome or failed-approach section; an incremental update prompt and a structured fold with source references exist | Add test outcomes and ruled-out approaches; check constraint survival deterministically | P0 |
| Re-attachment after compaction | 5 files by mtime, whole or pointer (`03`) | PARTIAL: `FileOperations` lists read, written and edited paths in the summary; content re-attachment not traced | Re-attach edited files first by use, not by mtime | P1 |
| Kept-tail note | "Summary written without seeing kept messages" (`03`) | UNKNOWN: `COMPACTION_SUMMARY_PREFIX` found; no equivalent note found by name | Add the note when a tail is kept verbatim | P2 |
| Honest completion wording | "Report outcomes faithfully" (lean layout only), "Delivering work" (model-gated) | UNKNOWN: coding prompt text was not read in full | Treat as prompt support only; the gate above is the real control | P2 |

## 7. Prioritized recommendations for DaVinci

1. **P0: run the built benchmark** (`davinci-success-research/benchmark`, six tasks, hidden acceptance tests, not run) with and without the verification layer. DaVinci already has the strongest local gate of the two systems; its effect is untested. Needs a paid model run and Julien's approval.
2. **P0: make summaries carry test outcomes and ruled-out approaches.** Claude Code's default arm does not ask for them, so they are lost with the tool results (`03`). Add the two sections and a deterministic check that every user constraint string still appears after compaction.
3. **P1: add a configured model fallback with preserved state.** Claude Code does this by rule after 3 consecutive overload errors (`02`). Log every switch.
4. **P1: add a code-level read-state check that survives compaction.** Claude Code's version is limited to legacy models and loses state at compaction (`03`); a better version re-attaches by use.
5. **P1: state the model-routing policy and log per-request sections.** Claude Code has no complexity routing; it has a configured table and many hidden per-model differences (`02`). Make DaVinci's differences visible.

Everything above except item 1's premise is a HYPOTHESIS about benefit; the Claude Code facts they rest on are labeled above.

## 8. Failure modes of this research

* Scripted runs cannot show model behavior, so no claim about success rate is made.
* Flag-gated rules were read with one account's flags.
* DaVinci was read at the README and module-header level for most rows. Statuses marked UNKNOWN or PARTIAL say what was not traced.
* The per-model layout facts depend on the catalog embedded in 2.1.296; a later version can change them.

## 9. Future Research. Only If Needed

* Run the benchmark above with live models (needs approval for cost).
* Summary quality with real models, per prompt arm (needs live runs).
* Plan-mode Bash rule (`Vxr` exemption) and ToolSearch, only if a coding decision depends on them.
* Server flag values for `tengu_curried_trinket` and `tengu_thistle_grebe` in other accounts.

The defined research mission is complete for what static analysis and scripted-proxy runs can show. These items need live-model runs or approval, not more decompilation.

## 10. Anchors

All anchors in this report are listed with their literal in `../final-runtime-control-decompilation/13-source-pins.json`:
`chunk-93pksqr2.js@187906`, `chunk-93pksqr2.js@188378`, `chunk-93pksqr2.js@188920`, `chunk-93pksqr2.js@67408`, `chunk-93pksqr2.js@199182`, `chunk-80kqkekd.js@168441`, `chunk-phacttch.js@2911347`, `chunk-phacttch.js@1988701`, `chunk-bykygzr4.js@6140`, `chunk-phacttch.js@2002645`, `chunk-phacttch.js@4442498`, `chunk-phacttch.js@3355376`, `chunk-phacttch.js@3361916`, `chunk-b6yrqcs2.js@17997`, `chunk-phacttch.js@2086295`, `chunk-jwmqjyrb.js@83520`, `chunk-jwmqjyrb.js@87492`.
