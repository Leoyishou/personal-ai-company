#!/usr/bin/env python3
"""
小红书封面生成 CLI

用法:
    # 使用知识卡片模板
    python -m xhs_cover --template knowledge \
        --title "5个让你效率翻倍的AI工具" \
        --main_image "path/to/image.png" \
        --points "ChatGPT" "Claude" "Midjourney" \
        --tags "#AI工具 #效率提升" \
        -o cover.png

    # 使用 JSON 配置文件
    python -m xhs_cover --config cover_config.json -o cover.png

    # 列出可用模板
    python -m xhs_cover --list

    # 预览模板布局
    python -m xhs_cover --preview knowledge
"""

import argparse
import json
import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from xhs_cover.renderer import render_template, list_templates, preview_template


def parse_args():
    parser = argparse.ArgumentParser(
        description="小红书封面模板生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 知识卡片
  python -m xhs_cover --template knowledge \\
      --title "5个AI工具推荐" \\
      --main_image ./robot.png \\
      --points "ChatGPT" "Claude" "Cursor" \\
      --tags "#AI工具" \\
      -o cover.png

  # 人物介绍
  python -m xhs_cover --template portrait \\
      --avatar ./avatar.png \\
      --name "Elon Musk" \\
      --title "Tesla & SpaceX CEO" \\
      --quote "当某件事足够重要时，即使成功概率不高，你也要去做" \\
      -o portrait.png

  # 使用配置文件
  python -m xhs_cover --config config.json -o cover.png

可用模板:
  - knowledge: 知识卡片（标题+主图+要点列表+标签）
  - portrait: 人物介绍（头像+姓名+头衔+金句）
  - tutorial: 步骤教程（4步图文教程）
  - comparison: 对比展示（Before/After）
        """
    )

    # 模式选择
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--list", action="store_true", help="列出所有可用模板")
    mode_group.add_argument("--preview", metavar="TEMPLATE", help="预览模板布局")
    mode_group.add_argument("--config", metavar="FILE", help="使用 JSON 配置文件")
    mode_group.add_argument("--template", help="模板名称")

    # 输出
    parser.add_argument("-o", "--output", help="输出文件路径")

    # 通用槽位参数
    parser.add_argument("--title", help="标题文字")
    parser.add_argument("--tags", help="标签文字")
    parser.add_argument("--summary", help="总结/说明文字")
    parser.add_argument("--footer", help="底部文字")
    parser.add_argument("--subtitle", help="副标题文字")

    # hero 模板（大图+标题）
    parser.add_argument("--image", help="主图路径（hero模板）")

    # 知识卡片
    parser.add_argument("--main_image", help="主图路径或 'generate:prompt'")
    parser.add_argument("--points", nargs="+", help="要点列表")

    # 人物介绍
    parser.add_argument("--avatar", help="头像图片路径")
    parser.add_argument("--name", help="人物姓名")
    parser.add_argument("--quote", help="金句/简介")
    parser.add_argument("--source", help="来源/账号")

    # 步骤教程
    parser.add_argument("--step1", help="步骤1图片")
    parser.add_argument("--step1_label", help="步骤1说明")
    parser.add_argument("--step2", help="步骤2图片")
    parser.add_argument("--step2_label", help="步骤2说明")
    parser.add_argument("--step3", help="步骤3图片")
    parser.add_argument("--step3_label", help="步骤3说明")
    parser.add_argument("--step4", help="步骤4图片")
    parser.add_argument("--step4_label", help="步骤4说明")

    # 对比展示
    parser.add_argument("--left_image", help="左侧图片")
    parser.add_argument("--left_label", help="左侧标签（如 Before）")
    parser.add_argument("--right_image", help="右侧图片")
    parser.add_argument("--right_label", help="右侧标签（如 After）")

    return parser.parse_args()


def parse_image_content(value: str) -> dict:
    """解析图片内容参数"""
    if value.startswith("generate:"):
        return {"type": "generate", "prompt": value[9:]}
    elif value.startswith("http://") or value.startswith("https://"):
        return {"type": "url", "url": value}
    else:
        return {"type": "file", "path": value}


def build_content_from_args(args) -> dict:
    """从命令行参数构建内容字典"""
    content = {}

    # 文字类槽位
    text_fields = ["title", "tags", "summary", "footer", "subtitle", "name", "quote", "source",
                   "step1_label", "step2_label", "step3_label", "step4_label",
                   "left_label", "right_label"]
    for field in text_fields:
        value = getattr(args, field, None)
        if value:
            content[field] = value

    # 列表类槽位
    if args.points:
        content["points"] = args.points

    # 图片类槽位
    image_fields = ["image", "main_image", "avatar", "step1", "step2", "step3", "step4",
                    "left_image", "right_image"]
    for field in image_fields:
        value = getattr(args, field, None)
        if value:
            content[field] = parse_image_content(value)

    return content


def main():
    args = parse_args()

    # 列出模板
    if args.list:
        templates = list_templates()
        print("可用模板:")
        for t in templates:
            print(f"  - {t}")
        return

    # 预览模板
    if args.preview:
        preview_template(args.preview)
        return

    # 使用配置文件
    if args.config:
        with open(args.config, "r", encoding="utf-8") as f:
            config = json.load(f)
        template = config.get("template", "knowledge")
        content = config.get("content", {})
        output = args.output or config.get("output", "cover.png")
        render_template(template, content, output)
        return

    # 使用命令行参数
    if args.template:
        if not args.output:
            print("错误: 请指定输出文件 (-o)")
            sys.exit(1)

        content = build_content_from_args(args)
        render_template(args.template, content, args.output)
        return

    # 无操作
    print("请指定操作: --template, --config, --list, 或 --preview")
    print("使用 --help 查看帮助")


if __name__ == "__main__":
    main()
