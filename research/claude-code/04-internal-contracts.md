# 04. Internal contracts recovered from evidence

Interface names are conceptual placeholders. Field names are real: each was read from a
captured request, a stream event, a hook stdin payload, or a lab transcript row. Markers:

- `// O` observed at runtime (experiment in brackets)
- `// S` read statically only (static pass number in brackets)
- `// P` proposed by this research, not observed

Field-level sources: `runtime-logs/E01-simple/http-summary.json`,
`runtime-logs/sessions/transcript-schema.json`, `runtime-logs/E07a-hooks-order/hooks-summary.json`,
and the `stream-summary.json` of each experiment.

## 1. ModelRequest (wire)

```ts
interface ModelRequest {                       // POST /v1/messages?beta=true        O [E01]
  model: string;                               // "claude-haiku-5-5", "claude-opus-5-5"
  messages: WireMessage[];
  system: SystemBlock[];                       // exactly 3 blocks in every capture
  tools: WireTool[];                           // full schemas every request
  metadata: { user_id: string };               // JSON string: {account_uuid, device_id, session_id}
  max_tokens: number;                          // 128000 observed
  thinking: { type: "adaptive"; display?: "updates" };   // display dropped after a 400 [E18c]
  context_management: { edits: [{ type: "clear_thinking_20251015"; keep: "all" }] };
  output_config: { effort: "low" | "medium" | "high" | "xhigh" | "max" };  // "medium" observed
  stream: true;
}
interface SystemBlock { type: "text"; text: string; cache_control?: CacheControl }
interface CacheControl { type: "ephemeral"; ttl?: "1h" }   // ttl absent on the compaction request [E17a]
interface WireMessage { role: "user" | "assistant" | "system"; content: ContentBlock[] | string }
type ContentBlock =
  | { type: "text"; text: string; cache_control?: CacheControl }
  | { type: "thinking"; thinking: string; signature: string }
  | { type: "tool_use"; id: string; name: string; input: object; cache_control?: CacheControl }
  | { type: "tool_result"; tool_use_id: string; content: string | ContentBlock[]; is_error?: boolean;
      cache_control?: CacheControl };
interface WireTool { name: string; description: string; input_schema: JsonSchema }   // no extra keys seen
```

Invariants (observed): the first message is `user`; every `tool_use` id in an assistant
message has a matching `tool_result` in the next user message, in the same order; at most
one moving `cache_control` marker on the newest message besides the two system markers;
`role: "system"` messages never appear first.

Headers the client sets: `anthropic-version`, `anthropic-beta` (14 values, slim profile),
`x-app: cli`, `user-agent: claude-cli/<version> (external, <entrypoint>)`,
`x-claude-code-session-id`, `anthropic-dangerous-direct-browser-access: true`,
`x-stainless-*`. `authorization` is a bearer credential (value never recorded).

## 2. StreamEvent (wire) and accumulation

```ts
type SseEvent =                                                              // O [E01, E08]
  | { type: "message_start"; message: { id; model; role; usage; content: []; stop_reason: null;
        container; context_management; diagnostics; stop_details; stop_sequence } }
  | { type: "content_block_start"; index: number; content_block: { type: "text" | "thinking" | "tool_use"; name?; id? } }
  | { type: "content_block_delta"; index: number;
      delta: { type: "text_delta" | "thinking_delta" | "signature_delta" | "input_json_delta"; ... } }
  | { type: "content_block_stop"; index: number }
  | { type: "message_delta"; delta: { stop_reason; stop_sequence; stop_details; container }; usage: Usage }
  | { type: "message_stop" }
  | { type: "ping" }
  | { type: "error"; error: { type: string; message: string } };
interface Usage { input_tokens; output_tokens; cache_creation_input_tokens; cache_read_input_tokens;
  cache_creation?: { ephemeral_5m_input_tokens; ephemeral_1h_input_tokens };
  output_tokens_details?: { thinking_tokens }; iterations?: object[]; service_tier?; inference_geo? }
```

