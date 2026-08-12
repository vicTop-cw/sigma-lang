# -*- coding: utf-8 -*-
"""
ΣLang 一键复核脚本 —— 批量验证 tests/reports/ 下所有 _impl_*.py 实现者的通过率。

用法:
    python sigma-impl-verify.py                 # 扫描默认目录 + 默认 §SK spec
    python sigma-impl-verify.py --impl <path>   # 只复核单个实现文件
    python sigma-impl-verify.py --spec <path>   # 指定规格 JSON

判定规则（与各实现内部自检一致）:
  - input 中嵌套 {"op": ..., "args": [...]} 先递归求值再传入
  - 期望 output 的测试: 实际返回值 == 期望值 即通过
  - 期望 error 的测试: 实现须抛出异常, 且错误名（ValueError 消息或异常类型名）与期望一致

退出码: 全部实现者 == 60/60 时 0; 任一实现者不足或加载失败时 1。
仅依赖标准库, 不修改 tests/reports/ 下的任何实现文件。
"""

import argparse
import importlib.util
import json
import os
import sys

DEFAULT_SPEC = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "spec", "spec_p0_socketkit.json")
)
DEFAULT_REPORTS = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "reports")
)

# 实现文件可能把操作表暴露在下列任一名字下
OPS_DICT_CANDIDATES = ("OPERATIONS", "OPS", "_OPS")


def resolve_ops(module, spec):
    """从已加载的实现模块解析 {op_name: callable} 映射。

    优先找操作表字典; 找不到则退回用模块级同名函数。
    仅收录 spec 中实际存在的操作名。
    """
    ops = {}
    for cand in OPS_DICT_CANDIDATES:
        obj = getattr(module, cand, None)
        if isinstance(obj, dict):
            ops = {k: v for k, v in obj.items() if callable(v)}
            break
    if not ops:
        for name in (op_def["name"] for op_def in spec["operations"]):
            fn = getattr(module, name, None)
            if callable(fn):
                ops[name] = fn
    return ops


