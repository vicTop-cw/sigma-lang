#!/usr/bin/env python3
"""
ΣLang spec→judge 最小可用版 — sigma-spec2judge.py
==================================================
整改项 4.6：从 spec JSON 自动产出可评测候选实现的 judge 工具。
对接「自动生成 LeetCode 式评测系统」：提交一份 user_code.py，judge 按 spec 的
tests 数组（含错误用例）逐条评测，输出 PASS/WA/TLE/MLE verdict 与 judge_report.json。

设计：
  * stdlib-only、单文件；不修改 sigma_engine.py（同目录存在时仅复用其 ERROR_NAMES，
    失败则用内置副本，保证可独立分发）。
  * 评测集 = spec JSON 全部操作的 tests（含错误用例）。测试输入里的表达式节点
    {"op": ...} / {"list": ...} / {"fn": ...} 与 "$_" 链按 sigma_engine.run_corpus
    语义解析——但链式调用走**候选函数**（LeetCode 式端到端评测）：如 accept_task
    的输入先经候选 task_create 构造状态；"$_" 引用上一个成功结果。
  * 候选提交：user_code.py 需定义与 spec 操作同名的函数；错误上报两种风格均可识别：
        raise ValueError("BountyErr")                 # ValueError + 规范错误名消息
        raise BountyErr("...")                        # 自定义异常类，类名须等于规范错误名
    另有 20 个内置规范错误名（BountyErr/StateError/AuthError/... 见 ERROR_NAMES）。
  * 隔离与限制：每条测试在独立子进程（sys.executable -I -u -c WORKER_SRC）中加载候选
    并求值；超时（subprocess timeout）判 TLE；POSIX 下经 preexec_fn setrlimit
    (RLIMIT_AS/RLIMIT_DATA) 限制内存、触发 MemoryError 判 MLE；Windows 无 resource
    模块 → 自动降级为仅时间限制。候选代码在仅含白名单 builtins 的命名空间 exec
    （无 open/eval/exec/__import__/input；print 被捕获进报告，不污染协议通道）。
  * 每条测试独立加载候选 → 测试间无状态泄漏；"$_" 链由 parent 侧缓存 prev 传递。

用法：
    python3 sigma-spec2judge.py --spec <spec.json> --submission <user_code.py> \
            [--time-limit 5] [--memory-limit 256] [--ops a,b] [--report judge_report.json] [--verbose]
    python3 sigma-spec2judge.py --selftest   # 内置自检（无参数时等价）

退出码：0 = 全部通过；1 = 有失败（WA/TLE/MLE）；2 = 用法 / spec 加载错误。
verdict 说明：
    PASS  输出等于期望值，或抛出与期望一致的规范错误
    WA    输出 / 错误与期望不符：值不匹配、错误名不匹配、意外异常、函数缺失、
          提交加载失败（含编译错误、导入被禁止等）
    TLE   单条测试超时（--time-limit 秒）
    MLE   超出内存限制（仅 POSIX 生效；Windows 降级为仅时间限制）
"""

import json
import os
import subprocess
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

__version__ = "0.1.0"

# ---------------------------------------------------------------------------
# 规范错误名（与 spec/json-schema.md「错误名约定」一致，共 20 个）
# ---------------------------------------------------------------------------

ERROR_NAMES = [
    "BountyErr", "StateError", "AuthError", "TypeError", "ShapeError",
    "QuotaExhausted", "InsufficientEscrow", "InsufficientPoints",
    "InsufficientStock", "TeamFull", "InsufficientFunds", "UnknownAsset",
    "InsufficientShares", "UnknownItem", "DivByZero", "NotTraceable",
    "ReserveErr", "BidAmountErr", "ClosedErr", "TimeoutErr",
]

try:  # sigma_engine.py 就在同目录时复用其错误名表（单一事实来源）；失败则用内置副本
    import sigma_engine as _sigma_engine
    ERROR_NAMES = list(_sigma_engine.ERROR_NAMES)
except Exception:
    pass

