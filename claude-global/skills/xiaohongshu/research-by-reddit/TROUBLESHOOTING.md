# 故障排查指南

遇到问题？本指南涵盖常见问题和解决方案。

## 目录

- [安装问题](#安装问题)
- [认证错误](#认证错误)
- [API 限制](#api-限制)
- [数据获取问题](#数据获取问题)
- [AI 分析问题](#ai-分析问题)
- [编码问题](#编码问题)
- [性能问题](#性能问题)

---

## 安装问题

### 问题: `ModuleNotFoundError: No module named 'praw'`

**原因**: 未安装 Python 依赖

**解决方案**:
```bash
cd .claude/skills/research-by-reddit
pip install -r scripts/requirements.txt
```

### 问题: `pip install` 失败

**原因**: Python 版本过低或 pip 未安装

**解决方案**:
```bash
# 检查 Python 版本（需要 3.7+）
python --version

# 升级 pip
python -m pip install --upgrade pip

# 使用 pip3 (macOS/Linux)
pip3 install -r scripts/requirements.txt

# 使用虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r scripts/requirements.txt
```

### 问题: 权限错误 (Permission denied)

**解决方案**:
```bash
# 使用 --user 安装
pip install --user -r scripts/requirements.txt

# 或使用 sudo (不推荐)
sudo pip install -r scripts/requirements.txt
```

---

## 认证错误

### 问题: `Missing Reddit credentials`

**错误信息**:
```
ValueError: Missing Reddit credentials. Set REDDIT_CLIENT_ID/REDDIT_CLIENT_SECRET
```

**原因**: 未配置 Reddit API 凭证

**解决方案**:

**方法 1: 环境变量**
```bash
export REDDIT_CLIENT_ID="your_client_id"
export REDDIT_CLIENT_SECRET="your_client_secret"
```

**方法 2: .env 文件**
```bash
# 创建 .env 文件
cat > .env <<EOF
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
EOF

# 安装 python-dotenv
pip install python-dotenv

# 在脚本中加载
from dotenv import load_dotenv
load_dotenv()
```

**方法 3: 更新配置文件**
```bash
# 编辑 NormVio/src/config.py
PRAW_CLIENT_ID = 'your_client_id'
PRAW_CLIENT_SECRET = 'your_client_secret'
```

### 问题: 如何获取 Reddit API 凭证？

**步骤**:
1. 访问 https://www.reddit.com/prefs/apps
2. 登录 Reddit 账号
3. 点击 "Create App" 或 "Create Another App"
4. 填写表单：
   - **name**: 任意名称（如 "reddit-research"）
   - **App type**: 选择 "script"
   - **description**: 可选
   - **about url**: 可选
   - **redirect uri**: 填写 `http://localhost:8080`
5. 点击 "Create app"
6. 复制 **Client ID** (应用名称下方的字符串)
7. 复制 **Client Secret** (标记为 "secret" 的字段)

### 问题: `401 Unauthorized` 或 `403 Forbidden`

**原因**: API 凭证无效或过期

**解决方案**:
1. 检查凭证是否正确复制（无多余空格）
2. 重新生成 Reddit App 凭证
3. 确认 App 类型为 "script"
4. 检查 User Agent 是否符合 Reddit 要求

```python
# 测试凭证
from reddit_client import build_reddit_client

reddit = build_reddit_client()
print(reddit.user.me())  # 应输出你的用户名（如果提供了用户名和密码）
```

---

## API 限制

### 问题: `429 Too Many Requests` 或 Rate Limit 错误

**错误信息**:
```
prawcore.exceptions.TooManyRequests: received 429 HTTP response
```

**原因**: 超过 Reddit API 请求限制

**Reddit API 限制**:
- 60 requests / minute
- 600 requests / 10 minutes

**解决方案**:

**1. 减少请求频率**
```python
# 减少 limit 参数
posts = fetch_search_results(reddit, "keyword", limit=5)  # 而不是 100

# 增加请求间隔
import time
for subreddit in subreddits:
    posts = fetch_posts(reddit, subreddit)
    time.sleep(2)  # 等待 2 秒
```

**2. PRAW 自动处理**
PRAW 会自动处理 rate limit，等待合适的时间后重试。通常无需手动干预。

**3. 升级 API 配额**
- 申请 OAuth2 App（更高配额）
- 联系 Reddit 支持

### 问题: 请求超时 (Timeout)

**解决方案**:
```python
# 增加超时时间
analysis, _ = request_openrouter(
    model,
    messages,
    api_key,
    base_url,
    timeout=180  # 3 分钟
)
```

---

## 数据获取问题

### 问题: `prawcore.exceptions.NotFound: received 404 HTTP response`

**原因**: Subreddit 或帖子不存在

**解决方案**:
```python
from prawcore.exceptions import NotFound

try:
    posts = fetch_posts(reddit, "nonexistent_subreddit")
except NotFound:
    print("Subreddit 不存在")
```

**常见错误**:
- Subreddit 名称拼写错误
- Subreddit 是私有的或被封禁
- 帖子已删除或 ID 错误

### 问题: 搜索返回空结果

**原因**:
- 搜索关键词太具体
- 时间范围太窄
- Subreddit 内容不匹配

**解决方案**:
```bash
# 扩大搜索范围
python analyze_reddit.py \
  --query "keyword" \
  --search-subreddit all \     # 搜索全站
  --time-filter all \           # 所有时间
  --limit 50                    # 增加数量

# 尝试不同关键词
python analyze_reddit.py --query "AI OR artificial intelligence"

# 使用不同排序
python analyze_reddit.py --query "keyword" --search-sort top
```

### 问题: 评论数据不完整

**原因**: Reddit API 限制，某些评论被折叠

**解决方案**:
```python
# 增加评论限制
posts = fetch_search_results(
    reddit,
    "keyword",
    include_comments=True,
    comment_limit=50  # 默认 10
)

# 手动展开评论
submission.comments.replace_more(limit=None)  # 展开所有（慢）
```

### 问题: 帖子文本被截断

**原因**: `max_text_length` 限制

**解决方案**:
```python
# 增加文本长度限制
posts = fetch_search_results(
    reddit,
    "keyword",
    max_text_length=5000,      # 默认 1500
    max_comment_length=2000    # 默认 500
)
```

---

## AI 分析问题

### 问题: `Missing OPENROUTER_API_KEY`

**原因**: 未配置 OpenRouter API Key

**解决方案**:
```bash
# 设置环境变量
export OPENROUTER_API_KEY="sk-or-..."

# 或在 .env 文件中添加
echo 'OPENROUTER_API_KEY=sk-or-...' >> .env
```

**获取 API Key**:
1. 访问 https://openrouter.ai/
2. 注册账号
3. 访问 https://openrouter.ai/keys
4. 创建新的 API Key

### 问题: AI 分析失败或返回错误

**错误信息**:
```
RuntimeError: OpenRouter request failed (402): Insufficient credits
```

**原因**:
- API Key 无效
- 余额不足
- 模型不可用
- 请求超时

**解决方案**:

**1. 检查余额**
```bash
# 访问 OpenRouter 控制台
https://openrouter.ai/credits
```

**2. 使用更便宜的模型**
```bash
python analyze_reddit.py \
  --query "..." \
  --model google/gemini-2-flash-thinking-exp  # 便宜且快速
```

**推荐模型**（按价格排序）:
- `google/gemini-2-flash-thinking-exp` - 最便宜
- `google/gemini-pro` - 中等
- `anthropic/claude-3.5-sonnet` - 较贵但质量高

**3. 跳过 AI 分析**
```bash
# 仅获取数据，不进行 AI 分析
python analyze_reddit.py \
  --query "..." \
  --skip-analysis \
  --output data.json
```

### 问题: AI 分析输出语言不正确

**原因**: `analysis-language` 参数设置错误

**解决方案**:
```bash
# 中文分析
python analyze_reddit.py --query "..." --analysis-language zh

# 英文分析
python analyze_reddit.py --query "..." --analysis-language en
```

### 问题: AI 分析质量不理想

**解决方案**:

**1. 提供更多数据**
```bash
python analyze_reddit.py \
  --query "..." \
  --limit 20 \              # 增加帖子数量
  --include-comments \      # 包含评论
  --comment-limit 20        # 增加评论数量
```

**2. 使用更强大的模型**
```bash
python analyze_reddit.py \
  --query "..." \
  --model anthropic/claude-3.5-sonnet  # 更强但更贵
```

**3. 自定义提示词**
编辑 `reddit_client.py` 中的 `build_analysis_prompt()` 函数。

---

## 编码问题

### 问题: 中文乱码

**原因**: 终端或文件编码不是 UTF-8

**解决方案**:

**macOS/Linux**:
```bash
# 设置终端编码
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# 或在脚本开头添加
# -*- coding: utf-8 -*-
```

**Windows**:
```powershell
# 设置控制台代码页为 UTF-8
chcp 65001

# 或使用 Windows Terminal
```

**保存文件时**:
```bash
# 确保使用 UTF-8 编码
python analyze_reddit.py --query "..." --output-md report.md
```

### 问题: JSON 输出乱码

**解决方案**:
```python
# 在脚本中使用 ensure_ascii=False
import json

with open("output.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

---

## 性能问题

### 问题: 脚本运行很慢

**原因**:
- 请求数据量大
- 包含大量评论
- API 响应慢
- AI 分析耗时

**解决方案**:

**1. 减少数据量**
```bash
python analyze_reddit.py \
  --query "..." \
  --limit 10 \              # 减少帖子数量
  --comment-limit 5 \       # 减少评论数量
  --max-text-length 500     # 限制文本长度
```

**2. 跳过 AI 分析**
```bash
python analyze_reddit.py --query "..." --skip-analysis
```

**3. 使用更快的模型**
```bash
python analyze_reddit.py \
  --query "..." \
  --model google/gemini-2-flash-thinking-exp  # 最快
```

**4. 并行处理**（高级）
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(fetch_posts, reddit, sub) for sub in subreddits]
    results = [f.result() for f in futures]
```

### 问题: 内存占用过高

**原因**: 获取大量数据

**解决方案**:
```python
# 分批处理
for i in range(0, 100, 10):
    posts = fetch_search_results(reddit, "keyword", limit=10)
    # 处理 posts
    # 释放内存
    del posts
```

---

## 其他问题

### 问题: Claude Code 未自动调用 skill

**原因**:
- Skill 未正确安装
- SKILL.md 中的 description 不匹配

**解决方案**:

**1. 检查 skill 位置**
```bash
# 项目级
ls .claude/skills/research-by-reddit/SKILL.md

# 用户级
ls ~/.claude/skills/research-by-reddit/SKILL.md
```

**2. 检查 YAML frontmatter**
```yaml
---
name: research-by-reddit
description: 基于 Reddit API 进行深度调研并生成研究报告...
allowed-tools: Bash(python:*), Read, Write
model: sonnet
---
```

**3. 重启 Claude Code**
```bash
# 退出并重新启动
```

**4. 手动触发**
在请求中明确提及 "Reddit 调研" 或 "基于 Reddit"。

### 问题: 脚本路径错误

**错误信息**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'scripts/analyze_reddit.py'
```

**解决方案**:
```bash
# 确保在正确的目录
cd .claude/skills/research-by-reddit

# 或使用绝对路径
python /full/path/to/.claude/skills/research-by-reddit/scripts/analyze_reddit.py
```

### 问题: Import 错误

**错误信息**:
```
ModuleNotFoundError: No module named 'reddit_client'
```

**解决方案**:
```bash
# 确保在 scripts 目录或添加到 PYTHONPATH
cd scripts
python analyze_reddit.py --query "..."

# 或设置 PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/.claude/skills/research-by-reddit/scripts"
```

---

## 调试技巧

### 1. 启用详细日志

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

### 2. 测试 Reddit 连接

```python
from reddit_client import build_reddit_client

reddit = build_reddit_client()
print(f"User: {reddit.user.me()}")  # 需要用户名密码
print("Connection successful!")
```

### 3. 测试 OpenRouter API

```bash
curl -X POST https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemini-2-flash-thinking-exp",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### 4. 检查环境变量

```bash
# 列出所有 Reddit 相关环境变量
env | grep REDDIT

# 列出所有 OpenRouter 相关环境变量
env | grep OPENROUTER
```

---

## 仍然有问题？

1. **查看日志**: 脚本输出的错误信息通常包含详细原因
2. **查看 API 文档**:
   - [PRAW 文档](https://praw.readthedocs.io/)
   - [Reddit API 文档](https://www.reddit.com/dev/api)
   - [OpenRouter 文档](https://openrouter.ai/docs)
3. **检查 GitHub Issues**: 搜索类似问题
4. **提交问题**: 创建新的 Issue，附带完整错误信息

**提交问题时请包含**:
- 完整的错误消息
- 使用的命令
- Python 版本 (`python --version`)
- PRAW 版本 (`pip show praw`)
- 操作系统

---

**快速诊断清单**:

- [ ] 安装了所有依赖 (`pip install -r requirements.txt`)
- [ ] 配置了 `REDDIT_CLIENT_ID` 和 `REDDIT_CLIENT_SECRET`
- [ ] 配置了 `OPENROUTER_API_KEY` (如需 AI 分析)
- [ ] Reddit API 凭证有效
- [ ] 网络连接正常
- [ ] Python 版本 3.7+
- [ ] 终端编码为 UTF-8
- [ ] 在正确的目录运行脚本
