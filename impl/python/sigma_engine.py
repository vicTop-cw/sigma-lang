#!/usr/bin/env python3
"""
ΣLang 通用 spec→verifier 引擎 — sigma_engine.py
=================================================
整改项 4.4：把「人手写 verifier」改为「引擎读 spec JSON 自动求值」。

设计原则（与 spec/json-schema.md v1.0 一一对应）：
  * 引擎只做「表达式求值 + 前置条件检查 + 表驱动状态转移」，不做定律证明。
  * 单一文件、stdlib-only（json / sys / os / functools），不依赖任何第三方包。
  * 错误名与参考实现 sigma_core.py 一致（§SK 段以 ValueError("Name") 抛出命名错误，
    本引擎直接抛同名的异常类，corpus 按异常类名匹配）。

用法：
    python3 sigma_engine.py                     # 内置自检：优先加载 spec JSON，否则用内置示例 spec
    python3 sigma_engine.py --spec <path.json>  # 加载指定 spec 并跑其 corpus（tests 数组）
    python3 sigma_engine.py --check-only        # 只做引擎能力自检，不跑 corpus

表达式节点语法（见 schema "definition 表达式的语法"）：
    * 字面量         : 整数 / 字符串 / 布尔
    * 参数引用       : 字符串与 definition.params 中的名字匹配时即参数引用；否则视为字符串字面量
    * 嵌套调用       : {"op": "op_name", "args": [expr, ...]}
    * 列表构造       : {"list": [expr, ...]}（裸列表同样按列表构造求值）
    * 映射构造       : {"map": {key: expr, ...}}（Map<K,V> 字面量，键为字符串，值为表达式）
    * 条件           : {"if": cond, "then": expr, "else": expr}
    * 内置函数       : {"fn": "name", "args": [...]}，见 BUILTIN_FNS 词汇表
    * 上一个结果     : "$_"（corpus 序列测试用；也允许在 corpus input 中直接嵌入 {"op": ...}
                       表达式节点，引擎先求值再作为入参）
    * 条件节点 cond  : {"field": i, "eq|ne|gt|ge|lt|le": v}（对首个列表参数/状态值取字段）、
                       {"expr": "b >= 0"}（受限求值的表达式串）、
                       {"fn": ...} / {"op": ...}（表达式求值后取布尔）、
                       {"not": ...} / {"and": [...]} / {"or": [...]}

kind=table 状态机（schema 原生支持；§SK v0.30 JSON 用 lambda+preconditions 表达等价语义）：
    table 行: {"when": cond, "set": [{"field": i, "value": expr}, ...], "guard": {"expr": ..., "error": "AuthError"}}
    按序匹配第一行 when；guard 失败 → 抛 guard.error；无行匹配 → 抛 definition.default_error（默认 StateError）。
    table 作用于第一个参数（状态值），返回其修改副本。

内置函数词汇表（BUILTIN_FNS，可经 register_builtin 扩展）：
    通用:     index / len / min / max / fold_add / map / add / sub / mul / floordiv / div / mod
              （div: 真除法 int/int → float，除零 → DivByZero；§IN fill_rate ℚ 语义）
    类型扩展: str_len / str_concat / str_contains（Str 字符串）
              time_now_epoch（Time，unix epoch，返回固定种子便于测试）
              option_some / option_none（Option<T>：None=none，非 None=some）
              map_get（Map<K,V> 取键；映射字面量 {"map": {k: expr}}）
    §SK 专属: weighted_accept / weighted_reject / weighted_support（加权评审/督导求和）
              fold_credit（契分折叠：kind 0 +5×count，kind 1 ×0.7 逐次取整，下限 0）
              split_floor（团队按贡献分配：floor(r·cᵢ/Σc)，Σc=0 → DivByZero）
              enumerate_ledger（积分台账编号：[[i, source_id, amount]]，source<1 → NotTraceable）
    §SK 前置条件辅助: sum_contribs / min_source_id（见 EXPR_HELPERS）

注：fold_add 对 List<nat> 为普通求和；对 List<List<nat>> 折叠各子列表末列
（§SK 语义：Action 的 delta 列、share 的 share 列），由 corpus 测试反推确定。
"""

import json
import os
import sys
from functools import reduce

__version__ = "0.3.1"   # 0.3.1: 新增通用 div（真除法，float 结果，除零 → DivByZero；§IN fill_rate 的 ℚ 语义需要）
                         # 0.3.0: 整改项 4.7 类型扩展（Str / Time / Option<T> / Map<K,V>）

# ---------------------------------------------------------------------------
# 命名错误体系（与 spec/json-schema.md「错误名约定」一致，共 20 个）
# ---------------------------------------------------------------------------

ERROR_NAMES = [
    "BountyErr", "StateError", "AuthError", "TypeError", "ShapeError",
    "QuotaExhausted", "InsufficientEscrow", "InsufficientPoints",
    "InsufficientStock", "TeamFull", "InsufficientFunds", "UnknownAsset",
    "InsufficientShares", "UnknownItem", "DivByZero", "NotTraceable",
    "ReserveErr", "BidAmountErr", "ClosedErr", "TimeoutErr",
]

_COMPARATORS = {
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "gt": lambda a, b: a > b,
    "ge": lambda a, b: a >= b,
    "lt": lambda a, b: a < b,
    "le": lambda a, b: a <= b,
}


class SigmaSpecError(Exception):
    """所有 spec 命名错误的基类；err.name 即规范错误名。"""

    def __init__(self, message=""):
        super().__init__(message)
        self.message = message
        self.name = self.__class__.__name__


