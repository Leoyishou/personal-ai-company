#!/bin/bash
# 滴答清单发送评论脚本
# 用法: dida_comment.sh <projectId> <taskId> <comment>

set -e

source ~/.claude/secrets.env

PROJECT_ID="$1"
TASK_ID="$2"
COMMENT="$3"

if [ -z "$PROJECT_ID" ] || [ -z "$TASK_ID" ] || [ -z "$COMMENT" ]; then
    echo "Usage: dida_comment.sh <projectId> <taskId> <comment>"
    echo "Example: dida_comment.sh inbox1019250222 68b430916f4fd1073a617b44 'Hello from AI'"
    exit 1
fi

if [ -z "$DIDA365_COOKIE_TOKEN" ]; then
    echo "Error: DIDA365_COOKIE_TOKEN not set in ~/.claude/secrets.env"
    exit 1
fi

# 生成 24 位十六进制 ID（类似 MongoDB ObjectId）
COMMENT_ID=$(openssl rand -hex 12)
# 当前时间 ISO 格式
CREATED_TIME=$(date -u +"%Y-%m-%dT%H:%M:%S.000+0000")

# 发送评论
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "https://api.dida365.com/api/v2/project/${PROJECT_ID}/task/${TASK_ID}/comment" \
  -H "Content-Type: application/json;charset=UTF-8" \
  -H "Cookie: t=${DIDA365_COOKIE_TOKEN}" \
  -d "{
    \"title\": \"${COMMENT}\",
    \"id\": \"${COMMENT_ID}\",
    \"createdTime\": \"${CREATED_TIME}\",
    \"taskId\": \"${TASK_ID}\",
    \"projectId\": \"${PROJECT_ID}\",
    \"userProfile\": {\"isMyself\": true},
    \"isNew\": true
  }")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo "Comment sent successfully!"
    echo "  Comment ID: $COMMENT_ID"
    echo "  Project: $PROJECT_ID"
    echo "  Task: $TASK_ID"
    echo "  Content: $COMMENT"
else
    echo "Failed to send comment. HTTP $HTTP_CODE"
    echo "$BODY"
    exit 1
fi
