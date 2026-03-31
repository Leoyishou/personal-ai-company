#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESL Comic Video Generator - Wrapper Script

Simplified wrapper for make_comic_video.py with sensible defaults.
Supports text-only input with automatic TTS generation (Edge TTS or ElevenLabs).

Usage:
    # Simplest - just provide text (auto-detects best TTS)
    python make_video.py --story story.txt

    # With speed control for ESL learners
    python make_video.py --story story.txt --speed 0.75

    # With existing audio
    python make_video.py --audio story.mp3
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path

# Paths
MAIN_SCRIPT = Path("/Users/liuyishou/usr/projects/inbox/ESL-video/make_comic_video.py")
PROJECT_DIR = MAIN_SCRIPT.parent
SKILL_DIR = Path(__file__).resolve().parent.parent

# Known .env locations to search for API keys
ENV_SEARCH_PATHS = [
    PROJECT_DIR / ".env",
    SKILL_DIR / ".env",
    Path.home() / ".claude/skills/nanobanana-draw/.env",
    Path.home() / ".env",
]

# TTS Configuration
DEFAULT_EDGE_VOICE = "en-US-GuyNeural"  # Changed to Guy for clearer pronunciation
DEFAULT_EDGE_RATE = "-10%"
DEFAULT_ELEVENLABS_VOICE = "kPzsL2i3teMYv0FxEYQ6"
DEFAULT_ELEVENLABS_MODEL = "eleven_multilingual_v2"


def load_env_file(env_path: Path) -> dict[str, str]:
    """Load environment variables from a .env file."""
    env_vars = {}
    if env_path.exists():
        try:
            content = env_path.read_text()
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip().strip('"').strip("'")
        except Exception:
            pass
    return env_vars


def find_api_key(key_name: str) -> str | None:
    """Search for API key in environment or .env files."""
    # Check environment first
    if os.getenv(key_name):
        return os.getenv(key_name)

    # Search known .env locations
    for env_path in ENV_SEARCH_PATHS:
        env_vars = load_env_file(env_path)
        if key_name in env_vars and env_vars[key_name]:
            return env_vars[key_name]
    return None


def find_elevenlabs_voice() -> str | None:
    """Search for default ElevenLabs voice ID in .env files."""
    for env_path in ENV_SEARCH_PATHS:
        env_vars = load_env_file(env_path)
        if "ELEVENLABS_VOICE_ID" in env_vars:
            return env_vars["ELEVENLABS_VOICE_ID"]
    return None


def ensure_env_file():
    """Ensure .env file exists in project directory with API key."""
    project_env = PROJECT_DIR / ".env"

    if project_env.exists():
        content = project_env.read_text()
        if "OPENROUTER_API_KEY=" in content:
            return True

    api_key = find_api_key("OPENROUTER_API_KEY")
    if api_key:
        for env_path in ENV_SEARCH_PATHS[1:]:
            if env_path.exists():
                shutil.copy(env_path, project_env)
                print(f"Copied .env from {env_path}")
                return True

        project_env.write_text(f"OPENROUTER_API_KEY={api_key}\n")
        print(f"Created .env with API key")
        return True

    return False


