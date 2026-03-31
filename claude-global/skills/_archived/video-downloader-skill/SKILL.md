---
name: video-downloader-skill
description: "Downloads videos and audio from YouTube, Bilibili, Twitter, and other platforms using yt-dlp. Supports quality selection, format conversion, and audio extraction."
---

# Video Downloader Skill

This skill downloads content from major video platforms by invoking the `/Users/liuyishou/.claude/skills/video-downloader-skill/scripts/video_download.py` script.

## When to Use

Use this skill when the user's intent is to **download**, **save**, or **grab** online video or audio. Common trigger commands include:

- "Download this Bilibili video..."
- "Extract audio from this YouTube video and convert it to MP3."
- "Save this Twitter video in 1080p."
- "Can I download the video from this link?"

## Command Structure

```bash
python3 /Users/liuyishou/.claude/skills/video-downloader-skill/scripts/video_download.py "<URL>" [OPTIONS]
```

## Core Parameters

| Parameter | Short | Description | Default |
|---|---|---|---|
| `--output` | `-o` | Specify output directory | Current directory |
| `--quality` | `-q` | Set video quality (`best`, `1080p`, `720p`...) | `best` |
| `--format` | `-f` | Set video format (`mp4`, `webm`, `mkv`) | `mp4` |
| `--audio-only` | `-a` | Download audio only and convert to MP3 | Off |
| `--cookies` | `-c` | Specify Cookies file for authentication | None |

## Usage Examples

1.  **Basic Download (Best Quality, MP4)**

    ```bash
    python3 /Users/liuyishou/.claude/skills/video-downloader-skill/scripts/video_download.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    ```

2.  **Download Bilibili Video with Specific Quality**

    ```bash
    python3 /Users/liuyishou/.claude/skills/video-downloader-skill/scripts/video_download.py "https://www.bilibili.com/video/BV1xx411c7mD" -q 1080p
    ```

3.  **Extract Audio Only**

    ```bash
    python3 /Users/liuyishou/.claude/skills/video-downloader-skill/scripts/video_download.py "https://www.youtube.com/watch?v=..." -a
    ```

4.  **Download using Cookies**

    ```bash
    python3 /Users/liuyishou/.claude/skills/video-downloader-skill/scripts/video_download.py "<URL>" -c /path/to/cookies.txt
    ```

## Supported Platforms

This skill uses `yt-dlp` under the hood and theoretically supports [numerous sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) supported by it, including but not limited to:

- YouTube
- Bilibili
- Twitter / X
- Vimeo
- Facebook
- TikTok

## Notes

- **Dependencies**: The script automatically handles the installation of `yt-dlp`, no manual intervention required.
- **Filenames**: Downloaded filenames are automatically generated based on the video title.
- **Playlists**: By default, only single videos are downloaded; playlists are not processed.
