#!/usr/bin/env python3
"""
X (Twitter) API v2 发推脚本
支持纯文本推文和带图片的推文
"""

import requests
from requests_oauthlib import OAuth1
import json
import sys
import base64
import os
import time
from pathlib import Path

# ========== 加载环境变量 ==========
def load_env():
    """从 .env 文件加载环境变量"""
    env_paths = [
        Path(__file__).parent / ".env",
        Path(__file__).parent.parent / ".env",
        Path.home() / ".claude" / "skills" / "x-post" / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ.setdefault(key.strip(), value.strip())
            break

load_env()

# ========== API 凭证（从环境变量读取）==========
API_KEY = os.environ.get("X_API_KEY", "D63kRXyq6OJ5Aij2RWrrSr6aZ")
API_SECRET = os.environ.get("X_API_SECRET", "gnCBbv24vlJBw5WrvNSX7CFs8sCSJzw1BkAx41JO2AaiJFKBj2")
ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN", "1365589306698395651-zaMBD5lVIuhU18sHoYiWYoHVN22fW3")
ACCESS_TOKEN_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET", "AdtIAAOLcltiTaMee6Q6Wy5jh9Ta0No4d5ndYN1gllNwr")

# ========== API 端点 ==========
TWEET_URL = "https://api.x.com/2/tweets"
MEDIA_UPLOAD_URL = "https://upload.twitter.com/1.1/media/upload.json"


def get_auth():
    """获取 OAuth1 认证对象"""
    return OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)


def upload_media(image_path: str) -> str:
    """
    上传图片到 Twitter，返回 media_id

    Args:
        image_path: 图片文件路径

    Returns:
        media_id 字符串
    """
    auth = get_auth()

    # 读取图片并转为 base64
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')

    # 上传
    response = requests.post(
        MEDIA_UPLOAD_URL,
        auth=auth,
        data={'media_data': image_data}
    )

    if response.status_code != 200:
        raise Exception(f"图片上传失败: {response.status_code} - {response.text}")

    result = response.json()
    return result['media_id_string']


def post_tweet(text: str, media_ids: list = None) -> dict:
    """
    发送推文

    Args:
        text: 推文内容 (最多 280 字符)
        media_ids: 可选，媒体 ID 列表

    Returns:
        API 响应
    """
    auth = get_auth()

    payload = {"text": text}

    if media_ids:
        payload["media"] = {"media_ids": media_ids}

    response = requests.post(
        TWEET_URL,
        auth=auth,
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    return response.status_code, response.json()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='发送推文到 X (Twitter)')
    parser.add_argument('text', nargs='?', help='推文内容')
    parser.add_argument('-i', '--images', nargs='+', help='图片路径（支持多张，最多4张）')

    args = parser.parse_args()

    # 获取推文内容
    if args.text:
        text = args.text
    else:
        text = input("请输入推文内容: ")

    # 处理图片
    media_ids = []
    if args.images:
        print(f"正在上传 {len(args.images)} 张图片...")
        for i, img_path in enumerate(args.images[:4]):  # 最多4张
            try:
                media_id = upload_media(img_path)
                media_ids.append(media_id)
                print(f"  [{i+1}] {os.path.basename(img_path)} 上传成功")
            except Exception as e:
                print(f"  [{i+1}] {os.path.basename(img_path)} 上传失败: {e}")

    # 发送推文
    print(f"\n正在发送推文...")
    status_code, result = post_tweet(text, media_ids if media_ids else None)

    print(f"状态码: {status_code}")
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

    if "data" in result:
        tweet_id = result['data']['id']
        print(f"\n✓ 发送成功!")
        print(f"  推文 ID: {tweet_id}")
        print(f"  链接: https://x.com/i/status/{tweet_id}")
        return 0
    else:
        print(f"\n✗ 发送失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
