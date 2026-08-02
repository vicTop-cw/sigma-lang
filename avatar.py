#!/usr/bin/env python3
"""
AVATAR — Autonomous Verification And Task Assignment for Repos

Usage:
  avatar --once          Run one cycle and exit
  avatar                 Run continuously (interval from avatar.toml)
  avatar --interval 1800 Override interval in seconds
"""

import os, sys, re, json, time, shlex, subprocess, hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Python 3.6 compat ──
if sys.version_info < (3, 7):
    ModuleNotFoundError = ImportError

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        # Minimal TOML parser for Python 3.6+
        def _parse_toml(text):
            import ast
            result = {}
            current_section = result
            section_stack = []
            for line in text.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('['):
                    if line.startswith('[['):
                        section_name = line[2:-2].strip()
                        if '.' in section_name:
                            parts = section_name.split('.')
                            current = result
                            for p in parts[:-1]:
                                if p not in current:
                                    current[p] = {}
                                current = current[p]
                            last = parts[-1]
                            if last not in current:
                                current[last] = []
                            current[last].append({})
                            current_section = current[last][-1]
                        else:
                            if section_name not in result:
                                result[section_name] = []
                            result[section_name].append({})
                            current_section = result[section_name][-1]
                    else:
                        section_name = line[1:-1].strip()
                        parts = section_name.split('.')
                        current_section = result
                        for p in parts:
                            if p not in current_section:
                                current_section[p] = {}
                            current_section = current_section[p]
                elif '=' in line:
                    key, _, val = line.partition('=')
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    current_section[key] = val
            return result
        tomllib = type('toml', (), {'loads': staticmethod(_parse_toml)})


# ═══════════════════════════════════════════
# Config loading
# ═══════════════════════════════════════════

CONFIG_FILE = "avatar.toml"
LOG_DIR = "logs"  # 项目内日志目录（可用 [cycle].log_dir 覆盖）
HISTORY_DIR = "history"

def get_log_dir(project_root: str, config: dict) -> str:
    """日志目录：默认 <project>/logs；不要用 /tmp（Windows 下会解析成盘符根）。"""
    rel = (config.get('cycle') or {}).get('log_dir') or LOG_DIR
    return os.path.join(project_root, rel)

def load_config(project_root: str) -> dict:
    path = os.path.join(project_root, CONFIG_FILE)
    if not os.path.exists(path):
        sys.exit(f"ERROR: {path} not found. Create avatar.toml first.")
    with open(path, 'r', encoding='utf-8') as f:
        return tomllib.loads(f.read())

def save_config(project_root: str, config: dict):
    """Best-effort TOML save. Only writes known sections."""
    path = os.path.join(project_root, CONFIG_FILE)
    # Simple TOML writer for the sections we manage
    lines = []
    lines.append(f'# AVATAR config — auto-managed')
    lines.append('')
    lines.append('[project]')
    lines.append(f'name = "{config.get("project",{}).get("name","unknown")}"')
    lines.append(f'path = "{config.get("project",{}).get("path",".")}"')
    lines.append('')
    
    gc = config.get('goal', {}).get('current', {})
    lines.append('[goal.current]')
    lines.append(f'id = "{gc.get("id","")}"')
    lines.append(f'title = "{gc.get("title","")}"')
    lines.append(f'description = """')
    lines.append(gc.get('description', ''))
    lines.append('"""')
    lines.append(f'created_at = "{gc.get("created_at","")}"')
    lines.append('')
    
    d = config.get('detect', {})
    lines.append('[detect]')
    lines.append(f'scan_todos = {"true" if d.get("scan_todos") else "false"}')
    lines.append(f'scan_fixme = {"true" if d.get("scan_fixme") else "false"}')
    lines.append(f'run_tests = {"true" if d.get("run_tests") else "false"}')
    lines.append(f'test_command = "{d.get("test_command","")}"')
    wps = d.get('watch_patterns') or []
    lines.append('watch_patterns = ' + json.dumps(wps))
    lines.append('')
    
    a = config.get('agent', {})
    lines.append('[agent]')
    lines.append(f'command = "{a.get("command","")}"')
    lines.append(f'args = ' + json.dumps(a.get('args', ['-p', '{prompt}', '-C', '{project_path}'])))
    lines.append(f'timeout_seconds = {a.get("timeout_seconds",300)}')
    lines.append(f'max_delegated_per_cycle = {a.get("max_delegated_per_cycle",1)}')
    lines.append('')
    
    c = config.get('cycle', {})
    lines.append('[cycle]')
    lines.append(f'interval_seconds = {c.get("interval_seconds",900)}')
    lines.append(f'auto_commit = {"true" if c.get("auto_commit") else "false"}')
    lines.append(f'auto_push = {"true" if c.get("auto_push") else "false"}')
    lines.append('')
    
    for h in config.get('goal', {}).get('history', []):
        lines.append('[[goal.history]]')
        lines.append(f'id = "{h.get("id","")}"')
        lines.append(f'title = "{h.get("title","")}"')
        lines.append(f'completed_at = "{h.get("completed_at","")}"')
        lines.append(f'result = "{h.get("result","")}"')
        if h.get('description'):
            lines.append(f'description = """{h.get("description","")}"""')
        lines.append('')
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


