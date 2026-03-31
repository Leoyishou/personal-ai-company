#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日选题情报 - 采集热点 + AI 评分 + 去重 + 推送

Usage:
    python3 briefing.py                     # 完整流程
    python3 briefing.py --collect-only      # 仅采集
    python3 briefing.py --sources hackernews,github
    python3 briefing.py --no-push           # 跳过推送
"""

import argparse
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from difflib import SequenceMatcher

import requests

# ── 环境变量 ──────────────────────────────────────────────

SECRETS_PATH = os.path.expanduser("~/.claude/secrets.env")
if os.path.exists(SECRETS_PATH):
    with open(SECRETS_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

# ── 配置 ──────────────────────────────────────────────────

SUPABASE_URL = "http://127.0.0.1:54321"
SUPABASE_KEY = os.getenv(
    "SUPABASE_LOCAL_ANON_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0",
)

LINEAR_API_KEY = os.getenv("LINEAR_API_KEY", "")
LINEAR_TEAM_ID = "C"  # 内容事业部
LINEAR_LABEL_IDEA = "7be8f7f1-b476-4c27-87e4-e4b36fc2e6cb"  # 灵感标签

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
SCORING_MODEL = "google/gemini-2.5-flash"

SKILLS_DIR = os.path.expanduser("~/.claude/skills")
NOTIFY_SCRIPT = os.path.join(SKILLS_DIR, "api-notify/scripts/notify.py")

ALL_SOURCES = ["hackernews", "github", "reddit", "twitter"]


# ── 数据采集 ──────────────────────────────────────────────


def collect_hackernews():
    """采集 HackerNews Top Stories (score > 100)"""
    items = []
    try:
        resp = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json", timeout=15
        )
        story_ids = resp.json()[:30]

        for sid in story_ids:
            try:
                r = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                    timeout=10,
                )
                story = r.json()
                if story and story.get("score", 0) >= 100:
                    items.append(
                        {
                            "title": story.get("title", ""),
                            "url": story.get("url", f"https://news.ycombinator.com/item?id={sid}"),
                            "source": "hackernews",
                            "score": story.get("score", 0),
                            "comments": story.get("descendants", 0),
                        }
                    )
            except Exception:
                continue
    except Exception as e:
        print(f"[hackernews] Error: {e}", file=sys.stderr)
    return items


def collect_github_trending():
    """采集 GitHub Trending 仓库"""
    items = []
    try:
        resp = requests.get(
            "https://api.github.com/search/repositories",
            params={
                "q": f"created:>{(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')}",
                "sort": "stars",
                "order": "desc",
                "per_page": 20,
            },
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=15,
        )
        for repo in resp.json().get("items", [])[:20]:
            items.append(
                {
                    "title": f"{repo['full_name']}: {repo.get('description', '') or ''}",
                    "url": repo["html_url"],
                    "source": "github",
                    "score": repo.get("stargazers_count", 0),
                    "language": repo.get("language", ""),
                }
            )
    except Exception as e:
        print(f"[github] Error: {e}", file=sys.stderr)
    return items


def collect_reddit():
    """采集 Reddit AI/编程热帖"""
    items = []
    subreddits = ["MachineLearning", "LocalLLaMA", "programming"]
    reddit_script = os.path.join(SKILLS_DIR, "api-fetch/search/reddit.py")

    for sub in subreddits:
        try:
            result = subprocess.run(
                [
                    sys.executable, reddit_script,
                    "--subreddit", sub,
                    "--sort", "hot",
                    "--limit", "10",
                    "--no-ai",
                ],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.path.dirname(reddit_script),
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for post in data.get("posts", []):
                    items.append(
                        {
                            "title": post.get("title", ""),
                            "url": f"https://reddit.com{post.get('permalink', '')}",
                            "source": "reddit",
                            "score": post.get("score", 0),
                            "subreddit": sub,
                        }
                    )
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
            print(f"[reddit/{sub}] Error: {e}", file=sys.stderr)
            # Fallback: direct API
            try:
                resp = requests.get(
                    f"https://www.reddit.com/r/{sub}/hot.json",
                    params={"limit": 10},
                    headers={"User-Agent": "TopicBriefing/1.0"},
                    timeout=15,
                )
                for post in resp.json().get("data", {}).get("children", []):
                    d = post["data"]
                    if d.get("score", 0) >= 50:
                        items.append(
                            {
                                "title": d.get("title", ""),
                                "url": f"https://reddit.com{d.get('permalink', '')}",
                                "source": "reddit",
                                "score": d.get("score", 0),
                                "subreddit": sub,
                            }
                        )
            except Exception:
                pass
    return items


def collect_twitter():
    """采集 Twitter/X AI 相关讨论（通过 Grok x_search）"""
    items = []
    twitter_script = os.path.join(SKILLS_DIR, "api-fetch/search/twitter.py")

    try:
        result = subprocess.run(
            [
                sys.executable, twitter_script,
                "--query", "AI LLM agent framework new release",
                "--limit", "10",
            ],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=os.path.dirname(twitter_script),
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            for tweet in data.get("results", []):
                items.append(
                    {
                        "title": tweet.get("text", "")[:200],
                        "url": tweet.get("url", ""),
                        "source": "twitter",
                        "score": 0,
                    }
                )
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"[twitter] Error: {e}", file=sys.stderr)
    return items


COLLECTORS = {
    "hackernews": collect_hackernews,
    "github": collect_github_trending,
    "reddit": collect_reddit,
    "twitter": collect_twitter,
}


def collect_all(sources=None):
    """并发采集所有数据源"""
    sources = sources or ALL_SOURCES
    all_items = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for src in sources:
            if src in COLLECTORS:
                futures[executor.submit(COLLECTORS[src])] = src

        for future in as_completed(futures):
            src = futures[future]
            try:
                items = future.result()
                print(f"[{src}] Collected {len(items)} items")
                all_items.extend(items)
            except Exception as e:
                print(f"[{src}] Failed: {e}", file=sys.stderr)

    return all_items


# ── 去重（标题相似度） ────────────────────────────────────


def deduplicate_items(items, threshold=0.7):
    """标题级去重，相似度 > threshold 的合并"""
    unique = []
    for item in items:
        title = item["title"].lower()
        is_dup = False
        for u in unique:
            if SequenceMatcher(None, title, u["title"].lower()).ratio() > threshold:
                is_dup = True
                # 保留分数更高的
                if item.get("score", 0) > u.get("score", 0):
                    u.update(item)
                break
        if not is_dup:
            unique.append(item)
    return unique


# ── AI 评分 ───────────────────────────────────────────────


def score_topics(items):
    """调用 OpenRouter (Gemini Flash) 评分"""
    if not OPENROUTER_API_KEY:
        print("[score] No OPENROUTER_API_KEY, skipping AI scoring", file=sys.stderr)
        return items[:10]

    # 准备输入
    topics_json = json.dumps(
        [{"title": i["title"], "source": i["source"], "url": i.get("url", "")} for i in items[:30]],
        ensure_ascii=False,
    )

    prompt = f"""你是一个选题顾问，为中国小红书/B站技术博主评估选题价值。

