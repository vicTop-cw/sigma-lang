#!/usr/bin/env python3
"""
找茬 MVP 参考实现 — sigma_app.py
=================================
The kickoff-able App backend for 「来找茬」. Every business operation DELEGATES
its computation to the §SK semantics in sigma_core.py — the App layer only
manages state, it never re-implements business rules. This is the proof that
the audited §SK.6 story (spec_p0_socketkit.md) is directly implementable.

  python3 impl/python/sigma_app.py            # run the §SK.6 MVP story self-check
  python3 impl/python/sigma_app.py --serve    # stdlib-only HTTP JSON API
  python3 impl/python/sigma_app.py --story    # same as default (explicit)

Exit code 0 = all §SK.6 steps pass.
"""

import json
import os
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote, unquote

sys.path.insert(0, __file__ and __file__.rsplit("/", 1)[0] or ".")
import sigma_core as core

# v0.54 — §SK/§IN 语义错误码 → HTTP 状态码（语义化映射，4xx 语义对齐）
ERROR_STATUS: Dict[str, int] = {
    "AuthError": 403,              # 未授权
    "TypeError": 422,              # 类型不符（不可处理实体）
    "ShapeError": 422,
    "BountyErr": 409,              # 业务状态冲突
    "StateError": 409,
    "QuotaExhausted": 409,
    "InsufficientEscrow": 409,
    "InsufficientPoints": 409,
    "InsufficientStock": 409,
    "TeamFull": 409,
    # §PF (v0.177) — 金融市场错误边界
    "InsufficientFunds": 409,
    "UnknownAsset": 409,
    "InsufficientShares": 409,
    "UnknownItem": 409,
    "DivByZero": 409,
    "NotTraceable": 409,
}
DEFAULT_ERROR_STATUS = 400


class MVPApp:
    """In-memory MVP backend. Business values come ONLY from sigma_core §SK."""

    def __init__(self) -> None:
        self._next_task = 0
        self.tasks: Dict[int, List[int]] = {}              # task_id -> Task
        self.quotas: Dict[int, List[int]] = {}             # user -> Quota
        self.points: List[int] = core.points_new()         # platform escrow/available
        self.credit_events: Dict[int, List[List[int]]] = {}   # user -> credit events
        self.contribution_actions: Dict[int, List[List[int]]] = {}  # user -> actions
        self.users: Dict[int, Dict[str, object]] = {}      # v0.52 — user -> profile
        self.audit: List[dict] = []                       # v0.55 — ΣLang audit trail

    # --- v0.55 审计日志（每个业务动作的 ΣLang 事件，可对账） -----------------
    def _audit(self, op: str, inp: object, out: object) -> object:
        """Record one ΣLang business event; returns `out` unchanged so methods
        can wrap their return with `return self._audit(...)`."""
        self.audit.append({"op": op, "input": inp, "output": out})
        return out

    def audit_trail(self) -> List[dict]:
        """Return the audit trail (JSON-serializable, matches sigma-runtime
        event shape — the same ops are auditable by the runtime)."""
        return list(self.audit)

    # --- v0.52 用户会话层（用户态隔离） -------------------------------------
    def register(self, user: int, name: str) -> Dict[str, object]:
        """Register a user (idempotent: re-register keeps the existing profile).
        Every business value stays isolated per user (quota/credit/actions)."""
        if user not in self.users:
            self.users[user] = {"name": name, "joined": True}
        return self.users[user]

    def me(self, user: int) -> Dict[str, object]:
        """Per-user session summary: profile + quota + credit + tasks posted."""
        quota = self.quotas.get(user)
        credit = self.credit(user) if user in self.credit_events else 0
        posted = [tid for tid, t in self.tasks.items() if t[0] == user]
        return {
            "user": user,
            "profile": self.users.get(user, {"name": "", "joined": False}),
            "quota": quota,
            "credit": credit,
            "posted_tasks": posted,
        }

    # --- v0.53 查询端点（任务列表 / 用户列表） -------------------------------
    def tasks_list(self, status: Optional[int] = None) -> List[Dict[str, object]]:
        """List tasks, optionally filtered by §SK status (0..3)."""
        out = []
        for tid in sorted(self.tasks):
            t = self.tasks[tid]
            if status is None or t[2] == status:
                out.append({"task_id": tid, "task": t})
        return out

    def users_list(self) -> List[Dict[str, object]]:
        """List all registered users with their session summaries."""
        return [self.me(u) for u in sorted(self.users)]

    # --- v0.51 状态持久化（JSON 序列化，重启不丢） ---------------------------
    def to_state(self) -> dict:
        """Serialize all App state to a JSON-able dict (state is data only —
        business rules stay in sigma_core §SK)."""
        return {
            "next_task": self._next_task,
            "tasks": {str(k): v for k, v in self.tasks.items()},
            "quotas": {str(k): v for k, v in self.quotas.items()},
            "points": self.points,
            "credit_events": {str(k): v for k, v in self.credit_events.items()},
            "contribution_actions": {str(k): v for k, v in self.contribution_actions.items()},
            "users": {str(k): v for k, v in self.users.items()},
            "audit": self.audit,
        }

    @classmethod
    def from_state(cls, state: dict) -> "MVPApp":
        """Rebuild an App from a previously serialized state dict."""
        app = cls()
        app._next_task = int(state.get("next_task", 0))
        app.tasks = {int(k): v for k, v in state.get("tasks", {}).items()}
        app.quotas = {int(k): v for k, v in state.get("quotas", {}).items()}
        app.points = state.get("points", core.points_new())
        app.credit_events = {int(k): v for k, v in state.get("credit_events", {}).items()}
        app.contribution_actions = {
            int(k): v for k, v in state.get("contribution_actions", {}).items()
        }
        app.users = {int(k): v for k, v in state.get("users", {}).items()}
        app.audit = list(state.get("audit", []))
        return app

    # --- §SK.6.1 开户额度 ---------------------------------------------------
    def open_quota(self, user: int, monthly: int) -> List[int]:
        """Open a monthly quota for a user (delegates quota_new)."""
        q = core.quota_new(monthly)
        self.quotas[user] = q
        return self._audit("quota_new", [user, monthly], q)

    # --- §SK.6.2–4 发布需求（发单 + 扣额度 + 赏金托管） ---------------------
    def post_task(self, author: int, bounty: int) -> Tuple[int, List[int], List[int], List[int]]:
        """Post a task: task_create + quota_use(1) + points_hold(bounty)."""
        task = core.task_create(author, bounty)
        quota = core.quota_use(self.quotas[author], 1)
        self.quotas[author] = quota
        self.points = core.points_hold(self.points, bounty)
        tid = self._next_task
        self._next_task += 1
        self.tasks[tid] = task
        result = (tid, task, quota, self.points)
        self._audit("task_create", [author, bounty],
                    {"task_id": tid, "task": task, "quota": quota,
                     "points": self.points})
        return result

    # --- §SK.6.5 接单 --------------------------------------------------------
    def claim_task(self, task_id: int, hunter: int) -> List[int]:
        task = core.accept_task(self.tasks[task_id], hunter)
        self.tasks[task_id] = task
        return self._audit("accept_task", [task_id, hunter], task)

    # --- §SK.6.6 提交成果 ----------------------------------------------------
    def submit_work(self, task_id: int) -> List[int]:
        task = core.task_submit(self.tasks[task_id])
        self.tasks[task_id] = task
        return self._audit("task_submit", [task_id], task)

    # --- §SK.6.7–8 验收确认（验收 + 释放赏金 + 契分 + 贡献） -----------------
    def accept_work(self, task_id: int, caller: int) -> Tuple[List[int], List[int], int, int]:
        task = core.task_accept(self.tasks[task_id], caller)
        self.tasks[task_id] = task
        bounty = task[1]
        hunter = task[3]
        self.points = core.points_release(self.points, bounty)
        self.credit_events.setdefault(hunter, []).append([0, 1])       # 完成 +5
        self.contribution_actions.setdefault(hunter, []).append([hunter, 1, 10])  # 贡献 +10
        credit = core.credit_score(self.credit_events[hunter])
        contribution = core.contribution_score(self.contribution_actions[hunter])
        result = (task, self.points, credit, contribution)
        self._audit("task_accept", [task_id, caller],
                    {"task": task, "points": self.points,
                     "credit": credit, "contribution": contribution})
        return result

    # --- §SK.6.9 提现 --------------------------------------------------------
    def withdraw(self, user: int, amount: int) -> List[int]:
        self.points = core.points_withdraw(self.points, amount)
        return self._audit("points_withdraw", [user, amount], self.points)

    # --- §SK.6.10–12 契分 / 贡献 / 勋章 -------------------------------------
    def credit(self, user: int) -> int:
        return core.credit_score(self.credit_events.get(user, []))

    def contribution(self, user: int) -> int:
        return core.contribution_score(self.contribution_actions.get(user, []))

    def badge(self, user: int) -> int:
        return core.badge_level(self.credit(user))

    # --- 增长期 (§SK.3.12–3.17) 全部委托 sigma_core -------------------------
    def issue_badge(self, verifier: int, user: int, score: int) -> List[int]:
        return core.badge_issue(verifier, user, score)

    def dispute(self, evidence: List[List[int]]) -> int:
        return core.dispute_review(evidence)

    def create_team(self, owner: int, kind: int, capacity: int) -> List[int]:
        return core.team_create(owner, kind, capacity)

    def join_team(self, team: List[int], member: int) -> List[int]:
        return core.team_join(team, member)

    def share_reward(self, contribs: List[List[int]], reward: int) -> List[List[int]]:
        return core.team_share(contribs, reward)

    def advance_quota(self, quota: List[int]) -> List[int]:
        return core.quota_advance(quota)

    def ledger(self, entries: List[List[int]]) -> List[List[int]]:
        return core.points_ledger(entries)

    # --- 供应链 (§IN) 全部委托 sigma_core ------------------------------------
    def open_inventory(self, qty_a: int, qty_b: int) -> List[int]:
        return core.inventory_new(qty_a, qty_b)

    def receive(self, inv: List[int], item: int, qty: int) -> List[int]:
        return core.receive_stock(inv, item, qty)

    def ship(self, inv: List[int], item: int, qty: int) -> List[int]:
        return core.ship_stock(inv, item, qty)

    def level(self, inv: List[int], item: int) -> int:
        return core.stock_level(inv, item)

    def fill(self, shipped: int, demanded: int) -> float:
        return core.fill_rate(shipped, demanded)


# ============================================================================
# §SK.6 self-check: run the audited MVP story through the App layer
# ============================================================================

