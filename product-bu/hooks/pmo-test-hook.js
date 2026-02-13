#!/usr/bin/env node
/**
 * 产品事业部 - PMO Agent 测试 Hook
 *
 * 触发时机：PostToolUse (Write) 写入 product-bu 目录下的 .pmo-test 文件
 * 职责：启动 PMO Agent 创建 Linear Issue
 */

const { spawn } = require('child_process');

const PMO_DIR = '/Users/liuyishou/usr/pac/pmo';
const CLAUDE_BIN = '/Users/liuyishou/.local/share/fnm/node-versions/v22.16.0/installation/bin/claude';

// 从 stdin 读取 hook 输入
let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  try {
    const hookData = JSON.parse(input);
    main(hookData);
  } catch (e) {
    // 静默失败
  }
});

function main(hookData) {
  const { tool_name, tool_input, tool_output, session_id } = hookData;

  // 只处理 Write 工具
  if (tool_name !== 'Write') return;

  // 只处理 product-bu 目录下的 .pmo-test 文件
  const filePath = tool_input?.file_path || '';
  if (!filePath.includes('product-bu') || !filePath.endsWith('.pmo-test')) return;

  // 提取测试内容
  const content = tool_input?.content || '测试内容';

  // 构建事件数据
  const event = {
    type: 'pmo_test',
    bu: 'product',
    sessionId: session_id || 'unknown',
    data: {
      filePath,
      content: content.substring(0, 200)
    }
  };

  // 启动 PMO Agent
  callPmoAgent(event);
}

function callPmoAgent(event) {
  const prompt = `这是一个 PMO Agent 测试事件。请根据 CLAUDE.md 和 rules/product-bu.md 规范创建 Linear Issue。

事件数据：
${JSON.stringify(event, null, 2)}

请：
1. 在产品事业部 (Team ID: fcaf8084-612e-43e2-b4e4-fe81ae523627) 创建一个测试 Issue
2. 标题格式：【MMdd-HH】PMO测试：Agent架构验证
3. 使用 Bash 工具执行 curl 调用 Linear GraphQL API
4. LINEAR_API_KEY 在 ~/.claude/secrets.env 中，用 export $(grep -v '^#' ~/.claude/secrets.env | xargs) 加载
5. 完成后输出 Issue 标识符

注意：这是后台任务，直接执行，不要询问确认。`;

  // 移除 ANTHROPIC_API_KEY，让 claude 使用 Pro 订阅认证而非 API key
  const { ANTHROPIC_API_KEY, ...cleanEnv } = process.env;

  const child = spawn(CLAUDE_BIN, [
    '--dangerously-skip-permissions',
    '--model', 'haiku',
    '--max-turns', '10'
  ], {
    cwd: PMO_DIR,
    detached: true,
    stdio: ['pipe', 'ignore', 'ignore'],
    env: cleanEnv
  });

  child.stdin.write(prompt);
  child.stdin.end();
  child.unref();

  console.log(JSON.stringify({
    result: 'success',
    message: 'PMO Agent spawned for product-bu test'
  }));
}
