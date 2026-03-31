#!/usr/bin/env python3
"""
Tier List 排行榜图片生成器
生成小红书风格的 9:16 竖版 Tier List 图片。

用法:
    python scripts/tier_list.py \
        --title "程序员工具 Tier List" \
        --tiers '[
            {"label": "夺", "items": ["Cursor", "Claude Code"]},
            {"label": "顶级", "items": ["VS Code", "Vim"]},
            {"label": "人上人", "items": ["JetBrains", "Sublime"]},
            {"label": "NPC", "items": ["Notepad++", "Atom"]},
            {"label": "拉完了", "items": ["记事本"]}
        ]' \
        --output /tmp/tier_list.png

    # 自定义 tier 颜色和标签
    python scripts/tier_list.py \
        --tiers '[{"label": "S", "color": "#FF0000", "items": ["Item1"]}, ...]'
"""

import argparse
import json
import os
import sys
from PIL import Image, ImageDraw, ImageFont


# Default tiers with colors (red -> orange -> yellow -> cream -> white)
DEFAULT_TIERS = [
    {"label": "夯", "color": "#FF2D2D"},
    {"label": "顶级", "color": "#FFA500"},
    {"label": "人上人", "color": "#FFE600"},
    {"label": "NPC", "color": "#FFF5CC"},
    {"label": "拉完了", "color": "#FFFFFF"},
]

CONTENT_BG = "#D9D9D9"  # Gray content area


def find_font(weight="bold"):
    """Find available Chinese font on the system."""
    bold_fonts = [
        ("/System/Library/Fonts/Hiragino Sans GB.ttc", 2),
        ("/System/Library/Fonts/STHeiti Medium.ttc", 1),
    ]
    regular_fonts = [
        ("/System/Library/Fonts/Hiragino Sans GB.ttc", 0),
        ("/System/Library/Fonts/STHeiti Medium.ttc", 0),
        ("/Library/Fonts/Arial Unicode.ttf", 0),
    ]
    candidates = bold_fonts if weight == "bold" else regular_fonts
    for path, index in candidates:
        if os.path.exists(path):
            return path, index
    return None, 0


