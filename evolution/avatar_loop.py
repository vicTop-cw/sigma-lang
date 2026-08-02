#!/usr/bin/env python3
"""
avatar_loop.py — ΣLang 统一自演化入口（单文件，复用 autopilot_runner + avatar）。

复用 autopilot_runner.py 的调度能力（锁/防重入/--interval/--kill/--status）
与 avatar.py 的目标生命周期能力（SCAN→DECIDE→GENERATE→DELEGATE→VERIFY→COMMIT→LOG），
并实现「两阶段完成 + 核验失败取消标记」：

  阶段1：目标达成（测试全过 + 无 TODO）→ 仅标注 completed_at + pending_verification=true，
         不迁移、不拟定新目标。
  阶段2：下一轮核验 —— git 变更中命中 watch_patterns（主项目源码）的文件：
         - 无改动 → 核验通过 → complete_goal()：归档 history/ + 拟定下一目标 + 首轮提示词
         - 有改动 → 核验未通过 → **取消完成标记**（移除 completed_at/pending_verification），
           日志说明未通过项，下一轮重新核验。

用法:
  python3 evolution/avatar_loop.py --dry-run                 # 只读试跑一轮
  python3 evolution/avatar_loop.py --once                    # 正式跑一轮（会调 atomcode 修复任务）
  python3 evolution/avatar_loop.py --interval 1800           # 每 30 分钟一轮（守护循环）
  python3 evolution/avatar_loop.py --kill                    # 强杀上次还在跑的进程
  python3 evolution/avatar_loop.py --status                  # 查看锁/运行状态

退出码: 0 = 正常；1 = 重入拒绝/错误；2 = 已 kill。
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)          # 仓库根
sys.path.insert(0, REPO)              # 让 avatar.py 可导入
sys.path.insert(0, HERE)              # 让 autopilot_runner.py 可导入

import avatar                        # 复用：目标生命周期（原文件不动）
import autopilot_runner as runner    # 复用：调度（锁/防重入/kill/log，原文件不动）

LOCK = os.path.join(HERE, ".avatar_loop.lock")
# 让 runner 的 read_lock/write_lock/clear_lock/kill_previous 操作本入口的锁
runner.LOCK = LOCK


# ═══════════════════════════════════════════
# 目标循环（复用 avatar 底层函数，核验失败行为在此定制）
# ═══════════════════════════════════════════

def run_cycle(project_root: str, dry_run: bool = False):
    """跑一轮：SCAN → 两阶段完成/核验 → DECIDE → GENERATE → DELEGATE → VERIFY → COMMIT → LOG。
    返回本轮日志路径。dry_run 时只读（不 delegate、不落盘）。"""
    config = avatar.load_config(project_root)
    goal = config.get('goal', {}).get('current', {})
    goal_id = goal.get('id', 'unknown')
    detect = config.get('detect', {})
    cycle_cfg = config.get('cycle', {})

    # ── 日志目录 ──
    log_dir = os.path.join(avatar.get_log_dir(project_root, config), goal_id)
    os.makedirs(log_dir, exist_ok=True)
    existing = [f for f in os.listdir(log_dir) if f.startswith('cycle_')]
    cycle_num = len(existing) + 1
    log_file = os.path.join(log_dir, f'cycle_{cycle_num:02d}.log')

    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"Cycle {cycle_num} | {datetime.datetime.now(datetime.timezone.utc).isoformat()}\n")
        f.write(f"Goal: {goal_id}\n\n")

    # ── SCAN ──
    runner.log(f"SCAN: 目标 [{goal_id}] cycle {cycle_num} — git fetch/status、测试、TODO 扫描…")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write("── SCAN ──\n")
    try:
        pull_output = avatar.run_git_pull(project_root)
        git_status = avatar.run_git_status(project_root)
        test_result = avatar.run_tests(project_root, detect.get('test_command', 'echo no tests'))
        todos = avatar.scan_todos(project_root, detect.get('watch_patterns', []))
    except Exception as e:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"SCAN ERROR: {e}\n")
        return log_file

    runner.log(f"SCAN 完成: 测试 {'✅' if test_result['passed'] else '❌'} | "
               f"TODO {len(todos)} 处 | git "
               f"{'有变更' if git_status and git_status != '(clean)' else '干净'}")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"git pull: {pull_output[:200]}\n")
        f.write(f"git status: {git_status}\n")
        f.write(f"tests: {'PASS' if test_result['passed'] else 'FAIL'}\n")
        f.write(f"todos: {len(todos)} items\n\n")

    # ── 两阶段完成 + 核验 ──
    if avatar.check_goal_complete(test_result, todos):
        runner.log("GOAL COMPLETE: 测试全过且无 TODO，进入两阶段完成/核验")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write("── GOAL COMPLETE ──\n")
        if dry_run:
            runner.log("GOAL COMPLETE (dry-run): 跳过完成流程，不落盘")
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write("   (dry-run: 跳过完成流程，不落盘)\n\n")
            return log_file

        pending = goal.get('pending_verification')
        if not pending:
            # 阶段1/2：本轮达成 → 仅标注完成，待下一轮核验
            goal['completed_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            goal['pending_verification'] = True
            avatar.save_config(project_root, config)
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write("   阶段1/2：目标达成，仅标注完成（pending_verification）。\n")
                f.write("   下一轮将核验主项目源码是否已无改动，通过后才拟定新目标。\n\n")
            runner.log(f"🎯 目标 [{goal_id}] 达成（阶段1/2 标注），待下一轮核验")
        else:
            # 阶段2/2：核验
            source_changes = avatar._source_changes_in_watch(
                git_status, detect.get('watch_patterns', []))
            if source_changes:
                # 核验未通过 → 取消完成标记（保留 pending，下一轮直接续核验）
                goal.pop('completed_at', None)
                avatar.save_config(project_root, config)
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write("   阶段2/2：核验未通过——已取消完成标记。\n")
                    f.write("   未通过项（主项目源码仍有改动）：\n")
                    for c in source_changes[:10]:
                        f.write(f"     - {c}\n")
                    f.write("   保持 pending，下一轮继续核验；修复并提交这些改动前，不拟定新目标。\n\n")
                runner.log(f"❌ 目标 [{goal_id}] 核验未通过，已取消完成标记。"
                           f"未通过项: {source_changes[:5]}")
            else:
                # 核验通过 → 真正完成：归档 + 拟定新目标 + 首轮提示词
                last_prompt = avatar.generate_prompt(
                    config, {'action': 'goal_complete',
                             'context': goal.get('description', '')},
                    goal.get('description', ''), todos, test_result, git_status)
                avatar.complete_goal(project_root, config, cycle_num, log_file, last_prompt)
                runner.log(f"✅ 目标 [{goal_id}] 核验通过，已拟定下一目标")
        return log_file

    # ── DECIDE ──
    goal_desc = goal.get('description', '')
    priority = avatar.decide_priority(goal_desc, test_result, todos, git_status)
    runner.log(f"DECIDE: {priority['action']}")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"── DECIDE: {priority['action']} ──\n\n")

    # ── GENERATE ──
    prompt = avatar.generate_prompt(config, priority, goal_desc, todos, test_result, git_status)
    runner.log("GENERATE: 提示词已合成（完整内容见本轮 cycle 日志）")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"── PROMPT ──\n{prompt[:1000]}\n...\n\n")

    # ── DELEGATE ──
    if dry_run:
        runner.log(f"DELEGATE: SKIPPED (dry-run) — 将调 "
                   f"{config.get('agent',{}).get('command','atomcode')}")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"── DELEGATE: SKIPPED (dry-run) ──\n")
            f.write(f"Prompt would be sent to: {config.get('agent',{}).get('command','atomcode')}\n\n")
        return log_file

    agent_cmd = config.get('agent', {}).get('command', 'atomcode')
    runner.log(f"DELEGATE: 调用 {agent_cmd} 修复任务（最长 "
               f"{config.get('agent',{}).get('timeout_seconds',600)}s）…")
    result = avatar.delegate_to_agent(config, prompt, log_file, project_root)
    runner.log(f"DELEGATE 完成: {'✅ SUCCESS' if result['success'] else '❌ FAILED'} "
               f"(rc={result['returncode']})")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"── RESULT: {'SUCCESS' if result['success'] else 'FAILED'}({result['returncode']}) ──\n")
        f.write(f"{result['stdout'][:500]}\n")

    # ── RE-VERIFY + COMMIT ──
    if result['success']:
        test_result2 = avatar.run_tests(project_root, detect.get('test_command', 'echo no tests'))
        runner.log(f"RE-VERIFY: {'✅ PASS' if test_result2['passed'] else '❌ FAIL'}")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"── RE-VERIFY: {'PASS' if test_result2['passed'] else 'FAIL'} ──\n")
        if cycle_cfg.get('auto_commit'):
            summary = f"avatar: [{goal_id[:12]}] c{cycle_num} {priority['action']}"
            commit_result = avatar.git_commit_and_push(
                project_root, summary, cycle_cfg.get('auto_push', False))
            runner.log(f"COMMIT: {summary} → "
                       f"{'✅ OK' if commit_result['committed'] else '⚠️ ' + commit_result['message'][:100]}")
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"── COMMIT: {commit_result['message'][:200]}\n")

    return log_file


# ═══════════════════════════════════════════
# 调度（复用 autopilot_runner 的锁/防重入/强杀）
# ═══════════════════════════════════════════

def run_once(project_root: str, dry_run: bool = False):
    """跑一轮。返回子进程退出码（此处为循环自身，直接返回 0/1）。"""
    if os.path.exists(LOCK):
        lock = runner.read_lock()
        pid = (lock or {}).get("pid", 0)
        if runner.pid_alive(pid):
            runner.log(f"❌ 重入拒绝：上次任务 (PID {pid}) 仍在运行。"
                       f"用 --kill 强杀，或等它结束后再跑。")
            return 1
        runner.log(f"上次锁已过期（PID {pid} 不存在），接管。")
    runner.write_lock(os.getpid())
    runner.log(f"启动 avatar_loop 轮次 (PID {os.getpid()})…")
    try:
        log_file = run_cycle(project_root, dry_run=dry_run)
        runner.log(f"本轮完成 → {log_file}")
        return 0
    except Exception as e:
        runner.log(f"❌ 本轮异常: {e}")
        return 1
    finally:
        runner.clear_lock()


def main():
    ap = argparse.ArgumentParser(description="ΣLang 统一自演化入口（runner 调度 + avatar 目标循环）")
    ap.add_argument("--once", action="store_true", help="只跑一轮（供外部调度器调用）")
    ap.add_argument("--dry-run", action="store_true", help="只读试跑：scan+prompt，不 delegate、不落盘")
    ap.add_argument("--project", type=str, default=REPO, help="项目根目录（默认仓库根）")
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
        return 2 if runner.kill_previous() else 0
    if args.status:
        lock = runner.read_lock()
        if not lock:
            print("状态: 无锁文件（上次任务未在跑或已结束）")
        else:
            alive = runner.pid_alive(lock.get("pid", 0))
            print(f"状态: PID {lock.get('pid')} 启动于 {lock.get('started')} "
                  f"→ {'仍在运行' if alive else '已退出'}")
        return 0

    project_root = os.path.abspath(args.project)
    if args.once or args.dry_run:
        return run_once(project_root, dry_run=args.dry_run)

    runner.log(f"进入 normal 调度：每 {args.interval}s 跑一轮；"
               f"若上次仍在运行则等待（{args.wait_interval}s/次，最多 {args.max_wait} 次），"
               f"仍存活则强杀后接管（Ctrl+C 退出）。")
    try:
        while True:
            rc = run_once(project_root)
            if rc == 1:
                waited = 0
                while waited < args.max_wait:
                    runner.log(f"上次任务仍在运行，等待 {args.wait_interval}s "
                               f"({waited + 1}/{args.max_wait})…")
                    time.sleep(args.wait_interval)
                    lock = runner.read_lock()
                    pid = (lock or {}).get("pid", 0)
                    if not runner.pid_alive(pid):
                        break
                    waited += 1
                lock = runner.read_lock()
                if runner.pid_alive((lock or {}).get("pid", 0)):
                    runner.log(f"等待 {args.max_wait} 次后上次任务仍在运行，执行强杀。")
                    runner.kill_previous()
                rc = run_once(project_root)
            runner.log(f"轮次结束 (rc={rc})，休眠 {args.interval}s…")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        runner.log("收到中断，退出守护循环。")
        return 0


if __name__ == "__main__":
    sys.exit(main())
