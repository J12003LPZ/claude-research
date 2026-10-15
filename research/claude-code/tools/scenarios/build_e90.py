"""Exploration-tool and read-guard scenarios with a scripted model (no upstream model call).
usage: build_e90.py <exp id> <glob|grep|read|guardw|guarde|guardr>
  glob    130 files with ascending mtimes, a gitignored dir, a hidden dir and node_modules: Glob limit, order, ignore rules, errors
  grep    a git project: Grep default limit, pagination, output modes, gitignore, hidden files, long lines, validation errors
  grepsize  two files whose full Grep output is about 15 KB and about 29 KB (head_limit 0): where Grep output is persisted
  grepslow  40,000 small files, each holding a match: Grep under a 1 s ripgrep timeout (set CLAUDE_CODE_GLOB_TIMEOUT_SECONDS=1)
  read    Read on a 3,000-line file, a token-heavy file, an oversized file, a long line, a missing file, a directory, a binary file
  guardw  Write on an existing file that was never Read
  guarde  Edit on an existing file that was never Read
  guardr  Read, then an external change to the file, then an Edit whose old_string still applies
Creates a disposable project under cc-rea-lab/ and writes lab/raw/<id>/http/fault.json. Prints the project dir.
Prompt for every mode: 'E90-LAB start'. The projects hold synthetic data only.
"""
import json
import os
import subprocess
import sys

exp, mode = sys.argv[1], sys.argv[2]
if not exp or any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-" for ch in exp):
    raise SystemExit("exp id must contain only ASCII letters, digits, '_' or '-'")
LAB = r"C:/Users/sergi/cc-rea-lab"
RAW = r"C:/Users/sergi/Desktop/claude-rea/lab/raw"
proj = f"{LAB}/proj-{exp.lower()}"
os.makedirs(proj, exist_ok=True)


def write(rel, data, binary=False):
    path = f"{proj}/{rel}"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb" if binary else "w", newline="" if not binary else None) as fh:
        fh.write(data)
    return path


def git_init():
    subprocess.run(["git", "init", "-q"], cwd=proj, check=True)


def calls(*blocks):
    return {"model": "claude-haiku-5-5", "stop_reason": "tool_use", "content": list(blocks)}


def text(value):
    return {"model": "claude-haiku-5-5", "stop_reason": "end_turn", "content": [{"type": "text", "text": value}]}


def use(tool_id, name, inp):
    return {"type": "tool_use", "id": tool_id, "name": name, "input": inp}


def chain(prefix, steps, done):
    """One request per step: step k is sent once the request already carries step k-1's id and not step k's."""
    ids = [f"toolu_{prefix}_{k + 1}" for k in range(len(steps))]
    seq = [{"body_contains": "E90-LAB", "body_not_contains": [ids[0]],
            "response": calls(use(ids[0], steps[0][0], steps[0][1]))}]
    for k in range(1, len(steps)):
        seq.append({"body_contains": ids[k - 1], "body_not_contains": [ids[k]],
                    "response": calls(use(ids[k], steps[k][0], steps[k][1]))})
    seq.append({"body_contains": ids[-1], "response": text(done)})
    return seq


seq = []
if mode == "glob":
    git_init()
    base = 1_700_000_000
    for i in range(130):
        path = write(f"src/f{i:03d}.txt", f"file {i}\n")
        os.utime(path, (base + i * 60, base + i * 60))
    write(".gitignore", "ig/\n")
    for rel in ("ig/ignored.txt", "node_modules/nm.txt", ".hidden/h.txt"):
        path = write(rel, "x\n")
        os.utime(path, (base + 200 * 60, base + 200 * 60))
    steps = [
        ("Glob", {"pattern": "**/*.txt"}),
        ("Glob", {"pattern": "**/*.txt", "path": f"{proj}/nope"}),
        ("Glob", {"pattern": "src/f00*.txt"}),
        ("Glob", {"pattern": "**/*.zzz"}),
        ("Glob", {"pattern": "**/HEAD"}),
        ("Glob", {"pattern": ".git/**", "path": proj}),
    ]
    seq = chain("g51", steps, "glob-done")
