#!/usr/bin/env python3
"""
Personal AI Agent - 统一调度器

这是整个系统的核心：
1. 常驻运行，监听 Telegram 消息
2. 每 30 分钟扫描滴答清单
3. 判断任务类型，选择合适的模型
4. 拉起子 Claude Code 进程执行具体任务
"""
import asyncio
import os
import sys
import subprocess
import json
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple

try:
    from telethon import TelegramClient, events
except ImportError:
    print("请先安装 telethon: pip install telethon")
    sys.exit(1)

# ============================================
# 配置
# ============================================

# Telegram 配置 (安装脚本会替换这些值)
API_ID = 'YOUR_API_ID'
API_HASH = 'YOUR_API_HASH'
SESSION_PATH = os.path.expanduser('~/.claude/skills/personal-assistant/session/telegram')

# 路径配置
SKILL_DIR = os.path.expanduser('~/.claude/skills/personal-assistant')
LOG_DIR = os.path.join(SKILL_DIR, 'logs')
STATE_FILE = os.path.join(SKILL_DIR, 'state.json')

# 扫描间隔（秒）
SCAN_INTERVAL = 30 * 60  # 30 分钟

# Claude 执行超时（秒）
CLAUDE_TIMEOUT = 300  # 5 分钟
CLAUDE_TIMEOUT_LONG = 600  # 10 分钟（用于 daily review 等复杂任务）

# 定时任务配置
DAILY_REVIEW_HOUR = 23  # 每晚 23:00 运行 daily review

# 确保目录存在
os.makedirs(LOG_DIR, exist_ok=True)


# ============================================
# 日志
# ============================================

def log(message: str):
    """写入日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line)

    log_file = os.path.join(LOG_DIR, 'scheduler.log')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_line + '\n')


# ============================================
# 任务路由：判断用什么模型
# ============================================

def route_task(task: str) -> Tuple[str, str]:
    """
    根据任务内容判断使用什么模型和执行方式

    返回: (model, skill_hint)
    - model: haiku / sonnet / opus
    - skill_hint: 给 Claude 的提示，告诉它用什么 skill
    """
    task_lower = task.lower()

    # 发推文 - 简单任务，用 haiku
    if any(kw in task_lower for kw in ['发推', 'twitter', 'x.com', '推文']):
        return 'haiku', '用 x-post skill 发送推文'

    # 发小红书 - 简单任务，用 haiku
    if any(kw in task_lower for kw in ['小红书', 'xhs', '红书']):
        return 'haiku', '用 xiaohongshu skill 发布'

    # 下载视频 - 简单任务，用 haiku
    if any(kw in task_lower for kw in ['下载', 'download']) and any(kw in task_lower for kw in ['视频', 'video', 'youtube', 'bilibili', 'b站', '抖音']):
        return 'haiku', '用 video-downloader-skill 下载'

    # 生成图片 - 需要创意，用 sonnet
    if any(kw in task_lower for kw in ['生成图', '画', '图片', 'nanobanana', '生成一张']):
        return 'sonnet', '用 nanobanana-draw skill 生成图片'

    # 调研/分析 - 复杂任务，用 opus
    if any(kw in task_lower for kw in ['调研', '研究', '分析', '报告', 'research']):
        return 'opus', '深度调研并生成报告'

    # 默认用 sonnet
    return 'sonnet', '灵活处理这个任务'


def is_task_executable(task: str) -> Tuple[bool, str]:
    """
    判断任务是否可以自动执行

    返回: (can_execute, reason)
    """
    # 太短的任务通常描述不清
    if len(task) < 5:
        return False, "任务描述太短"

    # 纯链接收藏，不是任务
    if task.startswith('http') and len(task.split()) == 1:
        return False, "只有链接，没有说要做什么"

    # 包含明确动词的任务更可能可执行
    action_verbs = ['发', '下载', '生成', '写', '调研', '分析', '总结', '翻译', '创建']
    has_action = any(verb in task for verb in action_verbs)

    if not has_action:
        return False, "没有明确的动作指令"

    # 检查是否有具体内容
    vague_patterns = [
        r'^发[两三几]条$',
        r'^做[个一]视频$',
        r'^写[个一]',
    ]
    for pattern in vague_patterns:
        if re.match(pattern, task):
            return False, "描述太模糊，缺少具体内容"

    return True, "可以执行"


# ============================================
# 执行 Claude
# ============================================

async def run_claude(prompt: str, model: str = 'sonnet') -> str:
    """
    运行 Claude Code 子进程

    Args:
        prompt: 要执行的任务
        model: 使用的模型 (haiku/sonnet/opus)

    Returns:
        执行结果
    """
    log(f"启动 Claude ({model}): {prompt[:80]}...")

    try:
        # 设置环境变量
        env = os.environ.copy()
        fnm_path = os.path.expanduser('~/.local/share/fnm/node-versions/v22.16.0/installation/bin')
        if os.path.exists(fnm_path):
            env['PATH'] = f"{fnm_path}:{env.get('PATH', '')}"

        # 构建命令
        cmd = ['claude', '-p', prompt, '--dangerously-skip-permissions']
        if model != 'sonnet':  # sonnet 是默认
            cmd.extend(['--model', model])

        # 运行
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT,
            env=env,
            cwd=SKILL_DIR
        )

        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr:
            output += f"\n\n错误: {result.stderr.strip()}"

        log(f"Claude 执行完成，输出 {len(output)} 字符")
        return output if output else "执行完成，无输出"

    except subprocess.TimeoutExpired:
        log(f"Claude 执行超时 ({CLAUDE_TIMEOUT}秒)")
        return f"执行超时（{CLAUDE_TIMEOUT // 60}分钟限制）"
    except Exception as e:
        log(f"Claude 执行失败: {e}")
        return f"执行失败: {e}"


async def send_telegram(client, message: str):
    """发送 Telegram 消息到 Saved Messages"""
    try:
        await client.send_message('me', message)
    except Exception as e:
        log(f"发送 Telegram 失败: {e}")


# ============================================
# 模式一：Telegram 消息处理
# ============================================

async def handle_telegram_message(client, message: str) -> str:
    """
    处理 Telegram 消息

    1. 判断任务类型
    2. 选择合适的模型
    3. 拉起 Claude 执行
    4. 返回结果
    """
    log(f"收到 Telegram 消息: {message[:50]}...")

    # 路由任务
    model, skill_hint = route_task(message)
    log(f"任务路由: model={model}, hint={skill_hint}")

    # 构建 prompt
    prompt = f"""请执行以下任务：

