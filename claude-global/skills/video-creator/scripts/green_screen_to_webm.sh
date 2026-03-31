#!/bin/bash
# 绿幕抠图脚本 - 将绿幕MP4转换为透明WebM
# 用法: ./green_screen_to_webm.sh input.mp4 output.webm [green_color] [similarity] [blend]

INPUT="$1"
OUTPUT="$2"
GREEN_COLOR="${3:-0x00FF00}"  # 默认纯绿色
SIMILARITY="${4:-0.3}"         # 相似度阈值
BLEND="${5:-0.1}"              # 边缘混合度

if [ -z "$INPUT" ] || [ -z "$OUTPUT" ]; then
    echo "用法: $0 <input.mp4> <output.webm> [green_color] [similarity] [blend]"
    echo ""
    echo "参数说明:"
    echo "  input.mp4    - 输入的绿幕视频"
    echo "  output.webm  - 输出的透明背景视频"
    echo "  green_color  - 绿幕颜色值 (默认: 0x00FF00)"
    echo "  similarity   - 相似度阈值 0-1 (默认: 0.3, 越小越精确)"
    echo "  blend        - 边缘混合度 0-1 (默认: 0.1)"
    echo ""
    echo "示例:"
    echo "  $0 video.mp4 output.webm"
    echo "  $0 video.mp4 output.webm 0x00FF00 0.25 0.05"
    exit 1
fi

if [ ! -f "$INPUT" ]; then
    echo "错误: 输入文件不存在: $INPUT"
    exit 1
fi

echo "开始绿幕抠图..."
echo "输入: $INPUT"
echo "输出: $OUTPUT"
echo "绿色值: $GREEN_COLOR"
echo "相似度: $SIMILARITY"
echo "混合度: $BLEND"
echo ""

ffmpeg -i "$INPUT" \
    -vf "chromakey=${GREEN_COLOR}:${SIMILARITY}:${BLEND}" \
    -c:v libvpx-vp9 \
    -pix_fmt yuva420p \
    -c:a libopus \
    -y \
    "$OUTPUT"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ 转换成功: $OUTPUT"
else
    echo ""
    echo "✗ 转换失败"
    exit 1
fi
