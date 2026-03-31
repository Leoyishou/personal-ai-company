#!/usr/bin/env node

/**
 * Daily Agent Report Generator
 *
 * 1. Syncs new sessions to Supabase
 * 2. Queries today's sessions
 * 3. Generates AI summary via OpenRouter (Gemini 3 Pro)
 * 4. Stores report in agent_daily_reports table
 * 5. Creates rich Notion entry in Agent Daily database
 *
 * Usage: node daily-report.mjs [--date 2026-01-23]
 */

import { readFileSync, readdirSync, existsSync, statSync } from 'fs';
import { join } from 'path';
import { homedir } from 'os';
import { execSync } from 'child_process';

const SUPABASE_URL = 'https://ebgmmkaxuhawfrwryzia.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImViZ21ta2F4dWhhd2Zyd3J5emlhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg1NjYxNjAsImV4cCI6MjA4NDE0MjE2MH0.TZJAZBJLWL0rkhn3vfAkxPhkpnfXKpaGhZruvysugho';
const OPENROUTER_KEY = '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';
const OPENROUTER_MODEL = 'google/gemini-2.5-pro-preview-06-05';
const NOTION_KEY = process.env.NOTION_API_KEY;
const AGENT_DB_ID = '2f17f9bf-d164-8191-887c-c4f29c13c673';

// Parse --date argument
const args = process.argv.slice(2);
let targetDate;
const dateIdx = args.indexOf('--date');
if (dateIdx !== -1 && args[dateIdx + 1]) {
  targetDate = args[dateIdx + 1];
} else {
  // Default to today (Asia/Shanghai timezone)
  const now = new Date();
  const shanghai = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Shanghai' }));
  targetDate = shanghai.toISOString().split('T')[0];
}

console.log(`📅 Generating report for: ${targetDate}\n`);

// --- Supabase helpers ---

async function supabaseFetch(path, options = {}) {
  const url = `${SUPABASE_URL}/rest/v1/${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'apikey': SUPABASE_KEY,
      'Authorization': `Bearer ${SUPABASE_KEY}`,
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Supabase error: ${res.status} ${text}`);
  }
  const contentType = res.headers.get('content-type');
  if (contentType && contentType.includes('json')) {
    return res.json();
  }
  return null;
}

// --- Step 1: Sync sessions first ---

async function syncSessions() {
  console.log('🔄 Syncing new sessions...');
  try {
    const scriptPath = join(homedir(), '.claude', 'scripts', 'sync-sessions.mjs');
    execSync(`"${process.execPath}" "${scriptPath}"`, {
      stdio: 'pipe',
      timeout: 60000,
    });
    console.log('   ✅ Sync complete\n');
  } catch (e) {
    console.log(`   ⚠️ Sync had issues: ${e.message}\n`);
  }
}

// --- Step 2: Query today's sessions ---

async function getTodaySessions(date) {
  // Get sessions that started on this date (UTC+8)
  // Convert date to UTC range: date 00:00 CST = date-1 16:00 UTC, date+1 00:00 CST = date 16:00 UTC
  const startUTC = new Date(`${date}T00:00:00+08:00`).toISOString();
  const endDate = new Date(new Date(`${date}T00:00:00+08:00`).getTime() + 86400000).toISOString();

  const sessions = await supabaseFetch(
    `agent_sessions?started_at=gte.${startUTC}&started_at=lt.${endDate}&order=started_at.asc`
  );

  return sessions;
}

async function getSessionMessages(sessionId) {
  const messages = await supabaseFetch(
    `agent_messages?session_id=eq.${sessionId}&order=seq.asc&select=seq,type,role,content,tools_used,timestamp`
  );
  return messages;
}

// --- Step 3: Build context for AI ---

function extractUserIntents(messages) {
  const intents = [];
  for (const msg of messages) {
    if (msg.type === 'user' && msg.content) {
      if (Array.isArray(msg.content)) {
        for (const block of msg.content) {
          if (block && block.type === 'text' && block.text) {
            intents.push(block.text.slice(0, 200));
          }
        }
      } else if (typeof msg.content === 'string') {
        intents.push(msg.content.slice(0, 200));
      }
    }
  }
  return intents;
}

function extractAssistantOutputs(messages) {
  const outputs = [];
  for (const msg of messages) {
    if (msg.type === 'assistant' && msg.content) {
      if (Array.isArray(msg.content)) {
        for (const block of msg.content) {
          if (block && block.type === 'text' && block.text) {
            outputs.push(block.text.slice(0, 300));
          }
        }
      }
    }
  }
  return outputs;
}