{message}

提示：{skill_hint}

执行完成后，简洁地告诉我结果。如果生成了文件或链接，请列出。"""

    # 执行
    result = await run_claude(prompt, model)

    return result


# ============================================
# 模式二：定时扫描滴答清单
# ============================================

async def run_daily_review(client):
    """
    每日复盘 - 运营部核心任务

    深度分析今天的行为数据，对齐 OKR，生成个性化洞察
    """
    log("=" * 40)
    log("开始每日复盘...")
    log("=" * 40)

    await send_telegram(client, "🔄 开始生成今日复盘...")

    prompt = """/daily-review

请执行完整的每日复盘流程：

## 数据源
1. **Supabase 数据**（用 mcp__supabase__execute_sql）
   - browsing_records: 今日浏览记录
   - agent_sessions: 今日 Agent 交互
   - agent_messages: 工具使用详情

2. **本地 Context**（用 Read 工具）
   - ~/odyssey/4 复盘/2025/2025-2026 战略屋.md（OKR 目标）
   - ~/odyssey/1 一切皆项目/进行中/（当前项目列表）

## 分析维度

### 1. 目标对齐度
把今天的活动归类到 OKR：
- O1 职业基建（技术学习、代码开发）
- O2 健康运维（运动、健康相关）
- O3 产品目标（Viva 等产品工作）
- O5 个人品牌（内容创作、社媒）
- O6 智能化升级（AI 工具、自动化）
- O7 托福/英语（语言学习）
- ⚠️ 无法归类（注意力黑洞）

### 2. 时间分配
- 各 OKR 的时间占比
- 深度工作 vs 碎片浏览
- 高价值活动 vs 低价值消耗

### 3. 知识增量
- 今天接触的新概念/关键词
- 可以关联到知识库的哪些已有概念

### 4. 执行偏差
- 如果有滴答清单数据，对比计划 vs 实际

### 5. 趋势预警（如果有历史数据）
- 和昨天/上周对比

## 输出要求

生成结构化报告，包含：
1. 📊 今日概览（一句话总结 + 3 个核心数字）
2. 🎯 OKR 进展（哪些目标有推进，哪些停滞）
3. 💡 关键洞察（2-3 条个性化观察）
4. ⚠️ 注意事项（如果有偏离轨道的迹象）
5. 📝 明日建议（1-2 条 actionable）

## 写入位置

1. **Supabase**:
   - 表名: daily_personal_reviews
   - 字段: review_date, okr_alignment, time_distribution, insights, raw_report

2. **Notion**:
   - 创建新页面到 Daily Review 数据库
   - 包含完整报告 + 可视化

