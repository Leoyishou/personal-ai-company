#!/usr/bin/env python3
"""
通俗解释 - 调用 Gemini 生成通俗易懂的概念解释
内置模型: google/gemini-3-pro-preview
"""

import os
import json
import argparse
import requests
from pathlib import Path

# 加载环境变量
secrets_path = Path.home() / ".claude" / "secrets.env"
if secrets_path.exists():
    with open(secrets_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value.strip('"').strip("'")

# 配置
DEFAULT_MODEL = "google/gemini-3-pro-preview"
FALLBACK_MODELS = [
    "google/gemini-2.5-flash-preview-05-20",
    "google/gemini-2.0-flash-001",
    "anthropic/claude-3.5-sonnet",
]

SYSTEM_PROMPT = """你是一位擅长用通俗类比解释复杂概念的科普作家。

要求：
1. 用日常生活中的比喻来解释
2. 避免专业术语，用大白话
3. 如果是流程/系统，用「公司运营」「家庭生活」等场景类比
4. 结构清晰，分步骤/分模块
5. 每个要点控制在 15 字以内，便于可视化
6. 输出格式：JSON 数组，每个元素是一张图的内容
   [{"title": "图标题", "points": ["要点1", "要点2", "要点3"]}]

对于对比类概念，输出 2 个对象分别描述；
对于流程类概念，按阶段输出多个对象；
对于单一概念，输出 1-2 个对象。"""


def call_openrouter(model: str, prompt: str) -> tuple[str, bool]:
    """调用 OpenRouter API，返回 (响应内容, 是否成功)"""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not found in environment")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/liuyishou/claude-skills",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 2000,
    }

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )

        if resp.status_code != 200:
            error_msg = resp.json().get("error", {}).get("message", resp.text)
            return f"Error ({resp.status_code}): {error_msg}", False

        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return content, True

    except requests.exceptions.Timeout:
        return "Request timeout", False
    except Exception as e:
        return str(e), False


def extract_json(text: str) -> str:
    """从响应中提取 JSON 部分"""
    # 尝试找到 JSON 数组
    start = text.find("[")
    end = text.rfind("]") + 1
    if start != -1 and end > start:
        return text[start:end]
    return text


def main():
    parser = argparse.ArgumentParser(description="通俗解释概念")
    parser.add_argument("concept", help="要解释的概念")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="模型 ID")
    parser.add_argument("--hint", default="", help="额外的类比提示")
    args = parser.parse_args()

    # 构建 prompt
    prompt = f"请用通俗易懂的方式解释：{args.concept}"
    if args.hint:
        prompt += f"\n\n提示：{args.hint}"

    # 尝试主模型，失败则 fallback
    models_to_try = [args.model] + FALLBACK_MODELS

    for model in models_to_try:
        content, success = call_openrouter(model, prompt)
        if success:
            # 提取并输出 JSON
            json_content = extract_json(content)
            print(json_content)
            return
        else:
            # 如果是模型不存在的错误，尝试下一个
            if "not a valid model" in content.lower() or "invalid model" in content.lower():
                continue
            # 其他错误直接报错
            print(f"Error with {model}: {content}", file=__import__("sys").stderr)
            continue

    # 所有模型都失败
    print("All models failed", file=__import__("sys").stderr)
    exit(1)


if __name__ == "__main__":
    main()
