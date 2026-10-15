# Local interactive permission UI

Status: `PARTIAL` — the local request lifecycle, dialog transport, shared dialog
store, terminal transport adapter, and shared selector's keyboard/focus
primitive are `VERIFIED-STATIC`; cross-kind arbitration, dynamic panel bodies,
and several cross-process races remain unresolved.

## Entry and dialog selection

The permission engine reaches the local ask path after rule, hook, classifier,
and mode evaluation. The dispatcher `lBt` at `chunk-57pw7ky5.js@47087` selects
a specialized dialog descriptor when the tool matches a known tool, a file or
sed preview, workflow/plugin/plan dialog, or another registered dialog kind.
Otherwise it builds the general tool-use descriptor. The dispatcher's
`requestDialog` comes from the current `toolUseContext`; if it is absent, the
local UI path has no surface to mount and the caller must resolve through its
non-UI policy.

The selection body also demonstrates that dynamic tools do not automatically
bypass permission UI. The generic descriptor uses `tool.isMcp`, MCP metadata,
the tool's user-facing renderer, permission decision reason, and optional
permission-card data. Specialized plugin/workflow/MCP surfaces are selected by
the same dispatcher rather than by a separate allow path.

## Per-request state

`Ie` at `chunk-57pw7ky5.js@51135` is the common local dialog lifecycle. It
receives the current request record, descriptor builder, bridge callbacks,
channel callbacks, and a resolve-once object. Its important state is:

```text
resolved / claimed request
tool-use id and assistant message id
original and possibly hook-rewritten input
current permission result and decision reason
dialog abort controller
dialog sequence/order number
reprompt count
latest descriptor / streamed descriptor updates
teardown callbacks
auto-deny deadline and timer
```

The function records an attribution increment and emits the permission-display
telemetry exactly once through `V`. It then opens the ask registry with
`eS.openAsk`, including a display description and `toolUseID`. The sequence
number comes from the session-host counter `Gt`; the request is placed under
another person-only prompt, on top for the external-racer case, or in the
normal queue. This is a real queue policy, not merely a renderer hint.

## Dialog construction and updates

`Ie` calls `n.buildDescriptor({input, permissionResult})`. The descriptor can
be a value or an async generator. It converts generator updates into a small
internal stream: the first consumer receives the current descriptor, later
updates are delivered to a waiting resolver or buffered in `mo`, and abort
closes the stream. The selected dialog receives:

```text
dialog descriptor/stream
AbortSignal for this request
place: under | queue | default
askOrder
armInputGrace
onFirstReveal
countedAsk when the dialog kind supports it
```

This explains why file/sed permission previews can be rebuilt after a hook
rewrite without treating the old preview as authoritative. The caller keeps a
reprompt count, rebuilds the descriptor, and aborts the old descriptor stream.
If a rewritten input can no longer be safely previewed, the caller cancels and
aborts rather than executing a stale preview (`chunk-57pw7ky5.js@45577`).

## Completion and decision mapping

The dialog promise resolves to one of `allow`, `deny`, or `cancelled`. The
common completion function first clears hook-failure and ask-registry state,
tears down subscriptions, and then:

### Allow

It stops any auto-deny fallback, forwards updated permissions to the bridge,
records an acceptance event, and calls `handleUserAllow`. The result can carry
rewritten input, permission updates, feedback/content blocks, a decision reason,
and the matched ask rule. The user-approved input is what proceeds to tool
execution.

### Deny

It forwards denial feedback, records a user-reject decision, and may return a
new `ask` result when the request ended or when a special outside-read flow
requires another question. For an outside-read decision, the user can block
future outside reads, ask again next time, allow once, or allow persistently;
the resulting setting update is handled asynchronously before the final
permission result is resolved.

### Cancelled

It records user abort, sends `User aborted` to the bridge, and either returns an
ask-again result for an ended/remote race or calls `cancelAndAbort` for the
active tool. This is distinct from an ordinary deny and is retained in the
tool-decision classification.

The result mapping and teardown are in `chunk-57pw7ky5.js@51135`. The broader
decision persistence is a separate finalization layer, not just a renderer
return value:

* `$Fo` at `chunk-phacttch.js@1880701` maps bridge outcomes into the canonical
  decision/source pair. A host `allow` becomes `accept` with a user source and
  may carry a permanent classification or updated-permissions destination; a
  host deny becomes `reject` with `user_reject` and feedback state. A turn
  abort is `user_abort`. Hook allow/deny is classified as a hook decision, and
  a recheck is accepted as a config decision.
* `vCn` at `chunk-phacttch.js@1881636` records the recheck/classifier timing and
  routes the mapped result to the accept or reject telemetry path. This is
  evidence that recheck decisions are observed separately from user answers;
  it does not prove that every recheck changes persistent permission rules.
* `JQo` at `chunk-phacttch.js@1881907` is the final decision recorder. It calls
  the accept/reject telemetry helpers, normalizes the source classification,
  updates special permission state asynchronously for the matching tool class,
  stores `{source, decision, timestamp, ...surface}` by `toolUseID`, and emits
  a `tool_decision` event containing the normalized tool name, tool-use id,
  MCP metadata when present, and tool parameters. Thus the decision is
  correlated after the local dialog has settled rather than inferred from UI
  state later.

These bodies are `VERIFIED-STATIC`; the earlier broad description was too
coarse and has been replaced with the defining offsets above.

## Worker/remote permission transport boundary

