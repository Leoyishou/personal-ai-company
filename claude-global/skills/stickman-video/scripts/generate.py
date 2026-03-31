#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stickman Video Generator - Main orchestration script.

This script coordinates the entire video generation workflow:
1. Generate script from topic
2. TTS voice synthesis
3. Search and download background music
4. Generate stickman illustrations
5. Compose final video with Remotion
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# Add parent directories to path
SCRIPT_DIR = Path(__file__).parent.absolute()
SKILL_DIR = SCRIPT_DIR.parent
SKILLS_ROOT = SKILL_DIR.parent
PROJECT_ROOT = SKILLS_ROOT.parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output" / "stickman-video"

sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SKILLS_ROOT / "volcengine-tts" / "scripts"))
sys.path.insert(0, str(SKILLS_ROOT / "bgm-search" / "scripts"))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass


def generate_script(topic: str, duration: int = 30, num_segments: int = None) -> dict:
    """
    Generate a video script template based on the topic.

    This generates a template structure. Claude will fill in the actual content,
    and should determine the number of scenes based on semantic meaning, not
    arbitrary limits.

    Args:
        topic: The video topic
        duration: Target duration in seconds
        num_segments: Number of text segments (auto-calculated if not provided)

    Returns:
        dict: Script template with title, segments and scenes
    """
    if num_segments is None:
        # Estimate ~4 seconds per segment
        num_segments = max(3, duration // 4)

    script = {
        "title": topic,
        "target_duration": duration,
        "segments": [],
        "scenes": [],  # 语义场景（图片）列表 - 数量由语义决定，不硬性限制
        "style": {
            "illustration": "black and white stick figure, minimalist line drawing, white background",
            "subtitle": "large Chinese text at bottom, black color",
            "mood": "relaxing"
        }
    }

    # 创建解说词段落模板
    for i in range(num_segments):
        script["segments"].append({
            "id": i + 1,
            "text": f"[第{i+1}段解说词 - 请根据主题'{topic}'填写]",
            "duration": 4,
            "scene_id": 1  # Claude 需要根据语义分配场景ID
        })

    # 场景模板示例 - Claude 应根据内容语义自主决定场景数量
    # 不设硬性限制，有多少个语义主题就生成多少张图
    script["scenes"].append({
        "id": 1,
        "description": "[场景语义描述 - 这个阶段讲什么主题]",
        "image_prompt": "[画面描述 - 火柴人在做什么]",
        "image_file": "scene_01.png"
    })

    return script


def save_script(script: dict, output_dir: Path) -> Path:
    """Save script to JSON file."""
    script_path = output_dir / "script.json"
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)
    return script_path


