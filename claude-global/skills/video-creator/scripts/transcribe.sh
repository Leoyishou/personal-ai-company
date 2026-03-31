#!/bin/bash
# 音频转录脚本 - 从视频提取音频并生成字幕
# 用法: ./transcribe.sh input_video output_dir [language] [model]

INPUT="$1"
OUTPUT_DIR="${2:-.}"
LANGUAGE="${3:-Chinese}"
MODEL="${4:-base}"

if [ -z "$INPUT" ]; then
    echo "用法: $0 <input_video> [output_dir] [language] [model]"
    echo ""
    echo "参数说明:"
    echo "  input_video  - 输入视频文件"
    echo "  output_dir   - 输出目录 (默认: 当前目录)"
    echo "  language     - 语言 (默认: Chinese)"
    echo "  model        - Whisper模型 (默认: base, 可选: tiny/small/medium/large)"
    echo ""
    echo "示例:"
    echo "  $0 video.webm ./public Chinese base"
    exit 1
fi

if [ ! -f "$INPUT" ]; then
    echo "错误: 输入文件不存在: $INPUT"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"
TEMP_AUDIO="$OUTPUT_DIR/temp_audio.wav"
BASENAME=$(basename "$INPUT" | sed 's/\.[^.]*$//')

echo "Step 1: 提取音频..."
ffmpeg -i "$INPUT" -vn -acodec pcm_s16le -ar 16000 -ac 1 "$TEMP_AUDIO" -y

if [ $? -ne 0 ]; then
    echo "✗ 音频提取失败"
    exit 1
fi

echo ""
echo "Step 2: 转录音频 (语言: $LANGUAGE, 模型: $MODEL)..."
uv run whisper "$TEMP_AUDIO" --language "$LANGUAGE" --model "$MODEL" --output_format srt --output_dir "$OUTPUT_DIR"

if [ $? -ne 0 ]; then
    echo "✗ 转录失败"
    rm -f "$TEMP_AUDIO"
    exit 1
fi

# 重命名输出文件
if [ -f "$OUTPUT_DIR/temp_audio.srt" ]; then
    mv "$OUTPUT_DIR/temp_audio.srt" "$OUTPUT_DIR/subtitles.srt"
fi

# 清理临时文件
rm -f "$TEMP_AUDIO"

echo ""
echo "✓ 转录完成: $OUTPUT_DIR/subtitles.srt"
