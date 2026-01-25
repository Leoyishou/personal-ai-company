#!/usr/bin/env python3
"""
Telegram 登录脚本
首次使用需要运行此脚本完成登录
"""
import asyncio
import os
import sys

try:
    from telethon import TelegramClient
    from telethon.errors import SessionPasswordNeededError
except ImportError:
    print("请先安装 telethon: pip install telethon")
    sys.exit(1)

# 配置（安装脚本会替换这些值）
API_ID = 'YOUR_API_ID'
API_HASH = 'YOUR_API_HASH'
PHONE = 'YOUR_PHONE'
SESSION_PATH = os.path.expanduser('~/.claude/skills/personal-assistant/session/telegram')


async def main():
    """登录 Telegram"""
    print("=" * 50)
    print("  Telegram 登录")
    print("=" * 50)
    print()

    # 确保目录存在
    os.makedirs(os.path.dirname(SESSION_PATH), exist_ok=True)

    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

    await client.connect()

    if await client.is_user_authorized():
        me = await client.get_me()
        print(f"已登录: {me.first_name} (@{me.username})")
        print("无需重新登录")
        await client.disconnect()
        return True

    print(f"手机号: {PHONE}")
    print("正在发送验证码...")

    try:
        await client.send_code_request(PHONE)
        print()
        code = input("请输入收到的验证码: ")

        try:
            await client.sign_in(PHONE, code)
        except SessionPasswordNeededError:
            print()
            password = input("请输入两步验证密码: ")
            await client.sign_in(password=password)

        me = await client.get_me()
        print()
        print(f"登录成功: {me.first_name} (@{me.username})")
        print(f"Session 已保存到: {SESSION_PATH}")

        await client.disconnect()
        return True

    except Exception as e:
        print(f"登录失败: {e}")
        await client.disconnect()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