The permission path also has a transport dispatcher that is distinct from the
terminal store. `kF` at `chunk-9w4htdvs.js@218600` and its continuation at
`chunk-9w4htdvs.js@220300` handle `can_use_tool` requests arriving over the
host/worker/remote transport:

```text
validate subtype and request_id
  -> validate request payload (malformed => deny response)
  -> deduplicate request_id in inFlight
  -> build permission descriptor and permission-result context
  -> requestDialog(descriptor, { place: "under", signal, ...flags })
  -> atomically remove inFlight entry
  -> allow => send updated input/permissions
     deny => send feedback/content blocks and optional interrupt
     cancel => send user/background abort denial and optional interrupt
  -> transport error => send explicit failure denial
```

The descriptor includes the tool, input, description, tool-use id, subagent
request source when applicable, assistant message, permission behavior and
decision reason, matched ask rule, blocked path, suppression/default-to-no
flags, theme, permission context, remote-workspace data, held-call state, and
an abort signal. A cancellation request aborts the matching in-flight dialog;
`drain()` aborts all remaining requests and sends the explicit
`Permission dispatcher unmounted` denial. Late replies cannot be applied after
the in-flight entry has been removed. This transport body proves request
validation, deduplication, response construction, and teardown, but it does
not identify the terminal panel that ultimately receives every request.

## Concrete default permission renderer

The default local approval dialog is a distinct path from `local_jsx`. Its
typed request contract is `HAe` at `chunk-cvvnq4he.js@478598`: kind
`permission_prompt`, payload validation requires `requestId`, `toolName`, and
`permissionResult`, the result requires a `behavior`, and the default result is
`{behavior:"cancelled"}`. `QO` at `chunk-57pw7ky5.js@13560` builds this
descriptor from the tool, input, MCP metadata, rendered tool-use text,
permission result, card data, and assistant message id. `lBt` selects `HAe`
for the generic path at `chunk-57pw7ky5.js@47087`; specialized tool matches
use their own dialog kind and descriptor builder before falling back to it.

The defining default panel is `pMr` at `chunk-bqb9mv4b.js@54618`. It renders
the tool description and input/card preview, then constructs the option set
from the permission result:

```text
defaultToNo       -> No is initially selected and placed first
normal ask        -> Yes and No are offered
showAlwaysAllow   -> Yes, and don't ask again (when rule display is safe)
workflow/auto     -> Yes, enable auto mode (when the request source permits it)
cancel            -> cancelled result
```

`Ko` at `chunk-bqb9mv4b.js@53100` maps those values to allow, deny, or
allow-with-`permissionUpdates`; `yes-dont-ask-again` only carries updates when
the proposed rule passes `Kw`. `pMr` passes the options, default focus, and
answer/cancel callbacks to `L9` at `chunk-bqb9mv4b.js@37769`. `L9` converts
feedback-configured choices into inline input rows, trims and attaches accept
or reject feedback, refuses to settle when the transport's
`wouldTakeAnswer()` gate returns false, and invokes `onCancel` for Escape.

The input/focus details are not merely renderer assumptions. `Uwe` at
`chunk-bqb9mv4b.js@35151` tracks accept/reject feedback text, toggles feedback
mode, exposes a Tab hint when amendment is available, logs submission, and
maps Escape to the dialog cancel action. The shared selector `Ve`/`Yi` at
`chunk-75p1g95y.js@40861` installs the focusable container, keyboard handler,
focused/selected option styling, mouse selection, input-row submission, and
cancel path. The `nE` refusal wrapper at `chunk-rcjkw193.js@672` counts refused
answers and temporarily records the refused option so the panel can choose a
new default focus; `pMr` derives the initial focus from `defaultToNo` and that
refusal state.

This resolves the generic interactive approval state machine. Specialized
dialogs (file/sed previews, web fetch, workflow, sandbox, and other registered
kinds) still have separate component bodies and may add choices or races; they
are not silently treated as instances of `pMr`.

### Shared selector focus and keyboard state machine

The previously broad focus gap can be narrowed. `Ve` at
`chunk-75p1g95y.js@40861` selects the accessibility-context implementation
`G9` when `nt()` observes `InternalAccessibilityContext`, and otherwise uses
the ink/terminal implementation `Yi`. `c3n` is the
`InternalAccessibilityContext` at `chunk-v44rfc3q.js@184129`. The terminal
path is not a passive renderer:

* `HYn` at `chunk-75p1g95y.js@38136` builds the option map and visible window,
  chooses `defaultFocusValue` (falling back to the first option), and exposes
  next/previous/page/set-focus transitions. `Di` at `@39814` keeps committed
  selection separate from `focusedValue`; `selectFocusedOption` commits the
  current focus and calls the supplied change handler.
* `Ci` at `chunk-75p1g95y.js@31583` installs the `Select` keybindings and
  returns `handleKeyDown`. It handles next/previous/first/last/accept/cancel,
  page movement, input-row navigation, multi-select space, and numeric
  selection. Boundary callbacks can hand movement back to the surrounding
  panel, so focus does not necessarily wrap inside the selector.
* `Yi` keeps `hasInkFocus` in state, attaches `tabIndex`, `onKeyDown`,
  `onFocus`, and `onBlur` to the container, and applies disabled/selection
  gates before a click can focus or commit an option (`@41200`–`@44000`).
  `Fh` at `chunk-pb1e761e.js@21952` focuses the container and reclaims focus
  if the terminal active element moves outside it; the hook blurs it when
  disabled.
