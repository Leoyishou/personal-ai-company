#!/bin/bash
# Personal AI Scheduler 安装脚本

set -e

echo "=========================================="
echo "  Personal AI Scheduler 安装程序"
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
cp scripts/send_telegram.py ~/.claude/skills/personal-assistant/scripts/
cp scripts/telegram_listener.py ~/.claude/skills/personal-assistant/scripts/
cp scripts/telegram_login.py ~/.claude/skills/personal-assistant/scripts/

# 替换配置值
sed -i '' "s/API_ID = '.*'/API_ID = '$TELEGRAM_API_ID'/" ~/.claude/skills/personal-assistant/scripts/*.py
sed -i '' "s/API_HASH = '.*'/API_HASH = '$TELEGRAM_API_HASH'/" ~/.claude/skills/personal-assistant/scripts/*.py
sed -i '' "s/PHONE = '.*'/PHONE = '$TELEGRAM_PHONE'/" ~/.claude/skills/personal-assistant/scripts/*.py

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

cat > ~/.claude/services/personal-assistant/run.sh << EOF
#!/bin/bash
# 定时扫描器启动脚本

export FNM_DIR="\$HOME/.local/share/fnm"
export PATH="\$FNM_DIR/node-versions/v22.16.0/installation/bin:\$PATH"

echo "=== \$(date '+%Y-%m-%d %H:%M:%S') 开始执行 ===" >> ~/.claude/services/personal-assistant/stdout.log

cd ~/.claude/skills/personal-assistant
claude -p "/personal-assistant" --dangerously-skip-permissions 2>&1 | tee -a ~/.claude/services/personal-assistant/stdout.log

echo "=== \$(date '+%Y-%m-%d %H:%M:%S') 执行完成 ===" >> ~/.claude/services/personal-assistant/stdout.log
EOF

cat > ~/.claude/services/personal-assistant/run_listener.sh << EOF
#!/bin/bash
# Telegram 监听器启动脚本

PYTHON="$PYTHON_PATH"
LOG_DIR="\$HOME/.claude/skills/personal-assistant/logs"
mkdir -p "\$LOG_DIR"

echo "=== \$(date '+%Y-%m-%d %H:%M:%S') 启动 Telegram 监听器 ===" >> "\$LOG_DIR/telegram_listener.log"

cd ~/.claude/skills/personal-assistant
\$PYTHON scripts/telegram_listener.py 2>&1 | tee -a "\$LOG_DIR/telegram_listener.log"
EOF

chmod +x ~/.claude/services/personal-assistant/*.sh

echo -e "${GREEN}✓${NC} 启动脚本已创建"
echo ""

# Step 7: 创建 launchd 配置
echo "Step 7: 创建 launchd 服务..."

SCAN_INTERVAL=${SCAN_INTERVAL:-1800}
USER_HOME=$HOME

cat > ~/Library/LaunchAgents/com.claude.personal-assistant.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.claude.personal-assistant</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$USER_HOME/.claude/services/personal-assistant/run.sh</string>
    </array>
    <key>StartInterval</key>
    <integer>$SCAN_INTERVAL</integer>
    <key>StandardOutPath</key>
    <string>$USER_HOME/.claude/services/personal-assistant/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>$USER_HOME/.claude/services/personal-assistant/launchd.log</string>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
EOF

cat > ~/Library/LaunchAgents/com.claude.telegram-listener.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.claude.telegram-listener</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$USER_HOME/.claude/services/personal-assistant/run_listener.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$USER_HOME/.claude/services/personal-assistant/listener_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$USER_HOME/.claude/services/personal-assistant/listener_stderr.log</string>
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

launchctl load ~/Library/LaunchAgents/com.claude.personal-assistant.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.claude.telegram-listener.plist 2>/dev/null || true

sleep 3

echo -e "${GREEN}✓${NC} 服务已加载"
echo ""

# Step 10: 验证
echo "Step 10: 验证安装..."

if launchctl list | grep -q "com.claude.personal-assistant"; then
    echo -e "${GREEN}✓${NC} 定时扫描服务运行中"
else
    echo -e "${RED}✗${NC} 定时扫描服务未运行"
fi

if launchctl list | grep -q "com.claude.telegram-listener"; then
    echo -e "${GREEN}✓${NC} Telegram 监听服务运行中"
else
    echo -e "${RED}✗${NC} Telegram 监听服务未运行"
fi

echo ""

# Step 11: 发送测试通知
echo "Step 11: 发送测试通知..."
python3 ~/.claude/skills/personal-assistant/scripts/send_telegram.py "Personal AI Scheduler 安装成功！发送消息即可触发 AI 执行。"

echo ""
echo "=========================================="
echo -e "${GREEN}  安装完成！${NC}"
echo "=========================================="
echo ""
echo "使用方式："
echo "  1. 在滴答清单添加任务，等待 AI 自动执行"
echo "  2. 在 Telegram Saved Messages 发消息触发 AI"
echo ""
echo "管理命令："
echo "  # 查看服务状态"
echo "  launchctl list | grep personal-ai"
echo ""
echo "  # 查看日志"
echo "  tail -f ~/.claude/skills/personal-assistant/logs/telegram_listener.log"
echo ""
echo "  # 手动触发扫描"
echo "  claude -p \"/personal-assistant\" --dangerously-skip-permissions"
echo ""
