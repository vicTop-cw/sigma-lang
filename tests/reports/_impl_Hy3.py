# -*- coding: utf-8 -*-
"""
ΣLang §SK 协议独立实现 —— Hy3
仅依据 TASK_SPEC.md 与 spec_p0_socketkit.json 实现，未参考仓库内任何已有实现。
本文件包含：22 个操作函数 + 内置函数 + 测试运行器（加载 spec JSON 的 tests 执行）。
"""

import json
import os

# ---------------------------------------------------------------------------
# 常量（取自 spec constants 区，v0.31）
# ---------------------------------------------------------------------------
C_BADGE_THRESHOLDS = [100, 300, 600]
C_VERIFIER_MIN_ID = 1000
C_CREDIT_INITIAL = 100
C_CREDIT_KIND0_PER = 5
C_CREDIT_RATIO_NUM = 7
C_CREDIT_RATIO_DEN = 10
C_CREDIT_FLOOR = 0

# ---------------------------------------------------------------------------
# 内置函数（definition 中的 {"fn": ...} 与 precondition 辅助函数）
# ---------------------------------------------------------------------------

def index(coll, i):
    """取列表第 i 个元素；越界抛 ShapeError；非列表/非整数参数抛 TypeError。"""
    if not isinstance(coll, list) or not isinstance(i, int):
        raise ValueError("TypeError")
    if i < 0 or i >= len(coll):
        raise ValueError("ShapeError")
    return coll[i]


def sigma_min(*args):
    if len(args) == 1 and isinstance(args[0], list):
        return min(args[0])
    return min(args)


def sigma_max(*args):
    if len(args) == 1 and isinstance(args[0], list):
        return max(args[0])
    return max(args)


def sigma_add(a, b):
    return a + b


def sigma_sub(a, b):
    return a - b


def ge(a, b):
    return a >= b


def lt(a, b):
    return a < b


def eq(a, b):
    return a == b


def gt(a, b):
    return a > b


def le(a, b):
    return a <= b


def ne(a, b):
    return a != b


def fold_add(xs):
    """若 xs 是列表的列表 -> 每行最后一个元素求和；否则普通求和。非列表抛 TypeError。"""
    if not isinstance(xs, list):
        raise ValueError("TypeError")
    if len(xs) > 0 and all(isinstance(r, list) for r in xs):
        return sum(r[-1] for r in xs)
    return sum(xs)


def fold_credit(init, events):
    """契分折叠：初始 init；事件 [kind, count]：kind=0 -> +5*count；kind=1 -> 逐次 *7//10。结果下限 0。"""
    if not isinstance(events, list):
        raise ValueError("TypeError")
    val = init
    for ev in events:
        kind = ev[0]
        count = ev[1]
        if kind == 0:
            val = val + C_CREDIT_KIND0_PER * count
        elif kind == 1:
            for _ in range(count):
                val = val * C_CREDIT_RATIO_NUM // C_CREDIT_RATIO_DEN
    if val < C_CREDIT_FLOOR:
        val = C_CREDIT_FLOOR
    return val


def weighted_accept(xs):
    if not isinstance(xs, list):
        raise ValueError("TypeError")
    return sum(row[2] for row in xs if row[1] == 1)


def weighted_support(xs):
    if not isinstance(xs, list):
        raise ValueError("TypeError")
    return sum(row[2] for row in xs if row[1] == 1)


def weighted_reject(xs):
    if not isinstance(xs, list):
        raise ValueError("TypeError")
    return sum(row[2] for row in xs if row[1] == 0)


