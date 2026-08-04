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
from urllib.parse import unquote

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
        return app

    # --- §SK.6.1 开户额度 ---------------------------------------------------
    def open_quota(self, user: int, monthly: int) -> List[int]:
        """Open a monthly quota for a user (delegates quota_new)."""
        q = core.quota_new(monthly)
        self.quotas[user] = q
        return q

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
        return (tid, task, quota, self.points)

    # --- §SK.6.5 接单 --------------------------------------------------------
    def claim_task(self, task_id: int, hunter: int) -> List[int]:
        task = core.accept_task(self.tasks[task_id], hunter)
        self.tasks[task_id] = task
        return task

    # --- §SK.6.6 提交成果 ----------------------------------------------------
    def submit_work(self, task_id: int) -> List[int]:
        task = core.task_submit(self.tasks[task_id])
        self.tasks[task_id] = task
        return task

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
        return (task, self.points, credit, contribution)

    # --- §SK.6.9 提现 --------------------------------------------------------
    def withdraw(self, user: int, amount: int) -> List[int]:
        self.points = core.points_withdraw(self.points, amount)
        return self.points

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

    def _json(self, obj, code: int = 200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
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

    def _save_state(self):
        """v0.51 — persist the whole App state after every request (--state)."""
        if _Handler._state_file:
            with open(_Handler._state_file, "w", encoding="utf-8") as f:
                json.dump(_Handler.app.to_state(), f, ensure_ascii=False)

    def do_GET(self):
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
            return self._json({"error": "unknown path"}, 404)
        except (ValueError, KeyError) as e:
            # v0.54 — 语义化错误码：§SK/§IN 错误 → 语义化 HTTP 状态码
            msg = str(e)
            status = ERROR_STATUS.get(msg, DEFAULT_ERROR_STATUS)
            return self._json({"error": msg}, status)
        finally:
            # v0.51 — persist after every request (--state FILE)
            self._save_state()

    def log_message(self, fmt, *args):
        sys.stderr.write(f"[sigma-app] {fmt % args}\n")


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


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    state_file = None
    for i, a in enumerate(argv):
        if a == "--state" and i + 1 < len(argv):
            state_file = argv[i + 1]
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
        if state_file and os.path.exists(state_file):
            with open(state_file, encoding="utf-8") as f:
                _Handler.app = MVPApp.from_state(json.load(f))
            print(f"找茬 MVP 参考实现 — loaded state from {state_file}")
        _Handler._state_file = state_file
        print(f"找茬 MVP 参考实现 — http://127.0.0.1:{port}  "
              f"(GET /post /claim /submit /accept /withdraw /badge)")
        HTTPServer(("127.0.0.1", port), _Handler).serve_forever()

    app = MVPApp()
    passed, total = run_story(app)
    print(f"sigma_app MVP story (§SK.6): {passed}/{total} passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
