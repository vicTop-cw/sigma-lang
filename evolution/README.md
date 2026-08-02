# evolution/ — ΣLang 自演化推进子系统

自动拉起 **AtomCode headless 任务**，按 `sigma-autopilot` skill（`.atomcode/skills/`）
周期性推进项目到 v0.11 可用（包管理器 + 标准库）。核心文件：

| 文件 | 作用 |
|------|------|
| `autopilot_runner.py` | 守护脚本：锁文件防重入、PID 存活检查、`--kill` 强杀、`--interval` 循环 |
| `run_autopilot.sh` | bash 便捷包装（透传参数） |
| `.autopilot.lock` | 锁文件（运行时生成，含 PID 与启动时间，已 gitignore） |
| `autopilot.log` | 每轮运行日志（已 gitignore） |

## 原理

每轮执行：

```sh
atomcode -p "<自主维护提示词>" -C <仓库根目录>
```

- 提示词要求代理：先读 `AUTOPILOT.md` 与 `sigma-autopilot` skill，再按
  SCAN→DECIDE→EXECUTE→VERIFY→COMMIT→REPORT 跑完整维护循环，推进 v0.11。
- 通过 `-C` 把工作目录固定在仓库根，让 `.atomcode.md` 与 skill 自动生效。

## 用法

```sh
# 1) 跑一轮（适合：手动触发 / Windows 任务计划器 / cron）
python3 evolution/autopilot_runner.py --once

# 2) normal 调度：每 15 分钟自动跑一轮（默认参数，前台常驻）
python3 evolution/autopilot_runner.py

# 3) normal 调度：自定义间隔与等待策略（如每 30 分钟一轮，最多等 10 次）
python3 evolution/autopilot_runner.py --interval 1800 --max-wait 10 --wait-interval 60

# 4) 强杀上次还在跑的轮次（重入拒绝时用）
python3 evolution/autopilot_runner.py --kill

# 5) 查看上次运行状态
python3 evolution/autopilot_runner.py --status
```

normal 模式参数（均可调整）：

| 参数 | 默认 | 含义 |
|------|------|------|
| `--interval` | 900（15 分钟） | 每 N 秒跑一轮 |
| `--max-wait` | 5 | 上次仍在运行时，最多等待 N 次 |
| `--wait-interval` | 60 | 每次等待 N 秒后重新检查上次进程 |

normal 行为：每 `interval` 秒尝试一轮；若发现上次任务仍在运行，则每 `wait-interval` 秒
检查一次、最多 `max-wait` 次；等待后仍存活 → **强杀**并接管重跑；然后休眠 `interval`
继续下一轮（Ctrl+C 退出）。

bash 包装等价：

```sh
./evolution/run_autopilot.sh --once
./evolution/run_autopilot.sh                      # normal：默认 15 分钟一轮
./evolution/run_autopilot.sh --interval 1800 --max-wait 10
./evolution/run_autopilot.sh --kill
./evolution/run_autopilot.sh --status
```

## 关键行为

- **防重入**：启动前读锁文件；若上次 PID 仍存活 → 拒绝启动（退出码 1），提示 `--kill`。
- **锁过期自愈**：若锁中 PID 已不存在（上次正常结束/崩溃）→ 自动接管，无需手动清锁。
- **kill**：`--kill` 用 `taskkill /F`（Windows）或 `SIGKILL`（POSIX）强杀上次进程，然后清锁。
- **间隔**：`--interval N` 进入守护循环；每轮结束后 sleep N 秒再跑下一轮。
- **日志**：所有轮次写入 `evolution/autopilot.log`（追加）。

## 常见部署：Windows 任务计划器（定时自演化）

1. `Win+R` → `taskschd.msc` → 创建任务：
   - 触发器：按你的频率（如每天 / 每小时）
   - 操作：启动程序 → `python`，参数：
     `"E:\IDEProjects\Ai\sigma-lang\evolution\autopilot_runner.py" --once`
   - 起始于：`E:\IDEProjects\Ai\sigma-lang`
2. 若上次跑超时未结束，下次触发会被防重入拒绝（或先用 `--kill` 清理）。

## 自定义

- 提示词：改 `autopilot_runner.py` 顶部的 `PROMPT` 常量。
- atomcode 路径：设环境变量 `ATOMCODE_BIN`（默认 `atomcode`）。

> 注意：`.autopilot.lock` 与 `autopilot.log` 已在 `.gitignore` 中，不会污染仓库。
