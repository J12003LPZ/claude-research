# MCP connection races and dynamic availability

Status: `PARTIAL` — connection admission, discovery waiting, generation checks,
stale-refresh rejection, call-level abort/timeout policy, and task-handle
cancellation are `VERIFIED-STATIC`; legacy/modern SSE and Streamable HTTP
retry/settlement bodies are now source-resolved, while native timing, replay
retention, and all dynamic host/provider paths remain open.

## Configuration and state vocabulary

The configuration schema accepts `stdio`, `sse`, `sse-ide`, `http`, `ws`, and
`sdk` transport variants (`chunk-ff982hys.js@58847`). A configured server is
represented by a client row such as `pending`, `connected`, `cached`, `failed`,
or `needs-auth`. The active tool registry is separate from the client row: a
server can be pending while its prior listing is cached, and a failed or
removed server can have no active model-facing tools.

The source distinguishes server identity/configuration from a tool's display
name. Plugin-owned MCP registrations maintain an owner map and server key;
`mre` mints the `mcp__server__tool` name and `Tht` verifies that the active
registration and server key still match (`chunk-phacttch.js@456210`).

## Pending discovery race

`ToolSearch` is a deferred-discovery tool (`chunk-phacttch.js@937427`). At call
time it snapshots the current tool pool and deferred tools, invalidates stale
tool-state search data, and queries the current MCP-client list. If the query
targets a pending server, it waits in an abort-aware loop for at most the
discovery window, polling at 50 ms. It then refreshes the tool/deferred lists
and searches again.

The important race behavior is:

```text
snapshot tools/deferred clients
  -> pending server detected
  -> wait while !aborted and server remains pending
  -> refresh current tools/deferred clients
  -> search the refreshed view
```

The search result can therefore report a tool that was not present at the
start of the call, or report a pending/failed server instead of a tool. An
abort exits the waiting loop; no source branch rewrites an already-issued
model request with a late schema.

## Dispatch-time pending wait

The shared dispatcher `Qj` first handles pending-MCP conditions before invoking
the normal permission/validation/tool-call pipeline
(`chunk-phacttch.js@2268196`). A pending alias can cause the dispatcher to wait
for connection progress and refresh the tool pool. If the name cannot be
resolved after refresh, it constructs the ordinary unknown-tool/error result
with the original tool-use id. This is why deferred discovery and direct
execution are separate stages: ToolSearch changes the later active tool set,
while `Qj` handles a call that has already been emitted by the model.

## Join and reconnect deduplication

Plugin-owned connection admission uses `K3.own` followed by `K3.join` and a
single connection callback (`chunk-phacttch.js@1826026`). If a plugin is
unloaded while its server is connecting, the code removes the server and
returns a failed/refused result rather than publishing a connection owned by a
dead plugin.

The reconnect loop in `chunk-0nh75v9f.js@11641` uses a reconnect attempt epoch,
checks whether the session is stopping or the configuration has changed, and
reuses a still-healthy settled connection when possible. After a reconnect
returns, it checks that the candidate is still current and that the connection
is still healthy. Only then does it publish the client row and refreshed tools.
If the candidate is stale or the server is stopping, it detaches/closes the
candidate instead of replacing a newer connection.

The controller-level retry state machine is also visible in that body:

```text
for attempt = 1 .. automaticLimit + slowLimit:
  if attempt > 1:
    if attempt is in slow phase:
      sleep(jittered exponential delay(base, cap, slowAttempt, random))
    else:
      sleep(normal reconnect delay(attempt - 1))
  stop if run ending, configuration changed, or another owner replaced row
  in slow phase, publish pending state unless another dial is unsettled
  if another dial is unsettled: skip this attempt, or give up at slow limit
  try a healthy settled-connection reuse, otherwise reconnect the server
  after return, detach/close if stale, stopped, or unhealthy
  if connected and still current: publish and refresh tools; finish
  classify failure as retryable or terminal
  at automatic exhaustion, publish failed/needs-auth; retryable failures
  switch to the slow background phase
```