# 动态生成 20 个命名异常类：BountyErr / StateError / AuthError / ...
ERROR_CLASSES = {n: type(n, (SigmaSpecError,), {}) for n in ERROR_NAMES}


class UnknownOpError(SigmaSpecError):
    """引擎内部错误：引用了 spec 中不存在的操作。"""


class SpecValidationError(SigmaSpecError):
    """引擎内部错误：spec JSON 结构不符合 schema。"""


def _raise_error(name, message=""):
    """按名字抛规范错误；未注册的错误名回退为 ValueError(name)，与参考实现行为一致。"""
    cls = ERROR_CLASSES.get(name)
    if cls is not None:
        raise cls(message)
    raise ValueError(name)


def _require_list(x, fn_name):
    if not isinstance(x, list):
        _raise_error("TypeError", f"{fn_name}: expected a list, got {type(x).__name__}")
    return x


def _require_int(x, fn_name):
    if not isinstance(x, int) or isinstance(x, bool):
        _raise_error("TypeError", f"{fn_name}: expected an int, got {x!r}")
    return x


def _require_str(x, fn_name):
    if not isinstance(x, str):
        _raise_error("TypeError", f"{fn_name}: expected a str, got {type(x).__name__}")
    return x


# ---------------------------------------------------------------------------
# 内置函数词汇表（通用 + §SK 专属，语义对齐 sigma_core.py §SK 段）
# ---------------------------------------------------------------------------

def _fn_index(xs, i):
    _require_list(xs, "index")
    _require_int(i, "index")
    try:
        return xs[i]
    except IndexError:
        _raise_error("ShapeError", f"index: index {i} out of range for list of len {len(xs)}")


def _fn_len(xs):
    return len(_require_list(xs, "len"))


def _fn_min(*args):
    if len(args) == 1:
        return min(_require_list(args[0], "min"))
    return min(_require_int(a, "min") for a in args)


def _fn_max(*args):
    if len(args) == 1:
        return max(_require_list(args[0], "max"))
    return max(_require_int(a, "max") for a in args)


def _fn_fold_add(xs):
    """List<nat> → 普通求和；List<List<nat>> → 折叠各子列表末列（§SK：delta / share 列）。"""
    _require_list(xs, "fold_add")
    if xs and all(isinstance(x, list) for x in xs):
        return sum(x[-1] for x in xs)
    return sum(xs)


def _fn_map(xs, field):
    _require_list(xs, "map")
    _require_int(field, "map")
    return [x[field] for x in xs]


def _fn_add(*args):
    return reduce(lambda a, b: a + b, (_require_int(x, "add") for x in args))


def _fn_sub(*args):
    return reduce(lambda a, b: a - b, (_require_int(x, "sub") for x in args))


def _fn_mul(*args):
    return reduce(lambda a, b: a * b, (_require_int(x, "mul") for x in args))


def _fn_floordiv(a, b):
    _require_int(a, "floordiv")
    _require_int(b, "floordiv")
    if b == 0:
        _raise_error("DivByZero", "floordiv: division by zero")
    return a // b


def _fn_div(a, b):
    """真除法（§IN fill_rate 的 ℚ 语义）：int/int → float；除零 → DivByZero。"""
    _require_int(a, "div")
    _require_int(b, "div")
    if b == 0:
        _raise_error("DivByZero", "div: division by zero")
    return a / b


def _fn_mod(a, b):
    _require_int(a, "mod")
    _require_int(b, "mod")
    if b == 0:
        _raise_error("DivByZero", "mod: division by zero")
    return a % b


def _fn_eq(a, b):
    return a == b


def _fn_ne(a, b):
    return a != b


def _fn_lt(a, b):
    return a < b


def _fn_le(a, b):
    return a <= b


def _fn_gt(a, b):
    return a > b


def _fn_ge(a, b):
    return a >= b


def _fn_weighted(xs, vote_value, fn_name):
    """加权求和：对 [reviewer, vote/side, weight] 行，取 vote==vote_value 的权重和。"""
    _require_list(xs, fn_name)
    total = 0
    for row in xs:
        _require_list(row, fn_name)
        if len(row) < 3:
            _raise_error("TypeError", f"{fn_name}: row {row!r} has fewer than 3 fields")
        if row[1] == vote_value:
            total += row[2]
    return total


def _fn_weighted_accept(xs):
    return _fn_weighted(xs, 1, "weighted_accept")


def _fn_weighted_reject(xs):
    return _fn_weighted(xs, 0, "weighted_reject")


def _fn_weighted_support(xs):
    return _fn_weighted(xs, 1, "weighted_support")


def _fn_fold_credit(init, events):
    """契分折叠（§SK.3.7）：base；kind 0 每次 +5×count；kind 1 每次 ×7//10（逐次取整）；下限 0。"""
    _require_int(init, "fold_credit")
    _require_list(events, "fold_credit")
    credit = init
    for event in events:
        _require_list(event, "fold_credit")
        if len(event) < 2:
            _raise_error("TypeError", f"fold_credit: event {event!r} has fewer than 2 fields")
        kind, count = event[0], event[1]
        if kind == 0:
            credit += 5 * count
        elif kind == 1:
            for _ in range(count):
                credit = (credit * 7) // 10
        else:
            _raise_error("TypeError", f"fold_credit: unknown event kind {kind}")
    return max(0, credit)


