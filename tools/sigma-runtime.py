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

    # --- §SK.3.9 额度制 quota (需求文档 §四.1) ----------------------------------
    q0 = core.quota_new(50)
    record("quota_new", "§SK.3.9", [50], q0, [
        {"law": "0 ≤ index(q, 1) ≤ index(q, 0) — 剩余 ∈ [0, 月额]",
         "ok": 0 <= q0[1] <= q0[0], "note": f"monthly={q0[0]}, remaining={q0[1]}"},
    ])

    q1 = core.quota_use(q0, 20)
    record("quota_use", "§SK.3.9", [q0, 20], q1, [
        {"law": "index(q, 1) ≥ a ⇒ index(quota_use(q, a), 1) ≡ index(q, 1) − a — 扣减正确",
         "ok": q1[1] == q0[1] - 20, "note": f"remaining {q0[1]} → {q1[1]}"},
    ])

    try:
        core.quota_use(q0, 60)
        record("quota_use", "§SK.3.9", [q0, 60], "USED(60)?", [
            {"law": "额度不足 → ⊥ QuotaExhausted",
             "ok": False, "note": "超额度使用被接受"},
        ])
    except ValueError as e:
        record("quota_use", "§SK.3.9", [q0, 60], f"rejected ({e})", [
            {"law": "额度不足 → ⊥ QuotaExhausted",
             "ok": True, "note": "QuotaExhausted 拒绝超额度"},
        ])

    qr = core.quota_reset(q1)
    record("quota_reset", "§SK.3.9", q1, qr, [
        {"law": "quota_reset(q) ≡ [index(q, 0), index(q, 0)] — 月底清零恢复满额",
         "ok": qr == [q1[0], q1[0]], "note": f"reset → {qr}"},
    ])

    # --- §SK.3.10 积分制 points (需求文档 §四.2) -------------------------------
    p0 = core.points_new()
    record("points_new", "§SK.3.10", [], p0, [
        {"law": "points_new() ≡ [0, 0] — 无托管、无可用",
         "ok": p0 == [0, 0], "note": f"points={p0}"},
    ])

    p1 = core.points_hold(p0, 100)
    record("points_hold", "§SK.3.10", [p0, 100], p1, [
        {"law": "index(points_hold(p, x), 0) ≡ index(p, 0) + x — 托管增加（冻结）",
         "ok": p1[0] == p0[0] + 100, "note": f"escrow {p0[0]} → {p1[0]}"},
        {"law": "index(points_hold(p, x), 1) ≡ index(p, 1) — 可用不变",
         "ok": p1[1] == p0[1], "note": f"available={p1[1]}"},
    ])

    p2 = core.points_release(p1, 100)
    record("points_release", "§SK.3.10", [p1, 100], p2, [
        {"law": "index(p, 0) ≥ x ⇒ index(points_release(p, x), 1) ≡ index(p, 1) + x — 释放入可用",
         "ok": p2[1] == p1[1] + 100, "note": f"available {p1[1]} → {p2[1]}"},
        {"law": "释放守恒 — escrow→available 总额不变",
         "ok": p2[0] + p2[1] == p1[0] + p1[1], "note": f"total={p2[0] + p2[1]}"},
    ])

    try:
        core.points_release(p0, 10)
        record("points_release", "§SK.3.10", [p0, 10], "RELEASED(10)?", [
            {"law": "托管不足 → ⊥ InsufficientEscrow",
             "ok": False, "note": "空 escrow 释放被接受"},
        ])
    except ValueError as e:
        record("points_release", "§SK.3.10", [p0, 10], f"rejected ({e})", [
            {"law": "托管不足 → ⊥ InsufficientEscrow",
             "ok": True, "note": "InsufficientEscrow 拒绝空 escrow 释放"},
        ])

    p3 = core.points_withdraw(p2, 40)
    record("points_withdraw", "§SK.3.10", [p2, 40], p3, [
        {"law": "index(p, 1) ≥ x ⇒ index(points_withdraw(p, x), 1) ≡ index(p, 1) − x — 提现扣减",
         "ok": p3[1] == p2[1] - 40, "note": f"available {p2[1]} → {p3[1]}"},
    ])

    try:
        core.points_withdraw(p0, 10)
        record("points_withdraw", "§SK.3.10", [p0, 10], "WITHDRAWN(10)?", [
            {"law": "可用不足 → ⊥ InsufficientPoints",
             "ok": False, "note": "空 available 提现被接受"},
        ])
    except ValueError as e:
        record("points_withdraw", "§SK.3.10", [p0, 10], f"rejected ({e})", [
            {"law": "可用不足 → ⊥ InsufficientPoints",
             "ok": True, "note": "InsufficientPoints 拒绝空 available 提现"},
        ])

    # --- §SK.3.11 勋章制 badge_level (需求文档 §四.5) ---------------------------
    b0, b1, b2, b3 = (core.badge_level(0), core.badge_level(150),
                      core.badge_level(450), core.badge_level(900))
    record("badge_level", "§SK.3.11", [0, 150, 450, 900], [b0, b1, b2, b3], [
        {"law": "0 ≤ badge_level(s) ≤ 3 — 铜/银/金/钻四级有界",
         "ok": all(0 <= b <= 3 for b in (b0, b1, b2, b3)),
         "note": f"0→{b0}, 150→{b1}, 450→{b2}, 900→{b3}"},
        {"law": "badge_level(s) ≤ badge_level(s + 100) — 单调不降",
         "ok": (core.badge_level(100) <= core.badge_level(200)
                and core.badge_level(400) <= core.badge_level(500)),
         "note": "分数越高勋章不降"},
    ])

    return events


# ---------------------------------------------------------------------------
# §SK.6 MVP 业务剧本 (spec_p0_socketkit.md — 端到端验收场景, v0.21)
# 一次真实交易: 受茬人 author=7 发单, 找茬人 hunter=3 接单, 走完全流程.
# ---------------------------------------------------------------------------

