#!/usr/bin/env python3
"""
发送 Telegram 消息通知
"""
import asyncio
import os
import sys

try:
    from telethon import TelegramClient
except ImportError:
    print("请先安装 telethon: pip install telethon")
    sys.exit(1)

# 配置（安装脚本会替换这些值）
API_ID = 'YOUR_API_ID'
API_HASH = 'YOUR_API_HASH'
SESSION_PATH = os.path.expanduser('~/.claude/skills/personal-assistant/session/telegram')


async def send_message(message: str, chat: str = 'me'):
    """
    发送消息到 Telegram

    Args:
        message: 要发送的消息内容
        chat: 发送目标，默认 'me' (Saved Messages)
    """
    # 确保 session 目录存在
    os.makedirs(os.path.dirname(SESSION_PATH), exist_ok=True)

    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            print("未登录 Telegram，请先运行: python3 scripts/telegram_login.py")
            return False

        await client.send_message(chat, message)
        print("Telegram 消息已发送")
        return True

    except Exception as e:
        print(f"发送失败: {e}")
        return False
    finally:
        await client.disconnect()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='发送 Telegram 消息')
    parser.add_argument('message', help='要发送的消息内容')
    parser.add_argument('--chat', default='me', help='发送目标 (默认: me/Saved Messages)')

    args = parser.parse_args()

    asyncio.run(send_message(args.message, args.chat))


if __name__ == "__main__":
    main()