The loop therefore suppresses overlapping reconnects with
`hasUnsettledDial`, carries `reconnectAttempt`/`maxReconnectAttempts` in the
pending row, and distinguishes “another dial is still in progress” from a
failed transport. It also records separate telemetry for automatic versus
slow reconnect and for `needs-auth`, exhaustion, and non-retryable outcomes.
The exact numeric constants are closed over by the minified module, but the
delay roles and phase transition are `VERIFIED-STATIC`; the SDK's own HTTP,
SSE, or WebSocket retry policy remains outside this controller.

## `tools/list_changed` race

The MCP list-change handler keeps weak identity associations for connected
clients. On a notification it obtains the current client row, compares the
stored server configuration with the event client's configuration, and fetches
the new listing. The update helper applies the result to both ordinary and
dynamic MCP state only if the current row still refers to the same server.
If another server now owns the name, the result is rejected with a stale-name
diagnostic. A failed list call can retain the previous tool set, as indicated
by the `kept-previous` outcome in the same refresh path (`chunk-0nh75v9f.js@11641`).

This closes one major race:

```text
client A emits list_changed
  -> before refresh completes, server name is replaced by client B
  -> config/identity check fails
  -> A's listing is not applied over B's active registry
```

It does not prove that a tool removed by a valid list refresh cancels an
already-running remote invocation.

## Disappearance between discovery and call

The generation/owner check in `Tht` runs against the active registration and
the current server key. If a tool disappears or the server generation changes
after the model saw the schema but before dispatch, the call fails the identity
check or reaches `Qj`'s unknown/pending path. The resulting conversation block
still carries the original `tool_use_id`, so the model receives a correlated
tool error rather than an unkeyed transport exception.

For a call already sent to the remote server, the inspected common dispatcher
and refresh code do not expose one identical settlement implementation for
every transport, but the generation-specific MCP client wrapper does expose
the caller-side cancellation contract. The runtime accessor selects the v1 or
v2 client tree by generation (`chunk-drrbp3n4.js@4838`); the v2 client’s
`ao` call wrapper at `chunk-9158d2ng.js@175589` passes the caller's abort signal
to `client.callTool`, creates an overall timeout, and maintains a 30-second
watchdog for no response/progress. It also tracks in-flight request ids and
arms a transport-loss failure when a request has been sent but its answer
stream ends or the transport has been silent after an armed error. The result
is a correlated MCP error classified as downstream-unreachable rather than a
generic unknown-tool result.

The wrapper races the actual call against the timeout/error promises and tears
down the watchdog, interval, and abort listener in `finally`
(`chunk-9158d2ng.js@182461`). For task-capable modern calls, an abort after a
task handle is returned sends `tasks/cancel` with a bounded abort timeout; the
inline task driver also uses the parent signal while polling and resolving
elicitation input. The stdio transport's close path ends stdin, waits for a
grace period, sends SIGTERM, waits again, and escalates to SIGKILL if the child
does not exit (`chunk-9158d2ng.js@21315`; its `start`/close event handling is
at `@19724`). Thus cancellation is statically proven at the wrapper and
stdio-child layers. The exact timing and ownership are now narrower: `close()`
ends stdin, waits up to two seconds, sends SIGTERM, waits another two seconds,
and escalates to SIGKILL if the child still has no exit code; `_dispose()` uses
an immediate SIGTERM, a one-second wait, then SIGKILL, destroys all stdio
streams, and clears the read buffer (`chunk-9158d2ng.js@19308`, `@20196`).
The transport reports child `close` through `onclose` and spawn/stdin/stdout
errors through `onerror`; stderr is only piped to its optional PassThrough and
is not converted to a tool result in this class. What remains unknown is how
each SDK HTTP/SSE/WS implementation settles its own already-written request
after receiving the signal, and the exact reconnect/backoff behavior after
that settlement.

The bounded stdio subclass adds a separate safety net for an MCP server that
never establishes a connection. `start()` rejects new processes after global
shutdown, arms `Bht` around the child, and `handOffExitCleanup()` removes that
exit-time cleanup after ownership transfer (`chunk-9158d2ng.js@26410`).
`Bht` registers one-shot exit cleanup and `pe` escalates unconnected children:
Windows closes stdin, waits 300 ms, then terminates the process tree and waits
600 ms; non-Windows sends SIGINT, SIGTERM, then SIGKILL with 100/400/100 ms
waits, stopping as soon as the child exits (`chunk-tem5x312.js@6146`,
`@6251`, `@6379`, `@6840`). This reaper covers an unconnected child, not MCP
call-result conversion.

