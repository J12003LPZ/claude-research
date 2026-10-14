# 06. Verification, coverage, cross-validation, open questions

Coverage here is counted over enumerated behaviours and tested scenarios. There is no
overall completeness percentage, on purpose.

Result vocabulary: **Verified** (static and runtime agree, or runtime alone is decisive),
**Partially verified** (one side only, or bracketed rather than pinned), **Inferred**,
**Untested**, **Blocked** (cannot be tested from this host or without the vendor), **Contradicted (scoped)**
(runtime behaviour differs from the static claim in a stated configuration; the claim is not shown false elsewhere).

## 1. Subsystem verification matrix

| Subsystem | Hypothesis | Static evidence | Runtime evidence | Result | Confidence | Remaining gap |
|---|---|---|---|---|---|---|
| Artifact | `claude` is one Bun standalone PE holding the app as JS | PE sections, trailer, module table parse | `Bun/1.4.3` user agent on `/api/hello` | Verified | High | bytecode/source equivalence untested |
| Startup | Entry module dispatches fast paths, then `main` | entry `cli` read in full | version and bad-flag runs make no API call | Verified | High | each side entry point not exercised |
| Config | flag > local > project; settings `env` beats process env | merge code, static 01 | C5, C6, C6b, C6c | Verified | High | user and managed layers not run |
| Config | `availableModels` constrains `--model` | static 01 | E01 vs E01b (not isolated) | Partially verified | Medium | single-variable run |
| Prompt | 3 system blocks, 2 cached for 1h | cache scope code, static 02 | E01 | Verified for the slim profile on first party | High | other profiles and providers |
| Prompt | Instruction files ride in the first user message | static 02 | C1, C2 marker offsets | Verified | High | |
| Prompt | Discovery order and lazy nested loading | static 02 | C1, C2, E08 | Verified | High | external-include approval rule |
| Prompt | `AGENTS.md` not loaded | static 02 (existence probe only) | C2 | Verified for one lab project layout | High | other settings and flags |
| Prompt | Mid-conversation `role: system` messages | beta id in `chunk-80kqkekd.js` | E01, E08, C2 | Verified | High | behaviour when the beta is off |
| Loop | Continue while tool_use present; one result message per assistant message | static 03 | E02, E08, E09 | Verified | High | |
| Loop | Tools start before `message_stop` | `streamingToolExecutor.addTool` | E08 event order | Verified | High | interaction with unsafe tools |
| Loop | Stop-hook block re-enters, capped at 8 | static 03 | E07h (one block); E40 (always-block hook, scripted model: 8 honored, 9th overridden, `completed`) | Verified | High | other cap values, `SubagentStop` |
| Loop | Max output-token recovery, 3 attempts | static 03 | E26 | Verified (E26: 3 recoveries, nudge text, final error; E45: with real text the partial is replayed as an assistant message, each nudge a separate user message) | High | `CLAUDE_CODE_MAX_OUTPUT_TOKENS` with text |
| Transport | App-level retry: 10 attempts, 500 ms base, 25% jitter, retry-after | static 03 constants | E18a, b, d, e | Verified | High | cap 32 s, give-up paths |
| Transport | 400 triggers a degraded retry | not located statically | E18c | Partially verified | Medium | which 400s qualify |
| Transport | Fallback model after 3 consecutive 529 | static 03 | E20, E21 | Verified | High | `--fallback-model` unset: 4 retries, no switch (E21) |
| Transport | Byte watchdog, non-streaming fallback | static 03 | E23 | Verified for the byte tier (E23 env 10 s; E38 default 180 s) and the event tier (E33: abort at exactly 300 s with env 15 s, warning at 150 s) | High | `[Stall]` warning purpose unexplained; non-first-party providers untested |
| Tools | Lifecycle: lookup, validate, PreToolUse, decide, call, PostToolUse | static 04 | E07a to E07g | Verified | High | PostToolUseFailure |
| Tools | Large results persisted to disk | static 04 | E22 (14 sizes) | Verified; Bash threshold is 30,000 raw characters, not 50,000 | High | other tools' caps, MCP tools |
| Permissions | deny > ask > allow | static 04 core check | E08b | Verified | High | cross-layer rule merge |
| Permissions | PreToolUse or PermissionRequest hook allow skips prompt; deny rule still wins | `resolveHookAndPermission` | E07e, E07f, E46-permreq | Verified | High | |
| Permissions | Headless ask becomes denial | static 04 | E06, E06b, E47-denied-danger | Verified without a host handler; E47 also covers a non-deciding PermissionRequest hook; host approval is a separate row (E19c, E19d) | High | interactive dialog |
| Permissions | Modes plan, bypass, dontAsk, acceptEdits | static 04 | P-plan, P-dontAsk, P-acceptEdits, P-bypassPermissions (2.1.296 and 2.1.299) | Verified for one Write plus one Bash per mode | Medium | `auto` has its own row below; its rule schema is read locally, see `runtime-logs/auto-mode-defaults/` |
| Permissions | `auto` mode: classifier stages, thresholds, fail closed, denial limits | static 04 | E41, E42, E42b, E42c, E43 (scripted classifier, no upstream call): thresholds 25 and 35, fail closed on error, limits at 3 consecutive and 20 total | Verified for `claude -p` with a scripted classifier; the static abort branch not reproduced | Medium | real classifier verdicts, interactive prompting, server-side classifier, which context throws `Agent aborted` |
| Hooks | Matching hooks run in parallel | static 04 | E07a timestamps | Verified | High | |
| Hooks | Exit 2 blocks, exit 1 does not | static 04 | E07c, E07d | Verified | High | per-event differences |
| Hooks | stdin schemas | static 04 | E07a, E17c, E46-hooks, E46-permreq | Verified for 17 event types across the current sanitized hook logs | High | 16 configured events not reached by these headless scenarios |
| Subagents | In-process nested loop with own prompt and tools | `runAgent`, static 05 | E11 | Verified | High | |
| Subagents | Siblings run concurrently | static 05 left this open | E10 | Verified | High | limit of 20 |
| Subagents | Depth 3, concurrency 20 | static 05 | E44a (depth 3 reached, level 3 has no `Agent` tool), E44b (20 spawned, 2 refused, exact text) | Verified (depth by tool removal, not by the static error text) | High | depth and spawn env overrides |
| Subagents | Background agent survives parent interrupt | static 05 (independent controller) | E39a, E39b, E39c (scripted model, SDK `interrupt` request): background and foreground agents both killed; control completes | Contradicted for the SDK interrupt (scoped) | Medium | TUI Esc untested; interrupt handler may stop all tasks by design |
| Tasks | Background shell with output file, TaskStop kills | static 05 | E14 | Verified | High | notification into a later turn |
| Compaction | Trigger = window - min(maxOut, 20000) - 13000 | static 02 | E17c brackets 59k..78k for 100k | Partially verified | Static High / runtime Medium | pin the exact runtime threshold |
| Compaction | Summary request reuses system, tools, history | static 02 | E17a | Verified | High | |
| Compaction | Hook order PreCompact, SubagentStop, SessionStart(compact), PostCompact | static 02 | E17c | Verified | High | |
| Compaction | Post-compact file re-attachment, 5 files | static 02 | E17c (2 files re-read) | Partially verified | Medium | 6+ files |
| Compaction | Thrash breaker after 3 quick refills | static 02 | E17c | Verified | High | |
| Compaction | Failure breaker after 3 distinct failed summaries | static 02 (`Won=3`, `failure_breaker_open`) | E35, E36, E37: 25 consecutive failed compactions in one process, every one on the reactive route; no breaker event, compaction retried each turn | Contradicted for the reactive route (scoped) | Medium | the source reads as if a local session never leaves the reactive route (`scr@2593137`, `@2596309`); not shown whether the counter is absent there or only in stream-json mode; remote mode not run |
| Sessions | JSONL chain by uuid and parentUuid; project dir from sanitized cwd | static 05 | lab transcripts, E15 | Verified | High | 200+ char path hashing |
| Sessions | resume, continue, fork semantics | static 05 | E15b, c, d | Verified | High | cross-directory resume |
| Sessions | Interrupted-turn repair on resume | static 05 | E24a, E24b | Verified | High | resume with no new prompt, `CLAUDE_CODE_RESUME_INTERRUPTED_TURN` |
| Interrupt | Abort closes HTTP stream, synthesizes messages | static 03 | E13b, E13c | Verified | High | TUI Esc, SIGINT |
| Rendering | Custom Ink-style renderer, 16 ms frames | static 05 only; not runtime-verified | none | Blocked | Low | PTY harness |
| Daemon / background sessions | Supervisor, workers, PTY host over named pipe | static 05 | passive surface plus pinned `daemon --help`/`status`, E82 trusted launch, E83 attach, and E84 respawn: service install disabled, on-demand idle contract, live `background` registry row in `blocked/idle`, attach output, successful respawn to `working/idle`, then stop/rm cleanup (`daemon-surface`, `daemon-lifecycle`, `E82-bg-stall`, `E83-bg-attach`, `E84-respawn`) | Partially verified | Medium | no active model turn or PTY data flow, spare pool, worker lifecycle respawn codes, or PTY auth |
| Server side | Model behaviour, rate limits, gates, server context edits | none possible | headers only | Blocked | n/a | vendor only |

