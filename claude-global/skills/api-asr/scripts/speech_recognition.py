#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
火山引擎语音识别工具 - 支持实时流式和上传音频两种模式

模式说明：
- streaming: 实时流式识别，WebSocket 接口，适合短音频（<2分钟）
- upload: 上传音频识别，HTTP 异步接口，支持长音频（最长4小时）
"""

import argparse
import asyncio
import json
import os
import requests
import struct
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import timedelta
from pathlib import Path

try:
    import websockets
except ImportError:
    websockets = None

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# 加载环境变量
if load_dotenv:
    dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    load_dotenv(dotenv_path, override=False)

# ==================== 常量配置 ====================

# 实时流式识别
STREAMING_URL = "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel"
STREAMING_RESOURCE_ID = "volc.bigasr.sauc.duration"
CHUNK_SIZE = 3200  # 100ms of 16kHz 16bit mono audio

# 上传音频识别
UPLOAD_SUBMIT_URL = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/submit"
UPLOAD_QUERY_URL = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/query"
UPLOAD_RESOURCE_ID = "volc.seedasr.auc"


# ==================== 通用工具函数 ====================

def get_credentials(args):
    """获取认证凭证"""
    app_id = args.app_id or os.getenv("VOLC_ASR_APPID")
    token = args.token or os.getenv("VOLC_ASR_TOKEN")
    api_key = args.api_key or os.getenv("VOLC_ASR_API_KEY")

    # 上传模式优先使用 api_key
    if args.mode == "upload":
        if not api_key:
            raise ValueError(
                "Missing API key for upload mode. Set VOLC_ASR_API_KEY "
                "in environment or use --api-key argument."
            )
        return None, None, api_key

    # 流式模式和分段模式需要 app_id 和 token
    if args.mode in ["streaming", "segment"]:
        if not app_id or not token:
            raise ValueError(
                "Missing credentials for streaming/segment mode. Set VOLC_ASR_APPID and VOLC_ASR_TOKEN "
                "in environment or use --app-id and --token arguments."
            )
        return app_id, token, None

    # auto 模式：返回所有可用凭证
    return app_id, token, api_key


def get_audio_duration(input_path: str) -> float:
    """获取音频时长（秒）"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        input_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return float(result.stdout.strip())
    return 0


