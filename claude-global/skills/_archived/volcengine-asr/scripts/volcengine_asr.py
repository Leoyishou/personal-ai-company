#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
火山引擎（豆包）语音识别工具

通过 WebSocket 连接火山引擎 ASR 大模型服务，将音频/视频文件转换为文字。
支持输出 TXT/SRT/VTT/JSON 格式。
"""

import argparse
import asyncio
import json
import os
import struct
import subprocess
import sys
import tempfile
import uuid
from datetime import timedelta
from pathlib import Path

try:
    import websockets
except ImportError:
    print("Error: websockets library not installed. Run: pip install websockets", file=sys.stderr)
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# 加载环境变量
if load_dotenv:
    dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    load_dotenv(dotenv_path, override=False)

# 常量
DEFAULT_SERVICE_URL = "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel"
DEFAULT_RESOURCE_ID = "volc.bigasr.sauc.duration"
CHUNK_SIZE = 3200  # 100ms of 16kHz 16bit mono audio


def get_credentials(args):
    """获取认证凭证"""
    app_id = args.app_id or os.getenv("VOLC_ASR_APPID")
    token = args.token or os.getenv("VOLC_ASR_TOKEN")
    resource_id = args.resource_id or os.getenv("VOLC_ASR_RESOURCE_ID", DEFAULT_RESOURCE_ID)

    if not app_id or not token:
        raise ValueError(
            "Missing credentials. Set VOLC_ASR_APPID and VOLC_ASR_TOKEN "
            "in environment or use --app-id and --token arguments."
        )

    return app_id, token, resource_id


def convert_to_pcm(input_path: str) -> str:
    """将音频/视频文件转换为 PCM 格式"""
    # 检查 ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError("ffmpeg not found. Please install ffmpeg first.")

    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(suffix=".pcm", delete=False)
    temp_path = temp_file.name
    temp_file.close()

    # 转换命令：16kHz, 16bit, mono, PCM
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-ar", "16000",      # 采样率 16kHz
        "-ac", "1",          # 单声道
        "-f", "s16le",       # 16bit little-endian
        "-acodec", "pcm_s16le",
        temp_path
    ]

    print(f"Converting audio to PCM format...", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        os.unlink(temp_path)
        raise RuntimeError(f"ffmpeg conversion failed: {result.stderr}")

    return temp_path


def build_request_payload(language: str, enable_punc: bool, enable_itn: bool) -> dict:
    """构建初始化请求的 JSON payload"""
    return {
        "user": {"uid": "claude_code_asr"},
        "audio": {
            "format": "pcm",
            "rate": 16000,
            "bits": 16,
            "channel": 1,
            "codec": "raw",
        },
        "request": {
            "model_name": "bigmodel",
            "language": language,
            "enable_itn": enable_itn,
            "enable_punc": enable_punc,
            "result_type": "single",
            "show_utterances": True,
            "vad": {
                "vad_enable": True,
                "end_window_size": 2000,
            },
        },
    }


def build_message_header(msg_type: int = 0x10) -> bytes:
    """构建消息头"""
    # Protocol version: 1, Header size: 1 (4 bytes), Message type, Serialization: JSON
    return struct.pack(">BBBB", 0x11, 0x10, msg_type, 0x00)


def build_audio_header() -> bytes:
    """构建音频数据消息头"""
    # Audio message type: 0x20
    return struct.pack(">BBBB", 0x11, 0x20, 0x00, 0x00)


def build_end_header() -> bytes:
    """构建结束消息头"""
    # End message type: 0x02
    return struct.pack(">BBBB", 0x11, 0x20, 0x02, 0x00)


async def transcribe_audio(
    pcm_path: str,
    app_id: str,
    token: str,
    resource_id: str,
    language: str = "zh-CN",
    enable_punc: bool = True,
    enable_itn: bool = True,
) -> list:
    """
    执行音频转录

    Returns:
        list: 识别结果列表，每项包含 text, start_time, end_time
    """
    connect_id = str(uuid.uuid4())

    headers = {
        "X-Api-App-Key": app_id,
        "X-Api-Access-Key": token,
        "X-Api-Resource-Id": resource_id,
        "X-Api-Connect-Id": connect_id,
    }

    results = []

    async with websockets.connect(
        DEFAULT_SERVICE_URL,
        additional_headers=headers,
        ping_interval=20,
        ping_timeout=60,
        close_timeout=10,
    ) as ws:
        print(f"Connected to Volcengine ASR service", file=sys.stderr)

        # 发送初始化请求
        payload = build_request_payload(language, enable_punc, enable_itn)
        payload_bytes = json.dumps(payload).encode("utf-8")
        header = build_message_header()
        size = struct.pack(">I", len(payload_bytes))
        await ws.send(header + size + payload_bytes)

        # 读取音频文件并发送
        with open(pcm_path, "rb") as f:
            audio_data = f.read()

        total_chunks = len(audio_data) // CHUNK_SIZE + (1 if len(audio_data) % CHUNK_SIZE else 0)
        print(f"Sending {total_chunks} audio chunks...", file=sys.stderr)

        # 发送音频数据
        for i in range(0, len(audio_data), CHUNK_SIZE):
            chunk = audio_data[i:i + CHUNK_SIZE]
            audio_header = build_audio_header()
            chunk_size = struct.pack(">I", len(chunk))
            await ws.send(audio_header + chunk_size + chunk)

            # 每发送一些数据就尝试接收响应
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=0.01)
                result = parse_response(response)
                if result:
                    results.extend(result)
            except asyncio.TimeoutError:
                pass

        # 发送结束标记
        end_header = build_end_header()
        end_size = struct.pack(">I", 0)
        await ws.send(end_header + end_size)
        print(f"Audio sent, waiting for final results...", file=sys.stderr)

        # 接收剩余响应（长音频需要更长的超时时间）
        try:
            while True:
                response = await asyncio.wait_for(ws.recv(), timeout=30.0)
                result = parse_response(response)
                if result:
                    results.extend(result)

                # 检查是否是最终响应
                if is_final_response(response):
                    break
        except asyncio.TimeoutError:
            print(f"Timeout waiting for more responses, processing {len(results)} segments so far", file=sys.stderr)
        except websockets.exceptions.ConnectionClosed:
            print(f"Connection closed, processing {len(results)} segments", file=sys.stderr)

    return results


def parse_response(data: bytes) -> list:
    """解析服务器响应"""
    if len(data) < 8:
        return []

    # 跳过消息头，找到 JSON 数据
    try:
        json_start = data.find(b"{")
        if json_start == -1:
            return []

        json_data = json.loads(data[json_start:].decode("utf-8"))

        results = []

        # 解析 utterances
        if "result" in json_data and "utterances" in json_data["result"]:
            for utt in json_data["result"]["utterances"]:
                if utt.get("text"):
                    results.append({
                        "text": utt["text"],
                        "start_time": utt.get("start_time", 0),
                        "end_time": utt.get("end_time", 0),
                        "definite": utt.get("definite", False),
                    })

        # 也检查直接的 text 字段
        elif "result" in json_data and "text" in json_data["result"]:
            text = json_data["result"]["text"]
            if text:
                results.append({
                    "text": text,
                    "start_time": 0,
                    "end_time": 0,
                    "definite": True,
                })

        return results
    except (json.JSONDecodeError, UnicodeDecodeError):
        return []


def is_final_response(data: bytes) -> bool:
    """检查是否是最终响应"""
    if len(data) < 4:
        return False

    # 检查消息类型标志
    msg_type_flags = data[2] if len(data) > 2 else 0
    # 最终响应的标志位
    return (msg_type_flags & 0x02) != 0


def deduplicate_results(results: list) -> list:
    """
    去重并整理结果

    流式识别会产生很多中间结果，需要去重保留最终版本。
    策略：按时间范围分组，保留每组最长的文本。
    """
    if not results:
        return []

    # 按 start_time 分组，保留最长的文本
    groups = {}
    for r in results:
        start = r.get("start_time", 0)
        text = r.get("text", "")
        if start not in groups or len(text) > len(groups[start].get("text", "")):
            groups[start] = r

    # 按时间排序
    sorted_results = sorted(groups.values(), key=lambda x: x.get("start_time", 0))

    # 进一步去重：如果一个片段是另一个的前缀，移除它
    final_results = []
    for i, r in enumerate(sorted_results):
        text = r.get("text", "")
        is_prefix = False
        for j, other in enumerate(sorted_results):
            if i != j:
                other_text = other.get("text", "")
                if text and other_text.startswith(text) and len(other_text) > len(text):
                    is_prefix = True
                    break
        if not is_prefix and text:
            final_results.append(r)

    return final_results


def format_time_srt(ms: int) -> str:
    """格式化时间为 SRT 格式: HH:MM:SS,mmm"""
    td = timedelta(milliseconds=ms)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{td.microseconds // 1000:03d}"


def format_time_vtt(ms: int) -> str:
    """格式化时间为 VTT 格式: HH:MM:SS.mmm"""
    td = timedelta(milliseconds=ms)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{td.microseconds // 1000:03d}"


def output_txt(results: list) -> str:
    """输出纯文本格式"""
    deduped = deduplicate_results(results)
    texts = [r["text"] for r in deduped if r.get("text")]
    return "\n".join(texts)


def output_srt(results: list) -> str:
    """输出 SRT 字幕格式"""
    deduped = deduplicate_results(results)
    lines = []
    idx = 1
    for r in deduped:
        if r.get("text"):
            start = format_time_srt(r.get("start_time", 0))
            end = format_time_srt(r.get("end_time", 0))
            lines.append(f"{idx}")
            lines.append(f"{start} --> {end}")
            lines.append(r["text"])
            lines.append("")
            idx += 1
    return "\n".join(lines)


def output_vtt(results: list) -> str:
    """输出 VTT 字幕格式"""
    deduped = deduplicate_results(results)
    lines = ["WEBVTT", ""]
    for r in deduped:
        if r.get("text"):
            start = format_time_vtt(r.get("start_time", 0))
            end = format_time_vtt(r.get("end_time", 0))
            lines.append(f"{start} --> {end}")
            lines.append(r["text"])
            lines.append("")
    return "\n".join(lines)


def output_json(results: list) -> str:
    """输出 JSON 格式"""
    return json.dumps(results, ensure_ascii=False, indent=2)


def parse_args():
    parser = argparse.ArgumentParser(
        description="火山引擎（豆包）语音识别工具 - 音频/视频转文字"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="输入音频/视频文件路径"
    )
    parser.add_argument(
        "--output", "-o",
        help="输出文件路径（默认输出到标准输出）"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["txt", "srt", "vtt", "json"],
        default="txt",
        help="输出格式 (default: txt)"
    )
    parser.add_argument(
        "--language", "-l",
        default="zh-CN",
        help="识别语言 (default: zh-CN)"
    )
    parser.add_argument(
        "--no-punc",
        action="store_true",
        help="不添加标点符号"
    )
    parser.add_argument(
        "--no-itn",
        action="store_true",
        help="不做数字规范化（如「一百二十三」不转为「123」）"
    )
    parser.add_argument(
        "--app-id",
        help="火山引擎 APP ID（或设置 VOLC_ASR_APPID 环境变量）"
    )
    parser.add_argument(
        "--token",
        help="火山引擎 Access Token（或设置 VOLC_ASR_TOKEN 环境变量）"
    )
    parser.add_argument(
        "--resource-id",
        help=f"Resource ID (default: {DEFAULT_RESOURCE_ID})"
    )
    return parser.parse_args()


async def main_async():
    args = parse_args()

    # 检查输入文件
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # 获取凭证
    try:
        app_id, token, resource_id = get_credentials(args)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # 转换音频格式
    temp_pcm = None
    pcm_path = str(input_path)

    if input_path.suffix.lower() not in [".pcm"]:
        try:
            temp_pcm = convert_to_pcm(str(input_path))
            pcm_path = temp_pcm
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    try:
        # 执行转录
        print(f"Starting transcription...", file=sys.stderr)
        results = await transcribe_audio(
            pcm_path,
            app_id,
            token,
            resource_id,
            language=args.language,
            enable_punc=not args.no_punc,
            enable_itn=not args.no_itn,
        )

        if not results:
            print("Warning: No transcription results", file=sys.stderr)

        # 格式化输出
        formatters = {
            "txt": output_txt,
            "srt": output_srt,
            "vtt": output_vtt,
            "json": output_json,
        }
        output = formatters[args.format](results)

        # 输出结果
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"Output saved to: {args.output}", file=sys.stderr)
        else:
            print(output)

        print(f"Transcription completed. Total segments: {len(results)}", file=sys.stderr)

    finally:
        # 清理临时文件
        if temp_pcm and os.path.exists(temp_pcm):
            os.unlink(temp_pcm)


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
