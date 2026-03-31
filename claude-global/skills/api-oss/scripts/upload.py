#!/usr/bin/env python3
"""
阿里云 OSS 文件上传工具

使用方法:
    python upload.py /path/to/file.mp3

输出:
    https://imagehosting4picgo.oss-cn-beijing.aliyuncs.com/tmp/file_a1b2c3d4.mp3
"""

import os
import sys
import secrets
from pathlib import Path

import oss2


def load_env():
    """从 secrets.env 加载环境变量"""
    secrets_path = Path.home() / ".claude" / "secrets.env"
    if secrets_path.exists():
        with open(secrets_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    # 处理 export 前缀
                    if line.startswith("export "):
                        line = line[7:]
                    key, _, value = line.partition("=")
                    # 去掉引号
                    value = value.strip('"\'')
                    if key not in os.environ:
                        os.environ[key] = value


def upload_to_oss(file_path: str) -> str:
    """
    上传文件到 OSS

    Args:
        file_path: 本地文件路径

    Returns:
        公网访问 URL
    """
    load_env()

    access_key_id = os.environ.get("ALIYUN_OSS_ACCESS_KEY_ID")
    access_key_secret = os.environ.get("ALIYUN_OSS_ACCESS_KEY_SECRET")
    bucket_name = os.environ.get("ALIYUN_OSS_BUCKET", "imagehosting4picgo")
    region = os.environ.get("ALIYUN_OSS_REGION", "oss-cn-beijing")

    if not access_key_id or not access_key_secret:
        raise ValueError("OSS credentials not found in environment")

    # 构建 endpoint
    endpoint = f"https://{region}.aliyuncs.com"

    # 创建 bucket 对象
    auth = oss2.Auth(access_key_id, access_key_secret)
    bucket = oss2.Bucket(auth, endpoint, bucket_name)

    # 生成 OSS key
    path = Path(file_path)
    random_suffix = secrets.token_hex(4)
    oss_key = f"tmp/{path.stem}_{random_suffix}{path.suffix}"

    # 上传文件
    with open(file_path, "rb") as f:
        bucket.put_object(oss_key, f)

    # 返回公网 URL
    url = f"https://{bucket_name}.{region}.aliyuncs.com/{oss_key}"
    return url


def main():
    if len(sys.argv) < 2:
        print("Usage: python upload.py <file_path>", file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    try:
        url = upload_to_oss(file_path)
        print(url)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
