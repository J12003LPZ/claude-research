# Host wake and background resumption

Status: `PARTIAL` — the local notification-to-main-loop wake path, attached-host
return self-wake, scheduled-loop wake, and process-exit orphan-agent recovery
are `VERIFIED-STATIC`. The remote-served background-shell path is also
statically shown not to notify its calling session on shell completion. The
external wake producer after process exit, other remote-session wake, and
shutdown behavior remain open.

## Scope and evidence

This report follows the path requested for the continuation pass: detached
completion notification to the next model request. The anchors are character
offsets in the extracted Claude Code 2.1.296 bundle, not source-map line
numbers. No new live-model experiment was run.

REA retained the application-level analysis as
`ev_f219362e2aa64d136c19e6f408087c8cf4e07c28d12011cd2041ba7f658f85d6`. A
focused trace identified `chunk-fzzrkchm.js` and its import relation, but REA
could not allocate semantic analysis for that module in the retained result
(`ev_23dd97c6ca05983d50cfeadcc05997130896bf05e10383a05d8c18c52332160f`). A
separate exact-string trace returned no graph match for `task-notification`
(`ev_fb6fa788689ca1ad1c181cc2141ac1d1350f25d6b765be9fbc6ddd0e8f66a4cf`);
because the graph is partial, that result is not evidence that the source
string is absent. The function-level claims below therefore rely on direct
reading of the extracted modules, with REA used as a cross-check and graph
limitation record.

The new REA feature trace for the remote background-shell metric also had no
graph match (`ev_6693d2e216fcc195747b5fdb9c0fa70ab43c5d9c8646044db89c69ef0d5dcd0c`);
that is likewise not a negative finding. The scoped remote result below is
from direct source reading.

## Recovered call graph

```text
detached tool execution
  -> CXt child run / task registry
  -> Ejo completion settlement
       -> sCe tool-result persistence
       -> optional _4 large-output spill
       -> hge completion/failure notification
       -> Qa / enqueuePendingNotification
            mode = task-notification
            agentId = current main agent
            passive = false for normal completion
            priority = next
            turnAttribution = inherit
       -> queue subscriber he
            -> ow(...)
                 -> Am.route()               # non-main-agent wakes
                 -> nw() predicate
                      -> wo() = Em.run()     # main-loop kick when idle
                           -> Lp.run()
                                -> xp.take()
                                -> turn runner
                                -> next model request when the turn policy queries
```

The detached admission and completion implementation is in
`chunk-phacttch.js@2216254`. `aqe` checks the detach policy, execution context,
stop state, feature gate, and hook restrictions. `CXt` links a child abort
controller to the parent, registers the task, and allows `backgroundNow()` to
release the foreground continuation. The detached completion path calls `Ejo`;
normal completion then calls `hge` with a non-passive result. `Ejo` persists the
tool result before attempting notification and spills oversized output through
the file-result path.

`hge` constructs a task notification and calls the queue facade with
`mode: "task-notification"`, `priority: "next"`, the main agent id, and
inherited turn attribution (`chunk-phacttch.js@2217060`). The generic notification
helper `LVt` uses the same mode and queue interface
(`chunk-phacttch.js@632678`). The queue facade alias `Qa` resolves to the
session queue's `enqueuePendingNotification` method
(`chunk-phacttch.js@238838`).

## Main-session wake predicate

The source defines the relevant classification and predicate together in
`chunk-phacttch.js@218545`:

- `hnr` recognizes `prompt`, `orphaned-permission`, `task-notification`, and
  `poll-event` queue modes.
- `Sp` tests ownership by the current agent id.
- `Zf` accepts an owned item when `passive !== true`.
- `mTe` uses the same ownership rule for main-thread items and applies a
  stricter current-agent rule to task notifications in subagent contexts.

The important correction is that `Zf` is not restricted to human prompts. A
normal detached completion emitted by `hge` is therefore eligible for the main
queue as long as it is owned by the current main agent and is not passive.

The queue-to-loop bridge is explicit in `chunk-fzzrkchm.js@224541`:

```text
nw = !running && !inputClosed && peek(Zf) exists
ow = subscribe(queue changes, route wakes, and kick when nw is true)
```

The setup wires `ow` to `Am.route` and `wo`, where `wo` invokes `Em.run`, in
`chunk-fzzrkchm.js@559872`. This establishes a local automatic kick for an
eligible task notification; it is not merely a priority annotation.

## Attached-machine host-return self-wake

The bundle contains a separate host-status wake controller that is narrower
than a general daemon or remote-session wake. Class `cd` begins at
`chunk-fzzrkchm.js@97910`; its origin is `{kind:"task-notification",source:
"host-return-wake"}`. Initializer `gS` at `chunk-fzzrkchm.js@102430` starts it
with the attached-machine registry, late-outcome tracker, message queue,
permission mode, turn counter, and a scheduler.

The controller registers an `onHostStatusChange` listener. For a host changing
to `back`, it requires the feature gate to be enabled and `toldModel` to be
true, records the host and turn count, and schedules a check after 10 seconds.
The check (`#o`) then:

1. refuses stale records, disabled mode, offline hosts, an existing
   `host-return-wake` queue item, rate-limit conditions, or a changed turn;
2. waits up to 60 seconds for the normal reconnect spacing and probes the
   host's `transport.probeLive` with the controller abort signal;
3. marks the host answered and optionally asks about calls that were given up;
4. waits another 60 seconds when the main call remains open and no “last word”
   notification is pending; and
5. calls `#g`, which enqueues:

```text
{ mode: "task-notification", priority: "later", agentId: currentMainAgent,
  isMeta: true, skipAttachments: true,
  origin: { kind: "task-notification", source: "host-return-wake" },
  value: host-return instruction }
```

The enqueue is at `chunk-fzzrkchm.js@100586`. The instruction explicitly says
that nobody typed it and asks the model to continue only within the user's
existing request. The resulting item is still eligible for the local `Zf`
queue predicate because it is owned, non-passive work; the ordinary
`ow`/`wo`/`Lp.run` path then admits it if the main drain is idle and input is
open.

There is a second `lastWordQueued` branch (`#f`) that applies the same enabled,
main-call, rate-limit, and 60-second spacing checks before enqueueing a
correction note. `lapsedAtTurnStart` at `chunk-fzzrkchm.js@101196` clears or
advances the host records when a turn begins, preventing repeated self-wakes
after a person has written, a head has been taken, a non-default permission
mode is active, or the wake rate limit has fired. `Bs` at
`chunk-fzzrkchm.js@102333` identifies these queue entries precisely.