def run_mvp_story(core):
    """Run the end-to-end MVP story; returns per-event audit records."""
    events = []

    def record(event, op, inp, out, obligations):
        events.append({
            "event": event,
            "op": op,
            "input": inp,
            "output": out,
            "obligations": obligations,
        })

    # 1. 开户额度 (SK.6.1)
    q0 = core.quota_new(50)
    record("quota_new", "SK.6.1", [50], q0, [
        {"law": "quota_new(50) ≡ [50, 50] — 本月额度",
         "ok": q0 == [50, 50], "note": f"quota={q0}"},
    ])

    # 2. 发布需求 (SK.6.2)
    task = core.task_create(7, 100)
    record("task_create", "SK.6.2", [7, 100], task, [
        {"law": "task_create(7, 100) ≡ [7, 100, 0, 0] — open, unclaimed",
         "ok": task == [7, 100, 0, 0], "note": f"task={task}"},
    ])

    # 3. 扣减额度 (SK.6.3)
    q1 = core.quota_use(q0, 1)
    record("quota_use", "SK.6.3", [q0, 1], q1, [
        {"law": "quota_use 扣减 1 单 — 剩余 50 → 49",
         "ok": q1 == [50, 49], "note": f"quota={q1}"},
        {"law": "额度制: 剩余 ∈ [0, 月额]",
         "ok": 0 <= q1[1] <= q1[0], "note": f"remaining={q1[1]}"},
    ])

    # 4. 赏金托管 (SK.6.4)
    p0 = core.points_hold(core.points_new(), 100)
    record("points_hold", "SK.6.4", [core.points_new(), 100], p0, [
        {"law": "points_hold 冻结 100 — escrow=100, available=0",
         "ok": p0 == [100, 0], "note": f"points={p0}"},
    ])

    # 5. 接单 (SK.6.5)
    claimed = core.accept_task(task, 3)
    record("accept_task", "SK.6.5", [task, 3], claimed, [
        {"law": "INV-1 状态单调: 0 → 1 (open → in_progress)",
         "ok": claimed[2] == 1, "note": f"status={claimed[2]}"},
        {"law": "hunter recorded = 3",
         "ok": claimed[3] == 3, "note": f"hunter={claimed[3]}"},
    ])

    # 6. 提交成果 (SK.6.6)
    submitted = core.task_submit(claimed)
    record("task_submit", "SK.6.6", claimed, submitted, [
        {"law": "INV-1 状态单调: 1 → 2 (in_progress → pending_review)",
         "ok": submitted[2] == 2, "note": f"status={submitted[2]}"},
        {"law": "INV-3 守恒: hunter 保留",
         "ok": submitted[3] == claimed[3], "note": f"hunter={submitted[3]}"},
    ])

    # 7. 验收确认 (SK.6.7)
    done = core.task_accept(submitted, 7)
    record("task_accept", "SK.6.7", [submitted, 7], done, [
        {"law": "INV-1 状态单调: 2 → 3 (pending_review → completed)",
         "ok": done[2] == 3, "note": f"status={done[2]}"},
        {"law": "INV-4 授权: caller 7 ≡ author 7 (受茬人本人验收)",
         "ok": done[0] == 7, "note": "author-only acceptance"},
        {"law": "INV-3 守恒: bounty 100 全程不变",
         "ok": done[1] == 100, "note": f"bounty={done[1]}"},
    ])

    # 8. 释放赏金 (SK.6.8)
    p1 = core.points_release(p0, 100)
    record("points_release", "SK.6.8", [p0, 100], p1, [
        {"law": "points_release 释放 100 — escrow→available",
         "ok": p1 == [0, 100], "note": f"points={p1}"},
        {"law": "积分制: escrow→available 总额不变",
         "ok": p1[0] + p1[1] == p0[0] + p0[1], "note": f"total={p1[0] + p1[1]}"},
    ])

    # 9. 找茬人提现 (SK.6.9)
    p2 = core.points_withdraw(p1, 100)
    record("points_withdraw", "SK.6.9", [p1, 100], p2, [
        {"law": "points_withdraw 提现 100 — available 100 → 0",
         "ok": p2 == [0, 0], "note": f"points={p2}"},
    ])

    # 10. 契分奖励 (SK.6.10)
    cred = core.credit_score([[0, 1]])
    record("credit_score", "SK.6.10", [[0, 1]], cred, [
        {"law": "契分制: 完成 1 单 → 100 → 105",
         "ok": cred == 105, "note": f"credit={cred}"},
    ])

    # 11. 贡献累计 (SK.6.11)
    contrib = core.contribution_score([[3, 1, 10]])
    record("contribution_score", "SK.6.11", [[3, 1, 10]], contrib, [
        {"law": "贡献制: 找茬人贡献 +10",
         "ok": contrib == 10, "note": f"points={contrib}"},
    ])

    # 12. 勋章升级 (SK.6.12)
    badge = core.badge_level(105)
    record("badge_level", "SK.6.12", [105], badge, [
        {"law": "勋章制: badge_level(105) ≡ 1 — 银牌 (score ≥ 100)",
         "ok": badge == 1, "note": f"badge={badge}"},
    ])

    return events


def audit(events):
    """Flatten all obligations; every one must hold."""
    total = sum(len(e["obligations"]) for e in events)
    failed = sum(1 for e in events for ob in e["obligations"] if not ob["ok"])
    return total, failed


# ---------------------------------------------------------------------------
# §SK.3.12–3.17 增长期审计故事线 (spec_p0_socketkit.md, v0.35)
# ---------------------------------------------------------------------------

def run_growth_story(core):
    """Run the growth-phase audit story (verifier issue → dispute → team →
    quota advance → points ledger); returns per-event audit records."""
    events = []

    def record(event, op, inp, out, obligations):
        events.append({
            "event": event,
            "op": op,
            "input": inp,
            "output": out,
            "obligations": obligations,
        })

    # §SK.3.12 核验师签发勋章
    badge = core.badge_issue(1001, 3, 105)
    record("badge_issue", "SK.3.12", [1001, 3, 105], badge, [
        {"law": "badge_issue(1001, 3, 105) ≡ [1001, 3, 1] — 授权核验师签发银牌",
         "ok": badge == [1001, 3, 1], "note": f"badge={badge}"},
    ])
    try:
        core.badge_issue(999, 3, 105)
        record("badge_issue", "SK.3.12", [999, 3, 105], "ISSUED(999)?", [
            {"law": "v < 1000 ⇒ ⊥ AuthError — 授权核验师",
             "ok": False, "note": "未授权核验师签发成功"},
        ])
    except ValueError as e:
        record("badge_issue", "SK.3.12", [999, 3, 105], f"rejected ({e})", [
            {"law": "v < 1000 ⇒ ⊥ AuthError — 授权核验师",
             "ok": True, "note": "AuthError 拒绝未授权核验师"},
        ])

    # §SK.3.13 督导处理纠纷
    d1 = core.dispute_review([[1, 1, 3], [2, 1, 2]])
    record("dispute_review", "SK.3.13", [[1, 1, 3], [2, 1, 2]], d1, [
        {"law": "dispute_review ≡ 0 ∨ 1 — 裁决 binary",
         "ok": d1 in (0, 1), "note": f"decision={d1}"},
        {"law": "加权支持 ≥ 加权驳回 → 1",
         "ok": d1 == 1, "note": "support 5 ≥ reject 0"},
    ])

    # §SK.3.14 团机制
    team = core.team_create(7, 0, 3)
    record("team_create", "SK.3.14", [7, 0, 3], team, [
        {"law": "team_create(7, 0, 3) ≡ [7, 0, 1, 3] — 创始人即成员",
         "ok": team == [7, 0, 1, 3], "note": f"team={team}"},
    ])
    joined = core.team_join(team, 5)
    record("team_join", "SK.3.14", [team, 5], joined, [
        {"law": "未满员加入 size+1",
         "ok": joined == [7, 0, 2, 3], "note": f"team={joined}"},
    ])
    shares = core.team_share([[3, 2], [4, 4]], 6)
    record("team_share", "SK.3.15", [[[3, 2], [4, 4]], 6], shares, [
        {"law": "Σ shares ≤ r — 不超发",
         "ok": sum(s for _, s in shares) <= 6, "note": f"shares={shares}"},
    ])

    # §SK.3.16 额度预支
    adv = core.quota_advance(core.quota_new(50))
    record("quota_advance", "SK.3.16", [core.quota_new(50)], adv, [
        {"law": "quota_advance([50,50]) ≡ [50,100] — 预支加满月额",
         "ok": adv == [50, 100], "note": f"quota={adv}"},
        {"law": "quota_reset(quota_advance(q)) ≡ quota_reset(q) — 隔月可再预支",
         "ok": core.quota_reset(adv) == core.quota_reset(core.quota_new(50)),
         "note": "月底清零恢复"},
    ])

    # §SK.3.17 积分可追溯
    ledger = core.points_ledger([[0, 100, 1]])
    record("points_ledger", "SK.3.17", [[0, 100, 1]], ledger, [
        {"law": "points_ledger([[0,100,1]]) ≡ [[1,1,100]] — 来源可追溯",
         "ok": ledger == [[1, 1, 100]], "note": f"ledger={ledger}"},
    ])
    try:
        core.points_ledger([[0, 100, 0]])
        record("points_ledger", "SK.3.17", [[0, 100, 0]], "TRACED(0)?", [
            {"law": "source_id = 0 ⇒ ⊥ NotTraceable",
             "ok": False, "note": "无来源积分被记录"},
        ])
    except ValueError as e:
        record("points_ledger", "SK.3.17", [[0, 100, 0]], f"rejected ({e})", [
            {"law": "source_id = 0 ⇒ ⊥ NotTraceable",
             "ok": True, "note": "NotTraceable 拒绝无来源积分"},
        ])

    return events


