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
# HTML - 飞书风格 CEO 仪表盘
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
        }

        .nav-item:hover { background: var(--bg-body); }
        .nav-item.active {
            background: var(--primary-light);
            color: var(--primary);
        }

        .nav-icon { font-size: 18px; width: 20px; text-align: center; }

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
        }

        .page-header {
            margin-bottom: 32px;
        }

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

        .stat-trend {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 8px;
        }

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

        .log-line { color: #9da5b4; }
        .log-line.info { color: #98c379; }
        .log-line.error { color: #e06c75; }
        .log-line.warning { color: #e5c07b; }

        /* 任务列表 */
        .task-list { max-height: 320px; overflow-y: auto; }

        .task-item {
            display: flex;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid var(--border);
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

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .input-group {
            display: flex;
            gap: 12px;
        }

        .input-group input {
            flex: 1;
            padding: 10px 14px;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.15s;
        }

        .input-group input:focus {
            border-color: var(--primary);
        }

        /* 图表 */
        .chart-container { height: 200px; }

        /* 全宽卡片 */
        .card-full { grid-column: span 2; }

        /* 响应式 */
        @media (max-width: 1200px) {
            .sidebar { width: 200px; }
            .stats-row { grid-template-columns: repeat(2, 1fr); }
        }

        @media (max-width: 900px) {
            .sidebar { display: none; }
            .content-grid { grid-template-columns: 1fr; }
            .card-full { grid-column: span 1; }
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
            <div class="nav-item active">
                <span class="nav-icon">📊</span>
                仪表盘
            </div>
            <div class="nav-item">
                <span class="nav-icon">📋</span>
                任务管理
            </div>
            <div class="nav-item">
                <span class="nav-icon">📜</span>
                执行日志
            </div>
            <div class="nav-item">
                <span class="nav-icon">⚙️</span>
                系统设置
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
        <header class="page-header">
            <h2 class="page-title">工作概览</h2>
            <p class="page-subtitle">实时监控 AI 助理的所有活动</p>
        </header>

        <!-- 统计卡片 -->
        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-label">总任务数</div>
                <div class="stat-value" id="stat-total">0</div>
                <div class="stat-trend">累计处理</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">已完成</div>
                <div class="stat-value success" id="stat-completed">0</div>
                <div class="stat-trend">执行成功</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">已跳过</div>
                <div class="stat-value warning" id="stat-skipped">0</div>
                <div class="stat-trend">需要更多信息</div>
            </div>
            <div class="stat-card">
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
                    <button class="btn btn-secondary" onclick="clearLogs()">清空</button>
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
                        <button class="btn btn-primary" onclick="triggerScan()">扫描滴答清单</button>
                        <button class="btn btn-secondary" onclick="refreshStats()">刷新数据</button>
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

            <!-- 任务历史 -->
            <div class="card card-full">
                <div class="card-header">
                    <span class="card-title">最近执行</span>
                </div>
                <div class="card-body">
                    <div class="task-list" id="task-list"></div>
                </div>
            </div>
        </div>
    </main>

    <script>
        const socket = io();
        let weeklyChart = null;

        socket.on('connect', () => {
            document.getElementById('status-dot').style.background = '#34c724';
            document.getElementById('status-text').textContent = '系统运行中';
        });

        socket.on('disconnect', () => {
            document.getElementById('status-dot').style.background = '#f54a45';
            document.getElementById('status-text').textContent = '连接已断开';
        });

        socket.on('log', (data) => addLog(data.message));

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

            while (logBox.children.length > 200) {
                logBox.removeChild(logBox.firstChild);
            }
        }

        function clearLogs() {
            document.getElementById('log-box').innerHTML = '';
        }

        async function loadInitialLogs() {
            const resp = await fetch('/api/logs');
            const logs = await resp.json();
            logs.forEach(log => addLog(log));
        }

        async function refreshStats() {
            const resp = await fetch('/api/stats');
            const stats = await resp.json();

            document.getElementById('stat-total').textContent = stats.total;
            document.getElementById('stat-completed').textContent = stats.statusCount.completed;
            document.getElementById('stat-failed').textContent = stats.statusCount.failed;
            document.getElementById('stat-skipped').textContent = stats.statusCount.skipped;

            updateChart(stats.weeklyData);
        }

        function updateChart(data) {
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

        async function loadTaskHistory() {
            const resp = await fetch('/api/tasks');
            const tasks = await resp.json();

            const list = document.getElementById('task-list');
            if (tasks.length === 0) {
                list.innerHTML = '<div style="text-align:center;color:#8f959e;padding:40px;">暂无执行记录</div>';
                return;
            }

            list.innerHTML = tasks.map(task => `
                <div class="task-item">
                    <div class="task-status ${task.status}"></div>
                    <div class="task-info">
                        <div class="task-title">${task.title || task.id}</div>
                        <div class="task-time">${task.processedAt ? task.processedAt.replace('T', ' ').slice(0, 19) : '未知'}</div>
                    </div>
                </div>
            `).join('');
        }

        async function triggerScan() {
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = '扫描中...';

            try {
                const resp = await fetch('/api/scan', { method: 'POST' });
                const result = await resp.json();
                addLog('[控制台] ' + result.message);
            } catch (e) {
                addLog('[控制台] 扫描失败: ' + e.message);
            }

            btn.disabled = false;
            btn.textContent = '扫描滴答清单';

            setTimeout(() => {
                refreshStats();
                loadTaskHistory();
            }, 2000);
        }

        async function executeTask() {
            const input = document.getElementById('manual-task');
            const task = input.value.trim();

            if (!task) {
                alert('请输入任务内容');
                return;
            }

            const btn = event.target;
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
            } catch (e) {
                addLog('[控制台] 执行失败: ' + e.message);
            }

            btn.disabled = false;
            btn.textContent = '执行';
            input.value = '';
        }

        document.getElementById('manual-task').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') executeTask();
        });

        // 初始化
        loadInitialLogs();
        refreshStats();
        loadTaskHistory();

        setInterval(refreshStats, 60000);
        setInterval(loadTaskHistory, 30000);
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
