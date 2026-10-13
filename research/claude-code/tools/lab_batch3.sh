#!/usr/bin/env bash
# Batch 3: real shell failure, subagents, background task, resume/continue/fork, manual
# compaction, injected transport faults (slim profile).
set -u
T="C:/Users/sergi/Desktop/claude-rea/research/claude-code/tools"
L="C:/Users/sergi/cc-rea-lab"
P="$L/proj-a"
RAW="C:/Users/sergi/Desktop/claude-rea/lab/raw"
SLIM=(--model haiku --setting-sources project,local --strict-mcp-config --mcp-config "$L/empty-mcp.json")
run() { local id="$1" prompt="$2"; shift 2; printf 'alpha\nbeta\ngamma\n' > "$P/notes.txt"
  python -I "$T/run_exp.py" --id "$id" --cwd "$P" --prompt "$prompt" --timeout 300 ${PRE[@]+"${PRE[@]}"} -- "${SLIM[@]}" "$@"
  python -I "$T/summarize_captures.py" "$id" --print | head -8 | cut -c1-200; }
sid() { python -I -c "
import json,sys
for l in open(r'$RAW/$1/stdout.jsonl',encoding='utf-8'):
    o=json.loads(l)
    if o.get('type')=='system' and o.get('subtype')=='init': print(o['session_id']); break"; }
PRE=()

run E05b-bash-realfail "Use the Bash tool to run exactly: ls nonexistent-file-here.txt   Then report the exit code and stderr in one line. Do not retry." --allowedTools "Bash(ls:*)"
run E11-subagent "Use the Agent tool with subagent_type general-purpose and the prompt: 'Read the file notes.txt in the current directory and reply with only its last line.' Then tell me what the subagent returned."
run E12-subagent-error "Call the Agent tool exactly once with subagent_type 'does-not-exist-agent' and prompt 'hello'. Report the exact error you get back. Do not retry."
run E14-background "Use the Bash tool with run_in_background set to true to run exactly: sleep 45   Then, without waiting, stop that background task with the TaskStop tool. Report the task id and what each tool returned." --allowedTools "Bash(sleep:*)"

run E15a-session-create "Remember the token ZEBRA-5512. Reply with only: OK"
S=$(sid E15a-session-create); echo "session=$S"
run E15b-resume "What token did I ask you to remember? Reply with only the token." --resume "$S"
run E15c-continue "Reply with only the token again, then the word CONT." --continue
run E15d-fork "Reply with only the token again, then the word FORK." --resume "$S" --fork-session
run E17a-compact-manual "/compact Keep the token." --resume "$S"
run E17b-after-compact "What token did I ask you to remember? Reply with only the token." --resume "$S"

[ "${SKIP_FAULTS:-0}" = 1 ] && exit 0
PRE=(--fault '{"path_contains":"/v1/messages","status":529,"times":2,"body":{"type":"error","error":{"type":"overloaded_error","message":"Overloaded (lab injected)"}}}')
run E18a-fault-529x2 "Reply with exactly: after-529"
PRE=(--fault '{"path_contains":"/v1/messages","status":500,"times":1,"body":{"type":"error","error":{"type":"api_error","message":"Internal (lab injected)"}}}')
run E18b-fault-500x1 "Reply with exactly: after-500"
PRE=(--fault '{"path_contains":"/v1/messages","status":400,"times":1,"body":{"type":"error","error":{"type":"invalid_request_error","message":"lab injected invalid request"}}}')
run E18c-fault-400 "Reply with exactly: after-400"
PRE=(--fault '{"path_contains":"/v1/messages","mode":"reset","times":1}')
run E18d-fault-reset "Reply with exactly: after-reset"
PRE=(--fault '{"path_contains":"/v1/messages","status":429,"times":1,"headers":{"retry-after":"2"},"body":{"type":"error","error":{"type":"rate_limit_error","message":"lab injected 429"}}}')
run E18e-fault-429-retryafter "Reply with exactly: after-429"
