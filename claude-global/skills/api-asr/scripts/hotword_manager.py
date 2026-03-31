#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
火山引擎热词管理工具

通过 API 创建、更新、删除热词表。
热词表创建后，可在语音识别时通过 --hotword-id 或 --hotword-name 参数使用。

使用方法：
    # 列出所有热词表
    python hotword_manager.py list --app-id YOUR_APP_ID

    # 创建热词表
    python hotword_manager.py create --app-id YOUR_APP_ID --name "AI术语" --file hotwords.txt

    # 从 JSON 转换并创建
    python hotword_manager.py create --app-id YOUR_APP_ID --name "AI术语" --json hotwords.json

    # 更新热词表
    python hotword_manager.py update --app-id YOUR_APP_ID --table-id xxx --file hotwords.txt

    # 删除热词表
    python hotword_manager.py delete --app-id YOUR_APP_ID --table-id xxx

环境变量：
    VOLC_ACCESS_KEY_ID: 火山引擎 AK
    VOLC_SECRET_ACCESS_KEY: 火山引擎 SK
"""

import argparse
import binascii
import datetime
import hashlib
import hmac
import json
import os
import sys
import urllib.parse

try:
    import requests
except ImportError:
    print("Error: requests library not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

# API 配置
DOMAIN = "open.volcengineapi.com"
REGION = "cn-north-1"
SERVICE = "speech_saas_prod"
VERSION = "2022-08-30"


def get_credentials():
    """获取 AK/SK"""
    ak = os.getenv("VOLC_ACCESS_KEY_ID")
    sk = os.getenv("VOLC_SECRET_ACCESS_KEY")

    if not ak or not sk:
        # 尝试从 secrets.env 加载
        secrets_path = os.path.expanduser("~/.claude/secrets.env")
        if os.path.exists(secrets_path):
            with open(secrets_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        if key == "VOLC_ACCESS_KEY_ID":
                            ak = value.strip().strip('"').strip("'")
                        elif key == "VOLC_SECRET_ACCESS_KEY":
                            sk = value.strip().strip('"').strip("'")

    if not ak or not sk:
        raise ValueError(
            "Missing credentials. Set VOLC_ACCESS_KEY_ID and VOLC_SECRET_ACCESS_KEY "
            "in environment or ~/.claude/secrets.env"
        )

    return ak, sk


def get_hmac_encode16(data: str) -> str:
    return binascii.b2a_hex(hashlib.sha256(data.encode("utf-8")).digest()).decode("ascii")


def get_volc_signature(secret_key: bytes, data: str) -> bytes:
    return hmac.new(secret_key, data.encode("utf-8"), digestmod=hashlib.sha256).digest()


def build_auth_headers(
    method: str,
    canonical_uri: str,
    canonical_query_string: str,
    content_type: str,
    payload_sign: str,
    ak: str,
    sk: str,
) -> dict:
    """构建带签名的请求头"""
    now = datetime.datetime.now(datetime.timezone.utc)
    utc_time_second = now.strftime("%Y%m%dT%H%M%SZ")
    utc_time_day = now.strftime("%Y%m%d")
    credential_scope = f"{utc_time_day}/{REGION}/{SERVICE}/request"

    canonical_headers = (
        f"content-type:{content_type}\n"
        f"host:{DOMAIN}\n"
        f"x-content-sha256:\n"
        f"x-date:{utc_time_second}\n"
    )
    signed_headers = "content-type;host;x-content-sha256;x-date"

    canonical_request = (
        f"{method}\n"
        f"{canonical_uri}\n"
        f"{canonical_query_string}\n"
        f"{canonical_headers}\n"
        f"{signed_headers}\n"
        f"{payload_sign}"
    )

    string_to_sign = (
        f"HMAC-SHA256\n"
        f"{utc_time_second}\n"
        f"{credential_scope}\n"
        f"{get_hmac_encode16(canonical_request)}"
    )

    signing_key = get_volc_signature(
        get_volc_signature(
            get_volc_signature(
                get_volc_signature(sk.encode("utf-8"), utc_time_day),
                REGION
            ),
            SERVICE
        ),
        "request"
    )
    signature = binascii.b2a_hex(get_volc_signature(signing_key, string_to_sign)).decode("ascii")

    return {
        "content-type": content_type,
        "x-date": utc_time_second,
        "Authorization": f"HMAC-SHA256 Credential={ak}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    }


def api_request(action: str, body: dict, ak: str, sk: str) -> dict:
    """发送 API 请求"""
    canonical_query_string = f"Action={action}&Version={VERSION}"
    url = f"https://{DOMAIN}/?{canonical_query_string}"

    content_type = "application/json; charset=utf-8"
    body_str = json.dumps(body)
    payload_sign = get_hmac_encode16(body_str)

    headers = build_auth_headers(
        "POST", "/", canonical_query_string, content_type, payload_sign, ak, sk
    )

    response = requests.post(url, headers=headers, data=body_str, timeout=30)

    try:
        result = response.json()
    except json.JSONDecodeError:
        raise RuntimeError(f"Invalid response: {response.text}")

    if response.status_code >= 400:
        error = result.get("ResponseMetadata", {}).get("Error", {})
        raise RuntimeError(f"API error: {error.get('Code')} - {error.get('Message')}")

    return result


def list_tables(app_id: int, ak: str, sk: str) -> list:
    """列出热词表"""
    body = {
        "Action": "ListBoostingTable",
        "Version": VERSION,
        "AppID": app_id,
        "PageNumber": 1,
        "PageSize": 100,
        "PreviewSize": 10,
    }

    result = api_request("ListBoostingTable", body, ak, sk)
    return result.get("Result", {}).get("BoostingTables", [])


def create_table(app_id: int, name: str, file_path: str, ak: str, sk: str) -> dict:
    """创建热词表（通过 multipart/form-data 上传文件）"""
    from datetime import datetime, timezone
    from requests_toolbelt import MultipartEncoder

    canonical_query_string = f"Action=CreateBoostingTable&Version={VERSION}"
    url = f"https://{DOMAIN}/?{canonical_query_string}"

    # 准备文件
    with open(file_path, "rb") as f:
        file_content = f.read()

    # 使用 MultipartEncoder 预构建 body
    encoder = MultipartEncoder(
        fields={
            "AppID": str(app_id),
            "BoostingTableName": name,
            "File": ("hotwords.txt", file_content, "text/plain"),
        }
    )
    body_bytes = encoder.to_string()
    content_type = encoder.content_type

    # 时间戳
    now = datetime.now(timezone.utc)
    utc_time_second = now.strftime("%Y%m%dT%H%M%SZ")
    utc_time_day = now.strftime("%Y%m%d")
    credential_scope = f"{utc_time_day}/{REGION}/{SERVICE}/request"

    # 计算 body 的 SHA256 hash
    body_hash = hashlib.sha256(body_bytes).hexdigest()

    # 构建规范请求
    canonical_headers = (
        f"content-type:{content_type}\n"
        f"host:{DOMAIN}\n"
        f"x-content-sha256:{body_hash}\n"
        f"x-date:{utc_time_second}\n"
    )
    signed_headers = "content-type;host;x-content-sha256;x-date"

    canonical_request = (
        f"POST\n"
        f"/\n"
        f"{canonical_query_string}\n"
        f"{canonical_headers}\n"
        f"{signed_headers}\n"
        f"{body_hash}"
    )

    string_to_sign = (
        f"HMAC-SHA256\n"
        f"{utc_time_second}\n"
        f"{credential_scope}\n"
        f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    )

    signing_key = get_volc_signature(
        get_volc_signature(
            get_volc_signature(
                get_volc_signature(sk.encode("utf-8"), utc_time_day),
                REGION
            ),
            SERVICE
        ),
        "request"
    )
    signature = binascii.b2a_hex(get_volc_signature(signing_key, string_to_sign)).decode("ascii")

    headers = {
        "Content-Type": content_type,
        "x-date": utc_time_second,
        "x-content-sha256": body_hash,
        "Authorization": f"HMAC-SHA256 Credential={ak}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    }

    response = requests.post(url, headers=headers, data=body_bytes, timeout=60)

    try:
        result = response.json()
    except json.JSONDecodeError:
        raise RuntimeError(f"Invalid response: {response.text}")

    if response.status_code >= 400 or "Error" in result.get("ResponseMetadata", {}):
        error = result.get("ResponseMetadata", {}).get("Error", {})
        raise RuntimeError(f"API error: {error.get('Code')} - {error.get('Message')}")

    return result.get("Result", {})


def delete_table(app_id: int, table_id: str, ak: str, sk: str) -> bool:
    """删除热词表"""
    body = {
        "Action": "DeleteBoostingTable",
        "Version": VERSION,
        "AppID": app_id,
        "BoostingTableID": table_id,
    }

    api_request("DeleteBoostingTable", body, ak, sk)
    return True


def json_to_txt(json_path: str, txt_path: str):
    """将 JSON 格式热词转换为 TXT 格式"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    hotwords = data.get("hotwords", data) if isinstance(data, dict) else data

    with open(txt_path, "w", encoding="utf-8") as f:
        for item in hotwords:
            if isinstance(item, dict):
                word = item.get("word", "")
                weight = item.get("weight", 4)
                if word:
                    # 确保词长度 <= 10
                    if len(word) <= 10:
                        f.write(f"{word}|{weight}\n")
                    else:
                        print(f"Warning: skipping '{word}' (> 10 chars)", file=sys.stderr)
            elif isinstance(item, str):
                if len(item) <= 10:
                    f.write(f"{item}|4\n")

    print(f"Converted {len(hotwords)} hotwords to {txt_path}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="火山引擎热词管理工具")
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # list 命令
    list_parser = subparsers.add_parser("list", help="列出热词表")
    list_parser.add_argument("--app-id", type=int, required=True, help="应用 ID")

    # create 命令
    create_parser = subparsers.add_parser("create", help="创建热词表")
    create_parser.add_argument("--app-id", type=int, required=True, help="应用 ID")
    create_parser.add_argument("--name", required=True, help="热词表名称")
    create_parser.add_argument("--file", help="热词文件路径 (TXT 格式)")
    create_parser.add_argument("--json", help="热词文件路径 (JSON 格式，会自动转换)")

    # delete 命令
    delete_parser = subparsers.add_parser("delete", help="删除热词表")
    delete_parser.add_argument("--app-id", type=int, required=True, help="应用 ID")
    delete_parser.add_argument("--table-id", required=True, help="热词表 ID")

    # convert 命令
    convert_parser = subparsers.add_parser("convert", help="转换 JSON 为 TXT 格式")
    convert_parser.add_argument("--input", required=True, help="输入 JSON 文件")
    convert_parser.add_argument("--output", required=True, help="输出 TXT 文件")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "convert":
        json_to_txt(args.input, args.output)
        return

    # 获取凭证
    try:
        ak, sk = get_credentials()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.command == "list":
        tables = list_tables(args.app_id, ak, sk)
        if not tables:
            print("No hotword tables found.")
        else:
            print(f"Found {len(tables)} hotword table(s):\n")
            for t in tables:
                print(f"  ID: {t['BoostingTableID']}")
                print(f"  Name: {t['BoostingTableName']}")
                print(f"  Words: {t.get('WordCount', 0)}")
                print(f"  Preview: {', '.join(t.get('Preview', [])[:5])}")
                print()

    elif args.command == "create":
        # 确定文件路径
        if args.json:
            # 转换 JSON 到临时 TXT
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
                txt_path = tmp.name
            json_to_txt(args.json, txt_path)
            file_path = txt_path
        elif args.file:
            file_path = args.file
        else:
            print("Error: must specify --file or --json", file=sys.stderr)
            sys.exit(1)

        if not os.path.exists(file_path):
            print(f"Error: file not found: {file_path}", file=sys.stderr)
            sys.exit(1)

        result = create_table(args.app_id, args.name, file_path, ak, sk)

        # 清理临时文件
        if args.json:
            os.unlink(txt_path)

        print(f"Created hotword table:")
        print(f"  ID: {result.get('BoostingTableID')}")
        print(f"  Name: {result.get('BoostingTableName')}")
        print(f"  Words: {result.get('WordCount', 0)}")
        print()
        print("Use in ASR:")
        print(f"  --hotword-id {result.get('BoostingTableID')}")
        print(f"  or --hotword-name {args.name}")

    elif args.command == "delete":
        delete_table(args.app_id, args.table_id, ak, sk)
        print(f"Deleted hotword table: {args.table_id}")


if __name__ == "__main__":
    main()
