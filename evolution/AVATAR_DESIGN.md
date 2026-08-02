# AVATAR — 我理解的产品设计

## 一、核心概念

```
avatar.toml            ← 配置文件（唯一入口）
├── [project]          ← 项目路径、名称
├── [goal.current]     ← 当前目标
├── [goal.history]     ← 已完成的目标列表
├── [detect]           ← 检测规则
├── [agents]           ← agent 分配
└── [cycle]            ← 轮询设置

logs/                  ← 每个目标周期一个独立日志
├── 20260802-143001-add iron laws/   ← 按"目标名+时间"分目录
│   ├── cycle_01.log                  ← 第 1 轮日志
│   ├── cycle_02.log                  ← 第 2 轮日志
│   └── final_summary.md              ← 完成总结
├── 20260803-090000-fix test module E/
│   └── ...
└── 20260805-150000-expand verify to 200/
    └── ...

history/               ← 已完成目标的归档（配置快照+最终提示词模板）
├── 20260802-143001-add iron laws/
│   ├── goal_snapshot.toml            ← 当时 avatar.toml 中此目标的快照
│   └── prompt_template.txt           ← 最后使用的提示词模板
└── 20260803-090000-fix test module E/
    └── ...
```

---

## 二、avatar.toml 配置结构

```toml
[project]
name = "sigma-lang"
path = "."                           # git 项目路径

# ── 当前目标 ──
[goal.current]
id = "20260802-143001-add-iron-laws"
title = "实现 12 条 Iron Law 的自动验证"
description = "在 verify_p0.py 中为 12 条 Iron Law 各加一组自动化测试，通过后更新 spec"
created_at = "2026-08-02T14:30:01"

# ── 检测规则 ──
[detect]
scan_todos = true                    # grep TODO/FIXME
scan_bugs = true                     # grep BUG/HACK
run_tests = true
test_command = "python3 verify_p0.py"
watch_patterns = ["spec*.md", "verify*.py", "impl/", "tools/"]

# ── Agent 分配 ──
[agents]
implementer = "reasonix"             # 主力实现 agent
reviewer = "claude-code"             # review agent
max_delegated_per_cycle = 1          # 每次最多派一个任务

# ── 轮询 ──
[cycle]
interval_seconds = 900               # 15 分钟一轮
auto_commit = true
auto_push = true

# ── 历史目标（完成后自动追加） ──
[[goal.history]]
id = "20260801-120000-baseline-tests"
title = "95 个 P0 基础测试全部通过"
completed_at = "2026-08-02T10:00:00"
result = "success"
logs_dir = "logs/20260801-120000-baseline-tests/"
```

---

## 三、一轮完整流程