### SDK closure-to-pending-call translation

The SDK `Client.connect()` installs wrappers around the selected transport's
existing `onclose`, `onerror`, and `onmessage` callbacks. A transport close
first invokes the previous callback and then enters `_onclose()`
(`chunk-6y1jd448.js@100162`). `_onclose()` snapshots and replaces the response
handler map, clears progress handlers and debounced notifications, clears all
request timeout timers, replaces and aborts inbound request-handler
controllers, creates one `ConnectionClosed` error, clears the active transport,
invokes the client's `onclose`, and finally rejects every pending response
handler with that error (`chunk-6y1jd448.js@100736`). Transport errors alone
only flow to the client's `onerror`; they do not, in this layer, reject pending
response handlers (`chunk-6y1jd448.js@101233`).

This is the common pending-call settlement contract for transports connected
through this SDK `Client`: a stdio child `close`, SSE `EventSource` close, or
Streamable HTTP close reaches the same pending-handler rejection once the
transport invokes `onclose`. The SSE transport's `close()` aborts its
controller, closes the event source, and calls `onclose`
(`chunk-6y1jd448.js@315922`, `@319109`). Streamable HTTP `close()` cancels
scheduled reconnect, aborts its controller, and calls `onclose`; its `_send`
uses that controller plus the per-request signal for POST cancellation and
suppresses `onerror` notification when the request signal is already aborted
(`chunk-6y1jd448.js@320990`, `@328757`, `@328935`). The remaining unknown is
whether a transport-specific disconnect path elects to reconnect or retain a
response stream before invoking `onclose`, and how WebSocket-specific close
timing enters the same contract.

### Legacy SSE versus Streamable HTTP reconnection (new continuation finding)

The extracted SDK contains two materially different HTTP/SSE lifecycles. The
legacy `Lgn` SSE transport opens an `EventSource`, parses the `endpoint` event,
and sends requests with a POST to that endpoint. Its EventSource error handler
rejects the current start/auth promise and calls `onerror`; it does not schedule
an automatic reconnect. A 401 can close the EventSource, run the auth-provider
unauthorized callback, and retry the start/auth operation once, but a normal
transport close is only emitted by the explicit `close()` body
(`chunk-6y1jd448.js@314500`, `@315922`).

The modern `StreamableHTTPClientTransport` (`_1t`) keeps a separate resumable
SSE channel. `_startOrAuthSse` combines the transport and request abort signals,
sends `Last-Event-ID` when a resumption token exists, retries 401 through the
auth provider, performs bounded 403 `insufficient_scope` step-up authorization,
and treats HTTP 405 as a terminal request-stream end. Other failed opens raise
`ClientHttpFailedToOpenStream` (`chunk-6y1jd448.js@320500`).

When the stream ends or throws, `_handleSseStream` records the newest event id
and resumption token. If the stream was an initial/resumed channel, a token was
seen, and no terminal response was observed, it calls `_scheduleReconnection`
instead of closing the transport. The default policy is two retries, with
initial delay 1,000 ms, growth factor 1.5, a 30,000 ms cap, and an SSE `retry`
value taking precedence; a supplied scheduler can replace the timer. Abort of
the transport or request suppresses further reconnects. After the retry limit,
the transport reports an error and calls `onRequestStreamEnd`
(`chunk-6y1jd448.js@320500`).

The POST path is coupled to this stream state. A request carrying a resumption
token starts/resumes the SSE channel instead of posting again. A successful
202 response starts an SSE channel when the request shape requires one; an
ordinary JSON or SSE response is delivered to `onmessage`. Its POST signal is
the combined transport/request signal, and an aborted request suppresses the
transport error callback (`chunk-6y1jd448.js@327500`). Therefore recoverable
Streamable HTTP stream drops do not enter the common Client `onclose` settlement
path during the reconnect window; pending RPC rejection is deferred to a
terminal close/end or an eventual response. This last consequence is a
caller/callee control-flow conclusion, not runtime verification.

### WebSocket transport and connection-manager cleanup

