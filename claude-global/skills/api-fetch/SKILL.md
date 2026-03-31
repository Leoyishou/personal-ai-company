---
name: api-fetch
shortname: api-fetch
description: 统一搜索与抓取能力层 - 整合所有外部信息获取接口（搜索、抓取、下载）
version: 1.0.0
author: Claude
allowed-tools: Bash(python:*), Read, Write, Glob, WebSearch, WebFetch
model: sonnet
tags: [fetch, search, download, twitter, reddit, perplexity, douyin, xiaohongshu]
---

# api-fetch - 统一搜索与抓取能力层

## 架构概览

```
api-fetch/
├── search/           # 搜索接口（返回搜索结果）
│   ├── perplexity.py    # Perplexity 全网搜索
│   ├── twitter.py       # Grok X/Twitter 搜索
│   ├── reddit.py        # Reddit 搜索与分析
│   └── v2ex.py          # V2EX 中文技术社区
│
├── fetch/            # 抓取接口（获取单个URL内容）
│   ├── twitter.py       # 推文详情抓取
│   ├── zhihu.py         # 知乎内容抓取
│   └── generic.py       # 通用网页抓取
│
└── download/         # 下载接口（下载媒体文件）
    ├── twitter.py       # Twitter 视频/图片下载
    ├── xiaohongshu.py   # 小红书视频/图片下载
    └── douyin.py        # 抖音视频下载
```

---

## 一、搜索接口（search/）

### 1.1 Perplexity 全网搜索

```bash
python3 ~/.claude/skills/api-fetch/search/perplexity.py \
  --query "搜索内容" \
  [--deep]              # 深度研究模式
  [--lang zh|en]        # 输出语言
  [--output file.md]    # 保存报告
```

**API**: OpenRouter → `perplexity/sonar-pro-search` / `sonar-deep-research`

### 1.2 Grok X/Twitter 搜索

```bash
python3 ~/.claude/skills/api-fetch/search/twitter.py \
  --query "搜索内容" \
  [--users elonmusk,sama]  # 限定用户
  [--from 2025-01-01]      # 开始日期
  [--to 2025-01-31]        # 结束日期
  [--output file.md]       # 保存报告
```

**API**: xAI → `grok-4-1-fast` (x_search tool)

### 1.3 Reddit 搜索

```bash
python3 ~/.claude/skills/api-fetch/search/reddit.py \
  --query "搜索内容" \
  [--subreddit all|specific]  # 限定社区
  [--limit 12]                # 结果数量
  [--include-comments]        # 包含评论
  [--output file.md]          # 保存报告
```

**API**: Reddit API

### 1.4 V2EX 搜索

```bash
python3 ~/.claude/skills/api-fetch/search/v2ex.py \
  --query "搜索内容" \
  [--size 10]            # 结果数量
  [--output file.md]     # 保存报告
```

**API**: SOV2EX API

---

## 二、抓取接口（fetch/）

### 2.1 Twitter 推文抓取

```bash
python3 ~/.claude/skills/api-fetch/fetch/twitter.py \
  --url "https://x.com/user/status/123456" \
  [--json]               # JSON 输出
```

**API**: TwitterAPI.io

**返回数据**：
```json
{
  "id": "推文ID",
  "text": "推文内容",
  "author": {"name": "作者", "username": "用户名"},
  "metrics": {"like_count": 100, "retweet_count": 50},
  "media": [...]
}
```

### 2.2 知乎内容抓取

```bash
python3 ~/.claude/skills/api-fetch/fetch/zhihu.py \
  --url "https://zhihu.com/question/123456" \
  [--json]
```

**支持类型**：问题、回答、专栏文章、用户主页

### 2.3 通用网页抓取

```bash
python3 ~/.claude/skills/api-fetch/fetch/generic.py \
  --url "https://example.com" \
  [--json]
```

---

## 三、下载接口（download/）

### 3.1 Twitter 媒体下载

