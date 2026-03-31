#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Freesound API client for searching and downloading free music/sounds.

API Documentation: https://freesound.org/docs/api/
"""

import os
import json
import requests
from typing import Optional, List, Dict, Any
from urllib.parse import urlencode

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    # Try skill directory first
    dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    load_dotenv(dotenv_path, override=False)
    # Also try project root
    project_root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".env"))
    if os.path.exists(project_root_env):
        load_dotenv(project_root_env, override=False)


# API endpoints
BASE_URL = "https://freesound.org/apiv2"
SEARCH_URL = f"{BASE_URL}/search/text/"
SOUND_URL = f"{BASE_URL}/sounds"


def get_api_key() -> str:
    """Get API key from environment."""
    api_key = os.getenv("FREESOUND_API_KEY")
    if not api_key:
        raise ValueError(
            "Missing FREESOUND_API_KEY. Set it via environment variable.\n"
            "Get your API key from: https://freesound.org/apiv2/apply"
        )
    return api_key


def search_sounds(
    query: str,
    tag: Optional[str] = None,
    duration_min: Optional[float] = None,
    duration_max: Optional[float] = None,
    limit: int = 5,
    sort: str = "rating_desc",
    fields: str = "id,name,tags,description,duration,previews,license,username,download,avg_rating,num_downloads",
) -> Dict[str, Any]:
    """
    Search for sounds on Freesound.

    Args:
        query: Search query text
        tag: Filter by tag (e.g., "music", "ambient")
        duration_min: Minimum duration in seconds
        duration_max: Maximum duration in seconds
        limit: Number of results to return (max 150)
        sort: Sort order - rating_desc, downloads_desc, duration_desc, etc.
        fields: Comma-separated list of fields to return

    Returns:
        dict: Search results with count and sounds list
    """
    api_key = get_api_key()

    # Build filter string
    filters = []
    if tag:
        filters.append(f'tag:"{tag}"')
    if duration_min is not None:
        filters.append(f"duration:[{duration_min} TO *]")
    if duration_max is not None:
        filters.append(f"duration:[* TO {duration_max}]")
    if duration_min is not None and duration_max is not None:
        # Override with range filter
        filters = [f for f in filters if not f.startswith("duration:")]
        filters.append(f"duration:[{duration_min} TO {duration_max}]")

    params = {
        "token": api_key,
        "query": query,
        "page_size": min(limit, 150),
        "sort": sort,
        "fields": fields,
    }

    if filters:
        params["filter"] = " ".join(filters)

    try:
        response = requests.get(SEARCH_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        raise RuntimeError("Search request timed out")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Search request failed: {e}")


def get_sound_info(sound_id: int) -> Dict[str, Any]:
    """
    Get detailed information about a specific sound.

    Args:
        sound_id: The Freesound sound ID

    Returns:
        dict: Sound information
    """
    api_key = get_api_key()

    url = f"{SOUND_URL}/{sound_id}/"
    params = {"token": api_key}

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to get sound info: {e}")


def download_sound(
    sound_id: int,
    output_path: str,
    api_key: Optional[str] = None,
) -> str:
    """
    Download a sound file from Freesound.

    Note: Downloading requires OAuth2 authentication for most sounds.
    For preview downloads, use download_preview instead.

    Args:
        sound_id: The Freesound sound ID
        output_path: Path to save the downloaded file
        api_key: Optional API key override

    Returns:
        str: Path to downloaded file
    """
    if api_key is None:
        api_key = get_api_key()

    # Get sound info first to get download URL
    sound_info = get_sound_info(sound_id)

    # For regular downloads, OAuth2 is needed
    # Use preview as fallback
    preview_url = sound_info.get("previews", {}).get("preview-hq-mp3")
    if not preview_url:
        preview_url = sound_info.get("previews", {}).get("preview-lq-mp3")

    if not preview_url:
        raise RuntimeError("No preview URL available for this sound")

    try:
        response = requests.get(preview_url, timeout=60)
        response.raise_for_status()

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(response.content)

        return output_path
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Download failed: {e}")


def download_preview(
    preview_url: str,
    output_path: str,
) -> str:
    """
    Download a preview audio file directly.

    Args:
        preview_url: The preview URL from search results
        output_path: Path to save the downloaded file

    Returns:
        str: Path to downloaded file
    """
    try:
        response = requests.get(preview_url, timeout=60)
        response.raise_for_status()

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(response.content)

        return output_path
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Download failed: {e}")


def format_duration(seconds: float) -> str:
    """Format duration in seconds to MM:SS format."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


def format_search_results(results: Dict[str, Any]) -> str:
    """
    Format search results for display.

    Args:
        results: Raw search results from API

    Returns:
        str: Formatted results string
    """
    sounds = results.get("results", [])
    count = results.get("count", 0)

    if not sounds:
        return "No results found."

    lines = [f"Found {count} results, showing {len(sounds)}:\n"]

    for i, sound in enumerate(sounds, 1):
        name = sound.get("name", "Unknown")
        duration = format_duration(sound.get("duration", 0))
        username = sound.get("username", "Unknown")
        license_name = sound.get("license", "").split("/")[-2] if sound.get("license") else "Unknown"
        rating = sound.get("avg_rating", 0)
        downloads = sound.get("num_downloads", 0)
        sound_id = sound.get("id", "")

        # Get preview URL
        previews = sound.get("previews", {})
        preview_url = previews.get("preview-hq-mp3", previews.get("preview-lq-mp3", ""))

        lines.append(f"{i}. {name}")
        lines.append(f"   ID: {sound_id} | Duration: {duration} | By: {username}")
        lines.append(f"   Rating: {rating:.1f}/5 | Downloads: {downloads:,} | License: {license_name}")
        if preview_url:
            lines.append(f"   Preview: {preview_url}")
        lines.append("")

    return "\n".join(lines)


# Common search presets for music
MOOD_KEYWORDS = {
    "happy": "happy cheerful upbeat joyful",
    "sad": "sad melancholy emotional sorrowful",
    "tense": "tense suspense thriller dramatic tension",
    "relaxing": "relaxing calm peaceful chill soothing",
    "romantic": "romantic love gentle tender",
    "inspiring": "inspiring motivational uplifting",
    "energetic": "energetic dynamic powerful driving",
    "mysterious": "mysterious dark eerie ambient",
}

STYLE_KEYWORDS = {
    "electronic": "electronic synth digital futuristic",
    "epic": "epic cinematic orchestral dramatic",
    "jazz": "jazz smooth swing",
    "classical": "classical piano orchestra",
    "rock": "rock guitar energetic",
    "ambient": "ambient atmospheric soundscape drone",
    "lofi": "lofi hiphop chill beats",
    "corporate": "corporate business professional",
}

SCENE_KEYWORDS = {
    "intro": "intro opening logo ident",
    "background": "background underscore subtle",
    "game": "game 8bit retro chiptune",
    "nature": "nature forest ocean birds",
    "city": "urban city street traffic",
    "action": "action fast chase pursuit",
}


def get_mood_keywords(mood: str) -> str:
    """Get search keywords for a mood."""
    return MOOD_KEYWORDS.get(mood.lower(), mood)


def get_style_keywords(style: str) -> str:
    """Get search keywords for a style."""
    return STYLE_KEYWORDS.get(style.lower(), style)


def get_scene_keywords(scene: str) -> str:
    """Get search keywords for a scene."""
    return SCENE_KEYWORDS.get(scene.lower(), scene)
