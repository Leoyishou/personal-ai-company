#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取 Twitter/X 用户时间线
支持通过 twitterapi.io 和官方 API 获取用户最近的推文
"""

import argparse
import sys
import json
import os
import requests
from datetime import datetime, timedelta
import re

# OAuth for Twitter
try:
    from requests_oauthlib import OAuth1
    HAS_OAUTH = True
except ImportError:
    HAS_OAUTH = False

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


# API 凭证
TWITTERAPI_IO_KEY = os.environ.get('TWITTERAPI_IO_KEY', 'new1_0a63d55aad214ca990884b2b6637419f')
X_API_KEY = os.environ.get('X_API_KEY', 'D63kRXyq6OJ5Aij2RWrrSr6aZ')
X_API_SECRET = os.environ.get('X_API_SECRET', 'gnCBbv24vlJBw5WrvNSX7CFs8sCSJzw1BkAx41JO2AaiJFKBj2')
X_ACCESS_TOKEN = os.environ.get('X_ACCESS_TOKEN', '1365589306698395651-zaMBD5lVIuhU18sHoYiWYoHVN22fW3')
X_ACCESS_TOKEN_SECRET = os.environ.get('X_ACCESS_TOKEN_SECRET', 'AdtIAAOLcltiTaMee6Q6Wy5jh9Ta0No4d5ndYN1gllNwr')


def extract_username(url_or_username):
    """从 URL 或用户名中提取 username"""
    # 如果是 URL，提取 username
    if 'twitter.com/' in url_or_username or 'x.com/' in url_or_username:
        match = re.search(r'(?:twitter\.com|x\.com)/([^/\?]+)', url_or_username)
        if match:
            return match.group(1).replace('@', '')
    # 否则假设是 username
    return url_or_username.replace('@', '')


def get_user_id_from_username(username):
    """通过 username 获取 user_id (使用 twitterapi.io)"""
    if not TWITTERAPI_IO_KEY:
        safe_print("[错误] 未配置 TWITTERAPI_IO_KEY")
        return None

    url = f"https://api.twitterapi.io/twitter/user?username={username}"
    headers = {"X-API-Key": TWITTERAPI_IO_KEY}

    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success' and data.get('user'):
                user_id = data['user'].get('rest_id') or data['user'].get('id_str')
                safe_print(f"[X] 用户 @{username} 的 ID: {user_id}")
                return user_id
        else:
            error_msg = response.json().get('message', response.text)
            safe_print(f"[错误] twitterapi.io 返回 {response.status_code}: {error_msg}")
            return None
    except Exception as e:
        safe_print(f"[错误] 获取用户信息失败: {e}")
        return None


def get_user_timeline_twitterapi_io(username, max_results=20):
    """通过 twitterapi.io 获取用户时间线"""
    if not TWITTERAPI_IO_KEY:
        return None

    # 先获取 user_id
    user_id = get_user_id_from_username(username)
    if not user_id:
        return None

    url = f"https://api.twitterapi.io/twitter/user/timeline?user_id={user_id}&count={max_results}"
    headers = {"X-API-Key": TWITTERAPI_IO_KEY}

    try:
        safe_print(f"[X] 正在获取 @{username} 的时间线...")
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success' and data.get('tweets'):
                tweets = data['tweets']
                safe_print(f"[X] 通过 twitterapi.io 获取到 {len(tweets)} 条推文")
                return {'source': 'twitterapi.io', 'tweets': tweets}
        else:
            error_msg = response.json().get('message', response.text)
            safe_print(f"[X] twitterapi.io 返回 {response.status_code}: {error_msg}")
            return None
    except Exception as e:
        safe_print(f"[X] twitterapi.io 请求失败: {e}")
        return None


def get_user_timeline_official(username, max_results=20):
    """通过官方 Twitter API 获取用户时间线（备用）"""
    if not HAS_OAUTH:
        safe_print("[错误] 需要安装 requests-oauthlib: pip install requests-oauthlib")
        return None

    auth = OAuth1(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)

    # 先获取 user ID
    user_url = f"https://api.twitter.com/2/users/by/username/{username}"
    try:
        response = requests.get(user_url, auth=auth, timeout=30)
        if response.status_code != 200:
            safe_print(f"[错误] 无法获取用户信息: {response.status_code}")
            return None
        user_data = response.json()
        user_id = user_data['data']['id']
    except Exception as e:
        safe_print(f"[错误] 获取用户 ID 失败: {e}")
        return None

    # 获取用户时间线
    timeline_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    params = {
        "max_results": max_results,
        "tweet.fields": "created_at,public_metrics,text,author_id",
        "expansions": "author_id",
        "user.fields": "name,username,profile_image_url"
    }

    try:
        safe_print(f"[X] 正在获取 @{username} 的时间线...")
        response = requests.get(timeline_url, auth=auth, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            tweets = data.get('data', [])
            safe_print(f"[X] 通过官方 API 获取到 {len(tweets)} 条推文")
            return {'source': 'official', **data}
        else:
            safe_print(f"[错误] API 返回 {response.status_code}: {response.text}")
            return None
    except Exception as e:
        safe_print(f"[错误] 获取时间线失败: {e}")
        return None


def get_user_timeline(username, max_results=20):
    """获取用户时间线 - 优先使用 twitterapi.io"""
    username = extract_username(username)

    # 方法1: twitterapi.io (推荐)
    result = get_user_timeline_twitterapi_io(username, max_results)
    if result:
        return result

    safe_print("[X] 尝试使用官方 API...")

    # 方法2: 官方 Twitter API (备用)
    return get_user_timeline_official(username, max_results)


def filter_tweets_by_time(tweets, hours=48, source='twitterapi.io'):
    """筛选指定时间内的推文"""
    cutoff_time = datetime.now() - timedelta(hours=hours)
    filtered = []

    for tweet in tweets:
        try:
            if source == 'twitterapi.io':
                # twitterapi.io 格式: "Wed Jan 29 12:34:56 +0000 2026"
                created_at_str = tweet.get('createdAt', '')
                created_at = datetime.strptime(created_at_str, "%a %b %d %H:%M:%S %z %Y")
            else:
                # 官方 API 格式: "2026-01-29T12:34:56.000Z"
                created_at_str = tweet.get('created_at', '')
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))

            # 转换为无时区的 datetime 进行比较
            created_at_naive = created_at.replace(tzinfo=None)

            if created_at_naive >= cutoff_time:
                filtered.append(tweet)
        except Exception as e:
            safe_print(f"[警告] 解析推文时间失败: {e}")
            continue

    return filtered


def format_tweet_output(username, tweets, source='twitterapi.io', markdown=False):
    """格式化推文输出"""
    if source == 'twitterapi.io':
        return format_tweet_twitterapi_io(username, tweets, markdown)
    else:
        return format_tweet_official(username, tweets, markdown)


def format_tweet_twitterapi_io(username, tweets, markdown=False):
    """格式化 twitterapi.io 推文"""
    if markdown:
        output = [f"## @{username}\n"]
        for tweet in tweets:
            text = tweet.get('text', '').replace('\n', ' ')
            created_at = tweet.get('createdAt', '')
            likes = tweet.get('likeCount', 0)
            retweets = tweet.get('retweetCount', 0)
            replies = tweet.get('replyCount', 0)

            # 解析时间
            try:
                dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                time_str = created_at

            output.append(f"- **{text[:100]}{'...' if len(text) > 100 else ''}**")
            output.append(f"  - 时间: {time_str}")
            output.append(f"  - 互动: ❤️ {likes} | 🔄 {retweets} | 💬 {replies}\n")

        return '\n'.join(output)
    else:
        # JSON 格式
        return json.dumps({
            'username': username,
            'count': len(tweets),
            'tweets': [
                {
                    'text': t.get('text', ''),
                    'created_at': t.get('createdAt', ''),
                    'likes': t.get('likeCount', 0),
                    'retweets': t.get('retweetCount', 0),
                    'replies': t.get('replyCount', 0),
                    'views': t.get('viewCount', 0),
                }
                for t in tweets
            ]
        }, ensure_ascii=False, indent=2)


def format_tweet_official(username, tweets, markdown=False):
    """格式化官方 API 推文"""
    if markdown:
        output = [f"## @{username}\n"]
        for tweet in tweets:
            text = tweet.get('text', '').replace('\n', ' ')
            created_at = tweet.get('created_at', '')
            metrics = tweet.get('public_metrics', {})
            likes = metrics.get('like_count', 0)
            retweets = metrics.get('retweet_count', 0)
            replies = metrics.get('reply_count', 0)

            # 解析时间
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                time_str = created_at

            output.append(f"- **{text[:100]}{'...' if len(text) > 100 else ''}**")
            output.append(f"  - 时间: {time_str}")
            output.append(f"  - 互动: ❤️ {likes} | 🔄 {retweets} | 💬 {replies}\n")

        return '\n'.join(output)
    else:
        # JSON 格式
        return json.dumps({
            'username': username,
            'count': len(tweets),
            'tweets': [
                {
                    'text': t.get('text', ''),
                    'created_at': t.get('created_at', ''),
                    'likes': t.get('public_metrics', {}).get('like_count', 0),
                    'retweets': t.get('public_metrics', {}).get('retweet_count', 0),
                    'replies': t.get('public_metrics', {}).get('reply_count', 0),
                    'views': t.get('public_metrics', {}).get('impression_count', 0),
                }
                for t in tweets
            ]
        }, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="获取 Twitter/X 用户时间线")
    parser.add_argument('users', nargs='+', help='用户名或用户主页链接（可多个）')
    parser.add_argument('-n', '--max-results', type=int, default=20, help='每个用户最多获取多少条推文（默认 20）')
    parser.add_argument('-t', '--time-filter', type=int, default=0, help='仅保留最近 N 小时内的推文（0 表示不过滤）')
    parser.add_argument('-m', '--markdown', action='store_true', help='输出 Markdown 格式（默认 JSON）')
    parser.add_argument('-o', '--output', help='输出文件路径（可选）')

    args = parser.parse_args()

    all_results = []

    for user in args.users:
        username = extract_username(user)
        safe_print(f"\n{'='*60}")
        safe_print(f"正在处理: @{username}")
        safe_print('='*60)

        result = get_user_timeline(username, args.max_results)

        if not result:
            safe_print(f"[错误] 无法获取 @{username} 的时间线")
            continue

        source = result.get('source', 'official')
        tweets = result.get('tweets', [])

        # 时间筛选
        if args.time_filter > 0:
            original_count = len(tweets)
            tweets = filter_tweets_by_time(tweets, args.time_filter, source)
            safe_print(f"[筛选] {original_count} 条推文 -> {len(tweets)} 条（最近 {args.time_filter} 小时）")

        if not tweets:
            safe_print(f"[提示] @{username} 在指定时间内没有推文")
            continue

        # 格式化输出
        formatted = format_tweet_output(username, tweets, source, args.markdown)

        if args.markdown:
            safe_print(f"\n{formatted}")

        all_results.append({
            'username': username,
            'source': source,
            'count': len(tweets),
            'formatted': formatted,
            'raw_tweets': tweets
        })

    # 保存到文件
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                if args.markdown:
                    f.write('\n\n'.join([r['formatted'] for r in all_results]))
                else:
                    json.dump(all_results, f, ensure_ascii=False, indent=2)
            safe_print(f"\n[成功] 结果已保存到: {args.output}")
        except Exception as e:
            safe_print(f"\n[错误] 保存文件失败: {e}")
    elif not args.markdown:
        # 如果没有指定输出文件且不是 markdown 格式，输出 JSON
        print(json.dumps(all_results, ensure_ascii=False, indent=2))

    safe_print(f"\n{'='*60}")
    safe_print(f"完成! 共处理 {len(all_results)} 个用户")
    safe_print('='*60)


if __name__ == "__main__":
    main()
