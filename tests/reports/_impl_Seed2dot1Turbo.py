# ΣLang §SK 独立实现 - Seed2dot1Turbo
# 仅基于 spec_p0_socketkit.json 和 TASK_SPEC.md 实现

import math

# ============ 常量 (来自 spec constants 区) ============
STATUS = {"open": 0, "in_progress": 1, "pending_review": 2, "completed": 3}
DECISION = {"reject": 0, "accept": 1}
BADGE_LEVELS = {"bronze": 0, "silver": 1, "gold": 2, "diamond": 3}
BADGE_THRESHOLDS = [100, 300, 600]
VERIFIER_MIN_ID = 1000
CREDIT_INITIAL = 100
CREDIT_KIND0_PER_COMPLETION = 5
CREDIT_KIND1_FLOOR_RATIO_NUM = 7
CREDIT_KIND1_FLOOR_RATIO_DEN = 10
CREDIT_FLOOR = 0
CONTRIBUTION_FLOOR = 0
TEAM_MIN_CAPACITY = 1
LEDGER_ENTRY_ID_START = 1
LEDGER_MIN_SOURCE_ID = 1


# ============ 内置函数 ============

def _check_list(x):
    if not isinstance(x, list):
        raise ValueError("TypeError")


def _check_int(x):
    if not isinstance(x, int) or isinstance(x, bool):
        raise ValueError("TypeError")


def fn_index(coll, i):
    _check_list(coll)
    _check_int(i)
    if i < 0 or i >= len(coll):
        raise ValueError("ShapeError")
    return coll[i]


def fn_min(*args):
    if len(args) == 1:
        _check_list(args[0])
        return min(args[0])
    return min(args)


def fn_max(*args):
    if len(args) == 1:
        _check_list(args[0])
        return max(args[0])
    return max(args)


def fn_add(a, b):
    return a + b


def fn_sub(a, b):
    return a - b


def fn_ge(a, b):
    return a >= b


def fn_gt(a, b):
    return a > b


def fn_lt(a, b):
    return a < b


def fn_le(a, b):
    return a <= b


def fn_eq(a, b):
    return a == b


def fn_ne(a, b):
    return a != b


def fn_fold_add(xs):
    _check_list(xs)
    if len(xs) > 0 and isinstance(xs[0], list):
        # 列表的列表: 每行最后一个元素求和
        total = 0
        for row in xs:
            _check_list(row)
            total += row[-1]
        return total
    else:
        return sum(xs)


def fn_fold_credit(init, events):
    _check_list(events)
    result = init
    for event in events:
        _check_list(event)
        kind = event[0]
        count = event[1]
        if kind == 0:
            for _ in range(count):
                result += CREDIT_KIND0_PER_COMPLETION
        elif kind == 1:
            for _ in range(count):
                result = (result * CREDIT_KIND1_FLOOR_RATIO_NUM) // CREDIT_KIND1_FLOOR_RATIO_DEN
    return max(result, CREDIT_FLOOR)


def fn_weighted_accept(xs):
    _check_list(xs)
    total = 0
    for row in xs:
        _check_list(row)
        # [reviewer, vote, weight]
        if row[1] == 1:
            total += row[2]
    return total


def fn_weighted_support(xs):
    _check_list(xs)
    total = 0
    for row in xs:
        _check_list(row)
        if row[1] == 1:
            total += row[2]
    return total


def fn_weighted_reject(xs):
    _check_list(xs)
    total = 0
    for row in xs:
        _check_list(row)
        if row[1] == 0:
            total += row[2]
    return total


def fn_split_floor(contribs, reward):
    _check_list(contribs)
    total = 0
    for c in contribs:
        _check_list(c)
        total += c[1]
    if total == 0:
        raise ValueError("DivByZero")
    result = []
    for c in contribs:
        share = (reward * c[1]) // total
        result.append([c[0], share])
    return result


def fn_enumerate_ledger(entries):
    _check_list(entries)
    result = []
    for idx, entry in enumerate(entries):
        _check_list(entry)
        # entry: [旧id, 金额, source]
        old_id, amount, source = entry[0], entry[1], entry[2]
        if source < LEDGER_MIN_SOURCE_ID:
            raise ValueError("NotTraceable")
        if amount < 0:
            raise ValueError("TypeError")
        new_id = LEDGER_ENTRY_ID_START + idx
        result.append([new_id, source, amount])
    return result


