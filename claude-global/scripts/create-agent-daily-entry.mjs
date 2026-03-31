#!/usr/bin/env node

const NOTION_KEY = process.env.NOTION_API_KEY;
const AGENT_DB_ID = '2f17f9bf-d164-8191-887c-c4f29c13c673';

function text(content, opts = {}) {
  const t = { type: 'text', text: { content } };
  const annotations = {};
  if (opts.bold) annotations.bold = true;
  if (opts.italic) annotations.italic = true;
  if (opts.code) annotations.code = true;
  if (Object.keys(annotations).length) t.annotations = annotations;
  return t;
}

function heading2(content) {
  return { object: 'block', type: 'heading_2', heading_2: { rich_text: [text(content)] } };
}

function callout(content, icon = '💡', color = 'blue_background') {
  const richText = typeof content === 'string' ? [text(content)] : content;
  return { object: 'block', type: 'callout', callout: { rich_text: richText, icon: { type: 'emoji', emoji: icon }, color } };
}

function divider() { return { object: 'block', type: 'divider', divider: {} }; }

function bullet(...richTexts) {
  return { object: 'block', type: 'bulleted_list_item', bulleted_list_item: { rich_text: richTexts } };
}

function toggle(title, children = []) {
  return { object: 'block', type: 'toggle', toggle: { rich_text: typeof title === 'string' ? [text(title)] : title, children } };
}

function tableBlock(rows) {
  const width = rows[0].length;
  return {
    object: 'block', type: 'table',
    table: { table_width: width, has_column_header: true, has_row_header: false,
      children: rows.map(row => ({
        object: 'block', type: 'table_row',
        table_row: { cells: row.map(cell => [text(String(cell))]) }
      }))
    }
  };
}

function codeBlock(content, language = 'plain text') {
  return { object: 'block', type: 'code', code: { rich_text: [text(content)], language } };
}

