#!/usr/bin/env node
/**
 * CC Dashboard Tracker Hook
 * 追踪 Skill 和 Subagent 调用，写入 Supabase
 *
 * 使用方式:
 *   - PostToolUse (Skill): node index.js skill
 *   - SubagentStart: node index.js subagent-start
 *   - SubagentStop: node index.js subagent-stop
 */

const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');

// 加载环境变量
const secretsPath = path.join(process.env.HOME, '.claude/secrets.env');
if (fs.existsSync(secretsPath)) {
  const content = fs.readFileSync(secretsPath, 'utf8');
  content.split('\n').forEach(line => {
    const match = line.match(/^export\s+(\w+)=["']?([^"'\n]+)["']?/);
    if (match) {
      process.env[match[1]] = match[2];
    }
  });
}

const SUPABASE_URL = process.env.PDC_URL;
const SUPABASE_KEY = process.env.PDC_SERVICE_KEY;

if (!SUPABASE_URL || !SUPABASE_KEY) {
  console.log(JSON.stringify({ continue: true }));
  process.exit(0);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

// 内存缓存 subagent 开始时间
const CACHE_FILE = path.join(process.env.HOME, '.claude/logs/subagent-cache.json');

function loadCache() {
  try {
    if (fs.existsSync(CACHE_FILE)) {
      return JSON.parse(fs.readFileSync(CACHE_FILE, 'utf8'));
    }
  } catch (e) {}
  return {};
}

function saveCache(cache) {
  const dir = path.dirname(CACHE_FILE);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  fs.writeFileSync(CACHE_FILE, JSON.stringify(cache));
}

// 从 stdin 读取 hook 输入
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

async function trackSkill(input) {
  const toolInput = input.tool_input || {};
  const skillName = toolInput.skill;

  if (!skillName) return;

  try {
    await supabase.from('cc_skill_invocations').insert({
      session_id: input.session_id,
      skill_name: skillName,
      agent_type: 'skill',
      input_summary: toolInput.args || null,
      status: 'completed',
      started_at: new Date().toISOString(),
      ended_at: new Date().toISOString(),
      metadata: { tool_result: input.tool_result?.substring?.(0, 500) }
    });
  } catch (e) {
    // 静默失败
  }
}

async function trackSubagentStart(input) {
  const toolInput = input.tool_input || {};
  const subagentType = toolInput.subagent_type;
  const description = toolInput.description;

  if (!subagentType) return;

  const invocationId = `${input.session_id}-${Date.now()}`;

  // 缓存开始时间
  const cache = loadCache();
  cache[invocationId] = {
    started_at: new Date().toISOString(),
    subagent_type: subagentType,
    description: description,
    session_id: input.session_id
  };
  saveCache(cache);

  try {
    const { data } = await supabase.from('cc_skill_invocations').insert({
      session_id: input.session_id,
      skill_name: subagentType,
      agent_type: 'subagent',
      input_summary: description,
      status: 'started',
      started_at: new Date().toISOString(),
      metadata: { invocation_id: invocationId, prompt: toolInput.prompt?.substring?.(0, 500) }
    }).select('id').single();

    if (data?.id) {
      cache[invocationId].db_id = data.id;
      saveCache(cache);
    }
  } catch (e) {
    // 静默失败
  }
}

async function trackSubagentStop(input) {
  const subagentType = input.subagent_type || input.tool_input?.subagent_type;

  // 找到最近的匹配项并更新
  const cache = loadCache();
  const keys = Object.keys(cache).filter(k =>
    cache[k].subagent_type === subagentType &&
    cache[k].session_id === input.session_id
  );

  if (keys.length === 0) return;

  // 取最近的一个
  const key = keys[keys.length - 1];
  const entry = cache[key];

  if (entry.db_id) {
    const duration = Date.now() - new Date(entry.started_at).getTime();

    try {
      await supabase.from('cc_skill_invocations')
        .update({
          status: 'completed',
          ended_at: new Date().toISOString(),
          duration_ms: duration
        })
        .eq('id', entry.db_id);
    } catch (e) {
      // 静默失败
    }
  }

  // 清理缓存
  delete cache[key];
  saveCache(cache);
}

async function main() {
  const action = process.argv[2];
  const input = await readInput();

  switch (action) {
    case 'skill':
      await trackSkill(input);
      break;
    case 'subagent-start':
      await trackSubagentStart(input);
      break;
    case 'subagent-stop':
      await trackSubagentStop(input);
      break;
  }

  console.log(JSON.stringify({ continue: true }));
}

main().catch(() => {
  console.log(JSON.stringify({ continue: true }));
});