This proves an attached-machine host-return wake into the local turn queue. It
does not prove that a disconnected process, arbitrary remote-control session,
or every daemon-managed worker is independently woken; those remain separate
host boundaries.

## Scheduled-loop wake and process-exit recovery

The `/loop` scheduler is a separate producer from detached task completion and
host-return self-wake. `ScheduleWakeup` at `chunk-e1qepm02.js@2208` computes a
clamped target, applies recurring-loop age and keepalive rules, and persists a
loop schedule through `@3775`; the persisted record contains the prompt,
reason, scheduled time, and optional keepalive/tool-use association. After a
resume, `uWo` at `chunk-e1qepm02.js@3481` re-arms a future pending fire when no
active loop is present. User abort cancels the loop schedules and keepalive
state through `O8n` at `chunk-e1qepm02.js@4928`.

The scheduled-task hook at `chunk-zdvza25y.js@18210` uses two different
delivery shapes. A normal loop fire constructs a `mode: "prompt"` event with
`priority: "later"`, `wakeupSource: "loop_wakeup"`, and scheduled task/fire
ids, then calls `enqueuePendingNotification`. A teammate-task fire instead
creates a `task-notification`, and orphaned cron records are removed. The
scheduler suppresses most fires while loading, except loop records, and
checks closed-input and kill gates before delivery. This is a local queue
producer; it does not itself prove that every scheduled prompt reaches an API
request because the ordinary drain/query policy still applies.

Resume reconciliation is implemented by `yft` at `chunk-rrep227n.js@43003`.
It restores the transcript/task view, carries cron state, reconciles an overdue
pending loop through `Yi` at `chunk-rrep227n.js@62600`, and then calls `Wi` at
`chunk-rrep227n.js@49606` to classify orphaned background agents. An overdue
loop fire is deliberately converted into a `task-notification` with
`shouldQuery: false`, so a process restart reports that the fire will not run
rather than silently issuing a model turn. A future loop is re-armed through
`uWo`.

`Wi` can return recent, disk-resumable agents to an optional resume callback;
it otherwise records stopped/failed state and notices. The call sites show why
this is not a universal auto-resume claim: the startup path in
`chunk-fzzrkchm.js@477551` supplies a running-pool stand-in, while the session
lifecycle path in `chunk-9w4htdvs.js@365354` supplies
`resumeOrphanedAgents`. That callback waits for MCP settlement and takeover
checks, then invokes `wX` with `continueInterruptedTurn: true`; its restart
notice is produced by `v0o` at `chunk-rrep227n.js@53530` and called from
`chunk-9w4htdvs.js@368057`. The frame restore path at
`chunk-9w4htdvs.js@352930` also calls `yft`, but does not by itself establish
that the callback is supplied.

The recovered state machine is therefore:

```text
process restart
  -> yft transcript/task reconstruction
  -> Yi pending-loop reconciliation
       future fire -> uWo re-arm
       overdue fire -> task-notification, shouldQuery:false
  -> Wi orphan-agent classification
       no resume callback -> persist stopped/failed state
       resume callback -> MCP settle/takeover checks -> wX continuation
                          -> separate task-notification result
```

This closes the local process-exit *reconciliation* gap, not the external
process-exit *wake* gap. The inspected code does not establish which host,
daemon, or scheduler causes a terminated process to be started again, nor does
it prove that every restored orphan is resumable.

## Remote-served background shell: no local completion notification

The remote-tool forwarding path has a distinct background-shell controller and
must not be conflated with the local detached `hge` path. In the remote shell
executor `so`, `chunk-bsjqfd0a.js@35653`, a per-caller `backgroundShells`
starter is created at `@37213`. It is enabled only when the call did not arrive
over the bridge, the remote policy enables background shells, and the caller's
per-session limit has capacity. The starter is passed into the remote tool
context and its `settle` method is called after `Un` returns at
`chunk-bsjqfd0a.js@39490`.

The owning registry is `nn.starterFor` at `chunk-qwgyf6qf.js@4678`. Its
`reserve`/`adopt` pair enforces the lifetime, generation, sandbox, and maximum
running-or-reserved checks. `#s` at `chunk-qwgyf6qf.js@5543` records the shell
under the caller's call id, emits start/exit events, applies the deadline and
parent-lifetime handlers, and removes the record on settlement. This is
per-caller remote execution bookkeeping; no call to the local
`enqueuePendingNotification` facade occurs in this path.

When the remote call returns a completed background-shell result, the same
executor appends the exported `KHo` message from
`chunk-0j0ezmy7.js@3077`. That message states that the calling session is not
notified when the shell finishes and that status is obtained from the remote
target's own mechanisms. This is a user-facing contract backed by the
completion branch at `chunk-bsjqfd0a.js@39490`; it is not evidence that every
remote transport or daemon has no independent wake protocol. It does establish
that this remote-served shell branch does not transform completion into the
local task-notification/main-loop edge recovered above.

## Turn-drain behavior

`Lp.run` in `chunk-fzzrkchm.js@118016` refuses to start a second drain while a
run is already active, or while stopping, terminal shutdown, or end-session
conditions apply. When admitted, it takes queue work through the selector and
processes a turn. Consequently:

| Session state when completion is enqueued | Static behavior |
|---|---|
| Main drain idle, input open, session not stopping | Queue subscriber calls `wo`; a new `Lp.run` is started. |
| Main drain already running | No concurrent second drain; the existing pass can consume the pending notification. |
| Input closed | `nw` is false, so the queue subscriber does not kick the main drain. |
| Stop, terminal shutdown, or end-session guard active | `Lp.run` refuses the new run; shutdown/parking behavior is separate. |
| Notification marked passive | It fails `Zf`; it is not an eligible main-agent wake item. |
| Completion belongs to another agent | It is routed through the agent wake router rather than the main `Zf` path. |

The model request is still conditional on the turn selector and query policy.
The recovered edge proves that a detached result can start the local main loop;
it does not prove that every started drain necessarily makes an API request.
In particular, the turn generator checks `shouldStopBeforeNextApiCall` and can
return `reason: "background_requested"` before another request
(`chunk-93pksqr2.js@134303`).

The positive request edge is also explicit. If that stop predicate is false and
the earlier setup gates do not return a blocking, consent, or model-error
terminal, the query API loop emits `query_api_streaming_start`, assigns
`I.callModel` to `Zd`, and consumes `Ca(Zd({...}))`; this is the actual model
request handoff (`chunk-93pksqr2.js@153755`). Therefore an eligible detached
notification can lead to another model request through the local drain, but only
after queue admission, prompt-submission settlement, the stop predicate, and
context/model gates all succeed. The source still does not establish that every
`task-notification` reaches this positive branch.