Accumulation rule (observed): keep one builder per `index`; concatenate `input_json_delta`
fragments and parse once at `content_block_stop`; hand a completed `tool_use` to the
executor immediately; finalize the assistant message at `message_stop`.

## 3. SDK output stream (`--output-format stream-json`)

```ts
type SdkEvent =
  | { type: "system"; subtype: "init"; session_id; cwd; model; tools: string[]; mcp_servers; permissionMode;
      apiKeySource; output_style; claude_code_version; slash_commands; skills; agents; plugins;
      memory_paths; capabilities; fast_mode_state; ... }                                  // O [E01]
  | { type: "system"; subtype: "status"; status: "requesting" | "compacting" | null; compact_result? }   // O [E17a]
  | { type: "system"; subtype: "hook_started" | "hook_progress" | "hook_response"; hook_event; hook_name;
      exit_code?; outcome? }                                                              // O [E07a]
  | { type: "system"; subtype: "permission_denied"; tool_name; tool_use_id; message }      // O [E06]
  | { type: "system"; subtype: "api_retry"; attempt; max_retries; retry_delay_ms; error_status; error }   // O [E18a]
  | { type: "system"; subtype: "compact_boundary"; compact_metadata: CompactMetadata; logical_parent_uuid }  // O [E17a]
  | { type: "system"; subtype: "task_started" | "task_progress" | "task_updated" | "task_notification"; task_id; run_id; ... }  // O [E11, E14]
  | { type: "system"; subtype: "thinking_tokens"; estimated_tokens; estimated_tokens_delta }   // O
  | { type: "system"; subtype: "informational" | "ui_invalidate"; ... }                   // O [E01]
  | { type: "stream_event"; event: SseEvent; parent_tool_use_id: string | null }          // with --include-partial-messages
  | { type: "assistant"; message: AssistantWire; parent_tool_use_id: string | null }      // one per content block
  | { type: "user"; message: { role: "user"; content }; parent_tool_use_id; tool_use_result?; isSynthetic?; isReplay? }
  | { type: "rate_limit_event"; rate_limit_info }
  | { type: "control_response"; response }                                                // O [E13b]
  | ResultEvent;

interface ResultEvent {                                                                    // O [all]
  type: "result";
  subtype: "success" | "error_max_turns" | "error_during_execution";
  is_error: boolean;                     // true with subtype "success" on an API error [E08b]
  terminal_reason: "completed" | "max_turns" | "aborted_streaming" | "api_error" | "rapid_refill_breaker" | null;
  result?: string; stop_reason: string | null; num_turns: number;
  duration_ms; duration_api_ms; ttft_ms; total_cost_usd; usage: Usage; modelUsage: Record<string, ModelUsage>;
  permission_denials: { tool_name; tool_use_id; tool_input }[];
  subagent_stats: SubagentStats; api_error_status: number | null; session_id; uuid;
}
interface CompactMetadata { trigger: "manual" | "auto"; pre_tokens; post_tokens; cumulative_dropped_tokens;
  duration_ms; preserved_segment: { head_uuid; anchor_uuid; tail_uuid }; preserved_messages?: { anchor_uuid; uuids; all_uuids } }
interface SubagentStats { spawned; requested: { background; foreground; unset }; started_in_background; max_depth;
  spawned_by_subagents; completed; failed; killed: { parent; user; system };
  refused: { depth_limit; concurrency_limit; budget }; by_type: Record<string, number> }
```

Input side (`--input-format stream-json`), observed:

```ts
type SdkInput =
  | { type: "user"; message: { role: "user"; content: string | ContentBlock[] } }
  | { type: "control_request"; request_id: string; request: { subtype: "interrupt" } };   // O [E13b]
// S [static 03]: further subtypes initialize, set_permission_mode, set_model, end_session, ...;
// the CLI sends control_request {subtype: "can_use_tool", tool_name, input, ...} to the host.
```

