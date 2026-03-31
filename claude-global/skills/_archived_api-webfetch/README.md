# WebFetchPlus - 智能网页内容抓取工具

<img alt="WebFetchPlus" src="https://img.shields.io/badge/WebFetchPlus-v1.0.0-blue">
<img alt="Python" src="https://img.shields.io/badge/Python-3.8+-green">
<img alt="License" src="https://img.shields.io/badge/License-MIT-yellow">

## 🚀 简介

WebFetchPlus 是一个智能的网页内容抓取工具，能够根据URL类型自动选择最佳的抓取策略。整合了多个强大的抓取能力：

- **TwitterAPI.io** - 无需官方API的Twitter内容抓取
- **Firecrawl** - 智能网页内容提取
- **Social Media** - 抖音、B站、小红书等社交媒体
- **Generic Fetch** - 通用网页抓取

## ✨ 特性

- 🤖 **智能路由** - 自动识别URL类型，选择最优策略
- 🌍 **多源支持** - Twitter、抖音、B站、小红书、YouTube等
- 📦 **统一接口** - 一致的调用方式和返回格式
- ⚡ **高性能** - 缓存机制、批量处理
- 🛡️ **错误处理** - 自动重试、降级策略
- 📊 **统计分析** - 抓取统计、成功率监控

## 📦 安装

```bash
# 克隆或复制到skills目录
cp -r webfetch-plus ~/.claude/skills/

# 安装依赖
pip install requests requests-oauthlib

# 设置执行权限
chmod +x ~/.claude/skills/webfetch-plus/webfetch_plus.py
```

## 🔧 配置

### 1. API密钥配置

编辑 `config.json`:

```json
{
  "twitter_api_key": "your_twitter_api_key",
  "firecrawl_api_key": "your_firecrawl_api_key"
}
```

### 2. 环境变量（可选）

```bash
export TWITTER_API_KEY="your_key"
export FIRECRAWL_API_KEY="your_key"
```

### 3. Cookies配置

抖音等平台需要cookies，放置在：
- 抖音: `~/.claude/douyin_cookies.txt`
- B站: `~/.claude/bilibili_cookies.txt`

## 📖 使用示例

### 基础使用

```bash
# 抓取推文
python webfetch_plus.py "https://x.com/elonmusk/status/123456789"

# 抓取用户信息
python webfetch_plus.py "https://x.com/OpenAI"

# 搜索Twitter
python webfetch_plus.py --search "GPT-4 news"

# 下载抖音视频
python webfetch_plus.py "https://v.douyin.com/xxxxx"
```

### Python API

```python
from webfetch_plus import WebFetchPlus

# 初始化
fetcher = WebFetchPlus()

# 抓取推文
tweet = fetcher.fetch("https://x.com/elonmusk/status/123456789")
print(f"推文内容: {tweet['text']}")
print(f"点赞数: {tweet['metrics']['like_count']}")

# 搜索
results = fetcher.search_twitter("AI", max_results=10)
for tweet in results["results"]:
    print(f"@{tweet['author']['username']}: {tweet['text'][:50]}...")

# 批量抓取
urls = [
    "https://x.com/OpenAI",
    "https://x.com/AnthropicAI",
    "https://v.douyin.com/xxxxx"
]
results = fetcher.batch_fetch(urls)
```

### 高级用法

```python
# 指定策略
from webfetch_plus import FetchStrategy

result = fetcher.fetch(
    "https://example.com",
    strategy=FetchStrategy.FIRECRAWL
)

# 自定义配置
fetcher = WebFetchPlus(config_path="custom_config.json")

# 获取统计
stats = fetcher.get_stats()
print(f"成功率: {stats['success_rate']}")
```

## 🎯 支持的平台

| 平台 | URL示例 | 功能 | 状态 |
|------|---------|------|------|
| Twitter/X | x.com/user/status/id | 推文、用户、搜索 | ✅ |
| 抖音 | v.douyin.com/xxxxx | 视频、图集 | ✅ |
| 知乎 | zhihu.com/question/xxx | 问答、文章、用户、专栏 | ✅ |
| B站 | bilibili.com/video/BV | 视频 | 🚧 |
| 小红书 | xiaohongshu.com/explore | 笔记 | 🚧 |
| YouTube | youtube.com/watch?v= | 视频 | 🚧 |
| 通用网页 | any URL | HTML内容 | ✅ |

## 📊 返回格式

### 标准格式

```json
{
  "content": "主要内容",
  "metadata": {
    "title": "标题",
    "author": "作者",
    "date": "日期"
  },
  "_metadata": {
    "url": "原始URL",
    "strategy": "使用的策略",
    "timestamp": "抓取时间",
    "success": true
  }
}
```

### 错误格式

```json
{
  "error": "错误描述",
  "_metadata": {
    "url": "请求的URL",
    "strategy": "尝试的策略",
    "timestamp": "时间戳",
    "success": false
  }
}
```

## 🐛 故障排除

### 常见问题

1. **Twitter API错误**
   - 检查API密钥
   - 确认未超过频率限制
   - 验证URL格式

2. **抖音下载失败**
   - 更新cookies文件
   - 检查网络连接
   - 确认视频可访问

3. **通用抓取超时**
   - 增加timeout配置
   - 检查代理设置
   - 尝试其他策略

### Debug模式

```bash
# 启用调试输出
python webfetch_plus.py "url" --debug

# 查看详细日志
tail -f ~/.claude/logs/webfetch-plus.log
```

## 📝 开发

### 添加新策略

```python
# 1. 定义策略
class CustomFetcher(BaseFetcher):
    def fetch(self, url, **kwargs):
        # 实现抓取逻辑
        return {"content": "..."}

# 2. 注册URL模式
URLDetector.PATTERNS[FetchStrategy.CUSTOM] = [
    r'custom\.site\.com'
]

# 3. 添加分发逻辑
def _dispatch_fetch(self, url, strategy, **kwargs):
    if strategy == FetchStrategy.CUSTOM:
        return CustomFetcher().fetch(url)
```

### 测试

```bash
# 运行测试
python -m pytest tests/

# 单元测试
python tests/test_twitter.py
python tests/test_router.py
```

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

## 📄 许可

MIT License

## 🔗 相关链接

- [TwitterAPI.io文档](https://docs.twitterapi.io)
- [Firecrawl文档](https://docs.firecrawl.dev)
- [Claude Skills开发指南](https://claude.ai/docs/skills)

## 📈 路线图

- [x] Twitter/X支持
- [x] 抖音支持
- [x] 智能路由
- [x] 知乎支持（问答、文章、用户、专栏）
- [ ] Firecrawl完整集成
- [ ] B站视频下载
- [ ] 小红书内容
- [ ] YouTube支持
- [ ] 异步处理
- [ ] Web UI
- [ ] API服务器模式

## 💡 提示

- 使用`--json`获取结构化输出
- 批量处理可提高效率
- 合理设置缓存减少重复请求
- 遵守各平台的使用条款

---

Made with ❤️ by Claude