## Exact stop-before-request predicate

The callback that controls this boundary is now source-resolved. The ordinary
tool-use context builder initially exposes a weaker callback that tests only
whether the gesture has a pending record (`Re.pending !== null`) at
`chunk-9w4htdvs.js@1395543`. The main-session `_runImpl` then deliberately
overrides that callback with `()=>Eo.stopsLoopForPending()` at
`chunk-9w4htdvs.js@1413024`. The query loop invokes the callback only for the
main query (`Mr` is `ko === "main" || ko === void 0`) and does so before
`stream_request_start`, model configuration, compaction, or the API request at
`chunk-93pksqr2.js@134246`. A true result exits the generator with
`{reason:"background_requested"}`. The same terminal-reason classifier treats
that reason as `{kind:"none"}` rather than retrying the turn, so this is a
deliberate request-suppression boundary, not an API failure retry.

`stopsLoopForPending()` is the `eV` background-gesture method at
`chunk-9w4htdvs.js@108462`. Its normal result is simply whether the pending
defer record still exists. Before returning, it has one feature-gated draft
exception: when a pending defer exists, the current input is non-empty, and
`tengu_keen_sloth` is enabled, it clears the pending record, emits the draft
warning, and returns false. This prevents a deferred background transition
from suppressing the next model request while unsent draft text is present.

The pending record is created only by the `defer-then-fork` branch. At
`chunk-9w4htdvs.js@117617`, that branch arms a cap timer, stores
`confirmedInterstitial`, `armedAtMs`, the absorb/last-press timestamps, the
carried-task count, and a `proceed()` continuation, then displays
“Backgrounding after the current tool finishes…”. The timer can later clear
the record and fork after the cap; normal turn cleanup clears it at
`chunk-9w4htdvs.js@1408892`. Thus a task notification arriving while the
deferred background gesture is pending may wake the local drain, but the next
query request is intentionally stopped before request preparation so the
background fork can take ownership. This callback is not a general task-result
policy and is not installed for subagent queries because the query-loop check
is guarded by the main-query predicate.

REA semantic tracing was also run backward from the `stopsLoopForPending`
property (`ev_14ec941b9a0d3543307d717ce6ca928665c2094771f6a20153a130b515d0d57a`).
It returned `status: partial` with zero matched semantic nodes; the retained
application graph does not expose this minified class property to that
extractor. This is a tooling limitation, not a negative source finding. The
function-level conclusion above is therefore `VERIFIED-STATIC`, with the REA
trace recorded as a partial cross-check only.

The drain-to-turn handoff is nevertheless concrete: after `xp.take()` and
`V.commit`, `Lp.run` arms the committed batch and invokes
`this.turnRunner.run({batch,input,tools,intake,memoryKick,turnStartClock})`
(`chunk-fzzrkchm.js@121177`, `@121518`). Thus an eligible host-return or
detached-result notification reaches the ordinary turn runner; the remaining
question is the runner/query policy's decision to issue or suppress its next
API call.

## Queue admission does not always mean an immediate query

The `xp.take()` body adds a more specific suppression branch. For a
`task-notification` whose value is a string, when the session is not ending, the
held completion-character budget remains within `ay`, the
`tengu_swirling_meteor` gate enables coalescing, and
`Ju.holdsQueryForFollower(...)` returns true, the command is rewritten with
`shouldQuery:false`, `queryHeldForNextTurn:true`, and no thread-state stamp
(`chunk-fzzrkchm.js@108084`). This is `VERIFIED-STATIC`: the queue item is
admitted to the ordinary drain, but its command metadata marks the resulting
continuation/result as held for a later turn. It is not, by itself, proof that
the current model request is skipped.

`holdsQueryForFollower` is itself narrow. It rejects a deferred human turn,
then looks for a non-handback `Nu` follower that is not rejected by the usage
limit predicate; it additionally requires `ly(e,s)`, the admission predicate,
and no prewait doom boundary (`chunk-fzzrkchm.js@106757`). The source does not
resolve the semantics of `ly` in this body, so that helper remains outside this
claim.

The held result is not silently discarded. `xp.noteTurnEnded` accumulates the
notification's character count and workload only when the held command ends
without an error, has no completed model turns, and returns an empty result.
If the next drain finds no eligible queue head, `xp.take()` can synthesize an
empty prompt with `skipSubmissionHooks:true`, carry the saved workload, and
clear the held counters (`chunk-fzzrkchm.js@108084`). Therefore the recovered
state machine is:

```text
eligible task notification
  -> local wake / Lp.run
  -> xp.take admission
  -> [coalescing predicate true]
       shouldQuery=false, queryHeldForNextTurn=true
       -> ordinary turn runner
       -> empty-result bookkeeping
       -> later synthetic empty prompt if the queue drains
  -> [predicate false]
       ordinary command metadata preserved
```

This narrows, but does not eliminate, the earlier API-request unknown. The
turn runner is definitely invoked (`@121518`). Its `kf.run` body then calls
`engine.submitMessage` with the command-derived context, and the query loop's
pre-request stop gate is the separate `shouldStopBeforeNextApiCall` predicate
(`chunk-fzzrkchm.js@190435`; `chunk-93pksqr2.js@134246`). The result router
does give `shouldQuery:false` a concrete downstream meaning: when
`queryHeldForNextTurn` is also false and the result is not a handback/usage
alert, it flushes and emits the result without entering the held-result path;
when the hold flag is true it continues through the holdback/release logic
(`chunk-fzzrkchm.js@137755`). Therefore the recovered evidence says
`shouldQuery:false` controls continuation/result delivery here; it does not
establish that the current API call is suppressed solely by that flag.

## Queue-to-prompt hook bridge

The local kick does not inject a task result directly into the model transport.
The query loop first builds a deliverable queue view and runs its fold/submission
path. `Di` maps a queued event into a prompt submission record, preserving the
event mode, `promptSource`, and optional `wakeupSource`; for a
`mode: "task-notification"` event, `Ui` supplies the semantic origin
`{kind: "task-notification"}` (`chunk-93pksqr2.js@11147`).

