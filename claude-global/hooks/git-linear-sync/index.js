#!/usr/bin/env node
/**
 * Git-Linear 同步 Hook
 *
 * 监听 Bash 工具调用，检测 git 操作并同步到 Linear：
 * - git checkout -b / git switch -c → Issue 状态变为 In Progress
 * - git worktree add → Issue 状态变为 In Progress
 * - gh pr create → Issue 状态变为 In Review
 */

const https = require('https');

const LINEAR_API_KEY = process.env.LINEAR_API_KEY;

// 状态 ID 映射
const STATES = {
  'In Progress': '53054e6e-1ca5-4b0d-b5c2-283ff2841ab4',
  'In Review': 'd8125aeb-6451-4da7-971c-b24581025d2a',
  '待人工测试': 'db66771b-185b-464e-beb1-dd11d54f44f9',
  '待发布': '177fe624-d3a6-4378-b3a3-b5b7a4246a7a',
  'Done': '05f950b5-1121-44e2-b60c-cdf923df4b28'
};

// 从 branch 名称提取 Issue Key (P-15, C-4 等)
function extractIssueKey(branchName) {
  const match = branchName.match(/[PC]-\d+/i);
  return match ? match[0].toUpperCase() : null;
}

// 解析命令，检测 git 操作
function parseCommand(command) {
  if (!command) return null;

  // git checkout -b / git switch -c (创建新分支)
  const checkoutMatch = command.match(/git\s+(?:checkout\s+-b|switch\s+-c)\s+([^\s]+)/);
  if (checkoutMatch) {
    return { type: 'branch_create', branch: checkoutMatch[1] };
  }

  // git worktree add
  const worktreeMatch = command.match(/git\s+worktree\s+add\s+[^\s]+\s+(?:-b\s+)?([^\s]+)/);
  if (worktreeMatch) {
    return { type: 'branch_create', branch: worktreeMatch[1] };
  }

  // gh pr create
  if (command.includes('gh pr create')) {
    // 获取当前分支名
    return { type: 'pr_create' };
  }

  return null;
}

// 调用 Linear API
async function linearRequest(query, variables = {}) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({ query, variables });

    const options = {
      hostname: 'api.linear.app',
      path: '/graphql',
      method: 'POST',
      headers: {
        'Authorization': LINEAR_API_KEY,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data)
      }
    };

    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(body));
        } catch (e) {
          reject(e);
        }
      });
    });

    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

// 根据 Issue Key 获取 Issue ID
async function getIssueByKey(issueKey) {
  const query = `
    query($filter: IssueFilter) {
      issues(filter: $filter, first: 1) {
        nodes {
          id
          identifier
          title
          state { id name }
          labels { nodes { name } }
        }
      }
    }
  `;

  const result = await linearRequest(query, {
    filter: { identifier: { eq: issueKey } }
  });

  return result?.data?.issues?.nodes?.[0];
}

// 更新 Issue 状态
async function updateIssueState(issueId, stateId) {
  const mutation = `
    mutation($issueId: String!, $stateId: String!) {
      issueUpdate(id: $issueId, input: { stateId: $stateId }) {
        success
        issue {
          identifier
          state { name }
        }
      }
    }
  `;

  return linearRequest(mutation, { issueId, stateId });
}

// 主函数
async function main() {
  try {
    // 从 stdin 读取 hook 数据
    let input = '';
    for await (const chunk of process.stdin) {
      input += chunk;
    }

    const hookData = JSON.parse(input);

    // 只处理 Bash 工具的 PostToolUse
    if (hookData.tool_name !== 'Bash') {
      console.log(JSON.stringify({ continue: true }));
      return;
    }

    const command = hookData.tool_input?.command;
    const gitOp = parseCommand(command);

    if (!gitOp) {
      console.log(JSON.stringify({ continue: true }));
      return;
    }

    let issueKey = null;
    let targetState = null;

    if (gitOp.type === 'branch_create') {
      issueKey = extractIssueKey(gitOp.branch);
      targetState = 'In Progress';
    } else if (gitOp.type === 'pr_create') {
      // 对于 PR 创建，尝试从工具输出中获取分支名
      // 或者从当前目录的 git branch 获取
      const output = hookData.tool_result?.stdout || '';
      const branchMatch = output.match(/head:\s*([^\s]+)/i) || output.match(/from\s+([^\s]+)\s+into/i);
      if (branchMatch) {
        issueKey = extractIssueKey(branchMatch[1]);
      }
      targetState = 'In Review';
    }

    if (!issueKey || !targetState) {
      console.log(JSON.stringify({ continue: true }));
      return;
    }

    // 获取 Issue 信息
    const issue = await getIssueByKey(issueKey);
    if (!issue) {
      console.log(JSON.stringify({
        continue: true,
        message: `Issue ${issueKey} not found in Linear`
      }));
      return;
    }

    // 如果状态已经是目标状态或更高级状态，不更新
    const currentStateName = issue.state?.name;
    if (currentStateName === targetState ||
        currentStateName === '待人工测试' ||
        currentStateName === '待发布' ||
        currentStateName === 'Done') {
      console.log(JSON.stringify({
        continue: true,
        message: `Issue ${issueKey} already in ${currentStateName}, skipping`
      }));
      return;
    }

    // 更新状态
    const stateId = STATES[targetState];
    const result = await updateIssueState(issue.id, stateId);

    if (result?.data?.issueUpdate?.success) {
      const message = `Linear: ${issueKey} → ${targetState}`;
      console.error(message); // 输出到 stderr 供用户看
      console.log(JSON.stringify({
        continue: true,
        message
      }));
    } else {
      console.log(JSON.stringify({
        continue: true,
        message: `Failed to update ${issueKey}`
      }));
    }

  } catch (error) {
    // Hook 出错不应阻止主流程
    console.error('git-linear-sync error:', error.message);
    console.log(JSON.stringify({ continue: true }));
  }
}

main();
