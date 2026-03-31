#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate IP character from reference image using Nanobanana via OpenRouter API.
根据参考图片生成IP人物形象。
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
from datetime import datetime

import requests

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    load_dotenv(dotenv_path, override=False)


DEFAULT_NANOBANANA_MODEL = os.getenv("NANOBANANA_MODEL", "google/gemini-3-pro-image-preview")
DEFAULT_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# 预设的IP人物风格
IP_STYLES = {
    "chibi": "可爱的Q版/赤壁风格,大头小身体,2-3头身比例,圆润可爱的造型",
    "cartoon": "卡通风格,简洁的线条,鲜艳的色彩,适合作为品牌吉祥物",
    "anime": "日系动漫风格,精致的细节,大眼睛,飘逸的发型",
    "mascot": "吉祥物风格,友好亲切,适合商业IP使用,简洁易识别",
    "3d": "3D渲染风格,立体感强,类似皮克斯/迪士尼的质感",
    "flat": "扁平化设计风格,简约现代,适合UI/品牌设计",
    "pixel": "像素艺术风格,复古游戏感,适合游戏IP",
    "watercolor": "水彩手绘风格,柔和的色彩过渡,艺术感强",
}

DEFAULT_IP_PROMPT = """请根据提供的参考图片,创作一个独特的IP人物形象。

要求:
1. 保留原图人物/主体的核心特征和气质
2. 转化为具有辨识度的IP角色设计
3. 造型简洁,易于在不同场景中应用
4. 表情生动有趣,具有亲和力
5. 色彩搭配和谐,视觉效果突出

请生成这个IP人物形象的正面全身图。"""


def encode_image_to_base64(image_path):
    """Read and encode image file to base64."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_mime_type(image_path):
    """Get MIME type from file path."""
    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type and mime_type.startswith("image/"):
        return mime_type
    # Default to jpeg for unknown types
    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    return mime_map.get(ext, "image/jpeg")


def build_headers(api_key):
    """Build OpenRouter request headers."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    site_url = os.getenv("OPENROUTER_SITE_URL")
    app_name = os.getenv("OPENROUTER_APP_NAME", "nanobanana-ip-character")
    if site_url:
        headers["HTTP-Referer"] = site_url
    if app_name:
        headers["X-Title"] = app_name
    return headers


def generate_ip_character(
    image_path,
    prompt=None,
    style=None,
    model=None,
    api_key=None,
    temperature=0.7,
    max_tokens=None,
    timeout=120,
):
    """
    Generate IP character from reference image.

    Args:
        image_path: Path to reference image
        prompt: Custom prompt (optional)
        style: IP style preset name (optional)
        model: Model ID
        api_key: OpenRouter API key
        temperature: Sampling temperature
        max_tokens: Max tokens for response
        timeout: Request timeout

    Returns:
        tuple: (content, raw_json)
    """
    api_key = api_key or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENROUTER_API_KEY")

    # Build the prompt
    if prompt:
        final_prompt = prompt
    else:
        final_prompt = DEFAULT_IP_PROMPT
        if style and style in IP_STYLES:
            final_prompt = f"风格要求: {IP_STYLES[style]}\n\n{final_prompt}"

    # Encode image
    image_base64 = encode_image_to_base64(image_path)
    mime_type = get_mime_type(image_path)
    image_url = f"data:{mime_type};base64,{image_base64}"

    # Build multimodal message
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": final_prompt},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        }
    ]

    payload = {
        "model": model or DEFAULT_NANOBANANA_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    base_url = os.getenv("OPENROUTER_BASE_URL", DEFAULT_OPENROUTER_URL)

    response = requests.post(
        base_url,
        json=payload,
        headers=build_headers(api_key),
        timeout=timeout,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"OpenRouter request failed ({response.status_code}): {response.text}"
        )

    data = response.json()
    choices = data.get("choices")
    if not choices:
        raise RuntimeError(f"OpenRouter response missing choices: {data}")

    return choices[0]["message"]["content"], data


def save_images_from_response(raw_json, output_dir=None, prefix="ip_character"):
    """Extract and save images from API response."""
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
                image_url = img.get("image_url", {})
                if isinstance(image_url, dict):
                    url = image_url.get("url", "")
                    if url.startswith("data:"):
                        try:
                            header, b64_data = url.split(",", 1)
                            if "png" in header:
                                mime_type = "image/png"
                            elif "jpeg" in header or "jpg" in header:
                                mime_type = "image/jpeg"
                        except ValueError:
                            pass
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
                filename = f"{prefix}_{timestamp}_{i}.{ext}"
                filepath = os.path.join(output_dir, filename)

                img_bytes = base64.b64decode(b64_data)
                with open(filepath, "wb") as f:
                    f.write(img_bytes)
                saved_files.append(filepath)

    return saved_files


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate IP character from reference image using Nanobanana.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available styles:
{chr(10).join(f'  {k:12} - {v}' for k, v in IP_STYLES.items())}

Examples:
  python nanobanana_ip_character.py photo.jpg
  python nanobanana_ip_character.py photo.jpg --style chibi
  python nanobanana_ip_character.py photo.jpg --style anime --prompt "生成一个手持魔法棒的角色"
""",
    )
    parser.add_argument("image", help="Path to reference image")
    parser.add_argument("--prompt", help="Custom prompt for IP character generation")
    parser.add_argument(
        "--style",
        choices=list(IP_STYLES.keys()),
        help="IP character style preset",
    )
    parser.add_argument("--model", default=DEFAULT_NANOBANANA_MODEL, help="Model ID")
    parser.add_argument("--temperature", type=float, default=0.7, help="Sampling temperature")
    parser.add_argument("--max-tokens", type=int, help="Max tokens for response")
    parser.add_argument("--print-json", action="store_true", help="Print full JSON response")
    parser.add_argument("--output", help="Save full JSON response to file")
    parser.add_argument("--save-dir", help="Directory to save generated images")
    parser.add_argument("--no-save", action="store_true", help="Do not save images automatically")
    parser.add_argument("--list-styles", action="store_true", help="List available styles and exit")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.list_styles:
        print("Available IP character styles:")
        print("-" * 60)
        for name, desc in IP_STYLES.items():
            print(f"  {name:12} - {desc}")
        return

    if not os.path.isfile(args.image):
        print(f"Error: Image file not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    print(f"Processing image: {args.image}")
    if args.style:
        print(f"Style: {args.style} - {IP_STYLES[args.style]}")

    content, raw = generate_ip_character(
        image_path=args.image,
        prompt=args.prompt,
        style=args.style,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(raw, f, ensure_ascii=False, indent=2)
        print(f"JSON response saved to: {args.output}")

    if not args.no_save:
        saved_files = save_images_from_response(raw, args.save_dir)
        if saved_files:
            for filepath in saved_files:
                print(f"Image saved: {filepath}")
        else:
            print("No images found in response")

    if args.print_json:
        print(json.dumps(raw, ensure_ascii=False, indent=2))
    elif content:
        print(f"\nModel response:\n{content}")


if __name__ == "__main__":
    main()
