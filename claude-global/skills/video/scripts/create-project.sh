#!/bin/bash
# 创建新的视频项目
# 用法: ./create-project.sh <项目名> <风格>

set -e

PROJECT_NAME=${1:-"my-video"}
STYLE=${2:-"pencil-whiteboard"}
PROJECT_DIR="/Users/liuyishou/usr/projects/inbox/$PROJECT_NAME"
SKILL_DIR="$HOME/.claude/skills/video"
ASSETS_DIR="$HOME/.claude/agents/content-pr-department/assets"

echo "📹 创建视频项目: $PROJECT_NAME"
echo "🎨 风格: $STYLE"

# 检查模板是否存在
if [ ! -d "$SKILL_DIR/templates/$STYLE" ]; then
    echo "❌ 错误: 风格模板 '$STYLE' 不存在"
    echo "可用模板:"
    ls "$SKILL_DIR/templates/"
    exit 1
fi

# 复制模板
echo "📁 复制模板..."
cp -r "$SKILL_DIR/templates/$STYLE" "$PROJECT_DIR"

# 复制音效（从内容公关部素材库）
echo "🔊 复制音效..."
cp "$ASSETS_DIR/audio/sfx/pencil_writing.mp3" "$PROJECT_DIR/public/audio/pencil.mp3"
cp "$ASSETS_DIR/audio/bgm/calm/口播背景_轻柔.mp3" "$PROJECT_DIR/public/audio/bgm.mp3"

# 安装依赖
echo "📦 安装依赖..."
cd "$PROJECT_DIR"
npm install --silent

echo ""
echo "✅ 项目创建完成!"
echo "📍 位置: $PROJECT_DIR"
echo ""
echo "下一步:"
echo "  1. 生成配音: volc-tts skill"
echo "  2. 生成图片: nanobanana-draw skill"
echo "  3. 编辑场景: $PROJECT_DIR/src/scenes.ts"
echo "  4. 预览: cd $PROJECT_DIR && npx remotion studio"
echo "  5. 渲染: npx remotion render Main out/video.mp4"