The custom WebSocket transport `yQe` is defined in `chunk-tem5x312.js@2933`.
Its constructor waits for the socket to be OPEN, rejects the `opened` promise
on an initial socket error, and installs message/error/close listeners. Message
frames are converted from text and passed through the selected JSON parser;
oversized frames call `handleError()` and then `close()`. Parse failures and
socket errors call `onerror` but do not themselves call `onclose`. A socket
close calls `handleCloseCleanup()`, which calls `onclose` and removes all three
listeners. `close()` itself calls the native socket close when the socket is
OPEN or CONNECTING and then performs the same cleanup immediately; `send()`
rejects when the socket is not OPEN and forwards synchronous native-send
failures through `onerror` (`chunk-tem5x312.js@2933`, `@3539`, `@4021`,
`@4613`, `@4720`).

The connection builder creates this transport for both `ws-ide` and `ws`
configurations (`chunk-9158d2ng.js@79789`, `@80238`). The connected-client
manager replaces the client's error and close callbacks. Its WebSocket error
branch records the drop and forwards the error; unlike SSE/HTTP it does not
enter the transport reconnection ladder. Its close callback removes the live
client and all tool/resource/command listing caches, invalidates MCP skills,
deletes the connection-cache row, and invokes the prior close callback
(`chunk-9158d2ng.js@103774`, `@107057`). The manager cleanup then calls the
client's `close()`; for WebSocket this reaches `yQe.close()`, while the
stdio-only `handOffExitCleanup()` path is not used
(`chunk-9158d2ng.js@107564`, `@108930`). Combined with the common SDK
`Client._onclose()` contract above, an actual WebSocket close rejects pending
RPC responses and then removes the dynamic listing state. An error without a
close is only forwarded and does not, by itself, settle pending RPCs.

### Already-written request settlement

The common v2 call wrapper narrows this boundary further. `ao` records each
request id in `Me` as `sent`, changes it to `taken` when the transport claims
the request, and removes it when an answer arrives
(`chunk-9158d2ng.js@176700`). If the transport closes while such entries are
still present, the catch path refuses to resend the tool call and throws a
correlated `MCP call not sent again after connection closed` error tagged
`downstream_unreachable` (`chunk-9158d2ng.js@182461`). A sent POST that fails
without showing whether the server received it follows the analogous
`MCP call went out and got no answer` branch, also tagged
`downstream_unreachable`. An abort-shaped failure instead returns an interrupted
error result after the wrapper's cleanup. Therefore, for the inspected common
wrapper, server disappearance after the request has been written does not
silently duplicate the call; the unresolved part is how each SDK transport
surfaces its close/abort event into this wrapper.

REA cross-check: an exact literal trace seeded at `MCP call not sent again after
connection closed` returned a partial graph with zero seed matches
(`ev_721246d2f78d0d6c5629893d4f57b837309ca22e190f4839d7193a8d1283970a`). This
is a graph-coverage limitation, not evidence that the source branch is absent;
the direct extracted-module read above remains the authoritative static anchor.

## OAuth and needs-auth boundary

The connection state can become `needs-auth` after reconnect failure. The
authentication flow reuses an active identity-compatible flow and reconnects
only after ownership/policy checks. Credential values were not read or
retained. The relevant remaining question is not credential content but the
pending-call policy while authentication is waiting: the inspected code proves
that future dispatch can wait/fail, but does not establish that an already
sent tool call is cancelled when the server transitions to needs-auth.

## Plugin unload race

Plugin MCP registration is coupled to the plugin lifecycle. On unload, the
plugin-owned server is removed; the function-hook connection wrapper rejects a
connection that completes after unload (`chunk-phacttch.js@1826026`). The
registry also forgets registered tools and removes the associated MCP server
through its owner key (`chunk-phacttch.js@456210`). A tool call already inside a
plugin sandbox has additional lifetime state; the full in-flight unload matrix
is not reconstructed here.

## Registry settlement and live tool-list races

The MCP registry contains an additional stale-settlement barrier beyond the
connection reconnect loop. `mfe` at `chunk-0nh75v9f.js@3225` applies a finished
connection attempt only if a matching app-state or dynamic-store row still
exists. It computes a server/config identity key with `Kn`; if either row now
refers to a different configuration, it closes the late connected client and
returns `"dropped"`. If the attempt epoch has been superseded by an account
switch, it likewise closes the client and returns `"superseded"`. Otherwise it
reconciles disabled/failed policy, updates both app and dynamic stores, removes
the old server's tools/resources, and installs the new client/listing. A
policy-refused result becomes a failed/empty listing and may drop the
discovery entry. The dynamic-store side is reconciled through `se`, which
preserves an already-current client but merges the incoming asked/config
state.

