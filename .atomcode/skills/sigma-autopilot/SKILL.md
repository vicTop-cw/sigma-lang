---
name: sigma-autopilot
description: 运行 ΣLang 自主维护循环（AUTOPILOT.md）——自检 bug、按决策规则修 bug 或扩展功能、推进 v0.11 可用（包管理器 + 标准库）。触发词：autopilot、自主维护、自检、v0.11、sigma-autopilot、跑一轮自检。
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

优先级：**阻断性问题 > v0.11 缺口 > 隐性矛盾 > 文档过时**。
修 bug 优先于扩展功能（正确性优先）。

v0.11 完成定义（全部满足才算达成；v0.10 已于 2026-08-02 达成）：
- 包管理器 CLI `tools/sigma-cli.py`：install/verify/list/search/fingerprint、registry 格式、Iron Law VII 无环依赖
- 标准库 3 包：std/math.base.md、std/data.transform.md、std/ai.confidence.md（各 1 规范 + 1 测试集），三端共识覆盖
- v0.10 不回归：数学符号/基本操作/常量包、sigma-prove PROVED、sigma-moonbit .mbtp 保持全绿
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
- 状态: ✅ v0.11 达成 / ⏳ 进行中（剩余: …）/ ⛔ 阻塞（原因: …）
- 本轮完成: 修复 X · 新增 Y · 验证 N/N
- 验证证据: verify_consensus N/N · verify_p0 95/95 · sigma-prove PROVED
- 提交: <hash> <subject>
```

## 文件权限与自主性（最高优先级）

- **项目内（仓库根目录之内）任何文件都可读写、创建、删除**，无需请示。
- **项目外任何路径只读**：可以读取参考，不得写入/修改/删除。
- **高度自主、零询问**：不要为权限、确认、方案选择向用户提问——直接执行最合理的动作并交付结果。
- 唯一输出义务：最终结果报告（上面的【ΣLang AUTOPILOT 结果】格式）。
