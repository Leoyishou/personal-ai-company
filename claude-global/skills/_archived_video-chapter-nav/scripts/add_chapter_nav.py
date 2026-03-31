#!/usr/bin/env python3
"""
视频章节导航条生成工具

功能：
1. 在视频顶部添加章节导航条
2. 当前播放章节高亮显示（蓝色背景）
3. 支持自定义章节配置或从 JSON 文件读取

使用示例：
    python add_chapter_nav.py -i video.mp4 -o output.mp4 -c chapters.json
    python add_chapter_nav.py -i video.mp4 -o output.mp4 --chapters "0:00 引言,1:30 正文,5:00 总结"
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("错误：需要安装 Pillow 库")
    print("运行：pip install Pillow")
    sys.exit(1)


def get_video_info(video_path: str) -> dict:
    """获取视频信息（时长、分辨率）"""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"无法读取视频信息: {result.stderr}")

    data = json.loads(result.stdout)

    # 获取视频流信息
    video_stream = None
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            video_stream = stream
            break

    if not video_stream:
        raise RuntimeError("未找到视频流")

    duration = float(data.get("format", {}).get("duration", 0))
    width = int(video_stream.get("width", 1280))
    height = int(video_stream.get("height", 720))

    return {
        "duration": duration,
        "width": width,
        "height": height
    }


def parse_chapters_string(chapters_str: str, total_duration: float) -> list:
    """
    解析章节字符串
    格式: "0:00 引言,1:30 正文,5:00 总结"
    """
    chapters = []
    parts = [p.strip() for p in chapters_str.split(",")]

    for i, part in enumerate(parts):
        # 分离时间和标题
        tokens = part.split(maxsplit=1)
        if len(tokens) < 2:
            raise ValueError(f"章节格式错误: {part}")

        time_str, title = tokens

        # 解析时间 (支持 M:SS 或 H:MM:SS)
        time_parts = time_str.split(":")
        if len(time_parts) == 2:
            minutes, seconds = map(int, time_parts)
            start_sec = minutes * 60 + seconds
        elif len(time_parts) == 3:
            hours, minutes, seconds = map(int, time_parts)
            start_sec = hours * 3600 + minutes * 60 + seconds
        else:
            raise ValueError(f"时间格式错误: {time_str}")

        chapters.append({
            "index": i + 1,
            "start": time_str,
            "start_sec": start_sec,
            "start_ms": start_sec * 1000,
            "title": title
        })

    # 计算每个章节的结束时间
    for i, ch in enumerate(chapters):
        if i < len(chapters) - 1:
            ch["end_sec"] = chapters[i + 1]["start_sec"]
        else:
            ch["end_sec"] = total_duration

    return chapters


def load_chapters_from_json(json_path: str, total_duration: float) -> list:
    """从 JSON 文件加载章节配置"""
    with open(json_path, "r", encoding="utf-8") as f:
        chapters = json.load(f)

    # 确保有必要的字段
    for i, ch in enumerate(chapters):
        if "index" not in ch:
            ch["index"] = i + 1

        # 解析开始时间
        if "start_sec" not in ch:
            if "start_ms" in ch:
                ch["start_sec"] = ch["start_ms"] / 1000
            elif "start" in ch:
                time_parts = ch["start"].split(":")
                if len(time_parts) == 2:
                    m, s = map(int, time_parts)
                    ch["start_sec"] = m * 60 + s
                elif len(time_parts) == 3:
                    h, m, s = map(int, time_parts)
                    ch["start_sec"] = h * 3600 + m * 60 + s
            else:
                ch["start_sec"] = 0

    # 计算结束时间
    for i, ch in enumerate(chapters):
        if i < len(chapters) - 1:
            ch["end_sec"] = chapters[i + 1]["start_sec"]
        else:
            ch["end_sec"] = total_duration

    return chapters


def find_chinese_font() -> str:
    """查找可用的中文字体"""
    font_paths = [
        "/System/Library/Fonts/Hiragino Sans GB.ttc",  # macOS
        "/System/Library/Fonts/PingFang.ttc",          # macOS
        "/System/Library/Fonts/STHeiti Light.ttc",     # macOS
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Linux
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",     # Linux
        "C:\\Windows\\Fonts\\msyh.ttc",                # Windows 微软雅黑
        "C:\\Windows\\Fonts\\simhei.ttf",              # Windows 黑体
    ]

    for path in font_paths:
        if os.path.exists(path):
            return path

    return None


def create_nav_images(
    chapters: list,
    width: int,
    height: int = 50,
    output_dir: str = None
) -> list:
    """
    为每个章节生成导航条图片
    当前章节用蓝色高亮，其他章节灰色
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="chapter_nav_")

    os.makedirs(output_dir, exist_ok=True)

    # 查找中文字体
    font_path = find_chinese_font()
    if font_path:
        try:
            font = ImageFont.truetype(font_path, 20)
        except Exception:
            font = ImageFont.load_default()
    else:
        font = ImageFont.load_default()

    num_chapters = len(chapters)
    segment_width = width // num_chapters

    image_paths = []

    for active_idx in range(num_chapters):
        # 创建半透明黑色背景
        img = Image.new('RGBA', (width, height), (0, 0, 0, 180))
        draw = ImageDraw.Draw(img)

        for i, ch in enumerate(chapters):
            x = i * segment_width
            text = f"{ch['index']}.{ch['title']}"

            # 计算文字位置（居中）
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except AttributeError:
                # 旧版 Pillow 兼容
                text_width, text_height = draw.textsize(text, font=font)

            text_x = x + (segment_width - text_width) // 2
            text_y = (height - text_height) // 2

            if i == active_idx:
                # 当前章节：蓝色背景 + 白色文字
                draw.rectangle(
                    [(x, 0), (x + segment_width, height)],
                    fill=(59, 130, 246, 255)  # Tailwind blue-500
                )
                draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)
            else:
                # 其他章节：灰色文字
                draw.text((text_x, text_y), text, fill=(180, 180, 180, 255), font=font)

            # 绘制分隔线
            if i < num_chapters - 1:
                line_x = (i + 1) * segment_width
                draw.line(
                    [(line_x, 5), (line_x, height - 5)],
                    fill=(255, 255, 255, 80),
                    width=1
                )

        # 保存图片
        img_path = os.path.join(output_dir, f"nav_chapter_{active_idx + 1}.png")
        img.save(img_path)
        image_paths.append(img_path)
        print(f"生成导航条图片: {img_path}")

    return image_paths