def split_floor(contribs, reward):
    """按贡献分账：share = floor(reward * c / total)；total==0 抛 DivByZero。"""
    total = sum(c[1] for c in contribs)
    if total == 0:
        raise ValueError("DivByZero")
    return [[c[0], reward * c[1] // total] for c in contribs]


def enumerate_ledger(entries):
    """输入 [[旧id, 金额, source], ...] -> 输出 [[1, source, 金额], ...]（编号 1..n）。
    source<1 抛 NotTraceable；金额<0 抛 TypeError。"""
    if not isinstance(entries, list):
        raise ValueError("TypeError")
    out = []
    for i, row in enumerate(entries):
        old_id, amount, source = row[0], row[1], row[2]
        if source < 1:
            raise ValueError("NotTraceable")
        if amount < 0:
            raise ValueError("TypeError")
        out.append([i + 1, source, amount])
    return out


# precondition 辅助函数（白名单）
def sum_contribs(c):
    """c 的每行第 2 列（贡献）之和。"""
    return sum(row[1] for row in c)


def min_source_id(e):
    """e 的每行第 3 列（source）最小值，空列表返回 +∞。"""
    if len(e) == 0:
        return float("inf")
    return min(row[2] for row in e)


# ---------------------------------------------------------------------------
# 22 个操作实现
# ---------------------------------------------------------------------------

def task_create(a, b):
    check_preconditions("task_create", {"a": a, "b": b})
    return [a, b, 0, 0]


def review_merge(os):
    if not isinstance(os, list):
        raise ValueError("TypeError")
    return 1 if ge(weighted_accept(os), weighted_reject(os)) else 0


def contribution_score(a):
    if not isinstance(a, list):
        raise ValueError("TypeError")
    return sigma_max(0, fold_add(a))


def accept_task(t, h):
    check_preconditions("accept_task", {"t": t, "h": h})
    return [index(t, 0), index(t, 1), 1, h]


def task_submit(t):
    check_preconditions("task_submit", {"t": t})
    return [index(t, 0), index(t, 1), 2, index(t, 3)]


def task_accept(t, c):
    check_preconditions("task_accept", {"t": t, "c": c})
    return [index(t, 0), index(t, 1), 3, index(t, 3)]


def credit_score(e):
    if not isinstance(e, list):
        raise ValueError("TypeError")
    return fold_credit(C_CREDIT_INITIAL, e)


def quota_new(m):
    return [m, m]


def quota_use(q, a):
    check_preconditions("quota_use", {"q": q, "a": a})
    return [index(q, 0), sigma_sub(index(q, 1), a)]


def quota_reset(q):
    return [index(q, 0), index(q, 0)]


def points_new():
    return [0, 0]


def points_hold(p, x):
    return [sigma_add(index(p, 0), x), index(p, 1)]


def points_release(p, x):
    check_preconditions("points_release", {"p": p, "x": x})
    return [sigma_sub(index(p, 0), x), sigma_add(index(p, 1), x)]


def points_withdraw(p, x):
    check_preconditions("points_withdraw", {"p": p, "x": x})
    return [index(p, 0), sigma_sub(index(p, 1), x)]


def badge_level(s):
    if lt(s, C_BADGE_THRESHOLDS[0]):
        return 0
    if lt(s, C_BADGE_THRESHOLDS[1]):
        return 1
    if lt(s, C_BADGE_THRESHOLDS[2]):
        return 2
    return 3


def badge_issue(v, u, s):
    check_preconditions("badge_issue", {"v": v, "u": u, "s": s})
    return [v, u, badge_level(s)]


def dispute_review(e):
    if not isinstance(e, list):
        raise ValueError("TypeError")
    return 1 if ge(weighted_support(e), weighted_reject(e)) else 0


def team_create(o, k, c):
    check_preconditions("team_create", {"o": o, "k": k, "c": c})
    return [o, k, 1, c]


def team_join(t, m):
    check_preconditions("team_join", {"t": t, "m": m})
    return [index(t, 0), index(t, 1), sigma_add(index(t, 2), 1), index(t, 3)]


def team_share(c, r):
    check_preconditions("team_share", {"c": c, "r": r})
    return split_floor(c, r)


def quota_advance(q):
    if not isinstance(q, list):
        raise ValueError("TypeError")
    return [index(q, 0), sigma_add(index(q, 1), index(q, 0))]


def points_ledger(e):
    if not isinstance(e, list):
        raise ValueError("TypeError")
    return enumerate_ledger(e)


# ---------------------------------------------------------------------------
# 操作注册表
# ---------------------------------------------------------------------------
OP = {
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
# precondition 检查（模块级纯数据，不依赖外部初始化 / 文件读取）
# 每个操作的前置条件直接硬编码：[ (expr, error), ... ]
# expr 中可用白名单辅助函数：index / sum_contribs / min_source_id /
# min / max / len / abs / sum
# ---------------------------------------------------------------------------
_PRECON = {
    "task_create": [("b >= 0", "BountyErr")],
    "accept_task": [("index(t, 2) == 0", "StateError")],
    "task_submit": [("index(t, 2) == 1", "StateError")],
    "task_accept": [
        ("index(t, 2) == 2", "StateError"),
        ("c == index(t, 0)", "AuthError"),
    ],
    "quota_use": [("a <= index(q, 1)", "QuotaExhausted")],
    "points_release": [("x <= index(p, 0)", "InsufficientEscrow")],
    "points_withdraw": [("x <= index(p, 1)", "InsufficientPoints")],
    "badge_issue": [("v >= 1000", "AuthError")],
    "team_create": [("c >= 1", "TypeError")],
    "team_join": [("index(t, 2) < index(t, 3)", "TeamFull")],
    "team_share": [("sum_contribs(c) > 0", "DivByZero")],
    "points_ledger": [("min_source_id(e) >= 1", "NotTraceable")],
}


def check_preconditions(name, env):
    """纯函数：依据模块级 _PRECON 检查前置条件，不依赖外部初始化。"""
    for expr, err in _PRECON.get(name, []):
        ns = {
            "index": index,
            "sum_contribs": sum_contribs,
            "min_source_id": min_source_id,
            "min": min,
            "max": max,
            "len": len,
            "abs": abs,
            "sum": sum,
        }
        local = dict(ns)
        local.update(env)
        ok = eval(expr, {"__builtins__": {}}, local)
        if not ok:
            raise ValueError(err)


# ---------------------------------------------------------------------------
# 测试运行器
# ---------------------------------------------------------------------------
def _load_spec():
    here = os.path.dirname(os.path.abspath(__file__))
    spec_path = os.path.normpath(os.path.join(here, "..", "..", "spec", "spec_p0_socketkit.json"))
    with open(spec_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _eval_arg(arg):
    if isinstance(arg, dict) and "op" in arg:
        sub = [_eval_arg(a) for a in arg["args"]]
        return OP[arg["op"]](*sub)
    return arg


def run_tests():
    spec = _load_spec()
    total = 0
    passed = 0
    failures = []
    for op in spec["operations"]:
        name = op["name"]
        for t in op["tests"]:
            total += 1
            args = [_eval_arg(a) for a in t["input"]]
            try:
                result = OP[name](*args)
                err = None
            except ValueError as ex:
                result = None
                err = str(ex)
            expected_err = t.get("error")
            expected_out = t.get("output")
            if expected_err is not None:
                ok = (err == expected_err)
                exp_disp = expected_err
                act_disp = err if err is not None else "(无错误)"
            else:
                ok = (result == expected_out)
                exp_disp = expected_out
                act_disp = result
            if ok:
                passed += 1
            else:
                failures.append({
                    "op": name,
                    "desc": t.get("description", ""),
                    "expected": exp_disp,
                    "actual": act_disp,
                })
    return total, passed, failures


if __name__ == "__main__":
    total, passed, failures = run_tests()
    print("TOTAL=%d PASSED=%d FAILED=%d" % (total, passed, len(failures)))
    if failures:
        print("--- FAILURES ---")
        for f in failures:
            print("[%s] %s" % (f["op"], f["desc"]))
            print("    expected: %r" % (f["expected"],))
            print("    actual:   %r" % (f["actual"],))
