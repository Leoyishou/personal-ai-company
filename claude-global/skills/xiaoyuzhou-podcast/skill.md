---
name: xiaoyuzhou-podcast
description: Use when user shares a xiaoyuzhoufm.com link, mentions downloading a podcast episode, or wants to transcribe podcast audio to text
---

# 小宇宙播客下载与转录

从小宇宙 FM 下载播客音频，可选转录为文字。

## 一、快速参考

```bash
SCRIPT=~/.claude/skills/xiaoyuzhou-podcast/scripts/xyz_download.py

# 仅查看元数据
python3 $SCRIPT "<URL>" --info-only --json

# 下载音频
python3 $SCRIPT "<URL>" -o ~/tmp

# 下载并转文字（组合 api-asr skill）
python3 $SCRIPT "<URL>" -o ~/tmp
# 然后用 api-asr skill 转录下载的 .m4a 文件
```

## 二、支持的 URL 格式

| 格式 | 示例 |
|------|------|
| Episode 页面 | `https://www.xiaoyuzhoufm.com/episode/{eid}` |
| 纯 Episode ID | `622b585e129436aac42f7fd2` |

## 三、输出

```
~/tmp/
├── 标题.m4a              # 音频文件
└── 标题_metadata.json    # 元数据（标题、描述、时间线、播客信息）
```

元数据包含：`title`, `description`(含时间线), `shownotes`(HTML), `audio_url`, `duration_min`, `podcast.title`, `podcast.author`

## 四、完整流程（下载 + 转录）

1. 下载音频：`python3 $SCRIPT "<URL>" -o ~/tmp`
2. 调用 `api-asr` skill 转录 .m4a 文件
3. 输出：时间戳逐句文字稿

## 五、技术细节

- CDN: `media.xyzcdn.net`，格式 `.m4a`，无需认证
- 数据提取自页面 `__NEXT_DATA__`（Next.js SSR）
- 备用方案：正则匹配 `.m4a` URL
- 无需 API key，无需登录
