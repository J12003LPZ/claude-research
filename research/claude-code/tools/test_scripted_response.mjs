import assert from "node:assert/strict";
import { buildJsonMessage, buildSse, takeFromSequence } from "./scripted_response.mjs";
import { faultMatches } from "./fault_match.mjs";

// SSE: text + tool_use blocks produce the canonical Anthropic event order.
const response = {
  model: "claude-haiku-5-5",
  stop_reason: "tool_use",
  content: [
    { type: "text", text: "hello" },
    { type: "tool_use", id: "toolu_lab_1", name: "Bash", input: { command: "echo hi" } },
  ],
};
const sse = buildSse(response);
const events = sse
  .split("\n\n")
  .filter(Boolean)
  .map((chunk) => {
    const lines = chunk.split("\n");
    return { event: lines[0].replace("event: ", ""), data: JSON.parse(lines[1].replace("data: ", "")) };
  });
assert.deepEqual(
  events.map((e) => e.event),
  [
    "message_start",
    "content_block_start", "content_block_delta", "content_block_stop",
    "content_block_start", "content_block_delta", "content_block_stop",
    "message_delta", "message_stop",
  ],
);
assert.equal(events[1].data.content_block.type, "text");
assert.equal(events[2].data.delta.type, "text_delta");
assert.equal(events[2].data.delta.text, "hello");
assert.equal(events[4].data.content_block.type, "tool_use");
assert.equal(events[4].data.content_block.id, "toolu_lab_1");
assert.equal(events[5].data.delta.type, "input_json_delta");
assert.deepEqual(JSON.parse(events[5].data.delta.partial_json), { command: "echo hi" });
assert.equal(events[7].data.delta.stop_reason, "tool_use");
assert.equal(events[0].data.message.model, "claude-haiku-5-5");

// Non-streaming JSON form.
const json = buildJsonMessage(response);
assert.equal(json.type, "message");
assert.equal(json.stop_reason, "tool_use");
assert.deepEqual(json.content, response.content);

// Matcher: body_not_contains.
assert.equal(faultMatches({ body_not_contains: ["parent-id"] }, "/v1/messages", "child only"), true);
assert.equal(faultMatches({ body_not_contains: ["parent-id"] }, "/v1/messages", "has parent-id here"), false);
assert.equal(faultMatches({ body_not_contains: "parent-id" }, "/v1/messages", "child only"), false);

// Sequence: consume the first matching entry, keep the rest, fall back to `otherwise`.
const state = {
  path_contains: "/v1/messages",
  sequence: [
    { body_contains: "AAA", response: { content: [{ type: "text", text: "first" }] } },
    { body_contains: "BBB", response: { content: [{ type: "text", text: "second" }] } },
  ],
  otherwise: { status: 400, body: { type: "error", error: { type: "invalid_request_error", message: "x" } } },
};
let r = takeFromSequence(state, "/v1/messages", "xx BBB xx");
assert.equal(r.entry.response.content[0].text, "second");
assert.equal(state.sequence.length, 1);
r = takeFromSequence(state, "/v1/messages", "nothing matches");
assert.equal(r.entry, state.otherwise);
assert.equal(state.sequence.length, 1);
r = takeFromSequence(state, "/v1/messages", "AAA");
assert.equal(r.entry.response.content[0].text, "first");
assert.equal(state.sequence.length, 0);
assert.equal(takeFromSequence(state, "/api/hello", "AAA"), null);

console.log("scripted response tests passed");
