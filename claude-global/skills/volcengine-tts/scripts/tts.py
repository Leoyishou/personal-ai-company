#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command-line tool for Volcengine TTS (Text-to-Speech).

Usage:
    python tts.py "要转换的文字"
    python tts.py "Hello world" --voice en_female_amanda_moon_bigtts
    python tts.py "测试语速" --speed 1.5 --output fast.mp3
    echo "从标准输入读取" | python tts.py
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 计算项目根目录和默认输出目录
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent  # .claude/skills/volcengine-tts/scripts -> project root
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output" / "volcengine-tts"

from tts_client import synthesize, get_voice_id, VOICES, DEFAULT_VOICE


def main():
    parser = argparse.ArgumentParser(
        description="Volcengine TTS - Text to Speech",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tts.py "你好，世界"
  python tts.py "Hello" --voice amanda --output hello.mp3
  python tts.py "快速播放" --speed 1.5
  echo "从管道输入" | python tts.py

Available voice presets:
  female   - 通用女声 (BV001_streaming)
  male     - 通用男声 (BV002_streaming)
  yangguang- 阳光男声 (BV056_streaming)
  wenrou   - 温柔小哥 (BV033_streaming)
  ruya     - 儒雅青年 (BV102_streaming)
  jackson  - 活力男声 (BV504_streaming, 需开通)

Or use full voice ID like: BV102_streaming
        """
    )

    parser.add_argument(
        "text",
        nargs="?",
        help="Text to synthesize (reads from stdin if not provided)"
    )
    parser.add_argument(
        "--voice", "-v",
        default=DEFAULT_VOICE,
        help=f"Voice type/preset (default: {DEFAULT_VOICE})"
    )
    parser.add_argument(
        "--speed", "-s",
        type=float,
        default=1.0,
        help="Speed ratio 0.5-2.0 (default: 1.0)"
    )
    parser.add_argument(
        "--volume",
        type=float,
        default=1.0,
        help="Volume ratio 0.5-2.0 (default: 1.0)"
    )
    parser.add_argument(
        "--pitch",
        type=float,
        default=1.0,
        help="Pitch ratio 0.5-2.0 (default: 1.0)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["mp3", "wav", "pcm"],
        default="mp3",
        help="Output format (default: mp3)"
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=24000,
        help="Sample rate in Hz (default: 24000)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: tts_[timestamp].[format])"
    )
    parser.add_argument(
        "--save-dir",
        default=None,
        help=f"Directory to save output file (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="List available voice presets"
    )
    parser.add_argument(
        "--print-path-only",
        action="store_true",
        help="Only print the output file path, no other messages"
    )

    args = parser.parse_args()

    # List voices and exit
    if args.list_voices:
        print("Available voice presets:\n")
        voice_info = {
            "female": "通用女声",
            "male": "通用男声",
            "yangguang": "阳光男声",
            "wenrou": "温柔小哥",
            "ruya": "儒雅青年",
            "jackson": "活力男声 (需开通)",
        }
        for name, vid in VOICES.items():
            if name in voice_info:
                print(f"  {name:10} {vid:20} {voice_info[name]}")
        return 0

    # Get text from argument or stdin
    text = args.text
    if not text:
        if not sys.stdin.isatty():
            text = sys.stdin.read().strip()
        else:
            print("Error: No text provided. Use --help for usage.", file=sys.stderr)
            return 1

    if not text:
        print("Error: Empty text provided.", file=sys.stderr)
        return 1

    # Resolve voice ID
    voice_id = get_voice_id(args.voice)

    # Generate output filename if not specified
    if args.output:
        output_path = args.output
    else:
        save_dir = args.save_dir if args.save_dir else str(DEFAULT_OUTPUT_DIR)
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tts_{timestamp}.{args.format}"
        output_path = os.path.join(save_dir, filename)

    # Ensure save directory exists
    save_dir = os.path.dirname(output_path) or "."
    os.makedirs(save_dir, exist_ok=True)

    if not args.print_path_only:
        print(f"Synthesizing text: {text[:50]}{'...' if len(text) > 50 else ''}")
        print(f"Voice: {voice_id}")
        print(f"Speed: {args.speed}, Volume: {args.volume}, Pitch: {args.pitch}")
        print(f"Format: {args.format}, Sample Rate: {args.sample_rate}Hz")
        print("Generating audio...")

    try:
        audio_data = synthesize(
            text=text,
            voice=voice_id,
            speed=args.speed,
            volume=args.volume,
            pitch=args.pitch,
            audio_format=args.format,
            sample_rate=args.sample_rate,
        )

        # Save to file
        with open(output_path, "wb") as f:
            f.write(audio_data)

        output_abs_path = os.path.abspath(output_path)

        if args.print_path_only:
            print(output_abs_path)
        else:
            print(f"\nAudio saved to: {output_abs_path}")
            print(f"File size: {len(audio_data):,} bytes")

        return 0

    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"TTS error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