完成后发 Telegram 通知老板。
"""

    try:
        result = await run_claude_long(prompt, 'opus')
        log(f"每日复盘完成，输出 {len(result)} 字符")

        # 截断过长结果
        summary = result[:3000] if len(result) > 3000 else result
        await send_telegram(client, f"✅ 今日复盘完成\n\n{summary}")

    except Exception as e:
        log(f"每日复盘失败: {e}")
        await send_telegram(client, f"❌ 今日复盘失败: {e}")


async def run_claude_long(prompt: str, model: str = 'opus') -> str:
    """
    运行 Claude Code 子进程（长时间任务版本）
    """
    log(f"启动 Claude 长任务 ({model}): {prompt[:80]}...")

    try:
        env = os.environ.copy()
        fnm_path = os.path.expanduser('~/.local/share/fnm/node-versions/v22.16.0/installation/bin')
        if os.path.exists(fnm_path):
            env['PATH'] = f"{fnm_path}:{env.get('PATH', '')}"

        cmd = ['claude', '-p', prompt, '--dangerously-skip-permissions', '--model', model]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT_LONG,
            env=env,
            cwd=os.path.expanduser('~')  # 从 home 目录运行，方便访问 odyssey
        )

        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr:
            output += f"\n\n错误: {result.stderr.strip()}"

        log(f"Claude 长任务完成，输出 {len(output)} 字符")
        return output if output else "执行完成，无输出"

    except subprocess.TimeoutExpired:
        log(f"Claude 长任务超时 ({CLAUDE_TIMEOUT_LONG}秒)")
        return f"执行超时（{CLAUDE_TIMEOUT_LONG // 60}分钟限制）"
    except Exception as e:
        log(f"Claude 长任务失败: {e}")
        return f"执行失败: {e}"


async def scan_dida_tasks(client):
    """
    扫描滴答清单，执行可自动化的任务

    这里我们调用 Claude 来完成扫描和判断，
    因为它需要调用 MCP 获取任务列表
    """
    log("开始扫描滴答清单...")

    prompt = """/personal-assistant

请执行完整的扫描流程：
1. 读取 state.json
2. 获取滴答清单任务
3. 筛选增量任务
4. 判断哪些可执行
5. 执行可执行的任务（使用 Task tool 启动子 agent）
6. 更新 state.json
7. 返回执行摘要

注意：
- 对于每个要执行的任务，根据类型选择模型：
  - 发推/发小红书/下载视频 → 用 haiku
  - 生成图片 → 用 sonnet
  - 调研分析 → 用 opus
- 无论有没有新任务，都要给我发 Telegram 通知"""

    result = await run_claude(prompt, 'sonnet')

    log(f"滴答清单扫描完成")
    return result


# ============================================
# 主循环
# ============================================

async def main():
    """主函数"""
    log("=" * 50)
    log("Personal AI Agent 调度器启动")
    log("=" * 50)

    # 连接 Telegram
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        log("未登录 Telegram，请先运行 telegram_login.py")
        return

    me = await client.get_me()
    log(f"Telegram 已登录: {me.first_name}")

    # 发送启动通知
    await send_telegram(client, """[调度器] 已上线

两种工作模式：
1. 发消息给我 → 立即执行
2. 待办清单 → 每 30 分钟自动扫描""")

    # 上次扫描时间
    last_scan = datetime.now() - timedelta(seconds=SCAN_INTERVAL)  # 立即执行第一次

    # 监听 Telegram 消息
    @client.on(events.NewMessage(chats='me', outgoing=True))
    async def handler(event):
        """处理 Telegram 消息"""
        message = event.message.message

        # 忽略空消息和自己的回复
        if not message or message.startswith('['):
            return

        # 发送"正在处理"
        processing_msg = await event.reply("[调度器] 收到，正在处理...")

        try:
            # 处理消息
            result = await handle_telegram_message(client, message)

            # 截断过长结果
            if len(result) > 4000:
                result = result[:4000] + "\n\n...(已截断)"

            # 回复结果
            await processing_msg.delete()
            await event.reply(f"[执行完成]\n\n{result}")

        except Exception as e:
            log(f"处理消息失败: {e}")
            await processing_msg.edit(f"[调度器] 处理失败: {e}")

    log("开始监听 Telegram 消息...")
    log(f"定时扫描间隔: {SCAN_INTERVAL // 60} 分钟")
    log(f"每日复盘时间: {DAILY_REVIEW_HOUR}:00")

    # 记录今天是否已运行过 daily review
    last_review_date = None

    # 主循环：定时扫描
    while True:
        try:
            now = datetime.now()

            # 检查是否需要扫描滴答清单
            if (now - last_scan).total_seconds() >= SCAN_INTERVAL:
                log("触发定时扫描...")
                await scan_dida_tasks(client)
                last_scan = now

            # 检查是否需要运行 daily review（每天 23:00）
            today = now.date()
            if now.hour == DAILY_REVIEW_HOUR and last_review_date != today:
                log(f"触发每日复盘 ({DAILY_REVIEW_HOUR}:00)...")
                await run_daily_review(client)
                last_review_date = today

            # 处理 Telegram 事件
            await asyncio.sleep(1)

        except KeyboardInterrupt:
            log("收到退出信号")
            break
        except Exception as e:
            log(f"主循环错误: {e}")
            await asyncio.sleep(10)

    await client.disconnect()
    log("调度器已停止")


if __name__ == "__main__":
    asyncio.run(main())
