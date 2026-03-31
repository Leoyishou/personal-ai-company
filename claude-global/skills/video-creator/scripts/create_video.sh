#!/bin/bash
# 一键视频创建脚本
# 用法: ./create_video.sh input.mp4 project_dir [green_color]

set -e

INPUT="$1"
PROJECT_DIR="${2:-./video-project}"
GREEN_COLOR="${3:-0x00FF00}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATES_DIR="$SCRIPT_DIR/../templates"

if [ -z "$INPUT" ]; then
    echo "======================================"
    echo "  Video Creator - 一键视频创建工具"
    echo "======================================"
    echo ""
    echo "用法: $0 <input.mp4> [project_dir] [green_color]"
    echo ""
    echo "参数说明:"
    echo "  input.mp4    - 输入的绿幕视频"
    echo "  project_dir  - 项目目录 (默认: ./video-project)"
    echo "  green_color  - 绿幕颜色值 (默认: 0x00FF00)"
    echo ""
    echo "示例:"
    echo "  $0 presenter.mp4"
    echo "  $0 presenter.mp4 ./my-video"
    echo "  $0 presenter.mp4 ./my-video 0x00FF00"
    echo ""
    echo "流程:"
    echo "  1. 绿幕抠图 (MP4 -> WebM)"
    echo "  2. 音频转录 (生成字幕)"
    echo "  3. [手动] 生成技术图 (使用 nanobanana)"
    echo "  4. 创建 Remotion 项目"
    echo "  5. 渲染最终视频"
    exit 1
fi

if [ ! -f "$INPUT" ]; then
    echo "错误: 输入文件不存在: $INPUT"
    exit 1
fi

echo "======================================"
echo "  Video Creator - 开始处理"
echo "======================================"
echo ""
echo "输入文件: $INPUT"
echo "项目目录: $PROJECT_DIR"
echo "绿幕颜色: $GREEN_COLOR"
echo ""

# Step 1: 创建项目目录
echo "Step 1: 创建项目结构..."
mkdir -p "$PROJECT_DIR/src"
mkdir -p "$PROJECT_DIR/public"
mkdir -p "$PROJECT_DIR/out"

# Step 2: 绿幕抠图
echo ""
echo "Step 2: 绿幕抠图..."
ffmpeg -i "$INPUT" \
    -vf "chromakey=${GREEN_COLOR}:0.3:0.1" \
    -c:v libvpx-vp9 \
    -pix_fmt yuva420p \
    -c:a libopus \
    -y \
    "$PROJECT_DIR/public/character.webm"

echo "✓ 生成: $PROJECT_DIR/public/character.webm"

# Step 3: 提取音频并转录
echo ""
echo "Step 3: 音频转录..."
TEMP_AUDIO="$PROJECT_DIR/temp_audio.wav"
ffmpeg -i "$PROJECT_DIR/public/character.webm" -vn -acodec pcm_s16le -ar 16000 -ac 1 "$TEMP_AUDIO" -y

uv run whisper "$TEMP_AUDIO" --language Chinese --model base --output_format srt --output_dir "$PROJECT_DIR/public"

if [ -f "$PROJECT_DIR/public/temp_audio.srt" ]; then
    mv "$PROJECT_DIR/public/temp_audio.srt" "$PROJECT_DIR/public/subtitles.srt"
fi
rm -f "$TEMP_AUDIO"

echo "✓ 生成: $PROJECT_DIR/public/subtitles.srt"

# Step 4: 获取视频信息
echo ""
echo "Step 4: 获取视频信息..."
DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$PROJECT_DIR/public/character.webm")
FPS=30
FRAMES=$(echo "$DURATION * $FPS" | bc | cut -d'.' -f1)

echo "视频时长: ${DURATION}秒"
echo "总帧数: $FRAMES"

# Step 5: 复制模板文件
echo ""
echo "Step 5: 创建 Remotion 项目..."
cp "$TEMPLATES_DIR/package.json" "$PROJECT_DIR/"
cp "$TEMPLATES_DIR/index.ts" "$PROJECT_DIR/src/"
cp "$TEMPLATES_DIR/VideoComposition.tsx" "$PROJECT_DIR/src/"

# 生成 Root.tsx (使用实际帧数)
cat > "$PROJECT_DIR/src/Root.tsx" << EOF
import { Composition } from "remotion";
import { VideoComposition } from "./VideoComposition";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="MainVideo"
      component={VideoComposition}
      durationInFrames={$FRAMES}
      fps={30}
      width={720}
      height={1280}
      defaultProps={{
        characterVideo: "character.webm",
        techIllustration: "tech-illustration.jpg",
        subtitlesFile: "subtitles.srt",
        backgroundColor: "#1a1a2e",
        accentColor: "#00d4ff",
      }}
    />
  );
};
EOF

# Step 6: 安装依赖
echo ""
echo "Step 6: 安装依赖..."
cd "$PROJECT_DIR"
npm install

echo ""
echo "======================================"
echo "  处理完成!"
echo "======================================"
echo ""
echo "下一步:"
echo "1. 生成技术图并保存为: $PROJECT_DIR/public/tech-illustration.jpg"
echo "   使用 nanobanana: 根据字幕内容描述生成技术图"
echo ""
echo "2. 预览视频:"
echo "   cd $PROJECT_DIR && npm start"
echo ""
echo "3. 渲染最终视频:"
echo "   cd $PROJECT_DIR && npm run build"
echo ""
echo "字幕内容:"
echo "----------------------------------------"
cat "$PROJECT_DIR/public/subtitles.srt"
echo "----------------------------------------"
