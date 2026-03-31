#!/usr/bin/env python3
"""
小宇宙播客下载器 - 从小宇宙 FM 下载播客音频并提取元数据

用法:
    python3 xyz_download.py <URL> [-o OUTPUT_DIR] [--info-only] [--json]

示例:
    python3 xyz_download.py https://www.xiaoyuzhoufm.com/episode/622b585e129436aac42f7fd2
    python3 xyz_download.py https://www.xiaoyuzhoufm.com/episode/622b585e129436aac42f7fd2 -o ~/tmp
    python3 xyz_download.py https://www.xiaoyuzhoufm.com/episode/622b585e129436aac42f7fd2 --info-only --json
"""

import sys
import os
import re
import json
import argparse
import subprocess
import html


def extract_episode_id(url):
    """从 URL 提取 episode ID"""
    m = re.search(r'/episode/([a-f0-9]+)', url)
    if m:
        return m.group(1)
    # 也可能是纯 ID
    if re.match(r'^[a-f0-9]{24}$', url):
        return url
    return None


def fetch_page(url):
    """用 curl 获取页面 HTML"""
    result = subprocess.run(
        ['curl', '-s', '-L', '-A',
         'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
         url],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed: {result.stderr}")
    return result.stdout


def extract_next_data(page_html):
    """从 HTML 中提取 __NEXT_DATA__ JSON"""
    m = re.search(r'<script\s+id="__NEXT_DATA__"\s+type="application/json">(.*?)</script>', page_html, re.DOTALL)
    if not m:
        raise RuntimeError("__NEXT_DATA__ not found in page")
    raw = html.unescape(m.group(1))
    return json.loads(raw)


def extract_audio_url_fallback(page_html):
    """备用方法：用正则直接提取 .m4a URL"""
    urls = re.findall(r'https?://media\.xyzcdn\.net/[^\s"\'\\]+\.m4a', page_html)
    return urls[0] if urls else None


def parse_episode(data):
    """从 __NEXT_DATA__ 解析 episode 信息"""
    ep = data.get('props', {}).get('pageProps', {}).get('episode', {})
    if not ep:
        raise RuntimeError("Episode data not found in __NEXT_DATA__")

    podcast = ep.get('podcast', {})

    # 构建音频 URL
    media_key = ep.get('mediaKey', '')
    enclosure = ep.get('enclosure', {})
    audio_url = enclosure.get('url', '') if isinstance(enclosure, dict) else ''

    if not audio_url and media_key:
        audio_url = f"https://media.xyzcdn.net/{media_key}"

    # 时长（秒→分钟）
    duration_sec = ep.get('duration', 0)
    duration_min = round(duration_sec / 60, 1) if duration_sec else 0

    return {
        'eid': ep.get('eid', ''),
        'title': ep.get('title', ''),
        'description': ep.get('description', ''),
        'shownotes': ep.get('shownotes', ''),
        'audio_url': audio_url,
        'media_key': media_key,
        'duration_sec': duration_sec,
        'duration_min': duration_min,
        'published_at': ep.get('pubDate', ep.get('publishedAt', '')),
        'podcast': {
            'title': podcast.get('title', ''),
            'author': podcast.get('author', ''),
            'description': podcast.get('description', ''),
        },
        'image': ep.get('image', {}).get('picUrl', '') if isinstance(ep.get('image'), dict) else '',
        'url': f"https://www.xiaoyuzhoufm.com/episode/{ep.get('eid', '')}",
    }


def sanitize_filename(name, max_len=80):
    """清理文件名"""
    name = re.sub(r'[/\\:*?"<>|]', '_', name)
    name = name.strip()
    if len(name) > max_len:
        name = name[:max_len]
    return name


def download_audio(audio_url, output_path):
    """下载音频文件"""
    print(f"Downloading: {audio_url}")
    print(f"Output: {output_path}")
    result = subprocess.run(
        ['curl', '-L', '-o', output_path, '-#', audio_url],
        timeout=600
    )
    if result.returncode != 0:
        raise RuntimeError("Download failed")
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Done: {size_mb:.1f} MB")
    return output_path


def main():
    parser = argparse.ArgumentParser(description='小宇宙播客下载器')
    parser.add_argument('url', help='小宇宙 episode URL 或 ID')
    parser.add_argument('-o', '--output', default=os.path.expanduser('~/tmp'),
                        help='输出目录 (default: ~/tmp)')
    parser.add_argument('--info-only', action='store_true',
                        help='仅提取元数据，不下载')
    parser.add_argument('--json', action='store_true',
                        help='JSON 格式输出')
    args = parser.parse_args()

    # 1. 解析 URL
    eid = extract_episode_id(args.url)
    if not eid:
        print(f"ERROR: Invalid URL or ID: {args.url}", file=sys.stderr)
        sys.exit(1)

    url = f"https://www.xiaoyuzhoufm.com/episode/{eid}"

    # 2. 获取页面
    print(f"Fetching: {url}", file=sys.stderr)
    page_html = fetch_page(url)

    # 3. 提取数据
    try:
        data = extract_next_data(page_html)
        episode = parse_episode(data)
    except Exception as e:
        print(f"WARN: __NEXT_DATA__ parse failed ({e}), trying fallback", file=sys.stderr)
        audio_url = extract_audio_url_fallback(page_html)
        if not audio_url:
            print("ERROR: Could not extract audio URL", file=sys.stderr)
            sys.exit(1)
        episode = {
            'eid': eid,
            'title': eid,
            'audio_url': audio_url,
            'url': url,
        }

    # 4. 输出信息
    if args.json or args.info_only:
        print(json.dumps(episode, ensure_ascii=False, indent=2))
        if args.info_only:
            return

    if not args.json:
        print(f"\nTitle: {episode.get('title', 'N/A')}", file=sys.stderr)
        print(f"Podcast: {episode.get('podcast', {}).get('title', 'N/A')}", file=sys.stderr)
        print(f"Duration: {episode.get('duration_min', 0)} min", file=sys.stderr)
        print(f"Audio: {episode.get('audio_url', 'N/A')}", file=sys.stderr)

    # 5. 下载
    if not episode.get('audio_url'):
        print("ERROR: No audio URL found", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output, exist_ok=True)
    filename = sanitize_filename(episode['title']) + '.m4a'
    output_path = os.path.join(args.output, filename)

    download_audio(episode['audio_url'], output_path)

    # 6. 保存元数据
    meta_path = os.path.join(args.output, sanitize_filename(episode['title']) + '_metadata.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(episode, f, ensure_ascii=False, indent=2)
    print(f"Metadata: {meta_path}", file=sys.stderr)

    # 7. 输出结果
    result = {
        'success': True,
        'audio_file': output_path,
        'metadata_file': meta_path,
        'title': episode['title'],
        'duration_min': episode.get('duration_min', 0),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
