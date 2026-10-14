"""Hook-event coverage scenario with a scripted model.
usage: build_e46.py <exp id> <hooks|permreq>
  hooks    all 33 hook events logged; the session expands a slash command, fails a Read, batches tools and runs a subagent
  permreq  default permission mode, a Bash call that needs approval, a PermissionRequest hook that allows it
Prints the project dir. The hook log lands in <project>/hooklog/hooklog.jsonl (LAB_HOOK_LOG_DIR).
"""
import json
import os
import sys

exp, mode = sys.argv[1], sys.argv[2]
LAB = r"C:/Users/sergi/cc-rea-lab"
RAW = r"C:/Users/sergi/Desktop/claude-rea/lab/raw"
proj = f"{LAB}/proj-{exp.lower()}"
os.makedirs(f"{proj}/.claude/commands", exist_ok=True)
os.makedirs(f"{proj}/hooklog", exist_ok=True)
for stale in ("hooklog/hooklog.jsonl",):
    if os.path.exists(f"{proj}/{stale}"):
        os.remove(f"{proj}/{stale}")

EVENTS = ["PreToolUse", "PostToolUse", "PostToolUseFailure", "PostToolBatch", "Notification", "UserPromptSubmit",
          "UserPromptExpansion", "SessionStart", "SessionEnd", "Stop", "StopFailure", "SubagentStart", "SubagentStop",
          "PreCompact", "PostCompact", "PreModelSwitch", "PostModelSwitch", "PermissionRequest", "PermissionDenied",
          "Setup", "TeammateIdle", "TaskCreated", "TaskCompleted", "Elicitation", "ElicitationResult", "ConfigChange",
          "WorktreeCreate", "WorktreeRemove", "InstructionsLoaded", "CwdChanged", "FileChanged", "DirectoryAdded",
          "MessageDisplay"]


def text(value):
    return {"model": "claude-haiku-5-5", "stop_reason": "end_turn", "content": [{"type": "text", "text": value}]}


def calls(*blocks):
    return {"model": "claude-haiku-5-5", "stop_reason": "tool_use", "content": list(blocks)}


def tool(tool_id, name, tool_input):
    return {"type": "tool_use", "id": tool_id, "name": name, "input": tool_input}


seq = []
if mode == "hooks":
    open(f"{proj}/.claude/commands/lab.md", "w").write("---\ndescription: lab command\n---\nExpanded lab command: $ARGUMENTS\n")
    hooks = {e: [{"hooks": [{"type": "command", "command": f"python C:/Users/sergi/cc-rea-lab/hooklog.py {e} log"}]}]
             for e in EVENTS}
    json.dump({"hooks": hooks}, open(f"{proj}/.claude/settings.json", "w"))
    seq = [
        {"body_contains": "ROOT-LAB", "body_not_contains": ["toolu_e46_read", "toolu_e46_agent"],
         "response": calls(tool("toolu_e46_read", "Read", {"file_path": f"{proj}/missing-file.txt"}),
                           tool("toolu_e46_bash", "Bash", {"command": "echo batch-ok", "description": "lab"}))},
        {"body_contains": "toolu_e46_read", "body_not_contains": ["toolu_e46_agent"],
         "response": calls(tool("toolu_e46_agent", "Agent", {"description": "lab child", "prompt": "CHILD-E46 say hi",
                                                              "subagent_type": "general-purpose",
                                                              "run_in_background": False}))},
        {"body_contains": "CHILD-E46", "body_not_contains": ["toolu_e46_agent", "toolu_e46_read"],
         "response": text("child-done")},
        {"body_contains": "toolu_e46_agent", "response": text("all-done")},
    ]
elif mode == "permreq":
    hook = f"{proj}/.claude/permreq.py"
    open(hook, "w").write(
        "import json, os, sys, time\n"
        "t_in = time.time()\n"
        "d = json.loads(sys.stdin.read() or '{}')\n"
        "rec = {'t_in': t_in, 't_out': time.time(), 'tag': 'PermissionRequest', 'mode': 'allow', 'pid': os.getpid(), 'ppid': os.getppid(), 'cwd': os.getcwd(), 'env_names': sorted(k for k in os.environ if k.startswith('CLAUDE')), 'stdin': d}\n"
        "with open(os.path.join(os.environ.get('LAB_HOOK_LOG_DIR', os.path.dirname(__file__)), 'hooklog.jsonl'), 'a', encoding='utf-8') as f: f.write(json.dumps(rec) + '\\n')\n"
        "print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PermissionRequest', 'decision': {'behavior': 'allow'}}}))\n")
    json.dump({"hooks": {"PermissionRequest": [{"hooks": [{"type": "command", "command": f"python {hook}"}]}]}},
              open(f"{proj}/.claude/settings.json", "w"))
    cmd = "python -c \"open('permreq-made.txt','w').write('x')\""
    seq = [
        {"body_contains": "ROOT-LAB", "body_not_contains": ["toolu_e46_pr"],
         "response": calls(tool("toolu_e46_pr", "Bash", {"command": cmd, "description": "lab write"}))},
        {"body_contains": "toolu_e46_pr", "response": text("permreq-done")},
    ]
else:
    raise SystemExit("mode must be hooks or permreq")

fault = {"path_contains": "/v1/messages", "sequence": seq,
         "otherwise": {"status": 400, "body": {"type": "error", "error": {
             "type": "invalid_request_error", "message": "lab otherwise"}}}}
os.makedirs(f"{RAW}/{exp}/http", exist_ok=True)
json.dump(fault, open(f"{RAW}/{exp}/http/fault.json", "w"))
print(proj)