When the event is eligible for prompt submission, `Ni` calls `Tbn` and settles
the surfaced queue entry based on the hook result. It can return `surfaces`,
`waits`, `dropped`, or `left`; cancellation and a hook-ended turn are handled
before the event is handed to the normal attachment path
(`chunk-93pksqr2.js@11874`). `Tbn` is the defining prompt-submission bridge,
not a model-call primitive: it runs `prompt.submit` hooks, handles rewritten
text, hook blocks, interruption, and queue settlement, and returns an
`ended`/drop outcome when submission should not continue
(`chunk-kgekdqv3.js@7480`).

Therefore the strongest local sequence is:

```text
queue kick
  -> query drain
  -> mTe queue selection
  -> Au/Ni fold submission
  -> Tbn prompt.submit hook pipeline
  -> surfaced attachment / settled queue entry
  -> query policy decides whether to call the model
```

This resolves an important boundary: a task notification can be automatically
processed without being treated as a synthetic user keystroke, but the source
does not establish that every processed notification reaches `callModel`.

## Non-main-agent wake and stranded resume

The `Lf` wake router in `chunk-fzzrkchm.js@229359` handles task notifications
for agents other than the main agent. It snapshots the queue, identifies
wakeable task entries, and calls `wX` with the target `agentId`, a task
notification prompt, and `promptOrigin.kind = "task-notification"`. The queue
entry is consumed only after delivery is committed. It maintains a wake-in-flight
set and rechecks the queue afterward. `startStrandedResume` also queues stranded
agent messages when the saved main-loop context is unavailable and flushes them
once that context returns.

This is a different mechanism from the main-session `ow`/`nw`/`wo` edge. It
supports child-agent resumption, but does not establish a universal host wake
for remote or exited sessions.

## Distinguishing detached completion from idle check-ins

The turn code has a separate goal/check-in scheduler. Its idle check-in policy
can defer a check-in until a user message in the applicable mode
(`chunk-93pksqr2.js@56010`). That limitation must not be generalized to the
detached-result path: detached results use `hge` and the queue subscriber, while
goal check-ins use the timer/check-in scheduler. The previous
`remaining-subsystems-decompilation/04-background-wake-policies.md` treated the
absence of a universal wake as if it also covered the local detached-result
kick. That was too broad and is corrected here.

## Cancellation and race boundaries

The recovered source proves these local boundaries:

1. Parent cancellation is linked to the detached child controller in `CXt`.
2. A detached task may be stopped by its ceiling timer or by the task registry.
3. `Ejo` persists before notification delivery; if the conversation is no
   longer heard, delivery can be dropped rather than injected into another
   conversation.
4. A running main drain serializes queue consumption; completion does not start
   a competing main drain.
5. Child-agent wake delivery has an in-flight guard and a post-delivery queue
   recheck.

The following were not established by the inspected paths: shutdown
parking for every task type beyond the exit-handoff and `wYn` semantics recorded above, duplicate completion suppression across resume,
host-level wake scheduling after process exit, remote wake behavior, and the
full interaction between compaction and a notification arriving during an
active turn.

## Shutdown and end-session gates on the wake path

This pass resolves what the `stopping`, `terminalShutdown`, and
`endSessionRequested` guards in `Lp.run` are bound to, and what each does to
the held-completion state recovered in `xp`.

**Guard bindings (`VERIFIED-STATIC`).** The print host constructs `Lp` with
`stopping:Ls` and `terminalShutdown:wn` (`chunk-fzzrkchm.js@555196`), and
other host consumers use `Ls()||wn()` (`@552456`, `@559789`). `Ls` is the
imported wrapper over the process shutdown controller's `isShuttingDown()`,
which returns `shutdownInProgress` (`chunk-phacttch.js@105753`, `@100147`).
`wn` returns a process-global `committed` boolean whose initial value is
false (`chunk-80kqkekd.js@150398`, `@150477`). The only writer found for
`committed` is `T8`, which sets it true; no code in the inspected files assigns
it back to false (scoped: a literal `.committed=` assignment pass over every
extracted `chunk-*.js` found `Ia.committed=!0` in `T8` as the only write to this
object; two other `committed` writes in `chunk-phacttch.js@743061`, `@833761`
belong to unrelated objects, and the pass does not cover aliased or computed
property writes).

**What commits shutdown (`VERIFIED-STATIC`).** `shutdown()` returns at once if
`shutdownInProgress` is already set; otherwise it sets
`shutdownInProgress=!0` and calls `T8()` before its first `await`
(`chunk-phacttch.js@101341`). `shutdownSync` calls `T8()` when no shutdown is in
progress and then starts `shutdown()` (`@97238`). The print-mode SIGTERM
handler returns if `Ls()` is already true, otherwise sets `T8()`, aborts the
local controller `Yn`, and calls `Zn(143)` (`chunk-fzzrkchm.js@491913`).
Other `T8` callers are the version-gate path (`chunk-0a768372.js@8365`), a
rejected-approval path (`chunk-evx88p26.js@8089`), and a settings-helper
refusal (`chunk-jzzwheky.js@40766`). `claimShutdown` sets
`shutdownInProgress` without `T8`, and `releaseShutdownClaim` clears it again
(`chunk-phacttch.js@100678`, `@100746`). Consequently `Ls` can return to false
after a released claim while `wn` cannot.

**Effect on a new drain (`VERIFIED-STATIC`).** `Lp.run` returns before setting
`drain.running` if `stopping()`, `terminalShutdown()`, or an end-session
request with no end-session head applies (`chunk-fzzrkchm.js@118016`). The
queue subscriber's kick therefore cannot start a drain after `shutdown()` has
run its synchronous prefix.

**Effect inside a running drain (`VERIFIED-STATIC`).**

* `xp.take` is `while(!this.stopping()){...}` and falls out returning
  `undefined`, so no further head is taken once shutdown is committed
  (`chunk-fzzrkchm.js@109230`).
* `Xu.isHeld` is false when `stopping()` is true, so a drain parked in
  `waitForHead` is released rather than waiting for the held prerequisite
  (`chunk-fzzrkchm.js@115186`, class `@114271`).
* The synthetic empty-prompt delivery for held task-notification completion is
  only emitted inside the loop body. It is skipped when an end-session request
  is set, when a main-agent command is already queued, or when the drain's
  abort controller is already aborted; in the abort case the held counters are
  zeroed (`chunk-fzzrkchm.js@109230`).
* `xp.exit` zeroes the held completion counters when `stopping()` or
  `endSessionRequested` holds at turn exit (`chunk-fzzrkchm.js@113101`).
  A held completion therefore does not survive a committed shutdown in this
  object. Whether it is persisted elsewhere is not shown here.

**Two distinct stop paths (`VERIFIED-STATIC`).**

