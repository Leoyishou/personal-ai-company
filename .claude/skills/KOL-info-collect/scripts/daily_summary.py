#!/usr/bin/env python3
"""
Telegram 勃勃投资群 - 每日增量总结脚本
每 2 小时运行一次，按天维度生成文档
"""
import asyncio
import os
import sys
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from pathlib import Path
import pytz

try:
    from telethon import TelegramClient
    from telethon.tl.functions.messages import GetHistoryRequest
except ImportError:
    print("请先安装 telethon: pip install telethon pytz requests")
    sys.exit(1)

# 配置
API_ID = '26421064'
API_HASH = '3cdcc576ab22d6b0ecdbf5d49bdb1502'
CHANNEL_USERNAME = '勃勃的美股投资日报会员群'
SESSION_PATH = os.path.expanduser('~/.claude/skills/telegram-bobo/session/bobo')

# 输出目录
OUTPUT_DIR = Path('/Users/liuyishou/usr/projects/odyssey/src/0 收集箱/投资')

# OpenRouter API
OPENROUTER_API_KEY = os.environ.get(
    'OPENROUTER_API_KEY',
    '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'
)
OPENROUTER_MODEL = 'google/gemini-2.0-flash-001'

BEIJING_TZ = pytz.timezone('Asia/Shanghai')


class Message:
    def __init__(self, date: datetime, message: str, sender: str = ""):
        self.date = date
        self.message = message
        self.sender = sender


async def fetch_messages(client, hours: int = 2) -> List[Message]:
    """获取指定时间范围内的消息"""
    dialogs = await client.get_dialogs()
    target_channel = next((d for d in dialogs if d.name == CHANNEL_USERNAME), None)

    if not target_channel:
        print(f"❌ 未找到频道: {CHANNEL_USERNAME}")
        return []

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=hours)

    messages = []
    offset_id = 0
    limit = 100
    reached_end = False

    while not reached_end:
        history = await client(GetHistoryRequest(
            peer=target_channel,
            limit=limit,
            offset_date=None,
            offset_id=offset_id,
            max_id=0,
            min_id=0,
            add_offset=0,
            hash=0
        ))

        if not history.messages:
            break

        for msg in history.messages:
            msg_date = msg.date.replace(tzinfo=timezone.utc)
            msg_text = msg.message if msg.message else ""

            if msg_date < start_time:
                reached_end = True
                break

            if msg_text.strip():
                sender = ""
                if hasattr(msg, 'from_id') and msg.from_id:
                    try:
                        entity = await client.get_entity(msg.from_id)
                        sender = getattr(entity, 'first_name', '') or getattr(entity, 'title', '')
                    except:
                        pass

                messages.append(Message(date=msg_date, message=msg_text, sender=sender))

        if reached_end or len(history.messages) < limit:
            break

        offset_id = history.messages[-1].id

    return messages


def summarize_with_ai(messages: List[Message], time_range: str) -> str:
    """使用 AI 总结消息"""
    if not messages:
        return "没有新消息"

    chat_log = "\n".join([
        f"[{msg.date.astimezone(BEIJING_TZ).strftime('%H:%M')}] {msg.sender}: {msg.message}"
        for msg in sorted(messages, key=lambda x: x.date)
    ])

    prompt = f"""总结这段时间 ({time_range}) 的投资群讨论，包括：
1. 主要话题和观点
2. 提到的股票/公司（单独列出）
3. 重要的投资建议或市场判断

聊天记录:
{chat_log}"""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"AI 总结失败: {e}"


async def main(hours: int = 2):
    """主函数"""
    session_dir = os.path.dirname(SESSION_PATH)
    os.makedirs(session_dir, exist_ok=True)

    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            print("❌ 未登录，请先运行登录脚本")
            return

        print(f"✓ 已连接 Telegram")

        # 获取消息
        print(f"📥 正在获取最近 {hours} 小时的消息...")
        messages = await fetch_messages(client, hours=hours)

        if not messages:
            print("没有新消息")
            return

        print(f"✓ 获取到 {len(messages)} 条消息")

        # 确保输出目录存在
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # 按天命名文件
        now = datetime.now(BEIJING_TZ)
        today_str = now.strftime('%Y-%m-%d')
        filename = f"{today_str}_勃勃投资群.md"
        filepath = OUTPUT_DIR / filename

        # 时间范围
        time_range = f"{(now - timedelta(hours=hours)).strftime('%H:%M')} - {now.strftime('%H:%M')}"

        # AI 总结
        print(f"🤖 正在生成 AI 总结...")
        summary = summarize_with_ai(messages, time_range)

        # 写入文件（增量追加）
        is_new_file = not filepath.exists()

        with open(filepath, 'a', encoding='utf-8') as f:
            if is_new_file:
                f.write(f"# {today_str} 勃勃投资群总结\n\n")

            f.write(f"## {time_range} ({len(messages)} 条消息)\n\n")
            f.write(summary)
            f.write("\n\n---\n\n")

        print(f"✓ 已{'创建' if is_new_file else '追加到'}: {filepath}")

    finally:
        await client.disconnect()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='勃勃投资群每日增量总结')
    parser.add_argument('--hours', type=int, default=2, help='获取最近 N 小时的消息 (默认: 2)')
    args = parser.parse_args()

    asyncio.run(main(hours=args.hours))
