import assert from "node:assert/strict";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";
import { once } from "node:events";
import net from "node:net";
import { fileURLToPath } from "node:url";

const proxyPath = path.join(path.dirname(fileURLToPath(import.meta.url)), "capture_proxy.mjs");
const outDir = fs.mkdtempSync(path.join(os.tmpdir(), "cc-capture-proxy-"));

function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const port = server.address().port;
      server.close(() => resolve(port));
    });
  });
}

const port = await freePort();
fs.writeFileSync(path.join(outDir, "fault.json"), JSON.stringify({
  path_contains: "/v1/messages",
  times: 1,
  mode: "sse_stall",
  stall_ms: 20,
}));

const proxy = spawn(process.execPath, [proxyPath, String(port), outDir], {
  stdio: ["ignore", "pipe", "pipe"],
});
let stdout = "";
proxy.stdout.setEncoding("utf8");
proxy.stdout.on("data", (chunk) => { stdout += chunk; });
for (let i = 0; i < 50 && !stdout.includes("lab proxy on"); i += 1) {
  await new Promise((resolve) => setTimeout(resolve, 10));
}
assert.match(stdout, /lab proxy on/);

const response = await new Promise((resolve, reject) => {
  const request = http.request({
    host: "127.0.0.1",
    port,
    path: "/v1/messages",
    method: "POST",
    headers: { "content-type": "application/json" },
  }, (res) => {
    const chunks = [];
    res.on("data", (chunk) => chunks.push(chunk));
    res.on("end", () => resolve({ res, body: Buffer.concat(chunks).toString("utf8") }));
  });
  request.on("error", reject);
  request.end("{}");
});

assert.equal(response.res.statusCode, 200);
assert.equal(response.res.headers["content-type"], "text/event-stream");
assert.match(response.body, /event: message_start/);

await new Promise((resolve) => setTimeout(resolve, 30));
const meta = JSON.parse(fs.readFileSync(path.join(outDir, "0001-res.json"), "utf8"));
const captured = fs.readFileSync(path.join(outDir, "0001-res.body"), "utf8");
assert.equal(meta.headers["content-type"], "text/event-stream");
assert.match(captured, /event: message_start/);

proxy.kill();
await once(proxy, "exit");
fs.rmSync(outDir, { recursive: true, force: true });
console.log("capture proxy SSE evidence test passed");
