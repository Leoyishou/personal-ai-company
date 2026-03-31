#!/usr/bin/env python3
"""
Telegram 登录脚本 - 支持两步式登录
"""
import asyncio
import os
import sys
from telethon import TelegramClient

API_ID = '26421064'
API_HASH = '3cdcc576ab22d6b0ecdbf5d49bdb1502'
PHONE = '+8613167265302'

# 优先使用原项目的 session
OLD_SESSION = os.path.expanduser('~/usr/projects/broker/session_name')
NEW_SESSION = os.path.expanduser('~/.claude/skills/telegram-bobo/session/bobo')
SESSION_PATH = NEW_SESSION  # 新手机号用新 session

async def send_code():
    """发送验证码"""
    os.makedirs(os.path.dirname(SESSION_PATH), exist_ok=True)
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

    await client.connect()

    if await client.is_user_authorized():
        me = await client.get_me()
        print(f"✓ 已登录: {me.first_name} ({me.phone})")
        await client.disconnect()
        return None

    result = await client.send_code_request(PHONE)
    print(f"✓ 验证码已发送到 {PHONE}")
    print(f"  phone_code_hash: {result.phone_code_hash}")

    # 保存 hash 供下一步使用
    hash_file = SESSION_PATH + '.hash'
    with open(hash_file, 'w') as f:
        f.write(result.phone_code_hash)

    await client.disconnect()
    return result.phone_code_hash

async def verify_code(code: str):
    """验证码登录"""
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

    await client.connect()

    # 读取 hash
    hash_file = SESSION_PATH + '.hash'
    if not os.path.exists(hash_file):
        print("❌ 请先运行 --send-code 发送验证码")
        await client.disconnect()
        return False

    with open(hash_file, 'r') as f:
        phone_code_hash = f.read().strip()

    try:
        await client.sign_in(PHONE, code, phone_code_hash=phone_code_hash)
        me = await client.get_me()
        print(f"✓ 登录成功: {me.first_name} ({me.phone})")

        # 清理 hash 文件
        os.remove(hash_file)

        # 测试
        dialogs = await client.get_dialogs()
        target = next((d for d in dialogs if '勃勃' in d.name), None)
        if target:
            print(f"✓ 找到群: {target.name}")

        await client.disconnect()
        return True
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        await client.disconnect()
        return False

async def check_status():
    """检查登录状态"""
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.connect()

    if await client.is_user_authorized():
        me = await client.get_me()
        print(f"✓ 已登录: {me.first_name} ({me.phone})")

        dialogs = await client.get_dialogs()
        target = next((d for d in dialogs if '勃勃' in d.name), None)
        if target:
            print(f"✓ 找到群: {target.name}")
    else:
        print("❌ 未登录")

    await client.disconnect()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Telegram 登录')
    parser.add_argument('--send-code', action='store_true', help='发送验证码')
    parser.add_argument('--verify', type=str, metavar='CODE', help='输入验证码完成登录')
    parser.add_argument('--status', action='store_true', help='检查登录状态')

    args = parser.parse_args()

    if args.send_code:
        asyncio.run(send_code())
    elif args.verify:
        asyncio.run(verify_code(args.verify))
    elif args.status:
        asyncio.run(check_status())
    else:
        parser.print_help()
        print("\n示例:")
        print("  python3 login.py --send-code      # 发送验证码")
        print("  python3 login.py --verify 12345   # 输入验证码登录")
        print("  python3 login.py --status         # 检查状态")
