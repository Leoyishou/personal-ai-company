#!/usr/bin/env python3
"""
生成增强音频的 LRC 歌词文件

由于增强音频有慢速段和 TTS 插入，时间轴需要重新计算。
"""

import argparse
import json
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from asr_processor import extract_definite_sentences, filter_by_duration, load_asr_file
from vocab_matcher import find_unfamiliar_words, get_known_words_set
from audio_mixer import get_audio_duration_ms


@dataclass
class EnhancementPoint:
    """增强点"""
    sentence_text: str
    start_ms: int
    end_ms: int
    unfamiliar_words: list[str]
    tts_text: str


def select_enhancement_points(
    sentences: list[dict],
    known_words: set[str],
    max_per_minute: int = 3,
    min_interval_ms: int = 10000
) -> list[EnhancementPoint]:
    """选择需要增强的句子（与 enhance_video.py 保持一致）"""

    DEFINITIONS = {
        "terabyte": "TB，一万亿字节",
        "megapixels": "百万像素",
        "gigabytes": "GB，十亿字节",
        "gigs": "GB的口语说法",
        "milliamp": "毫安，电池容量单位",
        "watts": "瓦特，功率单位",
        "stereo": "立体声",
        "vertu": "Vertu，英国奢侈手机品牌",
        "virtu": "Vertu品牌",
        "specs": "规格参数",
        "flagship": "旗舰产品",
        "amoled": "AMOLED屏幕",
        "bucks": "美元（口语）",
    }

    def generate_tts_text(words: list[str]) -> str:
        parts = []
        for word in words[:3]:
            lower_word = word.lower()
            if lower_word in DEFINITIONS:
                parts.append(f"{word}，{DEFINITIONS[lower_word]}")
            else:
                parts.append(word)
        return "。".join(parts)

    candidates = []
    for s in sentences:
        unfamiliar = find_unfamiliar_words(s["text"], known_words)
        if unfamiliar:
            tts_text = generate_tts_text(unfamiliar)
            candidates.append(EnhancementPoint(
                sentence_text=s["text"],
                start_ms=s["start_time"],
                end_ms=s["end_time"],
                unfamiliar_words=unfamiliar,
                tts_text=tts_text,
            ))

    candidates.sort(key=lambda x: len(x.unfamiliar_words), reverse=True)

    selected = []
    for candidate in candidates:
        too_close = False
        for existing in selected:
            if abs(candidate.start_ms - existing.start_ms) < min_interval_ms:
                too_close = True
                break

        if not too_close:
            selected.append(candidate)

        duration_minutes = (candidate.end_ms / 1000) / 60 + 1
        if len(selected) >= max_per_minute * duration_minutes:
            break

    selected.sort(key=lambda x: x.start_ms)
    return selected


def estimate_tts_duration_ms(text: str) -> int:
    """估算 TTS 音频时长（毫秒）"""
    # 中文约 4 字/秒，加上前后静音填充
    char_count = len(text)
    speech_ms = int(char_count / 4 * 1000)
    padding_ms = 800 + 1000  # 前 0.8s + 后 1s
    return speech_ms + padding_ms


def build_enhanced_timeline(
    sentences: list[dict],
    enhancement_points: list[EnhancementPoint],
    max_duration_ms: int
) -> list[tuple[int, str, Optional[str]]]:
    """
    构建增强音频的时间轴

    Returns:
        list of (enhanced_time_ms, text, note) - note 标记是否为讲解
    """
    timeline = []
    current_enhanced_ms = 0
    current_original_ms = 0

    ep_index = 0

    for s in sentences:
        if s["end_time"] > max_duration_ms:
            break

        # 检查是否有增强点
        is_enhanced = False
        ep = None
        if ep_index < len(enhancement_points):
            ep = enhancement_points[ep_index]
            if s["start_time"] == ep.start_ms:
                is_enhanced = True

        if is_enhanced:
            # 计算从上一个位置到增强点的时间
            gap_ms = ep.start_ms - current_original_ms
            current_enhanced_ms += gap_ms

            # 1. 慢速播放（0.7x = 时长 / 0.7）
            sentence_duration = ep.end_ms - ep.start_ms
            slow_duration = int(sentence_duration / 0.7)
            timeline.append((current_enhanced_ms, f"🐢 {s['text']}", "slow"))
            current_enhanced_ms += slow_duration

            # 2. TTS 讲解
            tts_duration = estimate_tts_duration_ms(ep.tts_text)
            words_str = ", ".join(ep.unfamiliar_words[:3])
            timeline.append((current_enhanced_ms, f"📖 {words_str}", "tts"))
            current_enhanced_ms += tts_duration

            # 3. 原速重播
            timeline.append((current_enhanced_ms, f"🔁 {s['text']}", "replay"))
            current_enhanced_ms += sentence_duration

            current_original_ms = ep.end_ms
            ep_index += 1
        else:
            # 普通句子，时间差累加
            gap_ms = s["start_time"] - current_original_ms
            current_enhanced_ms += gap_ms

            timeline.append((current_enhanced_ms, s["text"], None))

            sentence_duration = s["end_time"] - s["start_time"]
            current_enhanced_ms += sentence_duration
            current_original_ms = s["end_time"]

    return timeline


