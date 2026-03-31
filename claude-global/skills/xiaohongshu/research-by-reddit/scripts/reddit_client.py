#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reddit API Client Library
提供 Reddit 数据获取和分析的核心功能
"""

import json
import os
from datetime import datetime

import praw
import requests


DEFAULT_OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2-flash-thinking-exp")
DEFAULT_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def clip_text(text, max_chars):
    """裁剪文本到指定长度"""
    if not text:
        return ""
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[:max_chars].rstrip() + "…"


def resolve_language(language):
    """标准化语言代码"""
    if not language:
        return "简体中文"
    normalized = language.strip().lower()
    if normalized in {"zh", "zh-cn", "zh-hans", "cn", "中文"}:
        return "简体中文"
    return language


def build_reddit_client():
    """
    构建 Reddit API 客户端

    环境变量:
        REDDIT_CLIENT_ID: Reddit API Client ID (必需)
        REDDIT_CLIENT_SECRET: Reddit API Client Secret (必需)
        REDDIT_USERNAME: Reddit 用户名 (可选，用于需要认证的操作)
        REDDIT_PASSWORD: Reddit 密码 (可选)
        REDDIT_USER_AGENT: User Agent (可选)

    Returns:
        praw.Reddit: 配置好的 Reddit 客户端

    Raises:
        ValueError: 缺少必需的凭证
    """
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    username = os.getenv("REDDIT_USERNAME")
    password = os.getenv("REDDIT_PASSWORD")
    user_agent = os.getenv("REDDIT_USER_AGENT", "research-by-reddit:v1.0")

    if not client_id or not client_secret:
        raise ValueError(
            "Missing Reddit credentials. Please set:\n"
            "  REDDIT_CLIENT_ID\n"
            "  REDDIT_CLIENT_SECRET\n"
            "Or update NormVio/src/config.py"
        )

    if username and password:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
            user_agent=user_agent,
        )
    else:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )

    reddit.read_only = True
    return reddit


def build_submission_payload(
    submission,
    include_comments,
    comment_limit,
    max_text_length,
    max_comment_length
):
    """
    将 PRAW Submission 对象转换为结构化数据

    Args:
        submission: PRAW Submission 对象
        include_comments: 是否包含评论
        comment_limit: 最多包含多少条评论
        max_text_length: 帖子文本最大长度
        max_comment_length: 评论文本最大长度

    Returns:
        dict: 结构化的帖子数据
    """
    created_at = datetime.utcfromtimestamp(submission.created_utc).isoformat() + "Z"
    payload = {
        "id": submission.id,
        "title": clip_text(submission.title, max_text_length),
        "selftext": clip_text(submission.selftext or "", max_text_length),
        "author": submission.author.name if submission.author else "[deleted]",
        "subreddit": submission.subreddit.display_name,
        "score": submission.score,
        "num_comments": submission.num_comments,
        "created_utc": submission.created_utc,
        "created_at": created_at,
        "url": submission.url,
        "permalink": f"https://www.reddit.com{submission.permalink}",
    }

    if include_comments:
        submission.comment_sort = "top"
        submission.comments.replace_more(limit=0)
        comments = []
        for comment in list(submission.comments)[:comment_limit]:
            comments.append(
                {
                    "id": comment.id,
                    "author": comment.author.name if comment.author else "[deleted]",
                    "score": comment.score,
                    "body": clip_text(comment.body or "", max_comment_length),
                    "created_utc": comment.created_utc,
                }
            )
        payload["top_comments"] = comments

    return payload


def fetch_search_results(
    reddit,
    query,
    search_subreddit="all",
    search_sort="relevance",
    time_filter="week",
    limit=5,
    include_comments=False,
    comment_limit=10,
    max_text_length=1500,
    max_comment_length=500,
):
    """
    搜索 Reddit 帖子

    Args:
        reddit: PRAW Reddit 客户端
        query: 搜索关键词
        search_subreddit: 搜索范围（subreddit 名称或 "all"）
        search_sort: 排序方式 (relevance/hot/top/new/comments)
        time_filter: 时间过滤 (hour/day/week/month/year/all)
        limit: 返回结果数量
        include_comments: 是否包含评论
        comment_limit: 每个帖子的评论数量
        max_text_length: 帖子文本最大长度
        max_comment_length: 评论文本最大长度

    Returns:
        list: 帖子数据列表
    """
    subreddit_ref = reddit.subreddit(search_subreddit)
    submissions = subreddit_ref.search(
        query,
        sort=search_sort,
        time_filter=time_filter,
        limit=limit,
    )
    return [
        build_submission_payload(
            submission,
            include_comments,
            comment_limit,
            max_text_length,
            max_comment_length,
        )
        for submission in submissions
    ]


def fetch_posts(
    reddit,
    subreddit,
    sort="hot",
    limit=5,
    time_filter="week",
    include_comments=False,
    comment_limit=10,
    max_text_length=1500,
    max_comment_length=500,
):
    """
    获取 Subreddit 的帖子列表

    Args:
        reddit: PRAW Reddit 客户端
        subreddit: Subreddit 名称
        sort: 排序方式 (hot/new/top/controversial)
        limit: 返回结果数量
        time_filter: 时间过滤（仅用于 top/controversial）
        include_comments: 是否包含评论
        comment_limit: 每个帖子的评论数量
        max_text_length: 帖子文本最大长度
        max_comment_length: 评论文本最大长度

    Returns:
        list: 帖子数据列表
    """
    subreddit_ref = reddit.subreddit(subreddit)

    if sort == "hot":
        submissions = subreddit_ref.hot(limit=limit)
    elif sort == "new":
        submissions = subreddit_ref.new(limit=limit)
    elif sort == "top":
        submissions = subreddit_ref.top(limit=limit, time_filter=time_filter)
    elif sort == "controversial":
        submissions = subreddit_ref.controversial(limit=limit, time_filter=time_filter)
    else:
        raise ValueError(f"Unknown sort method: {sort}")

    return [
        build_submission_payload(
            submission,
            include_comments,
            comment_limit,
            max_text_length,
            max_comment_length,
        )
        for submission in submissions
    ]


def fetch_single_post(
    reddit,
    post_id=None,
    post_url=None,
    include_comments=False,
    comment_limit=10,
    max_text_length=1500,
    max_comment_length=500,
):
    """
    获取单个帖子的详细信息

    Args:
        reddit: PRAW Reddit 客户端
        post_id: Reddit 帖子 ID (与 post_url 二选一)
        post_url: Reddit 帖子 URL (与 post_id 二选一)
        include_comments: 是否包含评论
        comment_limit: 评论数量
        max_text_length: 帖子文本最大长度
        max_comment_length: 评论文本最大长度

    Returns:
        dict: 帖子数据
    """
    if post_id:
        submission = reddit.submission(id=post_id)
    elif post_url:
        submission = reddit.submission(url=post_url)
    else:
        raise ValueError("Must provide either post_id or post_url")

    return build_submission_payload(
        submission,
        include_comments,
        comment_limit,
        max_text_length,
        max_comment_length,
    )


def build_analysis_prompt(posts, language="zh"):
    """
    构建 AI 分析提示词

    Args:
        posts: 帖子数据列表
        language: 输出语言（zh/en）

    Returns:
        str: 分析提示词
    """
    language_label = resolve_language(language)
    serialized = json.dumps(posts, ensure_ascii=False, indent=2)
    return (
        "你是专业的 Reddit 阅读助手。\n"
        f"请用 {language_label} 输出分析，包含以下部分：\n"
        "1. 总体摘要（1-2 句话）\n"
        "2. 主要话题与观点（要点列表）\n"
        "3. 社区情绪与态度（积极/消极/中立，并说明依据）\n"
        "4. 有争议或值得深入的问题\n"
        "5. 值得进一步关注的线索或延伸阅读建议\n\n"
        "以下是帖子与评论数据（JSON）：\n"
        f"{serialized}"
    )


def render_markdown(result):
    """
    将结果渲染为 Markdown 格式

    Args:
        result: 包含 source、posts、analysis 的结果字典

    Returns:
        str: Markdown 格式的报告
    """
    source = result.get("source", {})
    posts = result.get("posts", [])
    lines = []

    # 标题和来源信息
    source_type = source.get("type")
    if source_type == "search":
        lines.append(f"# Reddit 搜索：{source.get('query', '')}")
        lines.append(f"- Subreddit: r/{source.get('subreddit', 'all')}")
        lines.append(f"- Sort: {source.get('search_sort', 'relevance')}")
        lines.append(f"- Time filter: {source.get('time_filter', '')}")
        lines.append(f"- Results: {len(posts)}")
    elif source_type == "subreddit":
        lines.append(f"# Reddit 帖子：r/{source.get('value', '')}")
        lines.append(f"- Sort: {source.get('sort', '')}")
        lines.append(f"- Time filter: {source.get('time_filter', '')}")
        lines.append(f"- Results: {len(posts)}")
    elif source_type == "submission":
        lines.append("# Reddit 帖子")
        lines.append(f"- Source: {source.get('value', '')}")
    else:
        lines.append("# Reddit 结果")

    lines.append("")

    # 帖子列表
    if not posts:
        lines.append("未找到匹配帖子。")
    else:
        for index, post in enumerate(posts, start=1):
            lines.append(f"## {index}. {post.get('title', '')}")
            lines.append(f"- Subreddit: r/{post.get('subreddit', '')}")
            lines.append(f"- Author: {post.get('author', '')}")
            lines.append(
                f"- Score: {post.get('score', 0)} | Comments: {post.get('num_comments', 0)}"
            )
            lines.append(f"- Created: {post.get('created_at', '')}")
            lines.append(f"- Link: {post.get('permalink', '')}")

            selftext = post.get("selftext")
            if selftext:
                lines.append("")
                lines.append(selftext)

            comments = post.get("top_comments")
            if comments:
                lines.append("")
                lines.append("### Top Comments")
                for comment in comments:
                    body = comment.get("body")
                    if body:
                        lines.append(f"- ({comment.get('score', 0)}) {body}")
            lines.append("")

    # AI 分析
    analysis = result.get("analysis")
    if analysis:
        lines.append("## 分析")
        lines.append(analysis)

    return "\n".join(lines).strip() + "\n"


def request_openrouter(model, messages, api_key=None, base_url=None, timeout=90):
    """
    调用 OpenRouter API 进行 AI 分析

    Args:
        model: 模型名称
        messages: 消息列表
        api_key: OpenRouter API Key
        base_url: API 端点
        timeout: 超时时间（秒）

    Returns:
        tuple: (分析文本, 完整响应)

    Raises:
        RuntimeError: API 调用失败
    """
    if not api_key:
        api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENROUTER_API_KEY")

    if not base_url:
        base_url = os.getenv("OPENROUTER_BASE_URL", DEFAULT_OPENROUTER_URL)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    site_url = os.getenv("OPENROUTER_SITE_URL")
    app_name = os.getenv("OPENROUTER_APP_NAME", "research-by-reddit")
    if site_url:
        headers["HTTP-Referer"] = site_url
    if app_name:
        headers["X-Title"] = app_name

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
    }

    response = requests.post(base_url, json=payload, headers=headers, timeout=timeout)

    if response.status_code != 200:
        raise RuntimeError(
            f"OpenRouter request failed ({response.status_code}): {response.text}"
        )

    data = response.json()
    if not data.get("choices"):
        raise RuntimeError(f"OpenRouter response missing choices: {data}")

    return data["choices"][0]["message"]["content"], data
