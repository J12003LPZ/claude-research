# 01. Repository exploration and code understanding

Target: Claude Code CLI 2.1.296, extraction `extracted/2.1.296/~BUN/root`. Scope: how the CLI discovers, searches, reads and
summarizes a repository before it changes code. Not covered here: model routing (report 02), compaction (report 03), the
consolidated workflow (final report).

## 0. Evidence base

| Source | What it is | Label it supports |
|---|---|---|
| `chunk-x.js@offset` anchors | Static reads of full function bodies in the extraction. Each anchor named in section 12 is pinned in `final-runtime-control-decompilation/13-source-pins.json` (literal text must start at the offset). | VERIFIED-STATIC |
| E90 series (this report) | Scripted runs of the pinned 2.1.296 binary against the lab proxy. The proxy answers every `/v1/messages` with a canned reply, so the real tools run and no upstream model is called. Builders: `tools/scenarios/build_e90.py`, `run_e90.sh`, `run_matrix_e90.py`. Sanitized summaries: `runtime-logs/E90*/exploration-probe.json` (`tools/exploration_probe.py`, tests in `tools/test_exploration_probe.py`). | VERIFIED-RUNTIME |
| E50 series (earlier) | Scripted runs of the Explore child and the system prompt layout by model. | VERIFIED-RUNTIME |

These runs show what the local tools return. They say nothing about how a real model uses the tools.
The lab projects are synthetic. Side effects outside the repository: lab projects under `C:/Users/sergi/cc-rea-lab/proj-e90*`
(two of them hold 40,000 small files) and session files under the Claude config directory, which the lab points at, as in the E50 runs.

Labels: VERIFIED-STATIC, VERIFIED-RUNTIME, VERIFIED-BOTH, INFERRED, HYPOTHESIS, UNKNOWN, CONTRADICTED.

## 1. Answers to the seven questions

| # | Question | Answer | Label |
|---|---|---|---|
| 1 | How does the CLI search for files and symbols? | With three read-only tools driven by the model: `Glob` (file names), `Grep` (ripgrep over contents), `Read` (file bodies). A fourth, `LSP`, exists but works only when a language server was configured by a plugin or setting. A built-in `Explore` subagent wraps the same tools. No index is consulted. | VERIFIED-BOTH |
| 2 | How do Glob, Grep and Read validate, limit and truncate? | Section 3 to 5. Glob stops at 100 paths. Grep stops at 250 lines or entries per call and after 20 s of ripgrep. Read returns the whole file up to 256 KB and 25,000 estimated tokens, with no 2,000-line cap. | VERIFIED-BOTH |
| 3 | How is Explore configured, prompted, restricted, invoked? | Section 7. Inherited model (capped at Opus family on first-party), 13 tools, Edit/Write/NotebookEdit/Agent removed by code, Bash kept and limited only by prompt, invoked only when the model chooses the Agent tool. | VERIFIED-BOTH |
| 4 | How do results reach the model or parent? | As `tool_result` strings in the next request. Oversized Grep output is replaced by a pointer and a 2 KB preview. A truncated Read adds a code-generated notice whose placement depends on the model. An Explore child returns its final message to the parent. | VERIFIED-BOTH |
| 5 | How are large repositories and big output handled? | Count and byte caps, a ripgrep timeout that returns partial results without a warning, a 20 MB output buffer, later clearing of old tool results. No sampling, ranking or repository map. | VERIFIED-BOTH |
| 6 | What is enforced in code and what is model choice? | Section 10. Code: tool caps, read-only tool set for Explore, read-before-edit for a fixed list of older models. Model choice: whether to explore at all, what to search, when to call Explore, how many queries. | VERIFIED-BOTH |
| 7 | Is there a persistent code graph, symbol index or dependency analysis? | None found. Negative scope in section 9. | INFERRED (bounded negative) |

## 2. The exploration tool set

| Tool | Definition | Read-only | Concurrency safe | `maxResultSizeChars` | Notes |
|---|---|---|---|---|---|
| Glob | `chunk-phacttch.js@762295` | yes | yes | 100,000 | `backgrounding:"never"`; remote-executable |
| Grep | `chunk-phacttch.js@768520` | yes | yes | 20,000 | `strict:true`; input coercion `MAt` at `@764561` |
| Read | `chunk-phacttch.js@3541060` | yes | yes | `Infinity` (`1/0`) | never persisted to a file; excluded from the aggregate budget |
| LSP | `chunk-rpwh4z9c.js@106593` | yes | yes | 100,000 | `shouldDefer:true`; enabled only after a server connected (section 9) |

