#!/usr/bin/env node

/**
 * Create a rich Notion daily report page with tables, callouts, toggles, etc.
 */

const NOTION_KEY = process.env.NOTION_API_KEY;
const PARENT_PAGE_ID = '2e77f9bf-d164-81f3-b4b9-e3e9e4820c66'; // 复盘

// --- Notion block builders ---

function text(content, opts = {}) {
  const t = { type: 'text', text: { content } };
  if (opts.bold) t.annotations = { ...t.annotations, bold: true };
  if (opts.italic) t.annotations = { ...t.annotations, italic: true };
  if (opts.code) t.annotations = { ...t.annotations, code: true };
  if (opts.color) t.annotations = { ...t.annotations, color: opts.color };
  return t;
}

function heading1(content, icon = '') {
  return {
    object: 'block', type: 'heading_1',
    heading_1: { rich_text: [text(icon ? `${icon} ${content}` : content)], is_toggleable: false }
  };
}

function heading2(content, icon = '') {
  return {
    object: 'block', type: 'heading_2',
    heading_2: { rich_text: [text(icon ? `${icon} ${content}` : content)], is_toggleable: false }
  };
}

function heading3(content) {
  return {
    object: 'block', type: 'heading_3',
    heading_3: { rich_text: [text(content)] }
  };
}

function paragraph(...richTexts) {
  return {
    object: 'block', type: 'paragraph',
    paragraph: { rich_text: richTexts }
  };
}

function callout(content, icon = '💡', color = 'blue_background') {
  const richText = typeof content === 'string' ? [text(content)] : content;
  return {
    object: 'block', type: 'callout',
    callout: { rich_text: richText, icon: { type: 'emoji', emoji: icon }, color }
  };
}

function divider() {
  return { object: 'block', type: 'divider', divider: {} };
}

function bullet(...richTexts) {
  return {
    object: 'block', type: 'bulleted_list_item',
    bulleted_list_item: { rich_text: richTexts }
  };
}

function numbered(...richTexts) {
  return {
    object: 'block', type: 'numbered_list_item',
    numbered_list_item: { rich_text: richTexts }
  };
}

function toggle(title, children = []) {
  return {
    object: 'block', type: 'toggle',
    toggle: { rich_text: typeof title === 'string' ? [text(title)] : title, children }
  };
}

function quote(...richTexts) {
  return {
    object: 'block', type: 'quote',
    quote: { rich_text: richTexts }
  };
}

function tableBlock(rows) {
  // rows is array of arrays of strings
  const width = rows[0].length;
  return {
    object: 'block',
    type: 'table',
    table: {
      table_width: width,
      has_column_header: true,
      has_row_header: false,
      children: rows.map(row => ({
        object: 'block',
        type: 'table_row',
        table_row: {
          cells: row.map(cell => [text(String(cell))])
        }
      }))
    }
  };
}

function codeBlock(content, language = 'plain text') {
  return {
    object: 'block', type: 'code',
    code: { rich_text: [text(content)], language }
  };
}

// --- Build the report ---

