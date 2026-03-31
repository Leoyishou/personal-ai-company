#!/usr/bin/env python3
"""
参考图获取工具 - 一键搜索、下载人物/产品照片

整合 firecrawl 图片搜索 + 智能选图 + 下载 + 可选抠图

用法:
    python fetch_reference.py --person "峰哥亡命天涯" -o /tmp/ref.jpg
    python fetch_reference.py --person "Elon Musk" -o /tmp/elon.jpg --remove-bg
    python fetch_reference.py --query "iPhone 15 product photo" -o /tmp/iphone.jpg
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests


def search_images(query: str, limit: int = 10) -> list[dict]:
    """
    使用 firecrawl API 搜索图片。

    Args:
        query: 搜索关键词
        limit: 返回结果数量

    Returns:
        图片结果列表，每项包含 url, width, height 等信息
    """
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        print("Error: FIRECRAWL_API_KEY not set")
        print("请在 ~/.claude/secrets.env 中配置 FIRECRAWL_API_KEY")
        sys.exit(1)

    try:
        response = requests.post(
            "https://api.firecrawl.dev/v1/search",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "query": query,
                "limit": limit,
                "sources": [{"type": "images"}],  # 只搜索图片
            },
            timeout=30,
        )

        if response.status_code != 200:
            print(f"Firecrawl search failed: {response.status_code}")
            print(response.text)
            return []

        data = response.json()
        results = data.get("data", [])

        # 提取图片信息
        images = []
        for r in results:
            img = {
                "url": r.get("url") or r.get("image"),
                "title": r.get("title", ""),
                "width": r.get("width", 0),
                "height": r.get("height", 0),
            }
            if img["url"]:
                images.append(img)

        return images

    except Exception as e:
        print(f"Search failed: {e}")
        return []


def search_web_for_images(query: str, limit: int = 5) -> list[dict]:
    """
    搜索网页并提取其中的图片（备选方案）。
    当图片搜索结果不理想时使用。
    """
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        return []

    try:
        response = requests.post(
            "https://api.firecrawl.dev/v1/search",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "query": f"{query} 照片 portrait photo",
                "limit": limit,
            },
            timeout=30,
        )

        if response.status_code != 200:
            return []

        data = response.json()
        results = data.get("data", [])

        images = []
        for r in results:
            # 从网页结果中提取图片
            for key in ["ogImage", "image", "thumbnail"]:
                if key in r and r[key]:
                    images.append({
                        "url": r[key],
                        "title": r.get("title", ""),
                        "source": r.get("url", ""),
                    })
                    break

        return images

    except Exception as e:
        print(f"Web search failed: {e}")
        return []


def get_image_size(url: str) -> tuple[int, int]:
    """
    尝试获取图片尺寸（不下载完整图片）。
    """
    try:
        # 先尝试 HEAD 请求获取 Content-Length
        response = requests.head(url, timeout=5, allow_redirects=True)
        content_length = int(response.headers.get("Content-Length", 0))

        # 大于 50KB 的图片通常质量较好
        if content_length > 50000:
            return (1000, 1000)  # 假设是高质量图片
        elif content_length > 10000:
            return (500, 500)
        else:
            return (100, 100)

    except Exception:
        return (0, 0)


def select_best_image(images: list[dict], prefer_large: bool = True) -> Optional[dict]:
    """
    从图片列表中选择最佳图片。

    优先级：
    1. 有明确尺寸信息的大图
    2. 文件大小较大的图片
    3. 来源可靠的图片
    """
    if not images:
        return None

    scored_images = []
    for img in images:
        score = 0
        url = img.get("url", "")

        # 基于尺寸评分
        w = img.get("width", 0)
        h = img.get("height", 0)
        if w and h:
            score += min(w * h / 100000, 100)  # 尺寸越大分越高

        # 基于文件格式评分
        url_lower = url.lower()
        if ".png" in url_lower:
            score += 10
        elif ".jpg" in url_lower or ".jpeg" in url_lower:
            score += 8
        elif ".webp" in url_lower:
            score += 5

        # 惩罚小图标
        if "icon" in url_lower or "thumb" in url_lower or "small" in url_lower:
            score -= 20
        if "avatar" in url_lower and w and w < 200:
            score -= 10

        # 奖励高分辨率关键词
        if "original" in url_lower or "large" in url_lower or "hd" in url_lower:
            score += 15

        scored_images.append((score, img))

    # 按分数排序
    scored_images.sort(key=lambda x: x[0], reverse=True)

    return scored_images[0][1] if scored_images else None


def download_image(url: str, output: str) -> str:
    """
    下载图片到指定路径。

    Args:
        url: 图片 URL
        output: 输出文件路径

    Returns:
        保存的文件路径
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, timeout=30, stream=True, headers=headers)

        if response.status_code != 200:
            raise Exception(f"Download failed: {response.status_code}")

        # 确定文件扩展名
        content_type = response.headers.get("Content-Type", "")
        if "png" in content_type:
            ext = ".png"
        elif "webp" in content_type:
            ext = ".webp"
        else:
            ext = ".jpg"

        # 如果输出路径没有扩展名，添加扩展名
        output_path = Path(output)
        if not output_path.suffix:
            output_path = output_path.with_suffix(ext)

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存文件
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Downloaded: {output_path}")
        return str(output_path)

    except Exception as e:
        print(f"Download failed: {e}")
        raise