elif mode == "grep":
    git_init()
    write("a.py", "".join(f"needle {i}\n" for i in range(3000)))
    write("b.py", "alpha\nneedle b1\nneedle b2\nomega\n")
    write(".gitignore", "ig/\n")
    write("ig/c.py", "needle ignored\n")
    write(".hid.py", "needle hidden\n")
    write("long.txt", "needle " + "z" * 800 + "\n")
    steps = [
        ("Grep", {"pattern": "needle", "output_mode": "content"}),
        ("Grep", {"pattern": "needle"}),
        ("Grep", {"pattern": "needle", "output_mode": "count"}),
        ("Grep", {"pattern": "needle", "output_mode": "content", "head_limit": 0}),
        ("Grep", {"pattern": "needle", "output_mode": "content", "offset": 250, "head_limit": 5}),
        ("Grep", {"pattern": "needle", "head_limit": -1}),
        ("Grep", {"pattern": "needle", "path": f"{proj}/nope"}),
        ("Grep", {"pattern": "("}),
        ("Grep", {"pattern": "needle b", "output_mode": "content", "glob": "*.py"}),
        ("Grep", {"pattern": "needle z", "output_mode": "content"}),
    ]
    seq = chain("r51", steps, "grep-done")
elif mode == "grepsize":
    git_init()
    write("s1.py", "".join(f"needleaa {i:04d}\n" for i in range(700)))
    write("s2.py", "".join(f"needlebb {i:04d}\n" for i in range(1300)))
    steps = [
        ("Grep", {"pattern": "needleaa", "output_mode": "content", "head_limit": 0}),
        ("Grep", {"pattern": "needlebb", "output_mode": "content", "head_limit": 0}),
    ]
    seq = chain("s51", steps, "grepsize-done")
elif mode == "grepslow":
    git_init()
    for d in range(400):
        for f in range(100):
            path = f"{proj}/tree/d{d:03d}/f{f:03d}.txt"
            if f == 0:
                os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as fh:
                fh.write("needleslow here\n")
    steps = [
        ("Grep", {"pattern": "needleslow", "output_mode": "count"}),
        ("Grep", {"pattern": "needleslow", "output_mode": "files_with_matches", "head_limit": 0}),
    ]
    seq = chain("sl51", steps, "grepslow-done")
elif mode == "read":
    write("lines3000.txt", "".join(f"line {i}\n" for i in range(3000)))
    write("lines30000.txt", "".join("xxxxxxx\n" for _ in range(30000)))
    write("huge.txt", ("y" * 99 + "\n") * 3000)
    write("longline.txt", "a" * 5000 + "\nsecond\n")
    write("blob.bin", bytes(range(256)) * 8, binary=True)
    write("src/missing.txt", "sibling\n")
    steps = [
        ("Read", {"file_path": f"{proj}/lines3000.txt"}),
        ("Read", {"file_path": f"{proj}/lines3000.txt"}),
        ("Read", {"file_path": f"{proj}/lines30000.txt"}),
        ("Read", {"file_path": f"{proj}/lines30000.txt", "offset": 1, "limit": 30000}),
        ("Read", {"file_path": f"{proj}/huge.txt"}),
        ("Read", {"file_path": f"{proj}/huge.txt", "offset": 1, "limit": 10}),
        ("Read", {"file_path": f"{proj}/longline.txt"}),
        ("Read", {"file_path": f"{proj}/src/missing.py"}),
        ("Read", {"file_path": f"{proj}/src"}),
        ("Read", {"file_path": f"{proj}/blob.bin"}),
    ]
    seq = chain("d51", steps, "read-done")
elif mode in ("guardw", "guarde", "guardr"):
    write("src/app.py", "def add(a, b):\n    return a - b\n")
    app = f"{proj}/src/app.py"
    if mode == "guardw":
        steps = [("Write", {"file_path": app, "content": "def add(a, b):\n    return a + b\n"})]
    elif mode == "guarde":
        steps = [("Edit", {"file_path": app, "old_string": "return a - b", "new_string": "return a + b"})]
    else:
        steps = [
            ("Read", {"file_path": app}),
            ("Bash", {"command": "python -c \"open('src/app.py','a').write('# external note\\n')\"",
                      "description": "lab external change"}),
            ("Edit", {"file_path": app, "old_string": "return a - b", "new_string": "return a + b"}),
        ]
    seq = chain("w51", steps, "guard-done")
else:
    raise SystemExit("mode must be glob, grep, grepsize, grepslow, read, guardw, guarde or guardr")

fault = {"path_contains": "/v1/messages", "sequence": seq,
         "otherwise": {"status": 400, "body": {"type": "error", "error": {
             "type": "invalid_request_error", "message": "lab otherwise"}}}}
os.makedirs(f"{RAW}/{exp}/http", exist_ok=True)
json.dump(fault, open(f"{RAW}/{exp}/http/fault.json", "w"))
print(proj)
