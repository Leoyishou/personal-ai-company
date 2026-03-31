#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Volcengine TTS (Text-to-Speech) client via HTTP API.

Based on: https://www.volcengine.com/docs/6561/79820
"""

import os
import json
import uuid
import base64
from typing import Optional

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    # Try skill directory first
    dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    load_dotenv(dotenv_path, override=False)
    # Also try project root
    project_root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".env"))
    if os.path.exists(project_root_env):
        load_dotenv(project_root_env, override=False)

try:
    import requests
except ImportError:
    raise ImportError(
        "Please install requests: pip install requests"
    )


# API endpoint
TTS_HTTP_URL = "https://openspeech.bytedance.com/api/v1/tts"

# Default voice (BV001_streaming for standard TTS service)
DEFAULT_VOICE = os.getenv("VOLC_TTS_VOICE", "BV001_streaming")

# Default cluster
DEFAULT_CLUSTER = os.getenv("VOLC_TTS_CLUSTER", "volcano_tts")


def resolve_credentials(app_id: Optional[str] = None, access_token: Optional[str] = None):
    """Resolve credentials from arguments or environment."""
    aid = app_id or os.getenv("VOLC_TTS_APPID")
    token = access_token or os.getenv("VOLC_TTS_ACCESS_TOKEN")

    if not aid:
        raise ValueError(
            "Missing VOLC_TTS_APPID. Set it via environment variable or pass app_id parameter.\n"
            "Get your credentials from: https://console.volcengine.com/speech/app"
        )
    if not token:
        raise ValueError(
            "Missing VOLC_TTS_ACCESS_TOKEN. Set it via environment variable or pass access_token parameter.\n"
            "Get your credentials from: https://console.volcengine.com/speech/app"
        )

    return aid, token


def synthesize(
    text: str,
    voice: str = DEFAULT_VOICE,
    speed: float = 1.0,
    volume: float = 1.0,
    pitch: float = 1.0,
    audio_format: str = "mp3",
    sample_rate: int = 24000,
    app_id: Optional[str] = None,
    access_token: Optional[str] = None,
    cluster: Optional[str] = None,
) -> bytes:
    """
    Synthesize text to speech audio via HTTP API.

    Args:
        text: Text to synthesize
        voice: Voice type ID
        speed: Speed ratio (0.5-2.0)
        volume: Volume ratio (0.5-2.0)
        pitch: Pitch ratio (0.5-2.0)
        audio_format: Output format (mp3/wav/pcm/ogg_opus)
        sample_rate: Audio sample rate (8000/16000/24000)
        app_id: Volcengine App ID
        access_token: Volcengine Access Token
        cluster: TTS cluster name (auto-detected if None)

    Returns:
        bytes: Audio data
    """
    aid, token = resolve_credentials(app_id, access_token)

    # Auto-detect cluster based on voice ID if not specified
    if cluster is None:
        cluster = get_cluster_for_voice(voice)

    # Build request payload
    # Reference: https://www.volcengine.com/docs/6561/79823
    payload = {
        "app": {
            "appid": aid,
            "token": "access_token",  # placeholder, real token in header
            "cluster": cluster
        },
        "user": {
            "uid": "claude_code_user"
        },
        "audio": {
            "voice_type": voice,
            "encoding": audio_format,
            "speed_ratio": speed,
            "volume_ratio": volume,
            "pitch_ratio": pitch,
            "sample_rate": sample_rate
        },
        "request": {
            "reqid": str(uuid.uuid4()),
            "text": text,
            "text_type": "plain",
            "operation": "query",
            "with_frontend": 1,
            "frontend_type": "unitTson"
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer;{token}"
    }

    try:
        response = requests.post(
            TTS_HTTP_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
        response.raise_for_status()

        result = response.json()

        # Check for errors
        if result.get("code") != 3000:
            error_msg = result.get("message", "Unknown error")
            error_code = result.get("code", "Unknown")
            raise RuntimeError(f"TTS API error ({error_code}): {error_msg}")

        # Extract audio data (base64 encoded)
        audio_base64 = result.get("data")
        if not audio_base64:
            raise RuntimeError("No audio data in response")

        # Decode base64 to binary
        audio_data = base64.b64decode(audio_base64)
        return audio_data

    except requests.exceptions.Timeout:
        raise RuntimeError("TTS request timed out")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"TTS request failed: {e}")


def synthesize_long_text(
    text: str,
    voice: str = DEFAULT_VOICE,
    speed: float = 1.0,
    volume: float = 1.0,
    pitch: float = 1.0,
    audio_format: str = "mp3",
    sample_rate: int = 24000,
    app_id: Optional[str] = None,
    access_token: Optional[str] = None,
    cluster: Optional[str] = None,
    max_chunk_size: int = 500,
) -> bytes:
    """
    Synthesize long text by splitting into chunks.

    Args:
        text: Text to synthesize (can be long)
        max_chunk_size: Maximum characters per chunk
        ... (other args same as synthesize)

    Returns:
        bytes: Combined audio data
    """
    # Split text into chunks
    chunks = []
    current_chunk = ""

    # Split by sentences (Chinese and English punctuation)
    import re
    sentences = re.split(r'([。！？.!?\n])', text)

    for i in range(0, len(sentences), 2):
        sentence = sentences[i]
        # Add punctuation back if exists
        if i + 1 < len(sentences):
            sentence += sentences[i + 1]

        if len(current_chunk) + len(sentence) > max_chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sentence
        else:
            current_chunk += sentence

    if current_chunk:
        chunks.append(current_chunk)

    # If no chunks created, use original text
    if not chunks:
        chunks = [text]

    # Synthesize each chunk
    audio_parts = []
    for chunk in chunks:
        if chunk.strip():
            audio_data = synthesize(
                text=chunk,
                voice=voice,
                speed=speed,
                volume=volume,
                pitch=pitch,
                audio_format=audio_format,
                sample_rate=sample_rate,
                app_id=app_id,
                access_token=access_token,
                cluster=cluster,
            )
            audio_parts.append(audio_data)

    # Combine audio parts
    return b''.join(audio_parts)


# Voice presets for easy access
VOICES = {
    # Standard streaming voices (通用版)
    "female": "BV001_streaming",      # 通用女声
    "male": "BV002_streaming",        # 通用男声
    "yangguang": "BV056_streaming",   # 阳光男声
    "wenrou": "BV033_streaming",      # 温柔小哥
    "ruya": "BV102_streaming",        # 儒雅青年
    "jackson": "BV504_streaming",     # 活力男声-Jackson (需开通)
    "bv001": "BV001_streaming",
    "bv002": "BV002_streaming",
    "bv056": "BV056_streaming",
    "bv033": "BV033_streaming",
    "bv102": "BV102_streaming",
    "bv504": "BV504_streaming",
}


def get_voice_id(voice_name: str) -> str:
    """Get full voice ID from preset name or return as-is."""
    return VOICES.get(voice_name.lower(), voice_name)


# 精品音色/音色定制 ID 列表 (使用 volcano_icl 集群)
# 添加定制音色时在这里添加
ICL_VOICE_IDS = set()


def get_cluster_for_voice(voice_id: str) -> str:
    """根据音色ID自动选择正确的集群."""
    # 精品音色使用 volcano_icl 集群
    if voice_id in ICL_VOICE_IDS:
        return "volcano_icl"
    # 检查是否有下划线分隔的长ID格式 (如 BV102_xxx_xxx)
    parts = voice_id.split("_")
    if len(parts) >= 3 and parts[0].startswith("BV"):
        return "volcano_icl"
    # 默认使用 volcano_tts
    return DEFAULT_CLUSTER


def list_voices() -> dict:
    """Return all available voice presets."""
    return VOICES.copy()
