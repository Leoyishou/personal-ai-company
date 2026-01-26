---
name: social-media-download
description: "下载社交媒体内容（小红书、X/Twitter、抖音），包括视频、图片、元数据和评论。支持短链接解析，确保获取用户视角一致的所有内容。"
---

# 社媒下载 Skill

统一下载小红书、X (Twitter) 和抖音的内容，包括视频、图片、元数据和评论。

## 触发条件

当用户提到以下意图时使用此 skill：
- "下载这个小红书/推特/X/抖音"
- "保存社媒内容"
- "抓取推文/笔记/抖音视频"
- 提供了 `xhslink.com`、`xiaohongshu.com`、`x.com`、`twitter.com`、`v.douyin.com`、`douyin.com` 链接
- 提供了抖音分享文本（如 "8.76 复制打开抖音..."）

## 支持平台

| 平台 | 视频 | 图片 | 评论 | 元数据 |
|------|------|------|------|--------|
| 小红书 | ✅ | ✅ | ✅ (需 MCP) | ✅ |
| X (Twitter) | ✅ | ✅ | ✅ | ✅ |
| 抖音 (Douyin) | ✅ | ❌ | ❌ | ❌ |

## 快速使用

### 自动识别平台

```bash
# 解析链接（自动识别平台）
python3 ~/.claude/skills/social-media-download/scripts/social_download.py parse "<URL>" --json

# 下载内容（自动识别平台）
python3 ~/.claude/skills/social-media-download/scripts/social_download.py download "<URL>" -o ~/Downloads
```

### X (Twitter) 专用

```bash
# 用推文 ID 直接下载
python3 ~/.claude/skills/social-media-download/scripts/social_download.py twitter <TWEET_ID> -o ~/Downloads
```

### 小红书专用

```bash
# 下载视频（详情需配合 MCP）
python3 ~/.claude/skills/social-media-download/scripts/social_download.py xiaohongshu "<URL>" -o ~/Downloads
```

### 抖音专用

```bash
# 从分享文本下载
python3 ~/.claude/skills/social-media-download/scripts/social_download.py douyin "8.76 复制打开抖音... https://v.douyin.com/xxx/" -o ~/Downloads

# 从链接下载
python3 ~/.claude/skills/social-media-download/scripts/social_download.py douyin "https://www.douyin.com/video/123456" -o ~/Downloads
```

## 完整工作流程

### 一、X (Twitter)

1. **解析链接**
```bash
python3 ~/.claude/skills/social-media-download/scripts/social_download.py parse "https://x.com/user/status/123" --json
```

2. **下载全部内容**（视频+图片+评论+元数据）
```bash
python3 ~/.claude/skills/social-media-download/scripts/social_download.py download "https://x.com/user/status/123" -o ~/Downloads/tweet
```

输出：
```
~/Downloads/tweet/
├── username_10368kbps.mp4   # 最高质量视频
├── metadata.json            # 完整元数据（含评论）
└── summary.md               # 可读摘要
```

### 二、小红书

小红书需要配合 MCP 获取完整内容：

1. **解析链接**
```bash
python3 ~/.claude/skills/social-media-download/scripts/social_download.py parse "http://xhslink.com/xxx" --json
```

2. **调用 MCP 获取详情**（Claude 执行）
```
mcp__xiaohongshu-mcp__get_feed_detail(
  feed_id="从上一步获取",
  xsec_token="从上一步获取",
  load_all_comments=true
)
```

3. **下载视频**
```bash
python3 ~/.claude/skills/social-media-download/scripts/social_download.py xiaohongshu "<URL>" -o ~/Downloads
```

4. **下载图片**（使用 MCP 返回的 imageList）
```bash
python3 ~/.claude/skills/social-media-download/scripts/social_download.py images \
  --data '<imageList JSON>' \
  -o ~/Downloads \
  -t "<标题>"
```

### 三、抖音

抖音使用 Playwright 无头浏览器下载，支持分享文本和直接链接：

