#!/usr/bin/env node
/**
 * Superpowers Tracker Hook
 *
 * 触发时机：PostToolUse (Skill)
 * 职责：检测 superpowers skill 调用，启动 PMO agent 处理
 *
 * 架构原则：Hook 只负责检测和投递，所有 Linear 操作通过 PMO Agent 实现
 */

const { spawn } = require('child_process');
const fs = require('fs');

// 需要追踪的 superpowers（影响 Linear 状态的关键节点）
const TRACKED_SUPERPOWERS = {
  'superpowers:brainstorming': {
    phase: 'requirements',
    linearAction: 'create_or_update_issue',
    description: '需求分析完成'
  },
  'superpowers:writing-plans': {
    phase: 'planning',
    linearAction: 'update_issue_with_plan',
    description: '实施计划写好'
  },
  'superpowers:using-git-worktrees': {
    phase: 'development',
    linearAction: 'set_in_progress',
    description: '开发分支创建'
  },
  'superpowers:test-driven-development': {
    phase: 'development',
    linearAction: 'log_activity',
    description: 'TDD 开发中'
  },
  'superpowers:requesting-code-review': {
    phase: 'review',
    linearAction: 'set_in_review',
    description: '请求代码审查'
  },
  'superpowers:verification-before-completion': {
    phase: 'verification',
    linearAction: 'log_verification',
    description: '验证完成'
  },
  'superpowers:finishing-a-development-branch': {
    phase: 'completion',
    linearAction: 'set_ready_for_release',
    description: '分支开发完成'
  }
};

const LOG_FILE = '/tmp/superpowers-tracker.log';
const PMO_DIR = '/Users/liuyishou/usr/pac/pmo';

function log(msg) {
  fs.appendFileSync(LOG_FILE, `[${new Date().toISOString()}] ${msg}\n`);
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

function detectBu(cwd) {
  if (!cwd) return 'unknown';
  if (cwd.includes('product-bu')) return 'product';
  if (cwd.includes('content-bu')) return 'content';
  if (cwd.includes('investment-bu')) return 'investment';
  return 'unknown';
}

async function main() {
  const input = await readInput();
  log(`Input: ${JSON.stringify(input)}`);

  const { tool_input, session_id, cwd } = input;

  // 检查是否是 Skill 工具调用
  const skillName = tool_input?.skill;
  if (!skillName) {
    console.log(JSON.stringify({ result: 'skipped', reason: 'Not a skill call' }));
    return;
  }

  // 检查是否是需要追踪的 superpower
  const tracked = TRACKED_SUPERPOWERS[skillName];
  if (!tracked) {
    console.log(JSON.stringify({ result: 'skipped', reason: 'Not a tracked superpower' }));
    return;
  }

  const bu = detectBu(cwd);

  // 只追踪产品事业部的 superpowers
  if (bu !== 'product') {
    console.log(JSON.stringify({ result: 'skipped', reason: `BU ${bu} not tracked` }));
    return;
  }

  // 构建事件对象
  const event = {
    type: 'superpower_event',
    skill: skillName,
    phase: tracked.phase,
    action: tracked.linearAction,
    description: tracked.description,
    sessionId: session_id,
    cwd: cwd,
    timestamp: new Date().toISOString()
  };

  log(`Dispatching to PMO Agent: ${JSON.stringify(event)}`);

  // 通过 PMO Agent 处理（异步，不阻塞）
  const prompt = `处理 superpower 事件：
${JSON.stringify(event, null, 2)}

请根据 CLAUDE.md 中的规则处理此事件，更新 Linear Issue。`;

  try {
    // 移除 ANTHROPIC_API_KEY，让 claude 使用 Pro 订阅认证而非 API key
    const { ANTHROPIC_API_KEY, ...cleanEnv } = process.env;

    // 启动 PMO Agent（后台运行，不阻塞 hook）
    const child = spawn('claude', [
      '--dangerously-skip-permissions',
      '--print',
      '-p', prompt
    ], {
      cwd: PMO_DIR,
      detached: true,
      stdio: ['ignore', 'pipe', 'pipe'],
      env: cleanEnv
    });

    // 捕获输出用于日志（可选）
    let output = '';
    child.stdout.on('data', (data) => { output += data.toString(); });
    child.stderr.on('data', (data) => { output += data.toString(); });

    child.on('close', (code) => {
      log(`PMO Agent finished with code ${code}`);
      if (output) log(`PMO Agent output: ${output.substring(0, 500)}`);
    });

    // 让子进程在后台运行
    child.unref();

    console.log(JSON.stringify({
      result: 'dispatched',
      skill: skillName,
      phase: tracked.phase,
      action: tracked.linearAction,
      bu: bu,
      message: 'Event dispatched to PMO Agent'
    }));
  } catch (e) {
    log(`Error spawning PMO Agent: ${e.message}`);
    console.log(JSON.stringify({
      result: 'error',
      skill: skillName,
      error: e.message
    }));
  }
}

main().catch(err => {
  log(`Fatal error: ${err.message}`);
  console.log(JSON.stringify({ result: 'error', reason: err.message }));
});
