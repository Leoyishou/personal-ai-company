# Reddit 调研 Skill (API 版)

基于 **Reddit API (PRAW)** 进行深度调研，自动生成结构化研究报告的 Claude Code skill。

使用真实的 Reddit API 而非搜索引擎，获取更精准、更完整的数据。

## 特性

✅ **直接 API 访问** - 使用 PRAW 库直接调用 Reddit API，数据更准确
✅ **完整元数据** - 获取分数、评论数、作者、创建时间等完整信息
✅ **深度评论分析** - 提取 top 评论及其上下文
✅ **AI 智能分析** - 使用 OpenRouter 模型自动生成洞察报告
✅ **多种输出格式** - JSON、Markdown、控制台输出
✅ **灵活配置** - 支持搜索、获取帖子、单帖分析等多种场景

## 文件结构

```
research-by-reddit/
├── SKILL.md              # 核心 skill 定义和工作流指令
├── API_REFERENCE.md      # 完整 API 参考文档
├── EXAMPLES.md           # 实际使用案例
├── TROUBLESHOOTING.md    # 故障排查指南
├── README.md             # 本文件
└── scripts/
    ├── reddit_client.py      # Reddit API 客户端库
    ├── analyze_reddit.py     # 主调研脚本
    └── requirements.txt      # Python 依赖
```

## 快速开始

### 1. 安装依赖

```bash
cd .claude/skills/research-by-reddit
pip install -r scripts/requirements.txt
```

**依赖说明**:
- `praw` - Reddit API 官方 Python 库
- `requests` - HTTP 请求库（用于 OpenRouter API）
- `python-dotenv` - 环境变量管理（可选）

### 2. 配置 Reddit API 凭证

**获取凭证**:
1. 访问 https://www.reddit.com/prefs/apps
2. 点击 "Create App" 或 "Create Another App"
3. 选择 **script** 类型
4. 填写名称和 redirect uri: `http://localhost:8080`
5. 获取 **Client ID** 和 **Client Secret**

**配置方式 A: 环境变量（推荐）**

```bash
export REDDIT_CLIENT_ID="your_client_id"
export REDDIT_CLIENT_SECRET="your_client_secret"
export OPENROUTER_API_KEY="sk-or-..."  # 用于 AI 分析
```

**配置方式 B: .env 文件**

```bash
# 在项目根目录创建 .env
cat > .env <<EOF
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_username  # 可选
REDDIT_PASSWORD=your_password  # 可选
OPENROUTER_API_KEY=sk-or-...
EOF
```

**获取 OpenRouter API Key**:
1. 访问 https://openrouter.ai/
2. 注册账号
3. 访问 https://openrouter.ai/keys 创建 API Key

### 3. 测试安装

```bash
cd scripts
python analyze_reddit.py --query "test" --limit 3 --skip-analysis
```

如果输出了 Reddit 帖子数据，说明配置成功！

## 安装方法

### 方法 1: 项目级安装

将整个文件夹复制到你的项目中：

```bash
cp -r /path/to/research-by-reddit /your/project/.claude/skills/
```

### 方法 2: 用户级安装（推荐）

所有项目都能使用：

```bash
# macOS / Linux
cp -r /path/to/research-by-reddit ~/.claude/skills/

# Windows
xcopy /path/to/research-by-reddit %USERPROFILE%\.claude\skills\ /E /I
```

### 方法 3: 直接使用当前 repo

如果你在这个 repo 中工作，skill 已经可用。

## 使用方法

### 在 Claude Code 中自动调用

Claude Code 会根据你的请求自动使用这个 skill：

```
帮我调研一下 Next.js 和 Remix 的实际使用体验
基于 Reddit 分析程序员对 AI 编程工具的看法
调研 r/webdev 上关于性能优化的讨论
```

### 直接运行脚本

**搜索调研**:
```bash
cd .claude/skills/research-by-reddit/scripts
python analyze_reddit.py \
  --query "Next.js vs Remix" \
  --search-subreddit reactjs \
  --limit 10 \
  --include-comments \
  --output-md report.md
```

**获取 Subreddit 热门**:
```bash
python analyze_reddit.py \
  --subreddit programming \
  --sort top \
  --time-filter week \
  --limit 20 \
  --include-comments \
  --output-md top_posts.md
```