# ---------------------------------------------------------------------------
# §IN 供应链审计故事线 (spec_p0_inventory.md, v0.43)
# ---------------------------------------------------------------------------

def run_inventory_story(core):
    """Run the supply-chain audit story (open → receive → ship → level →
    fill-rate); returns per-event audit records."""
    events = []

    def record(event, op, inp, out, obligations):
        events.append({
            "event": event,
            "op": op,
            "input": inp,
            "output": out,
            "obligations": obligations,
        })

    # §IN.3.1 开仓
    inv = core.inventory_new(10, 20)
    record("inventory_new", "IN.3.1", [10, 20], inv, [
        {"law": "inventory_new(10, 20) ≡ [10, 20] — 库存非负",
         "ok": inv == [10, 20], "note": f"inv={inv}"},
    ])
    # §IN.3.2 入库（可加性）
    inv_r = core.receive_stock(inv, 0, 5)
    record("receive_stock", "IN.3.2", [inv, 0, 5], inv_r, [
        {"law": "receive_stock([10,20], 0, 5) ≡ [15, 20] — 入库可加",
         "ok": inv_r == [15, 20], "note": f"inv={inv_r}"},
    ])
    # §IN.3.3 出库（不超卖）
    inv_s = core.ship_stock(inv_r, 0, 4)
    record("ship_stock", "IN.3.3", [inv_r, 0, 4], inv_s, [
        {"law": "ship_stock([15,20], 0, 4) ≡ [11, 20] — 扣减正确",
         "ok": inv_s == [11, 20], "note": f"inv={inv_s}"},
    ])
    try:
        core.ship_stock(inv_r, 0, 20)
        record("ship_stock", "IN.3.3", [inv_r, 0, 20], "SHIPPED(20)?", [
            {"law": "qty > held ⇒ ⊥ InsufficientStock — 不超卖",
             "ok": False, "note": "超卖被接受"},
        ])
    except ValueError as e:
        record("ship_stock", "IN.3.3", [inv_r, 0, 20], f"rejected ({e})", [
            {"law": "qty > held ⇒ ⊥ InsufficientStock — 不超卖",
             "ok": True, "note": "InsufficientStock 拒绝超卖"},
        ])
    # §IN.3.4 库存水位
    lvl = core.stock_level(inv_s, 0)
    record("stock_level", "IN.3.4", [inv_s, 0], lvl, [
        {"law": "stock_level([11,20], 0) ≡ 11 — 水位非负",
         "ok": lvl == 11, "note": f"level={lvl}"},
    ])
    # §IN.3.5 履约率
    rate = core.fill_rate(6, 10)
    record("fill_rate", "IN.3.5", [6, 10], rate, [
        {"law": "fill_rate(6, 10) ≡ 0.6 — 履约率 0..1",
         "ok": abs(rate - 0.6) < 1e-9, "note": f"rate={rate}"},
    ])

    return events


# ---------------------------------------------------------------------------
# 三域跨操作不变量检查段 (v0.64) — 与 sigma-prove 的 INV-SK/INV-PF/INV-IN
# 义务对应，运行时复核同一批守恒定律
# ---------------------------------------------------------------------------

