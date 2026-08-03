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

    # --- SK.3.1 task_create (发布需求) ---------------------------------------
    task = core.task_create(7, 100)
    record("task_create", "SK.3.1", [7, 100], task, [
        {"law": "0 ≤ task_create(a, b) — bounty ≥ 0",
         "ok": task[1] >= 0, "note": f"bounty={task[1]}"},
        {"law": "index(task_create(a, b), 2) ≡ 0 — freshly created task is open",
         "ok": task[2] == 0, "note": f"status={task[2]}"},
        {"law": "index(task_create(a, b), 3) ≡ 0 — freshly created task is unclaimed",
         "ok": task[3] == 0, "note": f"hunter={task[3]}"},
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

    # --- SK.3.2 accept_task (接单) --------------------------------------------
    claimed = core.accept_task(task, 3)
    record("accept_task", "SK.3.2", [task, 3], claimed, [
        {"law": "index(t, 2) ≡ 0 ⇒ index(accept_task(t, h), 2) ≡ 1 — claim moves to in_progress",
         "ok": claimed[2] == 1, "note": f"status={claimed[2]}"},
        {"law": "index(t, 2) ≡ 0 ⇒ index(accept_task(t, h), 3) ≡ h — hunter recorded",
         "ok": claimed[3] == 3, "note": f"hunter={claimed[3]}"},
    ])

    # Claiming a non-open task is a StateError (状态机前置).
    try:
        core.accept_task(claimed, 5)
        record("accept_task", "SK.3.2", [claimed, 5], "ACCEPTED(claimed)?", [
            {"law": "claiming a non-open task is a StateError",
             "ok": False, "note": "re-claim of in-progress task accepted"},
        ])
    except ValueError as e:
        record("accept_task", "SK.3.2", [claimed, 5], f"rejected ({e})", [
            {"law": "claiming a non-open task is a StateError",
             "ok": True, "note": "StateError raised on re-claim"},
        ])

    # --- SK.3.3 task_submit (提交成果) ----------------------------------------
    submitted = core.task_submit(claimed)
    record("task_submit", "SK.3.3", claimed, submitted, [
        {"law": "index(t, 2) ≡ 1 ⇒ index(task_submit(t), 2) ≡ 2 — submit moves to pending_review",
         "ok": submitted[2] == 2, "note": f"status={submitted[2]}"},
        {"law": "index(t, 2) ≡ 1 ⇒ index(task_submit(t), 3) ≡ index(t, 3) — hunter preserved",
         "ok": submitted[3] == claimed[3], "note": f"hunter={submitted[3]}"},
    ])

    # Submitting a non-in-progress task is a StateError.
    try:
        core.task_submit(task)
        record("task_submit", "SK.3.3", task, "SUBMITTED(open)?", [
            {"law": "submitting a non-in-progress task is a StateError",
             "ok": False, "note": "submit of open task accepted"},
        ])
    except ValueError as e:
        record("task_submit", "SK.3.3", task, f"rejected ({e})", [
            {"law": "submitting a non-in-progress task is a StateError",
             "ok": True, "note": "StateError raised on open-task submit"},
        ])

    # --- SK.3.4 task_accept (验收确认) ----------------------------------------
    done = core.task_accept(submitted, 7)  # caller 7 ≡ author (INV-4)
    record("task_accept", "SK.3.4", [submitted, 7], done, [
        {"law": "index(t, 2) ≡ 2 ⇒ index(task_accept(t, c), 2) ≡ 3 — accept moves to completed",
         "ok": done[2] == 3, "note": f"status={done[2]}"},
        {"law": "index(t, 2) ≡ 2 ⇒ index(task_accept(t, c), 3) ≡ index(t, 3) — hunter preserved",
         "ok": done[3] == submitted[3], "note": f"hunter={done[3]}"},
    ])

    # Accepting a non-pending task is a StateError.
    try:
        core.task_accept(task, 7)
        record("task_accept", "SK.3.4", [task, 7], "ACCEPTED(open)?", [
            {"law": "accepting a non-pending task is a StateError",
             "ok": False, "note": "accept of open task accepted"},
        ])
    except ValueError as e:
        record("task_accept", "SK.3.4", task, f"rejected ({e})", [
            {"law": "accepting a non-pending task is a StateError",
             "ok": True, "note": "StateError raised on open-task accept"},
        ])

    # --- SK.3.6 review_merge (增长期评审) --------------------------------------
    os_accept = [[1, 1, 3], [2, 1, 2]]          # accept 5 ≥ reject 0
    d1 = core.review_merge(os_accept)
    d1_rev = core.review_merge(list(reversed(os_accept)))
    record("review_merge", "SK.3.6", os_accept, d1, [
        {"law": "review_merge(o) ≡ 0 ∨ review_merge(o) ≡ 1 — decision is binary",
         "ok": d1 in (0, 1), "note": f"decision={d1}"},
        {"law": "review_merge(o) ≡ review_merge(reverse(o)) — order-independent",
         "ok": d1 == d1_rev, "note": f"reversed also gives {d1_rev}"},
    ])

    os_reject = [[1, 0, 5], [2, 1, 2]]          # accept 2 < reject 5
    d2 = core.review_merge(os_reject)
    record("review_merge", "SK.3.6", os_reject, d2, [
        {"law": "review_merge(o) ≡ 0 ∨ review_merge(o) ≡ 1 — decision is binary",
         "ok": d2 in (0, 1), "note": f"decision={d2}"},
        {"law": "weighted majority — accept iff weighted_accept ≥ weighted_reject",
         "ok": d2 == 0, "note": "accept 2 < reject 5 → reject"},
    ])

    # --- SK.3.5 contribution_score (贡献制) ------------------------------------
    acts = [[1, 1, 10], [2, 2, -4], [3, 1, 5]]  # fold → 11
    pts = core.contribution_score(acts)
    record("contribution_score", "SK.3.5", acts, pts, [
        {"law": "0 ≤ contribution_score(a) — points never negative",
         "ok": pts >= 0, "note": f"points={pts}"},
        {"law": "contribution_score(a) ≡ contribution_score(a ⊕ [0]) — zero delta neutral",
         "ok": pts == core.contribution_score(acts + [[9, 0, 0]]),
         "note": "appending [9, 0, 0] is neutral"},
    ])

    acts_floor = [[1, 1, -5], [2, 2, 3]]        # fold → -2, floored at 0
    pts2 = core.contribution_score(acts_floor)
    record("contribution_score", "SK.3.5", acts_floor, pts2, [
        {"law": "0 ≤ contribution_score(a) — points never negative",
         "ok": pts2 >= 0, "note": f"points={pts2} (folded -2, floored at 0)"},
    ])

    # --- SK.3.7 credit_score (契分制) ------------------------------------------
    cred = core.credit_score([])
    record("credit_score", "SK.3.7", [], cred, [
        {"law": "credit_score([]) ≡ 100 — base credit",
         "ok": cred == 100, "note": f"credit={cred}"},
    ])

    cred_done = core.credit_score([[0, 1], [0, 1]])  # two completions: 100+5+5
    record("credit_score", "SK.3.7", [[0, 1], [0, 1]], cred_done, [
        {"law": "kind 0 (complete): +5 per count — 每完成 1 单 +5",
         "ok": cred_done == 110, "note": f"credit={cred_done}"},
    ])

    cred_breach = core.credit_score([[1, 1]])  # one breach: 100×0.7
    record("credit_score", "SK.3.7", [[1, 1]], cred_breach, [
        {"law": "kind 1 (breach): ×0.7 per count — 违约 ×0.7",
         "ok": cred_breach == 70, "note": f"credit={cred_breach}"},
    ])

    # --- §SK.3.8 Invariants (状态机不变量, v0.18) -------------------------------
    # INV-1 状态单调: status 只前进不后退 (0 → 1 → 2 → 3).
    record("INV-1", "§SK.3.8", [task, claimed, submitted, done], done, [
        {"law": "INV-1 状态单调 — claim 0→1",
         "ok": claimed[2] > task[2], "note": f"{task[2]}→{claimed[2]}"},
        {"law": "INV-1 状态单调 — submit 1→2",
         "ok": submitted[2] > claimed[2], "note": f"{claimed[2]}→{submitted[2]}"},
        {"law": "INV-1 状态单调 — accept 2→3",
         "ok": done[2] > submitted[2], "note": f"{submitted[2]}→{done[2]}"},
    ])

    # INV-2 终态不可变: completed 任务不可再被任何状态操作改变.
    inv2_ok = True
    try:
        core.accept_task(done, 7)
        inv2_ok = False
    except ValueError:
        pass
    try:
        core.task_submit(done)
        inv2_ok = False
    except ValueError:
        pass
    try:
        core.task_accept(done, 7)
        inv2_ok = False
    except ValueError:
        pass
    record("INV-2", "§SK.3.8", done, "StateError×3", [
        {"law": "INV-2 终态不可变 — completed 任务 claim/submit/accept 全部 StateError",
         "ok": inv2_ok, "note": "所有状态操作被拒绝"},
    ])

    # INV-3 守恒: bounty 与 hunter 在状态流转中不变.
    record("INV-3", "§SK.3.8", [task, claimed, submitted, done], done, [
        {"law": "INV-3 守恒 — bounty 不变 (100)",
         "ok": (claimed[1] == task[1] and submitted[1] == task[1]
                and done[1] == task[1]),
         "note": f"bounty={task[1]}"},
        {"law": "INV-3 守恒 — hunter 一经记录不变 (3)",
         "ok": (submitted[3] == claimed[3] and done[3] == claimed[3]),
         "note": f"hunter={claimed[3]}"},
    ])

    # INV-4 作者授权: 只有受茬人本人可验收自己的单.
    try:
        core.task_accept(submitted, 9)  # 9 ≠ author 7
        record("INV-4", "§SK.3.8", [submitted, 9], "ACCEPTED(9)?", [
            {"law": "INV-4 作者授权 — 非作者 caller 验收被拒绝",
             "ok": False, "note": "非作者验收成功"},
        ])
    except ValueError as e:
        record("INV-4", "§SK.3.8", [submitted, 9], f"rejected ({e})", [
            {"law": "INV-4 作者授权 — 非作者 caller 验收被拒绝",
             "ok": True, "note": "AuthError 拒绝非作者 (caller 9 ≠ author 7)"},
        ])
    try:
        core.task_accept(submitted, 7)  # 7 ≡ author
        record("INV-4", "§SK.3.8", [submitted, 7], "ACCEPTED(7)", [
            {"law": "INV-4 作者授权 — 作者本人验收成功",
             "ok": True, "note": "caller 7 ≡ author 7 → completed"},
        ])
    except ValueError as e:
        record("INV-4", "§SK.3.8", [submitted, 7], f"rejected ({e})", [
            {"law": "INV-4 作者授权 — 作者本人验收成功",
             "ok": False, "note": f"作者被拒绝: {e}"},
        ])

    # --- §PF Portfolio Protocol (spec_p0_portfolio.md) -------------------------
    # 第二个自举新域：金融投资组合 — portfolio_new / buy / sell / value / risk.
    pf0 = core.portfolio_new(100)
    record("portfolio_new", "§PF.3.1", [100], pf0, [
        {"law": "0 ≤ portfolio_new(c) — cash ≥ 0",
         "ok": pf0[0] >= 0, "note": f"cash={pf0[0]}"},
        {"law": "index(portfolio_new(c), 1) ≡ 0 — qtyA starts at 0",
         "ok": pf0[1] == 0, "note": f"qtyA={pf0[1]}"},
        {"law": "index(portfolio_new(c), 2) ≡ 0 — qtyB starts at 0",
         "ok": pf0[2] == 0, "note": f"qtyB={pf0[2]}"},
    ])

    try:
        core.portfolio_new(-5)
        record("portfolio_new", "§PF.3.1", [-5], "ACCEPTED(-5)?", [
            {"law": "Cash : Type ≝ ℕ — negative cash rejected",
             "ok": False, "note": "negative cash accepted"},
        ])
    except ValueError as e:
        record("portfolio_new", "§PF.3.1", [-5], f"rejected ({e})", [
            {"law": "Cash : Type ≝ ℕ — negative cash rejected",
             "ok": True, "note": "TypeError raised at boundary"},
        ])

    pf1 = core.buy(pf0, 0, 30)
    record("buy", "§PF.3.2", [pf0, 0, 30], pf1, [
        {"law": "index(p, 0) ≥ q ⇒ portfolio_value(buy(p, a, q)) ≡ portfolio_value(p) — 守恒",
         "ok": core.portfolio_value(pf1) == core.portfolio_value(pf0),
         "note": f"value {core.portfolio_value(pf0)} → {core.portfolio_value(pf1)}"},
        {"law": "index(p, 0) ≥ q ⇒ index(buy(p, a, q), 0) ≥ 0 — cash never negative",
         "ok": pf1[0] >= 0, "note": f"cash={pf1[0]}"},
    ])

    try:
        core.buy(pf0, 0, 130)
        record("buy", "§PF.3.2", [pf0, 0, 130], "BOUGHT(130)?", [
            {"law": "insufficient cash → ⊥ InsufficientFunds",
             "ok": False, "note": "bought more than cash"},
        ])
    except ValueError as e:
        record("buy", "§PF.3.2", [pf0, 0, 130], f"rejected ({e})", [
            {"law": "insufficient cash → ⊥ InsufficientFunds",
             "ok": True, "note": "InsufficientFunds raised"},
        ])

    pf2 = core.sell(pf1, 0, 20)
    record("sell", "§PF.3.3", [pf1, 0, 20], pf2, [
        {"law": "index(p, a+1) ≥ q ⇒ portfolio_value(sell(p, a, q)) ≡ portfolio_value(p) — 守恒",
         "ok": core.portfolio_value(pf2) == core.portfolio_value(pf1),
         "note": f"value {core.portfolio_value(pf1)} → {core.portfolio_value(pf2)}"},
        {"law": "index(p, a+1) ≥ q ⇒ index(sell(p, a, q), a+1) ≥ 0 — no naked shorts",
         "ok": pf2[1] >= 0, "note": f"qtyA={pf2[1]}"},
    ])

    try:
        core.sell(pf1, 0, 40)
        record("sell", "§PF.3.3", [pf1, 0, 40], "SOLD(40)?", [
            {"law": "insufficient position → ⊥ InsufficientShares",
             "ok": False, "note": "sold more than held"},
        ])
    except ValueError as e:
        record("sell", "§PF.3.3", [pf1, 0, 40], f"rejected ({e})", [
            {"law": "insufficient position → ⊥ InsufficientShares",
             "ok": True, "note": "InsufficientShares raised"},
        ])

    val = core.portfolio_value(pf2)
    record("portfolio_value", "§PF.3.4", pf2, val, [
        {"law": "0 ≤ portfolio_value(p) — never negative",
         "ok": val >= 0, "note": f"value={val}"},
        {"law": "conservation across buy+sell — value unchanged from open",
         "ok": val == core.portfolio_value(pf0), "note": f"open={core.portfolio_value(pf0)}"},
    ])

    risk = core.risk_score(pf2)
    record("risk_score", "§PF.3.5", pf2, risk, [
        {"law": "0 ≤ risk_score(p) — never negative",
         "ok": risk >= 0, "note": f"risk={risk}"},
        {"law": "risk_score(p) ≤ portfolio_value(p) — exposure bounded by value",
         "ok": risk <= val, "note": f"risk={risk} ≤ value={val}"},
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
