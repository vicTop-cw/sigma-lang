# ΣLang §SK 协议独立实现任务说明书

> **任务编号**：TASK-2026-08-12-SK
> **用途**：跨工具（Qoder / TRAE / WorkBuddy / 其他 AI）独立实现一致性评测
> **预期耗时**：30-60 分钟

---

## 一、背景

ΣLang 是一套"面向可验证 AI 共识的规约协议"：把业务规则写成**机器可解析、无歧义**的规格（JSON），
任何 AI 读同一份规格，应该产出完全一致的实现。本任务是验证这一点——不同工具读同一份规格，
实现的业务行为是否逐项一致。

规格文件：`E:\IDEProjects\AI\sigma-lang\spec\spec_p0_socketkit.json`
（找茬业务：发单/接单/提交/验收/契分/额度/积分/徽章/团队/分账/账本，共 **22 个操作、60 条测试**）

**规格版本**：v0.31.0（本次新增顶层 `constants` 区，见「三、实现规则 §3.6」）

**硬性要求**：
- 只读 `spec_p0_socketkit.json`（与本文档），**禁止**查看仓库内任何已有实现
  （`impl/python/sigma_core.py`、`sigma_engine.py`、`corpus/`、`impl/verifier/`、`impl/elixir_rt/`）
- 独立实现，不与其他工具交流

---

## 二、任务步骤

1. 通读规格文件 `spec_p0_socketkit.json`（结构：`types` + `operations`，每个 operation 含
   `fingerprint` / `signature` / `definition` / `preconditions` / `tests`）
2. 按每个操作的 `definition` 实现同名 Python 函数（见下文"三、实现规则"）
3. 实现完成后，按"五、自检要求"逐条执行全部 60 条测试，统计通过率
4. 按"六、报告模板"生成报告，保存到 `E:\IDEProjects\AI\sigma-lang\tests\reports\<工具名>.md`

---

## 三、实现规则（重要）

### 3.1 函数签名

每个操作的函数签名按 `signature.params` 顺序定义，参数个数与顺序必须一致。

### 3.2 返回值

按 `definition.body` 求值：
- `{"list": [...]}` → 返回列表
- 参数名引用 → 返回对应参数值
- 嵌套调用 `{"op": "...", "args": [...]}` → 递归调用对应操作函数
- 条件 `{"if": cond, "then": ..., "else": ...}` → 按条件分支

### 3.3 错误处理（关键）

- 先检查 `preconditions`：不满足时抛 `ValueError("错误名")`
- 错误名必须与 `tests` 中 `error` 字段**完全一致**，常见错误名：
  `BountyErr` / `StateError` / `AuthError` / `TypeError` / `QuotaExhausted` /
  `InsufficientEscrow` / `InsufficientPoints` / `TeamFull` / `DivByZero` / `NotTraceable`
- 输入类型不对（如期望列表收到整数）也应抛 `ValueError("TypeError")`，不要抛 Python 原生异常
- **类型守卫规范（v0.31 固定）**：
  - 列表参数收到非列表（如 `review_merge(3)` / `quota_advance(5)`）→ 抛 `ValueError("TypeError")`
  - `index` 越界（索引超出列表长度）→ 抛 `ValueError("ShapeError")`（固定错误名）
  - 其余业务错误按各操作 `preconditions` 的 `error` 字段命名

### 3.4 内置函数语义（definition 中 `{"fn": "xxx", "args": [...]}`）

| 函数 | 语义 |
|------|------|
| `index(coll, i)` | 取列表第 i 个元素；**越界抛 `ShapeError`**；非列表/非整数参数抛 `TypeError` |
| `min` / `max` | **重载**：单列表参数 → 取该列表的最值；多参数 → 取所有参数的最值（§SK：`max(0, fold_add(a))`） |
| `add` / `sub` | 整数加 / 左结合减 |
| `ge` / `lt` / `eq` 等 | 比较运算 |
| `fold_add(xs)` | 若 xs 是列表的列表 → 每行**最后一个元素**求和；否则普通求和 |
| `fold_credit(init, events)` | 契分折叠：初始 init；事件 `[kind, count]`：kind=0 → `+5×count`；kind=1 → 逐次 `×7//10`（向下取整）；结果下限 0 |
| `weighted_accept(xs)` / `weighted_support(xs)` | 对 `[reviewer, vote, weight]` 行，vote==1 的 weight 之和 |
| `weighted_reject(xs)` | vote==0 的 weight 之和 |
| `split_floor(contribs, reward)` | 按贡献分账：`share = floor(reward × c / total)`；total==0 抛 `DivByZero` |
| `enumerate_ledger(entries)` | 输入 `[[旧id, 金额, source], ...]` → 输出 `[[1, source, 金额], [2, ...], ...]`（编号 1..n）；source<1 抛 `NotTraceable`；金额<0 抛 `TypeError` |

