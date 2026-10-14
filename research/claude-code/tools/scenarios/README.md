# Scripted-model scenarios

Builders for the experiments that run with the lab proxy's `sequence` mode (`tools/capture_proxy.mjs`,
`tools/scripted_response.mjs`): the proxy answers every `/v1/messages` with a canned reply, so the real CLI runs its
real tools and hooks with no upstream model call.

| File | Experiment | What it builds |
|---|---|---|
| `build_e39.py` | E39a/b/c | background or foreground agent, parent interrupt (`run_stream.py` script) |
| `build_e40.py` | E40 | always-blocking `Stop` hook project and a 15-reply sequence |
| `build_e41.py`, `run_e41.sh` | E41 to E42c | `auto` mode: scripted classifier severities (`"30>90"` = stage 1 then stage 2) |
| `build_e43.py` | E43 | background agent whose Bash calls the scripted classifier denies |

Paths are absolute for this machine (as in the other tools). `build_*` write the fault sequence to
`lab/raw/<id>/http/fault.json` and create a disposable project under `cc-rea-lab/`. Run them with `run_exp.py` or
`run_stream.py` and `CLAUDE_BIN` pinned to the original binary.