# ═══════════════════════════════════════════
# SCAN phase
# ═══════════════════════════════════════════

def run_git_status(project_root: str) -> str:
    try:
        r = subprocess.run(['git', '-C', project_root, 'status', '--short'],
                          capture_output=True, text=True, timeout=15)
        return r.stdout.strip() or "(clean)"
    except Exception as e:
        return f"git status failed: {e}"

def run_git_pull(project_root: str) -> str:
    try:
        env = os.environ.copy()
        env['GIT_TERMINAL_PROMPT'] = '0'
        r = subprocess.run(['git', '-C', project_root, 'fetch', '--no-tags', 'origin', 'main'],
                          capture_output=True, text=True, timeout=5, env=env)
        return r.stdout.strip()[-200:] or r.stderr.strip()[-200:]
    except subprocess.TimeoutExpired:
        return "git fetch: timeout (network down?)"
    except Exception as e:
        return f"git fetch failed: {e}"

def scan_todos(project_root: str, patterns: list) -> list:
    """扫描 watch_patterns 覆盖文件中的 TODO/FIXME/BUG/HACK。
    原生 Python 实现（不依赖 grep，跨平台无子进程卡死），跳过构建/缓存/隐藏目录。
    """
    import fnmatch
    skip_dirs = {'.git', '.hg', '.svn', 'target', 'node_modules', '__pycache__',
                 '_build', 'deps', '.idea', '.vscode', '.moon', 'logs', 'history', 'archive'}
    text_exts = {'.py', '.md', '.toml', '.txt', '.rs', '.lz', '.exs', '.ex', '.mbt', '.json'}
    todo_re = re.compile(r'TODO|FIXME|BUG|HACK')
    results = []

    def matches(rel: str) -> bool:
        if not patterns:
            return True
        for p in patterns:
            p = p.strip().rstrip('/')
            if not p:
                continue
            if rel.startswith(p + '/') or fnmatch.fnmatch(rel, p) \
               or fnmatch.fnmatch(os.path.basename(rel), p):
                return True
        return False

    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [d for d in dirnames
                       if d not in skip_dirs and not d.startswith('.')]
        for fname in filenames:
            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, project_root).replace('\\', '/')
            if not matches(rel):
                continue
            if os.path.splitext(fname)[1].lower() not in text_exts:
                continue
            try:
                if os.path.getsize(full) > 256 * 1024:
                    continue
                with open(full, 'r', encoding='utf-8', errors='replace') as f:
                    for lineno, line in enumerate(f, 1):
                        if todo_re.search(line):
                            results.append(f"{rel}:{lineno}: {line.strip()[:120]}")
                            if len(results) >= 30:
                                return results
            except OSError:
                continue
    return results

