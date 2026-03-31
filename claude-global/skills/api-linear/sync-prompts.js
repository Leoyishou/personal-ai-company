#!/usr/bin/env node
/**
 * 同步 api-draw prompt 模板到 Linear Documents
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const TEMPLATES_DIR = path.join(process.env.HOME, '.claude/skills/api-draw/templates');
const CONTENT_PROJECT_ID = null; // 不关联特定项目，放在内容事业部 Team 下

// Team IDs
const TEAMS = {
  content: '4bb065b8-982f-4a44-830d-8d88fe8c9828'
};

function getApiKey() {
  const secretsPath = path.join(process.env.HOME, '.claude/secrets.env');
  const secrets = fs.readFileSync(secretsPath, 'utf8');
  const match = secrets.match(/LINEAR_API_KEY=["']?([^"'\n]+)["']?/);
  return match ? match[1] : null;
}

function callLinear(query, variables = {}) {
  const apiKey = getApiKey();
  const payloadFile = `/tmp/linear-sync-${Date.now()}.json`;
  fs.writeFileSync(payloadFile, JSON.stringify({ query, variables }));

  try {
    const response = execSync(`curl -s -X POST https://api.linear.app/graphql \
      -H "Content-Type: application/json" \
      -H "Authorization: ${apiKey}" \
      -d @${payloadFile}`,
      { encoding: 'utf8', timeout: 30000 }
    );
    return JSON.parse(response);
  } finally {
    try { fs.unlinkSync(payloadFile); } catch (e) {}
  }
}

// 查询已有的 Documents
function getExistingDocuments() {
  const query = `
    query {
      documents(first: 50) {
        nodes { id title }
      }
    }
  `;
  const result = callLinear(query);
  return result.data?.documents?.nodes || [];
}

// 创建 Document（必须指定 teamId）
function createDocument(title, content) {
  const mutation = `
    mutation CreateDocument($input: DocumentCreateInput!) {
      documentCreate(input: $input) {
        success
        document { id title url }
      }
    }
  `;

  const result = callLinear(mutation, {
    input: {
      title: `[Prompt] ${title}`,
      content: content,
      teamId: TEAMS.content  // 放在内容事业部下
    }
  });

  if (result.errors) {
    console.error('Error:', JSON.stringify(result.errors, null, 2));
  }

  return result.data?.documentCreate;
}

// 更新 Document
function updateDocument(id, content) {
  const mutation = `
    mutation UpdateDocument($id: String!, $input: DocumentUpdateInput!) {
      documentUpdate(id: $id, input: $input) {
        success
        document { id title }
      }
    }
  `;

  return callLinear(mutation, { id, input: { content } });
}

// Main
async function main() {
  console.log('Syncing prompt templates to Linear Documents...\n');

  // 获取已有 Documents
  const existing = getExistingDocuments();
  const existingMap = {};
  existing.forEach(doc => {
    existingMap[doc.title] = doc.id;
  });

  // 读取所有模板
  const templates = fs.readdirSync(TEMPLATES_DIR)
    .filter(f => f.endsWith('.md'));

  console.log(`Found ${templates.length} templates\n`);

  const results = [];

  for (const file of templates) {
    const name = path.basename(file, '.md');
    const title = `[Prompt] ${name}`;
    const content = fs.readFileSync(path.join(TEMPLATES_DIR, file), 'utf8');

    if (existingMap[title]) {
      // 更新已有
      console.log(`Updating: ${name}`);
      const result = updateDocument(existingMap[title], content);
      results.push({ name, action: 'updated', id: existingMap[title] });
    } else {
      // 创建新的
      console.log(`Creating: ${name}`);
      const result = createDocument(name, content);
      if (result?.success) {
        results.push({
          name,
          action: 'created',
          id: result.document.id,
          url: result.document.url
        });
      } else {
        results.push({ name, action: 'failed' });
      }
    }
  }

  console.log('\n=== Results ===');
  console.log(JSON.stringify(results, null, 2));

  // 输出 Document ID 映射（供后续使用）
  console.log('\n=== Document ID Map ===');
  const allDocs = getExistingDocuments();
  const promptDocs = allDocs.filter(d => d.title.startsWith('[Prompt]'));
  const map = {};
  promptDocs.forEach(d => {
    const name = d.title.replace('[Prompt] ', '');
    map[name] = d.id;
  });
  console.log(JSON.stringify(map, null, 2));
}

main().catch(console.error);
