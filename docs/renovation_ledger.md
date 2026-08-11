# ΣLang 整改台账 · Renovation Ledger

> 生成时间：2026-08-11 · 最终更新：2026-08-11（复核修复后）
> 依据：docs/ROADMAP.md v1.0
> 状态图例：✅ 已完成 · 🔶 部分完成 · ⛔ 受阻（环境/外部依赖）

| 编号 | 标题 | 优先级 | 状态 | 证据 | 完成时间 |
|------|------|--------|------|------|----------|
| 4.1 | spec JSON 机器可解析格式 + §SK JSON | P0 | ✅ | `spec/spec_p0_socketkit.json`（22 ops / 60 tests，json.load 验证通过）；schema：`spec/json-schema.md`；复核 Agent 抽查 5 操作与 md 逐条一致 | 2026-08-11 |
| 4.2 | AI Verifier Benchmark 工具链 | P0 | ✅ | `tools/sigma-ai-bench.py`；`--mock --spec spec_p0_socketkit.json` 3 轮 90%→95%→100% 收敛 PASS（含复核发现的 codegen 偏差修复）；`bench/results.json` + `bench/leaderboard.json`；真实 LLM 需 SIGMA_LLM_API_KEY（见受阻项） | 2026-08-11 |
| 4.3 | README 重构 + 定位调整 | P0 | ✅ | `README.md` 415 行，五节结构（定位/快速体验/AI Benchmark/找茬 Demo/协议编写指南），主标题 "A Specification Protocol for Verifiable AI Consensus"；consensus 56/56、109/109、358 PROVED、--launch 等关键数据全部保留 | 2026-08-11 |
| 4.4 | 通用 spec→verifier 引擎 | P1 | ✅ | `impl/python/sigma_engine.py`；自检 102/102（corpus 60/60 + engine 42/42 含类型扩展用例）；加载 §SK JSON 求值全过 | 2026-08-11 |
| 4.5 | corpus JSON 格式迁移 | P1 | ✅ | `corpus/socketkit_taskflow_ok.json`（25 sequences / 42 steps，json.load 验证通过；$_ 链 12 处全部正确指向） | 2026-08-11 |
| 4.6 | spec → judge 二进制 | P2 | ✅（最小版） | `tools/sigma-spec2judge.py`；自检 correct 6/6 PASS、buggy 4/6 检出 2 条 WA；TLE/WA/MLE/缺函数/错误名不匹配均可检测；真实 spec CLI 验证通过 | 2026-08-11 |
| 4.7 | 类型系统扩展 | P2 | ✅（最小版） | 引擎新增 str_len/str_concat/str_contains/time_now_epoch/option_*/map_get 等 14 条用例；schema 追加 Str/Time/Option/Map 说明；原有 corpus 60/60 零破坏 | 2026-08-11 |
| 4.8 | 社区建设 | P2 | 🔶 部分完成 | ✅ `docs/spec-template.md`（编写模板+最佳实践+歧义自查表）；⛔ 跨模型排行榜发布需真实 LLM API 凭据、开放 benchmark 提交需外部平台 | 2026-08-11 |

## 验收标准映射（ROADMAP §六）

| 验收条件 | 对应整改项 | 验证结果 |
|----------|-----------|----------|
| §SK JSON 与 Markdown 语义等价 | 4.1 | JSON 22 ops/60 tests 合法；复核 Agent 抽查 5 操作 tests/laws 与 md 逐条对应 |
| sigma-ai-bench.py 可跑通 ≥1 模型 | 4.2 | `--mock --spec spec_p0_socketkit.json` 3 轮收敛 100%（mock 伪模型演示完整管线） |
| ≥1 AI 模型 ≤3 轮通过 consensus gate | 4.2 | ⛔ 需外部 LLM 凭据（SIGMA_LLM_API_KEY），本环境无法执行真实评测；工具链已就绪 |
| README 定位已修正 | 4.3 | 主标题/定位语/五节结构落地，关键数据保留 |
| 通用 verifier 引擎可消费 JSON spec | 4.4 | 引擎加载 §SK JSON 跑通 corpus 60/60 |
| spec→judge 可一键生成 | 4.6 | judge 自检 + 真实 spec CLI 验证（correct 6/6、buggy 检出 2 WA） |

## 回归验证（受整改影响的部分）

| 验证项 | 命令 | 结果 |
|--------|------|------|
| 引擎自检（含类型扩展） | `python3 impl/python/sigma_engine.py` | 102/102 通过 |
| 参考实现回归 | `python3 impl/python/sigma_core.py` | 167/167 通过（未改动） |
| 三端共识（复核 Agent 实证） | `python3 verify_consensus.py` | 56/56 全绿 |
| P0 算法正确性（复核 Agent 实证） | `python3 verify_p0.py` | 109/109 全绿 |
| bench mock 管线（修复后） | `python3 tools/sigma-ai-bench.py --mock --spec spec_p0_socketkit.json` | 90%→95%→100%，PASS |

## 变更清单（git status，整改产生）

**新增（本次整改）**：
- `spec/json-schema.md`、`spec/spec_p0_socketkit.json`
- `impl/python/sigma_engine.py`
- `tools/sigma-ai-bench.py`、`tools/sigma-spec2judge.py`
- `corpus/socketkit_taskflow_ok.json`
- `docs/ROADMAP.md`、`docs/spec-template.md`
- `bench/`（results.json、leaderboard.json）
- 此前实验产物：`docs/auction_dual_impl_report.html`、`spec/spec_p0_auction.md`、`impl/python/sigma_auction_a.py`、`sigma_auction_b.py`

**修改（本次整改）**：`README.md`（4.3 重构）

**仓库原有未提交修改（非本次整改产生，未触碰）**：AUTOPILOT.md、MASTER_PLAN.md、docs/USAGE.md、impl/python/sigma_app.py、impl/verifier/src/app.rs、tools/sigma-accept.py、tools/sigma-prove.py

**遗留临时文件（清理命令被安全策略拒绝，未删除）**：`impl/python/tmp_run1.txt`、`impl/python/tmp_run2.txt`（引擎自检输出）、`_judge_probe.py`（judge 探测文件）

## 假设与说明

1. ROADMAP 验收"≥1 AI 模型 ≤3 轮通过 consensus gate"需真实 LLM API 凭据，本环境无法执行；以 mock 模式验证工具链正确性作为替代证据（第 1 轮注入 2 个种子 bug → 反馈修正 → 第 3 轮 100%）。
2. 4.8 排行榜发布与开放提交需外部平台（模型厂商/GitHub），标记受阻并给出后续动作。
3. 4.6 "独立二进制"以脚本形式交付；内存限制在 POSIX 生效，Windows 降级为仅时间限制（工具内已实现降级提示）。
4. git 仓库中其他 M 文件为整改前已存在的未提交改动，整改期间未修改。
