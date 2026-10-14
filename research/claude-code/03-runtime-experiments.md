# 03. Runtime experiment catalog

Runs were predominantly Claude Code 2.1.296 on Windows 11; seven explicitly named `*-v299`
comparison runs used 2.1.299. All runs used `claude -p` (headless), synthetic prompts and files
only, and lab projects under `~\cc-rea-lab\`. Sanitized evidence for experiment `X` is in
`runtime-logs/X/` (`run.json`, `http-summary.json`, `stream-summary.json`,
`hooks-summary.json` where hooks were installed). `runtime-logs/MANIFEST.json` lists hashes.

**Profile.** Unless marked *default profile*, runs used the slim profile:
`--model haiku --setting-sources project,local --strict-mcp-config --mcp-config empty-mcp.json`
(26 tools, model `claude-haiku-5-5`). Behaviour that depends on model quality (which tool
the model chooses) is not a finding; only what the harness did is.

**Instrumentation** for every run: forward proxy on `ANTHROPIC_BASE_URL`, stream-json
output with partial messages and hook events, debug file, scrubbed parent environment.

**Reading the confidence column.** *Verified* means the observation was read directly from
captured bytes or events. Interpretations are stated separately and can be weaker.

## Summary table

| ID | Mission item | Objective | Outcome | Confidence |
|---|---|---|---|---|
| E01-simple | 1 | Simple question, default profile | 1 model request, 206 tools, 3 system blocks, `end_turn` | Verified |
| E01b-simple-slim | 1 | Same, slim profile | 26 tools, model flag honoured | Verified |
| E02-read | 2 | Single file read | 2 requests: `tool_use` then `end_turn` | Verified |
| E03-edit-accept | 3 | Edit with `acceptEdits` | Read, Edit, file changed on disk | Verified |
| E06-edit-denied | 3, 6 | Edit needing approval, no approver | denied, file unchanged, run still `success` | Verified |
| E04-bash-ok | 4 | Shell success | `Bash(echo:*)` rule allows, stdout returned | Verified |
| E05-bash-fail | 5 | Shell with out-of-tree path | blocked by path check before running | Verified |
| E05b-bash-realfail | 5 | Shell non-zero exit | `is_error: true`, `Exit code 2` plus stderr | Verified |
| E06b-bash-denied | 6 | Bash with no rule | denied, `permission_denials` populated | Verified |
| E07a-hooks-order | 7 | Hook ordering and stdin | full lifecycle order captured | Verified |
| E07b-hook-deny | 7 | PreToolUse JSON deny | tool blocked with hook reason | Verified |
| E07c-hook-exit2 | 7 | PreToolUse exit 2 | tool blocked, stderr fed to model | Verified |
| E07d-hook-exit1 | 7 | PreToolUse exit 1 | non-blocking, tool ran | Verified |
| E07e-hook-allow | 7 | PreToolUse allow in default mode | edit ran without approval | Verified |
| E07f-hook-allow-vs-deny | 7 | Hook allow against a deny rule | deny rule wins, tool absent | Verified |
| E07g-hook-rewrite | 7 | PreToolUse `updatedInput` | rewritten command executed | Verified |
| E07h-stop-block | 7 | Stop hook `decision: block` | loop re-entered once | Verified |
| E08-multi-parallel | 8, 10 | Three Reads in one message | executed during the stream, one merged result message | Verified |
| E08b-perm-rules | 6 | allow / deny / ask rule mix | deny > ask > allow; ended on a real 429 | Verified |
| E09-sequential | 9 | Grep then Read | 3 requests, each depends on the previous result | Verified |
| E10-parallel-agents | 10, 11 | Two Agent calls in one message | child requests overlap in time | Verified |
| E11-subagent | 11 | One subagent, creation to hand-back | separate prompt and tool list, result as tool_result | Verified |
| E12-subagent-error | 12 | Unknown agent type | `is_error` tool_result listing valid types | Verified |
| E13b-interrupt-stream | 13 | Interrupt during model streaming | HTTP stream closed within 5 ms, `aborted_streaming` | Verified |
| E13c-interrupt-tool | 13 | Interrupt during a running tool | synthetic rejection result, turn ends, next turn works | Verified |
| E13a-interrupt-tool | 13 | First attempt | invalid: `sleep 40` blocked by the Bash tool itself | Failed (kept as evidence of the block) |
| E14-background | 14 | Background shell then TaskStop | task `killed`, notification `stopped` | Verified |
| E15a..d | 15 | Create, resume, continue, fork | history restored; fork leaves the source untouched | Verified |
| E15e, E15f | 15 | Edit `CLAUDE.md` between create and resume | old text replayed, new text appended as a fresh reminder | Verified |
| E17-pre, E17a, E17b | 17 | Manual `/compact` | boundary event, summary message, 36,430 to 1,464 tokens | Verified |
| E17c-autocompact | 16, 17 | Large context, 100k window | 3 automatic compactions, then thrash breaker | Verified |
| E18a..e | 18 | Injected 529, 500, 400, reset, 429 | retries with backoff; 400 degrades a field | Verified |
| E27, E27b, E27c | 16, 17 | Compaction-fault controls | auth/path controls failed before the target: no request, 401, then real 429 | Verified controls; no compaction result |
| E28b | 17 | Manual `/compact` with body-targeted 529 | first summary attempt injected locally; second compact retry reached real 429; command exited 0 without a boundary | Partially verified |
| E30, E31 | 16, 17 | Automatic summary fault, body marker `<analysis>` | E30 had three injected 529 attempts; E31 had 11 injected 529 attempts, then `Reactive compact: summarization returned API error`; no failure-breaker event observed | Failure path verified; breaker unverified |
| C1..C4, C8 | prompt | Instruction discovery, system prompt flags | marker placement recorded | Verified |
| C5, C6, C6b, C6c | config | `env` precedence across settings sources | flag > local > project > process env | Verified |
| C7-maxturns | failure | `--max-turns 1` with a tool call | `error_max_turns`, exit 1 | Verified |
| C9, C10, C11 | output | json, text, bad flag | shapes and exit codes recorded | Verified |

Invalid runs kept out of the evidence set: the first batch-3 pass (ten runs) executed in the
default profile because of a harness bug (an empty argument pushed flags behind `--`). Their
raw output was moved to `lab/raw-invalid-batch3/` and the runs were repeated.

## Detailed observations

### E01 / E01b: request shape (items 1, 12)

- Sequence: `HEAD /api/hello` (user agent `Bun/1.4.3`), then `POST /v1/messages?beta=true`.
- Request headers, in wire order: Accept, Authorization, Content-Type, User-Agent
  (`claude-cli/2.1.296 (external, sdk-cli)`), X-Claude-Code-Session-Id, six `X-Stainless-*`
  (SDK package 0.128.0, retry count, timeout 600), `anthropic-beta`,
  `anthropic-dangerous-direct-browser-access: true`, `anthropic-version: 2023-06-01`,
  `x-app: cli`.
- Beta list (E18c raw, slim profile): `oauth-2025-04-20`, `interleaved-thinking-2025-05-14`,
  `thinking-token-count-2026-05-13`, `context-management-2025-06-27`,
  `prompt-caching-scope-2026-01-05`, `mid-conversation-system-2026-04-07`,
  `claude-code-20250219`, `per-turn-control-2026-07-01`,
  `mid-conversation-tool-changes-2026-07-01`, `inline-tools-2026-09-15`,
  `advisor-tool-2026-03-01`, `effort-2025-11-24`, `thinking-display-updates-2026-08-18`,
  `extended-cache-ttl-2025-04-11`.
- Body keys, in order: `model, messages, system, tools, metadata, max_tokens, thinking,
  context_management, output_config, stream`. Values seen: `max_tokens 128000`,
  `thinking {type: adaptive, display: updates}`,
  `context_management {edits: [{type: clear_thinking_20251015, keep: all}]}`,
  `output_config {effort: medium}`, `stream true`.
  `metadata.user_id` is a JSON string with keys `account_uuid, device_id, session_id`.
- `system` is three text blocks: a billing header line (74 chars, no cache control), an
  identity sentence (62 chars, `cache_control {type: ephemeral, ttl: 1h}`), and the main
  prompt (8,770 chars slim, same cache control).
- `messages[0]` (user) holds four text blocks: instruction files reminder, context reminder,
  attribution reminder, then the user's text. `messages[1]` has `role: "system"` and carries
  the environment block (8,948 chars).
- Response: SSE `message_start, content_block_start, ping, content_block_delta,
  content_block_stop, message_delta, message_stop`. Unified rate-limit headers
  (`anthropic-ratelimit-unified-*`) accompany every response.
- Competing explanation considered: the `role: "system"` message could be an artifact of
  the proxy. Rejected: the proxy forwards the body byte for byte and the beta
  `mid-conversation-system-2026-04-07` is declared by the client.
- Unresolved: whether the direct (unproxied) path sends the identical body.

`--model haiku` was ignored in the default profile and honoured in the slim one. Static
evidence shows `availableModels` gates model selection; the user settings here list models
without a haiku id. **STRONGLY INFERRED** cause, not isolated by a dedicated run.

### E02, E09: the tool loop (items 2, 9)

Each tool round is one more `POST /v1/messages` whose `messages` array is the previous one
plus the assistant message and a user message of `tool_result` blocks. E09 shows three
requests (Grep, Read, final). `result.num_turns` counted 3 for E06 (three requests) and 4
for E08 (two requests, three parallel tool results), so it does not equal the request count.

### E08: parallel tool calls and streaming execution (items 8, 10)

Stream order, verbatim from the event log:

```
content_block_start(tool_use Read #1) ... assistant(#1) content_block_stop
content_block_start(tool_use Read #2) input_json_delta
user(tool_result #1)                         <- result arrives while #2 is still streaming
... assistant(#2) content_block_stop
content_block_start(tool_use Read #3) input_json_delta
user(tool_result #2)
... assistant(#3) content_block_stop message_delta(stop_reason tool_use) message_stop
user(tool_result #3)
```

- A tool starts as soon as its own `tool_use` block is complete, before `message_stop`.
- The SDK stream emits one `assistant` event per content block, before that block's
  `content_block_stop`.
- The next request contains one assistant message with all three `tool_use` blocks and one
  user message with all three `tool_result` blocks in call order.
- A fifth message, `role: "system"`, appeared after the results: the contents of
  `sub/CLAUDE.md`, loaded because a file under `sub/` was read (lazy nested instructions).
- The newest block of the newest message carries the moving `cache_control` marker.

### E06, E06b, E05, E08b: permissions (item 6)

- No approver is available in plain `-p`. An `ask` outcome becomes: a
  `system/permission_denied` event (`tool_name, tool_use_id, message`), a `tool_result`
  with `is_error: true`, and an entry in `result.permission_denials`
  (`tool_name, tool_use_id, tool_input`). The loop continues; the run ends `success`,
  exit 0.
- Denial text differs by cause. No rule: "Claude requested permissions to use Bash, but you
  haven't granted it yet." Deny rule: "Permission to use Bash with command ... has been
  denied." Path outside the working directories (E05): "ls in '...' was blocked. For
  security, Claude Code may only list files in the allowed working directories".
- E08b rules `allow Bash(echo:*)`, `deny Bash(echo denied*)`, `ask Bash(echo ask*)`:
  `echo allowed-one` ran, `echo denied-two` denied by rule, `echo ask-three` treated as ask
  (then denied for lack of an approver). So deny beats ask beats allow.
- `deny Read(./secret/**)` surfaced as a `<tool_use_error>` validation failure ("File is in
  a directory that is denied by your permission settings"), not as a permission denial
  event.
- E05b: a compound command (`ls x; echo "exit=$?"`) was refused with "contains multiple
  operations. The following part requires approval". Sub-commands are checked one by one.
- C5 first attempt: `echo $LAB_PREC` was refused with "A variable in this command can't be
  checked before it runs." Unexpanded variables defeat prefix-rule matching.

### E07a to E07h: hooks (item 7)

Lifecycle order with millisecond offsets (E07a):

```
0     SessionStart(source=startup)
51    InstructionsLoaded x2 (load_reason=session_start, memory_type=Project)
396   UserPromptSubmit
2240  PreToolUse x3 for Read  (all three start within 1 ms; one sleeps 1 s)
3328  PostToolUse Read        (after the slowest PreToolUse finished)
4830  PreToolUse x2 for Edit
5915  PostToolUse Edit
7094  Stop
7190  SessionEnd(reason=other)
```

- Matching hooks for one event run in parallel. The tool waits for all of them.
- Stdin fields. Common: `session_id, transcript_path, cwd, hook_event_name`. Most add
  `prompt_id`. PreToolUse adds `permission_mode, effort, tool_name, tool_input,
  tool_use_id`. PostToolUse adds `tool_response, duration_ms`. Stop adds
  `stop_hook_active, last_assistant_message, background_tasks, session_crons`.
  UserPromptSubmit adds `prompt`. PreCompact adds `trigger, custom_instructions`.
  PostCompact adds `trigger, compact_summary`. InstructionsLoaded adds
  `file_path, load_reason, memory_type`. SessionStart adds `source`. SessionEnd adds `reason`.
- Environment given to hook processes includes `CLAUDE_PROJECT_DIR`, `CLAUDE_ENV_FILE`,
  `CLAUDE_CODE_SESSION_ID`, `CLAUDE_PID`, `CLAUDECODE`, `CLAUDE_CODE_ENTRYPOINT`.
- Decisions: JSON `permissionDecision: deny` blocks with the reason as the tool result
  (E07b) and is counted in `permission_denials`. Exit 2 blocks and passes stderr to the
  model (E07c). Exit 1 is reported as an error outcome but the tool runs (E07d).
- `permissionDecision: allow` let an Edit run in default mode with no approver (E07e).
- With `permissions.deny: ["Edit"]`, the same allow hook had no effect: the tool was
  removed from the session and the call returned "No such tool available: Edit" (E07f).
  The hook never saw the call.
- `updatedInput` replaced the Bash command. The executed output was `REWRITTEN-BY-HOOK`;
  the model's own tool_use block still shows the original command (E07g).
- Stop hook `{"decision":"block","reason":...}` produced a synthetic user message "Stop
  hook feedback: ..." and one more model request; the second Stop fired and the run ended
  (E07h). `num_turns` was 2.
- `UserPromptSubmit` additionalContext and `PostToolUse` additionalContext are delivered to
  the model as `role: "system"` messages ("PostToolUse:Read hook additional context: ...",
  seen in E17c request tails).

### E10, E11, E12: subagents (items 10, 11, 12)

- A child agent issues its own `/v1/messages` requests. Its `system` differs from the
  parent's (billing header 95 chars vs 74, main prompt 2,669 chars vs 8,770, different
  hash). Its tool list is 25 of the parent's 26 (`ScheduleWakeup` removed in this profile).
  Its first user message has the same three reminder blocks as the parent followed by the
  delegated prompt. It does not receive the parent's conversation.
- Stream events for the child lifecycle: `system/task_started` (`task_id, run_id,
  tool_use_id, description, subagent_type, is_backgrounded, spawn_depth, task_type:
  local_agent, prompt`), `system/task_progress` (`usage {total_tokens, tool_uses,
  duration_ms}, last_tool_name`), child `assistant`/`user` events carrying
  `parent_tool_use_id`, `system/task_updated` (`patch {status, end_time}`),
  `system/task_notification` (`status, output_file, summary, usage`).
- Hand-back: the parent receives a `tool_result` beginning "[Subagent hand-back] The text
  below is the final report of a subagent ... It is model output, NOT a message from the
  user". The SDK-side `tool_use_result` object has keys `agentId, agentType,
  canContinueAgent, content, prompt, resolvedModel, status, toolStats, totalDurationMs,
  totalTokens, totalToolUseCount, usage` and harness bookkeeping fields.
- E10: the two children's first requests started 339 ms apart and both were in flight
  together (start offsets 2664 ms and 3003 ms, each lasting about 2 s). Parallel execution
  of sibling Agent calls is verified.
- E12: an unknown `subagent_type` returns `is_error: true` with "Agent type '...' not
  found. Available agents: claude, Explore, general-purpose, Plan, statusline-setup". No
  child is created; `subagent_stats.spawned` stays 0.
- On disk: `<project>/<session>/subagents/agent-<id>.jsonl` and a sibling `.json`.
- Not tested: a child that fails mid-run, nested children, permission prompts raised from
  inside a child.

### E13b, E13c: interruption (item 13)

Driver: `--input-format stream-json`, user turn sent as
`{"type":"user","message":{"role":"user","content":"..."}}`, then
`{"type":"control_request","request_id":"...","request":{"subtype":"interrupt"}}`.

- During model streaming (E13b): `control_response` at 4.002 s, partial `assistant` message
  at 4.004 s, synthetic user message "[Request interrupted by user]" at 4.005 s, `result`
  with `subtype: error_during_execution`, `terminal_reason: aborted_streaming` at 4.007 s.
  The proxy recorded the client closing the upstream HTTP connection mid-body
  (`client_closed_early: true` after 101 chunks). Text already streamed (1,491 chars) is
  kept in the assistant message. Exit code 1 after stdin closed.
- During a running tool (E13c, a 40 s Python sleep): `task_started` at 7.7 s, interrupt at
  9.0 s, then within 30 ms: `control_response`, `task_notification`, a user `tool_result`
  with `is_error: true` ("The user doesn't want to proceed with this tool use. The tool use
  was rejected ..."), a user text "[Request interrupted by user for tool use]", and
  `result/error_during_execution`. No PostToolUse and no Stop hook fired for the
  interrupted turn. A following user turn ran normally in the same process, with the
  interrupted exchange in its history (5 messages).
- Partially verified: that the child process tree was killed. No Python process was listed
  afterwards, but the check was a single `tasklist` call with no pre-interrupt baseline.
- Not tested: Esc or Ctrl+C in the interactive TUI, SIGINT to the process.

### E14: background task and cancellation (item 14)

`Bash` with `run_in_background: true` returned at once: "Command running in background with
ID: <id>. Output is being written to: <temp>/claude/<project>/<session>/tasks/<id>.output".
Events: `task_started` (`task_type: local_bash`, `is_backgrounded: true`). `TaskStop`
returned `{message, task_id, task_type, command}`; events `task_updated` (`status: killed`)
and `task_notification` (`status: stopped`).

### E15: persistence and resume (item 15)

- `--resume <id>` rebuilt the full message list: the follow-up request carried 4 messages
  (original user + reminders, environment system message, assistant, new user).
- `--continue` picked the most recent session in the directory and appended to the same
  session (6 messages on the wire).
- `--resume <id> --fork-session` sent the same history (8 messages) but wrote to a new
  session; a later `--resume <id>` of the original did not contain the fork's turn.
- The reminder blocks and the environment system message are part of the stored history
  and are replayed, not regenerated. Tested directly (E15e, E15f,
  `runtime-logs/config/resume-replay.json`): `CLAUDE.md` was edited between create and
  resume. The resumed request kept the original text in message 0 and added the edited
  text as a new reminder block at the start of the new user message. So a resumed model
  sees both versions, old first.

### E17a, E17b, E17c: compaction (items 16, 17)

Manual (`/compact Keep the token.` on a resumed session):

- One model request. Same `system`, same `tools`, full history, and a 6,403-char
  instruction appended as an extra text block to the last user message (it begins
  "CRITICAL: Respond with TEXT ONLY. Do NOT call any tools." and asks for `<analysis>` and
  `<summary>`). Cache control on this request has no `ttl` (5-minute default) while normal
  turns use `1h`. The request read 36,307 tokens from cache, so it reuses the session's
  prefix.
- Events: `system/status compacting`, `system/status` with `compact_result`, `system/init`,
  `system/compact_boundary` (`compact_metadata {trigger: manual, pre_tokens: 36430,
  post_tokens: 1464, cumulative_dropped_tokens, duration_ms, preserved_segment {head_uuid,
  anchor_uuid, tail_uuid}}`), a synthetic user message starting "This session is being
  continued from a previous conversation that ran out of context", and a
  `<local-command-stdout>Compacted</local-command-stdout>` user message. `num_turns: 0`.
- The next turn's request had 5 messages and answered both the token and the file line
  from the summary without a tool call.

Automatic (`--autocompact 100k`, ten 62 KB files, about 22,600 tokens each per the
`cache_creation` deltas):

- Before each large Read the CLI called `POST /v1/messages/count_tokens` with the file
  content alone (1 message, no tools).
- After two files the context reached about 78,000 tokens and compaction ran:
  `pre_tokens 78258`, `post_tokens 15135`. After one file (about 59,000) it did not. That
  brackets the trigger between 59k and 78k, consistent with the static formula
  `window - min(max_output, 20000) - 13000 = 67,000` for a 100k window.
- Hook order per compaction: `PreCompact(trigger=auto)`, `SubagentStop` (empty
  `agent_type`, about 10 s later), `SessionStart(source=compact)`, `PostCompact`.
- After compaction the CLI re-read recent files (`count_tokens` calls for the two newest
  files) and re-attached them truncated ("[Truncated: PARTIAL view ...]" system messages),
  so the rebuilt context was about 15,000 tokens rather than about 1,500.
- The cycle repeated three times (`cumulative_dropped_tokens` 63,123, 125,394, 187,479).
  Then the run stopped by itself: `result.terminal_reason: rapid_refill_breaker`, result
  text "Autocompact is thrashing: the context refilled to the limit within 3 turns of the
  ...", exit code 1. Five of ten files had been read. This is a safe compaction-failure
  path observed without forcing an error.
- Not observed: a failing summarization request, the prompt-too-long retry path, partial
  compaction.

### E27 to E31: compaction-failure injection (items 16, 17)

The proxy was extended with optional literal `body_contains` and `body_contains_all` fault
matchers. This is a transport fixture change, not a claim about the CLI. In these fixtures it
lets the lab target the summary request, whose body contains the no-tools `<analysis>` /
`<summary>` instruction, rather than relying only on the shared `/v1/messages` path. It is a
literal heuristic, not a cryptographic request classifier. The matcher was syntax-checked and
then exercised by E28b, E30 and E31. Raw request bodies remain outside the repository;
sanitized evidence is in the corresponding `runtime-logs/` directories.

- E27 was a control failure: 2.1.296 reached no API request after the child environment
  lost its usable credential. E27b passed the stale environment token and received a real
  upstream 401. E27c selected the local OAuth store and received a real upstream account
  429 before compaction. These runs are retained to separate authentication/rate-limit
  failures from a compaction result.
- E28b used the literal `/compact Keep the token.` on the existing resumed session. The
  proxy matched `POST /v1/messages?beta=true` and returned the synthetic 529 locally
  (`injected:true`). The CLI retried the same `source=compact` request; that second compact
  attempt was not faulted and reached the real 429. No compact boundary was emitted and the
  local command exited 0 with an error result. This verifies the manual error injection and
  its headless exit shape, not the auto failure breaker.
- E30 resumed the already-large E17c session with the existing stdin fixture. Its captured
  request body was 231,252 bytes and did not contain the 188k flood text; it produced three
  successive `source=compact` requests that matched the body marker and returned injected
  529s. These were attempts 1, 2 and 3 of one summary operation; the fourth attempt reached
  the real 429. It would be incorrect to count those three transport attempts as three
  compaction failures.
- E31 repeated the flood with the 188,194-byte stdin fixture and a fault budget of 40. Eleven
  `source=compact` HTTP attempts were injected with 529, corresponding to attempt 1 through
  attempt 11 in the CLI's `1/11` retry counter. That is one initial attempt plus ten retries.
  Debug output then showed `Reactive compact: summarization returned API error` and a failed
  `session.compact` hook; the next `source=sdk` request reached the real 429 and the turn
  ended with exit 1. The fault file retained 29 unused injections. No
  `tengu_auto_compact_circuit_breaker`, `failure_breaker_open`, or compact boundary appeared.
  The observed failure is therefore **Verified** as summary API-error exhaustion and hook
  failure, while the static claim of three *distinct* failed summaries opening a session
  breaker remains **Untested**.
- Not observed here: partial compaction, direct-path
  cache-sharing fallback, or three separate failed auto-compaction operations in one live
  session. The account rate limit (`retry-after` reported by the server) prevented a
  final ordinary turn after E31; that server response is not attributed to the CLI breaker.
- E32 was a login control: without `CLAUDE_CONFIG_DIR`, the child reported `Not logged in` and
  made no model request. E32b supplied the existing local OAuth store and reached the real
  upstream account limit: one `HEAD /api/hello` followed by a `POST /v1/messages` returning
  429 before a model response. These canaries confirm that the live account was still blocked;
  they do not test the CLI failure breaker.

### E44 and E45: subagent limits, a failing child, and max-output replay (scripted model)

All four runs use the scripted proxy (no upstream model call); builders are `tools/scenarios/build_e44.py` and
`run_e44.sh`. `bypassPermissions`, foreground agents, `subagent_stats` read from the final `result` frame.

| Run | Setup | Observed |
|---|---|---|
| E44a depth | root asks level 1, which asks level 2, which asks level 3, which asks level 4 | `spawned:3`, `max_depth:3`, `spawned_by_subagents:2`, `completed:3`, all `refused` counters **0**. Request tool lists: root 26, levels 1 and 2 have 25 (with `Agent`), **level 3 has 24 and no `Agent`**. Level 3's attempt to call `Agent` got `<tool_use_error>Error: No such tool available: Agent. Agent is not among the tools available here. Continue with the tools you have.</tool_use_error>` (`is_error:true`) |
| E44b concurrency | one assistant message with 22 parallel foreground `Agent` calls | `spawned:20`, `completed:20`, `refused.concurrency_limit:2`; the two refused calls returned `Concurrent subagent limit reached. You can run 20 subagents at once. Do not retry. If the user wants more concurrent subagents, ask them to increase CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS.` (`is_error:true`); 22 model requests, `num_turns:23` |
| E44c failure | the child's first request gets HTTP 400 | `subagent_stats` `failed:1`, `completed:0`; the parent received `Agent terminated early due to an API error: API Error: 400 lab otherwise (error type unknown, HTTP 400, model sent to the API: claude-haiku-5-5)` (`is_error:true`) and carried on: result `completed`, exit 0 |
| E45 max-output text | three replies cut by `stop_reason:"max_tokens"` that carry real text, then a normal end | Four requests, `max_tokens` 128,000 on each. **The partial text is replayed**: request 2 holds the first reply as an `assistant` text message followed by a separate 183-character `user` text (the nudge); request 3 holds two partials and two nudges; request 4 holds three. Final `completed`, `num_turns:4` |

- **Verified depth cap by tool removal.** The depth-3 child cannot call `Agent` because the tool is absent, so the static
  `Subagent nesting limit reached (depth N of M)` error and `refused.depth_limit` are not reached on this path.
  `static-05` open question 4 is answered: the tool is already missing at depth 3.
- **Verified concurrency cap.** 20 by default, text and env name as the static report says.
- **E45 versus E26.** E26's cut replies carried only thinking, so no assistant message was replayed and the nudge was
  merged into the first user message. With real text the partial is kept and each nudge is its own user message.
  Not run here: a fourth consecutive cut (the E26 final error), or `CLAUDE_CODE_MAX_OUTPUT_TOKENS`.

### E46: hook-event coverage and PermissionRequest allow (scripted model)

Both runs use the local scripted proxy and Claude Code 2.1.296. No model request reached the upstream service.
The hook coverage project registered all 33 static hook event names with the lab logger. The PermissionRequest
project used default permission mode and a command hook that returned
`hookSpecificOutput.decision.behavior = "allow"` for a Bash write.

- **E46-hooks:** 17 hook invocations across 13 event types in one four-turn session: `SessionStart`,
  `InstructionsLoaded`, `UserPromptExpansion`, `UserPromptSubmit`, `PreToolUse`, `PostToolUseFailure`,
  `PostToolUse`, `PostToolBatch`, `SubagentStart`, `SubagentStop`, `MessageDisplay`, `Stop`, and `SessionEnd`.
  The scripted turn ran a missing-file `Read`, a successful Bash call in the same assistant message, and a foreground
  general-purpose subagent. The final result was `completed`, `num_turns:4`, with one spawned and completed child.
- **E46-permreq:** the default-mode Bash call fired `PermissionRequest:Bash`; the hook stdin contained
  `hook_event_name`, `tool_name`, `tool_input`, `permission_mode`, `permission_suggestions`, `effort`, and the
  normal session fields. The allow response was accepted, `permreq-made.txt` contains `x`, and the run ended
  `completed`, `num_turns:2`, with no permission denial.
- Across all sanitized hook logs now present, 17 of the 33 static event names have been observed. The remaining
  16 are not established by these headless scenarios. This is event coverage, not evidence that unobserved events
  are unreachable.
- **Not established:** event-specific blocking semantics for the newly observed events, interactive prompt behavior,
  and the 16 configured events not reached by these scenarios. Evidence: `runtime-logs/E46-hooks/hooks-summary.json`,
  `runtime-logs/E46-permreq/hooks-summary.json`, and their `stream-summary.json` files.

### E47: headless denial after a non-deciding PermissionRequest hook (scripted model)

E47 reused the all-event hook project with default permission mode, but changed the Bash tool input to a synthetic
Python file write that is not on the safe allowlist. The `PermissionRequest` hook logged the request and returned no
decision. The proxy still answered all model requests locally.

- The hook received `tool_name: Bash`, `permission_mode: default`, `permission_suggestions`, `effort`, and the
  normal session fields. No `PermissionRequest` decision was emitted.
- The Bash call was not run: `runtime-logs/E47-denied-danger/stream-summary.json` records one `permission_denials`
  entry for the Bash tool and `is_error: true` on the tool result. The synthetic `denied-made.txt` file is absent.
- The run continued through the scripted Agent child and ended `completed`, exit 0, `num_turns:4`. No
  `PermissionDenied` hook invocation appeared in this route.
- **Verified for headless mode:** after a `PermissionRequest` hook returns successfully without an allow or deny
  decision, the pending ask becomes a denial rather than an interactive prompt. This is a direct runtime check of
  the fallback described in `static-04`; it does not establish interactive behavior or all event-specific hooks.

### E41 to E43: `auto` permission mode with a scripted classifier

`--permission-mode auto` sends each unapproved tool call to a classifier, which is a model call. Here the lab proxy
answers the classifier too (a canned `<severity>` score), so the whole mode can be exercised with **no upstream
model request**. The parent is scripted to call `Bash` (a Python file write, not on the safe list). Build scripts are
in `tools/scenarios/`; the bisect is summarized by `tools/auto_thresholds.py` into
`runtime-logs/auto-mode-thresholds/summary.json`. Classifier prompt text is not kept (about 137,000 characters).

**Flow per call** (debug log): `[auto-mode] new action being classified: tool=Bash`, then a `classifier_request`
at `stage=xml_s1`, then, only if stage 1 escalates, `stage=xml_s2`. Before that the log shows
`[server-classifier] … server_no_result … classifies locally for the rest of this session` (no server verdict was
present because the scripted replies carry none). The gate line reads `verifyAutoModeGateAccess: enabledState=enabled`.

**Classifier request shape** (E41, structure only): no `tools`; `thinking:{type:"disabled"}`; model `claude-sonnet-5`
first (`claude-sonnet-5[1m]` in the log), then the session model as a fallback; three `system` blocks of 74, 137,394 (cache
`ephemeral`, ttl 1h) and 242 characters; two `user` messages (the second has five text blocks). Stage 1:
`max_tokens:64`, `stop_sequences:["</severity>"]`. Stage 2: `max_tokens:8192`, no stop sequence.

| Probe | Result |
|---|---|
| stage-1 score 0, 18, 20, 21, 25 | one classifier request; tool ran (**allowed**) |
| stage-1 score 25.5, 26, 28, 29, 30, 40, 50 | a second classifier request (stage 2) |
| stage 1 = 30, stage-2 score 10, 25, 26, 30, 30.5, 32, 35 | tool ran |
| stage 1 = 30, stage-2 score 35.5, 38, 40, 60, 90 | tool did not run (**denied**) |
| classifier answered 400 on both models (E41a) | `Sonnet 5 probe demotion errorKind=http_400`, fallback to the session model with `179987ms remaining`, then `Auto mode classifier unavailable, denying with retry guidance (fail closed)` and `Bash tool permission denied`; the run still ended `completed` |

- **Thresholds on this account:** block when severity is **strictly greater** than `t1 = 25` (stage 1, escalate) and
  `t2 = 35` (stage 2, deny). The static defaults `lBe=15`, `cBe=20` (`chunk-phacttch.js@1093223`) were not in
  effect; where 25 and 35 come from (remote config or a site default) was not determined.
- **Denial text.** A classifier denial returns an error `tool_result` and a `system/permission_denied` frame with
  `decision_reason_type:"classifier"`, `decision_reason:"Blocked by classifier"`, and a long guidance message beginning
  `Permission for this action was denied by the Claude Code auto mode classifier. Reason: Blocked by classifier.`
- **Denial limits in `claude -p` (E42, E42b, E42c, six, 22 and 24 denials).** Denials 1 and 2 use the guidance text. From
  the 3rd consecutive denial the classifier is still consulted at both stages, but the decision becomes an ask:
  `decision_reason` `N consecutive actions were blocked. Please review the transcript before continuing.` followed by
  `Latest blocked action: Blocked by classifier`, and in headless mode the model sees `This command requires approval`
  (log: `Classifier denial limit exceeded, falling back to prompting`). `N` counts up to 19. The 20th denial reads
  `20 actions were blocked this session`; after it the counters restart (the 21st and 22nd get the guidance text,
  the 23rd says `3 consecutive`). This matches `Kxr@3354151`, which resets both counters at the total limit.
  With an allow after every second denial (E42b, 22 denials, 11 allows) no limit message appeared at all.
- **Not reproduced:** `Agent aborted: too many classifier denials in headless mode`. The source throws it only when
  `shouldAvoidPermissionPrompts` is true. It did not occur in `-p` (E42, E42c) or for a background agent launched from a
  stream-json session whose Bash calls were denied 5 times (E43; the agent logged `falling back to prompting`, then
  failed on trailing requests that my script did not cover, which is a script limit, not CLI behaviour). Which
  context sets that flag was not found.
- **Not established:** real classifier verdicts and prompts, interactive prompting, the server-side classifier path,
  and why the scripted results carry no `server` verdict.

### E40: the Stop-hook block cap (scripted model)

A project `Stop` hook that **always** returns `{"decision":"block","reason":"..."}` and logs each call, plus a
scripted model that answers every request with a short text. Nothing went upstream. Results
(`runtime-logs/E40-stop-hook-cap/`):

- The hook ran **9 times**: once with `stop_hook_active:false`, then 8 times with `true`. The CLI made **9** model
  requests, with `messages` counts 2, 5, 8, 11, 14, 17, 20, 23, 26 (three added per re-entry: the assistant reply,
  the user message `Stop hook feedback:\n<reason>`, and one more message).
- On the 9th block the CLI stopped re-entering and emitted `system/informational` and `system/notification` frames:
  `A hook blocked the turn from ending 9 consecutive times - overriding and ending turn. For Stop/SubagentStop hooks,
  check stop_hook_active in the input and return success while it's true. Set CLAUDE_CODE_STOP_HOOK_BLOCK_CAP to raise
  this limit.`
- Final frame: `subtype:"success"`, `is_error:false`, `terminal_reason:"completed"`, `num_turns:10`, exit 0, 1.8 s.
- **Verified:** the default cap of 8 (8 blocks are honored, the 9th is overridden) and the `completed` end. **Not run:**
  `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` set to another value or to 0, and `SubagentStop`.

### E39: a parent interrupt with a background or foreground agent (scripted model)

These runs use the proxy's new `sequence` mode (`tools/scripted_response.mjs`): the lab proxy answers every
`/v1/messages` with a canned, valid Anthropic stream, so the real CLI runs its real tools while **no model
request goes upstream**. The script: turn 1 makes the parent call `Agent` (`run_in_background` true or false);
the child runs `Bash` (a Python sleep of 12 s, then writes `child-done.txt`); the parent then starts its own
30 s `Bash`. At 6 s the stream-json host sends an `interrupt` control request; at 10 s it sends a new user
message. Permission mode `bypassPermissions`. Build script and fault sequence stay in the scratchpad and
`lab/raw`; the structured results are in each run's `stream-summary.json` (`events`, `results`).

| Run | Agent | Interrupt | Task events | `child-done.txt` | Turn results |
|---|---|---|---|---|---|
| E39c | background | none | agent `completed`, both Bash tasks `completed`; the child's second request at 13.5 s | written | `completed` (3 turns) |
| E39a | background | at 6 s | `task_updated` patch `killed`; three `task_notification` `stopped` (agent plus two Bash); `background_tasks_changed` 1 then 0 | **absent** | first turn `aborted_tools` (error), then the 10 s message `completed` |
| E39b | foreground | at 6 s | `tool_dispatch_end tool=Agent outcome=aborted`; `task_updated` `killed`; two `task_notification` `stopped` | **absent** | first turn `aborted_tools` (error), then `completed` |

Debug lines for the cancelled agents: `[Stall] agent_completion … agentType=general-purpose exitPath=cancelled durationMs=5475`
(background) and `…durationMs=5474` (foreground), both within 1 s of the interrupt; the background run then logged
`[enqueueAgentNotification] skipped … status=killed … reason=already-notified`.

- **Contradicts the static claim for this interface.** `static-05` (abort linkage table, lines 412 to 418) says an
  interrupt of the parent turn does not stop a background agent, because it has an independent controller. Here the
  SDK `interrupt` control request killed the background agent as well as the foreground one, and the control run (same
  script, no interrupt) completes, so the kill is caused by the interrupt.
- **Scope:** this is the stream-json `interrupt` control request, not the TUI Esc key the static text names. The two
  paths may differ. The result is therefore **Contradicted (scoped)**: not shown false for Esc in the TUI.
- **Not established:** whether the host's interrupt handler stops all tasks by design, or whether the background
  agent shares the parent's controller in this build. The scripted model is not a real model: tool-use timing and
  content are canned.

### E38: the 180 s first-party byte default

No stream env at all, same local `sse_stall` fault. Timeline from `runtime-logs/E38-byte-watchdog-default/debug-summary.json`:
`[Stall]` warnings at 15, 30, 60, 120 s with `idleDeadlineMs=180000`; `Streaming idle warning: no chunks received for 150s`
(the event-level warning, half of 300 s); then at **180.000 s** `[byte-watchdog] firing: idle=180000ms` and
`Streaming idle timeout (byte-level): stream idle: no bytes for 180000ms`, then the non-streaming fallback
(second POST at 181 s, `stream:false`, `max_tokens:64000`). The event-tier 300 s timeout never came due because the byte
tier fired first, as `static-03` F6.4 predicts for an unset env. **Verified:** first-party default 180 s.

### E34: prompt-too-long during compaction (reactive path)

E34 resumed the same private session as E31 with `--autocompact 100k`, and the proxy answered
**every** `/v1/messages` request locally with HTTP 400 `invalid_request_error`, message
`prompt is too long: 250000 tokens > 200000 maximum`. The gap is therefore a lab constant of
50,000 tokens, not a measurement. Only `HEAD /api/hello` reached the real service; 8 of 9 requests
were injected and no model request went upstream. Raw bodies stay private; structured numbers are
in `runtime-logs/E34-ptl-summary-retry/debug-summary.json` (`reactive_compact`).

- The debug log shows `autocompact: routing through reactive (thresholdSource=settings)`, so this
  is the **reactive** compaction path. The static report did not read that path (`static-02` scope
  note); the non-reactive `Mon` drop-and-retry of F9.8 was not exercised.
- Round 1 made three `source=compact` requests (11, 11 and 5 messages; 623,737, 231,252 and 160,697
  bytes). After each 400 the CLI logged `attempt N hit prompt-too-long (gap=50000, gap_guided step S),
  next preserves K/7` with K = 3, 5, 6 and step 2, 2, 1. It then logged `no assistant messages in
  summarize set, bailing`, and the `session.compact` hook failed.
- The turn then sent its ordinary `source=sdk` request (809,955 bytes), which also got the 400
  (`StopFailure:invalid_request` hooks ran), and a second compaction round started: three attempts
  (preserves 4/7, 5/7, 6/7; 11, 8 and 5 messages), then `round ladder exhausted, last resort (keeping
  3 trailing messages, head truncations so far: 1)`, one last-resort request (2 messages, 96,937
  bytes), and `last-resort request still too long after 1 head truncations, giving up`.
- Final frame: `subtype:"success"`, `is_error:true`, `terminal_reason:"prompt_too_long"`,
  `api_error_status:400`, exit 1, 3.9 s, one turn.
- **Not established:** what `gap_guided step` and the `K/7` preserve ratio mean, which messages
  are kept, and behaviour when the server error carries no parsable token gap. Whether a real
  server overflow behaves the same is untested.

### E35 to E37: repeated compaction failure in one live process

These runs drive `run_stream.py` (stream-json input, one process, many turns) with the E31 session
resumed and the proxy answering **every** `/v1/messages` locally with a 400. Only `HEAD /api/hello`
reached the real service. Per-event numbers are in each run's `debug-summary.json` (`autocompact`) and
`stream-summary.json` (`results`).

| Run | Setup | Observed |
|---|---|---|
| E35 | `--autocompact 100k`, 5 short turns, 400 "prompt is too long" | Every turn: `level=compact`, `routing through reactive (thresholdSource=settings)`, two failed compaction rounds (E34's ladder), `prompt_too_long` end. 5 turns, 10 PreCompact hooks, 5 failed autocompact operations |
| E36 | no `--autocompact`, 6 short turns, generic 400 | `level=ok effectiveWindow=980000` on all six turns. No compaction. The default window of this model is about 980,000 tokens |
| E36p-* | one turn each with `--model` set to `claude-opus-4-1`, `claude-sonnet-4-5`, `claude-3-5-haiku-20241022` | `claude-opus-4-1` also reported `effectiveWindow=980000`. The other two printed no `autocompact:` line: for a source-`auto` model the should-compact predicate returns false before it logs (see below). No 200k-window model with a logged window was found |
| E37 | no `--autocompact`; 28 turns carrying the 186,116-character synthetic flood, then 8 short turns; generic 400 | `level` was `ok` x10, `warn` x1, `blocked` x25. Each of the 25 blocked turns: `routing through reactive (thresholdSource=model-default)`, one PreCompact hook, one `source=compact` request (400), `Reactive compact: summarization returned API error`, then the turn ended with `terminal_reason:"blocking_limit"` and **no** `source=sdk` request. The 11 turns before that ended `api_error` 400. 38 POSTs in total: 13 `source=sdk`, 25 `source=compact` |

- **No breaker appeared.** Across 25 consecutive failed compaction operations in one process (E37), plus
  5 in E35, the log never shows `circuit breaker tripped`, `tengu_auto_compact_circuit_breaker` or
  `failure_breaker_open`, and the CLI kept attempting compaction on every blocked turn. The static claim
  (`static-02` F8.4: three consecutive failures open a breaker) is therefore **contradicted for the route
  observed here**.
- **Why earlier runs never reached it.** The source (`chunk-phacttch.js@2596377`) routes through the reactive
  path when a reactive handler exists and the threshold source is not `auto`, or a classifier overflow or model
  override is present. Here the source was `settings` (E35) or `model-default` (E37), so all compaction in E27 to
  E37 used the reactive route. The static counter `consecutiveFailures` is read before that routing, so either it
  is never incremented on the reactive route or it is absent in this stream-json mode. This was not separated.
- **Source reading that ties E36p to E37** (`chunk-phacttch.js`): the should-compact predicate `scr@2593137` returns
  false at `if(r$()&&!Xae(n,r)&&!S)` before it writes the `autocompact: tokens=` line, and `Xae@862512` is
  `source !== "auto"`. In a local session (`r$()` true, `CLAUDE_CODE_REMOTE` unset) compaction therefore
  runs only for a non-`auto` threshold source, and the routing test at `@2596309` (`nt!=="auto"`) sends every
  such case down the reactive route. The window source is `auto` only for a recognized model below 1M that is
  not billed past 200k (`lv@860717`); `haiku-5-5` and `opus-4-1` here resolve to `model-default`.
- **New:** at level `blocked` with a failing compaction, the turn ends locally with `blocking_limit` and sends no
  model request. This matches the `blocking_limit` terminal reason listed in `static-03`.
- **Not established:** behaviour on the non-reactive route (no reactive handler), in interactive mode, or with
  a successful compaction between failures (the static reset rule). The 980,000-token window means a real
  overflow is not reachable cheaply; the flood was only possible because the proxy answered locally.

### E18a to E18e: transport faults (item 18)

Faults were answered locally by the proxy; nothing was sent upstream for those requests.

| Fault | CLI behaviour | `api_retry` event |
|---|---|---|
| 529 twice | 2 retries then success | attempt 1 delay 578 ms, attempt 2 delay 1127 ms, `max_retries 10`, `error: overloaded` |
| 500 once | 1 retry | delay 574 ms, `error: server_error` |
| connection reset | 1 retry | delay 552 ms, `error_status: null`, `error: unknown` |
| 429 with `retry-after: 2` | 1 retry after exactly 2000 ms | `error: rate_limit` |
| 400 `invalid_request_error` | immediate second request (5 ms later), no `api_retry` event | none |

- Delays fit `500 ms * 2^(attempt-1)` plus up to 25 percent jitter, the static constants.
- `x-stainless-retry-count` stayed `0` on every attempt, so retries are driven by the
  application's own wrapper, not the SDK's.
- The 400 follow-up differed from the failed request in exactly two places: the body's
  `thinking` lost `display: "updates"`, and the beta header dropped
  `thinking-display-updates-2026-08-18`. **STRONGLY INFERRED:** a one-shot "strip the newest
  optional field and retry" fallback for 400s. Which 400 messages trigger it is unknown.
- A real failure was also captured: E08b ended on HTTP 429 (account session limit). Result:
  `is_error: true`, `terminal_reason: api_error`, `stop_reason: stop_sequence`, the limit
  message as a synthetic assistant text, exit code 1. Transcript rows for it carry
  `isApiErrorMessage, apiError, apiErrorStatus`.

### C1 to C8: instruction discovery and system prompt flags

Layout: `nest/CLAUDE.md` (outside the git repo), `nest/proj-cfg/` (git root) with
`CLAUDE.md` (contains `@docs/inc.md`), `CLAUDE.local.md`, `.claude/CLAUDE.md`,
`.claude/rules/always.md`, `.claude/rules/scoped.md` (frontmatter `paths: sub/**/*.txt`),
`AGENTS.md`, `sub/CLAUDE.md`, `sub/inner/CLAUDE.md`. Evidence:
`runtime-logs/config/marker-placement.json`.

- Everything loaded at start goes into the first text block of the first user message,
  never into `system`. Order by offset: parent directory file (above the git root), project
  `CLAUDE.md`, its `@include` target, `.claude/CLAUDE.md`, unconditional rule,
  `CLAUDE.local.md`. With cwd `sub/`, `sub/CLAUDE.md` follows last.
- Directory walk goes above the git root (the `nest/` file loaded).
- `AGENTS.md` was not loaded.
- With cwd `sub/`, the `@docs/inc.md` include of the root file was absent, while from the
  root it was present. **HYPOTHESIS:** includes that resolve outside the cwd need approval
  (static pass 02 documents an external-include approval dialog). Not isolated.
- Subdirectory files and the path-scoped rule load lazily: after `Read sub/inner/x.txt` the
  next request gained a `role: "system"` message containing `sub/CLAUDE.md`,
  `sub/inner/CLAUDE.md` and the scoped rule, in that order.
- `--append-system-prompt X`: `X` is appended at the end of `system[2]`; the identity block
  `system[1]` also changed (62 to 94 chars).
- `--system-prompt X`: `system[2]` becomes `X` alone (36 chars). Billing and identity
  blocks stay. Instruction files and the environment message are still sent.
- `--exclude-dynamic-system-prompt-sections`: `system[2]` shrank from 8,777 to 6,375 chars.

### C5 to C6c: settings precedence (same key `env.LAB_PREC` in each source)

| Sources active | Value seen by a Bash child |
|---|---|
| project only (`--setting-sources project`) | `project` |
| project + local | `local` |
| project + local + `--settings file` | `flag` |
| project + local, and `LAB_PREC=shellenv` in the CLI's own environment | `local` |

Order verified: flag settings > local > project, and a settings `env` value overrides the
inherited process environment. A key present only in project settings stays visible when
other sources are layered (object merge, not replace). Not tested: user and managed
sources (user settings were excluded on purpose; managed settings would need admin paths).

### C7, C9, C10, C11: termination and output

- `--max-turns 1` with a tool call: `result.subtype: error_max_turns`,
  `terminal_reason: max_turns`, exit 1.
- `--output-format json`: one JSON object with the same keys as the stream's `result`
  event. Text format: the final text and a newline.
- Unknown flag: stderr `error: unknown option '--definitely-not-a-flag'`, exit 1, no API
  call.

## Permission modes (P-plan, P-dontAsk, P-acceptEdits, P-bypassPermissions)

One headless prompt per mode in a disposable project: "Write `out.txt` with the Write tool, then run
`python -c "print(123)"` with Bash". Slim profile, haiku, `--permission-mode <mode>`. Run on 2.1.296
(`CLAUDE_BIN` pinned to the original binary, `exe_sha256` recorded in `run.json`) and again on
2.1.299 (`*-v299`). Both builds behaved the same in every row.

| Mode | Write | Bash | Evidence |
|---|---|---|---|
| `plan` | not run on `out.txt`; the model wrote its plan to `~/.claude/plans/<slug>.md` instead (that Write succeeded) and ended the turn saying no step was done | not run | `result.permission_denials: []`, no `permission_denied` frame. Plan mode withheld the action through the model, not through a denial record |
| `acceptEdits` | allowed, file created, no approval | denied: `system/permission_denied`, `decision_reason_type:"other"`, message `This command requires approval`, `tool_result.is_error:true` | `result.permission_denials` has 1 entry (Bash) |
| `dontAsk` | denied with the `Yhe` text: `Permission to use Write has been denied because Claude Code is running in don't ask mode. IMPORTANT: ...` | same text for Bash; `permission_denied` frame has `decision_reason_type:"mode"` | 2 denials in `result.permission_denials`. Confirms the static `Yhe(name)` message in `static-04` |
| `bypassPermissions` | allowed | allowed, `tool_result` `123` | no `permission_denied`, no control request |

Side effects: plan mode created two plan files under `~/.claude/plans/` (one per build). The lab
project `out.txt` appeared only for `acceptEdits` and `bypassPermissions`. Not tested here: `auto`
mode decisions (they need the classifier, which is a model call), interactive plan approval, bypass with rules that should still win.

`claude auto-mode defaults` (2.1.296, local subcommand, exit 0) prints JSON with four string lists:
`allow` 17, `soft_deny` 72, `hard_deny` 1, `environment` 21. This matches the `auto_mode` settings
schema in `chunk-phacttch.js` (`allow`, `soft_deny`, `hard_deny`, `environment`). Only counts, sizes and a
hash are kept in `runtime-logs/auto-mode-defaults/summary.json`; the rule text is the classifier's own
prompt content and is withheld. That the command made no network call was not measured. The
subcommand `critique` calls a model and was not run.

## Fallback, watchdog and large-output experiments (E20 to E23)

All on 2.1.296 (`CLAUDE_BIN` pinned), slim profile, haiku. Injected faults were answered by the
local proxy; nothing was sent upstream for them. Proxy gained an `sse_stall` mode for E23.

| Id | Setup | Observed |
|---|---|---|
| E20-529x3-fallback | 3 injected 529, `--fallback-model sonnet` | Two `system/api_retry` frames (delays 585 and 1,198 ms), then on the third 529 a `system/model_fallback` frame (`trigger:"overloaded"`, `original_model:"claude-haiku-5-5"`, `fallback_model:"claude-sonnet-5-5"`, text `Switched to Sonnet 5.5 due to high demand for Haiku 5.5`), then a fourth request with model `claude-sonnet-5-5` and a one-byte-longer body that succeeded. Result `ok`. Matches the static `J8 = 3` rule |
| E21-529x4-nofallback | 4 injected 529, no fallback model | Four `api_retry` frames (delays 576, 1,041, 2,456, 4,232 ms), then success on the same model. No "repeated overload" error and no model switch, so that static branch did not fire for haiku on this account |
| E23-sse-stall-byte10s | upstream replies 200 with `message_start`, then silence; `CLAUDE_BYTE_STREAM_IDLE_TIMEOUT_MS=10000` | debug log: `[byte-watchdog] firing: idle=10000ms`, `Streaming idle timeout (byte-level)`, `Error streaming, falling back to non-streaming mode`. The next request had `stream:false` and `max_tokens:64000` (first was `stream:true`, `max_tokens:128000`) and succeeded. No `api_retry` frame and no SDK frame for the fallback. Run took 12.3 s |
| E22-bigout-N | `python -c "print('a'*N)"` under `bypassPermissions` | N = 5,000 to 29,998: tool_result inline (N chars; the trailing newline is trimmed). N = 29,999 and above (49,000, 51,000, 450,000 too): tool_result is a `<persisted-output>` block of about 2.2 KB: `Output too large (SIZE). Full output saved to: <config dir>/projects/<project>/<session>/tool-results/<id>.txt`, blank line, `Preview (first 2KB):`, preview, `...`, `</persisted-output>`. So the Bash threshold is 30,000 raw characters including the newline (the static report's 50,000 is the cap for tools that do not set a lower `maxResultSizeChars`) |

The `E23` result settles the static prediction for the byte tier only. With the stream-idle env unset the
byte default is 180 s on first party; that default was not waited out.

### E33: event-tier watchdog and its 300 s floor

2.1.296, slim profile, `CLAUDE_STREAM_IDLE_TIMEOUT_MS=15000` and `CLAUDE_BYTE_STREAM_IDLE_TIMEOUT_MS=1800000`
(the byte tier's maximum, so it cannot fire first). The proxy answered every `/v1/messages` with `sse_stall`:
a valid `message_start` frame, then silence. Nothing went upstream except `HEAD /api/hello`. The harness
killed the run at 420 s. Numbers are in `runtime-logs/E33-event-watchdog-floor/debug-summary.json` (`watchdog`).

| Time after the request | Observed |
|---|---|
| 15, 30, 60, 120 s | `[Stall] stream_idle_partial lastChunkAgeMs=… bytesTotal=247 idleDeadlineMs=1800000` |
| 150 s | `Streaming idle warning: no chunks received for 150s` |
| 300 s (07:29:26.1 to 07:34:26.4) | `Streaming idle timeout: no chunks received for 300s, aborting stream`, then `falling back to non-streaming mode` |
| about 301 s | second POST with `stream:false`, `max_tokens:64000` (first was `stream:true`, `128000`); it was stalled too |

- **Verified:** the event-tier timeout is `max(env, 300000)`. An env value of 15 s did not lower it. The
  warning came at half of the timeout, 150 s, as `static-03` F6.4 predicts. The timeout switches the
  request to non-streaming mode, the same fallback shape as E23's byte tier.
- The `idleDeadlineMs=1800000` field equals the byte timeout set here, so it belongs to the byte tier.
- **Unexplained:** the `[Stall] stream_idle_partial` warnings at 15, 30, 60 and 120 s are not in the static
  report. They stopped before the 150 s warning and there was none at 240 s. E38 (no stream env at all) shows
  the same 15, 30, 60, 120 s schedule, so the cadence is fixed, not derived from the env value. Their purpose
  is not known.
- **Not observed:** the `tengu_streaming_idle_timeout` event with `tier:"event"` does not appear in the debug
  log, so that tier label stays a static claim. The 180 s first-party byte default is still unwaited.

## Crash recovery and MCP calls (E24, E25)

| Id | Setup | Observed |
|---|---|---|
| E24a-crash-mid-tool | Bash `sleep 45` under `bypassPermissions`; the CLI process was killed hard (`kill`) at 12 s | exit code 1, killed by the harness. The transcript ends with the assistant `thinking` and `tool_use` rows; no `tool_result` was written |
| E24b-resume-after-crash | `--resume <session id>` with the prompt `Reply with exactly: resumed-ok` | The first request carried 6 messages. After the original user turn and the assistant `tool_use` came a synthetic user `tool_result`, `is_error:true`, text `[Tool call interrupted: the session ended before this call's result was recorded, so its outcome is unknown. Check whether it took effect before relying on it or running it again.]`, then a synthetic assistant text `No response requested.`, then the new user prompt. The transcript afterwards holds those two synthetic rows as ordinary `user` and `assistant` rows. The turn auto-ran only because a new prompt was given; no continuation without a prompt was tested |
| E25-mcp-call-manual | stdio MCP server `lab` (`tools/lab_mcp_echo.py`: `echo` with `readOnlyHint:true`, `mutate` without), headless default mode | `system/init` lists `mcp_servers: [{name:"lab", status:"connected", source:"dynamic"}]`. The wire tools are `mcp__lab__echo` and `mcp__lab__mutate`, appended after the built-ins, with only `name`, `description`, `input_schema`. The model called both in one turn. **Both were denied**, including the read-only-hinted one: `system/permission_denied` with `decision_reason_type` absent and `message: Claude requested permissions to use mcp__lab__echo, but you haven't granted it yet.`; the `tool_result` had the same text and `is_error:true` |
| E25-mcp-call-bypassPermissions | same, bypass | both ran; `tool_result.content` is the array `[{type:"text", text:"echo:hello-mcp"}]` and `[{type:"text", text:"mutate:x"}]`, no `is_error` |

The E25 deny text is the third headless wording seen: Bash uses `This command requires approval`
(E19b, P-acceptEdits), a path-safety deny uses `Claude requested permissions to write to <path>,
but you haven't granted it yet.` (E06), and a tool-level ask with no rule uses `Claude requested
permissions to use <tool>, but you haven't granted it yet.` (E25). All three are headless
auto-denials with no host handler.

## Max output token recovery (E26)

`CLAUDE_CODE_MAX_OUTPUT_TOKENS=200`, prompt asking for 400 numbers written as words. Four requests,
all `max_tokens: 200`, all `stop_reason: max_tokens` (one original plus three recoveries, as the static
pass predicted). Request 2 appended a text block to the same user message (`messages` stayed at 2):
`Output token limit hit. Resume directly — no apology, no recap of what you were doing. Pick up mid-thought if that is where the cut happened. Break remaining work into smaller pieces.`
Requests 3 and 4 appended the same text again, so the user message grew by one block each time. The
partial assistant output was not replayed in the request bodies; the stream shows `thinking_tokens`
frames and no text, so the 200 tokens were probably spent on thinking and a thinking-only message is
dropped (**STRONGLY INFERRED**, not isolated). Final frame: `result` with `subtype:"success"`,
`is_error:true`, `terminal_reason:"api_error"`, `num_turns:4`, exit code 1, text ending
`...exceeded the 200 output token maximum. To configure this behavior, set the CLAUDE_CODE_MAX_OUTPUT_TOKENS environment variable.`
Not tested: a response that has real text when it is cut (does the partial text enter the next request).

## Experiments not run, with reasons

| Item | Reason | What would settle it |
|---|---|---|
| Interactive TUI behaviour (rendering, Esc, permission dialog) | needs a PTY; REA process capture is unsupported on native Windows | run under WSL with REA `capture_process_scenario`, or ConPTY harness |
| Approval granted or refused through a host (`can_use_tool` control request) | **Verified (E19c allow, E19d deny)**; E19 and E19b were setup failures | E19 (earlier account state) ended `Not logged in`. E19b (stored login, `--permission-prompts host` alone) ran the model but emitted no control request: the Bash call was auto-denied with `system/permission_denied` (`decision_reason: This command requires approval`) and the result text was `This command needs approval, so it didn't run`. With `--permission-prompt-tool stdio` (E19c, E19d) the CLI wrote one `control_request` (`request.subtype:"can_use_tool"`, keys `tool_name`, `display_name`, `input`, `description`, `permission_suggestions`, `decision_reason`, `decision_reason_type`, `tool_use_id`) and waited. Allow reply: the tool ran, `tool_result` `host-approved`, `result.permission_denials: []`. Deny reply with `message`: `tool_result` carried the host's message verbatim with `is_error:true`, and `result.permission_denials` listed `tool_name`, `tool_use_id`, `tool_input`. `permission_suggestions` offered an `addRules` entry with destination `localSettings`. The earlier inference that env scrubbing caused the login failure was wrong for E19b: the stored login now works. |
| Subagent failing mid-run, nested subagents | time | prompt a child to call a denied tool; set depth |
| Failure breaker on the non-reactive route | **Reactive route observed (E35 to E37): 25 failures, no breaker.** The non-reactive route was never reached | find what leaves the reactive handler undefined or the threshold source equal to `auto`; original E31 note: keep the body-targeted fault, then drive three separate auto-compaction turns after the account rate limit resets; require `failure_breaker_open` or `tengu_auto_compact_circuit_breaker` |
| Partial compaction | no trigger for the partial path was found | locate the caller of the partial compaction function, then drive it |
| Prompt-too-long summary retry, non-reactive path | **Reactive path observed (E34)**; the non-reactive `Mon` path was not reached | find what makes autocompact skip the reactive route |
| Process kill and recovery on resume | **Verified (E24a/E24b)** | kill the CLI during a tool, then `--resume` |
| Direct (unproxied) baseline | proxy was the only body-level tap | compare `--debug api` logs with and without the proxy |
