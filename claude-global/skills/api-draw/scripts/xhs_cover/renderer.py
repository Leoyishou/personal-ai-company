"""
渲染引擎 - 读取模板 + 内容 → 生成封面
"""

import os
from typing import Any, Dict, Optional

from PIL import Image

from .core import Template, load_template


def hex_to_rgb(hex_color: str) -> tuple:
    """将十六进制颜色转换为 RGB 元组"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def render_template(
    template: str,
    content: Dict[str, Any],
    output: Optional[str] = None,
) -> Image.Image:
    """
    渲染模板生成封面

    Args:
        template: 模板名称（如 "knowledge"）或 Template 对象
        content: 内容字典，key 为槽位名称
        output: 输出文件路径（可选）

    Returns:
        PIL Image 对象
    """
    # 加载模板
    if isinstance(template, str):
        tmpl = load_template(template)
    else:
        tmpl = template

    # 创建画布
    canvas = Image.new('RGBA', tmpl.size, hex_to_rgb(tmpl.bg_color) + (255,))

    # 渲染每个槽位
    for slot in tmpl.slots:
        slot_content = content.get(slot.name)
        if slot_content is None:
            print(f"Warning: No content for slot '{slot.name}'")
            continue

        rect = slot.get_rect(tmpl.size)
        try:
            slot.render(canvas, slot_content, rect)
        except Exception as e:
            print(f"Error rendering slot '{slot.name}': {e}")

    # 保存文件
    if output:
        # 确保输出目录存在
        output_dir = os.path.dirname(output)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # 根据输出格式决定是否保留透明度
        if output.lower().endswith(('.jpg', '.jpeg')):
            # JPEG 不支持透明，转为 RGB
            final = Image.new('RGB', canvas.size, (255, 255, 255))
            final.paste(canvas, mask=canvas.split()[3])
            final.save(output, quality=95)
        else:
            canvas.save(output)

        print(f"封面已生成: {output}")
        print(f"  尺寸: {tmpl.size[0]}x{tmpl.size[1]}")

    return canvas


def list_templates() -> list:
    """列出所有可用模板"""
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    templates = []

    if os.path.exists(templates_dir):
        for f in os.listdir(templates_dir):
            if f.endswith('.json'):
                templates.append(f[:-5])

    return sorted(templates)


def preview_template(template_name: str) -> None:
    """预览模板布局（ASCII 艺术）"""
    tmpl = load_template(template_name)

    print(f"\n模板: {tmpl.name}")
    print(f"尺寸: {tmpl.size[0]}x{tmpl.size[1]}")
    print(f"背景: {tmpl.bg_color}")
    print("\n槽位布局:")

    # 简单的 ASCII 预览
    grid_w, grid_h = 60, 30
    grid = [[' ' for _ in range(grid_w)] for _ in range(grid_h)]

    # 绘制边框
    for x in range(grid_w):
        grid[0][x] = '-'
        grid[grid_h-1][x] = '-'
    for y in range(grid_h):
        grid[y][0] = '|'
        grid[y][grid_w-1] = '|'

    # 绘制槽位
    for i, slot in enumerate(tmpl.slots):
        x1 = int(slot.region[0] * (grid_w - 2)) + 1
        y1 = int(slot.region[1] * (grid_h - 2)) + 1
        x2 = int(slot.region[2] * (grid_w - 2)) + 1
        y2 = int(slot.region[3] * (grid_h - 2)) + 1

        # 绘制槽位边框
        for x in range(x1, x2):
            if 0 < y1 < grid_h - 1:
                grid[y1][x] = '='
            if 0 < y2 - 1 < grid_h - 1:
                grid[y2-1][x] = '='

        # 标记槽位名称
        label = f"[{slot.name[:8]}]"
        cx = (x1 + x2) // 2 - len(label) // 2
        cy = (y1 + y2) // 2
        if 0 < cy < grid_h - 1:
            for j, c in enumerate(label):
                if 0 < cx + j < grid_w - 1:
                    grid[cy][cx + j] = c

    # 输出
    for row in grid:
        print(''.join(row))

    print("\n槽位详情:")
    for slot in tmpl.slots:
        print(f"  - {slot.name}: {slot.__class__.__name__}")
        print(f"    区域: {slot.region}")
        if slot.options:
            for k, v in slot.options.items():
                print(f"    {k}: {v}")
