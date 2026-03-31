#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Perplexity Research Tool - 通过 OpenRouter 调用 Perplexity 进行网络调研

支持两种模式:
- sonar-pro-search: 快速搜索，适合简单问题
- sonar-deep-research: 深度研究，适合复杂调研
"""

import argparse
import json
import os
import sys
from datetime import datetime

import requests

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# 加载环境变量
if load_dotenv:
    dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    load_dotenv(dotenv_path, override=False)

# 模型常量
MODEL_QUICK = "perplexity/sonar-pro-search"
MODEL_DEEP = "perplexity/sonar-deep-research"

# OpenRouter API
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def get_api_key():
    """获取 OpenRouter API Key"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENROUTER_API_KEY environment variable")
    return api_key


def build_system_prompt(lang="zh"):
    """构建系统提示词"""
    if lang == "zh":
        return """你是一个专业的调研助手。请基于网络搜索结果，提供准确、全面的回答。

要求：
1. 回答要准确、有依据
2. 重要信息请标注来源
3. 使用中文回答
4. 结构清晰，易于阅读"""
    else:
        return """You are a professional research assistant. Provide accurate and comprehensive answers based on web search results.

Requirements:
1. Be accurate and well-sourced
2. Cite important information sources
3. Answer in English
4. Use clear structure"""


def call_perplexity(
    query: str,
    model: str = MODEL_QUICK,
    lang: str = "zh",
    temperature: float = 0.2,
    max_tokens: int = 4096,
    timeout: int = 120,
):
    """
    调用 Perplexity 模型

    Args:
        query: 调研问题
        model: 模型ID
        lang: 输出语言 (zh/en)
        temperature: 采样温度
        max_tokens: 最大输出token
        timeout: 请求超时(秒)

    Returns:
        tuple: (content, raw_response)
    """
    api_key = get_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "https://claude.ai"),
        "X-Title": os.getenv("OPENROUTER_APP_NAME", "perplexity-research"),
    }

    # 构建消息
    messages = [
        {"role": "system", "content": build_system_prompt(lang)},
        {"role": "user", "content": query},
    ]

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    # 发送请求
    response = requests.post(
        OPENROUTER_URL,
        json=payload,
        headers=headers,
        timeout=timeout,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"API request failed ({response.status_code}): {response.text}"
        )

    data = response.json()
    choices = data.get("choices")
    if not choices:
        raise RuntimeError(f"API response missing choices: {data}")

    content = choices[0]["message"]["content"]
    return content, data


def format_markdown_report(query: str, content: str, model: str) -> str:
    """格式化为 Markdown 报告"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    model_label = "深度研究" if "deep" in model else "快速搜索"

    report = f"""# 调研报告

## 问题
{query}

## 回答
{content}

---
**模型**: {model} ({model_label})
**时间**: {timestamp}
"""
    return report


def parse_args():
    parser = argparse.ArgumentParser(
        description="Perplexity Research Tool - 网络深度调研"
    )
    parser.add_argument(
        "--query", "-q",
        required=True,
        help="调研问题"
    )
    parser.add_argument(
        "--deep", "-d",
        action="store_true",
        help="使用深度研究模式 (sonar-deep-research)"
    )
    parser.add_argument(
        "--model", "-m",
        help="手动指定模型 (覆盖 --deep)"
    )
    parser.add_argument(
        "--lang", "-l",
        default="zh",
        choices=["zh", "en"],
        help="输出语言 (default: zh)"
    )
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=0.2,
        help="采样温度 (default: 0.2)"
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

    # 确定模型
    if args.model:
        model = args.model
    elif args.deep:
        model = MODEL_DEEP
    else:
        model = MODEL_QUICK

    # 显示正在使用的模型
    model_label = "深度研究" if "deep" in model else "快速搜索"
    print(f"[{model_label}] 正在调研: {args.query[:50]}...\n", file=sys.stderr)

    # 调用 API
    content, raw_response = call_perplexity(
        query=args.query,
        model=model,
        lang=args.lang,
        temperature=args.temperature,
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
        report = format_markdown_report(args.query, content, model)
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
