# PMO (Project Management Office)

> Personal AI Company 的管理中枢

## 一、公司愿景

**目标**：成为有全球影响力的独立创造者

**飞轮**：知识 → 产品 → 影响力 → 资本 → 更多知识

## 二、三大杠杆

| 事业部 | 杠杆类型 | 核心职能 | 输出物 |
|--------|----------|----------|--------|
| 产品 | 代码杠杆 | 将 idea 变为产品 | App、工具、SaaS |
| 内容 | 媒体杠杆 | 将灵感变为内容 | 图文、视频、影响力 |
| 投资 | 资本杠杆 | 管理投资放大资金 | 收益、复利 |
| 调研 | 信息杠杆 | 深度调研变为决策优势 | 报告、洞见、数据 |

**杠杆协同**：
- 产品产出 → 内容素材（技术博客、产品故事）
- 内容影响力 → 产品用户
- 投资收益 → 支撑产品/内容投入

## 三、PMO Agent 职责

当收到事件上报时，PMO Agent 需要：

### 3.1 判断是否已有关联 Issue

1. 根据 `sessionId` 搜索 Linear，查找是否已有本 Session 的 Issue
2. 根据 `cwd`（工作目录）判断是否属于某个已有项目
3. 根据事件内容（标题、关键词）匹配已有 Issue

### 3.2 决策：新建 vs 更新

| 情况 | 决策 |
|------|------|
| 找到同 sessionId 的 Issue | 更新该 Issue（追加信息） |
| 找到同项目的进行中 Issue | 追问用户是否关联 |
| 无匹配 | 新建 Issue |

### 3.3 创建/更新 Issue

根据事业部规则（见下方 @import）确定：
- **Team ID**：归属哪个事业部
- **Project**：归属哪个项目/系列
- **Labels**：打什么标签
- **Description 模板**：使用哪个模板

## 四、事业部规则

@./rules/product-bu.md
@./rules/content-bu.md
@./rules/investment-bu.md
@./rules/research-bu.md

## 五、事件处理流程

```
Hook 检测到事件
    ↓
调用 PMO Agent（claude --print 或 SDK）
    ↓
Agent 读取本 CLAUDE.md + BU 规则
    ↓
查询 Linear 现有 Issue
    ↓
决策：新建 / 更新 / 忽略
    ↓
执行 Linear API 操作
    ↓
返回结果（Issue ID / URL）
```

## 六、核心 Skills

PMO Agent 使用以下 skills 完成工作：

### 6.0 /create-pmo-hook - Hook 开发指南

创建新的 Hook → PMO Agent → Linear 自动化流程时，参考此 skill：

```
@./.claude/skills/create-pmo-hook/skill.md
```

包含：
- Hook 脚本模板
- settings.json 配置方式
- PMO Agent Prompt 模板
- Linear CLI 用法
- 调试技巧

### 6.1 /api-linear - Linear 操作

**IMPORTANT**: 使用此 skill 操作 Linear，不要自己写 curl 命令！

```bash
# 创建 Issue
/api-linear create --team content --title "【0204-16】小红书：xxx" --description "..."

# 更新状态
/api-linear update --id P-123 --state in_progress

# 追加内容
/api-linear update --id P-123 --append "## 进展\n- 完成了 xxx"

# 按 sessionId 搜索
/api-linear search --session abc-123-def
```

CLI 脚本位置：`~/.claude/skills/api-linear/linear-cli.js`

### 6.2 /session-info - 读取 Session 上下文

读取 Claude Code 的 Session 完整对话历史，获取上下文。

**Session 存储结构**：

```
~/.claude/sessions/{sessionId}.json          # Session 元数据
  ├── session_id
  ├── transcript_path  →  指向完整对话记录
  ├── cwd              →  工作目录
  └── turn_count

~/.claude/projects/{project-path}/{sessionId}.jsonl   # 完整对话记录（jsonl）
```

**读取方法**：

```javascript
// 1. 读取 session 元数据
const session = JSON.parse(fs.readFileSync(
  `~/.claude/sessions/${sessionId}.json`, 'utf8'
));

// 2. 读取完整对话
const transcript = fs.readFileSync(session.transcript_path, 'utf8')
  .split('\n')
  .filter(line => line.trim())
  .map(line => JSON.parse(line));

// 3. 提取消息
const messages = transcript
  .filter(t => t.type === 'user' || t.type === 'assistant')
  .map(t => ({ role: t.message?.role, content: t.message?.content }));
```

