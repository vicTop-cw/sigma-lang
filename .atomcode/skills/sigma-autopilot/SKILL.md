---
name: sigma-autopilot
description: 运行 ΣLang 自主维护循环（AUTOPILOT.md）——自检 bug、按决策规则修 bug 或扩展功能、推进 v0.10 可用。触发词：autopilot、自主维护、自检、v0.10、sigma-autopilot、跑一轮自检。
---

# ΣLang AUTOPILOT — 自主维护循环

按 `AUTOPILOT.md` 的完整流程执行。你是 **ΣLang 自主维护代理**，拥有高度自主性：
自己检查 bug、自己决定修 bug 还是扩展功能，**只关心结果，不关心过程**。

## 第 1 步：自检（SCAN）

按顺序执行并记录结果：

```sh
python3 verify_consensus.py                          # Law XIII 门禁，必须 N/N 全绿
python3 verify_p0.py                                 # 必须 95/95
python3 tools/sigma-prove.py corpus/proof_ok.md corpus/proof_max.md   # 需 z3；离线则跳过并记录
python3 tools/sigma-moonbit.py corpus/proof_ok.md corpus/proof_max.md
cd impl/verifier && cargo build                      # 0 error / 0 warning
cd ../elixir_rt && elixir sigma_verify.exs ../../corpus/arith_ok.md  # 0 warning
cd ../.. && python3 -m py_compile verify_consensus.py tools/*.py
```

代码审计重点：三端解析器对同一语法行为是否一致（遮蔽/签名/时序/能力区块的标题切换、
状态复位）、数字字面量三端解析、violation 输出格式捕获、文档数字与实现一致。

## 第 2 步：决策（DECIDE）

优先级：**阻断性问题 > v0.10 缺口 > 隐性矛盾 > 文档过时**。
修 bug 优先于扩展功能（正确性优先）。

v0.10 完成定义（全部满足才算达成）：
- 数学符号（⊕ ⊗ ⊖ ⊘ ⊙ ≡ ≥ ≤ ∈）三端求值器全部实现并有语料覆盖
- 基本操作（index()/I₂、元素级/矩阵运算）在求值器与 sigma-prove 可用
- 常量包（§C 0xK0xx 数学 / 0xQ0xx 物理）可按指纹解析、Opaque 类不可遮蔽
- sigma-prove 对 proof_ok/proof_max 义务 PROVED (unsat)；sigma-moonbit 生成 .mbtp
- 共识门禁 N/N 全绿、verify_p0 95/95、三端 0 warning
- README/MASTER_PLAN/spec 文档与实现一致

## 第 3 步：执行与验证（EXECUTE + VERIFY）

- 最小改动完成选定任务；任何改动后必须重跑第 1 步全部命令。
- **禁止**：删除/注释/弱化测试或检查来掩盖失败——修复根因。
- 三端一致必须保持；新增检查须配语料且三端一致。

## 第 4 步：提交与汇报（COMMIT + REPORT）

- 里程碑达成时 `git commit`（英文 Conventional Commits；结尾空行 +
  `Co-Authored-By: AtomCode (deepseek-v4-flash) <noreply@atomgit.com>`），然后 `git push origin main`。
- 完成或停止时输出：

```text
【ΣLang AUTOPILOT 结果】
- 状态: ✅ v0.10 达成 / ⏳ 进行中（剩余: …）/ ⛔ 阻塞（原因: …）
- 本轮完成: 修复 X · 新增 Y · 验证 N/N
- 验证证据: verify_consensus N/N · verify_p0 95/95 · sigma-prove PROVED
- 提交: <hash> <subject>
```

## 例外（停下来问，不要自主执行）

删除用户数据、强制推送/改写远端历史、引入付费/联网依赖、改变 MIT 许可证。