`isConcurrencySafe` and `isReadOnly` are `true` on Glob, Grep and Read (same definitions). Whether the model batches parallel exploration calls is
model choice; the system prompt text only says that independent calls may run in parallel.

All three tools ask the permission layer first. Read-deny rules are enforced twice for Grep and Glob: they are turned into ripgrep
exclusion globs, and results are filtered again after the search (`chunk-phacttch.js@772316`, `@756830`). **VERIFIED-STATIC** for the structure,
**UNKNOWN** for the exact glob text produced.

## 3. Glob

Defined at `chunk-phacttch.js@762295`; the search is `SAt` at `@756278` and its ripgrep call `Pno` at `@756830`.

**Static (VERIFIED-STATIC).**

* The command is `rg --files --null --glob <pattern> --sort=modified`, plus `--no-ignore` and `--hidden`. Both flags are on by default: the
  environment values `CLAUDE_CODE_GLOB_NO_IGNORE` and `CLAUDE_CODE_GLOB_HIDDEN` default to `"true"` (`@756830`). So `.gitignore` is not
  honored and hidden paths are listed.
* The limit is `globLimits.maxResults` or 100 (`@763672`). The result carries `totalMatches` and `countIsComplete`. The model-facing text is
  `(Showing N of M matching files; K more are not listed. Narrow the pattern or path to see the rest.)` (`@761443`), or a shorter note when the count is a floor.
* A missing `path` raises `Directory does not exist: <path>. Note: your current working directory is <cwd>.` and adds a `Did you mean` suggestion when
  a similarly located path exists (`xse`).
* The Glob command does not exclude VCS directories. Grep does (section 4).

**Runtime (E90a, VERIFIED-RUNTIME).** Project: 130 files `src/f000.txt` to `f129.txt` with ascending modification times, plus a gitignored
directory, `node_modules` and a hidden directory, each holding one `.txt` file.

| Call | Result |
|---|---|
| `**/*.txt` | 100 paths, `src/f000.txt` first and `src/f099.txt` last, then `(Showing 100 of 133 matching files; 33 more are not listed. ...)` |
| `**/*.txt` with a missing `path` | error, `Directory does not exist: ... Note: your current working directory is ...` |
| `src/f00*.txt` | 10 paths, `f000` to `f009` |
| `**/*.zzz` | `No files found` |
| `**/HEAD` | `.git/HEAD` |
| `.git/**` | 18 paths including `.git/description` and `.git/config` |

What this shows:

1. The total of 133 includes the gitignored file, the `node_modules` file and the hidden file. Glob ignores `.gitignore`.
2. The order is oldest first. The 33 omitted paths are the newest ones: `f100` to `f129` and the three files created last.
   A repository with more than 100 matches loses its most recently modified files first. The tool description says only "sorted by modification time".
   The direction is the ripgrep behavior of `--sort=modified` (ascending); the runtime run fixes it for this build.
3. `.git` internals are searchable through Glob.

## 4. Grep

Defined at `chunk-phacttch.js@768520`; validation at `@770617`; execution `Xno` at `@772316`; the ripgrep runner `gre` at `chunk-4gghv5aa.js@803919`
and its process spawn `YB` at `@800105`.

**Static (VERIFIED-STATIC).**

* Parameters: `pattern`, `path`, `glob`, `type`, `output_mode` (`content`, `files_with_matches`, `count`), `-A/-B/-C/context`, `-n`, `-i`, `-o`,
  `head_limit`, `offset`, `multiline`. `validateInput` requires `head_limit` and `offset` to be whole numbers of 0 or more
  (`head_limit must be a whole number of 0 or more, got -1. Pass 0 for unlimited.`).
* The command always includes `--hidden`, excludes `.git`, `.svn`, `.hg`, `.bzr`, `.jj`, `.sl` (`@767903`), caps each line at 500 columns
  (`--max-columns 500`), and leaves ripgrep's own ignore handling on, so `.gitignore` is honored.
* Default `head_limit` is 250 (`@767948`); `0` means unlimited; `offset` skips entries first (`INe`, `@767956`). Pagination is applied to the
  lines or entries after the search finished, not inside ripgrep.
* For `files_with_matches` the code `stat`s every file and sorts by modification time, newest first, before applying `head_limit`. For `content` and `count`
  the order is ripgrep's own order (no `--sort`).
