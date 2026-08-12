# ΣLang 下一步计划 · Next Plan v1.0

> **依据**：2026-08-12 跨工具一致性评测（5 实现者 60/60 全绿）+ 三份实现报告的规格改进建议
> **日期**：2026-08-12
> **原则**：先修规格质量（响应真实反馈）→ 再固化评测流程 → 然后推向真实场景（vq）与公开数据（排行榜）

---

## 0. 评测结论回顾（计划的依据）

| 结论 | 数据 |
|------|------|
| 行为层零分歧 | 5/5 实现者（DeepSeek / zai / Qwen3dot8Max / Seed2dot1Turbo / Hy3）全部 60/60 |
| 规格可被 AI 直接消费 | 全部仅凭 spec JSON + 任务说明书独立实现，无需人工翻译 |
| 错误语义可传递 | 10 种错误名全部被精确复现 |
| 表示层有改进空间 | 三份报告共同提出 6 类规格改进建议（见 P0-1） |
| 手动评测流程可行 | tests/ 目录流程（TASK_SPEC + PROMPT + reports）跑通，报告与实现文件可复核 |

---

## 1. 目标

1. **规格质量再进一步**：落实评测报告的全部改进建议，让 §SK 对任意 AI 的"零歧义"能力更强
2. **评测流程固化**：手动流程 + 自动化复核脚本，后续评测一条命令完成
3. **推向真实场景**：vq 口径层实验拿到真实业务数据
4. **公开首批数据**：5 模型跨工具排行榜发布

---

## 2. 整改项（按优先级）

### 🔴 P0-1：§SK spec v0.31 改进（响应三份报告的反馈）

**现状问题**（来自评测报告）：

| # | 问题 | 提出者 |
|---|------|--------|
| 1 | preconditions 用字符串表达式（`sum_contribs(c) > 0`），definition 用结构化 `{"fn":...}`，两套表示法并存 | Hy3、Qwen |
| 2 | `min`/`max` 重载语义不明确（列表最值 vs 两数取大） | Hy3 |
| 3 | `index` 越界报错名 "ShapeError 或 TypeError" 二选一未定 | Hy3、Qwen |
| 4 | 魔法常量散落（状态值 0-3、徽章阈值 100/300/600、验证者门槛 1000、契分系数 5/0.7） | Qwen |
| 5 | `points_ledger` law 行布局易误读（金额位 vs source 位） | Qwen |
| 6 | 类型守卫边界未统一定义（哪些操作需要类型检查、错误名） | Qwen、Seed |

**动作**：
1. `spec_p0_socketkit.json` 顶层新增 `constants` 区（状态值、阈值、系数集中定义）
2. preconditions 统一为结构化形式：`{"expr": "..."}` 保留兼容，新增 `{"fn": ...}` 结构化版本；内置函数表补全 `sum_contribs` / `min_source_id`
3. 固定 `index` 越界错误名（建议 `ShapeError`，与现有实现一致）
4. 在 `json-schema.md` 明确 `min`/`max` 重载语义（单列表参数取最值，多参数取最值）
5. `points_ledger` 的 laws 补充输入/输出行布局注释
6. 类型守卫规范写入 json-schema.md（列表参数收非列表 → `TypeError`）
7. 同步更新 `TASK_SPEC.md` 与 `spec-template.md`

**验收**：
- 规格变更后，5 个既有实现重跑仍全部 60/60（无回归）
- 新写的常量/结构测试进自检
- 变更记录在 git（commit message 标注 v0.31）

### 🔴 P0-2：评测复核工具化（固化 tests/ 流程）

**现状**：手动流程可行，但复核靠人（我逐份重跑）。

**动作**：
1. 新增 `tools/sigma-impl-verify.py`：扫描 `tests/reports/_impl_*.py`，逐个加载执行，
   与 `spec_p0_socketkit.json` 的 60 条测试对拍，输出汇总表（实现者 / 通过率 / 失败项）
2. 支持 `--spec` 参数（后续 §PF/§IN 复用）
3. README（tests/）补充"一键复核"命令