## 2. Behavioural test matrix: installed CLI versus the proposed reconstruction

"Reconstruction" is the design in `05-implementation-spec.md`. No reimplementation was
built in this investigation, so the last column records whether the spec defines the
behaviour precisely enough to test, not a pass or fail.

| # | Behaviour | Installed CLI (evidence) | Spec section | Status |
|---|---|---|---|---|
| 1 | Version without config or network | observed | 1 | Verified (spec defined) |
| 2 | Unknown flag exits 1 | C11 | 1 | Verified |
| 3 | Settings layering order | C5 to C6c | 2 | Verified |
| 4 | System block layout and cache markers | E01 | 3 | Verified |
| 5 | Instruction files in first user message, ordered | C1, C2 | 3 | Verified |
| 6 | Lazy nested instructions as a later message | E08, C2 | 3 | Verified |
| 7 | Append and replace system prompt flags | C3, C4 | 3 | Verified |
| 8 | Single tool round trip | E02 | 5 | Verified |
| 9 | Parallel tool calls, merged results | E08 | 5 | Verified |
| 10 | Tool starts before message end | E08 | 5 | Verified |
| 11 | Sequential dependent tools | E09 | 5 | Verified |
| 12 | Shell success and non-zero exit shapes | E04, E05b | 6 | Verified |
| 13 | Out-of-tree path refused | E05 | 7 | Verified |
| 14 | Compound command and variable checks | E05b, C5 | 7 | Partially verified (parser not specified) |
| 15 | Headless ask becomes denial | E06 | 7 | Verified |
| 15a | `auto` mode allow, escalate, deny, fail closed, denial limits | E41 to E43 | 7 | Verified (scripted classifier, `-p`); abort branch not reproduced |
| 16 | Rule precedence | E08b | 7 | Verified |
| 17 | Hook lifecycle order and parallel start | E07a, E46-hooks | 8 | Verified |
| 18 | Hook deny, exit 2, exit 1 | E07b, c, d | 8 | Verified |
| 19 | Hook allow and deny-rule interaction | E07e, E07f, E46-permreq | 7 | Verified |
| 20 | Hook input rewrite | E07g | 8 | Verified |
| 21 | Stop hook block | E07h | 5 | Verified |
| 22 | Subagent creation to hand-back | E11 | 9 | Verified |
| 23 | Parallel subagents | E10 | 9 | Verified |
| 24 | Unknown agent type | E12 | 9 | Verified |
| 24a | Subagent depth cap and concurrency cap | E44a, E44b | 9 | Verified |
| 25 | Background shell and stop | E14 | 9 | Verified |
| 26 | Interrupt during streaming | E13b | 13 | Verified |
| 26a | Parent interrupt with a background and a foreground agent | E39a, E39b, E39c | 13 | Verified (SDK interrupt, scripted model): both agents cancelled, `aborted_tools`, control completes |
| 27 | Interrupt during a tool | E13c | 13 | Partially verified (process kill not proven) |
| 28 | Resume, continue, fork | E15 | 11 | Verified |
| 29 | Manual compaction | E17a | 10 | Verified |
| 30 | Automatic compaction and thrash stop | E17c | 10 | Verified |
| 30a | Summary API-error exhaustion and manual compact fault surface | E28b, E30, E31 | 10 | Partially verified: targeted failure path observed; breaker not reached (see 30c) |
| 30c | Repeated compaction failure in one process, then `blocking_limit` | E35, E36, E37 | 10 | Verified: 25 failed operations on the reactive route, no breaker, `blocking_limit` end with no model request |
| 30b | Prompt-too-long during compaction (reactive path) | E34 | 10 | Partially verified: two rounds, gap-guided attempts, last resort, `prompt_too_long` end; injected constant gap, non-reactive path untested |
| 31 | Retry on 429, 500, 529, reset | E18 | 4 | Verified |
| 32 | Degraded retry on 400 | E18c | 4 | Partially verified |
| 33 | Max turns | C7 | 5 | Verified |
| 33a | Output-token recovery with real text | E45 | 5 | Verified |
| 34 | Output formats | C9, C10 | 1 | Verified |
| 35 | Real API error ends the run | E08b | 4 | Verified |
| 36 | Interactive permission dialog | none | 7 | Blocked |
| 37 | Terminal rendering | none | 12 | Blocked |
| 38 | Host approval over the control protocol | E19c, E19d | 7 | Verified |
| 39 | Subagent failure mid-run | E44c | 9 | Verified (child API error becomes a parent-visible error result) |
| 40 | Crash recovery on resume | E24 | 11 | Verified (synthetic interrupted result) |
| 41 | Large tool result persistence | E22 | 6 | Verified (Bash) |
| 42 | Model fallback | E20, E21 | 4 | Verified |
| 43 | Sandbox | `claude sandbox status` reports `supported:false`, `installed:false`, `enabled:false` on this host | 7 | Blocked (not exercisable here; enforcement itself unobserved) |
| 44 | MCP tool call | E25 | 14 | Verified (stdio server, deny and allow) |

