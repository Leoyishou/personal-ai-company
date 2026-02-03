#!/usr/bin/env python3
"""
Telegram 高级消息组件 Demo
展示图片、按钮、投票、定时消息等功能
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    from telethon import TelegramClient, Button, events
    from telethon.tl.types import (
        InputMediaPoll, Poll, PollAnswer,
        InputMediaDice
    )
    from telethon.tl.functions.messages import SendMediaRequest
except ImportError:
    print("请先安装 telethon: pip install telethon")
    sys.exit(1)

# 配置
API_ID = '26421064'
API_HASH = '3cdcc576ab22d6b0ecdbf5d49bdb1502'
# Dashboard 专用 session（独立于调度器，避免 SQLite 锁冲突）
SESSION_PATH = os.path.expanduser('~/.claude/agents/ceo-assistant/session/dashboard')
SKILL_DIR = Path(__file__).parent.parent


class TelegramDemo:
    def __init__(self):
        self.client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

    async def connect(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            print("未登录，请先登录")
            return False
        return True

    async def disconnect(self):
        await self.client.disconnect()

    # ==================== 1. 带图片的报告 ====================
    async def send_report_with_image(self, image_path: str = None, chat: str = 'me'):
        """发送带图片的统计报告"""

        # 如果没有图片，生成一个简单的统计图
        if not image_path:
            image_path = await self._generate_chart()

        caption = """**📊 AI 助理运行报告**

**时间**: `2026-01-26 06:00 - 12:00`

**执行统计**
├ 定时扫描: `27` 次
├ 成功: `12` 次
├ 超时: `15` 次
└ 失败: `0` 次

**任务执行**
├ 小红书: `10` 次
├ 发推: `11` 次
└ 总计: `~21` 件

_点击下方按钮查看详情_"""

        buttons = [
            [
                Button.url("📊 控制台", "http://localhost:5050"),
                Button.url("📜 日志", "http://localhost:5050/#logs")
            ],
            [
                Button.inline("🔄 刷新数据", b"refresh_stats"),
                Button.inline("📤 分享报告", b"share_report")
            ]
        ]

        if image_path and os.path.exists(image_path):
            await self.client.send_file(
                chat,
                image_path,
                caption=caption,
                parse_mode='md',
                buttons=buttons
            )
            print(f"✅ 带图片的报告已发送")
        else:
            # 没有图片就发纯文本
            await self.client.send_message(
                chat,
                caption,
                parse_mode='md',
                buttons=buttons
            )
            print(f"✅ 报告已发送（无图片）")

    async def _generate_chart(self) -> str:
        """生成简单的统计图表"""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            # 数据
            dates = ['01-20', '01-21', '01-22', '01-23', '01-24', '01-25', '01-26']
            tasks = [5, 8, 12, 7, 15, 10, 21]

            # 创建图表
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.bar(dates, tasks, color='#3370ff', width=0.6)
            ax.set_title('Weekly Task Execution', fontsize=14, fontweight='bold')
            ax.set_xlabel('Date')
            ax.set_ylabel('Tasks')
            ax.set_ylim(0, max(tasks) + 5)

            # 添加数值标签
            for i, v in enumerate(tasks):
                ax.text(i, v + 0.5, str(v), ha='center', fontsize=10)

            plt.tight_layout()

            # 保存
            chart_path = '/tmp/telegram_chart.png'
            plt.savefig(chart_path, dpi=150)
            plt.close()

            return chart_path

        except ImportError:
            print("matplotlib 未安装，跳过图表生成")
            return None

    # ==================== 2. 交互式按钮 ====================
    async def send_interactive_task(self, task_title: str, task_id: str = "task_001", chat: str = 'me'):
        """发送带交互按钮的任务通知"""

        text = f"""**❌ 任务执行失败**

📌 **{task_title}**

🆔 ID: `{task_id}`
⏱️ 耗时: `2分30秒`
📅 时间: `{datetime.now().strftime('%Y-%m-%d %H:%M')}`

**错误信息**
```
TimeoutError: Claude 执行超时 (300秒)
```

