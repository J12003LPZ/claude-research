# 01. Environment, installation provenance, artifact inventory, REA coverage

Labels: **VERIFIED** (observed directly in the artifact or at runtime), **STRONGLY
INFERRED**, **HYPOTHESIS**, **UNKNOWN**.

## 1. Host

| Fact | Value | Evidence |
|---|---|---|
| OS | Windows 11 Pro, NT 10.0.26300, AMD64 | `[System.Environment]::OSVersion`, `PROCESSOR_ARCHITECTURE` |
| Shells used | PowerShell 7, Git Bash | session |
| Node / npm / Bun on PATH | v24.19.0 / 12.2.0 / present | `node -v`, `npm -v`, `Get-Command bun` |
| WSL | `wsl.exe` present, not used | no Linux process was analysed |

## 2. What runs when you type `claude` (VERIFIED)

`Get-Command claude -All` and `where.exe claude` both return exactly one entry:

`C:\Users\<user>\.local\bin\claude.exe`

There is no npm global install (`%APPDATA%\npm\node_modules\@anthropic-ai\claude-code`
does not exist), no `.cmd`/`.ps1` shim named `claude`, and the file is a regular file, not a
link (`LinkType` empty). `claude --version` prints `2.1.296 (Claude Code)`.

### 2.1 Active artifact

| Field | Value |
|---|---|
| Path | `~\.local\bin\claude.exe` |
| Size | 260,489,376 bytes |
| SHA-256 | `76de74f7694a5bdc03378a5f837c9e132827bf004c98c276bc4e9094ff06769a` |
| PE | PE32+ x86-64, 13 sections, console subsystem (3), image base `0x140000000` |
| Version resource | FileVersion/ProductVersion `2.1.296.0`, ProductName `Claude Code`, CompanyName `Anthropic PBC`, **InternalName `bun`** |
| Authenticode | Valid. Subject `Anthropic, PBC` (Delaware, serial 4860621), issuer DigiCert Trusted G4 Code Signing RSA4096 SHA384 2021 CA1, DigiCert timestamp |
| Embedded build constants | `VERSION 2.1.296`, `BUILD_TIME 2026-10-09T01:31:52Z`, `GIT_SHA fdb6c17a97b6e0e3cf15e3566663fca58e7c43a9` (from the entry module) |
| Provenance class | original |

Evidence: `runtime-logs/static/pe-inventory-2.1.296.json`, `tools/pe_inventory.py`.

### 2.2 Installation format: Bun standalone executable (VERIFIED)

This is not inferred from the file name. Four independent artifact facts agree:

1. Version resource `InternalName` is `bun`.
2. PE sections include `.bun` (166,639,191 bytes virtual) and `.bunblt` (2.6 MB), beside the
   usual `.text` (68 MB native runtime), `.rdata`, `.data`, `.pdata`, `.rsrc`, `.reloc`.
3. The `.bun` section ends with the literal trailer `\n---- Bun! ----\n`, and the bytes
   before it parse as an offsets record that indexes 2,586 module records.
4. The entry module begins `// @bun @bytecode` and imports from `B:/~BUN/root/...`, and the
   runtime identifies itself to the network as `Bun/1.4.3` (`HEAD /api/hello` user agent,
   experiment E01).

So the executable is a hybrid: a native Bun runtime (JavaScriptCore, Zig/C++) in `.text`,
carrying a bundled JavaScript application in `.bun`. The application logic lives in the
JavaScript. Native analysis of `.text` would describe Bun, not Claude Code.

### 2.3 Layout of the embedded module graph (VERIFIED by parsing, `tools/bun_extract.py`)

```
.bun section   = u64 payload_len (166,639,183) | payload
payload tail   = Offsets | "\n---- Bun! ----\n"
Offsets (32 B) = u64 byte_count | {u32 off,u32 len} modules | u32 entry_point_id (6)
                 | {u32 off,u32 len} compile_exec_argv (empty) | u32 flags (0x1bff)
module record  = 6 x {u32 off,u32 len}: name, contents, sourcemap, bytecode, module_info,
                 bytecode_origin_path ; then u8 encoding, loader, module_format, side  (52 B)
```

The 52-byte record size was not assumed: the module table length (134,472) divides evenly
only by 52 among the candidate sizes, and every decoded name is a sane `B:/~BUN/root/...`
path.

| Module class | Count | Notes |
|---|---|---|
| JavaScript chunks (`chunk-xxxxxxxx.js`) | 2,343 | minified ESM, each with JavaScriptCore bytecode (95.4 MB total) |
| Entry module `cli` | 1 | 23,964 bytes, `entry_point_id = 6` |
| Embedded text assets (`.md`, `.txt`, `.zst`) | 235 | skills, docs, templates, prompt fragments; 140 are zstd-compressed |
| Native addon | 1 | `audio-capture.node` (509 KB) plus its JS loader |
| Other | `mermaid.min.js`, `chart.umd.min.js`, `hljsBundle.generated.min.js`, two `.woff2.asset` fonts | |
| Source maps | 0 bytes | none shipped |

Total source text 48.5 MB. Manifest with per-module size and SHA-256:
`runtime-logs/static/bun-module-manifest-2.1.296.json`. The extracted tree lives in
`extracted/2.1.296/` (generated, not committed, provenance class **extracted**).

Consequence for analysis: local identifiers are mangled, but export names are intact,
because dynamic `import()` call sites destructure by name. 31,751 exports across 2,348
chunks were indexed; 925 chunks carry human-readable export names
(`runtime-logs/static/export-catalog-2.1.296.tsv`).

### 2.4 Other installed copies

