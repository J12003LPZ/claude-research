#!/usr/bin/env bash
# One command for the local gate lane. Prints a pass/fail line per gate and exits 1 on any failure.
#   bash research/claude-code/tools/run_gates.sh
# Needs the extracted Bun tree at extracted/2.1.296/~BUN/root (not committed; see README "Reproducing").
cd "$(dirname "$0")/../../.." || exit 1
S=research/claude-code
ROOT="${CLAUDE_REA_EXTRACTED_ROOT:-$PWD/extracted/2.1.296/~BUN/root}"
# Windows Python cannot resolve Git-Bash style /c/... paths; convert when cygpath exists.
if command -v cygpath >/dev/null 2>&1; then ROOT=$(cygpath -m "$ROOT"); fi
TMP="${TEMP:-/tmp}"
fail=0
gate() { # name, command...
  local name=$1; shift
  if out=$("$@" 2>&1); then printf 'PASS  %s\n' "$name"; else printf 'FAIL  %s\n%s\n' "$name" "$out" | head -20; fail=1; fi
}

gate "python tests"        python -I -m unittest discover -s $S/tools -p 'test_*.py'
gate "davinci tests"       python -I -m unittest discover -s research/claude-code/davinci-success-research/tests -p 'test_*.py'
for f in test_capture_proxy test_capture_proxy_runtime test_scripted_response; do
  gate "node $f"           node $S/tools/$f.mjs
done
gate "node syntax"         node --check $S/tools/capture_proxy.mjs
gate "manifest + redaction" python -I $S/tools/build_manifest.py
gate "run counts in prose"  python -I $S/tools/sync_counts.py --check
gate "matrix footer"        python -I $S/tools/check_matrix.py

if [ -d "$ROOT" ]; then
  cit=$(python -I $S/tools/audit_static_citations.py --root "$ROOT" --output "$TMP/g-c.json" $S/static-0*.md 2>&1 \
        && python -I -c "import json,sys;s=json.load(open(sys.argv[1]))['summary'];sys.exit(0 if s['anchors_missing_file']==0 and s['anchors_out_of_bounds']==0 and s['anchors_total']==s['anchors_resolvable'] else 1)" "$TMP/g-c.json" 2>&1) \
    && printf 'PASS  static citations\n' || { printf 'FAIL  static citations\n%s\n' "$cit"; fail=1; }
  clm=$(python -I $S/tools/audit_static_claims.py --root "$ROOT" --output "$TMP/g-k.json" $S/static-0*.md 2>&1 \
        && python -I -c "import json,sys;s=json.load(open(sys.argv[1]))['summary'];print('units',s['units_total'],'anchored',s['units_all_anchors_resolvable']);sys.exit(0 if s['units_has_invalid_anchor']==0 else 1)" "$TMP/g-k.json" 2>&1) \
    && printf 'PASS  static claims (%s)\n' "$clm" || { printf 'FAIL  static claims\n%s\n' "$clm"; fail=1; }
else
  printf 'FAIL  static audits (extracted tree not found: %s)\n' "$ROOT"
  fail=1
fi
exit $fail
