# Setup Guide

详细的安装和配置指南，帮助你搭建自己的 Personal AI Company。

---

## 一、前提条件

### 1.1 硬件要求

| 要求 | 说明 |
|------|------|
| Mac 电脑 | macOS 12+ (Apple Silicon 或 Intel) |
| 常开状态 | 建议使用 [Amphetamine](https://apps.apple.com/app/amphetamine/id937984704) 防止休眠 |
| 网络 | 稳定的互联网连接 |

### 1.2 软件要求

```bash
# 1. Claude Code CLI (必须)
# 安装方式: https://claude.ai/download
# 需要 Claude Code Max 订阅 ($100-200/month)

# 2. Python 3.10+ (必须)
python3 --version  # 应该显示 3.10+

# 3. Node.js 18+ (可选，用于部分 MCP)
node --version  # 应该显示 18+

# 4. Git (必须)
git --version
```

---

## 二、安装步骤

### 2.1 克隆仓库

```bash
git clone https://github.com/Leoyishou/personal-ai-company.git
cd personal-ai-company
```

### 2.2 安装依赖

```bash
# 创建 Python 虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2.3 配置 Skills

Skills 是各部门的能力模块。需要将 `skills/` 目录链接到 Claude Code 的 skills 目录：

```bash
# 方式一：符号链接（推荐）
ln -s "$(pwd)/skills/"* ~/.claude/skills/

# 方式二：直接复制
cp -r skills/* ~/.claude/skills/
```

### 2.4 配置 Agents

Agents 定义了各部门的职责和行为：

```bash
# 复制部门定义到 Claude 配置
mkdir -p ~/.claude/agents/departments
cp agents/departments/*.md ~/.claude/agents/departments/
cp agents/ceo-assistant.md ~/.claude/agents/
```

### 2.5 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑填写必要的 API Keys
nano .env  # 或使用你喜欢的编辑器
```

---

## 三、API 凭证配置

### 3.1 必需配置

#### Telegram API (CEO 专线)

用于接收汇报和下达指令。

1. 访问 https://my.telegram.org/apps
2. 登录并创建新应用
3. 获取 `api_id` 和 `api_hash`

```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+8613800138000
```

#### 滴答清单 API (CEO 待办)

用于自动扫描任务。

1. 访问 https://developer.dida365.com/
2. 创建应用并获取凭证

```env
DIDA365_CLIENT_ID=your_client_id
DIDA365_CLIENT_SECRET=your_client_secret
DIDA365_REGION=china  # 或 international
```

### 3.2 可选配置（按部门需求）

#### 内容与公关部

```env
# X (Twitter) - 发推文
X_API_KEY=your_key
X_API_SECRET=your_secret
X_ACCESS_TOKEN=your_token
X_ACCESS_TOKEN_SECRET=your_token_secret
```

#### 战投部 / 调研能力

```env
# OpenRouter - 多模型调用
OPENROUTER_API_KEY=sk-or-v1-xxx

# Reddit API - 社区调研
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
```

#### 情报分析部

```env
# Firecrawl - 网页抓取
FIRECRAWL_API_KEY=fc-xxx
```

#### 研发部

```env
# Supabase - 数据库和后端
SUPABASE_ACCESS_TOKEN=sbp_xxx
SUPABASE_PROJECT_ID=your_project_id
SUPABASE_URL=https://xxx.supabase.co

# Apple/EAS - iOS 发布
EXPO_APPLE_ID=your_apple_id
APPLE_TEAM_ID=your_team_id
```

#### 运营部 - 每日复盘

```env
# Notion - 报告存储
NOTION_API_KEY=ntn_xxx
```

---

## 四、Supabase 配置

运营部的每日复盘功能需要 Supabase 存储数据。

### 4.1 创建项目

1. 访问 https://supabase.com/
2. 创建新项目
3. 记录 Project URL 和 API Keys

### 4.2 创建数据表

在 Supabase SQL Editor 中执行：

```sql
-- 浏览记录表（由浏览器插件写入）
CREATE TABLE IF NOT EXISTS browsing_records (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  url TEXT NOT NULL,
  title TEXT,
  domain TEXT,
  visit_time TIMESTAMPTZ DEFAULT NOW(),
  duration_seconds INT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent 会话记录表
CREATE TABLE IF NOT EXISTS agent_sessions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  session_id TEXT,
  message_count INT,
  topics TEXT[],
  summary TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 每日复盘表
CREATE TABLE IF NOT EXISTS daily_personal_reviews (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  review_date DATE UNIQUE NOT NULL,
  total_pages INT,
  total_domains INT,
  total_duration_minutes INT,
  agent_sessions INT,
  agent_messages INT,
  okr_alignment JSONB,
  time_distribution JSONB,
  one_line_summary TEXT,
  insights JSONB,
  tomorrow_suggestions JSONB,
  raw_report TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 五、启动公司

### 5.1 使用 install.sh

```bash
# 执行安装脚本
chmod +x install.sh
./install.sh

# 验证服务状态
launchctl list | grep personal-ai
```

### 5.2 手动启动

```bash
# 启动调度中心（后台）
nohup python3 scripts/scheduler.py > scheduler.log 2>&1 &

# 启动管理后台
python3 scripts/dashboard.py
# 访问 http://localhost:5050
```

### 5.3 开机自启动

创建 `~/Library/LaunchAgents/com.claude.personal-ai-agent.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.claude.personal-ai-agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/personal-ai-company/scripts/scheduler.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/personal-ai-agent.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/personal-ai-agent.error.log</string>
</dict>
</plist>
```

加载服务：

```bash
launchctl load ~/Library/LaunchAgents/com.claude.personal-ai-agent.plist
```

---

## 六、验证安装

### 6.1 检查服务状态

```bash
# 查看调度中心是否运行
launchctl list | grep personal-ai

# 查看日志
tail -f /tmp/personal-ai-agent.log
```

### 6.2 测试 Telegram 通信

1. 在 Telegram 的 Saved Messages 发送："你好"
2. 应该收到 CEO 助理的回复

### 6.3 测试管理后台

1. 打开 http://localhost:5050
2. 应该看到公司 Dashboard

### 6.4 测试任务执行

1. 在滴答清单创建任务："发条推，内容是测试"
2. 等待下一轮扫描（每 30 分钟）或手动触发
3. 应该收到 Telegram 通知

---

## 七、常见问题

### Q: Telegram 登录失败

```
解决方案：
1. 检查手机号格式（需要带国际区号 +86）
2. 检查 API_ID 和 API_HASH 是否正确
3. 首次运行需要手动输入验证码
```

### Q: 滴答清单连接失败

```
解决方案：
1. 确认 DIDA365_REGION 设置正确
   - 中国用户: china
   - 国际用户: international
2. 重新授权应用
```

### Q: Claude Code 调用失败

```
解决方案：
1. 检查 Claude Code 是否已登录: claude --version
2. 检查订阅是否有效
3. 检查 API 用量是否超限
```

### Q: 每日复盘没有数据

```
解决方案：
1. 确认 Supabase 表已创建
2. 确认有浏览记录写入（需要浏览器插件）
3. 检查 SUPABASE_URL 和 SUPABASE_ANON_KEY 配置
```

---

## 八、升级指南

```bash
# 拉取最新代码
cd personal-ai-company
git pull

# 更新依赖
pip install -r requirements.txt --upgrade

# 更新 Skills
cp -r skills/* ~/.claude/skills/

# 重启服务
launchctl stop com.claude.personal-ai-agent
launchctl start com.claude.personal-ai-agent
```

---

## 九、卸载

```bash
# 停止并移除服务
launchctl unload ~/Library/LaunchAgents/com.claude.personal-ai-agent.plist
launchctl unload ~/Library/LaunchAgents/com.claude.personal-ai-dashboard.plist
rm ~/Library/LaunchAgents/com.claude.personal-ai*.plist

# 删除 Skills 链接
rm -rf ~/.claude/skills/personal-assistant
# ... 其他 skills

# 删除项目目录
rm -rf /path/to/personal-ai-company
```

---

如有问题，欢迎在 [GitHub Issues](https://github.com/Leoyishou/personal-ai-company/issues) 提问。