async function buildDayContext(sessions) {
  const sessionSummaries = [];

  for (const session of sessions) {
    const messages = await getSessionMessages(session.session_id);

    const userIntents = extractUserIntents(messages);
    const assistantOutputs = extractAssistantOutputs(messages);

    // Collect all tools used across messages
    const allTools = [];
    for (const msg of messages) {
      if (msg.tools_used) allTools.push(...msg.tools_used);
    }
    const toolCounts = {};
    for (const t of allTools) {
      toolCounts[t] = (toolCounts[t] || 0) + 1;
    }

    sessionSummaries.push({
      first_prompt: session.first_prompt || '',
      project: session.project_path ? session.project_path.split('/').pop() : 'unknown',
      message_count: session.message_count,
      started_at: session.started_at,
      ended_at: session.ended_at,
      tools: toolCounts,
      user_intents_sample: userIntents.slice(0, 5), // First 5 user messages
      assistant_outputs_sample: assistantOutputs.slice(-3), // Last 3 assistant outputs
    });
  }

  return sessionSummaries;
}

// --- Step 4: AI Summarization ---

async function generateReport(date, sessionSummaries) {
  const totalMessages = sessionSummaries.reduce((sum, s) => sum + s.message_count, 0);
  const allTools = {};
  for (const s of sessionSummaries) {
    for (const [tool, count] of Object.entries(s.tools)) {
      allTools[tool] = (allTools[tool] || 0) + count;
    }
  }

  const prompt = `你是一个个人效率分析助手。请根据以下用户与 AI Agent 的一天交互数据，生成一份日报。

## 日期: ${date}
## 统计: ${sessionSummaries.length} 个会话, ${totalMessages} 条消息

## 各会话详情:
${sessionSummaries.map((s, i) => `
### 会话 ${i + 1} (${s.message_count}条消息, 项目: ${s.project})
- 开始: ${s.started_at}
- 首条意图: "${s.first_prompt.slice(0, 150)}"
- 使用工具: ${Object.entries(s.tools).map(([k, v]) => `${k}(${v})`).join(', ')}
- 用户主要意图:
${s.user_intents_sample.map(t => `  - ${t}`).join('\n')}
- AI 最后输出摘要:
${s.assistant_outputs_sample.map(t => `  - ${t.slice(0, 150)}`).join('\n')}
`).join('\n')}

## 工具使用汇总:
${Object.entries(allTools).sort((a, b) => b[1] - a[1]).slice(0, 15).map(([k, v]) => `- ${k}: ${v}次`).join('\n')}

---

请按以下格式生成日报（用中文）:

# 🗓 ${date} Agent 日报

## 今日概览
(会话数、消息量、活跃时段、涉及项目)

## 意图→产出清单
(用表格列出每个会话的：意图、AI杠杆、产出、状态)
| # | 意图 | AI杠杆 | 产出 | 状态 |

## AI 能力使用分布
(按类型分：创作、开发、研究、管理，列出具体工具和次数)

## 效率观察
(平均轮次、最长会话、重试情况)

## 今日洞察
(从交互模式中发现的规律、改进建议)

## 明日线索
(未完成的、值得继续的方向)

请确保内容精练、信息密度高。`;

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

// --- Step 5: Store report ---

async function storeReport(date, sessions, report) {
  const totalMessages = sessions.reduce((sum, s) => sum + s.message_count, 0);
  const projects = [...new Set(sessions.map(s => s.project_path ? s.project_path.split('/').pop() : 'unknown'))];
  const sessionIds = sessions.map(s => s.session_id);

  // Collect tools summary
  const allTools = {};
  for (const s of sessions) {
    // We already have this from buildDayContext, but let's just store session-level info
  }

  const reportData = {
    report_date: date,
    session_ids: sessionIds,
    session_count: sessions.length,
    total_messages: totalMessages,
    projects_worked: projects,
    ai_daily_summary: report,
  };

  // Upsert (in case we re-run for the same date)
  await supabaseFetch('agent_daily_reports?on_conflict=report_date', {
    method: 'POST',
    headers: {
      'Prefer': 'resolution=merge-duplicates,return=minimal',
    },
    body: JSON.stringify(reportData),
  });
}

// --- Step 6: Notion Integration ---

function nText(content, opts = {}) {
  const t = { type: 'text', text: { content } };
  const annotations = {};
  if (opts.bold) annotations.bold = true;
  if (opts.italic) annotations.italic = true;
  if (opts.code) annotations.code = true;
  if (Object.keys(annotations).length) t.annotations = annotations;
  return t;
}

function nHeading2(content) {
  return { object: 'block', type: 'heading_2', heading_2: { rich_text: [nText(content)] } };
}

function nCallout(content, icon = '💡', color = 'blue_background') {
  const richText = typeof content === 'string' ? [nText(content)] : content;
  return { object: 'block', type: 'callout', callout: { rich_text: richText, icon: { type: 'emoji', emoji: icon }, color } };
}

function nDivider() { return { object: 'block', type: 'divider', divider: {} }; }

function nBullet(...richTexts) {
  return { object: 'block', type: 'bulleted_list_item', bulleted_list_item: { rich_text: richTexts } };
}

function nToggle(title, children = []) {
  return { object: 'block', type: 'toggle', toggle: { rich_text: typeof title === 'string' ? [nText(title)] : title, children } };
}

function nTable(rows) {
  const width = rows[0].length;
  return {
    object: 'block', type: 'table',
    table: { table_width: width, has_column_header: true, has_row_header: false,
      children: rows.map(row => ({
        object: 'block', type: 'table_row',
        table_row: { cells: row.map(cell => [nText(String(cell))]) }
      }))
    }
  };
}

function nCodeBlock(content, language = 'plain text') {
  return { object: 'block', type: 'code', code: { rich_text: [nText(content)], language } };
}

function buildNotionBlocks(date, sessions, context, allToolCounts) {
  const blocks = [];
  const totalMessages = context.reduce((sum, s) => sum + s.message_count, 0);
  const completedCount = context.length; // All synced sessions are considered completed

  // Calculate time range
  const startTimes = context.map(s => s.started_at).filter(Boolean).sort();
  const endTimes = context.map(s => s.ended_at).filter(Boolean).sort();
  const firstTime = startTimes[0] ? new Date(startTimes[0]).toLocaleTimeString('zh-CN', { timeZone: 'Asia/Shanghai', hour: '2-digit', minute: '2-digit' }) : '??:??';
  const lastTime = endTimes[endTimes.length - 1] ? new Date(endTimes[endTimes.length - 1]).toLocaleTimeString('zh-CN', { timeZone: 'Asia/Shanghai', hour: '2-digit', minute: '2-digit' }) : '??:??';

  // Header callout
  blocks.push(nCallout([
    nText('时间: ', { bold: true }), nText(`${date} ${firstTime} ~ ${lastTime} (北京时间)\n`),
    nText('会话: ', { bold: true }), nText(`${context.length} 个  |  `),
    nText('消息: ', { bold: true }), nText(`${totalMessages.toLocaleString()} 条  |  `),
    nText('完成率: ', { bold: true }), nText(`${completedCount}/${context.length}`),
  ], '📊', 'blue_background'));

  blocks.push(nDivider());

  // Timeline
  blocks.push(nHeading2('⏱ 时间线'));
  const timelineLines = context.map((s, i) => {
    const t = s.started_at ? new Date(s.started_at).toLocaleTimeString('zh-CN', { timeZone: 'Asia/Shanghai', hour: '2-digit', minute: '2-digit' }) : '??:??';
    const barLen = Math.max(3, Math.min(30, Math.round(s.message_count / 20)));
    const bar = '━'.repeat(barLen);
    const label = s.first_prompt ? s.first_prompt.slice(0, 30) : s.project;
    return `${t} ${bar} ${label} (#${i + 1})`;
  });
  blocks.push(nCodeBlock(timelineLines.join('\n')));

  blocks.push(nDivider());

  // Intent → Output table
  blocks.push(nHeading2('🎯 意图 → 产出'));
  const tableRows = [['#', '意图', 'AI 杠杆', '项目', '消息', '状态']];
  for (let i = 0; i < context.length; i++) {
    const s = context[i];
    const intent = s.first_prompt ? s.first_prompt.slice(0, 25) : 'unknown';
    const tools = Object.keys(s.tools).slice(0, 3).join('+');
    tableRows.push([
      String(i + 1), intent, tools || '-', s.project, String(s.message_count), '✅'
    ]);
  }
  blocks.push(nTable(tableRows));

  blocks.push(nDivider());

  // AI Tool distribution
  blocks.push(nHeading2('🤖 AI 能力分布'));
  const sortedTools = Object.entries(allToolCounts).sort((a, b) => b[1] - a[1]);
  const totalToolCalls = sortedTools.reduce((sum, [, v]) => sum + v, 0);

  // Categorize tools
  const categories = {
    '💻 开发执行': ['Bash', 'Edit', 'Write', 'NotebookEdit'],
    '📖 代码理解': ['Read', 'Grep', 'Glob', 'Task'],
    '🔍 信息检索': ['WebFetch', 'WebSearch', 'mcp__firecrawl__firecrawl_search', 'mcp__firecrawl__firecrawl_scrape', 'mcp__firecrawl__firecrawl_map'],
    '☁️ 云服务': ['mcp__supabase__execute_sql', 'mcp__supabase__apply_migration', 'mcp__supabase__list_tables'],
    '🎨 内容发布': ['mcp__xiaohongshu-mcp__publish_content', 'mcp__xiaohongshu-mcp__search_feeds', 'Skill'],
  };

  const catRows = [['类别', '工具', '次数', '占比']];
  for (const [catName, catTools] of Object.entries(categories)) {
    let catCount = 0;
    const matchedTools = [];
    for (const [tool, count] of sortedTools) {
      if (catTools.some(ct => tool.includes(ct) || tool.startsWith(ct))) {
        catCount += count;
        matchedTools.push(tool.split('__').pop() || tool);
      }
    }
    if (catCount > 0) {
      const pct = totalToolCalls > 0 ? Math.round(catCount / totalToolCalls * 100) : 0;
      catRows.push([catName, matchedTools.slice(0, 3).join('+'), String(catCount), `${pct}%`]);
    }
  }
  if (catRows.length > 1) blocks.push(nTable(catRows));

  blocks.push(nDivider());

  // Session depth
  blocks.push(nHeading2('📐 会话深度'));
  const topSessions = [...context].sort((a, b) => b.message_count - a.message_count).slice(0, 5);
  if (topSessions.length > 0) {
    const depthRows = [['会话', '消息', '项目']];
    for (const s of topSessions) {
      const label = s.first_prompt ? s.first_prompt.slice(0, 20) : s.project;
      depthRows.push([label, String(s.message_count), s.project]);
    }
    blocks.push(nTable(depthRows));
  }

  blocks.push(nDivider());

  // Knowledge tags
  blocks.push(nHeading2('🧠 知识增量'));
  const uniqueTools = [...new Set(sortedTools.slice(0, 8).map(([t]) => t.split('__').pop() || t))];
  blocks.push(nBullet(...uniqueTools.flatMap((t, i) => i > 0 ? [nText(' · '), nText(t, { code: true })] : [nText(t, { code: true })])));

  return blocks;
}

async function createNotionEntry(date, sessions, context, allToolCounts) {
  const blocks = buildNotionBlocks(date, sessions, context, allToolCounts);
  const totalMessages = context.reduce((sum, s) => sum + s.message_count, 0);
  const projects = [...new Set(context.map(s => s.project))];
  const topTools = Object.entries(allToolCounts).sort((a, b) => b[1] - a[1]).slice(0, 3)
    .map(([k, v]) => `${k.split('__').pop() || k}(${v})`).join(', ');

  const body = {
    parent: { type: 'database_id', database_id: AGENT_DB_ID },
    icon: { type: 'emoji', emoji: '📅' },
    properties: {
      'Name': { title: [{ text: { content: `${date} Agent 日报` } }] },
      'Date': { date: { start: date } },
      'Sessions': { number: context.length },
      'Messages': { number: totalMessages },
      'Projects': { rich_text: [{ text: { content: projects.join(', ').slice(0, 200) } }] },
      'Top Tools': { rich_text: [{ text: { content: topTools } }] },
      'Completion': { rich_text: [{ text: { content: `${context.length}/${context.length}` } }] },
      'AI Summary': { rich_text: [{ text: { content: context.map(s => s.first_prompt || '').filter(Boolean).slice(0, 5).join('; ').slice(0, 200) } }] },
    },
    children: blocks.slice(0, 100),
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

// --- Main ---

async function main() {
  // Step 1: Sync
  await syncSessions();

  // Step 2: Get today's sessions
  const sessions = await getTodaySessions(targetDate);
  console.log(`📊 Found ${sessions.length} sessions for ${targetDate}`);

  if (sessions.length === 0) {
    console.log('   No sessions today. Skipping report generation.');
    return;
  }

  // Step 3: Build context
  console.log('📝 Building context from messages...');
  const context = await buildDayContext(sessions);

  // Step 4: Generate AI report
  console.log('🤖 Generating AI summary...');
  const report = await generateReport(targetDate, context);

  console.log('\n' + '='.repeat(60));
  console.log(report);
  console.log('='.repeat(60) + '\n');

  // Step 5: Store to Supabase
  console.log('💾 Storing report to Supabase...');
  await storeReport(targetDate, sessions, report);
  console.log('   ✅ Supabase saved');

  // Step 6: Create Notion entry
  console.log('📒 Creating Notion entry...');
  try {
    const allToolCounts = {};
    for (const s of context) {
      for (const [tool, count] of Object.entries(s.tools)) {
        allToolCounts[tool] = (allToolCounts[tool] || 0) + count;
      }
    }
    const notionUrl = await createNotionEntry(targetDate, sessions, context, allToolCounts);
    console.log(`   ✅ Notion: ${notionUrl}`);
  } catch (e) {
    console.error(`   ⚠️ Notion failed: ${e.message}`);
  }

  console.log('\n✅ All done!\n');
}

main().catch(e => {
  console.error('Fatal error:', e);
  process.exit(1);
});
