/**
 * PMO Handler - 核心策略逻辑
 *
 * 职责：
 * 1. 接收 BU 上报的事件
 * 2. 判断归属（新项目 vs 老项目）
 * 3. 创建或更新 Linear Issue
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Team IDs
const TEAMS = {
  product: 'fcaf8084-612e-43e2-b4e4-fe81ae523627',
  content: '4bb065b8-982f-4a44-830d-8d88fe8c9828',
  investment: '4bb065b8-982f-4a44-830d-8d88fe8c9828', // TODO: 创建投资事业部 Team 后更新
  pmo: '1e658f17-2cdf-4bdd-82ad-c63e8a7c4ebb'
};

// 项目配置
const PROJECTS = {
  content: {
    'n张图系列': { id: 'd6a1d29d-7bca-42c5-8779-71467fa97e5c', keywords: ['n张图', '图文', '科普'] },
    '人物语录系列': { id: '3a246550-a979-416e-8810-1c094fcc810c', keywords: ['语录', '名言'] },
    '技术科普系列': { id: 'b422ae73-64d5-42b1-9458-1992285877b2', keywords: ['技术', '科普', '编程'] }
  },
  product: {
    'Viva': { id: '50deb7b2-f67b-4dd4-b7e9-7809dd4229c0', keywords: ['viva', '英语', '词汇'] }
  }
};

/**
 * 获取 Linear API Key
 */
function getLinearApiKey() {
  const secretsPath = path.join(process.env.HOME, '.claude/secrets.env');
  let key = process.env.LINEAR_API_KEY;

  if (!key && fs.existsSync(secretsPath)) {
    const secrets = fs.readFileSync(secretsPath, 'utf8');
    const match = secrets.match(/LINEAR_API_KEY=["']?([^"'\n]+)["']?/);
    if (match) key = match[1];
  }

  return key;
}

/**
 * 调用 Linear GraphQL API
 */
