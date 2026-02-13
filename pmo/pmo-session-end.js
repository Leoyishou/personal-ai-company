#!/usr/bin/env node
/**
 * PMO Session End Hook
 *
 * 触发时机：SessionEnd
 * 职责：从 transcript 提取结构化摘要，spawn PMO Agent 创建 Linear Issue
 *
 * 提取策略（分层，用户优先）：
 * 1. 全量扫描用户消息（短，代表意图）
 * 2. 提取工具调用名称（代表做了什么）
 * 3. 只取最后一条 assistant 文本（通常是总结）
 * 4. 提取文件写入路径（代表产出物）
 */

const fs = require('fs');
const { spawn } = require('child_process');

const CONFIG = {
  MIN_TRANSCRIPT_LINES: 10,
  USER_MSG_MAX_CHARS: 500,       // 每条用户消息最大字符
  LAST_ASSISTANT_MAX_CHARS: 1500, // 最后一条 assistant 消息最大字符
  TOTAL_SUMMARY_MAX_CHARS: 4000   // 总摘要上限
};

async function readInput() {
  return new Promise((resolve) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('readable', () => {
      let chunk;
      while ((chunk = process.stdin.read()) !== null) data += chunk;
    });
    process.stdin.on('end', () => {
      try { resolve(JSON.parse(data)); }
      catch (e) { resolve({}); }
    });
  });
}

/**
 * 从 assistant content 中提取 tool_use 名称
 */
function extractToolNames(content) {
  if (!Array.isArray(content)) return [];
  return content
    .filter(c => c.type === 'tool_use')
    .map(c => c.name)
    .filter(Boolean);
}

/**
 * 从 assistant content 中提取文本
 */
function extractAssistantText(content) {
  if (typeof content === 'string') return content;
  if (!Array.isArray(content)) return '';
  return content
    .filter(c => c.type === 'text')
    .map(c => c.text)
    .join(' ');
}

/**
 * 从 tool_use 参数中提取文件路径
 */
function extractFilePaths(content) {
  if (!Array.isArray(content)) return [];
  const paths = [];
  for (const block of content) {
    if (block.type !== 'tool_use') continue;
    const input = block.input || {};
    // Write/Edit tool 的 file_path
    if (input.file_path) paths.push(input.file_path);
    // Bash 中的输出路径（简单匹配）
    if (input.command && />\s*\S+/.test(input.command)) {
      const match = input.command.match(/>\s*(\S+)/);
      if (match) paths.push(match[1]);
    }
  }
  return paths;
}

/**
 * 分层提取 session 摘要
 *
 * 层级：
 * 1. ALL 用户消息（意图层）
 * 2. ALL 工具调用名称（行为层）
 * 3. 最后一条 assistant 文本消息（结果层）
 * 4. 文件写入路径（产出层）
 */