def run_tests(project_root: str, test_cmd: str) -> dict:
    parts = shlex.split(test_cmd)
    # Windows 上 python3 可能不存在 → 用当前解释器
    if parts and parts[0] in ('python3', 'python'):
        parts[0] = sys.executable
    try:
        r = subprocess.run(
            parts,
            capture_output=True, text=True, timeout=30, cwd=project_root
        )
        return {
            'returncode': r.returncode,
            'output': r.stdout.strip()[-500:] + '\n' + r.stderr.strip()[-200:],
            'passed': r.returncode == 0
        }
    except Exception as e:
        return {'returncode': -1, 'output': str(e), 'passed': False}


# ═══════════════════════════════════════════
# DECIDE + GENERATE phase
# ═══════════════════════════════════════════

def decide_priority(goal_description: str, test_result: dict, todos: list, git_changes: str) -> dict:
    """Pick the most urgent task."""
    if not test_result['passed']:
        return {'action': 'fix_tests', 'context': test_result['output'][:500]}
    if todos:
        return {'action': 'resolve_todos', 'context': '\n'.join(todos[:5])}
    if git_changes and git_changes != '(clean)':
        return {'action': 'review_changes', 'context': git_changes}
    return {'action': 'advance_goal', 'context': goal_description[:500]}

def generate_prompt(config: dict, priority: dict, goal_desc: str, todos: list, test_result: dict, git_status: str) -> str:
    """Build the prompt dynamically."""
    goal = config.get('goal', {}).get('current', {})
    goal_id = goal.get('id', 'unknown')
    goal_title = goal.get('title', 'No goal')
    
    prompt = f"""你是 AVATAR 维护 Agent。当前目标: [{goal_id}] {goal_title}

【目标描述】
{goal_desc[:800]}

【项目状态】
- git status: {git_status[:300]}
- 测试: {'✅ 全部通过' if test_result['passed'] else '❌ 有失败'}
- TODO 列表:
{chr(10).join(todos[:8]) if todos else '(无)'}

【本轮任务 ({priority['action']})】
{priority['context'][:500]}

【工作步骤】
1. 只做一件事: {priority['action']}
2. 改代码 + 跑测试验证
3. 测试通过后再 commit
4. commit message 格式: "avatar: <简短描述>"

不要添加新功能，不要重构，只解决本轮任务。"""
    return prompt


# ═══════════════════════════════════════════
# DELEGATE phase  
# ═══════════════════════════════════════════

def delegate_to_agent(config: dict, prompt: str, cycle_log_file: str, project_root: str) -> dict:
    """Call the configured AI agent with the prompt."""
    agent_cfg = config.get('agent', {})
    cmd = agent_cfg.get('command', 'atomcode')
    timeout = int(agent_cfg.get('timeout_seconds', 600))
    
    # Build args, substituting placeholders (list form — no shell quoting needed)
    raw_args = agent_cfg.get('args', ['-p', '{prompt}', '-C', '{project_path}'])
    substituted = []
    for a in raw_args:
        a = a.replace('{prompt}', prompt)
        a = a.replace('{project_path}', project_root)
        substituted.append(a)
    
    full_cmd = [cmd] + substituted
    
    with open(cycle_log_file, 'a', encoding='utf-8') as log:
        log.write(f"\n{'='*60}\n")
        log.write(f"DELEGATE: {' '.join(full_cmd)[:200]}\n")
        log.write(f"{'='*60}\n")
    
    try:
        r = subprocess.run(full_cmd, capture_output=True, text=True, 
                          timeout=timeout, cwd=project_root)
        return {
            'success': r.returncode == 0,
            'stdout': r.stdout[-1000:],
            'stderr': r.stderr[-500:],
            'returncode': r.returncode
        }
    except subprocess.TimeoutExpired:
        return {'success': False, 'stdout': '', 'stderr': 'TIMEOUT', 'returncode': -1}
    except Exception as e:
        return {'success': False, 'stdout': '', 'stderr': str(e), 'returncode': -1}


