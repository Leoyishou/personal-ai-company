#!/usr/bin/env node
/**
 * 内容事业部 - 小红书发布上报
 *
 * 触发时机：PostToolUse (Skill)
 * 匹配条件：skill === 'xiaohongshu' && args 包含发布相关内容
 * 职责：检测发布成功 → 启动 PMO Agent 智能分析并创建 Linear Issue
 */

const { spawn } = require('child_process');
const fs = require('fs');

const PMO_DIR = '/Users/liuyishou/usr/pac/pmo';
const CLAUDE_BIN = '/Users/liuyishou/.local/share/fnm/node-versions/v22.16.0/installation/bin/claude';
const LOG_FILE = '/tmp/pmo-report-xhs.log';

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

  log(`Input: tool_name=${tool_name}, skill=${tool_input?.skill}`);

  // 只处理 Skill 工具调用
  if (tool_name !== 'Skill') return;

  // 只监控 xiaohongshu skill（所有小红书发布已收口到此 skill）
  const skill = tool_input?.skill;
  if (skill !== 'xiaohongshu') {
    log(`Skip: skill=${skill}, not xiaohongshu`);
    return;
  }

  // 获取 args
  const args = tool_input?.args || '';

  // 只处理发布动作（args 里有标题或图片）
  if (!args.includes('标题') && !args.includes('--title') && !args.includes('发布')) {
    log('Skip: not a publish action');
    return;
  }

  // 从 args 中提取信息
  const publishInfo = parsePublishArgs(args);

  if (!publishInfo.title) {
    log('Skip: no title found');
    return;
  }

  log(`Detected publish: ${JSON.stringify(publishInfo)}`);

  // 构建事件数据
  const event = {
    type: 'xhs_publish',
    bu: 'content',
    sessionId: session_id || 'unknown',
    data: {
      title: publishInfo.title,
      tags: publishInfo.tags,
      content: publishInfo.content?.substring(0, 500) || '',
      imageCount: publishInfo.imageCount,
      isVideo: publishInfo.isVideo
    }
  };

  // 启动 PMO Agent 智能分析
  callPmoAgent(event);
}

/**
 * 从 skill args 字符串中解析发布信息
 */
function parsePublishArgs(args) {
  const result = {
    title: null,
    content: null,
    tags: [],
    imageCount: 0,
    isVideo: false
  };

  // 尝试匹配"标题：xxx"或"标题:xxx"格式
  let titleMatch = args.match(/标题[：:]\s*([^\n]+)/);
  if (titleMatch) {
    result.title = titleMatch[1].trim();
  }

  // 尝试匹配 --title "xxx" 格式
  if (!result.title) {
    titleMatch = args.match(/--title\s+["']([^"']+)["']/);
    if (titleMatch) {
      result.title = titleMatch[1].trim();
    }
  }

  // 提取标签
  const tagsMatch = args.match(/标签[：:]?\s*([^\n]+)/);
  if (tagsMatch) {
    result.tags = tagsMatch[1].split(/[,，、]/).map(t => t.trim().replace(/^#/, ''));
  }

  // 从 hashtags 提取
  const hashtagMatch = args.match(/#(\S+)/g);
  if (hashtagMatch && result.tags.length === 0) {
    result.tags = hashtagMatch.map(t => t.replace('#', ''));
  }

  // 计算图片数量
  const imageMatches = args.match(/\.(jpg|jpeg|png|gif|webp)/gi);
  if (imageMatches) {
    result.imageCount = imageMatches.length;
  }

  // 检测是否视频
  result.isVideo = /视频|video|\.mp4|\.mov/i.test(args);

  // 提取内容（文案部分）
  const contentMatch = args.match(/文案[：:]\s*([\s\S]*?)(?=\n\n|标签|图片|$)/);
  if (contentMatch) {
    result.content = contentMatch[1].trim();
  }

  return result;
}

/**
 * 启动 PMO Agent 智能分析并创建 Linear Issue
 *
 * Agent 会：
 * 1. 读取 session 对话历史，了解完整上下文
 * 2. 阅读 CLAUDE.md 和 rules/content-bu.md 了解规范
 * 3. 智能提炼应该记录的内容
 * 4. 调用 /api-linear skill 创建 Issue
 */
function callPmoAgent(event) {
  const prompt = `你是 PMO 记录员，只负责创建 Linear Issue 来记录发布事件。

## 严格禁令
**禁止调用任何 MCP 工具（publish_content、publish_with_video、search_feeds 等）！**
**禁止执行任何发布操作！内容已经发布完成，你只需要记录到 Linear。**

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
- 特别关注：发布的标题、文案、图片、标签等

### 2. 按规范创建 Issue
阅读 rules/content-bu.md，按模板创建 Issue：
- 标题格式：【MMdd-HH】小红书：{笔记标题}
- Description 包含 sessionId、发布信息、内容预览、数据追踪表格

### 3. 调用 linear-cli.js 创建 Issue
使用 linear-cli.js 创建 Issue（自动处理 markdown 换行）：

\`\`\`bash
node ~/.claude/skills/api-linear/linear-cli.js create \\
  --team content \\
  --title "【0204-16】小红书：xxx" \\
  --description "sessionId: xxx\\n\\n## 发布信息\\n..." \\
  --labels "b4fa7209-3d42-4cdb-98c0-ee2742dd647a"
\`\`\`

**重要**：必须添加 \`--labels\` 参数，使用「发布」标签 ID: \`b4fa7209-3d42-4cdb-98c0-ee2742dd647a\`

### 4. 关联 Prompt 模板（如果识别到）
从 session 历史中检查是否使用了 api-draw skill，如果有，提取使用的模板名称（如「手绘白板」「人物语录」等）。

然后用 link-doc 命令关联到刚创建的 Issue：
\`\`\`bash
# 可用模板：手绘白板, 人物语录, 学霸笔记, 思维导图, 技术对比, 信息图表, 时间线, 知识卡片, 对话框, 数据可视化, 代码展示, 金句
node ~/.claude/skills/api-linear/linear-cli.js link-doc --id C-xxx --prompt "模板名"
\`\`\`

直接执行，不要询问确认。`;

  // 移除 ANTHROPIC_API_KEY，让 claude 使用 Pro 订阅认证
  const { ANTHROPIC_API_KEY, ...cleanEnv } = process.env;

  const child = spawn(CLAUDE_BIN, [
    '--dangerously-skip-permissions',
    '--model', 'haiku',
    '--max-turns', '10',
    '--disallowedTools', 'mcp__xiaohongshu-mcp*,Skill'
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