def add_nav_to_video(
    input_video: str,
    output_video: str,
    chapters: list,
    nav_images: list,
    crf: int = 23,
    preset: str = "fast"
) -> bool:
    """使用 ffmpeg 将导航条叠加到视频"""

    # 构建 ffmpeg 命令
    cmd = ["ffmpeg", "-y", "-i", input_video]

    # 添加所有导航条图片作为输入
    for img_path in nav_images:
        cmd.extend(["-i", img_path])

    # 构建 filter_complex
    # 根据时间段切换不同的导航条图片
    filter_parts = []
    num_chapters = len(chapters)

    for i, ch in enumerate(chapters):
        start = ch["start_sec"]
        end = ch["end_sec"]

        if i == 0:
            # 第一个 overlay
            if i == num_chapters - 1:
                # 只有一个章节
                enable_expr = f"gte(t,{start})"
            else:
                enable_expr = f"between(t,{start},{end})"
            filter_parts.append(
                f"[0:v][{i + 1}:v]overlay=0:0:enable='{enable_expr}'[v{i + 1}]"
            )
        else:
            # 后续 overlay
            prev_out = f"v{i}"
            if i == num_chapters - 1:
                # 最后一个章节
                enable_expr = f"gte(t,{start})"
            else:
                enable_expr = f"between(t,{start},{end})"
            filter_parts.append(
                f"[{prev_out}][{i + 1}:v]overlay=0:0:enable='{enable_expr}'[v{i + 1}]"
            )

    # 最后的输出标签
    final_output = f"v{num_chapters}"
    filter_complex = ";".join(filter_parts)

    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", f"[{final_output}]",
        "-map", "0:a",
        "-c:a", "copy",
        "-c:v", "libx264",
        "-preset", preset,
        "-crf", str(crf),
        output_video
    ])

    print(f"\n执行 ffmpeg 命令...")
    print(f"输入: {input_video}")
    print(f"输出: {output_video}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"\n成功生成视频: {output_video}")
        return True
    else:
        print(f"\n生成失败:")
        print(result.stderr[-1000:])  # 显示最后 1000 字符的错误
        return False


def main():
    parser = argparse.ArgumentParser(
        description="为视频添加章节导航条",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从 JSON 文件读取章节
  python add_chapter_nav.py -i video.mp4 -o output.mp4 -c chapters.json

  # 直接指定章节
  python add_chapter_nav.py -i video.mp4 -o output.mp4 --chapters "0:00 引言,1:30 正文,5:00 总结"

章节 JSON 格式:
  [
    {"index": 1, "start": "0:00", "title": "引言"},
    {"index": 2, "start": "1:30", "title": "正文"},
    {"index": 3, "start": "5:00", "title": "总结"}
  ]
        """
    )

    parser.add_argument("-i", "--input", required=True, help="输入视频文件")
    parser.add_argument("-o", "--output", required=True, help="输出视频文件")
    parser.add_argument("-c", "--config", help="章节配置 JSON 文件")
    parser.add_argument("--chapters", help="章节字符串，格式: '0:00 标题1,1:30 标题2,...'")
    parser.add_argument("--nav-height", type=int, default=50, help="导航条高度（默认 50）")
    parser.add_argument("--crf", type=int, default=23, help="视频质量 CRF 值（默认 23，越小质量越高）")
    parser.add_argument("--preset", default="fast", help="编码速度预设（默认 fast）")
    parser.add_argument("--keep-images", action="store_true", help="保留生成的导航条图片")
    parser.add_argument("--image-dir", help="导航条图片保存目录")

    args = parser.parse_args()

    # 检查输入文件
    if not os.path.exists(args.input):
        print(f"错误：输入文件不存在: {args.input}")
        sys.exit(1)

    # 必须指定章节来源
    if not args.config and not args.chapters:
        print("错误：必须指定 --config 或 --chapters")
        sys.exit(1)

    # 获取视频信息
    print(f"分析视频: {args.input}")
    video_info = get_video_info(args.input)
    print(f"  分辨率: {video_info['width']}x{video_info['height']}")
    print(f"  时长: {video_info['duration']:.1f} 秒")

    # 加载章节配置
    if args.config:
        print(f"\n从配置文件加载章节: {args.config}")
        chapters = load_chapters_from_json(args.config, video_info["duration"])
    else:
        print(f"\n解析章节字符串...")
        chapters = parse_chapters_string(args.chapters, video_info["duration"])

    print(f"共 {len(chapters)} 个章节:")
    for ch in chapters:
        print(f"  {ch['index']}. {ch['title']} ({ch['start_sec']:.0f}s - {ch['end_sec']:.0f}s)")

    # 生成导航条图片
    print(f"\n生成导航条图片...")
    nav_images = create_nav_images(
        chapters=chapters,
        width=video_info["width"],
        height=args.nav_height,
        output_dir=args.image_dir
    )

    # 添加导航条到视频
    success = add_nav_to_video(
        input_video=args.input,
        output_video=args.output,
        chapters=chapters,
        nav_images=nav_images,
        crf=args.crf,
        preset=args.preset
    )

    # 清理临时文件
    if not args.keep_images and not args.image_dir:
        import shutil
        temp_dir = os.path.dirname(nav_images[0])
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("已清理临时文件")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
