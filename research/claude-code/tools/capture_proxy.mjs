// Local observation proxy for controlled Claude Code experiments.
//
//   node capture_proxy.mjs <port> <raw_out_dir> [upstream_host=api.anthropic.com]
//
// The CLI is pointed here with ANTHROPIC_BASE_URL=http://127.0.0.1:<port> (a documented
// setting). Every request is forwarded unchanged to the real upstream over TLS, so
// authentication is neither bypassed nor altered. Credential-bearing header VALUES are
// never written to disk: only the header name and a "<redacted len=N>" marker.
//
// Raw captures contain prompt text and private instruction files, so <raw_out_dir> must
// live outside the research directory. summarize_captures.py turns them into the
// sanitized structural evidence that is kept.
//
// Fault injection (safe transport-failure experiments): if <raw_out_dir>/fault.json
// exists with {"path_contains": "/v1/messages", "body_contains_all": ["<analysis>",
// "<summary>"], "status": 529, "times": 2, "body": {...}, "headers": {...},
// "mode": "status" | "reset" | "stall" | "sse_stall", "after_bytes": 0,
// "stall_ms": 0}, matching requests are answered locally and `times` is
// decremented. Nothing is sent upstream for an injected fault. `body_contains`
// and `body_contains_all` are optional literal matchers for request-body-aware faults.
import http from "node:http";
import https from "node:https";
import fs from "node:fs";
import path from "node:path";
import { faultMatches } from "./fault_match.mjs";

const port = Number(process.argv[2]);
const outDir = process.argv[3];
const upstream = process.argv[4] || "api.anthropic.com";
fs.mkdirSync(outDir, { recursive: true });

const SENSITIVE = /^(authorization|x-api-key|cookie|set-cookie|proxy-authorization|anthropic-organization-id|x-organization.*|cf-ray|x-claude-code-session-id|x-client-request-id)$/i;
const redact = (h) =>
  Object.fromEntries(
    Object.entries(h).map(([k, v]) => [k, SENSITIVE.test(k) ? `<redacted len=${String(v).length}>` : v]),
  );

let seq = 0;
const t0 = Date.now();

function readFault(urlPath, bodyText) {
  const p = path.join(outDir, "fault.json");
  if (!fs.existsSync(p)) return null;
  try {
    const f = JSON.parse(fs.readFileSync(p, "utf8"));
    if (!f.times || f.times <= 0) return null;
    if (!faultMatches(f, urlPath, bodyText)) return null;
    f.times -= 1;
    fs.writeFileSync(p, JSON.stringify(f));
    return f;
  } catch {
    return null;
  }
}

