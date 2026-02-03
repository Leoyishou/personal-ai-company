#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reddit 调研主脚本
支持搜索、获取帖子、AI 分析等功能
"""
import argparse
import json
import os
import sys

from reddit_client import (
    build_reddit_client,
    fetch_search_results,
    fetch_posts,
    fetch_single_post,
    build_analysis_prompt,
    render_markdown,
    request_openrouter,
)

DEFAULT_OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2-flash-thinking-exp")
DEFAULT_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Read Reddit posts and analyze them with OpenRouter Gemini models."
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--subreddit", help="Subreddit name, e.g. 'worldnews'")
    source_group.add_argument("--post-id", help="Reddit post ID, e.g. 'abc123'")
    source_group.add_argument("--post-url", help="Full Reddit post URL")
    source_group.add_argument("--query", help="Search query, e.g. 'Polymarket'")

    parser.add_argument("--sort", choices=["hot", "new", "top", "controversial"], default="hot")
    parser.add_argument(
        "--time-filter",
        choices=["hour", "day", "week", "month", "year", "all"],
        default="week",
    )
    parser.add_argument("--search-subreddit", default="all")
    parser.add_argument(
        "--search-sort",
        choices=["relevance", "hot", "top", "new", "comments"],
        default="relevance",
    )
    parser.add_argument("--limit", type=int, default=5, help="Number of posts to read")
    parser.add_argument("--include-comments", action="store_true")
    parser.add_argument("--comment-limit", type=int, default=10)
    parser.add_argument("--max-text-length", type=int, default=1500)
    parser.add_argument("--max-comment-length", type=int, default=500)
    parser.add_argument("--analysis-language", default="zh")
    parser.add_argument("--model", default=DEFAULT_OPENROUTER_MODEL)
    parser.add_argument("--output", help="Save JSON result to a file")
    parser.add_argument("--output-md", help="Save Markdown result to a file")
    parser.add_argument("--skip-analysis", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    reddit = build_reddit_client()

    if args.query:
        posts = fetch_search_results(
            reddit,
            args.query,
            args.search_subreddit,
            args.search_sort,
            args.time_filter,
            args.limit,
            args.include_comments,
            args.comment_limit,
            args.max_text_length,
            args.max_comment_length,
        )
        source = {
            "type": "search",
            "query": args.query,
            "subreddit": args.search_subreddit,
            "search_sort": args.search_sort,
            "time_filter": args.time_filter,
        }
    elif args.subreddit:
        posts = fetch_posts(
            reddit,
            args.subreddit,
            args.sort,
            args.limit,
            args.time_filter,
            args.include_comments,
            args.comment_limit,
            args.max_text_length,
            args.max_comment_length,
        )
        source = {
            "type": "subreddit",
            "value": args.subreddit,
            "sort": args.sort,
            "time_filter": args.time_filter,
        }
    else:
        post = fetch_single_post(
            reddit,
            args.post_id,
            args.post_url,
            args.include_comments,
            args.comment_limit,
            args.max_text_length,
            args.max_comment_length,
        )
        posts = [post]
        source = {
            "type": "submission",
            "value": args.post_id or args.post_url,
        }

    result = {
        "source": source,
        "posts": posts,
    }

    if args.skip_analysis:
        output_text = (
            render_markdown(result) if args.output_md else json.dumps(result, ensure_ascii=False, indent=2)
        )
    else:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("Missing OPENROUTER_API_KEY in environment.")
        prompt = build_analysis_prompt(posts, args.analysis_language)
        analysis, _raw = request_openrouter(
            args.model,
            [{"role": "user", "content": prompt}],
            api_key,
            os.getenv("OPENROUTER_BASE_URL", DEFAULT_OPENROUTER_URL),
        )
        result["analysis"] = analysis
        result["model"] = args.model
        output_text = render_markdown(result) if args.output_md else analysis

    if args.output:
        with open(args.output, "w", encoding="utf-8") as file:
            json.dump(result, file, ensure_ascii=False, indent=2)

    if args.output_md:
        markdown = render_markdown(result)
        with open(args.output_md, "w", encoding="utf-8") as file:
            file.write(markdown)

    print(output_text)


if __name__ == "__main__":
    main()
