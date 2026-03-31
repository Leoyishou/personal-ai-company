#!/usr/bin/env python3
"""
NotebookLM Video Generator

Generate and download video overviews from NotebookLM notebooks.
Requires notebooklm skill to be authenticated first.
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

# Add notebooklm skill to path for browser utilities
NOTEBOOKLM_SKILL_DIR = Path.home() / ".claude" / "skills" / "notebooklm"
sys.path.insert(0, str(NOTEBOOKLM_SKILL_DIR / "scripts"))

try:
    from patchright.sync_api import sync_playwright
    from browser_utils import BrowserFactory
except ImportError:
    print("Error: notebooklm skill not found or not properly installed.")
    print("Please install notebooklm skill first:")
    print("  cd ~/.claude/skills/notebooklm && python scripts/run.py auth_manager.py setup")
    sys.exit(1)


def get_notebook_url_from_library(notebook_id: str) -> str | None:
    """Get notebook URL from notebooklm skill library."""
    library_file = NOTEBOOKLM_SKILL_DIR / "data" / "library.json"
    if not library_file.exists():
        return None

    try:
        with open(library_file, 'r') as f:
            library = json.load(f)

        for notebook in library.get('notebooks', []):
            if notebook.get('id') == notebook_id or notebook.get('name') == notebook_id:
                return notebook.get('url')
    except Exception as e:
        print(f"Warning: Could not read library: {e}")

    return None


def generate_video(
    notebook_url: str,
    output_dir: Path,
    wait_timeout_minutes: int = 15,
    headless: bool = True
) -> str | None:
    """
    Generate and download video from NotebookLM.

    Args:
        notebook_url: NotebookLM notebook URL
        output_dir: Directory to save the video
        wait_timeout_minutes: Max wait time for video generation
        headless: Run browser in headless mode

    Returns:
        Path to downloaded video, or None if failed
    """
    print(f"📚 Notebook: {notebook_url}")
    print(f"📁 Output: {output_dir}")
    print(f"⏱️  Timeout: {wait_timeout_minutes} minutes")
    print()

    playwright = None
    context = None

    try:
        playwright = sync_playwright().start()

        print("🔐 Launching browser with authenticated profile...")
        context = BrowserFactory.launch_persistent_context(
            playwright,
            headless=headless
        )

        page = context.new_page()

        # Navigate to notebook
        print("🚀 Opening notebook...")
        page.goto(notebook_url, wait_until="domcontentloaded", timeout=30000)

        try:
            page.wait_for_url(
                re.compile(r"^https://notebooklm\.google\.com/notebook/"),
                timeout=15000
            )
            print("✅ Notebook opened successfully")
        except:
            print("⚠️  Waiting for page load...")
            page.wait_for_timeout(5000)

        # Wait for page to stabilize
        page.wait_for_timeout(3000)

        # Get notebook title for filename
        try:
            title_elem = page.locator('h1, [class*="title"]').first
            notebook_title = title_elem.text_content().strip()[:50] if title_elem else "notebook"
        except:
            notebook_title = "notebook"

        print(f"📝 Notebook title: {notebook_title}")

        # Click Video button in Studio panel
        print("🎬 Looking for Video button...")

        video_clicked = False
        video_selectors = [
            '[aria-label*="Video"]',
            'button:has-text("Video")',
            'text="Video..."',
        ]

        for selector in video_selectors:
            try:
                btn = page.locator(selector).first
                if btn.is_visible(timeout=3000):
                    btn.click()
                    video_clicked = True
                    print(f"✅ Clicked Video button")
                    break
            except:
                continue

        if not video_clicked:
            print("❌ Could not find Video button")
            page.screenshot(path="/tmp/notebooklm-video-error.png", full_page=True)
            print("📸 Screenshot saved: /tmp/notebooklm-video-error.png")
            return None

        page.wait_for_timeout(2000)

        # Check if video already exists or needs generation
        print("🔍 Checking video status...")

        # Look for "Generate" button (video not yet created)
        try:
            generate_btn = page.locator('button:has-text("Generate")').first
            if generate_btn.is_visible(timeout=3000):
                generate_btn.click()
                print("✅ Started video generation")
        except:
            print("  Video may already be generating or ready...")

        page.wait_for_timeout(2000)

        # Wait for video generation
        print(f"⏳ Waiting for video generation (up to {wait_timeout_minutes} minutes)...")
        print("  Checking every 30 seconds...")

        check_interval = 30  # seconds
        total_checks = (wait_timeout_minutes * 60) // check_interval

        for i in range(total_checks):
            page.wait_for_timeout(check_interval * 1000)
            elapsed_min = ((i + 1) * check_interval) // 60
            elapsed_sec = ((i + 1) * check_interval) % 60

            # Check for download button (video ready)
            try:
                download_btn = page.locator('button:has-text("Download")').first
                if download_btn.is_visible(timeout=2000):
                    print(f"\n✅ Video ready! (took ~{elapsed_min}m {elapsed_sec}s)")

                    # Download the video
                    output_dir.mkdir(parents=True, exist_ok=True)
                    timestamp = int(time.time())
                    safe_title = re.sub(r'[^\w\-_]', '_', notebook_title)
                    filename = f"{safe_title}-{timestamp}.mp4"
                    output_path = output_dir / filename

                    with page.expect_download(timeout=120000) as download_info:
                        download_btn.click()
                        print("📥 Downloading video...")

                    download = download_info.value
                    download.save_as(str(output_path))
                    print(f"✅ Video saved: {output_path}")
                    return str(output_path)
            except:
                pass

            # Check if still generating
            generating = page.locator('text="Generating"').first
            try:
                if generating.is_visible(timeout=1000):
                    print(f"  Still generating... ({elapsed_min}m {elapsed_sec}s)")
                else:
                    # Not generating but no download button - check for errors
                    error = page.locator('text="error"').first
                    try:
                        if error.is_visible(timeout=500):
                            print(f"\n❌ Error during generation")
                            page.screenshot(path="/tmp/notebooklm-video-error.png", full_page=True)
                            return None
                    except:
                        print(f"  Checking... ({elapsed_min}m {elapsed_sec}s)")
            except:
                print(f"  Checking... ({elapsed_min}m {elapsed_sec}s)")

            # Take progress screenshot every 2 minutes
            if (i + 1) % 4 == 0:
                page.screenshot(path=f"/tmp/notebooklm-video-progress-{i}.png", full_page=True)

        print(f"\n⏰ Timeout after {wait_timeout_minutes} minutes")
        page.screenshot(path="/tmp/notebooklm-video-timeout.png", full_page=True)
        print("📸 Screenshot saved: /tmp/notebooklm-video-timeout.png")
        return None

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if context:
            context.close()
        if playwright:
            playwright.stop()


def main():
    parser = argparse.ArgumentParser(
        description="Generate video from NotebookLM notebook"
    )
    parser.add_argument(
        "--notebook-url",
        help="NotebookLM notebook URL"
    )
    parser.add_argument(
        "--notebook-id",
        help="Notebook ID from notebooklm skill library"
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path.home() / "Downloads"),
        help="Output directory for video (default: ~/Downloads)"
    )
    parser.add_argument(
        "--wait-timeout",
        type=int,
        default=15,
        help="Max wait time in minutes (default: 15)"
    )
    parser.add_argument(
        "--show-browser",
        action="store_true",
        help="Show browser window (for debugging)"
    )

    args = parser.parse_args()

    # Get notebook URL
    notebook_url = args.notebook_url

    if not notebook_url and args.notebook_id:
        notebook_url = get_notebook_url_from_library(args.notebook_id)
        if not notebook_url:
            print(f"❌ Notebook '{args.notebook_id}' not found in library")
            print("Available notebooks:")
            library_file = NOTEBOOKLM_SKILL_DIR / "data" / "library.json"
            if library_file.exists():
                with open(library_file, 'r') as f:
                    library = json.load(f)
                for nb in library.get('notebooks', []):
                    print(f"  - {nb.get('id')} ({nb.get('name')})")
            sys.exit(1)

    if not notebook_url:
        print("❌ Either --notebook-url or --notebook-id is required")
        parser.print_help()
        sys.exit(1)

    # Generate video
    output_dir = Path(args.output_dir)
    result = generate_video(
        notebook_url=notebook_url,
        output_dir=output_dir,
        wait_timeout_minutes=args.wait_timeout,
        headless=not args.show_browser
    )

    if result:
        print(f"\n🎉 Success! Video saved to: {result}")
        sys.exit(0)
    else:
        print("\n❌ Failed to generate video")
        sys.exit(1)


if __name__ == "__main__":
    main()
