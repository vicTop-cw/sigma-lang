# -*- coding: utf-8 -*-
"""ΣLang §SK 协议独立实现 — 工具: Qwen3dot8Max

依据 spec/spec_p0_socketkit.json (v0.31.0) 独立实现全部 22 个操作。
- 错误一律 raise ValueError("<错误名>")，错误名与规格 tests 的 error 字段一致
- 常量取自规格顶层 constants 区
- 类型守卫 (v0.31 固定): 列表参数收到非列表 -> TypeError; index 越界 -> ShapeError

本文件不参考仓库内任何已有实现。
"""

# ---------------------------------------------------------------------------
# constants (来自规格顶层 constants 区, v0.31 新增)
# ---------------------------------------------------------------------------
STATUS_OPEN = 0            # status.open
STATUS_IN_PROGRESS = 1     # status.in_progress
STATUS_PENDING_REVIEW = 2  # status.pending_review
STATUS_COMPLETED = 3       # status.completed

DECISION_REJECT = 0        # decision.reject
DECISION_ACCEPT = 1        # decision.accept

BADGE_THRESHOLDS = [100, 300, 600]  # badge.thresholds
BADGE_BRONZE = 0           # badge.levels.bronze
BADGE_SILVER = 1           # badge.levels.silver
BADGE_GOLD = 2             # badge.levels.gold
BADGE_DIAMOND = 3          # badge.levels.diamond

VERIFIER_MIN_ID = 1000     # verifier_min_id

CREDIT_INITIAL = 100       # credit.initial
CREDIT_KIND0_PER_COMPLETION = 5   # credit.kind0_per_completion
CREDIT_KIND1_NUM = 7       # credit.kind1_floor_ratio.num
CREDIT_KIND1_DEN = 10      # credit.kind1_floor_ratio.den
CREDIT_FLOOR = 0           # credit.floor

CONTRIBUTION_FLOOR = 0     # contribution.floor

TEAM_MIN_CAPACITY = 1      # team.min_capacity

LEDGER_ENTRY_ID_START = 1  # ledger.entry_id_start
LEDGER_MIN_SOURCE_ID = 1   # ledger.min_source_id


# ---------------------------------------------------------------------------
# 内置函数 / 类型守卫
# ---------------------------------------------------------------------------
def _require_list(v):
    """列表参数收到非列表 -> TypeError (v0.31 固定类型守卫)。"""
    if not isinstance(v, list):
        raise ValueError("TypeError")


def _require_nat(v):
    """nat 参数收到非整数(或负数以外类型不对) -> TypeError。"""
    if not isinstance(v, int) or isinstance(v, bool):
        raise ValueError("TypeError")


def _index(coll, i):
    """index(coll, i): 越界抛 ShapeError; 非列表/非整数参数抛 TypeError。"""
    if not isinstance(coll, list):
        raise ValueError("TypeError")
    if not isinstance(i, int) or isinstance(i, bool):
        raise ValueError("TypeError")
    if i < 0 or i >= len(coll):
        raise ValueError("ShapeError")
    return coll[i]


def _fold_add(xs):
    """fold_add: 若 xs 是列表的列表 -> 每行最后一个元素求和; 否则普通求和。"""
    _require_list(xs)
    if xs and all(isinstance(row, list) and row for row in xs):
        return sum(_index(row, len(row) - 1) for row in xs)
    return sum(xs)


def _weighted_vote(xs, want_vote):
    """对 [reviewer, vote, weight] 行, 累加 vote==want_vote 的 weight。"""
    _require_list(xs)
    total = 0
    for row in xs:
        _require_list(row)
        vote = _index(row, 1)
        weight = _index(row, 2)
        if vote == want_vote:
            total += weight
    return total


def weighted_accept(xs):
    return _weighted_vote(xs, DECISION_ACCEPT)


def weighted_support(xs):
    return _weighted_vote(xs, DECISION_ACCEPT)


def weighted_reject(xs):
    return _weighted_vote(xs, DECISION_REJECT)


def _fold_credit(init, events):
    """契分折叠: kind=0 -> +5×count; kind=1 -> 逐次 ×7//10; 结果下限 0。"""
    _require_list(events)
    score = init
    for ev in events:
        _require_list(ev)
        kind = _index(ev, 0)
        count = _index(ev, 1)
        if kind == 0:
            score += CREDIT_KIND0_PER_COMPLETION * count
        elif kind == 1:
            for _ in range(count):
                score = score * CREDIT_KIND1_NUM // CREDIT_KIND1_DEN
        else:
            raise ValueError("TypeError")
    return max(CREDIT_FLOOR, score)


def _sum_contribs(c):
    """sum_contribs(c): c 的每行第 2 列(贡献)之和。"""
    _require_list(c)
    return sum(_index(row, 1) for row in c)


