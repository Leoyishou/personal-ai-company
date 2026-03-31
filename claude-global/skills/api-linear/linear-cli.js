#!/usr/bin/env node
/**
 * Linear CLI - 命令行操作 Linear
 *
 * 通过文件传递 payload 避免 shell 转义问题，正确处理 markdown 换行
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Team IDs
const TEAMS = {
  product: 'fcaf8084-612e-43e2-b4e4-fe81ae523627',
  content: '4bb065b8-982f-4a44-830d-8d88fe8c9828',
  investment: '47b059ce-ce0b-4965-bad8-80481f71ecc9',
  research: '0851ce16-e2d0-411f-adfe-aacc26cdab7b',
  pmo: '1e658f17-2cdf-4bdd-82ad-c63e8a7c4ebb'
};

// 状态 IDs（产品事业部）
const STATES = {
  backlog: '52220171-86ac-4a6a-83af-24ec12d55f51',
  todo: 'd430a64c-e7c1-465b-a086-7fb8397941e1',
  in_progress: '53054e6e-1ca5-4b0d-b5c2-283ff2841ab4',
  in_review: 'd8125aeb-6451-4da7-971c-b24581025d2a',
  ready_for_qa: 'db66771b-185b-464e-beb1-dd11d54f44f9',
  ready_for_release: '177fe624-d3a6-4378-b3a3-b5b7a4246a7a',
  done: '05f950b5-1121-44e2-b60c-cdf923df4b28'
};

// 内容事业部 Labels
const CONTENT_LABELS = {
  '灵感': '7be8f7f1-b476-4c27-87e4-e4b36fc2e6cb',
  '做图': '5a95aaa6-ce9a-4871-81ef-1dcce2bbc3e7',
  '文案': 'be0f8c2e-7054-490f-84c1-f95212c07ef2',
  '发布': 'b4fa7209-3d42-4cdb-98c0-ee2742dd647a',
  '后评估': '072feefc-4d30-4522-af7d-ba6448ec960f'
};

// Prompt 模板 Document IDs（同步自 api-draw/templates）
const DOCUMENTS = {
  '手绘白板': 'd18b14b0-f198-411e-ba44-976f4774f8fa',
  '人物语录': 'd72daffd-745c-4055-981f-10f150bccd71',
  '学霸笔记': 'ea058ae8-3746-47d7-b835-fa1aa074d7ad',
  '思维导图': '57ac86f7-f1fa-4cfc-afb9-72acd6ad80c9',
  '技术对比': '8cf51bb2-1f47-4d31-95b1-4b1f15f18b9c',
  '信息图表': '50d8f8ef-e5e9-4e5d-a69b-ffca2f5f1b77',
  '时间线': '19e09dde-cbb5-4afc-aa02-21e3d6f92dc1',
  '知识卡片': '91e06e53-02ff-4ce3-834e-4d0a5f8ca8d5',
  '对话框': '19e9fced-f2b7-45b1-a6c1-2116a39e1a8f',
  '数据可视化': '86b85f57-3ecb-40a7-9e02-61f340fc5bb1',
  '代码展示': '86dda2a3-2d1b-476d-aa54-8da10fc07e1b',
  '金句': 'cb50b1d9-a10b-41dd-a1ae-59c2a4cff9b9'
};

/**
 * 获取 API Key
 */
function getApiKey() {
  const secretsPath = path.join(process.env.HOME, '.claude/secrets.env');
  let key = process.env.LINEAR_API_KEY;

  if (!key && fs.existsSync(secretsPath)) {
    const secrets = fs.readFileSync(secretsPath, 'utf8');
    const match = secrets.match(/LINEAR_API_KEY=["']?([^"'\n]+)["']?/);
    if (match) key = match[1];
  }

  if (!key) {
    console.error('ERROR: LINEAR_API_KEY not found');
    process.exit(1);
  }

  return key;
}

/**
 * 调用 Linear GraphQL API
 */