* A matching line longer than 500 characters is replaced by `[Omitted long matching line]` in content mode (`Zno`, `@777984`).
* The model-facing notes are `[Showing results with pagination = limit: N, offset: M]` and `Found N total occurrences across M files.`
  (`@769615`).
* Input coercion (`MAt`, `@764561`) rewrites `file_path` to `path`, `-l` to `output_mode:"files_with_matches"`, `-c` to `"count"`, and drops `-r`,
  and prepends a `Note:` to the result saying what it changed. This is a small recovery path for wrong parameter names.
* The ripgrep runner kills the process after 20 s (60 s under WSL), or after `CLAUDE_CODE_GLOB_TIMEOUT_SECONDS`, and caps stdout at
  20,000,000 bytes (`@788791`). On a timeout or buffer overflow with no results it throws `Ripgrep search timed out after 20 seconds ...`.
  **With some results it drops the last, possibly cut, line and returns the rest as if complete.** On `EAGAIN` it retries once with `-j 1`.

**Runtime (E90b, E90h, E90i, E90j, VERIFIED-RUNTIME).**

| Call | Result |
|---|---|
| `needle`, `content` | 250 lines, then `[Showing results with pagination = limit: 250]` (the project holds 3,004 matching lines) |
| `needle`, default mode | `Found 4 files`: hidden `.hid.py`, `long.txt`, `b.py`, `a.py`. The gitignored `ig/c.py` is absent. Hidden file present. Newest first. |
| `needle`, `count` | per-file counts in ripgrep order, then `Found 3004 total occurrences across 4 files.` |
| `content`, `head_limit:0` | 62.4 KB of output, replaced by `<persisted-output> Output too large (62.4KB). Full output saved to: ...` and a 2 KB preview |
| `content`, `offset:250`, `head_limit:5` | lines 251 to 255, `[Showing results with pagination = limit: 5, offset: 250]` |
| `head_limit:-1` | `<tool_use_error>head_limit must be a whole number of 0 or more, got -1. Pass 0 for unlimited.</tool_use_error>` |
| missing `path` | `Path does not exist: ... Note: your current working directory is ...` |
| pattern `(` | `Search failed ... ripgrep rejected the pattern, glob, or file type without searching:` plus ripgrep's message |
| line of 800 characters | `long.txt:1:[Omitted long matching line]` |
| `head_limit:0`, 700 matching lines (16,691 characters) | inline |
| `head_limit:0`, 1,300 matching lines | persisted (`<persisted-output>`) |
| 40,000 matching files, `count`, default timeout | `Found 40000 total occurrences across 40000 files.` |
| same project, `CLAUDE_CODE_GLOB_TIMEOUT_SECONDS=1` | `Found 9611 total occurrences across 9611 files.` No error, no warning, `is_error` false |

The last row is the main finding for large repositories: **a ripgrep timeout returns a plausible summary that is wrong, with no signal.** The
run used a 1 s limit to make the timeout reachable; the default 20 s limit takes the same code path (`gre`, `@803919`), so a search over a very large tree
that exceeds 20 s behaves the same way. That equivalence is **INFERRED**.

Unordered pagination: `content` and `count` modes pass no `--sort`, so the order of files across repeated calls is whatever ripgrep's parallel walk
produces. `offset` paging over those modes can skip or repeat entries if the order changes between calls. **INFERRED** from ripgrep's documented
behavior; not reproduced.

## 5. Read

Defined at `chunk-phacttch.js@3541060`; the call path `oOr` at `@3546618`; the file reader `uOr` at `@3552514`; the token check `whn` at `@3551059`.

**Static (VERIFIED-STATIC).**

* Defaults: 256 KB (`J5e=262144`, `chunk-dv0tf3v8.js@3931`) and 25,000 tokens (`Xgo=25000`, `chunk-j0bhqprc.js@854`), the token cap overridable with
  `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS` (`chunk-j0bhqprc.js@1751`). The `allow_large: true` parameter lifts both to what still fits in the
  remaining context, using the live context room (`dOr`) and a bytes-per-token figure for the current model.
* The line range reader is `yye` (`chunk-zdd7h7by.js@208689`) with `FI` (`@209429`). With no `limit` it reads the whole file; with a `limit` it reads a window and
  allows a larger byte budget (`maxSelectedBytes = max(maxTokens * 128, ...)`). **Nothing in these functions caps lines at 2,000 or cuts a long line.**
* The constant `NXt=2000` (`chunk-3qrxzjv5.js@87262`) appears in two places only: the tool description text, and the `@`-mention path, which reads a file with
  `limit: NXt` and says `was too large and has been truncated to the first 2000 lines` (`chunk-phacttch.js@3697564`, `@4477705`).