1. **从分享文本下载**
```bash
python3 ~/.claude/skills/social-media-download/scripts/social_download.py douyin \
  "8.76 复制打开抖音，看看【抖音】的作品 https://v.douyin.com/i5tgnBMJ/" \
  -o ~/Downloads/douyin
```

2. **从直接链接下载**
```bash
python3 ~/.claude/skills/social-media-download/scripts/social_download.py douyin \
  "https://www.douyin.com/video/7480014865260760357" \
  -o ~/Downloads/douyin
```

输出：
```
~/Downloads/douyin/
└── 视频标题.mp4   # 完整视频
```

## 命令参考

### parse - 解析链接

```bash
python3 .../social_download.py parse "<URL>" [--json]
```

返回：
- `platform`: 平台类型 (xiaohongshu/twitter/douyin)
- `feed_id` / `tweet_id` / `video_id`: 内容 ID
- `xsec_token`: 小红书访问令牌（如有）
- `full_url`: 完整链接

### download - 下载内容

```bash
python3 .../social_download.py download "<URL>" [-o OUTPUT] [--video-only] [--no-comments]
```

| 参数 | 说明 |
|------|------|
| `-o, --output` | 输出目录 |
| `--video-only` | 仅下载视频 |
| `--no-comments` | 不获取评论 |

### twitter - Twitter 专用

```bash
python3 .../social_download.py twitter <TWEET_ID> [-o OUTPUT]
```

### xiaohongshu - 小红书专用

```bash
python3 .../social_download.py xiaohongshu "<URL>" [-o OUTPUT]
```

### douyin - 抖音专用

```bash
python3 .../social_download.py douyin "<URL或分享文本>" [-o OUTPUT] [-c COOKIES]
```

| 参数 | 说明 |
|------|------|
| `-o, --output` | 输出目录 |
| `-c, --cookies` | Cookies 文件路径（默认 `~/.claude/douyin_cookies.txt`）|

## API 凭证

### X (Twitter)

脚本默认使用内置凭证，也可通过环境变量覆盖：

```bash
export X_API_KEY="your_key"
export X_API_SECRET="your_secret"
export X_ACCESS_TOKEN="your_token"
export X_ACCESS_TOKEN_SECRET="your_token_secret"
```

### 小红书

小红书通过 MCP 访问，需确保 MCP 已登录：
```
mcp__xiaohongshu-mcp__check_login_status
```

### 抖音

抖音使用 Playwright 无头浏览器，支持登录态 Cookies：
- Cookies 文件路径：`~/.claude/douyin_cookies.txt`
- 格式：Netscape HTTP Cookie File（可通过浏览器插件导出）
- 注意：即使没有 Cookies 也可下载公开视频

## 输出格式

### metadata.json

```json
{
  "downloaded_at": "2026-01-26T12:00:00",
  "tweet": { ... },      // Twitter
  "note": { ... },       // 小红书
  "user": { ... },
  "media": [ ... ],
  "replies": [ ... ]     // 评论
}
```

### summary.md

人类可读的摘要，包含：
- 基本信息（作者、时间、互动数据）
- 正文内容
- 下载时间

## 依赖

```bash
pip install requests requests-oauthlib playwright
playwright install chromium
```

- `requests-oauthlib`: X (Twitter) API 认证
- `playwright`: 抖音视频下载（无头浏览器）
- `yt-dlp`: 小红书视频下载（会自动安装）

## 故障排查

| 问题 | 解决方案 |
|------|---------|
| Twitter 401 | 检查 API 凭证是否有效 |
| 小红书 404 | 笔记可能已删除或私密 |
| 小红书无视频 | 确保 URL 包含 xsec_token |
| 抖音页面超时 | 检查网络连接，增加等待时间 |
| 抖音无法获取视频 URL | 视频可能有地区限制或已删除 |
| Playwright 未安装 | 运行 `pip install playwright && playwright install chromium` |
| 下载超时 | 检查网络，重试 |

## 相关 Skill

- `xiaohongshu-download`: 旧版小红书专用 skill（已合并）
- `video-downloader-skill`: 通用视频下载
