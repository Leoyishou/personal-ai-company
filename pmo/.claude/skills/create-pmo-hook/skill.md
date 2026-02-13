# create-pmo-hook

创建 Hook → 启动 PMO Agent → 记录到 Linear 的完整流程模板。

## 一、架构原则

```
事件发生（工具调用/Session 结束）
    ↓
Hook 检测事件（轻量判断，快速返回）
    ↓
Hook 启动 PMO Agent（后台，detached）
    ↓
PMO Agent 读取上下文 + 调用 Linear API
```

**关键原则**：
- Hook 只做**检测和投递**，不做复杂逻辑
- 所有 Linear 操作通过 **PMO Agent** 完成
- Agent 使用 **Pro 订阅**（移除 ANTHROPIC_API_KEY）

## 二、Hook 模板

### 2.1 文件结构

```
{bu}-bu/hooks/pmo-report-{event}.js   # Hook 脚本
{bu}-bu/.claude/settings.json         # Hook 注册
```

### 2.2 Hook 脚本模板

```javascript
#!/usr/bin/env node
/**
 * {事业部} - {事件描述}
 *
 * 触发时机：PostToolUse ({Tool})
 * 匹配条件：{具体条件}
 * 职责：检测{事件} → 启动 PMO Agent 创建 Linear Issue
 */

const { spawn } = require('child_process');
const fs = require('fs');

const PMO_DIR = '/Users/liuyishou/usr/pac/pmo';
const CLAUDE_BIN = '/Users/liuyishou/.local/share/fnm/node-versions/v22.16.0/installation/bin/claude';
const LOG_FILE = '/tmp/pmo-report-{event}.log';

function log(msg) {
  fs.appendFileSync(LOG_FILE, `[${new Date().toISOString()}] ${msg}\n`);
}

// 从 stdin 读取 hook 输入
let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  try {
    const hookData = JSON.parse(input);
    main(hookData);
  } catch (e) {
    log(`Parse error: ${e.message}`);
  }
});

function main(hookData) {
  const { tool_name, tool_input, tool_response, session_id, cwd } = hookData;

  log(`Input: tool_name=${tool_name}, ...`);

  // ========== 1. 过滤条件 ==========
  // 只处理特定工具
  if (tool_name !== 'Skill') {
    console.log(JSON.stringify({ result: 'skipped', reason: 'Not target tool' }));
    return;
  }

  // 只处理特定 skill/参数
  const skill = tool_input?.skill;
  if (skill !== 'target-skill') {
    log(`Skip: skill=${skill}`);
    console.log(JSON.stringify({ result: 'skipped', reason: 'Not target skill' }));
    return;
  }

  // 其他条件检查（cwd、args 等）
  // ...

  log(`Detected event: ...`);

  // ========== 2. 构建事件数据 ==========
  const event = {
    type: 'event_type',
    bu: 'product|content|investment',
    sessionId: session_id || 'unknown',
    data: {
      // 事件相关数据
    }
  };

  // ========== 3. 启动 PMO Agent ==========
  callPmoAgent(event);
}

/**
 * 启动 PMO Agent
 */
function callPmoAgent(event) {
  const prompt = `处理{事件}，创建 Linear Issue。

## 基本信息
- **sessionId**: ${event.sessionId}
- **事业部**: ${event.bu}

## 事件数据
${JSON.stringify(event.data, null, 2)}

## 任务

### 1. 获取完整上下文
读取 session 对话历史：
\`\`\`bash
cat ~/.claude/sessions/${event.sessionId}.json
\`\`\`
然后读取 transcript_path 指向的文件。

### 2. 创建 Issue
使用 linear-cli.js：
\`\`\`bash
node ~/.claude/skills/api-linear/linear-cli.js create \\
  --team {team} \\
  --title "【$(date +%m%d-%H)】{类型}：xxx" \\
  --project "{project-id}" \\
  --description "sessionId: ${event.sessionId}\\n\\n..."
\`\`\`

直接执行，不要询问确认。`;

  // 移除 ANTHROPIC_API_KEY，让 claude 使用 Pro 订阅认证
  const { ANTHROPIC_API_KEY, ...cleanEnv } = process.env;

  const child = spawn(CLAUDE_BIN, [
    '--dangerously-skip-permissions',
    '--model', 'haiku',        // 轻量任务用 haiku
    '--max-turns', '15'
  ], {
    cwd: PMO_DIR,
    detached: true,            // 后台运行
    stdio: ['pipe', 'ignore', 'ignore'],
    env: cleanEnv              // 不传 API key
  });

  child.stdin.write(prompt);
  child.stdin.end();
  child.unref();               // 不等待子进程

  log('PMO Agent spawned');

  console.log(JSON.stringify({
    result: 'success',
    message: 'PMO Agent spawned'
  }));
}
```

### 2.3 设置可执行权限

```bash
chmod +x {bu}-bu/hooks/pmo-report-{event}.js
```

## 三、注册 Hook

在 `{bu}-bu/.claude/settings.json` 中添加：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Skill",
        "hooks": [
          {
            "type": "command",
            "command": "node /Users/liuyishou/usr/pac/{bu}-bu/hooks/pmo-report-{event}.js",
            "timeout": 30,
            "statusMessage": "PMO tracking..."
          }
        ]
      }
    ]
  }
}
```