* `cb` at `chunk-cn7dpt66.js@957` drops activation/mount-settle stray clicks,
  while `zmt` at `@1312` supplies the short timing predicate used by the
  wheel/scroll guard. These are input-race guards, not permission decisions.

This is `VERIFIED-STATIC` for the shared selector primitive. It does not prove
that every specialized or dynamically supplied panel mounts this selector, or
that a queued request cannot be replaced by a different dialog kind before
the host selects it.

### File-operation specialized branch

One major specialized branch is also statically recoverable. `iWe` at
`chunk-57pw7ky5.js@22460` defines the `permission_file` contract with
`filePath` and `operationType` in addition to the common request fields. Its
renderer `ort` at `chunk-9w4htdvs.js@1251327` builds a file/diff preview via
`cho`, adds symlink warnings, and chooses the options through `Ont`.

`Ont` at `chunk-9w4htdvs.js@1241629` makes the file-specific policy visible:
it can offer accept-once, block-outside-reads, a session/directory grant,
reject, and allow-outside-read-once. Input-mode flags add inline feedback
editing. `lho` at `chunk-9w4htdvs.js@1249278` maps those options to allow,
deny, `permissionUpdates`, `blockOutsideReads`, and `askAgainOutsideReads`.
The renderer passes the resulting option list to the same `Ve` selector and
shares `Uwe` feedback state, so file approval is a specialized preview and
policy branch—not a separate transport or settlement mechanism.

The source also records branch guards: classifier or organization caps can
veto standing grants, a directory-only grant is distinct from a general
session grant, and `offersBlockOutsideReads` changes both labels and result
mapping. The remaining specialized bodies are enumerated in the component
registry but are not yet read to the same function-level depth.

### Bash, browser, and plan-mode registered panels

The central registry is now resolved for three additional permission kinds.
`Yke` at `chunk-9w4htdvs.js@1293453` maps the bash kind `ZJe` to `Jtt`, the
Chrome/browser kind `eBt` to `Ywe`, and the plan-entry kind `tBt` to `oke`.
This is a registry edge, not an inference from similarly named components:
the same object also maps the previously traced generic, file, web-fetch,
skill, PowerShell, and monitor descriptors to their renderer functions.

`Jtt` at `chunk-9w4htdvs.js@1200505` is the bash approval panel. It bounds or
withholds the command display, parses the command for a standing-prefix
suggestion, computes remote-machine and sandbox state, optionally shows a
destructive-command warning, and supplies backend permission suggestions.
`ztt` constructs the choices: allow once, an editable or backend-suggestion
grant when its gates pass, optional auto-mode enablement, and reject. `Yj`
maps allow, suggestion, edited-prefix, auto-mode, and deny values into the
common decision shape. Escape invokes the panel's `onCancel` callback, which
returns `{behavior:"deny"}`. The panel still uses `Ve` and `Uwe` for focus,
feedback, and selection, so its specialization is policy/display logic over
the common settlement path.

`Ywe` at `chunk-9w4htdvs.js@1206666` is the Chrome/browser panel. It
display-limits the URL, preserves a withheld marker instead of exposing the
URL, renders the requested verb and host, and can offer a session-scoped
host rule through `Ztt`. `Xtt` maps allow, allow-domain, and deny choices;
the allow-domain choice is only added by `eot` when the request is eligible
and the host is not wildcard/withheld. Escape returns
`{behavior:"cancelled"}` rather than deny. This is a distinct registered
panel from the web-fetch `Vke` branch.

`oke` at `chunk-9w4htdvs.js@1216982` is the enter-plan-mode approval panel.
It tracks the refusal epoch and remount key, suppresses stale answers when
the request is no longer answerable, and checks `wouldTakeAnswer()` before
settling. A yes answer records `tengu_plan_enter` with `entryMethod:"tool"`,
updates the permission mode to `plan` through `Zpe`, and maps through `fot`;
no maps to deny. The panel explicitly explains that it will explore the
codebase, identify patterns, design a strategy, present it for approval, and
make no code changes until approval. Its cancel label is “No, start
implementing now”; the generic refused-answer state remains active through
the shared `ms()`/`or` machinery.

These three panels close the previously registry-only branches at the
function-body level. They do not prove that every possible focus transition,
host approval race, or dynamically supplied `local_jsx` node is serialized
the same way as the common terminal selector.

### Web-fetch specialized branch

The web-fetch request has its own typed contract rather than using the generic
`permission_prompt`. `iBt` at `chunk-57pw7ky5.js@33506` requires the common
request fields plus `requestId`, `toolName`, `permissionResult`, and
`hostname`; its result carries a `behavior`, with cancellation as the default.
The `lBt` dispatcher selects this descriptor for the web-fetch family at
`chunk-57pw7ky5.js@47087`.

The registered panel is `Vke` at `chunk-9w4htdvs.js@1283914`, and the common
dialog registry maps `iBt` to it at `chunk-9w4htdvs.js@1292672`. The renderer
canonicalizes and display-limits the URL, marks withheld URLs without exposing
their full text, displays the request description and optional prompt, and
renders the permission result before the choice selector. It offers `Yes`, an
optional domain-scoped standing grant, and `No, and tell Claude what to do
differently (esc)`; Escape resolves `{behavior:"cancelled"}`.

