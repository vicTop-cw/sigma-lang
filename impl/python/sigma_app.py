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
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, __file__ and __file__.rsplit("/", 1)[0] or ".")
import sigma_core as core


class MVPApp:
    """In-memory MVP backend. Business values come ONLY from sigma_core §SK."""

    def __init__(self) -> None:
        self._next_task = 0
        self.tasks: Dict[int, List[int]] = {}              # task_id -> Task
        self.quotas: Dict[int, List[int]] = {}             # user -> Quota
        self.points: List[int] = core.points_new()         # platform escrow/available
        self.credit_events: Dict[int, List[List[int]]] = {}   # user -> credit events
        self.contribution_actions: Dict[int, List[List[int]]] = {}  # user -> actions

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

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        app = _Handler.app
        try:
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
            return self._json({"error": "unknown path"}, 404)
        except (ValueError, KeyError) as e:
            return self._json({"error": str(e)}, 400)

    def log_message(self, fmt, *args):
        sys.stderr.write(f"[sigma-app] {fmt % args}\n")


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if "--serve" in argv:
        port = 8080
        for i, a in enumerate(argv):
            if a == "--port" and i + 1 < len(argv):
                port = int(argv[i + 1])
        print(f"找茬 MVP 参考实现 — http://127.0.0.1:{port}  "
              f"(GET /post /claim /submit /accept /withdraw /badge)")
        HTTPServer(("127.0.0.1", port), _Handler).serve_forever()

    app = MVPApp()
    passed, total = run_story(app)
    print(f"sigma_app MVP story (§SK.6): {passed}/{total} passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
