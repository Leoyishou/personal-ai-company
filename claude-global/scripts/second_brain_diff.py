#!/usr/bin/env python3
"""
Second Brain Diff - 每日 Git 变更追踪
扫描 odyssey 仓库的当日变更，生成摘要并存入 Supabase
"""

import os
import sys
import subprocess
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

# 配置
REPO_PATH = Path.home() / "usr" / "odyssey"
REPO_NAME = "odyssey"

# 环境变量
SUPABASE_URL = "https://mwvsdfalfqblbqwnyqpn.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_PDC_ANON_KEY", "")
SUPABASE_ACCESS_TOKEN = os.environ.get("SUPABASE_ACCESS_TOKEN", "")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")


def run_git(args, cwd=None):
    """运行 git 命令"""
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd or REPO_PATH,
        capture_output=True,
        text=True
    )
    return result.stdout.strip()


def get_today_commits(target_date=None):
    """获取指定日期的 commits"""
    if target_date is None:
        target_date = datetime.now().date()

    # git log --since="2026-01-28 00:00" --until="2026-01-28 23:59" --oneline
    since = f"{target_date} 00:00"
    until = f"{target_date} 23:59"

    log_output = run_git([
        "log",
        f"--since={since}",
        f"--until={until}",
        "--oneline",
        "--no-merges"
    ])

    if not log_output:
        return []

    commits = []
    for line in log_output.split("\n"):
        if line.strip():
            parts = line.split(" ", 1)
            if len(parts) == 2:
                commits.append({
                    "hash": parts[0],
                    "message": parts[1]
                })

    return commits


def get_diff_stats(target_date=None):
    """获取当日变更统计"""
    if target_date is None:
        target_date = datetime.now().date()

    since = f"{target_date} 00:00"
    until = f"{target_date} 23:59"

    # 获取统计信息
    stat_output = run_git([
        "log",
        f"--since={since}",
        f"--until={until}",
        "--stat",
        "--no-merges"
    ])

    # 获取改动的文件列表
    files_output = run_git([
        "log",
        f"--since={since}",
        f"--until={until}",
        "--name-only",
        "--pretty=format:",
        "--no-merges"
    ])

    # 解析文件列表
    changed_files = list(set([f.strip() for f in files_output.split("\n") if f.strip()]))

    # 统计行数变化
    numstat = run_git([
        "log",
        f"--since={since}",
        f"--until={until}",
        "--numstat",
        "--pretty=format:",
        "--no-merges"
    ])

    lines_added = 0
    lines_deleted = 0
    for line in numstat.split("\n"):
        parts = line.split("\t")
        if len(parts) >= 2:
            try:
                added = int(parts[0]) if parts[0] != "-" else 0
                deleted = int(parts[1]) if parts[1] != "-" else 0
                lines_added += added
                lines_deleted += deleted
            except ValueError:
                continue

    return {
        "files_changed": len(changed_files),
        "changed_files": changed_files[:50],  # 限制数量
        "lines_added": lines_added,
        "lines_deleted": lines_deleted
    }


def generate_ai_summary(commits, stats):
    """使用 AI 生成摘要"""
    if not commits:
        return "今日无变更"

    if not OPENROUTER_API_KEY:
        # 降级：使用 commit messages 拼接
        return "; ".join([c["message"] for c in commits[:5]])

    context = f"""今日 Git 变更统计：
- Commits: {len(commits)} 个
- 文件变更: {stats['files_changed']} 个
- 新增: +{stats['lines_added']} 行
- 删除: -{stats['lines_deleted']} 行

Commit 消息：
{chr(10).join(['- ' + c['message'] for c in commits[:10]])}

主要改动文件：
{chr(10).join(['- ' + f for f in stats['changed_files'][:15]])}
"""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "google/gemini-2.0-flash-001",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是第二大脑（Obsidian 知识库）的变更总结助手。用 1-2 句话（30-60字）总结今天的知识库变更，重点说明做了什么、新增/修改了哪类内容。直接输出总结，不要前缀。"
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                "max_tokens": 150,
                "temperature": 0.3,
            },
            timeout=30,
        )

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"AI summary failed: {e}", file=sys.stderr)

    # 降级
    return "; ".join([c["message"] for c in commits[:3]])


def escape_sql_string(s):
    """转义 SQL 字符串"""
    if s is None:
        return "NULL"
    return "'" + s.replace("'", "''").replace("\\", "\\\\") + "'"


def format_pg_array(items):
    """格式化为 PostgreSQL 数组"""
    if not items:
        return "ARRAY[]::TEXT[]"
    escaped = [escape_sql_string(item) for item in items]
    return "ARRAY[" + ", ".join(escaped) + "]::TEXT[]"


