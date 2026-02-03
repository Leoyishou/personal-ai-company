#!/usr/bin/env python3
"""
音频混合器 - 使用 FFmpeg 处理音频

功能：
- 切割音频片段
- 变速处理（0.7x 慢放）
- 拼接音频
- 添加静音填充
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

# FFmpeg 路径（使用 homebrew Cellar 的完整路径）
FFMPEG_PATH = "/opt/homebrew/Cellar/ffmpeg/8.0.1_2/bin/ffmpeg"
FFPROBE_PATH = "/opt/homebrew/Cellar/ffmpeg/8.0.1_2/bin/ffprobe"

# 如果 Cellar 路径不存在，尝试其他位置
if not Path(FFMPEG_PATH).exists():
    FFMPEG_PATH = "/opt/homebrew/bin/ffmpeg"
if not Path(FFPROBE_PATH).exists():
    FFPROBE_PATH = "/opt/homebrew/bin/ffprobe"

# 最后回退到系统默认
if not Path(FFMPEG_PATH).exists():
    FFMPEG_PATH = "ffmpeg"
if not Path(FFPROBE_PATH).exists():
    FFPROBE_PATH = "ffprobe"


def run_ffmpeg(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """运行 FFmpeg 命令"""
    cmd = [FFMPEG_PATH, "-y", "-hide_banner", "-loglevel", "warning"] + args
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def get_audio_duration_ms(file_path: str) -> int:
    """获取音频时长（毫秒）"""
    cmd = [
        FFPROBE_PATH, "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration_sec = float(result.stdout.strip())
    return int(duration_sec * 1000)


def cut_audio(
    input_file: str,
    output_file: str,
    start_ms: int,
    end_ms: int,
    normalize: bool = True
) -> str:
    """
    切割音频片段

    Args:
        input_file: 输入文件
        output_file: 输出文件
        start_ms: 开始时间（毫秒）
        end_ms: 结束时间（毫秒）
        normalize: 是否标准化格式

    Returns:
        输出文件路径
    """
    start_sec = start_ms / 1000
    duration_sec = (end_ms - start_ms) / 1000

    args = [
        "-i", input_file,
        "-ss", str(start_sec),
        "-t", str(duration_sec),
    ]

    if normalize:
        args.extend(["-ar", "44100", "-ac", "2", "-b:a", "128k"])

    args.append(output_file)

    run_ffmpeg(args)
    return output_file


def slow_down_audio(
    input_file: str,
    output_file: str,
    tempo: float = 0.7
) -> str:
    """
    减慢音频速度

    Args:
        input_file: 输入文件
        output_file: 输出文件
        tempo: 速度倍率（0.7 = 减速到 70%）

    Returns:
        输出文件路径
    """
    # atempo 只支持 0.5-2.0 范围
    args = [
        "-i", input_file,
        "-filter:a", f"atempo={tempo}",
        "-ar", "44100", "-ac", "2", "-b:a", "128k",
        output_file
    ]

    run_ffmpeg(args)
    return output_file


def add_silence_padding(
    input_file: str,
    output_file: str,
    pad_start_ms: int = 800,
    pad_end_ms: int = 1000
) -> str:
    """
    为音频添加静音填充

    Args:
        input_file: 输入文件
        output_file: 输出文件
        pad_start_ms: 开头静音时长（毫秒）
        pad_end_ms: 结尾静音时长（毫秒）

    Returns:
        输出文件路径
    """
    pad_start_sec = pad_start_ms / 1000
    pad_end_sec = pad_end_ms / 1000

    filter_complex = f"apad=pad_len=0,adelay={int(pad_start_ms)}|{int(pad_start_ms)},apad=pad_dur={pad_end_sec}"

    args = [
        "-i", input_file,
        "-af", filter_complex,
        "-ar", "44100", "-ac", "2", "-b:a", "128k",
        output_file
    ]

    run_ffmpeg(args)
    return output_file


def concat_audios(
    input_files: list[str],
    output_file: str,
    crossfade_ms: int = 100
) -> str:
    """
    拼接多个音频文件

    Args:
        input_files: 输入文件列表
        output_file: 输出文件
        crossfade_ms: 交叉淡化时长（毫秒）

    Returns:
        输出文件路径
    """
    if len(input_files) == 1:
        # 只有一个文件，直接复制
        subprocess.run(["cp", input_files[0], output_file], check=True)
        return output_file

    # 创建 concat 文件列表
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for input_file in input_files:
            f.write(f"file '{input_file}'\n")
        concat_list = f.name

    try:
        args = [
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list,
            "-ar", "44100", "-ac", "2", "-b:a", "128k",
            output_file
        ]

        run_ffmpeg(args)
    finally:
        os.unlink(concat_list)

    return output_file


def normalize_audio(input_file: str, output_file: str) -> str:
    """
    标准化音频格式（44100Hz, stereo, 128kbps）

    Args:
        input_file: 输入文件
        output_file: 输出文件

    Returns:
        输出文件路径
    """
    args = [
        "-i", input_file,
        "-ar", "44100", "-ac", "2", "-b:a", "128k",
        output_file
    ]

    run_ffmpeg(args)
    return output_file


class AudioMixer:
    """音频混合器类"""

    def __init__(self, source_audio: str, work_dir: Optional[str] = None):
        """
        初始化混合器

        Args:
            source_audio: 原始音频文件
            work_dir: 工作目录（临时文件存放）
        """
        self.source_audio = source_audio
        self.work_dir = Path(work_dir) if work_dir else Path(tempfile.mkdtemp())
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.part_counter = 0

    def _next_part_path(self, suffix: str = ".mp3") -> str:
        """生成下一个临时文件路径"""
        self.part_counter += 1
        return str(self.work_dir / f"part_{self.part_counter:03d}{suffix}")

    def cut_segment(self, start_ms: int, end_ms: int) -> str:
        """切割一段音频"""
        output = self._next_part_path()
        return cut_audio(self.source_audio, output, start_ms, end_ms)

    def slow_segment(self, input_file: str, tempo: float = 0.7) -> str:
        """对片段进行减速"""
        output = self._next_part_path("_slow.mp3")
        return slow_down_audio(input_file, output, tempo)

    def add_tts(self, tts_file: str, pad_start: int = 800, pad_end: int = 1000) -> str:
        """添加 TTS 音频（带静音填充）"""
        output = self._next_part_path("_tts.mp3")
        # 先标准化
        normalized = self._next_part_path("_tts_norm.mp3")
        normalize_audio(tts_file, normalized)

        # 添加填充
        return add_silence_padding(normalized, output, pad_start, pad_end)

    def concat(self, parts: list[str], output_file: str) -> str:
        """拼接所有片段"""
        return concat_audios(parts, output_file)


if __name__ == "__main__":
    # 测试
    import sys

    if len(sys.argv) < 2:
        print("Usage: python audio_mixer.py <audio_file>")
        sys.exit(1)

    audio_file = sys.argv[1]
    duration = get_audio_duration_ms(audio_file)
    print(f"Duration: {duration}ms ({duration/1000:.2f}s)")
