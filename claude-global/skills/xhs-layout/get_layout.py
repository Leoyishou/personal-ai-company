#!/usr/bin/env python3
"""
小红书封面布局计算工具

用法：
    python get_layout.py hero --canvas 1080x1440
    python get_layout.py knowledge --canvas 1080x1440 --json
"""

import argparse
import json
from typing import Dict, List, Tuple

# 布局模板定义
TEMPLATES = {
    "hero": {
        "description": "大图+标题，适合视觉冲击型封面",
        "slots": [
            {"name": "image", "region": [0.05, 0.02, 0.95, 0.58]},
            {"name": "title", "region": [0.025, 0.60, 0.975, 0.96]},
        ]
    },
    "knowledge": {
        "description": "知识卡片，适合干货分享",
        "slots": [
            {"name": "title", "region": [0, 0, 1, 0.15]},
            {"name": "image", "region": [0.05, 0.17, 0.95, 0.60]},
            {"name": "points", "region": [0.08, 0.62, 0.92, 0.92]},
            {"name": "tags", "region": [0.05, 0.94, 0.95, 0.98]},
        ]
    },
    "portrait": {
        "description": "人物介绍，适合 KOL/名人金句",
        "slots": [
            {"name": "avatar", "region": [0.25, 0.05, 0.75, 0.35]},
            {"name": "name", "region": [0.1, 0.37, 0.9, 0.45]},
            {"name": "quote", "region": [0.08, 0.47, 0.92, 0.88]},
            {"name": "source", "region": [0.1, 0.90, 0.9, 0.97]},
        ]
    },
    "comparison": {
        "description": "对比展示，适合 Before/After",
        "slots": [
            {"name": "title", "region": [0, 0, 1, 0.12]},
            {"name": "left", "region": [0.02, 0.14, 0.49, 0.85]},
            {"name": "right", "region": [0.51, 0.14, 0.98, 0.85]},
            {"name": "summary", "region": [0.05, 0.87, 0.95, 0.97]},
        ]
    },
    "tutorial": {
        "description": "步骤教程，4 宫格截图",
        "slots": [
            {"name": "title", "region": [0, 0, 1, 0.10]},
            {"name": "step1", "region": [0.02, 0.12, 0.49, 0.52]},
            {"name": "step2", "region": [0.51, 0.12, 0.98, 0.52]},
            {"name": "step3", "region": [0.02, 0.54, 0.49, 0.94]},
            {"name": "step4", "region": [0.51, 0.54, 0.98, 0.94]},
            {"name": "footer", "region": [0, 0.95, 1, 1]},
        ]
    },
}


def calc_slot_size(region: List[float], canvas_size: Tuple[int, int]) -> Dict:
    """计算槽位的像素尺寸"""
    w, h = canvas_size
    x1, y1, x2, y2 = region
    return {
        "x": int(x1 * w),
        "y": int(y1 * h),
        "width": int((x2 - x1) * w),
        "height": int((y2 - y1) * h),
    }


def get_layout(template_name: str, canvas_size: Tuple[int, int]) -> Dict:
    """获取模板的完整布局信息"""
    if template_name not in TEMPLATES:
        raise ValueError(f"Unknown template: {template_name}. Available: {list(TEMPLATES.keys())}")

    template = TEMPLATES[template_name]
    result = {
        "template": template_name,
        "description": template["description"],
        "canvas": {"width": canvas_size[0], "height": canvas_size[1]},
        "slots": {}
    }

    for slot in template["slots"]:
        size = calc_slot_size(slot["region"], canvas_size)
        result["slots"][slot["name"]] = {
            "region": slot["region"],
            **size
        }

    return result


def main():
    parser = argparse.ArgumentParser(description="小红书封面布局计算工具")
    parser.add_argument("template", nargs="?", help="模板名称 (hero/knowledge/portrait/comparison/tutorial)")
    parser.add_argument("--canvas", default="1080x1440", help="画布尺寸 (默认 1080x1440)")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--list", action="store_true", help="列出所有模板")

    args = parser.parse_args()

    # 列出所有模板
    if args.list or not args.template:
        print("可用模板：")
        for name, tmpl in TEMPLATES.items():
            print(f"  {name}: {tmpl['description']}")
        return

    # 解析画布尺寸
    try:
        w, h = map(int, args.canvas.lower().split("x"))
    except ValueError:
        print(f"Invalid canvas size: {args.canvas}. Use format like '1080x1440'")
        return 1

    # 计算布局
    try:
        layout = get_layout(args.template, (w, h))
    except ValueError as e:
        print(str(e))
        return 1

    # 输出
    if args.json:
        print(json.dumps(layout, indent=2, ensure_ascii=False))
    else:
        print(f"模板: {layout['template']} - {layout['description']}")
        print(f"画布: {w}x{h}")
        print("槽位尺寸:")
        for name, slot in layout["slots"].items():
            print(f"  {name}: {slot['width']}x{slot['height']} @ ({slot['x']}, {slot['y']})")


if __name__ == "__main__":
    exit(main() or 0)
