#!/usr/bin/env python3
"""
ASR 结果处理器 - 提取精确句子

只提取 definite: true 的条目，这些是 ASR 确定的完整句子。
"""

import json
from typing import TypedDict


class Sentence(TypedDict):
    text: str
    start_time: int  # milliseconds
    end_time: int    # milliseconds


def extract_definite_sentences(asr_data: list[dict]) -> list[Sentence]:
    """
    从 ASR 数据中提取 definite: true 的句子

    Args:
        asr_data: ASR 输出的片段列表

    Returns:
        精确句子列表，按时间排序
    """
    sentences = []
    seen_texts = set()

    for segment in asr_data:
        if segment.get("definite") is True:
            text = segment.get("text", "").strip()
            start = segment.get("start_time", 0)
            end = segment.get("end_time", 0)

            # 去重（相同文本和时间的条目）
            key = (text, start, end)
            if key in seen_texts:
                continue
            seen_texts.add(key)

            if text and start < end:
                sentences.append(Sentence(
                    text=text,
                    start_time=start,
                    end_time=end
                ))

    # 按开始时间排序
    sentences.sort(key=lambda x: x["start_time"])

    return sentences


def filter_by_duration(sentences: list[Sentence], max_ms: int) -> list[Sentence]:
    """
    过滤出指定时长内的句子

    Args:
        sentences: 句子列表
        max_ms: 最大时长（毫秒）

    Returns:
        过滤后的句子列表
    """
    return [s for s in sentences if s["end_time"] <= max_ms]


def load_asr_file(file_path: str) -> list[dict]:
    """加载 ASR JSON 文件"""
    with open(file_path) as f:
        return json.load(f)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python asr_processor.py <asr_json_file> [max_duration_seconds]")
        sys.exit(1)

    asr_file = sys.argv[1]
    max_duration = int(sys.argv[2]) * 1000 if len(sys.argv) > 2 else None

    asr_data = load_asr_file(asr_file)
    sentences = extract_definite_sentences(asr_data)

    if max_duration:
        sentences = filter_by_duration(sentences, max_duration)

    print(f"Total definite sentences: {len(sentences)}")
    for i, s in enumerate(sentences, 1):
        start_s = s["start_time"] / 1000
        end_s = s["end_time"] / 1000
        print(f"{i:3}. [{start_s:6.2f}s - {end_s:6.2f}s] {s['text']}")