function callLinear(query, variables = {}) {
  const apiKey = getApiKey();

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
 * 创建 Issue
 */
function createIssue(options) {
  const { team, title, description, project, labels } = options;

  const teamId = TEAMS[team];
  if (!teamId) {
    console.error(`ERROR: Unknown team: ${team}`);
    process.exit(1);
  }

  const mutation = `
    mutation CreateIssue($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue { id identifier url title }
      }
    }
  `;

  const input = { teamId, title, description };
  if (project) input.projectId = project;
  if (labels) {
    // labels 可以是逗号分隔的 ID 列表
    input.labelIds = labels.split(',').map(id => id.trim());
  }

  const result = callLinear(mutation, { input });

  if (result.data?.issueCreate?.success) {
    const issue = result.data.issueCreate.issue;
    console.log(JSON.stringify({
      success: true,
      issue: {
        id: issue.id,
        identifier: issue.identifier,
        url: issue.url,
        title: issue.title
      }
    }, null, 2));
  } else {
    console.error(JSON.stringify({ success: false, errors: result.errors }, null, 2));
    process.exit(1);
  }
}

/**
 * 更新 Issue
 */
function updateIssue(options) {
  const { id, state, append } = options;

  // 如果是 identifier (如 P-123)，先查询获取 id
  let issueId = id;
  if (id.match(/^[A-Z]+-\d+$/)) {
    const query = `query { issue(id: "${id}") { id } }`;
    const result = callLinear(query);
    if (!result.data?.issue?.id) {
      console.error(`ERROR: Issue not found: ${id}`);
      process.exit(1);
    }
    issueId = result.data.issue.id;
  }

  const input = {};

  // 更新状态
  if (state) {
    const stateId = STATES[state];
    if (!stateId) {
      console.error(`ERROR: Unknown state: ${state}`);
      process.exit(1);
    }
    input.stateId = stateId;
  }

  // 追加内容
  if (append) {
    // 先获取当前 description
    const query = `query { issue(id: "${issueId}") { description } }`;
    const current = callLinear(query);
    const currentDesc = current.data?.issue?.description || '';
    input.description = currentDesc + '\n\n' + append;
  }

  if (Object.keys(input).length === 0) {
    console.error('ERROR: Nothing to update');
    process.exit(1);
  }

  const mutation = `
    mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
      issueUpdate(id: $id, input: $input) {
        success
        issue { id identifier state { name } }
      }
    }
  `;

  const result = callLinear(mutation, { id: issueId, input });

  if (result.data?.issueUpdate?.success) {
    console.log(JSON.stringify({
      success: true,
      issue: result.data.issueUpdate.issue
    }, null, 2));
  } else {
    console.error(JSON.stringify({ success: false, errors: result.errors }, null, 2));
    process.exit(1);
  }
}

/**
 * 解析 Issue identifier 为 UUID
 */
function resolveIssueId(identifier) {
  if (!identifier.match(/^[A-Z]+-\d+$/)) return identifier;
  const query = `query { issue(id: "${identifier}") { id } }`;
  const result = callLinear(query);
  if (!result.data?.issue?.id) {
    console.error(`ERROR: Issue not found: ${identifier}`);
    process.exit(1);
  }
  return result.data.issue.id;
}

/**
 * 创建 Document 并关联到 Issue/Project
 */
function docCreate(options) {
  const { title, content, 'content-file': contentFile, issue, project, team } = options;

  if (!title) {
    console.error('ERROR: --title is required');
    process.exit(1);
  }

  // 读取内容：--content 或 --content-file
  let docContent = content || '';
  if (contentFile) {
    if (!fs.existsSync(contentFile)) {
      console.error(`ERROR: File not found: ${contentFile}`);
      process.exit(1);
    }
    docContent = fs.readFileSync(contentFile, 'utf8');
  }

  const mutation = `
    mutation DocumentCreate($input: DocumentCreateInput!) {
      documentCreate(input: $input) {
        success
        document { id title url slugId }
      }
    }
  `;

  const input = { title, content: docContent };

  // 关联到 Issue
  if (issue) {
    const issueId = resolveIssueId(issue);
    input.issueId = issueId;
  }

  // 关联到 Project
  if (project) {
    input.projectId = project;
  }

  const result = callLinear(mutation, { input });

  if (result.data?.documentCreate?.success) {
    const doc = result.data.documentCreate.document;
    console.log(JSON.stringify({
      success: true,
      document: {
        id: doc.id,
        title: doc.title,
        url: doc.url,
        slugId: doc.slugId
      }
    }, null, 2));
  } else {
    console.error(JSON.stringify({ success: false, errors: result.errors }, null, 2));
    process.exit(1);
  }
}

/**
 * 更新已有 Document
 */
function docUpdate(options) {
  const { id, title, content, 'content-file': contentFile, append } = options;

  if (!id) {
    console.error('ERROR: --id is required');
    process.exit(1);
  }

  const input = {};

  if (title) input.title = title;

  // 完整替换内容
  if (content) {
    input.content = content;
  } else if (contentFile) {
    if (!fs.existsSync(contentFile)) {
      console.error(`ERROR: File not found: ${contentFile}`);
      process.exit(1);
    }
    input.content = fs.readFileSync(contentFile, 'utf8');
  }

  // 追加内容
  if (append) {
    const query = `query { document(id: "${id}") { content } }`;
    const current = callLinear(query);
    const currentContent = current.data?.document?.content || '';
    input.content = currentContent + '\n\n' + append;
  }

  if (Object.keys(input).length === 0) {
    console.error('ERROR: Nothing to update. Use --content, --content-file, --append, or --title');
    process.exit(1);
  }

  const mutation = `
    mutation DocumentUpdate($id: String!, $input: DocumentUpdateInput!) {
      documentUpdate(id: $id, input: $input) {
        success
        document { id title url }
      }
    }
  `;

  const result = callLinear(mutation, { id, input });

  if (result.data?.documentUpdate?.success) {
    const doc = result.data.documentUpdate.document;
    console.log(JSON.stringify({
      success: true,
      document: {
        id: doc.id,
        title: doc.title,
        url: doc.url
      }
    }, null, 2));
  } else {
    console.error(JSON.stringify({ success: false, errors: result.errors }, null, 2));
    process.exit(1);
  }
}

/**
 * 链接 Document 到 Issue
 */
function linkDoc(options) {
  const { id, document, prompt } = options;

  // 获取 Document ID
  let documentId = document;
  if (prompt) {
    // 按 prompt 模板名称查找
    documentId = DOCUMENTS[prompt];
    if (!documentId) {
      console.error(`ERROR: Unknown prompt template: ${prompt}`);
      console.error('Available templates:', Object.keys(DOCUMENTS).join(', '));
      process.exit(1);
    }
  }

  if (!documentId) {
    console.error('ERROR: --document or --prompt required');
    process.exit(1);
  }

  // 获取 Issue ID
  let issueId = id;
  if (id.match(/^[A-Z]+-\d+$/)) {
    const query = `query { issue(id: "${id}") { id } }`;
    const result = callLinear(query);
    if (!result.data?.issue?.id) {
      console.error(`ERROR: Issue not found: ${id}`);
      process.exit(1);
    }
    issueId = result.data.issue.id;
  }

  // 先获取 Document 的 title 和 url
  const docQuery = `query { document(id: "${documentId}") { title url } }`;
  const docResult = callLinear(docQuery);
  if (!docResult.data?.document) {
    console.error(`ERROR: Document not found: ${documentId}`);
    process.exit(1);
  }
  const { title, url } = docResult.data.document;

  // 使用 attachmentCreate 创建链接（需要 title 和 url）
  const mutation = `
    mutation CreateAttachment($input: AttachmentCreateInput!) {
      attachmentCreate(input: $input) {
        success
        attachment { id title url }
      }
    }
  `;

  const result = callLinear(mutation, {
    input: {
      issueId,
      title,
      url
    }
  });

  if (result.data?.attachmentCreate?.success) {
    console.log(JSON.stringify({
      success: true,
      message: `Document "${title}" linked to issue ${id}`,
      attachment: result.data.attachmentCreate.attachment
    }, null, 2));
  } else {
    console.error(JSON.stringify({ success: false, errors: result.errors }, null, 2));
    process.exit(1);
  }
}

/**
 * 搜索 Issue
 */
function searchIssue(options) {
  const { team, query: searchQuery, session } = options;

  let filter = {};

  if (session) {
    filter = { description: { contains: `sessionId: ${session}` } };
  } else if (searchQuery) {
    filter = { or: [
      { title: { contains: searchQuery } },
      { description: { contains: searchQuery } }
    ]};
  }

  let teamFilter = '';
  if (team) {
    const teamId = TEAMS[team];
    if (teamId) {
      teamFilter = `, team: { id: { eq: "${teamId}" } }`;
    }
  }

  const query = `
    query SearchIssues($filter: IssueFilter) {
      issues(filter: $filter, first: 10) {
        nodes {
          id
          identifier
          title
          state { name }
          project { name }
          createdAt
        }
      }
    }
  `;

  const result = callLinear(query, { filter });

  if (result.data?.issues?.nodes) {
    console.log(JSON.stringify({
      success: true,
      count: result.data.issues.nodes.length,
      issues: result.data.issues.nodes
    }, null, 2));
  } else {
    console.error(JSON.stringify({ success: false, errors: result.errors }, null, 2));
  }
}

/**
 * 解析命令行参数
 */
function parseArgs(args) {
  const options = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--')) {
      const key = args[i].slice(2);
      const value = args[i + 1] && !args[i + 1].startsWith('--') ? args[++i] : true;
      options[key] = value;
    }
  }
  return options;
}