def load_impl(path):
    """用 importlib 从文件加载实现模块（唯一模块名, 避免污染/冲突）。"""
    stem = os.path.splitext(os.path.basename(path))[0]
    mod_name = "sigma_verify_%s" % stem
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError("无法为 %s 创建加载 spec" % path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


def eval_input(node, ops):
    """递归求值测试 input: 仅 {"op": ...} 节点调用实现, 其余原样返回。"""
    if isinstance(node, dict) and "op" in node:
        args = [eval_input(a, ops) for a in node.get("args", [])]
        return ops[node["op"]](*args)
    if isinstance(node, list):
        return [eval_input(x, ops) for x in node]
    return node


def error_name(exc):
    """提取异常对应的"错误名": ValueError 消息优先, 否则用异常类型名。"""
    names = []
    if exc.args and isinstance(exc.args[0], str) and exc.args[0]:
        names.append(exc.args[0])
    names.append(type(exc).__name__)
    return names


def run_impl_tests(ops, spec):
    """按 spec 的 tests 逐条执行, 返回 (passed, total, failures)。"""
    total = passed = 0
    failures = []
    for op_def in spec["operations"]:
        name = op_def["name"]
        fn = ops.get(name)
        if fn is None:
            for test in op_def.get("tests", []):
                total += 1
                failures.append({
                    "op": name,
                    "desc": test.get("description", ""),
                    "expect": "可调用",
                    "actual": "模块中未找到操作 %s" % name,
                })
            continue
        for test in op_def.get("tests", []):
            total += 1
            expected_out = test.get("output")
            expected_err = test.get("error")
            try:
                args = [eval_input(a, ops) for a in test.get("input", [])]
                result = fn(*args)
                if expected_err is not None:
                    failures.append({
                        "op": name,
                        "desc": test.get("description", ""),
                        "expect": "Error: %s" % expected_err,
                        "actual": "未抛错, 返回 %r" % (result,),
                    })
                elif result == expected_out:
                    passed += 1
                else:
                    failures.append({
                        "op": name,
                        "desc": test.get("description", ""),
                        "expect": repr(expected_out),
                        "actual": repr(result),
                    })
            except Exception as exc:  # noqa: BLE001 - 复核脚本须兜住一切异常
                names = error_name(exc)
                if expected_err is not None and expected_err in names:
                    passed += 1
                else:
                    failures.append({
                        "op": name,
                        "desc": test.get("description", ""),
                        "expect": expected_err if expected_err is not None else repr(expected_out),
                        "actual": "异常 %s" % (" / ".join(names)),
                    })
    return passed, total, failures


def impl_label(path):
    """从文件名推导实现者名: _impl_Hy3.py -> Hy3"""
    stem = os.path.splitext(os.path.basename(path))[0]
    for prefix in ("_impl_", "impl_"):
        if stem.startswith(prefix):
            return stem[len(prefix):]
    return stem


def main(argv=None):
    ap = argparse.ArgumentParser(description="ΣLang 实现复核脚本 (stdlib-only)")
    ap.add_argument("--spec", default=DEFAULT_SPEC, help="规格 JSON 路径 (默认 §SK spec)")
    ap.add_argument("--impl", default=None, help="单文件模式: 只复核指定实现文件")
    args = ap.parse_args(argv)

    with open(args.spec, "r", encoding="utf-8") as f:
        spec = json.load(f)
    total_per_spec = sum(len(op_def.get("tests", [])) for op_def in spec["operations"])

    if args.impl:
        impl_paths = [os.path.abspath(args.impl)]
        if not os.path.isfile(impl_paths[0]):
            print("错误: 实现文件不存在: %s" % impl_paths[0])
            return 1
    else:
        if not os.path.isdir(DEFAULT_REPORTS):
            print("错误: reports 目录不存在: %s" % DEFAULT_REPORTS)
            return 1
        impl_paths = sorted(
            os.path.join(DEFAULT_REPORTS, fn)
            for fn in os.listdir(DEFAULT_REPORTS)
            if fn.startswith("_impl_") and fn.endswith(".py")
        )

    if not impl_paths:
        print("未找到任何 _impl_*.py 实现文件。")
        return 1

    results = []  # (label, path, passed, total, failures, load_error)
    for path in impl_paths:
        label = impl_label(path)
        try:
            module = load_impl(path)
            ops = resolve_ops(module, spec)
            missing = [d["name"] for d in spec["operations"] if d["name"] not in ops]
            if missing:
                results.append((label, path, 0, total_per_spec, [{
                    "op": m, "desc": "", "expect": "可调用", "actual": "操作未导出"
                } for m in missing], "缺少操作: %s" % ", ".join(missing)))
                continue
            passed, total, failures = run_impl_tests(ops, spec)
            results.append((label, path, passed, total, failures, None))
        except Exception as exc:  # noqa: BLE001
            results.append((label, path, 0, total_per_spec, [], "加载失败: %s" % exc))

    # ---- 汇总表 ----
    print("ΣLang 实现一键复核 (spec: %s, %d ops / %d tests)" % (
        os.path.basename(args.spec), len(spec["operations"]), total_per_spec))
    print("-" * 62)
    print("%-18s %-12s %-8s %s" % ("实现者", "通过率", "失败数", "状态"))
    print("-" * 62)
    any_fail = False
    for label, path, passed, total, failures, err in results:
        if err:
            any_fail = True
            status = "LOAD ERROR"
        elif passed < total:
            any_fail = True
            status = "FAIL"
        else:
            status = "PASS"
        print("%-18s %-12s %-8d %s" % (label, "%d/%d" % (passed, total), len(failures), status))
    print("-" * 62)

    # ---- 失败详情 (每个实现者最多前 3 条) ----
    shown_any = False
    for label, path, passed, total, failures, err in results:
        if err:
            print("[%s] %s" % (label, err))
            shown_any = True
            continue
        if failures:
            shown_any = True
            print("[%s] 失败 %d 项 (前 3 条):" % (label, len(failures)))
            for f in failures[:3]:
                print("  - [%s] %s | 期望 %s | 实际 %s" % (
                    f["op"], f["desc"] or "(无描述)", f["expect"], f["actual"]))
    if not shown_any:
        print("全部实现者 %d/%d 通过, 无失败项。" % (total_per_spec, total_per_spec))

    # ---- 收尾 ----
    if any_fail:
        print("AGENT_VERIFY_TOOL FAILED: %d impls verified, some below %d/%d" % (
            len(results), total_per_spec, total_per_spec))
        return 1
    print("AGENT_VERIFY_TOOL COMPLETE: %d impls verified, all %d/%d" % (
        len(results), total_per_spec, total_per_spec))
    return 0


if __name__ == "__main__":
    sys.exit(main())
