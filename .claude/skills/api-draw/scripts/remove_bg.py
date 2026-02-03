#!/usr/bin/env python3
"""
抠图工具 - 去除图片背景

支持两种模式：
1. 白底抠图（默认）：将白色/浅色背景变透明，适合圆形头像、图标等
2. AI抠图（需要 rembg）：通用智能抠图

用法：
    python remove_bg.py input.jpg -o output.png
    python remove_bg.py input.jpg -o output.png --threshold 240
    python remove_bg.py input.jpg -o output.png --mode ai  # 需要 rembg
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("请先安装依赖: pip install Pillow numpy")
    sys.exit(1)


def remove_white_background(
    image_path: str,
    output_path: str,
    threshold: int = 245,
    feather: int = 2
) -> str:
    """
    去除白色/浅色背景

    Args:
        image_path: 输入图片路径
        output_path: 输出图片路径（必须是 PNG）
        threshold: 亮度阈值，高于此值的像素视为背景（0-255）
        feather: 边缘羽化程度

    Returns:
        输出文件路径
    """
    # 读取图片
    img = Image.open(image_path).convert('RGBA')
    data = np.array(img)

    # 计算每个像素的亮度（RGB平均值）
    rgb = data[:, :, :3]
    brightness = np.mean(rgb, axis=2)

    # 创建透明度蒙版
    # 亮度高于阈值的像素变透明
    alpha = np.where(brightness > threshold, 0, 255).astype(np.uint8)

    # 可选：边缘羽化（让边缘更自然）
    if feather > 0:
        from PIL import ImageFilter
        alpha_img = Image.fromarray(alpha, mode='L')
        # 轻微模糊边缘
        alpha_img = alpha_img.filter(ImageFilter.GaussianBlur(feather))
        alpha = np.array(alpha_img)
        # 重新二值化但保留边缘渐变
        alpha = np.clip(alpha * 1.5, 0, 255).astype(np.uint8)

    # 应用新的透明度
    data[:, :, 3] = alpha

    # 保存
    result = Image.fromarray(data)

    # 确保输出为 PNG
    if not output_path.lower().endswith('.png'):
        output_path = str(Path(output_path).with_suffix('.png'))

    result.save(output_path)
    print(f"抠图完成: {output_path}")
    return output_path


def remove_background_ai(image_path: str, output_path: str) -> str:
    """
    使用 rembg (AI) 去除背景

    需要先安装: pip install rembg[gpu]  或 pip install rembg
    """
    try:
        from rembg import remove
    except ImportError:
        print("错误: 需要安装 rembg")
        print("安装方法: pip install rembg")
        sys.exit(1)

    img = Image.open(image_path)
    result = remove(img)

    # 确保输出为 PNG
    if not output_path.lower().endswith('.png'):
        output_path = str(Path(output_path).with_suffix('.png'))

    result.save(output_path)
    print(f"AI抠图完成: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description='抠图工具 - 去除图片背景',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 白底抠图（默认，适合头像/图标）
  python remove_bg.py portrait.jpg -o portrait_nobg.png

  # 调整阈值（更严格的白色判定）
  python remove_bg.py portrait.jpg -o portrait_nobg.png --threshold 230

  # AI智能抠图（需要 rembg）
  python remove_bg.py photo.jpg -o photo_nobg.png --mode ai
        """
    )
    parser.add_argument('image', help='输入图片路径')
    parser.add_argument('-o', '--output', required=True, help='输出图片路径（自动转为 PNG）')
    parser.add_argument('--mode', choices=['white', 'ai'], default='white',
                       help='抠图模式: white=白底抠图（默认）, ai=AI智能抠图')
    parser.add_argument('--threshold', type=int, default=245,
                       help='白底模式的亮度阈值（0-255，默认245）')
    parser.add_argument('--feather', type=int, default=2,
                       help='边缘羽化程度（默认2，0=不羽化）')

    args = parser.parse_args()

    if args.mode == 'ai':
        remove_background_ai(args.image, args.output)
    else:
        remove_white_background(args.image, args.output, args.threshold, args.feather)


if __name__ == '__main__':
    main()