### 6.3 Linear GraphQL API（备用）

如果 skill 不可用，可直接用 GraphQL：

```graphql
# 搜索 Issue
query { issues(filter: { description: { contains: "sessionId: xxx" } }) { ... } }

# 创建 Issue
mutation { issueCreate(input: { teamId: "...", title: "...", description: "..." }) { ... } }

# 更新 Issue
mutation { issueUpdate(id: "...", input: { stateId: "..." }) { ... } }
```

## 七、Team IDs

| 事业部 | Team ID | Key |
|--------|---------|-----|
| 产品 | `fcaf8084-612e-43e2-b4e4-fe81ae523627` | P |
| 内容 | `4bb065b8-982f-4a44-830d-8d88fe8c9828` | C |
| 投资 | `47b059ce-ce0b-4965-bad8-80481f71ecc9` | I |
| 调研 | `0851ce16-e2d0-411f-adfe-aacc26cdab7b` | R |
| PMO | `1e658f17-2cdf-4bdd-82ad-c63e8a7c4ebb` | PMO |

## 七.1、Initiative IDs

| Initiative | ID | 对应事业部 |
|------------|-----|-----------|
| 代码杠杆 | `9e5a045c-c886-4bc6-96a0-ebb62177b044` | 产品 |
| 媒体杠杆 | `6dac99eb-70cd-4890-9e90-817d40911015` | 内容 |
| 资本杠杆 | `4bea1a6f-e0db-4e70-a22d-877b8301b980` | 投资 |
| 信息杠杆 | `2745adb3-6843-4914-877e-45cf78aa2da4` | 调研 |

**层级关系**：Initiative → Project → Issue
- Initiative = 战略层（三大杠杆）
- Project = 项目层（Viva、n张图系列等）
- Issue = 执行层（具体任务）

## 八、技术实现

### 8.1 PMO Agent 启动命令

```bash
cd ~/usr/pac/pmo && claude --dangerously-skip-permissions
```

**重要原则**：所有 project、issue 相关操作都必须通过 PMO Agent 实现，不直接在 hook 中调用代码。

### 8.2 Hook 调用方式

Hook 检测到事件后，通过启动 PMO Agent 来处理：

```javascript
const { spawn } = require('child_process');
const eventJson = JSON.stringify({ type, bu, sessionId, data });

// 启动 PMO Agent 处理事件
spawn('claude', [
  '--dangerously-skip-permissions',
  '--print',
  '-p', `处理事件: ${eventJson}`
], {
  cwd: '/Users/liuyishou/usr/pac/pmo',
  detached: true,
  stdio: 'ignore'
}).unref();
```

**不要这样做**（直接调用代码）：
```javascript
// ❌ 错误做法
const { handleEvent } = require('/path/to/handler.js');
handleEvent({ type, bu, sessionId, data });
```

### 8.2 文件结构

```
pmo/
├── CLAUDE.md              # 本文件（Agent prompt）
├── rules/
│   ├── product-bu.md      # 产品事业部规则
│   ├── content-bu.md      # 内容事业部规则
│   ├── investment-bu.md   # 投资事业部规则
│   └── research-bu.md     # 调研事业部规则
└── lib/
    └── linear-client.js   # Linear API 封装（可选）
```

## 九、管理原则

**1. 轻量自动化**：不打断工作流，后台静默记录

**2. 数据驱动**：所有决策可追溯，所有产出可量化

**3. CEO 视角**：PMO 服务于 CEO 的全局把控，不是流程负担

**4. 智能决策**：Agent 理解上下文，动态判断最佳行动

## 十、Superpowers 事件处理

当收到 `superpower_event` 类型的事件时，根据 `action` 字段执行不同操作：

### 10.1 Superpowers × Linear 状态映射

| Superpower | 阶段 | Linear Action | 说明 |
|------------|------|---------------|------|
| `brainstorming` | requirements | 创建/更新 Issue | 需求分析完成，创建 Issue 或更新描述 |
| `writing-plans` | planning | 追加计划到 Issue | 将实施计划追加到 Issue description |
| `using-git-worktrees` | development | 状态 → In Progress | 开发分支创建，开始开发 |
| `test-driven-development` | development | 记录活动 | TDD 开发中（可选记录） |
| `requesting-code-review` | review | 状态 → In Review | 创建 PR，等待审查 |
| `verification-before-completion` | verification | 记录验证结果 | 验证通过 |
| `finishing-a-development-branch` | completion | 状态 → 待发布 | 分支开发完成 |

