#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
社媒内容下载工具
支持平台：小红书、X (Twitter)、抖音 (Douyin)
"""

import argparse
import sys
import subprocess
import json
import os
import re
import requests
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, unquote
from datetime import datetime

# OAuth for Twitter
try:
    from requests_oauthlib import OAuth1
    HAS_OAUTH = True
except ImportError:
    HAS_OAUTH = False

# Playwright for Douyin
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# Set UTF-8 encoding
if sys.platform == "win32":
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


def detect_platform(url):
    """检测 URL 属于哪个平台"""
    if 'xiaohongshu.com' in url or 'xhslink.com' in url:
        return 'xiaohongshu'
    elif 'twitter.com' in url or 'x.com' in url:
        return 'twitter'
    elif 'douyin.com' in url or 'iesdouyin.com' in url or 'v.douyin.com' in url:
        return 'douyin'
    else:
        return None


def extract_douyin_url(text):
    """从抖音分享文本中提取 URL"""
    # 匹配各种抖音链接格式
    patterns = [
        r'(https?://v\.douyin\.com/[a-zA-Z0-9]+/?)',
        r'(https?://www\.douyin\.com/video/\d+)',
        r'(https?://www\.iesdouyin\.com/share/video/\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


# ============== 小红书模块 ==============

def parse_xhs_url(url):
    """解析小红书链接"""
    safe_print(f"[小红书] 正在解析链接: {url}")

    if 'xhslink.com' in url:
        try:
            if url.startswith('http://'):
                url = url.replace('http://', 'https://')
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15'
            }
            response = requests.get(url, headers=headers, allow_redirects=True, timeout=15)
            url = response.url
            safe_print(f"[小红书] 重定向到: {url}")
        except Exception as e:
            safe_print(f"[错误] 无法解析短链接: {e}")
            return None

    parsed = urlparse(url)

    # 检查是否被安全机制拦截
    if '/404/' in parsed.path:
        safe_print("[警告] 链接被安全机制拦截，尝试从 originalUrl 提取...")
        query_params = parse_qs(parsed.query)
        original_url = query_params.get('originalUrl', [None])[0]
        if original_url:
            return parse_xhs_url(unquote(original_url))
        else:
            safe_print("[错误] 无法从拦截页面提取原始链接")
            return None

    path_match = re.search(r'/(?:discovery/item|explore)/([a-f0-9]+)', parsed.path)
    if not path_match:
        safe_print(f"[错误] 无法从路径提取 feed_id: {parsed.path}")
        return None

    feed_id = path_match.group(1)
    query_params = parse_qs(parsed.query)
    xsec_token = query_params.get('xsec_token', [None])[0]

    if not xsec_token:
        safe_print(f"[警告] 未找到 xsec_token，视频下载可能会失败")

    result = {
        "platform": "xiaohongshu",
        "feed_id": feed_id,
        "xsec_token": xsec_token,
        "full_url": url
    }

    safe_print(f"[小红书] feed_id: {feed_id}")
    return result


def download_xhs_video(url, xsec_token, output_dir):
    """下载小红书视频"""
    # 确保 yt-dlp 可用
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        safe_print("[安装] yt-dlp 未找到，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--user", "yt-dlp"], check=True)

    if xsec_token:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        query_params['xsec_token'] = [xsec_token]
        new_query = urlencode(query_params, doseq=True)
        url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"

    safe_print(f"\n[下载] 开始下载小红书视频...")
    output_template = str(Path(output_dir) / "%(title)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "-f", "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "-o", output_template,
        "--no-playlist",
        url
    ]

    try:
        subprocess.run(cmd, check=True)
        safe_print("[成功] 视频下载完成!")
        return True
    except subprocess.CalledProcessError as e:
        safe_print(f"[错误] 视频下载失败: {e}")
        return False


def download_xhs_images(image_list, output_dir, title="xiaohongshu"):
    """下载小红书图片"""
    if not image_list:
        return True

    safe_print(f"\n[下载] 开始下载 {len(image_list)} 张图片...")
    safe_title = re.sub(r'[\\/*?:"<>|]', '_', title)[:50]
    success_count = 0

    for i, img in enumerate(image_list):
        url = img.get('urlDefault') or img.get('url')
        if not url:
            continue
        if url.startswith('http://'):
            url = url.replace('http://', 'https://')

        ext = 'webp' if 'webp' in url else 'jpg'
        filename = f"{safe_title}_{i+1}.{ext}"
        filepath = Path(output_dir) / filename

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)',
                'Referer': 'https://www.xiaohongshu.com/'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            with open(filepath, 'wb') as f:
                f.write(response.content)
            success_count += 1
            safe_print(f"[下载] 图片 {i+1}/{len(image_list)}: {filename}")
        except Exception as e:
            safe_print(f"[错误] 下载图片 {i+1} 失败: {e}")

    safe_print(f"[成功] 图片下载完成: {success_count}/{len(image_list)}")
    return success_count > 0


# ============== Twitter/X 模块 ==============

# twitterapi.io API Key (推荐，配额更充足)
TWITTERAPI_IO_KEY = os.environ.get('TWITTERAPI_IO_KEY', 'new1_0a63d55aad214ca990884b2b6637419f')

# X 官方 API 凭证 (备用)
X_API_KEY = os.environ.get('X_API_KEY', 'D63kRXyq6OJ5Aij2RWrrSr6aZ')
X_API_SECRET = os.environ.get('X_API_SECRET', 'gnCBbv24vlJBw5WrvNSX7CFs8sCSJzw1BkAx41JO2AaiJFKBj2')
X_ACCESS_TOKEN = os.environ.get('X_ACCESS_TOKEN', '1365589306698395651-zaMBD5lVIuhU18sHoYiWYoHVN22fW3')
X_ACCESS_TOKEN_SECRET = os.environ.get('X_ACCESS_TOKEN_SECRET', 'AdtIAAOLcltiTaMee6Q6Wy5jh9Ta0No4d5ndYN1gllNwr')


def parse_twitter_url(url):
    """解析 Twitter/X 链接"""
    safe_print(f"[X] 正在解析链接: {url}")

    # 提取推文 ID
    # 格式: https://x.com/username/status/1234567890
    match = re.search(r'/status/(\d+)', url)
    if not match:
        safe_print(f"[错误] 无法从 URL 提取推文 ID")
        return None

    tweet_id = match.group(1)
    safe_print(f"[X] tweet_id: {tweet_id}")

    return {
        "platform": "twitter",
        "tweet_id": tweet_id,
        "full_url": url
    }


def get_tweet_via_twitterapi_io(tweet_id):
    """通过 twitterapi.io 获取推文详情（推荐）"""
    if not TWITTERAPI_IO_KEY:
        return None

    url = f"https://api.twitterapi.io/twitter/tweets?tweet_ids={tweet_id}"
    headers = {"X-API-Key": TWITTERAPI_IO_KEY}

    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success' and data.get('tweets'):
                tweet = data['tweets'][0]
                safe_print(f"[X] 通过 twitterapi.io 获取成功")
                return {'source': 'twitterapi.io', 'tweet': tweet}
        else:
            error_msg = response.json().get('message', response.text)
            safe_print(f"[X] twitterapi.io 返回 {response.status_code}: {error_msg}")
            return None
    except Exception as e:
        safe_print(f"[X] twitterapi.io 请求失败: {e}")
        return None


def get_twitter_tweet(tweet_id):
    """获取推文详情 - 优先使用 twitterapi.io，失败则回退到官方 API"""
    # 方法1: twitterapi.io (推荐)
    result = get_tweet_via_twitterapi_io(tweet_id)
    if result:
        return result

    safe_print("[X] 尝试使用官方 API...")

    # 方法2: 官方 Twitter API (备用)
    if not HAS_OAUTH:
        safe_print("[错误] 需要安装 requests-oauthlib: pip install requests-oauthlib")
        return None

    auth = OAuth1(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)

    url = f"https://api.twitter.com/2/tweets/{tweet_id}"
    params = {
        "tweet.fields": "created_at,author_id,conversation_id,public_metrics,attachments,text",
        "expansions": "attachments.media_keys,author_id",
        "media.fields": "url,preview_image_url,type,variants,duration_ms",
        "user.fields": "name,username,profile_image_url"
    }

    try:
        response = requests.get(url, auth=auth, params=params, timeout=30)
        if response.status_code == 200:
            return {'source': 'official', **response.json()}
        else:
            safe_print(f"[错误] API 返回 {response.status_code}: {response.text}")
            return None
    except Exception as e:
        safe_print(f"[错误] 获取推文失败: {e}")
        return None


def get_twitter_replies(conversation_id, max_results=50):
    """获取推文回复"""
    if not HAS_OAUTH:
        return None

    auth = OAuth1(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)

    url = "https://api.twitter.com/2/tweets/search/recent"
    params = {
        "query": f"conversation_id:{conversation_id}",
        "tweet.fields": "created_at,author_id,public_metrics,text",
        "expansions": "author_id",
        "user.fields": "name,username",
        "max_results": max_results
    }

    try:
        response = requests.get(url, auth=auth, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception:
        return None


def download_twitter_video(variants, output_dir, title="twitter_video"):
    """下载 Twitter 视频"""
    if not variants:
        safe_print("[警告] 没有视频可下载")
        return False

    # 找到最高质量的 MP4
    mp4_variants = [v for v in variants if v.get('content_type') == 'video/mp4']
    if not mp4_variants:
        safe_print("[错误] 没有找到 MP4 格式视频")
        return False

    # 按码率排序 (兼容 bit_rate 和 bitrate 两种字段名)
    mp4_variants.sort(key=lambda x: x.get('bit_rate', x.get('bitrate', 0)), reverse=True)
    best_video = mp4_variants[0]
    video_url = best_video['url']
    bitrate = best_video.get('bit_rate', best_video.get('bitrate', 0)) // 1000

    safe_title = re.sub(r'[\\/*?:"<>|]', '_', title)[:50]
    filename = f"{safe_title}_{bitrate}kbps.mp4"
    filepath = Path(output_dir) / filename

    safe_print(f"\n[下载] 开始下载 X 视频 ({bitrate} kbps)...")

    try:
        response = requests.get(video_url, stream=True, timeout=120)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    percent = (downloaded / total_size) * 100
                    print(f"\r[下载] 进度: {percent:.1f}%", end='', flush=True)

        print()  # 换行
        safe_print(f"[成功] 视频已保存: {filepath}")
        return True
    except Exception as e:
        safe_print(f"[错误] 视频下载失败: {e}")
        return False


def download_twitter_images(media_list, output_dir, title="twitter"):
    """下载 Twitter 图片"""
    images = [m for m in media_list if m.get('type') == 'photo']
    if not images:
        return True

    safe_print(f"\n[下载] 开始下载 {len(images)} 张图片...")
    safe_title = re.sub(r'[\\/*?:"<>|]', '_', title)[:50]

    for i, img in enumerate(images):
        # 兼容两种格式: 'url' (官方 API) 和 'media_url_https' (twitterapi.io)
        url = img.get('url') or img.get('media_url_https')
        if not url:
            continue

        ext = 'jpg'
        filename = f"{safe_title}_{i+1}.{ext}"
        filepath = Path(output_dir) / filename

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            with open(filepath, 'wb') as f:
                f.write(response.content)
            safe_print(f"[下载] 图片 {i+1}: {filename}")
        except Exception as e:
            safe_print(f"[错误] 下载图片 {i+1} 失败: {e}")

    return True


# ============== 抖音/Douyin 模块 ==============

DOUYIN_COOKIES_PATH = os.path.expanduser("~/.claude/douyin_cookies.txt")


def parse_douyin_url(url_or_text):
    """解析抖音链接"""
    safe_print(f"[抖音] 正在解析: {url_or_text[:50]}...")

    # 从分享文本中提取链接
    url = extract_douyin_url(url_or_text)
    if not url:
        url = url_or_text

    # 处理短链接
    if 'v.douyin.com' in url:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15'
            }
            response = requests.get(url, headers=headers, allow_redirects=True, timeout=15)
            url = response.url
            safe_print(f"[抖音] 重定向到: {url}")
        except Exception as e:
            safe_print(f"[错误] 无法解析短链接: {e}")
            return None

    # 提取视频 ID (抖音 ID 可能包含字母和数字)
    video_id = None
    patterns = [
        r'/video/([a-zA-Z0-9]+)',
        r'modal_id=([a-zA-Z0-9]+)',
        r'vid=([a-zA-Z0-9]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            break

    if not video_id:
        safe_print(f"[错误] 无法从 URL 提取视频 ID: {url}")
        return None

    safe_print(f"[抖音] video_id: {video_id}")

    # 构建标准的 douyin.com URL
    canonical_url = f"https://www.douyin.com/video/{video_id}"

    return {
        "platform": "douyin",
        "video_id": video_id,
        "full_url": canonical_url
    }


def download_douyin_video_playwright(url, output_dir, cookies_path=None):
    """使用 Playwright 下载抖音视频"""
    if not HAS_PLAYWRIGHT:
        safe_print("[错误] 需要安装 Playwright: pip install playwright && playwright install chromium")
        return False

    safe_print(f"\n[抖音] 使用 Playwright 获取视频信息...")

    video_url = None
    video_title = "douyin_video"

    try:
        with sync_playwright() as p:
            # 启动浏览器
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )

            # 加载 cookies
            if cookies_path and os.path.exists(cookies_path):
                cookies = load_netscape_cookies(cookies_path, '.douyin.com')
                if cookies:
                    context.add_cookies(cookies)
                    safe_print(f"[抖音] 已加载 {len(cookies)} 个 cookies")

            page = context.new_page()

            # 监听网络请求，捕获视频 URL
            video_urls = []

            def handle_response(response):
                url = response.url
                # 抖音视频 URL 特征 - 排除占位视频
                if 'uuu_' in url or 'placeholder' in url.lower():
                    return
                # 真实视频 URL 特征
                if any(x in url for x in ['douyinvod.com', 'bytedance.com', 'bytecdn.cn', 'amemv.com']):
                    if '.mp4' in url or 'video' in url.lower():
                        video_urls.append(url)
                        safe_print(f"[抖音] 捕获视频请求: {url[:80]}...")

            page.on('response', handle_response)

            # 访问页面
            safe_print(f"[抖音] 正在加载页面: {url}")
            page.goto(url, wait_until='domcontentloaded', timeout=60000)

            # 等待页面加载完成
            import time
            time.sleep(3)

            # 等待视频元素加载
            try:
                page.wait_for_selector('video', timeout=15000)
                safe_print("[抖音] 视频元素已加载")

                # 点击视频触发播放，捕获真实视频 URL
                try:
                    video_elem = page.query_selector('video')
                    if video_elem:
                        video_elem.click()
                        safe_print("[抖音] 已点击视频元素")
                except Exception:
                    pass

                # 等待视频加载
                import time
                time.sleep(5)

            except Exception:
                safe_print("[抖音] 等待视频元素超时，继续尝试...")

            # 尝试从页面获取标题
            try:
                title_elem = page.query_selector('h1') or page.query_selector('[class*="title"]')
                if title_elem:
                    video_title = title_elem.inner_text()[:50]
            except Exception:
                pass

            # 方法1: 优先从捕获的网络请求获取（最可靠）
            if video_urls:
                # 过滤掉占位视频和非视频 URL
                valid_urls = [u for u in video_urls if 'uuu_' not in u and ('douyinvod' in u or 'bytecdn' in u or 'amemv' in u)]
                if valid_urls:
                    video_url = max(valid_urls, key=len)
                    safe_print(f"[抖音] 方法1: 从网络请求捕获 ({len(valid_urls)} URLs)")

            # 方法2: 从 video 元素的 src 属性（可能是占位视频）
            if not video_url:
                try:
                    video_elem = page.query_selector('video')
                    if video_elem:
                        src = video_elem.get_attribute('src')
                        if src and src.startswith('http') and 'uuu_' not in src:
                            video_url = src
                            safe_print(f"[抖音] 方法2: 从 video src 获取")
                except Exception as e:
                    safe_print(f"[调试] 方法2失败: {e}")

            # 方法2b: 从 video source 元素
            if not video_url:
                try:
                    source_elem = page.query_selector('video source')
                    if source_elem:
                        src = source_elem.get_attribute('src')
                        if src and src.startswith('http') and 'uuu_' not in src:
                            video_url = src
                            safe_print(f"[抖音] 方法2b: 从 video source 获取")
                except Exception:
                    pass

            # 方法3: 从页面 JavaScript 数据 (SSR 数据)
            if not video_url:
                try:
                    # 抖音将数据嵌入到 script#RENDER_DATA 或 window.__INITIAL_STATE__
                    page_content = page.content()

                    # 尝试从 RENDER_DATA 提取
                    render_match = re.search(r'<script[^>]*id="RENDER_DATA"[^>]*>([^<]+)</script>', page_content)
                    if render_match:
                        from urllib.parse import unquote
                        render_data = unquote(render_match.group(1))
                        # 查找视频 URL
                        url_match = re.search(r'"playApi":\s*"([^"]+)"', render_data)
                        if url_match:
                            video_url = url_match.group(1).replace('\\u002F', '/')
                            if not video_url.startswith('http'):
                                video_url = 'https:' + video_url
                            safe_print(f"[抖音] 方法3: 从 RENDER_DATA 获取")
                except Exception as e:
                    safe_print(f"[调试] 方法3失败: {e}")

            # 方法4: 尝试播放视频触发请求
            if not video_url:
                try:
                    video_elem = page.query_selector('video')
                    if video_elem:
                        page.evaluate('document.querySelector("video").play()')
                        import time
                        time.sleep(2)
                        # 检查是否有新的视频 URL
                        if video_urls:
                            valid_urls = [u for u in video_urls if '.mp4' in u or 'video' in u.lower()]
                            if valid_urls:
                                video_url = max(valid_urls, key=len)
                                safe_print(f"[抖音] 方法4: 播放后捕获")
                except Exception:
                    pass

            browser.close()

    except Exception as e:
        safe_print(f"[错误] Playwright 执行失败: {e}")
        return False

    if not video_url:
        safe_print("[错误] 无法获取视频 URL")
        return False

    safe_print(f"[抖音] 找到视频 URL: {video_url[:100]}...")

    # 下载视频
    return download_video_from_url(video_url, output_dir, video_title)


def load_netscape_cookies(cookies_path, domain_filter=None):
    """加载 Netscape 格式的 cookies 文件"""
    cookies = []
    try:
        with open(cookies_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split('\t')
                if len(parts) >= 7:
                    domain = parts[0]
                    if domain_filter and domain_filter not in domain:
                        continue
                    cookie = {
                        'domain': domain,
                        'path': parts[2],
                        'secure': parts[3].lower() == 'true',
                        'expires': int(parts[4]) if parts[4].isdigit() else -1,
                        'name': parts[5],
                        'value': parts[6]
                    }
                    cookies.append(cookie)
    except Exception as e:
        safe_print(f"[警告] 加载 cookies 失败: {e}")
    return cookies


def download_video_from_url(video_url, output_dir, title="video"):
    """从 URL 下载视频"""
    safe_title = re.sub(r'[\\/*?:"<>|]', '_', title)[:50]
    filepath = Path(output_dir) / f"{safe_title}.mp4"

    safe_print(f"\n[下载] 开始下载视频...")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.douyin.com/'
        }
        response = requests.get(video_url, headers=headers, stream=True, timeout=60)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    percent = (downloaded / total_size) * 100
                    print(f"\r[下载] 进度: {percent:.1f}%", end='', flush=True)

        print()  # 换行
        safe_print(f"[成功] 视频已保存: {filepath}")
        return True

    except Exception as e:
        safe_print(f"[错误] 视频下载失败: {e}")
        return False


# ============== 元数据保存 ==============

def save_metadata(data, output_dir, filename="metadata.json"):
    """保存元数据"""
    metadata = {
        "downloaded_at": datetime.now().isoformat(),
        **data
    }
    filepath = Path(output_dir) / filename

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        safe_print(f"[成功] 元数据已保存: {filepath}")
        return True
    except Exception as e:
        safe_print(f"[错误] 保存元数据失败: {e}")
        return False


def create_summary(data, platform, output_dir, filename="summary.md"):
    """创建摘要"""
    filepath = Path(output_dir) / filename

    if platform == 'xiaohongshu':
        note = data.get('note', {})
        md = f"""# {note.get('title', '未知标题')}

