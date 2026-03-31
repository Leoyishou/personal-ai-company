#!/usr/bin/env node
/**
 * 小红书发布追踪 Hook
 *
 * 触发时机：PostToolUse (Bash)
 * 作用：
 * 1. 检测小红书发布成功
 * 2. 创建 Linear issue（内容事业部）
 * 3. 3分钟后自动查询笔记链接并回填
 */

const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

// 从 stdin 读取 hook 输入
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
  const { tool_name, tool_input, tool_output, session_id } = hookData;

  // 只处理 Bash 工具
  if (tool_name !== 'Bash') return;

  // 检测是否是小红书发布命令
  const command = tool_input?.command || '';
  if (!command.includes('xhs_publish.py') || !command.includes('publish')) return;

  // 检测发布成功
  const output = tool_output || '';
  if (!output.includes('发布完成') && !output.includes('发布成功')) return;

  // 提取标题
  const titleMatch = command.match(/--title\s+"([^"]+)"/);
  const title = titleMatch ? titleMatch[1] : '未知标题';

  // 提取标签
  const tagsMatch = command.match(/--tags\s+"([^"]+)"/);
  const tags = tagsMatch ? tagsMatch[1].split(',') : [];

  // 创建 Linear issue 并启动延时任务
  createIssueAndScheduleUpdate(title, tags, session_id);
}

function createIssueAndScheduleUpdate(title, tags, sessionId) {
  // 内容事业部 Team ID
  const CONTENT_TEAM_ID = '4bb065b8-982f-4a44-830d-8d88fe8c9828';

  // 从环境或 secrets 读取 Linear API key
  const secretsPath = path.join(process.env.HOME, '.claude/secrets.env');
  let linearApiKey = process.env.LINEAR_API_KEY;

  if (!linearApiKey && fs.existsSync(secretsPath)) {
    const secrets = fs.readFileSync(secretsPath, 'utf8');
    const match = secrets.match(/LINEAR_API_KEY=["']?([^"'\n]+)["']?/);
    if (match) linearApiKey = match[1];
  }

  if (!linearApiKey) {
    console.error('LINEAR_API_KEY not found');
    return;
  }

  const now = new Date();
  const dateStr = `${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}-${String(now.getHours()).padStart(2, '0')}`;

  const issueTitle = `【${dateStr}】小红书：${title}`;
  const issueDesc = `sessionId: ${sessionId || 'unknown'}

## 发布信息
- **标题**: ${title}
- **标签**: ${tags.join(', ')}
- **发布时间**: ${now.toISOString()}

## 笔记链接
⏳ 3分钟后自动回填...

## 数据追踪
| 时间 | 点赞 | 收藏 | 评论 |
|------|------|------|------|
| 发布时 | - | - | - |
`;

  // 创建 Linear issue
  const mutation = `
    mutation CreateIssue($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue {
          id
          identifier
          url
        }
      }
    }
  `;

  const variables = {
    input: {
      teamId: CONTENT_TEAM_ID,
      title: issueTitle,
      description: issueDesc,
      labelIds: ['b4fa7209-3d42-4cdb-98c0-ee2742dd647a']  // 发布
    }
  };

  try {
    const response = execSync(`curl -s -X POST https://api.linear.app/graphql \
      -H "Content-Type: application/json" \
      -H "Authorization: ${linearApiKey}" \
      -d '${JSON.stringify({ query: mutation, variables }).replace(/'/g, "'\\''")}'`,
      { encoding: 'utf8', timeout: 10000 }
    );

    const result = JSON.parse(response);
    if (result.data?.issueCreate?.success) {
      const issueId = result.data.issueCreate.issue.id;
      const issueUrl = result.data.issueCreate.issue.url;
      const identifier = result.data.issueCreate.issue.identifier;

      console.log(`✅ Linear issue created: ${identifier}`);

      // 启动后台任务，3分钟后更新
      scheduleUpdate(issueId, title, linearApiKey);

      // 注册 3d/7d 延迟回填任务
      scheduleBackfillTasks(issueId, identifier, title);
    }
  } catch (e) {
    console.error('Failed to create Linear issue:', e.message);
  }
}