# ============ 前置条件表达式辅助函数 ============

def pre_sum_contribs(c):
    _check_list(c)
    total = 0
    for row in c:
        _check_list(row)
        total += row[1]
    return total


def pre_min_source_id(e):
    _check_list(e)
    if len(e) == 0:
        return float('inf')
    min_val = float('inf')
    for row in e:
        _check_list(row)
        if row[2] < min_val:
            min_val = row[2]
    return min_val


def pre_len(x):
    _check_list(x)
    return len(x)


def pre_abs(x):
    return abs(x)


def pre_sum(x):
    _check_list(x)
    return sum(x)


# ============ 前置条件表达式求值 ============

def eval_precondition(expr_str, env):
    """
    求值前置条件表达式字符串。
    支持白名单函数: index, min, max, len, abs, sum, sum_contribs, min_source_id
    支持运算符: >=, <=, ==, !=, >, <, and, or, not, in
    """
    # 构造安全的 locals
    safe_locals = dict(env)
    safe_locals.update({
        'index': fn_index,
        'min': fn_min,
        'max': fn_max,
        'len': pre_len,
        'abs': pre_abs,
        'sum': pre_sum,
        'sum_contribs': pre_sum_contribs,
        'min_source_id': pre_min_source_id,
        'True': True,
        'False': False,
    })
    try:
        return eval(expr_str, {"__builtins__": {}}, safe_locals)
    except ValueError:
        raise
    except Exception:
        raise ValueError("TypeError")


# ============ definition body 求值 ============

def eval_body(body, env, op_funcs):
    if isinstance(body, dict):
        if "list" in body:
            result = []
            for item in body["list"]:
                result.append(eval_body(item, env, op_funcs))
            return result
        elif "fn" in body:
            fn_name = body["fn"]
            args = [eval_body(a, env, op_funcs) for a in body["args"]]
            fn_map = {
                "index": fn_index,
                "min": fn_min,
                "max": fn_max,
                "add": fn_add,
                "sub": fn_sub,
                "ge": fn_ge,
                "gt": fn_gt,
                "lt": fn_lt,
                "le": fn_le,
                "eq": fn_eq,
                "ne": fn_ne,
                "fold_add": fn_fold_add,
                "fold_credit": fn_fold_credit,
                "weighted_accept": fn_weighted_accept,
                "weighted_support": fn_weighted_support,
                "weighted_reject": fn_weighted_reject,
                "split_floor": fn_split_floor,
                "enumerate_ledger": fn_enumerate_ledger,
            }
            if fn_name not in fn_map:
                raise ValueError(f"Unknown fn: {fn_name}")
            return fn_map[fn_name](*args)
        elif "op" in body:
            op_name = body["op"]
            args = [eval_body(a, env, op_funcs) for a in body["args"]]
            if op_name not in op_funcs:
                raise ValueError(f"Unknown op: {op_name}")
            return op_funcs[op_name](*args)
        elif "if" in body:
            cond = eval_body(body["if"], env, op_funcs)
            if cond:
                return eval_body(body["then"], env, op_funcs)
            else:
                return eval_body(body["else"], env, op_funcs)
        else:
            raise ValueError(f"Unknown body dict keys: {list(body.keys())}")
    elif isinstance(body, str):
        if body in env:
            return env[body]
        else:
            # 可能是纯数字字符串?
            try:
                return int(body)
            except ValueError:
                raise ValueError(f"Unknown var: {body}")
    elif isinstance(body, int) or isinstance(body, bool):
        return body
    elif isinstance(body, list):
        return [eval_body(item, env, op_funcs) for item in body]
    else:
        raise ValueError(f"Unknown body type: {type(body)}")


# ============ 22 个操作实现 ============

def task_create(a, b):
    # preconditions
    if not (b >= 0):
        raise ValueError("BountyErr")
    return [a, b, 0, 0]


def review_merge(os):
    _check_list(os)
    wa = fn_weighted_accept(os)
    wr = fn_weighted_reject(os)
    return 1 if wa >= wr else 0