function buildReportBlocks() {
  const blocks = [];

  // === Header Callout ===
  blocks.push(callout(
    [
      text('时间范围: ', { bold: true }),
      text('2026-01-23 12:13 ~ 2026-01-24 12:13 (北京时间)\n'),
      text('会话数: ', { bold: true }), text('12 个有效会话  |  '),
      text('总消息: ', { bold: true }), text('1,944 条  |  '),
      text('活跃时长: ', { bold: true }), text('~10.7 小时'),
    ],
    '📊', 'blue_background'
  ));

  blocks.push(divider());

  // === 时间线 ===
  blocks.push(heading2('时间线', '⏱'));

  blocks.push(codeBlock(
`16:03 ━━━━━━━━ 健身动作图发XHS (#1-3)
      ┃
16:24 ━━━━━ 复合动作批量发布 (#2)
      ┃
16:39 ━━━━━━━━━━━━━━━━ 复合动作迭代发布 (#3)
      ┃
21:27 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Chrome插件Supabase集成 (#4) [最长]
      ┃
22:06 ━━━━━━━━━━ Manim白板视频 (#5-6)
      ┃
22:17 ━ CLAUDE.md配置 (#7)
      ┃
22:23 ━━━━━━━━━━━━━━━ Prompt逆向+肖像图发XHS (#8)
      ┃
23:53 ━━━━━━━━━━━━━━━━━━━ 大卡流设计研究报告 (#9-10)
      ┃
00:31 ━━━━━━━━━━━━━━ EAS TestFlight部署 (#11)
      ┃
01:16 ━━━━━━ Mac定时任务管理 (#12)
      ┃
02:46 ━ END`, 'plain text'
  ));

  blocks.push(divider());

  // === 意图→产出表 ===
  blocks.push(heading2('意图 → 产出', '🎯'));

  blocks.push(tableBlock([
    ['#', '意图', 'AI 杠杆', '产出物', '消息数', '状态'],
    ['1', '健身复合动作素描发XHS', 'Nanobanana + 小红书API', '小红书图文笔记', '22', '✅'],
    ['2', '批量生成动作图发布', 'Skill循环 + 社媒API', '6张素描 + 笔记', '53', '✅'],
    ['3', '迭代优化动作图发布', '多轮生图 + 发布', '优化版小红书笔记', '65', '✅'],
    ['4', 'Chrome插件集成Supabase', 'Supabase全套 + 代码生成', '完整数据库集成+Edge Function', '537', '✅'],
    ['5', 'Manim库白板讲解视频', 'Firecrawl + FFmpeg + 发布', '3b1b风格动画视频', '284', '✅'],
    ['6', 'Manim原理白板图', 'Firecrawl + Nanobanana', '技术原理图', '24', '✅'],
    ['7', '更新CLAUDE.md方法论', 'Read + Edit', '"三秒法则"认知沉淀', '9', '✅'],
    ['8', 'Prompt逆向+肖像图发XHS', '图像分析 + 生图 + 发布', '多风格肖像图文', '196', '✅'],
    ['9', '大卡流设计趋势研究', 'Web研究 + 报告生成', 'App Store设计分析报告', '347', '✅'],
    ['10', '大卡流研究(并行会话)', '同上(分支)', '补充研究材料', '157', '✅'],
    ['11', 'EAS TestFlight部署', 'Supabase + EAS配置', 'RN App构建配置', '194', '🔄'],
    ['12', 'Mac定时任务管理', 'Bash + cron', 'launchd任务清理', '56', '✅'],
  ]));

  blocks.push(divider());

  // === AI 能力使用 ===
  blocks.push(heading2('AI 能力使用分布', '🤖'));

  blocks.push(callout(
    [text('Top 5 工具: ', { bold: true }), text('Bash(159) → Read(130) → Edit(85) → Write(36) → Firecrawl Search(31)')],
    '🔧', 'gray_background'
  ));

  // 分类表
  blocks.push(heading3('按能力分类'));
  blocks.push(tableBlock([
    ['能力类别', '工具', '调用次数', '占比'],
    ['💻 开发执行', 'Bash + Edit + Write', '280', '52%'],
    ['📖 代码理解', 'Read + Grep + Glob', '143', '27%'],
    ['🔍 信息检索', 'Firecrawl (search+scrape)', '43', '8%'],
    ['☁️ 云服务', 'Supabase (全套)', '32', '6%'],
    ['🎨 内容发布', '小红书 + Skill', '23', '4%'],
    ['🧠 规划协作', 'Task + AskUser + PlanMode', '17', '3%'],
  ]));

  blocks.push(divider());

  // === 会话深度分析 ===
  blocks.push(heading2('会话深度分析', '📐'));

  blocks.push(tableBlock([
    ['会话', '消息数', '用户轮', 'AI轮', '人机比', '时长'],
    ['#4 Chrome+Supabase', '537', '164', '371', '1:2.3', '4.5h'],
    ['#9 大卡流研究', '347', '118', '228', '1:1.9', '3.0h'],
    ['#5 Manim视频', '284', '92', '189', '1:2.1', '1.3h'],
    ['#8 Prompt逆向', '196', '64', '130', '1:2.0', '2.9h'],
    ['#11 TestFlight', '194', '75', '118', '1:1.6', '2.2h'],
    ['#3 动作图迭代', '65', '25', '39', '1:1.6', '3.7h'],
    ['均值', '162', '54', '106', '1:2.0', '—'],
  ]));

  blocks.push(divider());

  // === 效率洞察 ===
  blocks.push(heading2('效率洞察', '💡'));

  blocks.push(callout(
    [text('完成率 11/12 (92%) — 仅 TestFlight 未完全完成')],
    '✅', 'green_background'
  ));

  blocks.push(toggle(
    [text('🔑 关键发现', { bold: true })],
    [
      bullet(text('内容创作流水线已成熟', { bold: true }), text(': 意图→生图→发布 仅需 3-10 分钟/篇')),
      bullet(text('开发类任务 AI 放大比最高', { bold: true }), text(': 人机比 1:2.3，AI 承担了大量代码生成和调试')),
      bullet(text('研究类任务需要多轮迭代', { bold: true }), text(': 大卡流研究开了 2 个并行会话，总 504 条消息')),
      bullet(text('Supabase 工具链使用熟练', { bold: true }), text(': 从建表→部署 Edge Function→安全审计，全链路自动化')),
    ]
  ));

  blocks.push(toggle(
    [text('⚠️ 改进空间', { bold: true })],
    [
      bullet(text('复合动作发XHS 尝试了 3 个会话', { bold: true }), text(' — 说明首次 prompt 描述不够精确')),
      bullet(text('Manim 视频也开了 2 个会话', { bold: true }), text(' — 可考虑在单会话内迭代')),
      bullet(text('最长会话(537条)可能超出了单次最佳协作长度', { bold: true }), text(' — 可拆分为多阶段')),
    ]
  ));

  blocks.push(divider());

  // === 知识增量 ===
  blocks.push(heading2('知识增量', '🧠'));
  blocks.push(
    bullet(text('Manim Community Edition', { code: true }), text(' — 3b1b 风格数学动画库')),
  );
  blocks.push(
    bullet(text('EAS Build + TestFlight', { code: true }), text(' — Expo 应用 iOS 发布全流程')),
  );
  blocks.push(
    bullet(text('Supabase Edge Functions', { code: true }), text(' — Deno 运行时的 Serverless 函数')),
  );
  blocks.push(
    bullet(text('大卡流设计趋势', { code: true }), text(' — App Store Today → 天猫/美团的设计传播路径')),
  );
  blocks.push(
    bullet(text('三秒法则', { code: true }), text(' — 社媒内容 Hook 优先的方法论')),
  );

  blocks.push(divider());

  // === 明日线索 ===
  blocks.push(heading2('明日线索', '🔮'));
  blocks.push(callout(
    [
      text('1. TestFlight 构建完成后需真机测试\n', { bold: false }),
      text('2. Chrome 扩展 Supabase 集成需端到端验证\n'),
      text('3. 大卡流研究报告可发布到小红书\n'),
      text('4. Manim 技能可应用到更多概念可视化'),
    ],
    '📋', 'yellow_background'
  ));

  return blocks;
}

