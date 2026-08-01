#!/usr/bin/env bash
# run_autopilot.sh — ΣLang 自演化守护的便捷包装（evolution/）。
# 用法见 evolution/README.md；底层调用 autopilot_runner.py。

set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'EOF'
用法:
  ./evolution/run_autopilot.sh --once            # 跑一轮自主维护（供任务计划器调用）
  ./evolution/run_autopilot.sh --interval 3600   # 守护循环，每 3600 秒一轮
  ./evolution/run_autopilot.sh --kill            # 强杀上次还在跑的轮次
  ./evolution/run_autopilot.sh --status          # 查看上次运行状态
EOF
}

[[ $# -eq 0 ]] && { usage; exit 1; }

python3 "$HERE/autopilot_runner.py" "$@"
exit $?
