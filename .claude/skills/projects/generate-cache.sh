#!/bin/bash
# 项目概览缓存生成脚本
# 每晚 23:50 由 crontab 触发

PROJ_ROOT="/Users/liuyishou/usr/projects"
CACHE_FILE="/Users/liuyishou/.claude/skills/projects/cache.json"
METADATA_FILE="/Users/liuyishou/.claude/skills/projects/metadata.json"

# 读取 metadata
if [ -f "$METADATA_FILE" ]; then
  METADATA=$(cat "$METADATA_FILE")
else
  METADATA="{}"
fi

# 生成缓存
{
  echo "{"
  echo "  \"generated_at\": \"$(date '+%Y-%m-%d %H:%M:%S')\","

  # 最近 3 天活跃项目
  echo "  \"recent_active\": ["
  first=true
  for proj in $(find "$PROJ_ROOT" -maxdepth 2 -mindepth 2 -type d 2>/dev/null); do
    if [ -d "$proj/.git" ]; then
      last_commit=$(git -C "$proj" log -1 --format="%ci" 2>/dev/null)
      if [ -n "$last_commit" ]; then
        commit_ts=$(date -j -f "%Y-%m-%d %H:%M:%S %z" "$last_commit" +%s 2>/dev/null)
        three_days_ago=$(date -v-3d +%s)
        if [ "$commit_ts" -gt "$three_days_ago" ] 2>/dev/null; then
          proj_name=$(basename "$proj")
          dir_name=$(basename $(dirname "$proj"))
          last_msg=$(git -C "$proj" log -1 --format="%s" 2>/dev/null | head -c 50 | sed 's/"/\\"/g')
          relative_time=$(git -C "$proj" log -1 --format="%ar" 2>/dev/null)

          if [ "$first" = true ]; then
            first=false
          else
            echo ","
          fi
          echo -n "    {\"name\": \"$proj_name\", \"dir\": \"$dir_name\", \"msg\": \"$last_msg\", \"time\": \"$relative_time\"}"
        fi
      fi
    fi
  done
  echo ""
  echo "  ],"

  # 各目录项目列表
  echo "  \"directories\": {"
  for dir in wip polish inbox published archive; do
    echo "    \"$dir\": ["
    first=true
    for proj in $(ls -t "$PROJ_ROOT/$dir" 2>/dev/null | grep -v "\.zip$\|\.md$\|\.html$\|\.DS_Store" | head -10); do
      if [ "$first" = true ]; then
        first=false
      else
        echo ","
      fi
      echo -n "      \"$proj\""
    done
    echo ""
    if [ "$dir" = "archive" ]; then
      echo "    ]"
    else
      echo "    ],"
    fi
  done
  echo "  },"

  # 统计
  echo "  \"stats\": {"
  for dir in wip polish inbox published archive; do
    count=$(ls "$PROJ_ROOT/$dir" 2>/dev/null | grep -v "\.zip$\|\.md$\|\.html$\|\.DS_Store" | wc -l | tr -d ' ')
    if [ "$dir" = "archive" ]; then
      echo "    \"$dir\": $count"
    else
      echo "    \"$dir\": $count,"
    fi
  done
  echo "  }"

  echo "}"
} > "$CACHE_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cache generated: $CACHE_FILE"
