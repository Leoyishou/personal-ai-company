#!/usr/bin/env python3
"""
人物封面合成工具 - 一步完成「白板 + 手绘圆框 + 头像」合成

核心思路：AI 生成不带圆框的白板图，圆框和头像由代码绘制，100% 可控对齐。

用法：
    python portrait_cover.py \\
        --bg whiteboard.jpg \\
        --portrait portrait.png \\
        --circle-y 200 \\
        --circle-radius 140 \\
        --portrait-size 260 \\
        -o output.png

    # 使用默认参数
    python portrait_cover.py --bg bg.jpg --portrait portrait.png -o cover.png
"""

import argparse
import math
import random
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("请先安装依赖: pip install Pillow")
    sys.exit(1)


def draw_hand_drawn_circle(
    draw: ImageDraw.Draw,
    center: tuple,
    radius: int,
    color: tuple,
    width: int = 3,
    passes: int = 3,
    wobble: int = 2
):
    """
    绘制手绘风格圆框（多圈微偏移叠加，模拟手绘抖动效果）

    Args:
        draw: PIL ImageDraw 对象
        center: (cx, cy) 圆心坐标
        radius: 圆框半径
        color: 颜色 (r, g, b) 或 (r, g, b, a)
        width: 线条宽度
        passes: 绘制圈数（越多越有手绘感）
        wobble: 抖动幅度（像素）
    """
    cx, cy = center

    for i in range(passes):
        # 每圈有微小随机偏移，模拟手绘抖动
        ox = random.randint(-wobble, wobble)
        oy = random.randint(-wobble, wobble)

        # 使用 arc 分段绘制，每段加入微小抖动
        segments = 36  # 分成36段，每段10度
        for j in range(segments):
            start_angle = j * 360 / segments
            end_angle = (j + 1) * 360 / segments

            # 每段的轻微偏移
            seg_ox = random.randint(-1, 1)
            seg_oy = random.randint(-1, 1)

            draw.arc(
                [
                    cx - radius + ox + seg_ox,
                    cy - radius + oy + seg_oy,
                    cx + radius + ox + seg_ox,
                    cy + radius + oy + seg_oy
                ],
                start=start_angle,
                end=end_angle,
                fill=color,
                width=width
            )


def parse_color(color_str: str) -> tuple:
    """解析颜色字符串为 RGB 元组"""
    if color_str.startswith('#'):
        r = int(color_str[1:3], 16)
        g = int(color_str[3:5], 16)
        b = int(color_str[5:7], 16)
        return (r, g, b)
    return (51, 51, 51)  # 默认深灰


def circle_crop_image(img: Image.Image, size: int) -> Image.Image:
    """
    将图片裁剪为圆形

    Args:
        img: PIL Image 对象
        size: 输出直径

    Returns:
        圆形裁剪后的 RGBA 图片
    """
    # 转为 RGBA
    img = img.convert('RGBA')

    # 裁剪为正方形（取中心区域）
    w, h = img.size
    min_dim = min(w, h)
    left = (w - min_dim) // 2
    top = (h - min_dim) // 2
    img = img.crop((left, top, left + min_dim, top + min_dim))

    # 缩放到目标尺寸
    img = img.resize((size, size), Image.Resampling.LANCZOS)

    # 创建圆形蒙版
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, size - 1, size - 1), fill=255)

    # 应用蒙版
    result = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    result.paste(img, (0, 0), mask)

    return result


