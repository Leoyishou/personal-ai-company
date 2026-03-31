#!/usr/bin/env python3
"""
发送 Telegram 结构化消息
支持格式化文本、Inline Keyboard 等原生组件
"""
import asyncio
import os
import sys
import json
from typing import Optional, List, Dict, Any

try:
    from telethon import TelegramClient, Button
    from telethon.tl.types import MessageEntityBold, MessageEntityCode, MessageEntityPre
except ImportError:
    print("请先安装 telethon: pip install telethon")
    sys.exit(1)

# 配置 (复用 telegram-bobo 的凭证)
API_ID = '26421064'
API_HASH = '3cdcc576ab22d6b0ecdbf5d49bdb1502'
# Dashboard 专用 session（独立于调度器，避免 SQLite 锁冲突）
SESSION_PATH = os.path.expanduser('~/.claude/agents/ceo-assistant/session/dashboard')


class TelegramNotifier:
    """Telegram 结构化消息发送器"""

    def __init__(self):
        self.client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

    async def connect(self) -> bool:
        await self.client.connect()
        if not await self.client.is_user_authorized():
            print("未登录 Telegram，请先运行登录脚本")
            return False
        return True

    async def disconnect(self):
        await self.client.disconnect()

    async def send_message(
        self,
        text: str,
        chat: str = 'me',
        parse_mode: str = 'md',
        buttons: Optional[List[List[Dict]]] = None
    ) -> bool:
        """
        发送格式化消息

        Args:
            text: 消息内容，支持 Markdown 格式
            chat: 发送目标
            parse_mode: 'md' (Markdown) 或 'html'
            buttons: 内联按钮配置 [[{text, url}, ...], ...]
        """
        try:
            # 构建按钮
            keyboard = None
            if buttons:
                keyboard = []
                for row in buttons:
                    btn_row = []
                    for btn in row:
                        if btn.get('url'):
                            btn_row.append(Button.url(btn['text'], btn['url']))
                        elif btn.get('data'):
                            btn_row.append(Button.inline(btn['text'], btn['data'].encode()))
                        else:
                            btn_row.append(Button.inline(btn['text'], btn['text'].encode()))
                    keyboard.append(btn_row)

            await self.client.send_message(
                chat,
                text,
                parse_mode=parse_mode,
                buttons=keyboard,
                link_preview=False
            )
            return True

        except Exception as e:
            print(f"发送失败: {e}")
            return False

    # ==================== 结构化消息模板 ====================

    async def send_scan_report(
        self,
        total_tasks: int,
        analyzed: int,
        executable: int,
        completed: int,
        skipped: int,
        failed: int = 0,
        details: Optional[str] = None,
        chat: str = 'me'
    ) -> bool:
        """发送扫描报告"""

        # 状态 emoji
        status_emoji = "✅" if failed == 0 else "⚠️" if failed < 3 else "❌"

        text = f"""**{status_emoji} AI 助理扫描报告**

📊 **统计数据**
├ 总任务数: `{total_tasks}`
├ 分析任务: `{analyzed}`
├ 可执行: `{executable}`
├ 已完成: `{completed}`
├ 已跳过: `{skipped}`
└ 失败: `{failed}`
"""

        if details:
            text += f"\n📝 **详情**\n{details}\n"

        # 按钮
        buttons = [
            [
                {'text': '📊 打开控制台', 'url': 'http://localhost:5050'},
                {'text': '🔄 立即扫描', 'data': 'scan_now'}
            ]
        ]

        return await self.send_message(text, chat, buttons=buttons)

    async def send_task_notification(
        self,
        title: str,
        status: str,  # 'completed', 'failed', 'skipped'
        task_id: Optional[str] = None,
        reason: Optional[str] = None,
        duration: Optional[str] = None,
        chat: str = 'me'
    ) -> bool:
        """发送任务执行通知"""

        status_map = {
            'completed': ('✅', '执行成功'),
            'failed': ('❌', '执行失败'),
            'skipped': ('⏭️', '已跳过'),
            'timeout': ('⏱️', '执行超时'),
            'running': ('⏳', '执行中')
        }

        emoji, status_text = status_map.get(status, ('📋', status))

        text = f"""**{emoji} 任务{status_text}**

📌 **{title}**
"""

        if task_id:
            text += f"🆔 ID: `{task_id[:12]}...`\n"

        if duration:
            text += f"⏱️ 耗时: `{duration}`\n"

        if reason:
            text += f"\n💬 **备注**\n{reason}\n"

        # 按钮
        buttons = []
        if status == 'failed':
            buttons.append([
                {'text': '🔄 重试', 'data': f'retry:{task_id}' if task_id else 'retry'},
                {'text': '📋 查看日志', 'url': 'http://localhost:5050/#logs'}
            ])
        else:
            buttons.append([
                {'text': '📊 查看详情', 'url': 'http://localhost:5050'}
            ])

        return await self.send_message(text, chat, buttons=buttons)

    async def send_activity_summary(
        self,
        time_range: str,
        scan_count: int,
        timeout_count: int,
        executed_count: int,
        xhs_count: int,
        tweet_count: int,
        failed_count: int,
        chat: str = 'me'
    ) -> bool:
        """发送活动摘要"""

        # 整体状态
        if failed_count > 0:
            status_line = f"⚠️ **{failed_count}** 个任务失败，请关注"
        elif timeout_count > scan_count // 2:
            status_line = f"⏱️ 超时率较高 ({timeout_count}/{scan_count})，建议检查"
        else:
            status_line = "✅ 系统运行正常"

        text = f"""**📊 活动摘要** ({time_range})

{status_line}

**执行统计**
```
定时扫描    {scan_count:>3} 次
├ 成功      {scan_count - timeout_count:>3} 次
└ 超时      {timeout_count:>3} 次

任务执行    {executed_count:>3} 件
├ 小红书    {xhs_count:>3} 次
├ 发推      {tweet_count:>3} 次
└ 失败      {failed_count:>3} 次
```
"""

        buttons = [
            [
                {'text': '📊 控制台', 'url': 'http://localhost:5050'},
                {'text': '📜 日志', 'url': 'http://localhost:5050/#logs'}
            ]
        ]

        return await self.send_message(text, chat, buttons=buttons)

    async def send_error_alert(
        self,
        error_type: str,
        message: str,
        suggestion: Optional[str] = None,
        chat: str = 'me'
    ) -> bool:
        """发送错误告警"""

        text = f"""**🚨 错误告警**

**类型**: `{error_type}`

**详情**
```
{message}
```
"""

        if suggestion:
            text += f"\n💡 **建议**: {suggestion}\n"

        buttons = [
            [
                {'text': '📜 查看日志', 'url': 'http://localhost:5050/#logs'},
                {'text': '🔄 重启服务', 'data': 'restart_service'}
            ]
        ]

        return await self.send_message(text, chat, buttons=buttons)

    async def send_daily_report(
        self,
        date: str,
        total_tasks: int,
        completed: int,
        failed: int,
        highlights: List[str],
        chat: str = 'me'
    ) -> bool:
        """发送每日报告"""

        success_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0

        # 根据成功率选择 emoji
        if success_rate >= 90:
            emoji = "🎉"
        elif success_rate >= 70:
            emoji = "👍"
        else:
            emoji = "⚠️"

        text = f"""**{emoji} 每日报告** - {date}

**📈 执行概览**
├ 总任务: `{total_tasks}`
├ 成功: `{completed}` ({success_rate:.0f}%)
└ 失败: `{failed}`

**✨ 今日亮点**
"""

        for i, highlight in enumerate(highlights[:5], 1):
            text += f"{i}. {highlight}\n"

        buttons = [
            [
                {'text': '📊 详细报告', 'url': 'http://localhost:5050'},
                {'text': '📈 趋势分析', 'url': 'http://localhost:5050/#cost'}
            ]
        ]

        return await self.send_message(text, chat, buttons=buttons)

    async def send_report_with_image(
        self,
        image_path: str,
        stats: dict,
        time_range: str = "今日",
        chat: str = 'me'
    ) -> bool:
        """发送带图片的统计报告"""

        caption = f"""**📊 AI 助理运行报告**

**时间**: `{time_range}`

**执行统计**
├ 定时扫描: `{stats.get('scanCount', 0)}` 次
├ 成功: `{stats.get('scanCount', 0) - stats.get('timeoutCount', 0)}` 次
├ 超时: `{stats.get('timeoutCount', 0)}` 次
└ 失败: `{stats.get('failedCount', 0)}` 次

**任务执行**
├ 小红书: `{stats.get('xhsCount', 0)}` 次
├ 发推: `{stats.get('tweetCount', 0)}` 次
└ 总计: `~{stats.get('executedTasks', 0)}` 件

_点击下方按钮查看详情_"""

        buttons = [
            [
                {'text': '📊 控制台', 'url': 'http://localhost:5050'},
                {'text': '📜 日志', 'url': 'http://localhost:5050/#logs'}
            ]
        ]

        try:
            keyboard = []
            for row in buttons:
                btn_row = []
                for btn in row:
                    if btn.get('url'):
                        btn_row.append(Button.url(btn['text'], btn['url']))
                keyboard.append(btn_row)

            if image_path and os.path.exists(image_path):
                await self.client.send_file(
                    chat,
                    image_path,
                    caption=caption,
                    parse_mode='md',
                    buttons=keyboard
                )
            else:
                await self.client.send_message(
                    chat,
                    caption,
                    parse_mode='md',
                    buttons=keyboard
                )
            return True
        except Exception as e:
            print(f"发送失败: {e}")
            return False

    async def send_failed_task_alert(
        self,
        title: str,
        task_id: str,
        error_msg: str,
        duration: str = None,
        chat: str = 'me'
    ) -> bool:
        """发送任务失败告警（带重试按钮）"""

        text = f"""**❌ 任务执行失败**

📌 **{title}**

🆔 ID: `{task_id[:16]}...`
"""
        if duration:
            text += f"⏱️ 耗时: `{duration}`\n"

        text += f"""
**错误信息**
```
{error_msg[:500]}
```

_选择下方操作：_"""

        buttons = [
            [
                {'text': '🔄 重试任务', 'data': f'retry:{task_id}'},
                {'text': '⏭️ 跳过', 'data': f'skip:{task_id}'}
            ],
            [
                {'text': '📋 查看日志', 'url': 'http://localhost:5050/#logs'}
            ]
        ]

        return await self.send_message(text, chat, buttons=buttons)


