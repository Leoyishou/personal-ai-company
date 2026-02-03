#!/usr/bin/env node
/**
 * 产品事业部 - Git Worktree 上报
 *
 * 触发时机：PostToolUse (Bash) - 检测 git worktree 命令
 * 职责：检测 git worktree 操作 → 上报 PMO
 */

const { handleEvent } = require('/Users/liuyishou/usr/pac/pmo/lib/handler');

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
  const { tool_name, tool_input, tool_output, session_id, cwd } = hookData;

  // 只处理 Bash 工具
  if (tool_name !== 'Bash') return;

  const command = tool_input?.command || '';

  // 检测 git worktree 命令
  if (!command.includes('git worktree')) return;

  // 解析 worktree 操作
  const addMatch = command.match(/git worktree add\s+(\S+)\s+(?:-b\s+)?(\S+)/);
  if (!addMatch) return;

  const worktreePath = addMatch[1];
  const branch = addMatch[2];

  // 从 branch 名提取 issue key (如 feat/P-15-xxx)
  const issueMatch = branch.match(/[PC]-\d+/);

  // 上报 PMO
  const result = handleEvent({
    type: 'git_worktree',
    bu: 'product',
    sessionId: session_id,
    data: {
      action: 'add',
      branch,
      worktreePath,
      issueKey: issueMatch ? issueMatch[0] : null,
      cwd
    }
  });

  if (result.result === 'existing_issue') {
    console.log(`✅ PMO: Linked to existing issue ${result.issueKey}`);
  } else if (result.result === 'new_branch') {
    console.log(`📝 PMO: New branch detected - ${branch}`);
  }
}
