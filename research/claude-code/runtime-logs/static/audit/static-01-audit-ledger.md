# Audit 01: static-01-startup-cli-config.md
Format: report line | claim | anchor | status | reason
Runtime conflicts: none (03-runtime-experiments.md C5-C6c agrees with flag>local>project and settings env over process env; user/managed untested).

## 0 Header / 1 Scope (lines 1-58)
3-9 | Target/labels | n/a | VERIFIED | version 2.1.296, Windows build confirmed (cli header, DD_SOURCEMAP_GROUP win32)
17-38 | read-in-full chunk list (process claim) | no anchors | NOT FOUND | process claim, not source-checkable; all named chunks exist in extracted tree
40-53 | not-reached list incl plist branch compiled out | chunk-wa87dk5k.js@1855 | VERIFIED | NWn returns plistStdouts:null; zMt()=false (chunk-7r9zgs5y.js)
55-58 | tools used / claude not run | none | NOT FOUND | unverifiable process statement
## 2.1 ladder (64-110)
66-73 | 0a NoDefaultCurrentDirectoryInExePath=1 | cli@~1290 | VERIFIED | cli:1332 region
66-73 | 0b COREPACK_ENABLE_AUTO_PIN=0 | cli@~1340 | VERIFIED | write-only, never read (see appendix correction)
72 | 0c VGn sets AI_AGENT claude-code_2-1-296_harness unless foreign value | chunk-cevevzs2.js@2315 | VERIFIED | VGn sets when unset or when starts with claude-code_ / claude-code/; JCo replaces dots with dashes
73 | 0d CLAUDE_CODE_REMOTE==="true" appends --max-old-space-size=8192 | cli@1493 | VERIFIED | exact
75-77 | Bt async ladder cli@2569, argv.slice(2), no await at end | cli@2569 | VERIFIED | function Bt; module ends with Bt(); (no await, no catch)
81 | row1 relay guard: env defined or --session-tunnel, continues | cli@2693 | VERIFIED | import.meta.require chunk-5bjjxefv.js guardRelayTokenDescriptor
82 | row2 --gh-standin parse, port regex, <=65535, refused | chunk-eshh1gca.js@683 | VERIFIED | jSs exact; omitted: it also truncates process.argv to 3 entries and requires non-empty caBundlePath and literal "--" separator
83 | row3 --handle-uri extra arg -> error string exit 1 | chunk-h8tvh2dn.js@615 | VERIFIED | E$n
84 | row4 version-only prints "2.1.296 (Claude Code)" + --verbose Commit | cli@~2900 | PARTIAL | output is VERSION + " (Claude Code)" + QB(); QB() suffix not mentioned/resolved; "zero imports" ok
85 | row5 cwd throws, ENOENT message, cwd_unavailable, exit 1 | cli@4720 | VERIFIED | st() + writeStartupFailureResult
86 | 5a profileCheckpoint cli_entry | cli@~4800 | VERIFIED | v("cli_entry")
87 | 5b pin only if not --preload/--bg-spare and CLAUDE_CODE_HOVER_REST | cli@4906 | VERIFIED | exact
88 | 5c JIT policy timer 10s unref, not for preload/bg-spare | cli@5058 | VERIFIED | setJITPolicy?.(1)
89 | row6 gh-standin policy + ghStandinMain | cli@~5200 | VERIFIED | exact
90 | row7 plugin test | cli@5359 | VERIFIED | REPORT_MARK path, pluginTestMain, endPluginTest all present
91-93 | rows 8-10 eval-mock-server, chrome mcp, native host | cli@6157/6462/6648 | VERIFIED | exact
94 | row11 --daemon-worker | cli@6799 | VERIFIED | policy error to stderr only; sessionFactsRestored; exit code
95 | row12 --bg-pty-host try/catch | cli@7292 | VERIFIED | message text matches
96-97 | rows 13,14 bg-spare, preload | cli@7640/7855 | VERIFIED | exact
98 | row15 remote-control/rc/remote/sync/bridge | cli@8069 | VERIFIED | policy fatal, sessionFactsRestored fatal, startRemoteControl
99 | row16 daemon via $Ss skipping leading skip-permission flags | cli@9780, chunk-w1fy6hed.js@2480 | PARTIAL | daemonMain branch verified; $Ss skip-flag behaviour in w1fy6hed not re-read
100 | row17 bg verbs / --bg | cli@10400 | VERIFIED | verb scan list and behindRootOptions logic exact
101 | row18 fleet gate | cli@13983 | VERIFIED | gate expression and inner flow exact (see 2.1.2)
102 | row19 self-hosted-runner subdispatch | cli@20565 | VERIFIED | orchestrator/setup/doctor/code-sign/decode-token/default
103 | row20 tmux+worktree | cli@21546 | VERIFIED | desktop conflict, eagerLoadSettings, policy fatal, isWorktreeModeEnabled fall-through
104 | row21 --update/--upgrade rewrite | cli@22907 | VERIFIED | exact
105 | row22 --bare before -- sets CLAUDE_CODE_SIMPLE=1 | cli@23044 | VERIFIED | exact
106 | row23 NON_REPL list, mcp serve, plugin(s) eval, rc anywhere, agents --json | chunk-qn110zvq.js@615 | VERIFIED | set = update,upgrade,doctor,forward-home-settings; predicates match
107 | row24 start mdm+keychain, configureZod, import main | cli@23731 | VERIFIED | exact
109-110 | isProjectVerbInvocation constant false | chunk-qn110zvq.js@~640 | VERIFIED | function i(o){return!1}
## 2.1.1 row 17 detail (112-134)
116 | step1 --desktop exits 1 two messages | cli@10400 | VERIFIED | at(t)
117-118 | step2 eager parse --settings/--managed-settings when x>0 | cli | VERIFIED | eagerParseCliFlag
119-120 | step3 tolerant verbs logs,stop,kill,rm | cli | VERIFIED | exact
121-122 | step4 sessionFactsRestored semantics | cli | VERIFIED | exact
123 | step5 ensureFleetGateHydrated, fleetGateRejected | cli | VERIFIED | exact
124-126 | step6 handler map, kill->stopHandler, default tengu_background/handleBgFlag | cli | VERIFIED | exact
127-128 | step7 flush race 500ms then exit(exitCode??0) | cli@~12600 | VERIFIED | both arms
130-134 | eRo verb index rules, refusal set | chunk-rb1fj9a1.js@4799 | VERIFIED | regexes, sets u,p,m,g match; short-cluster rule exact
## 2.1.2 row 18 detail (136-166)
140-144 | Yat hand parser option list | chunk-w1fy6hed.js@615 | VERIFIED | exact incl --setting-sources dropped
145 | restricted env 1/true/yes/on case-insens trimmed | cli@13887 | VERIFIED | exact
146-148 | xt dispatch defaults | cli@~1700 | VERIFIED | exact
149-150 | nt debug-flag-only | cli | VERIFIED | exact
151-153 | T and outer gate precedence | cli@13983 | VERIFIED | exact
154-157 | inner block, defaultToAgentsView, throw swallowed | cli | VERIFIED | exact
158-164 | P path: settings, plugin dirs, policy fatal, PLUGIN_DIRS, sideload, fleet enabled -> mount, shutdown(0) | cli | PARTIAL | verified, but omits fatal sessionFactsRestored after the fleet gate and ensureFleetGateHydrated before isAgentsFleetEnabled
165-166 | setIsInteractive(true), agents_view | cli@~16000 | VERIFIED | ht(!0), _t("agents_view")
## 2.2.1-2.2.2 (170-207)
172-179 | Commander.js evidence | chunk-jzzwheky.js@41068/41191 | VERIFIED | enablePositionalOptions, hook preAction at those offsets; library version UNK stays UNK
185-188 | module-top debugger exit; Pi() detail | chunk-zvnaqyp5.js@35970 | VERIFIED | ZE() is constant true in this build so execArgv regex is --inspect only; NODE_OPTIONS regex and inspector.url as stated
189-191 | Cn(): warning handler dedupe 1000 keys, tengu_node_warning, timer proxy clamp | @30304 | PARTIAL | warning handler verified; timer wrapper fn() seen only as fragment
192-193 | exit handler writes terminal reset | @37760 | VERIFIED | process.on exit Ui(); TTY choice detail not re-read
194-195 | --handle-uri main branch | @37857 | VERIFIED | exact
196-197 | W7o import shorthand rewrite | @~38000 | VERIFIED | rewrite or config-error
198 | vn({interactivity detect}) | | VERIFIED | exact
199-204 | Ni 3 parse strategies; -p without cc:// parses early | @38620/@~39130 | VERIFIED | D&&!U and !nRo(T)&&!U exact
206-207 | claude -p mcp treats mcp as prompt | none | PARTIAL | follows from code (no registration) but never run; open Q7 untested
## 2.2.3 preAction (209-237)
213 | step1 desktop+subcommand exit | @41191 | VERIFIED | exact
214-215 | step2 early initialize read | | VERIFIED | mUo(Epn) conditions exact
216-217 | step3 await Ddt/Atn, pre_action_mdm_keychain_ms | | VERIFIED | exact
218-219 | step4 project-config-root 3 messages | @41848 | VERIFIED | exact
220-221 | step5 init memoized uOr | | VERIFIED | exact
222 | step6 process.title unless CLAUDE_CODE_DISABLE_TERMINAL_TITLE | @43324 | VERIFIED | exact
223-226 | steps7-9 initSinks, gUo violation, inline plugins | | VERIFIED | exact
227 | step10 migrations Rr(s) | @44082 | VERIFIED | exact
228-231 | step11 managed gates incl version_below_minimum listed before sideload | @46250 | PARTIAL | ORDER: in code version_below_minimum (gbs) runs AFTER CLAUDE_CODE_PLUGIN_DIRS inline plugins and the sideload check (DQ), not before; same order error in 3.2 pseudo-code lines 1204-1205
232-234 | step12 sideload policy and its flag list | | PARTIAL | list also includes "plugins (initialize request)" and the CLAUDE_CODE_PLUGIN_DIRS inline-plugin merge, omitted
235-236 | step13 early plugin kick conditions | | VERIFIED | exact
237 | step14 markStartupActionStarted | | VERIFIED | IQr(q)
## 2.2.4 subcommands (239-271)
243-267 | subcommand table | zvnaqyp5 anchors | PARTIAL | gateway, mcp, auth, setup-token, agents, purge, ultrareview, auto-mode, import-conversations, edit-hook (524288 cap) present and verified; update/install/sandbox/doctor/rc/ project purge rows checked by name only, flags not each compared
248 | HDr registered commands "Not read" | | VERIFIED | honest unknown
262 | XJt apply-project-settings | chunk-w8x21rf4.js@~1660 | VERIFIED | lbr() tests argv[2]==="apply-project-settings"
269-271 | withStorageV5/withStartupHandles wrappers | chunk-jzzwheky.js@~41130 | VERIFIED | h and w closures exact
## 2.2.5 root options (273-381)
278-374 | 128 flag names | chunk-jzzwheky.js@46900..70680 | PARTIAL | all 128 reported names occur in registration slice; no missing root option (--routine appears only inside help text; --append-subagent-system-prompt-file covered by abbreviation line 315); defaults/choices/parsers not each re-checked
376-381 | arity table in rb1fj9a1 incl --routine,--exec/-m,--hard-fail,--project | chunk-rb1fj9a1.js@~620 | VERIFIED | sets i,p,m,u present; --hard-fail in p, --exec/-m/--handle-uri in m, --routine in u
## 2.2.6 flag consumption (383-404)
389 | -p read three times | | VERIFIED | u8e, Ni, _Hr
390-391 | --output-format / --input-format behaviours | @123059 | VERIFIED | validation messages match
392 | resume/continue validation zs | | VERIFIED | zs @58073 matches
393-401 | model, permission-mode, settings, mcp-config, agents, prompts, tools, add-dir | | PARTIAL | call shapes (bhs cli/env/settings) verified; inner precedence not read
402 | --bare sets CLAUDE_CODE_SIMPLE twice | @104629 | VERIFIED | cli row22 and _Hr o.bare
403 | --safe-mode env | @104672 | VERIFIED | Rr() sets SAFE_MODE and DISABLE_CLAUDE_MDS
404 | debug flags read from raw argv by logger | chunk-j0pppawn.js@49069 | VERIFIED | debugFromLaunch field present
## 2.3 interactivity (406-467)
408-419 | u8e predicate, rpt skips values, stops at -- | chunk-rb1fj9a1.js@3293 | VERIFIED | exact
421-424 | stdin not part of predicate | | VERIFIED | follows from u8e
425-427 | stream-json does not imply non-interactive; requires --print | @123197 | VERIFIED | message "requires --print."
428-431 | evaluated once in vn; zxo -> replaceIsInteractive; ke() | @31188,@93505,@92737 | VERIFIED | all three functions found
432 | non-interactive calls sK() = stopCapturingEarlyInput | | PARTIAL | sK() call verified; name equivalence not verified
433 | --sdk-url forces print/stream-json/verbose | @107781 | PARTIAL | not re-read
435-439 | client type ladder | @~31700 | PARTIAL | order exact; "any session-ingress token source" is also conditioned on CLAUDE_CODE_REMOTE && (qc()||NY()) for one arm
441-457 | _Hr result kinds, exited when process.exitCode set, Li/Fi/LL(true)/JC | @145558,@136534 | VERIFIED | kind exited guarded by process.exitCode; prepared-headless/interactive exact
459-467 | piped stdin Rs: not TTY, not mcp, stream-json, 10MiB cap, 3000ms peek | @21563,@21092 | VERIFIED | Ts=10485760, zon(stdin,3000), warning text
## 2.4.1 source list/merge order (471-495)
473-482 | ws list, lRr loop, later wins, order | chunk-db4p09wg.js@3859, ff982hys@428702 | VERIFIED | exact incl pluginBase first
484-485 | pluginBase | | VERIFIED | e.store.pluginBase
487-488 | Hv labels | @~3990 | VERIFIED | user, project, project gitignored, cli flag, managed
490-492 | cached mergedSettings, re-entrancy guard | chunk-mx6ygzc6.js@96849,@97163 | VERIFIED | _g(), isLoadingFromDisk guard
494-495 | bO(key) highest to lowest | @97051 | VERIFIED | exact
## 2.4.2 merge semantics (497-521)
501-507 | UY customizer table | chunk-ff982hys.js@428331 | VERIFIED | exact
509-512 | L = unique, A1 = lodash mergeWith (labelled SI) | | VERIFIED | stronger than SI: L=[...new Set], A1=createAssigner(baseMerge) (ff982hys@343959..344011); label can upgrade to VS
514-517 | policy overrides and deniedModels | @~430700 | PARTIAL | availableModels/enforceAvailableModels/modelPicker overwritten only if policy tier present (correct) BUT deniedModels is deleted whenever policy does not define it, even when NO policy tier exists (delete sits outside if(w))
519-521 | sandbox managed-only note | | VERIFIED | allowManagedReadPathsOnly / allowManagedDomainsOnly statusOnly warnings exact
## 2.4.3 file paths (523-561)
525-526 | ctx.cwd Gl, projectConfigDir, configHome ve() | | VERIFIED | M() context builder
528-535 | path table per source | @400947,@398269,@401359 | VERIFIED | $nn/Dz/Sse/EO exact
530 | cowork_settings.json | | VERIFIED | k_()
537-541 | RF canonical root, POSIX-only; SI for Windows | | PARTIAL | message verified; omitted: also requires root, .git and .claude entries owned by current uid; returns cwd when root equals cwd or real home dir; Windows consequence still SI/untested
543-544 | no upward walk | | VERIFIED | projectSettings = projectConfigDir ?? cwd
546-548 | project tier skipped when equal to user path, cited S_() | chunk-mx6ygzc6.js@~88200 | PARTIAL | effect real but via path dedupe Set c in lRr (if !c.has(K)); S_() is used only for as_read/warning/audit loops (@87931,@110182,@111758), not the merge skip. Cite is wrong
550-559 | configHome: CLAUDE_CONFIG_DIR else ~/.claude (SI) | chunk-g17170nn.js ve | PARTIAL | now VS: ve=(CLAUDE_CONFIG_DIR ?? join(homedir,".claude")).normalize("NFC"); uses ?? (empty string kept) whereas global config file uses || ; NFC omitted
561 | settings size limit 2 MiB | @394710 | VERIFIED | Of=2097152
## 2.4.4 managed settings (563-627)
567-577 | My() dirs mac/win/other; WSL path; ZT() SI | @360397,@830 | VERIFIED | My() exact; ZT()=Ad.getManagedFilePath()=cached My() is statically proven, SI should be VS (open Q2 partly resolved)
579-583 | managed-settings.json then d/ sorted .json files, ENOENT silent | @388896 | VERIFIED | fEo, h$s (file or symlink), cZ (.json, no leading dot)
585-596 | MDM reg.exe, keys, 5000ms, windowsHide, 2 MiB, WSL dead branch | @1855,@2119 | VERIFIED | exact; zMt()=false
598-600 | macOS UNK | | VERIFIED | honest
602-603 | remote V8 @392680 | | PARTIAL | not read
605-607 | parent slice invalid JSON ignored+warning+flag | @2516 | VERIFIED | vFs; flag name parentManagedSettingsInvalid not verified (TPo)
609-610 | policy helper tier/remoteSlot | | VERIFIED | v0(e).composes
612-624 | composition IA/nPs | @410081,@424599 | PARTIAL | HKCU-only-when-no-admin, parent slice under admin A1({},c,d,UY), env union verified; parent-slice gating is S$s(Ie,he) (true when no admin tier OR merge OR flag), more than stated
625-627 | user-writable keys stripped warning | chunk-mx6ygzc6.js@~9700 | VERIFIED | message text found at 9700
## 2.4.5-2.4.6 flags (629-667)
631-634 | Uvo errors and caller | @5100 | VERIFIED | exact
636-638 | default allowed all five; flag/policy re-added | @62996 | VERIFIED | dn(); No()
640-646 | cbr narrowers | @3114 | VERIFIED | restricted -> [] ; apply-project-settings; workspace restriction not re-read
648-649 | forwarded --setting-sources only if differs | @~5350 | PARTIAL | g() compares against 3 user/project/local sources; Kue returns undefined when restricted (aw())
653-663 | wFs inline JSON/path handling | @1652 | PARTIAL | verified; "C1 controls escaped" is regex [\u007f-\u009f] which also includes DEL 0x7F
665-667 | yfo eager load, UA last wins | @2888 | PARTIAL | UA internals not read
## 2.4.7 env vs settings (669-684)
671-675 | cli>env>settings consumer calls | @~112200,@~134000 | PARTIAL | bhs call shape verified; order inside unread (labelled SI)
676-682 | two-phase env apply; safe during init | | PARTIAL | ioe() is called in preAction after init (not inside init); full set via JC after trust verified (EUs)
683-684 | getPreSettingsEnvSnapshot | | VERIFIED | export name only (as stated)
## 2.5 global config (686-759)
690-702 | globalConfigFile logic | chunk-47shaprq.js@4536 | VERIFIED | Tt()/GAr() exact; legacy .config.json first
704-705 | asymmetry home vs .claude | | VERIFIED | exact
709-718 | global config keys | | PARTIAL | key names not each grepped
720-723 | division of labour (SI) | | VERIFIED | labelled inference
727-745 | saveConfigWithLock steps | @582684 | VERIFIED | retry delays, jitter, 1500/30000 boot signal, >100ms, stale stat, re-read [50,150,450], auto-repair, same-ref return false
747-748 | RMW not last-writer-wins | | VERIFIED | exact
750-753 | fallback Rl, mode 384, skip when lock held | @~579900 | VERIFIED | Al(), Cl()
755-756 | backups 60000ms keep 5 | @580861 | VERIFIED | Uw=60000,Bw=5
758-759 | enableConfigs callers | @591409 | PARTIAL | fleet/deep-link callers verified, init/ensureFastPath not re-read
## 2.6 env vars (761-844)
763-767 | typed registry, D.bool/str/int/enum/triBool, SPe accessor | @68833 | PARTIAL | verified; D.rawStr() parser also exists (unmentioned); a=SPe(Zx,p) exact
769-775 | counts 1,121 / 416 / 118 / 1,244 | | PARTIAL | 1,121 typed entries in chunk-47shaprq VERIFIED; 416 distinct process.env names recomputed = 416 VERIFIED; 118 raw-only and union 1,244 consistent with appendix rows (my own looser registry approximation gave 115, not exact)
779-835 | startup control-flow variable table (57 rows) | various | PARTIAL | spot-verified: REMOTE, CCR_AGENT_PROXY, HOVER_REST, SANDBOXED, CLAUBBIT, IS_DEMO, BRIDGE_REATTACH, BG_BACKEND, MESSAGING_SOCKET/TOKEN unset, STARTUP_FAILURE_RESULTS, JOB_DIR, SUPERVISED=70, DEBUG, CLAUDE_DEBUG, RESTRICTED, SIMPLE/SAFE_MODE/DISABLE_CLAUDE_MDS, USE_POWERSHELL_TOOL; ~30 other rows not individually checked
820 | USE_POWERSHELL_TOOL=0 on Windows w/o Git Bash fatal | chunk-we7c2g4z.js@9176 | PARTIAL | true, but a second fatal shell_tool_missing path exists (YR()===null) not mentioned
837-840 | self-set env list | | VERIFIED | consistent with code
842-844 | telemetry allow-list 33 names set li | @27885 | PARTIAL | set li exists; count 33 and "other" mapping not recounted
## 2.7 cwd/trust (846-954)
850-859 | project state, we/cr/zA, Wi(mOo) | chunk-w3dhb84t.js@~76700 | VERIFIED | Wi(e=mOo()) project originalCwd/projectRoot/cwd
861-864 | AsyncLocalStorage Wm | chunk-qh8hnnnf.js | VERIFIED | Wm(e,o) t.run({cwd:On(e)})
866-868 | Vm chdir + tolerant cwd | @79946 | VERIFIED | exact
872-885 | cwd change points | | PARTIAL | setup op(cwd), Can't access working directory, setcwd, worktree git-repo requirement, main-root resolution verified; deep-link steps and teleport chdir located but not fully read
887-889 | Node >=22 | @18035 | VERIFIED | exact
893-896 | git root usage | | PARTIAL | call-site claims not re-read
900-928 | trust check ks/XB/walkUp, lO | @560518,@563559 | VERIFIED | exact incl lO()=ke()?true:ks(); walk-up body (kw/Cw) partially read
930-932 | trust dialog second step, UGo | chunk-45qan3kr.js@8638 | VERIFIED | UMs step list: onboarding, trust (CLAUBBIT skip, UGo)
934-946 | trust-gated behaviours table | | PARTIAL | applyConfig/JC after trust, loadHooksModulesHeldForTrust, post-trust re-discover verified; others unread
948-950 | background never shows dialog | @~7700 | VERIFIED | message text exact
952-954 | -p skips dialog | @47416 | VERIFIED | help text matches
## 2.8 shutdown (956-1052)
958-960 | Ies, PQr, install idempotent | @91889,@105399 | VERIFIED | installed flag
964-974 | handler table SIGINT/TERM/BREAK/HUP codes | @94151,@94347 | VERIFIED | 0,143,0,129 exact
976-978 | orphan check 30s, 129 | @100195 | VERIFIED | exact
983-1004 | shutdown sequence 16 steps | @101341 | VERIFIED | order matches code incl failsafe max(5000,S+5000), DZ 2000 race, Est/Akn/FSt/eat, removeWorktree, hooks, Son, OAuth wait, flush, finalMessage, rPe/pwe, drain+1500, forceExit
1006-1013 | forceExit, failsafe, gracefulShutdownSync | @93131,@98517 | PARTIAL | shutdown body verified; forceExit/armShutdownFailsafe bodies not re-read
1015-1017 | resume hint | | PARTIAL | not re-read
1021-1032 | uncaught/unhandled behaviour, breaker 10/5000/3, http2 50/60000, watchdog 10000 | @91759 | PARTIAL | constants PHn=10,fAe=5000,MHn=3,RNs=50,ANs=60000,PNs=1e4 verified; unhandledRejection swallow list and supervised->70 verified; background->1 not fully read
1036-1039 | cleanup registries | @~4470 | PARTIAL | DZ=2000 verified (chunk-j0pppawn @4465)
1043-1052 | exit code table | various | PARTIAL | 70 (UWn), 75 (vxe), 78 (C1), 2 (unknown worker kind, g72zgfkm@14931), 129, 143 verified; an() verified; line 1045 offset approximate
## 2.9 error propagation (1054-1108)
1058-1063 | four exit helpers an/qo/xo/O8e | @796,@1289,@1234,@4194 | VERIFIED | exact
1065-1067 | other exitWithError in naj6e7dq (kUs) | | VERIFIED | export kUs as exitWithError
1069-1073 | exit-cause/exit-detail causes | @795..1000 | VERIFIED | Ky(); P=200; names present
1075-1091 | startup failure frames | @1307,@1145,@854 | VERIFIED | gate (nBe && stream-json && writable), 1000ms wait, session-id logic exact; reason strings found
1093-1097 | init error handling | @~9900 | VERIFIED | bg error stderr+Ps(1); qA config error dialog else message; rethrow
1099-1102 | Bt without catch | | VERIFIED | cli ends with Bt();
1104-1108 | invalid settings dialogs | | PARTIAL | not re-read
## 2.10 children (1110-1129)
1114 | MDM reg spawns, timeout, memoized | @1855 | VERIFIED | m() execFile timeout KAs, windowsHide, maxBuffer
1115 | Keychain prefetch Bun.secrets, #m manifest, 256x2400, 10s | @1118..2300 | VERIFIED | exact; macOS security spawn d() present
1116-1121 | stdin capture, JIT timer, preload children, daemon supervisor | | VERIFIED | consistent with code
1122 | hooks worker URL, SharedArrayBuffer | chunk-phacttch.js@1834264 | PARTIAL | HOOKS_WORKER_URL and SharedArrayBuffer exist; offset content not matched
1123-1127 | background housekeeping, UDS inbox, tmux, prefetch throttles | | PARTIAL | startCrossSessionInbox, tengu_cicada_nap_ms, startupPrefetchedAt present; tmux kill-on-chdir-fail not checked
1128-1129 | no daemon on plain launch (SI) | | VERIFIED | labelled weak
## 3 reconstructed flow (1131-1358)
1137-1174 | ladder pseudo-code | | VERIFIED | matches Bt
1176-1216 | main/run/preAction/action pseudo-code | | PARTIAL | ordering error inherited from 2.2.3 (sideload vs version gate); rootAction desktop branch not re-read
1218-1241 | prepareSession condensed | | PARTIAL | high-level; exited branch verified
1243-1334 | state machine | | PARTIAL | mirrors above; same ordering caveat
1336-1356 | settings load flowchart | | VERIFIED | matches lRr (deniedModels delete caveat in 2.4.2)
## 4 data contracts (1360-1508)
1365-1381 | FleetArgvParse | chunk-w1fy6hed.js@615 | VERIFIED | fields exact (settingSources only added later by Xat input)
1383-1391 | DispatchDefaults | cli@~1700 | VERIFIED | exact
1393-1399 | GhStandinArgs | | VERIFIED | exact
1401-1404 | SettingSource | | VERIFIED | exact
1406-1426 | SettingsContext | chunk-mx6ygzc6.js@86898 | PARTIAL | M() fields match; omits helperArmedFromRemote, helperMergesOutput, helperWarnings, helperArmedFromUserWritableBase, credentialHelperKeysFrom, launchFolderKeysFrom
1428-1441 | SettingsResult/Error | @~360700 | VERIFIED | Iy destructuring fields match
1443-1455 | MdmRawRead / SpawnOutcome | | VERIFIED | statuses ok/spawn_error/timeout/killed/exited
1457-1465 | StartupFailureResult | @1145 | VERIFIED | exact
1467-1485 | PreparedSession | | VERIFIED | names match
1487-1492 | ShutdownOptions | | VERIFIED | consistent with shutdown(r) usage
1494-1508 | GlobalConfigSlice (proposed) | | VERIFIED | labelled proposed
## 5 constants (1512-1561)
1516 | version/build/sha | cli@~2900 | VERIFIED | exact values
1517-1560 | 46 constant rows | various | PARTIAL | verified exact: 8192, 1e4 JIT, 500, 10485760, 3000, 524288, 2097152, 5000/2097152 reg, [200..4000], 1500/30000, [50,150,450], [30000,120000], 100, 60000/5, 384, Node 22, 1000, 200, 262144/30000, 2000/250, 600000, 30000 orphan, 1e4 mount grace, 10/5000/3, 50/60000/10, 15000, 1500, 2000; not rechecked: 512 truncation, 1,500 chrome scan, 5,000 artifact roster, uncaught text caps, 65,536 read cap
## 6 open questions (1565-1615)
1567-1615 | 16 planned experiments | none | NOT FOUND | forward-looking, no claims; Q2/Q5 partly answerable statically (ZT cached, project cwd-only)
## Appendix (1619-2945)
1621-1629 | method and totals | | PARTIAL | arithmetic 1126+118=1244 VERIFIED; method (1) says every export in chunk-47shaprq.js but 5 typed rows are anchored in other chunks (MCP_SERVE_TOOL_OUTPUT in chunk-pqa8vhhw.js, MESSAGING_SOCKET/TOKEN in chunk-qa64skwy.js, TETHER_LIVE, CCR_AGENT_PROXY_TOKEN_FILE_DESCRIPTOR absent from chunk-47shaprq)
1626-1627 | everything is read by shipped code | | CONTRADICTED | 8 raw-only rows are write-only in shipped code: COREPACK_ENABLE_AUTO_PIN (line 2738) and 7 SELF_HOSTED_RUNNER_* timeout vars (lines 2462,2463,2472,2475,2477,2482,2483, chunk-g8typhpc.js); line 1757 CLAUDE_CODE_COORDINATOR_MODE first cited site is a write (other read sites exist)
1634-2940 | 1244 inventory rows | | VERIFIED | machine check: all 1244 rows parse; 1126 typed rows match getter ident = D.type( at cited offset (or noted other chunk), constraints match; 118 raw rows have name at cited site except 9 write sites above; group headers sum to 1244


## Counts (claim groups, 198 rows): {'VERIFIED': 146, 'NOT FOUND': 3, 'PARTIAL': 48, 'CONTRADICTED': 1}
