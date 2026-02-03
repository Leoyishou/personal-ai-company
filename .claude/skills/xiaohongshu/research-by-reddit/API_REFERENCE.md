# Reddit 调研 API 参考文档

## 目录

- [核心函数](#核心函数)
- [环境变量配置](#环境变量配置)
- [命令行工具](#命令行工具)
- [PRAW API 参考](#praw-api-参考)
- [数据结构](#数据结构)

---

## 核心函数

### build_reddit_client()

构建并返回配置好的 Reddit API 客户端。

**返回值**: `praw.Reddit`

**环境变量**:
- `REDDIT_CLIENT_ID` (必需)
- `REDDIT_CLIENT_SECRET` (必需)
- `REDDIT_USERNAME` (可选)
- `REDDIT_PASSWORD` (可选)
- `REDDIT_USER_AGENT` (可选)

**示例**:
```python
from reddit_client import build_reddit_client

reddit = build_reddit_client()
```

**异常**:
- `ValueError`: 缺少必需的 API 凭证

---

### fetch_search_results()

在 Reddit 搜索关键词。

**参数**:
```python
fetch_search_results(
    reddit,                      # PRAW Reddit 客户端
    query,                       # 搜索关键词 (str)
    search_subreddit="all",      # 搜索范围 (str)
    search_sort="relevance",     # 排序方式 (str)
    time_filter="week",          # 时间范围 (str)
    limit=5,                     # 结果数量 (int)
    include_comments=False,      # 是否包含评论 (bool)
    comment_limit=10,            # 评论数量 (int)
    max_text_length=1500,        # 帖子文本最大长度 (int)
    max_comment_length=500,      # 评论文本最大长度 (int)
)
```

**排序方式** (`search_sort`):
- `relevance` - 相关性（默认）
- `hot` - 热度
- `top` - 最高分
- `new` - 最新
- `comments` - 评论数

**时间范围** (`time_filter`):
- `hour` - 过去1小时
- `day` - 过去24小时
- `week` - 过去一周（默认）
- `month` - 过去一月
- `year` - 过去一年
- `all` - 所有时间

**返回值**: `list[dict]` - 帖子数据列表

**示例**:
```python
posts = fetch_search_results(
    reddit,
    query="Next.js vs Remix",
    search_subreddit="reactjs",
    search_sort="top",
    time_filter="month",
    limit=10,
    include_comments=True
)
```

---

### fetch_posts()

获取特定 Subreddit 的帖子列表。

**参数**:
```python
fetch_posts(
    reddit,                      # PRAW Reddit 客户端
    subreddit,                   # Subreddit 名称 (str)
    sort="hot",                  # 排序方式 (str)
    limit=5,                     # 帖子数量 (int)
    time_filter="week",          # 时间过滤 (str)
    include_comments=False,      # 是否包含评论 (bool)
    comment_limit=10,            # 评论数量 (int)
    max_text_length=1500,        # 帖子文本最大长度 (int)
    max_comment_length=500,      # 评论文本最大长度 (int)
)
```

**排序方式** (`sort`):
- `hot` - 热门（默认）
- `new` - 最新
- `top` - 最高分（需要 time_filter）
- `controversial` - 争议性（需要 time_filter）

**返回值**: `list[dict]` - 帖子数据列表

**示例**:
```python
posts = fetch_posts(
    reddit,
    subreddit="programming",
    sort="top",
    time_filter="week",
    limit=20,
    include_comments=True
)
```

---

### fetch_single_post()

获取单个帖子的详细信息。

**参数**:
```python
fetch_single_post(
    reddit,                      # PRAW Reddit 客户端
    post_id=None,                # Reddit 帖子 ID (str, 可选)
    post_url=None,               # Reddit 帖子 URL (str, 可选)
    include_comments=False,      # 是否包含评论 (bool)
    comment_limit=10,            # 评论数量 (int)
    max_text_length=1500,        # 帖子文本最大长度 (int)
    max_comment_length=500,      # 评论文本最大长度 (int)
)
```

**注意**: `post_id` 和 `post_url` 必须提供一个。

**返回值**: `dict` - 帖子数据

**示例**:
```python
# 使用帖子 ID
post = fetch_single_post(reddit, post_id="abc123", include_comments=True)

# 使用帖子 URL
post = fetch_single_post(
    reddit,
    post_url="https://reddit.com/r/programming/comments/xyz",
    include_comments=True
)
```

---

### build_analysis_prompt()

构建 AI 分析提示词。

**参数**:
```python
build_analysis_prompt(
    posts,                       # 帖子数据列表 (list[dict])
    language="zh"                # 输出语言 (str)
)
```

**支持的语言**:
- `zh`, `zh-cn`, `cn`, `中文` → 简体中文
- 其他语言代码保持原样

**返回值**: `str` - 分析提示词

**示例**:
```python
prompt = build_analysis_prompt(posts, language="zh")
```

---

### request_openrouter()

调用 OpenRouter API 进行 AI 分析。

**参数**:
```python
request_openrouter(
    model,                       # 模型名称 (str)
    messages,                    # 消息列表 (list[dict])
    api_key=None,                # API Key (str, 可选)
    base_url=None,               # API 端点 (str, 可选)
    timeout=90                   # 超时时间 (int, 秒)
)
```

**支持的模型** (示例):
- `google/gemini-2-flash-thinking-exp` (推荐，快速+便宜)
- `google/gemini-pro`
- `anthropic/claude-3.5-sonnet`
- `openai/gpt-4o`

完整模型列表: https://openrouter.ai/models

**返回值**: `tuple[str, dict]` - (分析文本, 完整响应)

**示例**:
```python
messages = [{"role": "user", "content": prompt}]
analysis, raw_data = request_openrouter(
    "google/gemini-2-flash-thinking-exp",
    messages,
    api_key="sk-or-...",
)
```

**异常**:
- `ValueError`: 缺少 API Key
- `RuntimeError`: API 调用失败

---

### render_markdown()

将结果渲染为 Markdown 格式报告。

**参数**:
```python
render_markdown(
    result                       # 结果字典 (dict)
)
```

**结果字典结构**:
```python
{
    "source": {
        "type": "search",        # search/subreddit/submission
        "query": "...",          # 搜索关键词（仅 search 类型）
        "subreddit": "...",      # Subreddit 名称
        "value": "...",          # 帖子 ID/URL（仅 submission 类型）
        "sort": "...",
        "time_filter": "..."
    },
    "posts": [...],              # 帖子数据列表
    "analysis": "...",           # AI 分析（可选）
    "model": "..."               # 使用的模型（可选）
}
```

**返回值**: `str` - Markdown 格式报告

**示例**:
```python
result = {
    "source": {"type": "search", "query": "AI coding", "subreddit": "programming"},
    "posts": posts,
    "analysis": analysis
}
markdown = render_markdown(result)
```

---

## 环境变量配置

### Reddit API 凭证

| 变量名 | 必需 | 说明 | 示例 |
|--------|------|------|------|
| `REDDIT_CLIENT_ID` | ✅ | Reddit App Client ID | `abc123xyz` |
| `REDDIT_CLIENT_SECRET` | ✅ | Reddit App Client Secret | `secret_key_here` |
| `REDDIT_USERNAME` | ❌ | Reddit 用户名 | `your_username` |
| `REDDIT_PASSWORD` | ❌ | Reddit 密码 | `your_password` |
| `REDDIT_USER_AGENT` | ❌ | User Agent | `research-by-reddit:v1.0` |

### OpenRouter API (用于 AI 分析)

| 变量名 | 必需 | 说明 | 示例 |
|--------|------|------|------|
| `OPENROUTER_API_KEY` | ✅ | OpenRouter API Key | `sk-or-...` |
| `OPENROUTER_MODEL` | ❌ | 默认模型 | `google/gemini-2-flash-thinking-exp` |
| `OPENROUTER_BASE_URL` | ❌ | API 端点 | `https://openrouter.ai/api/v1/chat/completions` |
| `OPENROUTER_SITE_URL` | ❌ | 网站 URL (可选) | `https://yoursite.com` |
| `OPENROUTER_APP_NAME` | ❌ | 应用名称 (可选) | `research-by-reddit` |

### 配置方法

**方法 1: 导出环境变量** (临时)
```bash
export REDDIT_CLIENT_ID="your_client_id"
export REDDIT_CLIENT_SECRET="your_client_secret"
export OPENROUTER_API_KEY="sk-or-..."
```

**方法 2: `.env` 文件** (推荐)
```bash
# 在项目根目录创建 .env 文件
cat > .env <<EOF
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
OPENROUTER_API_KEY=sk-or-...
EOF

# 使用 python-dotenv 加载
pip install python-dotenv
```

**方法 3: Shell 配置文件** (永久)
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
echo 'export REDDIT_CLIENT_ID="your_client_id"' >> ~/.bashrc
echo 'export REDDIT_CLIENT_SECRET="your_client_secret"' >> ~/.bashrc
source ~/.bashrc
```

---

## 命令行工具

### analyze_reddit.py

主调研脚本，支持搜索、获取帖子、AI 分析。

**基本用法**:
```bash
# 搜索
python analyze_reddit.py --query "关键词" [选项]

# 获取 Subreddit 帖子
python analyze_reddit.py --subreddit subreddit_name [选项]

# 分析单个帖子
python analyze_reddit.py --post-id abc123 [选项]
python analyze_reddit.py --post-url "https://..." [选项]
```

**完整参数**:
```
数据源参数（互斥，必须选一个）:
  --query QUERY                搜索关键词
  --subreddit SUBREDDIT        Subreddit 名称
  --post-id POST_ID            帖子 ID
  --post-url POST_URL          帖子 URL

搜索参数:
  --search-subreddit SUBREDDIT 搜索范围（默认 all）
  --search-sort {relevance,hot,top,new,comments}
                               搜索排序（默认 relevance）

获取参数:
  --sort {hot,new,top,controversial}
                               排序方式（默认 hot）
  --time-filter {hour,day,week,month,year,all}
                               时间范围（默认 week）
  --limit N                    结果数量（默认 5）

评论参数:
  --include-comments           包含评论
  --comment-limit N            评论数量（默认 10）
  --max-text-length N          帖子文本最大长度（默认 1500）
  --max-comment-length N       评论文本最大长度（默认 500）

分析参数:
  --analysis-language {zh,en}  分析语言（默认 zh）
  --model MODEL                AI 模型（默认 gemini-2-flash-thinking-exp）
  --skip-analysis              跳过 AI 分析，仅获取数据

输出参数:
  --output FILE                保存 JSON 到文件
  --output-md FILE             保存 Markdown 到文件
```

**示例**:
```bash
# 搜索 + AI 分析 + 保存 Markdown
python analyze_reddit.py \
  --query "Next.js vs Remix" \
  --search-subreddit reactjs \
  --limit 10 \
  --include-comments \
  --analysis-language zh \
  --output-md report.md

# 获取热门帖子，仅数据
python analyze_reddit.py \
  --subreddit programming \
  --sort hot \
  --limit 20 \
  --skip-analysis \
  --output data.json

# 深度分析单个帖子
python analyze_reddit.py \
  --post-url "https://reddit.com/r/..." \
  --include-comments \
  --comment-limit 50 \
  --analysis-language zh \
  --output-md deep_analysis.md
```

---

## PRAW API 参考

### 搜索 Subreddit

```python
subreddit = reddit.subreddit("programming")

# 搜索
results = subreddit.search(
    "AI tools",
    sort="relevance",      # relevance/hot/top/new/comments
    time_filter="month",   # hour/day/week/month/year/all
    limit=10
)

# 热门帖子
hot = subreddit.hot(limit=20)

# 最新帖子
new = subreddit.new(limit=20)

# 最高分帖子
top = subreddit.top(time_filter="week", limit=20)

# 争议性帖子
controversial = subreddit.controversial(time_filter="week", limit=20)
```

### 获取帖子详情

```python
# 通过 ID
submission = reddit.submission(id="abc123")

# 通过 URL
submission = reddit.submission(url="https://reddit.com/r/...")

# 访问属性
print(submission.title)
print(submission.selftext)
print(submission.score)
print(submission.num_comments)
print(submission.author.name)
```

### 获取评论

```python
# 设置评论排序
submission.comment_sort = "top"  # top/new/controversial/old/qa

# 展开所有评论（移除 MoreComments）
submission.comments.replace_more(limit=0)

# 遍历评论
for comment in submission.comments:
    print(comment.body)
    print(comment.score)
    print(comment.author.name if comment.author else "[deleted]")
```

### Rate Limiting

PRAW 自动处理 Reddit API 的 rate limit，无需手动控制。

默认限制：
- 60 requests / minute
- 自动延迟请求以避免超限

---

## 数据结构

### 帖子数据 (Post)

```python
{
    "id": "abc123",                    # 帖子 ID
    "title": "...",                    # 标题
    "selftext": "...",                 # 正文（如果有）
    "author": "username",              # 作者用户名
    "subreddit": "programming",        # Subreddit 名称
    "score": 150,                      # 分数 (upvotes - downvotes)
    "num_comments": 45,                # 评论数
    "created_utc": 1704614400,         # 创建时间 (Unix timestamp)
    "created_at": "2024-01-07T12:00:00Z",  # 创建时间 (ISO 8601)
    "url": "https://...",              # 链接 URL
    "permalink": "https://reddit.com/r/...",  # Reddit 链接
    "top_comments": [...]              # Top 评论（如果 include_comments=True）
}
```

### 评论数据 (Comment)

```python
{
    "id": "xyz789",                    # 评论 ID
    "author": "username",              # 作者用户名
    "score": 25,                       # 分数
    "body": "...",                     # 评论内容
    "created_utc": 1704618000          # 创建时间 (Unix timestamp)
}
```

### 结果数据 (Result)

```python
{
    "source": {
        "type": "search",              # search/subreddit/submission
        "query": "AI tools",           # 搜索关键词（search 类型）
        "subreddit": "programming",    # Subreddit 名称
        "search_sort": "relevance",    # 搜索排序
        "sort": "hot",                 # 排序方式（subreddit 类型）
        "time_filter": "week",         # 时间范围
        "value": "abc123"              # 帖子 ID/URL（submission 类型）
    },
    "posts": [...],                    # 帖子数据列表
    "analysis": "...",                 # AI 分析文本（可选）
    "model": "google/gemini-2-flash-thinking-exp"  # 模型名称（可选）
}
```

---

## 最佳实践

### 1. 错误处理

```python
from reddit_client import build_reddit_client
from prawcore.exceptions import ResponseException, NotFound

try:
    reddit = build_reddit_client()
    posts = fetch_search_results(reddit, "keyword", limit=10)
except ValueError as e:
    print(f"配置错误: {e}")
except ResponseException as e:
    print(f"API 请求失败: {e}")
except NotFound:
    print("未找到 Subreddit 或帖子")
```

### 2. 性能优化

```python
# 限制结果数量，避免过载
posts = fetch_search_results(reddit, "keyword", limit=10)

# 仅在需要时包含评论
posts = fetch_search_results(reddit, "keyword", include_comments=False)

# 限制文本长度
posts = fetch_search_results(
    reddit,
    "keyword",
    max_text_length=500,
    max_comment_length=200
)
```

### 3. 批量操作

```python
# 一次性收集多个 subreddit 的数据
subreddits = ["programming", "webdev", "python"]
all_posts = []

for sub in subreddits:
    posts = fetch_posts(reddit, sub, limit=10)
    all_posts.extend(posts)
```

---

## 相关资源

- **PRAW 文档**: https://praw.readthedocs.io/
- **Reddit API 文档**: https://www.reddit.com/dev/api
- **OpenRouter 模型**: https://openrouter.ai/models
- **获取 Reddit API 凭证**: https://www.reddit.com/prefs/apps

---

更多问题？查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
