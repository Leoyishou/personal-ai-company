#!/bin/bash
# ~/.claude/services/personal-assistant/run_dashboard.sh
# CEO 助理 Web Dashboard (Flask + SocketIO, port 5050)

# 日志时间戳
echo "=== $(date '+%Y-%m-%d %H:%M:%S') Dashboard 启动 ==="

# 运行 Flask Dashboard（flask 装在 /usr/local/bin/python3）
cd ~/.claude/agents/ceo-assistant/scripts
exec /usr/local/bin/python3 dashboard.py
