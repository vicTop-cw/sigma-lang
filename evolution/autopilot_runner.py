#!/usr/bin/env python3
"""
autopilot_runner.py — ΣLang 自演化守护脚本 (evolution/).

周期性拉起一轮 AtomCode headless 任务，按 sigma-autopilot skill 推进项目：
  1. 检查锁文件：上次任务是否还在跑（PID 存活检查）→ 默认拒绝重入，可 --kill 强杀。
  2. 用 `atomcode -p "<autopilot prompt>" -C <repo>` 启动一轮自主维护。
  3. --interval N：每 N 秒跑一轮（默认单轮）。
  4. 每轮写日志 evolution/autopilot.log；锁文件 evolution/.autopilot.lock。

用法:
  python3 evolution/autopilot_runner.py --once            # 跑一轮（外部 cron/任务计划器用）
  python3 evolution/autopilot_runner.py --interval 3600   # 每 1 小时一轮（守护循环）
  python3 evolution/autopilot_runner.py --kill            # 强杀上次还在跑的进程
  python3 evolution/autopilot_runner.py --status          # 显示锁/上次运行状态

退出码: 0 = 正常（本轮完成或成功 kill）；1 = 重入拒绝/错误；2 = 已 kill。
"""

import argparse
import datetime
import json
import os
import signal
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 仓库根
LOCK = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".autopilot.lock")
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "autopilot.log")

# 默认启动命令：AtomCode headless 模式。可用环境变量覆盖（如指向别处/加 --model）。
ATOMCODE = os.environ.get("ATOMCODE_BIN", "atomcode")
PROMPT = (
    "你是 ΣLang 自主维护代理。先读 AUTOPILOT.md 与 .atomcode/skills/sigma-autopilot/SKILL.md，"
    "按其中流程执行一轮完整自主维护循环（SCAN→DECIDE→EXECUTE→VERIFY→COMMIT→REPORT），"
    "推进项目到 v0.11 可用（包管理器 tools/sigma-cli.py + 标准库 3 包，见 AUTOPILOT.md §6）。项目内（仓库根目录之内）任何文件可读写创建删除，项目外任何路径"
    "只读；高度自主，不要弹出任何询问，直接执行最合理的动作并交付结果。完成后按格式输出结果报告。"
)


def log(msg):
    line = f"[{datetime.datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def pid_alive(pid):
    """跨平台 PID 存活检查。"""
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            p = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True,
            )
            # 中文 Windows 下输出为 GBK（"没有运行的任务匹配指定标准"）。
            # tasklist 对不存在的 PID 也返回 0，故用"输出是否含该 PID 数字"判据，
            # 与编码无关、与退出码无关。
            out = p.stdout.decode("gbk", errors="replace")
            return str(pid) in out
        except OSError:
            return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def read_lock():
    try:
        with open(LOCK, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def write_lock(pid):
    with open(LOCK, "w", encoding="utf-8") as f:
        json.dump({"pid": pid, "started": datetime.datetime.now().isoformat()}, f)


def clear_lock():
    try:
        os.remove(LOCK)
    except OSError:
        pass


def kill_previous():
    """杀上次还在跑的进程（锁文件中的 PID）。返回 True 表示确实杀掉了。"""
    lock = read_lock()
    if not lock:
        log("没有锁文件，无上次进程可杀。")
        return False
    pid = lock.get("pid", 0)
    if not pid_alive(pid):
        log(f"锁中的 PID {pid} 已不在运行（上次已完成/已退出），仅清理锁文件。")
        clear_lock()
        return False
    log(f"发现上次任务仍存活 (PID {pid})，执行强杀…")
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                           capture_output=True, text=True)
        else:
            os.kill(pid, signal.SIGKILL)
    except OSError as e:
        log(f"杀进程失败: {e}")
        return False
    time.sleep(1)
    clear_lock()
    log(f"已杀 PID {pid} 并清理锁文件。")
    return True


def run_once():
    """跑一轮自主维护。返回子进程退出码。"""
    if os.path.exists(LOCK):
        lock = read_lock()
        pid = (lock or {}).get("pid", 0)
        if pid_alive(pid):
            log(f"❌ 重入拒绝：上次任务 (PID {pid}) 仍在运行。"
                f"用 --kill 强杀，或等它结束后再跑。")
            return 1
        log(f"上次锁已过期（PID {pid} 不存在），接管。")
    proc_pid = os.getpid()
    write_lock(proc_pid)
    log(f"启动自主维护轮次 (runner PID {proc_pid})…")
    cmd = [ATOMCODE, "-p", PROMPT, "-C", REPO]
    log(f"执行: {' '.join(cmd)}")
    try:
        rc = subprocess.call(cmd)
    except FileNotFoundError:
        log(f"❌ 找不到 {ATOMCODE}，请确认 atomcode 在 PATH（或用 ATOMCODE_BIN 指定）。")
        clear_lock()
        return 1
    log(f"本轮完成，退出码 {rc}")
    clear_lock()
    return rc


def main():
    ap = argparse.ArgumentParser(description="ΣLang 自演化守护脚本")
    ap.add_argument("--once", action="store_true", help="只跑一轮（供外部调度器调用）")
    ap.add_argument("--interval", type=int, default=900,
                    help="normal 模式：每 N 秒跑一轮（默认 900 = 15 分钟）")
    ap.add_argument("--max-wait", type=int, default=5,
                    help="normal 模式：重入时最多等待次数（默认 5）")
    ap.add_argument("--wait-interval", type=int, default=60,
                    help="normal 模式：每次等待秒数（默认 60）")
    ap.add_argument("--kill", action="store_true", help="强杀上次还在跑的进程")
    ap.add_argument("--status", action="store_true", help="显示锁/上次运行状态")
    args = ap.parse_args()

    if args.kill:
        return 2 if kill_previous() else 0
    if args.status:
        lock = read_lock()
        if not lock:
            print("状态: 无锁文件（上次任务未在跑或已结束）")
        else:
            alive = pid_alive(lock.get("pid", 0))
            print(f"状态: PID {lock.get('pid')} 启动于 {lock.get('started')} "
                  f"→ {'仍在运行' if alive else '已退出'}")
        return 0

    if args.once:
        return run_once()

    log(f"进入 normal 调度：每 {args.interval}s 跑一轮；"
        f"若上次仍在运行则等待（{args.wait_interval}s/次，最多 {args.max_wait} 次），"
        f"仍存活则强杀后接管（Ctrl+C 退出）。")
    try:
        while True:
            rc = run_once()
            if rc == 1:
                # 重入拒绝（上次还在跑）：按 max-wait 次等待，仍存活则强杀后接管。
                waited = 0
                while waited < args.max_wait:
                    log(f"上次任务仍在运行，等待 {args.wait_interval}s "
                        f"({waited + 1}/{args.max_wait})…")
                    time.sleep(args.wait_interval)
                    lock = read_lock()
                    pid = (lock or {}).get("pid", 0)
                    if not pid_alive(pid):
                        break  # 上次已结束，可接管
                    waited += 1
                lock = read_lock()
                if pid_alive((lock or {}).get("pid", 0)):
                    log(f"等待 {args.max_wait} 次后上次任务仍在运行，执行强杀。")
                    kill_previous()
                rc = run_once()  # 接管重跑
            log(f"轮次结束 (rc={rc})，休眠 {args.interval}s…")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        log("收到中断，退出守护循环。")
        return 0


if __name__ == "__main__":
    sys.exit(main())