def _fn_split_floor(contribs, reward):
    """团队收益按贡献分配（§SK.3.15）：shareᵢ = floor(r · cᵢ / Σc)；Σc = 0 → DivByZero。"""
    _require_list(contribs, "split_floor")
    _require_int(reward, "split_floor")
    total = 0
    rows = []
    for row in contribs:
        _require_list(row, "split_floor")
        if len(row) < 2:
            _raise_error("TypeError", f"split_floor: row {row!r} has fewer than 2 fields")
        rows.append(row)
        total += row[1]
    if total == 0:
        _raise_error("DivByZero", "split_floor: total contribution is 0")
    return [[m, (reward * c) // total] for m, c in rows]


def _fn_enumerate_ledger(entries):
    """积分台账编号（§SK.3.17）：entries → [[entry_id, source_id, amount], …]；source < 1 → NotTraceable。"""
    _require_list(entries, "enumerate_ledger")
    ledger = []
    for i, entry in enumerate(entries, 1):
        _require_list(entry, "enumerate_ledger")
        if len(entry) < 3:
            _raise_error("TypeError", f"enumerate_ledger: entry {entry!r} has fewer than 3 fields")
        _, amount, source_id = entry[0], entry[1], entry[2]
        if source_id < 1:
            _raise_error("NotTraceable", f"enumerate_ledger: source_id {source_id} not traceable")
        if amount < 0:
            _raise_error("TypeError", f"enumerate_ledger: negative amount {amount}")
        ledger.append([i, source_id, amount])
    return ledger


# ---------------------------------------------------------------------------
# 类型扩展（整改项 4.7）：Str / Time / Option<T> / Map<K,V>
# ---------------------------------------------------------------------------

#: time_now_epoch 的固定种子（unix epoch 秒）；确定性测试用，不依赖真实时钟
TIME_EPOCH_SEED = 1700000000


def _fn_str_len(s):
    """Str：字符串长度。"""
    return len(_require_str(s, "str_len"))


def _fn_str_concat(*parts):
    """Str：拼接一个或多个字符串。"""
    return "".join(_require_str(p, "str_concat") for p in parts)


def _fn_str_contains(haystack, needle):
    """Str：子串包含判断。"""
    _require_str(haystack, "str_contains")
    _require_str(needle, "str_contains")
    return needle in haystack


def _fn_time_now_epoch():
    """Time：当前 unix epoch 秒；返回固定种子 TIME_EPOCH_SEED 便于确定性测试。"""
    return TIME_EPOCH_SEED


def _fn_option_some(x):
    """Option<T> 构造：非 None 值即 some(T)；None 表示 none，不接受 None 入参。"""
    if x is None:
        _raise_error("TypeError", "option_some: None denotes none; wrap a non-None value")
    return x


def _fn_option_none():
    """Option<T> 构造：返回 None（= none）。"""
    return None


def _fn_map_get(m, key):
    """Map<K,V> 取键：未命中返回 None（配合 Option 语义：none）。"""
    if not isinstance(m, dict):
        _raise_error("TypeError", f"map_get: expected a Map (dict), got {type(m).__name__}")
    return m.get(key)


BUILTIN_FNS = {
    "index": _fn_index,
    "len": _fn_len,
    "min": _fn_min,
    "max": _fn_max,
    "fold_add": _fn_fold_add,
    "map": _fn_map,
    "add": _fn_add,
    "sub": _fn_sub,
    "mul": _fn_mul,
    "floordiv": _fn_floordiv,
    "div": _fn_div,
    "mod": _fn_mod,
    # 比较运算符（§SK: 条件里以 fn 节点出现，如 {"fn": "ge", ...} / {"fn": "lt", ...}）
    "eq": _fn_eq,
    "ne": _fn_ne,
    "lt": _fn_lt,
    "le": _fn_le,
    "gt": _fn_gt,
    "ge": _fn_ge,
    # §SK 专属
    "weighted_accept": _fn_weighted_accept,
    "weighted_reject": _fn_weighted_reject,
    "weighted_support": _fn_weighted_support,
    "fold_credit": _fn_fold_credit,
    "split_floor": _fn_split_floor,
    "enumerate_ledger": _fn_enumerate_ledger,
    # 类型扩展（整改项 4.7）：Str / Time / Option<T> / Map<K,V>
    "str_len": _fn_str_len,
    "str_concat": _fn_str_concat,
    "str_contains": _fn_str_contains,
    "time_now_epoch": _fn_time_now_epoch,
    "option_some": _fn_option_some,
    "option_none": _fn_option_none,
    "map_get": _fn_map_get,
}

# 前置条件表达式串（preconditions 的 "expr"）中可用的辅助函数
EXPR_HELPERS = {
    "min": min, "max": max, "len": len, "abs": abs, "sum": sum,
    "index": lambda xs, i: xs[i],
    "sum_contribs": lambda c: sum(x[1] for x in c),
    "min_source_id": lambda e: min((x[2] for x in e), default=10 ** 9),
}


# ---------------------------------------------------------------------------
# 表达式求值器（受限求值：仅参数名 + 白名单辅助函数，无 __builtins__）
# ---------------------------------------------------------------------------

class _ExprEvaluator:
    """共享表达式求值逻辑；SigmaEngine 继承之，以便嵌套调用回到 engine.eval。"""

    # ---- 表达式节点 ------------------------------------------------------

    def _eval_node(self, node, env):
        """求值一个表达式节点，返回其值。"""
        if node is None:
            return None
        if isinstance(node, bool):
            return node
        if isinstance(node, (int, float)):
            return node
        if isinstance(node, str):
            if node == "$_":
                if self._last_result is None:
                    raise SigmaSpecError("'$_' used before any operation result exists")
                return self._last_result
            if node in env:
                return env[node]
            return node  # 字符串字面量
        if isinstance(node, list):
            return [self._eval_node(x, env) for x in node]  # 裸列表 = 列表构造
        if isinstance(node, dict):
            if "op" in node:  # 嵌套调用
                return self.eval(node["op"],
                                 [self._eval_node(a, env) for a in node.get("args", [])])
            if "list" in node:
                return [self._eval_node(x, env) for x in node["list"]]
            if "map" in node:
                return {k: self._eval_node(v, env) for k, v in node["map"].items()}
            if "if" in node:  # 条件
                ctx = self._first_list_param(env)
                if self._eval_cond(node["if"], env, ctx):
                    return self._eval_node(node["then"], env)
                return self._eval_node(node.get("else"), env)
            if "fn" in node:
                return self._eval_fn(node, env)
            raise SpecValidationError(f"invalid expression node: {node!r}")
        raise SpecValidationError(f"invalid expression node type: {type(node).__name__}")

    def _eval_fn(self, node, env):
        """内置函数调用：按名称查 self.builtin_fns 词汇表。"""
        name = node["fn"]
        fn = self.builtin_fns.get(name)
        if fn is None:
            _raise_error("TypeError", f"unknown builtin fn: {name}")
        args = [self._eval_node(a, env) for a in node.get("args", [])]
        return fn(*args)

    # ---- 条件节点 --------------------------------------------------------

    def _eval_cond(self, cond, env, ctx):
        """求值条件节点（when / guard / if 的条件）。ctx 为 field 引用的状态值。"""
        if isinstance(cond, bool):
            return cond
        if isinstance(cond, dict):
            if "expr" in cond:
                return bool(self._eval_expr(cond["expr"], env))
            if "fn" in cond or "op" in cond:  # §SK: 条件可直接是表达式（如 fn ge/lt）
                return bool(self._eval_node(cond, env))
            if "not" in cond:
                return not self._eval_cond(cond["not"], env, ctx)
            if "and" in cond:
                return all(self._eval_cond(c, env, ctx) for c in cond["and"])
            if "or" in cond:
                return any(self._eval_cond(c, env, ctx) for c in cond["or"])
            if "field" in cond:
                op = next((k for k in _COMPARATORS if k in cond), None)
                if op is None or ctx is None:
                    raise SpecValidationError(f"invalid field condition: {cond!r}")
                val = ctx[cond["field"]]
                target = cond[op]
                if isinstance(target, (dict, list)):
                    target = self._eval_node(target, env)
                return bool(_COMPARATORS[op](val, target))
            raise SpecValidationError(f"invalid condition node: {cond!r}")
        raise SpecValidationError(f"invalid condition: {cond!r}")

    # ---- 受限表达式串（preconditions / 条件 expr） -------------------------

    def _eval_expr(self, expr, env):
        """受限 eval：无 __builtins__，仅参数名 + 白名单辅助函数。spec JSON 属受信输入。"""
        namespace = dict(self.expr_helpers)
        namespace.update(env)
        try:
            return eval(expr, {"__builtins__": {}}, namespace)  # noqa: S307
        except ZeroDivisionError:
            _raise_error("DivByZero", expr)
        except Exception as e:  # 语法/名字错误 → 引擎校验错误
            raise SpecValidationError(f"bad precondition expr {expr!r}: {e}") from e

    @staticmethod
    def _first_list_param(env):
        """if 条件里 field 引用的默认上下文：第一个列表参数（状态值）。"""
        for v in env.values():
            if isinstance(v, list):
                return v
        return None


# ---------------------------------------------------------------------------
# SigmaEngine — spec→verifier 引擎
# ---------------------------------------------------------------------------

#: 优先加载的 spec JSON 路径（§SK 已落地 v0.30）
DEFAULT_SPEC_PATH = r"E:\IDEProjects\AI\sigma-lang\spec\spec_p0_socketkit.json"


class SigmaEngine(_ExprEvaluator):
    """按 spec JSON 定义自动求值的通用 verifier 引擎。"""

    def __init__(self, spec=None):
        super().__init__()
        self.spec = spec
        self.operations = {}                 # name -> OperationDecl
        self.types = {}                      # name -> TypeDecl
        self.builtin_fns = dict(BUILTIN_FNS)  # 实例级词汇表，可 register_builtin 扩展
        self.expr_helpers = dict(EXPR_HELPERS)
        self._last_result = None             # "$_" 指向的上一个操作结果
        if spec is not None:
            self._load(spec)

    # ---- 加载 / 扩展 -----------------------------------------------------

    @classmethod
    def from_spec(cls, path):
        """从 JSON 文件加载 spec。"""
        with open(path, "r", encoding="utf-8") as f:
            spec = json.load(f)
        return cls(spec)

    def _load(self, spec):
        if not isinstance(spec, dict) or not isinstance(spec.get("operations"), list):
            raise SpecValidationError("spec JSON must be an object with an 'operations' list")
        self.spec = spec
        self.types = {t.get("name"): t for t in spec.get("types", [])}
        self.operations = {}
        for op in spec.get("operations", []):
            if not isinstance(op, dict) or not op.get("name"):
                raise SpecValidationError("each operation needs a 'name'")
            self.operations[op["name"]] = op

    def register_builtin(self, name, fn):
        """注册/覆盖一个内置函数（供新 spec 模块扩展词汇表）。"""
        self.builtin_fns[name] = fn

    # ---- 操作求值 --------------------------------------------------------

    def eval(self, op_name, args):
        """按 spec 求值操作：签名校验 → 前置条件 → definition 求值。"""
        op = self.operations.get(op_name)
        if op is None:
            raise UnknownOpError(f"unknown operation: {op_name}")
        sig = op.get("signature", {})
        n_params = len(sig.get("params", []))
        if len(args) != n_params:
            _raise_error("ShapeError",
                         f"{op_name}: expected {n_params} arg(s), got {len(args)}")
        definition = op.get("definition") or {}
        params = definition.get("params") or [f"arg{i}" for i in range(n_params)]
        env = dict(zip(params, args))
        for pc in op.get("preconditions", []):      # 前置条件：先于求值
            self._check_precondition(pc, env, op_name)
        kind = definition.get("kind", "lambda")
        if kind == "table":
            result = self._eval_table(op, args, env)
        elif kind in ("lambda", "expression"):
            result = self._eval_node(definition["body"], env)
        else:
            raise SpecValidationError(f"{op_name}: unknown definition kind {kind!r}")
        self._last_result = result                  # 更新 "$_" 指向
        return result

    def _check_precondition(self, pc, env, op_name):
        expr = pc.get("expr")
        if expr is None:
            raise SpecValidationError(f"{op_name}: precondition without 'expr'")
        if not self._eval_expr(expr, env):
            err = pc.get("error", "TypeError")
            desc = pc.get("description") or f"{op_name}: precondition failed: {expr}"
            _raise_error(err, desc)

    def _eval_table(self, op, args, env):
        """kind=table 状态机转移：按序匹配 when → 校验 guard → 应用 set。"""
        state = args[0]
        if not isinstance(state, list):
            _raise_error("TypeError", f"{op['name']}: table input must be a List")
        definition = op.get("definition", {})
        default_error = definition.get("default_error", "StateError")
        for row in definition.get("table", []):
            when = row.get("when")
            if when is not None and not self._eval_cond(when, env, state):
                continue
            guard = row.get("guard")
            if guard is not None:
                g_err = guard.get("error", default_error)
                g_cond = {k: v for k, v in guard.items() if k != "error"}
                if not self._eval_cond(g_cond, env, state):
                    _raise_error(g_err, f"{op['name']}: guard failed")
            result = list(state)
            sets = row.get("set") or []
            if isinstance(sets, dict):
                sets = [sets]
            for s in sets:
                idx = s.get("field")
                value = s.get("value")
                if idx is None or "value" not in s:
                    raise SpecValidationError(f"{op['name']}: set needs 'field' and 'value'")
                result[idx] = self._eval_node(value, env)
            return result
        _raise_error(default_error, f"{op['name']}: no table row matched for state {state!r}")

    # ---- corpus 测试序列 --------------------------------------------------

    def _resolve_input_node(self, x):
        """递归解析 corpus input 节点：表达式 dict（op/list/if/fn）先求值，"$_" 取上一个结果。"""
        if isinstance(x, dict):
            return self._eval_node(x, {})   # 表达式节点（如 {"op": "task_create", "args": [7, 100]}）
        if isinstance(x, list):
            return [self._resolve_input_node(v) for v in x]
        if x == "$_":
            if self._last_result is None:
                raise SigmaSpecError("'$_' in corpus input before any operation result")
            return self._last_result
        return x

    def run_corpus(self, ops=None):
        """按 spec 各操作的 tests 数组跑 corpus，返回 [(op, test, ok, detail), ...]。"""
        self._last_result = None  # "$_" 序列从头开始
        results = []
        for op in (ops if ops is not None else self.spec["operations"]):
            for t in op.get("tests", []):
                inputs = [self._resolve_input_node(v) for v in t["input"]]
                expected_err = t.get("error")
                expected_out = t.get("output")
                try:
                    out = self.eval(op["name"], inputs)
                except SigmaSpecError as e:
                    got = getattr(e, "name", None) or e.__class__.__name__
                    if expected_err and got == expected_err:
                        results.append((op["name"], t, True, f"expected error {expected_err}"))
                    elif expected_err:
                        results.append((op["name"], t, False,
                                        f"expected error {expected_err}, got {got}"))
                    else:
                        results.append((op["name"], t, False, f"unexpected {got}: {e}"))
                except Exception as e:
                    results.append((op["name"], t, False,
                                    f"unexpected exception {type(e).__name__}: {e}"))
                else:
                    if expected_err:
                        results.append((op["name"], t, False,
                                        f"expected error {expected_err}, got {out!r}"))
                    elif out == expected_out:
                        results.append((op["name"], t, True, f"{out!r}"))
                    else:
                        results.append((op["name"], t, False,
                                        f"expected {expected_out!r}, got {out!r}"))
        return results


# ---------------------------------------------------------------------------
# 内置最小示例 spec（§SK JSON 缺失时用于引擎自检；结构严格符合 json-schema.md）
# ---------------------------------------------------------------------------

BUILTIN_SPEC = r"""
{
  "spec": "§SK",
  "version": "0.7.0-builtin-sample",
  "fingerprint_prefix": "0xF000",
  "types": [
    {"name": "Task", "kind": "alias", "target": "List<nat>"},
    {"name": "Action", "kind": "alias", "target": "List<nat>"},
    {"name": "Quota", "kind": "alias", "target": "List<nat>"}
  ],
  "operations": [
    {
      "name": "task_create",
      "fingerprint": "0xF001",
      "signature": {"params": ["nat", "nat"], "returns": "Task"},
      "definition": {"kind": "lambda", "params": ["a", "b"], "body": ["a", "b", 0, 0]},
      "preconditions": [
        {"expr": "b >= 0", "error": "BountyErr", "description": "reserve must be >= 0"}
      ],
      "tests": [
        {"input": [2, 0], "output": [2, 0, 0, 0], "description": "zero bounty ok"},
        {"input": [7, 100], "output": [7, 100, 0, 0], "description": "basic create (feeds $_)"},
        {"input": [1, -5], "output": null, "error": "BountyErr", "description": "negative bounty"}
      ]
    },
    {
      "name": "accept_task",
      "fingerprint": "0xF002",
      "signature": {"params": ["Task", "nat"], "returns": "Task"},
      "definition": {
        "kind": "table",
        "params": ["task", "hunter"],
        "table": [
          {"when": {"field": 2, "eq": 0},
           "set": [{"field": 2, "value": 1}, {"field": 3, "value": "hunter"}]}
        ],
        "default_error": "StateError"
      },
      "tests": [
        {"input": ["$_", 3], "output": [7, 100, 1, 3], "description": "claim open task (corpus chain)"},
        {"input": ["$_", 5], "output": null, "error": "StateError", "description": "claim non-open task"}
      ]
    },
    {
      "name": "task_submit",
      "fingerprint": "0xF003",
      "signature": {"params": ["Task"], "returns": "Task"},
      "definition": {
        "kind": "table",
        "params": ["task"],
        "table": [{"when": {"field": 2, "eq": 1}, "set": [{"field": 2, "value": 2}]}],
        "default_error": "StateError"
      },
      "tests": [
        {"input": ["$_"], "output": [7, 100, 2, 3], "description": "submit in-progress task (corpus chain)"}
      ]
    },
    {
      "name": "task_accept",
      "fingerprint": "0xF004",
      "signature": {"params": ["Task", "nat"], "returns": "Task"},
      "definition": {
        "kind": "table",
        "params": ["task", "caller"],
        "table": [
          {"when": {"field": 2, "eq": 2},
           "guard": {"expr": "caller == task[0]", "error": "AuthError"},
           "set": [{"field": 2, "value": 3}]}
        ],
        "default_error": "StateError"
      },
      "tests": [
        {"input": ["$_", 7], "output": [7, 100, 3, 3], "description": "author accepts pending task (corpus chain)"},
        {"input": [[7, 100, 2, 3], 9], "output": null, "error": "AuthError", "description": "non-author rejected"},
        {"input": [[5, 50, 0, 0], 5], "output": null, "error": "StateError", "description": "accept non-pending task"}
      ]
    },
    {
      "name": "contribution_score",
      "fingerprint": "0xF005",
      "signature": {"params": ["List<Action>"], "returns": "nat"},
      "definition": {
        "kind": "lambda",
        "params": ["actions"],
        "body": {"fn": "max", "args": [0,
                 {"fn": "fold_add", "args": [{"fn": "map", "args": ["actions", 2]}]}]}
      },
      "tests": [
        {"input": [[[1, 1, 3], [2, 2, 4]]], "output": 7, "description": "fold over deltas"},
        {"input": [[[1, 1, -5], [2, 2, 3]]], "output": 0, "description": "negative floored at 0"}
      ]
    },
    {
      "name": "quota_new",
      "fingerprint": "0xF006",
      "signature": {"params": ["nat"], "returns": "Quota"},
      "definition": {"kind": "lambda", "params": ["monthly"], "body": ["monthly", "monthly"]},
      "preconditions": [
        {"expr": "monthly >= 0", "error": "TypeError", "description": "monthly must be >= 0"}
      ],
      "tests": [
        {"input": [10], "output": [10, 10], "description": "fresh quota"},
        {"input": [-3], "output": null, "error": "TypeError", "description": "negative monthly"}
      ]
    },
    {
      "name": "quota_use",
      "fingerprint": "0xF007",
      "signature": {"params": ["Quota", "nat"], "returns": "Quota"},
      "definition": {
        "kind": "lambda",
        "params": ["quota", "amount"],
        "body": {"list": [{"fn": "index", "args": ["quota", 0]},
                          {"fn": "sub", "args": [{"fn": "index", "args": ["quota", 1]}, "amount"]}]}
      },
      "preconditions": [
        {"expr": "amount <= quota[1]", "error": "QuotaExhausted", "description": "remaining quota"}
      ],
      "tests": [
        {"input": [[10, 10], 4], "output": [10, 6], "description": "spend within quota"},
        {"input": [[10, 2], 9], "output": null, "error": "QuotaExhausted", "description": "quota exhausted"}
      ]
    },
    {
      "name": "badge_level",
      "fingerprint": "0xF008",
      "signature": {"params": ["nat"], "returns": "nat"},
      "definition": {
        "kind": "lambda",
        "params": ["score"],
        "body": {"if": {"expr": "score >= 600"}, "then": 3,
                 "else": {"if": {"expr": "score >= 300"}, "then": 2,
                          "else": {"if": {"expr": "score >= 100"}, "then": 1, "else": 0}}}
      },
      "tests": [
        {"input": [700], "output": 3, "description": "diamond"},
        {"input": [50], "output": 0, "description": "bronze"}
      ]
    },
    {
      "name": "task_submit_claim",
      "fingerprint": "0xF009",
      "signature": {"params": ["Task", "nat"], "returns": "Task"},
      "definition": {
        "kind": "lambda",
        "params": ["task", "hunter"],
        "body": {"op": "task_submit",
                 "args": [{"op": "accept_task", "args": ["task", "hunter"]}]}
      },
      "tests": [
        {"input": [[5, 50, 0, 0], 3], "output": [5, 50, 2, 3], "description": "nested call chain"}
      ]
    }
  ]
}
"""


# ---------------------------------------------------------------------------
# 内置自检
# ---------------------------------------------------------------------------

def _expect_error(engine, exc_name, op_name, args):
    """断言 eval 抛出名为 exc_name 的规范错误。"""
    try:
        engine.eval(op_name, args)
    except SigmaSpecError as e:
        got = getattr(e, "name", None) or e.__class__.__name__
        if got == exc_name:
            return True
        raise AssertionError(f"{op_name}{args}: expected {exc_name}, got {got}: {e}")
    raise AssertionError(f"{op_name}{args}: expected {exc_name}, no error raised")


def _selftest(engine):
    """引擎能力自检：表达式原语（不依赖具体 spec）+ §SK 操作级检查（存在性守卫）。"""
    checks = []
    total = 0

    def check(name, fn):
        nonlocal total
        total += 1
        try:
            fn()
        except Exception as e:
            checks.append((name, False, f"{type(e).__name__}: {e}"))
        else:
            checks.append((name, True, "ok"))

    # —— 表达式求值器原语 ——
    check("expr.literal_int", lambda: engine._eval_node(42, {}) == 42)
    check("expr.literal_str", lambda: engine._eval_node("hello", {}) == "hello")
    check("expr.param_ref", lambda: engine._eval_node("b", {"b": 7}) == 7)
    check("expr.raw_list_construct", lambda: (
        engine._eval_node(["a", 1, True], {"a": 5}) == [5, 1, True]))
    check("expr.list_node", lambda: (
        engine._eval_node({"list": [1, "x"]}, {"x": 9}) == [1, 9]))
    check("expr.fn_index", lambda: (
        engine._eval_node({"fn": "index", "args": [[10, 20], 1]}, {}) == 20))
    check("expr.fn_min", lambda: (
        engine._eval_node({"fn": "min", "args": [[3, 1, 2]]}, {}) == 1))
    check("expr.fn_len", lambda: (
        engine._eval_node({"fn": "len", "args": [[1, 2]]}, {}) == 2))
    check("expr.if_expr_cond", lambda: (
        engine._eval_node({"if": {"expr": "x > 5"}, "then": "big", "else": "small"},
                          {"x": 9}) == "big"))
    check("expr.if_field_cond", lambda: (
        engine._eval_node({"if": {"field": 2, "eq": 0}, "then": 1, "else": 2},
                          {"t": [7, 100, 0, 0]}) == 1))
    check("expr.if_fn_cond", lambda: (
        engine._eval_node({"if": {"fn": "ge", "args": [5, 3]}, "then": 1, "else": 0}, {}) == 1))
    if "task_create" in engine.operations:
        check("expr.dollar_last_result", lambda: (
            engine.eval("task_create", [7, 100]) is not None
            and engine._eval_node("$_", {}) == [7, 100, 0, 0]))

    # —— 类型扩展（整改项 4.7）：Str / Time / Option<T> / Map<K,V> ——

    def check_fn_type_error(fn_name, args):
        try:
            engine._eval_node({"fn": fn_name, "args": args}, {})
        except SigmaSpecError as e:
            if getattr(e, "name", None) == "TypeError":
                return
            raise AssertionError(f"{fn_name}: expected TypeError, got {e.name}: {e}")
        raise AssertionError(f"{fn_name}: expected TypeError, no error raised")

    check("types.str_len", lambda: (
        engine._eval_node({"fn": "str_len", "args": ["hello"]}, {}) == 5))
    check("types.str_concat", lambda: (
        engine._eval_node({"fn": "str_concat", "args": ["foo", "bar"]}, {})
        == "foobar"))
    check("types.str_contains", lambda: (
        engine._eval_node({"fn": "str_contains", "args": ["hello", "ell"]}, {})
        is True))
    check("types.str_contains_miss", lambda: (
        engine._eval_node({"fn": "str_contains", "args": ["hello", "xyz"]}, {})
        is False))
    check("types.str_contains_type_error", lambda: (
        check_fn_type_error("str_contains", ["hello", 3])))
    check("types.option_some_value", lambda: (
        engine._eval_node({"fn": "option_some", "args": [42]}, {}) == 42))
    check("types.option_some_wrap_unwrap", lambda: (
        engine._eval_node({"fn": "str_len",
                           "args": [{"fn": "option_some", "args": ["hello"]}]}, {})
        == 5))
    check("types.option_none_is_none", lambda: (
        engine._eval_node({"fn": "option_none", "args": []}, {}) is None))
    check("types.option_some_rejects_none", lambda: (
        check_fn_type_error("option_some", [None])))
    check("types.map_get_key", lambda: (
        engine._eval_node({"fn": "map_get",
                           "args": [{"map": {"a": 1, "b": 2}}, "b"]}, {}) == 2))
    check("types.map_get_missing_none", lambda: (
        engine._eval_node({"fn": "map_get",
                           "args": [{"map": {"a": 1}}, "z"]}, {}) is None))
    check("types.map_get_type_error", lambda: (
        check_fn_type_error("map_get", [[1, 2], 0])))
    check("types.time_now_epoch_seed", lambda: (
        engine._eval_node({"fn": "time_now_epoch", "args": []}, {})
        == TIME_EPOCH_SEED))
    check("types.time_epoch_arithmetic", lambda: (
        engine._eval_node({"fn": "add", "args": [
            {"fn": "time_now_epoch", "args": []}, 86400]}, {})
        == TIME_EPOCH_SEED + 86400))

    # —— §SK 操作级（按加载的 spec 存在性守卫）——
    if "task_create" in engine.operations:
        check("sk.task_create_basic", lambda: (
            engine.eval("task_create", [7, 100]) == [7, 100, 0, 0]))
        check("sk.task_create_neg_bounty_bountyerr", lambda: (
            _expect_error(engine, "BountyErr", "task_create", [1, -5])))
    t0 = [7, 100, 0, 0]
    if "accept_task" in engine.operations:
        check("sk.accept_task_transition", lambda: (
            engine.eval("accept_task", [t0, 3]) == [7, 100, 1, 3]))
        check("sk.accept_task_non_open_stateerr", lambda: (
            _expect_error(engine, "StateError", "accept_task", [[7, 100, 1, 3], 5])))
    if "task_submit" in engine.operations:
        check("sk.task_submit_transition", lambda: (
            engine.eval("task_submit", [[7, 100, 1, 3]]) == [7, 100, 2, 3]))
    if "task_accept" in engine.operations:
        check("sk.task_accept_author", lambda: (
            engine.eval("task_accept", [[7, 100, 2, 3], 7]) == [7, 100, 3, 3]))
        check("sk.task_accept_non_author_autherr", lambda: (
            _expect_error(engine, "AuthError", "task_accept", [[7, 100, 2, 3], 9])))
    if "contribution_score" in engine.operations:
        check("sk.contribution_fold", lambda: (
            engine.eval("contribution_score", [[[1, 1, 3], [2, 2, 4]]]) == 7))
        check("sk.contribution_floor_at_0", lambda: (
            engine.eval("contribution_score", [[[1, 1, -5], [2, 2, 3]]]) == 0))
    if "quota_use" in engine.operations:
        check("sk.quota_use_deduct", lambda: (
            engine.eval("quota_use", [[10, 10], 4]) == [10, 6]))
        check("sk.quota_use_exhausted", lambda: (
            _expect_error(engine, "QuotaExhausted", "quota_use", [[10, 2], 9])))
    if "badge_level" in engine.operations:
        check("sk.badge_level_gold", lambda: engine.eval("badge_level", [450]) == 2)
    if "credit_score" in engine.operations:
        check("sk.credit_base", lambda: engine.eval("credit_score", [[]]) == 100)
        check("sk.credit_breach_chain", lambda: (
            engine.eval("credit_score", [[[1, 2]]]) == 49))
    if "task_create" in engine.operations:
        check("sig.arity_shape_error", lambda: (
            _expect_error(engine, "ShapeError", "task_create", [1])))
    check("engine.unknown_op", lambda: (
        _expect_error(engine, "UnknownOpError", "no_such_op", [])))

    passed = sum(1 for _, ok, _ in checks if ok)
    failures = [c for c in checks if not c[1]]
    return passed, total, failures


def _load_spec(engine, path):
    """优先加载 spec JSON；不存在则用内置示例 spec（并说明等待 §SK JSON）。"""
    if os.path.exists(path):
        engine._load(engine.from_spec(path).spec)
        return f"file: {path}"
    engine._load(json.loads(BUILTIN_SPEC))
    return ("builtin sample spec (spec/spec_p0_socketkit.json not found — "
            "等待 §SK JSON 落地后自动加载)")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    spec_path = DEFAULT_SPEC_PATH
    run_corpus_flag = True
    if "--spec" in argv:
        i = argv.index("--spec")
        spec_path = argv[i + 1]
    if "--check-only" in argv:
        run_corpus_flag = False

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    engine = SigmaEngine()
    source = _load_spec(engine, spec_path)
    spec_meta = engine.spec or {}
    print(f"ΣLang sigma_engine.py v{__version__} — spec→verifier engine self-check")
    print(f"spec source: {source}")
    print(f"spec: {spec_meta.get('spec', '?')} v{spec_meta.get('version', '?')}, "
          f"{len(engine.operations)} operations, "
          f"{len(engine.builtin_fns)} builtin fns")

    corpus_passed = corpus_total = 0
    if run_corpus_flag and engine.spec is not None:
        results = engine.run_corpus()
        corpus_total = len(results)
        corpus_passed = sum(1 for _, _, ok, _ in results if ok)
        for op, t, ok, detail in results:
            tag = "PASS" if ok else "FAIL"
            desc = t.get("description") or ""
            print(f"  [{tag}] {op}: {desc} — {detail}")
            if not ok:
                print(f"         test = {t}")
        print(f"corpus: {corpus_passed}/{corpus_total} passed")

    passed, total, failures = _selftest(engine)
    for name, ok, detail in [(c[0], c[1], c[2]) for c in failures]:
        print(f"  [FAIL] {name} — {detail}")
    print(f"engine: {passed}/{total} passed")

    grand_passed = corpus_passed + passed
    grand_total = corpus_total + total
    print(f"AGENT_ENGINE COMPLETE: {grand_passed}/{grand_total} passed")
    print(f"AGENT_TYPES COMPLETE: {passed}/{total} passed (含类型扩展用例)")
    return 0 if grand_passed == grand_total else 1


if __name__ == "__main__":
    sys.exit(main())
