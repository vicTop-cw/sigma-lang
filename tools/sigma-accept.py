#!/usr/bin/env python3
"""
ΣLang 一键收官验收 — sigma-accept.py
====================================
在一条命令里跑通全部验证门禁（v0.48 收官验收），汇总为可读报告：

  python3 tools/sigma-accept.py

Gates（任一失败 → 退出码 1）:
  1. 三端共识     verify_consensus.py            (47/47)
  2. 算法正确性   verify_p0.py                   (109/109)
  3. Python 参考  impl/python/sigma_core.py      (167/167)
  4. 三域审计     tools/sigma-runtime.py --domains (35/35)
  5. 证明消解     tools/sigma-prove.py (三域语料)  (全部 PROVED)
  6. 找茬冒烟     impl/python/sigma_app.py --smoke (25/25)
"""

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(cmd, cwd=ROOT, timeout=300):
    proc = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True,
                          text=True, timeout=timeout)
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out


def main():
    gates = [
        ("1. 三端共识 (Law XIII)", "python3 verify_consensus.py", ROOT, "47/47"),
        ("2. 算法正确性", "python3 verify_p0.py", ROOT, "109/109"),
        ("3. Python 参考实现", "python3 impl/python/sigma_core.py", ROOT, "167/167"),
        ("4. Rust 编译 (0 warning)",
         "cargo build", os.path.join(ROOT, "impl", "verifier"), "0 err/warn"),
        ("5. Rust §SK 自检",
         "cargo run -q -- --sk-self-check", os.path.join(ROOT, "impl", "verifier"), "88/88"),
        ("6. Elixir §SK 自检",
         "elixir sigma_verify.exs --sk-self-check",
         os.path.join(ROOT, "impl", "elixir_rt"), "88/88"),
        ("7. 三域审计故事线", "python3 tools/sigma-runtime.py --domains", ROOT, "83/83"),
        ("8. 证明消解 (全量语料重验)",
         "python3 tools/sigma-prove.py", ROOT, "302 PROVED"),
        ("9. 找茬参考后端冒烟", "python3 impl/python/sigma_app.py --smoke", ROOT, "36/36"),
        ("10. Rust 后端冒烟 (v0.84 对账)",
         "cargo run -q -- --app-smoke", os.path.join(ROOT, "impl", "verifier"), "36/36"),
    ]

    # v0.87 — --report FILE: write the per-gate results as a JSON report
    # (CI publishes the full regression report as an artifact).
    report_file = None
    for i, a in enumerate(sys.argv[1:]):
        if a == "--report" and i + 1 < len(sys.argv[1:]):
            report_file = sys.argv[1:][i + 1]

    print("ΣLang 一键收官验收 (v0.48)")
    print("=" * 64)
    results = []
    failed = 0
    for name, cmd, cwd, expect in gates:
        try:
            code, out = run(cmd, cwd)
        except subprocess.TimeoutExpired:
            print(f"  ⛔ {name}: TIMEOUT (expect {expect})")
            results.append({"name": name, "expect": expect, "ok": False,
                            "error": "TIMEOUT"})
            failed += 1
            continue
        ok = code == 0
        print(f"  {'✅' if ok else '❌'} {name} (expect {expect})"
              + ("" if ok else f"\n     {out.strip()[-200:]}"))
        results.append({"name": name, "expect": expect, "ok": ok,
                        "detail": "" if ok else out.strip()[-200:]})
        if not ok:
            failed += 1

    print("-" * 64)
    if failed:
        print(f"验收结果: {len(gates) - failed}/{len(gates)} 项通过 — {failed} 项失败")
    else:
        print(f"验收结果: {len(gates)}/{len(gates)} 项全部通过 — ΣLang 全链路可验收")

    # v0.87 — --report FILE: write the per-gate results as a JSON report
    # (CI publishes the full regression report as an artifact).
    # v0.116 — also run the runtime acceptance (--run-accept / --deploy-accept)
    # and record it in the report's "runtime" section.
    if report_file:
        runtime = {}
        for name, cmd in (
            ("run_accept", "python3 impl/python/sigma_app.py --run-accept"),
            ("deploy_accept", "python3 impl/python/sigma_app.py --deploy-accept"),
        ):
            try:
                code, out = run(cmd, ROOT)
                runtime[name] = {"ok": code == 0,
                                 "detail": "" if code == 0 else out.strip()[-200:]}
            except subprocess.TimeoutExpired:
                runtime[name] = {"ok": False, "detail": "TIMEOUT"}
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "spec": "0.7.0",
                "date": "2026-08-05",
                "gates": results,
                "runtime": runtime,
                "passed": len(gates) - failed,
                "total": len(gates),
                "all_ok": failed == 0,
            }, f, ensure_ascii=False, indent=2)
        print(f"验收报告已写入 {report_file}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
