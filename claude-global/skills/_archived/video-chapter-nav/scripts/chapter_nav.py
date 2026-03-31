#!/usr/bin/env python3
"""
视频章节导航条生成器
自动为视频添加动态章节导航条

工作流程:
1. 从视频提取音频
2. 使用 ASR 转录音频 (火山引擎或 Whisper)
3. 使用 LLM 分析字幕生成章节
4. 生成 .ass 导航字幕
5. FFmpeg 合成视频
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests

# ============================================================
# 配置和数据类型
# ============================================================

@dataclass
class Chapter:
    """章节信息"""
    title: str
    start_time: float  # 秒
    end_time: float    # 秒

@dataclass
class TranscriptSegment:
    """转录片段"""
    text: str
    start_time: float
    end_time: float

# ============================================================
# 辅助函数
# ============================================================

def format_time_ass(seconds: float) -> str:
    """将秒数转换为 ASS 时间格式 (H:MM:SS.cc)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centisecs = int((seconds % 1) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

def format_time_display(seconds: float) -> str:
    """将秒数转换为显示格式 (MM:SS)"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def get_video_duration(video_path: Path) -> float:
    """获取视频时长"""
    cmd = [
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def get_video_resolution(video_path: Path) -> tuple[int, int]:
    """获取视频分辨率"""
    cmd = [
        "ffprobe", "-v", "quiet", "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0", str(video_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    w, h = result.stdout.strip().split('x')
    return int(w), int(h)

# ============================================================
# 步骤 1: 音频提取
# ============================================================

def extract_audio(video_path: Path, output_path: Path) -> Path:
    """从视频提取音频"""
    print(f"[1/5] 提取音频: {video_path}")
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        "-y", str(output_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"  -> 音频已保存到: {output_path}")
    return output_path

# ============================================================
# 步骤 2: 语音转文字
# ============================================================

def transcribe_volcengine(audio_path: Path) -> list[TranscriptSegment]:
    """使用火山引擎 ASR 转录音频"""
    # 获取配置
    appid = os.environ.get("VOLC_ASR_APPID")
    token = os.environ.get("VOLC_ASR_TOKEN")

    if not appid or not token:
        raise ValueError(
            "火山引擎 ASR 需要配置 VOLC_ASR_APPID 和 VOLC_ASR_TOKEN\n"
            "请在火山引擎控制台获取: https://console.volcengine.com/speech/service/asr"
        )

    url = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash"

    # 读取音频文件并 Base64 编码
    with open(audio_path, 'rb') as f:
        audio_data = base64.b64encode(f.read()).decode('utf-8')

    headers = {
        "X-Api-App-Key": appid,
        "X-Api-Access-Key": token,
        "X-Api-Resource-Id": "volc.bigasr.auc_turbo",
        "X-Api-Request-Id": str(uuid.uuid4()),
        "X-Api-Sequence": "-1",
    }

    body = {
        "user": {"uid": appid},
        "audio": {"data": audio_data},
        "request": {
            "model_name": "bigmodel",
            "enable_itn": True,
            "enable_punc": True,
        }
    }

    print("  调用火山引擎 ASR API...")
    response = requests.post(url, json=body, headers=headers, timeout=300)

    if response.headers.get('X-Api-Status-Code') != '20000000':
        raise RuntimeError(f"ASR 失败: {response.headers.get('X-Api-Message')}")

    result = response.json()
    segments = []

    for utt in result.get("result", {}).get("utterances", []):
        segments.append(TranscriptSegment(
            text=utt["text"],
            start_time=utt["start_time"] / 1000,  # 毫秒转秒
            end_time=utt["end_time"] / 1000,
        ))

    return segments

def transcribe_whisper(audio_path: Path, model_name: str = "base") -> list[TranscriptSegment]:
    """使用 Whisper 转录音频"""
    try:
        import whisper
    except ImportError:
        raise RuntimeError("请安装 openai-whisper: pip install openai-whisper")

    print(f"  加载 Whisper 模型: {model_name}")
    model = whisper.load_model(model_name)

    print("  转录中...")
    result = model.transcribe(str(audio_path), fp16=False, language="zh")

    segments = []
    for seg in result.get("segments", []):
        segments.append(TranscriptSegment(
            text=seg["text"].strip(),
            start_time=seg["start"],
            end_time=seg["end"],
        ))

    return segments

def transcribe_audio(audio_path: Path, asr_engine: str = "auto") -> list[TranscriptSegment]:
    """转录音频"""
    print(f"[2/5] 转录音频: {audio_path}")

    if asr_engine == "auto":
        # 自动检测可用的 ASR 引擎
        if os.environ.get("VOLC_ASR_APPID") and os.environ.get("VOLC_ASR_TOKEN"):
            asr_engine = "volcengine"
        else:
            asr_engine = "whisper"

    print(f"  使用 ASR 引擎: {asr_engine}")

    if asr_engine == "volcengine":
        return transcribe_volcengine(audio_path)
    else:
        return transcribe_whisper(audio_path)

# ============================================================
# 步骤 3: LLM 章节分析
# ============================================================

def analyze_chapters_with_llm(
    transcript: list[TranscriptSegment],
    video_duration: float,
    num_chapters: int = 4,
) -> list[Chapter]:
    """使用 LLM 分析转录内容，生成章节"""
    print(f"[3/5] 分析章节 (目标: {num_chapters} 个)")

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("请配置 OPENROUTER_API_KEY")

    # 构建转录文本（带时间戳）
    transcript_text = "\n".join([
        f"[{format_time_display(seg.start_time)}-{format_time_display(seg.end_time)}] {seg.text}"
        for seg in transcript
    ])

    prompt = f"""分析以下视频转录内容，将其划分为 {num_chapters} 个章节。

转录内容（格式：[开始时间-结束时间] 文字）:
{transcript_text}

视频总时长: {format_time_display(video_duration)}

请返回 JSON 格式的章节列表，每个章节包含:
- title: 简短的章节标题（不超过6个中文字符或10个英文单词）
- start_time: 开始时间（秒数）

要求:
1. 章节标题要简洁明了，概括该段落的核心内容
2. 第一个章节的 start_time 必须是 0
3. 章节数量为 {num_chapters} 个
4. 章节时间点应该落在自然的内容分界处

只返回 JSON 数组，不要有其他文字:
[{{"title": "章节标题", "start_time": 0}}, ...]"""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "google/gemini-2.0-flash-001",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        },
        timeout=60
    )

    if response.status_code != 200:
        raise RuntimeError(f"LLM API 调用失败: {response.text}")

    result = response.json()
    content = result["choices"][0]["message"]["content"]

    # 提取 JSON
    json_match = re.search(r'\[[\s\S]*\]', content)
    if not json_match:
        raise ValueError(f"无法解析 LLM 返回的 JSON: {content}")

    chapters_data = json.loads(json_match.group())

    # 转换为 Chapter 对象
    chapters = []
    for i, ch in enumerate(chapters_data):
        start_time = float(ch["start_time"])
        # 计算结束时间（下一个章节的开始时间或视频结束）
        if i < len(chapters_data) - 1:
            end_time = float(chapters_data[i + 1]["start_time"])
        else:
            end_time = video_duration

        chapters.append(Chapter(
            title=ch["title"],
            start_time=start_time,
            end_time=end_time,
        ))

    for ch in chapters:
        print(f"  {format_time_display(ch.start_time)}-{format_time_display(ch.end_time)}: {ch.title}")

    return chapters

# ============================================================
# 步骤 4: 生成 ASS 字幕
# ============================================================

def generate_ass_subtitle(
    chapters: list[Chapter],
    video_duration: float,
    video_width: int,
    video_height: int,
    output_path: Path,
    position: str = "bottom",  # bottom, top
    margin: int = 60,
) -> Path:
    """生成 ASS 格式的导航条字幕"""
    print(f"[4/5] 生成导航字幕: {output_path}")

    # 计算位置
    if position == "bottom":
        vertical_pos = video_height - margin
        alignment = 2  # 底部居中
    else:
        vertical_pos = margin
        alignment = 8  # 顶部居中

    # 字体大小根据分辨率调整
    font_size = max(24, video_height // 30)

    # ASS 文件头
    ass_content = f"""[Script Info]
Title: Chapter Navigation
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
Timer: 100.0000

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Active,PingFang SC,{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,1,{alignment},10,10,{margin},1
Style: Inactive,PingFang SC,{font_size},&H80AAAAAA,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,1,0,{alignment},10,10,{margin},1
Style: Separator,PingFang SC,{font_size},&H80666666,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,{alignment},10,10,{margin},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    # 为每个时间段生成导航条
    num_chapters = len(chapters)

    for ch_idx, current_chapter in enumerate(chapters):
        start_ass = format_time_ass(current_chapter.start_time)
        end_ass = format_time_ass(current_chapter.end_time)

        # 构建导航条文本
        nav_parts = []
        for i, ch in enumerate(chapters):
            # 序号
            num_str = f"0{i+1}" if i < 9 else str(i+1)

            if i == ch_idx:
                # 当前章节 - 高亮
                nav_parts.append(f"{{\\rActive}}{num_str} {ch.title}")
            else:
                # 其他章节 - 灰色
                nav_parts.append(f"{{\\rInactive}}{num_str} {ch.title}")

        # 用分隔符连接
        separator = "{\\rSeparator}  ·  "
        nav_text = separator.join(nav_parts)

        # 添加事件
        ass_content += f"Dialogue: 0,{start_ass},{end_ass},Active,,0,0,0,,{nav_text}\n"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ass_content)

    print(f"  -> 字幕已保存到: {output_path}")
    return output_path

# ============================================================
# 步骤 5: 合成视频
# ============================================================

def burn_subtitles(
    input_video: Path,
    subtitle_path: Path,
    output_video: Path,
) -> Path:
    """将字幕烧录到视频中"""
    print(f"[5/5] 合成视频: {output_video}")

    # 转义路径中的特殊字符
    sub_path = str(subtitle_path).replace("\\", "/").replace(":", "\\:")

    cmd = [
        "ffmpeg", "-i", str(input_video),
        "-vf", f"ass='{sub_path}'",
        "-c:a", "copy",
        "-y", str(output_video)
    ]

    print(f"  执行: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    print(f"  -> 视频已保存到: {output_video}")
    return output_video

# ============================================================
# 主流程
# ============================================================

def process_video(
    input_video: str,
    output_video: Optional[str] = None,
    num_chapters: int = 4,
    asr_engine: str = "auto",
    position: str = "bottom",
    dry_run: bool = False,
) -> Path:
    """处理视频，添加章节导航条"""
    input_path = Path(input_video).expanduser().resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"视频文件不存在: {input_path}")

    # 确定输出路径
    if output_video:
        output_path = Path(output_video).expanduser().resolve()
    else:
        output_path = input_path.with_stem(f"{input_path.stem}_with_chapters")

    print(f"\n{'='*60}")
    print(f"视频章节导航条生成器")
    print(f"{'='*60}")
    print(f"输入: {input_path}")
    print(f"输出: {output_path}")
    print(f"章节数: {num_chapters}")
    print(f"ASR 引擎: {asr_engine}")
    print(f"导航位置: {position}")
    print(f"{'='*60}\n")

    if dry_run:
        print("试运行模式，不执行实际操作")
        return output_path

    # 获取视频信息
    duration = get_video_duration(input_path)
    width, height = get_video_resolution(input_path)
    print(f"视频信息: {width}x{height}, 时长 {format_time_display(duration)}\n")

    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # 1. 提取音频
        audio_path = tmpdir / "audio.wav"
        extract_audio(input_path, audio_path)

        # 2. 转录音频
        transcript = transcribe_audio(audio_path, asr_engine)
        print(f"  -> 转录完成，共 {len(transcript)} 个片段\n")

        # 3. 分析章节
        chapters = analyze_chapters_with_llm(transcript, duration, num_chapters)
        print()

        # 4. 生成 ASS 字幕
        subtitle_path = tmpdir / "chapters.ass"
        generate_ass_subtitle(
            chapters, duration, width, height, subtitle_path, position
        )
        print()

        # 5. 合成视频
        burn_subtitles(input_path, subtitle_path, output_path)

    print(f"\n{'='*60}")
    print(f"完成! 输出文件: {output_path}")
    print(f"{'='*60}\n")

    return output_path

def main():
    parser = argparse.ArgumentParser(
        description="为视频添加动态章节导航条",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python chapter_nav.py video.mp4
  python chapter_nav.py video.mp4 --chapters 5
  python chapter_nav.py video.mp4 --output video_nav.mp4
  python chapter_nav.py video.mp4 --asr whisper --position top
        """
    )

    parser.add_argument("video", help="输入视频文件路径")
    parser.add_argument("-o", "--output", help="输出视频文件路径")
    parser.add_argument(
        "-n", "--chapters",
        type=int, default=4,
        help="章节数量 (默认: 4)"
    )
    parser.add_argument(
        "--asr",
        choices=["auto", "whisper", "volcengine"],
        default="auto",
        help="ASR 引擎 (默认: auto)"
    )
    parser.add_argument(
        "--position",
        choices=["bottom", "top"],
        default="bottom",
        help="导航条位置 (默认: bottom)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="试运行，不执行实际操作"
    )

    args = parser.parse_args()

    try:
        process_video(
            input_video=args.video,
            output_video=args.output,
            num_chapters=args.chapters,
            asr_engine=args.asr,
            position=args.position,
            dry_run=args.dry_run,
        )
    except Exception as e:
        print(f"\n错误: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
