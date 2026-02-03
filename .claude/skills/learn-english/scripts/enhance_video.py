#!/usr/bin/env python3
"""
视频英语学习增强工具 - 主入口

功能：
1. 从 ASR 结果中提取精确句子
2. 识别包含生词的句子
3. 对这些句子进行慢速播放 + TTS 讲解 + 原速重播
4. 生成增强后的音频
5. 生成学习笔记 notes.txt

使用方法：
    python enhance_video.py \
        --audio /path/to/source.mp3 \
        --asr /path/to/asr.json \
        --output-dir ~/Library/Mobile Documents/com~apple~CloudDocs/practiceEngListen/260202_example \
        --duration 900
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# 添加当前目录到 path
sys.path.insert(0, str(Path(__file__).parent))

from asr_processor import extract_definite_sentences, filter_by_duration, load_asr_file
from vocab_matcher import find_unfamiliar_words, get_known_words_set
from audio_mixer import AudioMixer, cut_audio, slow_down_audio, normalize_audio, concat_audios, get_audio_duration_ms, FFMPEG_PATH


# TTS 脚本路径
TTS_SCRIPT = Path.home() / ".claude" / "skills" / "api-tts" / "scripts" / "tts.py"

# OpenRouter 脚本路径
OPENROUTER_SCRIPT = Path.home() / ".claude" / "skills" / "api-openrouter" / "scripts" / "openrouter_chat.py"

# iCloud practiceEngListen 目录
ICLOUD_BASE = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "practiceEngListen"

# 预置词汇释义（通俗版）
DEFINITIONS = {
    # 存储相关
    "terabyte": "TB，大约能存一千部高清电影",
    "megapixels": "百万像素，数字越大照片越清晰",
    "gigabytes": "GB，手机存储的常用单位",
    "gigs": "GB的口语说法",
    # 电池相关
    "milliamp": "毫安，电池容量单位",
    "watts": "瓦特，充电功率单位",
    # 音频相关
    "stereo": "立体声，左右耳听到不同声音",
    # 品牌相关
    "vertu": "Vertu，英国奢侈手机品牌",
    "virtu": "Vertu的另一种拼法",
    # 技术术语
    "specs": "规格参数的缩写",
    "flagship": "旗舰，最高端的产品",
    # 常见俚语
    "gooning": "沉迷于某事无法自拔",
    "edging": "故意拖延达到高潮",
    "binges": "暴饮暴食或沉迷行为",
}

# 难度判断阈值
DIFFICULTY_THRESHOLDS = {
    "min_unfamiliar_words": 2,  # 生词 >= 2 个视为困难，需要整句讲解
}


@dataclass
class EnhancementPoint:
    """增强点"""
    sentence_text: str
    start_ms: int
    end_ms: int
    unfamiliar_words: list[str]
    tts_text: str
    sentence_translation: str = ""  # 整句翻译
    word_explanations: list[dict] = field(default_factory=list)  # 生词详解
    is_difficult: bool = False  # 是否需要整句讲解


def is_difficult_sentence(sentence: str, unfamiliar_words: list[str]) -> bool:
    """
    判断句子是否难以理解，需要整句讲解

    条件：生词 >= 2 个

    Args:
        sentence: 原句
        unfamiliar_words: 生词列表

    Returns:
        是否难以理解
    """
    return len(unfamiliar_words) >= DIFFICULTY_THRESHOLDS["min_unfamiliar_words"]


def call_openrouter_for_explanation(sentence: str, unfamiliar_words: list[str]) -> tuple[str, list[dict]]:
    """
    调用 OpenRouter AI 翻译句子并解释生词

    Args:
        sentence: 原句
        unfamiliar_words: 生词列表

    Returns:
        (整句翻译, 生词解释列表)
    """
    words_str = ", ".join(unfamiliar_words[:5])

    prompt = f"""你是英语学习助手。用户是中国人，英语水平 C1（托福 100+，词汇量约 14000）。

