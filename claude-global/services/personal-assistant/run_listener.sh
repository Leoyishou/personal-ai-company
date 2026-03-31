#!/bin/bash
# Telegram 监听器启动脚本

# 使用 anaconda Python (有 telethon)
PYTHON="/opt/anaconda3/bin/python3"

# 日志
LOG_DIR="$HOME/.claude/skills/personal-assistant/logs"
mkdir -p "$LOG_DIR"

echo "=== $(date '+%Y-%m-%d %H:%M:%S') 启动 Telegram 监听器 ===" >> "$LOG_DIR/telegram_listener.log"

# 运行监听器
cd ~/.claude/skills/personal-assistant
$PYTHON scripts/telegram_listener.py 2>&1 | tee -a "$LOG_DIR/telegram_listener.log"
