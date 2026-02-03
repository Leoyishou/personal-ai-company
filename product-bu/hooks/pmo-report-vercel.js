#!/usr/bin/env node
/**
 * 产品事业部 - Vercel/Cloudflare 部署上报
 *
 * 触发时机：PostToolUse (Skill: api-deploy-static)
 * 职责：检测 Web 部署成功 → 上报 PMO
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

  // 只处理 Skill 工具且是 api-deploy-static
  if (tool_name !== 'Skill') return;
  const skillName = tool_input?.skill || tool_input?.name || '';
  if (!skillName.includes('deploy-static') && !skillName.includes('vercel')) return;

  // 检测部署成功
  const output = typeof tool_output === 'string' ? tool_output : JSON.stringify(tool_output || '');
  if (output.includes('失败') || output.includes('error') || output.includes('Error')) return;

  // 判断是 Vercel 还是 Cloudflare
  const platform = output.includes('cloudflare') ? 'Cloudflare' : 'Vercel';

  const result = handleEvent({
    type: 'deploy_web',
    bu: 'product',
    sessionId: session_id,
    data: {
      platform,
      cwd,
      output: output.substring(0, 500)
    }
  });

  if (result.result === 'created') {
    console.log(`✅ PMO: ${platform} deploy tracked - ${result.issue?.identifier}`);
  }
}