def contribution_score(a):
    _check_list(a)
    fa = fn_fold_add(a)
    return fn_max(0, fa)


def accept_task(t, h):
    _check_list(t)
    # preconditions
    if fn_index(t, 2) != 0:
        raise ValueError("StateError")
    return [fn_index(t, 0), fn_index(t, 1), 1, h]


def task_submit(t):
    _check_list(t)
    # preconditions
    if fn_index(t, 2) != 1:
        raise ValueError("StateError")
    return [fn_index(t, 0), fn_index(t, 1), 2, fn_index(t, 3)]


def task_accept(t, c):
    _check_list(t)
    # preconditions
    if fn_index(t, 2) != 2:
        raise ValueError("StateError")
    if c != fn_index(t, 0):
        raise ValueError("AuthError")
    return [fn_index(t, 0), fn_index(t, 1), 3, fn_index(t, 3)]


def credit_score(e):
    _check_list(e)
    return fn_fold_credit(CREDIT_INITIAL, e)


def quota_new(m):
    return [m, m]


def quota_use(q, a):
    _check_list(q)
    # preconditions
    if not (a <= fn_index(q, 1)):
        raise ValueError("QuotaExhausted")
    return [fn_index(q, 0), fn_sub(fn_index(q, 1), a)]


def quota_reset(q):
    _check_list(q)
    return [fn_index(q, 0), fn_index(q, 0)]


def points_new():
    return [0, 0]


def points_hold(p, x):
    _check_list(p)
    return [fn_add(fn_index(p, 0), x), fn_index(p, 1)]


def points_release(p, x):
    _check_list(p)
    # preconditions
    if not (x <= fn_index(p, 0)):
        raise ValueError("InsufficientEscrow")
    return [fn_sub(fn_index(p, 0), x), fn_add(fn_index(p, 1), x)]


def points_withdraw(p, x):
    _check_list(p)
    # preconditions
    if not (x <= fn_index(p, 1)):
        raise ValueError("InsufficientPoints")
    return [fn_index(p, 0), fn_sub(fn_index(p, 1), x)]


def badge_level(s):
    if s < 100:
        return 0
    elif s < 300:
        return 1
    elif s < 600:
        return 2
    else:
        return 3


def badge_issue(v, u, s):
    # preconditions
    if not (v >= 1000):
        raise ValueError("AuthError")
    return [v, u, badge_level(s)]


def dispute_review(e):
    _check_list(e)
    ws = fn_weighted_support(e)
    wr = fn_weighted_reject(e)
    return 1 if ws >= wr else 0


def team_create(o, k, c):
    # preconditions
    if not (c >= 1):
        raise ValueError("TypeError")
    return [o, k, 1, c]


def team_join(t, m):
    _check_list(t)
    # preconditions
    if not (fn_index(t, 2) < fn_index(t, 3)):
        raise ValueError("TeamFull")
    return [fn_index(t, 0), fn_index(t, 1), fn_add(fn_index(t, 2), 1), fn_index(t, 3)]


def team_share(c, r):
    _check_list(c)
    # preconditions
    if not (pre_sum_contribs(c) > 0):
        raise ValueError("DivByZero")
    return fn_split_floor(c, r)


def quota_advance(q):
    _check_list(q)
    return [fn_index(q, 0), fn_add(fn_index(q, 1), fn_index(q, 0))]


def points_ledger(e):
    _check_list(e)
    # preconditions
    if not (pre_min_source_id(e) >= 1):
        raise ValueError("NotTraceable")
    return fn_enumerate_ledger(e)


