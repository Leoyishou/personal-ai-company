#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Digital Human Video Generation using Volcengine OmniHuman1.5 API.

IMPORTANT: The API requires URL parameters (image_url, audio_url) instead of base64.
Local files must first be uploaded to a public URL (e.g., Supabase Storage).

Usage:
    python digital_human.py --image-url "https://..." --audio-url "https://..."
    python digital_human.py --image avatar.png --audio speech.mp3  # Requires supabase-upload skill
"""

import os
import sys
import time
import json
import base64
import hashlib
import hmac
import argparse
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from urllib.parse import urlencode

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    load_dotenv(dotenv_path, override=False)
    project_root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".env"))
    if os.path.exists(project_root_env):
        load_dotenv(project_root_env, override=False)


SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output" / "digital-human"

# OmniHuman1.5 req_key
REQ_KEY = "jimeng_realman_avatar_picture_omni_v15"

# API Configuration
API_HOST = "visual.volcengineapi.com"
API_REGION = "cn-north-1"
API_SERVICE = "cv"
API_VERSION = "2022-08-31"


def resolve_credentials() -> Tuple[str, str]:
    """Get credentials from environment."""
    ak = os.getenv("VOLC_ACCESSKEY")
    sk = os.getenv("VOLC_SECRETKEY")
    if not ak or not sk:
        raise ValueError("Missing VOLC_ACCESSKEY or VOLC_SECRETKEY")
    return ak, sk


def hmac_sha256(key: bytes, msg: str) -> bytes:
    """HMAC-SHA256 signature."""
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def hash_sha256(content: str) -> str:
    """SHA256 hash."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def sign_request(
    method: str,
    action: str,
    body: dict,
    ak: str,
    sk: str,
) -> Dict[str, str]:
    """
    Sign request using Volcengine V4 signature.
    Returns headers dict with authorization.
    """
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y%m%dT%H%M%SZ")
    short_date = now.strftime("%Y%m%d")

    # Query parameters
    query_params = {
        "Action": action,
        "Version": API_VERSION,
    }
    query_string = urlencode(sorted(query_params.items()))

    # Body
    body_str = json.dumps(body)
    body_hash = hash_sha256(body_str)

    # Canonical request
    canonical_uri = "/"
    canonical_headers = f"content-type:application/json\nhost:{API_HOST}\nx-content-sha256:{body_hash}\nx-date:{date_str}\n"
    signed_headers = "content-type;host;x-content-sha256;x-date"

    canonical_request = f"{method}\n{canonical_uri}\n{query_string}\n{canonical_headers}\n{signed_headers}\n{body_hash}"

    # String to sign
    credential_scope = f"{short_date}/{API_REGION}/{API_SERVICE}/request"
    string_to_sign = f"HMAC-SHA256\n{date_str}\n{credential_scope}\n{hash_sha256(canonical_request)}"

    # Signing key
    k_date = hmac_sha256(sk.encode("utf-8"), short_date)
    k_region = hmac_sha256(k_date, API_REGION)
    k_service = hmac_sha256(k_region, API_SERVICE)
    k_signing = hmac_sha256(k_service, "request")

    # Signature
    signature = hmac.new(k_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    # Authorization header
    authorization = f"HMAC-SHA256 Credential={ak}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"

    headers = {
        "Content-Type": "application/json",
        "Host": API_HOST,
        "X-Date": date_str,
        "X-Content-Sha256": body_hash,
        "Authorization": authorization,
    }

    return headers, query_string


def api_call(action: str, body: dict) -> Dict[str, Any]:
    """Make API call with V4 signature."""
    ak, sk = resolve_credentials()
    headers, query_string = sign_request("POST", action, body, ak, sk)

    url = f"https://{API_HOST}/?{query_string}"
    body_str = json.dumps(body)

    response = requests.post(url, headers=headers, data=body_str, timeout=60)

    try:
        return response.json()
    except:
        return {"code": -1, "message": response.text}


def file_to_base64(file_path: str) -> str:
    """Convert file to base64 string."""
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def url_to_base64(url: str) -> str:
    """Download file from URL and convert to base64."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return base64.b64encode(response.content).decode("utf-8")


def submit_task(
    image_url: str,
    audio_url: str,
    prompt: Optional[str] = None,
    callback_url: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> Dict[str, Any]:
    """Submit digital human video generation task using URLs."""
    body = {
        "req_key": REQ_KEY,
        "image_url": image_url,
        "audio_url": audio_url,
    }

    if prompt:
        body["prompt"] = prompt

    if callback_url:
        body["callback_url"] = callback_url

    # 输出视频尺寸控制
    if width:
        body["width"] = width
    if height:
        body["height"] = height

    return api_call("CVSubmitTask", body)


def query_task(task_id: str) -> Dict[str, Any]:
    """Query task status. NOTE: Can only be called ONCE per task!"""
    body = {
        "req_key": REQ_KEY,
        "task_id": task_id,
    }

    return api_call("CVGetResult", body)


def download_video(url: str, output_path: str) -> str:
    """Download video from URL."""
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate digital human video using OmniHuman1.5",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
IMPORTANT: The API requires URL parameters. Local files must be uploaded first.

Example with URLs:
  python digital_human.py --image-url "https://..." --audio-url "https://..."

Example with local files (requires supabase-upload skill configured):
  python digital_human.py --image avatar.png --audio speech.mp3
"""
    )

    parser.add_argument("--image", help="Local image file path (will be uploaded to Supabase)")
    parser.add_argument("--image-url", help="Image URL (preferred)")
    parser.add_argument("--audio", help="Local audio file path (will be uploaded to Supabase)")
    parser.add_argument("--audio-url", help="Audio URL (preferred)")
    parser.add_argument("--prompt", "-p", help="Optional prompt for motion/expression")
    parser.add_argument("--output", "-o", help="Output video path")
    parser.add_argument("--width", type=int, help="Output video width (e.g., 1080 for vertical video)")
    parser.add_argument("--height", type=int, help="Output video height (e.g., 1920 for vertical video)")
    parser.add_argument("--vertical", action="store_true", help="Shortcut for --width 1080 --height 1920 (9:16 vertical)")
    parser.add_argument("--callback-url", help="Webhook URL to receive completed video")
    parser.add_argument("--no-download", action="store_true", help="Don't download, just print URL")
    parser.add_argument("--no-query", action="store_true", help="Don't query status, just submit")
    parser.add_argument("--poll-interval", type=int, default=30, help="Polling interval in seconds (default: 30)")
    parser.add_argument("--max-polls", type=int, default=20, help="Max polling attempts (default: 20)")
    parser.add_argument("--debug", action="store_true", help="Save debug info to files")

    args = parser.parse_args()

    # Validate inputs
    if not args.image and not args.image_url:
        parser.error("Either --image or --image-url is required")
    if not args.audio and not args.audio_url:
        parser.error("Either --audio or --audio-url is required")

    # Get image URL
    if args.image_url:
        image_url = args.image_url
        print(f"Using image URL: {image_url}")
    else:
        print("Uploading image to Supabase...")
        try:
            # Import supabase upload
            supabase_script = Path(__file__).parent.parent.parent / "supabase-upload" / "scripts"
            sys.path.insert(0, str(supabase_script))
            from supabase_client import upload_file
            image_url = upload_file(args.image, folder="digital-human")
            print(f"Image uploaded: {image_url}")
        except Exception as e:
            print(f"Error uploading image: {e}", file=sys.stderr)
            print("Please use --image-url with a pre-uploaded URL", file=sys.stderr)
            return 1

    # Get audio URL
    if args.audio_url:
        audio_url = args.audio_url
        print(f"Using audio URL: {audio_url}")
    else:
        print("Uploading audio to Supabase...")
        try:
            supabase_script = Path(__file__).parent.parent.parent / "supabase-upload" / "scripts"
            sys.path.insert(0, str(supabase_script))
            from supabase_client import upload_file
            audio_url = upload_file(args.audio, folder="digital-human")
            print(f"Audio uploaded: {audio_url}")
        except Exception as e:
            print(f"Error uploading audio: {e}", file=sys.stderr)
            print("Please use --audio-url with a pre-uploaded URL", file=sys.stderr)
            return 1

    # 处理尺寸参数
    width = args.width
    height = args.height
    if args.vertical:
        width = width or 1080
        height = height or 1920
        print(f"Using vertical video format: {width}x{height}")
    elif width or height:
        print(f"Output size: {width or 'auto'}x{height or 'auto'}")

    # Submit task
    print("Submitting task...")
    try:
        response = submit_task(image_url, audio_url, args.prompt, args.callback_url, width, height)
    except Exception as e:
        print(f"Error submitting task: {e}", file=sys.stderr)
        return 1

    # Debug output
    if args.debug:
        os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
        debug_path = DEFAULT_OUTPUT_DIR / "debug_submit_response.json"
        with open(debug_path, "w", encoding="utf-8") as f:
            json.dump(response, f, ensure_ascii=False, indent=2)
        print(f"[DEBUG] Response saved to: {debug_path}")

    if response.get("code") != 10000:
        print(f"Error: {response.get('message', 'Unknown error')}", file=sys.stderr)
        print(f"Code: {response.get('code')}", file=sys.stderr)
        return 1

    data = response.get("data", {})
    task_id = data.get("task_id")

    # Check if video is already ready in submit response
    video_url = data.get("video_url") or data.get("output_url")
    if video_url:
        print(f"Video ready immediately: {video_url}")
        if not args.no_download:
            if args.output:
                output_path = args.output
            else:
                os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(DEFAULT_OUTPUT_DIR / f"digital_human_{timestamp}.mp4")
            print(f"Downloading to: {output_path}")
            download_video(video_url, output_path)
            print(f"Saved: {output_path}")
        return 0

    if not task_id:
        print(f"Error: No task_id in response", file=sys.stderr)
        return 1

    print(f"Task submitted: {task_id}")

    if args.callback_url:
        print(f"Callback URL: {args.callback_url}")
        print("Result will be POSTed to your callback URL when ready.")
        return 0

    if args.no_query:
        print("Task submitted. Use --callback-url to receive results.")
        return 0

    # Poll for results
    print(f"Polling for results (interval: {args.poll_interval}s, max: {args.max_polls} attempts)...")

    for attempt in range(1, args.max_polls + 1):
        print(f"\nQuery #{attempt}...")
        query_response = query_task(task_id)

        if args.debug:
            debug_path = DEFAULT_OUTPUT_DIR / f"debug_query_response_{attempt}.json"
            with open(debug_path, "w", encoding="utf-8") as f:
                json.dump(query_response, f, ensure_ascii=False, indent=2)

        if query_response.get("code") != 10000:
            print(f"Query error: {query_response.get('message')}", file=sys.stderr)
            return 1

        query_data = query_response.get("data") or {}
        status = query_data.get("status", "unknown")
        video_url = query_data.get("video_url", "")

        print(f"Status: {status}")

        if status == "done" and video_url:
            print(f"\nVideo URL: {video_url}")
            if not args.no_download:
                if args.output:
                    output_path = args.output
                else:
                    os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_path = str(DEFAULT_OUTPUT_DIR / f"digital_human_{timestamp}.mp4")

                print(f"Downloading to: {output_path}")
                download_video(video_url, output_path)
                print(f"Saved: {output_path}")
            return 0

        if status in ("failed", "error"):
            print(f"Task failed with status: {status}", file=sys.stderr)
            return 1

        if attempt < args.max_polls:
            print(f"Waiting {args.poll_interval}s...")
            time.sleep(args.poll_interval)

    print(f"\nMax polling attempts ({args.max_polls}) reached. Task may still be processing.")
    print("Use --callback-url for long-running tasks.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
