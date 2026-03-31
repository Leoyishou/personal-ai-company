#!/bin/bash
# Personal AI Agent - 统一调度器启动脚本

# 使用 anaconda Python (有 telethon)
PYTHON="/opt/anaconda3/bin/python3"

# 无缓冲输出，确保日志实时写入
export PYTHONUNBUFFERED=1

# 日志目录（使用 agents 目录）
LOG_DIR="$HOME/.claude/agents/ceo-assistant/logs"
mkdir -p "$LOG_DIR"

echo "=== $(date '+%Y-%m-%d %H:%M:%S') 启动统一调度器 ===" >> "$LOG_DIR/scheduler.log"

# 运行调度器（使用 agents 目录下的脚本）
cd ~/.claude/agents/ceo-assistant
$PYTHON scripts/scheduler.py 2>&1 | tee -a "$LOG_DIR/scheduler.log"
