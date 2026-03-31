#!/usr/bin/env python3
"""
Session Scanner - 扫描过期 session，触发 Linear Issue 更新
由 launchd 定时调用（每 5 分钟）
"""

import os
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

# 配置
SESSIONS_DIR = Path.home() / ".claude" / "sessions"
INACTIVE_THRESHOLD = 2 * 60 * 60  # 2 小时（秒）
LOG_FILE = Path.home() / ".claude" / "logs" / "session-scanner.log"

def log(msg: str):
    """写日志"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")

def summarize_transcript(transcript_path: str) -> str:
    """用 AI 总结 transcript（调用 OpenRouter）"""
    if not transcript_path or not os.path.exists(transcript_path):
        return "无法读取对话记录"

    try:
        # 读取 transcript（JSONL 格式）
        lines = []
        with open(transcript_path, "r") as f:
            for line in f:
                try:
                    msg = json.loads(line)
                    role = msg.get("role", "")
                    content = msg.get("message", {}).get("content", "")
                    if isinstance(content, list):
                        content = " ".join(
                            c.get("text", "") for c in content if c.get("type") == "text"
                        )
                    if role and content:
                        lines.append(f"{role}: {content[:500]}")
                except:
                    pass

        # 截取最后 50 条消息
        context = "\n".join(lines[-50:])

        # 调用 OpenRouter API 生成总结
        import subprocess
        result = subprocess.run(
            [
                "python3",
                str(Path.home() / ".claude/skills/api-openrouter/scripts/openrouter_chat.py"),
                "--model", "google/gemini-2.0-flash-001",
                "--system", "你是一个技术项目总结助手。请用中文总结以下对话的核心工作内容，包括：1. 做了什么 2. 关键决策 3. 遗留问题。格式简洁，不超过 300 字。",
                "--message", f"对话记录：\n{context}"
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"总结生成失败: {result.stderr[:200]}"
    except Exception as e:
        return f"总结生成异常: {str(e)[:200]}"

def update_linear_issue(session_data: dict, summary: str):
    """更新 Linear Issue（调用 Linear API）"""
    issue_id = session_data.get("linear_issue_id")
    session_id = session_data.get("session_id")

    if not issue_id:
        log(f"Session {session_id} 没有关联的 Linear Issue，跳过更新")
        return

    try:
        # 调用 Linear GraphQL API 更新 Issue
        # 这里需要你的 Linear API key
        api_key = os.environ.get("LINEAR_API_KEY", "")
        if not api_key:
            # 尝试从 secrets.env 读取
            secrets_file = Path.home() / ".claude" / "secrets.env"
            if secrets_file.exists():
                with open(secrets_file) as f:
                    for line in f:
                        if line.startswith("export LINEAR_API_KEY="):
                            api_key = line.split("=", 1)[1].strip().strip('"\'')
                            break

        if not api_key:
            log(f"未找到 LINEAR_API_KEY，跳过 Issue {issue_id} 更新")
            return

        # 构建更新内容
        update_text = f"""
## Session 结束总结

**Session ID**: `{session_id}`
**活跃轮次**: {session_data.get('turn_count', 0)}
**结束时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

### 工作总结
{summary}
"""

        # GraphQL mutation
        mutation = """
        mutation UpdateIssue($id: String!, $description: String!) {
            issueUpdate(id: $id, input: { description: $description }) {
                success
                issue { id title }
            }
        }
        """

        import urllib.request
        import json

        # 先获取现有 description
        query = """
        query GetIssue($id: String!) {
            issue(id: $id) {
                id
                description
            }
        }
        """

        req = urllib.request.Request(
            "https://api.linear.app/graphql",
            data=json.dumps({"query": query, "variables": {"id": issue_id}}).encode(),
            headers={
                "Authorization": api_key,
                "Content-Type": "application/json"
            }
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            current_desc = data.get("data", {}).get("issue", {}).get("description", "") or ""

        # 追加总结
        new_desc = current_desc + "\n\n---\n" + update_text

        req = urllib.request.Request(
            "https://api.linear.app/graphql",
            data=json.dumps({
                "query": mutation,
                "variables": {"id": issue_id, "description": new_desc}
            }).encode(),
            headers={
                "Authorization": api_key,
                "Content-Type": "application/json"
            }
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            if result.get("data", {}).get("issueUpdate", {}).get("success"):
                log(f"成功更新 Linear Issue {issue_id}")
            else:
                log(f"更新 Linear Issue {issue_id} 失败: {result}")

    except Exception as e:
        log(f"更新 Linear Issue 异常: {e}")

def finalize_session(state_file: Path, session_data: dict):
    """最终化 session：生成总结、更新 Linear、标记完成"""
    session_id = session_data.get("session_id")
    transcript_path = session_data.get("transcript_path")

    log(f"开始最终化 session: {session_id}")

    # 1. 生成总结
    summary = summarize_transcript(transcript_path)
    log(f"生成总结: {summary[:100]}...")

    # 2. 更新 Linear Issue
    update_linear_issue(session_data, summary)

    # 3. 标记为已完成
    session_data["status"] = "finalized"
    session_data["finalized"] = True
    session_data["finalized_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    session_data["summary"] = summary

    with open(state_file, "w") as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False)

    log(f"Session {session_id} 已最终化")

def scan_sessions():
    """扫描所有 session，处理过期的"""
    if not SESSIONS_DIR.exists():
        return

    now = time.time()

    for state_file in SESSIONS_DIR.glob("*.json"):
        try:
            with open(state_file) as f:
                data = json.load(f)

            # 跳过已完成的
            if data.get("finalized"):
                continue

            # 检查是否过期
            last_active = data.get("last_active_epoch", 0)
            inactive_seconds = now - last_active

            if inactive_seconds > INACTIVE_THRESHOLD:
                log(f"发现过期 session: {data.get('session_id')} (不活跃 {inactive_seconds/3600:.1f} 小时)")
                finalize_session(state_file, data)

        except Exception as e:
            log(f"处理 {state_file} 失败: {e}")

def cleanup_old_sessions(days: int = 7):
    """清理超过 N 天的旧 session 文件"""
    if not SESSIONS_DIR.exists():
        return

    cutoff = time.time() - (days * 24 * 60 * 60)

    for state_file in SESSIONS_DIR.glob("*.json"):
        try:
            mtime = state_file.stat().st_mtime
            if mtime < cutoff:
                state_file.unlink()
                log(f"清理旧 session 文件: {state_file.name}")
        except Exception as e:
            log(f"清理 {state_file} 失败: {e}")

if __name__ == "__main__":
    log("=== Session Scanner 开始运行 ===")
    scan_sessions()
    cleanup_old_sessions()
    log("=== Session Scanner 完成 ===")
