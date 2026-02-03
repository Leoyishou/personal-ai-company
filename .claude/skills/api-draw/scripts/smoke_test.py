#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smoke test for Nanobanana image generation.
"""

import sys

from nanobanana_client import generate_image


def run_smoke_test():
    """Run a simple smoke test to verify the setup."""
    print("🚀 开始 Nanobanana 画图功能测试...\n")

    test_prompt = "画一只可爱的橘猫,简笔画风格"

    try:
        print(f"📝 测试 Prompt: {test_prompt}")
        print("⏳ 正在生成图片...\n")

        content, raw = generate_image(
            prompt=test_prompt,
            temperature=0.7,
        )

        print("✅ 测试成功!")
        print(f"\n📊 响应信息:")
        print(f"  - 模型: {raw.get('model', 'N/A')}")
        print(f"  - 总 tokens: {raw.get('usage', {}).get('total_tokens', 'N/A')}")
        print(f"\n💬 生成内容:")
        print(f"  {content[:200]}..." if len(content) > 200 else f"  {content}")

        return 0

    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        print("\n💡 提示: 请确保已设置 OPENROUTER_API_KEY 环境变量")
        print("   export OPENROUTER_API_KEY='sk-or-v1-...'")
        return 1

    except RuntimeError as e:
        print(f"❌ API 调用失败: {e}")
        print("\n💡 提示: 请检查:")
        print("   1. API key 是否有效")
        print("   2. 账户余额是否充足")
        print("   3. 网络连接是否正常")
        return 1

    except Exception as e:
        print(f"❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_smoke_test())