def convert_to_pcm(input_path: str) -> str:
    """将音频/视频文件转换为 PCM 格式（流式识别用）"""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError("ffmpeg not found. Please install ffmpeg first.")

    temp_file = tempfile.NamedTemporaryFile(suffix=".pcm", delete=False)
    temp_path = temp_file.name
    temp_file.close()

    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-ar", "16000", "-ac", "1",
        "-f", "s16le", "-acodec", "pcm_s16le",
        temp_path
    ]

    print(f"Converting audio to PCM format...", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        os.unlink(temp_path)
        raise RuntimeError(f"ffmpeg conversion failed: {result.stderr}")

    return temp_path


def convert_to_mp3(input_path: str) -> str:
    """将音频/视频文件转换为 MP3 格式（上传识别用）"""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError("ffmpeg not found. Please install ffmpeg first.")

    temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    temp_path = temp_file.name
    temp_file.close()

    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-ar", "16000", "-ac", "1",
        "-b:a", "64k",
        temp_path
    ]

    print(f"Converting audio to MP3 format...", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        os.unlink(temp_path)
        raise RuntimeError(f"ffmpeg conversion failed: {result.stderr}")

    return temp_path


# ==================== 实时流式识别 ====================

def build_request_payload(
    language: str,
    enable_punc: bool,
    enable_itn: bool,
    hotword_id: str = None,
    hotword_name: str = None,
) -> dict:
    """构建初始化请求的 JSON payload"""
    payload = {
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

    # 添加热词表 ID
    if hotword_id:
        payload["request"]["boosting_table_id"] = hotword_id
        print(f"Using hotword table ID: {hotword_id}", file=sys.stderr)
    # 添加热词表名称
    elif hotword_name:
        payload["request"]["boosting_table_name"] = hotword_name
        print(f"Using hotword table name: {hotword_name}", file=sys.stderr)

    return payload


def build_message_header(msg_type: int = 0x10) -> bytes:
    return struct.pack(">BBBB", 0x11, 0x10, msg_type, 0x00)


def build_audio_header() -> bytes:
    return struct.pack(">BBBB", 0x11, 0x20, 0x00, 0x00)


def build_end_header() -> bytes:
    return struct.pack(">BBBB", 0x11, 0x20, 0x02, 0x00)


async def transcribe_streaming(
    pcm_path: str,
    app_id: str,
    token: str,
    language: str = "zh-CN",
    enable_punc: bool = True,
    enable_itn: bool = True,
    hotword_id: str = None,
    hotword_name: str = None,
) -> list:
    """实时流式识别"""
    if websockets is None:
        raise RuntimeError("websockets library not installed. Run: pip install websockets")

    connect_id = str(uuid.uuid4())
    headers = {
        "X-Api-App-Key": app_id,
        "X-Api-Access-Key": token,
        "X-Api-Resource-Id": STREAMING_RESOURCE_ID,
        "X-Api-Connect-Id": connect_id,
    }

    results = []

    async with websockets.connect(
        STREAMING_URL,
        additional_headers=headers,
        ping_interval=20,
        ping_timeout=60,
        close_timeout=10,
    ) as ws:
        print(f"Connected to Volcengine ASR (streaming mode)", file=sys.stderr)

        # 发送初始化请求
        payload = build_request_payload(language, enable_punc, enable_itn, hotword_id, hotword_name)
        payload_bytes = json.dumps(payload).encode("utf-8")
        header = build_message_header()
        size = struct.pack(">I", len(payload_bytes))
        await ws.send(header + size + payload_bytes)

        # 读取并发送音频
        with open(pcm_path, "rb") as f:
            audio_data = f.read()

        total_chunks = len(audio_data) // CHUNK_SIZE + (1 if len(audio_data) % CHUNK_SIZE else 0)
        print(f"Sending {total_chunks} audio chunks...", file=sys.stderr)

        for i in range(0, len(audio_data), CHUNK_SIZE):
            chunk = audio_data[i:i + CHUNK_SIZE]
            audio_header = build_audio_header()
            chunk_size = struct.pack(">I", len(chunk))
            await ws.send(audio_header + chunk_size + chunk)

            try:
                response = await asyncio.wait_for(ws.recv(), timeout=0.01)
                result = parse_streaming_response(response)
                if result:
                    results.extend(result)
            except asyncio.TimeoutError:
                pass

        # 发送结束标记
        end_header = build_end_header()
        end_size = struct.pack(">I", 0)
        await ws.send(end_header + end_size)
        print(f"Audio sent, waiting for final results...", file=sys.stderr)

        # 接收剩余响应
        try:
            while True:
                response = await asyncio.wait_for(ws.recv(), timeout=30.0)
                result = parse_streaming_response(response)
                if result:
                    results.extend(result)
                if is_final_response(response):
                    break
        except asyncio.TimeoutError:
            print(f"Timeout, got {len(results)} segments", file=sys.stderr)
        except websockets.exceptions.ConnectionClosed:
            print(f"Connection closed, got {len(results)} segments", file=sys.stderr)

    return results


def parse_streaming_response(data: bytes) -> list:
    """解析流式响应"""
    if len(data) < 8:
        return []

    try:
        json_start = data.find(b"{")
        if json_start == -1:
            return []

        json_data = json.loads(data[json_start:].decode("utf-8"))
        results = []

        if "result" in json_data and "utterances" in json_data["result"]:
            for utt in json_data["result"]["utterances"]:
                if utt.get("text"):
                    results.append({
                        "text": utt["text"],
                        "start_time": utt.get("start_time", 0),
                        "end_time": utt.get("end_time", 0),
                        "definite": utt.get("definite", False),
                    })
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
    msg_type_flags = data[2] if len(data) > 2 else 0
    return (msg_type_flags & 0x02) != 0


# ==================== 上传音频识别 ====================

def upload_to_aliyun_oss(audio_path: str) -> str:
    """
    上传音频到阿里云 OSS

    需要环境变量：
    - ALIYUN_OSS_ACCESS_KEY_ID
    - ALIYUN_OSS_ACCESS_KEY_SECRET
    - ALIYUN_OSS_BUCKET
    - ALIYUN_OSS_REGION
    """
    import hashlib
    import hmac
    import base64
    from datetime import datetime, timezone

    access_key_id = os.getenv("ALIYUN_OSS_ACCESS_KEY_ID")
    access_key_secret = os.getenv("ALIYUN_OSS_ACCESS_KEY_SECRET")
    bucket = os.getenv("ALIYUN_OSS_BUCKET")
    region = os.getenv("ALIYUN_OSS_REGION", "oss-cn-beijing")

    if not all([access_key_id, access_key_secret, bucket]):
        raise RuntimeError("Missing Aliyun OSS credentials in environment")

    # 生成对象名称
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = os.path.splitext(audio_path)[1]
    object_name = f"speech-recognition/{timestamp}{ext}"

    # 读取文件
    with open(audio_path, 'rb') as f:
        file_content = f.read()

    content_type = "audio/mpeg" if ext == ".mp3" else "audio/wav"

    # 构建签名
    date = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
    string_to_sign = f"PUT\n\n{content_type}\n{date}\n/{bucket}/{object_name}"
    signature = base64.b64encode(
        hmac.new(
            access_key_secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha1
        ).digest()
    ).decode('utf-8')

    # 上传
    url = f"https://{bucket}.{region}.aliyuncs.com/{object_name}"
    headers = {
        "Date": date,
        "Content-Type": content_type,
        "Authorization": f"OSS {access_key_id}:{signature}",
    }

    print(f"Uploading to Aliyun OSS: {object_name}...", file=sys.stderr)
    response = requests.put(url, data=file_content, headers=headers, timeout=300)

    if response.status_code in [200, 201]:
        print(f"  Uploaded: {url}", file=sys.stderr)
        return url
    else:
        raise RuntimeError(f"OSS upload failed: {response.status_code} {response.text}")


def upload_audio_to_storage(audio_path: str) -> str:
    """
    上传音频到存储服务并获取 URL

    优先级：
    1. 阿里云 OSS（如果配置了凭证）
    2. 0x0.st（免费，无需认证）
    3. file.io（免费，单次下载）
    """
    print("Uploading audio to storage...", file=sys.stderr)

    file_size = os.path.getsize(audio_path)
    print(f"  File size: {file_size / 1024 / 1024:.1f}MB", file=sys.stderr)

    # 优先使用阿里云 OSS
    if os.getenv("ALIYUN_OSS_ACCESS_KEY_ID"):
        try:
            return upload_to_aliyun_oss(audio_path)
        except Exception as e:
            print(f"  Aliyun OSS failed: {e}", file=sys.stderr)

    if file_size > 50 * 1024 * 1024:  # 50MB 限制（对于免费服务）
        raise RuntimeError(
            f"File too large ({file_size / 1024 / 1024:.1f}MB) for free upload services. "
            "Please configure Aliyun OSS or provide --audio-url"
        )

    # 尝试 0x0.st
    try:
        print("  Trying 0x0.st...", file=sys.stderr)
        with open(audio_path, 'rb') as f:
            response = requests.post(
                "https://0x0.st",
                files={"file": f},
                timeout=120
            )
        if response.status_code == 200:
            url = response.text.strip()
            print(f"  Uploaded: {url}", file=sys.stderr)
            return url
    except Exception as e:
        print(f"  0x0.st failed: {e}", file=sys.stderr)

    # 尝试 file.io
    try:
        print("  Trying file.io...", file=sys.stderr)
        with open(audio_path, 'rb') as f:
            response = requests.post(
                "https://file.io",
                files={"file": f},
                timeout=120
            )
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                url = result.get("link")
                print(f"  Uploaded: {url}", file=sys.stderr)
                return url
    except Exception as e:
        print(f"  file.io failed: {e}", file=sys.stderr)

    raise RuntimeError(
        "Failed to upload audio. Please configure Aliyun OSS or provide --audio-url"
    )


def transcribe_upload(
    audio_path: str,
    api_key: str,
    language: str = "zh-CN",
    enable_punc: bool = True,
    enable_itn: bool = True,
    audio_url: str = None,
) -> list:
    """上传音频识别（异步模式）"""

    # 如果没有提供 URL，先上传音频
    if not audio_url:
        audio_url = upload_audio_to_storage(audio_path)

    request_id = f"claude_{int(time.time() * 1000)}"

    # 提交任务
    submit_headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "X-Api-Resource-Id": UPLOAD_RESOURCE_ID,
        "X-Api-Request-Id": request_id,
        "X-Api-Sequence": "-1",
    }

    # 根据文件扩展名确定格式
    ext = os.path.splitext(audio_path)[1].lower()
    audio_format = {
        ".mp3": "mp3",
        ".wav": "wav",
        ".m4a": "m4a",
        ".pcm": "pcm",
    }.get(ext, "mp3")

    submit_payload = {
        "user": {"uid": "claude_code"},
        "audio": {
            "url": audio_url,
            "format": audio_format,
            "codec": "raw",
            "rate": 16000,
            "bits": 16,
            "channel": 1,
        },
        "request": {
            "model_name": "bigmodel",
            "enable_itn": enable_itn,
            "enable_punc": enable_punc,
            "enable_ddc": False,
            "enable_speaker_info": False,
            "enable_channel_split": False,
            "show_utterances": True,
            "vad_segment": False,
            "sensitive_words_filter": "",
        },
    }

    print(f"Submitting transcription task: {request_id}", file=sys.stderr)

    try:
        response = requests.post(
            UPLOAD_SUBMIT_URL,
            headers=submit_headers,
            json=submit_payload,
            timeout=30
        )
        response.raise_for_status()
        submit_result = response.json()
        print(f"Submit response: {json.dumps(submit_result, ensure_ascii=False)[:500]}", file=sys.stderr)

        # 检查是否直接返回了结果（同步模式）
        if submit_result.get("result", {}).get("text"):
            print("Got immediate result from submit", file=sys.stderr)
            return parse_upload_result(submit_result)

    except requests.RequestException as e:
        raise RuntimeError(f"Failed to submit task: {e}")

    # 轮询查询结果
    query_headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "X-Api-Resource-Id": UPLOAD_RESOURCE_ID,
        "X-Api-Request-Id": request_id,
    }
    query_payload = {}

    print("Waiting for transcription to complete...", file=sys.stderr)
    max_wait = 600  # 最多等待10分钟
    start_time = time.time()

    while time.time() - start_time < max_wait:
        try:
            response = requests.post(
                UPLOAD_QUERY_URL,
                headers=query_headers,
                json=query_payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            # 调试：打印完整响应（首次）
            if time.time() - start_time < 10:
                print(f"  Response: {json.dumps(result, ensure_ascii=False)[:500]}", file=sys.stderr)

            status = result.get("resp_data", {}).get("job_status", "") or result.get("job_status", "")

            if status == "Success":
                print("Transcription completed!", file=sys.stderr)
                return parse_upload_result(result)
            elif status in ["Failed", "Error"]:
                raise RuntimeError(f"Transcription failed: {result}")
            else:
                print(f"  Status: {status}", file=sys.stderr)
                time.sleep(5)

        except requests.RequestException as e:
            print(f"Query error: {e}, retrying...", file=sys.stderr)
            time.sleep(5)

    raise TimeoutError("Transcription timeout")


def parse_upload_result(result: dict) -> list:
    """解析上传识别的结果"""
    results = []

    resp_data = result.get("resp_data", {})
    asr_result = resp_data.get("result", {})

    # 解析 utterances
    utterances = asr_result.get("utterances", [])
    for utt in utterances:
        if utt.get("text"):
            results.append({
                "text": utt["text"],
                "start_time": utt.get("start_time", 0),
                "end_time": utt.get("end_time", 0),
                "definite": True,
            })

    # 如果没有 utterances，尝试获取整体文本
    if not results:
        text = asr_result.get("text", "")
        if text:
            results.append({
                "text": text,
                "start_time": 0,
                "end_time": 0,
                "definite": True,
            })

    return results


# ==================== 分段流式识别 ====================

def split_audio(input_path: str, segment_duration: int = 90) -> list:
    """将音频分割成多个片段"""
    total_duration = get_audio_duration(input_path)
    segments = []

    num_segments = int(total_duration / segment_duration) + 1
    print(f"Splitting audio into {num_segments} segments ({segment_duration}s each)...", file=sys.stderr)

    for i in range(num_segments):
        start_sec = i * segment_duration
        if start_sec >= total_duration:
            break

        temp_file = tempfile.NamedTemporaryFile(suffix=".pcm", delete=False)
        temp_path = temp_file.name
        temp_file.close()

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_sec),
            "-t", str(segment_duration),
            "-i", input_path,
            "-ar", "16000", "-ac", "1",
            "-f", "s16le", "-acodec", "pcm_s16le",
            temp_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
            segments.append({
                "path": temp_path,
                "start_ms": start_sec * 1000,
                "index": i + 1
            })

    print(f"Created {len(segments)} segments", file=sys.stderr)
    return segments


