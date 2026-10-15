# MCP tool lifecycle

Status: VERIFIED-STATIC for the central discovery/connection paths; PARTIAL for transport-specific implementation details and global caller enumeration.

## Server configuration and transports

The configuration schema in `chunk-ff982hys.js@58847` admits `stdio`, `sse`, `sse-ide`, `http`, `ws`, and `sdk` transports. `pCr` classifies SDK and IDE-oriented variants. Connection implementations are exported from `chunk-9158d2ng.js` (`listToolsRaw`, `invokeToolRaw`, `reconnectMcpServerImpl`, `persistLiveListing`, `processMCPResult`, `transformResultContent`) and related wrappers in `chunk-n0pj9mhh.js`.

## Connection state machine

`yGt` deduplicates concurrent joins and ownership. `BLs` waits for a pending client to settle, drops failed clients, adds missing configuration, and resolves through `pKt` or a failed timeout path (`AW`). The reconnect loop in `chunk-0nh75v9f.js@11641` retries transport connection, preserves and refreshes a healthy cached listing where possible, marks failed/needs-auth states, and performs cleanup on disconnection. OAuth handling in `chunk-032sc1gt.js@6437` reuses an active flow, discards it when identity/policy changes, reconnects, verifies client/session wiring, and either adopts the server or clears an orphan.

```text
config row
  -> pending MCP client
  -> join/reconnect deduplication
  -> transport connect (stdio/SSE/HTTP/WS/SDK)
  -> list tools/prompts/resources
  -> persist live listing + active tool registry
  -> ready / failed / needs-auth
       ^ retry / reconnect
       -> disconnect cleanup and stale-tool removal
```

The plugin path `kGt` in `chunk-phacttch.js@1826026` wraps this lifecycle for plugin-owned servers and removes a server that is unloaded during connection.

## Tool naming and registration

`mre` (`chunk-phacttch.js@456210`) builds the `mcp__server__tool` alias. `Tht` verifies that the server generation/configuration and active tool still match before use. Tool schemas are translated into the normal tool record, so execution runs through the shared dispatch/permission machinery (`Qj`/`AWo` in `chunk-phacttch.js@2268196–2275985`).

`ToolSearch` is the deferred-discovery boundary. Its built-in record is constructed near `chunk-phacttch.js@937427` (`Rrr`). The call captures current tools, `refreshTools`, MCP clients, and tool state. It filters eligible tools, reports pending servers, waits for changed/pending clients with a 50 ms polling interval, refreshes the active/deferred registry, and returns `tool_reference` blocks. Exact-name and keyword search have separate paths; a miss reports pending/failed servers and may say tools can become available shortly. A successful discovery updates the active tool set for later turns; the source does not show an in-flight model request being rewritten retroactively.

Deferred tool announcements are represented by `deferred_tools_record` around `chunk-phacttch.js@136472`, with name-only announcements, stripped references, and copied inputs. MCP availability deltas are represented as `deferred_tools_delta`; the active model context can therefore receive an incremental tool availability change.

## Invocation and result conversion

After alias/generation checks, the regular dispatcher resolves pending MCP waits, unknown tools, abort/isolation/routing conditions, and then invokes the common permission/validation/hooks/call path. `invokeToolRaw` and `processMCPResult` normalize transport content before it reaches the normal tool-result block. Errors are converted into tool-result error content rather than bypassing the conversation protocol.

## Failure, disappearance, and permissions

Pending connection timeout yields a failed server; reconnect can mark needs-auth; stale live listings are dropped during refresh/cleanup. If a server disappears between discovery and invocation, the alias/generation check or shared unknown-tool path is the evidence-backed rejection point. The exact behavior when the transport dies after the remote call has been sent is not recovered beyond the common error/result path.

MCP tools inherit the ordinary permission engine. Dynamic registration does not establish a separate permission database. Plugin-owned MCP tools additionally pass through plugin ownership/loading checks. Subagent restrictions and hooks are applied by the same dispatch context, but a global proof for every dynamic caller is unavailable because the REA semantic graph is partial.

## Confidence table

| Claim | Confidence | Anchor |
|---|---|---|
| Supported transport variants are schema-defined | VERIFIED-STATIC | `chunk-ff982hys.js@58847` |
| Joins/reconnects are deduplicated and stateful | VERIFIED-STATIC | `chunk-0nh75v9f.js@11641`, `chunk-phacttch.js@1824xxx` |
| Tool aliases use `mcp__server__tool` and generation checks | VERIFIED-STATIC | `chunk-phacttch.js@456210` |
| ToolSearch refreshes deferred/pending MCP state and returns references | VERIFIED-STATIC | `chunk-phacttch.js@937427` |
| MCP calls use shared permission/validation/hooks path | VERIFIED-STATIC | `chunk-phacttch.js@2268196–2275985` |
| Dynamic availability can change between turns | VERIFIED-STATIC | `chunk-phacttch.js@136472`, deferred delta handling |
| Every transport's reconnect/error semantics are fully recovered | UNKNOWN | transport wrappers and dynamic loading remain |

Open: exact stdio child-process shutdown sequencing, HTTP/SSE retry backoff values by transport, live-listing persistence schema, and whether every pending call is actively cancelled versus allowed to finish when a server disappears.