# ---------------------------------------------------------------------------
# 候选代码受限 builtins 白名单（无 open/eval/exec/__import__/input/globals 等）
# ---------------------------------------------------------------------------

SAFE_BUILTINS = {
    "True": True, "False": False, "None": None,
    "abs": abs, "all": all, "any": any, "bool": bool, "bytes": bytes,
    "chr": chr, "classmethod": classmethod, "dict": dict, "divmod": divmod,
    "enumerate": enumerate, "filter": filter, "float": float, "hash": hash,
    "hex": hex, "int": int, "isinstance": isinstance, "issubclass": issubclass,
    "len": len, "list": list, "map": map, "max": max, "min": min, "oct": oct,
    "ord": ord, "pow": pow, "print": print, "property": property,
    "range": range, "repr": repr, "reversed": reversed, "round": round,
    "set": set, "slice": slice, "sorted": sorted, "staticmethod": staticmethod,
    "str": str, "sum": sum, "super": super, "tuple": tuple, "type": type,
    "zip": zip,
    "BaseException": BaseException, "Exception": Exception,
    "ArithmeticError": ArithmeticError, "AttributeError": AttributeError,
    "EOFError": EOFError, "ImportError": ImportError, "IndexError": IndexError,
    "KeyError": KeyError, "LookupError": LookupError, "MemoryError": MemoryError,
    "NameError": NameError, "NotImplementedError": NotImplementedError,
    "OSError": OSError, "OverflowError": OverflowError, "RuntimeError": RuntimeError,
    "StopIteration": StopIteration, "TypeError": TypeError,
    "ValueError": ValueError, "ZeroDivisionError": ZeroDivisionError,
}

import builtins as _builtins  # noqa: E402  (class 语句需要 __build_class__)
if hasattr(_builtins, "__build_class__"):
    SAFE_BUILTINS["__build_class__"] = _builtins.__build_class__


class UsageError(Exception):
    """工具级用法错误（缺文件 / 坏 spec / 坏参数）→ 退出码 2。"""


# ---------------------------------------------------------------------------
# 单条测试执行器（worker，以隔离子进程方式运行；协议：stdin 1 行 JSON 配置，
# stdout 1 行 JSON 结果；候选代码的 print 被捕获进 stdout 字段，不污染协议通道）
# ---------------------------------------------------------------------------