async def transcribe_segmented(
    input_path: str,
    app_id: str,
    token: str,
    segment_duration: int = 90,
    language: str = "zh-CN",
    enable_punc: bool = True,
    enable_itn: bool = True,
    hotword_id: str = None,
    hotword_name: str = None,
) -> list:
    """分段流式识别：将长音频分割后逐段识别"""
    segments = split_audio(input_path, segment_duration)
    all_results = []

    try:
        for seg in segments:
            print(f"Processing segment {seg['index']}/{len(segments)}...", file=sys.stderr)

            try:
                results = await transcribe_streaming(
                    seg["path"],
                    app_id,
                    token,
                    language=language,
                    enable_punc=enable_punc,
                    enable_itn=enable_itn,
                    hotword_id=hotword_id,
                    hotword_name=hotword_name,
                )

                # 调整时间戳偏移
                offset_ms = seg["start_ms"]
                for r in results:
                    r["start_time"] = r.get("start_time", 0) + offset_ms
                    r["end_time"] = r.get("end_time", 0) + offset_ms

                all_results.extend(results)
                print(f"  Got {len(results)} segments", file=sys.stderr)

            except Exception as e:
                print(f"  Error: {e}", file=sys.stderr)

    finally:
        # 清理临时文件
        for seg in segments:
            if os.path.exists(seg["path"]):
                os.unlink(seg["path"])

    return all_results