def compose_portrait_cover(
    background_path: str,
    portrait_path: str,
    output_path: str,
    circle_y: int = 200,
    circle_radius: int = 140,
    portrait_size: int = 260,
    circle_color: str = "#333333",
    circle_width: int = 3,
    circle_passes: int = 3,
    circle_wobble: int = 2
) -> str:
    """
    合成人物封面

    流程：
    1. 读取白板背景图
    2. 在指定位置绘制手绘风格圆框
    3. 裁剪头像为圆形并放置在圆框中心
    4. 保存输出

    Args:
        background_path: 白板背景图路径（应为无圆框版本）
        portrait_path: 人物头像路径
        output_path: 输出图片路径
        circle_y: 圆心距顶部的像素（X 自动居中）
        circle_radius: 圆框半径
        portrait_size: 头像直径（应比圆框小，留出边距）
        circle_color: 圆框颜色（hex）
        circle_width: 圆框线条宽度
        circle_passes: 圆框绘制圈数（越多越有手绘感）
        circle_wobble: 圆框抖动幅度

    Returns:
        输出文件路径
    """
    # 读取背景
    bg = Image.open(background_path).convert('RGBA')
    bg_w, bg_h = bg.size

    # 圆心 X 坐标 = 图片水平居中
    circle_cx = bg_w // 2
    circle_cy = circle_y

    # 解析颜色
    color = parse_color(circle_color)

    # 绘制手绘圆框
    draw = ImageDraw.Draw(bg)
    draw_hand_drawn_circle(
        draw,
        center=(circle_cx, circle_cy),
        radius=circle_radius,
        color=color,
        width=circle_width,
        passes=circle_passes,
        wobble=circle_wobble
    )

    # 裁剪头像为圆形
    portrait_img = Image.open(portrait_path)
    portrait_circle = circle_crop_image(portrait_img, portrait_size)

    # 计算头像位置（居中于圆框）
    portrait_x = circle_cx - portrait_size // 2
    portrait_y = circle_cy - portrait_size // 2

    # 叠加头像
    bg.paste(portrait_circle, (portrait_x, portrait_y), portrait_circle)

    # 保存
    if output_path.lower().endswith(('.jpg', '.jpeg')):
        # JPEG 不支持透明，转为 RGB
        final = Image.new('RGB', bg.size, (255, 255, 255))
        final.paste(bg, mask=bg.split()[3])
        final.save(output_path, quality=95)
    else:
        bg.save(output_path)

    print(f"封面合成完成: {output_path}")
    print(f"  背景尺寸: {bg_w}x{bg_h}")
    print(f"  圆框位置: ({circle_cx}, {circle_cy}), 半径 {circle_radius}")
    print(f"  头像尺寸: {portrait_size}x{portrait_size}")
    print(f"  头像位置: ({portrait_x}, {portrait_y})")

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description='人物封面合成工具 - 白板 + 手绘圆框 + 头像',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基础用法（使用默认参数）
  python portrait_cover.py --bg whiteboard.jpg --portrait portrait.png -o cover.png

  # 自定义圆框位置和大小
  python portrait_cover.py \\
      --bg whiteboard.jpg \\
      --portrait portrait.png \\
      --circle-y 180 \\
      --circle-radius 150 \\
      --portrait-size 280 \\
      -o cover.png

  # 自定义圆框样式
  python portrait_cover.py \\
      --bg whiteboard.jpg \\
      --portrait portrait.png \\
      --circle-color "#555555" \\
      --circle-width 4 \\
      --circle-passes 5 \\
      -o cover.png

参数说明:
  --circle-y        圆心距顶部的像素，默认 200（适合 3:4 图的上部）
  --circle-radius   圆框半径，默认 140
  --portrait-size   头像直径，默认 260（比圆框直径小 20px 左右留边距）
  --circle-passes   绘制圈数，越多越有手绘感，默认 3
  --circle-wobble   抖动幅度，默认 2
        """
    )

    parser.add_argument('--bg', required=True, help='背景图路径（无圆框的白板图）')
    parser.add_argument('--portrait', required=True, help='人物头像路径')
    parser.add_argument('-o', '--output', required=True, help='输出图片路径')

    # 圆框位置和大小
    parser.add_argument('--circle-y', type=int, default=200,
                       help='圆心距顶部像素，默认 200')
    parser.add_argument('--circle-radius', type=int, default=140,
                       help='圆框半径，默认 140')
    parser.add_argument('--portrait-size', type=int, default=260,
                       help='头像直径，默认 260')

    # 圆框样式
    parser.add_argument('--circle-color', default='#333333',
                       help='圆框颜色，默认 #333333')
    parser.add_argument('--circle-width', type=int, default=3,
                       help='圆框线宽，默认 3')
    parser.add_argument('--circle-passes', type=int, default=3,
                       help='绘制圈数（手绘感），默认 3')
    parser.add_argument('--circle-wobble', type=int, default=2,
                       help='抖动幅度，默认 2')

    args = parser.parse_args()

    compose_portrait_cover(
        background_path=args.bg,
        portrait_path=args.portrait,
        output_path=args.output,
        circle_y=args.circle_y,
        circle_radius=args.circle_radius,
        portrait_size=args.portrait_size,
        circle_color=args.circle_color,
        circle_width=args.circle_width,
        circle_passes=args.circle_passes,
        circle_wobble=args.circle_wobble
    )


if __name__ == '__main__':
    main()
