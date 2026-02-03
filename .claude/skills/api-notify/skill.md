---
name: notify
description: "统一通知服务 - 支持 Mac 通知、Telegram、未来可扩展更多渠道"
allowed-tools: Bash(python:*), Read, Write
---

# Notify - 统一通知服务

跨渠道发送通知，支持 Mac 桌面通知、Telegram 等多种方式。

## 使用方式

### Python 调用

```python
from notify import send_notification

# 发送到所有渠道
send_notification("标题", "消息内容")

# 指定渠道
send_notification("标题", "消息内容", channels=["mac", "telegram"])

# 只发 Mac
send_notification("标题", "消息内容", channels=["mac"])

# 只发 Telegram
send_notification("标题", "消息内容", channels=["telegram"])
```

### 命令行调用

```bash
# 发送到所有渠道
python3 ~/.claude/skills/notify/scripts/notify.py --title "标题" --message "内容"

# 指定渠道
python3 ~/.claude/skills/notify/scripts/notify.py --title "标题" --message "内容" --channels mac telegram
```

## 支持的渠道

| 渠道 | 说明 | 状态 |
|------|------|------|
| `mac` | Mac 桌面通知 (terminal-notifier) | ✅ |
| `telegram` | Telegram Saved Messages | ✅ |
| `slack` | Slack Webhook | 🔜 |
| `discord` | Discord Webhook | 🔜 |
| `email` | 邮件通知 | 🔜 |

## 配置

通知配置存储在 `~/.claude/skills/notify/config.json`：

```json
{
  "default_channels": ["mac", "telegram"],
  "telegram": {
    "api_id": "xxx",
    "api_hash": "xxx",
    "session_path": "~/.claude/skills/KOL-info-collect/session/bobo"
  },
  "mac": {
    "sound": "Glass"
  }
}
```

## 环境变量

无需额外配置，复用现有凭证。
