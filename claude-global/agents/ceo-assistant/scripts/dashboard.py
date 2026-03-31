#!/usr/bin/env python3
"""
Personal AI Agent - Web Dashboard

飞书风格的 CEO 仪表盘：
1. 实时日志流
2. 任务执行历史
3. 手动触发任务
4. 统计图表
5. 成本追踪
"""
import asyncio
import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import threading
import time

from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO, emit

# ============================================
# 配置
# ============================================

SKILL_DIR = Path.home() / '.claude' / 'skills' / 'personal-assistant'
LOG_DIR = SKILL_DIR / 'logs'
STATE_FILE = SKILL_DIR / 'state.json'
COST_FILE = SKILL_DIR / 'cost.json'

LOG_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'personal-ai-agent-dashboard'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ============================================
# 数据读取
# ============================================

def read_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass
    return {"processedTasks": {}, "lastRunAt": None}


def read_recent_logs(lines: int = 100) -> list:
    log_file = LOG_DIR / 'scheduler.log'
    if not log_file.exists():
        return []
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            return all_lines[-lines:]
    except:
        return []


def get_task_history() -> list:
    state = read_state()
    tasks = []
    for task_id, info in state.get('processedTasks', {}).items():
        tasks.append({
            'id': task_id,
            'processedAt': info.get('processedAt', ''),
            'status': info.get('status', 'unknown'),
            'reason': info.get('reason', ''),
            'title': info.get('title', task_id[:30] + '...')
        })
    tasks.sort(key=lambda x: x['processedAt'], reverse=True)
    return tasks[:50]


def get_statistics() -> dict:
    state = read_state()
    tasks = state.get('processedTasks', {})

    status_count = {'completed': 0, 'failed': 0, 'skipped': 0}
    for info in tasks.values():
        status = info.get('status', 'unknown')
        if status in status_count:
            status_count[status] += 1

    daily_count = {}
    for info in tasks.values():
        processed_at = info.get('processedAt', '')
        if processed_at:
            try:
                date = processed_at[:10]
                daily_count[date] = daily_count.get(date, 0) + 1
            except:
                pass

    today = datetime.now().date()
    weekly_data = []
    for i in range(6, -1, -1):
        date = (today - timedelta(days=i)).isoformat()
        weekly_data.append({'date': date, 'count': daily_count.get(date, 0)})

    return {
        'total': len(tasks),
        'statusCount': status_count,
        'weeklyData': weekly_data,
        'lastRunAt': state.get('lastRunAt', 'Never')
    }


def read_cost_data() -> dict:
    """读取成本统计数据"""
    # 尝试从 cost.json 读取
    if COST_FILE.exists():
        try:
            return json.loads(COST_FILE.read_text())
        except:
            pass

    # 返回默认/示例数据
    today = datetime.now().date()
    daily_costs = []
    for i in range(6, -1, -1):
        date = (today - timedelta(days=i)).isoformat()
        daily_costs.append({
            'date': date,
            'tasks': 0,
            'inputTokens': 0,
            'outputTokens': 0,
            'cost': 0.0
        })

    return {
        'totalCost': 0.0,
        'todayCost': 0.0,
        'totalCalls': 0,
        'trend': 1.0,
        'dailyCosts': daily_costs,
        'modelUsage': {}
    }


import re

def parse_activity_log() -> list:
    """解析 scheduler.log 提取结构化活动数据"""
    log_file = LOG_DIR / 'scheduler.log'
    if not log_file.exists():
        return []

    activities = []

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            i += 1

            if not line:
                continue

            # 解析时间戳: [2026-01-26 10:11:04]
            timestamp_match = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\](.+)', line)
            if not timestamp_match:
                continue

            timestamp = timestamp_match.group(1)
            content = timestamp_match.group(2).strip()

            # ===== 定时扫描 =====
            if '触发定时扫描' in content:
                activity = {
                    'time': timestamp[11:16],
                    'fullTime': timestamp,
                    'event': '定时扫描滴答清单',
                    'model': 'sonnet',
                    'result': 'pending',
                    'resultIcon': '⏳',
                    'resultText': ''
                }

                # 向后查找结果
                for j in range(i, min(i + 20, len(lines))):
                    next_line = lines[j].strip()
                    if 'Claude 执行完成' in next_line:
                        activity['result'] = 'completed'
                        activity['resultIcon'] = '✅'
                        activity['resultText'] = '完成'
                        break
                    elif 'Claude 执行超时' in next_line:
                        activity['result'] = 'timeout'
                        activity['resultIcon'] = '⏱️'
                        activity['resultText'] = '超时'
                        break
                    elif '触发定时扫描' in next_line or '收到 Telegram 消息' in next_line:
                        # 遇到下一个事件，当前未完成
                        break

                activities.append(activity)

            # ===== 收到 Telegram 消息 =====
            elif '收到 Telegram 消息' in content:
                # 解析消息内容
                event_type = 'Telegram 汇报'

                # 提取可执行任务数
                num_match = re.search(r'(\d+)\s*[件个条]可执行', content)
                if num_match:
                    event_type = f"发现 {num_match.group(1)} 件可执行任务"
                elif '没有' in content or '无新' in content or '无可' in content or '暂时没有' in content:
                    event_type = '汇报：无新任务'
                elif '扫描报告' in content or '报告' in content:
                    event_type = 'AI 助理扫描报告'
                elif '扫描完成' in content:
                    event_type = '扫描完成汇报'

                activity = {
                    'time': timestamp[11:16],
                    'fullTime': timestamp,
                    'event': event_type,
                    'model': 'haiku',
                    'result': 'pending',
                    'resultIcon': '⏳',
                    'resultText': ''
                }

                # 向后查找任务路由和结果
                for j in range(i, min(i + 15, len(lines))):
                    next_line = lines[j].strip()

                    # 任务路由
                    if '任务路由' in next_line:
                        if 'x-post' in next_line.lower() or '发推' in next_line:
                            activity['resultText'] = '发推'
                        elif 'xiaohongshu' in next_line.lower() or '小红书' in next_line:
                            activity['resultText'] = '小红书'
                        elif 'telegram' in next_line.lower():
                            activity['resultText'] = 'Telegram'

                    # 执行完成
                    elif 'Claude 执行完成' in next_line:
                        activity['result'] = 'completed'
                        activity['resultIcon'] = '✅'
                        if not activity['resultText']:
                            activity['resultText'] = '完成'
                        break

                    # 执行超时
                    elif 'Claude 执行超时' in next_line:
                        activity['result'] = 'timeout'
                        activity['resultIcon'] = '⏱️'
                        activity['resultText'] = '超时'
                        break

                    # 错误
                    elif '错误' in next_line or 'Error' in next_line or '失败' in next_line:
                        activity['result'] = 'failed'
                        activity['resultIcon'] = '❌'
                        if 'command not found' in next_line.lower() or 'claude 命令' in next_line:
                            activity['resultText'] = 'claude 命令找不到'
                        else:
                            activity['resultText'] = '失败'
                        break

                    # 遇到下一个事件
                    elif '触发定时扫描' in next_line or '收到 Telegram 消息' in next_line:
                        break

                activities.append(activity)

    except Exception as e:
        print(f"解析活动日志出错: {e}")

    # 按时间倒序
    activities.reverse()
    return activities[:50]


def get_activity_stats(activities: list) -> dict:
    """统计活动数据"""
    stats = {
        'scanCount': 0,
        'timeoutCount': 0,
        'executedTasks': 0,
        'failedCount': 0,
        'xhsCount': 0,
        'tweetCount': 0
    }

    for act in activities:
        event = act.get('event', '')
        result = act.get('result', '')
        result_text = act.get('resultText', '')

        if '定时扫描' in event:
            stats['scanCount'] += 1

        if result == 'timeout':
            stats['timeoutCount'] += 1

        if result == 'failed':
            stats['failedCount'] += 1

        # 统计发现的可执行任务
        if '发现' in event and '可执行' in event:
            # 提取数字
            num_match = re.search(r'(\d+)', event)
            if num_match:
                stats['executedTasks'] += int(num_match.group(1))

        # 统计小红书和发推
        if '小红书' in result_text:
            stats['xhsCount'] += 1
        if '发推' in result_text:
            stats['tweetCount'] += 1

    return stats


# ============================================
# 日志监控
# ============================================

class LogWatcher(threading.Thread):
    def __init__(self, socketio):
        super().__init__(daemon=True)
        self.socketio = socketio
        self.running = True
        self.last_position = 0

    def run(self):
        log_file = LOG_DIR / 'scheduler.log'
        while self.running:
            try:
                if log_file.exists():
                    with open(log_file, 'r', encoding='utf-8') as f:
                        f.seek(self.last_position)
                        new_lines = f.readlines()
                        self.last_position = f.tell()
                        for line in new_lines:
                            if line.strip():
                                self.socketio.emit('log', {
                                    'message': line.strip(),
                                    'timestamp': datetime.now().isoformat()
                                })
            except Exception as e:
                print(f"LogWatcher error: {e}")
            time.sleep(1)

    def stop(self):
        self.running = False


log_watcher = None


