"""
σCore AI subagent implementation — §SK (socketkit) find-bugs business semantics.

Independent implementation derived solely from:
    E:\\IDEProjects\\AI\\sigma-lang\\spec\\spec_p0_socketkit.json

22 operations, 60 tests. Pure stdlib, no dependencies.
Errors are raised as ValueError("<ErrorName>") where <ErrorName> matches the
spec's test `error` fields exactly (BountyErr / StateError / AuthError /
QuotaExhausted / InsufficientEscrow / InsufficientPoints / TeamFull /
DivByZero / NotTraceable / TypeError).

Usage:
    python sigma_core_ai_subagent.py [spec.json]
Runs the full self-check suite against the spec (defaults to
spec_p0_socketkit.json) and prints a summary plus the final line
    AGENT_SK_IMPL COMPLETE: N/60 passed
"""

import json
import os
import sys

# ---------------------------------------------------------------------------
# Built-in functions (spec-internal semantics)
# ---------------------------------------------------------------------------


def index(lst, i):
    """index(list, i): element at position i."""
    return lst[i]


def _row_value(x):
    """Value contributed by one element of a fold: last element if row, else itself."""
    return x[-1] if isinstance(x, list) else x


def fold_add(rows):
    """fold_add: rows (each a list) -> sum of each row's last element; flat list -> plain sum."""
    return sum(_row_value(x) for x in rows)


def fold_credit(base, events):
    """fold_credit: kind0 event -> +5*count; kind1 event -> credit = credit*7//10 per count (floor, min 0)."""
    credit = base
    for ev in events:
        kind, count = ev[0], ev[1]
        if kind == 0:
            credit += 5 * count
        elif kind == 1:
            for _ in range(count):
                credit = credit * 7 // 10
    return max(0, credit)


def weighted_accept(rows):
    """weighted_accept: sum of row[2] (weight) where row[1] == 1 (decision/stance accept)."""
    return sum(r[2] for r in rows if r[1] == 1)


def weighted_reject(rows):
    """weighted_reject: sum of row[2] (weight) where row[1] == 0 (decision/stance reject)."""
    return sum(r[2] for r in rows if r[1] == 0)


def weighted_support(rows):
    """weighted_support: sum of row[2] (weight) where row[1] == 1 (support stance)."""
    return sum(r[2] for r in rows if r[1] == 1)


