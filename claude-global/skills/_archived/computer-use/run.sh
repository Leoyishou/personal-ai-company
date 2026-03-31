#!/bin/bash
# Computer Use - AI 自动操作电脑
# 基于 Simular AI Agent S
#
# 用法: ./run.sh [model]
# 示例:
#   ./run.sh                              # 使用默认模型 claude-sonnet-4
#   ./run.sh gpt-4o                       # 使用 GPT-4o
#   ./run.sh claude-sonnet-4-20250514     # 指定 Claude 版本

VENV_PATH="/Users/liuyishou/usr/projects/inbox/agent-s-env"
MODEL="${1:-claude-sonnet-4-20250514}"

# API Keys
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-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}"
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-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}"

# 检查虚拟环境
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ 错误: 虚拟环境不存在"
    echo "请先安装 Agent S: pip install gui-agents"
    exit 1
fi

# 检查权限提示
echo "🖥️  Computer Use (Agent S)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "模型: $MODEL"
echo "Embedding: OpenRouter (text-embedding-3-small)"
echo ""
echo "⚠️  确保已授予以下权限："
echo "   • 辅助功能 (Accessibility)"
echo "   • 屏幕录制 (Screen Recording)"
echo "   • 自动化 > System Events"
echo ""
echo "启动中..."
echo ""

# 激活虚拟环境并运行
source "$VENV_PATH/bin/activate"
agent_s --model "$MODEL"
