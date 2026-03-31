#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Downloader
Downloads videos from YouTube, Bilibili and other platforms with customizable quality and format options.
"""

import argparse
import sys
import subprocess
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    # Ensure stdout/stderr use UTF-8 where possible without detaching
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')


def safe_print(text):
    """Print text safely, handling encoding errors."""
    try:
        print(text)
    except UnicodeEncodeError:
        try:
            print(text.encode('utf-8', errors='ignore').decode('utf-8'))
        except Exception:
            safe_text = text.encode('ascii', 'ignore').decode('ascii')
            print(safe_text)


def is_bilibili_url(url):
    """Check if the URL is from Bilibili."""
    if not url:
        return False
    try:
        parsed_url = urlparse(url)
        bilibili_pattern = r'(.*\.)?bilibili\.com$'
        return bool(re.search(bilibili_pattern, parsed_url.netloc))
    except Exception:
        return False


def format_bilibili_url(url):
    """
    Clean Bilibili URL by keeping only essential parameters.
    """
    if not is_bilibili_url(url):
        return url
    
    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        # Construct base URL (without query params)
        base_path = parsed.path.rstrip('/')
        formatted_url = f"{parsed.scheme}://{parsed.netloc}{base_path}"
        
        # Keep 'p' parameter if present
        if 'p' in query_params:
            pid = query_params['p'][0]
            formatted_url += f"?p={pid}"
            
        return formatted_url
    except Exception:
        return url


def check_yt_dlp():
    """Check if yt-dlp is installed, install if not."""
    # Add user's local bin to PATH
    local_bin = str(Path.home() / ".local" / "bin")
    if local_bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{local_bin}:{os.environ.get('PATH', '')}"
    
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
        return
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    safe_print("yt-dlp not found. Installing...")
    try:
        # Try with --break-system-packages first (for newer pip versions)
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--break-system-packages", "yt-dlp"], 
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, result.args)
    except subprocess.CalledProcessError:
        # Fall back to regular install if --break-system-packages is not supported
        subprocess.run([sys.executable, "-m", "pip", "install", "--user", "yt-dlp"], check=True)
    
    safe_print("yt-dlp installed successfully!")


def get_video_info(url):
    """Get information about the video without downloading."""
    try:
        # Use a simpler call for info extraction
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-playlist", url],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return None
    except Exception:
        return None


def download_video_internal(url, output_path, quality, format_type, audio_only, is_retry=False):
    """
    Internal function to download video with specific URL.
    Returns (success, error_message)
    """
    # Check platform type
    is_bilibili = is_bilibili_url(url)
    
    # Build command
    cmd = ["yt-dlp"]
    
    # --- Bilibili-specific optimizations ---
    if is_bilibili:
        if not is_retry:
            safe_print("[Bilibili detected] Using optimized download strategy...")
        
        # Add required headers for Bilibili
        cmd.extend([
            "--add-header", "Referer:https://www.bilibili.com/",
            "--add-header", "User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ])
        
        # Force HTML5 mode to handle WBI signature
        cmd.extend(["--extractor-args", "bilibili:videomode=html5"])

    # ----------------------------------------
    
    if audio_only:
        cmd.extend([
            "-x",  # Extract audio
            "--audio-format", "mp3",
            "--audio-quality", "0",  # Best quality
        ])
    else:
        # Video quality settings
        if quality == "best":
            format_string = "bestvideo+bestaudio/best"
        elif quality == "worst":
            format_string = "worstvideo+worstaudio/worst"
        else:
            # Specific resolution (e.g., 1080p, 720p)
            height = quality.replace("p", "")
            format_string = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
        
        cmd.extend([
            "-f", format_string,
            "--merge-output-format", format_type,
        ])
    
    # Output template - use Path for cross-platform compatibility
    output_template = str(Path(output_path) / "%(title)s.%(ext)s")
    cmd.extend([
        "-o", output_template,
        "--no-playlist",  # Don't download playlists by default
    ])
    
    cmd.append(url)
    
    if not is_retry:
        safe_print(f"Downloading from: {url}")
        if is_bilibili:
            safe_print(f"Platform: Bilibili (with anti-412 protection)")
        safe_print(f"Quality: {quality}")
        safe_print(f"Format: {'mp3 (audio only)' if audio_only else format_type}")
        safe_print(f"Output: {output_path}\n")
        
        # Get video info first
        info = get_video_info(url)
        if info:
            safe_print(f"Title: {info.get('title', 'Unknown')}")
            duration = info.get('duration', 0)
            if duration:
                try:
                    duration_val = float(duration)
                    minutes = int(duration_val // 60)
                    seconds = int(duration_val % 60)
                    safe_print(f"Duration: {minutes}:{seconds:02d}")
                except (ValueError, TypeError):
                    safe_print(f"Duration: {duration}")
            safe_print(f"Uploader: {info.get('uploader', 'Unknown')}\n")
        else:
            safe_print("Warning: Could not fetch video info")
            safe_print("Attempting to download anyway...\n")
        
        safe_print("Starting download...")
    
    # Download the video - do NOT capture output to avoid buffer/encoding issues during progress updates
    try:
        # We don't use capture_output=True here so the user can see progress
        subprocess.run(cmd, check=True)
        return (True, None)
    except subprocess.CalledProcessError as e:
        return (False, f"yt-dlp failed with exit code {e.returncode}")
    except Exception as e:
        return (False, str(e))


def download_video(url, output_path=None, quality="best", format_type="mp4", audio_only=False):
    """
    Download a video from YouTube, Bilibili or other platforms.
    
    Args:
        url: Video URL
        output_path: Directory to save the video (default: smart detection)
        quality: Quality setting (best, 1080p, 720p, 480p, 360p, worst)
        format_type: Output format (mp4, webm, mkv, etc.)
        audio_only: Download only audio (mp3)
    """
    check_yt_dlp()
    
    # Smart default output path detection
    if output_path is None:
        cwd = Path.cwd()
        
        # Try to detect if we are inside a .claude directory structure
        claude_base = None
        for parent in [cwd] + list(cwd.parents):
            if parent.name == ".claude":
                claude_base = parent.parent
                break
        
        if claude_base:
            # If we found a .claude directory, we use its parent as the base
            # Prefer 'Downloads' folder if it exists in the base directory
            downloads_dir = claude_base
            if downloads_dir.exists() and downloads_dir.is_dir():
                output_path = str(downloads_dir)
            else:
                output_path = str(claude_base)
        else:
            # If no .claude found, use the current working directory
            output_path = str(cwd)
    
    # Ensure output directory exists and use absolute path
    output_path = os.path.abspath(output_path)
    os.makedirs(output_path, exist_ok=True)
    
    is_bilibili = is_bilibili_url(url)
    
    if is_bilibili:
        url = format_bilibili_url(url)

    try:
        # Attempt download
        success, error_msg = download_video_internal(
            url, output_path, quality, format_type, audio_only, is_retry=False
        )
        
        if success:
            safe_print("\n[SUCCESS] Download complete!")
            safe_print(f"Saved to: {output_path}")
            return True
        
        # If still failed, show error message
        safe_print("\n[ERROR] Error downloading video:")
        if error_msg:
            safe_print(error_msg)
        
        # Provide helpful hints for common errors
        if is_bilibili and error_msg:
            if "412" in error_msg:
                safe_print("\n[HINT] Bilibili 412 error. Try waiting a few minutes or using a different IP.")
            elif "403" in error_msg or "forbidden" in error_msg.lower():
                safe_print("\n[HINT] Access forbidden. The video might be restricted or login required.")
        
        return False
            
    except Exception as e:
        safe_print(f"\n[ERROR] Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download videos from YouTube, Bilibili and other platforms with customizable quality and format"
    )
    parser.add_argument("url", help="Video URL")
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output directory (default: current directory)"
    )
    parser.add_argument(
        "-q", "--quality",
        default="best",
        choices=["best", "1080p", "720p", "480p", "360p", "worst"],
        help="Video quality (default: best)"
    )
    parser.add_argument(
        "-f", "--format",
        default="mp4",
        choices=["mp4", "webm", "mkv"],
        help="Video format (default: mp4)"
    )
    parser.add_argument(
        "-a", "--audio-only",
        action="store_true",
        help="Download only audio as MP3"
    )
    
    args = parser.parse_args()
    
    success = download_video(
        url=args.url,
        output_path=args.output,
        quality=args.quality,
        format_type=args.format,
        audio_only=args.audio_only
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