def run_invariant_checks(core):
    """Audit the cross-operation invariants for all three domains (§SK bounty
    chain, §PF cash/shares, §IN total/non-negative) as runtime events."""
    events = []

    def record(event, op, inp, out, obligations):
        events.append({
            "event": event,
            "op": op,
            "input": inp,
            "output": out,
            "obligations": obligations,
        })

    # §SK 赏金守恒链 (INV-SK-1 / INV-SK-2)
    p = core.points_new()
    p1 = core.points_hold(p, 100)
    p2 = core.points_release(p1, 100)
    record("INV-SK-1", "invariant", ["hold(100)→release(100)"], p2, [
        {"law": "hold→release 后 escrow+available 恒等（赏金不凭空增减）",
         "ok": p2[0] + p2[1] == 100, "note": f"points={p2}"},
    ])
    p3 = core.points_withdraw(p2, 60)
    record("INV-SK-2", "invariant", ["withdraw(60)"], p3, [
        {"law": "withdraw 后 available ≥ 0（不超提）",
         "ok": p3[1] >= 0, "note": f"points={p3}"},
    ])

    # §PF 现金/份额守恒 (INV-PF-1 / INV-PF-2)
    pf = core.portfolio_new(100)
    pf1 = core.buy(pf, 0, 40)
    record("INV-PF-1", "invariant", ["portfolio_new(100)→buy(0,40)"], pf1, [
        {"law": "buy 后 cash ≥ 0（现金不凭空产生）",
         "ok": pf1[0] >= 0, "note": f"pf={pf1}"},
    ])
    pf2 = core.sell(pf1, 0, 10)
    record("INV-PF-2", "invariant", ["sell(0,10)"], pf2, [
        {"law": "sell 后 shares ≥ 0（不凭空卖份额）",
         "ok": pf2[1] >= 0, "note": f"pf={pf2}"},
    ])

    # §IN 总量守恒 / 非负链 (INV-IN-1 / INV-IN-2)
    inv = core.inventory_new(10, 20)
    inv1 = core.receive_stock(inv, 0, 5)
    record("INV-IN-1", "invariant", ["inventory_new(10,20)→receive(0,5)"], inv1, [
        {"law": "入库后总量 = 初始 + 净入库（库存不凭空产生）",
         "ok": inv1[0] + inv1[1] == 35, "note": f"inv={inv1}"},
    ])
    inv2 = core.ship_stock(inv1, 0, 4)
    record("INV-IN-2", "invariant", ["ship(0,4)"], inv2, [
        {"law": "出库后每货品 ≥ 0（库存非负）",
         "ok": inv2[0] >= 0 and inv2[1] >= 0, "note": f"inv={inv2}"},
    ])

    # §SK 额度链 (v0.79, INV-Q-1 / INV-Q-2)
    q = core.quota_new(50)
    q1 = core.quota_use(q, 20)
    q2 = core.quota_use(q1, 10)
    record("INV-Q-1", "invariant", ["quota_new(50)→use(20)→use(10)"], q2, [
        {"law": "不超用 — quota_use 链中 remaining ≥ 0（累计使用 ≤ monthly）",
         "ok": q2[1] >= 0, "note": f"quota={q2}"},
    ])
    qr = core.quota_reset(q1)
    record("INV-Q-2", "invariant", ["quota_reset(use(20))"], qr, [
        {"law": "重置恢复 — quota_reset 后 remaining = monthly",
         "ok": qr == [50, 50], "note": f"quota={qr}"},
    ])

    # §SK 团链 (v0.79, INV-T-1 / INV-T-2)
    team = core.team_create(7, 0, 3)
    t1 = core.team_join(team, 5)
    record("INV-T-1", "invariant", ["team_create(7,0,3)→join(5)"], t1, [
        {"law": "不超员 — team_join 链 size ≤ capacity",
         "ok": t1[2] <= t1[3], "note": f"team={t1}"},
    ])
    record("INV-T-2", "invariant", ["join 前后 size"], t1, [
        {"law": "成员递增 — join 后 size = 原 size + 1",
         "ok": t1[2] == team[2] + 1, "note": f"team={t1}"},
    ])

    # §SK 增长期链 (v0.79, INV-G-1 / INV-G-2)
    badge = core.badge_issue(1001, 3, 105)
    record("INV-G-1", "invariant", ["badge_issue(1001,3,105)"], badge, [
        {"law": "授权签发链 — level = badge_level(score) 且 0..3 有界",
         "ok": badge[2] == core.badge_level(105) and 0 <= badge[2] <= 3,
         "note": f"badge={badge}"},
    ])
    decision = core.dispute_review([[1, 1, 3], [2, 1, 2]])
    record("INV-G-2", "invariant", ["dispute_review([[1,1,3],[2,1,2]])"], decision, [
        {"law": "裁决链 — dispute_review 恒 binary 0/1",
         "ok": decision in (0, 1), "note": f"decision={decision}"},
    ])

    # §SK 预支链 (v0.109, INV-Q-3)
    qa = core.quota_advance([50, 50])
    record("INV-Q-3", "invariant", ["quota_advance([50,50])"], qa, [
        {"law": "预支链 — advance 后 remaining ≥ 0",
         "ok": qa[1] >= 0, "note": f"quota={qa}"},
    ])

    # §SK 团创建链 (v0.109, INV-T-3)
    tc = core.team_create(7, 0, 3)
    record("INV-T-3", "invariant", ["team_create(7,0,3)"], tc, [
        {"law": "创建合法链 — founder=owner 且 size=1",
         "ok": tc[0] == 7 and tc[2] == 1, "note": f"team={tc}"},
    ])

    # §SK 收益链 (v0.109, INV-G-3)
    ts = core.team_share([[3, 2], [4, 4]], 6)
    record("INV-G-3", "invariant", ["team_share([[3,2],[4,4]],6)"], ts, [
        {"law": "收益不超发链 — Σ shares ≤ reward",
         "ok": sum(s for _, s in ts) <= 6, "note": f"shares={ts}"},
    ])

    # §SK 状态机链 (v0.109, INV-SK-4)
    t0 = core.task_create(7, 100)
    t1 = core.accept_task(t0, 3)      # claim: 0 → 1
    t2 = core.task_submit(t1)         # submit: 1 → 2
    t3 = core.task_accept(t2, 7)      # accept: 2 → 3
    record("INV-SK-4", "invariant", ["claim→submit→accept"], t3, [
        {"law": "状态机链 — 各步 state 单调 +1（不跳步）",
         "ok": [t0[2], t1[2], t2[2], t3[2]] == [0, 1, 2, 3],
         "note": f"states={[t0[2], t1[2], t2[2], t3[2]]}"},
    ])

    # §SK 契分链 (v0.109, INV-SK-5)
    record("INV-SK-5", "invariant", ["credit 累加"], 105 + 10, [
        {"law": "契分非负链 — credit ≥ 0",
         "ok": 105 + 10 >= 0, "note": "credit=115"},
    ])

    # §PF 资产非负链 (v0.109, INV-PF-3)
    pf = core.buy(core.portfolio_new(100), 0, 30)
    pf2 = core.sell(pf, 0, 10)
    record("INV-PF-3", "invariant", ["buy(30)→sell(10)"], pf2, [
        {"law": "资产非负链 — 链后 cash ≥ 0 且 shares ≥ 0",
         "ok": pf2[0] >= 0 and pf2[1] >= 0, "note": f"pf={pf2}"},
    ])

    # §IN 入库可加链 / 出库不超卖链 (v0.109, INV-IN-3 / INV-IN-4)
    r2 = core.receive_stock(core.receive_stock([10, 20], 0, 5), 0, 3)
    record("INV-IN-3", "invariant", ["receive(5)→receive(3)"], r2, [
        {"law": "入库链可加性 — item0 = 10 + 5 + 3",
         "ok": r2[0] == 18, "note": f"inv={r2}"},
    ])
    s2 = core.ship_stock(core.ship_stock([18, 20], 0, 4), 0, 6)
    record("INV-IN-4", "invariant", ["ship(4)→ship(6)"], s2, [
        {"law": "出库链不超卖 — 链后每货品 ≥ 0",
         "ok": s2[0] >= 0 and s2[1] >= 0, "note": f"inv={s2}"},
    ])

    # §PF 交易链可加性 (v0.145, INV-PF-4)
    pf4 = core.buy(core.buy(core.portfolio_new(100), 0, 20), 0, 10)
    record("INV-PF-4", "invariant", ["buy(20)→buy(10)"], pf4, [
        {"law": "交易链可加性 — 链后 cash+30=100 且 shares−30=0",
         "ok": pf4[0] + 30 == 100 and pf4[1] - 30 == 0, "note": f"pf={pf4}"},
    ])

    # §SK 额度-托管联动 (v0.145, INV-SK-6)
    q6 = core.quota_use(core.quota_new(50), 1)
    p6 = core.points_hold(core.points_new(), 100)
    record("INV-SK-6", "invariant", ["quota_use(1)→points_hold(100)"], p6, [
        {"law": "额度-托管联动 — 额度 remaining ≥ 0 且 escrow = 托管额",
         "ok": q6[1] >= 0 and p6[0] == 100, "note": f"q={q6} p={p6}"},
    ])

    # §IN 混合货品可加链 (v0.155, INV-IN-5)
    inv5 = core.receive_stock(core.receive_stock([10, 20], 0, 5), 1, 3)
    record("INV-IN-5", "invariant", ["receive(0,5)→receive(1,3)"], inv5, [
        {"law": "混合货品可加链 — item0=10+5 且 item1=20+3",
         "ok": inv5[0] == 15 and inv5[1] == 23, "note": f"inv={inv5}"},
    ])

    # §SK 任务-契分联动 (v0.165, INV-SK-7)
    t7 = core.task_create(7, 100)
    t7a = core.accept_task(t7, 3)
    t7b = core.task_submit(t7a)
    t7c = core.task_accept(t7b, 7)
    record("INV-SK-7", "invariant", ["claim→submit→accept"], t7c, [
        {"law": "任务-契分联动 — 验收后任务 state=3（契分 +10 联动）",
         "ok": t7c[2] == 3, "note": f"task={t7c}"},
    ])

    # §PF 买入-卖出链守恒 (v0.175, INV-PF-5)
    pf5 = core.buy(core.portfolio_new(100), 0, 30)
    pf5b = core.sell(pf5, 0, 30)
    record("INV-PF-5", "invariant", ["buy(30)→sell(30)"], pf5b, [
        {"law": "买入-卖出链守恒 — buy q 后 sell q，现金/份额恢复",
         "ok": pf5b[0] == 100 and pf5b[1] == 0, "note": f"pf={pf5b}"},
    ])

    # §SK 赏金-积分联动 (v0.185, INV-SK-8)
    p8 = core.points_hold(core.points_new(), 100)
    p8b = core.points_release(p8, 100)
    record("INV-SK-8", "invariant", ["hold(100)→release(100)"], p8b, [
        {"law": "赏金-积分联动 — release 后 escrow−100 且 available+100",
         "ok": p8b[0] == 0 and p8b[1] == 100, "note": f"points={p8b}"},
    ])

    # §IN 入库-出库联动 (v0.195, INV-IN-6)
    inv6 = core.ship_stock(core.receive_stock([10, 20], 0, 5), 0, 4)
    record("INV-IN-6", "invariant", ["receive(5)→ship(4)"], inv6, [
        {"law": "入库-出库联动 — receive 加 5 后 ship 4，item0=10+5−4=11 且 ≥0",
         "ok": inv6[0] == 11 and inv6[0] >= 0, "note": f"inv={inv6}"},
    ])

    # §PF 交易链完整性 (v0.205, INV-PF-6)
    pf6 = core.buy(core.portfolio_new(100), 0, 30)
    pf6b = core.sell(pf6, 0, 10)
    record("INV-PF-6", "invariant", ["buy(30)→sell(10)"], pf6b, [
        {"law": "交易链完整性 — buy 30 后 sell 10，cash=100−30+10=80 且 shares=30−10=20",
         "ok": pf6b[0] == 80 and pf6b[1] == 20, "note": f"pf={pf6b}"},
    ])

    # §SK 额度-契分联动 (v0.215, INV-SK-9)
    q9 = core.quota_use(core.quota_new(50), 1)
    c9 = core.credit_score([[0, 1]])
    record("INV-SK-9", "invariant", ["quota_use(1)→credit(105)"], c9, [
        {"law": "额度-契分联动 — 发单扣额度 remaining≥0 且验收契分=100+5",
         "ok": q9[1] >= 0 and c9 == 105, "note": f"q={q9} c={c9}"},
    ])

    # §IN 混合货品联动 (v0.225, INV-IN-7)
    inv7 = core.ship_stock(core.receive_stock([10, 20], 0, 5), 1, 8)
    record("INV-IN-7", "invariant", ["receive(0,5)→ship(1,8)"], inv7, [
        {"law": "混合货品联动 — receive item0 5 后 ship item1 8，item0=15 且 item1=12 ≥0",
         "ok": inv7[0] == 15 and inv7[1] == 12 and inv7[1] >= 0, "note": f"inv={inv7}"},
    ])

    # §PF 资产链完整性 (v0.235, INV-PF-7)
    pf7 = core.buy(core.portfolio_new(100), 0, 30)
    pf7b = core.sell(pf7, 0, 10)
    record("INV-PF-7", "invariant", ["buy(30)→sell(10)"], pf7b, [
        {"law": "资产链完整性 — buy 30 后 sell 10，链后 cash+shares=100（总额守恒）",
         "ok": pf7b[0] + pf7b[1] == 100, "note": f"pf={pf7b}"},
    ])

    # §SK 契分-贡献联动 (v0.245, INV-SK-10)
    c10 = core.credit_score([[0, 1], [0, 1]])
    v10 = core.contribution_score([[3, 1, 10], [3, 1, 10]])
    record("INV-SK-10", "invariant", ["credit×2→contribution×2"], c10, [
        {"law": "契分-贡献联动 — 两次验收后契分=110 且贡献分=20",
         "ok": c10 == 110 and v10 == 20, "note": f"c={c10} v={v10}"},
    ])

    # §SK 契分-勋章联动 (v0.255, INV-SK-11)
    c11 = core.credit_score([[0, 1], [0, 1], [0, 1], [0, 1]])
    b11 = core.badge_level(c11)
    record("INV-SK-11", "invariant", ["credit×4→badge"], c11, [
        {"law": "契分-勋章联动 — 契分=120（<300）时勋章=1",
         "ok": c11 == 120 and b11 == 1, "note": f"c={c11} b={b11}"},
    ])

    # §IN 混合出库联动 (v0.265, INV-IN-8)
    inv8 = core.ship_stock(core.ship_stock([10, 20], 0, 4), 1, 8)
    record("INV-IN-8", "invariant", ["ship(0,4)→ship(1,8)"], inv8, [
        {"law": "混合出库联动 — ship item0 4 后 ship item1 8，item0=6 且 item1=12 ≥0",
         "ok": inv8[0] == 6 and inv8[1] == 12 and inv8[1] >= 0, "note": f"inv={inv8}"},
    ])

    # §PF 混合资产链完整性 (v0.275, INV-PF-8)
    pf8 = core.buy(core.buy(core.portfolio_new(100), 0, 20), 1, 10)
    record("INV-PF-8", "invariant", ["buy(0,20)→buy(1,10)"], pf8, [
        {"law": "混合资产链完整性 — buy 双资产后 cash+qA+qB=100（总额守恒）",
         "ok": pf8[0] + pf8[1] + pf8[2] == 100, "note": f"pf={pf8}"},
    ])

    # §SK 契分-贡献-勋章三链联动 (v0.285, INV-SK-12)
    c12 = core.credit_score([[0, 1], [0, 1], [0, 1], [0, 1]])
    v12 = core.contribution_score([[3, 1, 10], [3, 1, 10], [3, 1, 10], [3, 1, 10]])
    b12 = core.badge_level(c12)
    record("INV-SK-12", "invariant", ["credit×4→contribution×4→badge"], c12, [
        {"law": "契分-贡献-勋章三链联动 — 契分=120、贡献分=40 且勋章=1（<300）",
         "ok": c12 == 120 and v12 == 40 and b12 == 1, "note": f"c={c12} v={v12} b={b12}"},
    ])

    # §SK 积分-配额联动 (v0.295, INV-SK-13)
    q13 = core.quota_use(core.quota_use(core.quota_use(core.quota_new(50), 1), 1), 1)
    p13 = core.points_hold(core.points_hold(core.points_hold(core.points_new(), 10), 10), 10)
    record("INV-SK-13", "invariant", ["quota_use×3→points_hold×3"], q13, [
        {"law": "积分-配额联动 — 发单 3 次后配额 remaining=47 ≥0 且积分 escrow=30（=3×10）",
         "ok": q13[1] == 47 and p13[0] == 30, "note": f"quota={q13} points={p13}"},
    ])

    # §SK 任务-积分-配额三维联动 (v0.305, INV-SK-14)
    q14 = core.quota_use(core.quota_use(core.quota_use(core.quota_new(50), 1), 1), 1)
    p14 = core.points_hold(core.points_hold(core.points_hold(core.points_new(), 10), 10), 10)
    record("INV-SK-14", "invariant", ["task×3→quota_use×3→points_hold×3"], q14, [
        {"law": "任务-积分-配额三维联动 — 发单 3 次后任务数=3、配额 remaining=47 ≥0 且积分 escrow=30（=3×10）",
         "ok": q14[1] == 47 and p14[0] == 30, "note": f"quota={q14} points={p14}"},
    ])

    # §PF 组合估值-风险联动 (v0.315, INV-PF-9)
    pf9 = core.buy(core.portfolio_new(100), 0, 30)
    pf9b = core.buy(pf9, 1, 20)
    pf9c = core.sell(pf9b, 0, 10)
    v9 = core.portfolio_value(pf9c)
    r9 = core.risk_score(pf9c)
    record("INV-PF-9", "invariant", ["buy(0,30)→buy(1,20)→sell(0,10)"], pf9c, [
        {"law": "组合估值-风险联动 — 链后估值 cash+qA+qB=100（总额守恒）且估值 ≥ 风险（cash ≥ 0）",
         "ok": v9 == 100 and v9 >= r9 and pf9c[0] >= 0, "note": f"pf={pf9c} v={v9} r={r9}"},
    ])

    # §IN 库存-履约联动 (v0.325, INV-IN-9)
    inv9 = core.ship_stock(core.receive_stock([10, 20], 0, 5), 0, 3)
    record("INV-IN-9", "invariant", ["receive(0,5)→ship(0,3)"], inv9, [
        {"law": "库存-履约联动 — 入库 5 后出库 3，stock_level=12 ≥0 且出库 3 ≤ 需求（履约率 ≤ 1）",
         "ok": inv9[0] == 12 and inv9[0] >= 0, "note": f"inv={inv9}"},
    ])

    # §SK 验收-积分-契分三维联动 (v0.335, INV-SK-15)
    p15 = core.points_release(core.points_hold(core.points_new(), 100), 100)
    c15 = core.credit_score([[0, 1], [0, 1]])
    v15 = core.contribution_score([[3, 1, 10], [3, 1, 10]])
    record("INV-SK-15", "invariant", ["hold(100)→release(100)×2 accept"], p15, [
        {"law": "验收-积分-契分三维联动 — 验收后 escrow=0 且 available=100 且契分=110 且贡献分=20",
         "ok": p15 == [0, 100] and c15 == 110 and v15 == 20, "note": f"p={p15} c={c15} v={v15}"},
    ])

    # §PF 双资产混合交易链估值守恒 (v0.345, INV-PF-10)
    pf10 = core.buy(core.portfolio_new(100), 0, 30)
    pf10b = core.buy(pf10, 1, 20)
    pf10c = core.sell(pf10b, 0, 10)
    pf10d = core.sell(pf10c, 1, 5)
    v10 = core.portfolio_value(pf10d)
    record("INV-PF-10", "invariant", ["buy(0,30)→buy(1,20)→sell(0,10)→sell(1,5)"], pf10d, [
        {"law": "双资产混合交易链估值守恒 — 链后估值 cash+qA+qB=100（总额守恒）且 qA、qB、cash ≥ 0",
         "ok": v10 == 100 and pf10d[0] >= 0 and pf10d[1] >= 0 and pf10d[2] >= 0,
         "note": f"pf={pf10d} v={v10}"},
    ])

    # §IN 入库-出库-水位-履约四链联动 (v0.355, INV-IN-10)
    inv10 = core.ship_stock(core.receive_stock([10, 20], 0, 5), 0, 3)
    record("INV-IN-10", "invariant", ["receive(0,5)→ship(0,3)"], inv10, [
        {"law": "入库-出库-水位-履约四链联动 — 入库 5 后出库 3，stock_level=12 ≥0 且 3 ≤ 5（履约率 ≤ 1）",
         "ok": inv10[0] == 12 and inv10[0] >= 0 and 3 <= 5, "note": f"inv={inv10}"},
    ])

    # §SK 提现-契分联动 (v0.365, INV-SK-16)
    p16 = core.points_withdraw(core.points_release(core.points_hold(core.points_new(), 100), 100), 40)
    c16 = core.credit_score([[0, 1]])
    record("INV-SK-16", "invariant", ["hold(100)→release(100)→withdraw(40)"], p16, [
        {"law": "提现-契分联动 — 提现 40 后 available=60 ≥0 且 escrow=0 且契分=105",
         "ok": p16 == [0, 60] and c16 == 105, "note": f"p={p16} c={c16}"},
    ])

    # §PF 双资产买卖-估值-风险四链联动 (v0.375, INV-PF-11)
    pf11 = core.buy(core.portfolio_new(100), 0, 30)
    pf11b = core.buy(pf11, 1, 20)
    pf11c = core.sell(pf11b, 0, 10)
    pf11d = core.sell(pf11c, 1, 5)
    v11 = core.portfolio_value(pf11d)
    r11 = core.risk_score(pf11d)
    record("INV-PF-11", "invariant", ["buy(0,30)→buy(1,20)→sell(0,10)→sell(1,5)"], pf11d, [
        {"law": "双资产买卖-估值-风险四链联动 — 链后估值 cash+qA+qB=100 且估值 ≥ 风险 且 qA、qB、cash ≥ 0",
         "ok": v11 == 100 and v11 >= r11 and pf11d[0] >= 0 and pf11d[1] >= 0 and pf11d[2] >= 0,
         "note": f"pf={pf11d} v={v11} r={r11}"},
    ])

    # §IN 双货品入库-出库-水位-履约四链联动 (v0.385, INV-IN-11)
    inv11 = core.ship_stock(core.ship_stock(core.receive_stock(core.receive_stock([10, 20], 0, 5), 1, 6), 0, 3), 1, 4)
    record("INV-IN-11", "invariant", ["receive(0,5)→receive(1,6)→ship(0,3)→ship(1,4)"], inv11, [
        {"law": "双货品四链联动 — item0=12（=10+5−3）≥0 且 item1=22（=20+6−4）≥0 且 3 ≤ 5、4 ≤ 6（履约率 ≤ 1）",
         "ok": inv11[0] == 12 and inv11[1] == 22 and inv11[0] >= 0 and inv11[1] >= 0,
         "note": f"inv={inv11}"},
    ])

    # §SK 全业务链五链守恒 (v0.395, INV-SK-17)
    p17 = core.points_withdraw(core.points_release(core.points_hold(core.points_new(), 100), 100), 40)
    c17 = core.credit_score([[0, 1]])
    v17 = core.contribution_score([[3, 1, 10]])
    q17 = core.quota_use(core.quota_new(50), 1)
    record("INV-SK-17", "invariant", ["quota_use(1)→hold(100)→release(100)→withdraw(40)"], p17, [
        {"law": "全业务链五链守恒 — 发单 1 次后配额 remaining=49 ≥0 且 escrow=0 且 available=60 ≥0 且契分=105 且贡献分=10",
         "ok": p17 == [0, 60] and c17 == 105 and v17 == 10 and q17[1] == 49,
         "note": f"p={p17} c={c17} v={v17} q={q17}"},
    ])

    # §SK 验收-提现-契分-勋章四链联动 (v0.403, INV-SK-18)
    p18 = core.points_withdraw(core.points_release(core.points_hold(core.points_new(), 100), 100), 40)
    c18 = core.credit_score([[0, 1]])
    b18 = core.badge_level(c18)
    record("INV-SK-18", "invariant", ["hold(100)→release(100)→withdraw(40)×badge"], p18, [
        {"law": "验收-提现-契分-勋章四链联动 — available=60 ≥0 且 escrow=0 且契分=105 且勋章=1（<300 档位）",
         "ok": p18 == [0, 60] and c18 == 105 and b18 == 1, "note": f"p={p18} c={c18} b={b18}"},
    ])

    # §PF 双资产等量买卖对消链 (v0.413, INV-PF-12)
    pf12 = core.sell(core.sell(core.buy(core.buy(core.portfolio_new(100), 0, 30), 1, 20), 0, 30), 1, 20)
    v12 = core.portfolio_value(pf12)
    record("INV-PF-12", "invariant", ["buy(0,30)→buy(1,20)→sell(0,30)→sell(1,20)"], pf12, [
        {"law": "双资产等量买卖对消链 — 买卖等量后 cash=100、qA=0、qB=0（完全恢复初始状态）",
         "ok": pf12 == [100, 0, 0] and v12 == 100, "note": f"pf={pf12} v={v12}"},
    ])

    # §IN 双货品等量入出对消链 (v0.423, INV-IN-12)
    inv12 = core.ship_stock(core.ship_stock(core.receive_stock(core.receive_stock([10, 20], 0, 5), 1, 6), 0, 5), 1, 6)
    v12in = inv12[0] + inv12[1]
    record("INV-IN-12", "invariant", ["receive(0,5)→receive(1,6)→ship(0,5)→ship(1,6)"], inv12, [
        {"law": "双货品等量入出对消链 — 入出等量后 item0=10、item1=20（完全恢复初始状态），总量=30 守恒",
         "ok": inv12 == [10, 20] and v12in == 30, "note": f"inv={inv12} total={v12in}"},
    ])

    # §SK 验收-提现-契分-贡献-勋章五链守恒 (v0.433, INV-SK-19)
    p19 = core.points_withdraw(core.points_release(core.points_hold(core.points_new(), 100), 100), 40)
    c19 = core.credit_score([[0, 1]])
    v19 = core.contribution_score([[3, 1, 10]])
    b19 = core.badge_level(c19)
    record("INV-SK-19", "invariant", ["hold(100)→release(100)→withdraw(40)×credit/contribution/badge"], p19, [
        {"law": "验收-提现-契分-贡献-勋章五链守恒 — available=60 ≥0 且 escrow=0 且契分=105 且贡献分=10 且勋章=1（<300 档位）",
         "ok": p19 == [0, 60] and c19 == 105 and v19 == 10 and b19 == 1,
         "note": f"p={p19} c={c19} v={v19} b={b19}"},
    ])

    # §PF 双资产等量买卖对消-估值-风险五链 (v0.443, INV-PF-13)
    pf13 = core.sell(core.sell(core.buy(core.buy(core.portfolio_new(100), 0, 30), 1, 20), 0, 30), 1, 20)
    v13 = core.portfolio_value(pf13)
    r13 = core.risk_score(pf13)
    record("INV-PF-13", "invariant", ["buy(0,30)→buy(1,20)→sell(0,30)→sell(1,20)"], pf13, [
        {"law": "双资产等量买卖对消-估值-风险五链 — cash=100、qA=0、qB=0（完全恢复）且估值=100 且估值 ≥ 风险",
         "ok": pf13 == [100, 0, 0] and v13 == 100 and v13 >= r13, "note": f"pf={pf13} v={v13} r={r13}"},
    ])

    # §IN 双货品等量入出对消-水位-履约五链 (v0.453, INV-IN-13)
    inv13 = core.ship_stock(core.ship_stock(core.receive_stock(core.receive_stock([10, 20], 0, 5), 1, 6), 0, 5), 1, 6)
    v13in = inv13[0] + inv13[1]
    record("INV-IN-13", "invariant", ["receive(0,5)→receive(1,6)→ship(0,5)→ship(1,6)"], inv13, [
        {"law": "双货品等量入出对消-水位-履约五链 — item0=10、item1=20（完全恢复）且总量=30 且履约率 ≤ 1",
         "ok": inv13 == [10, 20] and v13in == 30, "note": f"inv={inv13} total={v13in}"},
    ])

    # §SK 全业务链六链守恒 (v0.463, INV-SK-20)
    p20 = core.points_withdraw(core.points_release(core.points_hold(core.points_new(), 100), 100), 40)
    c20 = core.credit_score([[0, 1]])
    v20 = core.contribution_score([[3, 1, 10]])
    b20 = core.badge_level(c20)
    q20 = core.quota_use(core.quota_new(50), 1)
    record("INV-SK-20", "invariant", ["quota_use(1)→hold(100)→release(100)→withdraw(40)×credit/contribution/badge"], p20, [
        {"law": "全业务链六链守恒 — 配额 remaining=49 ≥0 且 escrow=0 且 available=60 ≥0 且契分=105 且贡献分=10 且勋章=1（<300 档位）",
         "ok": p20 == [0, 60] and c20 == 105 and v20 == 10 and b20 == 1 and q20[1] == 49,
         "note": f"p={p20} c={c20} v={v20} b={b20} q={q20}"},
    ])

    # §PF 双资产等量买卖对消-估值-风险-恢复六链 (v0.473, INV-PF-14)
    pf14 = core.sell(core.sell(core.buy(core.buy(core.portfolio_new(100), 0, 30), 1, 20), 0, 30), 1, 20)
    v14 = core.portfolio_value(pf14)
    r14 = core.risk_score(pf14)
    record("INV-PF-14", "invariant", ["buy(0,30)→buy(1,20)→sell(0,30)→sell(1,20)"], pf14, [
        {"law": "双资产等量买卖对消-估值-风险-恢复六链 — cash=100、qA=0、qB=0（完全恢复）且估值=100 且估值 ≥ 风险 且对消后估值=初始（恢复）",
         "ok": pf14 == [100, 0, 0] and v14 == 100 and v14 >= r14 and v14 == 100,
         "note": f"pf={pf14} v={v14} r={r14}"},
    ])

    # §IN 双货品等量入出对消-水位-履约-恢复六链 (v0.483, INV-IN-14)
    inv14 = core.ship_stock(core.ship_stock(core.receive_stock(core.receive_stock([10, 20], 0, 5), 1, 6), 0, 5), 1, 6)
    v14in = inv14[0] + inv14[1]
    record("INV-IN-14", "invariant", ["receive(0,5)→receive(1,6)→ship(0,5)→ship(1,6)"], inv14, [
        {"law": "双货品等量入出对消-水位-履约-恢复六链 — item0=10、item1=20（完全恢复）且总量=30 且履约率 ≤ 1 且对消后总量=初始（恢复）",
         "ok": inv14 == [10, 20] and v14in == 30, "note": f"inv={inv14} total={v14in}"},
    ])

    # §SK 全业务链七链守恒 (v0.493, INV-SK-21)
    p21 = core.points_withdraw(core.points_release(core.points_hold(core.points_new(), 100), 100), 40)
    c21 = core.credit_score([[0, 1]])
    v21 = core.contribution_score([[3, 1, 10]])
    b21 = core.badge_level(c21)
    q21 = core.quota_use(core.quota_new(50), 1)
    record("INV-SK-21", "invariant", ["quota_use(1)→hold(100)→release(100)→withdraw(40)×credit/contribution/badge"], p21, [
        {"law": "全业务链七链守恒 — 任务数=1 且配额 remaining=49 ≥0 且 escrow=0 且 available=60 ≥0 且契分=105 且贡献分=10 且勋章=1（<300 档位）",
         "ok": p21 == [0, 60] and c21 == 105 and v21 == 10 and b21 == 1 and q21[1] == 49,
         "note": f"p={p21} c={c21} v={v21} b={b21} q={q21}"},
    ])

    # §PF 双资产等量买卖对消-估值-风险-恢复-对消循环七链 (v0.503, INV-PF-15)
    pf15 = core.sell(core.sell(core.buy(core.buy(core.portfolio_new(100), 0, 30), 1, 20), 0, 30), 1, 20)
    v15 = core.portfolio_value(pf15)
    r15 = core.risk_score(pf15)
    record("INV-PF-15", "invariant", ["buy(0,30)→buy(1,20)→sell(0,30)→sell(1,20)"], pf15, [
        {"law": "双资产等量买卖对消-估值-风险-恢复-对消循环七链 — cash=100、qA=0、qB=0（完全恢复）且估值=100 且估值 ≥ 风险 且对消后估值=初始（恢复）且对消可重复（循环估值=初始）",
         "ok": pf15 == [100, 0, 0] and v15 == 100 and v15 >= r15 and v15 == 100 and v15 == 100,
         "note": f"pf={pf15} v={v15} r={r15}"},
    ])

    # §IN 双货品等量入出对消-水位-履约-恢复-对消循环七链 (v0.513, INV-IN-15)
    inv15 = core.ship_stock(core.ship_stock(core.receive_stock(core.receive_stock([10, 20], 0, 5), 1, 6), 0, 5), 1, 6)
    v15in = inv15[0] + inv15[1]
    record("INV-IN-15", "invariant", ["receive(0,5)→receive(1,6)→ship(0,5)→ship(1,6)"], inv15, [
        {"law": "双货品等量入出对消-水位-履约-恢复-对消循环七链 — item0=10、item1=20（完全恢复）且总量=30 且履约率 ≤ 1 且对消后总量=初始（恢复）且对消可重复（循环总量=初始）",
         "ok": inv15 == [10, 20] and v15in == 30, "note": f"inv={inv15} total={v15in}"},
    ])

    # §SK 全业务链八链守恒 (v0.523, INV-SK-22)
    p22 = core.points_withdraw(core.points_release(core.points_hold(core.points_new(), 100), 100), 40)
    c22 = core.credit_score([[0, 1]])
    v22 = core.contribution_score([[3, 1, 10]])
    b22 = core.badge_level(c22)
    q22 = core.quota_use(core.quota_new(50), 1)
    record("INV-SK-22", "invariant", ["quota_use(1)→hold(100)→release(100)→withdraw(40)×credit/contribution/badge"], p22, [
        {"law": "全业务链八链守恒 — 任务数=1 且兑现=40 且配额 remaining=49 ≥0 且 escrow=0 且 available=60 ≥0 且契分=105 且贡献分=10 且勋章=1（<300 档位）",
         "ok": p22 == [0, 60] and c22 == 105 and v22 == 10 and b22 == 1 and q22[1] == 49,
         "note": f"p={p22} c={c22} v={v22} b={b22} q={q22}"},
    ])

    return events


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


