# Claude Code 2.1.296: forensic reconstruction

Target: the `claude` CLI installed on this Windows machine
(`~\.local\bin\claude.exe`, SHA-256 `76de74f7...06769a`, a signed Bun standalone executable).
Method: artifact extraction, static reading of the embedded JavaScript, REA's JavaScript
application analyzer, and 55 instrumented runtime experiments against disposable projects.

Start with `02-verified-architecture.md`. Use `06-verification-matrix.md` to see how far
each claim can be trusted.

## Documents

| Topic requested | Where |
|---|---|
| Environment and installation provenance | `01-environment-and-provenance.md` |
| Artifact inventory and hashes | `01-environment-and-provenance.md` sections 2.1 to 2.4, `runtime-logs/static/` |
| Static architecture | `02-verified-architecture.md` section 1, `static-01` to `static-05` |
| Startup and CLI dispatch | `02` section 2, `static-01-startup-cli-config.md` |
| Prompt assembly | `02` section 3, `static-02-prompt-context-compaction.md`, experiments C1 to C8 |
| Main agent loop | `02` section 4, `static-03-agent-loop-transport.md` |
| Model transport and streaming | `02` section 5, `static-03`, experiments E01, E18 |
| Tool registration and dispatch | `02` section 6, `static-04-tools-permissions-hooks.md` |
| Permissions and hooks | `02` section 6, `static-04`, experiments E06 to E08b |
| Subagents and scheduling | `02` section 7, `static-05-subagents-sessions-rendering.md`, E10 to E14 |
| Context management and compaction | `02` section 8, `static-02`, E17 |
| Session persistence and resume | `02` section 9, `static-05`, E15, `runtime-logs/sessions/` |
| Terminal rendering | `02` section 10, `static-05` part C (static only) |
| Failure recovery and cancellation | `03` sections E13 and E18, `05` section 13 |
| Runtime experiment catalog | `03-runtime-experiments.md` |
| Internal contracts | `04-internal-contracts.md` |
| Independent implementation specification | `05-implementation-spec.md` |
| Verified architecture | `02-verified-architecture.md` |
| Verification matrix, behavioural matrix, open questions, confidence | `06-verification-matrix.md` |
| Evidence index | this file, below, and `runtime-logs/MANIFEST.json` |
| Resume point for the investigation | `PROGRESS.md` |

## Evidence index

| Evidence | Path | Produced by |
|---|---|---|
| PE section table, Bun markers, hashes | `runtime-logs/static/pe-inventory-2.1.296.json` | `tools/pe_inventory.py` |
| Module manifest (2,586 modules, sizes, SHA-256) | `runtime-logs/static/bun-module-manifest-2.1.296.json` | `tools/bun_extract.py` |
| Import/export index of all chunks | `runtime-logs/static/chunk-index-2.1.296.json` | `tools/chunk_index.py` |
| Readable export catalog | `runtime-logs/static/export-catalog-2.1.296.tsv` | derived from the index |
| REA diagnostics and JS application analysis | `runtime-logs/rea/` | `rea doctor`, `rea providers`, MCP `analyze_javascript_application` |
| Per-experiment sanitized captures | `runtime-logs/<experiment id>/` | `tools/run_exp.py`, `tools/run_stream.py`, `tools/summarize_captures.py`, `tools/hooks_summary.py` |
| Instruction marker placement, resume replay | `runtime-logs/config/` | marker scans over raw request bodies |
| Transcript schema (lab sessions only) | `runtime-logs/sessions/transcript-schema.json` | `tools/transcript_schema.py` |
| Manifest with hashes and redaction check | `runtime-logs/MANIFEST.json` | `tools/build_manifest.py` |
| Static anchors | `chunk-xxxxxxxx.js@offset` citations inside `static-0N` | `tools/cq.py` over `extracted/` |

Not committed: `extracted/` (the unpacked proprietary module tree) and `lab/` (raw
captures with full prompt text and private instruction files). Both are reproducible with
the tools here.

## How far to trust each layer

- **Runtime findings** (`03`, and every V-RT tag in `02`): read directly from captured
  requests, events, hook logs and files. Highest confidence. Limits: headless mode only,
  mostly a slim configuration, all through a forwarding proxy.
- **Static passes** (`static-01` to `static-05`, about 520 KB): written by five parallel
  analysis agents reading minified code, each claim carrying a `chunk@offset` anchor, then
  **audited a second time** by five independent reviewers. Audit method and limits:
  - Mechanical: `tools/audit_static_citations.py` checks that every one of the 1,849
    `chunk@offset` citations names an extracted chunk and lies inside it. After one fix
    (`static-04` line 239) all 1,849 resolve. This proves the address exists, not that the
    prose is right.
  - Semantic: each reviewer read the claims against the source and the runtime logs and
    wrote a ledger, kept in `runtime-logs/static/audit/`. `runtime-logs/static/static-claim-ledger-2.1.296.json`
    lists all 747 report paragraphs with their anchors (436 carry none).
  - Results (claim groups): 01: 146 verified, 48 partial, 1 contradicted. 02: 126, 25, 4.
    03: 108, 21, 2. 04: about 138, about 52, 1. 05: 155, 63, 1. "Partial" means some part
    was confirmed and some part was omitted, inexact or not re-read. Runtime evidence
    contradicted no verified static claim.
  - Fixed in place: every contradiction (9 in total) is corrected in the report, marked
    "Audit correction". I re-checked six of them against the source myself (`deniedModels`
    delete, stop-hook condition, idle-timeout interaction, `ts` rendering selection, resume
    guidance condition, client-side tool-result clearing) plus the Read size sentinel, the
    detached-result path and the renderer facade chunk.
  - Merge progress: in `static-04`, eight addendum items were re-verified in source and merged
    (hook timeouts, bypass and dontAsk tests, `shouldDefer`, MCP concurrency, the second strict
    path, Stop-hook input fields, the Read size sentinel). One reviewer claim was found
    unsupported and replaced with the runtime-observed text. Reports 01, 02, 03, 05 have only
    their contradictions merged.
  - Not done: the remaining partial findings are recorded in a "5b. Audit addendum" in each
    report and are **not yet re-verified or merged into the text**. The reviewers were language
    models reading minified code, and I did not re-read their verified rows. Treat the
    addendum items as leads; treat any claim outside both lists as checked once by an agent.
- **Implementation spec** (`05`): separates REPRODUCE (observed) from CHOICE (design).

## Reproducing

```
python -I tools/pe_inventory.py  <claude.exe> out.json
python -I tools/bun_extract.py   <claude.exe> manifest.json <extract dir>
python -I tools/chunk_index.py   <extract dir>/~BUN/root index.json
python -I tools/run_exp.py --id X --cwd <lab project> --prompt "..." -- --model haiku --setting-sources project,local
python -I tools/summarize_captures.py X --print
python -I tools/build_manifest.py
```

Paths inside the tools are absolute for this machine; adjust `LAB`, `OUT`, `ROOT` at the
top of each script. Each experiment makes real model requests on the logged-in account.
In the default configuration of this machine one trivial request carried about 258,000
tokens of tools and context, so use the slim profile.
