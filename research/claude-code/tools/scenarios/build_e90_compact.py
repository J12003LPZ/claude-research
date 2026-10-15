"""Compaction fidelity scenario with a scripted model (no upstream model call).
usage: build_e90_compact.py <base id> [util bytes] [util line width] [count_tokens answer]
Creates a disposable project under cc-rea-lab/ and three fault.json files:
  <base>1-turn     prompt 'COMPACT-LAB turn1': reads 7 files (one large), fails a test, edits, passes the test
  <base>2-compact  prompt '/compact Keep the token.' (resumed session): the summary request gets a canned reply
  <base>3-after    prompt 'COMPACT-LAB after' (resumed session): captures the first request after compaction
Prints the project dir. The canned summary carries the marker CANNED-SUMMARY-MARKER so probes can find it.
"""
import json
import os
import sys

base = sys.argv[1]
UTIL_BYTES = int(sys.argv[2]) if len(sys.argv) > 2 else 0   # 0 keeps the default 1,500-function file
UTIL_WIDTH = int(sys.argv[3]) if len(sys.argv) > 3 else 80
COUNT_TOKENS = int(sys.argv[4]) if len(sys.argv) > 4 else 1000   # answer for POST /v1/messages/count_tokens
if not base or any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-" for ch in base):
    raise SystemExit("base id must contain only ASCII letters, digits, '_' or '-'")
LAB = r"C:/Users/sergi/cc-rea-lab"
RAW = r"C:/Users/sergi/Desktop/claude-rea/lab/raw"
proj = f"{LAB}/proj-{base.lower()}"
os.makedirs(f"{proj}/src", exist_ok=True)

open(f"{proj}/src/app.py", "w").write("def add(a, b):\n    return a - b\n")
open(f"{proj}/run_tests.py", "w").write(
    "import sys\nsys.path.insert(0, 'src')\nfrom app import add\n"
    "if add(2, 3) != 5:\n    print('FAILED: add(2, 3) != 5')\n    sys.exit(1)\nprint('PASSED')\n")
open(f"{proj}/notes.md", "w").write("note one\nnote two\n")
for name in ("a", "b", "c", "d"):
    open(f"{proj}/src/{name}.txt", "w").write(f"file {name}\n" * 5)
