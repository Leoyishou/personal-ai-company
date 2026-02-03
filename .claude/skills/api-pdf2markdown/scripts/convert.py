#!/usr/bin/env python3
"""
MinerU 文档转换脚本
将 PDF 转换为 Markdown/JSON 格式
支持本地处理和官方云 API
"""

import argparse
import subprocess
import sys
import os
import shutil
import time
import json
import requests
from pathlib import Path

# 官方 API 配置
MINERU_API_BASE = "https://mineru.net/api/v4"
DEFAULT_API_TOKEN = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI5ODkwMDgzNiIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc2OTM5ODA0OCwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiOWE3YThmMDAtNmU5ZC00MTU4LWE0NGMtYTQwZDg5MDI1MTFiIiwiZW1haWwiOiIiLCJleHAiOjE3NzA2MDc2NDh9.nXLV8nX1PA-MsDJjlpDuUiRI-e7Evs-4effvJUGOLbEH-T93JSgs9kNAhdKmw5rsSIfIZVRVQDdk5KuDdKAePg"


def check_mineru_installed():
    """检查 mineru 是否已安装"""
    return shutil.which("mineru") is not None


def install_mineru():
    """安装 mineru"""
    print("MinerU 未安装，正在安装...")
    if shutil.which("uv"):
        cmd = ["uv", "pip", "install", "-U", "mineru[all]"]
    else:
        cmd = [sys.executable, "-m", "pip", "install", "-U", "mineru[all]"]
    try:
        subprocess.run(cmd, check=True)
        print("MinerU 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"安装失败: {e}")
        return False


def detect_backend():
    """检测合适的后端"""
    import platform
    if platform.system() == "Darwin":
        return "pipeline"
    try:
        result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
        if result.returncode == 0:
            return "hybrid-auto-engine"
    except FileNotFoundError:
        pass
    return "pipeline"


def api_get_upload_url(file_name: str, token: str) -> dict:
    """获取预签名上传 URL"""
    url = f"{MINERU_API_BASE}/file-urls/batch"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "files": [{"name": file_name, "is_ocr": False}],
        "enable_formula": True,
        "enable_table": True,
    }

    print(f"请求上传 URL...")
    res = requests.post(url, headers=headers, json=data)
    if res.status_code != 200:
        raise Exception(f"获取上传 URL 失败: {res.status_code} - {res.text}")

    result = res.json()
    if result.get("code") != 0:
        raise Exception(f"API 错误: {result.get('msg')}")

    return result["data"]


def api_upload_file(file_path: Path, presigned_url: str):
    """上传文件到预签名 URL"""
    print(f"上传文件到云端...")

    with open(file_path, "rb") as f:
        file_content = f.read()

    # 使用 PUT 方法上传到 OSS（不加额外 header，预签名 URL 已包含签名）
    res = requests.put(presigned_url, data=file_content)

    if res.status_code not in [200, 201]:
        raise Exception(f"文件上传失败: {res.status_code} - {res.text}")

    print(f"文件上传成功 ({len(file_content) / 1024 / 1024:.2f} MB)")


def api_check_status(batch_id: str, token: str) -> dict:
    """查询任务状态"""
    url = f"{MINERU_API_BASE}/extract-results/batch/{batch_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        raise Exception(f"查询状态失败: {res.status_code} - {res.text}")

    return res.json()


def api_download_result(result_url: str, output_dir: Path, filename: str):
    """下载解析结果"""
    print(f"下载结果...")
    res = requests.get(result_url)
    if res.status_code != 200:
        raise Exception(f"下载失败: {res.status_code}")

    # 结果是 zip 文件
    zip_path = output_dir / f"{filename}.zip"
    with open(zip_path, "wb") as f:
        f.write(res.content)

    # 解压
    import zipfile
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)

    # 删除 zip
    zip_path.unlink()
    print(f"结果已保存到: {output_dir}")