# ═══════════════════════════════════════════
# VERIFY + COMMIT phase
# ═══════════════════════════════════════════

def git_commit_and_push(project_root: str, message: str, auto_push: bool) -> dict:
    try:
        subprocess.run(['git', '-C', project_root, 'add', '-A'],
                      capture_output=True, timeout=10)
        r = subprocess.run(['git', '-C', project_root, 'commit', '-m', message],
                          capture_output=True, text=True, timeout=10)
        if auto_push:
            subprocess.run(['git', '-C', project_root, 'push', 'origin', 'main'],
                          capture_output=True, timeout=30)
        return {'committed': True, 'message': r.stdout.strip()[-200:]}
    except Exception as e:
        return {'committed': False, 'message': str(e)}


# ═══════════════════════════════════════════
# GOAL COMPLETION
# ═══════════════════════════════════════════

def check_goal_complete(test_result: dict, todos: list) -> bool:
    return test_result['passed'] and len(todos) == 0

def _generate_next_goal(project_root: str, config: dict) -> dict:
    """扫描剩余 TODO/FIXME，自主定制下一轮目标（title + description）。"""
    detect = config.get('detect', {})
    patterns = detect.get('watch_patterns') or ['spec*.md', 'verify*.py', 'impl/', 'tools/']
    todos = scan_todos(project_root, patterns)
    now = datetime.now(timezone.utc)
    new_id = now.strftime('%Y%m%d-%H%M%S') + '-next'
    if todos:
        # 按文件分组，取 TODO 最集中的文件作为下一轮主战场
        from collections import Counter
        files = Counter(t.split(':', 1)[0] for t in todos)
        top_file, top_count = files.most_common(1)[0]
        top_lines = [t.split(':', 2)[-1].strip()[:80]
                     for t in todos if t.startswith(top_file + ':')][:5]
        title = f"解决 {top_file} 的遗留 TODO（{top_count} 处）"
        desc_lines = [f"聚焦 {top_file}，解决剩余 {top_count} 处 TODO/FIXME："]
        desc_lines += [f"- {ln}" for ln in top_lines]
        desc_lines.append("每修一处跑一遍验证器（verify_p0.py / verify_consensus.py）确保全绿。")
        description = '\n'.join(desc_lines)
    else:
        title = "推进项目里程碑（无遗留 TODO）"
        description = ("当前无 TODO/FIXME 遗留。检查 README / MASTER_PLAN / spec 中标注的"
                       "未完成项（如 v0.10 数学符号、包管理器、标准库），推进到 v0.10 可用。")
    return {'id': new_id, 'title': title, 'description': description,
            'created_at': now.isoformat()}

