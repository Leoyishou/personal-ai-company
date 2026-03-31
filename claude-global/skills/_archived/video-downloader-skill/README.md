# Video Downloader Skill

`video-downloader-skill` is a powerful command-line tool for downloading videos and audio from numerous websites, including YouTube, Bilibili, and Twitter. It is built on top of the popular `yt-dlp` library and provides a streamlined interface for common downloading tasks.

This skill is designed to be used as a Claude Code Skill, allowing for easy integration into automated workflows.

## Features

- **Wide Platform Support**: Download from YouTube, Bilibili, Twitter, and any other site supported by `yt-dlp`.
- **Quality Selection**: Choose your desired video quality, from `worst` to `best`, including specific resolutions like `1080p` or `720p`.
- **Format Conversion**: Save videos in your preferred format, such as `mp4`, `webm`, or `mkv`.
- **Audio Extraction**: Easily extract audio from a video and save it as an `mp3` file.
- **Bilibili Optimization**: Includes built-in optimizations to handle Bilibili's anti-scraping measures.
- **Cookie Support**: Use your browser's cookies to download videos that require a login.
- **Automatic Dependency Management**: The script automatically checks for and installs `yt-dlp` if it's not found.

## Installation

No manual installation is required. The script handles its own dependencies. Simply clone this repository and run the script.

```bash
git clone https://github.com/viva-org/video-downloader-skill.git
cd video-downloader-skill
```

## Usage

The skill is executed via the `video_download.py` script located in the `scripts/` directory.

```bash
python3 scripts/video_download.py "<URL>" [OPTIONS]
```

### Parameters

| Parameter      | Short | Description                                       | Default      |
|----------------|-------|---------------------------------------------------|--------------|
| `--output`     | `-o`  | Specifies the output directory.                   | Current Dir. |
| `--quality`    | `-q`  | Sets the video quality (`best`, `1080p`, etc.).   | `best`       |
| `--format`     | `-f`  | Sets the video container format (`mp4`, `webm`).  | `mp4`        |
| `--audio-only` | `-a`  | Downloads only the audio as an MP3 file.          | `False`      |
| `--cookies`    | `-c`  | Path to a Netscape cookies file for authentication. | `None`       |

### Examples

1.  **Basic Download (Best Quality, MP4)**

    ```bash
    python3 scripts/video_download.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    ```

2.  **Download a Bilibili Video in 1080p**

    ```bash
    python3 scripts/video_download.py "https://www.bilibili.com/video/BV1xx411c7mD" -q 1080p
    ```

3.  **Extract Audio Only**

    ```bash
    python3 scripts/video_download.py "https://www.youtube.com/watch?v=..." -a
    ```

4.  **Download to a Specific Directory**

    ```bash
    python3 scripts/video_download.py "<URL>" -o /path/to/downloads
    ```

5.  **Use Cookies for a Members-Only Video**

    ```bash
    python3 scripts/video_download.py "<URL>" -c /path/to/your/cookies.txt
    ```

## Supported Platforms

This skill uses `yt-dlp` as its backend, which supports a vast number of websites. For a complete list, please refer to the [official list of supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md).

Commonly used platforms include:

- YouTube
- Bilibili
- Twitter / X
- Vimeo
- Facebook
- TikTok

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
