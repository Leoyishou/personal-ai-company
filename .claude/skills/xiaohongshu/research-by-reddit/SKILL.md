---
name: research-by-reddit
description: 基于 Reddit API 进行深度调研并生成研究报告。支持搜索、获取帖子、评论分析、情感分析等。适用于市场调研、用户反馈分析、技术方案调研、产品评价收集、趋势分析等场景
allowed-tools: Bash(python:*), Read, Write
model: sonnet
---

# Reddit 深度调研工具

使用 Reddit API (PRAW) 进行专业的社区调研和分析，生成结构化报告。

## 快速开始

### 环境配置

首先确保已配置 Reddit API 凭证（环境变量）：

```bash
export REDDIT_CLIENT_ID="your_client_id"
export REDDIT_CLIENT_SECRET="your_client_secret"
export REDDIT_USERNAME="your_username"       # 可选
export REDDIT_PASSWORD="your_password"       # 可选
export OPENROUTER_API_KEY="your_api_key"     # 用于 AI 分析
```

或创建 `.env` 文件（项目根目录）：

```bash
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
OPENROUTER_API_KEY=your_openrouter_key
```

### 基础使用

**搜索调研：**
```bash
python scripts/search_reddit.py --query "Next.js vs Remix" --limit 10 --include-comments
```

**获取 Subreddit 热门帖子：**
```bash
python scripts/fetch_posts.py --subreddit reactjs --sort hot --limit 20 --include-comments
```

**分析单个帖子：**
```bash
python scripts/analyze_reddit.py --post-url "https://reddit.com/r/..." --include-comments
```

更多示例见 [EXAMPLES.md](EXAMPLES.md)

## 核心功能

### 1. 搜索 Reddit

在指定 subreddit 或全站搜索关键词：

```python
# 使用 scripts/search_reddit.py
--query "关键词"              # 搜索内容
--search-subreddit all       # 搜索范围（默认 all）
--search-sort relevance      # 排序方式
--time-filter week           # 时间范围
--limit 10                   # 结果数量
--include-comments           # 包含评论
```

### 2. 获取 Subreddit 帖子

获取特定社区的帖子列表：

```python
# 使用 scripts/fetch_posts.py
--subreddit programming      # Subreddit 名称
--sort hot                   # hot/new/top/controversial
--time-filter week           # 时间过滤
--limit 20                   # 帖子数量
--include-comments           # 包含 top 评论
```

### 3. AI 智能分析

使用 AI 模型分析 Reddit 讨论：

```python
# 使用 scripts/analyze_reddit.py
--query "AI coding tools"    # 或 --subreddit / --post-url
--analysis-language zh       # 分析语言（zh/en）
--model google/gemini-2-flash-thinking-exp # AI 模型
--output-md report.md        # 输出 Markdown 报告
```

### 4. 数据导出

支持多种输出格式：

- **JSON**: 完整结构化数据（`--output result.json`）
- **Markdown**: 可读性报告（`--output-md report.md`）
- **控制台**: 直接输出分析结果

## 调研工作流

当用户请求 Reddit 调研时，遵循以下流程：

### Step 1: 明确调研目标

与用户确认：
- 调研主题和关键问题
- 关注的 subreddit（技术/产品/市场等）
- 时间范围（最新/本周/本月/全部）
- 是否需要深入评论分析

### Step 2: 执行数据收集

根据需求选择合适的脚本：

**场景 A: 关键词搜索**
```bash
cd .claude/skills/research-by-reddit
python scripts/search_reddit.py \
  --query "TypeScript vs JavaScript" \
  --search-subreddit programming \
  --search-sort relevance \
  --time-filter month \
  --limit 15 \
  --include-comments \
  --comment-limit 10 \
  --output-md search_results.md
```

**场景 B: 社区热点分析**
```bash
python scripts/fetch_posts.py \
  --subreddit webdev \
  --sort top \
  --time-filter week \
  --limit 20 \
  --include-comments \
  --output-md top_posts.md
```

**场景 C: 深度帖子分析**
```bash
python scripts/analyze_reddit.py \
  --post-url "https://reddit.com/r/programming/comments/xyz" \
  --include-comments \
  --comment-limit 30 \
  --output-md deep_analysis.md
```

### Step 3: AI 智能分析

所有脚本支持 `--skip-analysis` 跳过 AI 分析，或使用 AI 生成深度洞察：

```bash
# 带 AI 分析（默认）
python scripts/search_reddit.py --query "..." --analysis-language zh

# 仅获取数据
python scripts/search_reddit.py --query "..." --skip-analysis --output data.json
```

AI 分析会生成：
1. 总体摘要
2. 主要话题与观点
3. 社区情绪与态度
4. 有争议的问题
5. 延伸阅读建议

### Step 4: 生成报告

使用 Read 工具读取生成的 Markdown 文件，并整合为最终报告：

```markdown
# [调研主题] Reddit 调研报告

## 执行摘要
- 调研时间：[自动生成]
- 数据来源：[subreddits 列表]
- 帖子数量：[统计]
- 核心发现：[AI 提取的关键洞察]

## 主要发现
[基于 AI 分析的结构化总结]

## 典型案例
[高票帖子和精彩评论]

## 数据明细
[完整帖子列表和评论]

## 行动建议
[基于调研的可执行建议]
```

