#!/bin/bash
# ~/.claude/services/personal-assistant/run.sh

# 设置 fnm 环境
export FNM_DIR="$HOME/.local/share/fnm"
export PATH="$FNM_DIR/node-versions/v22.16.0/installation/bin:$PATH"

# 日志时间戳
echo "=== $(date '+%Y-%m-%d %H:%M:%S') 开始执行 ===" >> ~/.claude/services/personal-assistant/stdout.log

# 运行 Claude Code
cd ~/.claude/skills/personal-assistant
claude -p "/personal-assistant" --dangerously-skip-permissions 2>&1 | tee -a ~/.claude/services/personal-assistant/stdout.log

echo "=== $(date '+%Y-%m-%d %H:%M:%S') 执行完成 ===" >> ~/.claude/services/personal-assistant/stdout.log
