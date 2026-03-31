#!/bin/bash
# Stop Hook - 每轮对话结束时保存 session 状态
# 由 Claude Code 的 Stop hook 调用
# 数据通过 stdin 以 JSON 格式传入

# 读取 stdin 中的 JSON
INPUT=$(cat)

# 用 jq 解析 JSON
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // ""')
CWD=$(echo "$INPUT" | jq -r '.cwd // ""')

# 确保 sessions 目录存在
mkdir -p "$HOME/.claude/sessions"

# 状态文件路径
STATE_FILE="$HOME/.claude/sessions/${SESSION_ID}.json"

# 获取当前时间戳
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
NOW_EPOCH=$(date +%s)

# 如果状态文件已存在，读取已有信息
if [ -f "$STATE_FILE" ]; then
    LINEAR_ISSUE_ID=$(jq -r '.linear_issue_id // empty' "$STATE_FILE" 2>/dev/null)
    CREATED_AT=$(jq -r '.created_at // empty' "$STATE_FILE" 2>/dev/null)
    TURN_COUNT=$(jq -r '.turn_count // 0' "$STATE_FILE" 2>/dev/null)
    TURN_COUNT=$((TURN_COUNT + 1))
else
    LINEAR_ISSUE_ID=""
    CREATED_AT="$NOW"
    TURN_COUNT=1
fi

# 保存状态
cat > "$STATE_FILE" << EOF
{
  "session_id": "${SESSION_ID}",
  "transcript_path": "${TRANSCRIPT_PATH}",
  "cwd": "${CWD}",
  "created_at": "${CREATED_AT}",
  "last_active_at": "${NOW}",
  "last_active_epoch": ${NOW_EPOCH},
  "turn_count": ${TURN_COUNT},
  "linear_issue_id": "${LINEAR_ISSUE_ID}",
  "status": "active",
  "finalized": false
}
EOF

# 静默退出，不输出任何内容到 stdout
exit 0