* Numbering is `cat -n` style: line number, a tab (or `:` when a tab-aware mode is on), the verbatim line (`e8e`, `chunk-dv0tf3v8.js@7676`).
* Token check (`whn`): an estimate first; above a quarter of the cap it asks the token counter; over the cap it throws. For a read with no offset and no limit the error is turned
  into a truncated head page, cut at about 85% of the cap and shrunk in up to six steps of 70%, with a continuation notice (`@3560509`).
  For a read with an explicit `offset` or `limit` that is still too large the error stands.
* Validation (`@3543459`): permission deny rule; binary extensions are refused (`This tool cannot read binary files ...`, `@3544003`); device files are refused;
  a PDF page range is validated.
* `ENOENT` (`@3549026`): `File does not exist. Note: your current working directory is <cwd>.` plus `Did you mean <path>?` from `xse` (same path under the current directory) or `sPe`
  (a sibling with a different extension).
* Read state: every read stores content, mtime, offset and limit in `readFileState`. A repeated identical read can return the stub
  `File unchanged since last read...` (`@3548371`) unless a remote kill switch (`tengu_read_dedup_killswitch`), a remote call, or the
  context-management clearing check disables it.

**Runtime (E90c, E90g, VERIFIED-RUNTIME).**

| Call | Result (haiku-5-5; sonnet-4-5, opus-4-7, sonnet-5-5, opus-5-5 agree on size and content) |
|---|---|
| 3,000-line file (42,788 characters) | all 3,000 lines, numbered, no cap, no notice |
| same file again | full content again, no stub, on all five models |
| 30,000-line file (240 KB) | head page of lines 1 to 10,625, then a notice: `[Truncated: PARTIAL view ... showing lines 1-10625 of 30001 total (60000 tokens, cap 25000). Call Read with offset=10626 limit=10625 for the next page, or Grep to find a specific section. To read it anyway ... allow_large: true ... Do NOT answer from this page alone if the answer may be further in the file.]` |
| same file, `offset:1`, `limit:30000` | error `File content (60000 tokens) exceeds maximum allowed tokens (25000). Use offset and limit parameters ...` |
| 293 KB file | error `File content (293KB) exceeds maximum allowed size (256KB). Use offset and limit ...` |
| same file, `offset:1`, `limit:10` | 10 lines |
| 5,000-character line | returned whole, no cut |
| missing `src/missing.py` with `src/missing.txt` present | `File does not exist. Note: ... Did you mean missing.txt?` |
| a directory | `EISDIR: illegal operation on a directory, read ...` |
| `.bin` file | `<tool_use_error>This tool cannot read binary files ...` |

Findings:

1. **The "reads up to 2000 lines by default" sentence in the tool description is not enforced** for the model's own `Read` call. A 3,000-line file is returned whole.
   The enforced limits are bytes and tokens. **CONTRADICTS** the description text; the code and the run agree.
2. **The truncation notice is generated by code**, not left to the model. Its placement depends on the model: for `sonnet-5-5` and `opus-5-5` it arrives as a separate
   `system`-role message after the tool result; for `sonnet-4-5` and `opus-4-7` it is appended inside the tool result in a `<system-reminder>`. Same text.
3. The repeated-read stub never appeared in five scripted runs. The static branch exists with several off switches. Why it stayed off here is **UNKNOWN** (the remote
   kill switch state cannot be read from the extraction). Do not assume Read deduplication in a real session.

## 6. What the model finally sees, and for how long

* A tool result is a string in the next request. Persistence of oversized output is the shared rule in `static-04-tools-permissions-hooks.md` (threshold
  `min(maxResultSizeChars, 50000)`; runtime E22 for Bash). E90h and E90b add the Grep side: 16,691 characters inline, 29 KB and 62 KB persisted. Read is never persisted
  and is excluded from the aggregate budget. Glob returns at most 100 paths, so it cannot reach the limit.
* Old results are cleared later. The clearing set is Read, Bash, PowerShell, Grep, Glob, WebSearch, WebFetch, Edit, Write (`chunk-3qrxzjv5.js@99350`). The
  client-side path (`jdo`, `mgs`, `@100389`, `@101364`) keeps the most recent results and replaces older ones with `[Old tool result content cleared]` once at
  least 20,000 tokens would be saved; the server-side path asks the API to clear tool uses (`clear_tool_uses_20250919`, keep 5, clear at least 20,000 tokens, after 3,900 s of idle,
  `@102148`). Triggers and details are in report 03. For exploration this means a file the model read early can be gone from its context
  while the file-state cache still says it was read.
