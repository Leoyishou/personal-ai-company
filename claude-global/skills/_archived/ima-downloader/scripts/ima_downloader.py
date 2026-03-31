#!/usr/bin/env python3
"""
IMA Copilot 知识库下载器

用法:
    python3 ima_downloader.py --name "知识库名称" --smoke-test    # 冒烟测试
    python3 ima_downloader.py --name "知识库名称" --download-all  # 完整下载
    python3 ima_downloader.py --id "知识库ID" --download-all      # 用 ID 下载

作者: Claude Code
"""

import os
import sys
import json
import time
import re
import argparse
import requests
from datetime import datetime
from urllib.parse import urlparse, unquote, parse_qs

# 配置
COOKIE_FILE = "/tmp/ima_cookie.txt"
BKN = "2065665700"  # 可能需要从 cookie 动态获取
API_BASE = "https://ima.qq.com/cgi-bin/knowledge_tab_reader"
DOWNLOAD_BASE = os.path.expanduser("~/Downloads/IMA_知识库")


def extract_kb_id(input_str):
    """
    从各种输入中提取知识库 ID
    支持:
    - 纯数字 ID: 7383025226642484
    - 完整 URL: https://ima.qq.com/knowledge/7383025226642484
    - 分享链接: https://ima.qq.com/share?knowledgeId=7383025226642484&...
    - 带参数的 URL: ...?knowledge_id=7383025226642484
    """
    input_str = input_str.strip()

    # 如果是纯数字，直接返回
    if input_str.isdigit() and len(input_str) > 10:
        return input_str

    # 尝试从 URL 中提取
    patterns = [
        r'knowledgeId[=:](\d+)',           # knowledgeId=xxx 或 knowledgeId:xxx
        r'knowledge_id[=:](\d+)',          # knowledge_id=xxx
        r'knowledge_base_id[=:](\d+)',     # knowledge_base_id=xxx
        r'/knowledge/(\d+)',               # /knowledge/xxx
        r'/kb/(\d+)',                       # /kb/xxx
        r'[?&]id=(\d+)',                   # ?id=xxx 或 &id=xxx
    ]

    for pattern in patterns:
        match = re.search(pattern, input_str, re.IGNORECASE)
        if match:
            return match.group(1)

    # 尝试找到任何长数字串 (可能是 ID)
    numbers = re.findall(r'\d{10,}', input_str)
    if len(numbers) == 1:
        return numbers[0]

    return None


def load_cookie():
    """加载 Cookie"""
    if not os.path.exists(COOKIE_FILE):
        print(f"错误: Cookie 文件不存在: {COOKIE_FILE}")
        print("请先从 IMA 应用获取 Cookie")
        sys.exit(1)
    with open(COOKIE_FILE, 'r') as f:
        return f.read().strip()


def get_headers():
    """获取请求头"""
    return {
        'Content-Type': 'application/json',
        'Cookie': load_cookie(),
        'x-ima-bkn': BKN,
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }


def get_joined_knowledge_bases():
    """获取用户加入的知识库列表"""
    url = f"{API_BASE}/get_joined_knowledge_base_list"
    payload = {
        "cursor": "",
        "limit": 50,
        "sort_type": 0
    }

    all_kbs = []
    while True:
        try:
            resp = requests.post(url, headers=get_headers(), json=payload, timeout=30)
            data = resp.json()
            if data.get('code') != 0:
                print(f"API 错误: {data.get('msg', 'Unknown')}")
                break

            kb_list = data.get('knowledge_base_list', [])
            all_kbs.extend(kb_list)

            if data.get('is_end', True):
                break

            payload['cursor'] = data.get('next_cursor', '')
            if not payload['cursor']:
                break

        except Exception as e:
            print(f"请求错误: {e}")
            break

    return all_kbs


def find_knowledge_base(name):
    """根据名称查找知识库"""
    kbs = get_joined_knowledge_bases()

    # 精确匹配
    for kb in kbs:
        if kb.get('title') == name:
            return kb

    # 模糊匹配
    matches = []
    name_lower = name.lower()
    for kb in kbs:
        title = kb.get('title', '')
        if name_lower in title.lower():
            matches.append(kb)

    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        print(f"找到多个匹配的知识库:")
        for i, kb in enumerate(matches, 1):
            print(f"  {i}. {kb.get('title')} (ID: {kb.get('knowledge_base_id')})")
        return None

    print(f"未找到名为 '{name}' 的知识库")
    print(f"已加入的知识库:")
    for kb in kbs[:10]:
        print(f"  - {kb.get('title')}")
    return None


