#!/usr/bin/env python3
"""
Telegram 勃勃投资群消息获取与总结脚本
每小时获取群聊消息并使用 AI 总结
"""
import asyncio
import os
import sys
import json
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import pytz

# 尝试导入 telethon
try:
    from telethon import TelegramClient
    from telethon.tl.functions.messages import GetForumTopicsRequest, GetHistoryRequest
except ImportError:
    print("请先安装 telethon: pip install telethon")
    sys.exit(1)

# 配置
API_ID = '26421064'
API_HASH = '3cdcc576ab22d6b0ecdbf5d49bdb1502'
PHONE = '+8613167265302'
CHANNEL_USERNAME = '勃勃的美股投资日报会员群'
# 使用 skill 目录的 session
SESSION_PATH = os.path.expanduser('~/.claude/skills/telegram-bobo/session/bobo')

# OpenRouter API 配置 (用于 AI 总结)
OPENROUTER_API_KEY = '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'
OPENROUTER_MODEL = 'google/gemini-2.0-flash-001'

# 时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

class Message:
    def __init__(self, date: datetime, message: str, sender: str = ""):
        self.date = date
        self.message = message
        self.sender = sender


async def get_topics(client) -> List[dict]:
    """获取群内所有话题"""
    dialogs = await client.get_dialogs()
    target_channel = next((d for d in dialogs if d.name == CHANNEL_USERNAME), None)

    if not target_channel:
        print(f"❌ 未找到频道: {CHANNEL_USERNAME}")
        return []

    topics = await client(GetForumTopicsRequest(
        channel=target_channel,
        offset_date=None,
        offset_id=0,
        offset_topic=0,
        limit=1000
    ))

    return [{"id": topic.id, "title": topic.title} for topic in topics.topics]


async def fetch_messages(
    client,
    topic_id: Optional[int] = None,
    hours: int = 1
) -> List[Message]:
    """获取指定时间范围内的消息"""
    dialogs = await client.get_dialogs()
    target_channel = next((d for d in dialogs if d.name == CHANNEL_USERNAME), None)

    if not target_channel:
        print(f"❌ 未找到频道: {CHANNEL_USERNAME}")
        return []

    # 计算时间范围
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

            # 超出时间范围
            if msg_date < start_time:
                reached_end = True
                break

            # 在时间范围内
            if msg_text.strip():  # 忽略空消息
                # 检查 topic 过滤
                if topic_id is None or (
                    hasattr(msg, 'reply_to') and
                    msg.reply_to and
                    getattr(msg.reply_to, 'forum_topic', False) and
                    (msg.reply_to.reply_to_msg_id == topic_id or
                     getattr(msg.reply_to, 'reply_to_top_id', None) == topic_id)
                ):
                    # 获取发送者名称
                    sender = ""
                    if hasattr(msg, 'from_id') and msg.from_id:
                        try:
                            entity = await client.get_entity(msg.from_id)
                            sender = getattr(entity, 'first_name', '') or getattr(entity, 'title', '')
                        except:
                            pass

                    messages.append(Message(
                        date=msg_date,
                        message=msg_text,
                        sender=sender
                    ))

        if reached_end or len(history.messages) < limit:
            break

        offset_id = history.messages[-1].id

    return messages


def summarize_with_ai(messages: List[Message]) -> str:
    """使用 OpenRouter API 总结消息"""
    if not messages:
        return "没有消息需要总结"

    # 构建聊天记录文本
    chat_log = "\n".join([
        f"[{msg.date.astimezone(BEIJING_TZ).strftime('%H:%M')}] {msg.sender}: {msg.message}"
        for msg in messages
    ])

    prompt = f"""帮我总结一下他们讨论的话题和观点，详细一些，如果有提到什么公司的股票的话，要单独列出来。

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
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        return f"AI 总结失败: {e}"


async def main(hours: int = 1, topic_name: Optional[str] = None, list_topics: bool = False):
    """主函数"""
    # 确保 session 目录存在
    session_dir = os.path.dirname(SESSION_PATH)
    os.makedirs(session_dir, exist_ok=True)

    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            print("❌ 未登录，请先运行: python3 ~/.claude/skills/telegram-bobo/scripts/login.py --send-code")
            await client.disconnect()
            return
        print(f"✓ 已连接 Telegram")

        # 列出话题
        if list_topics:
            topics = await get_topics(client)
            print(f"\n📋 {CHANNEL_USERNAME} 话题列表:")
            for t in topics:
                print(f"  - [{t['id']}] {t['title']}")
            return

        # 查找话题 ID
        topic_id = None
        if topic_name:
            topics = await get_topics(client)
            for t in topics:
                if topic_name.lower() in t['title'].lower():
                    topic_id = t['id']
                    print(f"✓ 找到话题: {t['title']} (ID: {topic_id})")
                    break
            if not topic_id:
                print(f"⚠️ 未找到匹配 '{topic_name}' 的话题，将获取所有消息")

        # 获取消息
        print(f"\n📥 正在获取最近 {hours} 小时的消息...")
        messages = await fetch_messages(client, topic_id=topic_id, hours=hours)

        if not messages:
            print("没有找到消息")
            return

        print(f"✓ 获取到 {len(messages)} 条消息")

        # 保存原始消息
        now = datetime.now(BEIJING_TZ)
        output_dir = os.path.expanduser('~/Downloads/telegram_bobo')
        os.makedirs(output_dir, exist_ok=True)

        filename = f"bobo_{now.strftime('%Y%m%d_%H%M')}.txt"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"勃勃投资群消息 - {now.strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"时间范围: 最近 {hours} 小时\n")
            f.write(f"消息数量: {len(messages)}\n")
            f.write("=" * 50 + "\n\n")

            for msg in sorted(messages, key=lambda x: x.date):
                f.write(f"[{msg.date.astimezone(BEIJING_TZ).strftime('%H:%M')}] {msg.sender}: {msg.message}\n\n")

        print(f"✓ 消息已保存到: {filepath}")

        # AI 总结
        print(f"\n🤖 正在生成 AI 总结...")
        summary = summarize_with_ai(messages)

        # 保存总结
        summary_file = filepath.replace('.txt', '_summary.md')
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"# 勃勃投资群消息总结\n\n")
            f.write(f"**时间**: {now.strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"**范围**: 最近 {hours} 小时\n")
            f.write(f"**消息数**: {len(messages)}\n\n")
            f.write("---\n\n")
            f.write(summary)

        print(f"✓ 总结已保存到: {summary_file}")

        # 输出总结
        print("\n" + "=" * 50)
        print("📊 消息总结")
        print("=" * 50)
        print(summary)

    finally:
        await client.disconnect()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='获取勃勃投资群消息并总结')
    parser.add_argument('--hours', type=int, default=1, help='获取最近 N 小时的消息 (默认: 1)')
    parser.add_argument('--topic', type=str, help='指定话题名称 (模糊匹配)')
    parser.add_argument('--list-topics', action='store_true', help='列出所有话题')

    args = parser.parse_args()

    asyncio.run(main(
        hours=args.hours,
        topic_name=args.topic,
        list_topics=args.list_topics
    ))