## 基本信息

| 项目 | 内容 |
|------|------|
| 平台 | 小红书 |
| 作者 | {note.get('user', {}).get('nickname', '未知')} |
| 类型 | {note.get('type', '未知')} |
| IP属地 | {note.get('ipLocation', '未知')} |
| 点赞 | {note.get('interactInfo', {}).get('likedCount', '0')} |
| 收藏 | {note.get('interactInfo', {}).get('collectedCount', '0')} |

## 正文

{note.get('desc', '')}

---
*下载时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    elif platform == 'twitter':
        tweet = data.get('tweet', {})
        user = data.get('user', {})
        metrics = tweet.get('public_metrics', {})
        md = f"""# @{user.get('username', 'unknown')} 的推文

## 基本信息

| 项目 | 内容 |
|------|------|
| 平台 | X (Twitter) |
| 作者 | {user.get('name', '')} (@{user.get('username', '')}) |
| 发布时间 | {tweet.get('created_at', '')} |
| 点赞 | {metrics.get('like_count', 0)} |
| 转发 | {metrics.get('retweet_count', 0)} |
| 回复 | {metrics.get('reply_count', 0)} |
| 曝光 | {metrics.get('impression_count', 0)} |

## 正文

{tweet.get('text', '')}

---
*下载时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    else:
        md = f"# 未知平台\n\n下载时间: {datetime.now()}"

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md)
        safe_print(f"[成功] 摘要已保存: {filepath}")
        return True
    except Exception as e:
        safe_print(f"[错误] 保存摘要失败: {e}")
        return False


# ============== 主函数 ==============

def main():
    parser = argparse.ArgumentParser(description="社媒内容下载工具 (小红书 / X)")

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # parse 命令
    parse_parser = subparsers.add_parser('parse', help='解析社媒链接')
    parse_parser.add_argument('url', help='社媒链接')
    parse_parser.add_argument('--json', action='store_true', help='输出 JSON')

    # download 命令
    dl_parser = subparsers.add_parser('download', help='下载内容')
    dl_parser.add_argument('url', help='社媒链接')
    dl_parser.add_argument('-o', '--output', default='.', help='输出目录')
    dl_parser.add_argument('--video-only', action='store_true', help='仅下载视频')
    dl_parser.add_argument('--no-comments', action='store_true', help='不获取评论')

    # twitter 命令 (直接用 tweet_id)
    tw_parser = subparsers.add_parser('twitter', help='下载 Twitter 内容')
    tw_parser.add_argument('tweet_id', help='推文 ID')
    tw_parser.add_argument('-o', '--output', default='.', help='输出目录')

    # xiaohongshu 命令 (需要 MCP 配合)
    xhs_parser = subparsers.add_parser('xiaohongshu', help='下载小红书内容')
    xhs_parser.add_argument('url', help='小红书链接')
    xhs_parser.add_argument('-o', '--output', default='.', help='输出目录')

    # douyin 命令
    dy_parser = subparsers.add_parser('douyin', help='下载抖音视频')
    dy_parser.add_argument('url', help='抖音链接或分享文本')
    dy_parser.add_argument('-o', '--output', default='.', help='输出目录')
    dy_parser.add_argument('-c', '--cookies', default=DOUYIN_COOKIES_PATH, help='Cookies 文件路径')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'parse':
        # 先尝试从分享文本提取抖音链接
        douyin_url = extract_douyin_url(args.url)
        if douyin_url:
            platform = 'douyin'
            url_to_parse = douyin_url
        else:
            platform = detect_platform(args.url)
            url_to_parse = args.url

        if platform == 'xiaohongshu':
            result = parse_xhs_url(url_to_parse)
        elif platform == 'twitter':
            result = parse_twitter_url(url_to_parse)
        elif platform == 'douyin':
            result = parse_douyin_url(url_to_parse)
        else:
            safe_print(f"[错误] 不支持的平台: {args.url}")
            sys.exit(1)

        if result and args.json:
            print(json.dumps(result, ensure_ascii=False))
        sys.exit(0 if result else 1)

    elif args.command == 'download':
        # 先尝试从分享文本提取抖音链接
        douyin_url = extract_douyin_url(args.url)
        if douyin_url:
            platform = 'douyin'
            url_to_use = douyin_url
        else:
            platform = detect_platform(args.url)
            url_to_use = args.url

        os.makedirs(args.output, exist_ok=True)

        if platform == 'douyin':
            parsed = parse_douyin_url(url_to_use)
            if not parsed:
                sys.exit(1)
            download_douyin_video_playwright(parsed['full_url'], args.output, DOUYIN_COOKIES_PATH)

        elif platform == 'twitter':
            parsed = parse_twitter_url(args.url)
            if not parsed:
                sys.exit(1)

            tweet_data = get_twitter_tweet(parsed['tweet_id'])
            if not tweet_data:
                sys.exit(1)

            # 根据数据来源解析
            if tweet_data.get('source') == 'twitterapi.io':
                tweet = tweet_data['tweet']
                author = tweet.get('author', {})
                username = author.get('userName', 'twitter')

                # 下载视频
                extended = tweet.get('extendedEntities', {})
                media_list = extended.get('media', [])
                for m in media_list:
                    if m.get('type') == 'video':
                        variants = m.get('video_info', {}).get('variants', [])
                        download_twitter_video(variants, args.output, username)

                # 下载图片
                download_twitter_images(media_list, args.output, username)

                # 保存元数据
                save_metadata({
                    'tweet': tweet,
                    'user': author,
                    'media': media_list,
                }, args.output)

                # 创建摘要 (适配 twitterapi.io 格式)
                summary_data = {
                    'tweet': {
                        'text': tweet.get('text', ''),
                        'created_at': tweet.get('createdAt', ''),
                        'public_metrics': {
                            'like_count': tweet.get('likeCount', 0),
                            'retweet_count': tweet.get('retweetCount', 0),
                            'reply_count': tweet.get('replyCount', 0),
                            'impression_count': tweet.get('viewCount', 0),
                        }
                    },
                    'user': {
                        'name': author.get('name', ''),
                        'username': username,
                    }
                }
                create_summary(summary_data, 'twitter', args.output)

            else:
                # 官方 API 格式
                data = tweet_data.get('data', {})
                includes = tweet_data.get('includes', {})
                media = includes.get('media', [])
                users = includes.get('users', [])
                user = users[0] if users else {}

                # 下载视频
                for m in media:
                    if m.get('type') == 'video':
                        variants = m.get('variants', [])
                        download_twitter_video(variants, args.output, user.get('username', 'twitter'))

                # 下载图片
                download_twitter_images(media, args.output, user.get('username', 'twitter'))

                # 获取评论
                replies = None
                if not args.no_comments:
                    replies = get_twitter_replies(data.get('conversation_id'))

                # 保存元数据
                save_metadata({
                    'tweet': data,
                    'user': user,
                    'media': media,
                    'replies': replies
                }, args.output)
                create_summary({'tweet': data, 'user': user}, 'twitter', args.output)

        elif platform == 'xiaohongshu':
            parsed = parse_xhs_url(args.url)
            if not parsed:
                sys.exit(1)

            # 小红书需要 MCP 获取详情，这里只下载视频
            download_xhs_video(parsed['full_url'], parsed['xsec_token'], args.output)
            safe_print("\n[提示] 小红书详情需要通过 MCP 获取，请参考 SKILL.md")

        else:
            safe_print(f"[错误] 不支持的平台")
            sys.exit(1)

    elif args.command == 'twitter':
        os.makedirs(args.output, exist_ok=True)
        tweet_data = get_twitter_tweet(args.tweet_id)
        if not tweet_data:
            sys.exit(1)

        # 根据数据来源解析
        if tweet_data.get('source') == 'twitterapi.io':
            tweet = tweet_data['tweet']
            author = tweet.get('author', {})
            username = author.get('userName', 'twitter')

            # 下载视频
            extended = tweet.get('extendedEntities', {})
            media_list = extended.get('media', [])
            for m in media_list:
                if m.get('type') == 'video':
                    variants = m.get('video_info', {}).get('variants', [])
                    download_twitter_video(variants, args.output, username)

            # 下载图片
            download_twitter_images(media_list, args.output, username)

            # 保存元数据
            save_metadata({
                'tweet': tweet,
                'user': author,
                'media': media_list,
            }, args.output)

            # 创建摘要
            summary_data = {
                'tweet': {
                    'text': tweet.get('text', ''),
                    'created_at': tweet.get('createdAt', ''),
                    'public_metrics': {
                        'like_count': tweet.get('likeCount', 0),
                        'retweet_count': tweet.get('retweetCount', 0),
                        'reply_count': tweet.get('replyCount', 0),
                        'impression_count': tweet.get('viewCount', 0),
                    }
                },
                'user': {
                    'name': author.get('name', ''),
                    'username': username,
                }
            }
            create_summary(summary_data, 'twitter', args.output)

        else:
            # 官方 API 格式
            data = tweet_data.get('data', {})
            includes = tweet_data.get('includes', {})
            media = includes.get('media', [])
            users = includes.get('users', [])
            user = users[0] if users else {}

            for m in media:
                if m.get('type') == 'video':
                    variants = m.get('variants', [])
                    download_twitter_video(variants, args.output, user.get('username', 'twitter'))

            download_twitter_images(media, args.output, user.get('username', 'twitter'))

            replies = get_twitter_replies(data.get('conversation_id'))

            save_metadata({
                'tweet': data,
                'user': user,
                'media': media,
                'replies': replies
            }, args.output)
            create_summary({'tweet': data, 'user': user}, 'twitter', args.output)

    elif args.command == 'xiaohongshu':
        os.makedirs(args.output, exist_ok=True)
        parsed = parse_xhs_url(args.url)
        if not parsed:
            sys.exit(1)
        download_xhs_video(parsed['full_url'], parsed['xsec_token'], args.output)

    elif args.command == 'douyin':
        os.makedirs(args.output, exist_ok=True)
        parsed = parse_douyin_url(args.url)
        if not parsed:
            sys.exit(1)
        download_douyin_video_playwright(parsed['full_url'], args.output, args.cookies)


if __name__ == "__main__":
    main()
