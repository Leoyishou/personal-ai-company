#!/usr/bin/env node
/**
 * 内容事业部 - B站发布上报
 *
 * 触发时机：PostToolUse (Bash: biliup upload)
 * 职责：检测 B站发布成功 → 上报 PMO
 */

const { handleEvent } = require('/Users/liuyishou/usr/pac/pmo/lib/handler');

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  try {
    const hookData = JSON.parse(input);
    main(hookData);
  } catch (e) {}
});

function main(hookData) {
  const { tool_name, tool_input, tool_output, session_id } = hookData;

  // 只处理 Bash 工具且包含 biliup
  if (tool_name !== 'Bash') return;
  const command = tool_input?.command || '';
  if (!command.includes('biliup')) return;

  // 检测发布成功
  const output = typeof tool_output === 'string' ? tool_output : JSON.stringify(tool_output || '');
  if (output.includes('失败') || output.includes('error') || output.includes('Error')) return;

  // 提取视频标题（从命令行参数）
  const titleMatch = command.match(/--title\s+["']([^"']+)["']/);
  const title = titleMatch ? titleMatch[1] : '未知标题';

  const result = handleEvent({
    type: 'bilibili_publish',
    bu: 'content',
    sessionId: session_id,
    data: {
      title,
      command: command.substring(0, 200),
      output: output.substring(0, 300)
    }
  });

  if (result.result === 'created') {
    console.log(`✅ PMO: B站发布 tracked - ${result.issue?.identifier}`);
  }
}
