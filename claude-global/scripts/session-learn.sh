#!/bin/bash
# session-learn.sh - 对历史 session 运行 exit-learn 工作流
#
# 用法：
#   session-learn.sh                     # 列出最近 20 个 session
#   session-learn.sh <session-id>        # 对指定 session 生成学习笔记
#   session-learn.sh <session-id> <cwd>  # 指定工作目录（可选）

set -e

SESSIONS_ROOT="$HOME/.claude/projects"
EXIT_LEARN_CMD="$HOME/.claude/commands/exit-learn.md"

# ── 列出最近 sessions ────────────────────────────────────────────
if [ -z "$1" ]; then
  echo "最近 20 个 sessions（按修改时间排序）："
  echo ""
  find "$SESSIONS_ROOT" -name "*.jsonl" \
    -not -path "*/subagents/*" \
    -not -path "*acompact*" \
    | sort -t/ -k1 \
    | xargs ls -lt 2>/dev/null \
    | head -20 \
    | awk '{print $NF}' \
    | while read f; do
        session_id=$(basename "$f" .jsonl)
        project=$(basename $(dirname "$f"))
        # 取第一条 user 消息作为预览
        preview=$(python3 -c "
import json, sys
try:
    with open('$f') as fp:
        for line in fp:
            obj = json.loads(line)
            if obj.get('type') == 'user' and not obj.get('isSidechain'):
                content = obj.get('message', {}).get('content', '')
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    text = ' '.join(c.get('text','') for c in content if isinstance(c,dict) and c.get('type')=='text')
                else:
                    text = ''
                text = text.strip().replace('\n', ' ')[:60]
                if text:
                    print(text)
                    break
except: pass
" 2>/dev/null)
        echo "  $session_id  [$project]"
        [ -n "$preview" ] && echo "    → $preview"
      done
  echo ""
  echo "用法：session-learn.sh <session-id>"
  exit 0
fi

SESSION_ID="$1"

# ── 找到 JSONL 文件 ─────────────────────────────────────────────
JSONL_FILE=$(find "$SESSIONS_ROOT" -name "${SESSION_ID}.jsonl" \
  -not -path "*/subagents/*" | head -1)

if [ -z "$JSONL_FILE" ]; then
  echo "❌ 找不到 session: $SESSION_ID"
  exit 1
fi

echo "📂 Session 文件: $JSONL_FILE"
echo ""

# ── 提取对话文本 ─────────────────────────────────────────────────
TRANSCRIPT=$(python3 << 'PYEOF'
import json, sys, os

jsonl_file = os.environ.get('JSONL_FILE')
messages = []

with open(jsonl_file) as f:
    for line in f:
        try:
            obj = json.loads(line)
        except:
            continue

        if obj.get('isSidechain'):
            continue
        if obj.get('type') not in ('user', 'assistant'):
            continue

        role = obj['type']
        content = obj.get('message', {}).get('content', '')

        if isinstance(content, str):
            text = content.strip()
        elif isinstance(content, list):
            parts = []
            for c in content:
                if not isinstance(c, dict):
                    continue
                # 跳过 thinking 块
                if c.get('type') == 'text':
                    parts.append(c.get('text', ''))
                elif c.get('type') == 'tool_result':
                    # tool result 太长，只取前200字
                    for sub in (c.get('content') or []):
                        if isinstance(sub, dict) and sub.get('type') == 'text':
                            parts.append(f"[工具结果片段]: {sub.get('text','')[:200]}")
            text = '\n'.join(parts).strip()
        else:
            text = ''

        if not text:
            continue

        # 截断超长消息
        if len(text) > 1000:
            text = text[:1000] + '...[截断]'

        label = 'USER' if role == 'user' else 'ASSISTANT'
        messages.append(f"[{label}]\n{text}")

# 限制总长度（约 50 轮对话）
output = '\n\n---\n\n'.join(messages[:100])
print(output)
PYEOF
)

if [ -z "$TRANSCRIPT" ]; then
  echo "❌ 无法提取对话内容"
  exit 1
fi

TRANSCRIPT_LEN=${#TRANSCRIPT}
echo "📝 提取到对话文本：${TRANSCRIPT_LEN} 字符"
echo ""

# ── 读取 exit-learn 工作流 ───────────────────────────────────────
EXIT_LEARN_WORKFLOW=$(cat "$EXIT_LEARN_CMD")

# ── 构建 prompt ──────────────────────────────────────────────────
PROMPT="你是一个学习笔记生成专家。以下是一段历史 session 的对话记录。

请严格按照 exit-learn 工作流处理这段对话，生成学习笔记并保存到 Obsidian。

## exit-learn 工作流

$EXIT_LEARN_WORKFLOW

## 历史 Session 对话记录

$TRANSCRIPT

## 执行指令

请现在开始执行上述 exit-learn 工作流（Step 1 → Step 6），基于以上对话内容生成学习笔记。
今天日期：$(date +%Y-%m-%d)
"

# ── 启动新的 claude -p 子进程 ────────────────────────────────────
echo "🚀 启动 Claude 子进程处理 session..."
echo "   (这是独立进程，不影响当前 session)"
echo ""

# 移除 ANTHROPIC_API_KEY，使用 Pro 订阅认证
CLAUDE_BIN=$(which claude)

# 写 prompt 到临时文件，避免 shell 转义问题
PROMPT_FILE=$(mktemp /tmp/session-learn-prompt-XXXXXX.txt)
echo "$PROMPT" > "$PROMPT_FILE"

# 用 --print 模式启动（非交互，直接输出结果）
env -u ANTHROPIC_API_KEY "$CLAUDE_BIN" \
  --print \
  --allowedTools "Bash,Read,Write,Glob,Grep" \
  < "$PROMPT_FILE"

rm -f "$PROMPT_FILE"
echo ""
echo "✅ 完成"
