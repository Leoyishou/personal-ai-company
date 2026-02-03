#!/usr/bin/env python3
"""生成小红书测试图片"""

from PIL import Image, ImageDraw, ImageFont
import random

def create_gradient_image(width=800, height=600):
    """创建渐变背景图片"""
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)

    # 创建紫红色渐变背景 (小红书风格)
    for y in range(height):
        # 从粉红色渐变到紫色
        r = int(255 - (y / height) * 100)
        g = int(100 - (y / height) * 50)
        b = int(150 + (y / height) * 100)
        draw.rectangle([(0, y), (width, y + 1)], fill=(r, g, b))

    return image, draw

def add_text_to_image(image, draw):
    """在图片上添加文字"""
    width, height = image.size

    # 使用系统默认字体
    try:
        # macOS 系统字体
        font_large = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 60)
        font_medium = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 40)
        font_small = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 30)
    except:
        # 如果找不到字体，使用默认字体
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 主标题
    main_text = "Claude Code"
    text_bbox = draw.textbbox((0, 0), main_text, font=font_large)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (width - text_width) // 2
    text_y = height // 3

    # 添加文字阴影
    draw.text((text_x + 3, text_y + 3), main_text, font=font_large, fill=(0, 0, 0, 128))
    # 添加主文字
    draw.text((text_x, text_y), main_text, font=font_large, fill=(255, 255, 255))

    # 副标题
    sub_text = "冒烟测试"
    text_bbox = draw.textbbox((0, 0), sub_text, font=font_medium)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (width - text_width) // 2
    text_y = height // 2

    draw.text((text_x + 2, text_y + 2), sub_text, font=font_medium, fill=(0, 0, 0, 128))
    draw.text((text_x, text_y), sub_text, font=font_medium, fill=(255, 255, 255))

    # 时间戳
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    text_bbox = draw.textbbox((0, 0), timestamp, font=font_small)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (width - text_width) // 2
    text_y = height * 2 // 3

    draw.text((text_x + 2, text_y + 2), timestamp, font=font_small, fill=(0, 0, 0, 128))
    draw.text((text_x, text_y), timestamp, font=font_small, fill=(255, 255, 255))

def add_decorations(image, draw):
    """添加装饰元素"""
    width, height = image.size

    # 添加一些圆形装饰
    for _ in range(10):
        x = random.randint(0, width)
        y = random.randint(0, height)
        r = random.randint(10, 30)
        alpha = random.randint(30, 100)
        color = (255, 255, 255, alpha)
        draw.ellipse([x-r, y-r, x+r, y+r], outline=color, width=2)

def main():
    """主函数"""
    # 创建图片
    image, draw = create_gradient_image(1080, 1080)  # 小红书推荐的正方形尺寸

    # 添加文字
    add_text_to_image(image, draw)

    # 添加装饰
    add_decorations(image, draw)

    # 保存图片
    output_path = "/Users/liuyishou/usr/projects/inbox/xiaohongshu/smoke_test_image.jpg"
    image.save(output_path, quality=95)
    print(f"✅ 测试图片已生成: {output_path}")
    return output_path

if __name__ == "__main__":
    main()
