# /projects - 项目概览

查看项目状态，追踪最近的 coding 活动。

## 执行步骤

### 1. 先扫描最近 3 天活跃的项目

```bash
PROJ_ROOT="/Users/liuyishou/usr/projects"
for proj in $(find "$PROJ_ROOT" -maxdepth 2 -mindepth 2 -type d 2>/dev/null); do
  if [ -d "$proj/.git" ]; then
    last_commit=$(git -C "$proj" log -1 --format="%ci" 2>/dev/null)
    if [ -n "$last_commit" ]; then
      commit_ts=$(date -j -f "%Y-%m-%d %H:%M:%S %z" "$last_commit" +%s 2>/dev/null)
      three_days_ago=$(date -v-3d +%s)
      if [ "$commit_ts" -gt "$three_days_ago" ] 2>/dev/null; then
        proj_name=$(basename "$proj")
        dir_name=$(basename $(dirname "$proj"))
        last_msg=$(git -C "$proj" log -1 --format="%s" 2>/dev/null | head -c 50)
        relative_time=$(git -C "$proj" log -1 --format="%ar" 2>/dev/null)
        echo "$last_commit|$dir_name|$proj_name|$last_msg|$relative_time"
      fi
    fi
  fi
done | sort -r
```

### 2. 扫描各目录项目列表

```bash
PROJ_ROOT="/Users/liuyishou/usr/projects"
for dir in wip polish inbox published archive; do
  count=$(ls "$PROJ_ROOT/$dir" 2>/dev/null | grep -v "\.zip$\|\.md$\|\.html$\|\.DS_Store" | wc -l | tr -d ' ')
  echo "=== $dir ($count) ==="
  ls -t "$PROJ_ROOT/$dir" 2>/dev/null | grep -v "\.zip$\|\.md$\|\.html$\|\.DS_Store" | head -5
done
```

### 3. 读取项目描述

```bash
cat ~/.claude/skills/projects/metadata.json | jq -r 'to_entries[] | "\(.key)|\(.value.desc // "")"' 2>/dev/null
```

## 输出格式

先展示最近 3 天活跃，再展示概览：

```
## 最近 3 天活跃

| 项目 | 目录 | 最近动态 | 时间 |
|------|------|---------|------|
| VoiceType | wip | Initial commit: macOS 语音转文本 | 1 天前 |
| personal-ai-company | published | 优化 readme | 2 天前 |

---

## 项目概览

### wip（活跃开发）
| 项目 | 描述 |
|------|------|
| VoiceType | macOS 语音转文本应用 |

### polish（打磨中）
...

### inbox（36 个，显示最近 5 个）
...

### published（已发布）
...

---

## 可用操作
- 「<项目名>」→ 查看详情
- 「mv <项目> wip」→ 移动到活跃开发
- 「health」→ 检查未提交代码
- 「cleanup」→ inbox 清理建议
- 「weekly」→ 本周 commit 周报
```

## 目录说明

| 目录 | 含义 |
|------|------|
| `inbox/` | 收集箱（新项目入口） |
| `wip/` | 活跃开发 |
| `polish/` | 打磨中 |
| `published/` | 已发布 |
| `archive/` | 搁置 |