**分析单个帖子**:
```bash
python analyze_reddit.py \
  --post-url "https://reddit.com/r/programming/comments/..." \
  --include-comments \
  --comment-limit 50 \
  --output-md deep_analysis.md
```

更多示例见 [EXAMPLES.md](EXAMPLES.md)

## 核心功能

### 1. 搜索 Reddit

在全站或特定 subreddit 搜索关键词：

```python
from reddit_client import build_reddit_client, fetch_search_results

reddit = build_reddit_client()
posts = fetch_search_results(
    reddit,
    query="AI coding tools",
    search_subreddit="programming",
    search_sort="relevance",
    time_filter="month",
    limit=15,
    include_comments=True
)
```

### 2. 获取 Subreddit 帖子

获取特定社区的热门/最新/最高分帖子：

```python
from reddit_client import fetch_posts

posts = fetch_posts(
    reddit,
    subreddit="webdev",
    sort="hot",  # hot/new/top/controversial
    limit=20,
    include_comments=True
)
```

### 3. 深度分析单帖

获取单个帖子的完整信息和评论：

```python
from reddit_client import fetch_single_post

post = fetch_single_post(
    reddit,
    post_url="https://reddit.com/r/.../comments/...",
    include_comments=True,
    comment_limit=50
)
```

### 4. AI 智能分析

使用 AI 模型自动分析讨论内容：

```python
from reddit_client import build_analysis_prompt, request_openrouter

prompt = build_analysis_prompt(posts, language="zh")
analysis, _ = request_openrouter(
    "google/gemini-2-flash-thinking-exp",
    [{"role": "user", "content": prompt}]
)
```

### 5. 生成 Markdown 报告

```python
from reddit_client import render_markdown

result = {
    "source": {"type": "search", "query": "AI tools"},
    "posts": posts,
    "analysis": analysis
}
markdown = render_markdown(result)
```

## 与 WebSearch 版本的对比

| 功能 | WebSearch 版 | API 版 (当前) |
|------|-------------|--------------|
| 数据来源 | 搜索引擎爬取 | Reddit 官方 API |
| 数据准确性 | 中等 | 高 |
| 元数据完整性 | 有限 | 完整（分数、评论数、作者等） |
| 评论深度 | 浅层 | 深度（可获取所有评论） |
| 速度 | 较快 | 快 |
| 配额限制 | 搜索引擎限制 | Reddit API 限制 (60 req/min) |
| 需要配置 | 否 | 是（需要 API 凭证） |
| 适用场景 | 快速浏览 | 深度调研 |

## 工作流示例

### 场景：技术选型调研

**用户请求**:
```
帮我调研一下 TypeScript 和 JavaScript 在实际项目中的使用体验
```

**Claude Code 执行流程**:

1. **明确调研目标**
   - 主题：TypeScript vs JavaScript
   - 范围：r/programming, r/webdev, r/typescript
   - 时间：最近一年

2. **执行搜索**
```bash
python scripts/analyze_reddit.py \
  --query "TypeScript vs JavaScript production" \
  --search-subreddit programming \
  --time-filter year \
  --limit 15 \
  --include-comments \
  --comment-limit 15 \
  --output-md typescript_research.md
```

3. **AI 分析**
   - 自动提取关键观点
   - 分析社区情感
   - 识别痛点和优势
   - 生成对比总结

4. **生成报告**
```markdown
# TypeScript vs JavaScript 调研报告

## 执行摘要
- 调研时间：2026-01-07
- 数据来源：r/programming (15 帖子，180+ 评论)
- 核心发现：
  - 大型项目更倾向 TypeScript (83% 正面评价)
  - 小型项目和原型开发 JavaScript 更灵活
  - 学习曲线是主要顾虑

## 主要发现
[详细分析...]

## 典型案例
[高票帖子精选...]

## 行动建议
1. 新项目推荐 TypeScript + strict mode
2. 现有 JS 项目可逐步迁移
3. 重点学习：泛型、类型推断、配置优化
```

更多场景见 [EXAMPLES.md](EXAMPLES.md)

## 配置说明

### allowed-tools

SKILL.md 中配置的工具限制：

```yaml
allowed-tools: Bash(python:*), Read, Write
```

- `Bash(python:*)` - 允许运行所有 Python 脚本
- `Read` - 读取生成的报告文件
- `Write` - 保存中间结果（如果需要）

