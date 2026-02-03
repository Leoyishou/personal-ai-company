---
name: x-post
description: "发送推文到 X (Twitter)。支持纯文本推文和带图片的推文，使用 X API v2。"
---

# X (Twitter) 发推 Skill

通过 X API v2 发送推文，支持纯文本和图片。

## 使用场景

当用户想要发推文、发 Twitter、发 X 时使用此 skill：

- "帮我发一条推文..."
- "发到 Twitter/X 上..."
- "发推: ..."
- "/x-post 内容"

## 命令格式

```bash
python3 /Users/liuyishou/.claude/skills/x-post/scripts/x_post.py "推文内容" [OPTIONS]
```

## 参数

| 参数 | 简写 | 说明 |
|------|------|------|
| `text` | - | 推文内容（必填） |
| `--images` | `-i` | 图片路径，支持多张（最多4张） |

## 使用示例

1. **发送纯文本推文**

```bash
python3 /Users/liuyishou/.claude/skills/x-post/scripts/x_post.py "今天天气真好！"
```

2. **发送带图片的推文**

```bash
python3 /Users/liuyishou/.claude/skills/x-post/scripts/x_post.py "看看这张照片" -i /path/to/image.jpg
```

3. **发送多张图片**

```bash
python3 /Users/liuyishou/.claude/skills/x-post/scripts/x_post.py "今日分享" -i img1.jpg img2.jpg img3.jpg
```

## 注意事项

- 推文内容最多 280 字符
- 图片最多 4 张
- 支持 JPG、PNG、GIF 格式
- API 限制：每 15 分钟最多 100 条推文

## 账号信息

- 用户名: liuysh2
- API 凭证已内置，无需额外配置