以下是今日采集的热点话题列表：

{topics_json}

评分标准（1-10分）：
1. 新颖度：是否是近期新出现的概念/工具/事件？
2. 可视化：能否用3-8张图讲清楚？适合做图文科普吗？
3. 受众匹配：AI/编程/技术圈的中国读者会感兴趣吗？

请返回 top 5 选题，严格用如下 JSON 格式（不要包含 markdown 代码块）：
[
  {{
    "title": "选题标题（中文）",
    "source": "来源",
    "source_url": "原始链接",
    "score": 8,
    "pitch": "一句话说明为什么值得做",
    "series_fit": "n张图系列"
  }}
]

series_fit 可选值：n张图系列、人物语录系列、技术科普系列、HOPICO系列"""

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json={
                "model": SCORING_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
            },
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=60,
        )

        if resp.status_code != 200:
            print(f"[score] OpenRouter error {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
            return items[:5]

        content = resp.json()["choices"][0]["message"]["content"]
        # 尝试提取 JSON
        json_match = re.search(r"\[.*\]", content, re.DOTALL)
        if json_match:
            scored = json.loads(json_match.group())
            return scored
        else:
            print(f"[score] Could not parse JSON from response", file=sys.stderr)
            return items[:5]

    except Exception as e:
        print(f"[score] Error: {e}", file=sys.stderr)
        return items[:5]


# ── 历史去重 ──────────────────────────────────────────────


def check_history_dedup(topics):
    """查 Linear Issue + Supabase content_posts 做历史去重"""
    existing_titles = set()

    # 1. 查 Supabase content_posts 已发布标题
    try:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/content_posts",
            params={"select": "title", "limit": 200},
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Accept-Profile": "pac",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            for post in resp.json():
                if post.get("title"):
                    existing_titles.add(post["title"].lower())
    except Exception as e:
        print(f"[dedup] Supabase query error: {e}", file=sys.stderr)

    # 2. 查 Supabase topic_briefings 最近 90 天
    try:
        cutoff = (datetime.now() - timedelta(days=90)).isoformat()
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/topic_briefings",
            params={
                "select": "topic",
                "created_at": f"gte.{cutoff}",
                "limit": 500,
            },
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Accept-Profile": "pac",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            for row in resp.json():
                if row.get("topic"):
                    existing_titles.add(row["topic"].lower())
    except Exception as e:
        print(f"[dedup] topic_briefings query error: {e}", file=sys.stderr)

    # 3. 查 Linear 内容团队最近 Issue（如果有 API key）
    if LINEAR_API_KEY:
        try:
            resp = requests.post(
                "https://api.linear.app/graphql",
                json={
                    "query": """
                    query {
                      issues(
                        filter: {
                          team: { key: { eq: "C" } }
                          createdAt: { gte: "%s" }
                        }
                        first: 100
                      ) {
                        nodes { title }
                      }
                    }
                    """
                    % (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
                },
                headers={"Authorization": LINEAR_API_KEY},
                timeout=15,
            )
            if resp.status_code == 200:
                for issue in resp.json().get("data", {}).get("issues", {}).get("nodes", []):
                    if issue.get("title"):
                        existing_titles.add(issue["title"].lower())
        except Exception as e:
            print(f"[dedup] Linear query error: {e}", file=sys.stderr)

    # 标记重复
    for topic in topics:
        title_lower = topic.get("title", "").lower()
        is_dup = any(
            SequenceMatcher(None, title_lower, existing).ratio() > 0.6
            for existing in existing_titles
        )
        if is_dup:
            topic["title"] = f"[已做过] {topic['title']}"
            topic["status"] = "rejected"

    return topics


# ── Supabase 写入 ────────────────────────────────────────


def save_to_supabase(topics):
    """将评分结果写入 pac.topic_briefings"""
    rows = []
    for t in topics:
        rows.append(
            {
                "topic": t.get("title", "").replace("[已做过] ", ""),
                "source": t.get("source", "unknown"),
                "source_url": t.get("source_url", t.get("url", "")),
                "score": t.get("score", 0),
                "pitch": t.get("pitch", ""),
                "series_fit": t.get("series_fit", ""),
                "status": t.get("status", "pending"),
            }
        )

    try:
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/topic_briefings",
            json=rows,
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Content-Profile": "pac",
                "Prefer": "return=representation",
            },
            timeout=10,
        )
        if resp.status_code in (200, 201):
            print(f"[supabase] Saved {len(rows)} topics")
            return resp.json()
        else:
            print(f"[supabase] Error {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
    except Exception as e:
        print(f"[supabase] Error: {e}", file=sys.stderr)
    return []


# ── 推送 ─────────────────────────────────────────────────


def push_telegram(topics):
    """推送到 Telegram Saved Messages"""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"**选题情报 {today}**\n"]

    for i, t in enumerate(topics, 1):
        score_emoji = "🔥" if t.get("score", 0) >= 8 else "⭐"
        dup_mark = " [已做过]" if t.get("status") == "rejected" else ""
        title = t.get("title", "").replace("[已做过] ", "")
        lines.append(f"{score_emoji} **{t.get('score', '?')}分** {title}{dup_mark}")
        if t.get("pitch"):
            lines.append(f"   → {t['pitch']}")
        if t.get("series_fit"):
            lines.append(f"   📂 {t['series_fit']}")
        lines.append("")

    message = "\n".join(lines)

    try:
        subprocess.run(
            [
                sys.executable, NOTIFY_SCRIPT,
                "--title", f"选题情报 {today}",
                "--message", message,
                "--channels", "telegram",
            ],
            timeout=30,
            capture_output=True,
        )
        print("[telegram] Pushed successfully")
    except Exception as e:
        print(f"[telegram] Push error: {e}", file=sys.stderr)


def create_linear_issues(topics):
    """为 top 3 未重复选题创建 Linear Issue"""
    if not LINEAR_API_KEY:
        print("[linear] No LINEAR_API_KEY, skipping issue creation", file=sys.stderr)
        return

    new_topics = [t for t in topics if t.get("status") != "rejected"][:3]

    for t in new_topics:
        title = t.get("title", "")
        description = f"""**来源**: {t.get('source', 'unknown')}
