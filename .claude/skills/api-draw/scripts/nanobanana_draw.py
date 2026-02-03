#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nanobanana image generation command-line tool.
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime

from nanobanana_client import DEFAULT_NANOBANANA_MODEL, generate_image


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate images using Nanobanana via OpenRouter API."
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Image generation prompt (or read from stdin)",
    )
    parser.add_argument("--system", help="System prompt (optional)")
    parser.add_argument("--model", default=DEFAULT_NANOBANANA_MODEL, help="Model ID")
    parser.add_argument("--temperature", type=float, default=0.7, help="Sampling temperature")
    parser.add_argument("--max-tokens", type=int, help="Max tokens for response")
    parser.add_argument("--print-json", action="store_true", help="Print full JSON response")
    parser.add_argument("--output", help="Save full JSON response to file")
    parser.add_argument("--save-dir", help="Directory to save generated images (defaults to current working directory)")
    parser.add_argument("--no-save", action="store_true", help="Do not save images automatically")
    parser.add_argument("--image", "-i", help="Reference image path for style transfer")
    parser.add_argument("--style", default="其他", help="Style name for filename (e.g. 手绘白板, 板书插画, 对比漫画, 学霸笔记, 线刻肖像, 其他)")
    parser.add_argument("--subject", default="未命名", help="Subject/topic for filename (concise, 2-8 chars)")
    parser.add_argument("--size", help="Target image size (e.g. 1080x1440, 972x806). Adds size hint to prompt.")
    parser.add_argument("--stats", action="store_true", help="Show usage statistics and exit")
    return parser.parse_args()


def read_prompt(args):
    """Read prompt from command line or stdin."""
    if args.prompt:
        return args.prompt
    elif not sys.stdin.isatty():
        return sys.stdin.read().strip()
    else:
        raise ValueError(
            "Please provide a prompt as an argument or via stdin.\n"
            "Example: python nanobanana_draw.py '画一只可爱的猫'"
        )


STATS_FILE = os.path.expanduser("~/.claude/Nanobanana-draw-图片/stats.json")


def load_stats():
    """Load statistics from file."""
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"total": 0, "by_style": {}}


def save_stats(stats):
    """Save statistics to file."""
    os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def record_usage(style):
    """Record a style usage."""
    stats = load_stats()
    stats["total"] = stats.get("total", 0) + 1
    if "by_style" not in stats:
        stats["by_style"] = {}
    stats["by_style"][style] = stats["by_style"].get(style, 0) + 1
    save_stats(stats)


def print_stats():
    """Print usage statistics."""
    stats = load_stats()
    total = stats.get("total", 0)
    by_style = stats.get("by_style", {})

    print(f"\n{'='*40}")
    print(f"Nanobanana 使用统计 (共 {total} 次)")
    print(f"{'='*40}")

    if by_style:
        # Sort by count descending
        sorted_styles = sorted(by_style.items(), key=lambda x: x[1], reverse=True)
        for style, count in sorted_styles:
            pct = (count / total * 100) if total > 0 else 0
            bar = "█" * int(pct / 5)  # 20 chars max
            print(f"{style:12} {count:4}次 ({pct:5.1f}%) {bar}")
    else:
        print("暂无使用记录")
    print(f"{'='*40}\n")


def save_images_from_response(raw_json, output_dir=None, style="其他", subject="未命名"):
    """
    Extract and save images from API response.

    Args:
        raw_json: The raw JSON response from the API
        output_dir: Directory to save images (defaults to current working directory)
        style: Style name for filename
        subject: Subject/topic for filename

    Returns:
        list: List of saved file paths
    """
    if output_dir is None:
        output_dir = os.path.expanduser("~/.claude/Nanobanana-draw-图片")

    saved_files = []
    choices = raw_json.get("choices", [])

    for choice in choices:
        message = choice.get("message", {})
        images = message.get("images", [])

        for i, img in enumerate(images):
            b64_data = None
            mime_type = "image/png"

            if isinstance(img, dict):
                # Handle format: {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
                image_url = img.get("image_url", {})
                if isinstance(image_url, dict):
                    url = image_url.get("url", "")
                    if url.startswith("data:"):
                        # Parse data URL: data:image/png;base64,xxxxx
                        try:
                            header, b64_data = url.split(",", 1)
                            if "png" in header:
                                mime_type = "image/png"
                            elif "jpeg" in header or "jpg" in header:
                                mime_type = "image/jpeg"
                        except ValueError:
                            pass
                # Also try direct base64 or data fields
                if not b64_data:
                    b64_data = img.get("base64") or img.get("data")
                    mime_type = img.get("mime_type", "image/png")
            elif isinstance(img, str):
                if img.startswith("data:"):
                    try:
                        header, b64_data = img.split(",", 1)
                        if "png" in header:
                            mime_type = "image/png"
                        elif "jpeg" in header or "jpg" in header:
                            mime_type = "image/jpeg"
                    except ValueError:
                        pass
                else:
                    b64_data = img

            if b64_data:
                ext = "png" if "png" in mime_type else "jpg"
                date_str = datetime.now().strftime("%Y%m%d")
                filename = f"{date_str}_{style}_{subject}_{i}.{ext}"
                filepath = os.path.join(output_dir, filename)

                img_bytes = base64.b64decode(b64_data)
                with open(filepath, "wb") as f:
                    f.write(img_bytes)
                saved_files.append(filepath)

    return saved_files


def add_size_hint(prompt: str, size: str) -> str:
    """Add size hint to prompt if specified."""
    if not size:
        return prompt
    try:
        w, h = map(int, size.lower().split("x"))
        from math import gcd
        g = gcd(w, h)
        ratio = f"{w//g}:{h//g}"
        size_hint = f"\n\n图片尺寸要求：{w}×{h}像素，{ratio}比例。"
        return prompt + size_hint
    except ValueError:
        print(f"Warning: Invalid size format '{size}', ignoring. Use format like '1080x1440'")
        return prompt


def main():
    args = parse_args()

    # Handle --stats flag
    if args.stats:
        print_stats()
        return

    prompt = read_prompt(args)

    if not prompt:
        raise ValueError("Prompt cannot be empty")

    # Add size hint to prompt if specified
    prompt = add_size_hint(prompt, args.size)

    content, raw = generate_image(
        prompt=prompt,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        system_prompt=args.system,
        reference_image=args.image,
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as file:
            json.dump(raw, file, ensure_ascii=False, indent=2)

    # Auto-save images unless --no-save is specified
    if not args.no_save:
        save_dir = args.save_dir  # None means use current working directory
        saved_files = save_images_from_response(raw, save_dir, style=args.style, subject=args.subject)
        if saved_files:
            for filepath in saved_files:
                print(f"Image saved: {filepath}")
            # Record usage statistics
            record_usage(args.style)
        else:
            print("No images found in response")

    if args.print_json:
        print(json.dumps(raw, ensure_ascii=False, indent=2))
    elif content:
        print(content)


if __name__ == "__main__":
    main()