The lower-level re-query path `ne` at `chunk-0nh75v9f.js@13379` applies a
fresh tool list through `PHt`/`Sdn` only while the named server slot still
accepts that client/configuration. If another server has claimed the name it
does not apply the list and emits the explicit “another server holds the name”
diagnostic. For a pending row it retains the result in a `WeakMap` keyed by
the pending client; for an already settled row it removes that temporary
entry. `vDo` exposes this as a store-bound callback.

`kDo` at `chunk-0nh75v9f.js@13974` installs one `tools/list_changed` handler
per connected client using a `WeakSet`, and tracks the newest client with a
`WeakMap`. On a notification it selects the current app/dynamic row only when
its config identity still matches the transport client, merges the current
client state with `ite`, then calls the shared `$ee` list refresh. A failed
refresh with status `kept-previous` leaves the old tool set active and emits a
diagnostic; a successful refresh updates the stores and reports the previous
and new tool counts. A notification synthesized after listen-stream reopen
or received before handler registration is labeled separately, but follows
the same guarded refresh path.

Consequently, a tool disappearing or being replaced while a call is pending
does not by itself prove cancellation of the already-running call: registry
state is protected from stale publication, while the call wrapper's own
abort/close policy determines settlement. The source now proves the
publication side of that race and leaves only the coupling from registry
removal to an in-flight call as `UNKNOWN`.

### Registry settlement versus active-client closure

The complete `mfe` settlement body narrows that coupling. Its local `v()`
helper calls `detachAndCloseConnection(o.client)`, but only on the paths that
drop a late candidate, reject an account-switch-superseded attempt, or refuse
the incoming configuration (`chunk-0nh75v9f.js@3225`). On the normal
`A="applied"` path it updates the app/dynamic stores through `Ofe` and `se`;
there is no call in that body that closes the previously registered active
client merely because its listing or registry row is being replaced. This is
`VERIFIED-STATIC` for the inspected settlement function.

The reconnect path has a different ownership rule. `SDo` receives a transport
close, invokes the current row's `cleanup()`, and only then starts the
reconnect chain; `de` captures the current identity/configuration and rejects
or abandons a candidate that no longer matches the live row
(`chunk-0nh75v9f.js@10400`, `@11641`). Thus an already-running call can be
settled by the transport/client close that initiated reconnect, while a valid
registry publication update alone does not establish an abort edge. The
remaining unknown is specifically any caller outside these inspected cleanup
paths that closes an active client when a server is removed or replaced.

### Removal and replacement callers that do close the active client

The lower-level cache API resolves part of that previously open edge. The
`clearServerCache` implementation first looks up the keyed connection promise;
an already-settled connected result is passed to `qt`, which disables its
`onclose` handler and calls the client's `cleanup()`. An unsettled dial is
instead handed to `Wc`, which marks the dial superseded, removes its discovery
entries, and cleans up a connected result if that dial later settles
(`chunk-9158d2ng.js@116439`, `@116861`). Therefore callers that invoke
`clearServerCache` can settle an in-flight call; callers that invoke only
`dropDiscoveryEntry` cannot be treated as equivalent from this source pass.

The following removal/replacement callers are now source-resolved:

* `uDo`'s configuration reconciliation removes stale or replaced names. For an
  old connected row it first disables the row's `onclose`, awaits the row's
  cleanup, and then clears the keyed cache before removing its tools and row
  (`chunk-exx7q64a.js@14371`, `@16225`, `@16815`). A newly dialed candidate
  whose identity epoch changes is separately closed by `ge`; this is candidate
  disposal, not replacement of the old row.
* The plugin-deduplication branch closes an already connected duplicate plugin
  through `clearServerCache` after disabling its `onclose`, while pending
  duplicates use `disposeServerConnectionDetached`; it then removes the
  duplicate tools, commands, resources, and client row
  (`chunk-416ekshr.js@11144`).