## 4. ToolDefinition, ToolInvocation, ToolResult

```ts
interface ToolDefinition {                         // S [static 04], shape P where marked
  name: string; aliases?: string[];
  inputSchema: ZodSchema;                          // serialized to JSON Schema for the wire
  isEnabled(): boolean; isReadOnly(input): boolean; isConcurrencySafe(input): boolean;
  validateInput?(input, ctx): { result: boolean; message?: string };
  checkPermissions(input, ctx): PermissionDecision;
  call(input, ctx, canUseTool, parentMessage, onProgress): AsyncIterable<ToolEvent> | Promise<ToolOutput>;
  mapToolResultToToolResultBlockParam(output, toolUseId): ContentBlock;
  maxResultSizeChars: number;                      // 100000 typical; larger output is persisted to a file
}
interface ToolInvocation { id: string; name: string; input: object; parentMessageUuid: string }   // O
interface ToolResultRow {                          // user row / SDK user event                     O
  message: { role: "user"; content: [{ type: "tool_result"; tool_use_id; content; is_error? }] };
  toolUseResult:                                    // structured, per tool
    | { type: "text"; file: object }                                           // Read  [E02]
    | { stdout; stderr; interrupted; isImage; noOutputExpected; backgroundTaskId? }   // Bash [E04, E14]
    | { agentId; agentType; content; prompt; status; totalDurationMs; totalTokens; totalToolUseCount; usage; ... }  // Agent [E11]
    | string;                                                                  // errors: "Error: ..."
}
```

Error text conventions (observed): validation and unknown-tool failures are wrapped in
`<tool_use_error>...</tool_use_error>`; shell failures start `Exit code N`; hook blocks
start `PreToolUse:<Tool> hook error:`; an interrupt yields "The user doesn't want to
proceed with this tool use. ...".

## 5. PermissionDecision

```ts
type PermissionDecision =                          // S [static 04]; outcomes O
  | { behavior: "allow"; updatedInput?: object; decisionReason? }
  | { behavior: "deny"; message: string; decisionReason? }
  | { behavior: "ask"; message: string; suggestions?: PermissionUpdate[] }
  | { behavior: "passthrough" };
type PermissionMode = "default" | "acceptEdits" | "plan" | "bypassPermissions" | "dontAsk" | "auto";
interface PermissionRules { allow: string[]; deny: string[]; ask: string[] }   // "Tool" | "Tool(specifier)"  O [E08b]
// Transcript annotation on the tool_result row (O):
interface PermissionDecisionRecord { decision: string; source: string; reasonType?: string }
```

## 6. HookEvent

```ts
interface HookInputBase { session_id: string; transcript_path: string; cwd: string; hook_event_name: string;
  prompt_id?: string }                                                                    // O [E07a]
interface PreToolUseInput extends HookInputBase { permission_mode; effort: { level }; tool_name; tool_input; tool_use_id }
interface PostToolUseInput extends PreToolUseInput { tool_response: object; duration_ms: number }
interface UserPromptSubmitInput extends HookInputBase { permission_mode; prompt: string }
interface StopInput extends HookInputBase { permission_mode; effort; stop_hook_active: boolean;
  last_assistant_message: string; background_tasks; session_crons }
interface SessionStartInput extends HookInputBase { source: "startup" | "resume" | "compact" | "clear" }  // startup, compact O
interface SessionEndInput extends HookInputBase { reason: string }                        // "other" O
interface PreCompactInput extends HookInputBase { trigger: "manual" | "auto"; custom_instructions }
interface PostCompactInput extends HookInputBase { trigger; compact_summary: string }
interface InstructionsLoadedInput extends HookInputBase { file_path; load_reason; memory_type }
interface SubagentStopInput extends HookInputBase { permission_mode; stop_hook_active; agent_type; effort }
interface PermissionRequestInput extends HookInputBase { permission_mode; effort; tool_name; tool_input;
  permission_suggestions? }                                                               // O [E46-permreq]

interface HookOutput {                                                                    // O [E07b..h, E46-permreq]
  decision?: "block"; reason?: string;                       // Stop
  hookSpecificOutput?: {
    hookEventName: string;
    permissionDecision?: "allow" | "deny" | "ask"; permissionDecisionReason?: string;   // PreToolUse
    decision?: { behavior: "allow" | "deny"; updatedInput?: object; updatedPermissions?: PermissionUpdate[]; message?: string; interrupt?: boolean } // PermissionRequest
    updatedInput?: object;                                                               // PreToolUse
    additionalContext?: string;                                                          // UserPromptSubmit, PostToolUse
  };
}
// Exit code contract (O): 0 = ok, parse stdout as HookOutput; 2 = block, stderr to model; other = non-blocking error.
```

