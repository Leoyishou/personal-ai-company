#!/usr/bin/env node
/**
 * 内容事业部 - X/Twitter 发布上报
 *
 * 触发时机：PostToolUse (Skill: x-post)
 * 职责：检测 X 发布成功 → 上报 PMO
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

  // 只处理 Skill 工具且是 x-post
  if (tool_name !== 'Skill') return;
  const skillName = tool_input?.skill || tool_input?.name || '';
  if (!skillName.includes('x-post') && !skillName.includes('twitter')) return;

  // 检测发布成功
  const output = typeof tool_output === 'string' ? tool_output : JSON.stringify(tool_output || '');
  if (output.includes('失败') || output.includes('error') || output.includes('Error')) return;

  // 提取推文内容
  const content = tool_input?.args || tool_input?.text || '';

  const result = handleEvent({
    type: 'x_publish',
    bu: 'content',
    sessionId: session_id,
    data: {
      content: content.substring(0, 280),
      output: output.substring(0, 300)
    }
  });

  if (result.result === 'created') {
    console.log(`✅ PMO: X 发布 tracked - ${result.issue?.identifier}`);
  }
}