* `FXe.applyQueuedUpdates` uses helper `v` for late policy/ownership results;
  `v` disables the row `onclose` handler and invokes `clearServerCache`. The
  same method directly calls `detachAndCloseConnection` for an identity-stale
  connected result and for a replace-only config mismatch
  (`chunk-bpav708b.js@1415`, `@4214`).
* The MCP management hook's disable operation calls `clearServerCache` for a
  connected server before publishing the disabled row, while a cached-only row
  uses `disposeServerConnectionDetached` (`chunk-9w4htdvs.js@1580387`,
  `@1586900`).
* The authentication panel's “clear credentials” action drops discovery state,
  then calls `clearServerCache` when the identity epoch has not changed, and
  finally publishes a failed row and removes the server's tool surfaces
  (`chunk-t680wpqf.js@105271`).

These are `VERIFIED-STATIC` closure edges. They narrow the former gap from
“removal/replacement may not close an active client” to “all callers outside
the inspected cache, reconciliation, plugin, queued-update, management, and
authentication paths remain unresolved.”

## Registry caller enumeration

The exact literal-token pass over every extracted `chunk-*.js` file found six
direct consumers of `mfe` beyond its definition, two direct consumers of the
MCP `ne` updater, two consumers of the local `pi` wrapper, and one `kDo`
registration call. The following are verified static edges; offsets identify
the call expression or setup site, not merely an import occurrence.

| Callee | Caller and context | Anchor | Observed behavior | Confidence |
|---|---|---|---|---|
| `mfe` | `Rln` account-switch re-dial callback | `chunk-0nh75v9f.js@7555` | settles each re-dial result through the registry barrier; failures are logged by the surrounding async chain | VERIFIED-STATIC |
| `mfe` | `de` transport-close reconnect loop | `chunk-0nh75v9f.js@10400` | publishes pending/reconnected/failed states only while the row and attempt remain current | VERIFIED-STATIC |
| `ne` | `SDo` kept-connection refresh | `chunk-0nh75v9f.js@12046` | re-queries tools after a kept connection and reports refresh failure without replacing the client | VERIFIED-STATIC |
| `ne` | `kDo` `tools/list_changed` handler | `chunk-0nh75v9f.js@14776` | applies a guarded refreshed list for the current client/config | VERIFIED-STATIC |
| `mfe` | bridge server-config meta mount `L` | `chunk-2pkntkhf.js@23047` | applies the reply mount or closes/drops the late connected client according to the settlement result | VERIFIED-STATIC |
| `mfe` | generic reconnect controller `tT` | `chunk-fzzrkchm.js@382970` | wraps cached-adopt, retry, and needs-auth settlement with the same registry result states | VERIFIED-STATIC |
| `mfe` | local `pi` wrapper definition | `chunk-fzzrkchm.js@504690` | binds the shared `Fr` app/dynamic stores and forwards `(name, result)` to `mfe` | VERIFIED-STATIC |
| `pi` | `Zi` reconnect-result normalizer | `chunk-fzzrkchm.js@506239` | uses `applied`, `superseded`, and `dropped` to choose the returned client shape | VERIFIED-STATIC |
| `pi` | `Xd` needs-auth re-adoption | `chunk-fzzrkchm.js@508488` | publishes a newly fetched listing only after epoch, identity, and row checks | VERIFIED-STATIC |
| `kDo` | MCP lifecycle setup | `chunk-fzzrkchm.js@509441` | creates the shared connected-client/list-change registration callback with `Fr` stores and `storageV5` | VERIFIED-STATIC |
| `mfe` | bridge projects reply mount `N` | `chunk-td0hhs53.js@3801` | applies or retracts the project reply mount, then reports retryable versus terminal failure | VERIFIED-STATIC |
| `clearServerCache` | `qt` settled-client cleanup / `Wc` pending-dial disposal | `chunk-9158d2ng.js@116439`, `@116861` | closes a settled connected client or supersedes a pending dial, then removes keyed discovery state | VERIFIED-STATIC |
| `uDo` configuration reconciliation | `clearServerCache` after old-row cleanup | `chunk-exx7q64a.js@14371`, `@16815` | closes stale/replaced connected rows before removing their surfaces | VERIFIED-STATIC |
| plugin deduplication | `clearServerCache` for connected duplicate | `chunk-416ekshr.js@11144` | disables close callback, closes duplicate client, removes duplicate plugin surfaces | VERIFIED-STATIC |
| `FXe.applyQueuedUpdates` | helper `v` / direct `detachAndCloseConnection` | `chunk-bpav708b.js@1415`, `@4214` | closes late ownership/policy results and identity-stale candidates | VERIFIED-STATIC |
| MCP management disable | `clearServerCache` | `chunk-9w4htdvs.js@1580387`, `@1586900` | closes connected server before publishing disabled state | VERIFIED-STATIC |
| authentication “clear credentials” | `clearServerCache` | `chunk-t680wpqf.js@105271` | closes the unchanged-epoch client before publishing failed state | VERIFIED-STATIC |