_选择下方操作：_"""

        buttons = [
            [
                Button.inline("🔄 重试任务", f"retry:{task_id}".encode()),
                Button.inline("⏭️ 跳过", f"skip:{task_id}".encode())
            ],
            [
                Button.inline("📋 查看详情", f"detail:{task_id}".encode()),
                Button.inline("🗑️ 删除任务", f"delete:{task_id}".encode())
            ],
            [
                Button.url("📊 打开控制台", "http://localhost:5050")
            ]
        ]

        await self.client.send_message(
            chat,
            text,
            parse_mode='md',
            buttons=buttons
        )
        print(f"✅ 交互式任务通知已发送")

    # ==================== 3. 投票 ====================
    async def send_task_poll(self, tasks: list, chat: str = 'me'):
        """发送任务选择投票"""
        from telethon.tl.types import TextWithEntities

        # 先发送说明消息
        intro = """**🗳️ 待执行任务投票**

以下任务需要你的确认，请投票选择要执行的任务：

_可多选，投票后 AI 助理将按顺序执行_"""

        await self.client.send_message(chat, intro, parse_mode='md')

        # 创建投票 - 使用 TextWithEntities
        poll = InputMediaPoll(
            poll=Poll(
                id=0,  # Telegram 会自动分配
                question=TextWithEntities(text="选择要执行的任务", entities=[]),
                answers=[
                    PollAnswer(
                        text=TextWithEntities(text=task[:100], entities=[]),
                        option=str(i).encode()
                    )
                    for i, task in enumerate(tasks[:10])  # 最多10个选项
                ],
                multiple_choice=True,  # 允许多选
                public_voters=False,   # 匿名投票
            )
        )

        await self.client(SendMediaRequest(
            peer=await self.client.get_input_entity(chat),
            media=poll,
            message=""
        ))

        print(f"✅ 投票已发送，包含 {len(tasks)} 个选项")

    # ==================== 4. 定时消息 ====================
    async def send_scheduled_report(self, delay_minutes: int = 1, chat: str = 'me'):
        """发送定时消息"""

        schedule_time = datetime.now() + timedelta(minutes=delay_minutes)

        text = f"""**⏰ 定时报告**

这是一条定时消息，发送于 `{schedule_time.strftime('%H:%M')}`

**今日概览**
├ 执行任务: `15` 件
├ 成功率: `93%`
└ 节省时间: `~2小时`

