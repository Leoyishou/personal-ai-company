#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smoke test for OpenRouter connectivity.
"""

import sys

from openrouter_client import DEFAULT_OPENROUTER_MODEL, request_openrouter


def main():
    try:
        content, _raw = request_openrouter(
            DEFAULT_OPENROUTER_MODEL,
            [{"role": "user", "content": "请回复 ok 作为连通性测试"}],
            temperature=0.0,
            max_tokens=10,
        )
    except Exception as exc:
        print(f"❌ Smoke test failed: {exc}")
        return 1

    print(content.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
