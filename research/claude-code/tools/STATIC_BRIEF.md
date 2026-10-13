# Static sweep brief (shared by every static-analysis pass)

## Target

Claude Code CLI 2.1.296, Windows x64. The installed artifact is a Bun standalone PE:
`C:\Users\<user>\.local\bin\claude.exe`, SHA-256
`76de74f7694a5bdc03378a5f837c9e132827bf004c98c276bc4e9094ff06769a`.

Its embedded module graph (2,586 modules) was extracted read-only to:

`C:\Users\<user>\Desktop\claude-rea\extracted\2.1.296\~BUN\root\`

- `cli` is the entry module (24 KB). It dispatches fast paths and finally calls
  `main` exported by `chunk-zvnaqyp5.js`.
- `chunk-*.js` are minified ESM chunks. Local identifiers are mangled, but **export
  names are real** (dynamic imports destructure them by name), and string literals,
  object keys, env var names, event names, and error messages are intact.
- `*.md`, `*.txt`, `*.zst` are embedded docs / skills / templates.

## Tools (all read-only)

```
python -I C:\Users\<user>\Desktop\claude-rea\research\claude-code\tools\cq.py exp  '<regex>'            # chunks by export name
python -I ...\cq.py files '<regex>'                 # hit counts per chunk
python -I ...\cq.py grep  '<regex>' [ctx=200] [max=40]   # hits with context chars
python -I ...\cq.py show  <chunk> <start> <len>     # slice of one chunk
python -I ...\cq.py info  <chunk>                   # imports/exports of a chunk
python -I ...\cq.py who   <chunk>                   # who imports a chunk
```

Export catalog (chunk, size, readable exports), grep-friendly:
`C:\Users\<user>\Desktop\claude-rea\research\claude-code\runtime-logs\static\export-catalog-2.1.296.tsv`

Chunks are single-line minified files up to 4.7 MB. Never `cat` or Read a whole chunk.
Always use `cq.py grep` / `show` with bounded context, and pipe long output through
`cut -c1-N` or `head`.

## Hard rules

1. Read-only. Do not modify the install, the extracted tree, `~/.claude`, or settings.
2. Never open or print `~/.claude/.credentials.json`, `~/.claude.json`, tokens, keys,
   cookies, or any existing session transcript under `~/.claude/projects`.
3. Do not run `claude` (runtime experiments are owned by the orchestrating session).
4. Every finding carries evidence as `chunk-xxxxxxxx.js@<char offset>` plus a quoted
   anchor of 120 characters or less (a string literal, key name, or export name).
5. Label every claim: **VERIFIED-STATIC** (read directly in the shipped code),
   **STRONGLY INFERRED**, **HYPOTHESIS**, or **UNKNOWN**. Static evidence proves the
   code exists; it never proves it runs. Say "the code does X when reached", not "X happens".
6. Do not invent identifiers. Mangled names are quoted as mangled. Conceptual names are
   marked as conceptual.
7. Do not paste long proprietary code or full prompt texts. Short anchors and your own
   pseudocode only. Describe prompt sections by role, order, and trigger, not verbatim text.
8. Constants matter: record exact numbers (timeouts, thresholds, limits, retry counts)
   with their evidence.
9. Write for an engineer who must reimplement the behavior without the original.

## Deliverable shape

One Markdown file at the path given in your task, with these sections:

1. Scope and coverage (what you searched, what you did not reach)
2. Findings, grouped by sub-question, each with label + evidence
3. Reconstructed control flow as pseudocode and at least one Mermaid diagram
4. Data contracts (TypeScript-style, observed fields vs proposed)
5. Constants table (name or role, value, evidence)
6. Open questions that need a runtime experiment to settle (be specific about the experiment)

Your final message back: a 15-line summary of the strongest findings and the open
questions. The detail lives in the file.
