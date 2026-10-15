# 03. Compaction fidelity

Target: Claude Code CLI 2.1.296, extraction `extracted/2.1.296/~BUN/root`. Scope: what the summary instructions ask the model to keep,
what the implementation itself keeps or drops, and what comes back in the first request after compaction. The compaction machinery
(triggers, thrash breaker, hook order) is not re-decompiled here; `static-02-prompt-context-compaction.md` sections 2.9 to 2.11
and `remaining-subsystems-decompilation/02` and `/03` cover it. Out of scope as briefed: compaction followed by rewind (`$l`), shutdown cleanup, remote transcript mirroring.

## 0. Evidence base and limits

| Source | What it gives | Label |
|---|---|---|
| Section 11 anchors | Whole-function reads of the prompt builders, the summary message builder `L8`, the re-attachment function `Ske` and its helpers. Pinned in `final-runtime-control-decompilation/13-source-pins.json`. | VERIFIED-STATIC |
| Evaluation of the prompt builders in Node (`cke` for each arm) | The exact request text of each arm. The control text is 6,361 chars without and 6,403 chars with the custom instruction "Keep the token." | VERIFIED-STATIC |
| E17a, E17b, E17c | Earlier live-model compactions (manual and automatic). The control arm's 6,403-char request was captured there. | VERIFIED-RUNTIME |
| E90za to E90zq (scripted proxy, `tools/compaction_probe.py`) | The lab proxy answers with scripted turns, so no upstream model is called and **no summary written by a real model was inspected**. Each run records what the CLI sends in the compaction request and in the first request after it. Summaries: `runtime-logs/E90z*/compaction-probe.json`. They hold booleans, counts, hashes and file names only. | VERIFIED-RUNTIME |

Limits that apply to every statement below:

* **Nothing here measures how well a model summarizes.** The scripted summary is a fixed string. Every claim about what a summary "keeps" is a claim about what the prompt asks for, not what a model delivers.
* Asking a model to remember something does not guarantee that it is remembered. The only guarantees are the items the implementation itself re-injects (section 6).
* Token counts in scripted runs are artifacts (`pre_tokens: 15`). `count_tokens` replies are scripted (section 5), so the restore-size rule is verified for the CLI's decision logic, not for the real tokenizer.
* Lab runs used the manual `/compact` path. Automatic compaction was seen with a live model only in E17c. Partial compaction, the prompt-too-long retry and PreCompact hook instructions were not exercised.

## 1. Answer first

