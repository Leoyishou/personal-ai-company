#!/usr/bin/env python3
"""
图片拼接工具 - 将多张图片拼接成一张，支持虚线边框
"""

import argparse
import os
import sys
from PIL import Image, ImageDraw


def draw_dashed_rect(draw, x1, y1, x2, y2, color='#888888', dash_length=12, gap_length=8, width=3):
    """绘制虚线矩形边框"""
    # 上边
    x = x1
    while x < x2:
        draw.line([(x, y1), (min(x + dash_length, x2), y1)], fill=color, width=width)
        x += dash_length + gap_length
    # 下边
    x = x1
    while x < x2:
        draw.line([(x, y2), (min(x + dash_length, x2), y2)], fill=color, width=width)
        x += dash_length + gap_length
    # 左边
    y = y1
    while y < y2:
        draw.line([(x1, y), (x1, min(y + dash_length, y2))], fill=color, width=width)
        y += dash_length + gap_length
    # 右边
    y = y1
    while y < y2:
        draw.line([(x2, y), (x2, min(y + dash_length, y2))], fill=color, width=width)
        y += dash_length + gap_length


def stitch_images(
    image_paths: list,
    output_path: str,
    direction: str = 'horizontal',
    target_size: int = 1440,
    gap: int = 30,
    padding: int = 40,
    border: int = 8,
    border_color: str = '#888888',
    border_style: str = 'dashed',
    bg_color: str = 'white'
):
    """
    拼接多张图片

    Args:
        image_paths: 图片路径列表
        output_path: 输出路径
        direction: 拼接方向 'horizontal' 或 'vertical'
        target_size: 目标尺寸（水平拼接时为高度，垂直拼接时为宽度）
        gap: 图片间距
        padding: 外边距
        border: 边框宽度
        border_color: 边框颜色
        border_style: 边框样式 'solid' 或 'dashed'
        bg_color: 背景颜色
    """
    # 加载图片
    imgs = []
    for p in image_paths:
        if not os.path.exists(p):
            print(f"警告: 文件不存在 {p}", file=sys.stderr)
            continue
        imgs.append(Image.open(p).convert('RGB'))

    if not imgs:
        print("错误: 没有有效的图片", file=sys.stderr)
        sys.exit(1)

    # 调整尺寸
    resized = []
    if direction == 'horizontal':
        # 水平拼接：统一高度
        for img in imgs:
            ratio = target_size / img.height
            new_width = int(img.width * ratio)
            resized.append(img.resize((new_width, target_size), Image.LANCZOS))
    else:
        # 垂直拼接：统一宽度
        for img in imgs:
            ratio = target_size / img.width
            new_height = int(img.height * ratio)
            resized.append(img.resize((target_size, new_height), Image.LANCZOS))

    # 计算画布尺寸
    n = len(resized)
    if direction == 'horizontal':
        total_width = sum(img.width for img in resized) + gap * (n - 1) + padding * 2 + border * 2 * n
        total_height = target_size + padding * 2 + border * 2
    else:
        total_width = target_size + padding * 2 + border * 2
        total_height = sum(img.height for img in resized) + gap * (n - 1) + padding * 2 + border * 2 * n

    # 创建画布
    canvas = Image.new('RGB', (total_width, total_height), bg_color)
    draw = ImageDraw.Draw(canvas)

    # 粘贴图片并绘制边框
    if direction == 'horizontal':
        x_offset = padding
        for img in resized:
            # 粘贴图片
            canvas.paste(img, (x_offset + border, padding + border))

            # 绘制边框
            if border_style == 'dashed':
                draw_dashed_rect(
                    draw,
                    x_offset, padding,
                    x_offset + img.width + border * 2, padding + img.height + border * 2,
                    color=border_color
                )
            else:
                draw.rectangle(
                    [x_offset, padding, x_offset + img.width + border * 2, padding + img.height + border * 2],
                    outline=border_color, width=border
                )

            x_offset += img.width + border * 2 + gap
    else:
        y_offset = padding
        for img in resized:
            # 粘贴图片
            canvas.paste(img, (padding + border, y_offset + border))

            # 绘制边框
            if border_style == 'dashed':
                draw_dashed_rect(
                    draw,
                    padding, y_offset,
                    padding + img.width + border * 2, y_offset + img.height + border * 2,
                    color=border_color
                )
            else:
                draw.rectangle(
                    [padding, y_offset, padding + img.width + border * 2, y_offset + img.height + border * 2],
                    outline=border_color, width=border
                )

            y_offset += img.height + border * 2 + gap

    # 保存
    if output_path.lower().endswith('.png'):
        canvas.save(output_path)
    else:
        canvas.save(output_path, quality=95)

    print(f"拼接完成: {output_path}")
    print(f"尺寸: {canvas.size[0]}x{canvas.size[1]}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description='图片拼接工具')
    parser.add_argument('images', nargs='+', help='要拼接的图片路径')
    parser.add_argument('-o', '--output', required=True, help='输出文件路径')
    parser.add_argument('-d', '--direction', choices=['horizontal', 'vertical', 'h', 'v'],
                        default='horizontal', help='拼接方向 (默认: horizontal)')
    parser.add_argument('-s', '--size', type=int, default=1440,
                        help='目标尺寸 - 水平拼接时为高度，垂直拼接时为宽度 (默认: 1440)')
    parser.add_argument('-g', '--gap', type=int, default=30, help='图片间距 (默认: 30)')
    parser.add_argument('-p', '--padding', type=int, default=40, help='外边距 (默认: 40)')
    parser.add_argument('-b', '--border', type=int, default=8, help='边框宽度 (默认: 8)')
    parser.add_argument('--border-color', default='#888888', help='边框颜色 (默认: #888888)')
    parser.add_argument('--border-style', choices=['solid', 'dashed'], default='dashed',
                        help='边框样式 (默认: dashed)')
    parser.add_argument('--bg-color', default='white', help='背景颜色 (默认: white)')

    args = parser.parse_args()

    # 处理方向简写
    direction = 'horizontal' if args.direction in ['horizontal', 'h'] else 'vertical'

    stitch_images(
        image_paths=args.images,
        output_path=args.output,
        direction=direction,
        target_size=args.size,
        gap=args.gap,
        padding=args.padding,
        border=args.border,
        border_color=args.border_color,
        border_style=args.border_style,
        bg_color=args.bg_color
    )


if __name__ == '__main__':
    main()