The result mapper `qrt` at `chunk-9w4htdvs.js@1282875` returns allow with the
original `input` for `yes`, deny for `no`, and allow with the proposed
`permissionUpdates` for `yes-dont-ask-again-domain` only when the proposed
rule passes `Kw`. `$rt` at `chunk-9w4htdvs.js@1283167` constructs the displayed
`domain:<hostname>` local-settings rule. `Qrt` at
`chunk-9w4htdvs.js@1283713` suppresses that option for a non-approvable safety
decision, an organization ask cap, an empty/wildcard hostname, or a withheld
URL. The selector is the shared `Ve` component used by the generic and file
branches; the web-fetch panel therefore changes the descriptor, display, and
domain-rule policy but not the underlying transport settlement path.

### Skill-use specialized branch

Skill approval has a separate `permission_skill` contract. `sBt` at
`chunk-57pw7ky5.js@33238` requires the common request fields plus `skill`; the
result carries `behavior` and defaults to cancellation. The component registry
maps this kind to `Wke` at `chunk-9w4htdvs.js@1292672`, whose renderer is
defined at `chunk-9w4htdvs.js@1280237`.

`Wke` displays the skill name/description and permission result, then builds a
shared `L9` choice list: `Yes`, optionally `Yes, and don't ask again` for the
exact skill, optionally a prefix-scoped standing grant, and `No`. Both accept
and reject choices enable their corresponding feedback input. Escape/cancel
calls the answer with `{behavior:"deny"}`, so this specialized panel treats
dismissal as denial rather than the generic renderer's explicit cancelled
result.

The result mapper `Mrt` at `chunk-9w4htdvs.js@1278093` returns allow with the
original input for `yes`, deny for `no`, and allow plus `permissionUpdates` for
the exact or prefix grant only when the proposed row passes `Kw`; optional
feedback is attached to allow/deny results. `Irt` at
`chunk-9w4htdvs.js@1278805` constructs the exact skill rule. `Urt` at
`chunk-9w4htdvs.js@1278625` extracts a prefix only from the first space-delimited
segment and rejects empty, wildcard, or colon-containing prefixes; `Ert` at
`chunk-9w4htdvs.js@1279317` constructs the `${prefix}:*` rule. `Wrt`, `Drt`,
and `Ort` at `chunk-9w4htdvs.js@1279923`, `@1280080`, and `@1280174` gate the
standing-grant offers on `showAlwaysAllow`, classifier approvability,
organization ask caps, nonempty/nonalready-wildcard skill text, and valid
prefix syntax. This is a policy specialization over the common dialog
transport, not a separate permission settlement path.

### PowerShell command specialized branch

PowerShell approval has a `permission_powershell` contract. `oBt` at
`chunk-57pw7ky5.js@32959` requires the common request fields plus `command`,
and defaults to a cancelled result. The registry maps this kind to `Trt` at
`chunk-9w4htdvs.js@1292672`, whose full renderer is at
`chunk-9w4htdvs.js@1271495`.

`Trt` performs more than display formatting before showing the shared selector:
it bounds/withholds oversized command text, asynchronously parses the command
with `Crt` to refine a suggested prefix, computes sandbox applicability for
PowerShell, renders a destructive-command warning when enabled, and passes
network allow-hosts and permission suggestions into the command panel. Its
option construction is `krt` at `chunk-9w4htdvs.js@1267767`: the normal `Yes`
choice can be followed by an editable prefix grant or backend-suggestion grant
when the standing-grant gate allows it, followed by `No`; both accept and
reject options may be inline feedback inputs.

The result mapper `p6` at `chunk-9w4htdvs.js@1270916` maps `yes` to allow with
the original input and optional feedback, `yes-apply-suggestions` to allow plus
validated permission updates, and `yes-prefix-edited` to allow plus updates
from `Jqn` only when the edited prefix is valid. `no` is deny with optional
feedback. The renderer's cancel callback also returns `{behavior:"deny"}`
(`chunk-9w4htdvs.js@1271495`), so this command family treats Escape as a
denial, not as the generic/web-fetch cancelled result. The command-specific
branch therefore combines safety/sandbox/display work with the same final
permission transport and shared focus/feedback component.

### Monitor/WebSocket specialized branch

The `permission_monitor` contract is `rBt` at
`chunk-57pw7ky5.js@32680`; in addition to common permission fields it requires
`intervalMs` and defaults to cancellation. The registry maps it to `Fke` at
`chunk-9w4htdvs.js@1292672`, defined at `chunk-9w4htdvs.js@1260316`.

`Fke` supports three monitored action shapes: a shell command, an MCP server
and tool polled at `intervalMs`, or a WebSocket URL with visible or withheld
subprotocols. It displays the monitor description, action details, network
allow-hosts, and the permission result. Its normal options are `Yes` and `No`
with accept/reject feedback; an optional `Yes, apply suggestions` row is
inserted only when standing grants are permitted. Withheld command arguments,
WebSocket URLs, or MCP arguments are shown through markers rather than full
content, and withheld WebSocket subprotocols produce an explicit warning.

`mrt` at `chunk-9w4htdvs.js@1258368` maps `yes` to allow with the original
input and optional feedback, `yes-apply-suggestions` to allow plus validated
permission updates, and `no` to deny with optional feedback. Escape returns
`{behavior:"deny"}`. `prt` at `chunk-9w4htdvs.js@1259097` constructs the
combined rule/directory suggestion row with bounded counts; `frt` at
`chunk-9w4htdvs.js@1259921` rejects standing grants for non-approvable safety
decisions or organization ask caps, while `grt` at
`chunk-9w4htdvs.js@1260091` suppresses them for withheld or missing action
data. This branch shares the common selector/feedback and settlement path but
adds action-shape-specific disclosure and standing-grant guards.