Counts: 51 behaviours enumerated. Verified 43, partially verified 5, untested 0, blocked 3.

## 3. Cross-validation per subsystem

Each block answers: what we know, how, what else could explain it, what would falsify it,
what is unknown.

**Artifact and startup.** Known: one signed PE, Bun runtime plus 2,586 embedded modules,
entry `cli`. How: PE parse, trailer and table decode, hash match with the version store,
runtime user agent. Alternative: the shipped JS source could differ from the bytecode that
executes. Falsifier: a behaviour that contradicts the source text; none in the 150 manifest runs.
Unknown: updater behaviour, each side entry point.

**Prompt assembly.** Known: block layout, reminder placement, discovery order, lazy
loading, flag effects. How: captured request bodies with synthetic markers at known
offsets. Alternative: the proxy path could differ from the direct path. Falsifier: a
direct-path debug dump with a different body. Unknown: server-side additions, exact
section list of the main prompt under every feature flag.

**Agent loop.** Known: loop condition, streaming tool start, result batching, stop-hook
re-entry, termination reasons. How: event order in the SDK stream cross-checked with HTTP
request sequence and static `streamingToolExecutor` code. Alternative: the early tool
result in E08 could be event reordering in the output layer. Rejected: the hook log
timestamps in E07a place PreToolUse before `message_delta`. Falsifier: a hook timestamp
later than the stream end. Unknown: behaviour with non-concurrency-safe tools in one
message.

