#!/bin/bash
# Personal AI Agent 安装脚本

set -e

echo "=========================================="
echo "  Personal AI Agent 安装程序"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 已安装"
        return 0
    else
        echo -e "${RED}✗${NC} $1 未安装"
        return 1
    fi
}

# Step 0: 检查前置条件
echo "Step 0: 检查前置条件..."
echo ""

check_command "claude" || {
    echo -e "${RED}请先安装 Claude Code CLI${NC}"
    echo "访问: https://docs.anthropic.com/en/docs/claude-code"
    exit 1
}

check_command "python3" || {
    echo -e "${RED}请先安装 Python 3${NC}"
    exit 1
}

check_command "pip3" || {
    echo -e "${RED}请先安装 pip3${NC}"
    exit 1
}

echo ""

# Step 1: 检查 .env 文件
echo "Step 1: 检查配置文件..."
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}未找到 .env 文件${NC}"
    echo "正在从 .env.example 创建..."
    cp .env.example .env
    echo ""
    echo -e "${YELLOW}请编辑 .env 文件，填入你的凭证：${NC}"
    echo "  nano .env"
    echo "  # 或"
    echo "  code .env"
    echo ""
    echo "填写完成后，重新运行此脚本。"
    exit 1
fi

# 加载环境变量
source .env

# 检查必填项
if [ -z "$TELEGRAM_API_ID" ] || [ -z "$TELEGRAM_API_HASH" ]; then
    echo -e "${RED}请在 .env 中填写 Telegram 配置${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} 配置文件已就绪"
echo ""

# Step 2: 安装 Python 依赖
echo "Step 2: 安装 Python 依赖..."
pip3 install telethon pytz requests --quiet
echo -e "${GREEN}✓${NC} Python 依赖已安装"
echo ""

# Step 3: 创建目录结构
echo "Step 3: 创建目录结构..."

mkdir -p ~/.claude/skills/personal-assistant/scripts
mkdir -p ~/.claude/skills/personal-assistant/logs
mkdir -p ~/.claude/skills/personal-assistant/results
mkdir -p ~/.claude/services/personal-assistant

echo -e "${GREEN}✓${NC} 目录结构已创建"
echo ""

# Step 4: 复制文件
echo "Step 4: 复制核心文件..."

cp skills/SKILL.md ~/.claude/skills/personal-assistant/
cp scripts/scheduler.py ~/.claude/skills/personal-assistant/scripts/
cp scripts/telegram_login.py ~/.claude/skills/personal-assistant/scripts/

# 替换配置值 (scheduler.py)
sed -i '' "s/API_ID = '.*'/API_ID = '$TELEGRAM_API_ID'/" ~/.claude/skills/personal-assistant/scripts/scheduler.py
sed -i '' "s/API_HASH = '.*'/API_HASH = '$TELEGRAM_API_HASH'/" ~/.claude/skills/personal-assistant/scripts/scheduler.py

# 替换配置值 (telegram_login.py)
sed -i '' "s/API_ID = '.*'/API_ID = '$TELEGRAM_API_ID'/" ~/.claude/skills/personal-assistant/scripts/telegram_login.py
sed -i '' "s/API_HASH = '.*'/API_HASH = '$TELEGRAM_API_HASH'/" ~/.claude/skills/personal-assistant/scripts/telegram_login.py
sed -i '' "s/PHONE = '.*'/PHONE = '$TELEGRAM_PHONE'/" ~/.claude/skills/personal-assistant/scripts/telegram_login.py

chmod +x ~/.claude/skills/personal-assistant/scripts/*.py

echo -e "${GREEN}✓${NC} 核心文件已复制"
echo ""

# Step 5: 初始化状态文件
echo "Step 5: 初始化状态文件..."
echo '{"processedTasks": {}}' > ~/.claude/skills/personal-assistant/state.json
echo -e "${GREEN}✓${NC} 状态文件已初始化"
echo ""

# Step 6: 创建启动脚本
echo "Step 6: 创建启动脚本..."

# 获取 Python 路径
PYTHON_PATH=$(which python3)

cat > ~/.claude/services/personal-assistant/run_scheduler.sh << EOF
#!/bin/bash
# Personal AI Agent - 统一调度器启动脚本

# 使用系统 Python (需要有 telethon)
PYTHON="$PYTHON_PATH"

# 日志
LOG_DIR="\$HOME/.claude/skills/personal-assistant/logs"
mkdir -p "\$LOG_DIR"

echo "=== \$(date '+%Y-%m-%d %H:%M:%S') 启动统一调度器 ===" >> "\$LOG_DIR/scheduler.log"

# 运行调度器
cd ~/.claude/skills/personal-assistant
\$PYTHON scripts/scheduler.py 2>&1 | tee -a "\$LOG_DIR/scheduler.log"
EOF

chmod +x ~/.claude/services/personal-assistant/*.sh

echo -e "${GREEN}✓${NC} 启动脚本已创建"
echo ""

# Step 7: 创建 launchd 配置
echo "Step 7: 创建 launchd 服务..."

USER_HOME=$HOME

# 统一调度器服务（KeepAlive，永久运行）
cat > ~/Library/LaunchAgents/com.claude.personal-ai-agent.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.claude.personal-ai-agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$USER_HOME/.claude/services/personal-assistant/run_scheduler.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$USER_HOME/.claude/services/personal-assistant/scheduler_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$USER_HOME/.claude/services/personal-assistant/scheduler_stderr.log</string>
    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
EOF

echo -e "${GREEN}✓${NC} launchd 服务配置已创建"
echo ""

# Step 8: Telegram 登录
echo "Step 8: Telegram 登录..."
echo "首次使用需要登录 Telegram（输入验证码）"
echo ""

python3 ~/.claude/skills/personal-assistant/scripts/telegram_login.py

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Telegram 登录失败，请稍后手动运行：${NC}"
    echo "  python3 ~/.claude/skills/personal-assistant/scripts/telegram_login.py"
fi

echo ""

# Step 9: 加载服务
echo "Step 9: 加载服务..."

# 先卸载旧服务（如果存在）
launchctl unload ~/Library/LaunchAgents/com.claude.personal-assistant.plist 2>/dev/null || true
launchctl unload ~/Library/LaunchAgents/com.claude.telegram-listener.plist 2>/dev/null || true

# 加载新的统一调度器服务
launchctl load ~/Library/LaunchAgents/com.claude.personal-ai-agent.plist 2>/dev/null || true

sleep 3

echo -e "${GREEN}✓${NC} 服务已加载"
echo ""

# Step 10: 验证
echo "Step 10: 验证安装..."

if launchctl list | grep -q "com.claude.personal-ai-agent"; then
    echo -e "${GREEN}✓${NC} 统一调度器服务运行中"
else
    echo -e "${RED}✗${NC} 统一调度器服务未运行"
fi

echo ""

echo "=========================================="
echo -e "${GREEN}  安装完成！${NC}"
echo "=========================================="
echo ""
echo "工作模式："
echo "  1. Telegram 发消息 → AI 立即执行"
echo "  2. 滴答清单添加任务 → 每 30 分钟自动扫描执行"
echo ""
echo "管理命令："
echo "  # 查看服务状态"
echo "  launchctl list | grep personal-ai"
echo ""
echo "  # 查看日志"
echo "  tail -f ~/.claude/skills/personal-assistant/logs/scheduler.log"
echo ""
echo "  # 重启服务"
echo "  launchctl stop com.claude.personal-ai-agent"
echo "  launchctl start com.claude.personal-ai-agent"
echo ""