## Request transport and terminal consumer

The local request surface is not a direct renderer callback. `AV` constructs a
per-session dialog transport with `vEe()` and adapts it to the typed dialog
request function `mCs()` (`chunk-9w4htdvs.js@173347`; `chunk-s46d15s3.js@2725`).
`vEe` allocates monotonically increasing `dialog-N` ids, stores one resolver per
request, rejects immediately when its signal is already aborted or there are no
subscribers, emits the request descriptor, and exposes separate cancellation
and descriptor-update channels. An abort removes the resolver, resolves the
request as `{cancelled:true}`, and emits the request id on the cancellation
channel. `reply` is ignored after the resolver has been removed, so a late
answer cannot settle a second time. `mCs` validates the descriptor with the
dialog schema, awaits the transport reply, maps cancellation or invalid result
payloads to the dialog's default, and additionally supports an async-generator
descriptor whose later values are forwarded through `update` until abort or
completion.

The terminal adapter is `HO` at `chunk-9w4htdvs.js@1326466`. It subscribes the
transport to the shared dialog store, maps transport cancellation to
`dismiss`, forwards descriptor updates only for ids currently opened by that
transport, and listens for store closure. An answered store entry calls
`transport.reply({id,result})`; any other closure replies with cancellation.
Unmount cleanup unsubscribes all four channels, dismisses still-open entries,
and replies cancelled for each one. This establishes a concrete local
renderer boundary; the remaining dynamic portion is the arbitrary
`local_jsx` node supplied by the producer and the cross-process host race.

The shared store is `PLr` at `chunk-gq0v7nj7.js@1100`. It maintains `open`, an
ask tally, closed-request notifications, reveal markers, and placement
metadata. `open` inserts a queued request using `askOrder`, otherwise promotes
`place:"under"` requests ahead of non-user prompts; a blocking top request can
hold its position unless the new request succeeds. It marks a request as
shown when it is behind another same-class request or when an idle grace rule
applies. `update` replaces the payload and refreshes `shownAt`; `answer` and
`dismiss` remove the request and emit an `onClosed` event; removal reveals the
next same-class request and increments its reveal sequence. The helper `v` at
`chunk-gq0v7nj7.js@2747` performs that promotion and records whether the
blocking top bare dialog was closed. Thus the source proves queue insertion
and promotion semantics, but not keyboard focus or the implementation of each
specialized panel.

The store's visible selectors are also explicit: `ik` returns the last open
non-user-invoked dialog, while `Sie` returns the last user-invoked dialog. The
`PLr` subscription compares both selectors and emits a UI update only when one
of those visible references changes. After `v` removes a top same-class entry,
the predecessor is marked with a fresh `shownAt` and incremented `revealSeq`
before publication (`chunk-gq0v7nj7.js@1100`, `@2747`). This proves reactive
visible-block promotion and separates it from the later terminal component's
keyboard-focus behavior. REA's property trace for `closedBlockingTopBare`
returned a partial graph with zero matches
(`ev_ece799b26112ebfed5071182c776933afe1ba05ae932dcec09dd95264e597274`), so
the direct bundle read remains authoritative.

### Display-host arbitration and stale-answer rejection

The terminal host adds a second arbitration layer above the store. `PA` and
`A6` at `chunk-9w4htdvs.js@1291712` and `@1291863` expose whether a
user-invoked dialog is present and whether a non-user dialog is eligible to
remain visible. `I6` at `@1292189` treats a user-invoked request, or the
currently selected non-user request, as modal only when the registered
component metadata classifies it as `modal`; `Lst` at `@1292512` applies the
same test to the store's latest non-user and user-invoked selectors.

The renderer host `_v` at `chunk-9w4htdvs.js@1320735` chooses the actual
request for the current surface/variant. A user-invoked request wins when it
matches the surface; otherwise the latest eligible non-user request is used.
`nCe` at `@1322913` converts prompt state (`panel`, `progress`, `draft`,
`typing`) into a hidden request and reason. `rCe` at `@1323202` builds the
buried non-user list: if any user-invoked request exists it returns no buried
non-user panels, otherwise it excludes the selected request, the hidden
request, and the current host request. Thus background permission/suggestion
cards are retained in the store but are not mounted over an active user
dialog.

`sCe` at `@1323852` tracks host display/displacement timestamps. A user
dialog is treated as displaced when it is no longer the most recently shown
request, and an idle transition or draft transition updates the timestamp
used by the host. The renderer then uses `iCe` at `@1324180` as a
resolve-once display gate: it verifies that the request id still exists and
that the payload is unchanged, computes `wouldTakeAnswer` from the host's
current reveal/age gate, dismisses a request whose component kind is no
longer registered, and only forwards an answer when that gate still accepts
it. It also wraps the component in the current notification/reserved-row
layout and emits `onFirstReveal` after the request is actually mounted.

The transport-to-store bridge `HO` at `chunk-9w4htdvs.js@1326466` completes
the lifecycle: transport subscribe calls `open`, transport cancellation calls
`dismiss`, updates are forwarded only for ids admitted by that transport, and
store closure replies with either the answer or cancellation. On unmount it
unsubscribes all channels, dismisses every still-open request, and replies
cancelled. These paths prove display selection, buried-request suppression,
stale-answer rejection, and teardown statically. They do not prove which
keyboard focus primitive wins inside `Ve`, nor how a simultaneous host/remote
answer is ordered outside this local bridge.