_此消息由 AI 助理自动发送_"""

        buttons = [
            [Button.url("📊 查看详情", "http://localhost:5050")]
        ]

        await self.client.send_message(
            chat,
            text,
            parse_mode='md',
            buttons=buttons,
            schedule=schedule_time
        )

        print(f"✅ 定时消息已设置，将于 {schedule_time.strftime('%Y-%m-%d %H:%M:%S')} 发送")

    # ==================== 5. 相册 ====================
    async def send_album(self, images: list, caption: str = None, chat: str = 'me'):
        """发送相册（多图）"""

        if not images:
            print("没有图片可发送")
            return

        # 过滤存在的文件
        valid_images = [img for img in images if os.path.exists(img)]

        if not valid_images:
            print("没有有效的图片文件")
            return

        await self.client.send_file(
            chat,
            valid_images,
            caption=caption or "📸 相册",
            parse_mode='md'
        )

        print(f"✅ 相册已发送，包含 {len(valid_images)} 张图片")

    # ==================== 6. 骰子/动画 ====================
    async def send_dice(self, emoji: str = "🎲", chat: str = 'me'):
        """发送骰子动画"""

        # 支持的 emoji: 🎲 🎯 🏀 ⚽ 🎳 🎰
        valid_emojis = ["🎲", "🎯", "🏀", "⚽", "🎳", "🎰"]

        if emoji not in valid_emojis:
            emoji = "🎲"

        msg = await self.client.send_file(
            chat,
            InputMediaDice(emoticon=emoji)
        )

        print(f"✅ 骰子已发送: {emoji}")
        return msg

    # ==================== 7. 带按钮回调处理的监听器 ====================
    async def start_button_listener(self):
        """启动按钮回调监听器"""

        @self.client.on(events.CallbackQuery)
        async def callback_handler(event):
            data = event.data.decode()
            print(f"收到按钮回调: {data}")

            if data.startswith("retry:"):
                task_id = data.split(":")[1]
                await event.answer(f"正在重试任务 {task_id}...", alert=True)
                # 这里可以触发实际的重试逻辑

            elif data.startswith("skip:"):
                task_id = data.split(":")[1]
                await event.answer(f"已跳过任务 {task_id}")

            elif data.startswith("detail:"):
                task_id = data.split(":")[1]
                await event.answer(f"任务详情: {task_id}", alert=True)

            elif data == "refresh_stats":
                await event.answer("数据已刷新 ✅")

            elif data == "share_report":
                await event.answer("分享功能开发中...")

            else:
                await event.answer(f"未知操作: {data}")

        print("✅ 按钮回调监听器已启动")
        print("点击消息中的按钮可以看到回调效果")
        await self.client.run_until_disconnected()


# ==================== Demo 运行函数 ====================

async def run_all_demos():
    """运行所有 Demo"""
    demo = TelegramDemo()

    if not await demo.connect():
        return

    try:
        print("\n" + "="*50)
        print("Telegram 高级消息组件 Demo")
        print("="*50 + "\n")

        # 1. 带图片的报告
        print("📊 发送带图片的报告...")
        await demo.send_report_with_image()
        await asyncio.sleep(2)

        # 2. 交互式按钮
        print("\n🔘 发送交互式任务通知...")
        await demo.send_interactive_task(
            task_title="下载抖音视频并转文字",
            task_id="task_20260126_001"
        )
        await asyncio.sleep(2)

        # 3. 投票
        print("\n🗳️ 发送任务投票...")
        await demo.send_task_poll([
            "📱 发布小红书：AI 工具推荐",
            "🐦 发推：每日技术分享",
            "📝 整理滴答清单任务",
            "📊 生成周报",
            "🔍 调研 Deeper Search 框架"
        ])
        await asyncio.sleep(2)

        # 4. 定时消息
        print("\n⏰ 发送定时消息（1分钟后）...")
        await demo.send_scheduled_report(delay_minutes=1)
        await asyncio.sleep(2)

        # 5. 骰子
        print("\n🎲 发送骰子动画...")
        await demo.send_dice("🎰")

        print("\n" + "="*50)
        print("✅ 所有 Demo 已发送！请查看 Telegram Saved Messages")
        print("="*50)

    finally:
        await demo.disconnect()


async def run_with_listener():
    """运行 Demo 并启动按钮监听"""
    demo = TelegramDemo()

    if not await demo.connect():
        return

    print("\n" + "="*50)
    print("Telegram 交互式 Demo（带按钮监听）")
    print("="*50 + "\n")

    # 发送交互式消息
    await demo.send_interactive_task(
        task_title="测试交互按钮",
        task_id="test_001"
    )

    print("\n⏳ 等待按钮点击...（Ctrl+C 退出）\n")

    # 启动监听器
    await demo.start_button_listener()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Telegram 高级消息组件 Demo')
    parser.add_argument('demo', nargs='?', default='all',
                        choices=['all', 'report', 'buttons', 'poll', 'schedule', 'dice', 'listen'],
                        help='要运行的 Demo')

    args = parser.parse_args()

    if args.demo == 'listen':
        asyncio.run(run_with_listener())
    elif args.demo == 'all':
        asyncio.run(run_all_demos())
    else:
        async def run_single():
            demo = TelegramDemo()
            if not await demo.connect():
                return
            try:
                if args.demo == 'report':
                    await demo.send_report_with_image()
                elif args.demo == 'buttons':
                    await demo.send_interactive_task("测试任务", "test_001")
                elif args.demo == 'poll':
                    await demo.send_task_poll(["选项1", "选项2", "选项3"])
                elif args.demo == 'schedule':
                    await demo.send_scheduled_report(1)
                elif args.demo == 'dice':
                    await demo.send_dice()
            finally:
                await demo.disconnect()

        asyncio.run(run_single())


if __name__ == "__main__":
    main()