## 7. SubagentTask and TaskScheduler

```ts
interface TaskRecord {                               // O [E11, E14]
  task_id: string; run_id: string; tool_use_id: string;
  task_type: "local_agent" | "local_bash";           // S: more kinds (remote_agent, in-process teammate, workflow)
  description: string; subagent_type?: string; prompt?: string;
  is_backgrounded: boolean; spawn_depth?: number;
  status: "running" | "completed" | "killed" | "failed";   // "stopped" appears in the notification
  output_file: string; end_time?: number;
  usage?: { total_tokens; tool_uses; duration_ms };
}
// Limits (S, static 05): depth 3, 20 concurrent subagents, notification text cap 100000 chars.
```

## 8. Session storage

```ts
interface TranscriptRowBase {                        // O [transcript-schema.json]
  type: string; uuid: string; parentUuid: string | null; timestamp: string;
  sessionId: string; cwd: string; gitBranch: string; version: string;
  userType: string; entrypoint: string; isSidechain: boolean; slug?: string;
}
interface UserRow extends TranscriptRowBase { type: "user"; message: { role: "user"; content };
  promptId?; promptSource?; permissionMode?; turnOrigin?; turnPosition?: { promptIndex; turnIndex };
  toolUseResult?; sourceToolAssistantUUID?; permissionDecision?; toolDenialKind?;
  isMeta?; isCompactSummary?; isVisibleInTranscriptOnly? }
interface AssistantRow extends TranscriptRowBase { type: "assistant"; message: AssistantWire; requestId;
  requestedModel; effort; perTurnEffort; apiBlockIndex; thinkingDisplay?; thinkingDurationMs?; wireToolInputs?;
  isApiErrorMessage?; apiError?; apiErrorStatus?; apiErrorParams?; quotaLimits?; error? }
interface AttachmentRow extends TranscriptRowBase { type: "attachment"; attachment: { type: string; ... };
  rendered: { content }[]; renderedRole: string; renderedBesideToolResult: boolean }
interface CompactBoundaryRow extends TranscriptRowBase { type: "system"; subtype: "compact_boundary";
  parentUuid: null; logicalParentUuid: string; compactMetadata: object; content: string; isMeta: boolean; level: string }
interface ApiErrorRow extends TranscriptRowBase { type: "system"; subtype: "api_error"; error: object;
  retryAttempt: number; maxRetries: number; retryInMs: number; source: string; level: string }
interface StopHookSummaryRow extends TranscriptRowBase { type: "system"; subtype: "stop_hook_summary";
  hookCount; hookInfos: { command; durationMs? }[]; hookErrors: string[]; hookAdditionalContext;
  preventedContinuation: boolean; stopReason: string; hasOutput: boolean; toolUseID: string }
// Metadata rows without uuid chains (O):
type MetaRow =
  | { type: "queue-operation"; operation: string; content?: string; timestamp; sessionId }
  | { type: "last-prompt"; lastPrompt: string; leafUuid: string; sessionId }
  | { type: "mode"; mode: string; sessionId }
  | { type: "cost-state"; totalCostUSD; modelUsage; totalAPIDuration; totalDuration; totalToolDuration;
      totalLinesAdded; totalLinesRemoved; startTime; hasUnknownModelCost; sessionId }
  | { type: "atis-latch"; atis: string; sessionId };
// Subagent rows add agentId (and attributionAgent on assistant rows).
```

