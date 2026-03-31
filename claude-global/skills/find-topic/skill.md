---
name: find-topic
description: "选题情报 - 自动采集 HN/GitHub/Reddit/X 热点 + AI 评分 + 去重推送"
user-invocable: true
allowed-tools: Bash(python:*), Read, Write
---

# Find Topic - 选题情报

自动采集多平台热点，AI 评分后推送最佳选题建议。

## 使用方式

```bash
# 完整流程：采集 + 评分 + 去重 + 推送
python3 ~/.claude/skills/find-topic/briefing.py

# 仅采集（不评分不推送）
python3 ~/.claude/skills/find-topic/briefing.py --collect-only

# 指定数据源
python3 ~/.claude/skills/find-topic/briefing.py --sources hackernews,github

# 跳过推送（调试用）
python3 ~/.claude/skills/find-topic/briefing.py --no-push
```

## 工作流

当用户说 `/find-topic` 时：

1. 运行 `briefing.py` 完整流程
2. 展示 Top 5 选题结果给用户
3. 用户确认后，为选中的选题创建 Linear Issue

## 数据源

| 源 | 采集内容 |
|----|----------|
| HackerNews | Top 30 stories (score > 100) |
| GitHub Trending | 每日趋势仓库 |
| Reddit | r/MachineLearning, r/LocalLLaMA, r/programming |
| Twitter/X | AI/LLM 相关讨论（通过 Grok） |

## 输出

- Telegram 推送每日摘要
- Linear 创建灵感 Issue（top 3 未重复）
- Supabase `pac.topic_briefings` 存储历史
- stdout 输出完整报告（供 Claude 展示）

## 环境变量

从 `~/.claude/secrets.env` 加载：
- `OPENROUTER_API_KEY` - AI 评分
- `XAI_API_KEY` - Twitter/X 采集
- `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` - Reddit 采集
- `LINEAR_API_KEY` - Linear 去重 + 创建 Issue