def complete_goal(project_root: str, config: dict, cycle_number: int, cycle_log: str,
                  last_prompt: str = ''):
    """Move current goal to history, generate new goal + its prompt template."""
    goal = config.setdefault('goal', {}).setdefault('current', {})
    goal_id = goal.get('id', 'unknown')
    
    # Save snapshot to history
    history_dir = os.path.join(project_root, HISTORY_DIR, goal_id)
    os.makedirs(history_dir, exist_ok=True)
    
    # Copy current config as snapshot
    import shutil
    shutil.copy(os.path.join(project_root, CONFIG_FILE),
                os.path.join(history_dir, 'goal_snapshot.toml'))
    
    # Save final prompt template (last used prompt, reproducible)
    prompt_path = os.path.join(history_dir, 'prompt_template.txt')
    with open(prompt_path, 'w', encoding='utf-8') as f:
        f.write(f"Goal: {goal.get('title', '')}\n")
        f.write(f"Description: {goal.get('description', '')}\n")
        f.write(f"Cycles: {cycle_number}\n")
        f.write(f"Completed: {datetime.now(timezone.utc).isoformat()}\n")
        if last_prompt:
            f.write(f"\n── 最后使用的提示词 ──\n{last_prompt}\n")
    
    # Generate new goal from remaining TODOs
    new_goal = _generate_next_goal(project_root, config)
    new_id = new_goal['id']
    
    # Write final summary
    summary_path = os.path.join(get_log_dir(project_root, config), goal_id, 'final_summary.md')
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(f"# Goal Complete: {goal.get('title', '')}\n\n")
        f.write(f"Cycles: {cycle_number}\n")
        f.write(f"Completed: {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"Next goal: [{new_id}] {new_goal['title']}\n")
    
    # Move to history
    config.setdefault('goal', {}).setdefault('history', []).append({
        'id': goal_id,
        'title': goal.get('title', ''),
        'completed_at': datetime.now(timezone.utc).isoformat(),
        'result': 'success'
    })
    
    # 切换到新目标后，再为新目标生成首轮提示词模板（标题/描述取自新目标）
    config['goal']['current'] = new_goal
    next_log_dir = os.path.join(get_log_dir(project_root, config), new_id)
    os.makedirs(next_log_dir, exist_ok=True)
    next_prompt = generate_prompt(config, {'action': 'advance_goal',
                                           'context': new_goal['description']},
                                  new_goal['description'], [],
                                  {'passed': True}, '(clean)')
    with open(os.path.join(next_log_dir, 'next_goal_prompt.txt'), 'w', encoding='utf-8') as f:
        f.write(f"# Next Goal: {new_goal['title']}\n\n")
        f.write(f"## 描述\n{new_goal['description']}\n\n")
        f.write(f"## 首轮提示词模板\n{next_prompt}\n")
    
    save_config(project_root, config)
    
    with open(cycle_log, 'a', encoding='utf-8') as f:
        f.write(f"\n🎯 GOAL COMPLETE after {cycle_number} cycles\n")
        f.write(f"   Snapshot → {history_dir}\n")
        f.write(f"   Next goal → [{new_id}] {new_goal['title']}\n")
        f.write(f"   Next prompt → {next_log_dir}/next_goal_prompt.txt\n")


# ═══════════════════════════════════════════
# Main cycle
# ═══════════════════════════════════════════

def run_one_cycle(project_root: str, dry_run: bool = False) -> Optional[str]:
    """Run a single cycle. Returns the cycle log path."""
    config = load_config(project_root)
    goal = config.get('goal', {}).get('current', {})
    goal_id = goal.get('id', 'unknown')
    detect = config.get('detect', {})
    cycle_cfg = config.get('cycle', {})
    
    
    # Setup log dir
    log_dir = os.path.join(get_log_dir(project_root, config), goal_id)
    os.makedirs(log_dir, exist_ok=True)
    
    # Find next cycle number
    existing = [f for f in os.listdir(log_dir) if f.startswith('cycle_')]
    cycle_num = len(existing) + 1
    log_file = os.path.join(log_dir, f'cycle_{cycle_num:02d}.log')
    
    
    with open(log_file, 'w', encoding='utf-8') as log:
        log.write(f"Cycle {cycle_num} | {datetime.now(timezone.utc).isoformat()}\n")
        log.write(f"Goal: {goal_id}\n\n")
    
    
    # ── SCAN ──
    with open(log_file, 'a', encoding='utf-8') as log:
        log.write("── SCAN ──\n")
    
    try:
        pull_output = run_git_pull(project_root)
        git_status = run_git_status(project_root)
        test_result = run_tests(project_root, detect.get('test_command', 'echo no tests'))
        todos = scan_todos(project_root, detect.get('watch_patterns', ['.']))
    except Exception as e:
        with open(log_file, 'a', encoding='utf-8') as log:
            log.write(f"SCAN ERROR: {e}\n")
        return log_file
    
    with open(log_file, 'a', encoding='utf-8') as log:
        log.write(f"git pull: {pull_output[:200]}\n")
        log.write(f"git status: {git_status}\n")
        log.write(f"tests: {'PASS' if test_result['passed'] else 'FAIL'}\n")
        log.write(f"todos: {len(todos)} items\n\n")
    
    # ── CHECK GOAL COMPLETE ──
    if check_goal_complete(test_result, todos):
        with open(log_file, 'a', encoding='utf-8') as log:
            log.write("── GOAL COMPLETE ──\n")
        if dry_run:
            # dry-run 只读：不改 avatar.toml、不建 history/、不迁移目标
            with open(log_file, 'a', encoding='utf-8') as log:
                log.write("   (dry-run: 跳过 complete_goal，不落盘)\n\n")
        else:
            # 生成完成态提示词存档（goal 已达成时的收尾提示词）
            last_prompt = generate_prompt(
                config, {'action': 'goal_complete', 'context': goal.get('description', '')},
                goal.get('description', ''), todos, test_result, git_status)
            complete_goal(project_root, config, cycle_num, log_file, last_prompt)
        return log_file
    
    # ── DECIDE ──
    goal_desc = goal.get('description', '')
    priority = decide_priority(goal_desc, test_result, todos, git_status)
    
    with open(log_file, 'a', encoding='utf-8') as log:
        log.write(f"── DECIDE: {priority['action']} ──\n\n")
    
    # ── GENERATE ──
    prompt = generate_prompt(config, priority, goal_desc, todos, test_result, git_status)
    
    with open(log_file, 'a', encoding='utf-8') as log:
        log.write(f"── PROMPT ──\n{prompt[:1000]}\n...\n\n")
    
    # ── DELEGATE ──
    if dry_run:
        with open(log_file, 'a', encoding='utf-8') as log:
            log.write(f"── DELEGATE: SKIPPED (dry-run) ──\n")
            log.write(f"Prompt would be sent to: {config.get('agent',{}).get('command','atomcode')}\n\n")
        return log_file
    
    result = delegate_to_agent(config, prompt, log_file, project_root)
    
    with open(log_file, 'a', encoding='utf-8') as log:
        log.write(f"── RESULT: {'SUCCESS' if result['success'] else 'FAILED'}({result['returncode']}) ──\n")
        log.write(f"{result['stdout'][:500]}\n")
    
    # ── RE-VERIFY ──
    if result['success']:
        test_result2 = run_tests(project_root, detect.get('test_command', 'echo no tests'))
        with open(log_file, 'a', encoding='utf-8') as log:
            log.write(f"── RE-VERIFY: {'PASS' if test_result2['passed'] else 'FAIL'} ──\n")
        
        # ── COMMIT ──
        if cycle_cfg.get('auto_commit'):
            summary = f"avatar: [{goal_id[:12]}] c{cycle_num} {priority['action']}"
            commit_result = git_commit_and_push(
                project_root, summary, cycle_cfg.get('auto_push', False)
            )
            with open(log_file, 'a', encoding='utf-8') as log:
                log.write(f"── COMMIT: {commit_result['message'][:200]}\n")
    
    return log_file


# ═══════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description='AVATAR — Autonomous Verification And Task Assignment for Repos')
    parser.add_argument('--once', action='store_true', help='Run one cycle and exit')
    parser.add_argument('--interval', type=int, default=0, help='Override interval in seconds')
    parser.add_argument('--project', type=str, default='.', help='Project root')
    parser.add_argument('--dry-run', action='store_true', help='Scan + generate prompt, skip delegate')
    args = parser.parse_args()
    
    project_root = os.path.abspath(args.project)
    print(f"AVATAR v0.1 — {project_root}")
    print(f"Config: {os.path.join(project_root, CONFIG_FILE)}")
    
    if args.once or args.dry_run:
        log_file = run_one_cycle(project_root, dry_run=args.dry_run)
        print(f"✅ Cycle complete → {log_file}")
        return
    
    # Continuous mode
    config = load_config(project_root)
    interval = args.interval or int(config.get('cycle', {}).get('interval_seconds', 900))
    
    print(f"Continuous mode — interval {interval}s. Ctrl+C to stop.")
    while True:
        try:
            log_file = run_one_cycle(project_root)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Cycle done → {log_file}")
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\nAVATAR stopped.")
            break
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {e}")
            time.sleep(interval)


if __name__ == '__main__':
    main()