// Main
const args = process.argv.slice(2);
const action = args[0];
const options = parseArgs(args.slice(1));

switch (action) {
  case 'create':
    createIssue(options);
    break;
  case 'update':
    updateIssue(options);
    break;
  case 'search':
    searchIssue(options);
    break;
  case 'link-doc':
    linkDoc(options);
    break;
  case 'doc-create':
    docCreate(options);
    break;
  case 'doc-update':
    docUpdate(options);
    break;
  case 'list-prompts':
    console.log(JSON.stringify({ prompts: Object.keys(DOCUMENTS) }, null, 2));
    break;
  default:
    console.log(`Usage: linear-cli.js <action> [options]

Actions:
  create      --team <team> --title "title" --description "desc" [--project <id>] [--labels <id,id>]
  update      --id <id> [--state <state>] [--append "content"]
  search      [--team <team>] [--query "keyword"] [--session <sessionId>]
  link-doc    --id <issue-id> --prompt <模板名> 或 --document <doc-id>
  doc-create  --title "标题" [--content "内容"] [--content-file <path>] [--issue <id>] [--project <id>]
  doc-update  --id <doc-id> [--content "内容"] [--content-file <path>] [--append "追加"] [--title "新标题"]
  list-prompts  列出所有可用的 prompt 模板

Teams: product, content, investment, research, pmo
States: backlog, todo, in_progress, in_review, ready_for_qa, ready_for_release, done
Prompts: ${Object.keys(DOCUMENTS).join(', ')}`);
}
