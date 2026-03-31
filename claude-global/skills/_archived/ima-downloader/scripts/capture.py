#!/usr/bin/env python3
"""
IMA Cookie & ID 自动抓取脚本
运行后打开 IMA 应用进入目标知识库，自动获取 Cookie 和知识库 ID
"""
from mitmproxy import ctx
import re

seen_ids = set()
cookie_saved = False

def request(flow):
    global cookie_saved

    if "ima.qq.com" not in flow.request.host:
        return

    # 保存 Cookie
    cookie = flow.request.headers.get("cookie", "")
    if cookie and "IMA-TOKEN" in cookie and not cookie_saved:
        with open("/tmp/ima_cookie.txt", "w") as f:
            f.write(cookie)
        cookie_saved = True
        ctx.log.info("✓ Cookie 已保存到 /tmp/ima_cookie.txt")

    # 从请求体提取 knowledge_base_id
    if flow.request.content:
        try:
            body = flow.request.content.decode('utf-8')
            matches = re.findall(r'"knowledge_base_id"\s*:\s*"?(\d+)"?', body)
            for kb_id in matches:
                if kb_id not in seen_ids:
                    seen_ids.add(kb_id)
                    print()
                    print("=" * 50)
                    print(f"✓ 发现知识库 ID: {kb_id}")
                    print("=" * 50)
                    print()
                    print("下载命令:")
                    print(f"  python3 ~/.claude/skills/ima-downloader/scripts/ima_downloader.py {kb_id}")
                    print()
        except:
            pass
