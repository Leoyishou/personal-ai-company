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
  investment: '47b059ce-ce0b-4965-bad8-80481f71ecc9',
  pmo: '1e658f17-2cdf-4bdd-82ad-c63e8a7c4ebb'
};

// 产品事业部状态 ID（按流程顺序）
const PRODUCT_STATES = {
  backlog: '52220171-86ac-4a6a-83af-24ec12d55f51',
  todo: 'd430a64c-e7c1-465b-a086-7fb8397941e1',
  in_progress: '53054e6e-1ca5-4b0d-b5c2-283ff2841ab4',
  in_review: 'd8125aeb-6451-4da7-971c-b24581025d2a',
  ready_for_qa: 'db66771b-185b-464e-beb1-dd11d54f44f9',    // 待人工测试
  ready_for_release: '177fe624-d3a6-4378-b3a3-b5b7a4246a7a', // 待发布
  done: '05f950b5-1121-44e2-b60c-cdf923df4b28'
};

// Superpower Action 到状态的映射
const ACTION_TO_STATE = {
  'create_or_update_issue': PRODUCT_STATES.backlog,
  'set_in_progress': PRODUCT_STATES.in_progress,
  'set_in_review': PRODUCT_STATES.in_review,
  'set_ready_for_qa': PRODUCT_STATES.ready_for_qa,
  'set_ready_for_release': PRODUCT_STATES.ready_for_release,
  'set_done': PRODUCT_STATES.done
};

// Initiative IDs（战略层：Initiative → Project → Issue）
const INITIATIVES = {
  product: '9e5a045c-c886-4bc6-96a0-ebb62177b044',  // 代码杠杆
  content: '6dac99eb-70cd-4890-9e90-817d40911015',  // 媒体杠杆
  investment: '4bea1a6f-e0db-4e70-a22d-877b8301b980', // 资本杠杆
};

// 内容事业部 Label IDs
const CONTENT_LABELS = {
  publish: 'b4fa7209-3d42-4cdb-98c0-ee2742dd647a',    // 发布
  drawing: '5a95aaa6-ce9a-4871-81ef-1dcce2bbc3e7',    // 做图
  copywriting: 'be0f8c2e-7054-490f-84c1-f95212c07ef2', // 文案
  inspiration: '7be8f7f1-b476-4c27-87e4-e4b36fc2e6cb', // 灵感
  review: '072feefc-4d30-4522-af7d-ba6448ec960f',      // 后评估
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

  // 用文件传递 payload 避免 shell 转义问题
  const payloadFile = `/tmp/linear-payload-${Date.now()}.json`;
  fs.writeFileSync(payloadFile, JSON.stringify({ query, variables }));

  try {
    const response = execSync(`curl -s -X POST https://api.linear.app/graphql \
      -H "Content-Type: application/json" \
      -H "Authorization: ${apiKey}" \
      -d @${payloadFile}`,
      { encoding: 'utf8', timeout: 15000 }
    );
    return JSON.parse(response);
  } finally {
    try { fs.unlinkSync(payloadFile); } catch (e) {}
  }
}

/**
 * 按 sessionId 搜索已有 Issue
 */
function searchIssueBySessionId(teamId, sessionId) {
  const query = `
    query SearchIssues($teamId: String!, $filter: IssueFilter) {
      team(id: $teamId) {
        issues(filter: $filter, first: 5) {
          nodes { id identifier title description state { id name } }
        }
      }
    }
  `;

  try {
    const result = callLinear(query, {
      teamId,
      filter: { description: { contains: `sessionId: ${sessionId}` } }
    });
    return result.data?.team?.issues?.nodes || [];
  } catch (e) {
    console.error('searchIssueBySessionId error:', e.message);
    return [];
  }
}

/**
 * 更新 Issue 状态
 */
function updateIssueState(issueId, stateId) {
  const mutation = `
    mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
      issueUpdate(id: $id, input: $input) {
        success
        issue { id identifier state { name } }
      }
    }
  `;

  try {
    const result = callLinear(mutation, {
      id: issueId,
      input: { stateId }
    });

    if (result.data?.issueUpdate?.success) {
      return { result: 'updated', issue: result.data.issueUpdate.issue };
    }
    return { result: 'failed', error: result.errors };
  } catch (e) {
    return { result: 'error', error: e.message };
  }
}

