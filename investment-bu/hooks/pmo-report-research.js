#!/usr/bin/env node
/**
 * 投资事业部 - 调研上报
 *
 * 触发时机：PostToolUse (Skill: research)
 * 职责：检测深度调研完成 → 上报 PMO
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
  const { tool_name, tool_input, tool_output, session_id, cwd } = hookData;

  // 只处理 Skill 工具且是 research
  if (tool_name !== 'Skill') return;
  const skillName = tool_input?.skill || tool_input?.name || '';
  if (!skillName.includes('research')) return;

  // 只在投资事业部目录下触发
  if (!cwd?.includes('investment-bu')) return;

  const output = typeof tool_output === 'string' ? tool_output : JSON.stringify(tool_output || '');

  // 提取调研主题
  const topic = tool_input?.args || '未知主题';

  const result = handleEvent({
    type: 'research',
    bu: 'investment',
    sessionId: session_id,
    data: {
      topic: topic.substring(0, 100),
      output: output.substring(0, 500)
    }
  });

  if (result.result === 'created') {
    console.log(`✅ PMO: 调研 tracked - ${result.issue?.identifier}`);
  }
}
