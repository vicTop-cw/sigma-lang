# AVATAR — 状态：已完成并验证（2026-08-02）

> 写给 AtomCode：这是一个配置驱动的自动维护 Agent，放到任意 Git 项目即可自动发现
> TODO/测试失败/git 变更，生成提示词并分派给 AI 专家修复；达成目标后自动定制下一轮
> goal 与对应的提示词模板，进入下一阶段。已在 **Windows 原生 Python 3.13** 上端到端验证通过。

---

## 一、完成状态

| 文件 | 行数 | 状态 |
|------|------|------|
| `avatar.toml` | ~45 | ✅ 配置模板，已测试可解析 |
| `avatar.py` | ~591 | ✅ 核心逻辑完成，Windows 原生 Python 跑通 |
| `evolution/AVATAR_DESIGN.md` | - | ✅ 设计文档（实现已对齐） |

---

## 二、avatar.py 架构（与实现一致）

```
main()
├── --once / --dry-run → run_one_cycle()
├── --interval N        → 循环调用 run_one_cycle()
│
run_one_cycle()
├── SCAN:   git fetch → git status → run tests → 原生 Python 扫描 TODO
├── CHECK:  测试全过 + 无 TODO → GOAL COMPLETE（dry-run 只读，不落盘）
│   └── 两阶段完成（防「以为完成却还有遗漏」）：
│       阶段1/2：达成 → 仅标注 goal.completed_at + pending_verification=true，
│                 不迁移、不拟定新目标
│       阶段2/2：下一轮核验 —— 检查 git 变更中命中 watch_patterns（主项目源码）
│                 的文件：
│                 - 有源码改动 → 核验未通过，保持 pending，继续下一轮
│                 - 无源码改动 → 核验通过，才 complete_goal()（迁移+新目标）
├── DECIDE: 测试失败 > TODO 列表 > git 变更 > 推进目标
├── GENERATE: 合并 goal + scan 结果 → 动态 prompt
├── DELEGATE: subprocess 调 AI agent (atomcode)，替换 {prompt}/{project_path}
├── VERIFY:  re-run tests
├── COMMIT:  git add -A && git commit && git push
└── LOG:     写入 logs/<goal_id>/cycle_NN.log

complete_goal()（核验通过后才调用）
├── 归档：history/<goal_id>/goal_snapshot.toml + prompt_template.txt
├── 快照：logs/<goal_id>/final_summary.md
├── 迁移：goal.current → goal.history
├── 定制下一轮 goal：_generate_next_goal() 扫描剩余 TODO，
│   按文件分组取 TODO 最集中者 → 生成新 title + description
└── 配置下一轮提示词：logs/<new_goal_id>/next_goal_prompt.txt
    （首轮提示词模板，标题/描述取自新目标）
```

---

## 三、本轮修复的问题

### 问题 1：`run_one_cycle()` 在 WSL 卡死 ✅ 已解决
- 根因：`scan_todos` 依赖外部 `grep` 子进程，WSL 下组合调用阻塞。
- 修复：改为**原生 Python `os.walk` 扫描**（不依赖 grep），按 `watch_patterns`
  匹配文件，跳过构建/缓存/隐藏目录（.git/target/__pycache__/archive 等），
  单文件 >256KB 跳过，最多返回 30 条。跨平台无子进程卡死。
- 顺带修复：原实现 `for pat in patterns:` 循环体没用 `pat`，会对每个 pattern
  重复扫全库，导致把自己（avatar.py/avatar.toml）扫进 TODO 列表。

### 问题 2：日志路径硬编码 `/tmp/avatar_logs` ✅ 已解决
- WSL 时代的 `/tmp` 在 Windows 下被解析成 `E:/tmp/avatar_logs`（盘符根）。
- 修复：改为项目内 `logs/`（`get_log_dir()`），可用 `[cycle].log_dir` 覆盖。

### 问题 3：测试命令 `python3` 在 Windows 不可靠 ✅ 已解决
- `run_tests` 把 `python3`/`python` 替换为 `sys.executable`，超时放宽到 30s。

