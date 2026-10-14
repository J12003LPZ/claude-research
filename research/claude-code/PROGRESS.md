# Investigation progress ledger

Resume point for this investigation after a context compaction or restart. Updated after
each stage. Evidence ids refer to `runtime-logs/<id>/` (sanitized) and `lab/raw/<id>/`
(raw, private, not committed).

## Stage status

| Stage | Status | Where |
|---|---|---|
| 1 Locate executable | done | `01-environment-and-provenance.md` |
| 2 REA audit | done | `01` section 3, `runtime-logs/rea/` |
| 3 to 12 Static architecture | done, 5 sweeps (spot-checked, not line-reviewed) | `static-0N-*.md` |
| 13 Runtime experiments | done, 109 manifest runs: 88 E, 13 C, 8 P | `03-runtime-experiments.md`, `runtime-logs/` |
| 14 Contracts | done | `04-internal-contracts.md` |
| 15, 18 Cross-validation and matrices | done | `06-verification-matrix.md` |
| 16 Repository and manifest | done, redaction check clean | `README.md`, `runtime-logs/MANIFEST.json` |
| 17 Implementation spec | done | `05-implementation-spec.md` |

Next steps if resumed: the remaining untested rows of `06` (three distinct failed auto-summary
operations and the failure breaker on the non-reactive route, the non-reactive prompt-too-long path and partial compaction, `auto` permission
mode, background-agent survival, daemon lifecycle and TUI behavior, sandbox enforcement (blocked: `sandbox status` reports unsupported on this host), the 180 s byte-watchdog default, and a
direct-path request dump). E35 to E37 ran 30 failed compactions in one process on the reactive
route with no breaker, so the static failure-breaker claim is contradicted there; the non-reactive
route was never reached.

## Tooling (all under `tools/`)

- `pe_inventory.py`, `bun_probe.py`, `bun_extract.py`: PE + Bun module-graph extraction.
- `chunk_index.py`, `cq.py`: export/import index and bounded search over extracted chunks.
- `capture_proxy.mjs`: logging forward proxy (`ANTHROPIC_BASE_URL`), credential values never stored, fault injection via `fault.json`.
- `run_exp.py`: one instrumented `claude -p` run. `summarize_captures.py`, `hooks_summary.py`, `show_exp.py`: sanitized evidence + views.
- `lab_batch1.sh`, `lab_batch2.sh`: experiment batches. Lab projects live in `C:\Users\<user>\cc-rea-lab\`.

## Slim experiment profile (cost control)

Default config on this machine sends 206 tools and ~258k cached tokens per first request
(E01: one word answer, notional cost 2.06 USD on Opus). Experiments therefore run with
`--model haiku --setting-sources project,local --strict-mcp-config --mcp-config empty-mcp.json`
(26 tools, ~36k tokens, ~0.002 to 0.008 USD per run). `--model haiku` alone was ignored under
user settings (E01: `availableModels` in user settings does not list a haiku id; the request
used the settings model). Status: partially verified (E01 vs E01b, not a single-variable run); see `06-verification-matrix.md` row 17.

## Verified runtime findings so far

1. Artifact: `claude` resolves to one PE, Bun standalone, `.bun` section holds 2,586 modules; entry `cli`. (static)
2. Transport: `POST /v1/messages?beta=true`, streamed SSE, preceded by `HEAD /api/hello`. Headers and body keys in `E01-simple/http-summary.json`.
3. Request body keys: model, messages, system, tools, metadata, max_tokens, thinking, context_management, output_config, stream. `metadata.user_id` is a JSON string with keys account_uuid, device_id, session_id.
4. System is 3 text blocks: billing header line (uncached), identity line (cache 1h), main prompt (cache 1h).
5. First user message carries reminder blocks ahead of the prompt: instruction files, context (date etc.), attribution, then the user text.
6. `messages` contains `role: "system"` entries mid-conversation (environment block after the first user message; lazily loaded nested CLAUDE.md after a Read in that subdirectory, E08).
7. Cache breakpoints move: the last block of the newest message carries `cache_control` (E08 msg[2] last tool_use, msg[4]).
8. Streaming tool execution: tool results are produced while the assistant stream is still open (E08: `user` tool_result events interleave with later `content_block_start`).
9. SDK stream emits one `assistant` message per content block, before `content_block_stop`.
10. Parallel tool calls: three tool_use blocks in one assistant message, three tool_results merged into one user message (E08).
11. Headless default mode: an `ask` decision becomes a denial with `is_error: true` tool_result, a `system/permission_denied` event, and an entry in `result.permission_denials`; the loop continues and the run still ends `success` (E06, E06b).
12. Bash path safety: `ls /outside` denied even with `Bash(ls:*)` allowed (E05).
13. Hook order for a tool: all matching PreToolUse hooks start in parallel (same ms), tool waits for the slowest, then PostToolUse, then result (E07a). Session order: SessionStart, InstructionsLoaded, UserPromptSubmit, [PreToolUse, PostToolUse]*, Stop, SessionEnd.
14. PreToolUse `permissionDecision: deny` blocks the tool, counted in permission_denials (E07b). Exit 2 blocks with stderr fed to the model (E07c). Exit 1 is non-blocking (E07d).
15. PreToolUse `allow` skips the permission prompt in default mode (E07e) but a `deny` rule wins: the denied tool is removed from the session entirely ("No such tool available", E07f).
16. PreToolUse `updatedInput` rewrites the command that runs; the model still sees its original tool_use (E07g).
17. Stop hook `decision: block` re-enters the loop with a synthetic user message "Stop hook feedback: ..." and the second Stop has `stop_hook_active` (E07h).
18. Rule precedence observed: deny > ask > allow for Bash prefix rules; Read deny rule on a path blocks via tool validation (E08b).
19. Real API failure captured: 429 session limit ends the run with `is_error: true`, `terminal_reason: api_error`, exit code 1, and a synthetic assistant text (E08b tail).
20. Compaction fault targeting: a literal request-body marker distinguishes summary calls from normal `/v1/messages` turns in the lab proxy (E28b, E30, E31).
21. Automatic summary failure: eleven injected 529 HTTP attempts (one initial attempt plus ten retries) exhaust one `source=compact` operation, then `Reactive compact: summarization returned API error` and `session.compact` hook failure occur; no failure-breaker event was observed (E31).
22. Evidence tooling now digests arbitrary error/non-JSON/SSE error text, structurally summarizes request and run metadata, accepts mixed SSE line endings, tolerates incomplete frames, retains explicit late breaker signals without raw message text, preserves injected SSE capture metadata/body, validates malformed fault matcher fields, and closes capture streams on cancellation.
23. E32b used the local OAuth store and reached a real upstream 429 after `HEAD /api/hello`; the account was still rate-limited, so no further live breaker experiments were run.

## Incidents

- Five parallel Opus static-sweep agents exhausted the account's 5-hour session limit. Four had
  already written complete reports; the fifth was resumed after the reset.
