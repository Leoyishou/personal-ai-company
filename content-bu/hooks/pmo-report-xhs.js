#!/usr/bin/env node
/**
 * 内容事业部 - 小红书发布上报
 *
 * 触发时机：PostToolUse (mcp__xiaohongshu-mcp__publish_content|publish_with_video)
 * 职责：检测发布成功 → 调用 PMO Agent 处理
 */

const { spawn } = require('child_process');
const path = require('path');

const PMO_DIR = '/Users/liuyishou/usr/pac/pmo';

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

  // 只处理小红书 MCP 发布
  if (!tool_name?.includes('xiaohongshu-mcp__publish')) return;

  // 检测发布成功
  const output = typeof tool_output === 'string' ? tool_output : JSON.stringify(tool_output || '');
  if (output.includes('失败') || output.includes('error') || output.includes('Error')) return;

  // 构建事件数据
  const event = {
    type: 'xhs_publish',
    bu: 'content',
    sessionId: session_id,
    data: {
      title: tool_input?.title || '未知标题',
      tags: tool_input?.tags || [],
      content: tool_input?.content || '',
      imageCount: tool_input?.images?.length || 0
    }
  };

  // 调用 PMO Agent（异步，不阻塞）
  callPmoAgent(event);
}

/**
 * 调用 PMO Agent 处理事件
 * 使用 spawn 异步执行，不阻塞 hook
 */
function callPmoAgent(event) {
  const prompt = `处理小红书发布事件，根据 rules/content-bu.md 规则创建 Linear Issue：

事件数据：
${JSON.stringify(event, null, 2)}

请：
1. 检查是否已有同 sessionId 的 Issue
2. 如果有，更新该 Issue（追加发布记录）
3. 如果没有，根据规则创建新 Issue
4. 返回 Issue 标识符`;

  // 使用 claude CLI 调用 PMO Agent
  // --print 模式直接输出结果，不进入交互
  // --model haiku 使用快速模型降低延迟
  const child = spawn('claude', [
    '--print',
    '-p', prompt,
    '--model', 'haiku',
    '--cwd', PMO_DIR
  ], {
    detached: true,
    stdio: ['ignore', 'pipe', 'pipe']
  });

  // 收集输出
  let stdout = '';
  child.stdout.on('data', data => stdout += data.toString());

  child.on('close', code => {
    if (code === 0 && stdout.includes('-')) {
      // 提取 Issue 标识符（如 C-123）
      const match = stdout.match(/[PC]-\d+/);
      if (match) {
        console.log(`✅ PMO Agent: ${match[0]}`);
      }
    }
  });

  // 不等待完成，让 hook 快速返回
  child.unref();
}