| Path | Size | SHA-256 | Role |
|---|---|---|---|
| `~\.local\share\claude\versions\2.1.296` | 260,489,376 | `76DE74F7...06769A` | byte-identical to the active exe (version store) |
| `~\.local\share\claude\versions\2.1.295` | 259,509,920 | `A3001274...83BCD6` | previous version, retained |
| `~\.local\share\claude\versions\2.1.294` | 256,155,808 | `1F6471EB...42163A` | older version, retained |

**STRONGLY INFERRED:** the native installer keeps a version store and copies the current
version to `~\.local\bin\claude.exe` (identical hash, mtimes 2 s apart) rather than linking
to it. Not analysed further: the updater itself.

### 2.5 Configuration and state locations (names only; contents not read)

`~\.claude\` holds `settings.json`, `settings.local.json`, `CLAUDE.md`, `projects\`
(transcripts), `sessions\`, `file-history\`, `plugins\`, `skills\`, `tasks\`, `daemon*`,
`history.jsonl`, and `.credentials.json`. `~\.claude.json` is the global config (145 KB).
The credentials file and global config were never opened. Settings were read for key
names only.

## 3. REA audit

| Item | Result | Evidence |
|---|---|---|
| CLI | `rea@6.4.0`, 127 CLI commands | `rea --help` |
| MCP server | `rea-agents` 6.4.0, SDK 2.3.1, connected | `runtime-logs/rea/rea-providers.json` |
| `rea doctor --json` | `healthy: false` (audit-wide scope, 27 checks); Ghidra provider available | `runtime-logs/rea/rea-doctor.json` |
| Native provider | Ghidra 12.1.4 at `~\tools\ghidra_12.1.4_PUBLIC` (headless) | providers JSON |
| Unavailable on this host | 10 macOS-only operations (`inspect_macho`, `inspect_signature`, `observe_native_calls`, ...) | `availability_code: unsupported_host` |
| Process capture | `capture_process_scenario` is PTY-based; REA documents it as not natively supported on Windows | skill guidance; not used |

### 3.1 What REA was used for

- `analyze_javascript_application` on the extracted tree (format `directory`, summary
  detail). Evidence id `ev_bc6b6f37...859bf8`, parent `ev_87d7ca73...022f73`. Result: 2,348
  relevant files, 2,344 JavaScript files parsed, 9,281,970 AST nodes visited, 195,726
  findings, 0 parse failures, 3 files with invalid UTF-8. Coverage status **partial**: REA
  reports 32,694 semantic-graph unknowns and 4,652 application-graph unknowns, and that
  expanded relationships for some chunks exceeded its result budget. Saved as
  `runtime-logs/rea/rea-js-application-summary-2.1.296.json`.
- Diagnostics (`doctor`, `capabilities`, `providers`, `binary_session`).

### 3.2 What REA was not used for, and why

- **Ghidra on `claude.exe`:** not run. The `.text` section is the Bun runtime. Decompiling
  68 MB of JavaScriptCore would not answer any question in scope, and passing the PE to the
  JavaScript analyzer would have inspected nothing. The JavaScript was extracted first and
  analysed as JavaScript.
- **REA process capture:** unsupported on native Windows. Runtime evidence came from the
  CLI's own structured interfaces instead (section 4).
- **JavaScriptCore bytecode:** not disassembled. The same modules ship as source text, and
  the bytecode is a cache of that source. **HYPOTHESIS, untested:** bytecode and source are
  equivalent. A mismatch would be visible as runtime behaviour that contradicts the source;
  none was seen across the 148 manifest runs.

## 4. Runtime instrumentation used instead of process tracing

| Channel | What it shows | Tool |
|---|---|---|
| `ANTHROPIC_BASE_URL` forward proxy | exact request bodies, header names, SSE stream with chunk timing, client disconnects | `tools/capture_proxy.mjs` |
| `--output-format stream-json --verbose --include-partial-messages --include-hook-events` | the CLI's own event stream | `tools/run_exp.py` |
| `--input-format stream-json` | control protocol (interrupt) | `tools/run_stream.py` |
| `--debug-file` | internal debug log | raw only |
| Command hooks | hook stdin JSON, ordering, timing, environment | `cc-rea-lab/hooklog.py` |
| Session files of lab projects | on-disk transcript schema | `tools/transcript_schema.py` |

The proxy forwards every request unchanged to `api.anthropic.com` over TLS. Credential
header values are never written (name plus length only). Raw captures stay in `lab/raw/`,
which is not committed; `runtime-logs/` holds structural summaries (lengths, hashes,
selected 80-character heads, and content-free digests where text may be arbitrary). `tools/build_manifest.py` fails if a token, key, email, workspace id or
the local account name appears in the sanitized runtime evidence tree. It does not scan the raw captures or the prose reports. Last run: clean.

### 4.1 Instrumentation caveats

1. The child CLI must not inherit the parent agent session's environment. Thirteen
   `CLAUDE*` variables were scrubbed per run (names recorded in each `run.json`).
2. Pointing the CLI at a non-default base URL could change behaviour. The dispatch log line
   still reads `dispatching to firstParty`, OAuth still worked, and the beta header set
   matched between proxied runs, but a direct-to-API baseline was not captured. **UNKNOWN:**
   whether any feature gate keys on the base URL host.
3. Experiments ran in a slim profile (`--model haiku --setting-sources project,local
   --strict-mcp-config`) after the default profile proved expensive (E01: 206 tools,
   ~258,000 cached tokens, notional 2.06 USD for a one-word answer). Findings about request
   shape were checked once against the default profile (E01) and otherwise come from the
   slim profile.
