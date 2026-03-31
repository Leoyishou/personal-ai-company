#!/usr/bin/env node

/**
 * Weekly Personal Insight Generator
 *
 * Runs every Sunday at 22:00 to generate OKR-based weekly analysis.
 *
 * 1. Collects daily insights/reports for the week from Supabase
 * 2. Collects agent session totals for the week
 * 3. Checks Odyssey git commits for the week
 * 4. Generates AI weekly OKR analysis via OpenRouter
 * 5. Writes/updates Odyssey weekly file
 *
 * Usage: node weekly-insight.mjs [--week 2026-W07]
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

const HOME = homedir();
const ODYSSEY_DIR = join(HOME, 'usr', 'odyssey');
const REVIEW_DIR = join(ODYSSEY_DIR, '4 复盘');

// --- Week calculation ---

function getISOWeek(date) {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() + 3 - ((d.getDay() + 6) % 7));
  const week1 = new Date(d.getFullYear(), 0, 4);
  return 1 + Math.round(((d - week1) / 86400000 - 3 + ((week1.getDay() + 6) % 7)) / 7);
}

function getWeekDateRange(year, week) {
  // ISO week: Monday is first day
  const jan4 = new Date(year, 0, 4);
  const dayOfWeek = jan4.getDay() || 7;
  const startOfWeek1 = new Date(jan4);
  startOfWeek1.setDate(jan4.getDate() - dayOfWeek + 1);

  const weekStart = new Date(startOfWeek1);
  weekStart.setDate(startOfWeek1.getDate() + (week - 1) * 7);

  const weekEnd = new Date(weekStart);
  weekEnd.setDate(weekStart.getDate() + 6);

  const fmt = d => d.toISOString().split('T')[0];
  return { start: fmt(weekStart), end: fmt(weekEnd) };
}

// Parse --week argument
const args = process.argv.slice(2);
let targetWeek, targetYear, weekNum;
const weekIdx = args.indexOf('--week');
if (weekIdx !== -1 && args[weekIdx + 1]) {
  const match = args[weekIdx + 1].match(/^(\d{4})-W(\d{1,2})$/);
  if (match) {
    targetYear = parseInt(match[1]);
    weekNum = parseInt(match[2]);
    targetWeek = `${targetYear}-W${String(weekNum).padStart(2, '0')}`;
  }
}
if (!targetWeek) {
  const now = new Date();
  const shanghai = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Shanghai' }));
  targetYear = shanghai.getFullYear();
  weekNum = getISOWeek(shanghai);
  targetWeek = `${targetYear}-W${String(weekNum).padStart(2, '0')}`;
}

const { start: weekStart, end: weekEnd } = getWeekDateRange(targetYear, weekNum);

console.log(`\n📅 Weekly Insight Generator`);
console.log(`📆 Week: ${targetWeek} (${weekStart} ~ ${weekEnd})\n`);

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

async function getDailyReviews() {
  try {
    return await supabaseFetch(
      `daily_personal_reviews?review_date=gte.${weekStart}&review_date=lte.${weekEnd}&order=review_date.asc`
    );
  } catch (e) {
    console.log(`   ⚠️ Failed to fetch daily reviews: ${e.message}`);
    return [];
  }
}

async function getDailyReports() {
  // agent_daily_reports table was removed, skip
  return [];
}

async function getWeeklyAgentSessions() {
  const startUTC = new Date(`${weekStart}T00:00:00+08:00`).toISOString();
  const endUTC = new Date(new Date(`${weekEnd}T00:00:00+08:00`).getTime() + 86400000).toISOString();

  try {
    const sessions = await supabaseFetch(
      `agent_sessions?created_at=gte.${startUTC}&created_at=lt.${endUTC}&select=session_id,first_prompt,project_path,metadata,created_at&order=created_at.asc`,
      {}, LOCAL_SB
    );
    return sessions || [];
  } catch (e) {
    console.log(`   ⚠️ Failed to fetch agent sessions: ${e.message}`);
    return [];
  }
}

function getOdysseyCommits() {
  try {
    const result = execSync(
      `cd "${ODYSSEY_DIR}" && git log --after="${weekStart}T00:00:00+08:00" --before="${weekEnd}T23:59:59+08:00" --oneline --stat 2>/dev/null || echo ""`,
      { encoding: 'utf8', timeout: 15000 }
    ).trim();
    if (!result) return { commits: 0, summary: '' };
    const commits = result.split('\n').filter(l => /^[a-f0-9]{7,}/.test(l)).length;
    return { commits, summary: result.slice(0, 1000) };
  } catch {
    return { commits: 0, summary: '' };
  }
}

// --- AI Generation ---

async function generateWeeklyInsight(dailyReviews, dailyReports, sessions, odyssey) {
  const totalSessions = sessions.length;
  const totalMessages = sessions.reduce((sum, s) => sum + (s.metadata?.message_count || 0), 0);
  const projects = [...new Set(sessions.map(s => s.project_path ? s.project_path.split('/').pop() : 'unknown'))];

  // Aggregate OKR distribution from daily reviews (okr_alignment stores decimals)
  const okrTotals = { O1: 0, O2: 0, O3: 0, O4: 0, O5: 0 };
  let okrDays = 0;
  for (const review of dailyReviews) {
    if (review.okr_alignment) {
      for (const [k, v] of Object.entries(review.okr_alignment)) {
        if (okrTotals[k] !== undefined) okrTotals[k] += (v * 100);
      }
      okrDays++;
    }
  }
  if (okrDays > 0) {
    for (const k of Object.keys(okrTotals)) okrTotals[k] = Math.round(okrTotals[k] / okrDays);
  }

  const dailyInsights = dailyReviews.map(r => {
    // Extract dominant_okr from raw_report if available
    let dominant = '';
    try {
      const raw = typeof r.raw_report === 'string' ? JSON.parse(r.raw_report) : r.raw_report;
      dominant = raw?.dominant_okr || '';
    } catch {}
    // Find dominant from okr_alignment if not in raw_report
    if (!dominant && r.okr_alignment) {
      dominant = Object.entries(r.okr_alignment).sort((a, b) => b[1] - a[1])[0]?.[0] || '';
    }
    return `${r.review_date}: [${dominant}] ${r.one_line_summary || ''}`;
  }).join('\n');

  const prompt = `你是一个个人成长分析助手。用户有以下 OKR 体系（2026战略屋）：

O1: 产品项目 - 将想法变为产品，找到付费用户
O2: 心智成长 - 阅读、反思、认知突破
O3: 全球能力 - 英语（托福110目标）、国际化
O4: 健康基建 - 运动、睡眠、饮食
O5: 数字化智能化 - AI 工具、自动化、第二大脑

根据以下周数据，生成周度 OKR 分析报告。

## 周: ${targetWeek} (${weekStart} ~ ${weekEnd})

## 每日洞见汇总:
${dailyInsights || '无每日洞见数据'}

## Agent 交互统计:
- 总会话: ${totalSessions}
- 总消息: ${totalMessages}
- 涉及项目: ${projects.join(', ')}

## OKR 周均分布:
${Object.entries(okrTotals).map(([k, v]) => `${k}: ${v}%`).join(', ')}

## 知识库: ${odyssey.commits} 次提交

## 日报概要:
${dailyReports.map(r => `${r.report_date}: ${r.session_count} 会话, ${r.total_messages} 消息, 项目: ${(r.projects_worked || []).join('+')}`).join('\n') || '无日报数据'}

---

请生成完整的周度分析报告，格式如下（Markdown）：

# ${targetWeek} 周度分析

## 📊 本周概览
（一段话总结，包含主导 OKR、关键投入方向、成果亮点）

## 🎯 OKR 周度评估

| OKR | 占比 | 评价 |
|-----|------|------|
（每个 OKR 一行，给出占比和简短评价）

## 💡 核心洞见
（2-3 条战略级洞见，每条包含影响和行动建议）

## ⚠️ 预警
（需要注意的失衡、风险或遗漏）

## 🎯 下周重点
（具体可执行的 1-2 件事）`;

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
  return data.choices[0].message.content;
}

// --- Odyssey Write ---

function writeToOdyssey(report) {
  const weekDir = join(REVIEW_DIR, String(targetYear));
  const weekFile = join(weekDir, `${targetYear}年第${weekNum}周.md`);

  if (!existsSync(weekDir)) mkdirSync(weekDir, { recursive: true });

  // Extract one-liner from report (first paragraph after ##)
  const overviewMatch = report.match(/## 📊 本周概览\n\n(.+?)(\n\n|$)/s);
  const overview = overviewMatch ? overviewMatch[1].trim().slice(0, 200) : '';

  const content = `---
uid: ${crypto.randomUUID()}
---

${report}

---

*🤖 AI 周报生成于 ${new Date().toISOString()}*
`;

  if (existsSync(weekFile)) {
    // Append to existing file (don't overwrite user content)
    const existing = readFileSync(weekFile, 'utf8');
    writeFileSync(weekFile, existing + '\n\n---\n\n' + report + `\n\n*🤖 AI 周报生成于 ${new Date().toISOString()}*\n`);
  } else {
    writeFileSync(weekFile, content);
  }

  return { weekFile, overview };
}

// --- Main ---

async function main() {
  console.log('📥 Collecting weekly data...');

  const [dailyReviews, dailyReports, sessions] = await Promise.all([
    getDailyReviews(),
    getDailyReports(),
    getWeeklyAgentSessions(),
  ]);
  const odyssey = getOdysseyCommits();

  console.log(`   ✅ Daily reviews: ${dailyReviews.length}`);
  console.log(`   ✅ Daily reports: ${dailyReports.length}`);
  console.log(`   ✅ Agent: ${sessions.length} sessions`);
  console.log(`   ✅ Odyssey: ${odyssey.commits} commits`);

  console.log('\n📝 Summarizing data...');
  console.log('\n🤖 Generating AI weekly insight...');
  const report = await generateWeeklyInsight(dailyReviews, dailyReports, sessions, odyssey);
  console.log('   ✅ AI insight generated');

  // Extract one-liner for summary
  const overviewMatch = report.match(/## 📊 本周概览\n\n(.+?)(\n\n|$)/s);
  const oneLiner = overviewMatch ? overviewMatch[1].trim().slice(0, 200) : report.slice(0, 200);

  console.log('\n' + '='.repeat(60));
  console.log(`📅 ${targetWeek}`);
  console.log(`💡 ${oneLiner}`);
  console.log('='.repeat(60));

  // Write to Odyssey
  console.log('\n📓 Updating Odyssey weekly file...');
  try {
    const { weekFile } = writeToOdyssey(report);
    console.log(`   ✅ Odyssey: ${weekFile}`);
  } catch (e) {
    console.error(`   ⚠️ Odyssey failed: ${e.message}`);
  }

  console.log('\n✅ Weekly insight generation complete!');

  // Extract warnings and next week focus for summary
  const warningsMatch = report.match(/## ⚠️ 预警\n\n([\s\S]*?)(?=\n## |$)/);
  const warnings = warningsMatch ? warningsMatch[1].trim().split('\n').filter(l => l.startsWith('-')).length : 0;
  const focusMatch = report.match(/## 🎯 下周重点\n\n([\s\S]*?)(?=\n## |$)/);
  const nextFocus = focusMatch ? focusMatch[1].trim().split('\n').find(l => l.startsWith('-') || l.startsWith('1'))?.replace(/^[-\d.]\s*/, '') || '' : '';

  console.log(`\n\n📱 Telegram Summary:`);
  console.log(`📅 ${targetWeek} 周报已生成`);
  console.log(`💡 ${oneLiner}`);
  if (warnings > 0) console.log(`⚠️ 预警: ${warnings} 条`);
  if (nextFocus) console.log(`🎯 下周重点: ${nextFocus}`);
}

main().catch(e => {
  console.error('Fatal error:', e);
  process.exit(1);
});
