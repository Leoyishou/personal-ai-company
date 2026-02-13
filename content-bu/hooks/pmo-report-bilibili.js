#!/usr/bin/env node
/**
 * 内容事业部 - B站发布上报
 *
 * 触发时机：PostToolUse (Bash)
 * 匹配条件：command 包含 biliup
 * 职责：检测 B站发布成功 → 启动 PMO Agent 智能分析并创建 Linear Issue
 */

const { spawn } = require('child_process');
const fs = require('fs');

const PMO_DIR = '/Users/liuyishou/usr/pac/pmo';
const CLAUDE_BIN = '/Users/liuyishou/.local/share/fnm/node-versions/v22.16.0/installation/bin/claude';
const LOG_FILE = '/tmp/pmo-report-bilibili.log';

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
  const { tool_name, tool_input, tool_output, session_id } = hookData;

  log(`Input: tool_name=${tool_name}`);

  // 只处理 Bash 工具且包含 biliup
  if (tool_name !== 'Bash') return;
  const command = tool_input?.command || '';
  if (!command.includes('biliup')) return;

  // 检测发布失败则跳过
  const output = typeof tool_output === 'string' ? tool_output : JSON.stringify(tool_output || '');
  if (output.includes('失败') || output.includes('error') || output.includes('Error')) {
    log('Skip: upload failed');
    return;
  }

  // 提取信息
  const publishInfo = parseBiliupCommand(command, output);

  if (!publishInfo.title) {
    log('Skip: no title found');
    return;
  }

  log(`Detected publish: ${JSON.stringify(publishInfo)}`);

  // 构建事件数据
  const event = {
    type: 'bilibili_publish',
    bu: 'content',
    sessionId: session_id || 'unknown',
    data: {
      title: publishInfo.title,
      desc: publishInfo.desc,
      tags: publishInfo.tags,
      tid: publishInfo.tid,
      bvid: publishInfo.bvid,
      command: command.substring(0, 300),
      output: output.substring(0, 500)
    }
  };

  // 启动 PMO Agent 智能分析
  callPmoAgent(event);
}

/**
 * 从 biliup 命令和输出中解析发布信息
 */
function parseBiliupCommand(command, output) {
  const result = {
    title: null,
    desc: null,
    tags: [],
    tid: null,
    bvid: null
  };

  // 提取 --title
  const titleMatch = command.match(/--title\s+["']([^"']+)["']/);
  if (titleMatch) result.title = titleMatch[1].trim();

  // 提取 --desc
  const descMatch = command.match(/--desc\s+["']([^"']+)["']/);
  if (descMatch) result.desc = descMatch[1].trim();

  // 提取 --tag
  const tagMatch = command.match(/--tag\s+["']([^"']+)["']/);
  if (tagMatch) result.tags = tagMatch[1].split(',').map(t => t.trim());

  // 提取 --tid
  const tidMatch = command.match(/--tid\s+(\d+)/);
  if (tidMatch) result.tid = tidMatch[1];

  // 从输出中提取 BV 号
  const bvMatch = output.match(/BV[a-zA-Z0-9]+/);
  if (bvMatch) result.bvid = bvMatch[0];

  return result;
}

/**
 * 启动 PMO Agent 智能分析并创建 Linear Issue
 */
function callPmoAgent(event) {
  const biliLink = event.data.bvid
    ? `https://www.bilibili.com/video/${event.data.bvid}`
    : '（未获取到 BV 号）';

  const prompt = `你是 PMO 记录员，只负责创建 Linear Issue 来记录 B站发布事件。

## 严格禁令
**禁止执行任何上传或发布操作！内容已经发布完成，你只需要记录到 Linear。**

## 基本信息
- **sessionId**: ${event.sessionId}
- **事业部**: ${event.bu}
- **事件类型**: ${event.type}

## 快速数据（来自 hook）
${JSON.stringify(event.data, null, 2)}

## 任务

### 1. 获取完整上下文
读取 session 对话历史，了解这次发布的完整上下文：
- 读取 ~/.claude/sessions/${event.sessionId}.json 获取 transcript_path
- 读取 transcript 文件，提取最近的对话内容
- 特别关注：视频主题、制作过程、使用的工具等

### 2. 按规范创建 Issue
阅读 rules/content-bu.md，按模板创建 Issue：
- 标题格式：【MMdd-HH】B站：{视频标题}
- Description 包含 sessionId、发布信息、视频链接、数据追踪

### 3. 调用 linear-cli.js 创建 Issue

\`\`\`bash
node ~/.claude/skills/api-linear/linear-cli.js create \\
  --team content \\
  --title "【MMdd-HH】B站：${(event.data.title || '').replace(/"/g, '\\"')}" \\
  --description "sessionId: ${event.sessionId}\\n\\n## 发布信息\\n- **标题**: ${(event.data.title || '').replace(/"/g, '\\"')}\\n- **标签**: ${(event.data.tags || []).join(', ')}\\n- **分区**: tid ${event.data.tid || '未知'}\\n- **发布时间**: ${new Date().toISOString()}\\n\\n## 视频链接\\n${biliLink}\\n\\n## 数据追踪\\n| 时间 | 播放 | 点赞 | 投币 | 收藏 |\\n|------|------|------|------|------|\\n| 发布时 | - | - | - | - |" \\
  --labels "b4fa7209-3d42-4cdb-98c0-ee2742dd647a"
\`\`\`

**重要**：必须添加 \`--labels\` 参数，使用「发布」标签 ID: \`b4fa7209-3d42-4cdb-98c0-ee2742dd647a\`

### 4. 关联项目（如果识别到）
从 session 历史中检查内容类型，如果属于已有系列（技术科普、n张图等），关联到对应 Project。

直接执行，不要询问确认。`;

  // 移除 ANTHROPIC_API_KEY，让 claude 使用 Pro 订阅认证
  const { ANTHROPIC_API_KEY, ...cleanEnv } = process.env;

  const child = spawn(CLAUDE_BIN, [
    '--dangerously-skip-permissions',
    '--model', 'haiku',
    '--max-turns', '10',
    '--disallowedTools', 'Skill'
  ], {
    cwd: PMO_DIR,
    detached: true,
    stdio: ['pipe', 'ignore', 'ignore'],
    env: cleanEnv
  });

  child.stdin.write(prompt);
  child.stdin.end();
  child.unref();

  log('PMO Agent spawned');

  console.log(JSON.stringify({
    result: 'success',
    message: 'PMO Agent spawned in background'
  }));
}
