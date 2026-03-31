#!/usr/bin/env python3
"""
Telegram 定时拉取脚本
白天 (8:00-22:00): 每 2 小时拉取，获取 2 小时内消息
夜间 (03:00): 每 5 小时拉取，获取 5 小时内消息

功能：
- 拉取勃勃投资群消息
- AI 总结
- 存入 Supabase
- Mac 通知
- Telegram Saved Messages 推送
"""
import asyncio
import os
import sys
import json
import subprocess
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import pytz

try:
    from telethon import TelegramClient
    from telethon.tl.functions.messages import GetHistoryRequest
except ImportError:
    print("请先安装 telethon: pip install telethon")
    sys.exit(1)

# 配置
API_ID = '26421064'
API_HASH = '3cdcc576ab22d6b0ecdbf5d49bdb1502'
SESSION_PATH = os.path.expanduser('~/.claude/skills/KOL-info-collect/session/bobo')
CHANNEL_USERNAME = '勃勃的美股投资日报会员群'

# API
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
SUPABASE_ACCESS_TOKEN = os.environ.get('SUPABASE_ACCESS_TOKEN', '')
PDC_PROJECT_ID = 'mwvsdfalfqblbqwnyqpn'

BEIJING_TZ = pytz.timezone('Asia/Shanghai')


def get_hours_to_fetch():
    """根据当前时间决定拉取多少小时的消息"""
    now = datetime.now(BEIJING_TZ)
    hour = now.hour

    if 8 <= hour < 22:
        return 2  # 白天: 2小时
    else:
        return 5  # 夜间: 5小时


async def fetch_messages(client, hours: int) -> List[dict]:
    """获取指定时间范围内的消息"""
    dialogs = await client.get_dialogs()
    target = next((d for d in dialogs if d.name == CHANNEL_USERNAME), None)

    if not target:
        print(f"未找到频道: {CHANNEL_USERNAME}")
        return []

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=hours)

    messages = []
    offset_id = 0

    while True:
        history = await client(GetHistoryRequest(
            peer=target,
            limit=100,
            offset_date=None,
            offset_id=offset_id,
            max_id=0, min_id=0, add_offset=0, hash=0
        ))

        if not history.messages:
            break

        for msg in history.messages:
            msg_date = msg.date.replace(tzinfo=timezone.utc)
            if msg_date < start_time:
                return messages

            if msg.message and msg.message.strip():
                sender = ""
                if hasattr(msg, 'from_id') and msg.from_id:
                    try:
                        entity = await client.get_entity(msg.from_id)
                        sender = getattr(entity, 'first_name', '') or ''
                    except:
                        pass

                messages.append({
                    "time": msg_date.astimezone(BEIJING_TZ).strftime('%Y-%m-%d %H:%M'),
                    "sender": sender,
                    "content": msg.message
                })

        offset_id = history.messages[-1].id

    return messages


def summarize_with_ai(messages: List[dict]) -> str:
    """AI 总结"""
    if not messages or not OPENROUTER_API_KEY:
        return ""

    chat_log = "\n".join([
        f"[{m['time']}] {m['sender']}: {m['content'][:500]}"
        for m in messages[:100]
    ])

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "google/gemini-2.0-flash-001",
                "messages": [{
                    "role": "user",
                    "content": f"总结这段投资群聊天的主要话题和观点，如有提到股票代码请列出：\n\n{chat_log}"
                }],
                "max_tokens": 500
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"AI 总结失败: {e}")

    return ""


# 导入统一通知服务
sys.path.insert(0, os.path.expanduser('~/.claude/skills/notify/scripts'))
from notify import NotifyService

# 全局通知服务实例
_notify_service = None

def get_notify_service():
    global _notify_service
    if _notify_service is None:
        _notify_service = NotifyService()
    return _notify_service


async def send_notifications(client, summary: str, msg_count: int, hours: int):
    """发送通知到所有渠道"""
    now = datetime.now(BEIJING_TZ)
    title = f"勃勃群摘要 ({msg_count}条)"
    message = f"""📊 勃勃投资群定时摘要

⏰ {now.strftime('%Y-%m-%d %H:%M')}
📨 最近 {hours} 小时 | {msg_count} 条消息

{summary[:3000]}
"""

    # Mac 通知
    service = get_notify_service()
    mac_result = service.send_mac(title, summary[:150])
    print(f"mac 通知{'已发送' if mac_result else '失败'}")

    # Telegram 通知（复用已有的 client）
    try:
        await client.send_message('me', f"🔔 **{title}**\n\n{message}")
        print("telegram 通知已发送")
    except Exception as e:
        print(f"telegram 通知失败: {e}")


def save_to_supabase(data: dict) -> bool:
    """保存到 Supabase"""
    if not SUPABASE_ACCESS_TOKEN:
        return False

    def escape_sql(s):
        if s is None:
            return "NULL"
        return "'" + str(s).replace("'", "''").replace("\\", "\\\\") + "'"

    query = f"""
    INSERT INTO telegram_messages (fetch_time, channel_name, hours_fetched, message_count, messages, ai_summary)
    VALUES (
        NOW(),
        {escape_sql(data['channel'])},
        {data['hours']},
        {data['count']},
        {escape_sql(json.dumps(data['messages'], ensure_ascii=False))}::jsonb,
        {escape_sql(data['summary'])}
    );
    """

    try:
        response = requests.post(
            f"https://api.supabase.com/v1/projects/{PDC_PROJECT_ID}/database/query",
            headers={
                "Authorization": f"Bearer {SUPABASE_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            },
            json={"query": query},
            timeout=30
        )
        return response.status_code in (200, 201)
    except:
        return False


async def main():
    hours = get_hours_to_fetch()
    now = datetime.now(BEIJING_TZ)
    print(f"[{now.strftime('%Y-%m-%d %H:%M')}] 开始拉取最近 {hours} 小时的消息...")

    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            print("未登录 Telegram")
            return

        messages = await fetch_messages(client, hours)
        print(f"获取到 {len(messages)} 条消息")

        if not messages:
            return

        # AI 总结
        summary = summarize_with_ai(messages)

        # 保存到数据库
        data = {
            "channel": CHANNEL_USERNAME,
            "hours": hours,
            "count": len(messages),
            "messages": messages,
            "summary": summary
        }

        if save_to_supabase(data):
            print("已保存到 Supabase")
        else:
            print("Supabase 保存失败，保存到本地文件")
            # 保存到本地
            output_dir = os.path.expanduser('~/Downloads/telegram_bobo')
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, f"bobo_{now.strftime('%Y%m%d_%H%M')}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"已保存到: {filepath}")

        if summary:
            print(f"\n总结:\n{summary}")

            # 发送通知（Mac + Telegram）
            await send_notifications(client, summary, len(messages), hours)

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