function callLinear(query, variables = {}) {
  const apiKey = getLinearApiKey();
  if (!apiKey) throw new Error('LINEAR_API_KEY not found');

  const payload = JSON.stringify({ query, variables }).replace(/'/g, "'\\''");

  const response = execSync(`curl -s -X POST https://api.linear.app/graphql \
    -H "Content-Type: application/json" \
    -H "Authorization: ${apiKey}" \
    -d '${payload}'`,
    { encoding: 'utf8', timeout: 15000 }
  );

  return JSON.parse(response);
}

/**
 * 生成时间戳标题前缀
 */
function getDatePrefix() {
  const now = new Date();
  return `${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}-${String(now.getHours()).padStart(2, '0')}`;
}

/**
 * 处理事件 - 核心入口
 * @param {Object} event - 上报的事件
 * @param {string} event.type - 事件类型 (xhs_publish, git_worktree, code_change, session_end)
 * @param {string} event.bu - 事业部 (content, product)
 * @param {string} event.sessionId - Session ID
 * @param {Object} event.data - 事件数据
 */
function handleEvent(event) {
  const { type, bu, sessionId, data } = event;

  switch (type) {
    // 产品事业部
    case 'git_worktree':
      return handleGitWorktree(bu, sessionId, data);
    case 'deploy_testflight':
      return handleDeploy(bu, sessionId, data, 'TestFlight');
    case 'deploy_web':
      return handleDeploy(bu, sessionId, data, data.platform || 'Vercel');
    // 内容事业部
    case 'xhs_publish':
      return handleXhsPublish(bu, sessionId, data);
    case 'bilibili_publish':
      return handleBilibiliPublish(bu, sessionId, data);
    case 'x_publish':
      return handleXPublish(bu, sessionId, data);
    // 投资事业部
    case 'trade':
      return handleTrade(bu, sessionId, data);
    case 'research':
      return handleResearch(bu, sessionId, data);
    // 全局
    case 'session_end':
      return handleSessionEnd(bu, sessionId, data);
    default:
      return { result: 'ignored', reason: `Unknown event type: ${type}` };
  }
}

/**
 * 处理小红书发布事件
 */
function handleXhsPublish(bu, sessionId, data) {
  const { title, tags, content, imageCount } = data;

  const issueTitle = `【${getDatePrefix()}】小红书：${title}`;
  const contentPreview = content?.length > 100 ? content.substring(0, 100) + '...' : content;

  const description = `sessionId: ${sessionId}

## 发布信息
- **标题**: ${title}
- **标签**: ${Array.isArray(tags) ? tags.join(', ') : tags}
- **图片数**: ${imageCount || 0}
- **发布时间**: ${new Date().toISOString()}

## 内容预览
${contentPreview || '(无)'}

## 笔记链接
⏳ 待回填...

## 数据追踪
| 时间 | 点赞 | 收藏 | 评论 |
|------|------|------|------|
| 发布时 | - | - | - |
`;

  const mutation = `
    mutation CreateIssue($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue { id identifier url }
      }
    }
  `;

  const result = callLinear(mutation, {
    input: {
      teamId: TEAMS.content,
      title: issueTitle,
      description
    }
  });

  if (result.data?.issueCreate?.success) {
    return {
      result: 'created',
      issue: result.data.issueCreate.issue
    };
  }

  return { result: 'failed', error: result.errors };
}

/**
 * 处理 Git Worktree 事件
 */
function handleGitWorktree(bu, sessionId, data) {
  const { branch, project, action } = data;

  // 从 branch 名提取 issue key (如 feat/P-15-xxx)
  const issueMatch = branch?.match(/[PC]-\d+/);

  if (issueMatch) {
    // 已有 issue，更新状态
    return { result: 'existing_issue', issueKey: issueMatch[0] };
  }

  // 新分支，可能需要创建 issue
  return { result: 'new_branch', branch, project };
}

/**
 * 处理部署事件
 */
function handleDeploy(bu, sessionId, data, platform) {
  const issueTitle = `【${getDatePrefix()}】部署：${platform}`;
  const description = `sessionId: ${sessionId}

## 部署信息
- **平台**: ${platform}
- **时间**: ${new Date().toISOString()}
- **目录**: ${data.cwd || '未知'}

## 输出
${data.output || '(无)'}
`;

  return createIssue(TEAMS.product, issueTitle, description);
}

/**
 * 处理 B站发布事件
 */
function handleBilibiliPublish(bu, sessionId, data) {
  const issueTitle = `【${getDatePrefix()}】B站：${data.title}`;
  const description = `sessionId: ${sessionId}

## 发布信息
- **标题**: ${data.title}
- **发布时间**: ${new Date().toISOString()}

## 视频链接
⏳ 待回填...
`;

  return createIssue(TEAMS.content, issueTitle, description);
}

/**
 * 处理 X 发布事件
 */
function handleXPublish(bu, sessionId, data) {
  const issueTitle = `【${getDatePrefix()}】X：${data.content?.substring(0, 30) || '推文'}`;
  const description = `sessionId: ${sessionId}

## 发布信息
- **内容**: ${data.content || '(无)'}
- **发布时间**: ${new Date().toISOString()}

## 推文链接
⏳ 待回填...
`;

  return createIssue(TEAMS.content, issueTitle, description);
}

/**
 * 处理交易事件
 */
function handleTrade(bu, sessionId, data) {
  const issueTitle = `【${getDatePrefix()}】交易记录`;
  const description = `sessionId: ${sessionId}

## 交易信息
- **时间**: ${new Date().toISOString()}

## 详情
${data.output || '(无)'}
`;

  return createIssue(TEAMS.investment, issueTitle, description);
}

/**
 * 处理调研事件
 */
function handleResearch(bu, sessionId, data) {
  const issueTitle = `【${getDatePrefix()}】调研：${data.topic || '深度调研'}`;
  const description = `sessionId: ${sessionId}

## 调研主题
${data.topic || '未知'}

## 调研摘要
${data.output || '(无)'}
`;

  return createIssue(TEAMS.investment, issueTitle, description);
}

/**
 * 通用创建 Issue 函数
 */
function createIssue(teamId, title, description) {
  const mutation = `
    mutation CreateIssue($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue { id identifier url }
      }
    }
  `;

  try {
    const result = callLinear(mutation, {
      input: { teamId, title, description }
    });

    if (result.data?.issueCreate?.success) {
      return { result: 'created', issue: result.data.issueCreate.issue };
    }
    return { result: 'failed', error: result.errors };
  } catch (e) {
    return { result: 'error', error: e.message };
  }
}

/**
 * 处理 Session 结束事件
 */
function handleSessionEnd(bu, sessionId, data) {
  const { summary, cwd } = data;

  // 判断是否值得上报
  if (!summary || summary.length < 100) {
    return { result: 'skipped', reason: 'Summary too short' };
  }

  // 根据 cwd 判断事业部
  const detectedBu = cwd?.includes('content-bu') ? 'content' :
                     cwd?.includes('product-bu') ? 'product' : 'pmo';

  return {
    result: 'needs_processing',
    bu: detectedBu,
    sessionId,
    summary: summary.substring(0, 500)
  };
}

module.exports = {
  handleEvent,
  getLinearApiKey,
  callLinear,
  TEAMS,
  PROJECTS
};
