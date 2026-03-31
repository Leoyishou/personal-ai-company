#!/usr/bin/env python3
"""
人物语录风格合成脚本
将 AI 生成的木刻肖像与语录文字卡片合成为小红书竖版图片。

用法:
    python scripts/quote_portrait.py \
        --portrait /path/to/portrait.png \
        --quote "语录内容" \
        --attribution "—作者名《书名》" \
        --output /path/to/output.png

    # 也可以用多行语录
    python scripts/quote_portrait.py \
        --portrait /path/to/portrait.png \
        --quote "想钱，想女人的男人，\n才是正人君子；\n不敢想，不敢说的男人，\n都是废物。" \
        --attribution "—刘震云《咸的玩笑》" \
        --bg-color "#0047AB"
"""

import argparse
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageEnhance


def hex_to_rgb(hex_color):
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def find_font(weight="bold"):
    """Find available Chinese font on the system."""
    bold_fonts = [
        ("/System/Library/Fonts/Hiragino Sans GB.ttc", 2),  # W6 bold
        ("/System/Library/Fonts/STHeiti Medium.ttc", 1),     # SC Medium
    ]
    regular_fonts = [
        ("/System/Library/Fonts/Hiragino Sans GB.ttc", 0),  # W3 regular
        ("/System/Library/Fonts/STHeiti Medium.ttc", 0),
        ("/Library/Fonts/Arial Unicode.ttf", 0),
    ]

    candidates = bold_fonts if weight == "bold" else regular_fonts
    for path, index in candidates:
        if os.path.exists(path):
            return path, index
    return None, 0


def generate_quote_portrait(
    portrait_path,
    quote,
    attribution,
    output_path=None,
    bg_color="#0047AB",
    target_w=1080,
    target_h=1440,
    card_opacity=235,
    quote_font_size=55,
    attr_font_size=40,
):
    """Generate a composite image with portrait and quote card overlay."""

    # Load portrait
    img = Image.open(portrait_path).convert("RGBA")
    w, h = img.size

    # Resize portrait to fill width
    scale = target_w / w
    new_w = target_w
    new_h = int(h * scale)
    img_resized = img.resize((new_w, new_h), Image.LANCZOS)

    # Create canvas with background color
    bg_rgb = hex_to_rgb(bg_color)
    canvas = Image.new("RGBA", (target_w, target_h), (*bg_rgb, 255))

    # Paste portrait at top
    canvas.paste(img_resized, (0, 0), img_resized)

    # If portrait doesn't fill canvas, extend with darkened bottom
    if new_h < target_h:
        crop_h = min(400, new_h)
        bottom_portion = img_resized.crop((0, new_h - crop_h, new_w, new_h))
        enhancer = ImageEnhance.Brightness(bottom_portion)
        bottom_dark = enhancer.enhance(0.4)
        canvas.paste(bottom_dark, (0, new_h), bottom_dark)

    # Calculate card dimensions
    card_margin = 60
    card_left = card_margin
    card_right = target_w - card_margin
    card_radius = 30

    # Calculate text height to determine card size
    font_path, font_index = find_font("bold")
    if font_path:
        quote_font = ImageFont.truetype(font_path, quote_font_size, index=font_index)
        attr_font = ImageFont.truetype(font_path, attr_font_size, index=font_index)
    else:
        quote_font = ImageFont.load_default()
        attr_font = ImageFont.load_default()

    # Measure text height
    lines = quote.replace("\\n", "\n").split("\n")
    line_spacing = 18
    total_text_h = 0
    for line in lines:
        bbox = quote_font.getbbox(line)
        total_text_h += (bbox[3] - bbox[1]) + line_spacing

    attr_bbox = attr_font.getbbox(attribution)
    attr_h = attr_bbox[3] - attr_bbox[1]

    # Card dimensions with padding
    card_padding_top = 50
    card_padding_bottom = 50
    card_h = card_padding_top + total_text_h + 25 + attr_h + card_padding_bottom

    card_top = target_h - card_h - 80
    card_bottom = card_top + card_h

    # Draw semi-transparent white card
    card_layer = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card_layer)
    card_draw.rounded_rectangle(
        [(card_left, card_top), (card_right, card_bottom)],
        radius=card_radius,
        fill=(255, 255, 255, card_opacity)
    )
    canvas = Image.alpha_composite(canvas, card_layer)

    # Draw text
    draw = ImageDraw.Draw(canvas)
    text_x = card_left + 50
    text_y = card_top + card_padding_top
    text_color = (0, 0, 0, 255)

    for line in lines:
        # Fake bold: draw with offsets
        for dx in range(2):
            draw.text((text_x + dx, text_y), line, font=quote_font, fill=text_color)
        bbox = quote_font.getbbox(line)
        text_y += (bbox[3] - bbox[1]) + line_spacing

    # Draw attribution (blue color matching background)
    text_y += 25
    attr_color = (*bg_rgb, 255)
    attr_x = card_right - 50 - attr_font.getlength(attribution)
    for dx in range(2):
        draw.text((attr_x + dx, text_y), attribution, font=attr_font, fill=attr_color)

    # Save output
    canvas = canvas.convert("RGB")
    if output_path is None:
        base = os.path.splitext(portrait_path)[0]
        output_path = f"{base}_quote.png"

    canvas.save(output_path, quality=95)
    print(f"Done: {output_path}")
    print(f"Size: {canvas.size[0]}x{canvas.size[1]}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="人物语录风格合成")
    parser.add_argument("--portrait", required=True, help="肖像图片路径")
    parser.add_argument("--quote", required=True, help="语录文本（用\\n分行）")
    parser.add_argument("--attribution", default="", help="署名（如 —作者《书名》）")
    parser.add_argument("--output", default=None, help="输出路径（默认在肖像同目录）")
    parser.add_argument("--bg-color", default="#0047AB", help="背景色（hex，默认钴蓝）")
    parser.add_argument("--width", type=int, default=1080, help="输出宽度")
    parser.add_argument("--height", type=int, default=1440, help="输出高度")
    parser.add_argument("--font-size", type=int, default=55, help="语录字号")
    parser.add_argument("--attr-font-size", type=int, default=40, help="署名字号")

    args = parser.parse_args()

    generate_quote_portrait(
        portrait_path=args.portrait,
        quote=args.quote,
        attribution=args.attribution,
        output_path=args.output,
        bg_color=args.bg_color,
        target_w=args.width,
        target_h=args.height,
        quote_font_size=args.font_size,
        attr_font_size=args.attr_font_size,
    )


if __name__ == "__main__":
    main()
