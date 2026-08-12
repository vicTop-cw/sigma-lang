# -*- coding: utf-8 -*-
"""
ΣLang §SK 协议独立实现 —— deepseek-v4-flash
============================================
实现方式：通读 spec/spec_p0_socketkit.json（顶层 constants / types / operations，
22 个操作、60 条测试）后直接实现，未参考仓库内任何已有实现。

约定（与 TASK_SPEC.md 三、实现规则一致）：
  * 列表参数收到非列表 -> ValueError("TypeError")
  * index 越界             -> ValueError("ShapeError")
  * 业务错误按各操作 preconditions 的 error 字段命名
  * 顶层 constants 的数值必须使用，不得自行另设（§3.6）
"""

import json
import os

# ---------------------------------------------------------------------------
# 顶层 constants（v0.31 新增，直接取自规格，禁止另设魔法常量）
# ---------------------------------------------------------------------------
_SPEC_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "spec", "spec_p0_socketkit.json"
)

with open(_SPEC_PATH, encoding="utf-8") as _f:
    _SPEC = json.load(_f)

C = _SPEC["constants"]

STATUS = C["status"]                     # open=0 / in_progress=1 / pending_review=2 / completed=3
DECISION = C["decision"]                 # reject=0 / accept=1
BADGE_LEVELS = C["badge"]["levels"]      # bronze=0 / silver=1 / gold=2 / diamond=3
BADGE_THRESHOLDS = C["badge"]["thresholds"]   # [100, 300, 600]
VERIFIER_MIN_ID = C["verifier_min_id"]   # 1000
CREDIT_INITIAL = C["credit"]["initial"]  # 100
CREDIT_KIND0 = C["credit"]["kind0_per_completion"]        # 5
CREDIT_KIND1_NUM = C["credit"]["kind1_floor_ratio"]["num"]  # 7
CREDIT_KIND1_DEN = C["credit"]["kind1_floor_ratio"]["den"]  # 10
CREDIT_FLOOR = C["credit"]["floor"]      # 0
CONTRIBUTION_FLOOR = C["contribution"]["floor"]  # 0
TEAM_MIN_CAPACITY = C["team"]["min_capacity"]    # 1
LEDGER_ENTRY_ID_START = C["ledger"]["entry_id_start"]    # 1
LEDGER_MIN_SOURCE_ID = C["ledger"]["min_source_id"]      # 1

OPEN = STATUS["open"]
IN_PROGRESS = STATUS["in_progress"]
PENDING_REVIEW = STATUS["pending_review"]
COMPLETED = STATUS["completed"]
REJECT = DECISION["reject"]
ACCEPT = DECISION["accept"]
BRONZE, SILVER, GOLD, DIAMOND = (BADGE_LEVELS["bronze"], BADGE_LEVELS["silver"],
                                 BADGE_LEVELS["gold"], BADGE_LEVELS["diamond"])

# ---------------------------------------------------------------------------
# 内置函数（definition 中 {"fn": ...} 的语义，见 TASK_SPEC §3.4）
# ---------------------------------------------------------------------------

def _index(coll, i):
    """取列表第 i 个元素；越界抛 ShapeError；非列表/非整数抛 TypeError。"""
    if not isinstance(coll, list) or not isinstance(i, int) or isinstance(i, bool):
        raise ValueError("TypeError")
    if i < 0 or i >= len(coll):
        raise ValueError("ShapeError")
    return coll[i]


def _minmax(kind, *args):
    """min/max 重载：单列表参数 -> 取该列表的最值；多参数 -> 取所有参数的最值。"""
    if len(args) == 1 and isinstance(args[0], list):
        vals = args[0]
    else:
        vals = list(args)
    return min(vals) if kind == "min" else max(vals)


def _add(*xs):
    return sum(xs)


def _sub(*xs):
    acc = xs[0]
    for x in xs[1:]:
        acc -= x
    return acc


def _ge(a, b):
    return a >= b


def _lt(a, b):
    return a < b


def _eq(a, b):
    return a == b


def _fold_add(xs):
    """列表的列表 -> 每行最后一个元素求和；否则普通求和。"""
    if not isinstance(xs, list):
        raise ValueError("TypeError")
    if xs and all(isinstance(x, list) for x in xs):
        return sum(row[-1] for row in xs)
    return sum(xs)


def _fold_credit(init, events):
    """契分折叠：kind=0 -> +5*count；kind=1 -> 逐次 *7//10；结果下限 0。"""
    if not isinstance(events, list):
        raise ValueError("TypeError")
    s = init
    for ev in events:
        kind, count = ev[0], ev[1]
        if kind == 0:
            s += CREDIT_KIND0 * count
        else:  # kind == 1：逐次向下取整
            for _ in range(count):
                s = s * CREDIT_KIND1_NUM // CREDIT_KIND1_DEN
    if s < CREDIT_FLOOR:
        s = CREDIT_FLOOR
    return s


def _weighted_accept(xs):
    """[reviewer, vote, weight] 行中 vote==1 的 weight 之和（accept/support 同语义）。"""
    return sum(row[2] for row in xs if row[1] == 1)


