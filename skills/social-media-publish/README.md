# Social Media Publish

一个 Claude Code Skill，帮你完成社交媒体（X、小红书、B站）的发布工作。

## 支持平台

| 平台 | 内容类型 | 限制 |
|------|----------|------|
| **X (Twitter)** | 文字 + 图片 | 280字符，4张图 |
| **小红书** | 图文 / 视频 | 标题20字，正文1000字 |
| **B站** | 视频 | 标题80字 |

## 安装

将此目录放到 `~/.claude/skills/social-media-publish/`

## 快速开始

### 检查登录状态

```bash
python3 ~/.claude/skills/social-media-publish/scripts/publish.py status
```

### 发布到 X

```bash
python3 scripts/publish.py x "今天天气真好！"
python3 scripts/publish.py x "看图" -i image.jpg
```

### 发布到小红书

```bash
python3 scripts/publish.py xhs \
  -t "标题" \
  -c "正文内容" \
  --tags "标签1,标签2" \
  --images cover.jpg
```

### 发布到 B站

```bash
python3 scripts/publish.py bilibili video.mp4 \
  -t "视频标题" \
  -d "视频简介" \
  --tid 231
```

## 在 Claude Code 中使用

直接对 Claude 说：

- "发推：今天天气真好"
- "帮我发到小红书"
- "上传这个视频到B站"
- "多平台发布这段内容"

## 前置依赖

### X (Twitter)
- 需要配置 API 密钥（环境变量或 .env 文件）

### 小红书
- 需要运行 [xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp) 服务
- 首次使用需扫码登录

### B站
- 需要安装 [biliup](https://github.com/biliup/biliup)：`pip install biliup`
- 首次使用需扫码登录：`biliup login`

## 许可证

MIT
