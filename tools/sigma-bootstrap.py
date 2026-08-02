#!/usr/bin/env python3
"""
ΣLang AI Bootstrapping Test — sigma-bootstrap.py
================================================
MASTER_PLAN Phase 5 / P2 milestone: ONE clean run proving the bootstrapping
loop closes:  spec → impl → verify → pass.

Protocol under test (a fresh AI receives only the spec + verifier):
  1. read the spec modules — each must carry an `## Implementation Checklist
     (for AI)` section telling the AI exactly what to implement
  2. write the reference implementation (`impl/python/sigma_core.py`)
  3. run the verifier (`verify_p0.py`) and obtain a full pass

Run:  python3 tools/sigma-bootstrap.py
Exit code 0 = bootstrap loop closed (all steps pass).
"""

import os
import re
import subprocess
import sys

# Force UTF-8 on stdout/stderr so emoji/Unicode output survives Windows
# consoles (GBK/cp936 default), mirroring verify_p0.py.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The 4 P0 spec modules that must each carry an Implementation Checklist.
SPEC_MODULES = [
    ("spec/spec_p0_time.md",        "T"),
    ("spec/spec_p0_error.md",       "E"),
    ("spec/spec_p0_confidence.md",  "C"),
    ("spec/spec_p0_io.md",          "I"),
]
CHECKLIST_HEADING = "## Implementation Checklist (for AI)"
CHECKLIST_RE = re.compile(r"^##\s+Implementation Checklist\s+\(for\s+AI\)\s*$", re.M)

REF_IMPL = "impl/python/sigma_core.py"
VERIFIER = "verify_p0.py"


def _run(args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True)


def _ok(name, detail=""):
    print(f"  ✅ {name}" + (f" — {detail}" if detail else ""))
    return True


def _fail(name, detail=""):
    print(f"  ❌ {name}" + (f" — {detail}" if detail else ""))
    return False


def step1_specs_readable():
    """Protocol step 2+4: every P0 module spec has an Implementation Checklist."""
    print("Step 1: spec modules carry an Implementation Checklist (for AI)")
    ok = True
    for rel, tag in SPEC_MODULES:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            ok = _fail(f"{tag}: {rel}", "spec file missing") and ok
            continue
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        if not CHECKLIST_RE.search(text):
            ok = _fail(f"{tag}: {rel}", f"missing heading {CHECKLIST_HEADING!r}") and ok
        else:
            _ok(f"{tag}: {rel}", "checklist present")
    return ok


def step2_impl_exists_and_passes():
    """Protocol step 5: the reference implementation passes its canonical tests."""
    print("Step 2: reference implementation self-check")
    if not os.path.isfile(os.path.join(ROOT, REF_IMPL)):
        return _fail(REF_IMPL, "file missing")
    r = _run([sys.executable, REF_IMPL])
    out = (r.stdout + r.stderr).strip()
    if r.returncode != 0:
        return _fail(REF_IMPL, f"exit {r.returncode}: {out[-300:]}")
    m = re.search(r"(\d+)/(\d+) passed", out)
    detail = f"{m.group(1)}/{m.group(2)} passed" if m else out[-200:]
    if m and int(m.group(1)) == int(m.group(2)):
        return _ok(REF_IMPL, detail)
    return _fail(REF_IMPL, f"failed counts: {detail}")


def step3_verifier_passes():
    """Protocol step 6: the verifier certifies the implementation 95/95."""
    print("Step 3: verifier run (verify_p0.py)")
    r = _run([sys.executable, VERIFIER])
    out = (r.stdout + r.stderr).strip()
    if r.returncode != 0:
        return _fail(VERIFIER, f"exit {r.returncode}: {out[-300:]}")
    m = re.search(r"TOTAL:\s*(\d+)/(\d+)", out)
    if m and int(m.group(1)) == int(m.group(2)):
        return _ok(VERIFIER, f"{m.group(1)}/{m.group(2)} tests passed")
    return _fail(VERIFIER, "no 'TOTAL: N/N' pass line in output")


def main() -> int:
    print("ΣLang AI Bootstrapping Test — spec → impl → verify → pass\n")
    steps = [step1_specs_readable, step2_impl_exists_and_passes,
             step3_verifier_passes]
    results = [fn() for fn in steps]
    print()
    if all(results):
        print("🏆 BOOTSTRAP LOOP CLOSED — a fresh AI can go spec → impl → verify → pass")
        return 0
    print("⛔ BOOTSTRAP BLOCKED — fix the failing step(s) above, then re-run")
    return 1


if __name__ == "__main__":
    sys.exit(main())
