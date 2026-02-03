#!/usr/bin/env python3
"""
统一画图入口 - 整合搜索、下载、生图的完整流程

这是 api-draw 能力的 Python 入口，供 Canvas 等 UI 调用。
封装了 CC 调用 skill 时的完整逻辑：
1. 根据风格加载 prompt 模板
2. 如果是肖像类，搜索人物照片
3. 下载参考图
4. 调用 nanobanana 生成

用法:
    python draw_with_search.py "峰哥" --style 线刻肖像 --subject 峰哥
    python draw_with_search.py "5个AI工具推荐" --style 手绘白板 --subject AI工具
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# 当前脚本目录
SCRIPT_DIR = Path(__file__).parent
TEMPLATES_DIR = SCRIPT_DIR.parent / "templates"


def load_template_prompt(style: str, user_content: str, target_size: tuple = None) -> str:
    """
    根据风格加载模板并构建完整 prompt。
    """
    size_hint = ""
    if target_size:
        w, h = target_size
        from math import gcd
        g = gcd(w, h)
        ratio = f"{w//g}:{h//g}"
        size_hint = f"\n图片尺寸要求：{w}×{h}像素，{ratio}比例。"

    if style == "手绘白板":
        return f"""生成一张小红书风格封面图，
手绘白板草图风格，视觉笔记美学，
极简线条艺术，粗黑马克笔线条，蓝色高亮点缀，
简单涂鸦图标，流程图结构，箭头连接各元素，
纯白背景，干净专业，商业概念可视化。
{size_hint}

{user_content}

风格：Excalidraw 手绘美学，无阴影，无渐变，无3D效果，略带不规则的草图线条。
VERY simple doodle, NOT realistic, childlike simple sketch, crude imperfect lines,
like drawn with marker on whiteboard, wobbly hand-drawn style."""

    elif style in ("木刻肖像", "线刻肖像"):
        return f"""将这张照片中的人物转换为黑白线刻版画风格，但衣服保留彩色：
- 人物面部用精细的黑白平行线条刻画，木刻版画质感
- 衣服保留鲜艳的彩色，形成视觉焦点
- 背景极简：纯白色或浅米色，干净留白
- 黑白线条人像 + 彩色衣服的对比，吸引眼球
- 整体风格：简约现代的线刻插画
{size_hint}

{user_content}"""

    elif style == "板书插画":
        return f"""生成一张小红书风格封面图，
白板教学插画风格，像老师在白板上讲课，
干净的白色背景，黑色手写字体，
搭配简单的卡通人物或涂鸦图标，
有重点标记（橙色/黄色高亮），
适合财经理财、知识科普、教育课程、技术教程。
{size_hint}

{user_content}"""

    elif style == "学霸笔记":
        return f"""生成一张小红书风格封面图，
学霸笔记风格，方格纸背景，
手写字体配合荧光笔标记，
适合知识图解、原理拆解、错误vs正确对比。
{size_hint}

{user_content}"""

    elif style == "对比漫画":
        return f"""生成一张小红书风格封面图，
上下两格漫画风格，简单线条人物，
适合对比、反差、吐槽、生活感悟。
{size_hint}

{user_content}"""

    else:
        if size_hint:
            return f"{user_content}{size_hint}"
        return user_content


def search_person_photo(query: str) -> str | None:
    """
    使用 firecrawl 搜索人物照片。
    返回照片 URL，如果失败返回 None。
    """
    try:
        # 尝试使用 firecrawl MCP（通过 HTTP 调用）
        # 这里直接用 requests 调用 firecrawl 的搜索 API
        import requests

        # firecrawl API (需要 FIRECRAWL_API_KEY)
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            print("Warning: FIRECRAWL_API_KEY not set, skipping photo search")
            return None

        response = requests.post(
            "https://api.firecrawl.dev/v1/search",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "query": f"{query} 照片 portrait",
                "limit": 5,
            },
            timeout=30,
        )

        if response.status_code != 200:
            print(f"Firecrawl search failed: {response.status_code}")
            return None

        data = response.json()
        results = data.get("data", [])

        # 找到第一个有图片的结果
        for result in results:
            # 检查是否有图片 URL
            if "image" in result:
                return result["image"]
            if "ogImage" in result:
                return result["ogImage"]

        print("No images found in search results")
        return None

    except Exception as e:
        print(f"Photo search failed: {e}")
        return None


def download_image(url: str) -> str | None:
    """
    下载图片到临时文件。
    返回本地文件路径，如果失败返回 None。
    """
    try:
        import requests
        from datetime import datetime

        response = requests.get(url, timeout=30, stream=True)
        if response.status_code != 200:
            print(f"Image download failed: {response.status_code}")
            return None

        # 保存到临时文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = url.split(".")[-1].split("?")[0]
        if ext not in ("jpg", "jpeg", "png", "webp"):
            ext = "jpg"

        temp_path = f"/tmp/ref_photo_{timestamp}.{ext}"
        with open(temp_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Downloaded reference photo: {temp_path}")
        return temp_path

    except Exception as e:
        print(f"Image download failed: {e}")
        return None


def generate_image(
    prompt: str,
    style: str,
    subject: str,
    ref_image: str = None,
    target_size: tuple = None,
) -> str | None:
    """
    调用 nanobanana_draw.py 生成图片。
    返回生成的图片路径。
    """
    # 构建完整 prompt
    full_prompt = load_template_prompt(style, prompt, target_size)

    # 构建命令
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "nanobanana_draw.py"),
        full_prompt,
        "--style", style,
        "--subject", subject,
    ]

    if ref_image:
        cmd.extend(["--image", ref_image])

    print(f"Generating image with style: {style}")
    print(f"Reference image: {ref_image or 'None'}")

    # 执行
    result = subprocess.run(
        cmd,
        cwd=str(SCRIPT_DIR),
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        print(f"Generation failed: {result.stderr}")
        return None

    # 找到生成的图片
    import glob
    output_dir = os.path.expanduser("~/.claude/Nanobanana-draw-图片")
    pattern = os.path.join(output_dir, f"*{style}*{subject}*.png")
    files = glob.glob(pattern)

    if not files:
        pattern = os.path.join(output_dir, "*.png")
        files = glob.glob(pattern)

    if files:
        return max(files, key=os.path.getctime)

    return None


def main():
    parser = argparse.ArgumentParser(description="统一画图入口 - 整合搜索、下载、生图")
    parser.add_argument("prompt", help="画图描述/人物名")
    parser.add_argument("--style", default="其他", help="风格 (手绘白板/线刻肖像/板书插画/学霸笔记/对比漫画)")
    parser.add_argument("--subject", default="未命名", help="主题（用于文件命名）")
    parser.add_argument("--ref-image", help="手动指定参考图片路径")
    parser.add_argument("--width", type=int, default=972, help="目标宽度")
    parser.add_argument("--height", type=int, default=806, help="目标高度")
    parser.add_argument("--no-search", action="store_true", help="禁用自动搜索")

    args = parser.parse_args()

    ref_image = args.ref_image

    # 如果是肖像类且没有提供参考图，尝试搜索
    if args.style in ("线刻肖像", "木刻肖像") and not ref_image and not args.no_search:
        print(f"Searching for photos of: {args.prompt}")
        photo_url = search_person_photo(args.prompt)
        if photo_url:
            ref_image = download_image(photo_url)

    # 生成图片
    output = generate_image(
        prompt=args.prompt,
        style=args.style,
        subject=args.subject,
        ref_image=ref_image,
        target_size=(args.width, args.height),
    )

    if output:
        print(f"\n生成成功: {output}")
        return 0
    else:
        print("\n生成失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