# ============ 操作函数字典 ============
OP_FUNCS = {
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


# ============ 测试输入求值 (处理嵌套 op 和 $_) ============

def eval_test_input(input_val, op_funcs, last_result=None):
    """
    求值测试 input，处理嵌套 {"op": "...", "args": [...]} 调用和 "$_" 引用。
    """
    if isinstance(input_val, dict):
        if "op" in input_val:
            op_name = input_val["op"]
            args = [eval_test_input(a, op_funcs, last_result) for a in input_val["args"]]
            return op_funcs[op_name](*args)
        else:
            raise ValueError(f"Unknown input dict: {input_val}")
    elif isinstance(input_val, str):
        if input_val == "$_":
            return last_result
        else:
            try:
                return int(input_val)
            except ValueError:
                raise ValueError(f"Unknown input string: {input_val}")
    elif isinstance(input_val, list):
        return [eval_test_input(item, op_funcs, last_result) for item in input_val]
    elif isinstance(input_val, int) or isinstance(input_val, bool):
        return input_val
    else:
        raise ValueError(f"Unknown input type: {type(input_val)}")


# ============ 结果比较 ============

def results_equal(actual, expected):
    if isinstance(actual, list) and isinstance(expected, list):
        if len(actual) != len(expected):
            return False
        for a, e in zip(actual, expected):
            if not results_equal(a, e):
                return False
        return True
    return actual == expected


# ============ 主测试运行器 ============

if __name__ == "__main__":
    import json
    import sys
    from datetime import datetime

    spec_path = r"E:\IDEProjects\AI\sigma-lang\spec\spec_p0_socketkit.json"
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    passed = 0
    total = 0
    failures = []

    last_result = None

    for op in spec["operations"]:
        op_name = op["name"]
        op_func = OP_FUNCS[op_name]
        for test in op["tests"]:
            total += 1
            test_desc = test.get("description", "")
            try:
                # 求值输入参数
                input_args = eval_test_input(test["input"], OP_FUNCS, last_result)
                if not isinstance(input_args, list):
                    input_args = [input_args]
                # 调用操作函数
                actual = op_func(*input_args)
                # 保存 last_result (用于序列测试的 "$_")
                last_result = actual
                # 检查期望
                if "error" in test and test["error"] is not None:
                    failures.append({
                        "op": op_name,
                        "desc": test_desc,
                        "expected": f"Error: {test['error']}",
                        "actual": f"Value: {actual}",
                    })
                    print(f"FAIL [{op_name}] {test_desc}: expected error {test['error']}, got value {actual}")
                elif "output" in test:
                    expected = test["output"]
                    if results_equal(actual, expected):
                        passed += 1
                        print(f"PASS [{op_name}] {test_desc}")
                    else:
                        failures.append({
                            "op": op_name,
                            "desc": test_desc,
                            "expected": str(expected),
                            "actual": str(actual),
                        })
                        print(f"FAIL [{op_name}] {test_desc}: expected {expected}, got {actual}")
                else:
                    failures.append({
                        "op": op_name,
                        "desc": test_desc,
                        "expected": "output or error field",
                        "actual": "neither specified",
                    })
            except ValueError as e:
                error_name = str(e)
                if "error" in test and test["error"] is not None:
                    if error_name == test["error"]:
                        passed += 1
                        last_result = None
                        print(f"PASS [{op_name}] {test_desc}: correct error {error_name}")
                    else:
                        failures.append({
                            "op": op_name,
                            "desc": test_desc,
                            "expected": f"Error: {test['error']}",
                            "actual": f"Error: {error_name}",
                        })
                        print(f"FAIL [{op_name}] {test_desc}: expected error {test['error']}, got error {error_name}")
                else:
                    failures.append({
                        "op": op_name,
                        "desc": test_desc,
                        "expected": str(test.get("output", "value")),
                        "actual": f"Error: {error_name}",
                    })
                    print(f"FAIL [{op_name}] {test_desc}: expected value, got error {error_name}")
            except Exception as e:
                failures.append({
                    "op": op_name,
                    "desc": test_desc,
                    "expected": test.get("output", test.get("error", "none")),
                    "actual": f"Unexpected {type(e).__name__}: {e}",
                })
                print(f"FAIL [{op_name}] {test_desc}: unexpected {type(e).__name__}: {e}")

    # 输出汇总
    print(f"\n=== 汇总 ===")
    print(f"通过: {passed} / {total}")
    print(f"通过率: {passed / total * 100:.1f}%")
    if failures:
        print(f"失败: {len(failures)}")
        for i, f in enumerate(failures[:5]):
            print(f"  {i+1}. [{f['op']}] {f['desc']}")
            print(f"     期望: {f['expected']}")
            print(f"     实际: {f['actual']}")

    # 生成报告
    report_path = r"E:\IDEProjects\AI\sigma-lang\tests\reports\Seed2dot1Turbo.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    rate = passed / total * 100

    report_lines = [
        f"# Seed2dot1Turbo × ΣLang §SK 实现报告",
        "",
        f"- **完成时间**: {now}",
        f"- **实现方式**: 直接实现 (逐行阅读 spec JSON，按 definition/preconditions 手写 22 个 Python 函数，加内置函数与测试运行器)",
        f"- **通过率**: {passed}/{total} ({rate:.1f}%)",
        "",
        f"## 失败清单 (如有)",
        f"| 操作 | 测试描述 | 期望 | 实际 |",
        f"|------|----------|------|------|",
    ]

    if failures:
        for f in failures:
            # 转义管道符和换行
            desc = f["desc"].replace("|", "\\|").replace("\n", " ")
            exp = str(f["expected"]).replace("|", "\\|").replace("\n", " ")
            act = str(f["actual"]).replace("|", "\\|").replace("\n", " ")
            report_lines.append(f"| {f['op']} | {desc} | {exp} | {act} |")
    else:
        report_lines.append("| - | 无 | - | - |")

    report_lines.extend([
        "",
        "## 实现说明",
        "",
        "1. **常量**: 使用 spec 顶层 constants 区的数值 (credit.initial=100, badge thresholds=[100,300,600], verifier_min_id=1000, team.min_capacity=1, ledger.min_source_id=1, credit.kind1_floor_ratio=7//10)。",
        "2. **内置函数**:",
        "   - `index(coll, i)`: 先类型检查 (非列表/非整数→TypeError)，越界→ShapeError。",
        "   - `fold_add(xs)`: xs 首元素为列表时，每行最后一个元素求和；否则普通 sum。",
        "   - `fold_credit(init, events)`: kind=0 逐次+5，kind=1 逐次×7//10，下限 max(result, 0)。",
        "   - `split_floor(contribs, reward)`: share = floor(reward × c / total)，total==0→DivByZero。",
        "   - `enumerate_ledger(entries)`: 输出 [新编号, source, 金额]，编号从 1 起；source<1→NotTraceable；金额<0→TypeError。",
        "3. **22 个操作**: 严格按 definition.body 的结构实现，不偷工简化。前置条件按 TASK_SPEC 3.3 规则——失败抛 ValueError(错误名)，错误名与 tests.error 完全一致。",
        "4. **类型守卫**: 列表参数收非列表 (如 review_merge(3)) 统一抛 ValueError('TypeError')；index 越界抛 ShapeError。",
        "5. **测试运行器**: 处理嵌套 op 调用 (先递归求值 args 再调函数)；支持 \"$_\" 引用上一操作结果；用深比较 (列表逐元素相等) 判定通过。",
        "",
        "## 困难与建议",
        "",
        "- **歧义点 1**：`fold_add` 在 xs 为空列表时行为——按「否则普通求和」即 sum([])=0，这与 contribution_score([[]]) 的隐含测试期望一致 (贡献为 0 时 floor(0,0)=0)。",
        "- **歧义点 2**：`points_ledger` 的 preconditions 用 min_source_id(e) >= 1 检测 NotTraceable；在 enumerate_ledger 内部再重复检查 source>=1 一次，双保险避免漏检。",
        "- **歧义点 3**：`credit_score` 中 kind1 的 count 次循环是逐次应用 ×7//10 还是一次性应用 (count=2 时 100→49 而非 100×49/100=49，两者碰巧相同，但 count=3 时 100→34 vs 34.3，必须用逐次)。",
        "- **建议**：spec 中 tests 覆盖了大多数边界，结构清晰；可以考虑给内置函数的每条语义加一个 law 级别的测试，以便独立实现者在遇到歧义时有更明确的锚点。",
        "",
        "## 声明",
        "- 我确认未参考仓库内已有实现 (sigma_core.py / sigma_engine.py / corpus/ / impl/verifier/ / impl/elixir_rt/ 等)。",
    ])

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\n报告已写入: {report_path}")
    sys.exit(0 if passed == total else 1)