def get_knowledge_list(kb_id, folder_id="", cursor="", limit=50):
    """获取知识库文件列表"""
    url = f"{API_BASE}/get_knowledge_list"
    payload = {
        "knowledge_base_id": kb_id,
        "folder_id": folder_id,
        "cursor": cursor,
        "limit": limit,
        "sort_type": 0,
        "need_default_cover": True,
        "compared_knowledge_base_id": "",
        "compared_folder_id": ""
    }

    try:
        resp = requests.post(url, headers=get_headers(), json=payload, timeout=30)
        data = resp.json()
        if data.get('code') == 0:
            return data
        # 显示具体的 API 错误
        error_code = data.get('code')
        error_msg = data.get('msg', 'Unknown')
        if error_code == 600001:
            print(f"\n错误: Cookie 可能已过期 (code: {error_code})")
            print("请重新获取 IMA Cookie 并保存到 /tmp/ima_cookie.txt")
            print("\n获取方法:")
            print("1. 打开 IMA Copilot 应用")
            print("2. 进入任意知识库")
            print("3. 使用 mitmproxy 或浏览器开发者工具捕获 Cookie")
        else:
            print(f"API 错误: code={error_code}, msg={error_msg}")
        return None
    except Exception as e:
        print(f"请求错误: {e}")
        return None


def get_all_files(kb_id, folder_id="", parent_path=""):
    """递归获取所有文件"""
    all_files = []
    cursor = ""

    while True:
        data = get_knowledge_list(kb_id, folder_id, cursor)
        if not data:
            break

        for item in data.get('knowledge_list', []):
            media_type = item.get('media_type')
            title = item.get('title', 'unknown')
            media_id = item.get('media_id', '')

            # 清理文件名
            clean_title = "".join(c for c in title if c not in '<>:"/\\|?*').strip()
            if not clean_title:
                clean_title = media_id

            item_path = os.path.join(parent_path, clean_title) if parent_path else clean_title

            if media_type == 99:  # 文件夹
                folder_id_inner = item.get('folder_info', {}).get('folder_id', '')
                sub_files = get_all_files(kb_id, folder_id_inner, item_path)
                all_files.extend(sub_files)
            else:
                file_info = {
                    'title': clean_title,
                    'path': item_path,
                    'media_id': media_id,
                    'media_type': media_type,
                    'raw_file_url': item.get('raw_file_url', ''),
                    'file_size': item.get('file_size', '0')
                }
                all_files.append(file_info)

        if data.get('is_end', True):
            break

        cursor = data.get('next_cursor', '')
        if not cursor:
            break

        time.sleep(0.3)

    return all_files


def get_signed_download_url(media_id, kb_id):
    """获取签名下载 URL"""
    url = f"{API_BASE}/get_knowledge"
    payload = {"knowledge_base_id": kb_id, "media_id": media_id}

    try:
        resp = requests.post(url, headers=get_headers(), json=payload, timeout=30)
        data = resp.json()
        if data.get('code') == 0:
            knowledge = data.get('knowledge', {})
            jump_url = knowledge.get('jump_url', '')
            if jump_url and 'sign=' in jump_url:
                return jump_url
        return None
    except:
        return None


def get_note_content(media_id, kb_id):
    """获取笔记内容"""
    url = f"{API_BASE}/get_knowledge"
    payload = {"knowledge_base_id": kb_id, "media_id": media_id}

    try:
        resp = requests.post(url, headers=get_headers(), json=payload, timeout=30)
        data = resp.json()
        if data.get('code') == 0:
            k = data.get('knowledge', {})
            return {
                'title': k.get('title', ''),
                'abstract': k.get('abstract', ''),
                'introduction': k.get('introduction', ''),
                'file_size': k.get('file_size', ''),
                'jump_url': k.get('jump_url', '')
            }
        return None
    except:
        return None