WORKER_SRC = r'''
import io
import json
import sys

# 输入表达式节点里的内置函数（MVP 子集，与 sigma_engine.BUILTIN_FNS 同名同参）
_WORKER_BUILTINS = {
    "index": lambda xs, i: xs[i],
    "len": lambda xs: len(xs),
    "min": lambda *a: min(a[0] if len(a) == 1 else list(a)),
    "max": lambda *a: max(a[0] if len(a) == 1 else list(a)),
    "add": lambda *a: sum(a),
    "sub": lambda a, b: a - b,
    "mul": lambda a, b: a * b,
    "floordiv": lambda a, b: a // b,
    "mod": lambda a, b: a % b,
    "fold_add": lambda xs: (sum(x[-1] for x in xs)
                            if xs and all(isinstance(x, list) for x in xs) else sum(xs)),
    "map": lambda xs, field: [x[field] for x in xs],
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "lt": lambda a, b: a < b,
    "le": lambda a, b: a <= b,
    "gt": lambda a, b: a > b,
    "ge": lambda a, b: a >= b,
}


def _extract_error_name(e, error_names):
    """提取规范错误名：优先异常类名；其次 ValueError 消息以错误名开头（如 "BountyErr: ..."）。"""
    cls = type(e).__name__
    if cls in error_names:
        return cls
    msg = str(e)
    for name in error_names:
        if msg == name or msg.startswith(name + ":") or msg.startswith(name + "("):
            return name
    return cls


def main():
    real_out = sys.stdout
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    line = sys.stdin.readline()
    if not line:
        return
    cfg = json.loads(line)
    error_names = cfg.get("error_names") or []
    memory_active = bool(cfg.get("memory_active"))
    has_prev = bool(cfg.get("has_prev"))
    last = cfg.get("prev") if has_prev else None

    captured = io.StringIO()
    sys.stdout = captured  # 候选代码的 print 被捕获，不污染协议通道

    def reply(payload):
        sys.stdout = real_out
        real_out.write(json.dumps(payload, ensure_ascii=True) + "\n")
        real_out.flush()

    def call_op(name, args):
        fn = ns.get(name)
        if not callable(fn):
            raise ValueError(name + ": function not defined")
        return fn(*args)

    def resolve(x):
        nonlocal last
        if isinstance(x, dict):
            if "op" in x:
                val = call_op(x["op"], [resolve(a) for a in x.get("args", [])])
                last = val
                return val
            if "list" in x:
                return [resolve(a) for a in x["list"]]
            if "fn" in x:
                fn = _WORKER_BUILTINS.get(x["fn"])
                if fn is None:
                    raise ValueError("unknown builtin fn in input expression: " + str(x["fn"]))
                return fn(*[resolve(a) for a in x.get("args", [])])
            raise ValueError("unsupported input expression node: " + repr(x))
        if isinstance(x, list):
            return [resolve(v) for v in x]
        if x == "$_":
            if not has_prev:
                raise ValueError("'$_' used before any operation result")
            return last
        return x

    import builtins as _bi
    safe_builtins = {n: getattr(_bi, n) for n in (cfg.get("safe_builtin_names") or [])}
    if hasattr(_bi, "__build_class__"):
        safe_builtins.setdefault("__build_class__", _bi.__build_class__)
    ns = {"__name__": "submission", "__builtins__": safe_builtins}
    try:
        code = compile(cfg["candidate_source"], cfg.get("candidate_path", "submission.py"), "exec")
        exec(code, ns)
    except BaseException as e:  # noqa: BLE001 -- worker 端兜底：任何加载失败都如实上报
        reply({"kind": "load_error", "message": type(e).__name__ + ": " + str(e),
               "stdout": captured.getvalue()[-2000:], "last": last})
        return

    op_name = cfg["op"]
    fn = ns.get(op_name)
    if not callable(fn):
        reply({"kind": "missing", "op": op_name, "last": last})
        return

    try:
        args = [resolve(a) for a in cfg["args"]]
        out = call_op(op_name, args)
        last = out
    except MemoryError as e:
        payload = {"kind": "err", "name": "MemoryError", "message": str(e), "last": last,
                   "stdout": captured.getvalue()[-2000:]}
        if memory_active:
            payload["mle"] = True
        reply(payload)
        return
    except BaseException as e:  # noqa: BLE001 -- 规范错误 / 任意异常统一上报，由 parent 判定
        reply({"kind": "err", "name": _extract_error_name(e, error_names),
               "message": type(e).__name__ + ": " + str(e),
               "last": last, "stdout": captured.getvalue()[-2000:]})
        return
    reply({"kind": "ok", "value": out, "last": last, "stdout": captured.getvalue()[-2000:]})


if __name__ == "__main__":
    main()
'''


def _make_rlimit_fn(memory_limit_mb):
    """POSIX 子进程内存限制：RLIMIT_AS（+ RLIMIT_DATA 可用时）。"""
    limit_bytes = max(1, int(memory_limit_mb)) * 1024 * 1024

    def _apply():
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
        if hasattr(resource, "RLIMIT_DATA"):
            try:
                resource.setrlimit(resource.RLIMIT_DATA, (limit_bytes, limit_bytes))
            except (ValueError, OSError):
                pass

    return _apply


