#!/usr/bin/env node
/**
 * PMO Session End Hook
 *
 * 触发时机：SessionEnd
 * 职责：启动 PMO Agent 做 session 总结
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const CONFIG = {
  MIN_TRANSCRIPT_LINES: 10,
  WORK_DIR: path.join(process.env.HOME, 'usr/pac/pmo'),
  TEMP_DIR: path.join(process.env.HOME, '.claude/temp')
};

if (!fs.existsSync(CONFIG.TEMP_DIR)) {
  fs.mkdirSync(CONFIG.TEMP_DIR, { recursive: true });
}

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

function extractSummary(transcriptPath, maxLines = 100) {
  if (!fs.existsSync(transcriptPath)) return null;

  const content = fs.readFileSync(transcriptPath, 'utf8');
  const lines = content.trim().split('\n');

  if (lines.length < CONFIG.MIN_TRANSCRIPT_LINES) return null;

  const messages = [];
  for (const line of lines.slice(-maxLines)) {
    try {
      const entry = JSON.parse(line);
      if (entry.type === 'user' && entry.message?.content) {
        messages.push(`User: ${entry.message.content.substring(0, 500)}`);
      } else if (entry.type === 'assistant' && entry.message?.content) {
        const text = Array.isArray(entry.message.content)
          ? entry.message.content.filter(c => c.type === 'text').map(c => c.text).join(' ')
          : entry.message.content;
        if (text) messages.push(`Assistant: ${text.substring(0, 500)}`);
      }
    } catch (e) {}
  }

  return messages.join('\n\n');
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

  // 写入临时文件
  const tempFile = path.join(CONFIG.TEMP_DIR, `pmo-task-${Date.now()}.json`);
  fs.writeFileSync(tempFile, JSON.stringify({
    session_id,
    transcript_path,
    transcript_summary: summary,
    cwd,
    reason,
    timestamp: new Date().toISOString()
  }, null, 2));

  // 启动 PMO Agent
  const prompt = `执行 PMO 任务：分析 session 并上报到 Linear。
Session 数据文件：${tempFile}
按 CLAUDE.md 中的指令执行。`;

  const claude = spawn('claude', ['-p', prompt, '--dangerously-skip-permissions'], {
    cwd: CONFIG.WORK_DIR,
    detached: true,
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env, CLAUDE_SKIP_SESSION_END_HOOK: '1' }
  });

  claude.unref();

  const logFile = path.join(CONFIG.TEMP_DIR, `pmo-log-${Date.now()}.txt`);
  const logStream = fs.createWriteStream(logFile);
  claude.stdout.pipe(logStream);
  claude.stderr.pipe(logStream);

  console.log(JSON.stringify({
    result: 'spawned',
    message: 'PMO Agent started',
    taskFile: tempFile,
    logFile
  }));
}

main().catch(err => {
  console.log(JSON.stringify({ result: 'error', reason: err.message }));
});