def smoke_test(kb_name=None, kb_id=None):
    """冒烟测试"""
    print("=" * 60)
    print("IMA 知识库冒烟测试")
    print("=" * 60)

    # 查找知识库
    if kb_name:
        print(f"\n正在搜索知识库: {kb_name}")
        kb = find_knowledge_base(kb_name)
        if not kb:
            return None
        kb_id = kb.get('knowledge_base_id')
        kb_title = kb.get('title')
    else:
        kb_title = f"ID: {kb_id}"

    print(f"\n找到知识库: {kb_title}")
    print(f"知识库 ID: {kb_id}")

    # 获取文件列表
    print("\n正在获取文件列表...")
    all_files = get_all_files(kb_id)

    # 统计
    downloadable = [f for f in all_files if '/' in f.get('raw_file_url', '')]
    notes = [f for f in all_files if f.get('raw_file_url', '').isdigit()]

    total_size = sum(int(f.get('file_size', 0)) for f in downloadable)

    print("\n" + "=" * 60)
    print("冒烟测试结果")
    print("=" * 60)
    print(f"知识库名称: {kb_title}")
    print(f"知识库 ID: {kb_id}")
    print(f"总文件数: {len(all_files)}")
    print(f"可下载文件: {len(downloadable)} 个")
    print(f"笔记数量: {len(notes)} 个")
    print(f"预计大小: {total_size / 1024 / 1024:.1f} MB")
    print("=" * 60)

    # 测试一个文件的下载
    if downloadable:
        print("\n测试下载第一个文件...")
        test_file = downloadable[0]
        url = get_signed_download_url(test_file['media_id'], kb_id)
        if url:
            try:
                resp = requests.head(url, timeout=10)
                if resp.status_code == 200:
                    print(f"✓ 下载测试成功: {test_file['title'][:40]}")
                else:
                    print(f"✗ 下载测试失败: HTTP {resp.status_code}")
            except Exception as e:
                print(f"✗ 下载测试失败: {e}")
        else:
            print("✗ 无法获取下载 URL")

    # 测试一个笔记
    if notes:
        print("\n测试获取第一个笔记...")
        test_note = notes[0]
        content = get_note_content(test_note['media_id'], kb_id)
        if content and (content.get('introduction') or content.get('abstract')):
            print(f"✓ 笔记测试成功: {test_note['title'][:40]}")
        else:
            print(f"✗ 笔记测试失败")

    print("\n" + "=" * 60)

    return {
        'kb_id': kb_id,
        'kb_title': kb_title,
        'total': len(all_files),
        'downloadable': len(downloadable),
        'notes': len(notes),
        'size_mb': total_size / 1024 / 1024,
        'files': all_files
    }


