---
name: telegram-bobo
description: "获取 Telegram 勃勃投资群聊天记录并用 AI 总结。支持时间范围和话题过滤。"
---

# Telegram 勃勃投资群监控

获取 Telegram "勃勃的美股投资日报会员群" 的聊天记录，并使用 AI 总结。

## When to Use

当用户想要获取勃勃投资群消息时：

- "/telegram-bobo" - 获取最近 1 小时消息并总结
- "帮我看看勃勃群最近在聊什么"
- "总结一下投资群的讨论"

## 前置条件

1. 需要 telethon 库：
```bash
pip install telethon pytz requests
```

2. **首次使用需要登录**（在终端中运行）：
```bash
python3 ~/.claude/skills/telegram-bobo/scripts/login.py
```
输入收到的验证码完成登录，之后 session 会保存下来。

## Workflow

### 快速获取

```bash
python3 ~/.claude/skills/telegram-bobo/scripts/fetch_and_summarize.py
```

### 指定时间范围

```bash
# 最近 2 小时
python3 ~/.claude/skills/telegram-bobo/scripts/fetch_and_summarize.py --hours 2

# 最近 24 小时
python3 ~/.claude/skills/telegram-bobo/scripts/fetch_and_summarize.py --hours 24
```

### 列出话题

```bash
python3 ~/.claude/skills/telegram-bobo/scripts/fetch_and_summarize.py --list-topics
```

### 指定话题

```bash
python3 ~/.claude/skills/telegram-bobo/scripts/fetch_and_summarize.py --topic "美股"
```

## Output

- 原始消息: `~/Downloads/telegram_bobo/bobo_YYYYMMDD_HHMM.txt`
- AI 总结: `~/Downloads/telegram_bobo/bobo_YYYYMMDD_HHMM_summary.md`

## 定时任务 (可选)

每小时自动获取，添加 crontab：

```bash
crontab -e
```

添加：
```
0 * * * * /usr/bin/python3 ~/.claude/skills/telegram-bobo/scripts/fetch_and_summarize.py >> ~/Downloads/telegram_bobo/cron.log 2>&1
```

## 配置

Telegram API 凭证已内置：
- API_ID: 26421064
- Channel: 勃勃的美股投资日报会员群

Session 文件位置: `~/.claude/skills/telegram-bobo/session/`

首次运行会自动从 `~/usr/projects/broker/session_name.session` 复制现有 session。
