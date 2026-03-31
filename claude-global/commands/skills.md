# /skills - 技能列表

列出所有可用技能，包含描述和调用统计。

## 执行步骤

### 1. 收集所有 SKILL.md 信息

```bash
SKILLS_DIR="$HOME/.claude/skills"
STATS_FILE="$HOME/.claude/skills/stats.json"

# 初始化统计文件（如不存在）
[ ! -f "$STATS_FILE" ] && echo '{}' > "$STATS_FILE"

# 遍历所有 SKILL.md，提取 name 和 description
for skill_file in "$SKILLS_DIR"/*/SKILL.md; do
  if [ -f "$skill_file" ]; then
    skill_dir=$(dirname "$skill_file")
    skill_name=$(basename "$skill_dir")

    # 提取 description（处理 Windows/Unix 换行符）
    desc=$(tr -d '\r' < "$skill_file" | awk '/^---$/{p=!p; next} p && /^description:/' | sed 's/^description: *//' | sed 's/^"//' | sed 's/"$//' | cut -c1-45)

    # 获取调用次数
    count=$(jq -r --arg name "$skill_name" '.[$name] // 0' "$STATS_FILE" 2>/dev/null || echo "0")

    printf "%d|%s|%s\n" "$count" "$skill_name" "$desc"
  fi
done | LC_ALL=C sort -t'|' -k1 -rn
```

### 2. 读取统计数据

```bash
cat "$HOME/.claude/skills/stats.json" 2>/dev/null || echo '{}'
```

## 输出格式

展示为分类表格，按调用次数排序。技能分为三类：

1. **业务技能** - 常规技能（非 api- 和非 _archived_ 前缀）
2. **原子化技能** - `api-` 前缀，底层能力封装
3. **已归档技能** - `_archived_` 前缀，历史版本

```
## 业务技能

| 技能名 | 描述 | 调用次数 |
|--------|------|----------|
| research | 深度调研工具，支持多信息源并发搜索... | 42 |
| social-media | 社交媒体统一入口 - 下载/发布/文案... | 28 |
| video | 视频制作与处理... | 15 |
| ...更多... |

## 原子化技能 (api-)

底层能力封装，供其他技能调用或直接使用。

| 技能名 | 描述 | 调用次数 |
|--------|------|----------|
| api-asr | 火山引擎语音识别... | 5 |
| api-tts | 火山引擎语音合成... | 3 |
| api-draw | 综合画图工具... | 2 |
| ...更多... |

## 已归档技能 (_archived_)

| 技能名 | 描述 | 调用次数 |
|--------|------|----------|
| _archived_perplexity-research | 基于 Perplexity 进行调研... | 1 |
| ...更多... |

---

共 XX 个技能（业务 X + 原子化 X + 归档 X），累计调用 XX 次

**提示**：使用 `/技能名` 调用技能
```

## 更新统计

当 skill 被调用时，需要更新统计：

```bash
# 增加调用计数
SKILL_NAME="xxx"
STATS_FILE="$HOME/.claude/skills/stats.json"
jq --arg name "$SKILL_NAME" '.[$name] = ((.[$name] // 0) + 1)' "$STATS_FILE" > "$STATS_FILE.tmp" && mv "$STATS_FILE.tmp" "$STATS_FILE"
```