```bash
python3 ~/.claude/skills/api-fetch/download/twitter.py \
  --url "https://x.com/user/status/123456" \
  -o ~/Downloads
```

### 3.2 小红书下载

```bash
python3 ~/.claude/skills/api-fetch/download/xiaohongshu.py \
  --url "https://www.xiaohongshu.com/explore/xxx" \
  -o ~/Downloads
```

### 3.3 抖音下载

```bash
python3 ~/.claude/skills/api-fetch/download/douyin.py \
  --url "https://v.douyin.com/xxx" \
  -o ~/Downloads \
  [-c cookies.txt]       # 自定义 cookies 路径
```

---

## 四、统一入口

### 4.1 智能路由

```bash
python3 ~/.claude/skills/api-fetch/main.py <URL或关键词> [选项]
```

自动识别：
- URL → 调用 fetch/ 或 download/
- 关键词 → 调用 search/

### 4.2 示例

```bash
# 搜索
python3 ~/.claude/skills/api-fetch/main.py "Claude Code" --source perplexity

# 抓取推文
python3 ~/.claude/skills/api-fetch/main.py "https://x.com/xxx/status/123"

# 下载抖音
python3 ~/.claude/skills/api-fetch/main.py "https://v.douyin.com/xxx" --download
```

---

## 五、环境配置

### API Keys（`~/.claude/secrets.env`）

```bash
# Perplexity (通过 OpenRouter)
OPENROUTER_API_KEY=sk-or-xxx

# Grok X/Twitter (需要 X Premium)
XAI_API_KEY=xai-xxx

# Reddit
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx

# Twitter API (twitterapi.io)
TWITTERAPI_IO_KEY=xxx
```

### Cookies 文件

| 平台 | 路径 |
|------|------|
| 抖音 | `~/.claude/douyin_cookies.txt` |
| B站 | `~/.claude/skills/biliup-publish/cookies.json` |

---

## 六、调用方规范

上层 skill（如 research、social-media）调用本 skill 时，使用以下路径：

```python
# 搜索
~/.claude/skills/api-fetch/search/perplexity.py
~/.claude/skills/api-fetch/search/twitter.py
~/.claude/skills/api-fetch/search/reddit.py
~/.claude/skills/api-fetch/search/v2ex.py

# 抓取
~/.claude/skills/api-fetch/fetch/twitter.py
~/.claude/skills/api-fetch/fetch/zhihu.py
~/.claude/skills/api-fetch/fetch/generic.py

# 下载
~/.claude/skills/api-fetch/download/twitter.py
~/.claude/skills/api-fetch/download/xiaohongshu.py
~/.claude/skills/api-fetch/download/douyin.py
```

---

## 七、能力矩阵

| 能力 | Perplexity | Twitter | Reddit | V2EX | 知乎 | 抖音 | 小红书 |
|------|:----------:|:-------:|:------:|:----:|:----:|:----:|:------:|
| 搜索 | ✅ | ✅ | ✅ | ✅ | - | - | - |
| 抓取 | - | ✅ | ✅ | ✅ | ✅ | - | ✅(MCP) |
| 下载 | - | ✅ | - | - | - | ✅ | ✅ |

---

## 八、迁移说明

本 skill 整合了以下能力：

| 原位置 | 新位置 |
|--------|--------|
| `research/scripts/sources/perplexity_research.py` | `api-fetch/search/perplexity.py` |
| `research/scripts/sources/grok_x_search.py` | `api-fetch/search/twitter.py` |
| `research/scripts/sources/analyze_reddit.py` | `api-fetch/search/reddit.py` |
| `research/scripts/sources/v2ex_search.py` | `api-fetch/search/v2ex.py` |
| `api-webfetch/webfetch_plus.py` | `api-fetch/fetch/*.py` |
| `social-media/scripts/platforms/social_download.py` | `api-fetch/download/*.py` |

旧路径保留软链接，确保向后兼容。