The literal `mfe` pass covered all `chunk-*.js` files and returned only its
definition plus the six call expressions listed above. The `ne` name is common
in the bundle and is also imported for unrelated helpers in other modules, so
only the two calls inside the defining MCP module are asserted for this
callee. Imported aliases, registry callbacks reached through string dispatch,
and host/native injection remain outside this bounded static result.

## Permission and subagent interaction

After a dynamic MCP tool resolves, it enters the same `Qj`/`RWo` validation,
hook, permission, and cancellation path as built-in tools
(`chunk-phacttch.js@2268196`). MCP metadata can alter the displayed permission
card and always-allow policy, but discovery does not grant permission. A
subagent's tool context still governs the call; the global set of dynamic
subagent callers is addressed by report 07 and remains partial.

## Race state machine

```text
configured
  -> pending
       -> connected + listing -> active tools
       -> failed / needs-auth
       -> removed / plugin unloaded

model tool call
  -> generation/owner check
       valid -> pending wait if needed -> Qj permission/hooks/call
       stale -> correlated unknown/error result

connected client
  -> tools/list_changed
       same identity/config -> refresh and publish
       replaced/stale -> discard refresh
       list failure -> keep previous listing or mark failure

reconnect candidate
  -> still current + healthy -> publish
  -> stop/config change/stale -> close candidate, do not publish
```

## Confidence ledger

