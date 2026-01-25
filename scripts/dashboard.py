#!/usr/bin/env python3
"""
Personal AI Agent - Web Dashboard

功能：
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

# 确保目录存在
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Flask 配置
app = Flask(__name__)
app.config['SECRET_KEY'] = 'personal-ai-agent-dashboard'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ============================================
# 数据读取
# ============================================

def read_state() -> dict:
    """读取状态文件"""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass
    return {"processedTasks": {}, "lastRunAt": None}


def read_cost() -> dict:
    """读取成本记录"""
    if COST_FILE.exists():
        try:
            return json.loads(COST_FILE.read_text())
        except:
            pass
    return {"daily": {}, "totalTokens": 0, "totalCost": 0}


def save_cost(cost_data: dict):
    """保存成本记录"""
    COST_FILE.write_text(json.dumps(cost_data, indent=2, ensure_ascii=False))


def read_recent_logs(lines: int = 100) -> list:
    """读取最近的日志"""
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
    """获取任务执行历史"""
    state = read_state()
    tasks = []

    for task_id, info in state.get('processedTasks', {}).items():
        tasks.append({
            'id': task_id,
            'processedAt': info.get('processedAt', ''),
            'status': info.get('status', 'unknown'),
            'reason': info.get('reason', ''),
            'title': info.get('title', task_id[:20] + '...')
        })

    # 按时间倒序
    tasks.sort(key=lambda x: x['processedAt'], reverse=True)
    return tasks[:50]  # 最近50条


def get_statistics() -> dict:
    """获取统计数据"""
    state = read_state()
    tasks = state.get('processedTasks', {})

    # 统计各状态数量
    status_count = {'completed': 0, 'failed': 0, 'skipped': 0}
    for info in tasks.values():
        status = info.get('status', 'unknown')
        if status in status_count:
            status_count[status] += 1

    # 最近7天每天执行数量
    daily_count = {}
    for info in tasks.values():
        processed_at = info.get('processedAt', '')
        if processed_at:
            try:
                date = processed_at[:10]
                daily_count[date] = daily_count.get(date, 0) + 1
            except:
                pass

    # 填充最近7天
    today = datetime.now().date()
    weekly_data = []
    for i in range(6, -1, -1):
        date = (today - timedelta(days=i)).isoformat()
        weekly_data.append({
            'date': date,
            'count': daily_count.get(date, 0)
        })

    return {
        'total': len(tasks),
        'statusCount': status_count,
        'weeklyData': weekly_data,
        'lastRunAt': state.get('lastRunAt', 'Never')
    }


# ============================================
# 日志监控线程
# ============================================

class LogWatcher(threading.Thread):
    """监控日志文件变化并推送到 WebSocket"""

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


# 启动日志监控
log_watcher = None


# ============================================
# HTML 模板
# ============================================

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Personal AI Agent - Dashboard</title>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f7;
            color: #1d1d1f;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { font-size: 24px; font-weight: 600; }
        .status-badge {
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
        }
        .status-online { background: rgba(52, 199, 89, 0.2); color: #34c759; }
        .status-offline { background: rgba(255, 59, 48, 0.2); color: #ff3b30; }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }

        .card {
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .card-title {
            font-size: 18px;
            font-weight: 600;
            color: #1d1d1f;
        }

        /* 统计卡片 */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            grid-column: span 2;
        }
        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        }
        .stat-value {
            font-size: 32px;
            font-weight: 700;
            color: #667eea;
        }
        .stat-label {
            font-size: 14px;
            color: #86868b;
            margin-top: 4px;
        }

        /* 日志区域 */
        .log-container {
            grid-column: span 2;
        }
        .log-box {
            background: #1d1d1f;
            border-radius: 12px;
            padding: 16px;
            height: 300px;
            overflow-y: auto;
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 13px;
        }
        .log-line {
            color: #98989d;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-all;
        }
        .log-line.info { color: #30d158; }
        .log-line.error { color: #ff453a; }
        .log-line.warning { color: #ffd60a; }

        /* 任务历史 */
        .task-list {
            max-height: 400px;
            overflow-y: auto;
        }
        .task-item {
            display: flex;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        .task-item:last-child { border-bottom: none; }
        .task-status {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 12px;
        }
        .task-status.completed { background: #34c759; }
        .task-status.failed { background: #ff3b30; }
        .task-status.skipped { background: #ff9500; }
        .task-info { flex: 1; }
        .task-title { font-size: 14px; font-weight: 500; }
        .task-time { font-size: 12px; color: #86868b; }

        /* 快捷操作 */
        .action-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .action-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        .action-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        /* 手动输入 */
        .manual-input {
            display: flex;
            gap: 12px;
            margin-top: 16px;
        }
        .manual-input input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e5e5e5;
            border-radius: 10px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }
        .manual-input input:focus {
            border-color: #667eea;
        }

        /* 图表 */
        .chart-container {
            height: 200px;
        }

        /* 响应式 */
        @media (max-width: 1024px) {
            .container { grid-template-columns: 1fr; }
            .stats-grid { grid-column: span 1; grid-template-columns: repeat(2, 1fr); }
            .log-container { grid-column: span 1; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Personal AI Agent</h1>
        <span id="status" class="status-badge status-online">Online</span>
    </div>

    <div class="container">
        <!-- 统计卡片 -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value" id="stat-total">0</div>
                <div class="stat-label">Total Tasks</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="stat-completed">0</div>
                <div class="stat-label">Completed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="stat-failed">0</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="stat-skipped">0</div>
                <div class="stat-label">Skipped</div>
            </div>
        </div>

        <!-- 实时日志 -->
        <div class="card log-container">
            <div class="card-header">
                <span class="card-title">Live Logs</span>
                <button class="action-btn" onclick="clearLogs()">Clear</button>
            </div>
            <div class="log-box" id="log-box"></div>
        </div>

        <!-- 每周图表 -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">Weekly Activity</span>
            </div>
            <div class="chart-container">
                <canvas id="weeklyChart"></canvas>
            </div>
        </div>

        <!-- 快捷操作 -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">Quick Actions</span>
            </div>
            <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                <button class="action-btn" onclick="triggerScan()">Scan Dida365</button>
                <button class="action-btn" onclick="refreshStats()">Refresh Stats</button>
            </div>
            <div class="manual-input">
                <input type="text" id="manual-task" placeholder="Enter a task for AI to execute...">
                <button class="action-btn" onclick="executeTask()">Execute</button>
            </div>
        </div>

        <!-- 任务历史 -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">Task History</span>
            </div>
            <div class="task-list" id="task-list"></div>
        </div>

        <!-- 成本追踪 -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">Cost Tracking</span>
            </div>
            <div style="text-align: center; padding: 20px;">
                <div class="stat-value" id="total-cost">$0.00</div>
                <div class="stat-label">This Month</div>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        let weeklyChart = null;

        // WebSocket 连接
        socket.on('connect', () => {
            document.getElementById('status').className = 'status-badge status-online';
            document.getElementById('status').textContent = 'Online';
        });

        socket.on('disconnect', () => {
            document.getElementById('status').className = 'status-badge status-offline';
            document.getElementById('status').textContent = 'Offline';
        });

        socket.on('log', (data) => {
            addLog(data.message);
        });

        // 添加日志
        function addLog(message) {
            const logBox = document.getElementById('log-box');
            const line = document.createElement('div');
            line.className = 'log-line';

            if (message.includes('错误') || message.includes('Error') || message.includes('失败')) {
                line.classList.add('error');
            } else if (message.includes('警告') || message.includes('Warning')) {
                line.classList.add('warning');
            } else if (message.includes('完成') || message.includes('成功') || message.includes('启动')) {
                line.classList.add('info');
            }

            line.textContent = message;
            logBox.appendChild(line);
            logBox.scrollTop = logBox.scrollHeight;

            // 限制日志行数
            while (logBox.children.length > 200) {
                logBox.removeChild(logBox.firstChild);
            }
        }

        function clearLogs() {
            document.getElementById('log-box').innerHTML = '';
        }

        // 加载初始日志
        async function loadInitialLogs() {
            const resp = await fetch('/api/logs');
            const logs = await resp.json();
            logs.forEach(log => addLog(log));
        }

        // 加载统计数据
        async function refreshStats() {
            const resp = await fetch('/api/stats');
            const stats = await resp.json();

            document.getElementById('stat-total').textContent = stats.total;
            document.getElementById('stat-completed').textContent = stats.statusCount.completed;
            document.getElementById('stat-failed').textContent = stats.statusCount.failed;
            document.getElementById('stat-skipped').textContent = stats.statusCount.skipped;

            // 更新图表
            updateChart(stats.weeklyData);
        }

        // 更新图表
        function updateChart(data) {
            const ctx = document.getElementById('weeklyChart').getContext('2d');

            if (weeklyChart) {
                weeklyChart.destroy();
            }

            weeklyChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.map(d => d.date.slice(5)),
                    datasets: [{
                        label: 'Tasks',
                        data: data.map(d => d.count),
                        backgroundColor: 'rgba(102, 126, 234, 0.8)',
                        borderRadius: 6,
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

        // 加载任务历史
        async function loadTaskHistory() {
            const resp = await fetch('/api/tasks');
            const tasks = await resp.json();

            const list = document.getElementById('task-list');
            list.innerHTML = tasks.map(task => `
                <div class="task-item">
                    <div class="task-status ${task.status}"></div>
                    <div class="task-info">
                        <div class="task-title">${task.title || task.id}</div>
                        <div class="task-time">${task.processedAt || 'Unknown'}</div>
                    </div>
                </div>
            `).join('');
        }

        // 触发扫描
        async function triggerScan() {
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = 'Scanning...';

            try {
                const resp = await fetch('/api/scan', { method: 'POST' });
                const result = await resp.json();
                addLog('[Dashboard] ' + result.message);
            } catch (e) {
                addLog('[Dashboard] Scan failed: ' + e.message);
            }

            btn.disabled = false;
            btn.textContent = 'Scan Dida365';

            // 刷新数据
            setTimeout(() => {
                refreshStats();
                loadTaskHistory();
            }, 2000);
        }

        // 执行任务
        async function executeTask() {
            const input = document.getElementById('manual-task');
            const task = input.value.trim();

            if (!task) {
                alert('Please enter a task');
                return;
            }

            const btn = event.target;
            btn.disabled = true;
            btn.textContent = 'Executing...';

            try {
                const resp = await fetch('/api/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ task })
                });
                const result = await resp.json();
                addLog('[Dashboard] Task submitted: ' + task);
            } catch (e) {
                addLog('[Dashboard] Execute failed: ' + e.message);
            }

            btn.disabled = false;
            btn.textContent = 'Execute';
            input.value = '';
        }

        // Enter 键提交
        document.getElementById('manual-task').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') executeTask();
        });

        // 初始化
        loadInitialLogs();
        refreshStats();
        loadTaskHistory();

        // 定时刷新
        setInterval(refreshStats, 60000);
        setInterval(loadTaskHistory, 30000);
    </script>
</body>
</html>
'''


# ============================================
# API 路由
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


@app.route('/api/scan', methods=['POST'])
def api_scan():
    """手动触发扫描"""
    try:
        # 设置环境变量
        env = os.environ.copy()
        fnm_path = os.path.expanduser('~/.local/share/fnm/node-versions/v22.16.0/installation/bin')
        if os.path.exists(fnm_path):
            env['PATH'] = f"{fnm_path}:{env.get('PATH', '')}"

        # 异步启动扫描
        subprocess.Popen(
            ['claude', '-p', '/personal-assistant', '--dangerously-skip-permissions'],
            env=env,
            cwd=str(SKILL_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return jsonify({'success': True, 'message': 'Scan started'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/execute', methods=['POST'])
def api_execute():
    """执行指定任务"""
    data = request.json
    task = data.get('task', '')

    if not task:
        return jsonify({'success': False, 'message': 'No task provided'})

    try:
        env = os.environ.copy()
        fnm_path = os.path.expanduser('~/.local/share/fnm/node-versions/v22.16.0/installation/bin')
        if os.path.exists(fnm_path):
            env['PATH'] = f"{fnm_path}:{env.get('PATH', '')}"

        # 异步执行
        subprocess.Popen(
            ['claude', '-p', task, '--dangerously-skip-permissions'],
            env=env,
            cwd=str(SKILL_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return jsonify({'success': True, 'message': 'Task submitted'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ============================================
# 主函数
# ============================================

def main():
    global log_watcher

    print("=" * 50)
    print("Personal AI Agent - Dashboard")
    print("=" * 50)
    print()
    print("Dashboard URL: http://localhost:5050")
    print()

    # 启动日志监控
    log_watcher = LogWatcher(socketio)
    log_watcher.start()

    # 启动 Web 服务
    socketio.run(app, host='0.0.0.0', port=5050, debug=False, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    main()
