# Claude Code 全局配置

## 基本信息

- 位置：虹桥国际科技广场，上海市长宁区金钟路999号（121.36, 31.23）
- 公司根目录：`/Users/liuyishou/usr/pac` (Personal AI Company)
- 代理工具：Surge，配置：`/Users/liuyishou/usr/surge.conf`

## 模块化规则

@~/.claude/rules/security.md
@~/.claude/rules/workflow.md
@~/.claude/rules/coding-style.md
@~/.claude/rules/profile.md

## 知识库

**Obsidian 笔记库**：`/Users/liuyishou/usr/odyssey`（3115 篇笔记）

**知识索引**：`~/.claude/knowledge/concepts-index.json`
- 按领域索引用户的知识版图
- expertise_level 表示该领域的笔记深度（aware/learning/proficient/deep）
- 当需要了解用户在某领域的知识积累时，可参考此索引

**深度领域**（可信任用户的判断）：
- CS/人工智能（449 篇）、软件工程（237 篇）、编程语言（211 篇）
- 投资系统（94 篇）、英语学习（76 篇）、数学（133 篇）

**按需检索**：如需查询具体笔记内容，直接读取 Obsidian 库中的文件

## 凭证管理

**IMPORTANT**: 所有 API 密钥存储在 `~/.claude/secrets.env`，不要在代码中硬编码。

加载方式：`source ~/.claude/secrets.env`

## Hook 启动 Agent 规范

**IMPORTANT**: 当 Hook 通过 `spawn` 启动 Claude Agent 子进程时，**必须移除 `ANTHROPIC_API_KEY` 环境变量**，让子进程使用 Pro 订阅认证而非 API key。

**原因**：API key 有独立余额，可能耗尽；Pro 订阅额度更充足且已付费。

**标准写法**：
```javascript
// 移除 ANTHROPIC_API_KEY，让 claude 使用 Pro 订阅认证
const { ANTHROPIC_API_KEY, ...cleanEnv } = process.env;

const child = spawn(CLAUDE_BIN, [...], {
  env: cleanEnv  // 不传 API key
});
```

**错误写法**（禁止）：
```javascript
env: { ...process.env }  // 会传递 API key，可能导致余额不足
```

## 常用路径

| 用途 | 路径 |
|------|------|
| Skills | `~/.claude/skills/` |
| Agents | `~/.claude/agents/` |
| Hooks | `~/.claude/hooks/` |
| Commands | `~/.claude/commands/` |
| Cookies | `~/.claude/douyin_cookies.txt`, `~/.claude/skills/biliup-publish/cookies.json` |

## 账号信息

| 平台 | 账号/说明 |
|------|----------|
| B站 | 转了码的刘公子 |
| X/Twitter | liuysh2 |
| Apple | 876538875@qq.com (Team: 52LKR8ZM8L) |
| EAS | luisleonard |

## Supabase 项目

**IMPORTANT**: 新项目优先使用本地 Supabase 开发，避免污染线上数据库。

### 本地 Supabase（优先）

| 配置 | 值 |
|------|-----|
| API URL | `http://127.0.0.1:54321` |
| Studio | `http://127.0.0.1:54323` |
| DB 端口 | `54322` |
| Anon Key | 见 `~/.claude/secrets.env` 中的 `SUPABASE_LOCAL_ANON_KEY` |

**启动方式**：
```bash
cd ~/usr/pac/infrastructure
npx supabase start
```

**PAC Schema**：`pac` - 公司统一数据存储
- `pac.bu_artifacts` - 各事业部产物索引
- `pac.content_posts` - 内容发布记录
- `pac.investment_trades` - 投资交易记录

**隔离方式**：
- Schema 隔离：不同项目用不同 schema（推荐）
- 表前缀：共用 public schema，用项目名前缀

### 线上 Supabase

| 项目 | Project ID | URL |
|------|------------|-----|
| AI50 | `ebgmmkaxuhawfrwryzia` | `https://ebgmmkaxuhawfrwryzia.supabase.co` |
| PersonalDigitalCenter | `mwvsdfalfqblbqwnyqpn` | `https://mwvsdfalfqblbqwnyqpn.supabase.co` |

## Redis（消息队列）

| 配置 | 值 |
|------|-----|
| 地址 | `127.0.0.1:6379` |
| 配置文件 | `/opt/homebrew/etc/redis.conf` |

**启动**：`brew services start redis`

## Notion 数据库

| 数据库 | ID |
|--------|-----|
| Personal Review | `2f47f9bf-d164-81a2-886f-de01e398ac38` |
| Agent Daily | `2f17f9bf-d164-8191-887c-c4f29c13c673` |
| Browsing Daily | `2f17f9bf-d164-818d-944b-ecd9f922f913` |

## 英语能力

**词汇量**：~14,000 词（CEFR C1 高级）
- 基础词汇：托福 100+ 级别 (13,436 词)
- 额外积累：593 词（不在托福词表中）

**听力语速**：100 WPM（慢速级别）
- 超过此语速的音频会自动减速到目标值
- 减速使用 ffmpeg atempo 滤镜

**数据存储**：AI50 Supabase
- `vocab_levels.toefl-100` - 基础词表
- `user_vocab` - 个人词汇 (1,739 条记录)

**生词判断**：不在 toefl-100 词表 + 不在 user_vocab(known) 中的词

## 公司架构 (Personal AI Company)

```
~/usr/pac/
├── product-bu/      # 产品事业部（代码杠杆）
├── content-bu/      # 内容事业部（媒体杠杆）
├── investment-bu/   # 投资事业部（资本杠杆）
├── infrastructure/  # 基础设施（本地 Supabase）
├── pmo/             # 项目管理办公室
├── archive/         # 归档
└── inbox/           # 临时项目（未分类）
```

### 事业部入口

| 事业部 | 路径 | 职责 |
|--------|------|------|
| 产品 | `~/usr/pac/product-bu` | 将 idea 变为产品 |
| 内容 | `~/usr/pac/content-bu` | 将灵感变为社媒内容 |
| 投资 | `~/usr/pac/investment-bu` | 管理投资，放大资金 |

### 新项目规范

**触发条件**：当 session 涉及以下情况时，询问用户创建项目：
- 需要写大量代码
- 会产生较多数据文件
- 涉及完整的产品/功能开发

**创建位置**：对应事业部的 `inbox/` 目录，必须包含 `sessionInfo.md`：

```markdown
# Session Info

- **Session ID**: <cc session id>
- **Created**: <日期>
- **Purpose**: <项目目的简述>
```