* `end_session` sets `endSessionRequested`, clears the budget timer, aborts the
  drain's abort controller with reason `shutdown`, aborts `Yn`, discards `_r`,
  and breaks the input loop (`chunk-fzzrkchm.js@572889`). `Vn` is true exactly
  when that controller is aborted with a shutdown reason, and is what the turn
  runner receives as `turnAbortedForShutdown` (`@486420`, `@552456`). With the
  flag set, `xp.take` only takes the end-session head.
* The SIGTERM handler above does not abort the drain's abort controller;
  SIGINT does, with reason `user-cancel` (`chunk-fzzrkchm.js@491804`).
  So after SIGTERM an in-flight turn is not cancelled by this handler, but
  no new head is taken and no new drain starts.
* `Lp.teardown` sets `endSessionRequested`, freezes delivery-ledger terminals,
  runs registered teardown callbacks, and aborts the controller
  (`chunk-fzzrkchm.js@116858`).

**Child-agent wake router (`VERIFIED-STATIC`).** `Lf.route` returns first when
`resumesNothing()` is true, which is
`endSessionRequested || Ls() || wn() || aB(maxBudgetUsd)`
(`chunk-fzzrkchm.js@228384`, definition `@230910`). A completed child result
is therefore not resumed once shutdown, end-session, or the budget limit holds.

**Superseded unknown.** The earlier open question about whether `shutdown()`
waits for an in-flight turn is answered in "Shutdown execution timeline"
below. The compaction interaction is in `02-cross-subsystem-concurrency.md`.

## Shutdown execution timeline

This section replaces the earlier `UNKNOWN` on whether `shutdown()` waits for
an in-flight turn. It decompiles `gpt`, `Est`, `FSt`, `eat` and every other
awaited step of `shutdown()` (`chunk-phacttch.js@101341`), then the signal and
end-of-run entry points. All timings below are source constants; wall-clock
behavior under load is not measured (no runtime experiment was run).

### What each awaited helper actually waits for

| Step | Implementation | What it awaits | Bound |
|---|---|---|---|
| `gpt` | `async function gpt(){await ge().cleanup.drain()}` (`chunk-j0pppawn.js@4520`) over class `We` (`@3916`) | Runs every callback registered with `St(...)` concurrently, `Promise.allSettled`, then rethrows the first rejection. It snapshots and clears the registry first, so a callback registered after the drain started is never run by this drain | Raced against `DZ=2000` ms in `shutdown()` (`@4461`); the race loser is not cancelled |
| `Est` | `Fte().drain()` over `vst.pendingWrites` (`chunk-phacttch.js@51131`, class `@50696`) | Only promises passed to `h8o` (`@51059`). The sole `h8o` call found is the exit-handoff promise at `chunk-4afqvhsq.js@5666` | None of its own; bounded only by the failsafe timer |
| `FSt` | `Promise.allSettled(lAe().pendingKillBackstops)` (`chunk-phacttch.js@80875`) | The SIGKILL backstop promises added by shell `kill()` (`#E`, `@85881`) | Backstop escalates to SIGKILL after `fHn=1500` ms, polls death every `pHn=100` ms |
| `Akn` | loop over `liveShellCommands`, `kill()` when `status==="running"` (`@80961`) | Nothing. Synchronous, fire-and-forget; `kill()` returns the backstop promise that `FSt` later awaits | n/a |
| `eat` | iterates `pendingEscalationsByTaskId`, then `while(inFlightProcessSweeps.size>0) await Promise.all(...)` (`@90434`) | Process-tree sweeps already in flight | None of its own |
| SessionEnd hooks `skt` | `yM(... signal, timeoutMs:DZo())` inside `skr({boundMs:JEe()})` (`@2943885`) | Hook commands | `signal=AbortSignal.timeout(S)`; `S=JEe()` is `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` or `max(1500, min(longest configured SessionEnd hook timeout, 60000))` (`@2955308`, `@2955612`) |
| `mL` | `Promise.all` of registered drains, each `.catch(()=>{})` (`chunk-mx6ygzc6.js@3358`, `@3540`) | Registered drain callbacks | None |
| `PDe` | dynamic import then `flushAnalyticsSinks()` (`chunk-phacttch.js@104942`) | Analytics sinks | None of its own |
| `rPe`, `pwe`, `g2n` | diagnostics-file write queue (`chunk-zf629ea9.js@1621`), `Ce().instance.flush()` (`chunk-j0pppawn.js@59342`), `preExitFlush.drain()` (`@4667`) | Their own queues | `g2n` is a plain drain; individual `HP` registrants add their own races (for example `chunk-pzqsmv9v.js@9121` waits at most `1e4` ms) |
| `BDt` | stdout end and flush (`chunk-ww4e4yyz.js@3629`) | Pending stdout bytes | `Ut(..., fxr(e))` where `fxr=min(30000,max(e,ceil(outstandingBytes*1000/262144)))` (`@4083`) |

All of these are `VERIFIED-STATIC` as to what they await. None of them
references the model turn, the drain (`Ee`), `Lp`, or the turn's abort
controller.

### Exact order inside `shutdown()` (`chunk-phacttch.js@101341`)

1. Return if `shutdownInProgress`. Else set `shutdownInProgress`, call `T8()`,
   set `process.exitCode`.
2. `await import(chunk-7xzs7f0h.js)` and compute `S`. The failsafe is not armed
   until this import resolves.
3. `armShutdownFailsafe(max(5000, S+5000))` (`@98517`), so 6500 ms with the
   default `S=1500`. The timer is `unref`'d.
4. `dTe()` restores terminal modes; `printResumeHint()`.
5. `gpt()` raced against 2000 ms. On timeout the race rejects with `dat`
   (`@105059`), the `catch` swallows it, and the cleanup callbacks keep running
   as ordinary promises.
6. If `Tst()` (pending exit-handoff writes) then re-arm the failsafe to
   `max(15000, S+5000)` from now (`INs=15000`).
7. `await Est()`, `Akn()`, `await FSt()`, `await eat()`.
8. Optional worktree removal, which re-arms the failsafe.
9. SessionEnd hooks unless a spare-claim state is active (`sLt`).
10. `Akn()`, `await FSt()`, `Son()`, `llr()`, `Rkn("session_end")`.
11. `waitForHeldOAuthRefresh`, `mL()`, `PDe()`.
12. `rPe()`, `pwe()`, `g2n()`.
13. `armFailsafeAndDrainStdout`: re-arm to `fxr()+1500` (at least 3500 ms),
    then `BDt()` (`@102947`).
