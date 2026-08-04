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
        ("7. 三域审计故事线", "python3 tools/sigma-runtime.py --domains", ROOT, "35/35"),
        ("8. 证明消解 (全量语料重验)",
         "python3 tools/sigma-prove.py", ROOT, "73 PROVED"),
        ("9. 找茬参考后端冒烟", "python3 impl/python/sigma_app.py --smoke", ROOT, "25/25"),
    ]

    print("ΣLang 一键收官验收 (v0.48)")
    print("=" * 64)
    failed = 0
    for name, cmd, cwd, expect in gates:
        try:
            code, out = run(cmd, cwd)
        except subprocess.TimeoutExpired:
            print(f"  ⛔ {name}: TIMEOUT (expect {expect})")
            failed += 1
            continue
        ok = code == 0
        print(f"  {'✅' if ok else '❌'} {name} (expect {expect})"
              + ("" if ok else f"\n     {out.strip()[-200:]}"))
        if not ok:
            failed += 1

    print("-" * 64)
    if failed:
        print(f"验收结果: {len(gates) - failed}/{len(gates)} 项通过 — {failed} 项失败")
        return 1
    print(f"验收结果: {len(gates)}/{len(gates)} 项全部通过 — ΣLang 全链路可验收")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
