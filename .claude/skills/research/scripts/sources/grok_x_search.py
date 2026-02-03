#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grok X/Twitter Search Tool - 通过 xAI API 搜索 X/Twitter 实时公开内容

使用 Grok 的 x_search 工具进行：
- 关键词搜索
- 用户推文搜索
- 时间范围过滤
- 媒体内容理解
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

import requests

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# 加载环境变量
if load_dotenv:
    # 尝试加载本地 .env
    dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    load_dotenv(dotenv_path, override=False)
    # 也加载全局 secrets.env
    secrets_path = os.path.expanduser("~/.claude/secrets.env")
    if os.path.exists(secrets_path):
        load_dotenv(secrets_path, override=False)

# xAI API 配置 - 使用 Responses API (Agent Tools 需要)
XAI_API_URL = "https://api.x.ai/v1/responses"
DEFAULT_MODEL = "grok-4-1-fast"  # server-side tools 只支持 grok-4 系列


def get_api_key():
    """获取 xAI API Key"""
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        raise ValueError(
            "Missing XAI_API_KEY environment variable. "
            "Get your key from https://console.x.ai/"
        )
    return api_key


def build_system_prompt(lang="zh"):
    """构建系统提示词"""
    if lang == "zh":
        return """你是一个专业的社交媒体分析助手。请基于 X/Twitter 搜索结果，提供准确的分析和总结。

要求：
1. 客观呈现搜索到的推文内容
2. 标注重要推文的作者和时间
3. 使用中文回答
4. 如有争议性内容，呈现多方观点"""
    else:
        return """You are a professional social media analyst. Analyze and summarize X/Twitter search results.

Requirements:
1. Present tweet content objectively
2. Note author and timestamp for important tweets
3. Answer in English
4. Present multiple perspectives for controversial topics"""


def call_grok_x_search(
    query: str,
    users: list = None,
    from_date: str = None,
    to_date: str = None,
    model: str = DEFAULT_MODEL,
    lang: str = "zh",
    enable_image: bool = False,
    enable_video: bool = False,
    max_tokens: int = 4096,
    timeout: int = 120,
):
    """
    调用 Grok 的 x_search 工具

    Args:
        query: 搜索关键词
        users: 限定用户列表 (e.g., ["elonmusk", "sama"])
        from_date: 开始日期 (YYYY-MM-DD)
        to_date: 结束日期 (YYYY-MM-DD)
        model: Grok 模型
        lang: 输出语言 (zh/en)
        enable_image: 启用图片理解
        enable_video: 启用视频理解
        max_tokens: 最大输出 token
        timeout: 请求超时(秒)

    Returns:
        tuple: (content, raw_response)
    """
    api_key = get_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 构建用户消息
    user_message = f"搜索 X/Twitter 上关于「{query}」的最新讨论和观点。"
    if users:
        user_message += f" 重点关注以下用户：{', '.join(users)}。"
    if from_date or to_date:
        date_range = ""
        if from_date:
            date_range += f"从 {from_date} "
        if to_date:
            date_range += f"到 {to_date}"
        user_message += f" 时间范围：{date_range}。"

    user_message += " 请总结主要观点、热门推文和讨论趋势。"

    # 构建输入 - Responses API 使用 input 字段
    input_messages = [
        {"role": "system", "content": build_system_prompt(lang)},
        {"role": "user", "content": user_message},
    ]

    # 构建 x_search 工具配置 - Responses API 格式
    # 参考: https://docs.x.ai/docs/guides/tools/overview
    x_search_tool = {
        "type": "x_search",
    }
    if users:
        x_search_tool["allowed_x_handles"] = users
    if from_date:
        x_search_tool["from_date"] = from_date
    if to_date:
        x_search_tool["to_date"] = to_date
    if enable_image:
        x_search_tool["enable_image_understanding"] = True
    if enable_video:
        x_search_tool["enable_video_understanding"] = True

    payload = {
        "model": model,
        "input": input_messages,
        "tools": [x_search_tool],
    }

    # 发送请求
    response = requests.post(
        XAI_API_URL,
        json=payload,
        headers=headers,
        timeout=timeout,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"API request failed ({response.status_code}): {response.text}"
        )

    data = response.json()

    # Responses API 返回格式解析
    # output 数组包含 tool_call 和最终的 output_text
    if "output" in data:
        output = data.get("output", [])
        content_parts = []
        for item in output:
            # 查找包含 content 数组的 item
            if "content" in item:
                for block in item.get("content", []):
                    if block.get("type") == "output_text":
                        content_parts.append(block.get("text", ""))
                    elif block.get("type") == "text":
                        content_parts.append(block.get("text", ""))
        content = "\n".join(content_parts)
    elif "choices" in data:
        # 旧 Chat Completions 格式 (兼容)
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError(f"API response missing content: {data}")
        content = choices[0]["message"]["content"]
    else:
        raise RuntimeError(f"Unexpected API response format: {data}")

    return content, data