* The repository snapshot in the first request is small: `git status --short` cut at 2,000 characters (`GLe=2000`, `chunk-phacttch.js@676340`), the last five commits, the
  branch names, the git user (`@678068`). There is no directory tree in the snapshot.

## 7. The Explore agent

**Definition (VERIFIED-STATIC).** `XT` at `chunk-phacttch.js@201549`:

```
agentType: "Explore", source: "built-in", model: "inherit", omitClaudeMd: true,
disallowedTools: [Agent, Artifact, ArtifactComments, ArtifactData, ArtifactCheck, ExitPlanMode, Edit, Write, NotebookEdit],
whenToUse: "Fast read-only search agent for locating code ..." ; whenToUseLean: "Read-only search agent for broad fan-out searches ..."
```

* Registered by `if(tH())n.push(XT,ute)` (`@2086587`). `tH()` is true unless `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS` is set (`@143145`).
* The prompt (`r1n`, `@198147`, about 2,900 characters) says: read-only, never create, modify, delete, move or copy files, no redirects or heredocs, "you do not have
  access to file editing tools", use Glob, Grep and Read, use Bash only for read-only commands, adapt to the thoroughness the caller gives, spawn parallel
  tool calls where possible, report as a normal message. When the embedded search tools are active (`uE()`, `@197837`, environment `EMBEDDED_SEARCH_TOOLS`)
  the text tells the child to run `find` and `grep` through Bash instead of Glob and Grep.
* The caller-facing description asks for a breadth word: `quick`, `medium` or `very thorough`. It also says the agent "reads excerpts rather than whole files, so it locates code;
  it doesn't review or audit it".
* The agent-list line shown to the main model uses `whenToUseLean` when the lean layout is on (`tar`, `@3609138`). Runtime: the lean text appears in this session's own Agent tool listing.

**Restrictions at runtime (E50r, E50u, VERIFIED-RUNTIME).** The child request carries 13 tools: Bash, EnterWorktree, ExitWorktree, Glob, Grep, Monitor, PowerShell, Read,
SendMessage, Skill, TaskStop, WebFetch, WebSearch, against 26 in the parent. A `Write` call returns `No such tool available: Write`. A `Bash` command that writes a file
succeeded under `bypassPermissions`. So read-only is code for the file tools and prompt-only for Bash.

**Invocation (VERIFIED-BOTH).**

