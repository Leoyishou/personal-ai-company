#!/usr/bin/env python3
"""
Telegram 消息监听器
监听 Saved Messages，收到消息后触发 Claude Code 执行
"""
import asyncio
import os
import sys
import subprocess
import signal
from datetime import datetime

try:
    from telethon import TelegramClient, events
except ImportError:
    print("请先安装 telethon: pip install telethon")
    sys.exit(1)

# 配置 (复用 telegram-bobo 的凭证)
API_ID = '26421064'
API_HASH = '3cdcc576ab22d6b0ecdbf5d49bdb1502'
SESSION_PATH = os.path.expanduser('~/.claude/skills/telegram-bobo/session/bobo')

# 日志文件
LOG_FILE = os.path.expanduser('~/.claude/skills/personal-assistant/logs/telegram_listener.log')

# 确保日志目录存在
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)


def log(message: str):
    """写入日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_line + '\n')


async def run_claude(prompt: str) -> str:
    """
    运行 Claude Code 并返回结果
    """
    log(f"执行 Claude: {prompt[:100]}...")

    try:
        # 设置环境变量确保 fnm/node 可用
        env = os.environ.copy()
        fnm_path = os.path.expanduser('~/.local/share/fnm/node-versions/v22.16.0/installation/bin')
        env['PATH'] = f"{fnm_path}:{env.get('PATH', '')}"

        # 运行 Claude
        result = subprocess.run(
            ['claude', '-p', prompt, '--dangerously-skip-permissions'],
            capture_output=True,
            text=True,
            timeout=300,  # 5 分钟超时
            env=env,
            cwd=os.path.expanduser('~/.claude/skills/personal-assistant')
        )

        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr:
            output += f"\n\n错误: {result.stderr.strip()}"

        log(f"Claude 执行完成，输出 {len(output)} 字符")
        return output if output else "执行完成，无输出"

    except subprocess.TimeoutExpired:
        log("Claude 执行超时")
        return "执行超时（5分钟限制）"
    except Exception as e:
        log(f"Claude 执行失败: {e}")
        return f"执行失败: {e}"


async def main():
    """主函数"""
    log("启动 Telegram 监听器...")

    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

    await client.connect()
    if not await client.is_user_authorized():
        log("未登录 Telegram，请先运行 telegram-bobo 的登录脚本")
        return

    me = await client.get_me()
    log(f"已登录: {me.first_name} (@{me.username})")

    # 监听发给自己的消息 (Saved Messages)
    @client.on(events.NewMessage(chats='me', outgoing=True))
    async def handler(event):
        """处理收到的消息"""
        message = event.message.message

        if not message or message.startswith('[Claude]'):
            # 忽略空消息和 Claude 的回复
            return

        log(f"收到消息: {message[:50]}...")

        # 发送"正在处理"提示
        processing_msg = await event.reply("[Claude] 收到，正在处理...")

        try:
            # 运行 Claude
            result = await run_claude(message)

            # 截断过长的结果
            if len(result) > 4000:
                result = result[:4000] + "\n\n...(结果过长，已截断)"

            # 删除"正在处理"消息，发送结果
            await processing_msg.delete()
            await event.reply(f"[Claude] 执行完成：\n\n{result}")

        except Exception as e:
            log(f"处理消息失败: {e}")
            await processing_msg.edit(f"[Claude] 处理失败: {e}")

    log("开始监听 Saved Messages...")
    log("发送消息到 Saved Messages 即可触发 Claude")

    # 发送启动通知
    await client.send_message('me', "[Claude] 助理已上线，发送消息即可触发执行")

    # 保持运行
    await client.run_until_disconnected()


if __name__ == "__main__":
    # 处理 Ctrl+C
    def signal_handler(sig, frame):
        log("收到停止信号，正在退出...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    asyncio.run(main())