def _weighted_reject(xs):
    """vote==0 的 weight 之和。"""
    return sum(row[2] for row in xs if row[1] == 0)


def _split_floor(contribs, reward):
    """按贡献分账：share = floor(reward * c / total)；total==0 抛 DivByZero。"""
    total = sum(row[1] for row in contribs)
    if total == 0:
        raise ValueError("DivByZero")
    return [[row[0], (reward * row[1]) // total] for row in contribs]


def _enumerate_ledger(entries):
    """[[旧id, 金额, source], ...] -> [[新编号(1..n), source, 金额], ...]。
    source < 1 抛 NotTraceable；金额 < 0 抛 TypeError。"""
    out = []
    for i, row in enumerate(entries, start=LEDGER_ENTRY_ID_START):
        _old_id, amount, source = row[0], row[1], row[2]
        if source < LEDGER_MIN_SOURCE_ID:
            raise ValueError("NotTraceable")
        if amount < 0:
            raise ValueError("TypeError")
        out.append([i, source, amount])
    return out


# preconditions 表达式辅助函数（白名单中的 sum_contribs / min_source_id）
def _sum_contribs(c):
    """c 的每行第 2 列（贡献）之和。"""
    return sum(row[1] for row in c)


def _min_source_id(e):
    """e 的每行第 3 列（source）最小值；空列表返回 +∞。"""
    if not e:
        return float("inf")
    return min(row[2] for row in e)


# ---------------------------------------------------------------------------
# 22 个操作（0xF001..0xF016）
# ---------------------------------------------------------------------------

def task_create(a, b):
    """0xF001: [author, bounty, open, unclaimed]；bounty < 0 -> BountyErr。"""
    if b < 0:
        raise ValueError("BountyErr")
    return [a, b, OPEN, OPEN]


def review_merge(os_):
    """0xF002: weighted_accept >= weighted_reject -> accept(1) else reject(0)。"""
    if not isinstance(os_, list):
        raise ValueError("TypeError")
    return ACCEPT if _weighted_accept(os_) >= _weighted_reject(os_) else REJECT


def contribution_score(a):
    """0xF003: max(0, fold_add(a))。"""
    if not isinstance(a, list):
        raise ValueError("TypeError")
    return max(CONTRIBUTION_FLOOR, _fold_add(a))


def accept_task(t, h):
    """0xF004: 接单；须 open(0)；-> [author, bounty, in_progress, hunter]。"""
    if not isinstance(t, list):
        raise ValueError("TypeError")
    if _index(t, 2) != OPEN:
        raise ValueError("StateError")
    return [t[0], t[1], IN_PROGRESS, h]


def task_submit(t):
    """0xF005: 提交；须 in_progress(1)；-> [author, bounty, pending_review, hunter]。"""
    if not isinstance(t, list):
        raise ValueError("TypeError")
    if _index(t, 2) != IN_PROGRESS:
        raise ValueError("StateError")
    return [t[0], t[1], PENDING_REVIEW, t[3]]


def task_accept(t, c):
    """0xF006: 验收；须 pending_review(2) 且 c == 作者；-> completed。"""
    if not isinstance(t, list):
        raise ValueError("TypeError")
    if _index(t, 2) != PENDING_REVIEW:
        raise ValueError("StateError")
    if c != t[0]:
        raise ValueError("AuthError")
    return [t[0], t[1], COMPLETED, t[3]]


def credit_score(e):
    """0xF007: fold_credit(100, e)。"""
    if not isinstance(e, list):
        raise ValueError("TypeError")
    return _fold_credit(CREDIT_INITIAL, e)


def quota_new(m):
    """0xF008: [limit, remaining] = [m, m]。"""
    return [m, m]


def quota_use(q, a):
    """0xF009: 消耗额度；a > remaining -> QuotaExhausted。"""
    if not isinstance(q, list):
        raise ValueError("TypeError")
    if a > q[1]:
        raise ValueError("QuotaExhausted")
    return [q[0], q[1] - a]


def quota_reset(q):
    """0xF00A: 月末重置 -> [limit, limit]。"""
    if not isinstance(q, list):
        raise ValueError("TypeError")
    return [q[0], q[0]]


def points_new():
    """0xF00B: [escrow, available] = [0, 0]。"""
    return [0, 0]


def points_hold(p, x):
    """0xF00C: 冻结 x 进托管 -> [escrow+x, available]。"""
    if not isinstance(p, list):
        raise ValueError("TypeError")
    return [p[0] + x, p[1]]


def points_release(p, x):
    """0xF00D: 释放托管；x > escrow -> InsufficientEscrow。"""
    if not isinstance(p, list):
        raise ValueError("TypeError")
    if x > p[0]:
        raise ValueError("InsufficientEscrow")
    return [p[0] - x, p[1] + x]


def points_withdraw(p, x):
    """0xF00E: 提现；x > available -> InsufficientPoints。"""
    if not isinstance(p, list):
        raise ValueError("TypeError")
    if x > p[1]:
        raise ValueError("InsufficientPoints")
    return [p[0], p[1] - x]


def badge_level(s):
    """0xF00F: 档位 0/1/2/3 = <100 / <300 / <600 / else。"""
    t = BADGE_THRESHOLDS
    if s < t[0]:
        return BRONZE
    if s < t[1]:
        return SILVER
    if s < t[2]:
        return GOLD
    return DIAMOND


def badge_issue(v, u, s):
    """0xF010: 核验师 v >= 1000 发徽章 -> [v, u, badge_level(s)]。"""
    if v < VERIFIER_MIN_ID:
        raise ValueError("AuthError")
    return [v, u, badge_level(s)]


def dispute_review(e):
    """0xF011: weighted_support >= weighted_reject -> accept(1) else reject(0)。"""
    if not isinstance(e, list):
        raise ValueError("TypeError")
    return ACCEPT if _weighted_accept(e) >= _weighted_reject(e) else REJECT


def team_create(o, k, c):
    """0xF012: [owner, kind, size=1, capacity]；capacity < 1 -> TypeError。"""
    if c < TEAM_MIN_CAPACITY:
        raise ValueError("TypeError")
    return [o, k, 1, c]


def team_join(t, m):
    """0xF013: 入队；size >= capacity -> TeamFull。"""
    if not isinstance(t, list):
        raise ValueError("TypeError")
    if t[2] >= t[3]:
        raise ValueError("TeamFull")
    return [t[0], t[1], t[2] + 1, t[3]]


def team_share(c, r):
    """0xF014: split_floor(c, r)；总贡献 <= 0 -> DivByZero。"""
    if not isinstance(c, list):
        raise ValueError("TypeError")
    if _sum_contribs(c) <= 0:
        raise ValueError("DivByZero")
    return _split_floor(c, r)


def quota_advance(q):
    """0xF015: 预支一个整月额度 -> [limit, remaining+limit]。"""
    if not isinstance(q, list):
        raise ValueError("TypeError")
    return [q[0], q[1] + q[0]]


def points_ledger(e):
    """0xF016: 账本重编号 -> [[1, source, amount], ...]；source < 1 -> NotTraceable。"""
    if not isinstance(e, list):
        raise ValueError("TypeError")
    if _min_source_id(e) < LEDGER_MIN_SOURCE_ID:
        raise ValueError("NotTraceable")
    return _enumerate_ledger(e)


OPS = {
    "task_create": task_create,
    "review_merge": review_merge,
    "contribution_score": contribution_score,
    "accept_task": accept_task,
    "task_submit": task_submit,
    "task_accept": task_accept,
    "credit_score": credit_score,
    "quota_new": quota_new,
    "quota_use": quota_use,
    "quota_reset": quota_reset,
    "points_new": points_new,
    "points_hold": points_hold,
    "points_release": points_release,
    "points_withdraw": points_withdraw,
    "badge_level": badge_level,
    "badge_issue": badge_issue,
    "dispute_review": dispute_review,
    "team_create": team_create,
    "team_join": team_join,
    "team_share": team_share,
    "quota_advance": quota_advance,
    "points_ledger": points_ledger,
}

# ---------------------------------------------------------------------------
# 自检：逐条执行规格中的全部 60 条测试
# ---------------------------------------------------------------------------

def _resolve_arg(arg):
    """测试 input 中的嵌套调用 {"op": ..., "args": [...]} 先求值。"""
    if isinstance(arg, dict) and "op" in arg:
        fn = OPS[arg["op"]]
        args = [_resolve_arg(a) for a in arg.get("args", [])]
        return fn(*args)
    return arg


def _run_all_tests():
    total = passed = 0
    failures = []
    for opdef in _SPEC["operations"]:
        name = opdef["name"]
        fn = OPS[name]
        for t in opdef.get("tests", []):
            total += 1
            desc = t.get("description", "")
            args = [_resolve_arg(a) for a in t.get("input", [])]
            if t.get("error") is not None:
                try:
                    fn(*args)
                    failures.append((name, desc, "error " + t["error"], "未抛错"))
                except ValueError as e:
                    if str(e) == t["error"]:
                        passed += 1
                    else:
                        failures.append((name, desc, t["error"], str(e)))
                except Exception as e:  # noqa: BLE001
                    failures.append((name, desc, t["error"], f"{type(e).__name__}: {e}"))
            else:
                try:
                    got = fn(*args)
                    if got == t["output"]:
                        passed += 1
                    else:
                        failures.append((name, desc, repr(t["output"]), repr(got)))
                except ValueError as e:
                    failures.append((name, desc, repr(t["output"]), f"ValueError({e})"))
                except Exception as e:  # noqa: BLE001
                    failures.append((name, desc, repr(t["output"]), f"{type(e).__name__}: {e}"))
    return total, passed, failures


if __name__ == "__main__":
    total, passed, failures = _run_all_tests()
    print(f"总计 {total} 条测试，通过 {passed} 条，失败 {len(failures)} 条")
    print(f"通过率: {passed}/{total} ({passed * 100.0 / total:.1f}%)")
    for name, desc, expected, actual in failures:
        print(f"  FAIL [{name}] {desc}: 期望={expected} 实际={actual}")