请翻译这句话，并解释其中的生词。要求：
1. 翻译要通俗自然，用大白话
2. 生词解释要简洁，10 字以内
3. 只返回 JSON，不要其他内容

原句：{sentence}

生词：{words_str}

返回格式：
{{"translation": "整句翻译", "words": [{{"word": "xxx", "meaning": "简短解释"}}]}}"""

    try:
        result = subprocess.run(
            ["python", str(OPENROUTER_SCRIPT), "--prompt", prompt, "--model", "google/gemini-2.0-flash-001"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(OPENROUTER_SCRIPT.parent.parent),
        )

        if result.returncode == 0:
            output = result.stdout.strip()
            # 提取 JSON 部分
            if "{" in output and "}" in output:
                json_start = output.find("{")
                json_end = output.rfind("}") + 1
                json_str = output[json_start:json_end]
                data = json.loads(json_str)
                translation = data.get("translation", "")
                words = data.get("words", [])
                return translation, words
    except Exception as e:
        print(f"  OpenRouter call failed: {e}")

    return "", []


def load_definitions(file_path: Optional[str] = None) -> dict:
    """加载词汇释义"""
    definitions = DEFINITIONS.copy()

    if file_path and Path(file_path).exists():
        with open(file_path) as f:
            custom = json.load(f)
            definitions.update(custom)

    return definitions


def generate_tts_text(words: list[str], sentence: str, definitions: dict) -> tuple[str, str, list[dict]]:
    """
    生成 TTS 讲解文本（通俗易懂版）

    Args:
        words: 生词列表
        sentence: 原句
        definitions: 词汇释义字典

    Returns:
        (tts_text, sentence_translation, word_explanations)
    """
    parts = []
    word_explanations = []

    for word in words[:3]:  # 最多讲解 3 个词
        lower_word = word.lower()
        if lower_word in definitions:
            explanation = definitions[lower_word]
            parts.append(f"{word}，{explanation}")
            word_explanations.append({"word": word, "meaning": explanation})
        else:
            # 没有预置释义，只读单词
            parts.append(word)
            word_explanations.append({"word": word, "meaning": "（需查词典）"})

    tts_text = "。".join(parts)

    # 整句翻译留空，由调用者用 AI 补充
    sentence_translation = ""

    return tts_text, sentence_translation, word_explanations


def call_tts(text: str, output_path: str) -> str:
    """
    调用 TTS 脚本生成语音

    Args:
        text: 待合成文本
        output_path: 输出文件路径

    Returns:
        输出文件路径
    """
    cmd = [
        "python", str(TTS_SCRIPT),
        text,
        "--voice", "yangyang",  # 使用炀炀音色
        "--output", output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"TTS failed: {result.stderr}")
        raise RuntimeError(f"TTS synthesis failed: {result.stderr}")

    return output_path


def select_enhancement_points(
    sentences: list[dict],
    known_words: set[str],
    max_per_minute: int = 3,
    min_interval_ms: int = 10000
) -> list[EnhancementPoint]:
    """
    选择需要增强的句子

    规则：
    - 每分钟最多 max_per_minute 个增强点
    - 相邻增强间隔 >= min_interval_ms
    - 优先选择生词多的句子

    Args:
        sentences: 句子列表
        known_words: 已知词汇集合
        max_per_minute: 每分钟最大增强数
        min_interval_ms: 最小间隔（毫秒）

    Returns:
        增强点列表
    """
    definitions = load_definitions()

    # 为每个句子计算生词
    candidates = []
    for s in sentences:
        unfamiliar = find_unfamiliar_words(s["text"], known_words)
        if unfamiliar:
            tts_text, sentence_translation, word_explanations = generate_tts_text(
                unfamiliar, s["text"], definitions
            )
            is_diff = is_difficult_sentence(s["text"], unfamiliar)
            candidates.append(EnhancementPoint(
                sentence_text=s["text"],
                start_ms=s["start_time"],
                end_ms=s["end_time"],
                unfamiliar_words=unfamiliar,
                tts_text=tts_text,
                sentence_translation=sentence_translation,
                word_explanations=word_explanations,
                is_difficult=is_diff,
            ))

    # 按生词数量降序排序
    candidates.sort(key=lambda x: len(x.unfamiliar_words), reverse=True)

    # 选择增强点（考虑间隔限制）
    selected = []
    for candidate in candidates:
        # 检查与已选择点的间隔
        too_close = False
        for existing in selected:
            if abs(candidate.start_ms - existing.start_ms) < min_interval_ms:
                too_close = True
                break

        if not too_close:
            selected.append(candidate)

        # 检查每分钟限制
        duration_minutes = (candidate.end_ms / 1000) / 60 + 1
        if len(selected) >= max_per_minute * duration_minutes:
            break

    # 按时间排序
    selected.sort(key=lambda x: x.start_ms)

    # 对难句调用 AI 翻译
    difficult_count = sum(1 for ep in selected if ep.is_difficult)
    if difficult_count > 0:
        print(f"  Translating {difficult_count} difficult sentences with AI...")
        for ep in selected:
            if ep.is_difficult:
                translation, ai_words = call_openrouter_for_explanation(ep.sentence_text, ep.unfamiliar_words)
                if translation:
                    ep.sentence_translation = translation
                    # 用 AI 解释更新 TTS 文本
                    ep.tts_text = f"这句话的意思是，{translation}"
                if ai_words:
                    # 合并 AI 解释到 word_explanations
                    ai_dict = {w["word"].lower(): w["meaning"] for w in ai_words}
                    for we in ep.word_explanations:
                        if we["word"].lower() in ai_dict:
                            we["meaning"] = ai_dict[we["word"].lower()]

    return selected


def ms_to_time_str(ms: int) -> str:
    """毫秒转时间字符串 MM:SS"""
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def ms_to_lrc_time(ms: int) -> str:
    """毫秒转 LRC 时间格式 [mm:ss.xx]"""
    total_sec = ms / 1000
    minutes = int(total_sec // 60)
    seconds = total_sec % 60
    return f"[{minutes:02d}:{seconds:05.2f}]"


@dataclass
class TimelineEntry:
    """时间轴条目"""
    start_ms: int
    text: str
    entry_type: str  # "normal", "slow", "tts", "replay"
    unfamiliar_words: list[str] = field(default_factory=list)


def mark_unfamiliar_words(text: str, unfamiliar_words: list[str]) -> str:
    """在文本中标记生词，用 __word__ 格式"""
    if not unfamiliar_words:
        return text

    # 创建小写生词集合用于匹配
    unfamiliar_set = {w.lower() for w in unfamiliar_words}

    # 按单词分割，保留标点
    import re
    # 分割保留单词和非单词部分
    parts = re.split(r'(\b\w+\b)', text)

    result = []
    for part in parts:
        if part and part.lower() in unfamiliar_set:
            result.append(f"__{part}__")
        else:
            result.append(part)

    return ''.join(result)


def generate_lrc_file(
    output_dir: Path,
    timeline: list[TimelineEntry],
    title: str = "Enhanced Audio",
) -> str:
    """
    生成 LRC 歌词文件

    Args:
        output_dir: 输出目录
        timeline: 时间轴条目列表
        title: 标题

    Returns:
        LRC 文件路径
    """
    lrc_path = output_dir / "enhanced.lrc"

    lines = [
        f"[ti:{title}]",
        "[ar:Learn English]",
        "[by:viva-enhance]",
        "",
    ]

    for entry in timeline:
        lrc_time = ms_to_lrc_time(entry.start_ms)
        # 标记生词
        marked_text = mark_unfamiliar_words(entry.text, entry.unfamiliar_words)
        # 根据类型添加标记
        if entry.entry_type == "slow":
            lines.append(f"{lrc_time}🐢 {marked_text}")
        elif entry.entry_type == "tts":
            lines.append(f"{lrc_time}📖 {entry.text}")  # TTS 不标记生词
        elif entry.entry_type == "replay":
            lines.append(f"{lrc_time}🔁 {marked_text}")
        else:
            lines.append(f"{lrc_time}{entry.text}")  # 普通句子不标记

    lrc_content = "\n".join(lines)

    with open(lrc_path, "w", encoding="utf-8") as f:
        f.write(lrc_content)

    return str(lrc_path)


def generate_notes_file(
    output_dir: Path,
    enhancement_points: list[EnhancementPoint],
    source_url: str = "",
    duration_seconds: int = 0,
) -> str:
    """
    生成学习笔记 notes.txt

    Args:
        output_dir: 输出目录
        enhancement_points: 增强点列表
        source_url: 原始视频 URL
        duration_seconds: 处理时长

    Returns:
        notes.txt 路径
    """
    folder_name = output_dir.name
    notes_path = output_dir / "notes.txt"

    lines = [
        f"# {folder_name} 英语学习笔记",
        "",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
    ]

    if source_url:
        lines.append(f"原始视频：{source_url}")

    if duration_seconds:
        minutes = duration_seconds // 60
        lines.append(f"处理时长：{minutes} 分钟")

    lines.extend(["", "---", ""])

    for i, ep in enumerate(enhancement_points, 1):
        time_range = f"{ms_to_time_str(ep.start_ms)} - {ms_to_time_str(ep.end_ms)}"

        lines.extend([
            f"## 增强点 {i} [{time_range}]",
            "",
            f"原文：{ep.sentence_text}",
        ])

        if ep.sentence_translation:
            lines.append(f"整句意思：{ep.sentence_translation}")
        else:
            lines.append("整句意思：（需补充）")

        lines.extend(["", "生词讲解："])

        for we in ep.word_explanations:
            lines.append(f"- {we['word']}: {we['meaning']}")

        lines.extend(["", "---", ""])

    notes_content = "\n".join(lines)
    notes_path.write_text(notes_content, encoding="utf-8")

    return str(notes_path)


def calculate_wpm(asr_data: list, max_duration_ms: Optional[int] = None) -> tuple[int, int, int]:
    """
    计算 ASR 数据的语速 (Words Per Minute)

    Args:
        asr_data: ASR 段落列表
        max_duration_ms: 最大时长限制（毫秒）

    Returns:
        (wpm, total_words, duration_ms)
    """
    definite_segs = [s for s in asr_data if s.get('definite', False)]
    if not definite_segs:
        return 0, 0, 0

    total_words = 0
    max_time = 0
    min_time = float('inf')

    for seg in definite_segs:
        if max_duration_ms and seg['start_time'] > max_duration_ms:
            continue
        words = len(seg['text'].split())
        total_words += words
        if seg['start_time'] < min_time:
            min_time = seg['start_time']
        if seg['end_time'] > max_time:
            max_time = min(seg['end_time'], max_duration_ms) if max_duration_ms else seg['end_time']

    duration_ms = max_time - min_time if max_time > min_time else 0
    duration_minutes = duration_ms / 1000 / 60
    wpm = int(total_words / duration_minutes) if duration_minutes > 0 else 0

    return wpm, total_words, duration_ms


def adjust_speed_if_needed(
    source_audio: str,
    asr_data: list,
    target_wpm: int,
    current_wpm: int,
    work_dir: Path
) -> tuple[str, list, float]:
    """
    如果当前语速超过目标，减速音频并调整 ASR 时间戳

    Returns:
        (adjusted_audio_path, adjusted_asr_data, scale_factor)
    """
    if current_wpm <= target_wpm:
        return source_audio, asr_data, 1.0

    # 计算减速比例
    atempo = target_wpm / current_wpm
    scale_factor = current_wpm / target_wpm

    print(f"  Speed adjustment: {current_wpm} WPM → {target_wpm} WPM (atempo={atempo:.3f})")

    # 减速音频
    adjusted_audio = work_dir / "speed_adjusted.mp3"
    cmd = [
        FFMPEG_PATH, "-y", "-i", source_audio,
        "-filter:a", f"atempo={atempo}",
        str(adjusted_audio)
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    # 调整 ASR 时间戳
    adjusted_asr = []
    for seg in asr_data:
        new_seg = seg.copy()
        new_seg['start_time'] = int(seg['start_time'] * scale_factor)
        new_seg['end_time'] = int(seg['end_time'] * scale_factor)
        adjusted_asr.append(new_seg)

    return str(adjusted_audio), adjusted_asr, scale_factor


def enhance_audio(
    source_audio: str,
    asr_file: str,
    output_dir: str,
    max_duration_ms: Optional[int] = None,
    target_wpm: int = 100,
    source_url: str = "",
    work_dir: Optional[str] = None
) -> tuple[str, str]:
    """
    增强音频

    Args:
        source_audio: 原始音频文件
        asr_file: ASR JSON 文件
        output_dir: 输出目录
        max_duration_ms: 最大处理时长（毫秒）
        target_wpm: 目标语速 WPM（默认 100）
        source_url: 原始视频 URL
        work_dir: 工作目录

    Returns:
        (enhanced.mp3 路径, notes.txt 路径, enhanced.lrc 路径)
    """
    # 创建输出目录
    output_path = Path(output_dir).expanduser()
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / "enhanced.mp3"

    print(f"Loading ASR data from {asr_file}...")
    asr_data = load_asr_file(asr_file)

    # 创建临时工作目录（语速调整需要）
    if work_dir:
        work_path = Path(work_dir)
        work_path.mkdir(parents=True, exist_ok=True)
    else:
        work_path = Path(tempfile.mkdtemp())

    # 计算当前语速并调整
    current_wpm, total_words, _ = calculate_wpm(asr_data, max_duration_ms)
    print(f"  Current speed: {current_wpm} WPM ({total_words} words)")

    if target_wpm and current_wpm > target_wpm:
        source_audio, asr_data, scale_factor = adjust_speed_if_needed(
            source_audio, asr_data, target_wpm, current_wpm, work_path
        )
        # 调整 max_duration_ms
        if max_duration_ms:
            max_duration_ms = int(max_duration_ms * scale_factor)
            print(f"  Adjusted duration limit: {max_duration_ms/1000:.1f}s")

    print("Extracting definite sentences...")
    sentences = extract_definite_sentences(asr_data)
    print(f"  Found {len(sentences)} definite sentences")

    if max_duration_ms:
        sentences = filter_by_duration(sentences, max_duration_ms)
        print(f"  After filtering: {len(sentences)} sentences within {max_duration_ms/1000:.1f}s")

    print("Loading vocabulary from Supabase...")
    known_words = get_known_words_set()
    print(f"  Known words: {len(known_words)}")

    print("Selecting enhancement points...")
    enhancement_points = select_enhancement_points(sentences, known_words)
    print(f"  Selected {len(enhancement_points)} enhancement points:")

    for i, ep in enumerate(enhancement_points, 1):
        difficulty_mark = " [难]" if ep.is_difficult else ""
        print(f"    {i}. [{ep.start_ms/1000:.1f}s - {ep.end_ms/1000:.1f}s]{difficulty_mark} {ep.unfamiliar_words}")

    if not enhancement_points:
        print("No enhancement points found, copying original audio...")
        subprocess.run(["cp", source_audio, str(output_file)], check=True)
        # 生成空的 notes.txt 和 LRC
        notes_path = generate_notes_file(
            output_path, [], source_url,
            int(max_duration_ms / 1000) if max_duration_ms else 0
        )
        lrc_path = generate_lrc_file(output_path, [], title=output_path.name)
        return str(output_file), notes_path, lrc_path

    print(f"Work directory: {work_path}")

    # 获取音频总时长
    total_duration_ms = get_audio_duration_ms(source_audio)
    if max_duration_ms:
        total_duration_ms = min(total_duration_ms, max_duration_ms)

    # 构建音频片段列表和时间轴
    parts = []
    timeline: list[TimelineEntry] = []
    current_pos = 0
    part_idx = 0
    enhanced_time_ms = 0  # 增强后的累计时间

    # 创建增强点时间集合，用于判断句子是否是增强点
    enhancement_start_times = {ep.start_ms for ep in enhancement_points}

    def add_normal_sentences_to_timeline(start_ms: int, end_ms: int, base_enhanced_ms: int):
        """将指定时间范围内的普通句子添加到 timeline"""
        for s in sentences:
            # 句子在范围内且不是增强点
            if s["start_time"] >= start_ms and s["end_time"] <= end_ms:
                if s["start_time"] not in enhancement_start_times:
                    # 计算在增强后时间轴上的位置
                    offset = s["start_time"] - start_ms
                    timeline.append(TimelineEntry(
                        start_ms=base_enhanced_ms + offset,
                        text=s["text"],
                        entry_type="normal"
                    ))

    for ep in enhancement_points:
        # 1. 增强点之前的原始音频
        if ep.start_ms > current_pos:
            part_idx += 1
            before_file = work_path / f"part_{part_idx:03d}_before.mp3"
            cut_audio(source_audio, str(before_file), current_pos, ep.start_ms)
            parts.append(str(before_file))
            # 记录普通句子的时间轴
            add_normal_sentences_to_timeline(current_pos, ep.start_ms, enhanced_time_ms)
            before_duration = get_audio_duration_ms(str(before_file))
            enhanced_time_ms += before_duration
            print(f"  Part {part_idx}: before segment [{current_pos/1000:.1f}s - {ep.start_ms/1000:.1f}s]")

        # 2. 慢速播放增强句子
        part_idx += 1
        highlight_orig = work_path / f"part_{part_idx:03d}_highlight_orig.mp3"
        cut_audio(source_audio, str(highlight_orig), ep.start_ms, ep.end_ms)

        highlight_slow = work_path / f"part_{part_idx:03d}_highlight_slow.mp3"
        slow_down_audio(str(highlight_orig), str(highlight_slow), tempo=0.7)
        parts.append(str(highlight_slow))
        # 记录慢速时间轴（包含生词标记）
        timeline.append(TimelineEntry(
            start_ms=enhanced_time_ms,
            text=ep.sentence_text,
            entry_type="slow",
            unfamiliar_words=ep.unfamiliar_words
        ))
        slow_duration = get_audio_duration_ms(str(highlight_slow))
        enhanced_time_ms += slow_duration
        print(f"  Part {part_idx}: slow segment [{ep.start_ms/1000:.1f}s - {ep.end_ms/1000:.1f}s] (0.7x)")

        # 3. TTS 讲解
        if ep.tts_text:
            part_idx += 1
            tts_raw = work_path / f"part_{part_idx:03d}_tts_raw.mp3"
            tts_padded = work_path / f"part_{part_idx:03d}_tts_padded.mp3"

            print(f"  Generating TTS: {ep.tts_text[:50]}...")
            call_tts(ep.tts_text, str(tts_raw))

            # 标准化并添加静音填充
            tts_norm = work_path / f"part_{part_idx:03d}_tts_norm.mp3"
            normalize_audio(str(tts_raw), str(tts_norm))

            # 使用 ffmpeg 添加静音
            subprocess.run([
                FFMPEG_PATH, "-y", "-hide_banner", "-loglevel", "warning",
                "-i", str(tts_norm),
                "-af", "adelay=800|800,apad=pad_dur=1",
                "-ar", "44100", "-ac", "2", "-b:a", "128k",
                str(tts_padded)
            ], check=True)

            parts.append(str(tts_padded))
            # 记录 TTS 时间轴
            timeline.append(TimelineEntry(
                start_ms=enhanced_time_ms,
                text=ep.tts_text,
                entry_type="tts"
            ))
            tts_duration = get_audio_duration_ms(str(tts_padded))
            enhanced_time_ms += tts_duration
            print(f"  Part {part_idx}: TTS with padding")

        # 4. 原速重播
        part_idx += 1
        replay = work_path / f"part_{part_idx:03d}_replay.mp3"
        normalize_audio(str(highlight_orig), str(replay))
        parts.append(str(replay))
        # 记录重播时间轴（包含生词标记）
        timeline.append(TimelineEntry(
            start_ms=enhanced_time_ms,
            text=ep.sentence_text,
            entry_type="replay",
            unfamiliar_words=ep.unfamiliar_words
        ))
        replay_duration = get_audio_duration_ms(str(replay))
        enhanced_time_ms += replay_duration
        print(f"  Part {part_idx}: replay at normal speed")

        current_pos = ep.end_ms

    # 5. 最后的原始音频
    if current_pos < total_duration_ms:
        part_idx += 1
        after_file = work_path / f"part_{part_idx:03d}_after.mp3"
        cut_audio(source_audio, str(after_file), current_pos, total_duration_ms)
        parts.append(str(after_file))
        # 记录最后段落中的普通句子
        add_normal_sentences_to_timeline(current_pos, total_duration_ms, enhanced_time_ms)
        print(f"  Part {part_idx}: after segment [{current_pos/1000:.1f}s - {total_duration_ms/1000:.1f}s]")

    # 拼接所有片段
    print(f"\nConcatenating {len(parts)} parts...")
    concat_audios(parts, str(output_file))

    # 生成学习笔记
    print("Generating notes.txt...")
    notes_path = generate_notes_file(
        output_path,
        enhancement_points,
        source_url,
        int(max_duration_ms / 1000) if max_duration_ms else int(total_duration_ms / 1000)
    )

    # 生成 LRC 歌词文件
    print("Generating enhanced.lrc...")
    lrc_path = generate_lrc_file(
        output_path,
        timeline,
        title=output_path.name
    )

    # 输出统计
    enhanced_duration = get_audio_duration_ms(str(output_file))
    print(f"\nEnhancement complete!")
    print(f"  Original duration: {total_duration_ms/1000:.1f}s")
    print(f"  Enhanced duration: {enhanced_duration/1000:.1f}s")
    print(f"  Timeline entries: {len(timeline)}")
    print(f"  Output directory: {output_dir}")
    print(f"  - enhanced.mp3")
    print(f"  - enhanced.lrc")
    print(f"  - notes.txt")

    return str(output_file), notes_path, lrc_path


def main():
    parser = argparse.ArgumentParser(description="视频英语学习增强工具")
    parser.add_argument("--audio", "-a", required=True, help="原始音频文件")
    parser.add_argument("--asr", "-r", required=True, help="ASR JSON 文件")

    # 支持两种输出方式
    output_group = parser.add_mutually_exclusive_group(required=True)
    output_group.add_argument("--output", "-o", help="输出文件（旧版兼容）")
    output_group.add_argument("--output-dir", help="输出目录（推荐，会生成 enhanced.mp3 和 notes.txt）")

    parser.add_argument("--duration", "-d", type=int, help="只处理前 N 秒")
    parser.add_argument("--target-wpm", type=int, default=100, help="目标语速 WPM（默认 100）")
    parser.add_argument("--url", "-u", help="原始视频 URL（可选，用于 notes.txt）")
    parser.add_argument("--work-dir", "-w", help="工作目录（存放临时文件）")

    args = parser.parse_args()

    max_duration_ms = args.duration * 1000 if args.duration else None

    if args.output_dir:
        # 新版：输出到目录
        enhance_audio(
            source_audio=args.audio,
            asr_file=args.asr,
            output_dir=args.output_dir,
            max_duration_ms=max_duration_ms,
            target_wpm=args.target_wpm,
            source_url=args.url or "",
            work_dir=args.work_dir,
        )
    else:
        # 旧版兼容：输出到单个文件
        # 创建临时目录，然后移动文件
        temp_dir = tempfile.mkdtemp()
        enhance_audio(
            source_audio=args.audio,
            asr_file=args.asr,
            output_dir=temp_dir,
            max_duration_ms=max_duration_ms,
            target_wpm=args.target_wpm,
            source_url=args.url or "",
            work_dir=args.work_dir,
        )
        # 移动 enhanced.mp3 到指定位置
        import shutil
        shutil.move(Path(temp_dir) / "enhanced.mp3", args.output)
        print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