**preconditions 表达式辅助函数**（`preconditions[].expr` 字符串中可用，白名单）：
`index` / `min` / `max` / `len` / `abs` / `sum` / `sum_contribs` / `min_source_id`。

- `sum_contribs(c)`：c 的每行第 2 列（贡献）之和（`team_share` 前置条件用）；
- `min_source_id(e)`：e 的每行第 3 列（source）最小值，空列表返回 +∞（`points_ledger` 前置条件用）。

### 3.5 关键业务规则速查（与规格 JSON 一致，以 JSON 为准）

- 任务状态机：0=open →(accept_task)→ 1=in_progress →(task_submit)→ 2=pending_review →(task_accept)→ 3=completed
- `task_accept` 仅作者本人（caller == 作者）可验收，否则 `AuthError`；状态不对抛 `StateError`
- `credit_score` 从 100 起算（fold_credit）
- `badge_issue` 需要 v ≥ 1000（核验师权限）
- `team_join` 超过容量抛 `TeamFull`；`team_share` 总贡献为 0 抛 `DivByZero`
- 积分：`points_hold` 冻结（可用→托管），`points_release` 释放（托管→可用），余额不足分别抛 `InsufficientEscrow` / `InsufficientPoints`

### 3.6 顶层 `constants` 区（v0.31 新增）

spec JSON 顶层新增 `constants` 对象，集中声明散落在 definition / laws / preconditions 中的魔法常量。
实现**必须使用** `constants` 中的数值，不得自行另设：

| 常量 | 值 | 出处 |
|------|-----|------|
| `status` | open=0 / in_progress=1 / pending_review=2 / completed=3 | 任务状态机 |
| `decision` | reject=0 / accept=1 | 评审/仲裁结果 |
| `badge.thresholds` | 100 / 300 / 600 | `badge_level` 档位 |
| `badge.levels` | bronze=0 / silver=1 / gold=2 / diamond=3 | 徽章等级 |
| `verifier_min_id` | 1000 | `badge_issue` 核验师门槛 |
| `credit.initial` | 100 | `credit_score` 起算值 |
| `credit.kind0_per_completion` | 5 | 完成事件 +5 |
| `credit.kind1_floor_ratio` | 7/10（×7//10） | 违约事件系数 |
| `credit.floor` | 0 | 契分下限 |
| `contribution.floor` | 0 | `contribution_score` 下限 |
| `team.min_capacity` | 1 | `team_create` 容量下限 |
| `ledger.entry_id_start` / `ledger.min_source_id` | 1 / 1 | `points_ledger` 编号起点与可追溯门槛 |

---

## 四、测试输入说明

- 测试 `input` 中可能出现嵌套调用 `{"op": "task_create", "args": [7, 100]}` ——表示先求值该调用，结果作为参数
- `"$_"` 表示上一操作的结果（仅序列测试使用）
- 测试 `expect` 为期望输出；`error` 为期望错误名；两者必有其一

---

## 五、自检要求

- 逐条执行 60 条测试（不要抽样）
- 每条判定：输出完全相等（列表逐元素相等）或错误名完全一致
- 输出汇总：`通过 N / 60`

---

## 六、报告模板

报告保存为 `E:\IDEProjects\AI\sigma-lang\tests\reports\<工具名>.md`，格式：

```markdown
# <工具名> × ΣLang §SK 实现报告

- **完成时间**：YYYY-MM-DD HH:MM
- **实现方式**：（如：直接实现 / 读 JSON 后实现 / 其他）
- **通过率**：N/60（x%）

## 失败清单（如有）
| 操作 | 测试描述 | 期望 | 实际 |
|------|----------|------|------|

## 实现说明
（你如何理解 definition、遇到的主要歧义点）

## 困难与建议
（规格中不清楚的地方、改进建议）

## 声明
- 我确认未参考仓库内已有实现（sigma_core.py 等）
```

---

## 七、验收

- 报告存在且通过率明确
- 失败清单逐条列出（如全过则写"无"）
- 通过率数字可复核（报告附上执行过程说明）
