#!/usr/bin/env python3
"""
统一通知服务
支持 Mac 通知、Telegram 等多种渠道
"""
import asyncio
import subprocess
import os
import sys
import json
from typing import List, Optional
from datetime import datetime

# 配置
CONFIG = {
    "default_channels": ["mac", "telegram"],
    "telegram": {
        "api_id": "26421064",
        "api_hash": "3cdcc576ab22d6b0ecdbf5d49bdb1502",
        "session_path": os.path.expanduser("~/.claude/skills/api-notify/session/notify")
    },
    "mac": {
        "sound": "Glass",
        "notifier_path": "/opt/homebrew/bin/terminal-notifier"
    }
}


class NotifyService:
    """通知服务"""

    def __init__(self):
        self._telegram_client = None

    # ==================== Mac 通知 ====================
    def send_mac(self, title: str, message: str, sound: str = None) -> bool:
        """发送 Mac 桌面通知"""
        try:
            sound = sound or CONFIG["mac"]["sound"]
            notifier = CONFIG["mac"]["notifier_path"]

            # 截断消息
            short_msg = message[:200] + "..." if len(message) > 200 else message

            # 尝试 terminal-notifier
            if os.path.exists(notifier):
                result = subprocess.run(
                    [notifier, "-title", title, "-message", short_msg, "-sound", sound],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return True

            # Fallback: osascript
            script = f'display notification "{short_msg}" with title "{title}" sound name "{sound}"'
            subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
            return True

        except Exception as e:
            print(f"[Mac] 通知失败: {e}", file=sys.stderr)
            return False

    # ==================== Telegram 通知 ====================
    async def _get_telegram_client(self):
        """获取或创建 Telegram 客户端"""
        if self._telegram_client is None:
            try:
                from telethon import TelegramClient
                self._telegram_client = TelegramClient(
                    CONFIG["telegram"]["session_path"],
                    CONFIG["telegram"]["api_id"],
                    CONFIG["telegram"]["api_hash"]
                )
                await self._telegram_client.connect()
            except ImportError:
                print("[Telegram] telethon 未安装", file=sys.stderr)
                return None
        return self._telegram_client

    async def send_telegram_async(self, title: str, message: str) -> bool:
        """发送 Telegram 通知到 Saved Messages"""
        try:
            client = await self._get_telegram_client()
            if not client:
                return False

            if not await client.is_user_authorized():
                print("[Telegram] 未登录", file=sys.stderr)
                return False

            # 格式化消息
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            full_message = f"🔔 **{title}**\n\n{message}\n\n_{now}_"

            # 截断过长消息
            if len(full_message) > 4000:
                full_message = full_message[:3900] + "\n\n...(已截断)"

            await client.send_message("me", full_message)
            return True

        except Exception as e:
            print(f"[Telegram] 通知失败: {e}", file=sys.stderr)
            return False

    def send_telegram(self, title: str, message: str) -> bool:
        """同步包装"""
        return asyncio.run(self.send_telegram_async(title, message))

    # ==================== Slack 通知 (预留) ====================
    def send_slack(self, title: str, message: str, webhook_url: str = None) -> bool:
        """发送 Slack 通知"""
        # TODO: 实现 Slack webhook
        print("[Slack] 暂未实现", file=sys.stderr)
        return False

    # ==================== Discord 通知 (预留) ====================
    def send_discord(self, title: str, message: str, webhook_url: str = None) -> bool:
        """发送 Discord 通知"""
        # TODO: 实现 Discord webhook
        print("[Discord] 暂未实现", file=sys.stderr)
        return False

    # ==================== 统一入口 ====================
    async def send_async(
        self,
        title: str,
        message: str,
        channels: List[str] = None
    ) -> dict:
        """
        发送通知到指定渠道

        Args:
            title: 通知标题
            message: 通知内容
            channels: 渠道列表，默认使用 config 中的 default_channels

        Returns:
            dict: 各渠道发送结果 {"mac": True, "telegram": False, ...}
        """
        channels = channels or CONFIG["default_channels"]
        results = {}

        for channel in channels:
            if channel == "mac":
                results["mac"] = self.send_mac(title, message)
            elif channel == "telegram":
                results["telegram"] = await self.send_telegram_async(title, message)
            elif channel == "slack":
                results["slack"] = self.send_slack(title, message)
            elif channel == "discord":
                results["discord"] = self.send_discord(title, message)
            else:
                print(f"[Notify] 未知渠道: {channel}", file=sys.stderr)
                results[channel] = False

        return results

    def send(self, title: str, message: str, channels: List[str] = None) -> dict:
        """同步包装"""
        return asyncio.run(self.send_async(title, message, channels))

    async def close(self):
        """关闭连接"""
        if self._telegram_client:
            await self._telegram_client.disconnect()
            self._telegram_client = None


# ==================== 便捷函数 ====================
_service = None

def get_service() -> NotifyService:
    global _service
    if _service is None:
        _service = NotifyService()
    return _service


def send_notification(
    title: str,
    message: str,
    channels: List[str] = None
) -> dict:
    """
    发送通知（便捷函数）

    示例:
        send_notification("提醒", "任务完成")
        send_notification("提醒", "任务完成", channels=["mac"])
    """
    return get_service().send(title, message, channels)


async def send_notification_async(
    title: str,
    message: str,
    channels: List[str] = None
) -> dict:
    """异步版本"""
    return await get_service().send_async(title, message, channels)


# ==================== CLI ====================
def main():
    import argparse

    parser = argparse.ArgumentParser(description="统一通知服务")
    parser.add_argument("--title", "-t", required=True, help="通知标题")
    parser.add_argument("--message", "-m", required=True, help="通知内容")
    parser.add_argument("--channels", "-c", nargs="+", default=None,
                        help="通知渠道 (mac, telegram, slack, discord)")

    args = parser.parse_args()

    results = send_notification(args.title, args.message, args.channels)

    # 输出结果
    for channel, success in results.items():
        status = "✓" if success else "✗"
        print(f"[{status}] {channel}")

    # 返回码
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
