#!/usr/bin/env python3
"""
圆形裁剪工具 - 将图片裁剪为圆形

用法：
    python circle_crop.py input.png -o output.png
    python circle_crop.py input.png -o output.png --size 300
    python circle_crop.py input.png -o output.png --border 4 --border-color "#333333"
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("请先安装依赖: pip install Pillow")
    sys.exit(1)


def circle_crop(
    image_path: str,
    output_path: str,
    size: int = None,
    border_width: int = 0,
    border_color: str = "#333333"
) -> str:
    """
    将图片裁剪为圆形

    Args:
        image_path: 输入图片路径
        output_path: 输出图片路径（必须是 PNG）
        size: 输出尺寸（直径），None 则保持原始尺寸
        border_width: 边框宽度（像素）
        border_color: 边框颜色（hex）

    Returns:
        输出文件路径
    """
    # 读取图片
    img = Image.open(image_path).convert('RGBA')

    # 裁剪为正方形（取中心区域）
    w, h = img.size
    min_dim = min(w, h)
    left = (w - min_dim) // 2
    top = (h - min_dim) // 2
    img = img.crop((left, top, left + min_dim, top + min_dim))

    # 缩放到目标尺寸
    if size:
        img = img.resize((size, size), Image.Resampling.LANCZOS)

    final_size = img.size[0]

    # 创建圆形蒙版
    mask = Image.new('L', (final_size, final_size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, final_size - 1, final_size - 1), fill=255)

    # 应用蒙版
    result = Image.new('RGBA', (final_size, final_size), (0, 0, 0, 0))
    result.paste(img, (0, 0), mask)

    # 添加边框
    if border_width > 0:
        # 解析颜色
        if border_color.startswith('#'):
            r = int(border_color[1:3], 16)
            g = int(border_color[3:5], 16)
            b = int(border_color[5:7], 16)
            color = (r, g, b, 255)
        else:
            color = (51, 51, 51, 255)  # 默认深灰

        # 绘制圆形边框
        border_draw = ImageDraw.Draw(result)
        for i in range(border_width):
            border_draw.ellipse(
                (i, i, final_size - 1 - i, final_size - 1 - i),
                outline=color
            )

    # 确保输出为 PNG
    if not output_path.lower().endswith('.png'):
        output_path = str(Path(output_path).with_suffix('.png'))

    result.save(output_path)
    print(f"圆形裁剪完成: {output_path}")
    print(f"  尺寸: {final_size}x{final_size}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description='圆形裁剪工具 - 将图片裁剪为圆形',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基础用法
  python circle_crop.py portrait.png -o portrait_circle.png

  # 指定输出尺寸
  python circle_crop.py portrait.png -o portrait_circle.png --size 300

  # 添加边框
  python circle_crop.py portrait.png -o portrait_circle.png --border 4 --border-color "#333333"
        """
    )
    parser.add_argument('image', help='输入图片路径')
    parser.add_argument('-o', '--output', required=True, help='输出图片路径（自动转为 PNG）')
    parser.add_argument('--size', type=int, help='输出尺寸（直径，像素）')
    parser.add_argument('--border', type=int, default=0, help='边框宽度（默认0，无边框）')
    parser.add_argument('--border-color', default='#333333', help='边框颜色（默认 #333333 深灰）')

    args = parser.parse_args()

    circle_crop(
        image_path=args.image,
        output_path=args.output,
        size=args.size,
        border_width=args.border,
        border_color=args.border_color
    )


if __name__ == '__main__':
    main()
