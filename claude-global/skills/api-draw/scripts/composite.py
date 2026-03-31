#!/usr/bin/env python3
"""
图片合成工具 - 将前景图叠加到背景图上

支持功能：
- 指定位置（左上角坐标或预设位置）
- 调整前景图大小
- 透明背景叠加

用法：
    python composite.py --bg main.jpg --fg portrait.png -o output.jpg
    python composite.py --bg main.jpg --fg portrait.png --position top-right --size 150 -o output.jpg
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("请先安装依赖: pip install Pillow")
    sys.exit(1)


def composite_images(
    background_path: str,
    foreground_path: str,
    output_path: str,
    position: str = 'top-right',
    x: int = None,
    y: int = None,
    size: int = None,
    padding: int = 40
) -> str:
    """
    将前景图叠加到背景图上

    Args:
        background_path: 背景图路径
        foreground_path: 前景图路径（建议PNG透明背景）
        output_path: 输出路径
        position: 预设位置（top-left, top-right, bottom-left, bottom-right, center）
        x, y: 自定义位置（优先于 position）
        size: 前景图尺寸（等比缩放到此宽/高）
        padding: 边距（用于预设位置）

    Returns:
        输出文件路径
    """
    # 读取图片
    bg = Image.open(background_path).convert('RGBA')
    fg = Image.open(foreground_path).convert('RGBA')

    bg_w, bg_h = bg.size
    fg_w, fg_h = fg.size

    # 缩放前景图
    if size:
        ratio = size / max(fg_w, fg_h)
        new_size = (int(fg_w * ratio), int(fg_h * ratio))
        fg = fg.resize(new_size, Image.Resampling.LANCZOS)
        fg_w, fg_h = fg.size

    # 计算位置
    if x is not None and y is not None:
        pos_x, pos_y = x, y
    else:
        positions = {
            'top-left': (padding, padding),
            'top-right': (bg_w - fg_w - padding, padding),
            'bottom-left': (padding, bg_h - fg_h - padding),
            'bottom-right': (bg_w - fg_w - padding, bg_h - fg_h - padding),
            'center': ((bg_w - fg_w) // 2, (bg_h - fg_h) // 2),
        }
        pos_x, pos_y = positions.get(position, positions['top-right'])

    # 合成
    # 创建一个与背景同尺寸的透明图层
    composite = Image.new('RGBA', bg.size, (0, 0, 0, 0))
    composite.paste(bg, (0, 0))

    # 叠加前景（使用前景的透明度作为蒙版）
    composite.paste(fg, (pos_x, pos_y), fg)

    # 保存
    # 根据输出格式决定是否保留透明度
    if output_path.lower().endswith(('.jpg', '.jpeg')):
        # JPEG 不支持透明，转为 RGB
        final = Image.new('RGB', composite.size, (255, 255, 255))
        final.paste(composite, mask=composite.split()[3])  # 用透明度作蒙版
        final.save(output_path, quality=95)
    else:
        composite.save(output_path)

    print(f"合成完成: {output_path}")
    print(f"  背景: {bg_w}x{bg_h}")
    print(f"  前景: {fg_w}x{fg_h} @ ({pos_x}, {pos_y})")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description='图片合成工具 - 将前景图叠加到背景图上',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 头像放右上角（默认）
  python composite.py --bg whiteboard.jpg --fg portrait.png -o result.jpg

  # 头像放右上角，缩放到150px
  python composite.py --bg whiteboard.jpg --fg portrait.png --position top-right --size 150 -o result.jpg

  # 自定义位置
  python composite.py --bg whiteboard.jpg --fg portrait.png --x 700 --y 200 --size 120 -o result.jpg

预设位置:
  top-left, top-right, bottom-left, bottom-right, center
        """
    )
    parser.add_argument('--bg', required=True, help='背景图路径')
    parser.add_argument('--fg', required=True, help='前景图路径（建议PNG透明背景）')
    parser.add_argument('-o', '--output', required=True, help='输出图片路径')
    parser.add_argument('--position', default='top-right',
                       choices=['top-left', 'top-right', 'bottom-left', 'bottom-right', 'center'],
                       help='预设位置（默认: top-right）')
    parser.add_argument('--x', type=int, help='自定义X坐标（优先于position）')
    parser.add_argument('--y', type=int, help='自定义Y坐标（优先于position）')
    parser.add_argument('--size', type=int, help='前景图尺寸（等比缩放）')
    parser.add_argument('--padding', type=int, default=40, help='边距（默认40px）')

    args = parser.parse_args()

    composite_images(
        background_path=args.bg,
        foreground_path=args.fg,
        output_path=args.output,
        position=args.position,
        x=args.x,
        y=args.y,
        size=args.size,
        padding=args.padding
    )


if __name__ == '__main__':
    main()