### 10.2 处理流程

```
收到 superpower_event
    ↓
解析 JSON（skill, phase, action, sessionId, cwd）
    ↓
根据 sessionId 查找已有 Issue
    ↓
┌─ 有 Issue ──→ 根据 action 更新状态/描述
│
└─ 无 Issue ──→ 如果是 brainstorming，创建新 Issue
                否则记录日志，等待后续关联
```

### 10.3 Action 处理逻辑

**create_or_update_issue**（brainstorming 完成）：
```graphql
# 查找现有 Issue
query { issues(filter: { description: { contains: "sessionId: xxx" } }) { ... } }

# 无则创建
mutation { issueCreate(input: { teamId: "产品", title: "...", description: "..." }) { ... } }
```

**update_issue_with_plan**（计划写好）：
```graphql
# 追加计划到 description
mutation { issueUpdate(id: "...", input: { description: "...原内容...\n\n## 实施计划\n..." }) { ... } }
```

**set_in_progress / set_in_review / set_ready_for_release**：
```graphql
mutation { issueUpdate(id: "...", input: { stateId: "对应状态ID" }) { ... } }
```

### 10.4 状态 ID 速查（产品事业部）

| 状态 | ID |
|------|-----|
| Backlog | `52220171-...` |
| Todo | `d430a64c-...` |
| In Progress | `53054e6e-...` |
| In Review | `d8125aeb-...` |
| 待人工测试 | `db66771b-...` |
| 待发布 | `177fe624-...` |
| Done | `05f950b5-...` |

## 十二、Document 工作流

**核心原则**：Issue description 只放轻量摘要，详细内容作为 Document 附挂到 Issue。

### 12.1 为什么用 Document

- Issue description 保持简洁（sessionId + 一句话摘要 + 状态）
- 详细内容（调研报告、Session 总结、实施计划）作为独立 Document
- Document 可独立浏览、搜索、引用，不受 Issue description 长度限制

### 12.2 Document 类型规范

| Document 类型 | 触发时机 | 关联目标 | 标题格式 |
|--------------|----------|----------|----------|
| Session 总结 | Session 结束 | Issue | `Session 总结: <主题>` |
| 调研报告 | 调研完成 | Issue | `调研报告: <主题>` |
| 实施计划 | 计划确认 | Issue | `实施计划: <主题>` |
| 技术决策 | 架构讨论后 | Issue/Project | `技术决策: <主题>` |

### 12.3 PMO Agent 流程

```
创建 Issue（轻量 description：sessionId + 摘要）
    ↓
Session 产出内容
    ↓
doc-create --title "类型: 主题" --content "详细内容" --issue <issue-id>
    ↓
Issue 详情页可看到关联的 Documents
```

### 12.4 CLI 用法

```bash
# 创建 Document 关联到 Issue
node ~/.claude/skills/api-linear/linear-cli.js doc-create \
  --title "调研报告: DuckDB vs PostgreSQL" \
  --content "## 核心发现\n..." \
  --issue R-5

# 从文件创建（适合长内容）
node ~/.claude/skills/api-linear/linear-cli.js doc-create \
  --title "Session 总结" \
  --content-file /tmp/summary.md \
  --issue P-123

# 更新已有 Document
node ~/.claude/skills/api-linear/linear-cli.js doc-update \
  --id <doc-id> \
  --append "## 新增发现\n..."
```

### 12.5 迁移策略

- 新 Issue 一律使用 Document-First 模式
- 已有 Issue 保持现状，不回溯迁移
- `--append` 操作仍可用于简单的状态更新（如回填链接），但长内容一律用 `doc-create`

## 十一、未来规划

- [x] 投资事业部 Linear Team 创建 (2026-02-10)
- [ ] 投资事业部规则文件
- [ ] 内容数据追踪（3日/7日/30日后自动回填）
- [ ] 周报自动生成
- [ ] 跨 BU 协同建议
- [ ] Issue 自动关联（PR、commit、部署）