| Question | Answer | Label |
|---|---|---|
| Who writes the summary? | The model, in one extra request that reuses the turn's system text, tools and full history, with a long instruction appended. | VERIFIED-BOTH |
| Which instructions does it get? | One of five prompt arms. The default `control` arm lists 9 sections (section 3). The arm is chosen by env `CLAUDE_CODE_CURRIED_TRINKET`, else the server flag `tengu_curried_trinket`, else `control`. | VERIFIED-BOTH |
| Does the prompt ask for test outcomes and failed approaches? | Not by name in the default arm. They are reachable only through "Errors and fixes" and "Problem Solving". "Test output" appears only in an example of a custom instruction. | VERIFIED-STATIC |
| What does code keep without the model? | System prompt, CLAUDE.md and memory, up to 5 re-read files (only files of at most 5,000 tokens), the plan reference, invoked skills, background task and shell status, the plan-mode reminder, goal status, SessionStart(compact) hook output, the transcript path, any kept tail of recent messages, and the custom `/compact` text. | VERIFIED-BOTH |
| What is gone unless the summary carries it? | The original user prompt, every earlier tool call and tool result (including failing test output), file contents that were not re-attached, and the reasoning. | VERIFIED-RUNTIME |
| Is the file re-attachment "five most recently read, long ones cut short"? | No. Selection follows file modification time recorded at read, and a file over the size limit is replaced by a one-line pointer, not cut. | CONTRADICTED (the lean prompt's own claim, and the E17c prose) |
| Does compaction affect the read-before-edit guard? | Yes, on the legacy models that enforce it. Compaction clears the read state, and only re-attached files count as read afterwards. | VERIFIED-RUNTIME |

## 2. The compaction request

`cke(extra, arm, ...)` (`chunk-phacttch.js@2504347`) builds the instruction as: `wnn(replyShape)` (a "CRITICAL: Respond with TEXT ONLY. Do NOT call any tools" preamble that says tool calls will be rejected) + the arm's instructions + optional `Additional Instructions:` with the custom text + a closing reminder not to call tools.
The block is appended to the last user message of the full history.

| Property | Result | Label |
|---|---|---|
| History sent | The whole history, 22 messages in the scripted scenario, not a trimmed view. | VERIFIED-RUNTIME |
| System and tools | Same text and same tool list as the turn, so the prompt cache prefix is shared. Only `cache_control` differs. | VERIFIED-RUNTIME |
| Arm text on the wire | For all five arms the request equals the statically evaluated `cke(...)` byte for byte by SHA-256. The control arm's 6,403 chars match E17a's captured request. | VERIFIED-BOTH |
| Custom text | `/compact <text>` and CLAUDE.md "Compact Instructions" reach the model as the `Additional Instructions:` block (the control prompt tells the model that CLAUDE.md may add instructions). | VERIFIED-RUNTIME for the `/compact` argument; INFERRED for CLAUDE.md |
| Tools in the summary turn | The tools are listed but the prompt forbids using them and the CLI rejects tool calls. A reply with no `<summary>` block is a failed attempt (`cur`, `chunk-phacttch.js@2511817`). | VERIFIED-STATIC |
| No summary text | The compaction throws "Failed to generate conversation summary - response did not contain valid text content" (`chunk-phacttch.js@2567400`). Nothing is dropped in that case. | VERIFIED-STATIC |

## 3. What the summary prompt asks for

### 3.1 The five arms

| Arm | Reply shape | Size | What it asks | Label |
|---|---|---|---|---|
| `control` (default) | `<analysis>` then `<summary>` | 6,361 chars | The 9 sections in 3.2, an analysis pass first, verbatim preservation of security-relevant constraints. | VERIFIED-BOTH |
| `lean` | `<summary>` only | 2,077 chars | What the user is trying to get done and why; what was decided, learned, tried and ruled out; where the work stands; what comes next. States that the summary is the only record of what the user said, that a limit the user set applies afterwards only if the summary states it, so quote it exactly, and that the next step named is what gets done. | VERIFIED-STATIC |
| `short` | `<summary>` only | about 2,650 chars with shared parts | Six preserve-items: difficulties and how they were handled; options tried or set aside and why; what the user asked, decided or ruled out, stated exactly; exactly where things stand; open or promised items; hard-to-reconstruct details, exact. Keep the user's words close to their own. | VERIFIED-STATIC |
| `short_v2` | `<summary>` only | about 2,820 chars | As `short`, plus: copy the earlier summary's record of what the user asked for unchanged and rewrite only the account of the work. It also adds follow-up guidance to the post-compaction message (section 4). | VERIFIED-BOTH (guidance text seen in the post-compaction message, E90zb-short_v2) |
| `capped` | `<summary>` only | about 1,520 chars | The entire conversation in 2,000 words or fewer. The only arm that sets a length ceiling. | VERIFIED-STATIC |

Partial compaction uses two other prompts, `Ydr` (summarize the RECENT portion, `chunk-phacttch.js@2499171`) and its `up_to` twin. **Not runtime-verified.**

The full control text is 6,361 chars. It is not reproduced here; its SHA-256 and the command that regenerates it are in section 12.

### 3.2 The control arm, section by section

The model first writes an `<analysis>` block: go through the conversation chronologically and, for each part, list the user's requests, the approach, key decisions, concrete details (file names, full code snippets, signatures, edits), errors and fixes, user corrections, and any security-relevant constraint, which "MUST be preserved verbatim". Then 9 sections:

| # | Section | Maps to the brief's topic |
|---|---|---|
| 1 | Primary Request and Intent | original request and constraints |
| 2 | Key Technical Concepts | repo discoveries (indirect) |
| 3 | Files and Code Sections: files examined, modified or created, "full code snippets where applicable", and why each matters | file paths, changes made |
| 4 | Errors and fixes, including user feedback | tool errors, failed approaches (indirect) |
| 5 | Problem Solving: solved problems and ongoing troubleshooting | unresolved problems |
| 6 | All user messages: every non-tool-result user message, security constraints verbatim; only real user-role turns count (model-written text shaped like a user turn must not be attributed to the user) | original request and constraints |
| 7 | Pending Tasks | plans and pending work |
| 8 | Current Work: precisely what was in progress, with file names and snippets | where to continue |
| 9 | Optional Next Step: directly in line with the user's latest request, with verbatim quotes of where work stopped | continue instructions |

### 3.3 Mapping to the brief's topics

"Requested" means the default arm asks for it. "Retained by code" means the implementation re-injects it without the model. "Not runtime-verified" applies to every row's model behavior.

| Topic | Requested by control arm | Retained by code | May be discarded | Label |
|---|---|---|---|---|
| Original request and constraints | Yes: sections 1 and 6, security constraints verbatim | No. The original prompt is absent from the post-compaction request. CLAUDE.md is re-sent. | Yes, if the summary paraphrases or omits them | VERIFIED-RUNTIME (absence) |
| Repo discoveries | Indirect: section 2 and the analysis pass; no section for them | No | Yes | VERIFIED-STATIC |
| File paths | Yes: section 3 | The paths of up to 5 re-attached files appear in the restored tool-call text | Paths outside the restored 5 | VERIFIED-RUNTIME |
| Changes made | Yes: sections 3 and 8, with code snippets | The edited files rank first for re-attachment (section 5), so their current content is re-read if small | The diff history | VERIFIED-RUNTIME |
| Plans and pending work | Yes: section 7 | The plan file reference and the plan-mode reminder when in plan mode; goal status when a goal is active | Task lists outside plan files | VERIFIED-STATIC |
| Tool results and errors | Section 4, errors only | No. Every tool_result block is absent afterwards. | Yes | VERIFIED-RUNTIME |
| Failed approaches | Not by name; reachable through sections 4 and 5. The `lean` and `short` arms ask for "ruled out" and "set aside" explicitly. | No | Yes | VERIFIED-STATIC |
| Test outcomes | **Not requested by name.** | No. The failing test output is absent afterwards. | Yes | VERIFIED-RUNTIME |
| Unresolved problems | Section 5 ("ongoing troubleshooting") and 7 | No | Yes | VERIFIED-STATIC |
| Instructions to continue | Section 9 plus section 8. The message builder adds "Continue the conversation ... Pick up the last task as if the break never happened" (section 4). | Yes, that continuation text is code, not model output | The model's chosen next step can be wrong | VERIFIED-BOTH |

## 4. How the messages are rebuilt

The summary reply is post-processed by `Qdr` (`chunk-phacttch.js@2504575`): the `<analysis>` block is removed and `<summary>...</summary>` becomes "Summary:\n...". `L8` (`chunk-phacttch.js@2504760`) then builds the first message. In order:

1. An optional warning that the summary may restate content written by other people (artifact content), to be treated as data.
2. The lead sentence `SRt` (`chunk-8mpz435d.js@32635`): "This session is being continued from a previous conversation that ran out of context. The summary below covers the earlier portion of the conversation."
3. The summary.
4. A transcript pointer ("If you need specific details from before compaction ... read the full transcript at: <path>"). Present when a transcript path exists and the session is not in a remote mode. VERIFIED-RUNTIME in `-p` runs.
5. When the earliest part was too large to summarize: a note that it is NOT covered, and that the model should say so rather than guess.
6. When follow-up questions are suppressed: "Continue the conversation from where it left off without asking the user any further questions. Resume directly ... Pick up the last task as if the break never happened." The `short_v2` arm inserts its own guidance between those sentences: whatever is not started, not finished, not checked, or different from what the user asked for must be finished or put right before reporting back, each requested thing tried at least once, failures fixed.
7. When recent messages are kept verbatim after the summary, `Dnn` appends: the kept messages are the most recent ones and the summary was written without seeing them, so something it says has not happened yet may already have happened in them (`chunk-phacttch.js@2506294`).

**Layout of the first request after a manual `/compact`** (VERIFIED-RUNTIME, E90za3): `[user: summary message]`, `[system-role: empty message with effort]`, `[assistant: "No response requested."]`, `[user: reminders (CLAUDE.md etc.), the local-command caveat and command text, "Compacted", the new prompt]`, `[system-role: re-attached files, agent listing, environment and model identity, skills list]`.

| Present after compaction | Absent after compaction |
|---|---|
| Summary message, CLAUDE.md content, the `/compact` argument text, the new prompt, re-attached files (section 5) | The original user prompt, all tool_use blocks, all tool_result blocks, the failing test output |

Microcompaction runs earlier and is a separate discard path. Old tool results are replaced by "[Old tool result content cleared]" (`chunk-phacttch.js@4399105`; the cleared tool set and the minimum saving of 20,000 tokens are in `chunk-3qrxzjv5.js@99350`), and a server-side context edit `clear_tool_uses_20250919` is configured at `chunk-3qrxzjv5.js@102696`. A tool result can therefore be gone before any summary is written. Their trigger rules were not re-verified in this task.

## 5. Re-attachment (`Ske`)

`Ske` (`chunk-phacttch.js@2585926`) runs after `readFileState` is cleared (`chunk-phacttch.js@2567812`; the saved copy is passed in). Order of what it adds:

1. Recently read files (`zur`, `@2587436`): at most `RYe=5` files, each read through `l4t` (`@3695357`) in "compact" mode with a 5,000-token ceiling (`CYe`), total at most `Fur=50000`.
2. Local agent task status, running background shells, peer hand-back commands.
3. Plan file reference.
4. `OYe`: the plan-mode reminder attachment when the permission mode is plan. (This resolves the role left open in the earlier report.)
5. Invoked skills (`Kur`, `@2588174`): `$ur=5000` tokens each, `xYe=25000` in total.
6. Tool, MCP, agent and sandbox deltas; environment and model-identity restatement.
7. Goal status when a goal is active.
8. SessionStart(compact) hook output. (`NYe` was not decoded; minor.)

### 5.1 Which files come back

| Finding | Evidence | Label |
|---|---|---|
| Selection is `sort(timestamp descending).slice(0, 5)` over the saved read state (`chunk-phacttch.js@2587630`). `timestamp` is the file's modification time recorded at read, **not** the read order. | Same scenario, same read order, file mtimes reversed: E90zp-reversed restored app.py, notes.md, a.txt, b.txt, util.py (the files read earliest were newest on disk). Forward mtimes: app.py, d.txt, c.txt, util.py, b.txt. | VERIFIED-RUNTIME |
| An edited file ranks first, because the edit refreshes its recorded time. | app.py (edited) first in every run. | VERIFIED-RUNTIME |
| Files with equal mtimes make the restored set vary from run to run. | Earlier runs without distinct mtimes returned different sets (E90zn series, not committed). | VERIFIED-RUNTIME (superseded runs) |
| The lean prompt's sentence "up to five recently read files" is therefore inaccurate. | Rows above. | CONTRADICTED |

### 5.2 How big a file may be

| Finding | Evidence | Label |
|---|---|---|
| The CLI asks the API to count tokens unless its own estimate is at most a quarter of the cap. | E90zg1 and E90zg6: 0 `count_tokens` calls; E90zg2 to E90zg5 and E90zg7: 1 call. | VERIFIED-RUNTIME |
| A count of 5,000 tokens or less restores the whole file. | A 62 KB file was restored whole when the scripted count said 100 (E90zg2) and 4,900 (E90zg7). | VERIFIED-RUNTIME |
| A count above 5,000 gives a one-line pointer: "Note: <path> was read before the last conversation was summarized, but the contents are too large to include. Use Read tool if you need to access it." | Scripted count 5,100: util.py became `note_too_large` (E90zg5). A failed count call gave the same note. | VERIFIED-RUNTIME; the real tokenizer was not involved |
| There is no partial truncation. | The restore reader returns content or the note (`chunk-phacttch.js@4458754`). | VERIFIED-BOTH |

So the E17c prose "re-attached them truncated ('[Truncated: PARTIAL view ...]')" in `03-runtime-experiments.md` is wrong as stated. The PARTIAL strings in the E17c post-compaction requests came from the model's own re-reads. The "too large to include" note was also present in those requests. The lean prompt's "long ones cut short" is likewise inaccurate. Both are CONTRADICTED.

### 5.3 Effect on the read-before-edit guard (single process, E90zq)

Compaction clears the read state. Only re-attached files re-enter it. On the legacy models that enforce the guard (claude-sonnet-4-5, opus-4-5, haiku-4-5, opus-4-6; see `01-repository-exploration.md`):

| Edit target | Result |
|---|---|
| d.txt (re-attached) | Applied |
| notes.md, a.txt (read before compaction, not re-attached) | Refused: "File has not been read yet" |

On models that skip the guard (haiku-5-5, opus-4-7) all three edits applied. VERIFIED-RUNTIME, deterministic with `MTIME_ORDER=forward`. Separate-process `--resume` runs lose the read state across processes and were not used for this claim.

## 6. Enforced, prompted, model-chosen

| Behavior | Who decides | Label |
|---|---|---|
| Whether and when to compact | Code (thresholds, `/compact`, API errors) | VERIFIED-STATIC |
| The instruction text and the arm | Code plus a server flag | VERIFIED-BOTH |
| What the summary contains | The model. The prompt requests; nothing validates content. The only check is that a `<summary>` block exists. | VERIFIED-STATIC |
| Which 5 files return, and in what form | Code (mtime sort, 5,000-token rule) | VERIFIED-RUNTIME |
| That the model re-reads what it needs | The model. The transcript pointer and the "too large" note invite it. | VERIFIED-STATIC |
| That the user's constraints survive | The model, helped by the prompt wording. The code re-sends CLAUDE.md only. | VERIFIED-STATIC |

## 7. Failure modes

| Failure | Mechanism | Label |
|---|---|---|
| A user constraint stated only in conversation is lost | Not in CLAUDE.md, not copied into the summary | INFERRED from sections 3 and 4 |
| A failing test or its output is not carried | No section asks for test results; tool results are dropped | VERIFIED-RUNTIME (absence), INFERRED (consequence) |
| A restored-file set misses the files that matter | Selected by mtime, not by relevance or recency of use | VERIFIED-RUNTIME |
| A large file is replaced by a pointer | Over 5,000 tokens | VERIFIED-RUNTIME |
| Edit refused after compaction on guard models | Read state cleared | VERIFIED-RUNTIME |
| The summary says a step is pending that already happened | Summary written without seeing the kept tail; the `Dnn` note addresses it | VERIFIED-STATIC |
| The summary is invalid | No `<summary>` block fails the attempt and nothing is dropped | VERIFIED-STATIC |

## 8. Not runtime-verified

* The quality of any summary written by a real model, and the effect of each arm on fidelity (no live-model experiments were allowed).
* Partial compaction and the prompt-too-long retry.
* PreCompact hook text added to the instruction.
* The automatic-compaction path in scripted runs (E17c covers it with a live model, before this task's corrections).
* The server flag value in other accounts (`tengu_curried_trinket`).

## 9. Corrections to earlier statements

| Earlier statement | Correction |
|---|---|
| `03-runtime-experiments.md` E17c: files re-attached truncated with "[Truncated: PARTIAL view ...]" | A re-attached file is whole (5,000 tokens or less) or a pointer note. PARTIAL text came from the model's re-reads. |
| Lean prompt text: "up to five recently read files ... long ones cut short" | Selection is by recorded mtime; there is no truncation. |
| Role of `OYe` unknown | Plan-mode reminder attachment when the permission mode is plan. |

## 10. Lessons for DaVinci (HYPOTHESES, none tested)

* HYPOTHESIS: carry the facts a summary loses by construction as structured state, not prose: the original request, user constraints, the last failing test command and its result, and the list of files changed. Claude Code leaves these to the model.
* HYPOTHESIS: add an explicit test-outcome and ruled-out-approaches section. The default Claude Code arm does not name them.
* HYPOTHESIS: choose re-attached files by relevance (edited, then most recently used), not by file mtime.
* HYPOTHESIS: verify after compaction that stated constraints still appear in the summary, with a deterministic check.

## 11. Anchors

All anchors in this report are listed with their literal in `final-runtime-control-decompilation/13-source-pins.json`.

| Item | Anchor |
|---|---|
| Reply shape and control prompt | `chunk-phacttch.js@2487553`, `chunk-phacttch.js@2490398` |
| Lean, short and recent-portion prompts | `chunk-phacttch.js@2494710`, `chunk-phacttch.js@2496335`, `chunk-phacttch.js@2499171` |
| Arm table, builder, list, selector | `chunk-phacttch.js@2498265`, `chunk-phacttch.js@2504347`, `chunk-phacttch.js@2507189`, `chunk-phacttch.js@2507268` |
| Post-processing and checks | `chunk-phacttch.js@2504575`, `chunk-phacttch.js@2504709`, `chunk-phacttch.js@2511817` |
| Summary message and kept-tail note | `chunk-phacttch.js@2504760`, `chunk-phacttch.js@2506062`, `chunk-phacttch.js@2506294`, `chunk-8mpz435d.js@32635` |
| Read state cleared, no-summary error | `chunk-phacttch.js@2567812`, `chunk-phacttch.js@2567400` |
| Re-attachment, selection, constants, skills | `chunk-phacttch.js@2585926`, `chunk-phacttch.js@2587436`, `chunk-phacttch.js@2587630`, `chunk-phacttch.js@2559446`, `chunk-phacttch.js@2588174` |
| Restore reader and pointer note | `chunk-phacttch.js@3695357`, `chunk-phacttch.js@4458754` |
| Microcompaction | `chunk-phacttch.js@4399105`, `chunk-3qrxzjv5.js@102696` |
| Read token cap | `chunk-j0bhqprc.js@1284` |

## 12. Reproduce

```
python tools/compaction_probe.py <base id>                 # summarize a scripted compaction run
python tools/scenarios/build_e90_compact.py <base> [util bytes] [width] [count_tokens answer]
UTIL_BYTES=... COUNT_TOKENS=... tools/scenarios/run_e90_compact_1p.sh <base> [arm] [model]
python -m pytest -q tools/test_compaction_probe.py
```

The control arm's request SHA-256 (6,403 chars, with "Keep the token.") is `6ffda2b58888bf70086ca99b6ed2209e27a1643bee2863c03a34b1a6de09e60c`. Arms are selected with `CLAUDE_CODE_CURRIED_TRINKET`. Raw request bodies stay in `lab/raw` (uncommitted); they contain account data.