function scheduleUpdate(issueId, noteTitle, linearApiKey) {
  // 创建延时更新脚本
  const updateScript = `
#!/bin/bash
sleep 180  # 等待3分钟

# 搜索笔记获取链接
SEARCH_RESULT=$(python3 -c "
import json
import subprocess
import sys

# 调用 MCP 搜索笔记
# 这里使用简化的方式：直接用 curl 调用本地 MCP
import urllib.request
import urllib.parse

try:
    # 搜索小红书
    req = urllib.request.Request(
        'http://localhost:18060/mcp',
        data=json.dumps({
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'tools/call',
            'params': {
                'name': 'search_feeds',
                'arguments': {
                    'keyword': '''${noteTitle}''',
                    'filters': {'sort_by': '最新', 'publish_time': '一天内'}
                }
            }
        }).encode(),
        headers={'Content-Type': 'application/json'}
    )
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())

    # 提取第一条匹配的笔记
    feeds = result.get('result', {}).get('feeds', [])
    for feed in feeds:
        if feed.get('noteCard', {}).get('user', {}).get('nickname') == '转了码的刘公子':
            note_id = feed.get('id')
            note_url = f'https://www.xiaohongshu.com/explore/{note_id}'
            interact = feed.get('noteCard', {}).get('interactInfo', {})
            likes = interact.get('likedCount', '0')
            collects = interact.get('collectedCount', '0')
            comments = interact.get('commentCount', '0')
            print(json.dumps({
                'url': note_url,
                'likes': likes,
                'collects': collects,
                'comments': comments
            }))
            sys.exit(0)

    print('{}')
except Exception as e:
    print('{}')
" 2>/dev/null)

# 如果搜索成功，更新 Linear issue
if [ -n "$SEARCH_RESULT" ] && [ "$SEARCH_RESULT" != "{}" ]; then
    NOTE_URL=$(echo "$SEARCH_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('url',''))")
    LIKES=$(echo "$SEARCH_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('likes','0'))")
    COLLECTS=$(echo "$SEARCH_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('collects','0'))")
    COMMENTS=$(echo "$SEARCH_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('comments','0'))")

    if [ -n "$NOTE_URL" ]; then
        # 更新 Linear issue
        curl -s -X POST https://api.linear.app/graphql \\
          -H "Content-Type: application/json" \\
          -H "Authorization: ${linearApiKey}" \\
          -d '{
            "query": "mutation { issueUpdate(id: \\"${issueId}\\", input: { description: \\"## 笔记链接\\n✅ '"$NOTE_URL"'\\n\\n## 数据追踪\\n| 时间 | 点赞 | 收藏 | 评论 |\\n|------|------|------|------|\\n| 3分钟后 | '"$LIKES"' | '"$COLLECTS"' | '"$COMMENTS"' |\\" }) { success } }"
          }' > /dev/null

        echo "✅ Updated Linear issue with note URL: $NOTE_URL"
    fi
fi
`;

  // 将脚本写入临时文件并后台执行
  const tmpScript = `/tmp/xhs-update-${Date.now()}.sh`;
  fs.writeFileSync(tmpScript, updateScript, { mode: 0o755 });

  // 后台执行，不阻塞主进程
  spawn('bash', [tmpScript], {
    detached: true,
    stdio: 'ignore'
  }).unref();
}

function scheduleBackfillTasks(issueId, identifier, noteTitle) {
  const schedulerPath = path.join(process.env.HOME, 'usr/pac/infrastructure/scheduler/scheduler.js');
  if (!fs.existsSync(schedulerPath)) return;

  const payload = JSON.stringify({
    issue_id: issueId,
    issue_identifier: identifier,
    note_title: noteTitle,
    platform: 'xiaohongshu',
  });

  // Schedule 3-day backfill
  try {
    const { execSync: exec } = require('child_process');
    exec(`node "${schedulerPath}" add --type content_backfill --delay 3d --payload '${payload.replace(/'/g, "'\\''")}' --description "${identifier} 3日数据回填"`, { timeout: 5000 });
  } catch {}

  // Schedule 7-day backfill
  try {
    const payloadWith7d = JSON.stringify({ ...JSON.parse(payload), backfill_label: '7日后' });
    const { execSync: exec } = require('child_process');
    exec(`node "${schedulerPath}" add --type content_backfill --delay 7d --payload '${payloadWith7d.replace(/'/g, "'\\''")}' --description "${identifier} 7日数据回填"`, { timeout: 5000 });
  } catch {}
}
