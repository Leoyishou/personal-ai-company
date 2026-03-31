#!/usr/bin/env node
/**
 * Subagent Tracker Hook
 * 追踪 subagent 的启动和停止，记录调用日志
 */

const fs = require('fs');
const path = require('path');

const LOG_FILE = path.join(process.env.HOME, '.claude', 'logs', 'subagent-usage.jsonl');
const action = process.argv[2]; // 'start' or 'stop'

// 确保日志目录存在
const logDir = path.dirname(LOG_FILE);
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}

// 从 stdin 读取 hook 输入
let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('readable', () => {
  let chunk;
  while ((chunk = process.stdin.read()) !== null) {
    input += chunk;
  }
});

process.stdin.on('end', () => {
  try {
    const hookData = JSON.parse(input);

    const logEntry = {
      timestamp: new Date().toISOString(),
      action: action,
      session_id: hookData.session_id,
      subagent_type: hookData.tool_input?.subagent_type || hookData.subagent_type,
      description: hookData.tool_input?.description || hookData.description,
    };

    // 追加到日志文件
    fs.appendFileSync(LOG_FILE, JSON.stringify(logEntry) + '\n');

    // 输出成功
    console.log(JSON.stringify({ continue: true }));
  } catch (err) {
    // 解析失败时静默继续
    console.log(JSON.stringify({ continue: true }));
  }
});