* The only trigger is the model choosing the Agent tool with `subagent_type: "Explore"`. The code path is the ordinary Agent launch (`chunk-h6wy99cb.js@27625`).
* Text that encourages the call exists in two places, both gated by model layout:
  * Session guidance: `For broad codebase exploration or research that'll take more than 3 queries, spawn Agent with subagent_type=Explore. Otherwise use the Glob or Grep directly.`
    (`@2012784`, built by `SBo`, `@2011894`, registered at `@2020473`). It is added only when the lean layout is off, the Agent tool is present, Explore is enabled, the subagent steer is
    `default` and fork mode is off. **Runtime:** the sentence is present in the full layout (`claude-sonnet-4-5`, `claude-opus-4-7`) and absent in the lean layout
    (`haiku-5-5`, `fable-5-1`, `mythos-5`, and this session's own prompt).
  * Plan mode: phase 1 tells the model to "launch up to N Explore agents IN PARALLEL" (default 3, `CLAUDE_CODE_PLAN_V2_EXPLORE_AGENT_COUNT`, `@4361170`; text at `@4444995`), and to use "1 agent when the task
    is isolated to known files". Gated by `tH()` and the steer being `default`.
* Nothing in the host requires an Explore call. No code path counts the model's searches or forces a delegation. **VERIFIED-STATIC** (all call sites of `XT` read; list in `chunk-phacttch.js` at `@2012899`, `@2086601`, `@4444710`, `@4445015`).
* The child's model: `Fge` (`@201740`) returns `inherit` or `{inheritCap:"opus"}`; the cap logic and the rest of the model decision tree are in report 02.

**Result delivery.** A foreground child returns status, content and usage to the parent; a background child returns a receipt and a later notification. Both are covered by
`coding-workflow-decompilation/04-builtin-agents-internals.md` section 7. In the E50r runs the launch returned `Async agent launched successfully`.

## 8. Model-dependent presentation of the exploration tools

* Glob, Grep and Read descriptions have a lean and a verbose form selected by `Kx` (`chunk-bykygzr4.js@6222`). Runtime: with `claude-haiku-5-5` the Glob description is 140 characters and the Grep description 477,
  which are exactly the lean strings (the verbose Glob text is 243 or 386 characters). So the lean form is what current models receive. The gate itself is decoded in report 02.
* The "Prefer dedicated tools over Bash" guidance in `# Using your tools` (`_Bo`, `chunk-phacttch.js@2009298`) exists only in the full layout. The lean layout carries one line: `Prefer the dedicated file/search tools over shell commands when one fits.`
* The read-before-edit rule (next section) also depends on the model.

## 9. Code intelligence and indexes

**LSP (VERIFIED-STATIC).** The `LSP` tool offers `goToDefinition`, `findReferences`, `hover`, `documentSymbol`, `workspaceSymbol`, `goToImplementation`, `prepareCallHierarchy`,
`incomingCalls`, `outgoingCalls` (`chunk-svt0njrf.js@5444`). It is deferred (loaded on demand), enabled only when `hasEverConnected()` is true for the LSP manager (`chunk-rpwh4z9c.js@106812`,
`chunk-phacttch.js@4154905`), refuses files over 10 MB, and answers `No LSP server available for file type: .x` when none is configured. The server `command` comes from configuration;
the only language-server name in the package is the schema example `typescript-language-server` (`chunk-ff982hys.js@138321`). **No language server is bundled.** Servers come from plugin manifests
(`lspServers`). The repository can therefore have symbol and reference queries only after a plugin or setting supplies a server. Runtime: the LSP tool appeared in a session that had it configured through the user's plugins;
it is absent from the 26-tool lab sessions.

**Index and graph (bounded negative).** Searches of every `chunk-*.js` in the extraction for `ctags`, `symbolIndex`, `repoMap`, `codeGraph`, `dependencyGraph`, `importGraph`, `callGraph`,
`embedding`, `vectorStore` and `semanticSearch` returned no code that indexes a repository. `tree-sitter` is present only for parsing Bash commands for the permission layer
(`chunk-mkgsmhwy.js@1306`). `getProjectContextBlock` reads a claude.ai project identified by `CLAUDE_PROJECT_UUID`, not a repository. The inspected scope is the text of the extraction's chunk files. Text search
does not prove absence, so this stays **INFERRED**: no local persistent code graph, symbol index or dependency analysis was found. The mechanisms that do carry repository knowledge are: the prompt-assembled git snapshot,
CLAUDE.md and memory files, nested CLAUDE.md and skills discovered when a file is read (`GU` in `oOr`; lab experiment C2), file-state records, and the transcript.

## 10. The link from exploration to editing: the read guard

`Edit` and `Write` refuse to touch an existing file that was not read: `File has not been read yet. Read it first before writing to it.` (`chunk-80kqkekd.js@165185`).
The check sits in each tool's `validateInput` (`chunk-phacttch.js@4164511` for Edit, `@737471` for Write) and is **skipped** when all of these hold: the model is not in a fixed
legacy list (`chunk-bykygzr4.js@2857`: `claude-opus-4-6`, `claude-haiku-4-5`, `claude-opus-4-5`, `claude-opus-4-1`, `claude-opus-4-0`, `claude-sonnet-4-5`, `claude-sonnet-4-0`,
`claude-3-7-sonnet`, `claude-3-5-sonnet`, `claude-3-5-haiku`; `WXt` at `@3100`), the Read tool (or REPL) is in the tool set (`Lf`, `eFe`), and a Read of that path would be allowed without a prompt (`$f`, `chunk-p9na5vps.js@231585`; a
`bypassPermissions` session counts as allowed). The telemetry names (`tengu_write_tool_not_read_hypothetical`, `guardSkipped`) show the guard is being phased out model by model.

**Runtime (E90d, E90e, E90f, VERIFIED-RUNTIME, with VERIFIED-STATIC for the rule).** Write or Edit on an existing file never read in the session:

| Model | `bypassPermissions` | `acceptEdits` | default (headless) |
|---|---|---|---|
| `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`, `claude-fable-5-1`, `claude-mythos-5`, `claude-opus-4-7` | applied | applied | blocked by the permission prompt, not by the guard |
| `claude-sonnet-4-5`, `claude-opus-4-5`, `claude-opus-4-6`, `claude-haiku-4-5` | refused: `File has not been read yet` | refused | refused |

`claude-opus-4-1` is mapped to a newer model by the CLI before the check (E50), so it is not a separate row. The stale-read side is looser still: after a Read, an external append to the file, and an `Edit` whose
`old_string` still occurs, the edit was applied on all three models tried (`haiku-5-5`, `sonnet-4-5`, `opus-4-7`). The code accepts a changed file when the edit still applies (`De`, `chunk-phacttch.js@4164511` region).

Consequence: for current models the CLI does **not** force the model to read a file before overwriting it. What remains is the tool description text ("you MUST use the Read tool first") and the model's habit.
The earlier note in `static-04-tools-permissions-hooks.md` (check site not read) is resolved by this section.

## 11. Enforced, prompted, chosen

| Behavior | Code-enforced | Prompt only | Model choice |
|---|---|---|---|
| Max 100 Glob paths, 250 Grep lines, 256 KB and 25,000 tokens per Read, 20 s ripgrep | yes | no | no |
| Explore cannot use Edit, Write, NotebookEdit, Agent | yes | no | no |
| Explore does not run mutating shell commands | no | yes | yes |
| Read a file before overwriting it | only for 10 legacy model ids | yes (tool text) | yes |
| Use Glob and Grep rather than shell `find` and `grep` | no | yes (lean line, verbose section) | yes |
| Spawn Explore for more than 3 queries | no | full layout only; plan mode text | yes |
| Explore at all before implementing | no (E50s: a write with no prior read or search ran to completion) | plan mode text only | yes |
| Re-read after the file changed | no (edit applies if its `old_string` still matches) | yes | yes |
| Notice when a search was cut | Read yes (notice), Grep persisted-output yes, Glob yes (count), **Grep timeout no** | n/a | n/a |

## 12. Failure modes and limits

1. **Silent partial Grep after a timeout.** Section 4. The model sees a plausible total.
2. **Glob truncation keeps the oldest files.** For more than 100 matches, newly changed files are the first to disappear.
3. **Glob lists ignored and VCS files** (`node_modules`, `.git`), spending the 100-path budget on them. Grep does the opposite for ignored files, so the two tools can disagree about what exists.
4. **Unordered `offset` paging** in Grep content and count modes (INFERRED).
5. **The Read description overstates a 2,000-line limit.** The model may request a 40,000-line file and receive 25,000 tokens of it, with a notice.
6. **No relevance ranking, no repository map, no symbol lookup.** Every discovery is a model-written pattern. LSP helps only where a server was configured.
7. **Read deduplication unobserved**, so repeated reads can re-spend context.
8. **Old exploration results are cleared** after the cache window or a size threshold, with the file-state cache still marking the file as read.
9. **Read-before-edit is not enforced for current models**, so an edit can be applied to code the model only guessed at from search snippets.
10. **Explore reads excerpts**, by its own description, so it can miss content past its window; its report to the parent is a model summary.

## 13. Where a graph engine could differ (HYPOTHESES, not tested)

* HYPOTHESIS: ranking candidate files by graph relevance and recency would avoid the oldest-first Glob cut and the unranked Grep order. No success-rate evidence exists.
* HYPOTHESIS: definition, reference and caller queries answered from a persistent graph, without a configured language server, would cover the gap that LSP leaves. Cost, freshness after edits and language coverage are unmeasured.
* HYPOTHESIS: a completeness flag on every search result (`complete`, `timed_out`, `truncated_to_N`) closes the silent-partial failure at no model cost. This one is a design inference from section 4, not an experiment.
* HYPOTHESIS: a code-level "grounding gate" (an edit is allowed only when the edited span was returned by a read or a graph query in this session) would restore what Claude Code has removed for current models. Whether it raises task success is untested.

## 14. Corrections to earlier research

* `static-04-tools-permissions-hooks.md` (read-before-edit check site "not read"): resolved here, and the rule is model-dependent, not universal.
* `coding-workflow-decompilation/04-builtin-agents-internals.md` section 5 gave Explore at `@201330`; the definition literal starts at `chunk-phacttch.js@201549`. The behavior described there stands.
* Tool description text claiming a 2,000-line default read is not what the code enforces (section 5).

## 15. Remaining unknowns

* State of the remote kill switch for Read deduplication. Needs a live account's feature data; not read.
* Exact ripgrep exclusion globs derived from Read-deny rules (`_ae`, `kae`).
* Whether any real model uses Glob's oldest-first order well. Needs model experiments, excluded here.
* LSP behavior with a real language server (no server was available in the lab).

## 16. Reproduce

```
bash research/claude-code/tools/scenarios/run_e90.sh <new id> glob|grep|grepsize|grepslow|read|guardw|guarde|guardr [permission mode]
MODEL=<model> E90_ENV=CLAUDE_CODE_GLOB_TIMEOUT_SECONDS=1 bash .../run_e90.sh E90x-name grepslow
python -I research/claude-code/tools/exploration_probe.py <id>
python -I research/claude-code/tools/scenarios/run_matrix_e90.py d guardw,guarde haiku,claude-sonnet-4-5 bypassPermissions,acceptEdits
```

Runs: E90a Glob, E90b Grep, E90c Read, E90d guard matrix (3 models by 3 modes by Write and Edit), E90e guard by model, E90f stale read, E90g Read on four more models, E90h Grep output size, E90i and E90j large-tree Grep.

### Pinned anchors by name

Each anchor starts at the literal recorded in `13-source-pins.json`.

| Name | Anchor |
|---|---|
| `grep_default_limit` | `chunk-phacttch.js@767948` |
| `grep_slice` | `chunk-phacttch.js@767956` |
| `grep_vcs_excl` | `chunk-phacttch.js@767903` |
| `grep_run` | `chunk-phacttch.js@771689` |
| `grep_path_missing` | `chunk-phacttch.js@771408` |
| `grep_json_parse` | `chunk-phacttch.js@777984` |
| `grep_validate` | `chunk-phacttch.js@770617` |
| `grep_result_map` | `chunk-phacttch.js@769615` |
| `glob_call` | `chunk-phacttch.js@763672` |
| `glob_run` | `chunk-phacttch.js@756830` |
| `glob_search` | `chunk-phacttch.js@756278` |
| `glob_trunc_note` | `chunk-phacttch.js@761443` |
| `rg_spawn` | `chunk-4gghv5aa.js@800105` |
| `rg_maxbuf` | `chunk-4gghv5aa.js@788791` |
| `rg_timeout_msg` | `chunk-4gghv5aa.js@806230` |
| `read_validate` | `chunk-phacttch.js@3543459` |
| `read_call` | `chunk-phacttch.js@3546618` |
| `read_impl` | `chunk-phacttch.js@3552514` |
| `read_tokcheck` | `chunk-phacttch.js@3551059` |
| `read_partial_msg` | `chunk-phacttch.js@3560509` |
| `read_dedup` | `chunk-phacttch.js@3548371` |
| `read_enoent` | `chunk-phacttch.js@3549026` |
| `read_defaults_fn` | `chunk-j0bhqprc.js@1828` |
| `read_range_fmt` | `chunk-zdd7h7by.js@209429` |
| `read_prompt` | `chunk-3qrxzjv5.js@87669` |
| `read_partial_const` | `chunk-3qrxzjv5.js@87219` |
| `grep_prompt` | `chunk-3qrxzjv5.js@91297` |
| `glob_prompt` | `chunk-3qrxzjv5.js@90663` |
| `atmention_trunc` | `chunk-phacttch.js@4477705` |
| `explore_prompt` | `chunk-phacttch.js@198147` |
| `explore_cap` | `chunk-phacttch.js@201968` |
| `explore_nudge` | `chunk-phacttch.js@2012784` |
| `explore_nudge_fn` | `chunk-phacttch.js@2011894` |
| `explore_gate` | `chunk-phacttch.js@143145` |
| `builtin_push` | `chunk-phacttch.js@2086587` |
| `plan_explore` | `chunk-phacttch.js@4444995` |
| `plan_explore_count` | `chunk-phacttch.js@4361170` |
| `embedded_search` | `chunk-phacttch.js@197837` |
| `agent_list_line` | `chunk-phacttch.js@3609138` |
| `git_status_text` | `chunk-phacttch.js@678068` |
| `guard_stale_msg` | `chunk-80kqkekd.js@165513` |
| `guard_write` | `chunk-phacttch.js@737471` |
| `guard_wxt` | `chunk-bykygzr4.js@3100` |
| `guard_jce` | `chunk-p9na5vps.js@232998` |
| `guard_lf` | `chunk-p9na5vps.js@232851` |
| `guard_zne` | `chunk-p9na5vps.js@231916` |
| `micro_clear_fn` | `chunk-3qrxzjv5.js@100389` |
| `micro_exec` | `chunk-3qrxzjv5.js@101364` |
| `micro_server_cfg` | `chunk-3qrxzjv5.js@102148` |
| `micro_placeholder` | `chunk-3qrxzjv5.js@99072` |
| `lean_I` | `chunk-bykygzr4.js@6270` |
