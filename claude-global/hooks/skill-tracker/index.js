#!/usr/bin/env node
/**
 * Skill Tracker Hook (PostToolUse)
 * 追踪 skill 调用次数
 */

const fs = require('fs');
const path = require('path');

const STATS_FILE = path.join(process.env.HOME, '.claude/skills/stats.json');

// 从 stdin 读取输入
async function readInput() {
  return new Promise((resolve) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('readable', () => {
      let chunk;
      while ((chunk = process.stdin.read()) !== null) {
        data += chunk;
      }
    });
    process.stdin.on('end', () => {
      try {
        resolve(JSON.parse(data));
      } catch (e) {
        resolve({});
      }
    });
  });
}

function loadStats() {
  try {
    if (fs.existsSync(STATS_FILE)) {
      return JSON.parse(fs.readFileSync(STATS_FILE, 'utf8'));
    }
  } catch (e) {
    // ignore
  }
  return {};
}

function saveStats(stats) {
  try {
    fs.writeFileSync(STATS_FILE, JSON.stringify(stats, null, 2));
  } catch (e) {
    // ignore
  }
}

async function main() {
  const input = await readInput();

  // 获取 skill 名称
  const toolInput = input.tool_input || {};
  const skillName = toolInput.skill || '';

  if (!skillName) {
    console.log(JSON.stringify({ result: 'skipped' }));
    return;
  }

  // 更新统计
  const stats = loadStats();
  stats[skillName] = (stats[skillName] || 0) + 1;
  saveStats(stats);

  console.log(JSON.stringify({
    result: 'success',
    message: `[skill-tracker] ${skillName} 调用次数: ${stats[skillName]}`
  }));
}

main().catch(console.error);
