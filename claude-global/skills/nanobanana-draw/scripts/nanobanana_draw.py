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
from pathlib import Path

from nanobanana_client import DEFAULT_NANOBANANA_MODEL, generate_image

# 计算项目根目录和默认输出目录
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent  # .claude/skills/nanobanana-draw/scripts -> project root
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output" / "nanobanana-draw"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate images using Nanobanana via OpenRouter API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic text prompt
  python nanobanana_draw.py "画一只可爱的橘猫"

  # With reference images (for style transfer or IP generation)
  python nanobanana_draw.py "将这个人物转换成3D卡通风格" --image photo.jpg --style-image cartoon_style.png

  # With single image reference
  python nanobanana_draw.py "根据这张照片生成卡通IP形象" --image my_photo.jpg
"""
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
    parser.add_argument("--save-dir", help=f"Directory to save generated images (defaults to {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--no-save", action="store_true", help="Do not save images automatically")
    # New: Reference image support
    parser.add_argument("--image", "-i", action="append", dest="images",
                        help="Reference image path or URL (can be used multiple times)")
    parser.add_argument("--style-image", "-s", help="Style reference image path or URL")
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


def save_images_from_response(raw_json, output_dir=None):
    """
    Extract and save images from API response.

    Args:
        raw_json: The raw JSON response from the API
        output_dir: Directory to save images (defaults to current working directory)

    Returns:
        list: List of saved file paths
    """
    if output_dir is None:
        output_dir = os.getcwd()

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
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"nanobanana_{timestamp}_{i}.{ext}"
                filepath = os.path.join(output_dir, filename)

                img_bytes = base64.b64decode(b64_data)
                with open(filepath, "wb") as f:
                    f.write(img_bytes)
                saved_files.append(filepath)

    return saved_files


def main():
    args = parse_args()
    prompt = read_prompt(args)

    if not prompt:
        raise ValueError("Prompt cannot be empty")

    # Collect reference images
    reference_images = []
    if args.images:
        reference_images.extend(args.images)
    if args.style_image:
        reference_images.append(args.style_image)

    content, raw = generate_image(
        prompt=prompt,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        system_prompt=args.system,
        reference_images=reference_images if reference_images else None,
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as file:
            json.dump(raw, file, ensure_ascii=False, indent=2)

    # Auto-save images unless --no-save is specified
    if not args.no_save:
        save_dir = args.save_dir if args.save_dir else str(DEFAULT_OUTPUT_DIR)
        os.makedirs(save_dir, exist_ok=True)
        saved_files = save_images_from_response(raw, save_dir)
        if saved_files:
            for filepath in saved_files:
                print(f"Image saved: {filepath}")
        else:
            print("No images found in response")

    if args.print_json:
        print(json.dumps(raw, ensure_ascii=False, indent=2))
    elif content:
        print(content)


if __name__ == "__main__":
    main()