## Local-JSX renderer registry boundary

The standard `kg` dialog kind is more specific than the name “permission
panel” suggests. Its defining schema is in `chunk-gpztfb1a.js@765`: the kind
is `local_jsx`, its payload contains `nodeId`, `commandName`, `immediate`,
`hidesPrompt`, and optional `holdsQueue`, and its result is the nullable
`Bm()` result. `Q_t` in the same module checks whether an open `local_jsx`
request still holds the queue. This is a command-panel contract, not a
complete visual approval schema.

`Aee` at `chunk-9w4htdvs.js@174417` is the producer-side registry. Each
`show()` call increments a local counter, creates `local-jsx-N`, stores the
render node, and calls the typed `requestDialog` transport with the `kg`
descriptor. The returned `closed` promise maps an abort to `"closed"` and a
transport settlement to `"dismissed"`; `retireAtTurnBoundary` records an
abort callback, and `closeCommandPanels()` aborts all retained panels.

On the consumer side, `Hst` is defined at `chunk-9w4htdvs.js@1291149`. It
reads the `nodeId` from the `local_jsx` payload, obtains the
`LocalJsxRegistryContext`, looks up the node in that registry, and renders the
resolved node. It throws when mounted outside the provider. The main screen
creates that provider at `chunk-9w4htdvs.js@1309973`, passing the active
`localJsx` registry as its value. The common dialog component registry maps
`kg` to `Hst` at `chunk-9w4htdvs.js@1292672`.

This closes the request-to-registry handoff but not the final panel body:
the node supplied to `Aee.show()` is an arbitrary local JSX component, and the
source does not expose a single universal permission-panel implementation.
The exact focus/keyboard behavior of that arbitrary node remains `UNKNOWN`; the
shared `Ve`/`Yi` selector primitive is recovered above, but a dynamically
supplied node is not required by the `local_jsx` contract to use it. The
terminal surface resolves a per-request node by `nodeId`, while the dialog
store and `HO` adapter still own settlement and cancellation.

### Local-JSX command caller and registry contents (new continuation finding)

The retained-node lifecycle has a direct bundled caller in the slash-command
dispatcher. For a `local-jsx` command, the dispatcher first rejects a
non-interactive session, then selects `s.load` or
`options.resolveCommandDialog(s)` as a dialog-loader callback. If no loader is
available it returns the ordinary command fallback. If the loader resolves a
node, the dispatcher checks `o.localJsx`; when the panel host is absent it again
returns the fallback. Otherwise it calls `localJsx.show(node, {commandName,
immediate, hidesPrompt:true, retireAtTurnBoundary:true})` and treats a
`"dismissed"` close as a completed command with no model query
(`chunk-qqv1hedf.js@27800`, `@29100`). The loader is therefore a dynamic
implementation boundary, but its admission, headless behavior, missing-host
fallback, and post-dismissal result are source-resolved.

`Aee.show()` allocates monotonically numbered `local-jsx-N` ids, stores the
returned render node in a snapshot map, optionally registers an abort callback
for turn-boundary retirement, and sends the typed `kg` request through
`requestDialog`. The returned `closed` promise removes the node and retirement
callback before resolving to `"closed"` when the controller was aborted or
`"dismissed"` otherwise. `closeCommandPanels()` aborts every retained panel
(`chunk-9w4htdvs.js@174423`). This means the local registry owns node lifetime;
the permission/dialog store owns request placement and answer settlement.

The renderer registry literal `Yke` also enumerates the statically bundled
component mappings: `local_jsx` plus generic, file, web-fetch, skill,
PowerShell, monitor, bash, browser, plan, elicitation, sandbox, managed
settings, account/memory, connector, Slack, and other built-in dialog kinds.
Several entries are conditional on feature/module availability, and Slack
consent entries are expanded from a module-provided list. This closes the
static registry scope of the extracted renderer module, while arbitrary
`resolveCommandDialog` loaders and host-injected node implementations remain
outside that literal (`chunk-9w4htdvs.js@1292300`).

## Ask-registry selection under concurrent permission requests

The common lifecycle's `eS.openAsk`/`closeAsk` calls resolve to a shared ask
registry defined at `chunk-phacttch.js@2931335`. The registry keeps separate
current blocks for permission, dialog, sandbox, managed-settings, elicitation,
and their queued variants, plus a `Map` keyed by `toolUseID`. Each `openAsk`
increments a registry-local `opened` counter and stores the request block with
the caller's `order` and `onTop` metadata. `closeAsk` removes only the matching
tool-use entry, then recomputes the visible permission block.

The selection function has three ordered cases. If a request's `order` equals
the registry's explicitly selected order, it wins immediately. Otherwise the
registry prefers an `onTop` request over non-top requests; among requests in
the same placement class it chooses the larger `opened` value for top entries
and the smaller `order` for queued entries. It then publishes the selected
block through the registry emitter. The priority list used for publication
checks elicitation, sandbox, managed-settings, permission, dialog, and queued
elicitation/sandbox states in that order, so a visible permission card can be
superseded by a higher-class system prompt even while its tool-use record
remains in the map.

This closes the previously inferred internal-selection gap: concurrent safe
tool calls do not overwrite one shared permission result, and their ask blocks
are deterministically selected by tool-use id, explicit order, topness, and
arrival order. The registry does not itself settle requests or decide keyboard
focus; those remain in the dialog store/terminal adapter. A late answer is
still rejected by the per-request resolve-once claim in `Ie`.

