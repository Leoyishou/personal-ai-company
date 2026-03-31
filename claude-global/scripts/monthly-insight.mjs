#!/usr/bin/env node

/**
 * Monthly Personal Insight Generator
 *
 * Runs on the 1st of each month at 21:00 to generate monthly OKR analysis.
 *
 * 1. Collects weekly reports and daily reviews for the month from Supabase
 * 2. Collects Odyssey git commits for the month
 * 3. Generates AI monthly theme analysis via OpenRouter
 * 4. Creates Odyssey monthly summary file
 *
 * Usage: node monthly-insight.mjs [--month 2026-02]
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

// --- Month calculation ---

function getMonthRange(year, month) {
  const start = `${year}-${String(month).padStart(2, '0')}-01`;
  const endDate = new Date(year, month, 0); // last day of month
  const end = `${year}-${String(month).padStart(2, '0')}-${String(endDate.getDate()).padStart(2, '0')}`;
  return { start, end };
}

const MONTH_NAMES = ['', '1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];

// Parse --month argument
const args = process.argv.slice(2);
let targetYear, targetMonth;
const monthIdx = args.indexOf('--month');
if (monthIdx !== -1 && args[monthIdx + 1]) {
  const match = args[monthIdx + 1].match(/^(\d{4})-(\d{1,2})$/);
  if (match) {
    targetYear = parseInt(match[1]);
    targetMonth = parseInt(match[2]);
  }
}
if (!targetYear) {
  // Default to previous month (since this runs on the 1st)
  const now = new Date();
  const shanghai = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Shanghai' }));
  targetYear = shanghai.getFullYear();
  targetMonth = shanghai.getMonth(); // 0-indexed, so this is previous month
  if (targetMonth === 0) {
    targetMonth = 12;
    targetYear--;
  }
}

const targetMonthStr = `${targetYear}-${String(targetMonth).padStart(2, '0')}`;
const { start: monthStart, end: monthEnd } = getMonthRange(targetYear, targetMonth);

console.log(`\n📅 Monthly Insight Generator`);
console.log(`📆 Month: ${targetMonthStr} (${monthStart} ~ ${monthEnd})\n`);

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
      `daily_personal_reviews?review_date=gte.${monthStart}&review_date=lte.${monthEnd}&order=review_date.asc`
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

async function getMonthlyAgentSessions() {
  const startUTC = new Date(`${monthStart}T00:00:00+08:00`).toISOString();
  const endUTC = new Date(new Date(`${monthEnd}T00:00:00+08:00`).getTime() + 86400000).toISOString();

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
      `cd "${ODYSSEY_DIR}" && git log --after="${monthStart}T00:00:00+08:00" --before="${monthEnd}T23:59:59+08:00" --oneline --stat 2>/dev/null || echo ""`,
      { encoding: 'utf8', timeout: 15000 }
    ).trim();
    if (!result) return { commits: 0, filesChanged: 0, newConcepts: 0 };

    const lines = result.split('\n');
    const commits = lines.filter(l => /^[a-f0-9]{7,}/.test(l)).length;
    const statLines = lines.filter(l => l.includes('files changed') || l.includes('file changed'));
    const filesChanged = statLines.reduce((sum, l) => sum + parseInt(l.match(/(\d+) files? changed/)?.[1] || '0'), 0);

    return { commits, filesChanged, newConcepts: 0 };
  } catch {
    return { commits: 0, filesChanged: 0, newConcepts: 0 };
  }
}

// --- AI Generation ---

async function generateMonthlyInsight(dailyReviews, dailyReports, sessions, odyssey) {
  const totalSessions = sessions.length;
  const totalMessages = sessions.reduce((sum, s) => sum + (s.metadata?.message_count || 0), 0);
  const projects = [...new Set(sessions.map(s => s.project_path ? s.project_path.split('/').pop() : 'unknown'))];

  // Aggregate OKR distribution (okr_alignment stores decimals)
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

  // Dominant OKRs per day (extract from raw_report or compute from okr_alignment)
  const dominantCounts = {};
  for (const review of dailyReviews) {
    let dominant = '';
    try {
      const raw = typeof review.raw_report === 'string' ? JSON.parse(review.raw_report) : review.raw_report;
      dominant = raw?.dominant_okr || '';
    } catch {}
    if (!dominant && review.okr_alignment) {
      dominant = Object.entries(review.okr_alignment).sort((a, b) => b[1] - a[1])[0]?.[0] || '';
    }
    if (dominant) {
      dominantCounts[dominant] = (dominantCounts[dominant] || 0) + 1;
    }
  }

  const prompt = `你是一个个人成长分析助手。用户有以下 OKR 体系（2026战略屋）：

O1: 产品项目 - 将想法变为产品，找到付费用户
O2: 心智成长 - 阅读、反思、认知突破
O3: 全球能力 - 英语（托福110目标）、国际化
O4: 健康基建 - 运动、睡眠、饮食
O5: 数字化智能化 - AI 工具、自动化、第二大脑

根据以下月度数据，生成月度总结报告。

## 月份: ${targetMonthStr} (${monthStart} ~ ${monthEnd})

## 数据总量:
- Agent 会话: ${totalSessions}
- Agent 消息: ${totalMessages}
- 涉及项目: ${projects.join(', ')}
- 有数据天数: ${dailyReviews.length}
- 知识库提交: ${odyssey.commits} 次
- 文件变更: ${odyssey.filesChanged} 个

## OKR 月均分布:
${Object.entries(okrTotals).map(([k, v]) => `${k}: ${v}%`).join(', ')}

## 主导 OKR 天数统计:
${Object.entries(dominantCounts).map(([k, v]) => `${k}: ${v}天`).join(', ') || '无数据'}

## 每日洞见汇总:
${dailyReviews.map(r => {
    let dominant = '';
    try {
      const raw = typeof r.raw_report === 'string' ? JSON.parse(r.raw_report) : r.raw_report;
      dominant = raw?.dominant_okr || '';
    } catch {}
    if (!dominant && r.okr_alignment) {
      dominant = Object.entries(r.okr_alignment).sort((a, b) => b[1] - a[1])[0]?.[0] || '';
    }
    return `${r.review_date}: [${dominant}] ${r.one_line_summary || ''}`;
  }).join('\n').slice(0, 2000) || '无数据'}

## 日报统计:
${dailyReports.map(r => `${r.report_date}: ${r.session_count} 会话, ${r.total_messages} 消息`).join('\n').slice(0, 1000) || '无数据'}

---

请生成完整的月度总结报告，格式严格如下（Markdown）：

# ${targetYear}年${targetMonth}月 总结

> ${monthStart} ~ ${monthEnd}

## 📊 月度总结
（一段话概括本月核心主题、关键成果和主要问题）

---

## 🦋 身份演化

### 正在涌现的身份
（本月开始形成的新身份/角色）

### 持续强化的身份
（已有且在加强的身份）

### 逐渐弱化的身份
（在衰退的身份）

---

## 🎯 OKR 月度回顾

| OKR | 月均 | 评价 |
|-----|------|------|
（每个 OKR 一行：名称、月均占比、简短评价如"稳步推进"/"严重停滞"等）

---

## 💡 战略洞见
（2-3 条深度洞见，每条包含：现象描述 + 影响分析 + 具体行动建议）

---

## 🔧 OKR 调整建议
（哪些 OKR 占比需要调高/调低，给出原因）

---

## 🎯 下月主题
（一句话主题）

### Top 3 优先事项
（编号列表，每项包含成功指标）

---

## 📈 突破时刻
（本月最值得记录的 1-2 个突破性事件）

---

## 📋 本月数据

- 有数据天数: ${dailyReviews.length} 天
- 知识库提交: ${odyssey.commits} 次
- 文件变更: ${odyssey.filesChanged} 个
- Agent 会话: ${totalSessions}
- Agent 消息: ${totalMessages}

---

*🤖 AI 月报生成于 ${new Date().toISOString()}*`;

  const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${OPENROUTER_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: OPENROUTER_MODEL,
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 6000,
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
  const yearDir = join(REVIEW_DIR, String(targetYear));
  const monthFile = join(yearDir, `${targetYear}年${targetMonth}月总结.md`);

  if (!existsSync(yearDir)) mkdirSync(yearDir, { recursive: true });

  const content = `---
uid: ${crypto.randomUUID()}
---

${report}
`;

  writeFileSync(monthFile, content);
  return monthFile;
}

// --- Main ---

async function main() {
  console.log('📥 Collecting monthly data...');

  const [dailyReviews, dailyReports, sessions] = await Promise.all([
    getDailyReviews(),
    getDailyReports(),
    getMonthlyAgentSessions(),
  ]);
  const odyssey = getOdysseyCommits();

  console.log(`   ✅ Daily reviews: ${dailyReviews.length}`);
  console.log(`   ✅ Daily reports: ${dailyReports.length}`);
  console.log(`   ✅ Agent: ${sessions.length} sessions`);
  console.log(`   ✅ Odyssey: ${odyssey.commits} commits`);

  console.log('\n📝 Summarizing data...');
  console.log('\n🤖 Generating AI monthly insight...');
  const report = await generateMonthlyInsight(dailyReviews, dailyReports, sessions, odyssey);
  console.log('   ✅ AI insight generated');

  // Extract summary line
  const summaryMatch = report.match(/## 📊 月度总结\n\n(.+?)(\n\n|$)/s);
  const oneLiner = summaryMatch ? summaryMatch[1].trim().slice(0, 200) : report.slice(0, 200);

  // Extract next month theme
  const themeMatch = report.match(/## 🎯 下月主题\n\n\*?\*?(.+?)\*?\*?(\n|$)/);
  const nextTheme = themeMatch ? themeMatch[1].trim() : '';

  console.log('\n' + '='.repeat(60));
  console.log(`📅 ${targetMonthStr}`);
  console.log(`💡 ${oneLiner}`);
  if (nextTheme) console.log(`🎯 下月主题: ${nextTheme}`);
  console.log('='.repeat(60));

  // Write to Odyssey
  console.log('\n📓 Creating Odyssey monthly file...');
  try {
    const monthFile = writeToOdyssey(report);
    console.log(`   ✅ Odyssey: ${monthFile}`);
  } catch (e) {
    console.error(`   ⚠️ Odyssey failed: ${e.message}`);
  }

  console.log('\n✅ Monthly insight generation complete!');

  // Extract top priority for summary
  const topMatch = report.match(/### Top 3 优先事项\n\n1\.\s*(.+?)(\n|$)/);
  const topPriority = topMatch ? topMatch[1].trim() : '';

  console.log(`\n\n📱 Telegram Summary:`);
  console.log(`📅 ${targetMonthStr} 月报已生成`);
  console.log(`💡 ${oneLiner}`);
  if (nextTheme) console.log(`🎯 下月主题: ${nextTheme}`);
  if (topPriority) console.log(`🔝 首要事项: ${topPriority}`);
}

main().catch(e => {
  console.error('Fatal error:', e);
  process.exit(1);
});
