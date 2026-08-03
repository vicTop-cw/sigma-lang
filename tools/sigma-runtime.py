#!/usr/bin/env python3
"""
ΣLang Audit Runtime — sigma-runtime.py
======================================
Executes the canonical SocketKit business trace (task_create → review_merge →
contribution_score) against the §SK reference implementation
(impl/python/sigma_core.py) and emits a per-event ΣLang obligation log.

Every event output is checked against the §SK laws from
spec/spec_p0_socketkit.md. Exit code 0 = every obligation satisfied.

    python3 tools/sigma-runtime.py            # human-readable audit log
    python3 tools/sigma-runtime.py --json     # machine-readable audit log

Spec: spec/spec_p0_socketkit.md (§SK) — 「来找茬」app behavior made auditable.
"""

import importlib.util
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE_PATH = os.path.join(REPO_ROOT, "impl", "python", "sigma_core.py")


def load_core():
    """Import sigma_core.py by path (stdlib-only, no PYTHONPATH games)."""
    spec = importlib.util.spec_from_file_location("sigma_core", CORE_PATH)
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)
    return core


# ---------------------------------------------------------------------------
# Canonical SocketKit trace (spec_p0_socketkit.md §SK.3)
# ---------------------------------------------------------------------------

def run_trace(core):
    """Run the canonical trace, returning a list of event audit records.

    Each record: {event, op, input, output, obligations: [{law, ok, note}]}.
    """
    events = []

    def record(event, op, inp, out, obligations):
        events.append({
            "event": event,
            "op": op,
            "input": inp,
            "output": out,
            "obligations": obligations,
        })

    # --- SK.3.1 task_create -------------------------------------------------
    task = core.task_create(7, 100)
    record("task_create", "SK.3.1", [7, 100], task, [
        {"law": "0 ≤ task_create(a, b) — bounty ≥ 0",
         "ok": task[1] >= 0, "note": f"bounty={task[1]}"},
        {"law": "index(task_create(a, b), 2) ≡ 0 — freshly created task is open",
         "ok": task[2] == 0, "note": f"status={task[2]}"},
    ])

    # Negative bounty is rejected at the type boundary (Bounty : Type ≝ ℕ).
    try:
        core.task_create(9, -5)
        record("task_create", "SK.3.1", [9, -5], "ACCEPTED(-5)?", [
            {"law": "Bounty : Type ≝ ℕ — negative bounty rejected",
             "ok": False, "note": "negative bounty accepted — boundary violated"},
        ])
    except ValueError as e:
        record("task_create", "SK.3.1", [9, -5], f"rejected ({e})", [
            {"law": "Bounty : Type ≝ ℕ — negative bounty rejected",
             "ok": True, "note": "BountyErr raised at boundary"},
        ])

    # --- SK.3.2 review_merge ------------------------------------------------
    os_accept = [[1, 1, 3], [2, 1, 2]]          # accept 5 ≥ reject 0
    d1 = core.review_merge(os_accept)
    d1_rev = core.review_merge(list(reversed(os_accept)))
    record("review_merge", "SK.3.2", os_accept, d1, [
        {"law": "review_merge(o) ≡ 0 ∨ review_merge(o) ≡ 1 — decision is binary",
         "ok": d1 in (0, 1), "note": f"decision={d1}"},
        {"law": "review_merge(o) ≡ review_merge(reverse(o)) — order-independent",
         "ok": d1 == d1_rev, "note": f"reversed also gives {d1_rev}"},
    ])

    os_reject = [[1, 0, 5], [2, 1, 2]]          # accept 2 < reject 5
    d2 = core.review_merge(os_reject)
    record("review_merge", "SK.3.2", os_reject, d2, [
        {"law": "review_merge(o) ≡ 0 ∨ review_merge(o) ≡ 1 — decision is binary",
         "ok": d2 in (0, 1), "note": f"decision={d2}"},
        {"law": "weighted majority — accept iff weighted_accept ≥ weighted_reject",
         "ok": d2 == 0, "note": "accept 2 < reject 5 → reject"},
    ])

    # --- SK.3.3 contribution_score ------------------------------------------
    acts = [[1, 1, 10], [2, 2, -4], [3, 1, 5]]  # fold → 11
    pts = core.contribution_score(acts)
    record("contribution_score", "SK.3.3", acts, pts, [
        {"law": "0 ≤ contribution_score(a) — points never negative",
         "ok": pts >= 0, "note": f"points={pts}"},
        {"law": "contribution_score(a) ≡ contribution_score(a ⊕ [0]) — zero delta neutral",
         "ok": pts == core.contribution_score(acts + [[9, 0, 0]]),
         "note": "appending [9, 0, 0] is neutral"},
    ])

    acts_floor = [[1, 1, -5], [2, 2, 3]]        # fold → -2, floored at 0
    pts2 = core.contribution_score(acts_floor)
    record("contribution_score", "SK.3.3", acts_floor, pts2, [
        {"law": "0 ≤ contribution_score(a) — points never negative",
         "ok": pts2 >= 0, "note": f"points={pts2} (folded -2, floored at 0)"},
    ])

    return events


def audit(events):
    """Flatten all obligations; every one must hold."""
    total = sum(len(e["obligations"]) for e in events)
    failed = sum(1 for e in events for ob in e["obligations"] if not ob["ok"])
    return total, failed


def render_human(events):
    lines = []
    lines.append("ΣLang Audit Runtime — SocketKit trace (spec_p0_socketkit.md §SK)")
    lines.append("=" * 64)
    for i, e in enumerate(events, 1):
        lines.append(f"[{i}] {e['op']} {e['event']}  input={e['input']}")
        lines.append(f"    → {e['output']}")
        for ob in e["obligations"]:
            mark = "✓" if ob["ok"] else "✗ VIOLATION"
            lines.append(f"    {mark} {ob['law']}  ({ob['note']})")
    total, failed = audit(events)
    if failed:
        lines.append(f"Audit: {total - failed}/{total} obligations satisfied — "
                     f"{failed} VIOLATION(S)")
    else:
        lines.append(f"Audit: {total}/{total} obligations satisfied — "
                     f"trace is ΣLang-auditable")
    return "\n".join(lines)


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    as_json = "--json" in argv

    core = load_core()
    events = run_trace(core)
    total, failed = audit(events)

    if as_json:
        print(json.dumps({
            "tool": "sigma-runtime",
            "spec": "spec_p0_socketkit.md §SK",
            "trace": events,
            "obligations_total": total,
            "violations": failed,
            "auditable": failed == 0,
        }, indent=2, ensure_ascii=False))
    else:
        print(render_human(events))

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