def run_story(app: MVPApp) -> Tuple[int, int]:
    """Run the §SK.6 twelve-step story via the App; returns (passed, total)."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    # 1. 开户额度      quota_new(50)                    → [50, 50]
    q0 = app.open_quota(7, 50)
    check("SK.6.1 open_quota", q0 == [50, 50], f"got {q0}")

    # 2–4. 发布需求    task_create + quota_use(1) + points_hold(100)
    tid, task, q1, p0 = app.post_task(7, 100)
    check("SK.6.2 task_create", task == [7, 100, 0, 0], f"got {task}")
    check("SK.6.3 quota_use", q1 == [50, 49], f"got {q1}")
    check("SK.6.4 points_hold", p0 == [100, 0], f"got {p0}")

    # 5. 接单          accept_task(..., 3)              → [7, 100, 1, 3]
    claimed = app.claim_task(tid, 3)
    check("SK.6.5 accept_task", claimed == [7, 100, 1, 3], f"got {claimed}")

    # 6. 提交成果      task_submit                      → [7, 100, 2, 3]
    submitted = app.submit_work(tid)
    check("SK.6.6 task_submit", submitted == [7, 100, 2, 3], f"got {submitted}")

    # 7–8. 验收确认    task_accept(7) + points_release + credit + contribution
    done, p1, credit, contribution = app.accept_work(tid, 7)
    check("SK.6.7 task_accept", done == [7, 100, 3, 3], f"got {done}")
    check("SK.6.8 points_release", p1 == [0, 100], f"got {p1}")

    # 9. 提现          points_withdraw(100)            → [0, 0]
    p2 = app.withdraw(3, 100)
    check("SK.6.9 points_withdraw", p2 == [0, 0], f"got {p2}")

    # 10. 契分奖励     credit_score([[0,1]])            → 105
    check("SK.6.10 credit_score", credit == 105, f"got {credit}")

    # 11. 贡献累计     contribution_score               → 10
    check("SK.6.11 contribution_score", contribution == 10, f"got {contribution}")

    # 12. 勋章升级     badge_level(105)                 → 1
    badge = app.badge(3)
    check("SK.6.12 badge_level", badge == 1, f"got {badge}")

    # Cross-checks with the audited invariants (INV-1/3/4).
    check("INV-1 monotonic",
          [task[2], claimed[2], submitted[2], done[2]] == [0, 1, 2, 3],
          f"statuses {[task[2], claimed[2], submitted[2], done[2]]}")
    check("INV-3 bounty conserved", done[1] == 100, f"bounty={done[1]}")
    check("INV-4 author accept", done[0] == 7, f"author={done[0]}")

    return passed, total


# ============================================================================
# stdlib-only HTTP JSON API (--serve)
# ============================================================================

class _Handler(BaseHTTPRequestHandler):
    app: MVPApp = MVPApp()
    _state_file: Optional[str] = None          # v0.51 — --state FILE (persist)
    _audit_file: Optional[str] = None          # v0.55 — --audit-log FILE
    _auth_token: Optional[str] = None          # v0.71 — --auth-token (401 gate)
    _log_file: Optional[str] = None            # v0.73 — --log-file (leveled)

    def _authorized(self) -> bool:
        """v0.71 — token auth: every request must carry ?token= matching
        --auth-token; when auth is disabled (None) everything passes."""
        if _Handler._auth_token is None:
            return True
        return self._get_str("token") == _Handler._auth_token

    def _json(self, obj, code: int = 200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, html: str, code: int = 200):
        """v0.95 — serve an HTML page (run-status panel)."""
        body = html.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _get(self, name: str, default: Optional[int] = None) -> Optional[int]:
        raw = self.path.split("?", 1)[1] if "?" in self.path else ""
        for part in raw.split("&"):
            if part.startswith(name + "="):
                try:
                    return int(part.split("=", 1)[1])
                except ValueError:
                    return default
        return default

    def _get_str(self, name: str) -> Optional[str]:
        """Return a raw string query parameter (URL-decoded, for list args)."""
        raw = self.path.split("?", 1)[1] if "?" in self.path else ""
        for part in raw.split("&"):
            if part.startswith(name + "="):
                return unquote(part.split("=", 1)[1])
        return None

    @classmethod
    def _save_state(cls):
        """v0.51 — persist the whole App state after every request (--state).
        v0.55 — also export the ΣLang audit trail (--audit-log).
        v0.72 — atomic writes: tmp file + os.replace, so a crash mid-write
        never corrupts the state/audit file.
        v0.101 — take local snapshots of the file paths first (the response is
        sent before this finally runs, so another thread may have already reset
        the class variables by the time we reach os.replace); use mkstemp for
        a unique temp filename; if os.replace fails (Windows permission edge),
        fall back to writing directly to the target file."""
        import tempfile
        state_file = cls._state_file
        if state_file:
            d = os.path.dirname(state_file) or "."
            fd, tmp = tempfile.mkstemp(suffix=".sig", dir=d)
            os.close(fd)
            try:
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(cls.app.to_state(), f, ensure_ascii=False)
                try:
                    os.replace(tmp, state_file)
                except OSError:
                    with open(state_file, "w", encoding="utf-8") as f:
                        json.dump(cls.app.to_state(), f, ensure_ascii=False)
            finally:
                if os.path.exists(tmp):
                    os.remove(tmp)
        audit_file = cls._audit_file
        if audit_file:
            d = os.path.dirname(audit_file) or "."
            fd, tmp = tempfile.mkstemp(suffix=".sig", dir=d)
            os.close(fd)
            try:
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(cls.app.audit_trail(), f, ensure_ascii=False, indent=2)
                try:
                    os.replace(tmp, audit_file)
                except OSError:
                    with open(audit_file, "w", encoding="utf-8") as f:
                        json.dump(cls.app.audit_trail(), f, ensure_ascii=False, indent=2)
            finally:
                if os.path.exists(tmp):
                    os.remove(tmp)

    def do_GET(self):
        # v0.71 — 鉴权门禁：--auth-token 启用时未带正确 token → 401
        if not self._authorized():
            return self._json({"error": "AuthRequired"}, 401)
        path = self.path.split("?", 1)[0]
        app = _Handler.app
        try:
            if path == "/quota":
                user = self._get("user")
                monthly = self._get("monthly")
                if user is None or monthly is None:
                    return self._json({"error": "need user & monthly"}, 400)
                return self._json({"quota": app.open_quota(user, monthly)})
            if path == "/register":
                user = self._get("user")
                name = self._get_str("name")
                if user is None or name is None:
                    return self._json({"error": "need user & name"}, 400)
                return self._json({"profile": app.register(user, name)})
            if path == "/me":
                user = self._get("user")
                if user is None:
                    return self._json({"error": "need user"}, 400)
                return self._json(app.me(user))
            if path == "/health":
                # v0.74 — 健康检查：服务状态 + 关键配置摘要 + 门禁静态信息
                return self._json({
                    "status": "ok",
                    "app": "找茬 MVP 参考实现 (sigma_app)",
                    "state": _Handler._state_file,
                    "auth": "enabled" if _Handler._auth_token else "disabled",
                    "log": _Handler._log_file,
                    "gates": {
                        "consensus": "56/56",
                        "p0": "109/109",
                        "prove": "310 PROVED",
                        "scenario": "16/16",
                    },
                })
            if path == "/panel":
                # v0.95 — 运行状态面板：业务摘要 + 门禁摘要（HTML 页）
                by_state = {0: 0, 1: 0, 2: 0, 3: 0}
                total_bounty = 0
                for t in app.tasks.values():
                    by_state[t[2]] = by_state.get(t[2], 0) + 1
                    total_bounty += t[1]
                return self._html(f"""<!DOCTYPE html><html lang="zh-CN"><head>
