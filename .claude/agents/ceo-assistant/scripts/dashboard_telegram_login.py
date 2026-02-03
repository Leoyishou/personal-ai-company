#!/usr/bin/env python3
"""
为 Dashboard 创建独立的 Telegram session
运行一次即可，之后 Dashboard 发送消息就不会与调度器冲突
"""
import asyncio
import os

try:
    from telethon import TelegramClient
except ImportError:
    print("请先安装 telethon: pip install telethon")
    exit(1)

API_ID = '26421064'
API_HASH = '3cdcc576ab22d6b0ecdbf5d49bdb1502'
SESSION_PATH = os.path.expanduser('~/.claude/agents/ceo-assistant/session/dashboard')

async def main():
    print("=" * 50)
    print("Dashboard Telegram Session 登录")
    print("=" * 50)
    print()
    print("这将创建一个独立的 session，避免与调度器冲突")
    print()
    
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.start()
    
    me = await client.get_me()
    print(f"\n✅ 登录成功: {me.first_name} (@{me.username})")
    print(f"Session 已保存到: {SESSION_PATH}.session")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
