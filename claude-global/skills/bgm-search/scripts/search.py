#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command-line tool for searching background music on Freesound.

Usage:
    python search.py "happy upbeat music"
    python search.py "electronic" --tag music --duration 60-180
    python search.py "ambient relaxing" --download --output ./bgm/
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 计算项目根目录和默认输出目录
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent  # .claude/skills/bgm-search/scripts -> project root
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output" / "bgm-search"

from freesound_client import (
    search_sounds,
    format_search_results,
    download_preview,
    get_mood_keywords,
    get_style_keywords,
    get_scene_keywords,
    MOOD_KEYWORDS,
    STYLE_KEYWORDS,
    SCENE_KEYWORDS,
)


def parse_duration(duration_str: str) -> tuple:
    """Parse duration string like '60-180' into (min, max) tuple."""
    if not duration_str:
        return None, None

    if "-" in duration_str:
        parts = duration_str.split("-")
        try:
            min_dur = float(parts[0]) if parts[0] else None
            max_dur = float(parts[1]) if parts[1] else None
            return min_dur, max_dur
        except ValueError:
            return None, None
    else:
        try:
            dur = float(duration_str)
            return dur, dur
        except ValueError:
            return None, None


def main():
    parser = argparse.ArgumentParser(
        description="Search for free background music on Freesound",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python search.py "happy upbeat"
  python search.py "electronic ambient" --tag music
  python search.py "cinematic epic" --duration 60-300 --limit 10
  python search.py "relaxing piano" --download --output ./bgm/

Mood presets: happy, sad, tense, relaxing, romantic, inspiring, energetic, mysterious
Style presets: electronic, epic, jazz, classical, rock, ambient, lofi, corporate
Scene presets: intro, background, game, nature, city, action

Use --list-presets to see all available keyword presets.
        """
    )

    parser.add_argument(
        "query",
        nargs="?",
        help="Search query (keywords in English)"
    )
    parser.add_argument(
        "--tag", "-t",
        help="Filter by tag (e.g., music, ambient, loop)"
    )
    parser.add_argument(
        "--duration", "-d",
        help="Duration range in seconds (e.g., 60-180)"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=5,
        help="Number of results to return (default: 5)"
    )
    parser.add_argument(
        "--sort", "-s",
        choices=["rating", "downloads", "duration", "created"],
        default="rating",
        help="Sort order (default: rating)"
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download the first result"
    )
    parser.add_argument(
        "--download-all",
        action="store_true",
        help="Download all results"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help=f"Output directory for downloads (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--mood",
        help="Search by mood preset (happy, sad, tense, relaxing, etc.)"
    )
    parser.add_argument(
        "--style",
        help="Search by style preset (electronic, epic, jazz, etc.)"
    )
    parser.add_argument(
        "--scene",
        help="Search by scene preset (intro, background, game, etc.)"
    )
    parser.add_argument(
        "--list-presets",
        action="store_true",
        help="List all available keyword presets"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )

    args = parser.parse_args()

    # List presets and exit
    if args.list_presets:
        print("=== Mood Presets ===")
        for name, keywords in MOOD_KEYWORDS.items():
            print(f"  {name}: {keywords}")
        print("\n=== Style Presets ===")
        for name, keywords in STYLE_KEYWORDS.items():
            print(f"  {name}: {keywords}")
        print("\n=== Scene Presets ===")
        for name, keywords in SCENE_KEYWORDS.items():
            print(f"  {name}: {keywords}")
        return 0

    # Build query from presets and/or direct query
    query_parts = []

    if args.query:
        query_parts.append(args.query)

    if args.mood:
        query_parts.append(get_mood_keywords(args.mood))

    if args.style:
        query_parts.append(get_style_keywords(args.style))

    if args.scene:
        query_parts.append(get_scene_keywords(args.scene))

    if not query_parts:
        print("Error: No search query provided. Use --help for usage.", file=sys.stderr)
        return 1

    query = " ".join(query_parts)

    # Parse duration
    duration_min, duration_max = parse_duration(args.duration)

    # Map sort options
    sort_map = {
        "rating": "rating_desc",
        "downloads": "downloads_desc",
        "duration": "duration_desc",
        "created": "created_desc",
    }
    sort_order = sort_map.get(args.sort, "rating_desc")

    print(f"Searching for: {query}")
    if args.tag:
        print(f"Tag filter: {args.tag}")
    if args.duration:
        print(f"Duration: {args.duration} seconds")
    print()

    try:
        results = search_sounds(
            query=query,
            tag=args.tag,
            duration_min=duration_min,
            duration_max=duration_max,
            limit=args.limit,
            sort=sort_order,
        )

        if args.json:
            import json
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print(format_search_results(results))

        # Download if requested
        sounds = results.get("results", [])
        if sounds and (args.download or args.download_all):
            output_dir = args.output if args.output else str(DEFAULT_OUTPUT_DIR)
            os.makedirs(output_dir, exist_ok=True)

            to_download = sounds if args.download_all else sounds[:1]

            for sound in to_download:
                name = sound.get("name", "unknown").replace("/", "_").replace("\\", "_")
                sound_id = sound.get("id", "unknown")
                previews = sound.get("previews", {})
                preview_url = previews.get("preview-hq-mp3", previews.get("preview-lq-mp3"))

                if preview_url:
                    # Clean filename
                    safe_name = "".join(c for c in name if c.isalnum() or c in " -_").strip()
                    output_path = os.path.join(output_dir, f"{sound_id}_{safe_name}.mp3")

                    print(f"Downloading: {name}...")
                    try:
                        download_preview(preview_url, output_path)
                        print(f"Saved to: {output_path}")
                    except Exception as e:
                        print(f"Download failed: {e}", file=sys.stderr)

        return 0

    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"Search error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