def split_floor(rows, reward):
    """split_floor: share_i = floor(reward * row_i[1] / total); total = sum of row[*][1]; total == 0 -> DivByZero."""
    total = sum(r[1] for r in rows)
    if total <= 0:
        raise ValueError("DivByZero")
    return [[r[0], (reward * r[1]) // total] for r in rows]


def enumerate_ledger(rows):
    """enumerate_ledger: input rows [old_id, amount, source] -> [[i+1, source, amount]]; source < 1 -> NotTraceable."""
    out = []
    for i, row in enumerate(rows):
        if row[2] < 1:
            raise ValueError("NotTraceable")
        out.append([i + 1, row[2], row[1]])
    return out


# ---------------------------------------------------------------------------
# §SK operations (one function per operation in spec_p0_socketkit.json)
# ---------------------------------------------------------------------------


def task_create(a, b):
    # precondition: bounty >= 0 (bounty may be 0)
    if b < 0:
        raise ValueError("BountyErr")
    return [a, b, 0, 0]


def review_merge(os):
    if not isinstance(os, list):
        raise ValueError("TypeError")
    return 1 if weighted_accept(os) >= weighted_reject(os) else 0


def contribution_score(a):
    if not isinstance(a, list):
        raise ValueError("TypeError")
    return max(0, fold_add(a))


def accept_task(t, h):
    # precondition: task must be open (status 0)
    if not isinstance(t, list):
        raise ValueError("TypeError")
    if index(t, 2) != 0:
        raise ValueError("StateError")
    return [index(t, 0), index(t, 1), 1, h]


def task_submit(t):
    # precondition: task must be in_progress (status 1)
    if not isinstance(t, list):
        raise ValueError("TypeError")
    if index(t, 2) != 1:
        raise ValueError("StateError")
    return [index(t, 0), index(t, 1), 2, index(t, 3)]


def task_accept(t, c):
    # preconditions: status must be pending_review (2); caller must be the author
    if not isinstance(t, list):
        raise ValueError("TypeError")
    if index(t, 2) != 2:
        raise ValueError("StateError")
    if c != index(t, 0):
        raise ValueError("AuthError")
    return [index(t, 0), index(t, 1), 3, index(t, 3)]


def credit_score(e):
    if not isinstance(e, list):
        raise ValueError("TypeError")
    return fold_credit(100, e)


def quota_new(m):
    return [m, m]


def quota_use(q, a):
    # precondition: amount must not exceed remaining quota
    if not isinstance(q, list):
        raise ValueError("TypeError")
    if a > index(q, 1):
        raise ValueError("QuotaExhausted")
    return [index(q, 0), index(q, 1) - a]


def quota_reset(q):
    if not isinstance(q, list):
        raise ValueError("TypeError")
    return [index(q, 0), index(q, 0)]


def points_new():
    return [0, 0]


def points_hold(p, x):
    if not isinstance(p, list):
        raise ValueError("TypeError")
    return [index(p, 0) + x, index(p, 1)]


def points_release(p, x):
    # precondition: release amount must not exceed escrow
    if not isinstance(p, list):
        raise ValueError("TypeError")
    if x > index(p, 0):
        raise ValueError("InsufficientEscrow")
    return [index(p, 0) - x, index(p, 1) + x]


def points_withdraw(p, x):
    # precondition: withdraw amount must not exceed available
    if not isinstance(p, list):
        raise ValueError("TypeError")
    if x > index(p, 1):
        raise ValueError("InsufficientPoints")
    return [index(p, 0), index(p, 1) - x]


def badge_level(s):
    if s < 100:
        return 0
    if s < 300:
        return 1
    if s < 600:
        return 2
    return 3


def badge_issue(v, u, s):
    # precondition: only authorized verifiers (v >= 1000) may issue badges
    if v < 1000:
        raise ValueError("AuthError")
    return [v, u, badge_level(s)]


def dispute_review(e):
    if not isinstance(e, list):
        raise ValueError("TypeError")
    return 1 if weighted_support(e) >= weighted_reject(e) else 0


def team_create(o, k, c):
    # precondition: capacity must be >= 1
    if c < 1:
        raise ValueError("TypeError")
    return [o, k, 1, c]


def team_join(t, m):
    # precondition: team must not be full
    if not isinstance(t, list):
        raise ValueError("TypeError")
    if index(t, 2) >= index(t, 3):
        raise ValueError("TeamFull")
    return [index(t, 0), index(t, 1), index(t, 2) + 1, index(t, 3)]


def team_share(c, r):
    # precondition: total contribution must be > 0 (total = 0 -> DivByZero)
    if not isinstance(c, list):
        raise ValueError("TypeError")
    if sum(row[1] for row in c) <= 0:
        raise ValueError("DivByZero")
    return split_floor(c, r)


def quota_advance(q):
    if not isinstance(q, list):
        raise ValueError("TypeError")
    return [index(q, 0), index(q, 1) + index(q, 0)]


def points_ledger(e):
    # precondition: every entry must be traceable (source_id >= 1)
    if not isinstance(e, list):
        raise ValueError("TypeError")
    if any(row[2] < 1 for row in e):
        raise ValueError("NotTraceable")
    return enumerate_ledger(e)


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
# Expression resolver + self-check harness
# ---------------------------------------------------------------------------

_LAST = None  # "$_" support: previous top-level test result


def resolve(x):
    """Recursively evaluate {"op": ..., "args": [...]} nodes; lists resolve element-wise."""
    global _LAST
    if isinstance(x, dict):
        if "op" in x:
            args = [resolve(a) for a in x.get("args", [])]
            return OPS[x["op"]](*args)
        return x
    if isinstance(x, list):
        return [resolve(e) for e in x]
    if isinstance(x, str) and x == "$_":
        return _LAST
    return x


def run_selfcheck(spec_path):
    global _LAST
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    total = 0
    passed = 0
    failures = []

    for op in spec["operations"]:
        op_name = op["name"]
        for test in op.get("tests", []):
            total += 1
            desc = test.get("description", "")
            expected_error = test.get("error")
            expected_output = test.get("output")
            try:
                args = [resolve(a) for a in test.get("input", [])]
                result = OPS[op_name](*args)
                _LAST = result
                if expected_error is not None:
                    failures.append((op_name, desc, "expected error %r but got result %r" % (expected_error, result)))
                elif result != expected_output:
                    failures.append((op_name, desc, "expected %r but got %r" % (expected_output, result)))
                else:
                    passed += 1
            except ValueError as e:
                if expected_error is not None and str(e) == expected_error:
                    passed += 1
                else:
                    failures.append((op_name, desc, "unexpected ValueError %r (expected %r)" % (str(e), expected_error)))
            except Exception as e:  # noqa: BLE001 - harness reports any crash
                failures.append((op_name, desc, "crash: %r" % (e,)))

    print("=" * 64)
    print("self-check against %s" % os.path.basename(spec_path))
    print("operations in spec: %d" % len(spec["operations"]))
    print("tests executed: %d" % total)
    print("-" * 64)
    if failures:
        print("FAILURES (%d):" % len(failures))
        for op_name, desc, msg in failures:
            print("  [%s] %s -> %s" % (op_name, desc, msg))
    else:
        print("all tests passed")
    print("-" * 64)
    print("AGENT_SK_IMPL COMPLETE: %d/%d passed" % (passed, total))
    return passed, total


if __name__ == "__main__":
    default_spec = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "spec", "spec_p0_socketkit.json",
    )
    spec_file = sys.argv[1] if len(sys.argv) > 1 else default_spec
    p, t = run_selfcheck(spec_file)
    sys.exit(0 if p == t else 1)
