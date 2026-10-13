#!/usr/bin/env bash
# Batch 2: hooks and permission-rule experiments (slim profile).
set -u
T="C:/Users/sergi/Desktop/claude-rea/research/claude-code/tools"
L="C:/Users/sergi/cc-rea-lab"
RAW="C:/Users/sergi/Desktop/claude-rea/lab/raw"
SLIM=(--model haiku --setting-sources project,local --strict-mcp-config --mcp-config "$L/empty-mcp.json")
run() { local id="$1" proj="$2" prompt="$3"; shift 3; printf 'alpha\nbeta\ngamma\n' > "$L/$proj/notes.txt"; rm -f "$L/stopblock.flag"; mkdir -p "$RAW/$id"
  python -I "$T/run_exp.py" --id "$id" --cwd "$L/$proj" --prompt "$prompt" --timeout 240 --env "LAB_HOOK_LOG_DIR=$RAW/$id" -- "${SLIM[@]}" "$@"
  python -I "$T/summarize_captures.py" "$id" --print | head -2; }

run E07a-hooks-order proj-hooks "Use Read on notes.txt, then use Edit to change 'beta' to 'beta-h'. Then say done." --permission-mode acceptEdits
run E07b-hook-deny proj-hook-deny "Use the Bash tool to run exactly: echo hello-from-bash   If refused say REFUSED and stop." --allowedTools "Bash(echo:*)"
run E07c-hook-exit2 proj-hook-exit2 "Use Read on notes.txt and tell me line 1. If the read is blocked, say BLOCKED and stop."
run E07d-hook-exit1 proj-hook-exit1 "Use Read on notes.txt and tell me line 1."
run E07e-hook-allow proj-hook-allow "Use Read on notes.txt, then use Edit to change 'beta' to 'beta-hook-allowed'. If refused say REFUSED."
echo "notes after E07e:"; cat "$L/proj-hook-allow/notes.txt"
run E07f-hook-allow-vs-deny proj-hook-allow-vs-deny "Use Read on notes.txt, then use Edit to change 'beta' to 'beta-should-not'. If the Edit tool is unavailable or refused say REFUSED and stop."
echo "notes after E07f:"; cat "$L/proj-hook-allow-vs-deny/notes.txt"
run E07g-hook-rewrite proj-hook-rewrite "Use the Bash tool to run exactly: echo ORIGINAL-COMMAND   Then report the exact output."
run E07h-stop-block proj-hook-stopblock "Reply with exactly: first-answer"
run E08b-perm-rules proj-perm-rules "Run these four Bash commands one at a time, each in its own tool call, and report for each whether it ran or was refused: (1) echo allowed-one (2) echo denied-two (3) echo ask-three (4) Read the file secret/s.txt with the Read tool."
