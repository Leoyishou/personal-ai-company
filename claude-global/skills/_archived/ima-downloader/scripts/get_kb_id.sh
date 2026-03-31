#!/bin/bash
# 自动抓取 IMA 知识库 ID
# 用法: ./get_kb_id.sh

echo "=========================================="
echo "IMA 知识库 ID 抓取工具"
echo "=========================================="
echo ""
echo "步骤:"
echo "1. 脚本会启动 mitmproxy 代理"
echo "2. 打开 IMA 应用，进入目标知识库"
echo "3. 脚本会自动提取 knowledge_base_id"
echo ""
echo "按 Ctrl+C 退出"
echo ""

# 启动 mitmproxy 并过滤 IMA 请求
mitmdump --mode local:ima-copilot -p 8888 --quiet \
  -s <(cat << 'PYTHON'
from mitmproxy import ctx
import re
import json

seen_ids = set()

def request(flow):
    if "ima.qq.com" in flow.request.host:
        # 保存 Cookie
        cookie = flow.request.headers.get("cookie", "")
        if cookie and "IMA-TOKEN" in cookie:
            with open("/tmp/ima_cookie.txt", "w") as f:
                f.write(cookie)

        # 从请求体提取 knowledge_base_id
        if flow.request.content:
            try:
                body = flow.request.content.decode('utf-8')
                matches = re.findall(r'"knowledge_base_id"\s*:\s*"?(\d+)"?', body)
                for kb_id in matches:
                    if kb_id not in seen_ids:
                        seen_ids.add(kb_id)
                        print(f"\n{'='*50}")
                        print(f"发现知识库 ID: {kb_id}")
                        print(f"{'='*50}")
                        print(f"\n使用命令下载:")
                        print(f"  python3 ~/.claude/skills/ima-downloader/scripts/ima_downloader.py {kb_id}")
                        print()
            except:
                pass
PYTHON
)