# ==================== 便捷函数 ====================

async def send_message(message: str, chat: str = 'me', buttons: list = None):
    """发送简单消息"""
    notifier = TelegramNotifier()
    try:
        if not await notifier.connect():
            return False
        return await notifier.send_message(message, chat, buttons=buttons)
    finally:
        await notifier.disconnect()


async def send_scan_report(**kwargs):
    """发送扫描报告"""
    notifier = TelegramNotifier()
    try:
        if not await notifier.connect():
            return False
        return await notifier.send_scan_report(**kwargs)
    finally:
        await notifier.disconnect()


async def send_task_notification(**kwargs):
    """发送任务通知"""
    notifier = TelegramNotifier()
    try:
        if not await notifier.connect():
            return False
        return await notifier.send_task_notification(**kwargs)
    finally:
        await notifier.disconnect()


async def send_activity_summary(**kwargs):
    """发送活动摘要"""
    notifier = TelegramNotifier()
    try:
        if not await notifier.connect():
            return False
        return await notifier.send_activity_summary(**kwargs)
    finally:
        await notifier.disconnect()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='发送 Telegram 结构化消息')
    subparsers = parser.add_subparsers(dest='command', help='命令')

    # 简单消息
    msg_parser = subparsers.add_parser('msg', help='发送简单消息')
    msg_parser.add_argument('message', help='消息内容 (支持 Markdown)')
    msg_parser.add_argument('--chat', default='me', help='发送目标')

    # 扫描报告
    scan_parser = subparsers.add_parser('scan', help='发送扫描报告')
    scan_parser.add_argument('--total', type=int, default=0, help='总任务数')
    scan_parser.add_argument('--analyzed', type=int, default=0, help='分析数')
    scan_parser.add_argument('--executable', type=int, default=0, help='可执行数')
    scan_parser.add_argument('--completed', type=int, default=0, help='完成数')
    scan_parser.add_argument('--skipped', type=int, default=0, help='跳过数')
    scan_parser.add_argument('--failed', type=int, default=0, help='失败数')

    # 任务通知
    task_parser = subparsers.add_parser('task', help='发送任务通知')
    task_parser.add_argument('title', help='任务标题')
    task_parser.add_argument('--status', default='completed', help='状态')
    task_parser.add_argument('--reason', help='原因/备注')

    # 活动摘要
    summary_parser = subparsers.add_parser('summary', help='发送活动摘要')
    summary_parser.add_argument('--range', dest='time_range', default='今日', help='时间范围')
    summary_parser.add_argument('--json', dest='json_data', help='JSON 格式数据')

    args = parser.parse_args()

    if args.command == 'msg':
        asyncio.run(send_message(args.message, args.chat))

    elif args.command == 'scan':
        asyncio.run(send_scan_report(
            total_tasks=args.total,
            analyzed=args.analyzed,
            executable=args.executable,
            completed=args.completed,
            skipped=args.skipped,
            failed=args.failed
        ))

    elif args.command == 'task':
        asyncio.run(send_task_notification(
            title=args.title,
            status=args.status,
            reason=args.reason
        ))

    elif args.command == 'summary':
        if args.json_data:
            data = json.loads(args.json_data)
        else:
            data = {
                'time_range': args.time_range,
                'scan_count': 0,
                'timeout_count': 0,
                'executed_count': 0,
                'xhs_count': 0,
                'tweet_count': 0,
                'failed_count': 0
            }
        asyncio.run(send_activity_summary(**data))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