| Finding | Confidence | Anchor |
|---|---|---|
| Supported transport schema and normalization | VERIFIED-STATIC | `chunk-ff982hys.js@58847` |
| Deferred discovery waits abort-aware for pending MCP state | VERIFIED-STATIC | `chunk-phacttch.js@937427` |
| Dispatch performs pending wait/refresh and correlated unknown-tool result | VERIFIED-STATIC | `chunk-phacttch.js@2268196` |
| Plugin connection join rejects unload-after-connect | VERIFIED-STATIC | `chunk-phacttch.js@1826026` |
| Tool aliases and generation/owner checks are enforced | VERIFIED-STATIC | `chunk-phacttch.js@456210` |
| Reconnect candidates are epoch/currentness checked before publication | VERIFIED-STATIC | `chunk-0nh75v9f.js@11641` |
| Automatic reconnect limit, overlap suppression, jittered delay, and slow background retry phase | VERIFIED-STATIC | `chunk-0nh75v9f.js@11641` |
| A stale `tools/list_changed` result cannot overwrite a replaced server | VERIFIED-STATIC | `chunk-0nh75v9f.js@11641` |
| Caller abort/overall timeout/idle watchdog terminate an MCP call attempt | VERIFIED-STATIC | `chunk-9158d2ng.js@175589`, `@182461` |
| Task-capable MCP calls send `tasks/cancel` after abort | VERIFIED-STATIC | `chunk-9158d2ng.js@176700` |
| Stdio child cleanup escalates SIGTERM to SIGKILL | VERIFIED-STATIC | `chunk-9158d2ng.js@21315`, `@21768` |
| Stdio close/dispose timing and stream cleanup | VERIFIED-STATIC | `chunk-9158d2ng.js@19308`, `@20196` |
| Unconnected stdio-child exit reaper and platform escalation | VERIFIED-STATIC | `chunk-9158d2ng.js@26410`; `chunk-tem5x312.js@6146`, `@6251`, `@6379`, `@6840` |
| SDK transport-close settlement rejects pending calls | VERIFIED-STATIC | `chunk-6y1jd448.js@100162`, `@100736`, `@101233` |
| SSE and Streamable HTTP close/abort wiring | VERIFIED-STATIC | `chunk-6y1jd448.js@315922`, `@319109`, `@320990`, `@328757`, `@328935` |
| WebSocket message/error/close behavior | VERIFIED-STATIC | `chunk-tem5x312.js@2933`, `@3539`, `@4021`, `@4613`, `@4720` |
| Legacy SSE has explicit-close/onerror behavior and no transport-level reconnect loop | VERIFIED-STATIC | `chunk-6y1jd448.js@314500`, `@315922` |
| Streamable HTTP resumable SSE auth, retry, token, and terminal-end policy | VERIFIED-STATIC | `chunk-6y1jd448.js@320500` |
| Streamable HTTP POST/resumption/202 promotion and combined abort behavior | VERIFIED-STATIC | `chunk-6y1jd448.js@327500` |
| Recoverable Streamable HTTP drops bypass common `onclose` until terminal end | INFERRED | `chunk-6y1jd448.js@320500`, `@327500`; common client `@100736` |
| WebSocket construction and connection-cache cleanup | VERIFIED-STATIC | `chunk-9158d2ng.js@79789`, `@80238`, `@103774`, `@107057`, `@107564`, `@108930` |
| Already-written v2 calls are not resent after close/no-answer | VERIFIED-STATIC | `chunk-9158d2ng.js@176700`, `@182461` |
| Late connection settlements are dropped on config mismatch or account-switch epoch supersession | VERIFIED-STATIC | `chunk-0nh75v9f.js@3225` |
| Applied registry settlement updates stores without directly closing the prior active client in `mfe` | VERIFIED-STATIC (scoped) | `chunk-0nh75v9f.js@3225` |
| Transport-close reconnect starts from row cleanup and current identity/configuration checks | VERIFIED-STATIC | `chunk-0nh75v9f.js@10400`, `@11641` |
| `clearServerCache` closes a settled connected client through `qt.cleanup()` and disposes an unsettled dial through `Wc` | VERIFIED-STATIC | `chunk-9158d2ng.js@116439`, `@116861` |
| Configuration reconciliation closes stale/replaced connected rows before removing their surfaces | VERIFIED-STATIC | `chunk-exx7q64a.js@14371`, `@16815` |
| Plugin deduplication, queued updates, management disable, and authentication clear reach active-client closure | VERIFIED-STATIC | `chunk-416ekshr.js@11144`; `chunk-bpav708b.js@1415`, `@4214`; `chunk-9w4htdvs.js@1580387`, `@1586900`; `chunk-t680wpqf.js@105271` |
| Re-queried tool lists cannot overwrite a server-name slot claimed by another server | VERIFIED-STATIC | `chunk-0nh75v9f.js@13379` |
| `tools/list_changed` handlers are one-per-client, config-guarded, and keep the previous listing on refresh failure | VERIFIED-STATIC | `chunk-0nh75v9f.js@13974` |
| Tool disappearance always actively cancels a call before dispatch | UNKNOWN | registry disappearance is proven; pre-dispatch coupling remains open |

## Open gaps

1. Streamable HTTP retry/resumption and legacy SSE behavior are now recovered;
   native EventSource/WebSocket timing and host transport scheduling remain
   runtime-dependent. The exact server-side meaning of replayed messages and
   response retention across a reconnect is still outside the bundle.
2. The common SDK pending-handler settlement is recovered, but plugin unload
   still lacks a complete proof that every in-flight SDK client is closed and
   every dynamic call reaches that settlement path.
3. Whether cached listings are canonical for a specific session mode.
4. Complete dynamic caller graph for MCP tools and ToolSearch; the direct
   registry-token callers are now enumerated, but aliased, string-dispatched,
   and host/provider callers remain open.
5. Native WebSocket close timing and any host/runtime behavior not visible
   through the custom transport and common SDK `Client` adapter.
6. Removal/replacement callers outside the inspected `clearServerCache`,
   `uDo`, plugin-deduplication, `FXe.applyQueuedUpdates`, management-disable,
   authentication-clear, `mfe`, `SDo`, and `de` paths; the remaining dynamic
   registry/provider/host callers may still close active clients and settle
   in-flight calls.