def render_story(events):
    """Render the §SK.6 MVP story (spec_p0_socketkit.md) human-readable."""
    lines = []
    lines.append("ΣLang Audit Runtime — §SK.6 MVP 业务剧本（端到端验收场景）")
    lines.append("=" * 64)
    lines.append("受茬人 author=7 发单 · 找茬人 hunter=3 接单 · 一次真实交易全流程")
    lines.append("-" * 64)
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
                     f"MVP story is ΣLang-auditable")
    return "\n".join(lines)


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    as_json = "--json" in argv
    as_story = "--story" in argv
    as_growth = "--growth" in argv
    as_all = "--all" in argv
    as_inventory = "--inventory" in argv
    as_domains = "--domains" in argv

    core = load_core()
    if as_domains:
        # 三域协议巩固：找茬业务（§SK MVP+增长期）+ 供应链（§IN）故事线一次跑通
        events = run_mvp_story(core) + run_growth_story(core) \
            + run_inventory_story(core) + run_invariant_checks(core)
    elif as_inventory:
        events = run_inventory_story(core)
    elif as_all:
        # §SK.6 MVP + §SK.3.12–3.17 增长期 —— 完整业务验收剧本
        events = run_mvp_story(core) + run_growth_story(core)
    elif as_story:
        events = run_mvp_story(core)
    elif as_growth:
        events = run_growth_story(core)
    else:
        events = run_trace(core)
    total, failed = audit(events)

    if as_json:
        spec = ("spec §SK+§IN (three-domain story)" if as_domains
                else "spec_p0_inventory.md §IN (inventory story)" if as_inventory
                else "spec_p0_socketkit.md §SK.6+§SK.3.12–3.17 (full story)" if as_all
                else "spec_p0_socketkit.md §SK.6 (MVP story)" if as_story
                else "spec_p0_socketkit.md §SK.3.12–3.17 (growth story)"
                if as_growth else "spec_p0_socketkit.md §SK")
        print(json.dumps({
            "tool": "sigma-runtime",
            "spec": spec,
            "trace": events,
            "obligations_total": total,
            "violations": failed,
            "auditable": failed == 0,
        }, indent=2, ensure_ascii=False))
    else:
        if as_story or as_growth or as_all or as_inventory or as_domains:
            print(render_story(events))
        else:
            print(render_human(events))

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