### 模型选择

默认使用 `sonnet`，可在 SKILL.md 中修改：

```yaml
model: sonnet  # 或 opus, haiku
```

## 高级用法

### 自定义分析提示词

编辑 `scripts/reddit_client.py` 中的 `build_analysis_prompt()` 函数：

```python
def build_analysis_prompt(posts, language="zh"):
    # 自定义你的提示词
    return f"分析这些 Reddit 讨论，重点关注：1) 技术细节 2) 性能对比 3) 社区共识\n\n{posts}"
```

### 批量处理多个 Subreddit

```python
subreddits = ["programming", "webdev", "python"]
all_posts = []

for sub in subreddits:
    posts = fetch_posts(reddit, sub, limit=10)
    all_posts.extend(posts)

# 统一分析
analysis = request_openrouter(model, [{"role": "user", "content": build_analysis_prompt(all_posts)}])
```

### 定时调研任务

```bash
# crontab 示例：每周一早上 9 点执行
0 9 * * 1 cd /path/to/.claude/skills/research-by-reddit/scripts && python analyze_reddit.py --subreddit programming --sort top --time-filter week --output-md weekly_report.md
```

## API 参考

完整的 API 文档见 [API_REFERENCE.md](API_REFERENCE.md)

**核心函数**:
- `build_reddit_client()` - 构建 Reddit 客户端
- `fetch_search_results()` - 搜索 Reddit
- `fetch_posts()` - 获取 Subreddit 帖子
- `fetch_single_post()` - 获取单个帖子
- `build_analysis_prompt()` - 构建 AI 分析提示
- `request_openrouter()` - 调用 AI 分析
- `render_markdown()` - 生成 Markdown 报告

## 故障排查

遇到问题？查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

**常见问题**:
- ❌ `Missing Reddit credentials` → 配置环境变量
- ❌ `429 Too Many Requests` → 减少请求频率或等待
- ❌ `ModuleNotFoundError` → 运行 `pip install -r requirements.txt`
- ❌ 中文乱码 → 确保终端编码为 UTF-8
- ❌ Skill 未触发 → 重启 Claude Code 或明确提及 "Reddit 调研"

## 最佳实践

### 数据收集
1. ✅ 使用明确的关键词
2. ✅ 选择相关的 subreddit
3. ✅ 合理设置时间范围（避免过老或过新）
4. ✅ 包含评论以获取多元观点
5. ✅ 限制结果数量（避免过载）

### 分析质量
1. ✅ 提供足够的上下文（10+ 帖子）
2. ✅ 选择合适的 AI 模型（平衡成本和质量）
3. ✅ 使用中文分析（如需中文报告）
4. ✅ 验证 AI 分析的结论（对比原始数据）

### 性能优化
1. ✅ 使用 `--skip-analysis` 仅获取数据
2. ✅ 减少 `comment_limit` 和 `max_text_length`
3. ✅ 使用更快的 AI 模型
4. ✅ 批处理而非单独请求

## 适用场景

### ✅ 推荐使用
- 技术框架/工具选型调研
- 产品市场反馈分析
- 用户痛点和需求挖掘
- 社区趋势和情感分析
- 竞品对比研究
- 最佳实践收集

### ❌ 不推荐使用
- 实时舆情监控（API 有延迟）
- 大规模数据挖掘（受 API 限制）
- 私密内容访问（仅公开数据）
- 精确统计分析（样本偏差）

## 贡献和反馈

发现问题或有改进建议？

1. 查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. 提交 Issue
3. 提交 Pull Request
4. 分享你的使用案例

## 许可证

MIT License - 自由使用和修改

---

## 相关资源

- **PRAW 文档**: https://praw.readthedocs.io/
- **Reddit API**: https://www.reddit.com/dev/api
- **OpenRouter**: https://openrouter.ai/
- **Claude Code Skills**: https://code.claude.com/docs/en/skills

---

**开始使用**:

1. 安装依赖：`pip install -r scripts/requirements.txt`
2. 配置 API 凭证（环境变量或 .env 文件）
3. 测试运行：`python scripts/analyze_reddit.py --query "test" --limit 3`
4. 在 Claude Code 中说："帮我调研一下 [你的主题]"

🚀 享受专业的 Reddit 调研体验！
