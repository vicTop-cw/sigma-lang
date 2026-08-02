# AVATAR — 当前进度与接手说明

> 写给 AtomCode：这是一个配置驱动的自动维护 Agent，放到任意 Git 项目即可自动发现 TODO/测试失败/git 变更，生成提示词并分派给 AI 专家修复。
> WSL 环境有文件 I/O 问题，请在 Windows 原生 Python 上继续调试。

---

## 一、已完成的文件

| 文件 | 行数 | 状态 |
|------|------|------|
| `avatar.toml` | 60 | ✅ 配置模板，已测试可解析 |
| `avatar.py` | ~500 | ⚠️ 核心逻辑写完，WSL 上 run_one_cycle 卡在 scan 阶段 |
| `evolution/AVATAR_DESIGN.md` | - | ✅ 设计文档 |

---

## 二、avatar.py 架构

```
main()
├── --once / --dry-run → run_one_cycle()
├── --interval N        → 循环调用 run_one_cycle()
│
run_one_cycle()
├── SCAN:   git fetch → git status → run tests → grep TODOs
├── DECIDE: 测试失败 > TODO 列表 > git 变更 > 推进目标
├── GENERATE: merge goal + scan results → 动态 prompt
├── DELEGATE: subprocess 调 AI agent (atomcode/reasonix)
├── VERIFY:  re-run tests
├── COMMIT:  git add -A && git commit && git push
├── LOG:     写入 logs/<goal_id>/cycle_NN.log
└── GOAL COMPLETE CHECK: 测试全过 + 无 TODO → 完成目标
```

---

## 三、待修复的问题

### 问题 1：`run_one_cycle()` 在 WSL 卡死

**现象：**
- `python3 avatar.py --dry-run` 超时（exit 124）
- 日志只写到 `── SCAN ──` 标题行，scan 结果未写入
- 4 个 scan 函数单独调用全部正常（已验证）

**已排查：**
- ✅ 日志目录改到 `/tmp/avatar_logs/`（避免 WSL /mnt/e/ 写卡）
- ✅ `run_git_pull` — 5s timeout + GIT_TERMINAL_PROMPT=0，单独测 OK
- ✅ `run_git_status` — 单独测 OK  
- ✅ `run_tests` — 10s timeout，单独测 OK
- ✅ `scan_todos` — `--include=*.py` 过滤，单独测 OK
- ✅ config 解析 — 单独测 OK

**推测：**
函数内部组合调用时发生某种 WSL 子进程阻塞（strace 显示最后是 grep 在运行）。在 Windows 原生 Python 上应该正常。

### 问题 2：dry-run 时 delegate 未验证

按设计 dry-run 跳过 delegate 阶段，但实际还没跑到 DECIDE 就卡了。

---

## 四、接入后的验证步骤

```bash
cd E:\IDEProjects\AI\sigma-lang

# 1. 确认配置可解析
python -c "import avatar; cfg=avatar.load_config('.'); print(cfg['project']['name'])"
# 预期: sigma-lang

# 2. 干跑一轮
python avatar.py --dry-run
# 预期: scan → generate prompt → 写日志到 logs/

# 3. 查看日志
type logs\20260802-baseline\cycle_01.log

# 4. 正式跑（会调 atomcode）
python avatar.py --once --project .
```

---

## 五、avatar.py 关键函数速查

| 函数 | 行号 | 用途 |
|------|------|------|
| `load_config()` | 80 | TOML 解析，Python 3.6 兼容 |
| `run_git_pull()` | 151 | git fetch，5s 超时 |
| `run_git_status()` | 163 | git status --short |
| `scan_todos()` | 166 | grep TODO/FIXME，3s 超时 |
| `run_tests()` | 179 | subprocess 跑测试，10s 超时 |
| `decide_priority()` | 198 | 优先级决策 |
| `generate_prompt()` | 208 | 动态 prompt 合成 |
| `delegate_to_agent()` | 228 | 调 AI agent |
| `complete_goal()` | 290 | 目标完成迁移 |
| `run_one_cycle()` | 358 | 主循环 |
| `main()` | 448 | 入口 |
