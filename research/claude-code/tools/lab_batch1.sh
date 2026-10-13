#!/usr/bin/env bash
# Batch 1: core tool-loop experiments in the slim profile (haiku, no user settings, no MCP).
# Usage: bash lab_batch1.sh
set -u
T="C:/Users/sergi/Desktop/claude-rea/research/claude-code/tools"
P="C:/Users/sergi/cc-rea-lab/proj-a"
SLIM=(--model haiku --setting-sources project,local --strict-mcp-config --mcp-config "C:/Users/sergi/cc-rea-lab/empty-mcp.json")
reset() { printf 'alpha\nbeta\ngamma\n' > "$P/notes.txt"; }
run() { local id="$1" prompt="$2"; shift 2; reset; python -I "$T/run_exp.py" --id "$id" --cwd "$P" --prompt "$prompt" --timeout 240 -- "${SLIM[@]}" "$@"; python -I "$T/summarize_captures.py" "$id" --print | cut -c1-1400; echo; }

run E02-read "Use the Read tool on notes.txt and tell me the second line. Do not use any other tool."
run E03-edit-accept "Use the Edit tool to change the line 'beta' in notes.txt to 'beta-edited'. Read the file first if required." --permission-mode acceptEdits
echo "notes.txt after E03:"; cat "$P/notes.txt"
run E06-edit-denied "Use the Edit tool to change the line 'beta' in notes.txt to 'beta-edited'. Read the file first if required. If the edit is refused, say REFUSED and stop."
echo "notes.txt after E06:"; cat "$P/notes.txt"
run E04-bash-ok "Use the Bash tool to run exactly: echo lab-ok   Then report the output." --allowedTools "Bash(echo:*)"
run E05-bash-fail "Use the Bash tool to run exactly: ls /nonexistent-lab-path-xyz   Then report the exit status and stderr in one line. Do not retry." --allowedTools "Bash(ls:*)"
run E06b-bash-denied "Use the Bash tool to run exactly: echo should-not-run   If it is refused, say REFUSED and stop. Do not try other tools."
run E08-multi-parallel "In ONE assistant message, issue three Read tool calls in parallel for notes.txt, src/calc.py and sub/deep/d.txt. Then list the first line of each."
run E09-sequential "First use Grep to find which file under this directory contains the text 'def greet'. Then Read that file. Then tell me what greet('x') returns."