## 工具脚本详解

### search_reddit.py - 搜索工具

**用途**: 在 Reddit 搜索关键词

**参数**:
```
--query              搜索关键词（必需）
--search-subreddit   搜索范围（默认 all）
--search-sort        排序：relevance/hot/top/new/comments
--time-filter        时间：hour/day/week/month/year/all
--limit              结果数量（默认 5）
--include-comments   包含评论
--comment-limit      评论数量（默认 10）
--analysis-language  分析语言（zh/en）
--output             保存 JSON
--output-md          保存 Markdown
```

### fetch_posts.py - 帖子获取

**用途**: 获取 subreddit 的帖子列表

**参数**:
```
--subreddit          Subreddit 名称（必需）
--sort               排序：hot/new/top/controversial
--time-filter        时间范围
--limit              帖子数量
--include-comments   包含评论
```

### analyze_reddit.py - 深度分析

**用途**: 分析单个帖子或执行综合调研

**参数**:
```
--post-id           帖子 ID
--post-url          帖子 URL
--query             搜索查询
--subreddit         Subreddit 名称
--model             AI 模型（默认 gemini-2-flash-thinking-exp）
--analysis-language 输出语言
```

完整 API 参考见 [API_REFERENCE.md](API_REFERENCE.md)

## 最佳实践

### 数据收集策略

1. **多维度搜索**
   - 使用不同关键词组合
   - 跨多个相关 subreddit
   - 尝试不同时间范围

2. **质量优先**
   - 优先分析 top/hot 帖子
   - 关注高评分评论
   - 过滤 spam 和低质量内容

3. **上下文理解**
   - 包含评论以获取多元观点
   - 注意帖子的时间背景
   - 理解 subreddit 文化差异

### 分析原则

1. **客观中立**: 呈现不同观点，避免选择性偏见
2. **数据驱动**: 用 score、评论数等量化指标支持结论
3. **可追溯**: 保留原始链接，便于验证
4. **时效性**: 注明数据收集时间

### 性能优化

1. **限制结果数量**: 使用 `--limit` 控制，避免过载
2. **合理使用评论**: 仅在需要时 `--include-comments`
3. **文本长度**: 使用 `--max-text-length` 和 `--max-comment-length` 控制
4. **批处理**: 一次性收集数据，避免重复调用 API

## 输出格式

### JSON 格式（结构化数据）

```json
{
  "source": {
    "type": "search",
    "query": "Next.js",
    "subreddit": "reactjs"
  },
  "posts": [
    {
      "id": "abc123",
      "title": "...",
      "selftext": "...",
      "author": "username",
      "score": 150,
      "num_comments": 45,
      "created_at": "2026-01-07T...",
      "permalink": "https://reddit.com/r/...",
      "top_comments": [...]
    }
  ],
  "analysis": "AI 生成的分析...",
  "model": "google/gemini-2-flash-thinking-exp"
}
```

### Markdown 格式（可读性报告）

自动生成包含：
- 搜索/来源信息
- 帖子列表（标题、作者、分数、链接）
- Top 评论摘要
- AI 分析（如果启用）

## 常见应用场景

### 技术选型调研
```bash
python scripts/search_reddit.py \
  --query "Docker vs Podman production" \
  --search-subreddit devops \
  --time-filter year \
  --limit 20 \
  --include-comments
```

### 产品市场调研
```bash
python scripts/search_reddit.py \
  --query "Notion alternatives 2026" \
  --search-subreddit productivity \
  --search-sort top \
  --limit 15
```

### 用户痛点分析
```bash
python scripts/fetch_posts.py \
  --subreddit vscode \
  --sort controversial \
  --time-filter month \
  --include-comments \
  --comment-limit 20
```

### 趋势分析
```bash
python scripts/search_reddit.py \
  --query "AI coding assistant" \
  --time-filter year \
  --limit 30 \
  --analysis-language zh
```

## 隐私与安全

1. **不存储敏感信息**: 仅分析公开讨论内容
2. **环境变量管理**: API key 通过环境变量配置
3. **遵守 API 限制**: 使用官方 PRAW 库，自动处理 rate limiting
4. **用户隐私**: 报告中不包含个人识别信息

## 故障排查

遇到问题？查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

常见问题：
- Reddit API 认证失败 → 检查环境变量
- Rate limit 错误 → 减少请求频率或升级 API 配额
- 分析失败 → 检查 OPENROUTER_API_KEY
- 中文乱码 → 确保使用 UTF-8 编码

## 依赖安装

首次使用需安装 Python 依赖：

```bash
cd .claude/skills/research-by-reddit
pip install -r scripts/requirements.txt
```

或使用虚拟环境：

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r scripts/requirements.txt
```

## 开始调研

配置完成后，直接在 Claude Code 中说：

```
帮我调研一下 Next.js 和 Remix 的实际使用体验
分析 r/programming 上关于 AI 编程工具的讨论
调研 Notion 用户最关心的问题
```

Claude 会自动使用这个 skill 执行专业的 Reddit API 调研！