def save_to_supabase(data):
    """保存到 Supabase"""
    if not SUPABASE_ACCESS_TOKEN:
        print("Warning: SUPABASE_ACCESS_TOKEN not set", file=sys.stderr)
        return False

    # 清理文件名（移除引号和特殊转义）
    clean_files = []
    for f in data["changed_files"][:50]:
        # 移除引号包裹
        f = f.strip('"')
        # 尝试解码转义的 UTF-8
        try:
            f = f.encode('utf-8').decode('unicode_escape').encode('latin1').decode('utf-8')
        except:
            pass
        clean_files.append(f)

    # 使用 Management API
    query = f"""
    INSERT INTO second_brain_diffs (date, repo_name, commit_count, files_changed, lines_added, lines_deleted, commit_messages, changed_files, ai_summary)
    VALUES (
        {escape_sql_string(data["date"])},
        {escape_sql_string(data["repo_name"])},
        {data["commit_count"]},
        {data["files_changed"]},
        {data["lines_added"]},
        {data["lines_deleted"]},
        {format_pg_array(data["commit_messages"])},
        {format_pg_array(clean_files)},
        {escape_sql_string(data["ai_summary"])}
    )
    ON CONFLICT (date, repo_name) DO UPDATE SET
        commit_count = EXCLUDED.commit_count,
        files_changed = EXCLUDED.files_changed,
        lines_added = EXCLUDED.lines_added,
        lines_deleted = EXCLUDED.lines_deleted,
        commit_messages = EXCLUDED.commit_messages,
        changed_files = EXCLUDED.changed_files,
        ai_summary = EXCLUDED.ai_summary;
    """

    try:
        response = requests.post(
            "https://api.supabase.com/v1/projects/mwvsdfalfqblbqwnyqpn/database/query",
            headers={
                "Authorization": f"Bearer {SUPABASE_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"query": query},
            timeout=30,
        )

        if response.status_code in (200, 201):
            # 空数组 [] 或包含数据都表示成功
            return True
        else:
            print(f"Supabase error ({response.status_code}): {response.text}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"Supabase save failed: {e}", file=sys.stderr)
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Second Brain Diff - 每日变更追踪")
    parser.add_argument("date", nargs="?", help="目标日期 (YYYY-MM-DD)，默认今天")
    parser.add_argument("--dry-run", action="store_true", help="只输出，不保存到数据库")
    parser.add_argument("--quiet", "-q", action="store_true", help="静默模式")
    args = parser.parse_args()

    # 解析日期
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"Invalid date: {args.date}", file=sys.stderr)
            sys.exit(1)
    else:
        target_date = datetime.now().date()

    if not args.quiet:
        print(f"📅 扫描 {target_date} 的变更...", file=sys.stderr)

    # 检查仓库
    if not (REPO_PATH / ".git").exists():
        print(f"Error: {REPO_PATH} is not a git repository", file=sys.stderr)
        sys.exit(1)

    # 获取 commits
    commits = get_today_commits(target_date)

    if not commits:
        if not args.quiet:
            print(f"❌ {target_date} 没有 commits", file=sys.stderr)
        sys.exit(0)

    # 获取统计
    stats = get_diff_stats(target_date)

    # 生成摘要
    ai_summary = generate_ai_summary(commits, stats)

    # 构建数据
    data = {
        "date": str(target_date),
        "repo_name": REPO_NAME,
        "commit_count": len(commits),
        "files_changed": stats["files_changed"],
        "lines_added": stats["lines_added"],
        "lines_deleted": stats["lines_deleted"],
        "commit_messages": [c["message"] for c in commits],
        "changed_files": stats["changed_files"],
        "ai_summary": ai_summary
    }

    # 输出
    if not args.quiet:
        print(f"\n📊 {target_date} Second Brain Diff", file=sys.stderr)
        print(f"   Commits: {data['commit_count']}", file=sys.stderr)
        print(f"   Files: {data['files_changed']}", file=sys.stderr)
        print(f"   +{data['lines_added']} / -{data['lines_deleted']} lines", file=sys.stderr)
        print(f"   Summary: {ai_summary}", file=sys.stderr)

    # 保存
    if not args.dry_run:
        if save_to_supabase(data):
            if not args.quiet:
                print(f"\n✅ 已保存到 Supabase", file=sys.stderr)
        else:
            print(f"\n❌ 保存失败", file=sys.stderr)
            sys.exit(1)

    # JSON 输出
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