def _run_single_test(cfg, time_limit, memory_limit_mb):
    """spawn 一个 worker 子进程执行单条测试；返回 {verdict, detail, reply, stdout, stderr}。"""
    argv = [sys.executable, "-I", "-u", "-c", WORKER_SRC]
    kwargs = dict(
        input=json.dumps(cfg, ensure_ascii=True) + "\n",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace",
    )
    if os.name == "posix" and memory_limit_mb and memory_limit_mb > 0:
        kwargs["preexec_fn"] = _make_rlimit_fn(memory_limit_mb)
    try:
        proc = subprocess.run(argv, timeout=time_limit, **kwargs)
    except subprocess.TimeoutExpired as e:
        return {"verdict": "TLE", "detail": "time limit %.1fs exceeded" % time_limit,
                "reply": None, "stdout": (e.stdout or "") or "", "stderr": (e.stderr or "") or ""}
    out = (proc.stdout or "").strip()
    if proc.returncode != 0 or not out:
        stderr_tail = ((proc.stderr or "").strip().splitlines() or [""])[-3:]
        return {"verdict": "WA",
                "detail": "worker crashed (exit %s): %s" % (proc.returncode, " | ".join(stderr_tail)),
                "reply": None, "stdout": out, "stderr": (proc.stderr or "") or ""}
    try:
        reply = json.loads(out.splitlines()[0])
    except Exception as e:
        return {"verdict": "WA", "detail": "worker protocol error: %s" % e,
                "reply": None, "stdout": out, "stderr": (proc.stderr or "") or ""}
    return {"verdict": None, "detail": None, "reply": reply,
            "stdout": reply.get("stdout") or "", "stderr": (proc.stderr or "") or ""}


def _classify(reply, test, op_name):
    """worker 结果 → (verdict, detail)。期望优先 error 键（错误用例），否则 output 键。"""
    kind = reply.get("kind")
    expected_err = test.get("error")
    expected_out = test.get("output")
    if kind == "ok":
        if expected_err:
            return "WA", "expected error %s, got value %r" % (expected_err, reply.get("value"))
        if reply.get("value") == expected_out:
            return "PASS", "ok: %r" % (reply.get("value"),)
        return "WA", "expected %r, got %r" % (expected_out, reply.get("value"))
    if kind == "err":
        got = reply.get("name")
        if reply.get("mle"):
            return "MLE", "memory limit exceeded: %s" % reply.get("message")
        if expected_err and got == expected_err:
            return "PASS", "expected error %s" % expected_err
        if expected_err:
            return "WA", "expected error %s, got %s: %s" % (expected_err, got, reply.get("message"))
        return "WA", "unexpected error %s: %s" % (got, reply.get("message"))
    if kind == "missing":
        return "WA", "function %r not defined in submission" % op_name
    if kind == "load_error":
        return "WA", "submission load error: %s" % reply.get("message")
    return "WA", "unknown worker reply kind %r" % kind