# ============================================
# HTML - 飞书风格 CEO 仪表盘 (增强版)
# ============================================

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 助理控制台</title>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #3370ff;
            --primary-light: #e8f0ff;
            --success: #34c724;
            --warning: #ff9f0a;
            --danger: #f54a45;
            --text-primary: #1f2329;
            --text-secondary: #646a73;
            --text-muted: #8f959e;
            --bg-body: #f5f6f7;
            --bg-card: #ffffff;
            --border: #dee0e3;
            --shadow: 0 1px 2px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.1);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-body);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
        }

        /* 侧边栏 */
        .sidebar {
            width: 240px;
            background: var(--bg-card);
            border-right: 1px solid var(--border);
            padding: 24px 0;
            display: flex;
            flex-direction: column;
            position: fixed;
            height: 100vh;
            left: 0;
            top: 0;
            z-index: 100;
        }

        .logo {
            padding: 0 24px 24px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 16px;
        }

        .logo h1 {
            font-size: 18px;
            font-weight: 700;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .logo-icon {
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, var(--primary) 0%, #6366f1 100%);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 16px;
        }

        .nav-item {
            padding: 12px 24px;
            display: flex;
            align-items: center;
            gap: 12px;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.15s;
            font-size: 14px;
            font-weight: 500;
            user-select: none;
        }

        .nav-item:hover { background: var(--bg-body); }
        .nav-item.active {
            background: var(--primary-light);
            color: var(--primary);
        }

        .nav-icon { font-size: 18px; width: 20px; text-align: center; }

        .nav-badge {
            margin-left: auto;
            background: var(--danger);
            color: white;
            font-size: 11px;
            padding: 2px 6px;
            border-radius: 10px;
            font-weight: 600;
        }

        .sidebar-footer {
            margin-top: auto;
            padding: 16px 24px;
            border-top: 1px solid var(--border);
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            color: var(--text-muted);
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        /* 主内容区 */
        .main {
            flex: 1;
            padding: 32px;
            overflow-y: auto;
            margin-left: 240px;
            min-height: 100vh;
        }

        .page { display: none; }
        .page.active { display: block; }

        .page-header {
            margin-bottom: 32px;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }

        .page-header-left {}

        .page-title {
            font-size: 24px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 8px;
        }

        .page-subtitle {
            font-size: 14px;
            color: var(--text-muted);
        }

        /* 统计卡片 */
        .stats-row {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 24px;
        }

        .stat-card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 20px;
            box-shadow: var(--shadow);
            cursor: pointer;
            transition: transform 0.15s, box-shadow 0.15s;
        }

        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        .stat-label {
            font-size: 13px;
            color: var(--text-muted);
            margin-bottom: 8px;
            font-weight: 500;
        }

        .stat-value {
            font-size: 32px;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1;
        }

        .stat-value.success { color: var(--success); }
        .stat-value.warning { color: var(--warning); }
        .stat-value.danger { color: var(--danger); }
        .stat-value.primary { color: var(--primary); }

        .stat-trend {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 8px;
        }

        .stat-trend.up { color: var(--success); }
        .stat-trend.down { color: var(--danger); }

        /* 内容网格 */
        .content-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }

        .card {
            background: var(--bg-card);
            border-radius: 12px;
            box-shadow: var(--shadow);
            overflow: hidden;
        }

        .card-header {
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .card-title {
            font-size: 15px;
            font-weight: 600;
            color: var(--text-primary);
        }

        .card-actions {
            display: flex;
            gap: 8px;
        }

        .card-body { padding: 20px; }

        /* 日志 */
        .log-box {
            background: #1e1e1e;
            border-radius: 8px;
            padding: 16px;
            height: 320px;
            overflow-y: auto;
            font-family: 'SF Mono', Monaco, 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.8;
        }

        .log-box.full-height {
            height: calc(100vh - 280px);
            min-height: 400px;
        }

        .log-line { color: #9da5b4; }
        .log-line.info { color: #98c379; }
        .log-line.error { color: #e06c75; }
        .log-line.warning { color: #e5c07b; }
        .log-line.debug { color: #61afef; }

        /* 任务列表 */
        .task-list { max-height: 320px; overflow-y: auto; }
        .task-list.full-height {
            max-height: calc(100vh - 400px);
            min-height: 300px;
        }

        .task-item {
            display: flex;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid var(--border);
            cursor: pointer;
            transition: background 0.15s;
            margin: 0 -20px;
            padding-left: 20px;
            padding-right: 20px;
        }

        .task-item:hover {
            background: var(--bg-body);
        }

        .task-item:last-child { border-bottom: none; }

        .task-status {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 12px;
            flex-shrink: 0;
        }

        .task-status.completed { background: var(--success); }
        .task-status.failed { background: var(--danger); }
        .task-status.skipped { background: var(--warning); }

        .task-info { flex: 1; min-width: 0; }
        .task-title {
            font-size: 14px;
            font-weight: 500;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .task-time {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 2px;
        }

        .task-arrow {
            color: var(--text-muted);
            font-size: 14px;
        }

        /* 快捷操作 */
        .action-group {
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
        }

        .btn {
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s;
            border: none;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        .btn-primary {
            background: var(--primary);
            color: white;
        }

        .btn-primary:hover { background: #2563eb; }

        .btn-secondary {
            background: var(--bg-body);
            color: var(--text-primary);
            border: 1px solid var(--border);
        }

        .btn-secondary:hover { background: #ebedf0; }

        .btn-sm {
            padding: 6px 12px;
            font-size: 13px;
        }

        .btn-icon {
            padding: 8px;
            border-radius: 6px;
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .input-group {
            display: flex;
            gap: 12px;
        }

        .input-group input, .input-group select {
            flex: 1;
            padding: 10px 14px;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.15s;
            background: white;
        }

        .input-group input:focus, .input-group select:focus {
            border-color: var(--primary);
        }

        /* 图表 */
        .chart-container { height: 200px; }

        /* 全宽卡片 */
        .card-full { grid-column: span 2; }

        /* 搜索和过滤栏 */
        .filter-bar {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }

        .filter-bar input, .filter-bar select {
            padding: 10px 14px;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 14px;
            outline: none;
            background: white;
        }

        .filter-bar input {
            flex: 1;
            min-width: 200px;
        }

        .filter-bar select {
            min-width: 120px;
        }

        .filter-bar input:focus, .filter-bar select:focus {
            border-color: var(--primary);
        }

        /* 标签 */
        .tag {
            display: inline-flex;
            align-items: center;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }

        .tag.success { background: #dcfce7; color: #16a34a; }
        .tag.warning { background: #fef3c7; color: #d97706; }
        .tag.danger { background: #fee2e2; color: #dc2626; }
        .tag.info { background: var(--primary-light); color: var(--primary); }

        /* 模态框 */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transition: all 0.2s;
        }

        .modal-overlay.active {
            opacity: 1;
            visibility: visible;
        }

        .modal {
            background: var(--bg-card);
            border-radius: 16px;
            width: 90%;
            max-width: 600px;
            max-height: 80vh;
            overflow: hidden;
            transform: scale(0.9);
            transition: transform 0.2s;
            display: flex;
            flex-direction: column;
        }

        .modal-overlay.active .modal {
            transform: scale(1);
        }

        .modal-header {
            padding: 20px 24px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-title {
            font-size: 18px;
            font-weight: 600;
        }

        .modal-close {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            border: none;
            background: var(--bg-body);
            cursor: pointer;
            font-size: 18px;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .modal-close:hover {
            background: var(--border);
        }

        .modal-body {
            padding: 24px;
            overflow-y: auto;
            flex: 1;
        }

        .modal-footer {
            padding: 16px 24px;
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: flex-end;
            gap: 12px;
        }

        /* 详情项 */
        .detail-item {
            margin-bottom: 20px;
        }

        .detail-label {
            font-size: 12px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }

        .detail-value {
            font-size: 14px;
            color: var(--text-primary);
            line-height: 1.6;
        }

        .detail-value pre {
            background: var(--bg-body);
            padding: 12px;
            border-radius: 8px;
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 12px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-all;
        }

        /* 成本统计 */
        .cost-overview {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 24px;
        }

        .cost-card {
            background: linear-gradient(135deg, var(--primary) 0%, #6366f1 100%);
            border-radius: 12px;
            padding: 24px;
            color: white;
        }

        .cost-card.secondary {
            background: var(--bg-card);
            color: var(--text-primary);
            box-shadow: var(--shadow);
        }

        .cost-label {
            font-size: 13px;
            opacity: 0.9;
            margin-bottom: 8px;
        }

        .cost-card.secondary .cost-label {
            color: var(--text-muted);
        }

        .cost-value {
            font-size: 28px;
            font-weight: 700;
        }

        .cost-card.secondary .cost-value {
            color: var(--text-primary);
        }

        .cost-trend {
            font-size: 12px;
            margin-top: 8px;
            opacity: 0.8;
        }

        /* 成本表格 */
        .cost-table {
            width: 100%;
            border-collapse: collapse;
        }

        .cost-table th, .cost-table td {
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }

        .cost-table th {
            font-size: 12px;
            color: var(--text-muted);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .cost-table td {
            font-size: 14px;
        }

        .cost-table tr:hover {
            background: var(--bg-body);
        }

        /* Toast 通知 */
        .toast-container {
            position: fixed;
            top: 24px;
            right: 24px;
            z-index: 2000;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .toast {
            background: var(--bg-card);
            border-radius: 8px;
            padding: 16px 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            gap: 12px;
            animation: slideIn 0.3s ease;
            max-width: 360px;
        }

        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        .toast-icon {
            font-size: 20px;
        }

        .toast-content {
            flex: 1;
        }

        .toast-title {
            font-weight: 600;
            font-size: 14px;
            margin-bottom: 2px;
        }

        .toast-message {
            font-size: 13px;
            color: var(--text-muted);
        }

        /* 响应式 */
        @media (max-width: 1200px) {
            .sidebar { width: 200px; }
            .main { margin-left: 200px; }
            .stats-row { grid-template-columns: repeat(2, 1fr); }
            .cost-overview { grid-template-columns: 1fr; }
        }

        @media (max-width: 900px) {
            .sidebar { display: none; }
            .main { margin-left: 0; }
            .content-grid { grid-template-columns: 1fr; }
            .card-full { grid-column: span 1; }
        }

        /* 空状态 */
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: var(--text-muted);
        }

        .empty-state-icon {
            font-size: 48px;
            margin-bottom: 16px;
            opacity: 0.5;
        }

        .empty-state-title {
            font-size: 16px;
            font-weight: 500;
            color: var(--text-secondary);
            margin-bottom: 8px;
        }

        .empty-state-desc {
            font-size: 14px;
        }

        /* CEO 助理页面布局 */
        .ceo-page-layout {
            display: grid;
            grid-template-columns: 380px 1fr;
            gap: 20px;
            height: calc(100vh - 180px);
            min-height: 500px;
        }

        .ceo-activities-panel {
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .panel-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
            flex-shrink: 0;
        }

        .panel-title {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
            margin: 0;
        }

        .panel-badge {
            background: var(--primary);
            color: white;
            font-size: 12px;
            padding: 2px 8px;
            border-radius: 10px;
        }

        .btn-icon {
            background: none;
            border: none;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 4px;
            opacity: 0.6;
            transition: all 0.2s;
        }

        .btn-icon:hover {
            opacity: 1;
            background: var(--bg-hover);
        }

        .ceo-activities-list {
            flex: 1;
            overflow-y: auto;
            padding: 12px;
        }

        .activity-loading {
            text-align: center;
            color: var(--text-muted);
            padding: 40px;
        }

        .activity-item {
            padding: 12px 14px;
            border-radius: 8px;
            margin-bottom: 8px;
            background: var(--bg-main);
            border-left: 3px solid var(--border);
            transition: all 0.2s;
        }

        .activity-item:hover {
            background: var(--bg-hover);
        }

        .activity-item.completed {
            border-left-color: #34c759;
        }

        .activity-item.skipped {
            border-left-color: #ff9500;
        }

        .activity-item.failed {
            border-left-color: #ff3b30;
        }

        .activity-title {
            font-size: 13px;
            font-weight: 500;
            color: var(--text-primary);
            margin-bottom: 6px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .activity-meta {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 11px;
            color: var(--text-muted);
        }

        .activity-status {
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 500;
        }

        .activity-status.completed {
            background: rgba(52, 199, 89, 0.15);
            color: #34c759;
        }

        .activity-status.skipped {
            background: rgba(255, 149, 0, 0.15);
            color: #ff9500;
        }

        .activity-status.failed {
            background: rgba(255, 59, 48, 0.15);
            color: #ff3b30;
        }

        .activity-summary {
            font-size: 11px;
            color: var(--text-secondary);
            margin-top: 6px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .activity-empty {
            text-align: center;
            padding: 40px 20px;
            color: var(--text-muted);
        }

        .activity-empty-icon {
            font-size: 32px;
            margin-bottom: 8px;
        }

        /* 聊天界面 */
        .chat-container {
            background: var(--bg-card);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .chat-welcome {
            text-align: center;
            padding: 60px 20px;
            color: var(--text-muted);
        }

        .chat-welcome-icon {
            font-size: 48px;
            margin-bottom: 16px;
        }

        .chat-welcome-title {
            font-size: 18px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 8px;
        }

        .chat-welcome-desc {
            font-size: 14px;
        }

        .chat-message {
            display: flex;
            gap: 12px;
            max-width: 85%;
        }

        .chat-message.user {
            align-self: flex-end;
            flex-direction: row-reverse;
        }

        .chat-message.assistant {
            align-self: flex-start;
        }

        .chat-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            flex-shrink: 0;
        }

        .chat-message.user .chat-avatar {
            background: var(--primary);
            color: white;
        }

        .chat-message.assistant .chat-avatar {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
        }

        .chat-bubble {
            padding: 12px 16px;
            border-radius: 16px;
            font-size: 14px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-word;
        }

        .chat-message.user .chat-bubble {
            background: var(--primary);
            color: white;
            border-bottom-right-radius: 4px;
        }

        .chat-message.assistant .chat-bubble {
            background: var(--bg-body);
            color: var(--text-primary);
            border-bottom-left-radius: 4px;
        }

        .chat-bubble.processing {
            color: var(--text-muted);
            font-style: italic;
        }

        .chat-bubble.error {
            background: #fee2e2;
            color: #dc2626;
        }

        .chat-bubble pre {
            background: rgba(0,0,0,0.05);
            padding: 12px;
            border-radius: 8px;
            overflow-x: auto;
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 12px;
            margin: 8px 0;
        }

        .chat-message.user .chat-bubble pre {
            background: rgba(255,255,255,0.15);
        }

        .chat-time {
            font-size: 11px;
            color: var(--text-muted);
            margin-top: 4px;
        }

        .chat-message.user .chat-time {
            text-align: right;
        }

        .chat-input-area {
            padding: 16px 24px 20px;
            border-top: 1px solid var(--border);
            background: var(--bg-card);
        }

        .chat-input-wrapper {
            display: flex;
            gap: 12px;
            align-items: flex-end;
        }

        .chat-input-wrapper textarea {
            flex: 1;
            padding: 12px 16px;
            border: 1px solid var(--border);
            border-radius: 12px;
            font-size: 14px;
            line-height: 1.5;
            resize: none;
            outline: none;
            max-height: 150px;
            font-family: inherit;
            transition: border-color 0.15s;
        }

        .chat-input-wrapper textarea:focus {
            border-color: var(--primary);
        }

        .chat-send-btn {
            padding: 12px 24px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.15s;
            white-space: nowrap;
        }

        .chat-send-btn:hover {
            background: #2563eb;
        }

        .chat-send-btn:disabled {
            background: var(--text-muted);
            cursor: not-allowed;
        }

        .chat-hint {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 8px;
            text-align: center;
        }

        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 8px 0;
        }

        .typing-indicator span {
            width: 8px;
            height: 8px;
            background: var(--text-muted);
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }

        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
            30% { transform: translateY(-4px); opacity: 1; }
        }
    </style>
</head>
<body>
    <!-- 侧边栏 -->
    <aside class="sidebar">
        <div class="logo">
            <h1>
                <span class="logo-icon">AI</span>
                助理控制台
            </h1>
        </div>

        <nav>
            <div class="nav-item active" data-page="dashboard">
                <span class="nav-icon">📊</span>
                仪表盘
            </div>
            <div class="nav-item" data-page="tasks">
                <span class="nav-icon">📋</span>
                任务管理
                <span class="nav-badge" id="failed-badge" style="display:none">0</span>
            </div>
            <div class="nav-item" data-page="logs">
                <span class="nav-icon">📜</span>
                执行日志
            </div>
            <div class="nav-item" data-page="cost">
                <span class="nav-icon">💰</span>
                成本追踪
            </div>
            <div class="nav-item" data-page="settings">
                <span class="nav-icon">⚙️</span>
                系统设置
            </div>
            <div class="nav-item" data-page="chat">
                <span class="nav-icon">🤖</span>
                CEO 助理
            </div>
        </nav>

        <div class="sidebar-footer">
            <div class="status-indicator">
                <span class="status-dot" id="status-dot"></span>
                <span id="status-text">系统运行中</span>
            </div>
        </div>
    </aside>

    <!-- 主内容 -->
    <main class="main">
        <!-- ========== 仪表盘页面 ========== -->
        <div class="page active" id="page-dashboard">
            <header class="page-header">
                <div class="page-header-left">
                    <h2 class="page-title">工作概览</h2>
                    <p class="page-subtitle">实时监控 AI 助理的所有活动</p>
                </div>
            </header>

            <!-- 统计卡片 -->
            <div class="stats-row">
                <div class="stat-card" onclick="navigateTo('tasks')">
                    <div class="stat-label">总任务数</div>
                    <div class="stat-value" id="stat-total">0</div>
                    <div class="stat-trend">累计处理</div>
                </div>
                <div class="stat-card" onclick="navigateTo('tasks', 'completed')">
                    <div class="stat-label">已完成</div>
                    <div class="stat-value success" id="stat-completed">0</div>
                    <div class="stat-trend">执行成功</div>
                </div>
                <div class="stat-card" onclick="navigateTo('tasks', 'skipped')">
                    <div class="stat-label">已跳过</div>
                    <div class="stat-value warning" id="stat-skipped">0</div>
                    <div class="stat-trend">需要更多信息</div>
                </div>
                <div class="stat-card" onclick="navigateTo('tasks', 'failed')">
                    <div class="stat-label">失败</div>
                    <div class="stat-value danger" id="stat-failed">0</div>
                    <div class="stat-trend">执行异常</div>
                </div>
            </div>

            <!-- 内容区 -->
            <div class="content-grid">
                <!-- 实时日志 -->
                <div class="card card-full">
                    <div class="card-header">
                        <span class="card-title">实时日志</span>
                        <div class="card-actions">
                            <button class="btn btn-secondary btn-sm" onclick="navigateTo('logs')">查看全部</button>
                            <button class="btn btn-secondary btn-sm" onclick="clearLogs()">清空</button>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="log-box" id="log-box"></div>
                    </div>
                </div>

                <!-- 快捷操作 -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">快捷指令</span>
                    </div>
                    <div class="card-body">
                        <div class="action-group">
                            <button class="btn btn-primary" onclick="triggerScan()">
                                <span>🔍</span> 扫描滴答清单
                            </button>
                            <button class="btn btn-secondary" onclick="refreshAll()">
                                <span>🔄</span> 刷新
                            </button>
                        </div>
                        <div class="input-group">
                            <input type="text" id="manual-task" placeholder="输入任务，让 AI 立即执行...">
                            <button class="btn btn-primary" onclick="executeTask()">执行</button>
                        </div>
                    </div>
                </div>

                <!-- 周趋势 -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">本周趋势</span>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="weeklyChart"></canvas>
                        </div>
                    </div>
                </div>

                <!-- 活动清单 -->
                <div class="card card-full">
                    <div class="card-header">
                        <span class="card-title">活动清单</span>
                        <div class="card-actions">
                            <span class="activity-time-range" id="activity-time-range" style="color:var(--text-muted);font-size:13px;margin-right:12px;">--</span>
                            <button class="btn btn-secondary btn-sm" onclick="sendTelegramReportWithChart()" title="发送带图表的报告到 Telegram">
                                <span>📊</span> 发送图表报告
                            </button>
                            <button class="btn btn-secondary btn-sm" onclick="refreshActivities()">刷新</button>
                        </div>
                    </div>
                    <div class="card-body" style="padding:0;">
                        <div class="activity-table-wrapper" style="max-height:400px;overflow-y:auto;">
                            <table class="activity-table" style="width:100%;border-collapse:collapse;">
                                <thead style="position:sticky;top:0;background:var(--bg-card);z-index:1;">
                                    <tr>
                                        <th style="width:70px;padding:12px 16px;text-align:left;font-size:12px;color:var(--text-muted);font-weight:500;border-bottom:1px solid var(--border);">时间</th>
                                        <th style="padding:12px 16px;text-align:left;font-size:12px;color:var(--text-muted);font-weight:500;border-bottom:1px solid var(--border);">事件</th>
                                        <th style="width:80px;padding:12px 16px;text-align:left;font-size:12px;color:var(--text-muted);font-weight:500;border-bottom:1px solid var(--border);">模型</th>
                                        <th style="width:140px;padding:12px 16px;text-align:left;font-size:12px;color:var(--text-muted);font-weight:500;border-bottom:1px solid var(--border);">结果</th>
                                    </tr>
                                </thead>
                                <tbody id="activity-table-body">
                                    <tr>
                                        <td colspan="4" style="text-align:center;color:var(--text-muted);padding:40px;">
                                            加载中...
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- 活动统计 -->
                <div class="card card-full">
                    <div class="card-header">
                        <span class="card-title">统计</span>
                        <button class="btn btn-secondary btn-sm" onclick="sendTelegramSummary()">
                            <span>📤</span> 发送到 Telegram
                        </button>
                    </div>
                    <div class="card-body">
                        <div style="display:flex;gap:24px;flex-wrap:wrap;">
                            <div style="flex:1;min-width:120px;">
                                <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">定时扫描</div>
                                <div style="font-size:20px;font-weight:600;" id="stat-scan-count">0 次</div>
                            </div>
                            <div style="flex:1;min-width:120px;">
                                <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">超时</div>
                                <div style="font-size:20px;font-weight:600;color:var(--warning);" id="stat-timeout-count">0 次</div>
                            </div>
                            <div style="flex:1;min-width:120px;">
                                <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">执行任务</div>
                                <div style="font-size:20px;font-weight:600;" id="stat-executed-count">0 件</div>
                            </div>
                            <div style="flex:1;min-width:120px;">
                                <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">小红书</div>
                                <div style="font-size:20px;font-weight:600;color:var(--success);" id="stat-xhs-count">0 次</div>
                            </div>
                            <div style="flex:1;min-width:120px;">
                                <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">发推</div>
                                <div style="font-size:20px;font-weight:600;color:var(--success);" id="stat-tweet-count">0 次</div>
                            </div>
                            <div style="flex:1;min-width:120px;">
                                <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">失败</div>
                                <div style="font-size:20px;font-weight:600;color:var(--danger);" id="stat-fail-count">0 次</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 任务历史 -->
                <div class="card card-full">
                    <div class="card-header">
                        <span class="card-title">滴答清单任务记录</span>
                        <button class="btn btn-secondary btn-sm" onclick="navigateTo('tasks')">查看全部</button>
                    </div>
                    <div class="card-body">
                        <div class="task-list" id="task-list-dashboard"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- ========== 任务管理页面 ========== -->
        <div class="page" id="page-tasks">
            <header class="page-header">
                <div class="page-header-left">
                    <h2 class="page-title">任务管理</h2>
                    <p class="page-subtitle">查看和管理所有已执行的任务</p>
                </div>
            </header>

            <div class="filter-bar">
                <input type="text" id="task-search" placeholder="搜索任务..." oninput="filterTasks()">
                <select id="task-filter-status" onchange="filterTasks()">
                    <option value="">全部状态</option>
                    <option value="completed">已完成</option>
                    <option value="skipped">已跳过</option>
                    <option value="failed">失败</option>
                </select>
                <select id="task-filter-date" onchange="filterTasks()">
                    <option value="">全部时间</option>
                    <option value="today">今天</option>
                    <option value="week">本周</option>
                    <option value="month">本月</option>
                </select>
            </div>

            <div class="card">
                <div class="card-body">
                    <div class="task-list full-height" id="task-list-full"></div>
                </div>
            </div>
        </div>

        <!-- ========== 执行日志页面 ========== -->
        <div class="page" id="page-logs">
            <header class="page-header">
                <div class="page-header-left">
                    <h2 class="page-title">执行日志</h2>
                    <p class="page-subtitle">查看详细的系统运行日志</p>
                </div>
                <div class="action-group">
                    <button class="btn btn-secondary" onclick="downloadLogs()">
                        <span>📥</span> 导出日志
                    </button>
                    <button class="btn btn-secondary" onclick="clearAllLogs()">
                        <span>🗑️</span> 清空日志
                    </button>
                </div>
            </header>

            <div class="filter-bar">
                <input type="text" id="log-search" placeholder="搜索日志..." oninput="filterLogs()">
                <select id="log-filter-level" onchange="filterLogs()">
                    <option value="">全部级别</option>
                    <option value="info">信息</option>
                    <option value="warning">警告</option>
                    <option value="error">错误</option>
                </select>
            </div>

            <div class="card">
                <div class="card-body">
                    <div class="log-box full-height" id="log-box-full"></div>
                </div>
            </div>
        </div>

        <!-- ========== 成本追踪页面 ========== -->
        <div class="page" id="page-cost">
            <header class="page-header">
                <div class="page-header-left">
                    <h2 class="page-title">成本追踪</h2>
                    <p class="page-subtitle">监控 AI 调用费用和资源使用</p>
                </div>
            </header>

            <div class="cost-overview">
                <div class="cost-card">
                    <div class="cost-label">本月总费用</div>
                    <div class="cost-value" id="cost-total">$0.00</div>
                    <div class="cost-trend" id="cost-trend">较上月 --</div>
                </div>
                <div class="cost-card secondary">
                    <div class="cost-label">今日费用</div>
                    <div class="cost-value" id="cost-today">$0.00</div>
                    <div class="cost-trend">预估本月 $0.00</div>
                </div>
                <div class="cost-card secondary">
                    <div class="cost-label">总调用次数</div>
                    <div class="cost-value" id="cost-calls">0</div>
                    <div class="cost-trend">平均 $0.00/次</div>
                </div>
            </div>

            <div class="content-grid">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">费用趋势</span>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="costChart"></canvas>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <span class="card-title">模型使用分布</span>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="modelChart"></canvas>
                        </div>
                    </div>
                </div>

                <div class="card card-full">
                    <div class="card-header">
                        <span class="card-title">费用明细</span>
                    </div>
                    <div class="card-body">
                        <table class="cost-table">
                            <thead>
                                <tr>
                                    <th>日期</th>
                                    <th>任务数</th>
                                    <th>输入 Token</th>
                                    <th>输出 Token</th>
                                    <th>费用</th>
                                </tr>
                            </thead>
                            <tbody id="cost-table-body">
                                <tr>
                                    <td colspan="5" style="text-align:center;color:var(--text-muted);padding:40px;">
                                        暂无费用数据
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- ========== 系统设置页面 ========== -->
        <div class="page" id="page-settings">
            <header class="page-header">
                <div class="page-header-left">
                    <h2 class="page-title">系统设置</h2>
                    <p class="page-subtitle">配置 AI 助理的运行参数</p>
                </div>
            </header>

            <div class="content-grid">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">调度设置</span>
                    </div>
                    <div class="card-body">
                        <div class="detail-item">
                            <div class="detail-label">扫描间隔</div>
                            <div class="input-group">
                                <select id="scan-interval">
                                    <option value="5">5 分钟</option>
                                    <option value="10">10 分钟</option>
                                    <option value="15" selected>15 分钟</option>
                                    <option value="30">30 分钟</option>
                                    <option value="60">1 小时</option>
                                </select>
                            </div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">启用自动执行</div>
                            <div class="input-group">
                                <label style="display:flex;align-items:center;gap:8px;cursor:pointer">
                                    <input type="checkbox" id="auto-execute" checked style="width:18px;height:18px">
                                    <span>自动执行检测到的任务</span>
                                </label>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <span class="card-title">通知设置</span>
                    </div>
                    <div class="card-body">
                        <div class="detail-item">
                            <div class="detail-label">任务完成通知</div>
                            <div class="input-group">
                                <label style="display:flex;align-items:center;gap:8px;cursor:pointer">
                                    <input type="checkbox" id="notify-complete" checked style="width:18px;height:18px">
                                    <span>任务完成时发送通知</span>
                                </label>
                            </div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">失败通知</div>
                            <div class="input-group">
                                <label style="display:flex;align-items:center;gap:8px;cursor:pointer">
                                    <input type="checkbox" id="notify-failed" checked style="width:18px;height:18px">
                                    <span>任务失败时发送通知</span>
                                </label>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card card-full">
                    <div class="card-header">
                        <span class="card-title">系统信息</span>
                    </div>
                    <div class="card-body">
                        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:20px;">
                            <div class="detail-item">
                                <div class="detail-label">版本</div>
                                <div class="detail-value">1.0.0</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">运行时间</div>
                                <div class="detail-value" id="uptime">--</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">最后扫描</div>
                                <div class="detail-value" id="last-scan">--</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- ========== CEO 助理页面 ========== -->
        <div class="page" id="page-chat">
            <header class="page-header">
                <div class="page-header-left">
                    <h2 class="page-title">CEO 助理</h2>
                    <p class="page-subtitle">永久驻留的 AI 调度器 · Session: 9826a95e</p>
                </div>
                <div class="action-group">
                    <button class="btn btn-secondary" onclick="refreshCeoActivities()">
                        <span>🔄</span> 刷新
                    </button>
                </div>
            </header>

            <div class="ceo-page-layout">
                <!-- 左侧：最近活动 -->
                <div class="card ceo-activities-panel">
                    <div class="panel-header">
                        <h3 class="panel-title">📋 最近活动</h3>
                        <span class="panel-badge" id="activity-count">0</span>
                    </div>
                    <div class="ceo-activities-list" id="ceo-activities-list">
                        <div class="activity-loading">加载中...</div>
                    </div>
                </div>

                <!-- 右侧：对话 -->
                <div class="card chat-container">
                    <div class="panel-header">
                        <h3 class="panel-title">💬 与助理对话</h3>
                        <button class="btn-icon" onclick="clearChatHistory()" title="清空记录">🗑️</button>
                    </div>
                    <!-- 消息列表 -->
                    <div class="chat-messages" id="chat-messages">
                        <div class="chat-welcome">
                            <div class="chat-welcome-icon">🤖</div>
                            <div class="chat-welcome-title">CEO 助理</div>
                            <div class="chat-welcome-desc">发送消息，我会帮你执行任务</div>
                        </div>
                    </div>

                    <!-- 输入区 -->
                    <div class="chat-input-area">
                        <div class="chat-input-wrapper">
                            <textarea
                                id="chat-input"
                                placeholder="输入消息，按 Enter 发送..."
                                rows="1"
                                onkeydown="handleChatKeydown(event)"
                                oninput="autoResizeTextarea(this)"
                            ></textarea>
                            <button class="chat-send-btn" id="chat-send-btn" onclick="sendChatMessage()">
                                <span>发送</span>
                            </button>
                        </div>
                        <div class="chat-hint">Shift+Enter 换行 · 执行可能需要数分钟</div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <!-- 任务详情模态框 -->
    <div class="modal-overlay" id="task-modal">
        <div class="modal">
            <div class="modal-header">
                <h3 class="modal-title">任务详情</h3>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body" id="task-modal-body">
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeModal()">关闭</button>
                <button class="btn btn-primary" onclick="retryTask()">重新执行</button>
            </div>
        </div>
    </div>

    <!-- Toast 容器 -->
    <div class="toast-container" id="toast-container"></div>

    <script>
        const socket = io();
        let weeklyChart = null;
        let costChart = null;
        let modelChart = null;
        let allTasks = [];
        let allLogs = [];
        let currentTaskId = null;
        const startTime = Date.now();

        // ========== Socket 事件 ==========
        socket.on('connect', () => {
            document.getElementById('status-dot').style.background = '#34c724';
            document.getElementById('status-text').textContent = '系统运行中';
        });

        socket.on('disconnect', () => {
            document.getElementById('status-dot').style.background = '#f54a45';
            document.getElementById('status-text').textContent = '连接已断开';
        });

        socket.on('log', (data) => {
            addLog(data.message);
            allLogs.push({ message: data.message, timestamp: data.timestamp });
        });

        socket.on('task_update', (data) => {
            showToast('任务更新', data.title + ' - ' + data.status, data.status === 'completed' ? 'success' : 'warning');
            refreshAll();
        });

        // ========== 导航 ==========
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                const page = item.dataset.page;
                if (page) navigateTo(page);
            });
        });

        function navigateTo(page, filter = null) {
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            document.querySelector(`.nav-item[data-page="${page}"]`)?.classList.add('active');

            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.getElementById(`page-${page}`)?.classList.add('active');

            if (page === 'tasks' && filter) {
                document.getElementById('task-filter-status').value = filter;
                filterTasks();
            }

            if (page === 'logs') {
                renderFullLogs();
            }

            if (page === 'cost') {
                loadCostData();
            }

            if (page === 'chat') {
                loadCeoActivities();
            }
        }

        // ========== CEO 助理活动 ==========
        async function loadCeoActivities() {
            const listEl = document.getElementById('ceo-activities-list');
            const countEl = document.getElementById('activity-count');

            try {
                const resp = await fetch('/api/ceo/activities');
                const data = await resp.json();

                if (data.activities && data.activities.length > 0) {
                    countEl.textContent = data.activities.length;
                    listEl.innerHTML = data.activities.map(act => `
                        <div class="activity-item ${act.status}">
                            <div class="activity-title">${escapeHtml(act.title)}</div>
                            <div class="activity-meta">
                                <span class="activity-status ${act.status}">${getStatusText(act.status)}</span>
                                <span>${act.time}</span>
                            </div>
                            ${act.summary ? `<div class="activity-summary">${escapeHtml(act.summary)}</div>` : ''}
                        </div>
                    `).join('');
                } else {
                    countEl.textContent = '0';
                    listEl.innerHTML = `
                        <div class="activity-empty">
                            <div class="activity-empty-icon">📭</div>
                            <div>暂无活动记录</div>
                        </div>
                    `;
                }
            } catch (err) {
                listEl.innerHTML = `<div class="activity-loading">加载失败: ${err.message}</div>`;
            }
        }

        function refreshCeoActivities() {
            loadCeoActivities();
            showToast('刷新', '活动列表已更新', 'info');
        }

        function getStatusText(status) {
            const map = {
                'completed': '已完成',
                'skipped': '已跳过',
                'failed': '失败'
            };
            return map[status] || status;
        }

        // ========== AI 对话 ==========
        let chatHistory = [];
        let isProcessing = false;

        function handleChatKeydown(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendChatMessage();
            }
        }

        function autoResizeTextarea(textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
        }

        function addChatMessage(role, content, isError = false) {
            const messagesDiv = document.getElementById('chat-messages');
            const welcome = messagesDiv.querySelector('.chat-welcome');
            if (welcome) welcome.remove();

            const now = new Date();
            const timeStr = now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });

            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${role}`;

            const avatar = role === 'user' ? '👤' : '🤖';
            const bubbleClass = isError ? 'chat-bubble error' : 'chat-bubble';

            messageDiv.innerHTML = `
                <div class="chat-avatar">${avatar}</div>
                <div>
                    <div class="${bubbleClass}">${escapeHtml(content)}</div>
                    <div class="chat-time">${timeStr}</div>
                </div>
            `;

            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;

            return messageDiv;
        }

        function addProcessingMessage() {
            const messagesDiv = document.getElementById('chat-messages');
            const welcome = messagesDiv.querySelector('.chat-welcome');
            if (welcome) welcome.remove();

            const messageDiv = document.createElement('div');
            messageDiv.className = 'chat-message assistant';
            messageDiv.id = 'processing-message';

            messageDiv.innerHTML = `
                <div class="chat-avatar">🤖</div>
                <div>
                    <div class="chat-bubble processing">
                        <div class="typing-indicator">
                            <span></span><span></span><span></span>
                        </div>
                        正在执行...
                    </div>
                </div>
            `;

            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function removeProcessingMessage() {
            const processing = document.getElementById('processing-message');
            if (processing) processing.remove();
        }

        async function sendChatMessage() {
            const input = document.getElementById('chat-input');
            const message = input.value.trim();

            if (!message || isProcessing) return;

            isProcessing = true;
            const sendBtn = document.getElementById('chat-send-btn');
            sendBtn.disabled = true;
            input.value = '';
            input.style.height = 'auto';

            // 添加用户消息
            addChatMessage('user', message);
            chatHistory.push({ role: 'user', content: message });

            // 添加处理中提示
            addProcessingMessage();

            try {
                const resp = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message })
                });

                const data = await resp.json();
                removeProcessingMessage();

                if (data.success) {
                    addChatMessage('assistant', data.result);
                    chatHistory.push({ role: 'assistant', content: data.result });
                } else {
                    addChatMessage('assistant', data.error || '执行失败', true);
                }
            } catch (err) {
                removeProcessingMessage();
                addChatMessage('assistant', '请求失败: ' + err.message, true);
            }

            isProcessing = false;
            sendBtn.disabled = false;
            input.focus();
        }

        async function clearChatHistory() {
            if (confirm('确定要清空聊天记录并重置会话吗？这将开启一个全新的对话，Claude 不会记得之前的内容。')) {
                // 重置后端会话
                try {
                    await fetch('/api/chat/reset', { method: 'POST' });
                } catch (e) {
                    console.error('重置会话失败:', e);
                }

                // 清空前端
                chatHistory = [];
                const messagesDiv = document.getElementById('chat-messages');
                messagesDiv.innerHTML = `
                    <div class="chat-welcome">
                        <div class="chat-welcome-icon">🤖</div>
                        <div class="chat-welcome-title">Claude 助理</div>
                        <div class="chat-welcome-desc">发送消息，我会帮你执行任务</div>
                    </div>
                `;
                showToast('会话已重置', '开始全新对话', 'info');
            }
        }

        // ========== 日志 ==========
        function addLog(message, target = 'log-box') {
            const logBox = document.getElementById(target);
            if (!logBox) return;

            const line = document.createElement('div');
            line.className = 'log-line';
            line.dataset.message = message.toLowerCase();

            if (message.includes('错误') || message.includes('Error') || message.includes('失败')) {
                line.classList.add('error');
                line.dataset.level = 'error';
            } else if (message.includes('警告') || message.includes('Warning')) {
                line.classList.add('warning');
                line.dataset.level = 'warning';
            } else if (message.includes('完成') || message.includes('成功') || message.includes('启动')) {
                line.classList.add('info');
                line.dataset.level = 'info';
            } else {
                line.dataset.level = 'debug';
            }

            line.textContent = message;
            logBox.appendChild(line);
            logBox.scrollTop = logBox.scrollHeight;

            while (logBox.children.length > 500) {
                logBox.removeChild(logBox.firstChild);
            }
        }

        function clearLogs() {
            document.getElementById('log-box').innerHTML = '';
        }

        function clearAllLogs() {
            if (confirm('确定要清空所有日志吗？')) {
                allLogs = [];
                document.getElementById('log-box').innerHTML = '';
                document.getElementById('log-box-full').innerHTML = '';
                showToast('日志已清空', '所有日志记录已被清除', 'info');
            }
        }

        function renderFullLogs() {
            const logBox = document.getElementById('log-box-full');
            logBox.innerHTML = '';
            allLogs.forEach(log => addLog(log.message, 'log-box-full'));
        }

        function filterLogs() {
            const search = document.getElementById('log-search').value.toLowerCase();
            const level = document.getElementById('log-filter-level').value;

            document.querySelectorAll('#log-box-full .log-line').forEach(line => {
                const matchSearch = !search || line.dataset.message.includes(search);
                const matchLevel = !level || line.dataset.level === level;
                line.style.display = matchSearch && matchLevel ? '' : 'none';
            });
        }

        function downloadLogs() {
            const content = allLogs.map(l => `[${l.timestamp}] ${l.message}`).join('\\n');
            const blob = new Blob([content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `ai-assistant-logs-${new Date().toISOString().slice(0,10)}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        }

        async function loadInitialLogs() {
            const resp = await fetch('/api/logs');
            const logs = await resp.json();
            logs.forEach(log => {
                addLog(log);
                allLogs.push({ message: log, timestamp: new Date().toISOString() });
            });
        }

        // ========== 统计 ==========
        async function refreshStats() {
            const resp = await fetch('/api/stats');
            const stats = await resp.json();

            document.getElementById('stat-total').textContent = stats.total;
            document.getElementById('stat-completed').textContent = stats.statusCount.completed;
            document.getElementById('stat-failed').textContent = stats.statusCount.failed;
            document.getElementById('stat-skipped').textContent = stats.statusCount.skipped;

            // 更新失败任务徽章
            const badge = document.getElementById('failed-badge');
            if (stats.statusCount.failed > 0) {
                badge.textContent = stats.statusCount.failed;
                badge.style.display = '';
            } else {
                badge.style.display = 'none';
            }

            document.getElementById('last-scan').textContent = stats.lastRunAt || '从未';

            updateWeeklyChart(stats.weeklyData);
        }

        function updateWeeklyChart(data) {
            const ctx = document.getElementById('weeklyChart').getContext('2d');

            if (weeklyChart) weeklyChart.destroy();

            weeklyChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.map(d => d.date.slice(5)),
                    datasets: [{
                        label: '任务数',
                        data: data.map(d => d.count),
                        backgroundColor: '#3370ff',
                        borderRadius: 4,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, ticks: { stepSize: 1 } }
                    }
                }
            });
        }

        // ========== 任务 ==========
        async function loadTaskHistory() {
            const resp = await fetch('/api/tasks');
            allTasks = await resp.json();
            renderTaskList('task-list-dashboard', allTasks.slice(0, 10));
            renderTaskList('task-list-full', allTasks);
        }

        function renderTaskList(targetId, tasks) {
            const list = document.getElementById(targetId);
            if (!list) return;

            if (tasks.length === 0) {
                list.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">📋</div>
                        <div class="empty-state-title">暂无任务记录</div>
                        <div class="empty-state-desc">执行的任务将在这里显示</div>
                    </div>
                `;
                return;
            }

            list.innerHTML = tasks.map(task => `
                <div class="task-item" onclick="showTaskDetail('${task.id}')">
                    <div class="task-status ${task.status}"></div>
                    <div class="task-info">
                        <div class="task-title">${escapeHtml(task.title || task.id)}</div>
                        <div class="task-time">${task.processedAt ? task.processedAt.replace('T', ' ').slice(0, 19) : '未知'}</div>
                    </div>
                    <span class="task-arrow">›</span>
                </div>
            `).join('');
        }

        function filterTasks() {
            const search = document.getElementById('task-search').value.toLowerCase();
            const status = document.getElementById('task-filter-status').value;
            const dateRange = document.getElementById('task-filter-date').value;

            const now = new Date();
            const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
            const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
            const monthAgo = new Date(today.getFullYear(), today.getMonth() - 1, today.getDate());

            const filtered = allTasks.filter(task => {
                const matchSearch = !search ||
                    (task.title && task.title.toLowerCase().includes(search)) ||
                    task.id.toLowerCase().includes(search);

                const matchStatus = !status || task.status === status;

                let matchDate = true;
                if (dateRange && task.processedAt) {
                    const taskDate = new Date(task.processedAt);
                    if (dateRange === 'today') matchDate = taskDate >= today;
                    else if (dateRange === 'week') matchDate = taskDate >= weekAgo;
                    else if (dateRange === 'month') matchDate = taskDate >= monthAgo;
                }

                return matchSearch && matchStatus && matchDate;
            });

            renderTaskList('task-list-full', filtered);
        }

        function showTaskDetail(taskId) {
            const task = allTasks.find(t => t.id === taskId);
            if (!task) return;

            currentTaskId = taskId;

            const statusMap = {
                completed: { text: '已完成', class: 'success' },
                failed: { text: '失败', class: 'danger' },
                skipped: { text: '已跳过', class: 'warning' }
            };
            const statusInfo = statusMap[task.status] || { text: task.status, class: 'info' };

            document.getElementById('task-modal-body').innerHTML = `
                <div class="detail-item">
                    <div class="detail-label">任务 ID</div>
                    <div class="detail-value">${escapeHtml(task.id)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">标题</div>
                    <div class="detail-value">${escapeHtml(task.title || '无标题')}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">状态</div>
                    <div class="detail-value">
                        <span class="tag ${statusInfo.class}">${statusInfo.text}</span>
                    </div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">执行时间</div>
                    <div class="detail-value">${task.processedAt ? task.processedAt.replace('T', ' ') : '未知'}</div>
                </div>
                ${task.reason ? `
                <div class="detail-item">
                    <div class="detail-label">备注/原因</div>
                    <div class="detail-value"><pre>${escapeHtml(task.reason)}</pre></div>
                </div>
                ` : ''}
            `;

            document.getElementById('task-modal').classList.add('active');
        }

        function closeModal() {
            document.getElementById('task-modal').classList.remove('active');
            currentTaskId = null;
        }

        async function retryTask() {
            if (!currentTaskId) return;
            const task = allTasks.find(t => t.id === currentTaskId);
            if (task && task.title) {
                closeModal();
                document.getElementById('manual-task').value = task.title;
                executeTask();
            }
        }

        // ========== 操作 ==========
        async function triggerScan() {
            const btn = event.target.closest('button');
            btn.disabled = true;
            const originalText = btn.innerHTML;
            btn.innerHTML = '<span>⏳</span> 扫描中...';

            try {
                const resp = await fetch('/api/scan', { method: 'POST' });
                const result = await resp.json();
                addLog('[控制台] ' + result.message);
                showToast('扫描启动', result.message, 'success');
            } catch (e) {
                addLog('[控制台] 扫描失败: ' + e.message);
                showToast('扫描失败', e.message, 'error');
            }

            btn.disabled = false;
            btn.innerHTML = originalText;

            setTimeout(refreshAll, 3000);
        }

        async function executeTask() {
            const input = document.getElementById('manual-task');
            const task = input.value.trim();

            if (!task) {
                showToast('请输入任务', '任务内容不能为空', 'warning');
                return;
            }

            const btn = event.target.closest('button');
            btn.disabled = true;
            btn.textContent = '执行中...';

            try {
                const resp = await fetch('/api/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ task })
                });
                const result = await resp.json();
                addLog('[控制台] 任务已提交: ' + task);
                showToast('任务已提交', task.slice(0, 30) + '...', 'success');
            } catch (e) {
                addLog('[控制台] 执行失败: ' + e.message);
                showToast('执行失败', e.message, 'error');
            }

            btn.disabled = false;
            btn.textContent = '执行';
            input.value = '';
        }

        function refreshAll() {
            refreshStats();
            loadTaskHistory();
        }

        // ========== 成本 ==========
        async function loadCostData() {
            try {
                const resp = await fetch('/api/cost');
                const data = await resp.json();

                document.getElementById('cost-total').textContent = '$' + (data.totalCost || 0).toFixed(2);
                document.getElementById('cost-today').textContent = '$' + (data.todayCost || 0).toFixed(2);
                document.getElementById('cost-calls').textContent = data.totalCalls || 0;

                if (data.trend) {
                    const trendEl = document.getElementById('cost-trend');
                    const trendValue = ((data.trend - 1) * 100).toFixed(0);
                    trendEl.textContent = `较上月 ${trendValue >= 0 ? '+' : ''}${trendValue}%`;
                    trendEl.className = 'cost-trend ' + (trendValue >= 0 ? 'up' : 'down');
                }

                updateCostChart(data.dailyCosts || []);
                updateModelChart(data.modelUsage || {});
                renderCostTable(data.dailyCosts || []);
            } catch (e) {
                console.error('Failed to load cost data:', e);
            }
        }

        function updateCostChart(data) {
            const ctx = document.getElementById('costChart').getContext('2d');
            if (costChart) costChart.destroy();

            costChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.map(d => d.date.slice(5)),
                    datasets: [{
                        label: '费用 ($)',
                        data: data.map(d => d.cost),
                        borderColor: '#3370ff',
                        backgroundColor: 'rgba(51, 112, 255, 0.1)',
                        fill: true,
                        tension: 0.4,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        }

        function updateModelChart(data) {
            const ctx = document.getElementById('modelChart').getContext('2d');
            if (modelChart) modelChart.destroy();

            const labels = Object.keys(data);
            const values = Object.values(data);

            if (labels.length === 0) {
                labels.push('暂无数据');
                values.push(1);
            }

            modelChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: ['#3370ff', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef'],
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom' }
                    }
                }
            });
        }

        function renderCostTable(data) {
            const tbody = document.getElementById('cost-table-body');
            if (data.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="5" style="text-align:center;color:var(--text-muted);padding:40px;">
                            暂无费用数据
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = data.slice(0, 10).map(d => `
                <tr>
                    <td>${d.date}</td>
                    <td>${d.tasks || 0}</td>
                    <td>${(d.inputTokens || 0).toLocaleString()}</td>
                    <td>${(d.outputTokens || 0).toLocaleString()}</td>
                    <td>$${(d.cost || 0).toFixed(4)}</td>
                </tr>
            `).join('');
        }

        // ========== Toast ==========
        function showToast(title, message, type = 'info') {
            const container = document.getElementById('toast-container');
            const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };

            const toast = document.createElement('div');
            toast.className = 'toast';
            toast.innerHTML = `
                <span class="toast-icon">${icons[type]}</span>
                <div class="toast-content">
                    <div class="toast-title">${escapeHtml(title)}</div>
                    <div class="toast-message">${escapeHtml(message)}</div>
                </div>
            `;

            container.appendChild(toast);

            setTimeout(() => {
                toast.style.animation = 'slideIn 0.3s ease reverse';
                setTimeout(() => toast.remove(), 300);
            }, 4000);
        }

        // ========== 工具函数 ==========
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function updateUptime() {
            const elapsed = Date.now() - startTime;
            const hours = Math.floor(elapsed / 3600000);
            const minutes = Math.floor((elapsed % 3600000) / 60000);
            document.getElementById('uptime').textContent = `${hours}小时 ${minutes}分钟`;
        }

        // ========== 键盘事件 ==========
        document.getElementById('manual-task').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') executeTask();
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeModal();
        });

        document.getElementById('task-modal').addEventListener('click', (e) => {
            if (e.target.id === 'task-modal') closeModal();
        });

        // ========== 活动清单 ==========
        let allActivities = [];

        async function refreshActivities() {
            try {
                const resp = await fetch('/api/activities');
                const data = await resp.json();
                allActivities = data.activities || [];
                renderActivities(allActivities);
                updateActivityStats(data.stats || {});
            } catch (e) {
                console.error('Failed to load activities:', e);
            }
        }

        function renderActivities(activities) {
            const tbody = document.getElementById('activity-table-body');

            if (activities.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="4" style="text-align:center;color:var(--text-muted);padding:40px;">
                            暂无活动记录
                        </td>
                    </tr>
                `;
                document.getElementById('activity-time-range').textContent = '--';
                return;
            }

            // 计算时间范围
            const firstTime = activities[activities.length - 1]?.time || '--';
            const lastTime = activities[0]?.time || '--';
            document.getElementById('activity-time-range').textContent = `${firstTime} - ${lastTime}`;

            tbody.innerHTML = activities.map(act => {
                const resultClass = act.result === 'completed' ? 'success' :
                                   act.result === 'timeout' ? 'warning' :
                                   act.result === 'failed' ? 'danger' : '';
                const resultStyle = resultClass ? `color:var(--${resultClass})` : '';

                return `
                    <tr style="border-bottom:1px solid var(--border);">
                        <td style="padding:12px 16px;font-size:14px;font-weight:500;">${act.time}</td>
                        <td style="padding:12px 16px;font-size:14px;">${escapeHtml(act.event)}</td>
                        <td style="padding:12px 16px;font-size:13px;">
                            <span style="background:${act.model === 'sonnet' ? '#e8f0ff' : '#f3f4f6'};color:${act.model === 'sonnet' ? 'var(--primary)' : 'var(--text-secondary)'};padding:2px 8px;border-radius:4px;font-weight:500;">${act.model}</span>
                        </td>
                        <td style="padding:12px 16px;font-size:14px;${resultStyle}">
                            ${act.resultIcon || ''} ${act.resultText || ''}
                        </td>
                    </tr>
                `;
            }).join('');
        }

        function updateActivityStats(stats) {
            document.getElementById('stat-scan-count').textContent = (stats.scanCount || 0) + ' 次';
            document.getElementById('stat-timeout-count').textContent = (stats.timeoutCount || 0) + ' 次';
            document.getElementById('stat-executed-count').textContent = '~' + (stats.executedTasks || 0) + ' 件';
            document.getElementById('stat-xhs-count').textContent = (stats.xhsCount || 0) + ' 次';
            document.getElementById('stat-tweet-count').textContent = (stats.tweetCount || 0) + ' 次';
            document.getElementById('stat-fail-count').textContent = (stats.failedCount || 0) + ' 次';
        }

        // ========== Telegram 通知 ==========
        async function sendTelegramSummary() {
            const btn = event.target.closest('button');
            btn.disabled = true;
            const originalText = btn.innerHTML;
            btn.innerHTML = '<span>⏳</span> 发送中...';

            try {
                const resp = await fetch('/api/telegram/summary', { method: 'POST' });
                const result = await resp.json();

                if (result.success) {
                    showToast('发送成功', result.message, 'success');
                } else {
                    showToast('发送失败', result.message, 'error');
                }
            } catch (e) {
                showToast('发送失败', e.message, 'error');
            }

            btn.disabled = false;
            btn.innerHTML = originalText;
        }

        async function sendTelegramMessage(message) {
            try {
                const resp = await fetch('/api/telegram/message', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message })
                });
                const result = await resp.json();

                if (result.success) {
                    showToast('发送成功', '消息已发送到 Telegram', 'success');
                } else {
                    showToast('发送失败', result.message, 'error');
                }
            } catch (e) {
                showToast('发送失败', e.message, 'error');
            }
        }

        async function sendTelegramReportWithChart() {
            const btn = event.target.closest('button');
            btn.disabled = true;
            const originalText = btn.innerHTML;
            btn.innerHTML = '<span>⏳</span> 生成中...';

            try {
                const resp = await fetch('/api/telegram/report-with-chart', { method: 'POST' });
                const result = await resp.json();

                if (result.success) {
                    showToast('发送成功', '带图表的报告已发送到 Telegram', 'success');
                } else {
                    showToast('发送失败', result.message, 'error');
                }
            } catch (e) {
                showToast('发送失败', e.message, 'error');
            }

            btn.disabled = false;
            btn.innerHTML = originalText;
        }

        // ========== 初始化 ==========
        loadInitialLogs();
        refreshStats();
        loadTaskHistory();
        refreshActivities();
        updateUptime();

        setInterval(refreshStats, 60000);
        setInterval(loadTaskHistory, 30000);
        setInterval(refreshActivities, 30000);
        setInterval(updateUptime, 60000);
    </script>
</body>
</html>
'''


# ============================================
# API
# ============================================

@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML)


@app.route('/api/logs')
def api_logs():
    logs = read_recent_logs(100)
    return jsonify([line.strip() for line in logs if line.strip()])


@app.route('/api/stats')
def api_stats():
    return jsonify(get_statistics())


@app.route('/api/tasks')
def api_tasks():
    return jsonify(get_task_history())


@app.route('/api/ceo/activities')
def api_ceo_activities():
    """获取 CEO 助理最近活动 - 从 state.json 读取"""
    try:
        state_file = SKILL_DIR / 'state.json'
        if not state_file.exists():
            return jsonify({'activities': []})

        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)

        processed = state.get('processedTasks', {})

        # 转换为列表并按时间排序
        activities = []
        for task_id, info in processed.items():
            processed_at = info.get('processedAt', '')
            # 解析时间显示
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(processed_at.replace('Z', '+00:00'))
                time_str = dt.strftime('%m-%d %H:%M')
            except:
                time_str = processed_at[:16] if processed_at else '--'

            activities.append({
                'id': task_id,
                'title': info.get('title', '未知任务'),
                'status': info.get('status', 'completed'),
                'time': time_str,
                'summary': info.get('summary', info.get('reason', ''))
            })

        # 按时间倒序
        activities.sort(key=lambda x: x.get('time', ''), reverse=True)

        return jsonify({'activities': activities[:20]})  # 只返回最近 20 条

    except Exception as e:
        return jsonify({'activities': [], 'error': str(e)})


@app.route('/api/scan', methods=['POST'])
def api_scan():
    try:
        env = os.environ.copy()
        fnm_path = os.path.expanduser('~/.local/share/fnm/node-versions/v22.16.0/installation/bin')
        if os.path.exists(fnm_path):
            env['PATH'] = f"{fnm_path}:{env.get('PATH', '')}"

        subprocess.Popen(
            ['claude', '-p', '/personal-assistant', '--dangerously-skip-permissions'],
            env=env,
            cwd=str(SKILL_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return jsonify({'success': True, 'message': '扫描已启动'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/execute', methods=['POST'])
def api_execute():
    data = request.json
    task = data.get('task', '')

    if not task:
        return jsonify({'success': False, 'message': '请输入任务内容'})

    try:
        env = os.environ.copy()
        fnm_path = os.path.expanduser('~/.local/share/fnm/node-versions/v22.16.0/installation/bin')
        if os.path.exists(fnm_path):
            env['PATH'] = f"{fnm_path}:{env.get('PATH', '')}"

        subprocess.Popen(
            ['claude', '-p', task, '--dangerously-skip-permissions'],
            env=env,
            cwd=str(SKILL_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return jsonify({'success': True, 'message': '任务已提交'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# CEO 助理 Agent 配置
CEO_AGENT = 'ceo-assistant'
CEO_SESSION_ID = '9826a95e-9bf8-4116-8d6e-70f8a1a7dfd8'

def session_exists(session_id: str) -> bool:
    """检查 session 是否存在"""
    session_file = SKILL_DIR.parent.parent / 'projects' / '-Users-liuyishou--claude-skills-personal-assistant' / f'{session_id}.jsonl'
    return session_file.exists()

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """聊天接口 - 与 CEO 助理 Agent 对话，保持永久上下文"""
    data = request.json
    message = data.get('message', '').strip()

    if not message:
        return jsonify({'success': False, 'error': '请输入消息'})

    try:
        env = os.environ.copy()
        fnm_path = os.path.expanduser('~/.local/share/fnm/node-versions/v22.16.0/installation/bin')
        if os.path.exists(fnm_path):
            env['PATH'] = f"{fnm_path}:{env.get('PATH', '')}"

        # 构建命令
        cmd = [
            'claude',
            '-p', message,
            '--agent', CEO_AGENT,
            '--dangerously-skip-permissions'
        ]

        # 检查 session 是否存在，决定用 --session-id 还是 --resume
        if session_exists(CEO_SESSION_ID):
            cmd.extend(['--resume', CEO_SESSION_ID])
        else:
            cmd.extend(['--session-id', CEO_SESSION_ID])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 分钟超时
            env=env,
            cwd=str(SKILL_DIR)
        )

        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr:
            output += f"\n\n错误: {result.stderr.strip()}"

        return jsonify({
            'success': True,
            'result': output if output else '执行完成，无输出',
            'agent': CEO_AGENT,
            'sessionId': CEO_SESSION_ID
        })

    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': '执行超时（5分钟限制）'})
    except FileNotFoundError:
        return jsonify({'success': False, 'error': 'claude 命令未找到，请确保 Claude CLI 已安装'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/chat/reset', methods=['POST'])
def api_chat_reset():
    """重置聊天会话 - 生成新的 Session ID"""
    global CEO_SESSION_ID
    import uuid
    old_session = CEO_SESSION_ID
    CEO_SESSION_ID = str(uuid.uuid4())
    return jsonify({
        'success': True,
        'message': '会话已重置，开启全新对话',
        'oldSessionId': old_session,
        'newSessionId': CEO_SESSION_ID
    })


@app.route('/api/cost')
def api_cost():
    """获取成本统计数据"""
    cost_data = read_cost_data()
    return jsonify(cost_data)


@app.route('/api/activities')
def api_activities():
    """获取活动清单"""
    activities = parse_activity_log()
    stats = get_activity_stats(activities)
    return jsonify({
        'activities': activities,
        'stats': stats
    })


@app.route('/api/telegram/summary', methods=['POST'])
def api_telegram_summary():
    """发送活动摘要到 Telegram"""
    import subprocess

    activities = parse_activity_log()
    stats = get_activity_stats(activities)

    # 计算时间范围
    if activities:
        first_time = activities[-1].get('time', '--')
        last_time = activities[0].get('time', '--')
        time_range = f"{first_time} - {last_time}"
    else:
        time_range = "无数据"

    # 构建 JSON 数据
    json_data = json.dumps({
        'time_range': time_range,
        'scan_count': stats.get('scanCount', 0),
        'timeout_count': stats.get('timeoutCount', 0),
        'executed_count': stats.get('executedTasks', 0),
        'xhs_count': stats.get('xhsCount', 0),
        'tweet_count': stats.get('tweetCount', 0),
        'failed_count': stats.get('failedCount', 0)
    })

    try:
        result = subprocess.run(
            ['python3', str(SKILL_DIR / 'scripts' / 'send_telegram.py'), 'summary', '--json', json_data],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return jsonify({'success': True, 'message': '活动摘要已发送到 Telegram'})
        else:
            return jsonify({'success': False, 'message': result.stderr or '发送失败'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/telegram/message', methods=['POST'])
def api_telegram_message():
    """发送自定义消息到 Telegram"""
    import subprocess

    data = request.json
    message = data.get('message', '')

    if not message:
        return jsonify({'success': False, 'message': '消息内容不能为空'})

    try:
        result = subprocess.run(
            ['python3', str(SKILL_DIR / 'scripts' / 'send_telegram.py'), 'msg', message],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return jsonify({'success': True, 'message': '消息已发送'})
        else:
            return jsonify({'success': False, 'message': result.stderr or '发送失败'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/telegram/report-with-chart', methods=['POST'])
def api_telegram_report_with_chart():
    """发送带图表的报告到 Telegram"""
    import asyncio
    import sys

    # 添加 scripts 目录到路径
    scripts_dir = str(SKILL_DIR / 'scripts')
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    activities = parse_activity_log()
    stats = get_activity_stats(activities)

    # 计算时间范围
    if activities:
        first_time = activities[-1].get('time', '--')
        last_time = activities[0].get('time', '--')
        time_range = f"{first_time} - {last_time}"
    else:
        time_range = "无数据"

    # 生成图表
    chart_path = generate_activity_chart(activities)

    # 发送到 Telegram
    try:
        from send_telegram import TelegramNotifier

        async def send():
            notifier = TelegramNotifier()
            if not await notifier.connect():
                return False, "Telegram 未登录"
            try:
                success = await notifier.send_report_with_image(
                    image_path=chart_path,
                    stats=stats,
                    time_range=time_range
                )
                return success, "带图报告已发送" if success else "发送失败"
            finally:
                await notifier.disconnect()

        success, message = asyncio.run(send())

        # 清理临时图表
        if chart_path and os.path.exists(chart_path):
            os.remove(chart_path)

        return jsonify({'success': success, 'message': message})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


def generate_activity_chart(activities: list) -> Optional[str]:
    """生成活动统计图表"""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from collections import defaultdict

        # 按小时统计
        hourly_data = defaultdict(lambda: {'success': 0, 'timeout': 0, 'failed': 0})

        for act in activities:
            hour = act.get('time', '00:00')[:2] + ':00'
            result = act.get('result', '')
            if result == 'completed':
                hourly_data[hour]['success'] += 1
            elif result == 'timeout':
                hourly_data[hour]['timeout'] += 1
            elif result == 'failed':
                hourly_data[hour]['failed'] += 1

        if not hourly_data:
            return None

        # 排序
        hours = sorted(hourly_data.keys())
        success = [hourly_data[h]['success'] for h in hours]
        timeout = [hourly_data[h]['timeout'] for h in hours]
        failed = [hourly_data[h]['failed'] for h in hours]

        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 5))

        x = range(len(hours))
        width = 0.25

        ax.bar([i - width for i in x], success, width, label='成功', color='#34c724')
        ax.bar(x, timeout, width, label='超时', color='#ff9f0a')
        ax.bar([i + width for i in x], failed, width, label='失败', color='#f54a45')

        ax.set_xlabel('时间')
        ax.set_ylabel('次数')
        ax.set_title('活动统计（按小时）')
        ax.set_xticks(x)
        ax.set_xticklabels(hours, rotation=45)
        ax.legend()

        plt.tight_layout()

        # 保存
        chart_path = '/tmp/activity_chart.png'
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()

        return chart_path

    except ImportError:
        print("matplotlib 未安装")
        return None
    except Exception as e:
        print(f"生成图表失败: {e}")
        return None


# ============================================
# Main
# ============================================

def main():
    global log_watcher

    print("=" * 50)
    print("Personal AI Agent - 控制台")
    print("=" * 50)
    print()
    print("访问地址: http://localhost:5050")
    print()

    log_watcher = LogWatcher(socketio)
    log_watcher.start()

    socketio.run(app, host='0.0.0.0', port=5050, debug=False, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    main()
