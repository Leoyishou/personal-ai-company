#!/usr/bin/env node
/**
 * 产品事业部 - 测试工作上报
 *
 * 触发时机：PostToolUse (Skill)
 * 匹配条件：skill === 'playwright-skill' && cwd 包含 viva 或其他产品目录
 * 职责：检测测试工作完成 → 启动 PMO Agent 创建测试类型 Issue
 */

const { spawn } = require('child_process');
const fs = require('fs');

const PMO_DIR = '/Users/liuyishou/usr/pac/pmo';
const CLAUDE_BIN = '/Users/liuyishou/.local/share/fnm/node-versions/v22.16.0/installation/bin/claude';
const LOG_FILE = '/tmp/pmo-report-test.log';

// 已知产品及其 Linear Project ID
const PROJECTS = {
  viva: {
    name: 'Viva',
    projectId: '50deb7b2-f67b-4dd4-b7e9-7809dd4229c0',
    keywords: ['viva', 'VoiceType']
  },
  'vocab-highlighter': {
    name: 'Vocab Highlighter',
    projectId: null, // TODO
    keywords: ['highlighter', 'vocab-highlighter']
  }
};

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

/**
 * 从 cwd 匹配产品项目
 */
function detectProject(cwd) {
  if (!cwd) return null;

  const cwdLower = cwd.toLowerCase();
  for (const [key, project] of Object.entries(PROJECTS)) {
    if (project.keywords.some(kw => cwdLower.includes(kw.toLowerCase()))) {
      return { key, ...project };
    }
  }
  return null;
}

function main(hookData) {
  const { tool_name, tool_input, tool_response, session_id, cwd } = hookData;

  log(`Input: tool_name=${tool_name}, skill=${tool_input?.skill}, cwd=${cwd}`);

  // 只处理 Skill 工具调用
  if (tool_name !== 'Skill') {
    console.log(JSON.stringify({ result: 'skipped', reason: 'Not a Skill call' }));
    return;
  }

  // 只监控 playwright-skill（测试工作的显式信号）
  const skill = tool_input?.skill;
  if (skill !== 'playwright-skill') {
    log(`Skip: skill=${skill}, not playwright-skill`);
    console.log(JSON.stringify({ result: 'skipped', reason: 'Not playwright-skill' }));
    return;
  }

  // 匹配产品项目
  const project = detectProject(cwd);
  if (!project) {
    log(`Skip: cwd=${cwd} doesn't match any known project`);
    console.log(JSON.stringify({ result: 'skipped', reason: 'Unknown project' }));
    return;
  }

  log(`Detected test for project: ${project.name}`);

  // 从 args 提取测试描述
  const args = tool_input?.args || '';

  // 构建事件数据
  const event = {
    type: 'app_test',
    bu: 'product',
    sessionId: session_id || 'unknown',
    project: project,
    data: {
      testArgs: args.substring(0, 500),
      cwd
    }
  };

  // 启动 PMO Agent 智能分析
  callPmoAgent(event);
}

/**
 * 启动 PMO Agent 智能分析并创建测试 Issue
 */
function callPmoAgent(event) {
  const prompt = `处理测试工作事件，创建 Linear Issue。

## 基本信息
- **sessionId**: ${event.sessionId}
- **事业部**: ${event.bu}
- **项目**: ${event.project.name}
- **Linear Project ID**: ${event.project.projectId || '无'}

## 测试参数
${event.data.testArgs || '(无)'}

## 任务

### 1. 获取完整上下文
读取 session 对话历史，了解这次测试的完整内容：
\`\`\`bash
# 读取 session 元数据
cat ~/.claude/sessions/${event.sessionId}.json
\`\`\`
然后读取 transcript_path 指向的文件，提取测试相关内容：
- 测试了哪些功能
- 发现了什么问题
- 测试结果如何

### 2. 按规范创建 Issue
标题格式：【MMdd-HH】测试：${event.project.name} xxx
在 Description 中包含：
- sessionId: ${event.sessionId}
- 测试范围
- 测试结果
- 发现的问题（如有）

### 3. 使用 linear-cli.js 创建 Issue
\`\`\`bash
node ~/.claude/skills/api-linear/linear-cli.js create \\
  --team product \\
  --title "【$(date +%m%d-%H)】测试：${event.project.name} xxx" \\
  --project "${event.project.projectId || ''}" \\
  --description "sessionId: ${event.sessionId}\\n\\n## 测试范围\\n...\\n\\n## 测试结果\\n..."
\`\`\`

### 4. 打上测试 Label
用 Linear GraphQL API 添加 Label（如有"测试"标签的话）。

直接执行，不要询问确认。完成后输出创建的 Issue 标识符。`;

  // 移除 ANTHROPIC_API_KEY，让 claude 使用 Pro 订阅认证
  const { ANTHROPIC_API_KEY, ...cleanEnv } = process.env;

  const child = spawn(CLAUDE_BIN, [
    '--dangerously-skip-permissions',
    '--model', 'haiku',
    '--max-turns', '15'
  ], {
    cwd: PMO_DIR,
    detached: true,
    stdio: ['pipe', 'ignore', 'ignore'],
    env: cleanEnv
  });

  child.stdin.write(prompt);
  child.stdin.end();
  child.unref();

  log('PMO Agent spawned for test report');

  console.log(JSON.stringify({
    result: 'success',
    message: `PMO Agent spawned for ${event.project.name} test report`
  }));
}