`ResumeState` (P, derived from E15 and static pass 05): leaf uuid from the last
`last-prompt` row, chain rebuilt by walking `parentUuid`, a compact boundary acting as a
chain root, then mode, cost state and attachments restored from the metadata rows.

## 9. CompactionRequest

```ts
// O [E17a]: not a distinct endpoint or schema. It is a ModelRequest where
//   system, tools  = the session's own (cache prefix reused)
//   messages       = current history, with one extra text block appended to the last user message
//                    holding the summarization instruction (analysis + summary sections, no tools)
//   cache_control  = ephemeral without ttl
// Output: one assistant text. The loop stores a compact_boundary row and a synthetic user message
// (isCompactSummary) that begins "This session is being continued from a previous conversation".
```

## 10. Daemon worker and PTY contracts

```ts
interface DaemonWorkerStdin {                         // S [g72zgfkm@14736]
  config: Record<string, unknown>;
  initialAccessToken: string;
}
type WorkerExit = 0 | 1 | 2 | 75 | 78;              // S [mwtqc60a@615; g72zgfkm@14736]

interface PtyFrame {                                  // S [k6k3h9nt@7067, @7235, @7383]
  payloadLength: number;                              // uint32be
  kind: 0 | 1;                                        // DATA | JSON control
  payload: Uint8Array | string;
}
type PtyHostToClient =
  | { t: "hello"; replPid: number; version: string }
  | { t: "live" }
  | { t: "ping" }
  | { t: "exit"; code?: number; signal?: string }
  | { t: "auth-required" };
type PtyClientToHost =
  | { t: "auth"; token: string }
  | { t: "pong" }
  | { t: "resize"; cols: number; rows: number }
  | { t: "kill"; sig: "SIGTERM" | "SIGKILL" };
```

The host gates DATA forwarding on the per-socket token, not the entire control channel;
frame payloads over 1 MiB and malformed or unknown frames close the parser. Static sources:
`chunk-jn2r7nez.js@1906`, `@2994`, `@3498`; `chunk-5zh5q8ee.js@1564`.
This contract is static only. Named-pipe ACLs and Bun.Terminal behavior remain unknown.

## 11. Renderer and input scheduler contracts

```ts
interface RenderScheduler {                            // S [v44rfc3q@319390, @319644, @320043, @320611]
  minFrameIntervalMs: 16;                             // tg
  inputPriorityWindowMs: 50;                          // oUo
  inputPriorityFrameIntervalMs: 4;                    // sUo
  nonBlockingStdoutLimitBytes: 16384;                 // iUo
  backpressureRetryMs: 250;                            // IFr
  frameMicrotaskQueued: boolean;
  lastPacedFrameAt: number;
}
type PermissionDialogResult = "allow" | "deny" | "cancelled"; // S [57pw7ky5@58350; 9w4htdvs@1249278]
```

`rootNode.onRender` schedules the renderer; input marks the priority window and dispatches
through discrete updates. Escape is context-sensitive: permission selectors call `onCancel`,
while composers and task viewers consume it according to their own state. The local dialog
maps allow, deny, and cancel to different abort/feedback paths; remote dialogs validate
`can_use_tool` and `request_id`, deduplicate in-flight requests, and conditionally send an
interrupt on denial/cancellation. Sources: `chunk-v44rfc3q.js@233800`, `@235996`, `@236400`,
`@311434`, `@319390`, `@319644`, `@320043`, `@320611`; `chunk-75p1g95y.js@10757`,
`@16461`; `chunk-9w4htdvs.js@1249278`, `@1251327`, `@217294`, `@222896`, `@223400`; `chunk-57pw7ky5.js@51135`,
`@55500`, `@58350`, `@6732`.