14. `forceExit(code)` (`@93131`): clears the failsafe, `drainStdin`, then
    `process.exit(code)`; if that throws, `process.kill(pid,"SIGKILL")`.

### Answers to the shutdown questions

**1. Does shutdown wait for an active model turn? No (`VERIFIED-STATIC`,
scoped).** No step above awaits `Ee.running`, the turn promise, or the model
request. I enumerated every `St(...)` callback registered from the print host
(`chunk-fzzrkchm.js`): the shutdown reporter (`@492154`) only persists, resolves
a latch, logs `run_state_at_shutdown`, and emits
`tengu_shutdown_pending_state`; the other registrants end the keep-alive
(`@216079`), flush tool-CPU telemetry (`@448241`), tear down headless MCP
(`@509305`), and unregister a lookahead (`@577365`). None aborts or joins the
turn. The same literal pass over all 114 `St`/`HP` registrations that import
`chunk-j0pppawn.js` was read by context only; I did not decompile all 114
bodies, so a registrant elsewhere that joins a turn is not excluded for hosts
other than the print host.

The waits for a turn are on other paths:

* Normal end of a headless run: after the result, the run calls `Ps(code)`
  (`chunk-fzzrkchm.js@483089`), a sync wrapper that reaches `shutdown()`. The turn
  has already finished, so shutdown does not wait for it; it follows it.
* Input closed: the `closeInput` callback returns without teardown while
  `Ee.running` or a poll is active (`chunk-fzzrkchm.js@658756`); the drain tail's
  `onInputClosed` (`@559312`) runs `Qh`/`$h` later (`@549992`, `@550957`). That is
  host teardown, not process shutdown.
* `end_session`: sets `endSessionRequested`, aborts the turn controller with a
  shutdown reason, then the same `closeInput` path applies (`@572889`).

**5. Can SIGTERM terminate a running turn without cancelling its controller?
Yes (`VERIFIED-STATIC`).** The print-mode SIGTERM handler (`@491913`) runs
`T8()`, `Akn()`, `Yn.abort()`, `Zn(143)`. `Yn` is `lr(500)` (`@487609`), the
control-request controller used for staged MCP calls, handoff waits, and
`stop:` signals (`@520685`, `@590390`, `@615219`); it is not the turn
controller `Ee.abortController`. SIGINT is different: it aborts
`Ee.abortController` with `user-cancel` (`@491804`). After SIGTERM the turn
continues until `forceExit` calls `process.exit`; no step awaits it.

**2/3. Foreground and background tools.**

* Foreground shells with `status==="running"` receive `kill()` synchronously in
  the SIGTERM handler and again before and after the hooks (`@80961`).
  `kill()` marks the command killed, settles its result with code 137, sends
  SIGTERM to the tree, and starts a 1500 ms SIGKILL backstop (`@85881`);
  `FSt` awaits that backstop.
* Backgrounded shells are not killed by `Akn` (their status is
  `"backgrounded"`). The exit-handoff cleanup registered by `chunk-jzzwheky.js@35440`
  (`CHt`) detaches them (`vYn`, `chunk-7gqqhxfr.js@6832`: `detach()` unrefs the
  child), aborts workflow and agent controllers with reason `background`,
  waits at most `F=2000` ms for agent transcripts (`chunk-4afqvhsq.js@1967`),
  and writes `adopt.json` for the next wake of the session (`@3677`). If that
  write fails the shells are killed.
* After handoff, any task still `running` that was not handed off is handled
  by `wYn` (`chunk-4afqvhsq.js@5952`): shells are killed; otherwise, if
  shutdown is already committed (`wn()`), the task is only unregistered (`Qp`),
  not aborted and not marked stopped; if not committed it is aborted and a
  `stopped` notification is emitted.
* Foreground non-shell work (a tool call in progress) has no cancellation step
  in `shutdown()`; it is abandoned at `process.exit`.

**4. Awaited versus fire-and-forget.** Awaited, in order: `gpt` (2000 ms
race), `Est`, `FSt`, `eat`, hooks, `mL`, `PDe`, `rPe`, `pwe`, `g2n`, `BDt`.
Fire-and-forget: `Akn` and each `kill()` initiation, `dTe`, `printResumeHint`,
`Son`, `llr`, `Rkn`, and the continuation of any `gpt` callback after its race
timed out.

### Failsafe, forced exit, and what can be abandoned

* The failsafe is a `setTimeout` that calls `dTe()`, `printResumeHint()`,
  then `BDt(500,{scaleBudgetToQueue:false})`, then `forceExit` (`@98517`). It
  can interrupt any `await` in steps 5 to 13. It cannot run while the event loop
  is blocked, and is not armed before step 3.
* `forceExit` runs no async cleanup. Pending promises are discarded. Only
  `process.on("exit")` listeners run, and they are synchronous.
* **Transcript.** The project transcript writer registers `uNs` with `St` when
  it is created (`chunk-phacttch.js@4554487`). `uNs` (`@4553723`) races its exit
  drains for 500 ms, awaits `project.flush()`, awaits `nAn()`, races an
  asynchronous re-stamp for 500 ms, and in `finally` calls the synchronous
  re-stamp `BJr` (`@4552789`). `BJr` is also an `exit` listener, so a forced exit
  still appends the session-metadata re-stamp synchronously. It does not flush
  buffered transcript entries. Because `uNs` is inside `gpt`, its
  `project.flush()` is inside the 2000 ms race. No `preExitFlush` registrant
  and no later awaited step joins that promise, so a flush still running when the
  race times out is not waited for. Whether it finishes depends on how long steps 6
  to 13 take (`INFERRED`); the source prints a warning that entries
  "may be missing from the transcript" when the writer is degraded (`@4553723`).
* **Exit handoff.** Its promise is joined by `Est` (step 7) with no timeout of
  its own, so the effective bound is the re-armed failsafe (at least 15 s).
  Agent transcripts inside it are flushed with a 2000 ms race.
* **Error log, diagnostics, and analytics queues** are drained at steps 11 and
  12 and are all abandoned if the failsafe fires first.
* **Task results** are covered in the compaction and background-notification
  section of `02-cross-subsystem-concurrency.md`.

### Event timelines