def convert_with_api(input_path: Path, output_dir: Path, token: str):
    """使用官方云 API 转换文档"""
    print(f"使用 MinerU 官方云 API")
    print(f"输入: {input_path}")
    print("-" * 50)

    # 1. 获取上传 URL
    upload_info = api_get_upload_url(input_path.name, token)
    batch_id = upload_info["batch_id"]
    presigned_url = upload_info["file_urls"][0]

    print(f"Batch ID: {batch_id}")

    # 2. 上传文件
    api_upload_file(input_path, presigned_url)

    # 3. 轮询等待完成（上传后系统自动开始处理）
    print("等待解析完成", end="", flush=True)
    max_wait = 600  # 最多等待 10 分钟
    wait_time = 0
    poll_interval = 3

    while wait_time < max_wait:
        time.sleep(poll_interval)
        wait_time += poll_interval
        print(".", end="", flush=True)

        status = api_check_status(batch_id, token)
        if status.get("code") != 0:
            print()
            raise Exception(f"查询失败: {status.get('msg')}")

        data = status.get("data", {})
        extract_result = data.get("extract_result", [])

        if extract_result:
            file_result = extract_result[0]
            state = file_result.get("state")

            if state == "done":
                print(" 完成!")
                # 下载结果
                full_zip_url = file_result.get("full_zip_url")
                if full_zip_url:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    api_download_result(full_zip_url, output_dir, input_path.stem)

                    # 列出输出文件
                    print("\n生成的文件:")
                    for f in output_dir.rglob("*"):
                        if f.is_file():
                            print(f"  - {f.relative_to(output_dir)}")
                return
            elif state == "failed":
                print()
                raise Exception(f"解析失败: {file_result.get('err_msg', '未知错误')}")
            elif state == "waiting-file":
                # 文件还没被识别，继续等待
                pass
            # 其他状态继续轮询

    print()
    raise Exception("等待超时，请稍后查询结果")


def convert_local(input_path: Path, output_dir: Path, backend: str = None, lang: str = "ch"):
    """使用本地 mineru 转换"""
    if not input_path.exists():
        print(f"错误: 输入文件不存在: {input_path}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    if backend is None:
        backend = detect_backend()
        print(f"自动选择后端: {backend}")

    cmd = [
        "mineru",
        "-p", str(input_path),
        "-o", str(output_dir),
        "-b", backend,
        "-l", lang
    ]

    print(f"执行: {' '.join(cmd)}")
    print("-" * 50)

    try:
        subprocess.run(cmd, check=True)
        print("-" * 50)
        print(f"转换完成！输出目录: {output_dir}")

        print("\n生成的文件:")
        for f in output_dir.rglob("*"):
            if f.is_file():
                print(f"  - {f.relative_to(output_dir)}")

    except subprocess.CalledProcessError as e:
        print(f"转换失败: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="MinerU 文档转换工具 - 将 PDF 转为 Markdown/JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用云 API (推荐，精度最高)
  %(prog)s document.pdf --api

  # 本地处理 (Mac 推荐 pipeline)
  %(prog)s document.pdf -b pipeline

  # 指定输出目录
  %(prog)s document.pdf -o ./output --api
"""
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="输入 PDF 文件或目录路径"
    )
    parser.add_argument(
        "-o", "--output",
        default="./mineru_output",
        help="输出目录 (默认: ./mineru_output)"
    )
    parser.add_argument(
        "-b", "--backend",
        choices=["pipeline", "hybrid-auto-engine", "vlm-auto-engine"],
        help="本地解析后端 (默认: 自动选择)"
    )
    parser.add_argument(
        "-l", "--lang",
        default="ch",
        choices=["ch", "en", "japan", "korean", "chinese_cht", "latin", "arabic"],
        help="OCR 语言 (默认: ch)"
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="使用官方云 API (精度最高)"
    )
    parser.add_argument(
        "--token",
        default=DEFAULT_API_TOKEN,
        help="API Token (默认使用内置 token)"
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="仅安装 MinerU 不执行转换"
    )

    args = parser.parse_args()

    # 仅安装模式
    if args.install:
        if not check_mineru_installed():
            if not install_mineru():
                sys.exit(1)
            print("安装完成")
        else:
            print("MinerU 已安装")
        sys.exit(0)

    # 需要输入文件
    if not args.input:
        parser.error("请指定输入文件路径")

    input_path = Path(args.input).resolve()
    output_dir = Path(args.output).resolve()

    if not input_path.exists():
        print(f"错误: 文件不存在: {input_path}")
        sys.exit(1)

    # 选择处理方式
    if args.api:
        convert_with_api(input_path, output_dir, args.token)
    else:
        # 本地处理需要安装
        if not check_mineru_installed():
            if not install_mineru():
                sys.exit(1)
        convert_local(input_path, output_dir, args.backend, args.lang)


if __name__ == "__main__":
    main()