/**
 * 追加内容到 Issue description
 */
function appendToIssueDescription(issueId, appendContent) {
  // 先获取当前 description
  const query = `query { issue(id: "${issueId}") { description } }`;
  const current = callLinear(query);
  const currentDesc = current.data?.issue?.description || '';

  const mutation = `
    mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
      issueUpdate(id: $id, input: $input) {
        success
        issue { id identifier }
      }
    }
  `;

  return callLinear(mutation, {
    id: issueId,
    input: { description: currentDesc + '\n\n' + appendContent }
  });
}

/**
 * 生成时间戳标题前缀
 */
function getDatePrefix() {
  const now = new Date();
  return `${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}-${String(now.getHours()).padStart(2, '0')}`;
}

/**
 * 获取上海时间字符串
 */
function getShanghaiTime() {
  return new Date().toLocaleString('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  });
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
    // Superpower 事件（产品生命周期核心）
    case 'superpower_event':
      return handleSuperpowerEvent(event);
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
 * 处理 Superpower 事件 - 产品生命周期状态流转核心
 */
function handleSuperpowerEvent(event) {
  const { skill, phase, action, description, sessionId, cwd } = event;

  // 确定 Team（目前只支持产品事业部）
  const teamId = TEAMS.product;

  // 搜索同 sessionId 的已有 Issue
  const existingIssues = searchIssueBySessionId(teamId, sessionId);

  switch (action) {
    case 'create_or_update_issue':
      // brainstorming 完成 - 创建或更新 Issue
      if (existingIssues.length > 0) {
        // 已有 Issue，追加需求分析结果
        const issue = existingIssues[0];
        appendToIssueDescription(issue.id, `\n## ${getShanghaiTime()} - 需求分析\n${description}`);
        return { result: 'updated', issue: { id: issue.id, identifier: issue.identifier }, action };
      } else {
        // 创建新 Issue
        const title = `【${getDatePrefix()}】${extractProjectFromCwd(cwd)}功能开发`;
        const desc = `sessionId: ${sessionId}\n\n## 阶段: ${phase}\n\n${description}\n\n## 时间线\n- ${getShanghaiTime()}: 需求分析完成`;
        return createIssue(teamId, title, desc);
      }

    case 'update_issue_with_plan':
      // writing-plans 完成 - 追加实施计划
      if (existingIssues.length > 0) {
        const issue = existingIssues[0];
        appendToIssueDescription(issue.id, `\n## ${getShanghaiTime()} - 实施计划\n${description}`);
        return { result: 'plan_added', issue: { id: issue.id, identifier: issue.identifier } };
      }
      return { result: 'skipped', reason: 'No existing issue for plan' };

    case 'set_in_progress':
      // using-git-worktrees - 开发开始
      if (existingIssues.length > 0) {
        const issue = existingIssues[0];
        updateIssueState(issue.id, PRODUCT_STATES.in_progress);
        appendToIssueDescription(issue.id, `\n- ${getShanghaiTime()}: 开发开始`);
        return { result: 'state_changed', state: 'In Progress', issue: { identifier: issue.identifier } };
      }
      return { result: 'skipped', reason: 'No existing issue to update' };

    case 'set_in_review':
      // requesting-code-review - 进入代码审查
      if (existingIssues.length > 0) {
        const issue = existingIssues[0];
        updateIssueState(issue.id, PRODUCT_STATES.in_review);
        appendToIssueDescription(issue.id, `\n- ${getShanghaiTime()}: 代码审查中`);
        return { result: 'state_changed', state: 'In Review', issue: { identifier: issue.identifier } };
      }
      return { result: 'skipped', reason: 'No existing issue to update' };

    case 'log_verification':
      // verification-before-completion - 验证完成，进入待测试/待发布
      if (existingIssues.length > 0) {
        const issue = existingIssues[0];
        // 根据是否有 GUI 决定下一状态（暂时默认进入待发布）
        updateIssueState(issue.id, PRODUCT_STATES.ready_for_release);
        appendToIssueDescription(issue.id, `\n- ${getShanghaiTime()}: 验证通过，待发布`);
        return { result: 'state_changed', state: '待发布', issue: { identifier: issue.identifier } };
      }
      return { result: 'skipped', reason: 'No existing issue to update' };

    case 'set_ready_for_release':
      // finishing-a-development-branch - 分支开发完成
      if (existingIssues.length > 0) {
        const issue = existingIssues[0];
        updateIssueState(issue.id, PRODUCT_STATES.ready_for_release);
        appendToIssueDescription(issue.id, `\n- ${getShanghaiTime()}: 分支开发完成，待发布`);
        return { result: 'state_changed', state: '待发布', issue: { identifier: issue.identifier } };
      }
      return { result: 'skipped', reason: 'No existing issue to update' };

    case 'log_activity':
      // test-driven-development 等 - 仅记录活动
      if (existingIssues.length > 0) {
        const issue = existingIssues[0];
        appendToIssueDescription(issue.id, `\n- ${getShanghaiTime()}: ${description}`);
        return { result: 'logged', issue: { identifier: issue.identifier } };
      }
      return { result: 'skipped', reason: 'No existing issue to log' };

    default:
      return { result: 'ignored', reason: `Unknown action: ${action}` };
  }
}

/**
 * 从 cwd 提取项目名
 */
function extractProjectFromCwd(cwd) {
  if (!cwd) return '未知项目';

  // 匹配 product-bu 下的项目目录
  const match = cwd.match(/product-bu\/([^\/]+)/);
  if (match) return match[1];

  // 匹配已知项目关键词
  for (const [name, config] of Object.entries(PROJECTS.product || {})) {
    if (config.keywords.some(k => cwd.toLowerCase().includes(k.toLowerCase()))) {
      return name;
    }
  }

  return '产品';
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
- **发布时间**: ${getShanghaiTime()}

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
      description,
      labelIds: [CONTENT_LABELS.publish]
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
- **时间**: ${getShanghaiTime()}
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
- **发布时间**: ${getShanghaiTime()}

## 视频链接
⏳ 待回填...
`;

  return createIssue(TEAMS.content, issueTitle, description, { labelIds: [CONTENT_LABELS.publish] });
}

/**
 * 处理 X 发布事件
 */
function handleXPublish(bu, sessionId, data) {
  const issueTitle = `【${getDatePrefix()}】X：${data.content?.substring(0, 30) || '推文'}`;
  const description = `sessionId: ${sessionId}

## 发布信息
- **内容**: ${data.content || '(无)'}
- **发布时间**: ${getShanghaiTime()}

## 推文链接
⏳ 待回填...
`;

  return createIssue(TEAMS.content, issueTitle, description, { labelIds: [CONTENT_LABELS.publish] });
}

/**
 * 处理交易事件
 */
function handleTrade(bu, sessionId, data) {
  const issueTitle = `【${getDatePrefix()}】交易记录`;
  const description = `sessionId: ${sessionId}

## 交易信息
- **时间**: ${getShanghaiTime()}

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
 * @param {string} teamId
 * @param {string} title
 * @param {string} description
 * @param {Object} [options] - 可选参数
 * @param {string[]} [options.labelIds] - Label IDs
 * @param {string} [options.projectId] - Project ID
 */
function createIssue(teamId, title, description, options = {}) {
  const mutation = `
    mutation CreateIssue($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue { id identifier url }
      }
    }
  `;

  const input = { teamId, title, description };
  if (options.labelIds?.length) input.labelIds = options.labelIds;
  if (options.projectId) input.projectId = options.projectId;

  try {
    const result = callLinear(mutation, { input });

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
  handleSuperpowerEvent,
  getLinearApiKey,
  callLinear,
  searchIssueBySessionId,
  updateIssueState,
  createIssue,
  TEAMS,
  INITIATIVES,
  PROJECTS,
  PRODUCT_STATES,
  CONTENT_LABELS,
  ACTION_TO_STATE
};