def check_and_install_edge_tts():
    """Check if edge-tts is installed, install if not."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import edge_tts"],
            capture_output=True
        )
        if result.returncode == 0:
            return True
    except Exception:
        pass

    print("Installing edge-tts for TTS generation...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "edge-tts", "-q"],
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        print("Warning: Failed to install edge-tts", file=sys.stderr)
        return False


def generate_edge_tts(text: str, output_path: Path, voice: str, rate: str) -> bool:
    """Generate TTS audio using Edge TTS."""
    if not check_and_install_edge_tts():
        return False

    print(f"Generating TTS audio with Edge TTS voice: {voice}...")
    try:
        cmd = [
            "edge-tts",
            "--voice", voice,
            "--text", text,
            "--write-media", str(output_path),
            f"--rate={rate}"
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"TTS audio saved to: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error generating TTS: {e.stderr.decode() if e.stderr else str(e)}", file=sys.stderr)
        return False


def generate_elevenlabs_tts(
    text: str,
    output_path: Path,
    api_key: str,
    voice_id: str = DEFAULT_ELEVENLABS_VOICE,
    model_id: str = DEFAULT_ELEVENLABS_MODEL,
) -> bool:
    """Generate TTS audio using ElevenLabs API."""
    print(f"Generating TTS audio with ElevenLabs voice: {voice_id}...")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key,
    }

    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }

    try:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=120) as response:
            audio_data = response.read()

        output_path.write_bytes(audio_data)
        print(f"TTS audio saved to: {output_path}")
        return True

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else str(e)
        print(f"ElevenLabs API error: {error_body}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error generating ElevenLabs TTS: {e}", file=sys.stderr)
        return False


def adjust_video_speed(input_path: Path, output_path: Path, speed: float) -> bool:
    """Adjust video playback speed using ffmpeg."""
    if speed == 1.0:
        return True  # No adjustment needed

    print(f"Adjusting video speed to {speed}x...")

    # Calculate filter values
    # speed < 1 means slower, speed > 1 means faster
    video_pts = 1.0 / speed  # PTS multiplier for video
    audio_tempo = speed  # atempo value for audio

    # atempo only supports 0.5 to 2.0, chain multiple for extreme values
    atempo_filters = []
    remaining = audio_tempo
    while remaining < 0.5:
        atempo_filters.append("atempo=0.5")
        remaining /= 0.5
    while remaining > 2.0:
        atempo_filters.append("atempo=2.0")
        remaining /= 2.0
    atempo_filters.append(f"atempo={remaining}")
    atempo_chain = ",".join(atempo_filters)

    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-filter_complex",
            f"[0:v]setpts={video_pts}*PTS[v];[0:a]{atempo_chain}[a]",
            "-map", "[v]", "-map", "[a]",
            str(output_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"Speed-adjusted video saved to: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error adjusting video speed: {e.stderr.decode() if e.stderr else str(e)}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Generate comic-style video from story text/audio",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simplest usage - just provide text
  %(prog)s --story story.txt

  # Slow down for ESL learners (0.75x speed)
  %(prog)s --story story.txt --speed 0.75

  # With existing audio
  %(prog)s --audio lesson.mp3

  # Force use Edge TTS instead of ElevenLabs
  %(prog)s --story story.txt --tts edge
        """
    )

    # Input options
    input_group = parser.add_argument_group("Input (at least one required)")
    input_group.add_argument("--text", "-t", help="Story text directly (will generate TTS)")
    input_group.add_argument("--story", "-s", help="Story text file (txt/md)")
    input_group.add_argument("--audio", "-a", help="Input audio file (MP3)")

    # Output options
    output_group = parser.add_argument_group("Output")
    output_group.add_argument("--output", "-o", help="Output directory")
    output_group.add_argument("--name", "-n", help="Project name (used as prefix)")
    output_group.add_argument("--speed", type=float, default=1.0,
                             help="Video playback speed (e.g., 0.75 for slower, 1.25 for faster)")

    # TTS options
    tts_group = parser.add_argument_group("TTS Options")
    tts_group.add_argument("--tts", choices=["edge", "elevenlabs", "auto"], default="auto",
                          help="TTS engine: auto (prefer ElevenLabs), edge, or elevenlabs")
    tts_group.add_argument("--voice", "-v", help="Edge TTS voice")
    tts_group.add_argument("--rate", default=DEFAULT_EDGE_RATE, help="Edge TTS speech rate")
    tts_group.add_argument("--elevenlabs-key", help="ElevenLabs API key (reads from .env if not provided)")
    tts_group.add_argument("--elevenlabs-voice", help="ElevenLabs voice ID (reads from .env if not provided)")
    tts_group.add_argument("--elevenlabs-model", default=DEFAULT_ELEVENLABS_MODEL,
                          help="ElevenLabs model")

    # Feature toggles
    feature_group = parser.add_argument_group("Features")
    feature_group.add_argument("--no-images", action="store_true", help="Skip image generation")
    feature_group.add_argument("--no-subtitles", action="store_true", help="Skip subtitle burning")
    feature_group.add_argument("--no-polish", action="store_true", help="Skip audio polish")
    feature_group.add_argument("--no-keywords", action="store_true", help="Disable keyword highlighting")
    feature_group.add_argument("--motion", action="store_true", help="Enable pan/zoom motion effects")
    feature_group.add_argument("--moviepy", action="store_true", help="Use MoviePy renderer with page-flip")

    # Advanced
    adv_group = parser.add_argument_group("Advanced")
    adv_group.add_argument("--model", default="google/gemini-3-pro-image-preview", help="Image generation model")
    adv_group.add_argument("--seed", type=int, default=42, help="Random seed for consistency")
    adv_group.add_argument("--force", action="store_true", help="Force re-render existing segments")
    adv_group.add_argument("--dry-run", action="store_true", help="Print command without executing")

    args = parser.parse_args()

    # Validate input
    if not any([args.text, args.story, args.audio]):
        parser.error("At least one of --text, --story, or --audio is required")

    # Validate speed
    if args.speed <= 0 or args.speed > 2.0:
        parser.error("Speed must be between 0.1 and 2.0")

    # Determine project name
    if args.name:
        prefix = args.name
    elif args.audio:
        prefix = Path(args.audio).stem
    elif args.story:
        prefix = Path(args.story).stem
    else:
        prefix = "comic_video"

    # Determine output directory
    output_dir = Path(args.output).resolve() if args.output else (Path.cwd() / "output" / prefix)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Handle text input
    story_path = None
    story_text = None

    if args.text:
        story_text = args.text
        story_path = output_dir / "story.txt"
        story_path.write_text(story_text, encoding="utf-8")
        print(f"Story text saved to: {story_path}")
    elif args.story:
        story_path = Path(args.story).resolve()
        if not story_path.exists():
            print(f"Error: Story file not found: {story_path}", file=sys.stderr)
            sys.exit(1)
        story_text = story_path.read_text(encoding="utf-8").strip()

    # Determine TTS engine
    tts_engine = args.tts
    elevenlabs_key = args.elevenlabs_key or find_api_key("ELEVENLABS_API_KEY")
    elevenlabs_voice = args.elevenlabs_voice or find_elevenlabs_voice() or DEFAULT_ELEVENLABS_VOICE

    if tts_engine == "auto":
        # Prefer ElevenLabs if key is available
        if elevenlabs_key:
            tts_engine = "elevenlabs"
            print("Auto-detected ElevenLabs API key, using ElevenLabs TTS")
        else:
            tts_engine = "edge"
            print("No ElevenLabs API key found, using Edge TTS")

    # Handle audio input
    audio_path = None
    if args.audio:
        audio_path = Path(args.audio).resolve()
        if not audio_path.exists():
            print(f"Error: Audio file not found: {audio_path}", file=sys.stderr)
            sys.exit(1)
    elif story_text:
        # Generate TTS from story text
        audio_path = output_dir / "story.mp3"

        if tts_engine == "elevenlabs":
            if not elevenlabs_key:
                print("Error: ElevenLabs API key required. Set ELEVENLABS_API_KEY in .env", file=sys.stderr)
                sys.exit(1)

            if not generate_elevenlabs_tts(
                story_text,
                audio_path,
                elevenlabs_key,
                elevenlabs_voice,
                args.elevenlabs_model,
            ):
                print("ElevenLabs failed, falling back to Edge TTS...", file=sys.stderr)
                tts_engine = "edge"

        if tts_engine == "edge":
            voice = args.voice or DEFAULT_EDGE_VOICE
            if not generate_edge_tts(story_text, audio_path, voice, args.rate):
                print("Error: Failed to generate TTS audio", file=sys.stderr)
                sys.exit(1)
    else:
        print("Error: Need either --audio or text input (--text/--story) for TTS", file=sys.stderr)
        sys.exit(1)

    # Ensure OpenRouter API key is available
    if not ensure_env_file():
        print("Warning: OPENROUTER_API_KEY not found. Image generation may fail.", file=sys.stderr)

    # Build command
    cmd = [
        sys.executable,
        str(MAIN_SCRIPT),
        "--audio", str(audio_path),
        "--output-dir", str(output_dir),
        "--prefix", prefix,
        "--model", args.model,
        "--seed", str(args.seed),
    ]

    if story_path:
        cmd.extend(["--story", str(story_path)])

    # Feature flags
    if not args.no_images:
        cmd.append("--generate-images")
    if not args.no_subtitles:
        cmd.append("--subtitles")
    if not args.no_polish:
        cmd.append("--audio-polish")
    if args.no_keywords:
        cmd.append("--no-highlight-keywords")
    if args.motion:
        cmd.append("--motion")
    if args.moviepy:
        cmd.extend(["--renderer", "moviepy"])
    if args.force:
        cmd.append("--force")

    # Execute or print
    print()
    print("=" * 60)
    print(f"Project: {prefix}")
    print(f"Output:  {output_dir}")
    print(f"Audio:   {audio_path}")
    print(f"TTS:     {tts_engine}")
    if args.speed != 1.0:
        print(f"Speed:   {args.speed}x")
    if story_path:
        print(f"Story:   {story_path}")
    print("=" * 60)
    print()

    if args.dry_run:
        print(f"Command: {' '.join(cmd)}")
        print("Dry run - not executing")
        return

    # Run the command
    try:
        subprocess.run(cmd, check=True)

        final_video = output_dir / "final" / f"{prefix}.mp4"

        # Apply speed adjustment if needed
        if args.speed != 1.0 and final_video.exists():
            speed_suffix = f"_{args.speed}x".replace(".", "_")
            slow_video = output_dir / "final" / f"{prefix}{speed_suffix}.mp4"
            if adjust_video_speed(final_video, slow_video, args.speed):
                final_video = slow_video

        print()
        print("=" * 60)
        print("Video generation completed!")
        print(f"Output: {final_video}")
        print("=" * 60)

        # Try to open the output
        if sys.platform == "darwin":
            print("\nOpening video...")
            subprocess.run(["open", str(final_video)], check=False)

    except subprocess.CalledProcessError as e:
        print(f"Error: Command failed with return code {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