def download_all(kb_name=None, kb_id=None, files=None):
    """下载所有文件"""
    # 如果没有文件列表，先获取
    if not files:
        if kb_name:
            kb = find_knowledge_base(kb_name)
            if not kb:
                return
            kb_id = kb.get('knowledge_base_id')
            kb_title = kb.get('title')
        else:
            kb_title = f"ID_{kb_id}"

        print("正在获取文件列表...")
        files = get_all_files(kb_id)
    else:
        kb_title = kb_name or f"ID_{kb_id}"

    # 创建下载目录
    safe_title = "".join(c for c in kb_title if c not in '<>:"/\\|?*').strip()[:50]
    download_dir = os.path.join(DOWNLOAD_BASE, safe_title)
    files_dir = os.path.join(download_dir, "files")
    notes_dir = os.path.join(download_dir, "notes_摘要版")

    os.makedirs(files_dir, exist_ok=True)
    os.makedirs(notes_dir, exist_ok=True)

    # 分类文件
    downloadable = [f for f in files if '/' in f.get('raw_file_url', '')]
    notes = [f for f in files if f.get('raw_file_url', '').isdigit()]

    print(f"\n下载目录: {download_dir}")
    print(f"可下载文件: {len(downloadable)}")
    print(f"笔记: {len(notes)}")

    # 保存文件列表
    list_file = os.path.join(download_dir, 'file_list.json')
    with open(list_file, 'w', encoding='utf-8') as f:
        json.dump(files, f, ensure_ascii=False, indent=2)

    # 下载文件
    print("\n" + "=" * 40)
    print("开始下载文件...")
    print("=" * 40)

    success_files = 0
    failed_files = 0

    for i, file_info in enumerate(downloadable, 1):
        title = file_info['title'][:50]
        media_id = file_info['media_id']
        path = file_info.get('path', '')

        print(f"[{i}/{len(downloadable)}] {title}...")

        # 获取签名 URL
        download_url = get_signed_download_url(media_id, kb_id)
        if not download_url:
            print("  跳过 (无 URL)")
            failed_files += 1
            continue

        # 创建目录
        full_path = os.path.join(files_dir, path)
        dir_path = os.path.dirname(full_path)
        os.makedirs(dir_path, exist_ok=True)

        # 添加扩展名
        raw_url = file_info.get('raw_file_url', '')
        if '/' in raw_url:
            ext = os.path.splitext(raw_url)[1]
            if ext and not os.path.splitext(full_path)[1]:
                full_path = full_path + ext

        # 跳过已存在
        if os.path.exists(full_path):
            print("  已存在")
            success_files += 1
            continue

        # 下载
        try:
            resp = requests.get(download_url, timeout=120, stream=True)
            resp.raise_for_status()

            with open(full_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            size = os.path.getsize(full_path)
            print(f"  已下载 ({size:,} bytes)")
            success_files += 1
        except Exception as e:
            print(f"  失败: {e}")
            failed_files += 1

        time.sleep(0.3)

    # 导出笔记
    print("\n" + "=" * 40)
    print("开始导出笔记摘要...")
    print("=" * 40)

    success_notes = 0
    failed_notes = 0

    for i, note in enumerate(notes, 1):
        title = note['title'][:50]
        media_id = note['media_id']
        path = note.get('path', '')

        print(f"[{i}/{len(notes)}] {title}...")

        content = get_note_content(media_id, kb_id)
        if not content:
            print("  跳过 (无内容)")
            failed_notes += 1
            continue

        intro = content.get('introduction', '')
        abstract = content.get('abstract', '')

        if not intro and not abstract:
            print("  跳过 (空)")
            failed_notes += 1
            continue

        # 创建目录
        full_dir = os.path.join(notes_dir, os.path.dirname(path)) if path else notes_dir
        os.makedirs(full_dir, exist_ok=True)

        # 清理文件名
        clean_title = "".join(c for c in note['title'] if c not in '<>:"/\\|?*').strip()[:80]
        filename = f"[摘要] {clean_title}.md"
        filepath = os.path.join(full_dir, filename)

        # 写入 Markdown
        md = f"""# {content['title']}

> **注意**: 这是摘要版本，可能不完整。原始大小: {content.get('file_size', 'N/A')} 字节
> [在 IMA 中查看]({content.get('jump_url', '')})

## AI 摘要
{abstract or '无'}

## 内容预览
{intro or '无'}

---
*导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md)

        print(f"  已保存 (摘要:{len(abstract)}字, 预览:{len(intro)}字)")
        success_notes += 1

        time.sleep(0.3)

    # 报告结果
    print("\n" + "=" * 60)
    print("下载完成!")
    print("=" * 60)
    print(f"文件下载: {success_files} 成功, {failed_files} 失败")
    print(f"笔记导出: {success_notes} 成功, {failed_notes} 失败")
    print(f"保存位置: {download_dir}")

    # 计算总大小
    total_size = 0
    for root, dirs, files_list in os.walk(download_dir):
        for f in files_list:
            total_size += os.path.getsize(os.path.join(root, f))

    print(f"总大小: {total_size / 1024 / 1024:.1f} MB")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='IMA 知识库下载器',
        epilog='''
示例:
  %(prog)s "https://ima.qq.com/share?knowledgeId=7383025226642484"  # 从分享链接下载
  %(prog)s 7383025226642484                                         # 直接用 ID
  %(prog)s --id 7383025226642484 --smoke-test                       # 仅冒烟测试
  %(prog)s --id 7383025226642484 --download-all                     # 完整下载

获取分享链接:
  1. 打开 IMA 应用，进入知识库
  2. 点击右上角"分享"按钮
  3. 复制链接，粘贴到这里
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('input', nargs='?', help='知识库 ID 或分享链接 (最简单的方式)')
    parser.add_argument('--id', '-i', help='知识库 ID')
    parser.add_argument('--smoke-test', '-s', action='store_true', help='仅执行冒烟测试')
    parser.add_argument('--download-all', '-d', action='store_true', help='下载所有文件')

    args = parser.parse_args()

    # 从各种输入中提取 KB ID
    kb_id = None

    if args.input:
        kb_id = extract_kb_id(args.input)
        if not kb_id:
            print(f"错误: 无法从输入中提取知识库 ID")
            print(f"输入: {args.input}")
            print()
            print("请提供以下格式之一:")
            print("  - 分享链接: https://ima.qq.com/share?knowledgeId=xxx")
            print("  - 知识库 ID: 7383025226642484")
            print()
            print("获取分享链接的方法:")
            print("  1. 打开 IMA 应用，进入目标知识库")
            print("  2. 点击右上角「分享」按钮")
            print("  3. 复制链接，粘贴到这里")
            return

    if args.id:
        kb_id = extract_kb_id(args.id)

    if not kb_id:
        parser.print_help()
        return

    print(f"知识库 ID: {kb_id}")

    if args.smoke_test:
        smoke_test(kb_id=kb_id)
    elif args.download_all:
        download_all(kb_id=kb_id)
    else:
        # 默认执行冒烟测试
        smoke_test(kb_id=kb_id)


if __name__ == '__main__':
    main()