## Abort and teardown

The request's abort signal is linked to a local dialog controller. On teardown,
the code aborts the descriptor stream, removes the ask entry, closes hook-failure
state, unsubscribes permission recheck listeners, and runs registered teardown
callbacks. `n.onRacersReady` allows file/IDE and other external approval racers
to register their own dismissal and cleanup operations.

The dialog is therefore single-settlement even when several actors race:

```text
user answer | remote bridge answer | hook recheck | parent abort | auto-deny
       \          |          |          |          /
             resolve-once claim
                     -> cleanup -> tool decision
```

The source prevents a late answer from applying when the request was already
claimed/resolved. The shared selector's input and focus race guards are now
source-backed, but renderer-specific and cross-process answer ordering remain
outside this common lifecycle.

## Timers and automatic denial

For classifier safety-check and denial-limit fallback states, `Ie` arms a
deadline from `autoDenyAfterMs`. The timer updates the decision metadata,
tears down the dialog, sends a deny result, logs the auto-denied event, and
resolves the configured denial. If the dialog kind is temporarily unavailable,
the timer can be re-armed rather than denying immediately. On teardown the
timer is cleared.

This is distinct from the generic “user did not answer” path in
`chunk-fzzrkchm.js@61693`. `gy` tracks newly pending permission requests,
exponentially increases its grace interval, and after an ending/held condition
injects a deny control response with an explicit withdrawal message. It is a
queue cleanup mechanism for unanswered requests, not the normal interactive
terminal renderer.

## Concurrent prompts and ordering

The local source proves both the ask-registry selection and the dialog-store
placement. `eS.openAsk` receives an `order`; `personOnly` and external-racer
flags can place a request under or on top of another request. The common
lifecycle is per tool-use id, so two safe sibling calls do not share one
decision record. Registry selection and same-class promotion are
`VERIFIED-STATIC`, but the exact final focus/keyboard behavior and whether
every specialized panel follows the same promotion timing remain `UNKNOWN`.
The registry is therefore a one-visible/many-open structure: `openAsk` retains
each tool-use id, while `closeAsk` removes only the completed id and recomputes
the visible block (`chunk-phacttch.js@2931335`). It serializes presentation,
not the underlying approval promises or tool execution.

## Permission modes and dynamic tools

The existing engine supports `plan`, `default`, `acceptEdits`, `dontAsk`,
`bypassPermissions`, and `auto` mode branches. `Ie` does not itself select the
mode; it receives the already-classified permission result. Dynamic plugin/MCP
tools use the same descriptor fields and shared resolver. MCP-specific
permission-card and “always allow” suppression flags are reflected in the
descriptor, not used to bypass the common decision result.

## Confidence ledger