# ==================== 输出格式化 ====================

def deduplicate_results(results: list) -> list:
    """去重并整理结果"""
    if not results:
        return []

    groups = {}
    for r in results:
        start = r.get("start_time", 0)
        text = r.get("text", "")
        if start not in groups or len(text) > len(groups[start].get("text", "")):
            groups[start] = r

    sorted_results = sorted(groups.values(), key=lambda x: x.get("start_time", 0))

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
    td = timedelta(milliseconds=ms)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{td.microseconds // 1000:03d}"


def format_time_vtt(ms: int) -> str:
    td = timedelta(milliseconds=ms)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{td.microseconds // 1000:03d}"


def output_txt(results: list) -> str:
    deduped = deduplicate_results(results)
    texts = [r["text"] for r in deduped if r.get("text")]
    return "\n".join(texts)


def output_srt(results: list) -> str:
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
    return json.dumps(results, ensure_ascii=False, indent=2)


# ==================== 主程序 ====================

def parse_args():
    parser = argparse.ArgumentParser(
        description="火山引擎语音识别工具 - 支持实时流式和上传音频两种模式"
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
        "--mode", "-m",
        choices=["auto", "streaming", "upload", "segment"],
        default="auto",
        help="识别模式: auto(自动选择), streaming(实时流式), upload(上传音频), segment(分段流式) (default: auto)"
    )
    parser.add_argument(
        "--segment-duration",
        type=int,
        default=90,
        help="分段模式下每段时长（秒），默认90秒"
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
        help="不做数字规范化"
    )
    parser.add_argument(
        "--audio-url",
        help="音频文件的公网 URL（上传模式可选）"
    )
    parser.add_argument(
        "--app-id",
        help="火山引擎 APP ID（流式模式）"
    )
    parser.add_argument(
        "--token",
        help="火山引擎 Access Token（流式模式）"
    )
    parser.add_argument(
        "--api-key",
        help="火山引擎 API Key（上传模式）"
    )
    parser.add_argument(
        "--hotword-id",
        help="热词表 ID（在火山引擎控制台创建）"
    )
    parser.add_argument(
        "--hotword-name",
        help="热词表名称（在火山引擎控制台创建）"
    )
    return parser.parse_args()


async def main_async():
    args = parse_args()

    # 检查输入文件
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # 自动选择模式
    if args.mode == "auto":
        duration = get_audio_duration(str(input_path))
        print(f"Audio duration: {duration:.1f}s", file=sys.stderr)

        if duration > 120:  # 超过2分钟
            if args.audio_url or os.getenv("VOLC_ASR_API_KEY"):
                args.mode = "upload"
                print("Auto-selected: upload mode (audio > 2 minutes, API key available)", file=sys.stderr)
            else:
                args.mode = "segment"
                print("Auto-selected: segment mode (audio > 2 minutes, no upload API)", file=sys.stderr)
        else:
            args.mode = "streaming"
            print("Auto-selected: streaming mode (audio <= 2 minutes)", file=sys.stderr)

    # 获取凭证
    try:
        app_id, token, api_key = get_credentials(args)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # 热词配置
    hotword_id = args.hotword_id or os.getenv("VOLC_ASR_HOTWORD_ID")
    hotword_name = args.hotword_name or os.getenv("VOLC_ASR_HOTWORD_NAME")

    # 执行转录
    temp_file = None
    results = []

    try:
        if args.mode == "streaming":
            # 流式模式：转换为 PCM
            if input_path.suffix.lower() != ".pcm":
                temp_file = convert_to_pcm(str(input_path))
                pcm_path = temp_file
            else:
                pcm_path = str(input_path)

            print(f"Starting streaming transcription...", file=sys.stderr)
            results = await transcribe_streaming(
                pcm_path,
                app_id,
                token,
                language=args.language,
                enable_punc=not args.no_punc,
                enable_itn=not args.no_itn,
                hotword_id=hotword_id,
                hotword_name=hotword_name,
            )

        elif args.mode == "segment":
            # 分段模式：分割音频后逐段流式识别
            print(f"Starting segmented transcription...", file=sys.stderr)
            results = await transcribe_segmented(
                str(input_path),
                app_id,
                token,
                segment_duration=args.segment_duration,
                language=args.language,
                enable_punc=not args.no_punc,
                enable_itn=not args.no_itn,
                hotword_id=hotword_id,
                hotword_name=hotword_name,
            )

        else:  # upload 模式
            # 上传模式：转换为 MP3（如果需要）
            if input_path.suffix.lower() not in [".mp3", ".wav"]:
                temp_file = convert_to_mp3(str(input_path))
                audio_path = temp_file
            else:
                audio_path = str(input_path)

            print(f"Starting upload transcription...", file=sys.stderr)
            results = transcribe_upload(
                audio_path,
                api_key,
                language=args.language,
                enable_punc=not args.no_punc,
                enable_itn=not args.no_itn,
                audio_url=args.audio_url,
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
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