def format_markdown_report(query: str, content: str, users: list = None) -> str:
    """格式化为 Markdown 报告"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    user_info = ""
    if users:
        user_info = f"\n**关注用户**: {', '.join(['@' + u for u in users])}"

    report = f"""# X/Twitter 搜索报告

## 搜索条件
**关键词**: {query}{user_info}
**时间**: {timestamp}

## 搜索结果

{content}

---
**数据来源**: xAI Grok x_search API
**声明**: 仅包含公开推文，不包含私密账号或私信内容
"""
    return report


def parse_args():
    parser = argparse.ArgumentParser(
        description="Grok X/Twitter Search - 搜索 X/Twitter 实时内容"
    )
    parser.add_argument(
        "--query", "-q",
        required=True,
        help="搜索关键词"
    )
    parser.add_argument(
        "--users", "-u",
        help="限定用户，逗号分隔 (e.g., elonmusk,sama)"
    )
    parser.add_argument(
        "--from",
        dest="from_date",
        help="开始日期 (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--to",
        dest="to_date",
        help="结束日期 (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help=f"Grok 模型 (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--lang", "-l",
        default="zh",
        choices=["zh", "en"],
        help="输出语言 (default: zh)"
    )
    parser.add_argument(
        "--image",
        action="store_true",
        help="启用图片理解"
    )
    parser.add_argument(
        "--video",
        action="store_true",
        help="启用视频理解"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="最大输出 token (default: 4096)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="请求超时秒数 (default: 120)"
    )
    parser.add_argument(
        "--output", "-o",
        help="保存结果到 Markdown 文件"
    )
    parser.add_argument(
        "--output-json",
        help="保存完整 JSON 响应"
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="输出完整 JSON 响应"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # 默认日期：如果没有指定日期范围，使用最近7天
    from_date = args.from_date
    to_date = args.to_date
    if not from_date and not to_date:
        today = datetime.now()
        from_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        to_date = today.strftime("%Y-%m-%d")
    elif not to_date:
        to_date = datetime.now().strftime("%Y-%m-%d")

    # 解析用户列表
    users = None
    if args.users:
        users = [u.strip().lstrip("@") for u in args.users.split(",")]

    # 显示搜索信息
    print(f"[X/Twitter 搜索] 关键词: {args.query}", file=sys.stderr)
    print(f"[X/Twitter 搜索] 日期范围: {from_date} ~ {to_date}", file=sys.stderr)
    if users:
        print(f"[X/Twitter 搜索] 用户: {', '.join(users)}", file=sys.stderr)
    print("", file=sys.stderr)

    # 调用 API
    content, raw_response = call_grok_x_search(
        query=args.query,
        users=users,
        from_date=from_date,
        to_date=to_date,
        model=args.model,
        lang=args.lang,
        enable_image=args.image,
        enable_video=args.video,
        max_tokens=args.max_tokens,
        timeout=args.timeout,
    )

    # 保存 JSON 响应
    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(raw_response, f, ensure_ascii=False, indent=2)
        print(f"JSON 已保存到: {args.output_json}", file=sys.stderr)

    # 保存 Markdown 报告
    if args.output:
        report = format_markdown_report(args.query, content, users)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"报告已保存到: {args.output}", file=sys.stderr)

    # 输出结果
    if args.print_json:
        print(json.dumps(raw_response, ensure_ascii=False, indent=2))
    else:
        print(content)


if __name__ == "__main__":
    main()