def judge_spec(spec_path, submission_path, time_limit=5.0, memory_limit=256,
               ops_filter=None, verbose=False, report_path="judge_report.json",
               print_final=True):
    """评测主流程：提取 tests → 逐条隔离评测 → 汇总 + 写 judge_report.json。

    返回 {"summary": {...}, "exit_code": 0|1, "report_path": ...}；
    用法级错误抛 UsageError（调用方转退出码 2）。
    """
    if time_limit is None or time_limit <= 0:
        raise UsageError("--time-limit must be > 0")
    if memory_limit is None or memory_limit < 0:
        raise UsageError("--memory-limit must be >= 0 (0 = unlimited)")

    spec_abspath = os.path.abspath(spec_path)
    if not os.path.isfile(spec_path):
        raise UsageError("spec file not found: %s" % spec_path)
    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            spec = json.load(f)
    except (OSError, ValueError) as e:
        raise UsageError("cannot load spec %s: %s" % (spec_path, e))
    if not isinstance(spec, dict) or not isinstance(spec.get("operations"), list):
        raise UsageError("spec JSON must be an object with an 'operations' list (see spec/json-schema.md)")

    sub_abspath = os.path.abspath(submission_path)
    if not os.path.isfile(submission_path):
        raise UsageError("submission file not found: %s" % submission_path)
    with open(submission_path, "r", encoding="utf-8") as f:
        source = f.read()

    # 评测集：全部操作的 tests（含错误用例），按 spec 顺序（"$_" 链依赖顺序）
    plan = []
    used_ops = []
    for op in spec["operations"]:
        name = op.get("name")
        if not isinstance(name, str) or not isinstance(op.get("tests"), list):
            continue
        if ops_filter and name not in ops_filter:
            continue
        for t in op["tests"]:
            if not isinstance(t, dict) or "input" not in t:
                continue
            plan.append((name, t))
        used_ops.append(name)
    if not plan:
        raise UsageError("spec has no tests to judge (ops_filter=%r)" % (ops_filter,))
    if ops_filter:
        unknown = [n for n in ops_filter if n not in used_ops]
        if unknown:
            print("warning: --ops names not present in spec: %s" % ", ".join(unknown))

    compile_error = None
    try:
        compile(source, submission_path, "exec")
    except SyntaxError as e:
        compile_error = "%s: %s" % (type(e).__name__, e)

    memory_enforced = os.name == "posix" and (memory_limit or 0) > 0
    if os.name != "posix" and (memory_limit or 0) > 0:
        print("note: resource module unavailable on %s; memory limit not enforced (time-only)" % os.name)

    summary = {"total": len(plan), "pass": 0, "wa": 0, "tle": 0, "mle": 0}
    results = []
    last, has_last = None, False

    for i, (op_name, test) in enumerate(plan):
        expected = {"error": test["error"]} if "error" in test else {"output": test.get("output")}
        entry = {"index": i, "op": op_name, "description": test.get("description") or "",
                 "input": test["input"], "expected": expected}
        if compile_error is not None:
            entry["verdict"], entry["detail"] = "WA", "submission compile error: %s" % compile_error
            results.append(entry)
            summary["wa"] += 1
            if verbose:
                print("[WA] %s #%d %s — %s" % (op_name, i, entry["description"], entry["detail"]))
            continue

        cfg = {"candidate_source": source, "candidate_path": sub_abspath,
               "op": op_name, "args": test["input"],
               "prev": last, "has_prev": has_last,
               "error_names": ERROR_NAMES, "safe_builtin_names": list(SAFE_BUILTINS),
               "memory_active": memory_enforced}
        r = _run_single_test(cfg, time_limit, memory_limit)
        if r["reply"] is not None and "last" in r["reply"]:
            last, has_last = r["reply"]["last"], True
        if r["verdict"] is not None:
            verdict, detail = r["verdict"], r["detail"]
        else:
            verdict, detail = _classify(r["reply"], test, op_name)
        entry["verdict"], entry["detail"] = verdict, detail
        if r.get("stdout"):
            entry["stdout"] = r["stdout"][-2000:]
        if r.get("stderr") and verdict != "PASS":
            entry["stderr_tail"] = "\n".join(((r["stderr"] or "").strip().splitlines() or [""])[-5:])
        results.append(entry)
        summary[verdict.lower()] += 1
        if verbose or verdict != "PASS":
            print("[%s] %s #%d %s — %s" % (verdict, op_name, i, entry["description"], detail))
            if verbose and entry.get("stdout"):
                print("       candidate stdout: %r" % entry["stdout"][-300:])

    report = {
        "tool": "sigma-spec2judge", "version": __version__,
        "spec": {"path": spec_abspath, "name": spec.get("spec"), "version": spec.get("version")},
        "submission": {"path": sub_abspath},
        "limits": {"time_limit_s": time_limit, "memory_limit_mb": memory_limit,
                   "memory_enforced": memory_enforced},
        "summary": summary,
        "results": results,
        "exit_code": 0 if summary["pass"] == summary["total"] else 1,
    }
    report_abspath = os.path.abspath(report_path)
    os.makedirs(os.path.dirname(report_abspath), exist_ok=True)
    with open(report_abspath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("summary: PASS=%d WA=%d TLE=%d MLE=%d (%d/%d)" % (
        summary["pass"], summary["wa"], summary["tle"], summary["mle"],
        summary["pass"], summary["total"]))
    print("report: %s" % report_abspath)
    if print_final:
        print("AGENT_JUDGE COMPLETE: %d/%d passed" % (summary["pass"], summary["total"]))
    return {"summary": summary, "exit_code": report["exit_code"], "report_path": report_abspath}


# ---------------------------------------------------------------------------
# 内置自检：sample spec（复用 spec_p0_socketkit.json 的 task_create / accept_task
# 子集，共 6 条测试）+ 正确提交 + 故意带 1 个 bug 的提交
# ---------------------------------------------------------------------------

SAMPLE_SPEC = {
    "spec": "§SK",
    "version": "0.30.0-subset",
    "fingerprint_prefix": "0xF000",
    "types": [{"name": "Task", "kind": "alias", "target": "List<nat>"}],
    "operations": [
        {
            "name": "task_create",
            "fingerprint": "0xF001",
            "signature": {"params": ["nat", "nat"], "returns": "Task"},
            "definition": {"kind": "lambda", "params": ["a", "b"],
                           "body": {"list": ["a", "b", 0, 0]}},
            "preconditions": [{"expr": "b >= 0", "error": "BountyErr",
                               "description": "bounty must be >= 0"}],
            "laws": [],
            "tests": [
                {"input": [7, 100], "output": [7, 100, 0, 0],
                 "description": "basic create: [author, bounty, open, unclaimed]"},
                {"input": [2, 0], "output": [2, 0, 0, 0], "description": "zero bounty allowed"},
                {"input": [1, -5], "output": None, "error": "BountyErr",
                 "description": "negative bounty rejected"}
            ]
        },
        {
            "name": "accept_task",
            "fingerprint": "0xF004",
            "signature": {"params": ["Task", "nat"], "returns": "Task"},
            "definition": {"kind": "lambda", "params": ["t", "h"],
                           "body": {"list": [{"fn": "index", "args": ["t", 0]},
                                             {"fn": "index", "args": ["t", 1]}, 1, "h"]}},
            "preconditions": [{"expr": "index(t, 2) == 0", "error": "StateError",
                               "description": "task must be open"}],
            "laws": [],
            "tests": [
                {"input": [{"op": "task_create", "args": [7, 100]}, 3],
                 "output": [7, 100, 1, 3], "description": "hunter 3 claims open task"},
                {"input": [{"op": "task_create", "args": [2, 0]}, 9],
                 "output": [2, 0, 1, 9], "description": "hunter 9 claims zero-bounty task"},
                {"input": [[7, 100, 1, 3], 5], "output": None, "error": "StateError",
                 "description": "in_progress task cannot be claimed again"}
            ]
        }
    ]
}

SAMPLE_CORRECT = '''\
# 正确提交：task_create 用 ValueError("错误名") 风格，accept_task 用自定义异常类风格
class StateError(Exception):
    pass


def task_create(a, b):
    """create task: [author, bounty, status=open(0), hunter=unclaimed(0)]"""
    if b < 0:
        raise ValueError("BountyErr")
    return [a, b, 0, 0]


def accept_task(t, h):
    """claim an open task: status -> in_progress(1), hunter = h"""
    if t[2] != 0:
        raise StateError("task not open")
    return [t[0], t[1], 1, h]
'''

SAMPLE_BUGGY = '''\
# 故意带 1 个 bug 的提交：accept_task 忘记把状态置为 in_progress(1)，仍返回 open(0)
def task_create(a, b):
    if b < 0:
        raise ValueError("BountyErr")
    return [a, b, 0, 0]


def accept_task(t, h):
    if t[2] != 0:
        raise ValueError("StateError")
    return [t[0], t[1], 0, h]   # BUG: 状态仍为 open(0)
'''


def selftest():
    """内置自检：正确提交应 6/6 PASS；带 1 个 bug 的提交应 4/6（检出 2 条 WA）。"""
    tmp = tempfile.mkdtemp(prefix="sigma-judge-self-")
    spec_path = os.path.join(tmp, "sample_spec.json")
    with open(spec_path, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_SPEC, f, ensure_ascii=False, indent=1)
    ok_path = os.path.join(tmp, "submission_correct.py")
    bad_path = os.path.join(tmp, "submission_buggy.py")
    with open(ok_path, "w", encoding="utf-8") as f:
        f.write(SAMPLE_CORRECT)
    with open(bad_path, "w", encoding="utf-8") as f:
        f.write(SAMPLE_BUGGY)

    print("sigma-spec2judge v%s self-check — sample spec: task_create (3 tests) + accept_task (3 tests)"
          % __version__)
    r_ok = judge_spec(spec_path, ok_path, time_limit=5.0, memory_limit=256,
                      verbose=True, report_path=os.path.join(tmp, "judge_report_correct.json"),
                      print_final=False)
    r_bad = judge_spec(spec_path, bad_path, time_limit=5.0, memory_limit=256,
                       verbose=True, report_path=os.path.join(tmp, "judge_report_buggy.json"),
                       print_final=False)

    s_ok, s_bad = r_ok["summary"], r_bad["summary"]
    ok_flag = (s_ok["total"] == 6 and s_ok["pass"] == 6 and s_ok["wa"] == 0)
    bad_flag = (s_bad["total"] == 6 and s_bad["pass"] == 4 and s_bad["wa"] == 2)
    if ok_flag and bad_flag:
        print("self-check OK: correct 6/6 PASS; buggy 4/6 with 2 WA detected "
              "(exit codes %d / %d)" % (r_ok["exit_code"], r_bad["exit_code"]))
    else:
        print("self-check FAILED: correct=%d/%d (wa=%d), buggy=%d/%d (wa=%d), expected 6/6 and 4/6"
              % (s_ok["pass"], s_ok["total"], s_ok["wa"], s_bad["pass"], s_bad["total"], s_bad["wa"]))
    print("AGENT_JUDGE COMPLETE: correct=%d/%d buggy=%d/%d" % (
        s_ok["pass"], s_ok["total"], s_bad["pass"], s_bad["total"]))
    return 0 if (ok_flag and bad_flag) else 1


def main(argv=None):
    import argparse
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(
        prog="sigma-spec2judge.py",
        description="ΣLang spec→judge：从 spec JSON 自动评测候选提交（整改项 4.6）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="verdicts: PASS / WA / TLE / MLE\n"
               "exit codes: 0 = all pass, 1 = failures, 2 = usage / spec error\n"
               "no arguments = run built-in self-check (correct 6/6, buggy 4/6)")
    parser.add_argument("--spec", metavar="spec.json")
    parser.add_argument("--submission", metavar="user_code.py")
    parser.add_argument("--time-limit", type=float, default=5.0, metavar="sec",
                        help="per-test time limit (default 5.0)")
    parser.add_argument("--memory-limit", type=int, default=256, metavar="MB",
                        help="per-test memory limit, POSIX only; 0 = unlimited "
                             "(Windows degrades to time-only)")
    parser.add_argument("--ops", metavar="a,b",
                        help="judge only listed operations (comma separated)")
    parser.add_argument("--report", default="judge_report.json", metavar="path",
                        help="report output path (default ./judge_report.json)")
    parser.add_argument("--selftest", action="store_true", help="run built-in self-check")
    parser.add_argument("--verbose", action="store_true", help="print per-test detail lines")
    args = parser.parse_args(argv)

    if args.selftest:
        return selftest()
    if not (args.spec and args.submission):
        parser.error("--spec and --submission are both required (or use --selftest)")

    try:
        r = judge_spec(args.spec, args.submission, time_limit=args.time_limit,
                       memory_limit=args.memory_limit,
                       ops_filter=[s.strip() for s in args.ops.split(",")] if args.ops else None,
                       verbose=args.verbose, report_path=args.report,
                       print_final=False)
    except UsageError as e:
        print("error: %s" % e)
        return 2
    print("AGENT_JUDGE COMPLETE: %d/%d passed" % (r["summary"]["pass"], r["summary"]["total"]))
    return r["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