### 3.1 Matcher 类型

| Matcher | 触发条件 |
|---------|---------|
| `Skill` | 任何 skill 调用 |
| `Write` | 写文件 |
| `Edit` | 编辑文件 |
| `Bash` | 执行命令 |
| `*` | 所有工具 |

### 3.2 多个 Hook 并行

同一 matcher 下的多个 hook 会**并行执行**：

```json
{
  "matcher": "Skill",
  "hooks": [
    { "command": "node hook1.js", ... },
    { "command": "node hook2.js", ... }
  ]
}
```

## 四、PMO Agent Prompt 模板

### 4.1 通用结构

```
处理{事件类型}，创建 Linear Issue。

## 基本信息
- sessionId、事业部、时间戳等

## 事件数据
- Hook 传递的快速数据

## 任务
### 1. 获取上下文
- 读取 session 历史
- 提取关键信息

### 2. 创建/更新 Issue
- 调用 linear-cli.js
- 按规范填写字段

### 3. 附加操作（可选）
- 打标签
- 关联项目
- 关联文档

直接执行，不要询问确认。
```

### 4.2 Session 历史读取

```bash
# 读取 session 元数据
cat ~/.claude/sessions/{sessionId}.json

# 元数据结构：
# {
#   "session_id": "...",
#   "transcript_path": "~/.claude/projects/.../xxx.jsonl",
#   "cwd": "/path/to/project",
#   "turn_count": 15
# }

# 读取完整对话
cat {transcript_path}
```

## 五、Linear CLI 用法

### 5.1 创建 Issue

```bash
node ~/.claude/skills/api-linear/linear-cli.js create \
  --team product \
  --title "【0204-15】测试：Viva 首页" \
  --project "50deb7b2-f67b-4dd4-b7e9-7809dd4229c0" \
  --labels "label-id-1,label-id-2" \
  --description "sessionId: xxx\n\n## 内容\n..."
```

### 5.2 更新 Issue

```bash
# 更新状态
node linear-cli.js update --id P-123 --state in_progress

# 追加内容
node linear-cli.js update --id P-123 --append "## 新增内容\n..."
```

### 5.3 搜索 Issue

```bash
# 按 sessionId 搜索
node linear-cli.js search --session abc-123-def

# 按关键词搜索
node linear-cli.js search --query "Viva"
```

## 六、Team 和 Project ID 速查

### 6.1 Team IDs

| 事业部 | Team ID | Key |
|--------|---------|-----|
| 产品 | `fcaf8084-612e-43e2-b4e4-fe81ae523627` | P |
| 内容 | `4bb065b8-982f-4a44-830d-8d88fe8c9828` | C |
| PMO | `1e658f17-2cdf-4bdd-82ad-c63e8a7c4ebb` | PMO |

### 6.2 Project IDs（产品）

| 项目 | Project ID |
|------|------------|
| Viva | `50deb7b2-f67b-4dd4-b7e9-7809dd4229c0` |

### 6.3 Project IDs（内容）

| 项目 | Project ID |
|------|------------|
| n张图系列 | `d6a1d29d-7bca-42c5-8779-71467fa97e5c` |
| 人物语录系列 | `3a246550-a979-416e-8810-1c094fcc810c` |
| 技术科普系列 | `b422ae73-64d5-42b1-9458-1992285877b2` |

## 七、调试技巧

### 7.1 查看 Hook 日志

```bash
tail -f /tmp/pmo-report-{event}.log
```

### 7.2 手动测试 Hook

```bash
echo '{"tool_name":"Skill","tool_input":{"skill":"playwright-skill"},"session_id":"test-123","cwd":"/path/to/viva"}' | node hooks/pmo-report-test.js
```

### 7.3 查看 PMO Agent 输出

PMO Agent 以 detached 模式运行，输出被忽略。如需调试：

```javascript
// 临时修改 stdio
stdio: ['pipe', fs.openSync('/tmp/pmo-agent.log', 'a'), fs.openSync('/tmp/pmo-agent.log', 'a')]
```

## 八、已有 Hook 参考

| Hook | 位置 | 触发条件 |
|------|------|---------|
| superpowers-tracker | `pmo/hooks/` | Skill(superpowers:*) |
| pmo-report-xhs | `content-bu/hooks/` | Skill(xiaohongshu) |
| pmo-report-test | `product-bu/hooks/` | Skill(playwright-skill) + cwd∈viva |

## 九、注意事项

1. **移除 API Key**：必须用 `cleanEnv` 启动 agent，否则会消耗 API 余额
2. **后台运行**：使用 `detached: true` + `child.unref()`，不阻塞主 session
3. **快速返回**：Hook 需在 timeout 内返回 JSON，复杂逻辑交给 Agent
4. **幂等设计**：PMO Agent 应检查是否已有相同 sessionId 的 Issue
5. **日志记录**：写入 `/tmp/` 便于调试，不污染项目目录
