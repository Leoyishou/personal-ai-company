#!/usr/bin/env python3
"""
火山引擎（豆包）语音合成 TTS 工具
使用 HTTP 非流式接口，一次性合成并返回音频文件
"""

import argparse
import base64
import json
import os
import sys
import uuid
from pathlib import Path

import requests

# 默认配置
DEFAULT_VOICE = "BV001_streaming"
DEFAULT_ENCODING = "mp3"
DEFAULT_CLUSTER = "volcano_tts"
DEFAULT_SPEED = 1.0
DEFAULT_SAMPLE_RATE = 24000

# 常用音色列表
# ★ = 已购买实例（到期 2027-01-23）
VOICE_LIST = {
    # 已购买实例
    "yangyang": "BV705_streaming",      # ★ 炀炀
    "mengwa": "BV051_streaming",        # ★ 奶气萌娃
    "huopo": "BV005_streaming",         # ★ 活泼女声（视频配音）
    # 免费音色
    "female": "BV001_streaming",        # 通用女声
    "male": "BV002_streaming",          # 通用男声
}

TTS_API_URL = "https://openspeech.bytedance.com/api/v1/tts"


def load_config():
    """从环境变量或 .env 文件加载配置"""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())

    appid = os.environ.get("VOLC_TTS_APPID", "")
    token = os.environ.get("VOLC_TTS_TOKEN", "")
    return appid, token


def synthesize(text, voice_type=None, encoding=None, speed=None,
               output_path=None, appid=None, token=None, sample_rate=None):
    """
    调用火山引擎 TTS HTTP 接口合成语音

    Args:
        text: 待合成文本（最大1024字节/约300字符）
        voice_type: 音色ID
        encoding: 音频格式 (mp3/wav/pcm/ogg_opus)
        speed: 语速 [0.1, 2.0]
        output_path: 输出文件路径
        appid: 应用ID
        token: Access Token
        sample_rate: 采样率 (8000/16000/24000)

    Returns:
        输出文件路径
    """
    if not appid or not token:
        cfg_appid, cfg_token = load_config()
        appid = appid or cfg_appid
        token = token or cfg_token

    if not appid or not token:
        print("错误: 缺少 VOLC_TTS_APPID 或 VOLC_TTS_TOKEN")
        print("请在 ~/.claude/skills/volc-tts/.env 中配置:")
        print("  VOLC_TTS_APPID=你的appid")
        print("  VOLC_TTS_TOKEN=你的token")
        print("\n获取方式: https://console.volcengine.com/speech/service/8")
        sys.exit(1)

    voice_type = voice_type or DEFAULT_VOICE
    encoding = encoding or DEFAULT_ENCODING
    speed = speed or DEFAULT_SPEED
    sample_rate = sample_rate or DEFAULT_SAMPLE_RATE

    # 如果传入的是音色别名，转换为完整ID
    if voice_type in VOICE_LIST:
        voice_type = VOICE_LIST[voice_type]

    # 生成输出文件名
    if not output_path:
        output_dir = Path(__file__).parent.parent / "output"
        output_dir.mkdir(exist_ok=True)
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"tts_{timestamp}.{encoding}"

    reqid = str(uuid.uuid4())

    payload = {
        "app": {
            "appid": appid,
            "token": "fake_token",  # 文档说明此字段无实际鉴权作用
            "cluster": DEFAULT_CLUSTER,
        },
        "user": {
            "uid": "claude_code_user",
        },
        "audio": {
            "voice_type": voice_type,
            "encoding": encoding,
            "speed_ratio": speed,
            "rate": sample_rate,
        },
        "request": {
            "reqid": reqid,
            "text": text,
            "operation": "query",
        },
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer;{token}",
    }

    try:
        resp = requests.post(TTS_API_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        result = resp.json()

        if result.get("code") != 3000:
            print(f"合成失败: code={result.get('code')}, message={result.get('message')}")
            sys.exit(1)

        # 解码音频数据
        audio_data = base64.b64decode(result["data"])
        output_path = Path(output_path)
        output_path.write_bytes(audio_data)

        duration_ms = result.get("addition", {}).get("duration", "未知")
        print(f"合成成功!")
        print(f"  文件: {output_path}")
        print(f"  时长: {duration_ms}ms")
        print(f"  音色: {voice_type}")
        print(f"  格式: {encoding} / {sample_rate}Hz")
        return str(output_path)

    except requests.exceptions.RequestException as e:
        print(f"网络请求失败: {e}")
        sys.exit(1)


def list_voices():
    """列出可用音色"""
    print("常用音色列表:")
    print(f"{'别名':<15} {'完整ID'}")
    print("-" * 60)
    for alias, vid in VOICE_LIST.items():
        print(f"  {alias:<13} {vid}")
    print("\n更多音色: https://www.volcengine.com/docs/6561/1257544")


def main():
    parser = argparse.ArgumentParser(description="火山引擎 TTS 语音合成")
    parser.add_argument("text", nargs="?", help="待合成文本（也可从 stdin 读取）")
    parser.add_argument("--voice", "-v", default=DEFAULT_VOICE, help="音色ID或别名")
    parser.add_argument("--encoding", "-e", default=DEFAULT_ENCODING,
                        choices=["mp3", "wav", "pcm", "ogg_opus"], help="音频格式")
    parser.add_argument("--speed", "-s", type=float, default=DEFAULT_SPEED,
                        help="语速 [0.1, 2.0]")
    parser.add_argument("--rate", "-r", type=int, default=DEFAULT_SAMPLE_RATE,
                        choices=[8000, 16000, 24000], help="采样率")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--appid", help="App ID (优先于环境变量)")
    parser.add_argument("--token", help="Access Token (优先于环境变量)")
    parser.add_argument("--list-voices", action="store_true", help="列出可用音色")

    args = parser.parse_args()

    if args.list_voices:
        list_voices()
        return

    # 获取文本
    text = args.text
    if not text:
        if not sys.stdin.isatty():
            text = sys.stdin.read().strip()
        else:
            print("错误: 请提供待合成文本")
            parser.print_help()
            sys.exit(1)

    if not text:
        print("错误: 文本不能为空")
        sys.exit(1)

    # 文本长度检查
    if len(text.encode("utf-8")) > 1024:
        print(f"警告: 文本长度 {len(text.encode('utf-8'))} 字节，超过1024字节限制")
        print("建议分段合成")
        sys.exit(1)

    synthesize(
        text=text,
        voice_type=args.voice,
        encoding=args.encoding,
        speed=args.speed,
        output_path=args.output,
        appid=args.appid,
        token=args.token,
        sample_rate=args.rate,
    )


if __name__ == "__main__":
    main()