function extractStructuredSummary(transcriptPath) {
  if (!fs.existsSync(transcriptPath)) return null;

  const content = fs.readFileSync(transcriptPath, 'utf8');
  const lines = content.trim().split('\n');

  if (lines.length < CONFIG.MIN_TRANSCRIPT_LINES) return null;

  const userMessages = [];
  const toolNames = new Set();
  const filePaths = new Set();
  let lastAssistantText = '';
  let totalTurns = 0;

  for (const line of lines) {
    let entry;
    try { entry = JSON.parse(line); } catch (e) { continue; }

    if (entry.type === 'user' && entry.message?.content) {
      totalTurns++;
      const text = typeof entry.message.content === 'string'
        ? entry.message.content
        : JSON.stringify(entry.message.content);
      userMessages.push(text.substring(0, CONFIG.USER_MSG_MAX_CHARS));
    }

    if (entry.type === 'assistant' && entry.message?.content) {
      // 工具调用名称（累积全量）
      for (const name of extractToolNames(entry.message.content)) {
        toolNames.add(name);
      }
      // 文件路径（累积全量）
      for (const p of extractFilePaths(entry.message.content)) {
        filePaths.add(p);
      }
      // 文本（只保留最后一条）
      const text = extractAssistantText(entry.message.content);
      if (text.trim()) {
        lastAssistantText = text;
      }
    }
  }

  if (userMessages.length === 0) return null;

  // 组装结构化摘要
  const sections = [];

  sections.push(`## 用户消息（${userMessages.length} 条，共 ${totalTurns} 轮）`);
  sections.push(userMessages.map((m, i) => `${i + 1}. ${m}`).join('\n'));

  if (toolNames.size > 0) {
    sections.push(`## 使用的工具（${toolNames.size} 种）`);
    sections.push([...toolNames].join(', '));
  }

  if (filePaths.size > 0) {
    sections.push(`## 文件产出（${filePaths.size} 个）`);
    sections.push([...filePaths].slice(0, 20).join('\n'));
  }

  if (lastAssistantText) {
    sections.push('## AI 最后回复（通常是总结）');
    sections.push(lastAssistantText.substring(0, CONFIG.LAST_ASSISTANT_MAX_CHARS));
  }

  const summary = sections.join('\n\n');
  return summary.substring(0, CONFIG.TOTAL_SUMMARY_MAX_CHARS);
}

function detectBu(cwd) {
  if (!cwd) return 'unknown';
  if (cwd.includes('product-bu')) return 'product';
  if (cwd.includes('content-bu')) return 'content';
  if (cwd.includes('investment-bu')) return 'investment';
  if (cwd.includes('research-bu')) return 'research';
  if (cwd.includes('pmo')) return 'pmo';
  return 'unknown';
}

/**
 * 触发 PMO Agent 后台分析 session
 * 移除 ANTHROPIC_API_KEY，使用 Pro 订阅认证
 */
function spawnPmoAgent(eventData) {
  const { ANTHROPIC_API_KEY, ...cleanEnv } = process.env;

  const prompt = `处理 session_end 事件，根据 CLAUDE.md 规则判断是否需要创建 Linear Issue：

事件数据：
${JSON.stringify(eventData, null, 2)}

请：
1. 分析结构化摘要（用户消息=意图，工具=行为，最后回复=结果，文件=产出）
2. 判断是否值得创建 Issue（纯聊天/咨询不需要，有实际产出的才需要）
3. 如果值得，根据 BU 规则确定 Team、Project、Labels
4. 调用 /api-linear skill 创建 Issue
5. 如果有详细产出，用 doc-create 创建 Document 关联到 Issue`;

  try {
    const child = spawn('claude', [
      '--dangerously-skip-permissions',
      '--print',
      '-p', prompt
    ], {
      cwd: '/Users/liuyishou/usr/pac/pmo',
      detached: true,
      stdio: 'ignore',
      env: cleanEnv
    });

    child.unref();
    return true;
  } catch (err) {
    return false;
  }
}

async function main() {
  const input = await readInput();
  const { session_id, transcript_path, cwd, reason } = input;

  if (!transcript_path || !fs.existsSync(transcript_path)) {
    console.log(JSON.stringify({ result: 'skipped', reason: 'No transcript' }));
    return;
  }

  const summary = extractStructuredSummary(transcript_path);
  if (!summary) {
    console.log(JSON.stringify({ result: 'skipped', reason: 'Transcript too short or empty' }));
    return;
  }

  const bu = detectBu(cwd);

  const agentSpawned = spawnPmoAgent({
    type: 'session_end',
    bu,
    sessionId: session_id,
    data: {
      summary,
      cwd,
      transcript_path,
      reason
    }
  });

  console.log(JSON.stringify({
    result: agentSpawned ? 'agent_spawned' : 'spawn_failed',
    session_id,
    bu
  }));
}

main().catch(err => {
  console.log(JSON.stringify({ result: 'error', reason: err.message }));
});