def load_script(script_path: Path) -> dict:
    """Load script from JSON file."""
    with open(script_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_tts(script: dict, output_dir: Path, voice: str = "yangguang") -> list:
    """
    Generate TTS audio for each segment.

    Args:
        script: The video script
        output_dir: Directory to save audio files
        voice: TTS voice ID

    Returns:
        list: Paths to generated audio files
    """
    audio_dir = output_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    tts_script = SKILLS_ROOT / "volcengine-tts" / "scripts" / "tts.py"
    audio_files = []

    for segment in script["segments"]:
        segment_id = segment["id"]
        text = segment["text"]
        output_path = audio_dir / f"segment_{segment_id:02d}.mp3"

        print(f"Generating TTS for segment {segment_id}: {text[:30]}...")

        cmd = [
            sys.executable, str(tts_script),
            text,
            "--voice", voice,
            "--output", str(output_path)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            audio_files.append(output_path)
            print(f"  Saved to: {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"  TTS failed: {e.stderr}")
            audio_files.append(None)

    return audio_files


def search_bgm(mood: str, output_dir: Path, duration: int = 60) -> Path:
    """
    Search and download background music.

    Args:
        mood: Music mood (happy, relaxing, etc.)
        output_dir: Directory to save BGM
        duration: Minimum duration in seconds

    Returns:
        Path: Path to downloaded BGM file
    """
    bgm_dir = output_dir / "bgm"
    bgm_dir.mkdir(parents=True, exist_ok=True)

    search_script = SKILLS_ROOT / "bgm-search" / "scripts" / "search.py"

    print(f"Searching for {mood} background music...")

    cmd = [
        sys.executable, str(search_script),
        "--mood", mood,
        "--tag", "music",
        "--duration", f"{duration}-300",
        "--limit", "1",
        "--download",
        "--output", str(bgm_dir)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)

        # Find downloaded file
        for f in bgm_dir.iterdir():
            if f.suffix == ".mp3":
                return f
    except subprocess.CalledProcessError as e:
        print(f"BGM search failed: {e.stderr}")

    return None


def generate_image_prompts(script: dict) -> dict:
    """
    Generate image prompts for each scene (not each segment).

    Args:
        script: The video script

    Returns:
        dict: Updated script with image prompts for scenes
    """
    base_style = script.get("style", {}).get(
        "illustration",
        "black and white stick figure, minimalist line drawing, white background"
    )

    # 为每个场景生成图片提示词
    for scene in script.get("scenes", []):
        description = scene.get("image_prompt", scene.get("description", ""))
        prompt = f"Simple {base_style}, {description}, cute cartoon style, hand-drawn sketch look, no text"
        scene["full_prompt"] = prompt

    return script


def create_remotion_config(script: dict, output_dir: Path, audio_files: list, bgm_path: Path) -> Path:
    """
    Create Remotion configuration file.

    Args:
        script: The video script
        output_dir: Output directory
        audio_files: List of audio file paths
        bgm_path: Path to background music

    Returns:
        Path: Path to config file
    """
    # 构建场景图片映射
    scene_images = {}
    for scene in script.get("scenes", []):
        scene_id = scene["id"]
        image_file = scene.get("image_file", f"scene_{scene_id:02d}.png")
        scene_images[scene_id] = str(output_dir / "images" / image_file)

    config = {
        "title": script["title"],
        "width": 960,
        "height": 720,
        "fps": 30,
        "scenes": script.get("scenes", []),  # 场景列表
        "segments": [],
        "bgm": str(bgm_path) if bgm_path else None
    }

    for i, segment in enumerate(script["segments"]):
        scene_id = segment.get("scene_id", 1)
        segment_config = {
            "id": segment["id"],
            "text": segment["text"],
            "duration": segment.get("duration", 4),
            "audio": str(audio_files[i]) if i < len(audio_files) and audio_files[i] else None,
            "scene_id": scene_id,
            "image": scene_images.get(scene_id, str(output_dir / "images" / "scene_01.png"))
        }
        config["segments"].append(segment_config)

    config_path = output_dir / "remotion_config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    return config_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate stickman-style short videos",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--topic", "-t",
        required=True,
        help="Video topic"
    )
    parser.add_argument(
        "--duration", "-d",
        type=int,
        default=30,
        help="Target duration in seconds (default: 30)"
    )
    parser.add_argument(
        "--voice", "-v",
        default="yangguang",
        help="TTS voice (default: yangguang)"
    )
    parser.add_argument(
        "--mood", "-m",
        default="relaxing",
        help="BGM mood (default: relaxing)"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--script-only",
        action="store_true",
        help="Only generate script template, don't process further"
    )
    parser.add_argument(
        "--from-script",
        help="Use existing script file instead of generating new one"
    )
    parser.add_argument(
        "--skip-tts",
        action="store_true",
        help="Skip TTS generation"
    )
    parser.add_argument(
        "--skip-bgm",
        action="store_true",
        help="Skip BGM search"
    )
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="Skip image generation"
    )

    args = parser.parse_args()

    # Setup output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_output = Path(args.output) if args.output else DEFAULT_OUTPUT_DIR
    output_dir = base_output / f"{timestamp}_{args.topic[:20]}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Stickman Video Generator ===")
    print(f"Topic: {args.topic}")
    print(f"Duration: {args.duration}s")
    print(f"Output: {output_dir}")
    print()

    # Step 1: Generate or load script
    if args.from_script:
        print("Loading existing script...")
        script = load_script(Path(args.from_script))
    else:
        print("Generating script template...")
        script = generate_script(args.topic, args.duration)
        script = generate_image_prompts(script)

    script_path = save_script(script, output_dir)
    print(f"Script saved to: {script_path}")

    if args.script_only:
        print("\n[Script-only mode] Please edit the script and run again with --from-script")
        print(f"\nEdit: {script_path}")
        return 0

    # Step 2: Generate TTS
    audio_files = []
    if not args.skip_tts:
        print("\n--- Generating TTS Audio ---")
        audio_files = generate_tts(script, output_dir, args.voice)

    # Step 3: Search BGM
    bgm_path = None
    if not args.skip_bgm:
        print("\n--- Searching Background Music ---")
        bgm_path = search_bgm(args.mood, output_dir, args.duration)
        if bgm_path:
            print(f"BGM downloaded: {bgm_path}")

    # Step 4: Create image directory and prompts
    if not args.skip_images:
        print("\n--- Image Generation ---")
        images_dir = output_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        num_scenes = len(script.get("scenes", []))
        num_segments = len(script.get("segments", []))
        print(f"共 {num_segments} 段解说词，分为 {num_scenes} 个语义场景")
        print("每个场景生成一张图片，多段解说词共享同一张图：\n")

        for scene in script.get("scenes", []):
            # 找出属于这个场景的所有段落
            related_segments = [s for s in script["segments"] if s.get("scene_id") == scene["id"]]
            segment_ids = [str(s["id"]) for s in related_segments]

            print(f"场景 {scene['id']} (段落 {', '.join(segment_ids)}):")
            print(f"  语义: {scene.get('description', '')}")
            print(f"  Prompt: {scene.get('full_prompt', scene.get('image_prompt', ''))}")
            print(f"  保存为: {images_dir / scene.get('image_file', f'scene_{scene[\"id\"]:02d}.png')}")
            print()

    # Step 5: Create Remotion config
    print("\n--- Creating Remotion Config ---")
    config_path = create_remotion_config(script, output_dir, audio_files, bgm_path)
    print(f"Remotion config saved to: {config_path}")

    # Summary
    print("\n=== Generation Complete ===")
    print(f"Output directory: {output_dir}")
    print(f"Script: {script_path}")
    print(f"Audio files: {len([a for a in audio_files if a])} generated")
    print(f"BGM: {'Downloaded' if bgm_path else 'Not downloaded'}")
    print("\nNext steps:")
    print("1. Review and edit script.json if needed")
    print("2. Generate stickman images using the prompts")
    print("3. Run Remotion to compose the final video")

    return 0


if __name__ == "__main__":
    sys.exit(main())