function buildBlocks() {
  const blocks = [];

  blocks.push(callout([
    text('时间: ', { bold: true }), text('2026-01-23 16:03 ~ 2026-01-24 02:46 (北京时间)\n'),
    text('会话: ', { bold: true }), text('12 个  |  '),
    text('消息: ', { bold: true }), text('1,944 条  |  '),
    text('活跃: ', { bold: true }), text('~10.7h  |  '),
    text('完成率: ', { bold: true }), text('92%'),
  ], '📊', 'blue_background'));

  blocks.push(divider());
  blocks.push(heading2('⏱ 时间线'));
  blocks.push(codeBlock(
`16:03 ━━━━━━━━ 健身动作图发XHS (#1-3)
16:24 ━━━━━ 复合动作批量发布 (#2)
16:39 ━━━━━━━━━━━━━━━━ 复合动作迭代发布 (#3)
21:27 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Chrome插件Supabase集成 (#4) [最长]
22:06 ━━━━━━━━━━ Manim白板视频 (#5-6)
22:17 ━ CLAUDE.md配置 (#7)
22:23 ━━━━━━━━━━━━━━━ Prompt逆向+肖像图发XHS (#8)
23:53 ━━━━━━━━━━━━━━━━━━━ 大卡流设计研究报告 (#9-10)
00:31 ━━━━━━━━━━━━━━ EAS TestFlight部署 (#11)
01:16 ━━━━━━ Mac定时任务管理 (#12)
02:46 ━ END`));

  blocks.push(divider());
  blocks.push(heading2('🎯 意图 → 产出'));
  blocks.push(tableBlock([
    ['#', '意图', 'AI 杠杆', '产出物', '消息', '状态'],
    ['1', '健身复合动作素描发XHS', 'Nanobanana+小红书API', '图文笔记', '22', '✅'],
    ['2', '批量生成动作图发布', 'Skill循环+社媒API', '6张素描+笔记', '53', '✅'],
    ['3', '迭代优化动作图发布', '多轮生图+发布', '优化版笔记', '65', '✅'],
    ['4', 'Chrome插件集成Supabase', 'Supabase全套+代码生成', 'DB集成+Edge Fn', '537', '✅'],
    ['5', 'Manim库白板讲解视频', 'Firecrawl+FFmpeg+发布', '3b1b风格动画', '284', '✅'],
    ['6', 'Manim原理白板图', 'Firecrawl+Nanobanana', '技术原理图', '24', '✅'],
    ['7', '更新CLAUDE.md方法论', 'Read+Edit', '"三秒法则"沉淀', '9', '✅'],
    ['8', 'Prompt逆向+肖像图', '图像分析+生图+发布', '多风格肖像图文', '196', '✅'],
    ['9', '大卡流设计趋势研究', 'Web研究+报告生成', '设计分析报告', '347', '✅'],
    ['10', '大卡流研究(并行)', '同上(分支)', '补充材料', '157', '✅'],
    ['11', 'EAS TestFlight部署', 'Supabase+EAS配置', 'RN App构建', '194', '🔄'],
    ['12', 'Mac定时任务管理', 'Bash+cron', 'launchd清理', '56', '✅'],
  ]));

  blocks.push(divider());
  blocks.push(heading2('🤖 AI 能力分布'));
  blocks.push(tableBlock([
    ['类别', '工具', '次数', '占比'],
    ['💻 开发执行', 'Bash+Edit+Write', '280', '52%'],
    ['📖 代码理解', 'Read+Grep+Glob', '143', '27%'],
    ['🔍 信息检索', 'Firecrawl', '43', '8%'],
    ['☁️ 云服务', 'Supabase', '32', '6%'],
    ['🎨 内容发布', '小红书+Skill', '23', '4%'],
    ['🧠 规划协作', 'Task+AskUser+Plan', '17', '3%'],
  ]));

  blocks.push(divider());
  blocks.push(heading2('📐 会话深度'));
  blocks.push(tableBlock([
    ['会话', '消息', '人机比', '时长'],
    ['#4 Chrome+Supabase', '537', '1:2.3', '4.5h'],
    ['#9 大卡流研究', '347', '1:1.9', '3.0h'],
    ['#5 Manim视频', '284', '1:2.1', '1.3h'],
    ['#8 Prompt逆向', '196', '1:2.0', '2.9h'],
    ['#11 TestFlight', '194', '1:1.6', '2.2h'],
  ]));

  blocks.push(divider());
  blocks.push(heading2('💡 洞察'));
  blocks.push(toggle([text('🔑 关键发现', { bold: true })], [
    bullet(text('内容创作流水线成熟', { bold: true }), text(': 意图→生图→发布 仅 3-10 分钟')),
    bullet(text('开发类 AI 放大比最高', { bold: true }), text(': 人机比 1:2.3')),
    bullet(text('Supabase 全链路自动化', { bold: true }), text(': 建表→Edge Function→安全审计')),
  ]));
  blocks.push(toggle([text('⚠️ 改进空间', { bold: true })], [
    bullet(text('健身图发了3个session — prompt 首次描述不够精确')),
    bullet(text('最长会话537条 — 可拆分为多阶段')),
  ]));

  blocks.push(divider());
  blocks.push(heading2('🧠 知识增量'));
  blocks.push(bullet(
    text('Manim CE', { code: true }), text(' · '),
    text('EAS+TestFlight', { code: true }), text(' · '),
    text('Edge Functions', { code: true }), text(' · '),
    text('大卡流设计', { code: true }), text(' · '),
    text('三秒法则', { code: true })
  ));

  blocks.push(divider());
  blocks.push(heading2('🔮 明日线索'));
  blocks.push(callout(
    '1. TestFlight 真机测试\n2. Chrome 扩展端到端验证\n3. 大卡流报告可发XHS\n4. Manim应用更多概念',
    '📋', 'yellow_background'
  ));

  return blocks;
}

async function main() {
  const blocks = buildBlocks();
  console.log(`Built ${blocks.length} blocks`);

  const body = {
    parent: { type: 'database_id', database_id: AGENT_DB_ID },
    icon: { type: 'emoji', emoji: '📅' },
    properties: {
      'Name': { title: [{ text: { content: '2026-01-23 Agent 日报' } }] },
      'Date': { date: { start: '2026-01-23' } },
      'Sessions': { number: 12 },
      'Messages': { number: 1944 },
      'Projects': { rich_text: [{ text: { content: '口播剪映模板, vocab-highlighter' } }] },
      'Top Tools': { rich_text: [{ text: { content: 'Bash(159), Read(130), Edit(85)' } }] },
      'Completion': { rich_text: [{ text: { content: '11/12 (92%)' } }] },
      'AI Summary': { rich_text: [{ text: { content: '内容创作(XHS发帖x6) + 开发(Chrome插件Supabase集成) + 研究(大卡流趋势) + 学习(Manim视频)' } }] },
    },
    children: blocks,
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
    console.error('Error:', res.status, await res.text());
    process.exit(1);
  }

  const data = await res.json();
  console.log('✅ Entry created:', data.url);
}

main();