def generate_tier_list(
    tiers,
    title=None,
    output_path=None,
    target_w=1080,
    target_h=1920,
    label_width=200,
    row_gap=6,
    item_font_size=42,
    label_font_size=72,
    title_font_size=64,
):
    """Generate a tier list image.

    Args:
        tiers: list of dicts with keys: label, items, color (optional)
        title: optional title text at the top
        output_path: where to save the image
    """
    canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    # Load fonts
    bold_path, bold_idx = find_font("bold")
    reg_path, reg_idx = find_font("regular")

    if bold_path:
        label_font = ImageFont.truetype(bold_path, label_font_size, index=bold_idx)
        item_font = ImageFont.truetype(bold_path, item_font_size, index=bold_idx)
        title_font = ImageFont.truetype(bold_path, title_font_size, index=bold_idx)
    else:
        label_font = ImageFont.load_default()
        item_font = ImageFont.load_default()
        title_font = ImageFont.load_default()

    # Merge default tier colors with user data
    for i, tier in enumerate(tiers):
        if "color" not in tier:
            if i < len(DEFAULT_TIERS):
                tier["color"] = DEFAULT_TIERS[i]["color"]
            else:
                tier["color"] = "#CCCCCC"
        if "items" not in tier:
            tier["items"] = []

    # Layout calculations
    margin_x = 40
    content_left = margin_x + label_width + row_gap
    content_right = target_w - margin_x

    # Title area
    y_cursor = 60
    if title:
        title_bbox = title_font.getbbox(title)
        title_h = title_bbox[3] - title_bbox[1]
        title_x = (target_w - title_font.getlength(title)) / 2
        draw.text((title_x, y_cursor), title, font=title_font, fill=(0, 0, 0))
        y_cursor += title_h + 50

    # Calculate row height based on available space
    num_tiers = len(tiers)
    available_h = target_h - y_cursor - 60  # bottom margin
    total_gap = row_gap * (num_tiers - 1)
    row_h = int((available_h - total_gap) / num_tiers)
    row_h = min(row_h, 340)  # cap max row height

    for tier in tiers:
        label = tier["label"]
        items = tier["items"]
        color = tier["color"]

        # Parse color
        hex_color = color.lstrip("#")
        r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        # Draw label background
        draw.rectangle(
            [(margin_x, y_cursor), (margin_x + label_width, y_cursor + row_h)],
            fill=(r, g, b),
        )

        # Draw label text (centered)
        label_bbox = label_font.getbbox(label)
        lw = label_font.getlength(label)
        lh = label_bbox[3] - label_bbox[1]
        lx = margin_x + (label_width - lw) / 2
        ly = y_cursor + (row_h - lh) / 2 - label_bbox[1]
        # Use dark text
        draw.text((lx, ly), label, font=label_font, fill=(0, 0, 0))

        # Draw content background (gray)
        draw.rectangle(
            [(content_left, y_cursor), (content_right, y_cursor + row_h)],
            fill=CONTENT_BG,
        )

        # Draw items as text tags
        if items:
            item_margin = 30
            item_gap = 20
            item_x = content_left + item_margin
            # Vertical center
            sample_bbox = item_font.getbbox("测")
            single_h = sample_bbox[3] - sample_bbox[1]
            line_h = single_h + 24  # padding around tag
            # Calculate total lines needed
            lines = []
            current_line = []
            cx = item_x
            for item in items:
                tw = item_font.getlength(item) + 36  # tag padding
                if cx + tw > content_right - item_margin and current_line:
                    lines.append(current_line)
                    current_line = [item]
                    cx = item_x + tw + item_gap
                else:
                    current_line.append(item)
                    cx += tw + item_gap
            if current_line:
                lines.append(current_line)

            total_lines_h = len(lines) * line_h + (len(lines) - 1) * 8
            start_y = y_cursor + (row_h - total_lines_h) / 2

            for line_items in lines:
                ix = item_x
                for item in line_items:
                    tw = item_font.getlength(item)
                    tag_w = tw + 36
                    tag_h = line_h
                    tag_y = start_y
                    # Draw tag background (white rounded rect)
                    draw.rounded_rectangle(
                        [(ix, tag_y), (ix + tag_w, tag_y + tag_h)],
                        radius=12,
                        fill=(255, 255, 255),
                    )
                    # Draw tag text
                    text_x = ix + 18
                    text_y = tag_y + (tag_h - single_h) / 2 - sample_bbox[1]
                    draw.text((text_x, text_y), item, font=item_font, fill=(51, 51, 51))
                    ix += tag_w + item_gap
                start_y += line_h + 8

        y_cursor += row_h + row_gap

    # Save
    if output_path is None:
        output_path = "/tmp/tier_list.png"

    canvas.save(output_path, quality=95)
    print(f"Done: {output_path}")
    print(f"Size: {canvas.size[0]}x{canvas.size[1]}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Tier List 排行榜图片生成")
    parser.add_argument("--tiers", required=True, help="JSON array of tier data")
    parser.add_argument("--title", default=None, help="Title text at the top")
    parser.add_argument("--output", default=None, help="Output path")
    parser.add_argument("--width", type=int, default=1080, help="Image width")
    parser.add_argument("--height", type=int, default=1920, help="Image height (default 1920 for 9:16)")
    parser.add_argument("--label-width", type=int, default=200, help="Width of tier label column")
    parser.add_argument("--label-font-size", type=int, default=72, help="Tier label font size")
    parser.add_argument("--item-font-size", type=int, default=42, help="Item text font size")
    parser.add_argument("--title-font-size", type=int, default=64, help="Title font size")

    args = parser.parse_args()

    tiers = json.loads(args.tiers)

    generate_tier_list(
        tiers=tiers,
        title=args.title,
        output_path=args.output,
        target_w=args.width,
        target_h=args.height,
        label_width=args.label_width,
        label_font_size=args.label_font_size,
        item_font_size=args.item_font_size,
        title_font_size=args.title_font_size,
    )


if __name__ == "__main__":
    main()
