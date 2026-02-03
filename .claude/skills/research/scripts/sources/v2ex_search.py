#!/usr/bin/env python3
"""
V2EX 搜索工具 - 基于 SOV2EX API

使用第三方 SOV2EX 搜索引擎 API 搜索 V2EX 帖子。
"""

import argparse
import json
import sys
from datetime import datetime
from urllib.parse import quote
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


SOV2EX_API = "https://www.sov2ex.com/api/search"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def search_v2ex(
    query: str,
    size: int = 10,
    sort: str = "relevance",  # relevance, created
    node: str = None,
) -> dict:
    """
    搜索 V2EX 帖子

    Args:
        query: 搜索关键词
        size: 返回结果数量 (max 50)
        sort: 排序方式 (relevance=相关性, created=时间)
        node: 限定节点 (如 python, apple, programmer)

    Returns:
        搜索结果字典
    """
    params = f"q={quote(query)}&from=0&size={min(size, 50)}"
    if sort == "created":
        params += "&sort=created:desc"
    if node:
        params += f"&node={node}"

    url = f"{SOV2EX_API}?{params}"

    req = Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data
    except HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}", file=sys.stderr)
        return None
    except URLError as e:
        print(f"URL Error: {e.reason}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}", file=sys.stderr)
        return None


def format_results(data: dict, query: str) -> str:
    """格式化搜索结果为 Markdown"""
    if not data or "hits" not in data:
        return f"搜索「{query}」无结果"

    total = data.get("total", 0)
    hits = data.get("hits", [])
    took = data.get("took", 0)

    lines = [
        f"### V2EX 搜索结果：「{query}」",
        f"",
        f"共 {total} 条结果，耗时 {took}ms",
        f"",
    ]

    for i, hit in enumerate(hits, 1):
        source = hit.get("_source", {})
        highlight = hit.get("highlight", {})

        title = source.get("title", "无标题")
        content = source.get("content", "")[:200]
        member = source.get("member", "匿名")
        replies = source.get("replies", 0)
        created = source.get("created", "")
        topic_id = source.get("id", "")
        node = source.get("node", "")

        # 格式化时间
        if created:
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                created_str = dt.strftime("%Y-%m-%d")
            except:
                created_str = created[:10]
        else:
            created_str = "未知"

        # 使用高亮内容（如果有）
        if "content" in highlight and highlight["content"]:
            # 移除 HTML 标签
            content_preview = highlight["content"][0]
            content_preview = content_preview.replace("<em>", "**").replace("</em>", "**")
        else:
            content_preview = content[:150] + "..." if len(content) > 150 else content

        url = f"https://www.v2ex.com/t/{topic_id}"

        lines.append(f"**{i}. [{title}]({url})**")
        lines.append(f"   - 作者: @{member} | 回复: {replies} | 时间: {created_str}")
        lines.append(f"   - {content_preview}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="V2EX 搜索工具")
    parser.add_argument("--query", "-q", required=True, help="搜索关键词")
    parser.add_argument("--size", "-n", type=int, default=10, help="结果数量 (默认 10)")
    parser.add_argument(
        "--sort",
        "-s",
        choices=["relevance", "created"],
        default="relevance",
        help="排序方式 (默认 relevance)",
    )
    parser.add_argument("--node", help="限定节点 (如 python, apple)")
    parser.add_argument("--json", action="store_true", help="输出原始 JSON")

    args = parser.parse_args()

    print(f"[V2EX 搜索] 关键词: {args.query}", file=sys.stderr)

    data = search_v2ex(
        query=args.query,
        size=args.size,
        sort=args.sort,
        node=args.node,
    )

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(format_results(data, args.query))


if __name__ == "__main__":
    main()
