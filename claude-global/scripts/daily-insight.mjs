#!/usr/bin/env node

/**
 * Daily Personal Insight Generator
 *
 * Runs nightly at 23:15 to generate OKR-based personal insights.
 *
 * 1. Collects agent session summaries from Supabase
 * 2. Checks Odyssey (knowledge base) git changes
 * 3. Generates AI insight via OpenRouter (OKR framework)
 * 4. Saves to Supabase daily_personal_reviews table
 * 5. Creates Notion entry in Personal Review database
 * 6. Appends insight to Odyssey weekly file
 *
 * Usage: node daily-insight.mjs [--date 2026-02-12]
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';
import { homedir } from 'os';
import { execSync } from 'child_process';

// --- Config ---
// AI50 Supabase (online) - for daily_personal_reviews
const SUPABASE_URL = 'https://ebgmmkaxuhawfrwryzia.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImViZ21ta2F4dWhhd2Zyd3J5emlhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg1NjYxNjAsImV4cCI6MjA4NDE0MjE2MH0.TZJAZBJLWL0rkhn3vfAkxPhkpnfXKpaGhZruvysugho';
// Local Supabase - for agent_sessions
const LOCAL_SUPABASE_URL = 'http://127.0.0.1:54321';
const LOCAL_SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0';
// Load secrets from env file
function loadEnv(path) {
  try {
    const content = readFileSync(path, 'utf8');
    for (const line of content.split('\n')) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      const eqIdx = trimmed.indexOf('=');
      if (eqIdx === -1) continue;
      const key = trimmed.slice(0, eqIdx).replace(/^export\s+/, '').trim();
      let val = trimmed.slice(eqIdx + 1).trim();
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'")))
        val = val.slice(1, -1);
      if (!process.env[key]) process.env[key] = val;
    }
  } catch {}
}
loadEnv(join(homedir(), '.claude', 'secrets.env'));

const OPENROUTER_KEY = process.env.OPENROUTER_API_KEY;
const OPENROUTER_MODEL = 'google/gemini-2.5-pro-preview-06-05';
const NOTION_KEY = process.env.NOTION_API_KEY;
const REVIEW_DB_ID = '2f47f9bf-d164-81a2-886f-de01e398ac38';

// Paths relative to home directory
const HOME = homedir();
const ODYSSEY_DIR = join(HOME, 'usr', 'odyssey');
const REVIEW_DIR = join(ODYSSEY_DIR, '4 复盘');

// Parse --date argument
const args = process.argv.slice(2);
let targetDate;
const dateIdx = args.indexOf('--date');
if (dateIdx !== -1 && args[dateIdx + 1]) {
  targetDate = args[dateIdx + 1];
} else {
  const now = new Date();
  const shanghai = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Shanghai' }));
  targetDate = shanghai.toISOString().split('T')[0];
}

console.log(`\n📊 Daily Insight Generator`);
console.log(`📅 Target date: ${targetDate}\n`);

// --- Supabase helpers ---

async function supabaseFetch(path, options = {}, { baseUrl = SUPABASE_URL, apiKey = SUPABASE_KEY } = {}) {
  const url = `${baseUrl}/rest/v1/${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'apikey': apiKey,
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Supabase error: ${res.status} ${text}`);
  }
  const contentType = res.headers.get('content-type');
  if (contentType && contentType.includes('json')) return res.json();
  return null;
}

const LOCAL_SB = { baseUrl: LOCAL_SUPABASE_URL, apiKey: LOCAL_SUPABASE_KEY };
const AI50_SB = { baseUrl: SUPABASE_URL, apiKey: SUPABASE_KEY };

// --- Data Collection ---

async function getAgentSessions(date) {
  const startUTC = new Date(`${date}T00:00:00+08:00`).toISOString();
  const endDate = new Date(new Date(`${date}T00:00:00+08:00`).getTime() + 86400000).toISOString();

  try {
    const sessions = await supabaseFetch(
      `agent_sessions?created_at=gte.${startUTC}&created_at=lt.${endDate}&order=created_at.asc&select=session_id,first_prompt,project_path,metadata,created_at`,
      {}, LOCAL_SB
    );
    return sessions || [];
  } catch (e) {
    console.log(`   ⚠️ Failed to fetch agent sessions: ${e.message}`);
    return [];
  }
}

async function getDailyReport(date) {
  // agent_daily_reports was removed from AI50, skip for now
  return null;
}

function getOdysseyChanges(date) {
  try {
    const result = execSync(
      `cd "${ODYSSEY_DIR}" && git log --after="${date}T00:00:00+08:00" --before="${date}T23:59:59+08:00" --oneline --stat 2>/dev/null || echo ""`,
      { encoding: 'utf8', timeout: 10000 }
    ).trim();
    if (!result) return { commits: 0, filesChanged: 0, summary: '' };

    const lines = result.split('\n');
    const commits = lines.filter(l => /^[a-f0-9]{7,}/.test(l)).length;
    const statLine = lines.find(l => l.includes('files changed') || l.includes('file changed'));
    const filesChanged = statLine ? parseInt(statLine.match(/(\d+) files? changed/)?.[1] || '0') : 0;

    return { commits, filesChanged, summary: result.slice(0, 500) };
  } catch (e) {
    return { commits: 0, filesChanged: 0, summary: '' };
  }
}

// --- AI Insight Generation ---

async function generateInsight(date, sessions, dailyReport, odysseyChanges) {
  const totalMessages = sessions.reduce((sum, s) => sum + (s.metadata?.message_count || 0), 0);
  const projects = [...new Set(sessions.map(s => s.project_path ? s.project_path.split('/').pop() : 'unknown'))];
  const intents = sessions.map(s => s.first_prompt || '').filter(Boolean).slice(0, 10);

  const prompt = `你是一个个人成长分析助手。用户有以下 OKR 体系（2026战略屋）：

O1: 产品项目 - 将想法变为产品，找到付费用户
O2: 心智成长 - 阅读、反思、认知突破
O3: 全球能力 - 英语（托福110目标）、国际化
O4: 健康基建 - 运动、睡眠、饮食
O5: 数字化智能化 - AI 工具、自动化、第二大脑

根据以下数据，生成今日个人洞见。

## 日期: ${date}
## Agent 交互: ${sessions.length} 个会话, ${totalMessages} 条消息
## 涉及项目: ${projects.join(', ')}
## 主要意图:
${intents.map(i => `- ${i.slice(0, 100)}`).join('\n')}

${dailyReport ? `## 日报摘要:\n${dailyReport.ai_daily_summary?.slice(0, 800) || '无'}` : ''}

## 知识库变更: ${odysseyChanges.commits} 次提交, ${odysseyChanges.filesChanged} 个文件
${odysseyChanges.summary ? `变更概要:\n${odysseyChanges.summary.slice(0, 300)}` : ''}

---

请按以下 JSON 格式输出（严格 JSON，不要 markdown 代码块）:
{
  "insight": "一句话洞见（50字以内，说明今天的核心投入方向和OKR关联）",
  "dominant_okr": "O1-O5 中最主导的一个",
  "okr_distribution": {"O1": 百分比, "O2": 百分比, "O3": 百分比, "O4": 百分比, "O5": 百分比},
  "highlights": ["今日亮点1", "今日亮点2"],
  "tomorrow_focus": "明日建议重点（具体可执行的一件事）",
  "warnings": ["需要注意的失衡点"]
}`;

  const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${OPENROUTER_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: OPENROUTER_MODEL,
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 4000,
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`OpenRouter error: ${res.status} ${text}`);
  }

  const data = await res.json();
  const content = data.choices?.[0]?.message?.content || '';

  if (!content) {
    console.error('   ⚠️ Empty AI response, raw:', JSON.stringify(data).slice(0, 500));
    throw new Error('Empty AI response');
  }

  // Parse JSON from response (handle markdown wrapping and extra text)
  let jsonStr = content.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();

  // Try to extract JSON object if there's extra text around it
  const jsonMatch = jsonStr.match(/\{[\s\S]*\}/);
  if (jsonMatch) jsonStr = jsonMatch[0];

  try {
    return JSON.parse(jsonStr);
  } catch (e) {
    console.error('   ⚠️ Failed to parse AI response:', content.slice(0, 300));
    throw new Error(`JSON parse failed: ${e.message}`);
  }
}

// --- Save to Supabase ---

async function saveToSupabase(date, insight, sessions) {
  const totalMessages = sessions.reduce((sum, s) => sum + (s.metadata?.message_count || 0), 0);

  // Convert okr_distribution percentages to decimals for okr_alignment
  const okrAlignment = {};
  if (insight.okr_distribution) {
    for (const [k, v] of Object.entries(insight.okr_distribution)) {
      okrAlignment[k] = v / 100;
    }
  }

  const data = {
    review_date: date,
    okr_alignment: okrAlignment,
    one_line_summary: insight.insight,
    insights: insight.highlights || [],
    tomorrow_suggestions: [insight.tomorrow_focus, ...(insight.warnings || [])].filter(Boolean),
    raw_report: JSON.stringify(insight),
    agent_sessions: sessions.length,
    agent_messages: totalMessages,
  };

  await supabaseFetch('daily_personal_reviews?on_conflict=review_date', {
    method: 'POST',
    headers: { 'Prefer': 'resolution=merge-duplicates,return=minimal' },
    body: JSON.stringify(data),
  }, AI50_SB);
}

// --- Notion Entry ---

async function createNotionEntry(date, insight, sessions) {
  const totalMessages = sessions.reduce((sum, s) => sum + (s.message_count || 0), 0);

  const body = {
    parent: { type: 'database_id', database_id: REVIEW_DB_ID },
    icon: { type: 'emoji', emoji: '📊' },
    properties: {
      'Name': { title: [{ text: { content: `${date} 个人洞见` } }] },
      'Date': { date: { start: date } },
    },
    children: [
      {
        object: 'block', type: 'callout',
        callout: {
          rich_text: [{ type: 'text', text: { content: `💡 ${insight.insight}` } }],
          icon: { type: 'emoji', emoji: '💡' },
          color: 'blue_background',
        },
      },
      { object: 'block', type: 'divider', divider: {} },
      {
        object: 'block', type: 'heading_2',
        heading_2: { rich_text: [{ type: 'text', text: { content: '🎯 OKR 分布' } }] },
      },
      {
        object: 'block', type: 'table',
        table: {
          table_width: 2, has_column_header: true, has_row_header: false,
          children: [
            ['OKR', '占比'],
            ...Object.entries(insight.okr_distribution).map(([k, v]) => [k, `${v}%`]),
          ].map(row => ({
            object: 'block', type: 'table_row',
            table_row: { cells: row.map(cell => [{ type: 'text', text: { content: String(cell) } }]) },
          })),
        },
      },
      { object: 'block', type: 'divider', divider: {} },
      {
        object: 'block', type: 'heading_2',
        heading_2: { rich_text: [{ type: 'text', text: { content: '✨ 亮点' } }] },
      },
      ...insight.highlights.map(h => ({
        object: 'block', type: 'bulleted_list_item',
        bulleted_list_item: { rich_text: [{ type: 'text', text: { content: h } }] },
      })),
      { object: 'block', type: 'divider', divider: {} },
      {
        object: 'block', type: 'heading_2',
        heading_2: { rich_text: [{ type: 'text', text: { content: '🎯 明日重点' } }] },
      },
      {
        object: 'block', type: 'paragraph',
        paragraph: { rich_text: [{ type: 'text', text: { content: insight.tomorrow_focus } }] },
      },
      ...(insight.warnings.length > 0 ? [
        { object: 'block', type: 'divider', divider: {} },
        {
          object: 'block', type: 'heading_2',
          heading_2: { rich_text: [{ type: 'text', text: { content: '⚠️ 预警' } }] },
        },
        ...insight.warnings.map(w => ({
          object: 'block', type: 'bulleted_list_item',
          bulleted_list_item: { rich_text: [{ type: 'text', text: { content: w } }] },
        })),
      ] : []),
      { object: 'block', type: 'divider', divider: {} },
      {
        object: 'block', type: 'paragraph',
        paragraph: {
          rich_text: [{ type: 'text', text: { content: `📊 ${sessions.length} 会话 | ${sessions.reduce((s, x) => s + (x.metadata?.message_count || 0), 0)} 消息 | 主导: ${insight.dominant_okr}` } }],
        },
      },
    ],
  };

  const res = await fetch('https://api.notion.com/v1/pages', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${NOTION_KEY}`,
      'Notion-Version': '2022-06-28',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Notion create page failed: ${res.status} ${errText}`);
  }

  const data = await res.json();
  return data.url;
}

// --- Odyssey Append ---

function appendToOdyssey(date, insight) {
  const d = new Date(`${date}T00:00:00+08:00`);
  const year = d.getFullYear();

  // Calculate ISO week number
  const jan1 = new Date(year, 0, 1);
  const dayOfYear = Math.floor((d - jan1) / 86400000) + 1;
  const weekNum = Math.ceil((dayOfYear + jan1.getDay()) / 7);

  const weekDir = join(REVIEW_DIR, String(year));
  const weekFile = join(weekDir, `${year}年第${weekNum}周.md`);

  if (!existsSync(weekDir)) mkdirSync(weekDir, { recursive: true });

  const entry = `\n\n---\n\n### 📊 ${date} 洞见\n\n> 💡 ${insight.insight}\n\n- 主导 OKR: ${insight.dominant_okr}\n- 亮点: ${insight.highlights.join('；')}\n- 明日重点: ${insight.tomorrow_focus}\n${insight.warnings.length > 0 ? `- ⚠️ ${insight.warnings.join('；')}\n` : ''}\n*🤖 AI 日度洞见生成于 ${new Date().toISOString()}*\n`;

  if (existsSync(weekFile)) {
    const existing = readFileSync(weekFile, 'utf8');
    writeFileSync(weekFile, existing + entry);
  } else {
    const header = `---\nuid: ${crypto.randomUUID()}\n---\n\n# ${year}年第${weekNum}周\n`;
    writeFileSync(weekFile, header + entry);
  }

  return weekFile;
}

// --- Main ---

async function main() {
  console.log('📥 Collecting data...');

  const [sessions, dailyReport] = await Promise.all([
    getAgentSessions(targetDate),
    getDailyReport(targetDate),
  ]);
  const odysseyChanges = getOdysseyChanges(targetDate);

  console.log(`   ✅ Agent: ${sessions.length} sessions`);
  console.log(`   ✅ Odyssey: ${odysseyChanges.commits} commits, ${odysseyChanges.filesChanged} files changed`);

  if (sessions.length === 0 && odysseyChanges.commits === 0) {
    console.log('\n⚠️ No data for today. Skipping insight generation.');
    return;
  }

  console.log('\n📝 Summarizing data...');
  console.log('\n🤖 Generating AI insight...');
  const insight = await generateInsight(targetDate, sessions, dailyReport, odysseyChanges);
  console.log('   ✅ AI insight generated');

  console.log('\n' + '='.repeat(60));
  console.log(`💡 ${insight.insight}`);
  console.log('='.repeat(60));

  // Save to Supabase
  console.log('\n💾 Saving to Supabase...');
  try {
    await saveToSupabase(targetDate, insight, sessions);
    console.log('   ✅ Supabase saved');
  } catch (e) {
    console.error(`   ⚠️ Supabase failed: ${e.message}`);
  }

  // Create Notion entry
  console.log('\n📒 Creating Notion entry...');
  let notionUrl = null;
  try {
    notionUrl = await createNotionEntry(targetDate, insight, sessions);
    console.log(`   ✅ Notion: ${notionUrl}`);
  } catch (e) {
    console.error(`   ⚠️ Notion failed: ${e.message}`);
  }

  // Append to Odyssey
  console.log('\n📓 Appending to Odyssey...');
  try {
    const weekFile = appendToOdyssey(targetDate, insight);
    console.log(`   ✅ Odyssey: ${weekFile}`);
  } catch (e) {
    console.error(`   ⚠️ Odyssey failed: ${e.message}`);
  }

  console.log('\n✅ Daily insight generation complete!');

  // Telegram-style summary for logging
  console.log(`\n\n📱 Telegram Summary:`);
  console.log(`📊 ${targetDate} 洞见已生成`);
  console.log(`💡 ${insight.insight}`);
  console.log(`🎯 明日重点: ${insight.tomorrow_focus}`);
  if (notionUrl) console.log(`👉 详情: ${notionUrl}`);
}

main().catch(e => {
  console.error('Fatal error:', e);
  process.exit(1);
});