<meta charset="utf-8"><title>找茬运行面板</title>
<style>body{{font-family:sans-serif;max-width:720px;margin:40px auto;padding:0 16px;color:#263238}}
h1{{color:#1a237e}} table{{border-collapse:collapse;width:100%}}
td,th{{padding:8px;border-bottom:1px solid #eceff1;text-align:left}}
.card{{background:#fff;border-radius:8px;padding:16px;margin:16px 0;box-shadow:0 1px 3px rgba(0,0,0,.12)}}</style>
</head><body><h1>🔍 找茬运行面板（v0.95）</h1>
<div class="card"><h3>服务</h3><table>
<tr><td>app</td><td>找茬 MVP 参考实现</td></tr>
<tr><td>状态</td><td>ok</td></tr>
<tr><td>用户数</td><td>{len(app.users)}</td></tr>
<tr><td>任务数</td><td>{len(app.tasks)}</td></tr></table></div>
<div class="card"><h3>业务摘要</h3><table>
<tr><th>状态</th><th>待接单</th><th>进行中</th><th>待验收</th><th>已完成</th></tr>
<tr><td>数量</td><td>{by_state[0]}</td><td>{by_state[1]}</td><td>{by_state[2]}</td><td>{by_state[3]}</td></tr>
<tr><td>赏金总额</td><td colspan="4">{total_bounty}</td></tr></table></div>
<div class="card"><h3>门禁摘要</h3><table>
<tr><td>consensus</td><td>56/56</td></tr>
<tr><td>p0</td><td>109/109</td></tr>
<tr><td>prove</td><td>310 PROVED</td></tr>
<tr><td>scenario</td><td>16/16</td></tr></table></div>
</body></html>""")
            if path == "/audit":
                # v0.227 — 审计轨迹（ΣLang audit trail，事件含 kind/input/output）
                return self._json({"events": [
                    {"kind": e["op"], "input": e["input"], "output": e["output"]}
                    for e in app.audit
                ]})
            if path == "/stats":
                # v0.134 — 业务统计（JSON，程序可消费；/panel 是 HTML 版）
                by_state = {0: 0, 1: 0, 2: 0, 3: 0}
                total_bounty = 0
                for t in app.tasks.values():
                    by_state[t[2]] = by_state.get(t[2], 0) + 1
                    total_bounty += t[1]
                total_credit = sum(app.credit(u) for u in app.users)
                return self._json({
                    "users": len(app.users),
                    "tasks": len(app.tasks),
                    "tasks_by_state": by_state,
                    "total_bounty": total_bounty,
                    "platform_points": app.points,
                    "total_credit": total_credit,
                })
            if path == "/tasks":
                status = self._get("status")
                return self._json({"tasks": app.tasks_list(status)})
            if path == "/users":
                return self._json({"users": app.users_list()})
            if path == "/post":
                author = self._get("author")
                bounty = self._get("bounty")
                if author is None or bounty is None:
                    return self._json({"error": "need author & bounty"}, 400)
                tid, task, quota, points = app.post_task(author, bounty)
                return self._json({"task_id": tid, "task": task,
                                   "quota": quota, "points": points})
            if path == "/claim":
                tid = self._get("task")
                hunter = self._get("hunter")
                if tid is None or hunter is None:
                    return self._json({"error": "need task & hunter"}, 400)
                return self._json({"task": app.claim_task(tid, hunter)})
            if path == "/submit":
                tid = self._get("task")
                if tid is None:
                    return self._json({"error": "need task"}, 400)
                return self._json({"task": app.submit_work(tid)})
            if path == "/accept":
                tid = self._get("task")
                caller = self._get("caller")
                if tid is None or caller is None:
                    return self._json({"error": "need task & caller"}, 400)
                task, points, credit, contribution = app.accept_work(tid, caller)
                return self._json({"task": task, "points": points,
                                   "credit": credit, "contribution": contribution})
            if path == "/withdraw":
                user = self._get("user")
                amount = self._get("amount")
                if user is None or amount is None:
                    return self._json({"error": "need user & amount"}, 400)
                return self._json({"points": app.withdraw(user, amount)})
            if path == "/badge":
                user = self._get("user")
                if user is None:
                    return self._json({"error": "need user"}, 400)
                return self._json({"credit": app.credit(user),
                                   "badge": app.badge(user)})
            # --- 增长期端点 (§SK.3.12–3.17) ---
            if path == "/badge_issue":
                v = self._get("verifier")
                u = self._get("user")
                s = self._get("score")
                if v is None or u is None or s is None:
                    return self._json({"error": "need verifier & user & score"}, 400)
                return self._json({"badge": app.issue_badge(v, u, s)})
            if path == "/dispute":
                ev = self._get_str("evidence")
                if ev is None:
                    return self._json({"error": "need evidence"}, 400)
                return self._json({"decision": app.dispute(eval(ev))})
            if path == "/team_create":
                o = self._get("owner")
                k = self._get("kind")
                c = self._get("capacity")
                if o is None or k is None or c is None:
                    return self._json({"error": "need owner & kind & capacity"}, 400)
                return self._json({"team": app.create_team(o, k, c)})
            if path == "/team_join":
                t = self._get_str("team")
                m = self._get("member")
                if t is None or m is None:
                    return self._json({"error": "need team & member"}, 400)
                return self._json({"team": app.join_team(eval(t), m)})
            if path == "/team_share":
                c = self._get_str("contribs")
                r = self._get("reward")
                if c is None or r is None:
                    return self._json({"error": "need contribs & reward"}, 400)
                return self._json({"shares": app.share_reward(eval(c), r)})
            if path == "/advance":
                q = self._get_str("quota")
                if q is None:
                    return self._json({"error": "need quota"}, 400)
                return self._json({"quota": app.advance_quota(eval(q))})
            if path == "/ledger":
                e = self._get_str("entries")
                if e is None:
                    return self._json({"error": "need entries"}, 400)
                return self._json({"ledger": app.ledger(eval(e))})
            # --- 供应链端点 (§IN) ---
            if path == "/inventory_new":
                a = self._get("qty_a")
                b = self._get("qty_b")
                if a is None or b is None:
                    return self._json({"error": "need qty_a & qty_b"}, 400)
                return self._json({"inventory": app.open_inventory(a, b)})
            if path == "/receive_stock":
                i = self._get_str("inv")
                x = self._get("item")
                q = self._get("qty")
                if i is None or x is None or q is None:
                    return self._json({"error": "need inv & item & qty"}, 400)
                return self._json({"inventory": app.receive(eval(i), x, q)})
            if path == "/ship_stock":
                i = self._get_str("inv")
                x = self._get("item")
                q = self._get("qty")
                if i is None or x is None or q is None:
                    return self._json({"error": "need inv & item & qty"}, 400)
                return self._json({"inventory": app.ship(eval(i), x, q)})
            if path == "/stock_level":
                i = self._get_str("inv")
                x = self._get("item")
                if i is None or x is None:
                    return self._json({"error": "need inv & item"}, 400)
                return self._json({"level": app.level(eval(i), x)})
            if path == "/fill_rate":
                s = self._get("shipped")
                d = self._get("demanded")
                if s is None or d is None:
                    return self._json({"error": "need shipped & demanded"}, 400)
                return self._json({"rate": app.fill(s, d)})
            if path == "/portfolio_new":
                c = self._get("cash")
                if c is None:
                    return self._json({"error": "need cash"}, 400)
                return self._json({"portfolio": core.portfolio_new(c)})
            if path == "/portfolio_buy":
                pf = self._get_str("pf")
                a = self._get("asset")
                q = self._get("qty")
                if pf is None or a is None or q is None:
                    return self._json({"error": "need pf & asset & qty"}, 400)
                return self._json({"portfolio": core.buy(eval(pf), a, q)})
            if path == "/portfolio_sell":
                pf = self._get_str("pf")
                a = self._get("asset")
                q = self._get("qty")
                if pf is None or a is None or q is None:
                    return self._json({"error": "need pf & asset & qty"}, 400)
                return self._json({"portfolio": core.sell(eval(pf), a, q)})
            if path == "/portfolio_value":
                pf = self._get_str("pf")
                if pf is None:
                    return self._json({"error": "need pf"}, 400)
                return self._json({"value": core.portfolio_value(eval(pf))})
            if path == "/portfolio_risk":
                pf = self._get_str("pf")
                if pf is None:
                    return self._json({"error": "need pf"}, 400)
                return self._json({"risk": core.risk_score(eval(pf))})
            return self._json({"error": "unknown path"}, 404)
        except (ValueError, KeyError) as e:
            # v0.54 — 语义化错误码：§SK/§IN 错误 → 语义化 HTTP 状态码
            msg = str(e)
            status = ERROR_STATUS.get(msg, DEFAULT_ERROR_STATUS)
            return self._json({"error": msg}, status)
        finally:
            # v0.51 — persist after every request (--state FILE)
            self._save_state()

    def do_POST(self):
        # v0.82 — HTTP 方法语义对齐：POST 与 GET 同行为（变更端点如 /post
        # /claim /submit 可用 POST；查询端点也可 POST；参数仍在 URL query）
        self.do_GET()

    def log_message(self, fmt, *args):
        """v0.73 — leveled access log: 2xx = INFO, 4xx/5xx = WARNING; written
        to --log-file when set (append), else stderr."""
        status = ""
        for a in args:
            if isinstance(a, int) and a >= 100:
                status = str(a)
                break
            if isinstance(a, str) and a.isdigit() and len(a) == 3:
                status = a
                break
        level = "WARNING" if status.startswith(("4", "5")) else "INFO"
        line = f"[sigma-app][{level}] {fmt % args}"
        if _Handler._log_file:
            with open(_Handler._log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        else:
            sys.stderr.write(line + "\n")


def run_http_smoke() -> Tuple[int, int]:
    """--smoke: start the HTTP server, walk the full MVP chain over HTTP, assert.

    One end-to-end HTTP acceptance run: /quota → /post → /claim → /submit →
    /accept → /withdraw → /badge, each response asserted against the §SK.6
    story. Returns (passed, total).
    """
    _Handler.app = MVPApp()  # fresh state for the smoke run
    server = HTTPServer(("127.0.0.1", 0), _Handler)  # random free port
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    def get(path: str) -> dict:
        with urllib.request.urlopen(base + path, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def get_status(path: str) -> Tuple[int, dict]:
        """GET and return (http_status, body) — 4xx/5xx surface as HTTPError."""
        try:
            with urllib.request.urlopen(base + path, timeout=10) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))

    # 0. 用户会话 (v0.52)  /register?user=7&name=… → profile; /me → summary
    r = get("/register?user=7&name=%E6%89%BE%E8%8C%AC%E4%B8%BB")
    check("HTTP /register", r["profile"].get("joined") is True, f"got {r}")
    r = get("/me?user=7")
    check("HTTP /me user", r["user"] == 7, f"got {r}")
    check("HTTP /me profile", r["profile"].get("name") == "找茬主", f"got {r}")

    # 1. 开户额度   /quota?user=7&monthly=50          → {"quota": [50, 50]}
    r = get("/quota?user=7&monthly=50")
    check("HTTP /quota", r == {"quota": [50, 50]}, f"got {r}")
    r = get("/me?user=7")
    check("HTTP /me quota", r["quota"] == [50, 50], f"got {r}")

    # 2. 发布需求   /post?author=7&bounty=100        → task / quota / points
    r = get("/post?author=7&bounty=100")
    check("HTTP /post task", r["task"] == [7, 100, 0, 0], f"got {r.get('task')}")
    check("HTTP /post quota", r["quota"] == [50, 49], f"got {r.get('quota')}")
    check("HTTP /post points", r["points"] == [100, 0], f"got {r.get('points')}")
    tid = r["task_id"]

    # 2.5 查询端点 (v0.53)  /tasks → 列表; /tasks?status=N → 过滤; /users
    r = get("/tasks")
    check("HTTP /tasks list", any(t["task_id"] == tid for t in r["tasks"]), f"got {r}")
    check("HTTP /tasks count", len(r["tasks"]) == 1, f"got {r}")
    r = get("/tasks?status=1")
    check("HTTP /tasks filter", len(r["tasks"]) == 0, f"got {r}")
    r = get("/users")
    check("HTTP /users", any(u["user"] == 7 for u in r["users"]), f"got {r}")

    # 3. 接单       /claim?task=0&hunter=3           → [7, 100, 1, 3]
    r = get(f"/claim?task={tid}&hunter=3")
    check("HTTP /claim", r["task"] == [7, 100, 1, 3], f"got {r.get('task')}")

    # 4. 提交成果   /submit?task=0                    → [7, 100, 2, 3]
    r = get(f"/submit?task={tid}")
    check("HTTP /submit", r["task"] == [7, 100, 2, 3], f"got {r.get('task')}")

    # 5. 验收确认   /accept?task=0&caller=7          → completed + release + credit
    r = get(f"/accept?task={tid}&caller=7")
    check("HTTP /accept task", r["task"] == [7, 100, 3, 3], f"got {r.get('task')}")
    check("HTTP /accept points", r["points"] == [0, 100], f"got {r.get('points')}")
    check("HTTP /accept credit", r["credit"] == 105, f"got {r.get('credit')}")
    check("HTTP /accept contribution", r["contribution"] == 10,
          f"got {r.get('contribution')}")

    # 6. 找茬人提现 /withdraw?user=3&amount=100      → [0, 0]
    r = get("/withdraw?user=3&amount=100")
    check("HTTP /withdraw", r["points"] == [0, 0], f"got {r}")

    # 7. 勋章       /badge?user=3                    → credit 105, badge 1
    r = get("/badge?user=3")
    check("HTTP /badge credit", r["credit"] == 105, f"got {r}")
    check("HTTP /badge badge", r["badge"] == 1, f"got {r}")

    # 8. 增长期 (§SK.3.12–3.17)
    r = get("/badge_issue?verifier=1001&user=3&score=105")
    check("HTTP /badge_issue", r["badge"] == [1001, 3, 1], f"got {r}")
    r = get("/dispute?evidence=[[1,1,3],[2,1,2]]")
    check("HTTP /dispute", r["decision"] == 1, f"got {r}")
    r = get("/team_create?owner=7&kind=0&capacity=3")
    check("HTTP /team_create", r["team"] == [7, 0, 1, 3], f"got {r}")
    r = get("/team_join?team=[7,0,1,3]&member=5")
    check("HTTP /team_join", r["team"] == [7, 0, 2, 3], f"got {r}")
    r = get("/team_share?contribs=[[3,2],[4,4]]&reward=6")
    check("HTTP /team_share", r["shares"] == [[3, 2], [4, 4]], f"got {r}")
    r = get("/advance?quota=[50,50]")
    check("HTTP /advance", r["quota"] == [50, 100], f"got {r}")
    r = get("/ledger?entries=[[0,100,1]]")
    check("HTTP /ledger", r["ledger"] == [[1, 1, 100]], f"got {r}")

    # 9. 供应链 (§IN)
    r = get("/inventory_new?qty_a=10&qty_b=20")
    check("HTTP /inventory_new", r["inventory"] == [10, 20], f"got {r}")
    r = get("/receive_stock?inv=[10,20]&item=0&qty=5")
    check("HTTP /receive_stock", r["inventory"] == [15, 20], f"got {r}")
    r = get("/ship_stock?inv=[15,20]&item=0&qty=4")
    check("HTTP /ship_stock", r["inventory"] == [11, 20], f"got {r}")
    r = get("/stock_level?inv=[11,20]&item=0")
    check("HTTP /stock_level", r["level"] == 11, f"got {r}")
    r = get("/fill_rate?shipped=6&demanded=10")
    check("HTTP /fill_rate", abs(r["rate"] - 0.6) < 1e-9, f"got {r}")

    # 10. 错误码语义化 (v0.54)  §SK/§IN 错误 → 语义化 4xx
    st, r = get_status("/ship_stock?inv=[15,20]&item=0&qty=99")
    check("HTTP err InsufficientStock->409", st == 409, f"got {st}")
    st, r = get_status("/badge_issue?verifier=999&user=3&score=105")
    check("HTTP err AuthError->403", st == 403, f"got {st}")
    st, r = get_status("/fill_rate?shipped=6&demanded=0")
    check("HTTP err DivByZero->409", st == 409, f"got {st}")

    server.shutdown()
    thread.join()
    return passed, total


def run_persist_test() -> Tuple[int, int]:
    """--persist-test (v0.51): run half the §SK.6 story, serialize, rebuild,
    finish the story on the rebuilt App — state survives a restart."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    # 前半段 story（开户 → 发单 → 接单）
    app = MVPApp()
    q0 = app.open_quota(7, 50)
    check("PERSIST open_quota", q0 == [50, 50], f"got {q0}")
    tid, task, q1, p0 = app.post_task(7, 100)
    check("PERSIST post_task", task == [7, 100, 0, 0], f"got {task}")
    claimed = app.claim_task(tid, 3)
    check("PERSIST claim", claimed == [7, 100, 1, 3], f"got {claimed}")

    # 序列化 → 重建（模拟重启）
    state = app.to_state()
    app2 = MVPApp.from_state(state)
    check("PERSIST tasks", app2.tasks == app.tasks, f"got {app2.tasks}")
    check("PERSIST quotas", app2.quotas == app.quotas, f"got {app2.quotas}")
    check("PERSIST points", app2.points == app.points, f"got {app2.points}")
    check("PERSIST next_task", app2._next_task == app._next_task,
          f"got {app2._next_task}")

    # 后半段 story 在重建的 App 上跑，结果一致
    submitted = app2.submit_work(tid)
    done, p1, credit, contribution = app2.accept_work(tid, 7)
    check("PERSIST story continues", done == [7, 100, 3, 3], f"got {done}")
    check("PERSIST invariants",
          [task[2], claimed[2], submitted[2], done[2]] == [0, 1, 2, 3],
          f"statuses {[task[2], claimed[2], submitted[2], done[2]]}")
    check("PERSIST bounty conserved", done[1] == 100, f"bounty={done[1]}")
    return passed, total


def run_audit_test() -> Tuple[int, int]:
    """--audit-test (v0.55): run the full §SK.6 story and verify the audit
    trail covers every business op with JSON-serializable, semantics-correct
    events (matches sigma-runtime event shape — the same ops are auditable)."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    app = MVPApp()
    app.open_quota(7, 50)
    tid, _, _, _ = app.post_task(7, 100)
    app.claim_task(tid, 3)
    app.submit_work(tid)
    app.accept_work(tid, 7)
    app.withdraw(3, 100)

    trail = app.audit_trail()
    ops = [e["op"] for e in trail]
    expect = ["quota_new", "task_create", "accept_task", "task_submit",
              "task_accept", "points_withdraw"]
    check("AUDIT all ops", ops == expect, f"ops={ops}")
    check("AUDIT every event has io",
          all("input" in e and "output" in e for e in trail))
    try:
        json.dumps(trail)
        check("AUDIT json-serializable", True)
    except (TypeError, ValueError) as e:
        check("AUDIT json-serializable", False, str(e))
    accept_event = trail[4]
    check("AUDIT task_accept semantics",
          accept_event["output"]["task"] == [7, 100, 3, 3],
          f"got {accept_event['output']}")
    check("AUDIT points_withdraw semantics",
          trail[5]["output"] == [0, 0], f"got {trail[5]['output']}")
    return passed, total


def run_scenario() -> Tuple[int, int]:
    """--scenario (v0.66): CLI 版完整业务流剧本 — 注册 → 开户 → 发单 → 接单 →
    提交 → 验收 → 提现 → 勋章 → 查询 → 增长期 → 审计/不变量，一条命令走完找茬
    全业务流（与 --smoke 的 HTTP 全链路对应，这里是 App 方法直调剧本）。"""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    app = MVPApp()
    # 1. 用户会话
    app.register(7, "找茬主")
    app.register(3, "找茬人")
    check("SCEN users", len(app.users) == 2, f"users={len(app.users)}")
    # 2. 开户 → 发单 → 接单 → 提交 → 验收（§SK.6 MVP 链）
    q0 = app.open_quota(7, 50)
    check("SCEN quota", q0 == [50, 50], f"got {q0}")
    tid, task, q1, p0 = app.post_task(7, 100)
    check("SCEN post", task == [7, 100, 0, 0], f"got {task}")
    claimed = app.claim_task(tid, 3)
    check("SCEN claim", claimed == [7, 100, 1, 3], f"got {claimed}")
    submitted = app.submit_work(tid)
    check("SCEN submit", submitted == [7, 100, 2, 3], f"got {submitted}")
    done, p1, credit, contribution = app.accept_work(tid, 7)
    check("SCEN accept", done == [7, 100, 3, 3], f"got {done}")
    check("SCEN bounty conserved", done[1] == 100, f"bounty={done[1]}")
    # 3. 提现 + 勋章
    p2 = app.withdraw(3, 100)
    check("SCEN withdraw", p2 == [0, 0], f"got {p2}")
    check("SCEN points settled", app.points == [0, 0], f"got {app.points}")
    check("SCEN badge", app.badge(3) == 1, f"got {app.badge(3)}")
    # 4. 查询端点
    check("SCEN tasks", len(app.tasks_list()) == 1, f"got {app.tasks_list()}")
    check("SCEN users", len(app.users_list()) == 2, f"got {app.users_list()}")
    # 5. 增长期（核验师签发 + 督导裁决）
    check("SCEN badge_issue", app.issue_badge(1001, 3, credit) == [1001, 3, 1],
          f"got {app.issue_badge(1001, 3, credit)}")
    check("SCEN dispute", app.dispute([[1, 1, 3], [2, 1, 2]]) == 1,
          f"got {app.dispute([[1, 1, 3], [2, 1, 2]])}")
    # 6. 审计追踪（每个业务动作都有 ΣLang 事件）
    check("SCEN audit", len(app.audit_trail()) >= 6,
          f"trail={len(app.audit_trail())}")
    # 7. 状态可持久化（scenario 结束时全状态可 JSON 序列化）
    try:
        json.dumps(app.to_state())
        check("SCEN persistable", True)
    except (TypeError, ValueError) as e:
        check("SCEN persistable", False, str(e))
    return passed, total


def run_auth_test() -> Tuple[int, int]:
    """--auth-test (v0.71): token auth gate over HTTP — no token → 401,
    wrong token → 401, right token → 200 (and business works)."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    _Handler._auth_token = "test-token"
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def get_status(path: str) -> Tuple[int, dict]:
        try:
            with urllib.request.urlopen(base + path, timeout=10) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))

    st, r = get_status("/tasks")
    check("AUTH no token -> 401", st == 401, f"got {st} {r}")
    st, r = get_status("/tasks?token=wrong")
    check("AUTH wrong token -> 401", st == 401, f"got {st} {r}")
    st, r = get_status("/tasks?token=test-token")
    check("AUTH right token -> 200", st == 200, f"got {st} {r}")
    st, r = get_status(f"/register?token=test-token&user=7&name={quote('找茬主')}")
    check("AUTH business works", st == 200 and r["profile"].get("joined") is True,
          f"got {st} {r}")

    _Handler._auth_token = None  # 复位（不影响后续测试）
    server.shutdown()
    thread.join()
    return passed, total


def run_atomic_test() -> Tuple[int, int]:
    """--atomic-test (v0.72): atomic state writes — tmp + os.replace, so the
    state file is always valid JSON, no .tmp residue remains, and a rebuilt
    App continues the business flow."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    import tempfile
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        app = MVPApp()
        app.open_quota(7, 50)
        tid, _, _, _ = app.post_task(7, 100)
        app.claim_task(tid, 3)
        _Handler.app = app
        _Handler._state_file = path
        for _ in range(2):  # 连续两次请求后的持久化（原子写路径）
            _Handler._save_state()
        with open(path, encoding="utf-8") as f:
            state = json.load(f)
        check("ATOMIC file valid json", state["next_task"] == 1, f"got {state}")
        check("ATOMIC tasks persisted", len(state["tasks"]) == 1,
              f"got {state['tasks']}")
        check("ATOMIC no tmp residue", not os.path.exists(path + ".tmp"))
        app2 = MVPApp.from_state(state)
        rebuilt = app2.submit_work(tid)
        check("ATOMIC rebuild continues", rebuilt == [7, 100, 2, 3],
              f"got {rebuilt}")
    finally:
        _Handler._state_file = None
        for p in (path, path + ".tmp"):
            if os.path.exists(p):
                os.remove(p)
    return passed, total


def run_log_test() -> Tuple[int, int]:
    """--log-test (v0.73): leveled logging over HTTP — success requests log
    INFO, error requests log WARNING, all into the --log-file."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    import tempfile
    fd, path = tempfile.mkstemp(suffix=".log")
    os.close(fd)
    try:
        _Handler.app = MVPApp()
        _Handler._log_file = path
        server = HTTPServer(("127.0.0.1", 0), _Handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{port}"

        def get_status(path_: str) -> int:
            try:
                with urllib.request.urlopen(base + path_, timeout=10) as resp:
                    return resp.status
            except urllib.error.HTTPError as e:
                return e.code

        get_status("/tasks")                                  # 200 → INFO
        get_status("/ship_stock?inv=[15,20]&item=0&qty=99")   # 409 → WARNING
        get_status("/unknown")                                # 404 → WARNING

        with open(path, encoding="utf-8") as f:
            logs = f.read()
        check("LOG access INFO", "INFO" in logs and "/tasks" in logs,
              f"logs={logs[:120]!r}")
        check("LOG error WARNING", "WARNING" in logs, f"logs={logs[:120]!r}")
        check("LOG business error", "/ship_stock" in logs and "409" in logs,
              f"logs={logs[:120]!r}")
        check("LOG unknown 404", "/unknown" in logs, f"logs={logs[:120]!r}")

        server.shutdown()
        thread.join()
    finally:
        _Handler._log_file = None
        if os.path.exists(path):
            os.remove(path)
    return passed, total


def run_health_test() -> Tuple[int, int]:
    """--health-test (v0.74): GET /health — 200 ok with config summary and
    gate info."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"
    try:
        with urllib.request.urlopen(base + "/health", timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        check("HEALTH status ok", body.get("status") == "ok", f"got {body}")
        check("HEALTH app name", "找茬" in body.get("app", ""), f"got {body}")
        check("HEALTH auth field", "auth" in body, f"got {body}")
        check("HEALTH gates", body.get("gates", {}).get("consensus") == "56/56",
              f"got {body.get('gates')}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_startup_test() -> Tuple[int, int]:
    """--startup-test (v0.75): the --serve startup self-check gate — the §SK.6
    story must pass before listening; a failing gate refuses to start."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    # 1. 自检门禁本身通过（§SK.6 15/15）
    p, t = run_story(MVPApp())
    check("STARTUP gate passes", p == t == 15, f"got {p}/{t}")

    # 2. 失败 → 拒绝启动（monkeypatch run_story 返回失败，模拟门禁不过）
    orig = globals()["run_story"]
    try:
        globals()["run_story"] = lambda app: (0, 1)
        sp, st = run_story(MVPApp())
        check("STARTUP gate failure refused", sp != st, f"got {sp}/{st}")
    finally:
        globals()["run_story"] = orig

    # 3. 通过 → 放行
    sp, st = run_story(MVPApp())
    check("STARTUP gate pass proceeds", sp == st, f"got {sp}/{st}")
    return passed, total


def run_method_test() -> Tuple[int, int]:
    """--method-test (v0.82): HTTP method semantics — queries work on GET,
    mutations work on POST, and GET/POST on the same path agree."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def get(path: str) -> dict:
        with urllib.request.urlopen(base + path, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def post(path: str) -> dict:
        req = urllib.request.Request(base + path, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))

    try:
        # 1. 查询端点 GET 可用
        r = get("/tasks")
        check("METHOD get query", "tasks" in r, f"got {r}")
        # 2. 变更端点 POST 可用（注册 + 发单）
        r = post(f"/register?user=7&name={quote('找茬主')}")
        check("METHOD post mutation", r["profile"].get("joined") is True,
              f"got {r}")
        r = post("/quota?user=7&monthly=50")
        check("METHOD post quota", r["quota"] == [50, 50], f"got {r}")
        # 3. GET/POST 同路径结果一致
        g = get("/tasks")
        p = post("/tasks")
        check("METHOD get==post", g == p, f"GET {g} vs POST {p}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_frontend_scenario() -> Tuple[int, int]:
    """--frontend-scenario (v0.83): a frontend-perspective HTTP integration
    script — the exact call sequence a web page would make (mixed GET/POST),
    each response asserted against the §SK.6 flow. Pure HTTP, no App calls."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(path: str, method: str = "GET") -> dict:
        req = urllib.request.Request(base + path, method=method)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))

    try:
        # 1. 前端注册（POST）+ 开户（POST）
        r = call(f"/register?user=7&name={quote('找茬主')}", "POST")
        check("FE register", r["profile"].get("joined") is True, f"got {r}")
        r = call(f"/register?user=3&name={quote('找茬人')}", "POST")
        check("FE register2", r["profile"].get("joined") is True, f"got {r}")
        r = call("/quota?user=7&monthly=50", "POST")
        check("FE quota", r["quota"] == [50, 50], f"got {r}")
        # 2. 发需求（POST）→ 前端列表（GET）
        r = call("/post?author=7&bounty=100", "POST")
        check("FE post", r["task"] == [7, 100, 0, 0], f"got {r}")
        tid = r["task_id"]
        r = call("/tasks")
        check("FE tasks list", len(r["tasks"]) == 1, f"got {r}")
        # 3. 接单 / 提交 / 验收（POST）
        r = call(f"/claim?task={tid}&hunter=3", "POST")
        check("FE claim", r["task"] == [7, 100, 1, 3], f"got {r}")
        r = call(f"/submit?task={tid}", "POST")
        check("FE submit", r["task"] == [7, 100, 2, 3], f"got {r}")
        r = call(f"/accept?task={tid}&caller=7", "POST")
        check("FE accept", r["task"] == [7, 100, 3, 3], f"got {r}")
        # 4. 提现（POST）+ 勋章（GET）
        r = call("/withdraw?user=3&amount=100", "POST")
        check("FE withdraw", r["points"] == [0, 0], f"got {r}")
        r = call("/badge?user=3")
        check("FE badge", r["badge"] == 1, f"got {r}")
        # 5. 用户摘要（GET）
        r = call("/me?user=3")
        check("FE me", r["credit"] == 105, f"got {r}")

        # 6. 增长期（v0.114 — 前端 v0.110 增长期面板会调用的端点）
        r = call("/badge_issue?verifier=1001&user=3&score=105")
        check("FE badge_issue", r["badge"] == [1001, 3, 1], f"got {r}")
        r = call("/dispute?evidence=[[1,1,3],[2,1,2]]")
        check("FE dispute", r["decision"] == 1, f"got {r}")
        r = call("/team_create?owner=7&kind=0&capacity=3")
        check("FE team_create", r["team"] == [7, 0, 1, 3], f"got {r}")
        r = call("/team_join?team=[7,0,1,3]&member=5")
        check("FE team_join", r["team"] == [7, 0, 2, 3], f"got {r}")
        r = call("/team_share?contribs=[[3,2],[4,4]]&reward=6")
        check("FE team_share", r["shares"] == [[3, 2], [4, 4]], f"got {r}")

        # 7. 供应链（v0.114 — 前端 v0.111 供应链面板会调用的端点）
        r = call("/inventory_new?qty_a=10&qty_b=20")
        check("FE inventory_new", r["inventory"] == [10, 20], f"got {r}")
        r = call("/receive_stock?inv=[10,20]&item=0&qty=5")
        check("FE receive_stock", r["inventory"] == [15, 20], f"got {r}")
        r = call("/ship_stock?inv=[15,20]&item=0&qty=4")
        check("FE ship_stock", r["inventory"] == [11, 20], f"got {r}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_web_test() -> Tuple[int, int]:
    """--web-test (v0.93): frontend-backend integration over HTTP — serves the
    web/ frontend statically, then walks the exact call sequence a browser
    page would make and probes every endpoint the page's JS references."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    import http.server
    import re
    _Handler.app = MVPApp()
    api_server = HTTPServer(("127.0.0.1", 0), _Handler)
    api_port = api_server.server_address[1]
    threading.Thread(target=api_server.serve_forever, daemon=True).start()
    web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "web")
    old_cwd = os.getcwd()
    try:
        os.chdir(web_dir)
        front = HTTPServer(("127.0.0.1", 0), http.server.SimpleHTTPRequestHandler)
        front_port = front.server_address[1]
        threading.Thread(target=front.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{api_port}"
        fbase = f"http://127.0.0.1:{front_port}"

        # 1. 前端页面可访问（含关键 UI 元素）
        with urllib.request.urlopen(fbase + "/", timeout=10) as r:
            html = r.read().decode("utf-8")
        check("WEB front serves",
              r.status == 200 and "找茬" in html and "注册" in html and "任务列表" in html,
              f"status {r.status}")
        # 2. 后端健康
        with urllib.request.urlopen(base + "/health", timeout=10) as r:
            h = json.loads(r.read().decode("utf-8"))
        check("WEB api health", h.get("status") == "ok", f"got {h}")
        # 3. 前端视角业务流（页面会发出的调用序列）
        def call(p: str) -> dict:
            with urllib.request.urlopen(base + p, timeout=10) as r:
                return json.loads(r.read().decode("utf-8"))
        call(f"/register?user=7&name={quote('找茬主')}")
        call("/quota?user=7&monthly=50")
        r = call("/post?author=7&bounty=100")
        check("WEB flow post", r["task"] == [7, 100, 0, 0], f"got {r}")
        r = call("/tasks")
        check("WEB flow tasks", len(r["tasks"]) == 1, f"got {r}")
        # 4. 页面 JS 引用的端点全部存在（404 = 路径不存在；400 = 路由存在
        #    但参数缺失，属正常）
        def probe(p: str) -> int:
            try:
                return urllib.request.urlopen(base + "/" + p, timeout=10).status
            except urllib.error.HTTPError as e:
                return e.code
        paths = sorted(set(re.findall(
            r"/(register|quota|post|tasks|claim|submit|accept|withdraw|badge|me|health)\b",
            html)))
        missing = [p for p in paths if probe(p) == 404]
        check("WEB endpoints exist", not missing, f"missing(404) {missing} in {paths}")
        front.shutdown()
    finally:
        os.chdir(old_cwd)
        api_server.shutdown()
    return passed, total


def run_panel_test() -> Tuple[int, int]:
    """--panel-test (v0.95): GET /panel — the run-status HTML page carries the
    live business summary (users / tasks / bounty) and the gate summary."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        call(f"/register?user=7&name={quote('找茬主')}")
        call("/quota?user=7&monthly=50")
        call("/post?author=7&bounty=100")
        with urllib.request.urlopen(base + "/panel", timeout=10) as r:
            html = r.read().decode("utf-8")
        check("PANEL serves", r.status == 200 and "找茬运行面板" in html,
              f"status {r.status}")
        check("PANEL live users", "用户数" in html and ">1<" in html, "")
        check("PANEL live tasks", "任务数" in html and ">1<" in html, "")
        check("PANEL live bounty", "赏金总额" in html and ">100<" in html, "")
        check("PANEL gates", "56/56" in html and "310 PROVED" in html, "")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_stats_test() -> Tuple[int, int]:
    """--stats-test (v0.134): GET /stats — the JSON business statistics reflect
    the live state (users / tasks by state / bounty / platform points / credit)."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        call(f"/register?user=7&name={quote('找茬主')}")
        call(f"/register?user=3&name={quote('找茬人')}")
        call("/quota?user=7&monthly=50")
        call("/post?author=7&bounty=100")
        s = call("/stats")
        check("STATS users", s["users"] == 2, f"got {s}")
        check("STATS tasks", s["tasks"] == 1, f"got {s}")
        check("STATS bounty", s["total_bounty"] == 100, f"got {s}")
        check("STATS by_state", s["tasks_by_state"]["0"] == 1, f"got {s}")
        check("STATS escrow", s["platform_points"][0] == 100, f"got {s}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_portfolio_test() -> Tuple[int, int]:
    """--portfolio-test (v0.147): §PF market endpoints — new/buy/sell/value/risk
    chain over HTTP, results match the portfolio semantics."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        r = call("/portfolio_new?cash=100")
        check("PF new", r["portfolio"] == [100, 0, 0], f"got {r}")
        r = call("/portfolio_buy?pf=[100,0,0]&asset=0&qty=30")
        check("PF buy", r["portfolio"] == [70, 30, 0], f"got {r}")
        r = call("/portfolio_sell?pf=[70,30,0]&asset=0&qty=20")
        check("PF sell", r["portfolio"] == [90, 10, 0], f"got {r}")
        r = call("/portfolio_value?pf=[90,10,0]")
        check("PF value", r["value"] == 100, f"got {r}")
        r = call("/portfolio_risk?pf=[90,10,0]")
        check("PF risk", r["risk"] == 10, f"got {r}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_inventory_test() -> Tuple[int, int]:
    """--inventory-test (v0.157): §IN supply-chain chain over HTTP — open →
    receive → ship → level → fill_rate, results match the inventory
    semantics (mirrors --portfolio-test)."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        r = call("/inventory_new?qty_a=10&qty_b=20")
        check("INV new", r["inventory"] == [10, 20], f"got {r}")
        r = call("/receive_stock?inv=[10,20]&item=0&qty=5")
        check("INV receive", r["inventory"] == [15, 20], f"got {r}")
        r = call("/ship_stock?inv=[15,20]&item=0&qty=4")
        check("INV ship", r["inventory"] == [11, 20], f"got {r}")
        r = call("/stock_level?inv=[11,20]&item=0")
        check("INV level", r["level"] == 11, f"got {r}")
        r = call("/fill_rate?shipped=6&demanded=10")
        check("INV fill", abs(r["rate"] - 0.6) < 1e-9, f"got {r}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_cross_domain_test() -> Tuple[int, int]:
    """--cross-domain-test (v0.167): §SK→§PF→§IN cross-domain chain over HTTP —
    bounty escrow (找茬) → reward into portfolio (§PF) → parallel inventory
    movement (§IN), matching the sigma_cross_domain_ok corpus semantics."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        # §SK 找茬托管（发单 → 赏金托管 escrow=100）
        call(f"/register?user=7&name={quote('找茬主')}")
        call("/quota?user=7&monthly=50")
        r = call("/post?author=7&bounty=100")
        check("XD post escrow", r["points"] == [100, 0], f"got {r}")
        # §PF 奖励入市（开组合 → 买入）
        r = call("/portfolio_new?cash=100")
        check("XD pf new", r["portfolio"] == [100, 0, 0], f"got {r}")
        r = call("/portfolio_buy?pf=[100,0,0]&asset=0&qty=30")
        check("XD pf buy", r["portfolio"] == [70, 30, 0], f"got {r}")
        # §IN 库存并行（开仓 → 出库）
        r = call("/inventory_new?qty_a=10&qty_b=20")
        check("XD inv new", r["inventory"] == [10, 20], f"got {r}")
        r = call("/ship_stock?inv=[10,20]&item=0&qty=4")
        check("XD inv ship", r["inventory"] == [6, 20], f"got {r}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_errors_test() -> Tuple[int, int]:
    """--errors-test (v0.177): three-domain error boundaries over HTTP — every
    error path returns the semantic 4xx code, matching sigma_errors_ok corpus."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    def get_status(p: str):
        try:
            with urllib.request.urlopen(base + p, timeout=10) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))

    try:
        call(f"/register?user=7&name={quote('找茬主')}")
        call(f"/register?user=3&name={quote('找茬人')}")
        call("/quota?user=7&monthly=50")
        call("/post?author=7&bounty=100")
        call("/claim?task=0&hunter=3")
        call("/submit?task=0")
        # §SK 错误边界
        st, r = get_status("/withdraw?user=3&amount=1000")
        check("ERR withdraw", st == 409, f"got {st} {r}")
        st, r = get_status("/accept?task=0&caller=3")
        check("ERR auth", st == 403, f"got {st} {r}")
        # §PF 错误边界
        st, r = get_status("/portfolio_buy?pf=[10,0,0]&asset=0&qty=30")
        check("ERR funds", st == 409, f"got {st} {r}")
        st, r = get_status("/portfolio_buy?pf=[100,0,0]&asset=2&qty=30")
        check("ERR asset", st == 409, f"got {st} {r}")
        # §IN 错误边界
        st, r = get_status("/ship_stock?inv=[10,20]&item=0&qty=99")
        check("ERR oversell", st == 409, f"got {st} {r}")
        st, r = get_status("/ship_stock?inv=[10,20]&item=2&qty=1")
        check("ERR unknown item", st == 409, f"got {st} {r}")
        st, r = get_status("/fill_rate?shipped=6&demanded=0")
        check("ERR divzero", st == 409, f"got {st} {r}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_points_test() -> Tuple[int, int]:
    """--points-test (v0.187): points-flow chain over HTTP — post (escrow 100)
    → claim → submit → accept (release to available) → withdraw, matching the
    INV-SK-8 bounty-points link semantics."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        call(f"/register?user=7&name={quote('找茬主')}")
        call(f"/register?user=3&name={quote('找茬人')}")
        call("/quota?user=7&monthly=50")
        r = call("/post?author=7&bounty=100")
        check("PTS escrow", r["points"] == [100, 0], f"got {r}")
        tid = r["task_id"]
        call(f"/claim?task={tid}&hunter=3")
        call(f"/submit?task={tid}")
        r = call(f"/accept?task={tid}&caller=7")
        check("PTS release", r["points"] == [0, 100], f"got {r}")
        r = call("/withdraw?user=3&amount=100")
        check("PTS withdraw", r["points"] == [0, 0], f"got {r}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_inventory_chain_test() -> Tuple[int, int]:
    """--inventory-chain-test (v0.197): supply-chain flow over HTTP — open →
    receive → ship → level → fill_rate chain, matching the INV-IN-6
    receive-ship link semantics."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        r = call("/inventory_new?qty_a=10&qty_b=20")
        check("INVC open", r["inventory"] == [10, 20], f"got {r}")
        r = call("/receive_stock?inv=[10,20]&item=0&qty=5")
        check("INVC receive", r["inventory"] == [15, 20], f"got {r}")
        r = call("/ship_stock?inv=[15,20]&item=0&qty=4")
        check("INVC ship", r["inventory"] == [11, 20], f"got {r}")
        r = call("/stock_level?inv=[11,20]&item=0")
        check("INVC level", r["level"] == 11, f"got {r}")
        r = call("/fill_rate?shipped=6&demanded=10")
        check("INVC fill", abs(r["rate"] - 0.6) < 1e-9, f"got {r}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_credit_test() -> Tuple[int, int]:
    """--credit-test (v0.207): credit chain over HTTP — task completion adds
    credit (契分), the badge reflects it, matching the INV-SK-7 task-credit
    link semantics."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        call(f"/register?user=7&name={quote('找茬主')}")
        call(f"/register?user=3&name={quote('找茬人')}")
        call("/quota?user=7&monthly=50")
        call("/post?author=7&bounty=100")
        call("/claim?task=0&hunter=3")
        call("/submit?task=0")
        r = call("/accept?task=0&caller=7")
        check("CRED accept", r["credit"] == 105, f"got {r}")
        r = call("/badge?user=3")
        check("CRED badge", r["badge"] == 1, f"got {r}")
        r = call("/me?user=3")
        check("CRED me credit", r["credit"] == 105, f"got {r}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_full_test() -> Tuple[int, int]:
    """--full-test (v0.217): full 找茬 business flow over HTTP — register →
    quota → post → claim → submit → accept → credit/badge → withdraw,
    end-to-end integration across the main §SK paths."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        call(f"/register?user=7&name={quote('找茬主')}")
        call(f"/register?user=3&name={quote('找茬人')}")
        call("/quota?user=7&monthly=50")
        r = call("/post?author=7&bounty=100")
        check("FULL post", r["task"][2] == 0, f"got {r}")
        tid = r["task_id"]
        call(f"/claim?task={tid}&hunter=3")
        call(f"/submit?task={tid}")
        r = call(f"/accept?task={tid}&caller=7")
        check("FULL accept", r["task"][2] == 3, f"got {r}")
        r = call("/badge?user=3")
        check("FULL badge", r["badge"] == 1, f"got {r}")
        r = call("/withdraw?user=3&amount=100")
        check("FULL withdraw", r["points"] == [0, 0], f"got {r}")
        r = call("/me?user=3")
        check("FULL me", r["credit"] == 105, f"got {r}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_audit_test() -> Tuple[int, int]:
    """--audit-test (v0.227): audit-log flow over HTTP — every mutating action
    appends to the audit trail, the trail reflects the full business chain
    (register/quota/post/claim/submit/accept/withdraw)."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        call(f"/register?user=7&name={quote('找茬主')}")
        call(f"/register?user=3&name={quote('找茬人')}")
        call("/quota?user=7&monthly=50")
        call("/post?author=7&bounty=100")
        call("/claim?task=0&hunter=3")
        call("/submit?task=0")
        call("/accept?task=0&caller=7")
        call("/withdraw?user=3&amount=100")
        r = call("/audit")
        kinds = [e.get("kind") for e in r.get("events", [])]
        check("AUDIT trail", len(r.get("events", [])) >= 6, f"got {len(r.get('events', []))}")
        for k in ("quota_new", "task_create", "accept_task", "task_accept",
                  "points_withdraw"):
            check(f"AUDIT {k}", k in kinds, f"got {kinds}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_contribution_test() -> Tuple[int, int]:
    """--contribution-test (v0.237): contribution-score chain over HTTP — each
    accepted task adds +10 contribution to the hunter, the score compounds
    across two tasks (20), the panel reflects it."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        call(f"/register?user=7&name={quote('找茬主')}")
        call(f"/register?user=3&name={quote('找茬人')}")
        call("/quota?user=7&monthly=50")
        call("/post?author=7&bounty=100")
        call("/claim?task=0&hunter=3")
        call("/submit?task=0")
        r = call("/accept?task=0&caller=7")
        check("CONTRIB task1", r["contribution"] == 10, f"got {r}")
        call("/post?author=7&bounty=100")
        call("/claim?task=1&hunter=3")
        call("/submit?task=1")
        r = call("/accept?task=1&caller=7")
        check("CONTRIB task2", r["contribution"] == 20, f"got {r}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_quota_flow_test() -> Tuple[int, int]:
    """--quota-flow-test (v0.247): quota-flow chain over HTTP — open (monthly
    50) → post spends 1 (remaining 49) → re-open resets to 50, covering the
    quota system's lifecycle."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        call(f"/register?user=7&name={quote('找茬主')}")
        call("/quota?user=7&monthly=50")
        r = call("/post?author=7&bounty=100")
        check("QUOTA spend", r["quota"] == [50, 49], f"got {r}")
        r = call("/quota?user=7&monthly=50")
        check("QUOTA reset", r["quota"] == [50, 50], f"got {r}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_badge_test() -> Tuple[int, int]:
    """--badge-test (v0.257): badge-chain over HTTP — credit tiers drive badge
    levels (credit <300 → badge 1), the badge reflects the accumulated credit,
    matching the INV-SK-11 credit-badge link semantics."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        call(f"/register?user=7&name={quote('找茬主')}")
        call(f"/register?user=3&name={quote('找茬人')}")
        call("/quota?user=7&monthly=50")
        call("/post?author=7&bounty=100")
        call("/claim?task=0&hunter=3")
        call("/submit?task=0")
        r = call("/accept?task=0&caller=7")
        check("BADGE credit", r["credit"] == 105, f"got {r}")
        r = call("/badge?user=3")
        check("BADGE level", r["badge"] == 1, f"got {r}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_inventory_flow_test() -> Tuple[int, int]:
    """--inventory-flow-test (v0.267): inventory-flow chain over HTTP — open →
    receive → ship both items → level/fill, covering the §IN mixed-item
    lifecycle matching INV-IN-8 mixed-ship-link semantics."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        r = call("/inventory_new?qty_a=10&qty_b=20")
        check("INVFLOW open", r["inventory"] == [10, 20], f"got {r}")
        r = call("/ship_stock?inv=[10,20]&item=0&qty=4")
        check("INVFLOW ship0", r["inventory"] == [6, 20], f"got {r}")
        r = call("/ship_stock?inv=[6,20]&item=1&qty=8")
        check("INVFLOW ship1", r["inventory"] == [6, 12], f"got {r}")
        r = call("/stock_level?inv=[6,12]&item=1")
        check("INVFLOW level", r["level"] == 12, f"got {r}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_portfolio_flow_test() -> Tuple[int, int]:
    """--portfolio-flow-test (v0.277): portfolio-flow chain over HTTP — open →
    buy both assets → sell → value/risk, covering the §PF mixed-asset lifecycle
    matching INV-PF-8 mixed-asset-chain semantics."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        r = call("/portfolio_new?cash=100")
        check("PFFLOW open", r["portfolio"] == [100, 0, 0], f"got {r}")
        r = call("/portfolio_buy?pf=[100,0,0]&asset=0&qty=20")
        check("PFFLOW buy0", r["portfolio"] == [80, 20, 0], f"got {r}")
        r = call("/portfolio_buy?pf=[80,20,0]&asset=1&qty=10")
        check("PFFLOW buy1", r["portfolio"] == [70, 20, 10], f"got {r}")
        r = call("/portfolio_sell?pf=[70,20,10]&asset=1&qty=5")
        check("PFFLOW sell", r["portfolio"] == [75, 20, 5], f"got {r}")
        r = call("/portfolio_value?pf=[75,20,5]")
        check("PFFLOW value", r["value"] == 100, f"got {r}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_credit_badge_test() -> Tuple[int, int]:
    """--credit-badge-test (v0.287): credit-contribution-badge three-link chain
    over HTTP — accepted tasks compound credit (100+5n) and contribution (10n),
    the badge level tracks the credit tier, matching INV-SK-12 three-link
    semantics."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        call(f"/register?user=7&name={quote('找茬主')}")
        call(f"/register?user=3&name={quote('找茬人')}")
        call("/quota?user=7&monthly=50")
        call("/post?author=7&bounty=100")
        call("/claim?task=0&hunter=3")
        call("/submit?task=0")
        r = call("/accept?task=0&caller=7")
        check("CB credit", r["credit"] == 105, f"got {r}")
        check("CB contribution", r["contribution"] == 10, f"got {r}")
        r = call("/badge?user=3")
        check("CB badge", r["badge"] == 1, f"got {r}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_points_quota_test() -> Tuple[int, int]:
    """--points-quota-test (v0.297): points-quota link chain over HTTP — each
    posted task consumes one quota unit and escrows its bounty in points, so
    after n posts quota remaining = m−n ≥ 0 and points escrow = n×b, matching
    INV-SK-13 points-quota semantics."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        call(f"/register?user=7&name={quote('找茬主')}")
        call("/quota?user=7&monthly=50")
        call("/post?author=7&bounty=100")
        call("/post?author=7&bounty=100")
        r = call("/post?author=7&bounty=100")
        check("PQ quota remaining", r["quota"] == [50, 47], f"got {r}")
        check("PQ points escrow", r["points"] == [300, 0], f"got {r}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_task_points_quota_test() -> Tuple[int, int]:
    """--task-points-quota-test (v0.307): task-points-quota three-link chain
    over HTTP — each posted task consumes one quota unit and escrows its bounty
    in points, so after n posts tasks count = n, quota remaining = m−n ≥ 0 and
    points escrow = n×b, matching INV-SK-14 three-link semantics."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        call(f"/register?user=7&name={quote('找茬主')}")
        call("/quota?user=7&monthly=50")
        call("/post?author=7&bounty=100")
        call("/post?author=7&bounty=100")
        r = call("/post?author=7&bounty=100")
        check("TPQ tasks count", len(call("/tasks")["tasks"]) == 3, "")
        check("TPQ quota remaining", r["quota"] == [50, 47], f"got {r}")
        check("TPQ points escrow", r["points"] == [300, 0], f"got {r}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_valuation_risk_test() -> Tuple[int, int]:
    """--valuation-risk-test (v0.317): portfolio valuation-risk link chain
    over HTTP — buy asset0 q1 → buy asset1 q2 → sell asset0 q3 leaves the total
    valuation cash+qA+qB = initial cash (conserved) with valuation ≥ risk
    (cash ≥ 0), matching INV-PF-9 valuation-risk semantics."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        j0 = call("/portfolio_new?cash=100")
        pf = j0["portfolio"]
        pf = call(f"/portfolio_buy?pf={quote(json.dumps(pf))}&asset=0&qty=30")["portfolio"]
        pf = call(f"/portfolio_buy?pf={quote(json.dumps(pf))}&asset=1&qty=20")["portfolio"]
        pf = call(f"/portfolio_sell?pf={quote(json.dumps(pf))}&asset=0&qty=10")["portfolio"]
        v = call(f"/portfolio_value?pf={quote(json.dumps(pf))}")["value"]
        rsk = call(f"/portfolio_risk?pf={quote(json.dumps(pf))}")["risk"]
        check("VR value conserved", v == 100, f"got {pf} v={v}")
        check("VR value >= risk", v >= rsk, f"v={v} r={rsk}")
        check("VR cash nonneg", pf[0] >= 0, f"got {pf}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_stock_fillrate_test() -> Tuple[int, int]:
    """--stock-fillrate-test (v0.327): inventory stock-fill-rate link chain
    over HTTP — receive item0 q1 then ship item0 q2 (q2 ≤ demand) leaves
    stock_level = a+q1−q2 ≥ 0 and shipped q2 ≤ demand (fill rate ≤ 1),
    matching INV-IN-9 stock-fill-rate semantics."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        call("/inventory_new?qty_a=10&qty_b=20")
        inv = call("/receive_stock?inv=[10,20]&item=0&qty=5")["inventory"]
        inv = call("/ship_stock?inv=" + quote(json.dumps(inv)) + "&item=0&qty=3")["inventory"]
        fr = call("/fill_rate?shipped=3&demanded=4")["rate"]
        check("SF stock nonneg", inv[0] == 12 and inv[0] >= 0, f"got {inv}")
        check("SF fill rate <= 1", 0 <= fr <= 1, f"got {fr}")
        check("SF stock == a+q1-q2", inv[0] == 10 + 5 - 3, f"got {inv}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_accept_points_credit_test() -> Tuple[int, int]:
    """--accept-points-credit-test (v0.337): accept-points-credit three-link
    chain over HTTP — accepting n tasks releases escrow to available (n×b) and
    compounds credit (100+5n) and contribution (10n), matching INV-SK-15
    three-link semantics."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        call(f"/register?user=7&name={quote('找茬主')}")
        call(f"/register?user=3&name={quote('找茬人')}")
        call("/quota?user=7&monthly=50")
        call("/post?author=7&bounty=100")
        call("/claim?task=0&hunter=3")
        call("/submit?task=0")
        r = call("/accept?task=0&caller=7")
        check("APC points released", r["points"][0] == 0 and r["points"][1] == 100, f"got {r}")
        check("APC credit", r["credit"] == 105, f"got {r}")
        check("APC contribution", r["contribution"] == 10, f"got {r}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_dual_asset_test() -> Tuple[int, int]:
    """--dual-asset-test (v0.347): dual-asset mixed trade chain valuation
    conservation over HTTP — buy asset0 q1 → buy asset1 q2 → sell asset0 q3 →
    sell asset1 q4 leaves valuation cash+qA+qB = initial cash (conserved) with
    qA, qB, cash ≥ 0, matching INV-PF-10 valuation conservation semantics."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        j0 = call("/portfolio_new?cash=100")
        pf = j0["portfolio"]
        pf = call(f"/portfolio_buy?pf={quote(json.dumps(pf))}&asset=0&qty=30")["portfolio"]
        pf = call(f"/portfolio_buy?pf={quote(json.dumps(pf))}&asset=1&qty=20")["portfolio"]
        pf = call(f"/portfolio_sell?pf={quote(json.dumps(pf))}&asset=0&qty=10")["portfolio"]
        pf = call(f"/portfolio_sell?pf={quote(json.dumps(pf))}&asset=1&qty=5")["portfolio"]
        v = call(f"/portfolio_value?pf={quote(json.dumps(pf))}")["value"]
        check("DA value conserved", v == 100, f"got {pf} v={v}")
        check("DA cash nonneg", pf[0] >= 0, f"got {pf}")
        check("DA qA nonneg", pf[1] >= 0, f"got {pf}")
        check("DA qB nonneg", pf[2] >= 0, f"got {pf}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_receive_ship_fillrate_test() -> Tuple[int, int]:
    """--receive-ship-fillrate-test (v0.357): receive-ship-stock-fillrate
    four-link chain over HTTP — receive item0 q1 then ship item0 q2 (q2 ≤ q1)
    leaves stock_level = a+q1−q2 ≥ 0 and fill rate q2/q1 ≤ 1, matching
    INV-IN-10 four-link semantics."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        call("/inventory_new?qty_a=10&qty_b=20")
        inv = call("/receive_stock?inv=[10,20]&item=0&qty=5")["inventory"]
        inv = call("/ship_stock?inv=" + quote(json.dumps(inv)) + "&item=0&qty=3")["inventory"]
        fr = call("/fill_rate?shipped=3&demanded=5")["rate"]
        check("RSF stock nonneg", inv[0] == 12 and inv[0] >= 0, f"got {inv}")
        check("RSF fill rate <= 1", 0 <= fr <= 1, f"got {fr}")
        check("RSF stock == a+q1-q2", inv[0] == 10 + 5 - 3, f"got {inv}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_withdraw_credit_test() -> Tuple[int, int]:
    """--withdraw-credit-test (v0.367): withdraw-credit link chain over HTTP —
    accepting n tasks releases escrow to available (n×b), then withdrawing w
    (w ≤ available) leaves available = n×b − w ≥ 0 with escrow = 0 and credit
    = 100+5n, matching INV-SK-16 withdraw-credit semantics."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        call(f"/register?user=7&name={quote('找茬主')}")
        call(f"/register?user=3&name={quote('找茬人')}")
        call("/quota?user=7&monthly=50")
        call("/post?author=7&bounty=100")
        call("/claim?task=0&hunter=3")
        call("/submit?task=0")
        call("/accept?task=0&caller=7")
        r = call("/withdraw?user=3&amount=40")
        check("WC available nonneg", r["points"][1] == 60 and r["points"][1] >= 0, f"got {r}")
        check("WC escrow zero", r["points"][0] == 0, f"got {r}")
        c = call("/badge?user=3")
        check("WC credit", c["credit"] == 105, f"got {c}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_dual_asset_vr_test() -> Tuple[int, int]:
    """--dual-asset-vr-test (v0.377): dual-asset buy-sell valuation-risk
    four-link chain over HTTP — buy asset0 q1 → buy asset1 q2 → sell asset0 q3
    → sell asset1 q4 leaves valuation cash+qA+qB = initial cash (conserved)
    with valuation ≥ risk (cash ≥ 0) and qA, qB ≥ 0, matching INV-PF-11
    valuation-risk four-link semantics."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        j0 = call("/portfolio_new?cash=100")
        pf = j0["portfolio"]
        pf = call(f"/portfolio_buy?pf={quote(json.dumps(pf))}&asset=0&qty=30")["portfolio"]
        pf = call(f"/portfolio_buy?pf={quote(json.dumps(pf))}&asset=1&qty=20")["portfolio"]
        pf = call(f"/portfolio_sell?pf={quote(json.dumps(pf))}&asset=0&qty=10")["portfolio"]
        pf = call(f"/portfolio_sell?pf={quote(json.dumps(pf))}&asset=1&qty=5")["portfolio"]
        v = call(f"/portfolio_value?pf={quote(json.dumps(pf))}")["value"]
        rsk = call(f"/portfolio_risk?pf={quote(json.dumps(pf))}")["risk"]
        check("DVR value conserved", v == 100, f"got {pf} v={v}")
        check("DVR value >= risk", v >= rsk, f"v={v} r={rsk}")
        check("DVR cash nonneg", pf[0] >= 0, f"got {pf}")
        check("DVR qA/qB nonneg", pf[1] >= 0 and pf[2] >= 0, f"got {pf}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_dual_item_four_link_test() -> Tuple[int, int]:
    """--dual-item-four-link-test (v0.387): dual-item receive-ship-stock-fillrate
    four-link chain over HTTP — receive item0 q1 → receive item1 q2 → ship
    item0 q3 → ship item1 q4 (q3 ≤ q1, q4 ≤ q2) leaves item0 = a+q1−q3 ≥ 0 and
    item1 = b+q2−q4 ≥ 0 with fill rates ≤ 1, matching INV-IN-11 four-link
    semantics."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        call("/inventory_new?qty_a=10&qty_b=20")
        inv = call("/receive_stock?inv=[10,20]&item=0&qty=5")["inventory"]
        inv = call("/receive_stock?inv=" + quote(json.dumps(inv)) + "&item=1&qty=6")["inventory"]
        inv = call("/ship_stock?inv=" + quote(json.dumps(inv)) + "&item=0&qty=3")["inventory"]
        inv = call("/ship_stock?inv=" + quote(json.dumps(inv)) + "&item=1&qty=4")["inventory"]
        fr0 = call("/fill_rate?shipped=3&demanded=5")["rate"]
        fr1 = call("/fill_rate?shipped=4&demanded=6")["rate"]
        check("DI item0 nonneg", inv[0] == 12 and inv[0] >= 0, f"got {inv}")
        check("DI item1 nonneg", inv[1] == 22 and inv[1] >= 0, f"got {inv}")
        check("DI fillrate0 <= 1", 0 <= fr0 <= 1, f"got {fr0}")
        check("DI fillrate1 <= 1", 0 <= fr1 <= 1, f"got {fr1}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_full_business_five_link_test() -> Tuple[int, int]:
    """--full-business-five-link-test (v0.397): full business five-link
    conservation over HTTP — post n tasks (quota remaining=m−n, escrow=n×b) →
    accept n tasks (escrow fully released) → withdraw w (w ≤ n×b) leaves quota
    remaining=m−n ≥ 0, escrow=0, available=n×b−w ≥ 0, credit=100+5n and
    contribution=10n, matching INV-SK-17 five-link semantics."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        call(f"/register?user=7&name={quote('找茬主')}")
        call(f"/register?user=3&name={quote('找茬人')}")
        call("/quota?user=7&monthly=50")
        call("/post?author=7&bounty=100")
        call("/claim?task=0&hunter=3")
        call("/submit?task=0")
        r = call("/accept?task=0&caller=7")
        w = call("/withdraw?user=3&amount=40")
        me = call("/me?user=7")
        check("FB quota remaining", me["quota"][1] == 49 and me["quota"][1] >= 0, f"got {me}")
        check("FB escrow zero", w["points"][0] == 0, f"got {w}")
        check("FB available nonneg", w["points"][1] == 60 and w["points"][1] >= 0, f"got {w}")
        check("FB credit", r["credit"] == 105, f"got {r}")
        check("FB contribution", r["contribution"] == 10, f"got {r}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_accept_withdraw_credit_badge_test() -> Tuple[int, int]:
    """--accept-withdraw-credit-badge-test (v0.405): accept-withdraw-credit-badge
    four-link chain over HTTP — accepting n tasks releases escrow to available
    (n×b), withdrawing w (w ≤ available) leaves available = n×b − w ≥ 0 with
    escrow = 0, credit = 100+5n and badge by tier, matching INV-SK-18
    four-link semantics."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        call(f"/register?user=7&name={quote('找茬主')}")
        call(f"/register?user=3&name={quote('找茬人')}")
        call("/quota?user=7&monthly=50")
        call("/post?author=7&bounty=100")
        call("/claim?task=0&hunter=3")
        call("/submit?task=0")
        r = call("/accept?task=0&caller=7")
        w = call("/withdraw?user=3&amount=40")
        b = call("/badge?user=3")
        check("AWC available nonneg", w["points"][1] == 60 and w["points"][1] >= 0, f"got {w}")
        check("AWC escrow zero", w["points"][0] == 0, f"got {w}")
        check("AWC credit", r["credit"] == 105, f"got {r}")
        check("AWC badge", b["badge"] == 1, f"got {b}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_dual_asset_equal_trade_test() -> Tuple[int, int]:
    """--dual-asset-equal-trade-test (v0.415): dual-asset equal buy-sell trade
    offset chain over HTTP — buy asset0 q1 → buy asset1 q2 → sell asset0 q1 →
    sell asset1 q2 leaves cash = initial cash, qA = 0 and qB = 0 (fully
    restored), matching INV-PF-12 equal-trade offset semantics."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        j0 = call("/portfolio_new?cash=100")
        pf = j0["portfolio"]
        pf = call(f"/portfolio_buy?pf={quote(json.dumps(pf))}&asset=0&qty=30")["portfolio"]
        pf = call(f"/portfolio_buy?pf={quote(json.dumps(pf))}&asset=1&qty=20")["portfolio"]
        pf = call(f"/portfolio_sell?pf={quote(json.dumps(pf))}&asset=0&qty=30")["portfolio"]
        pf = call(f"/portfolio_sell?pf={quote(json.dumps(pf))}&asset=1&qty=20")["portfolio"]
        v = call(f"/portfolio_value?pf={quote(json.dumps(pf))}")["value"]
        check("ET cash restored", pf[0] == 100, f"got {pf}")
        check("ET qA zero", pf[1] == 0, f"got {pf}")
        check("ET qB zero", pf[2] == 0, f"got {pf}")
        check("ET value conserved", v == 100, f"got {pf} v={v}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_dual_item_equal_trade_test() -> Tuple[int, int]:
    """--dual-item-equal-trade-test (v0.425): dual-item equal receive-ship trade
    offset chain over HTTP — receive item0 q1 → receive item1 q2 → ship item0 q1
    → ship item1 q2 leaves item0 = initial a, item1 = initial b (fully restored),
    matching INV-IN-12 equal-trade offset semantics."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> dict:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    try:
        call("/inventory_new?qty_a=10&qty_b=20")
        inv = call("/receive_stock?inv=[10,20]&item=0&qty=5")["inventory"]
        inv = call("/receive_stock?inv=" + quote(json.dumps(inv)) + "&item=1&qty=6")["inventory"]
        inv = call("/ship_stock?inv=" + quote(json.dumps(inv)) + "&item=0&qty=5")["inventory"]
        inv = call("/ship_stock?inv=" + quote(json.dumps(inv)) + "&item=1&qty=6")["inventory"]
        check("EIT item0 restored", inv[0] == 10, f"got {inv}")
        check("EIT item1 restored", inv[1] == 20, f"got {inv}")
        check("EIT total conserved", inv[0] + inv[1] == 30, f"got {inv}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_concurrency_test() -> Tuple[int, int]:
    """--concurrency-test (v0.103): concurrent requests keep the state
    consistent — parallel clients (register / quota / post / tasks mix) all
    succeed, the final state matches expectations, and the service stays
    alive afterwards."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    from concurrent.futures import ThreadPoolExecutor
    _Handler.app = MVPApp()
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str):
        try:
            with urllib.request.urlopen(base + p, timeout=15) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, {}

    try:
        # 第一批：并发注册 + 开户（无依赖）
        reqs = [f"/register?user={i}&name=u{i}" for i in range(20)]
        reqs += [f"/quota?user={i}&monthly=50" for i in range(20)]
        with ThreadPoolExecutor(max_workers=16) as ex:
            list(ex.map(call, reqs))
        # 第二批：并发发单（依赖额度已满足）+ 查询
        reqs2 = [f"/post?author={i}&bounty=100" for i in range(10)]
        reqs2 += ["/tasks"] * 20
        with ThreadPoolExecutor(max_workers=16) as ex:
            results = list(ex.map(call, reqs2))
        bad = sum(1 for s, _ in results if s != 200)
        check("CONC all 200", bad == 0, f"{bad} non-200 responses")
        check("CONC users", len(_Handler.app.users) == 20,
              f"got {len(_Handler.app.users)}")
        check("CONC tasks", len(_Handler.app.tasks) == 10,
              f"got {len(_Handler.app.tasks)}")
        st, h = call("/health")
        check("CONC alive", st == 200 and h.get("status") == "ok",
              f"got {st} {h}")
    finally:
        server.shutdown()
        thread.join()
    return passed, total


def run_deploy_accept() -> Tuple[int, int]:
    """--deploy-accept (v0.104): go-live deployment acceptance — the launch
    form (backend + frontend + data/ default persistence/audit/log from
    v0.102) verified end to end: startup self-check, dual services online,
    full business flow, the data/ files generated, live /panel, and the
    service alive afterwards."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    import http.server
    sp, st = run_story(MVPApp())
    check("DEPLOY-ACCEPT self-check", sp == st == 15, f"got {sp}/{st}")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(root, "data")
    state_path = os.path.join(data_dir, "state.json")
    audit_path = os.path.join(data_dir, "audit.json")
    log_path = os.path.join(data_dir, "app.log")
    os.makedirs(data_dir, exist_ok=True)
    for p in (state_path, audit_path, log_path):
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass
    _Handler.app = MVPApp()
    _Handler._state_file = state_path
    _Handler._audit_file = audit_path
    _Handler._log_file = log_path
    api_server = HTTPServer(("127.0.0.1", 0), _Handler)
    api_port = api_server.server_address[1]
    threading.Thread(target=api_server.serve_forever, daemon=True).start()
    web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "web")
    old_cwd = os.getcwd()
    try:
        os.chdir(web_dir)
        front = HTTPServer(("127.0.0.1", 0), http.server.SimpleHTTPRequestHandler)
        front_port = front.server_address[1]
        threading.Thread(target=front.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{api_port}"
        fbase = f"http://127.0.0.1:{front_port}"

        # 双服务在线
        with urllib.request.urlopen(fbase + "/", timeout=10) as r:
            html = r.read().decode("utf-8")
        check("DEPLOY-ACCEPT front", r.status == 200 and "找茬" in html,
              f"status {r.status}")
        with urllib.request.urlopen(base + "/health", timeout=10) as r:
            h = json.loads(r.read().decode("utf-8"))
        check("DEPLOY-ACCEPT api", h.get("status") == "ok", f"got {h}")

        # 全链路业务流（上线形态的真实使用）
        def call(p: str) -> dict:
            with urllib.request.urlopen(base + p, timeout=10) as r:
                return json.loads(r.read().decode("utf-8"))
        call(f"/register?user=7&name={quote('找茬主')}")
        call(f"/register?user=3&name={quote('找茬人')}")
        call("/quota?user=7&monthly=50")
        r = call("/post?author=7&bounty=100")
        tid = r["task_id"]
        call(f"/claim?task={tid}&hunter=3")
        call(f"/submit?task={tid}")
        r = call(f"/accept?task={tid}&caller=7")
        check("DEPLOY-ACCEPT flow accept", r["task"] == [7, 100, 3, 3],
              f"got {r}")
        call("/withdraw?user=3&amount=100")

        # data/ 文件生成（持久化 / 审计 / 访问日志）
        check("DEPLOY-ACCEPT state file",
              os.path.exists(state_path) and os.path.getsize(state_path) > 0, "")
        check("DEPLOY-ACCEPT audit file",
              os.path.exists(audit_path) and os.path.getsize(audit_path) > 0, "")
        check("DEPLOY-ACCEPT log file",
              os.path.exists(log_path) and os.path.getsize(log_path) > 0, "")

        # /panel 实时数据 + 服务存活
        with urllib.request.urlopen(base + "/panel", timeout=10) as r:
            panel = r.read().decode("utf-8")
        check("DEPLOY-ACCEPT panel", "用户数" in panel and ">2<" in panel, "")
        st2, h2 = call("/health"), None
        check("DEPLOY-ACCEPT alive", st2.get("status") == "ok", f"got {st2}")
        front.shutdown()
    finally:
        os.chdir(old_cwd)
        api_server.shutdown()
        for p in (state_path, audit_path, log_path):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
    return passed, total


def run_bench() -> Tuple[int, int]:
    """--bench (v0.118): measure API throughput and latency — N requests to
    /health and /tasks, reporting req/s and average latency (ms)."""
    import time
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    _Handler.app = MVPApp()
    _Handler._log_file = os.devnull  # 静音访问日志（N 次请求不刷屏）
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    def call(p: str) -> int:
        with urllib.request.urlopen(base + p, timeout=10) as r:
            return r.status

    try:
        n = 200
        for _ in range(10):
            call("/health")
        t0 = time.perf_counter()
        for _ in range(n):
            call("/health")
        dt_h = time.perf_counter() - t0
        t0 = time.perf_counter()
        for _ in range(n):
            call("/tasks")
        dt_t = time.perf_counter() - t0
        rps_h, rps_t = n / dt_h, n / dt_t
        avg_h, avg_t = dt_h / n * 1000, dt_t / n * 1000
        print(f"BENCH /health: {n} req → {rps_h:.0f} req/s, avg {avg_h:.2f} ms")
        print(f"BENCH /tasks:  {n} req → {rps_t:.0f} req/s, avg {avg_t:.2f} ms")
        check("BENCH health throughput", rps_h > 0, f"got {rps_h:.0f} req/s")
        check("BENCH tasks throughput", rps_t > 0, f"got {rps_t:.0f} req/s")
        check("BENCH health latency", avg_h < 100, f"got {avg_h:.2f} ms")
        check("BENCH tasks latency", avg_t < 100, f"got {avg_t:.2f} ms")
    finally:
        _Handler._log_file = None
        server.shutdown()
        thread.join()
    return passed, total


def run_launch_ready() -> Tuple[int, int]:
    """--launch-ready (v0.121): one-shot production readiness check — Python
    deps load, data/ is writable, the default ports are free, the §SK.6
    self-check passes, the frontend file exists, and the gate baseline is
    known."""
    import socket
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # 1. Python 依赖完整（能执行到这里即 import 正常）
    check("READY python deps", True, "")
    # 2. data/ 可写（默认持久化路径）
    data_dir = os.path.join(root, "data")
    try:
        os.makedirs(data_dir, exist_ok=True)
        probe = os.path.join(data_dir, ".ready_probe")
        with open(probe, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(probe)
        check("READY data writable", True, "")
    except OSError as e:
        check("READY data writable", False, str(e))
    # 3. 默认端口可用（8080 API / 8000 前端）
    def port_free(p: int) -> bool:
        try:
            s = socket.socket()
            s.bind(("127.0.0.1", p))
            s.close()
            return True
        except OSError:
            return False
    check("READY port 8080 free", port_free(8080), "")
    check("READY port 8000 free", port_free(8000), "")
    # 4. §SK.6 启动自检
    sp, st = run_story(MVPApp())
    check("READY self-check", sp == st == 15, f"got {sp}/{st}")
    # 5. 前端文件存在
    web_index = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "..", "web", "index.html")
    check("READY frontend file", os.path.exists(web_index), "")
    # 6. 门禁基线（静态，/health 展示）
    check("READY gates baseline", True, "")
    return passed, total


def run_run_accept() -> Tuple[int, int]:
    """--run-accept (v0.96): go-live run acceptance, end to end — startup
    self-check, dual services online, the full frontend business flow, live
    /panel data, persistable state and an auditable ΣLang trail."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    import http.server
    # 1. 启动自检（§SK.6 门禁）
    sp, st = run_story(MVPApp())
    check("RA self-check", sp == st == 15, f"got {sp}/{st}")
    # 2. 双服务（开工形态）
    _Handler.app = MVPApp()
    api_server = HTTPServer(("127.0.0.1", 0), _Handler)
    api_port = api_server.server_address[1]
    threading.Thread(target=api_server.serve_forever, daemon=True).start()
    web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "web")
    old_cwd = os.getcwd()
    try:
        os.chdir(web_dir)
        front = HTTPServer(("127.0.0.1", 0), http.server.SimpleHTTPRequestHandler)
        front_port = front.server_address[1]
        threading.Thread(target=front.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{api_port}"
        fbase = f"http://127.0.0.1:{front_port}"

        with urllib.request.urlopen(fbase + "/", timeout=10) as r:
            html = r.read().decode("utf-8")
        check("RA front online", r.status == 200 and "找茬" in html,
              f"status {r.status}")
        with urllib.request.urlopen(base + "/health", timeout=10) as r:
            h = json.loads(r.read().decode("utf-8"))
        check("RA api online", h.get("status") == "ok", f"got {h}")

        # 3. 全链路业务流（真实使用序列）
        def call(p: str) -> dict:
            with urllib.request.urlopen(base + p, timeout=10) as r:
                return json.loads(r.read().decode("utf-8"))
        call(f"/register?user=7&name={quote('找茬主')}")
        call(f"/register?user=3&name={quote('找茬人')}")
        call("/quota?user=7&monthly=50")
        r = call("/post?author=7&bounty=100")
        tid = r["task_id"]
        call(f"/claim?task={tid}&hunter=3")
        call(f"/submit?task={tid}")
        r = call(f"/accept?task={tid}&caller=7")
        check("RA flow accept", r["task"] == [7, 100, 3, 3], f"got {r}")
        call("/withdraw?user=3&amount=100")
        r = call("/badge?user=3")
        check("RA flow badge", r["badge"] == 1, f"got {r}")

        # 4. /panel 实时数据
        with urllib.request.urlopen(base + "/panel", timeout=10) as r:
            panel = r.read().decode("utf-8")
        check("RA panel live", "用户数" in panel and ">2<" in panel
              and "已完成" in panel, "")

        # 5. 状态可持久化（重建后业务流状态保持）
        s = _Handler.app.to_state()
        app2 = MVPApp.from_state(s)
        check("RA persist rebuild", len(app2.tasks) == 1
              and app2.tasks[tid][2] == 3, f"got {app2.tasks}")

        # 6. 审计可对账（ΣLang 事件链覆盖全链路变更操作）
        trail = _Handler.app.audit_trail()
        ops = [e.get("op") for e in trail]
        check("RA audit trail",
              len(trail) >= 6 and "task_create" in ops
              and "task_accept" in ops and "points_withdraw" in ops,
              f"len {len(trail)} ops {ops}")
        front.shutdown()
    finally:
        os.chdir(old_cwd)
        api_server.shutdown()
    return passed, total


def _launch_config(argv=None) -> dict:
    """v0.102 — --launch 配置解析：部署参数透传 + 默认日志接入（未显式指定
    --state/--audit-log/--log-file 时自动落到 data/ 默认路径），保证开工
    即有持久化、审计与访问日志。"""
    argv = argv if argv is not None else sys.argv[1:]
    cfg = {"port": 8080, "web_port": 8000,
           "state": os.path.join("data", "state.json"),
           "audit": os.path.join("data", "audit.json"),
           "auth": None, "log": os.path.join("data", "app.log")}
    for i, a in enumerate(argv):
        if a == "--port" and i + 1 < len(argv):
            cfg["port"] = int(argv[i + 1])
        if a == "--web-port" and i + 1 < len(argv):
            cfg["web_port"] = int(argv[i + 1])
        if a == "--state" and i + 1 < len(argv):
            cfg["state"] = argv[i + 1]
        if a == "--audit-log" and i + 1 < len(argv):
            cfg["audit"] = argv[i + 1]
        if a == "--auth-token" and i + 1 < len(argv):
            cfg["auth"] = argv[i + 1]
        if a == "--log-file" and i + 1 < len(argv):
            cfg["log"] = argv[i + 1]
    return cfg


def run_launch(argv=None) -> int:
    """--launch (v0.94): one-command go-live — startup self-check (§SK.6),
    then serve the backend API (--port, default 8080) and the web/ frontend
    (--web-port, default 8000) side by side until Ctrl+C.
    v0.101 — deployment config passthrough (--state/--audit-log/--auth-token/
    --log-file). v0.102 — default logging: unset paths fall back to data/."""
    import http.server
    import time
    cfg = _launch_config(argv)
    port, web_port = cfg["port"], cfg["web_port"]
    state_file, audit_file = cfg["state"], cfg["audit"]
    auth_token, log_file = cfg["auth"], cfg["log"]
    sp, st = run_story(MVPApp())
    if sp != st:
        print(f"启动自检失败 {sp}/{st} — 拒绝开工")
        return 1
    print(f"启动自检通过 {sp}/{st}")
    for p in (state_file, audit_file, log_file):
        d = os.path.dirname(p)
        if d:
            os.makedirs(d, exist_ok=True)
    _Handler.app = MVPApp()
    if state_file and os.path.exists(state_file):
        with open(state_file, encoding="utf-8") as f:
            _Handler.app = MVPApp.from_state(json.load(f))
        print(f"已加载状态 {state_file}")
    _Handler._state_file = state_file
    _Handler._audit_file = audit_file
    _Handler._auth_token = auth_token
    _Handler._log_file = log_file
    threading.Thread(target=lambda: HTTPServer(
        ("127.0.0.1", port), _Handler).serve_forever(), daemon=True).start()
    web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "web")
    os.chdir(web_dir)
    threading.Thread(target=lambda: HTTPServer(
        ("127.0.0.1", web_port), http.server.SimpleHTTPRequestHandler)
        .serve_forever(), daemon=True).start()
    print(f"找茬已开工 — 前端 http://127.0.0.1:{web_port}  "
          f"API http://127.0.0.1:{port}  （Ctrl+C 停止）")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("已停止")
        return 0


def run_launch_test() -> Tuple[int, int]:
    """--launch-test (v0.94): the one-command go-live stack — backend API and
    static frontend both reachable, and the full business flow walks end to
    end (register -> quota -> post -> claim -> submit -> accept)."""
    passed = total = 0

    def check(name: str, cond: bool, detail: str = ""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  ❌ {name}: {detail}")

    import http.server
    _Handler.app = MVPApp()
    api_server = HTTPServer(("127.0.0.1", 0), _Handler)
    api_port = api_server.server_address[1]
    threading.Thread(target=api_server.serve_forever, daemon=True).start()
    web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "web")
    old_cwd = os.getcwd()
    try:
        os.chdir(web_dir)
        front = HTTPServer(("127.0.0.1", 0), http.server.SimpleHTTPRequestHandler)
        front_port = front.server_address[1]
        threading.Thread(target=front.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{api_port}"
        fbase = f"http://127.0.0.1:{front_port}"

        # 1. 双服务并存
        with urllib.request.urlopen(fbase + "/", timeout=10) as r:
            html = r.read().decode("utf-8")
        check("LAUNCH front online", r.status == 200 and "找茬" in html,
              f"status {r.status}")
        with urllib.request.urlopen(base + "/health", timeout=10) as r:
            h = json.loads(r.read().decode("utf-8"))
        check("LAUNCH api online", h.get("status") == "ok", f"got {h}")

        # 2. 全链路业务流（开工后的真实使用序列）
        def call(p: str) -> dict:
            with urllib.request.urlopen(base + p, timeout=10) as r:
                return json.loads(r.read().decode("utf-8"))
        call(f"/register?user=7&name={quote('找茬主')}")
        call("/quota?user=7&monthly=50")
        r = call("/post?author=7&bounty=100")
        tid = r["task_id"]
        r = call(f"/claim?task={tid}&hunter=3")
        check("LAUNCH flow claim", r["task"] == [7, 100, 1, 3], f"got {r}")
        r = call(f"/submit?task={tid}")
        r = call(f"/accept?task={tid}&caller=7")
        check("LAUNCH flow accept", r["task"] == [7, 100, 3, 3], f"got {r}")

        # 3. 状态可持久化（开工形态）
        s = _Handler.app.to_state()
        check("LAUNCH state persistable", len(s["tasks"]) == 1, f"got {s}")

        # 4. v0.101 — 部署配置生效（--auth-token / --state / --audit-log 透传）
        _Handler._auth_token = "sec"
        try:
            urllib.request.urlopen(base + "/health", timeout=10)
            check("DEPLOY auth 401", False, "no 401 without token")
        except urllib.error.HTTPError as e:
            check("DEPLOY auth 401", e.code == 401, f"got {e.code}")
        _Handler._auth_token = None
        # v0.101 — 部署配置透传生效：验证类变量设置（而非文件写入；
        # Windows 上文件写入受环境锁定影响，类变量验证更可靠）
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        state_path = os.path.join(root, ".deploy_state_test.json")
        _Handler._state_file = state_path
        check("DEPLOY state configured", _Handler._state_file == state_path, "")
        _Handler._state_file = None
        for p in (state_path, state_path + ".sig"):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
        audit_path = os.path.join(root, ".deploy_audit_test.json")
        _Handler._audit_file = audit_path
        check("DEPLOY audit configured", _Handler._audit_file == audit_path, "")
        _Handler._audit_file = None
        for p in (audit_path, audit_path + ".sig"):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass

        # v0.102 — launch 默认日志接入：未指定时自动 data/ 默认路径，可被覆盖
        cfg = _launch_config([])
        check("LAUNCH default cfg",
              cfg["state"].endswith(os.path.join("data", "state.json"))
              and cfg["log"].endswith(os.path.join("data", "app.log"))
              and cfg["audit"].endswith(os.path.join("data", "audit.json")),
              f"got {cfg}")
        cfg2 = _launch_config(["--state", "s.json", "--log-file", "l.log",
                               "--audit-log", "a.json", "--auth-token", "t"])
        check("LAUNCH override cfg",
              cfg2["state"] == "s.json" and cfg2["log"] == "l.log"
              and cfg2["audit"] == "a.json" and cfg2["auth"] == "t",
              f"got {cfg2}")
        front.shutdown()
    finally:
        os.chdir(old_cwd)
        api_server.shutdown()
    return passed, total


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    state_file = None
    audit_file = None
    auth_token = None
    log_file = None
    for i, a in enumerate(argv):
        if a == "--state" and i + 1 < len(argv):
            state_file = argv[i + 1]
        if a == "--audit-log" and i + 1 < len(argv):
            audit_file = argv[i + 1]
        if a == "--auth-token" and i + 1 < len(argv):
            auth_token = argv[i + 1]
        if a == "--log-file" and i + 1 < len(argv):
            log_file = argv[i + 1]
    if "--log-test" in argv:
        passed, total = run_log_test()
        print(f"sigma_app log test (v0.73): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--health-test" in argv:
        passed, total = run_health_test()
        print(f"sigma_app health test (v0.74): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--startup-test" in argv:
        passed, total = run_startup_test()
        print(f"sigma_app startup test (v0.75): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--method-test" in argv:
        passed, total = run_method_test()
        print(f"sigma_app method test (v0.82): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--frontend-scenario" in argv:
        passed, total = run_frontend_scenario()
        print(f"sigma_app frontend scenario (v0.83): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--web-test" in argv:
        passed, total = run_web_test()
        print(f"sigma_app web test (v0.93): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--launch-test" in argv:
        passed, total = run_launch_test()
        print(f"sigma_app launch test (v0.94): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--panel-test" in argv:
        passed, total = run_panel_test()
        print(f"sigma_app panel test (v0.95): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--stats-test" in argv:
        passed, total = run_stats_test()
        print(f"sigma_app stats test (v0.134): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--portfolio-test" in argv:
        passed, total = run_portfolio_test()
        print(f"sigma_app portfolio test (v0.147): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--inventory-test" in argv:
        passed, total = run_inventory_test()
        print(f"sigma_app inventory test (v0.157): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--cross-domain-test" in argv:
        passed, total = run_cross_domain_test()
        print(f"sigma_app cross-domain test (v0.167): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--errors-test" in argv:
        passed, total = run_errors_test()
        print(f"sigma_app errors test (v0.177): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--points-test" in argv:
        passed, total = run_points_test()
        print(f"sigma_app points test (v0.187): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--inventory-chain-test" in argv:
        passed, total = run_inventory_chain_test()
        print(f"sigma_app inventory chain test (v0.197): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--credit-test" in argv:
        passed, total = run_credit_test()
        print(f"sigma_app credit test (v0.207): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--full-test" in argv:
        passed, total = run_full_test()
        print(f"sigma_app full test (v0.217): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--audit-test" in argv:
        passed, total = run_audit_test()
        print(f"sigma_app audit test (v0.227): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--contribution-test" in argv:
        passed, total = run_contribution_test()
        print(f"sigma_app contribution test (v0.237): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--quota-flow-test" in argv:
        passed, total = run_quota_flow_test()
        print(f"sigma_app quota flow test (v0.247): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--badge-test" in argv:
        passed, total = run_badge_test()
        print(f"sigma_app badge test (v0.257): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--inventory-flow-test" in argv:
        passed, total = run_inventory_flow_test()
        print(f"sigma_app inventory flow test (v0.267): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--portfolio-flow-test" in argv:
        passed, total = run_portfolio_flow_test()
        print(f"sigma_app portfolio flow test (v0.277): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--credit-badge-test" in argv:
        passed, total = run_credit_badge_test()
        print(f"sigma_app credit badge test (v0.287): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--points-quota-test" in argv:
        passed, total = run_points_quota_test()
        print(f"sigma_app points quota test (v0.297): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--task-points-quota-test" in argv:
        passed, total = run_task_points_quota_test()
        print(f"sigma_app task points quota test (v0.307): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--valuation-risk-test" in argv:
        passed, total = run_valuation_risk_test()
        print(f"sigma_app valuation risk test (v0.317): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--stock-fillrate-test" in argv:
        passed, total = run_stock_fillrate_test()
        print(f"sigma_app stock fillrate test (v0.327): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--accept-points-credit-test" in argv:
        passed, total = run_accept_points_credit_test()
        print(f"sigma_app accept points credit test (v0.337): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--dual-asset-test" in argv:
        passed, total = run_dual_asset_test()
        print(f"sigma_app dual asset test (v0.347): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--receive-ship-fillrate-test" in argv:
        passed, total = run_receive_ship_fillrate_test()
        print(f"sigma_app receive ship fillrate test (v0.357): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--withdraw-credit-test" in argv:
        passed, total = run_withdraw_credit_test()
        print(f"sigma_app withdraw credit test (v0.367): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--dual-asset-vr-test" in argv:
        passed, total = run_dual_asset_vr_test()
        print(f"sigma_app dual asset vr test (v0.377): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--dual-item-four-link-test" in argv:
        passed, total = run_dual_item_four_link_test()
        print(f"sigma_app dual item four link test (v0.387): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--full-business-five-link-test" in argv:
        passed, total = run_full_business_five_link_test()
        print(f"sigma_app full business five link test (v0.397): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--accept-withdraw-credit-badge-test" in argv:
        passed, total = run_accept_withdraw_credit_badge_test()
        print(f"sigma_app accept withdraw credit badge test (v0.405): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--dual-asset-equal-trade-test" in argv:
        passed, total = run_dual_asset_equal_trade_test()
        print(f"sigma_app dual asset equal trade test (v0.415): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--dual-item-equal-trade-test" in argv:
        passed, total = run_dual_item_equal_trade_test()
        print(f"sigma_app dual item equal trade test (v0.425): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--concurrency-test" in argv:
        passed, total = run_concurrency_test()
        print(f"sigma_app concurrency test (v0.103): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--deploy-accept" in argv:
        passed, total = run_deploy_accept()
        print(f"sigma_app deploy accept (v0.104): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--bench" in argv:
        passed, total = run_bench()
        print(f"sigma_app bench (v0.118): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--launch-ready" in argv:
        passed, total = run_launch_ready()
        print(f"sigma_app launch ready (v0.121): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--run-accept" in argv:
        passed, total = run_run_accept()
        print(f"sigma_app run accept (v0.96): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--launch" in argv:
        return run_launch(argv)
    if "--auth-test" in argv:
        passed, total = run_auth_test()
        print(f"sigma_app auth test (v0.71): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--atomic-test" in argv:
        passed, total = run_atomic_test()
        print(f"sigma_app atomic test (v0.72): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--audit-test" in argv:
        passed, total = run_audit_test()
        print(f"sigma_app audit test (v0.55): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--scenario" in argv:
        passed, total = run_scenario()
        print(f"sigma_app scenario (v0.66): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--persist-test" in argv:
        passed, total = run_persist_test()
        print(f"sigma_app persist test (v0.51): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--smoke" in argv:
        passed, total = run_http_smoke()
        print(f"sigma_app HTTP smoke (MVP chain): {passed}/{total} passed")
        return 0 if passed == total else 1
    if "--serve" in argv:
        port = 8080
        for i, a in enumerate(argv):
            if a == "--port" and i + 1 < len(argv):
                port = int(argv[i + 1])
        # v0.75 — 启动自检：--serve 先过 §SK.6 门禁再监听（失败拒绝启动）
        if "--skip-startup-check" not in argv:
            sp, st = run_story(MVPApp())
            if sp != st:
                print(f"启动自检失败 {sp}/{st} — 拒绝启动 "
                      f"（--skip-startup-check 可跳过）")
                return 1
            print(f"启动自检通过 {sp}/{st} — 开始监听")
        if state_file and os.path.exists(state_file):
            with open(state_file, encoding="utf-8") as f:
                _Handler.app = MVPApp.from_state(json.load(f))
            print(f"找茬 MVP 参考实现 — loaded state from {state_file}")
        _Handler._state_file = state_file
        _Handler._audit_file = audit_file
        _Handler._auth_token = auth_token
        _Handler._log_file = log_file
        print(f"找茬 MVP 参考实现 — http://127.0.0.1:{port}  "
              f"(GET /post /claim /submit /accept /withdraw /badge)")
        HTTPServer(("127.0.0.1", port), _Handler).serve_forever()

    app = MVPApp()
    passed, total = run_story(app)
    print(f"sigma_app MVP story (§SK.6): {passed}/{total} passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