```
┌─────────────────────────────────────────────────────────┐
│ 第 N 轮开始                                              │
│                                                         │
│ 1. SCAN 阶段                                            │
│    ├── git pull origin main                              │
│    ├── git status --short                                │
│    ├── grep -rn "TODO|FIXME|BUG" spec* verify* impl/     │
│    └── python3 verify_p0.py                              │
│                                                         │
│ 2. DECIDE 阶段                                          │
│    ├── 无变更 + 测试全过 → "本轮无事，等待下一轮"          │
│    ├── 测试失败 → "修复失败的测试"                        │
│    ├── 有 TODO → "实现 TODO 项"                          │
│    └── 以上都没有 → "从 goal.description 拆下一步任务"    │
│                                                         │
│ 3. GENERATE 阶段                                        │
│    ├── 合并 goal.description + 检测结果                  │
│    ├── 生成一个具体的子任务提示词                          │
│    └── 写入本轮日志                                      │
│                                                         │
│ 4. DELEGATE 阶段                                        │
│    ├── delegate_task → agents.implementer                │
│    └── 等待完成                                          │
│                                                         │
│ 5. VERIFY 阶段                                          │
│    ├── 跑测试验证                                        │
│    ├── 失败 → 把错误信息追加到下一轮提示词中               │
│    └── 通过 → 继续                                       │
│                                                         │
│ 6. COMMIT 阶段                                          │
│    ├── git add -A                                       │
│    ├── git commit -m "avatar: <本轮任务摘要>"            │
│    └── git push origin main                              │
│                                                         │
│ 7. LOG 阶段                                             │
│    └── 写入 logs/<goal_id>/cycle_<N>.log                 │
│                                                         │
│ 8. CHECK GOAL 完成？                                     │
│    ├── 检测条件：所有测试通过 + 无 TODO + goal 描述匹配   │
│    ├── 未完成 → sleep → 下一轮                            │
│    └── 完成 → 进入目标完成流程                            │
└─────────────────────────────────────────────────────────┘

目标完成流程:
  1. 生成 final_summary.md（本轮做了什么、测试变化、新功能列表）
  2. 将 goal.current 移动到 goal.history
  3. 将当前 .toml 快照保存到 history/<goal_id>/goal_snapshot.toml
  4. 把最后使用的提示词模板保存到 history/<goal_id>/prompt_template.txt
  5. 扫描剩余 TODO → 生成新 goal 模板
  6. 更新 avatar.toml 中 goal.current 为新目标
  7. 新目标从第一轮开始 → 新 logs/<new_goal_id>/ 目录
```

---

## 四、日志分离示例

```
logs/
├── 20260801-120000-baseline-tests/
│   ├── cycle_01.log   "开始: 95 个测试当前 0 通过"
│   ├── cycle_02.log   "修复: Module T 时间模块"
│   ├── cycle_03.log   "修复: Module E 错误模块"
│   ├── ...
│   ├── cycle_12.log   "95/95 全部通过!"
│   └── final_summary.md
│
├── 20260802-143001-add-iron-laws/
│   ├── cycle_01.log   "扫描: 发现 12 条 Iron Law 未验证"
│   ├── cycle_02.log   "实现: Law I-III 的验证"
│   └── ...（进行中）
│
└── 20260805-090000-expand-verify-to-200/
    └── ...（下一个目标）
```

**每个目标一个目录，每个目录内每轮一个日志。不揉在一起。**

---

## 五、历史提示词不丢失

```
history/20260801-120000-baseline-tests/
├── goal_snapshot.toml       ← 该目标完成时的 avatar.toml 完整快照
└── prompt_template.txt      ← 最后使用的提示词模板（可复现、可迭代）

history/20260802-143001-add-iron-laws/
├── goal_snapshot.toml
└── prompt_template.txt
```

新目标生成时，可以从历史模板中**继承**之前的检测规则和 agent 配置，只改变 goal。

---

## 六、最终目录结构

```
sigma-lang/
├── avatar.toml                       ← 唯一入口
├── avatar.py                         ← 守护进程（150行）
├── logs/                             ← 日志（按目标分目录）
│   ├── 20260801-120000-baseline-tests/
│   ├── 20260802-143001-add-iron-laws/
│   └── ...
├── history/                          ← 历史快照
│   ├── 20260801-120000-baseline-tests/
│   └── ...
├── verify_p0.py                      ← 现有项目文件（不变）
├── spec*.md
└── ...
```

---

## 七、和我理解对比确认

| 你的要求 | 我的理解 |
|---------|---------|
| "历史的自动提示词配置不能丢" | history/ 保存每个目标的配置快照 + prompt 模板 |
| "完成目标后进入历史" | goal.current → goal.history 自动迁移 |
| "起一个新的配置提示词模板" | 扫描剩余 TODO → 生成新 goal 填入 avatar.toml |
| "每个提示词配置要有相应的 log" | logs/<goal_id>/cycle_<N>.log 分目录分文件 |
| "不要全部揉在一起" | 一个目标 = 一个日志目录，一轮 = 一个文件 |

---

**这个理解对吗？对的话我开始写 `avatar.py`。**