def format_lrc_time(ms: int) -> str:
    """格式化为 LRC 时间 [mm:ss.xx]"""
    total_sec = ms / 1000
    minutes = int(total_sec // 60)
    seconds = total_sec % 60
    return f"[{minutes:02d}:{seconds:05.2f}]"


def generate_lrc(
    asr_file: str,
    output_file: str,
    max_duration_ms: Optional[int] = None,
    title: str = "Enhanced Audio",
    artist: str = "Learn English"
) -> str:
    """生成 LRC 歌词文件"""

    print(f"Loading ASR data from {asr_file}...")
    asr_data = load_asr_file(asr_file)

    print("Extracting definite sentences...")
    sentences = extract_definite_sentences(asr_data)

    if max_duration_ms:
        sentences = filter_by_duration(sentences, max_duration_ms)

    print("Loading vocabulary...")
    known_words = get_known_words_set()

    print("Selecting enhancement points...")
    enhancement_points = select_enhancement_points(sentences, known_words)

    print(f"Building timeline for {len(sentences)} sentences, {len(enhancement_points)} enhancement points...")
    timeline = build_enhanced_timeline(sentences, enhancement_points, max_duration_ms or 999999999)

    # 生成 LRC
    lines = [
        f"[ti:{title}]",
        f"[ar:{artist}]",
        "[by:learn-english skill]",
        "",
    ]

    for time_ms, text, note in timeline:
        lrc_time = format_lrc_time(time_ms)
        lines.append(f"{lrc_time}{text}")

    lrc_content = "\n".join(lines)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(lrc_content)

    print(f"LRC saved to {output_file}")
    print(f"Total lines: {len(timeline)}")

    return output_file


def embed_lrc_to_mp3(mp3_file: str, lrc_file: str, output_file: str) -> str:
    """将 LRC 歌词嵌入 MP3（使用 eyeD3）"""
    import subprocess

    # 读取 LRC 内容
    with open(lrc_file, "r", encoding="utf-8") as f:
        lrc_content = f.read()

    # 先复制文件
    if mp3_file != output_file:
        subprocess.run(["cp", mp3_file, output_file], check=True)

    # 使用 eyeD3 嵌入歌词（如果可用）
    try:
        import eyed3
        audiofile = eyed3.load(output_file)
        if audiofile.tag is None:
            audiofile.initTag()

        # 添加同步歌词
        audiofile.tag.lyrics.set(lrc_content, description="Enhanced")
        audiofile.tag.save()
        print(f"Lyrics embedded to {output_file}")
    except ImportError:
        # 回退：使用 ffmpeg 添加元数据
        print("eyeD3 not available, using ffmpeg metadata...")
        temp_file = output_file + ".tmp.mp3"
        subprocess.run([
            "/opt/homebrew/Cellar/ffmpeg/8.0.1_2/bin/ffmpeg",
            "-y", "-hide_banner", "-loglevel", "warning",
            "-i", output_file,
            "-metadata", f"lyrics={lrc_content[:500]}",  # ffmpeg lyrics 有长度限制
            "-c", "copy",
            temp_file
        ], check=True)
        subprocess.run(["mv", temp_file, output_file], check=True)
        print(f"Metadata added to {output_file} (truncated due to ffmpeg limit)")
        print(f"Tip: Copy {lrc_file} alongside the MP3 for full lyrics support")

    return output_file


def main():
    parser = argparse.ArgumentParser(description="生成增强音频的 LRC 歌词")
    parser.add_argument("--asr", "-a", required=True, help="ASR JSON 文件")
    parser.add_argument("--output", "-o", required=True, help="输出 LRC 文件")
    parser.add_argument("--mp3", "-m", help="要嵌入歌词的 MP3 文件")
    parser.add_argument("--duration", "-d", type=int, help="只处理前 N 秒")
    parser.add_argument("--title", "-t", default="Enhanced Audio", help="歌曲标题")

    args = parser.parse_args()

    max_duration_ms = args.duration * 1000 if args.duration else None

    generate_lrc(
        asr_file=args.asr,
        output_file=args.output,
        max_duration_ms=max_duration_ms,
        title=args.title,
    )

    if args.mp3:
        output_mp3 = args.mp3.replace(".mp3", "_with_lyrics.mp3")
        embed_lrc_to_mp3(args.mp3, args.output, output_mp3)


if __name__ == "__main__":
    main()
