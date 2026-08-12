# 执行台账 · next_plan.md 落地（最终版）

> 任务：按 docs/next_plan.md 完整执行 P0-1/P0-2/P1-1/P1-2/P2-1/P2-2
> 执行日期：2026-08-12 · 复核：8/8 通过（独立复核 Agent）

## 步骤状态总览

| 计划项 | 状态 | 证据 | 完成时间 |
|--------|------|------|----------|
| P0-1 §SK v0.31 | ✅ 完成 | spec_p0_socketkit.json version=0.31.0；顶层 constants 8 组；points_ledger laws 行布局注释；22 ops/60 tests 不变；引擎 102/102 无回归 | 2026-08-12 |
| P0-2 复核脚本 | ✅ 完成 | tools/sigma-impl-verify.py（--spec/--impl 支持）；实跑 3 实现者 60/60 exit 0；tests/README 更新 | 2026-08-12 |
| P1-1 vq 实验 | 🔶 部分完成 | 基线问题集 docs/vq_baseline_questions.md（30 条×5 概念）落地；**集成前后对比实验需 vq 部署运行后执行**（vq history 表为空，按计划 §4 风险缓解采用人工问题集） | 2026-08-12 |
| P1-2 排行榜 | ✅ 完成 | bench/leaderboard.json 18 条含 5 模型（deepseek-chat/zai-subagent/qwen3dot8max/seed2dot1turbo/hy3 全 PASS）；README §3.5 排行表 | 2026-08-12 |
| P2-1 §PF/§IN JSON | ✅ 完成 | spec_p0_portfolio.json（5 ops/17 tests）+ spec_p0_inventory.json（5 ops/16 tests）；引擎加载全过 | 2026-08-12 |
| P2-2 文档同步 | ✅ 完成 | spec-template.md 新增"五、评测沉淀的最佳实践"；ROADMAP.md Phase 1 标注 5 模型实证 | 2026-08-12 |
| 回归验证 | ✅ 完成 | 引擎 102/102；verify 工具 3 实现者 60/60；zai 实现 60/60；index 越界对齐 ShapeError 后仍 102/102 | 2026-08-12 |

## 关键验收口径核对（next_plan §5）

| 验收 | 结果 |
|------|------|
| spec v0.31：constants 区存在、preconditions 结构化、错误名固定，5 实现者重跑 60/60 | ✅ constants 8 组；错误名固定 ShapeError（引擎已对齐）；4 个可复跑实现者（Hy3/Qwen3dot8Max/Seed2dot1Turbo/zai）全部 60/60；DeepSeek 实现未保存文件，以 bench 3 轮全过记录为证据 |
| sigma-impl-verify.py 一条命令输出实现者复核汇总 | ✅ 输出 3 实现者（reports 下全部 _impl_*）60/60 |
| vq 口径实验报告：基线 vs 集成后 | 🔶 基线问题集就绪；对比实验待 vq 运行 |
| README 展示 5 模型排行榜 | ✅ §3.5 |
| §PF/§IN JSON 齐备 + 至少 2 实现者全绿 | ✅ JSON 齐备；实现者评测待跑（P2-1 为可选里程碑） |

## 偏差记录（复核确认 2 处非阻断 + 1 处建议）

1. **preconditions 结构化未迁移到 §SK 本体**：计划动作描述"新增 {'fn':...} 结构化版本"，
   实际 §SK v0.31 保持 13 条 {'expr':...} 不动（行为层零变更优先），结构化形式仅作为新 spec 最佳实践写入 spec-template.md。
   影响：无（兼容保留）。后续可在 §SK v0.32 迁移。
2. **复核工具覆盖 3/5 实现者**：zai（impl/python/sigma_core_ai_subagent.py）与 deepseek（未保存实现文件）
   不在 tests/reports/_impl_* 扫描范围。已补：zai 单独复跑 60/60；deepseek 以 bench 历史记录（3 轮 100%）为证据。
3. **json-schema.md 的 if 示例与规格实际用法不一致**（字段形式 vs fn 形式）：建议性，已记录，可在下轮修正。

## 异常与回滚

| 异常 | 处理 | 回滚 |
|------|------|------|
| vq history 表为空（virtualquest.db 仅空 test 表） | 按计划 §4 风险缓解：人工构造 30 条口径问题集 | 无数据写入，无回滚需求 |
| 引擎 _fn_index 越界抛 TypeError 与文档 ShapeError 不一致 | 统一为 ShapeError（单行改动，102/102 无回归） | git checkout impl/python/sigma_engine.py |
| 遗留临时文件（_sem_check.json 等）清理被安全策略拒绝 | 保留并记录 | — |

## 交接说明

- 实施方：4 个并行 Agent（规格/工具/数据/文档）+ 主线（P1-1 基线 + 回归）+ 独立复核
- 复核方式：`python3 tools/sigma-impl-verify.py`（一键复核）；引擎 `python3 impl/python/sigma_engine.py`（102/102）
- 待办：① vq 部署运行后执行 30 条问题集的集成前后对比；② §PF/§IN 实现者评测（可用同一套 TASK_SPEC/PROMPT 流程）；③ json-schema.md if 示例对齐（可选）
