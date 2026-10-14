import assert from "node:assert/strict";
import { faultMatches } from "./fault_match.mjs";

assert.equal(
  faultMatches({ path_contains: "/v1/messages", body_contains: "<analysis>" }, "/v1/messages?beta=true", "prefix <analysis> suffix"),
  true,
);
assert.equal(
  faultMatches({ path_contains: "/v1/messages", body_contains: "<analysis>" }, "/v1/messages?beta=true", "ordinary turn"),
  false,
);
assert.equal(
  faultMatches({ path_contains: "/v1/messages", body_contains: "<analysis>" }, "/api/hello", "prefix <analysis> suffix"),
  false,
);
assert.equal(
  faultMatches({ body_contains_all: ["<analysis>", "<summary>"] }, "/v1/messages", "<analysis> then <summary>"),
  true,
);
assert.equal(
  faultMatches({ body_contains_all: ["<analysis>", "<summary>"] }, "/v1/messages", "<analysis> only"),
  false,
);
assert.equal(
  faultMatches({}, "/v1/messages", "anything"),
  true,
);

console.log("capture proxy fault matcher tests passed");