// --- Notion API ---

async function createPage(title, blocks) {
  const body = {
    parent: { type: 'page_id', page_id: PARENT_PAGE_ID },
    icon: { type: 'emoji', emoji: '🤖' },
    properties: {
      title: { title: [{ text: { content: title } }] }
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
    const err = await res.text();
    throw new Error(`Create page failed: ${res.status} ${err}`);
  }

  const data = await res.json();
  const pageId = data.id;

  // Append remaining blocks if > 100
  if (blocks.length > 100) {
    for (let i = 100; i < blocks.length; i += 100) {
      const batch = blocks.slice(i, i + 100);
      const appendRes = await fetch(`https://api.notion.com/v1/blocks/${pageId}/children`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${NOTION_KEY}`,
          'Notion-Version': '2022-06-28',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ children: batch }),
      });
      if (!appendRes.ok) {
        console.error('Append failed:', await appendRes.text());
      }
    }
  }

  return data.url;
}

// --- Main ---
async function main() {
  console.log('🏗  Building report blocks...');
  const blocks = buildReportBlocks();
  console.log(`   ${blocks.length} blocks generated`);

  console.log('📤 Creating Notion page...');
  const url = await createPage('2026-01-23 Agent 日报 (详细版)', blocks);
  console.log(`✅ Done: ${url}`);
}

main().catch(e => { console.error(e); process.exit(1); });