**链接**: {t.get('source_url', t.get('url', ''))}
**AI 评分**: {t.get('score', '?')}/10
**Pitch**: {t.get('pitch', '')}
**推荐系列**: {t.get('series_fit', '')}

---
*由选题情报自动创建*"""

        try:
            resp = requests.post(
                "https://api.linear.app/graphql",
                json={
                    "query": """
                    mutation CreateIssue($input: IssueCreateInput!) {
                      issueCreate(input: $input) {
                        success
                        issue { id identifier url }
                      }
                    }
                    """,
                    "variables": {
                        "input": {
                            "teamId": LINEAR_TEAM_ID,
                            "title": title,
                            "description": description,
                            "labelIds": [LINEAR_LABEL_IDEA],
                        }
                    },
                },
                headers={"Authorization": LINEAR_API_KEY},
                timeout=15,
            )
            if resp.status_code == 200:
                result = resp.json()
                issue = result.get("data", {}).get("issueCreate", {}).get("issue", {})
                if issue:
                    print(f"[linear] Created: {issue.get('identifier')} - {title[:50]}")
                    t["linear_issue_id"] = issue.get("id", "")
            else:
                print(f"[linear] Error {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
        except Exception as e:
            print(f"[linear] Error creating issue: {e}", file=sys.stderr)


# ── 主流程 ────────────────────────────────────────────────


def format_report(topics):
    """格式化报告输出到 stdout"""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"# 选题情报 {today}",
        "",
    ]

    for i, t in enumerate(topics, 1):
        score = t.get("score", "?")
        title = t.get("title", "")
        lines.append(f"## {i}. [{score}分] {title}")
        if t.get("pitch"):
            lines.append(f"**Pitch**: {t['pitch']}")
        if t.get("series_fit"):
            lines.append(f"**推荐系列**: {t['series_fit']}")
        if t.get("source"):
            lines.append(f"**来源**: {t['source']}")
        if t.get("source_url") or t.get("url"):
            lines.append(f"**链接**: {t.get('source_url', t.get('url', ''))}")
        if t.get("status") == "rejected":
            lines.append("**状态**: ⚠️ 已做过")
        if t.get("linear_issue_id"):
            lines.append(f"**Linear**: 已创建 Issue")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="每日选题情报")
    parser.add_argument("--sources", default=",".join(ALL_SOURCES),
                        help="数据源，逗号分隔")
    parser.add_argument("--collect-only", action="store_true",
                        help="仅采集，不评分不推送")
    parser.add_argument("--no-push", action="store_true",
                        help="跳过推送")
    args = parser.parse_args()

    sources = [s.strip() for s in args.sources.split(",")]
    print(f"=== 选题情报 {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    print(f"数据源: {', '.join(sources)}")
    print()

    # Step 1: 并发采集
    print("── Step 1: 采集 ──")
    raw_items = collect_all(sources)
    print(f"总计采集: {len(raw_items)} 条\n")

    if not raw_items:
        print("未采集到任何数据，退出")
        return

    # Step 2: 初步去重
    print("── Step 2: 去重 ──")
    unique_items = deduplicate_items(raw_items)
    print(f"去重后: {len(unique_items)} 条\n")

    if args.collect_only:
        print(json.dumps(unique_items, ensure_ascii=False, indent=2))
        return

    # Step 3: AI 评分
    print("── Step 3: AI 评分 ──")
    scored = score_topics(unique_items)
    print(f"评分完成: {len(scored)} 条\n")

    # Step 4: 历史去重
    print("── Step 4: 历史去重 ──")
    scored = check_history_dedup(scored)
    dup_count = sum(1 for t in scored if t.get("status") == "rejected")
    print(f"历史重复: {dup_count} 条\n")

    # Step 5: 写入 Supabase
    print("── Step 5: 存储 ──")
    saved = save_to_supabase(scored)

    if not args.no_push:
        # Step 6: 推送
        print("\n── Step 6: 推送 ──")
        push_telegram(scored)

        # Step 7: 创建 Linear Issues
        print("\n── Step 7: Linear Issues ──")
        create_linear_issues(scored)

        # 回写 linear_issue_id 到 Supabase
        for t in scored:
            if t.get("linear_issue_id") and saved:
                topic_name = t.get("title", "").replace("[已做过] ", "")
                for s in saved:
                    if s.get("topic") == topic_name:
                        try:
                            requests.patch(
                                f"{SUPABASE_URL}/rest/v1/topic_briefings",
                                params={"id": f"eq.{s['id']}"},
                                json={"linear_issue_id": t["linear_issue_id"]},
                                headers={
                                    "apikey": SUPABASE_KEY,
                                    "Authorization": f"Bearer {SUPABASE_KEY}",
                                    "Content-Type": "application/json",
                                    "Content-Profile": "pac",
                                },
                                timeout=5,
                            )
                        except Exception:
                            pass

    # 输出报告
    print("\n" + "=" * 50)
    print(format_report(scored))


if __name__ == "__main__":
    main()