**Transport.** Known: endpoint, headers, body keys, retry timing, abort. How: proxy
captures and injected faults. Alternative: delays could come from the SDK. Rejected:
`x-stainless-retry-count` stayed 0 and the delays match the application constants.
Falsifier: a retry with a non-zero SDK retry header. Unknown: the purpose of the `[Stall]` warnings, non-first-party providers, and other fallback variants.

**Permissions and hooks.** Known: precedence, hook ordering, decision effects. How: hook
logs with timestamps, file state on disk before and after, denial events. Alternative:
E07f could be the model declining to call Edit. Rejected: the call was made and returned
"No such tool available". Falsifier: an allow hook that makes a denied tool run. Unknown:
real `auto` classifier verdicts (the flow is verified with a scripted one), sandbox enforcement (not supported on this host), and interactive approval UI.

**Subagents and tasks.** Known: nested loop, separate prompt, parallel siblings, event
lifecycle, hand-back framing. How: overlapping request timestamps on the proxy, task
events, on-disk subagent transcripts. Alternative: overlap could be an artifact of proxy
timing. Rejected: 339 ms separation with 2 s durations on both. Falsifier: strictly serial
child requests under the same prompt. Unknown: background survival under TUI Esc (killed under the SDK interrupt, E39). Depth and concurrency limits and a failing child are verified (E44).