def remove_background(image_path: str, output_path: str = None, mode: str = "ai") -> str:
    """
    调用 remove_bg.py 进行抠图。

    Args:
        image_path: 输入图片路径
        output_path: 输出路径（默认在原文件名后加 _nobg）
        mode: 抠图模式 (ai/white)

    Returns:
        抠图后的文件路径
    """
    if output_path is None:
        p = Path(image_path)
        output_path = str(p.parent / f"{p.stem}_nobg.png")

    script_dir = Path(__file__).parent
    remove_bg_script = script_dir / "remove_bg.py"

    cmd = [
        sys.executable,
        str(remove_bg_script),
        image_path,
        "-o", output_path,
        "--mode", mode,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Remove background failed: {result.stderr}")
        return image_path  # 失败时返回原图

    print(f"Background removed: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="参考图获取工具 - 一键搜索、下载人物/产品照片",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 搜索人物照片
  python fetch_reference.py --person "峰哥亡命天涯" -o /tmp/fengge.jpg

  # 搜索并抠图
  python fetch_reference.py --person "Elon Musk" -o /tmp/elon.png --remove-bg

  # 自定义搜索词
  python fetch_reference.py --query "iPhone 15 product white background" -o /tmp/iphone.jpg

  # 指定返回结果数量（选最优）
  python fetch_reference.py --person "张三丰" -o /tmp/zsf.jpg --limit 20
        """
    )

    # 搜索方式（二选一）
    search_group = parser.add_mutually_exclusive_group(required=True)
    search_group.add_argument("--person", help="人物名称（自动添加 '照片 portrait' 关键词）")
    search_group.add_argument("--query", help="自定义搜索词")

    # 输出
    parser.add_argument("-o", "--output", required=True, help="输出文件路径")

    # 选项
    parser.add_argument("--limit", type=int, default=10, help="搜索结果数量（默认10）")
    parser.add_argument("--remove-bg", action="store_true", help="下载后自动抠图")
    parser.add_argument("--bg-mode", choices=["ai", "white"], default="ai",
                       help="抠图模式: ai=智能抠图（默认）, white=白底抠图")
    parser.add_argument("--fallback-web", action="store_true",
                       help="图片搜索无结果时尝试网页搜索")
    parser.add_argument("--dry-run", action="store_true", help="只搜索不下载，打印结果")

    args = parser.parse_args()

    # 构建搜索词
    if args.person:
        query = f"{args.person} 照片 portrait face"
    else:
        query = args.query

    print(f"Searching: {query}")

    # 搜索图片
    images = search_images(query, args.limit)

    # 如果图片搜索无结果，尝试网页搜索
    if not images and (args.fallback_web or args.person):
        print("Image search returned no results, trying web search...")
        images = search_web_for_images(query, args.limit)

    if not images:
        print("No images found")
        sys.exit(1)

    print(f"Found {len(images)} images")

    # 选择最佳图片
    best = select_best_image(images)
    if not best:
        print("Could not select a suitable image")
        sys.exit(1)

    print(f"Selected: {best.get('title', 'Untitled')}")
    print(f"URL: {best['url']}")

    if args.dry_run:
        print("\n[Dry run] Would download to:", args.output)
        print("\nAll results:")
        for i, img in enumerate(images[:5], 1):
            print(f"  {i}. {img.get('url', 'N/A')}")
        sys.exit(0)

    # 下载
    output_path = download_image(best["url"], args.output)

    # 可选抠图
    if args.remove_bg:
        output_path = remove_background(output_path, mode=args.bg_mode)

    print(f"\nDone: {output_path}")
    return output_path


if __name__ == "__main__":
    main()
