#!/usr/bin/env node
/**
 * 投资事业部 - 交易上报
 *
 * 触发时机：PostToolUse (Skill: futu-trades)
 * 职责：检测交易执行 → 上报 PMO
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

  // 只处理 Skill 工具且是 futu-trades
  if (tool_name !== 'Skill') return;
  const skillName = tool_input?.skill || tool_input?.name || '';
  if (!skillName.includes('futu')) return;

  const output = typeof tool_output === 'string' ? tool_output : JSON.stringify(tool_output || '');

  // 只追踪实际交易，不追踪查询
  if (!output.includes('买入') && !output.includes('卖出') && !output.includes('成交')) return;

  const result = handleEvent({
    type: 'trade',
    bu: 'investment',
    sessionId: session_id,
    data: {
      output: output.substring(0, 500)
    }
  });

  if (result.result === 'created') {
    console.log(`✅ PMO: 交易 tracked - ${result.issue?.identifier}`);
  }
}