| Event | Ordered effects |
|---|---|
| Normal end of a headless run | run finishes and emits result; `Ps(code)` (`chunk-fzzrkchm.js@483089`) then `shutdownSync` then `T8()`, steps 1 to 14 above |
| `end_session` | `endSessionRequested=true`, budget timer cleared, turn controller aborted with `shutdown`, `Yn.abort()`, stdin loop broken (`chunk-fzzrkchm.js@572889`); then `closeInput` (`@79415`) sets `drain.inputClosed`; if a turn is running the close callback returns without teardown (`@658765`); the drain run then calls `onInputClosed` (`@123350`, `@559312`), which runs `Qh` then host teardown `$h` (`@550957`), which ends the output stream `Qt`; the consumer loop in `runHeadless` (`@479791`) finishes and calls `Ps(code)` (`@483089`), which starts `shutdown()`. See "End-session exit chain" |
| SIGTERM (print mode) | `T8()`; synchronous `kill()` of running shells; `Yn.abort()`; `Zn(143)`; handler returns; turn controller untouched; steps 2 to 14 run while the turn continues until `process.exit` |
| SIGTERM (other modes) | generic handler logs, calls `UZ()`, then `shutdown(143)` (`chunk-phacttch.js@93777`); no up-front `Akn` |
| SIGINT (print mode) | if already shutting down, `UZ()` and return; else abort turn controller with `user-cancel`, `Yn.abort()`, `Zn(0)` |
| Failsafe | timer fires: terminal modes restored, hint printed, 500 ms stdout drain, `forceExit` |

### End-session exit chain (resolves the `Zn`/`Ps` caller)

`VERIFIED-STATIC`, scoped to the print host `VL` (`chunk-fzzrkchm.js@483776`).

1. `VL` starts the stdin loop in a detached async function whose rejection goes
   to `r_`, and returns the output stream `Qt` (`@658985`). `runHeadless`
   consumes it with `for await (... of VL(...))` (`@479791`).
2. On `end_session` the loop sets `endSessionRequested`, aborts the turn
   controller with `shutdown`, calls `Yn.abort()` and `break`s (`@572889`).
   Normal stdin EOF ends the loop the same way.
3. After the loop, `closeInput` (`chunk-fzzrkchm.js@79415`) awaits the admission barrier, the
   first-turn gate and any parked frames, sets `drain.inputClosed=true`, then
   runs its callback. The callback runs `Yn.abort()` and **returns without
   teardown when a turn is running or a poll is active**
   (`Ee.running||Yh.pollActive()`).
4. In that case the drain run method finishes the turn, then reaches
   `if(e.inputClosed)await r.onInputClosed()` (`chunk-fzzrkchm.js@123350`). `onInputClosed`
   (`chunk-fzzrkchm.js@559312`) runs `Qh` (`chunk-fzzrkchm.js@549992`), which returns `teardown-now`, or
   `handed-off` while a team or swarm owns teardown, and then `$h`
   (`@550957`).
5. `$h` awaits settles and detaches, disposes subsystems, and ends the stream
   with `Qt.done()` unless the session errored. `$h` itself calls neither `Zn`
   nor `Ps`.
6. The consumer loop ends, `runHeadless` prints the result, awaits `$Xr`, races
   synced-file and agent drains against 5000 ms, and calls `Ps(code)`
   (`chunk-fzzrkchm.js@483089`). `Ps` is `ab().shutdownSync` (`chunk-phacttch.js@105703`):
   `shutdownSync` sets `process.exitCode`, runs `T8()` and starts
   `shutdown(code)`.

Consequence: on the `end_session` and EOF paths the host sequences the aborted
turn **before** `shutdown()`, so `shutdown()` does not need to join the turn
there. The turn is not forced: it ends when the aborted controller is honored.
On SIGTERM and SIGINT the host does not do this, so the earlier timeline
stands (the turn continues until `process.exit`). `Zn` is the async
`shutdown(e,n,r)` wrapper and is used only by the signal handlers in this chunk
(`chunk-phacttch.js@105640`).

### Project writer `flush()` and what survives exit

`VERIFIED-STATIC` for the bodies; behavior under timing is `INFERRED`.

* `flush()` (`chunk-phacttch.js@4572755`) clears the 100 ms flush timer,
  awaits the active drain, calls `drainWriteQueue()`, then loops
  `while(pendingWriteCount>0)` awaiting a resolver that fires only when
  `decrementPendingWrites` reaches zero (`chunk-phacttch.js@4559797`), draining again after each
  wake. It finally throws a stored `storeFence`. It has **no timeout of its
  own**; its only bounds are the 2000 ms `gpt` race and the failsafe.
* Appends are buffered in `writeQueues` and written by `scheduleDrain`
  (`chunk-phacttch.js@4560975`) after `FLUSH_INTERVAL_MS=100`. `drainWriteQueue` (`chunk-phacttch.js@4562109`)
  chains drains, so rows queued but not yet drained are lost if the process
  exits before a flush completes.
* `uNs` additionally awaits `nAn` (`Tnt.settle`, the async-append lane) and a
  500 ms re-stamp race, all inside the same 2000 ms race.
* **Append seal.** `sealAppendsForShutdown` (`chunk-phacttch.js@4582147`) sets
  `appendsSealedForShutdown`; afterwards `enqueueWrite` returns a resolved
  promise without queueing (`chunk-phacttch.js@4560024`) and `shouldSkipPersistence` is true.
  It is reached only through `zJr` (`chunk-phacttch.js@4555416`), wired as the CCR client's
  `onInternalEventLaneClosed` (`chunk-cest8dre.js@52965`), and called from
  `finishShutdown` (`chunk-a5wd77pa.js@95811`) after a 3000 ms flush race.
  `finishShutdown` is a `preExitFlush` registrant
  (`registerShutdownCleanup`, `chunk-a5wd77pa.js@95292`), so it runs in step `g2n`, after the
  cleanup drain. In a remote CCR session, transcript rows appended by a turn
  that is still running after `g2n` are silently dropped (`INFERRED`: depends
  on a turn outliving the earlier steps). Non-remote sessions do not seal.

**Remaining unknowns after this pass.** The value of `Uvr` (the OAuth hold
bound); the completion behavior of the `$Xr` and synced-file drains under a
stuck upload; any non-print-host `St` registrant that joins a turn; and the
crash durability of the 100 ms in-memory write queue beyond the exit paths
read here.

## Confidence ledger