const server = http.createServer((req, res) => {
  const id = String(++seq).padStart(4, "0");
  const started = Date.now();
  const chunks = [];
  req.on("data", (c) => chunks.push(c));
  req.on("end", () => {
    const body = Buffer.concat(chunks);
    let parsed = null;
    try {
      parsed = JSON.parse(body.toString("utf8"));
    } catch {}
    fs.writeFileSync(
      path.join(outDir, `${id}-req.json`),
      JSON.stringify({
        seq: id,
        t_ms: started - t0,
        iso: new Date(started).toISOString(),
        method: req.method,
        url: req.url,
        headers: redact(req.headers),
        header_order: req.rawHeaders.filter((_, i) => i % 2 === 0),
        body_bytes: body.length,
        body: parsed ?? (body.length ? `<non-json ${body.length} bytes>` : null),
      }),
    );

    const fault = readFault(req.url, body.toString("utf8"));
    const timing = fs.createWriteStream(path.join(outDir, `${id}-res.chunks.jsonl`));
    const resBody = fs.createWriteStream(path.join(outDir, `${id}-res.body`));
    const meta = (o) => fs.writeFileSync(path.join(outDir, `${id}-res.json`), JSON.stringify(o));
    const endCapture = () => {
      if (!timing.writableEnded) timing.end();
      if (!resBody.writableEnded) resBody.end();
    };

    if (fault) {
      const mode = fault.mode || "status";
      if (mode === "reset") {
        meta({ seq: id, injected: true, mode, t_ms: Date.now() - t0 });
        req.socket.destroy();
        endCapture();
        return;
      }
      if (mode === "sse_stall") {
        // Valid SSE start, then silence: exercises the idle watchdogs. After stall_ms
        // (default: never) the connection is closed without further events.
        const start = { type: "message_start", message: { id: "msg_lab_stall", type: "message", role: "assistant",
          model: fault.model || "claude-haiku-5-5", content: [], stop_reason: null, stop_sequence: null,
          usage: { input_tokens: 1, output_tokens: 1 } } };
        const sseHeaders = { "content-type": "text/event-stream", "cache-control": "no-cache" };
        meta({ seq: id, injected: true, mode, status: 200, headers: sseHeaders, t_ms: Date.now() - t0 });
        res.writeHead(200, sseHeaders);
        const ssePayload = `event: message_start
data: ${JSON.stringify(start)}

`;
        res.write(ssePayload);
        resBody.write(ssePayload);
        if (fault.stall_ms) setTimeout(() => { res.end(); endCapture(); }, fault.stall_ms);
        req.on("close", endCapture);
        return;
      }
      const payload = JSON.stringify(
        fault.body ?? { type: "error", error: { type: "overloaded_error", message: "Overloaded (injected by lab proxy)" } },
      );
      const headers = { "content-type": "application/json", ...(fault.headers || {}) };
      meta({ seq: id, injected: true, mode, status: fault.status, headers, t_ms: Date.now() - t0 });
      const send = () => {
        res.writeHead(fault.status || 529, headers);
        res.end(payload);
        resBody.end(payload);
        timing.end();
      };
      if (mode === "stall") setTimeout(send, fault.stall_ms || 0);
      else send();
      return;
    }

    const headers = { ...req.headers, host: upstream };
    delete headers["accept-encoding"]; // identity upstream so the SSE tee is readable
    const up = https.request(
      { host: upstream, port: 443, method: req.method, path: req.url, headers },
      (ur) => {
        meta({
          seq: id,
          injected: false,
          status: ur.statusCode,
          headers: redact(ur.headers),
          ttfb_ms: Date.now() - started,
          t_ms: Date.now() - t0,
        });
        res.writeHead(ur.statusCode || 502, ur.headers);
        ur.on("data", (c) => {
          timing.write(JSON.stringify({ t_ms: Date.now() - started, bytes: c.length }) + "\n");
          resBody.write(c);
          res.write(c);
        });
        ur.on("end", () => {
          timing.write(JSON.stringify({ t_ms: Date.now() - started, end: true }) + "\n");
          endCapture();
          res.end();
        });
        ur.on("error", () => {
          endCapture();
          res.destroy();
        });
      },
    );
    up.on("error", (e) => {
      meta({ seq: id, injected: false, upstream_error: String(e.code || e.message), t_ms: Date.now() - t0 });
      endCapture();
      if (!res.headersSent) res.writeHead(502, { "content-type": "application/json" });
      res.end(JSON.stringify({ type: "error", error: { type: "api_error", message: "lab proxy upstream error" } }));
    });
    // client went away mid-stream (cancellation evidence)
    res.on("close", () => {
      if (!res.writableEnded) {
        fs.appendFileSync(
          path.join(outDir, `${id}-res.chunks.jsonl`),
          JSON.stringify({ t_ms: Date.now() - started, client_closed_early: true }) + "\n",
        );
        endCapture();
        up.destroy();
      }
    });
    up.end(body);
  });
});

server.listen(port, "127.0.0.1", () => {
  fs.writeFileSync(path.join(outDir, "proxy.pid"), String(process.pid));
  console.log(`lab proxy on 127.0.0.1:${port} -> https://${upstream}  raw=${outDir}`);
});
