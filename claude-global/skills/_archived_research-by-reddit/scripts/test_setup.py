#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Reddit API 配置
验证所有依赖和凭证是否正确配置
"""

import sys


def test_imports():
    """测试依赖包是否安装"""
    print("📦 测试依赖包...")
    try:
        import praw
        print("  ✅ praw 已安装 (版本: {})".format(praw.__version__))
    except ImportError:
        print("  ❌ praw 未安装")
        print("     运行: pip install praw")
        return False

    try:
        import requests
        print("  ✅ requests 已安装")
    except ImportError:
        print("  ❌ requests 未安装")
        print("     运行: pip install requests")
        return False

    return True


def test_reddit_credentials():
    """测试 Reddit API 凭证"""
    print("\n🔐 测试 Reddit API 凭证...")
    try:
        from reddit_client import build_reddit_client

        reddit = build_reddit_client()
        print("  ✅ Reddit 客户端创建成功")

        # 测试简单的 API 调用
        subreddit = reddit.subreddit("python")
        print(f"  ✅ API 调用成功 (测试 subreddit: r/{subreddit.display_name})")
        return True

    except ValueError as e:
        print(f"  ❌ 配置错误: {e}")
        print("\n     请设置环境变量:")
        print("       export REDDIT_CLIENT_ID='your_client_id'")
        print("       export REDDIT_CLIENT_SECRET='your_client_secret'")
        print("\n     或创建 .env 文件")
        return False
    except Exception as e:
        print(f"  ❌ API 调用失败: {e}")
        return False


def test_openrouter_credentials():
    """测试 OpenRouter API 凭证（可选）"""
    print("\n🤖 测试 OpenRouter API 凭证...")
    import os

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("  ⚠️  OPENROUTER_API_KEY 未设置")
        print("     AI 分析功能将不可用")
        print("     如需使用，请访问: https://openrouter.ai/keys")
        return None

    print("  ✅ OPENROUTER_API_KEY 已设置")
    print("     注意：未验证 key 是否有效（需要实际调用 API）")
    return True


def test_basic_search():
    """测试基本搜索功能"""
    print("\n🔍 测试基本搜索功能...")
    try:
        from reddit_client import build_reddit_client, fetch_search_results

        reddit = build_reddit_client()
        posts = fetch_search_results(
            reddit,
            query="python",
            search_subreddit="programming",
            limit=1
        )

        if posts:
            print(f"  ✅ 搜索成功，找到 {len(posts)} 个结果")
            print(f"     示例: {posts[0]['title'][:50]}...")
            return True
        else:
            print("  ⚠️  搜索成功但没有结果")
            return True

    except Exception as e:
        print(f"  ❌ 搜索失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("="*60)
    print("Reddit 调研 Skill - 配置验证")
    print("="*60)

    all_passed = True

    # 测试依赖
    if not test_imports():
        all_passed = False

    # 测试 Reddit 凭证
    if not test_reddit_credentials():
        all_passed = False

    # 测试 OpenRouter 凭证（可选）
    test_openrouter_credentials()

    # 测试基本功能
    if not test_basic_search():
        all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("✅ 所有测试通过！配置完成，可以开始使用。")
        print("\n快速开始:")
        print("  python analyze_reddit.py --query 'test' --limit 3")
    else:
        print("❌ 部分测试失败，请检查配置。")
        print("\n查看故障排查指南:")
        print("  cat ../TROUBLESHOOTING.md")
    print("="*60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