| Finding | Confidence | Evidence anchor |
|---|---|---|
| Detached completion persists and emits a task notification | VERIFIED-STATIC | `chunk-phacttch.js@2216254`, `@2217060` |
| Normal completion is non-passive and priority `next` | VERIFIED-STATIC | `chunk-phacttch.js@2217060` |
| Task notifications are recognized by queue/turn classification | VERIFIED-STATIC | `chunk-phacttch.js@218545` |
| Idle main queue changes invoke the local turn kick | VERIFIED-STATIC | `chunk-fzzrkchm.js@224541`, `@559872` |
| Main drain prevents a concurrent second run | VERIFIED-STATIC | `chunk-fzzrkchm.js@118016` |
| Non-main agent task results can resume the target agent | VERIFIED-STATIC | `chunk-fzzrkchm.js@229359` |
| Attached host returning online can enqueue a model-facing self-wake note | VERIFIED-STATIC | `chunk-fzzrkchm.js@97910`, `@100586`, `@101196`, `@102333`, `@102430` |
| Remote-served background-shell completion uses per-caller ownership and a non-notifying result contract | VERIFIED-STATIC (scoped) | `chunk-bsjqfd0a.js@35653`, `@37213`, `@39490`; registry `chunk-qwgyf6qf.js@4678`, `@5543`; notice `chunk-0j0ezmy7.js@3077` |
| A detached completion always produces a new API request | UNKNOWN | query/stop policy remains conditional at `chunk-93pksqr2.js@134303` |
| Main-session stop-before-request callback is installed by the turn controller | VERIFIED-STATIC | `chunk-9w4htdvs.js@1395543`, `@1413024`; query gate `chunk-93pksqr2.js@134246` |
| A pending deferred background gesture suppresses request preparation | VERIFIED-STATIC | `chunk-9w4htdvs.js@108462`, `@117617`, `@1408892` |
| Draft text cancels the suppression under `tengu_keen_sloth` | VERIFIED-STATIC | `chunk-9w4htdvs.js@108462` |
| Task-notification coalescing can admit a command with `shouldQuery:false` and hold its completion for a later turn | VERIFIED-STATIC | `chunk-fzzrkchm.js@106757`, `@108084` |
| Turn execution still enters `engine.submitMessage`; `shouldQuery:false` is handled concretely by result routing | VERIFIED-STATIC | `chunk-fzzrkchm.js@137755`, `@190435`; `chunk-93pksqr2.js@134246` |
| The positive query path invokes `I.callModel` only after the stop and setup gates | VERIFIED-STATIC | `chunk-93pksqr2.js@134246`, `@153755` |
| Task notifications bypass prompt-submission hooks | CONTRADICTED | `chunk-93pksqr2.js@11147`, `@11874`; `chunk-kgekdqv3.js@7480` |
| `Lp.run`'s `stopping`/`terminalShutdown` are `Ls` (`shutdownInProgress`) and `wn` (process-global committed flag set by `T8`) | VERIFIED-STATIC (scoped) | `chunk-fzzrkchm.js@555196`; `chunk-phacttch.js@105753`, `@100147`; `chunk-80kqkekd.js@150398`, `@150477` |
| `shutdown()` sets `shutdownInProgress` and `T8` before its first await; SIGTERM handler sets `T8` and aborts `Yn` but not the drain controller | VERIFIED-STATIC | `chunk-phacttch.js@101341`, `@97238`; `chunk-fzzrkchm.js@491913`, `@491804` |
| After commit, `xp.take` takes no head, `Xu.isHeld` releases waits, and `xp.exit` zeroes held completion counters | VERIFIED-STATIC | `chunk-fzzrkchm.js@109230`, `@115186`, `@113101` |
| `end_session` aborts the drain controller with a shutdown reason; the child-agent wake router refuses to resume under `endSessionRequested`, `Ls`, `wn`, or budget limit | VERIFIED-STATIC | `chunk-fzzrkchm.js@572889`, `@486420`, `@228384`, `@230910` |
| `shutdown()` does not await or cancel the model turn; no awaited step references the drain or turn controller | VERIFIED-STATIC (scoped to the print-host `St` registrants and `shutdown()` body) | `chunk-phacttch.js@101341`; `chunk-j0pppawn.js@4520`; `chunk-fzzrkchm.js@492154`, `@216079`, `@448241`, `@509305`, `@577365` |
| `gpt` runs registered cleanups concurrently, is raced for 2000 ms, and the loser is not cancelled | VERIFIED-STATIC | `chunk-j0pppawn.js@3916`, `@4461`, `@4520`; `chunk-phacttch.js@101341`, `@105059` |
| `Est` joins only the exit-handoff write promise; `FSt` joins shell SIGKILL backstops (1500 ms); `Akn` is synchronous kill initiation for `running` shells | VERIFIED-STATIC | `chunk-phacttch.js@51131`, `@80875`, `@80961`, `@85881`; `chunk-4afqvhsq.js@5666` |
| SIGTERM does not abort the turn controller; `Yn` is the control-request controller | VERIFIED-STATIC | `chunk-fzzrkchm.js@491913`, `@487609`, `@520685`, `@591948` |
| Exit handoff detaches backgrounded shells, aborts agents/workflows with reason `background`, bounds the agent transcript flush at 2000 ms, writes `adopt.json`; `wYn` unregisters unhanded running tasks without aborting them when shutdown is committed | VERIFIED-STATIC | `chunk-4afqvhsq.js@1967`, `@3677`, `@5952`; `chunk-7gqqhxfr.js@6832`; `chunk-jzzwheky.js@35440` |
| Transcript flush is a `gpt` cleanup inside the 2000 ms race; a synchronous `exit` listener re-stamps metadata only | VERIFIED-STATIC | `chunk-phacttch.js@4553723`, `@4552789`, `@4554487` |
| A transcript flush that outlives the 2000 ms race is joined by no later awaited step | VERIFIED-STATIC (scoped to `St`/`HP` registrants read) | same anchors; `chunk-j0pppawn.js@4667` |
| Whether such a flush completes before `process.exit` | INFERRED (depends on later step durations) | `chunk-phacttch.js@101341` |
| Caller that reaches `Zn`/`Ps` after `end_session` host teardown | VERIFIED-STATIC | `runHeadless` consumes `VL` (`chunk-fzzrkchm.js@479791`, `@483776`); `Ps(code)` at `@483089`; teardown `$h` at `@550957` calls neither |
| External/remote host wake after process exit or outside the served-shell branch | UNKNOWN | inspected local queue, router, turn-drain, and the served-shell owner; no complete external host boundary recovered |

## Bottom line

The local behavior is stronger than the previous report stated: an eligible
detached completion does automatically kick an idle, input-open main loop, and
an attached host returning online has a separate guarded self-wake enqueue.
The remote-served background-shell branch is a separate scoped negative for
local completion notification: it records/settles the remote shell and tells
the session to query the remote target rather than enqueueing the local task
notification. The report remains `PARTIAL` because disconnected-process and
other remote wake, shutdown races, and compaction interaction are unresolved.