| Finding | Confidence | Anchor |
|---|---|---|
| Local ask dispatch selects specialized or generic dialogs | VERIFIED-STATIC | `chunk-57pw7ky5.js@47087` |
| Per-request local lifecycle is resolve-once and teardown-aware | VERIFIED-STATIC | `chunk-57pw7ky5.js@51135` |
| Ask ordering and queue placement are explicit | VERIFIED-STATIC | `chunk-57pw7ky5.js@51135` |
| Descriptor streams support async updates and abort | VERIFIED-STATIC | `chunk-57pw7ky5.js@51135` |
| Hook-rewritten preview can reprompt and rebuild safely | VERIFIED-STATIC | `chunk-57pw7ky5.js@45577` |
| Generic permission descriptor schema and builder | VERIFIED-STATIC | `chunk-cvvnq4he.js@478598`, `chunk-57pw7ky5.js@13560` |
| Default permission panel option construction and result mapping | VERIFIED-STATIC | `chunk-bqb9mv4b.js@54618`, `@53100` |
| Choice selection, feedback input, and Escape cancellation | VERIFIED-STATIC | `chunk-bqb9mv4b.js@37769`, `@35151` |
| Shared focusable selector and keyboard/click submission path | VERIFIED-STATIC | `chunk-75p1g95y.js@40861` |
| Refused-answer counter/default-focus state | VERIFIED-STATIC | `chunk-rcjkw193.js@672` |
| File-permission schema, preview renderer, option policy, and result mapping | VERIFIED-STATIC | `chunk-57pw7ky5.js@22460`; `chunk-9w4htdvs.js@1241629`, `@1249278`, `@1251327` |
| Web-fetch permission schema, renderer, registry, option mapper, and domain-grant guards | VERIFIED-STATIC | `chunk-57pw7ky5.js@33506`, `@47087`; `chunk-9w4htdvs.js@1282875`, `@1283167`, `@1283713`, `@1283914`, `@1292672` |
| Skill permission schema, renderer, exact/prefix grant policy, result mapping, and cancel behavior | VERIFIED-STATIC | `chunk-57pw7ky5.js@33238`; `chunk-9w4htdvs.js@1278093`, `@1278625`, `@1278805`, `@1279317`, `@1279923`, `@1280080`, `@1280174`, `@1280237`, `@1292672` |
| PowerShell permission schema, command renderer, suggestion/prefix options, result mapping, and deny-on-cancel behavior | VERIFIED-STATIC | `chunk-57pw7ky5.js@32959`; `chunk-9w4htdvs.js@1267767`, `@1270916`, `@1271495`, `@1292672` |
| Monitor/WebSocket permission schema, action renderer, suggestion guards, result mapping, and deny-on-cancel behavior | VERIFIED-STATIC | `chunk-57pw7ky5.js@32680`; `chunk-9w4htdvs.js@1258368`, `@1259097`, `@1259921`, `@1260091`, `@1260316`, `@1292672` |
| Auto-deny deadline is separate from unanswered-request cleanup | VERIFIED-STATIC | `chunk-57pw7ky5.js@51135`, `chunk-fzzrkchm.js@61693` |
| Dynamic MCP/plugin tools use the shared permission descriptor path | VERIFIED-STATIC | `chunk-57pw7ky5.js@47087` |
| Transport-to-dialog-store answer/cancel/update wiring | VERIFIED-STATIC | `chunk-9w4htdvs.js@1326466` |
| Dialog-store queue insertion and same-class promotion | VERIFIED-STATIC | `chunk-gq0v7nj7.js@1100`, `@2747` |
| Shared ask registry selection, per-tool-use entries, and close/recompute behavior | VERIFIED-STATIC | `chunk-phacttch.js@2931335`; caller `chunk-57pw7ky5.js@51135` |
| Local registry serializes visible presentation but retains concurrent asks | VERIFIED-STATIC | `chunk-phacttch.js@2931335` |
| Dialog-store visible selectors and reactive same-class reveal publication | VERIFIED-STATIC | `chunk-gq0v7nj7.js@1100`, `@2747` |
| Display-host selection, modal classification, buried-request suppression, and stale-answer gate | VERIFIED-STATIC | `chunk-9w4htdvs.js@1291712`, `@1291863`, `@1292189`, `@1292512`, `@1320735`, `@1322913`, `@1323202`, `@1323852`, `@1324180` |
| Transport/store bridge teardown and cancellation reply | VERIFIED-STATIC | `chunk-9w4htdvs.js@1326466` |
| Typed unary/streaming request validation and cancellation defaults | VERIFIED-STATIC | `chunk-s46d15s3.js@2725` |
| `local_jsx` dialog schema and queue-holding predicate | VERIFIED-STATIC | `chunk-gpztfb1a.js@765`, `@1043` |
| Producer-side local JSX registry allocates IDs and closes panels | VERIFIED-STATIC | `chunk-9w4htdvs.js@174417` |
| Common renderer maps `local_jsx` to registry lookup | VERIFIED-STATIC | `chunk-9w4htdvs.js@1291149`, `@1292672` |
| Main screen supplies the local JSX registry context | VERIFIED-STATIC | `chunk-9w4htdvs.js@1309973` |
| Local-JSX command dispatcher resolves loaders, handles headless/missing-host fallbacks, and mounts returned nodes | VERIFIED-STATIC | `chunk-qqv1hedf.js@27800`, `@29100` |
| `Aee.show` owns numbered node retention, abort retirement, request transport, close result, and bulk close | VERIFIED-STATIC | `chunk-9w4htdvs.js@174423` |
| `Yke` enumerates statically bundled dialog-kind mappings with conditional feature/module entries | VERIFIED-STATIC | `chunk-9w4htdvs.js@1292300` |
| Bridge outcome classification (user, hook, abort, config) | VERIFIED-STATIC | `chunk-phacttch.js@1880701` |
| Recheck/classifier decision telemetry path | VERIFIED-STATIC | `chunk-phacttch.js@1881636` |
| Final tool-decision persistence and event emission | VERIFIED-STATIC | `chunk-phacttch.js@1881907` |
| Host/worker `can_use_tool` validation, in-flight deduplication, and response mapping | VERIFIED-STATIC | `chunk-9w4htdvs.js@218600`, `@220300` |
| Generic `permission_prompt` renderer and selector plumbing | VERIFIED-STATIC | `chunk-bqb9mv4b.js@54618`, `@37769`; `chunk-75p1g95y.js@40861` |
| Bash, browser, plan, generic, file, web-fetch, skill, PowerShell, and monitor panel bodies | VERIFIED-STATIC | `chunk-9w4htdvs.js@1200505`, `@1206666`, `@1216982`, `@1241629`, `@1251327`, `@1260316`, `@1271495`, `@1280237`, `@1283914`, `@1293453`; generic body `chunk-bqb9mv4b.js@54618` |
| Shared selector keyboard/focus primitive | VERIFIED-STATIC | `G9`, `Ci`, `HYn`, `Di`, `Yi`, `Fh`, `cb`, and `zmt` establish focus state, keyboard transitions, focus reclamation, and input-race guards |
| Cross-kind focus arbitration, host-versus-remote answer races, and dynamically supplied local-JSX node bodies | UNKNOWN | the bundled registry and loader handoff are recovered, but arbitrary loader implementations, node focus behavior, and cross-process ordering are not |
| All simultaneous local dialogs are visibly serialized | INFERRED | store ordering/promotion is static; final visual serialization is not proven |

## Remaining gaps

1. The statically bundled `Yke` registry is enumerated, but conditionally loaded and host-supplied dialog implementations are not exhaustively recoverable from the renderer literal.
2. Cross-kind focus arbitration when a queued request is promoted or a different dialog kind replaces the mounted panel. The shared selector primitive is resolved, but the host-wide policy is not.
3. Complete timeout behavior for every specialized dialog kind.
4. Permission-request replay after resume/compaction.
5. Cross-process approval races where a local and remote answer arrive together.

The transport dispatcher narrows the last item: duplicate request ids and
dispatcher teardown are handled locally, but the ordering between a local
terminal answer and an independently arriving remote answer remains unresolved
because the final renderer/host arbitration is outside the recovered common
body.