**验收**：一条命令 `python3 tools/sigma-impl-verify.py` 输出 5 实现者的复核汇总，数字与手工复核一致。

### 🟡 P1-1：vq 口径语义层实验（第一个真实业务数据）

**现状**：M1/M2 已实现（spec_service + 5 概念 + prompt 注入），M3 校验模块已有雏形。

**动作**：
1. 按 `virtualQuest/docs/sigma_integration.md` §6 建立基线：从 history 导出问题，按三类错误打标，算口径类错误率基线
2. 集成后同批问题对比，验证口径类错误率下降 ≥30%
3. 补 M3 联调（spec_validator 接入 sql_validator 之后的口径校验）

**验收**：拿到 vq 的真实对比数据（基线 vs 集成后），写入 sigma-lang 文档作为 case study。

### 🟡 P1-2：AI Benchmark 首批排行榜发布

**现状**：5 个实现者数据已存在（leaderboard.json 有 deepseek + mock；qwen/seed/hy3/zai 在 tests/reports/）。

**动作**：
1. 把 5 个模型的结果统一录入 `bench/leaderboard.json`（格式统一：模型 / spec / 轮次 / 通过率 / 来源）
2. README §3（AI Benchmark）展示跨模型排行榜表
3. 更新 `docs/ai_consistency_report.html` / `docs/cross_tool_report.html` 互为引用

**验收**：README 一处即可看到 5 模型排行；数据可追溯到报告文件。

### 🔵 P2-1：§PF / §IN 复用评测（可选）

**现状**：只有 §SK 有 JSON 格式（4.1 只做了 §SK）。

**动作**：
1. 为 `spec_p0_portfolio.md`（§PF 金融）与 `spec_p0_inventory.md`（§IN 供应链）生成 JSON
2. 用同一套 TASK_SPEC/PROMPT 流程评测（或 bench 驱动）
3. 三域全绿 → 协议跨域一致性的完整证据

**验收**：三域 JSON 齐备；至少 2 个实现者在 §PF/§IN 上 60/60。

### 🔵 P2-2：文档与模板同步

- `docs/spec-template.md` 加入本评测沉淀的最佳实践（constants 区、结构化 preconditions、类型守卫、错误名固定）
- `docs/ROADMAP.md` 更新 Phase 1 状态（AI 评测已实证 5 模型）

---

## 3. 依赖与时间线

```
第 1 周：P0-1（spec v0.31）→ P0-2（复核脚本）→ 5 实现者重跑回归
第 2 周：P1-1（vq 实验）‖ P1-2（排行榜发布）
第 3 周起：P2-1（§PF/§IN JSON + 评测）→ P2-2（文档同步）
```

依赖关系：
- P0-1 → P0-2（复核脚本按新 spec 写）
- P0-1 → P1-2（排行榜数据用 v0.31 规格重跑确认）
- P1-1 独立（vq 侧）
- P2-1 依赖 §PF/§IN JSON 转换

---

## 4. 风险与假设

| 风险 | 缓解 |
|------|------|
| spec v0.31 改动导致既有实现回归 | 5 实现者重跑是强制验收；改动集中在表示层（constants/结构化），行为层不变 |
| vq 实验拿不到足够历史数据（history 表数据少） | 用人工构造的 20-30 条口径问题集代替（方案文档 §6.3 最少实验集） |
| §PF/§IN JSON 转换工作量大 | 复用 §SK 转换经验；可与 vq 实验并行 |
| 排行榜数据口径不一致（不同轮次/来源） | leaderboard 记录来源字段（api/agent/manual），注明评测方式 |

---

## 5. 成功标准（可检查）

- [ ] `spec_p0_socketkit.json` v0.31：constants 区存在、preconditions 结构化、错误名固定，5 实现者重跑 60/60
- [ ] `tools/sigma-impl-verify.py` 一条命令输出 5 实现者复核汇总
- [ ] vq 口径实验报告：口径类错误率基线 vs 集成后对比
- [ ] README 展示 5 模型排行榜
- [ ] （可选）§PF/§IN JSON 齐备 + 至少 2 实现者全绿
