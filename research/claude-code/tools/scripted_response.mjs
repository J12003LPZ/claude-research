// Canned model responses for the lab proxy. Pure functions, no I/O.
//
// A fault.json with a `sequence` array lets a local experiment run without any upstream model
// call: each entry carries the usual matchers (path_contains, body_contains, body_contains_all,
// body_not_contains) and a `response` ({model, content, stop_reason}). The first entry that
// matches a request is consumed and answered; `otherwise` answers any other request that matches
// the top-level path so nothing unmatched is forwarded upstream.
import { faultMatches } from "./fault_match.mjs";

const usage = (outputTokens) => ({ input_tokens: 10, output_tokens: outputTokens });

function messageShell(response) {
  return {
    id: response.id || "msg_lab_scripted",
    type: "message",
    role: "assistant",
    model: response.model || "claude-haiku-5-5",
    content: [],
    stop_reason: null,
    stop_sequence: null,
    usage: usage(1),
  };
}

function event(name, data) {
  return `event: ${name}\ndata: ${JSON.stringify(data)}\n\n`;
}

export function buildSse(response) {
  let out = event("message_start", { type: "message_start", message: messageShell(response) });
  response.content.forEach((block, index) => {
    if (block.type === "text") {
      out += event("content_block_start", { type: "content_block_start", index, content_block: { type: "text", text: "" } });
      out += event("content_block_delta", { type: "content_block_delta", index, delta: { type: "text_delta", text: block.text } });
    } else if (block.type === "tool_use") {
      out += event("content_block_start", {
        type: "content_block_start", index,
        content_block: { type: "tool_use", id: block.id, name: block.name, input: {} },
      });
      out += event("content_block_delta", {
        type: "content_block_delta", index,
        delta: { type: "input_json_delta", partial_json: JSON.stringify(block.input ?? {}) },
      });
    } else {
      throw new Error(`unsupported scripted block type: ${block.type}`);
    }
    out += event("content_block_stop", { type: "content_block_stop", index });
  });
  out += event("message_delta", {
    type: "message_delta",
    delta: { stop_reason: response.stop_reason || "end_turn", stop_sequence: null },
    usage: usage(5),
  });
  out += event("message_stop", { type: "message_stop" });
  return out;
}

export function buildJsonMessage(response) {
  return {
    ...messageShell(response),
    content: response.content,
    stop_reason: response.stop_reason || "end_turn",
    usage: usage(5),
  };
}

// Consume the first matching sequence entry. Returns {entry} or null when the request is not
// covered by this fault at all. Mutates `state.sequence`.
export function takeFromSequence(state, urlPath, bodyText) {
  if (!Array.isArray(state.sequence)) return null;
  if (!faultMatches({ path_contains: state.path_contains }, urlPath, bodyText)) return null;
  const index = state.sequence.findIndex((entry) => faultMatches(entry, urlPath, bodyText));
  if (index >= 0) {
    const [entry] = state.sequence.splice(index, 1);
    return { entry };
  }
  return state.otherwise ? { entry: state.otherwise } : null;
}
