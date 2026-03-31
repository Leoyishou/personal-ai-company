---
name: webfetch-plus
shortname: 🌐 webfetch+
description: 智能网页内容抓取工具，根据URL自动选择最佳抓取策略
version: 1.0.0
author: Claude
tags: [fetch, scraper, twitter, social-media, firecrawl, api]
---

# WebFetchPlus - 智能网页内容抓取工具

## 功能概述

WebFetchPlus 是一个强大的智能网页抓取工具，能够根据URL类型自动选择最佳的抓取策略：

- 🐦 **Twitter/X**: 使用 TwitterAPI.io 获取推文、用户信息、时间线
- 🔥 **Firecrawl**: 通用网页内容智能提取
- 🎵 **抖音**: 视频、图片、音频下载
- 📺 **B站**: 视频内容抓取
- 📝 **小红书**: 笔记内容获取
- 🌐 **通用抓取**: 任意网页内容

## 核心特性

### 智能路由
- 自动识别URL类型
- 选择最优抓取策略
- 失败自动降级

### 多源支持
- Twitter/X (推文、用户、搜索)
- 抖音 (视频、图集、直播)
- B站 (视频、番剧)
- 小红书 (笔记、用户)
- YouTube
- 通用网页

### 统一接口
- 一致的调用方式
- 标准化的返回格式
- 完整的元数据

## 使用方法

### 命令行使用

```bash
# 自动识别并抓取
skill webfetch-plus "https://x.com/elonmusk/status/123456789"

# 抓取抖音视频
skill webfetch-plus "https://v.douyin.com/xxxxx"

# 搜索Twitter
skill webfetch-plus --search "AI news"

# 批量抓取
skill webfetch-plus --batch urls.txt

# 指定策略
skill webfetch-plus "https://example.com" --strategy firecrawl

# JSON输出
skill webfetch-plus "https://x.com/OpenAI" --json
```

### Python调用

```python
from webfetch_plus import WebFetchPlus

# 初始化
fetcher = WebFetchPlus()

# 抓取推文
result = fetcher.fetch("https://x.com/elonmusk/status/123456789")
print(result["text"])
print(result["author"]["username"])

# 搜索Twitter
results = fetcher.search_twitter("GPT-4", max_results=20)
for tweet in results["results"]:
    print(f"@{tweet['author']['username']}: {tweet['text']}")

# 批量抓取
urls = ["url1", "url2", "url3"]
results = fetcher.batch_fetch(urls)

# 获取用户信息
user = fetcher.fetch("https://x.com/OpenAI")
print(f"{user['name']} - {user['metrics']['followers_count']} followers")
```

## 返回格式

### Twitter推文
```json
{
  "id": "123456789",
  "text": "推文内容",
  "created_at": "2024-01-28T10:00:00Z",
  "author": {
    "name": "Elon Musk",
    "username": "elonmusk",
    "verified": true
  },
  "metrics": {
    "like_count": 10000,
    "retweet_count": 5000,
    "reply_count": 1000
  },
  "media": [...],
  "_metadata": {
    "url": "原始URL",
    "strategy": "twitter_api",
    "timestamp": "抓取时间",
    "success": true
  }
}
```

### 抖音视频
```json
{
  "title": "视频标题",
  "author": "作者名",
  "video_url": "视频地址",
  "cover_url": "封面地址",
  "stats": {
    "likes": 10000,
    "comments": 500,
    "shares": 200
  },
  "_metadata": {...}
}
```

## 策略说明

### TwitterAPI.io
- **优势**: 无需官方API密钥，稳定可靠
- **功能**: 推文、用户、搜索、时间线
- **限制**: 有请求频率限制

### Firecrawl
- **优势**: 智能提取，自动解析
- **功能**: 文章、产品、文档
- **适用**: 结构化网页内容

### 社交媒体
- **抖音**: 需要cookies（自动读取）
- **B站**: 公开视频直接下载
- **小红书**: 需要登录状态

### 通用抓取
- **降级方案**: 其他策略失败时使用
- **基础HTTP**: 获取原始HTML

## 配置文件

配置文件位置：`~/.claude/skills/webfetch-plus/config.json`

```json
{
  "twitter_api_key": "your_key",
  "firecrawl_api_key": "your_key",
  "proxy": null,
  "timeout": 30,
  "max_retries": 3,
  "save_path": "~/webfetch_downloads",
  "debug": false,
  "strategies": {
    "twitter": {
      "enabled": true,
      "api_base": "https://api.twitterapi.io"
    },
    "firecrawl": {
      "enabled": false,
      "api_base": "https://api.firecrawl.dev"
    },
    "douyin": {
      "enabled": true,
      "use_cookies": true
    }
  }
}
```

## 环境变量

支持通过环境变量配置：

```bash
export TWITTER_API_KEY="your_twitter_api_key"
export FIRECRAWL_API_KEY="your_firecrawl_api_key"
export WEBFETCH_PROXY="http://proxy:port"
```

## 高级功能

### 自定义策略
```python
# 添加自定义抓取策略
from webfetch_plus import WebFetchPlus, FetchStrategy

fetcher = WebFetchPlus()
fetcher.add_strategy(
    FetchStrategy.CUSTOM,
    patterns=[r'custom\.site\.com'],
    handler=my_custom_handler
)
```

### 中间件支持
```python
# 添加请求中间件
def auth_middleware(request):
    request.headers["Authorization"] = "Bearer token"
    return request

fetcher.add_middleware(auth_middleware)
```

### 缓存控制
```python
# 启用缓存
fetcher.enable_cache(ttl=3600)  # 1小时缓存

# 清除缓存
fetcher.clear_cache()
```

## 错误处理

所有错误都会在返回的JSON中包含`error`字段：

```json
{
  "error": "错误描述",
  "_metadata": {
    "url": "请求的URL",
    "strategy": "使用的策略",
    "timestamp": "时间戳",
    "success": false
  }
}
```

## 统计信息

获取抓取统计：

```bash
skill webfetch-plus --stats
```

输出：
```json
{
  "total_fetches": 100,
  "success": 95,
  "failed": 5,
  "success_rate": "95.0%"
}
```

## 注意事项

1. **API密钥**: Twitter API需要配置密钥
2. **频率限制**: 注意各平台的请求限制
3. **登录状态**: 某些平台需要cookies
4. **代理设置**: 部分网站可能需要代理
5. **内容版权**: 尊重内容版权和使用条款

## 故障排除

### Twitter抓取失败
- 检查API密钥是否正确
- 确认URL格式正确
- 查看是否触发频率限制

### 抖音下载失败
- 确认cookies文件存在
- 检查cookies是否过期
- 尝试更新cookies

### 通用抓取问题
- 检查网络连接
- 尝试设置代理
- 查看debug日志

## 更新日志

### v1.0.0 (2024-01)
- 初始版本发布
- 支持Twitter/X抓取
- 集成抖音下载
- 智能路由系统
- 统一接口设计

## 开发计划

- [ ] 完善Firecrawl集成
- [ ] 添加B站视频下载
- [ ] 实现小红书抓取
- [ ] 支持YouTube
- [ ] 添加异步处理
- [ ] 实现结果缓存
- [ ] Web UI界面