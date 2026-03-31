#!/usr/bin/env python3
"""
视频章节导航条添加工具
为视频添加底部章节导航条，显示当前章节和进度
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Optional

class ChapterNavGenerator:
    """章节导航条生成器"""

    def __init__(self, video_path: str, chapters: List[Dict], output_path: str):
        self.video_path = Path(video_path)
        self.chapters = chapters
        self.output_path = Path(output_path)

        # 导航条样式配置
        self.nav_height = 80
        self.bg_opacity = 0.8
        self.progress_color = "4A90E2"
        self.text_color = "FFFFFF"
        self.font_size = 24
        self.position = "bottom"

        if not self.video_path.exists():
            raise FileNotFoundError(f"输入视频不存在: {self.video_path}")

    def get_video_info(self) -> Dict:
        """获取视频信息"""
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,duration',
            '-of', 'json',
            str(self.video_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        info = json.loads(result.stdout)

        stream = info['streams'][0]
        return {
            'width': int(stream['width']),
            'height': int(stream['height']),
            'duration': float(stream.get('duration', 0))
        }

    def generate_nav_overlay(self) -> str:
        """生成导航条overlay滤镜"""
        video_info = self.get_video_info()
        width = video_info['width']
        height = video_info['height']

        # 导航条位置
        if self.position == "bottom":
            nav_y = height - self.nav_height
        else:
            nav_y = 0

        # 构建滤镜链
        filters = []

        # 背景矩形
        bg_filter = (
            f"color=c=black@{self.bg_opacity}:s={width}x{self.nav_height}[bg];"
            f"[0:v][bg]overlay=x=0:y={nav_y}[v1]"
        )
        filters.append(bg_filter)

        # 为每个章节添加进度条和文字
        for i, chapter in enumerate(self.chapters):
            start_time = chapter['start']
            end_time = chapter['end']
            duration = end_time - start_time
            title = chapter['title']

            # 进度条
            progress_x = int((start_time / video_info['duration']) * width)
            progress_width = int((duration / video_info['duration']) * width)

            progress_filter = (
                f"[v{i+1}]drawbox="
                f"x={progress_x}:y={nav_y+self.nav_height-5}:"
                f"w={progress_width}:h=5:"
                f"c=#{self.progress_color}@1:"
                f"t=fill:"
                f"enable='between(t,{start_time},{end_time})'[v{i+2}]"
            )
            filters.append(progress_filter)

            # 章节标题
            text_x = progress_x + 10
            text_y = nav_y + (self.nav_height // 2) - (self.font_size // 2)

            text_filter = (
                f"[v{i+2}]drawtext="
                f"text='{title}':"
                f"x={text_x}:y={text_y}:"
                f"fontcolor=#{self.text_color}:"
                f"fontsize={self.font_size}:"
                f"enable='between(t,{start_time},{end_time})'[v{i+3}]"
            )
            filters.append(text_filter)

        # 组合所有滤镜
        filter_complex = ";".join(filters)

        # 最终输出
        filter_complex = filter_complex.replace(f"[v{len(self.chapters)*2+1}]", "")

        return filter_complex

    def add_navigation(self):
        """添加导航条到视频"""
        print(f"正在为视频添加章节导航条...")
        print(f"输入: {self.video_path}")
        print(f"输出: {self.output_path}")
        print(f"章节数: {len(self.chapters)}")

        # 生成滤镜
        filter_complex = self.generate_nav_overlay()

        # FFmpeg命令
        cmd = [
            'ffmpeg', '-y',
            '-i', str(self.video_path),
            '-filter_complex', filter_complex,
            '-c:a', 'copy',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            str(self.output_path)
        ]

        # 执行命令
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        # 实时输出进度
        for line in process.stderr:
            if 'time=' in line:
                time_str = line.split('time=')[1].split()[0]
                print(f"\r处理进度: {time_str}", end='', flush=True)

        process.wait()
        print("\n")

        if process.returncode == 0:
            print(f"✅ 导航条添加成功！")
            print(f"输出文件: {self.output_path}")

            # 显示文件大小
            size_mb = self.output_path.stat().st_size / (1024 * 1024)
            print(f"文件大小: {size_mb:.2f} MB")
        else:
            print(f"❌ 处理失败，错误代码: {process.returncode}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='为视频添加章节导航条')
    parser.add_argument('--input', '-i', required=True, help='输入视频文件')
    parser.add_argument('--output', '-o', required=True, help='输出视频文件')
    parser.add_argument('--chapters', '-c', required=True, help='章节配置JSON文件')
    parser.add_argument('--style', default='default',
                       choices=['default', 'minimal', 'full'],
                       help='导航条样式')
    parser.add_argument('--position', default='bottom',
                       choices=['top', 'bottom'],
                       help='导航条位置')

    args = parser.parse_args()

    # 读取章节配置
    with open(args.chapters, 'r', encoding='utf-8') as f:
        config = json.load(f)
        chapters = config.get('chapters', [])

    if not chapters:
        print("错误：章节配置为空")
        sys.exit(1)

    # 创建生成器
    generator = ChapterNavGenerator(
        video_path=args.input,
        chapters=chapters,
        output_path=args.output
    )

    # 设置样式
    if args.style == 'minimal':
        generator.nav_height = 60
        generator.font_size = 20
    elif args.style == 'full':
        generator.nav_height = 100
        generator.font_size = 28

    generator.position = args.position

    # 添加导航条
    generator.add_navigation()

if __name__ == '__main__':
    main()