# the largest file read in the turn; UTIL_BYTES sets its size, the default is a 1,500-function file (about 60 KB)
if UTIL_BYTES:
    line = "# " + "x" * (UTIL_WIDTH - 3) + "\n"
    open(f"{proj}/src/util.py", "w").write(line * max(1, UTIL_BYTES // len(line)))
else:
    open(f"{proj}/src/util.py", "w").write("".join(f"def helper_{i:04d}(x):\n    return x + {i}\n\n" for i in range(1500)))
open(f"{proj}/CLAUDE.md", "w").write("# Project notes\nKeep failing test names when compacting.\n")
if os.environ.get("MTIME_ORDER"):
    # give each file a distinct modification time so the restore order cannot come from ties.
    # "reversed": the file read first is the oldest on disk is false here, it is the newest; "forward": the file read last is the newest.
    import time
    order = ["notes.md", "src/a.txt", "src/b.txt", "src/util.py", "src/c.txt", "src/d.txt", "src/app.py"]   # read order
    now = time.time()
    for rank, rel in enumerate(order):
        age = (rank if os.environ["MTIME_ORDER"] == "reversed" else len(order) - rank) * 100
        os.utime(f"{proj}/{rel}", (now - age, now - age))


_n = [0]


def _mid():
    # a distinct message id per scripted reply: with one shared id the CLI merges consecutive assistant
    # blocks into a single message, which would change the message counts these runs are meant to show
    _n[0] += 1
    return f"msg_cp_{_n[0]:03d}"


def text(value):
    return {"id": _mid(), "model": "claude-haiku-5-5", "stop_reason": "end_turn", "content": [{"type": "text", "text": value}]}


def use(tool_id, name, inp):
    return {"type": "tool_use", "id": tool_id, "name": name, "input": inp}


def calls(*blocks):
    return {"id": _mid(), "model": "claude-haiku-5-5", "stop_reason": "tool_use", "content": list(blocks)}


FIX_OLD = "    return a - b\n"
FIX_NEW = "    return a + b\n"
reads = ["notes.md", "src/a.txt", "src/b.txt", "src/util.py", "src/c.txt", "src/d.txt", "src/app.py"]
steps = [use(f"toolu_cp_r{i}", "Read", {"file_path": f"{proj}/{p}"}) for i, p in enumerate(reads)]
steps.append(use("toolu_cp_t1", "Bash", {"command": "python run_tests.py", "description": "run tests (fails)"}))
steps.append(use("toolu_cp_e1", "Edit", {"file_path": f"{proj}/src/app.py", "old_string": FIX_OLD, "new_string": FIX_NEW}))
steps.append(use("toolu_cp_t2", "Bash", {"command": "python run_tests.py", "description": "run tests (passes)"}))
turn1 = []
turn1.append({"body_contains": "COMPACT-LAB turn1", "body_not_contains": [steps[0]["id"]], "response": calls(steps[0])})
for k in range(1, len(steps)):
    turn1.append({"body_contains": steps[k - 1]["id"], "body_not_contains": [steps[k]["id"]], "response": calls(steps[k])})
turn1.append({"body_contains": steps[-1]["id"], "response": text("turn1-done: add() fixed, run_tests.py PASSED")})

SUMMARY = ("<analysis>scripted analysis block</analysis>\n<summary>\nCANNED-SUMMARY-MARKER\n"
           "1. Primary Request and Intent: fix add() in src/app.py (scripted).\n"
           "9. Optional Next Step: none.\n</summary>")
compact = [{"body_contains": "CRITICAL: Respond with TEXT ONLY", "response": text(SUMMARY)}]
if os.environ.get("AFTER_EDITS"):
    # edit one file that compaction restored (d.txt) and two that it did not (notes.md, a.txt)
    edits = [use("toolu_cp_x1", "Edit", {"file_path": f"{proj}/src/d.txt", "old_string": "file d\n", "new_string": "FILE D\n", "replace_all": True}),
             use("toolu_cp_x2", "Edit", {"file_path": f"{proj}/notes.md", "old_string": "note one", "new_string": "NOTE ONE"}),
             use("toolu_cp_x3", "Edit", {"file_path": f"{proj}/src/a.txt", "old_string": "file a\n", "new_string": "FILE A\n", "replace_all": True})]
    after = [{"body_contains": "COMPACT-LAB after", "body_not_contains": ["toolu_cp_x1"], "response": calls(edits[0])},
             {"body_contains": "toolu_cp_x1", "body_not_contains": ["toolu_cp_x2"], "response": calls(edits[1])},
             {"body_contains": "toolu_cp_x2", "body_not_contains": ["toolu_cp_x3"], "response": calls(edits[2])},
             {"body_contains": "toolu_cp_x3", "response": text("after-ok")}]
else:
    after = [{"body_contains": "COMPACT-LAB after", "response": text("after-ok")}]
counts = [{"path_contains": "count_tokens", "status": 200, "body": {"input_tokens": COUNT_TOKENS}} for _ in range(40)]
for suffix, seq in (("1-turn", turn1), ("2-compact", compact), ("3-after", after)):
    seq = seq + counts   # the CLI asks the API to count a large file before restoring it; answer locally
    d = f"{RAW}/{base}{suffix}/http"
    os.makedirs(d, exist_ok=True)
    json.dump({"path_contains": "/v1/messages", "sequence": seq, "otherwise": {"status": 400, "body": {"type": "error", "error": {
        "type": "invalid_request_error", "message": "lab otherwise"}}}},
              open(f"{d}/fault.json", "w"))
# one process, three turns (run_e90_compact_1p.sh): every entry in one sequence, matched by its markers
single = f"{RAW}/{base}0-single/http"
os.makedirs(single, exist_ok=True)
json.dump({"path_contains": "/v1/messages", "sequence": turn1 + compact + after + counts, "otherwise": {"status": 400, "body": {
    "type": "error", "error": {"type": "invalid_request_error", "message": "lab otherwise"}}}}, open(f"{single}/fault.json", "w"))
print(proj)