def _split_floor(contribs, reward):
    """按贡献分账: share = floor(reward × c / total); total==0 抛 DivByZero。"""
    _require_list(contribs)
    _require_nat(reward)
    total = _sum_contribs(contribs)
    if total == 0:
        raise ValueError("DivByZero")
    return [[_index(row, 0), reward * _index(row, 1) // total] for row in contribs]


def _min_source_id(entries):
    """min_source_id(e): 每行第 3 列(source)最小值, 空列表返回 +∞。"""
    _require_list(entries)
    if not entries:
        return float("inf")
    return min(_index(row, 2) for row in entries)


def _enumerate_ledger(entries):
    """[[旧id, 金额, source], ...] -> [[1, source, 金额], [2, ...], ...]。"""
    _require_list(entries)
    out = []
    for i, row in enumerate(entries):
        _require_list(row)
        amount = _index(row, 1)
        source = _index(row, 2)
        if source < LEDGER_MIN_SOURCE_ID:
            raise ValueError("NotTraceable")
        if amount < 0:
            raise ValueError("TypeError")
        out.append([LEDGER_ENTRY_ID_START + i, source, amount])
    return out


# ---------------------------------------------------------------------------
# 22 个操作
# ---------------------------------------------------------------------------
def task_create(a, b):
    """发单: [author, bounty, open, unclaimed]。bounty >= 0 (赏金可为 0)。"""
    _require_nat(a)
    if not isinstance(b, int) or isinstance(b, bool):
        raise ValueError("TypeError")
    if b < 0:
        raise ValueError("BountyErr")
    return [a, b, STATUS_OPEN, 0]


def review_merge(os):
    """评审合并: 加权支持 >= 加权驳回 -> accept(1), 否则 reject(0)。"""
    _require_list(os)
    if weighted_accept(os) >= weighted_reject(os):
        return DECISION_ACCEPT
    return DECISION_REJECT


def contribution_score(a):
    """贡献分: max(0, fold_add(a)) — 下限 0。"""
    _require_list(a)
    return max(CONTRIBUTION_FLOOR, _fold_add(a))


def accept_task(t, h):
    """接单: open(0) -> in_progress(1), 记录猎手 h。"""
    _require_list(t)
    _require_nat(h)
    if _index(t, 2) != STATUS_OPEN:
        raise ValueError("StateError")
    return [_index(t, 0), _index(t, 1), STATUS_IN_PROGRESS, h]


def task_submit(t):
    """提交: in_progress(1) -> pending_review(2), 猎手不变。"""
    _require_list(t)
    if _index(t, 2) != STATUS_IN_PROGRESS:
        raise ValueError("StateError")
    return [_index(t, 0), _index(t, 1), STATUS_PENDING_REVIEW, _index(t, 3)]


def task_accept(t, c):
    """验收: pending_review(2) -> completed(3); 仅作者本人可验收。"""
    _require_list(t)
    _require_nat(c)
    if _index(t, 2) != STATUS_PENDING_REVIEW:
        raise ValueError("StateError")
    if c != _index(t, 0):
        raise ValueError("AuthError")
    return [_index(t, 0), _index(t, 1), STATUS_COMPLETED, _index(t, 3)]


def credit_score(e):
    """契分: 从 100 起算的折叠。"""
    _require_list(e)
    return _fold_credit(CREDIT_INITIAL, e)


def quota_new(m):
    """新建月度额度: [limit, remaining] = [m, m]。"""
    _require_nat(m)
    return [m, m]


def quota_use(q, a):
    """消耗额度: remaining -= a; 不得超过 remaining。"""
    _require_list(q)
    _require_nat(a)
    if a > _index(q, 1):
        raise ValueError("QuotaExhausted")
    return [_index(q, 0), _index(q, 1) - a]


def quota_reset(q):
    """月末重置: remaining 恢复为 limit。"""
    _require_list(q)
    return [_index(q, 0), _index(q, 0)]


def points_new():
    """全新积分账户: [escrow, available] = [0, 0]。"""
    return [0, 0]


def points_hold(p, x):
    """冻结: x 计入 escrow, available 不变。"""
    _require_list(p)
    _require_nat(x)
    return [_index(p, 0) + x, _index(p, 1)]


def points_release(p, x):
    """释放: x 从 escrow 移入 available; 不得超过 escrow。"""
    _require_list(p)
    _require_nat(x)
    if x > _index(p, 0):
        raise ValueError("InsufficientEscrow")
    return [_index(p, 0) - x, _index(p, 1) + x]


def points_withdraw(p, x):
    """提现: available -= x; 不得超过 available。"""
    _require_list(p)
    _require_nat(x)
    if x > _index(p, 1):
        raise ValueError("InsufficientPoints")
    return [_index(p, 0), _index(p, 1) - x]


def badge_level(s):
    """徽章等级: <100 铜(0) / <300 银(1) / <600 金(2) / >=600 钻石(3)。"""
    _require_nat(s)
    if s < BADGE_THRESHOLDS[0]:
        return BADGE_BRONZE
    if s < BADGE_THRESHOLDS[1]:
        return BADGE_SILVER
    if s < BADGE_THRESHOLDS[2]:
        return BADGE_GOLD
    return BADGE_DIAMOND


def badge_issue(v, u, s):
    """发徽章: 仅核验师 (v >= 1000); [verifier, user, level]。"""
    _require_nat(v)
    _require_nat(u)
    _require_nat(s)
    if v < VERIFIER_MIN_ID:
        raise ValueError("AuthError")
    return [v, u, badge_level(s)]


def dispute_review(e):
    """争议仲裁: 加权支持 >= 加权驳回 -> 支持(1), 否则 驳回(0)。"""
    _require_list(e)
    if weighted_support(e) >= weighted_reject(e):
        return DECISION_ACCEPT
    return DECISION_REJECT


def team_create(o, k, c):
    """建团: [owner, kind, size=1, capacity]; capacity >= 1。"""
    _require_nat(o)
    _require_nat(k)
    if not isinstance(c, int) or isinstance(c, bool) or c < TEAM_MIN_CAPACITY:
        raise ValueError("TypeError")
    return [o, k, 1, c]


def team_join(t, m):
    """入团: size += 1; 满员抛 TeamFull。"""
    _require_list(t)
    _require_nat(m)
    if _index(t, 2) >= _index(t, 3):
        raise ValueError("TeamFull")
    return [_index(t, 0), _index(t, 1), _index(t, 2) + 1, _index(t, 3)]


def team_share(c, r):
    """分账: 按贡献向下取整; 总贡献为 0 抛 DivByZero。"""
    _require_list(c)
    if _sum_contribs(c) <= 0:
        raise ValueError("DivByZero")
    return _split_floor(c, r)


def quota_advance(q):
    """预支: remaining += limit (隔月 reset 后消失)。"""
    _require_list(q)
    return [_index(q, 0), _index(q, 1) + _index(q, 0)]


def points_ledger(e):
    """账本: 每行 source >= 1 可追溯; 重编号 1..n, 行布局 [新编号, source, 金额]。"""
    _require_list(e)
    if _min_source_id(e) < LEDGER_MIN_SOURCE_ID:
        raise ValueError("NotTraceable")
    return _enumerate_ledger(e)


# ---------------------------------------------------------------------------
# 自检: 逐条执行规格中的全部 tests
# ---------------------------------------------------------------------------
_OPS = {
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


def _eval_arg(arg):
    """测试 input 中的嵌套调用 {"op": ..., "args": [...]} 先求值。"""
    if isinstance(arg, dict) and "op" in arg:
        fn = _OPS[arg["op"]]
        return fn(*[_eval_arg(a) for a in arg.get("args", [])])
    return arg


def run_tests(spec_path):
    """逐条执行规格 tests, 返回 (通过数, 总数, 失败清单)。"""
    import json

    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    total = 0
    passed = 0
    failures = []

    for opdef in spec["operations"]:
        name = opdef["name"]
        fn = _OPS[name]
        for t in opdef.get("tests", []):
            total += 1
            desc = t.get("description", "")
            try:
                args = [_eval_arg(a) for a in t.get("input", [])]
                actual = fn(*args)
                err = None
            except ValueError as ex:
                actual = None
                err = str(ex)

            if "error" in t and t["error"] is not None:
                ok = err == t["error"]
                expected = "error=%s" % t["error"]
                got = "error=%s" % err if err is not None else repr(actual)
            else:
                ok = err is None and actual == t.get("output")
                expected = repr(t.get("output"))
                got = "error=%s" % err if err is not None else repr(actual)

            if ok:
                passed += 1
                print("PASS  %-20s %s" % (name, desc))
            else:
                failures.append((name, desc, expected, got))
                print("FAIL  %-20s %s | 期望 %s | 实际 %s" % (name, desc, expected, got))

    return passed, total, failures


if __name__ == "__main__":
    import os

    spec_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "spec", "spec_p0_socketkit.json",
    )
    spec_path = os.path.normpath(spec_path)
    passed, total, failures = run_tests(spec_path)
    print("-" * 60)
    print("通过 %d / %d (%.1f%%)" % (passed, total, 100.0 * passed / total))
    if failures:
        print("失败清单:")
        for name, desc, expected, got in failures:
            print("  - %s | %s | 期望 %s | 实际 %s" % (name, desc, expected, got))
