#!/usr/bin/env node
/**
 * PMO Session End Hook
 *
 * 触发时机：SessionEnd
 * 职责：spawn PMO Agent 后台分析 session 并创建 Linear Issue
 *
 * PMO Agent 使用 Pro 订阅认证（移除 ANTHROPIC_API_KEY）
 */

const fs = require('fs');
const { spawn } = require('child_process');

const CONFIG = {
  MIN_TRANSCRIPT_LINES: 10
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

function extractSummary(transcriptPath, maxLines = 50) {
  if (!fs.existsSync(transcriptPath)) return null;

  const content = fs.readFileSync(transcriptPath, 'utf8');
  const lines = content.trim().split('\n');

  if (lines.length < CONFIG.MIN_TRANSCRIPT_LINES) return null;

  const messages = [];
  for (const line of lines.slice(-maxLines)) {
    try {
      const entry = JSON.parse(line);
      if (entry.type === 'user' && entry.message?.content) {
        messages.push(`User: ${entry.message.content.substring(0, 300)}`);
      } else if (entry.type === 'assistant' && entry.message?.content) {
        const text = Array.isArray(entry.message.content)
          ? entry.message.content.filter(c => c.type === 'text').map(c => c.text).join(' ')
          : entry.message.content;
        if (text) messages.push(`Assistant: ${text.substring(0, 300)}`);
      }
    } catch (e) {}
  }

  return messages.slice(0, 20).join('\n\n');
}

function detectBu(cwd) {
  if (!cwd) return 'unknown';
  if (cwd.includes('product-bu')) return 'product';
  if (cwd.includes('content-bu')) return 'content';
  if (cwd.includes('investment-bu')) return 'investment';
  if (cwd.includes('pmo')) return 'pmo';
  return 'unknown';
}

/**
 * 触发 PMO Agent 后台分析 session
 * 移除 ANTHROPIC_API_KEY，使用 Pro 订阅认证
 */
function spawnPmoAgent(eventData) {
  // 移除 ANTHROPIC_API_KEY，让 claude 使用 Pro 订阅认证
  const { ANTHROPIC_API_KEY, ...cleanEnv } = process.env;

  const prompt = `处理 session_end 事件，根据 CLAUDE.md 规则判断是否需要创建 Linear Issue：

事件数据：
${JSON.stringify(eventData, null, 2)}

请：
1. 分析 session 摘要，判断是否值得创建 Issue
2. 如果值得，根据 cwd 判断归属事业部
3. 调用 Linear API 创建或更新 Issue
4. 返回处理结果`;

  try {
    const child = spawn('claude', [
      '--dangerously-skip-permissions',
      '--print',
      '-p', prompt
    ], {
      cwd: '/Users/liuyishou/usr/pac/pmo',
      detached: true,
      stdio: 'ignore',
      env: cleanEnv  // 使用 Pro 订阅，不传 API key
    });

    child.unref();
    return true;
  } catch (err) {
    // spawn 失败静默处理
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

  const summary = extractSummary(transcript_path);
  if (!summary) {
    console.log(JSON.stringify({ result: 'skipped', reason: 'Transcript too short' }));
    return;
  }

  const bu = detectBu(cwd);

  // 直接 spawn PMO Agent 分析
  const agentSpawned = spawnPmoAgent({
    type: 'session_end',
    bu,
    sessionId: session_id,
    data: {
      summary: summary.substring(0, 2000),
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