### 问题 4：dry-run 产生真实副作用 ✅ 已解决
- 原实现 dry-run 也会触发 `complete_goal`（改 avatar.toml、建 history/）。
- 修复：dry-run 检测到 GOAL COMPLETE 时只写日志并注明「不落盘」。

### 问题 5：`save_config` 丢字段 / delegate 引号 bug ✅ 已解决
- `save_config` 补回 `watch_patterns`、`agent.args`、`max_delegated_per_cycle`、
  history 的 `description`。
- `delegate_to_agent` 去掉 `shlex.quote`（list 形式传参不需要 shell 引号，
  Windows 下会把引号当字面量传给程序）。

---

## 四、端到端验证结果（Windows 原生 Python 3.13）

临时项目 `_avatar_test/`（git 仓库，验证后已删除）：

### 目标达成闭环（上一轮已验）
1. 有 TODO（`src/legacy.py` 2 处）→ DECIDE `resolve_todos`，prompt 正确生成 ✅
2. 无 TODO 时新目标为「推进项目里程碑（无遗留 TODO）」；有 TODO 时聚焦
   TODO 最集中的文件并列出具体行 ✅

### 两阶段完成闭环（本轮新增验证）
**场景 A（核验通过）：**
1. 第 1 轮：测试 PASS + 无 TODO → 阶段1/2，仅写 `completed_at` +
   `pending_verification=true`，**不**迁移、**不**拟定新目标、无 history ✅
2. 第 2 轮：git 变更中无命中 watch_patterns 的文件 → 阶段2/2 核验通过 →
   `complete_goal()`：归档 `history/test-goal-003/`、拟定新目标
   `20260802-061327-next`、生成 `next_goal_prompt.txt`、迁移 goal.current ✅

**场景 B（核验失败——源码有改动）：**
1. 第 1 轮：达成 → 仅标注 pending ✅
2. 修改 `src/mod.py` 后第 2 轮：核验检出 `src/mod.py` 改动 →
   **保持 pending**，不拟定新目标、不建 history，日志注明
   「下一轮继续核验」✅

### 既有回归
- dry-run 只读：不落盘（avatar.toml 无 pending 字段、无 history）✅

---

## 五、接入后的验证步骤

```bash
cd E:\IDEProjects\AI\sigma-lang

# 1. 确认配置可解析
python -c "import avatar; cfg=avatar.load_config('.'); print(cfg['project']['name'])"
# 预期: sigma-lang

# 2. 干跑一轮（只读：scan + generate prompt，不 delegate、不改配置）
python avatar.py --dry-run
# 预期: scan → generate prompt → 写日志到 logs/20260802-baseline/cycle_NN.log

# 3. 查看日志
cat logs/20260802-baseline/cycle_01.log

# 4. 正式跑（会调 atomcode 修复任务）
python avatar.py --once --project .
```

---

## 六、avatar.py 关键函数速查（行号随实现微调，以 list_symbols 为准）

| 函数 | 用途 |
|------|------|
| `load_config()` | TOML 解析（Python 3.6+ 兼容，tomllib/tomli/内置 parser 三级降级） |
| `save_config()` | 写回 avatar.toml（含 watch_patterns/agent.args） |
| `scan_todos()` | 原生 Python 扫描 TODO/FIXME/BUG/HACK，按 watch_patterns 过滤 |
| `run_tests()` | 跑测试（python3→sys.executable，30s 超时） |
| `decide_priority()` | 优先级决策：测试失败 > TODO > git 变更 > 推进目标 |
| `generate_prompt()` | 动态 prompt 合成 |
| `delegate_to_agent()` | 调 AI agent（占位符替换，list 传参） |
| `_generate_next_goal()` | 扫描剩余 TODO → 定制下一轮 goal |
| `complete_goal()` | 目标完成迁移 + 新目标 + 新提示词模板 |
| `run_one_cycle()` | 主循环 |
| `main()` | 入口 |

> 说明：`evolution/autopilot_runner.py`（自演化守护脚本）是另一套独立机制，
> 通过 `atomcode -p` 拉起完整自主维护循环；avatar.py 是配置驱动的目标管理闭环。
> 两者可并行使用：runner 负责周期触发，avatar 负责目标生命周期与提示词定制。
