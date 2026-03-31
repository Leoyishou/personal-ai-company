# Session Info Skill

读取 Claude Code Session 的完整对话历史。

## 使用方式

```
/session-info <sessionId>
```

## Session 存储结构

Claude Code 的 session 数据存储在两层：

```
~/.claude/sessions/{sessionId}.json          # Session 元数据
  ├── session_id
  ├── transcript_path  →  指向完整对话记录
  ├── cwd              →  工作目录
  ├── created_at
  ├── last_active_at
  └── turn_count

~/.claude/projects/{project-path}/{sessionId}.jsonl   # 完整对话记录
  每行一个 JSON，包含：
  ├── type: "user" / "assistant" / "tool_use" / "tool_result"
  ├── message: { role, content }
  └── timestamp
```

## 读取步骤

1. 读取 `~/.claude/sessions/{sessionId}.json`
2. 获取 `transcript_path`
3. 读取 transcript 文件（jsonl 格式）
4. 解析每行 JSON，提取对话内容

## 示例代码

```javascript
const fs = require('fs');
const path = require('path');

function getSessionInfo(sessionId) {
  // 1. 读取 session 元数据
  const sessionPath = path.join(process.env.HOME, '.claude/sessions', `${sessionId}.json`);
  const session = JSON.parse(fs.readFileSync(sessionPath, 'utf8'));

  // 2. 读取完整对话
  const transcript = fs.readFileSync(session.transcript_path, 'utf8')
    .split('\n')
    .filter(line => line.trim())
    .map(line => JSON.parse(line));

  // 3. 提取用户消息和 AI 回复
  const messages = transcript
    .filter(t => t.type === 'user' || t.type === 'assistant')
    .map(t => ({
      role: t.message?.role,
      content: typeof t.message?.content === 'string'
        ? t.message.content
        : t.message?.content?.[0]?.text || JSON.stringify(t.message?.content)
    }));

  return {
    sessionId: session.session_id,
    cwd: session.cwd,
    createdAt: session.created_at,
    turnCount: session.turn_count,
    messages
  };
}
```

## 输出示例

```json
{
  "sessionId": "abc-123-def",
  "cwd": "/Users/xxx/project",
  "createdAt": "2026-02-04T08:00:00Z",
  "turnCount": 5,
  "messages": [
    { "role": "user", "content": "帮我发一条小红书..." },
    { "role": "assistant", "content": "好的，我来帮你发布..." }
  ]
}
```

## 注意事项

- transcript 文件可能很大，建议只读取最近 N 条消息
- 消息内容可能是字符串或数组（tool_use 时）
- session 文件按 sessionId 命名，是 UUID 格式
