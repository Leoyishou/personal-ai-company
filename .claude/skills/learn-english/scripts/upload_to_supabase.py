#!/usr/bin/env python3
"""
上传增强音频和 LRC 到 Supabase

功能：
1. 上传音频文件到 Supabase Storage
2. 读取 LRC 内容
3. 插入 audio_lessons 记录

使用方法：
    python upload_to_supabase.py \
        --dir ~/Library/Mobile\ Documents/com~apple~CloudDocs/practiceEngListen/260202_ai_bottlenecks \
        --title "AI Bottlenecks" \
        --url "https://youtube.com/xxx"
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(Path.home() / ".claude" / "secrets.env")

from supabase import create_client, Client


# Supabase 配置 (AI50 项目)
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://ebgmmkaxuhawfrwryzia.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

# Storage bucket 名称
AUDIO_BUCKET = "audio-lessons"


def get_supabase_client() -> Client:
    """获取 Supabase 客户端"""
    if not SUPABASE_KEY:
        raise ValueError("SUPABASE_ANON_KEY 或 SUPABASE_KEY 未设置")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_audio_to_storage(supabase: Client, audio_path: Path, folder_name: str) -> str:
    """
    上传音频文件到 Supabase Storage

    Args:
        supabase: Supabase 客户端
        audio_path: 本地音频文件路径
        folder_name: 存储目录名（如 260202_ai_bottlenecks）

    Returns:
        存储路径 (如 audio-lessons/260202_ai_bottlenecks/enhanced.mp3)
    """
    storage_path = f"{folder_name}/{audio_path.name}"

    with open(audio_path, "rb") as f:
        audio_data = f.read()

    # 上传到 Storage
    result = supabase.storage.from_(AUDIO_BUCKET).upload(
        storage_path,
        audio_data,
        file_options={"content-type": "audio/mpeg"}
    )

    print(f"  Uploaded: {storage_path}")
    return f"{AUDIO_BUCKET}/{storage_path}"


def read_lrc_content(lrc_path: Path) -> str:
    """读取 LRC 文件内容"""
    with open(lrc_path, "r", encoding="utf-8") as f:
        return f.read()


def get_audio_duration_seconds(audio_path: Path) -> int:
    """获取音频时长（秒）"""
    import subprocess
    result = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_path)
    ], capture_output=True, text=True)

    if result.returncode == 0:
        return int(float(result.stdout.strip()))
    return 0


def insert_audio_lesson(
    supabase: Client,
    title: str,
    audio_path: str,
    lrc_content: str,
    source_url: str = "",
    duration_seconds: int = 0,
    user_id: str = ""
) -> dict:
    """
    插入 audio_lessons 记录

    Args:
        supabase: Supabase 客户端
        title: 课程标题
        audio_path: Storage 中的音频路径
        lrc_content: LRC 歌词内容
        source_url: 原始视频 URL
        duration_seconds: 音频时长（秒）
        user_id: 用户 ID

    Returns:
        插入的记录
    """
    data = {
        "title": title,
        "audio_path": audio_path,
        "lrc_content": lrc_content,
        "source_url": source_url,
        "duration_seconds": duration_seconds,
        "created_at": datetime.now().isoformat(),
    }

    if user_id:
        data["user_id"] = user_id

    result = supabase.table("audio_lessons").insert(data).execute()
    return result.data[0] if result.data else {}


def upload_lesson(
    lesson_dir: str,
    title: str = "",
    source_url: str = "",
    user_id: str = ""
) -> dict:
    """
    上传增强音频课程到 Supabase

    Args:
        lesson_dir: 课程目录（包含 enhanced.mp3 和 enhanced.lrc）
        title: 课程标题（默认使用目录名）
        source_url: 原始视频 URL
        user_id: 用户 ID

    Returns:
        插入的记录
    """
    lesson_path = Path(lesson_dir)

    if not lesson_path.exists():
        raise FileNotFoundError(f"目录不存在: {lesson_dir}")

    audio_file = lesson_path / "enhanced.mp3"
    lrc_file = lesson_path / "enhanced.lrc"

    if not audio_file.exists():
        raise FileNotFoundError(f"音频文件不存在: {audio_file}")

    if not lrc_file.exists():
        raise FileNotFoundError(f"LRC 文件不存在: {lrc_file}")

    # 使用目录名作为默认标题
    folder_name = lesson_path.name
    if not title:
        # 从目录名提取标题（去掉日期前缀）
        title = folder_name.split("_", 1)[1] if "_" in folder_name else folder_name
        title = title.replace("_", " ").title()

    print(f"Uploading lesson: {title}")
    print(f"  Directory: {lesson_dir}")

    # 1. 获取 Supabase 客户端
    supabase = get_supabase_client()

    # 2. 上传音频到 Storage
    print("  Uploading audio to Storage...")
    audio_storage_path = upload_audio_to_storage(supabase, audio_file, folder_name)

    # 3. 读取 LRC 内容
    print("  Reading LRC content...")
    lrc_content = read_lrc_content(lrc_file)

    # 4. 获取音频时长
    duration = get_audio_duration_seconds(audio_file)
    print(f"  Duration: {duration}s")

    # 5. 插入数据库记录
    print("  Inserting database record...")
    record = insert_audio_lesson(
        supabase,
        title=title,
        audio_path=audio_storage_path,
        lrc_content=lrc_content,
        source_url=source_url,
        duration_seconds=duration,
        user_id=user_id
    )

    print(f"\nUpload complete!")
    print(f"  Record ID: {record.get('id', 'N/A')}")
    print(f"  Audio path: {audio_storage_path}")
    print(f"  LRC lines: {len(lrc_content.splitlines())}")

    return record


def main():
    parser = argparse.ArgumentParser(description="上传增强音频到 Supabase")
    parser.add_argument("--dir", "-d", required=True, help="课程目录")
    parser.add_argument("--title", "-t", help="课程标题（默认使用目录名）")
    parser.add_argument("--url", "-u", help="原始视频 URL")
    parser.add_argument("--user-id", help="用户 ID")

    args = parser.parse_args()

    try:
        record = upload_lesson(
            lesson_dir=args.dir,
            title=args.title,
            source_url=args.url or "",
            user_id=args.user_id or ""
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