**Compaction.** Known: trigger region, request shape, hook order, rebuild, and the rapid-refill
breaker. How: three successful automatic cycles and one manual one, with boundary metadata
and hook logs. E30/E31 added a body-targeted summary fault: the CLI exhausted the summary
API retry loop and failed the `session.compact` hook, but did not emit the distinct-failure
breaker. Alternative: the rapid-refill breaker could be a token budget rather than a refill
counter. Rejected: the result text and `terminal_reason` name the refill condition, and
static pass 02 has the counter. Falsifier for the rapid-refill claim: a run that compacts more
than three times in quick succession without stopping. Unknown: the failure breaker on the
non-reactive route (contradicted on the reactive route, E37), the non-reactive prompt-too-long path, partial compaction, and
server-side context edits.

**Sessions.** Known: layout, row types, chain links, resume semantics. How: schema
extraction from lab sessions only, message counts on resumed requests. Alternative: resume
could rebuild reminders rather than replay them. Rejected by E15e/E15f: after editing
`CLAUDE.md`, the resumed request kept the old text in message 0 and carried the new text
in a fresh reminder on the new user message. Falsifier: a resumed request whose first
message shows the edited file. Unknown: remaining interrupted-turn repair variants and retention sweeps.

## 4. Ten most consequential open questions

Targeted follow-up was attempted where it was cheap. Status after that:

| # | Question | Why it matters | Attempt | Status |
|---|---|---|---|---|
| 1 | Does the proxied path equal the direct path? | Every request-shape claim rests on it | Checked debug log line `dispatching to firstParty`, OAuth unaffected, stable beta list | Open. Needs a direct-path body dump |
| 2 | Which 400 errors trigger the degraded retry, and what else gets stripped? | A reimplementation needs the rule | Diffed E18c request pair: `thinking.display` and one beta removed | Partly answered |
| 3 | Exact auto-compact threshold | Affects when context is lost | Bracketed 59k..78k; static formula gives 67k | Partly answered |
| 4 | Are reminders and environment text replayed or regenerated on resume? | Cache reuse and correctness after file edits | Ran the falsifier (E15e, E15f): edited `CLAUDE.md` between create and resume | Answered. The stored first message is replayed unchanged, and the current file content is added as a new reminder block on the new user message |
| 5 | Is the tool's process tree killed on interrupt? | Orphan processes | Single process listing after E13c, none found | Partly answered |
| 6 | How does host approval (`can_use_tool`) flow end to end? | Needed for any SDK host | Static 03 documents the fields | Answered at runtime (E19c allow, E19d deny); needs `--permission-prompt-tool stdio`, `--permission-prompts host` alone auto-denies |
| 7 | Do background agents survive a parent interrupt? | Cancellation model | Static 05 says yes; E39 scripted run (SDK `interrupt`) | Answered: no, for the SDK interrupt (E39a). TUI Esc open |
| 8 | What do plan, dontAsk, bypass and auto modes do in practice? | `auto` unobserved | Static 04 algorithm extracted | Answered for plan, dontAsk, acceptEdits, bypass (P-* runs); `auto` open |
| 9 | Interactive rendering and input | Whole UI unverified | Blocked by PTY tooling on native Windows | Blocked |
| 10 | Is the shipped bytecode equivalent to the shipped source? | All static claims read the source | No contradiction in 150 manifest runs | Open. Would need a JavaScriptCore bytecode disassembler |

Also answered during this pass: static pass 05 could not tell whether parallel `Agent`
calls overlap. E10 shows they do.

## 5. Architecture corrections made along the way

1. First assumption: a Node/npm package. Wrong. It is a native-installer Bun standalone
   executable with no npm footprint.
2. First assumption: instruction files are part of the system prompt. Wrong. They are in
   the first user message; the system array stays byte-stable for caching.
3. First assumption: the environment block is in the system prompt. Wrong. It is a
   mid-conversation `system` role message.
4. First assumption: tools run after the model finishes its message. Wrong for
   concurrency-safe tools: they start as their block completes.
5. First assumption: SDK-level retries. Wrong. The application retries; the SDK header
   stays at 0.
6. Static passes initially pointed at small named chunks (`query`, `runAgent`) as the
   implementations. They are re-export shims; the bodies are in shared chunks.
7. Experiment design errors corrected: `ls /absolute` tests path policy, not shell failure;
   `sleep N` is refused by the tool; Git Bash rewrote `/compact` into a Windows path; an
   empty argument pushed flags behind `--` and silently ran ten experiments in the wrong
   profile.
