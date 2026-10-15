# 02. Static-only findings and unknowns

Source: the extracted 2.1.296 module tree (not committed). Anchors and the full reading notes are in
`../static-02-prompt-context-compaction.md`, section "Coding-workflow control paths and the lean prompt (twenty-sixth
source pass)". This file keeps the conclusions and sorts them by what enforces them.

Labels: VERIFIED-STATIC = read in source, not run. VERIFIED-RUNTIME = also seen in an E50 run (see file 01).
Never read "VERIFIED-STATIC" as "executes at runtime". Decompiled text is not the original source.

## 1. What is enforced by code, what is text, what is left to the model

| Behavior | Enforced by code | Prompt text only | Left to the model | Evidence |
|---|---|---|---|---|
| Edits refused in plan mode (Write) | yes | reminder also sent | | VERIFIED-RUNTIME E50q; `Lpn` in static-02 section 25 |
| Cannot leave plan mode in `-p` | yes (tool disabled) | | | VERIFIED-RUNTIME E50q; `gK.isEnabled` |
| Mode restored after plan approval | yes, in `call()` after the ask | | | VERIFIED-STATIC `chunk-z3vv06zx.js@8810` |
| Plan approval by the user | yes, a permission "ask" (team mode: lead's inbox) | | | VERIFIED-STATIC `@7602`, `@8226` |
| Explore and Plan cannot edit with Edit or Write | yes, tool list | prompt says read-only | | Explore VERIFIED-RUNTIME E50r; Plan VERIFIED-STATIC only (not run) |
| Explore and Plan cannot write through the shell | **no** | prompt only | | Explore: tool succeeded, file existence STRONGLY INFERRED (E50u); Plan not run |
| Proactivity level sets the permission mode | yes (`mde`) | block text also sent | | VERIFIED-RUNTIME E50w |
| Run tests after a change | **no** | `proactive` block only; full layout models: UI check line | model | VERIFIED-RUNTIME E50s, E50t; E50p |
| Retest after a failed test | **no** | none found in lean layout | model | VERIFIED-RUNTIME E50t |
| Report failures honestly | no | lean body sentence `V0o` | model | VERIFIED-RUNTIME (text present, E50m); behavior UNKNOWN |
| Do not repeat a failed approach | no | coordinator worker prompt: "more than once"; autonomous addendum: retry after errors | model | VERIFIED-STATIC |
| Independent review of a diff | no default agent | `/security-review` command; coordinator prompt (fresh verifier worker) | model | VERIFIED-STATIC |
| Block completion while checks fail | **only if the user configures a Stop hook** | | | VERIFIED-RUNTIME E50v |
| Todo reminder after idle turns | yes (attachment after 10 turns) | | model reads it | VERIFIED-STATIC (static-02 section 25); runtime not run |
| Proactivity text and level choice | yes | | | VERIFIED-RUNTIME E50p |

Bounded negatives (scope stated): no code path was found that runs a test command, forces a retest, or refuses a
final message because a test failed, **within** the functions named in the static-02 sections 25 and 26, the agent
loop and stop-hook driver read in static-03, and the ExitPlanMode tool. The remaining modules (about 2,500 of 2,586)
were not searched for this.

## 2. Findings that change the DaVinci plan

1. **The "workflow" is mostly model behavior plus a few hard gates.** The hard gates are plan-mode edit refusal,
   Explore and Plan tool lists, the permission mode, and the Stop hook. Everything else (explore first, test, retest,
   review) is text the model may follow.
2. **Instruction text is model-dependent.** The 5-series gets a short harness body. Do not copy "Doing tasks" and
   "Executing actions" text into DaVinci expecting parity: they are not what current models receive.
3. **The permission mode is bundled with proactivity.** Raising initiative also loosens approval (`proactive` goes to
   bypass or auto). A reliability design should keep these two independent and make the loosening explicit.
4. **A Stop hook is a working verification gate** (E50v). It needs the check command and a pass/fail rule, and it has
   a loop cap. The DaVinci controller generalizes it with freshness, baseline comparison and an approach ledger.
5. **There is no default reviewer or verifier agent.** The only written workflow with a separate verification worker
   is coordinator mode, opt-in by environment variable, prompt text only, not run here.

## 3. Unknowns, ranked by how much they would change the design

| # | Unknown | Why it matters | How to settle it |
|---|---|---|---|
| 1 | Real-model rate of running tests unprompted, and of claiming done after a failure | Decides whether text-only workflow is good enough | Live benchmark (file 05), needs approval |
| 2 | Which models get the lean layout beyond those tested; the host table behind `V4` | Parity claims for other models | Run E50m with more model ids; read the host method |
| 3 | Interactive plan approval dialog behavior and its "keep context" options | Approval transition details | PTY session with scripted model |
| 4 | Coordinator mode behavior at runtime (verification worker spawn, fresh-verifier rule) | Only written verification workflow | Scripted run with `CLAUDE_CODE_COORDINATOR_MODE=1` |
| 5 | Plan-mode shell rule independent of the auto classifier | Whether plan mode blocks `Bash` writes by itself | Run with auto mode unavailable or a scripted classifier (E41 setup) |
| 6 | Predicates `xFn`, `n1`, `ZH`, `Ugs`, `UH`, `Fx`, `s2` | Which text blocks appear when | Read each; compare with E50 grids |
| 7 | Todo reminder delivery at runtime (10-turn counters, brief-tool exemption) | Task tracking claim in the target workflow | Scripted run of 12 turns without a task tool call |
| 8 | Why plan mode sent `claude-sonnet-5-5` when `--model haiku` was set | Model routing in plan mode | Read the plan-mode model selection |
| 9 | Compaction effect on the proactivity and plan-mode reminders | State preservation across compaction | E17-style run in plan mode |

## 4. Not covered here

Hooks other than Stop, MCP, sandboxing, the daemon and bridge layers, rendering. They are covered elsewhere in the
research set and do not change the coding-workflow conclusions.
