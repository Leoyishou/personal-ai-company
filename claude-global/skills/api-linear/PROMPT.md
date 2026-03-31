# Linear API Skill

操作 Linear 项目管理系统的统一接口。

## 使用方式

```
/api-linear <action> [options]
```

## 支持的 Action

### 1. create - 创建 Issue

```
/api-linear create --team <team> --title "标题" --description "描述"
```

**参数**：
- `--team`: 事业部名称（product/content/investment/pmo）
- `--title`: Issue 标题
- `--description`: Issue 描述（支持 markdown，会正确处理换行）
- `--project`: （可选）项目名称
- `--labels`: （可选）标签，逗号分隔

### 2. update - 更新 Issue

```
/api-linear update --id <issue-id> --state <state>
/api-linear update --id <issue-id> --append "追加内容"
```

**参数**：
- `--id`: Issue ID 或 identifier（如 P-123）
- `--state`: 状态名称（backlog/todo/in_progress/in_review/done）
- `--append`: 追加到 description 的内容

### 3. search - 搜索 Issue

```
/api-linear search --team <team> --query "关键词"
/api-linear search --session <sessionId>
```

**参数**：
- `--team`: 事业部名称
- `--query`: 搜索关键词
- `--session`: 按 sessionId 搜索

### 4. link-doc - 链接 Document 到 Issue

```
/api-linear link-doc --id <issue-id> --prompt <模板名>
/api-linear link-doc --id C-123 --document <document-id>
```

**参数**：
- `--id`: Issue ID 或 identifier（如 C-123）
- `--prompt`: prompt 模板名称（如「手绘白板」「人物语录」）
- `--document`: Document ID（直接指定）

**用途**：将内容创作使用的 prompt 模板关联到对应的 Issue，便于追踪哪个内容用了哪个模板。

**实现原理**：
1. 根据 prompt 名称或 document ID 查询 Document 的 `title` 和 `url`
2. 使用 `attachmentCreate` API 创建附件链接到 Issue
3. Linear 的 attachment 需要 `title` + `url`，不支持直接用 `documentId`

### 5. doc-create - 创建 Document 并关联到 Issue/Project

```
/api-linear doc-create --title "调研报告" --content "markdown内容" --issue R-5
/api-linear doc-create --title "Session 总结" --content-file /path/to/report.md --project <projectId>
```

**参数**：
- `--title`: （必填）文档标题
- `--content`: 文档内容（Markdown）
- `--content-file`: 从文件读取内容（与 --content 二选一）
- `--issue`: 关联的 Issue ID 或 identifier（如 R-5）
- `--project`: 关联的 Project ID

**用途**：创建独立的 Linear Document 附挂到 Issue，让 Issue description 保持轻量摘要，详细内容作为 Document 独立存在。

### 6. doc-update - 更新已有 Document

```
/api-linear doc-update --id <doc-id> --content "新内容"
/api-linear doc-update --id <doc-id> --content-file /path/to/new-content.md
/api-linear doc-update --id <doc-id> --append "追加内容"
/api-linear doc-update --id <doc-id> --title "新标题"
```

**参数**：
- `--id`: （必填）Document ID
- `--content`: 完整替换文档内容
- `--content-file`: 从文件读取内容完整替换（与 --content 二选一）
- `--append`: 追加内容到文档末尾
- `--title`: 更新文档标题

### 7. list-prompts - 列出所有 prompt 模板

```
/api-linear list-prompts
```

返回所有可用的 prompt 模板名称。

## Team 信息

| 事业部 | Team ID | Key |
|--------|---------|-----|
| product | fcaf8084-612e-43e2-b4e4-fe81ae523627 | P |
| content | 4bb065b8-982f-4a44-830d-8d88fe8c9828 | C |
| pmo | 1e658f17-2cdf-4bdd-82ad-c63e8a7c4ebb | PMO |

## 状态 ID（产品事业部）

| 状态 | ID |
|------|-----|
| backlog | 52220171-86ac-4a6a-83af-24ec12d55f51 |
| todo | d430a64c-e7c1-465b-a086-7fb8397941e1 |
| in_progress | 53054e6e-1ca5-4b0d-b5c2-283ff2841ab4 |
| in_review | d8125aeb-6451-4da7-971c-b24581025d2a |
| ready_for_qa | db66771b-185b-464e-beb1-dd11d54f44f9 |
| ready_for_release | 177fe624-d3a6-4378-b3a3-b5b7a4246a7a |
| done | 05f950b5-1121-44e2-b60c-cdf923df4b28 |

## 内容事业部 Labels

| Label | ID | 颜色 |
|-------|-----|------|
| 灵感 | `7be8f7f1-b476-4c27-87e4-e4b36fc2e6cb` | 橙色 |
| 做图 | `5a95aaa6-ce9a-4871-81ef-1dcce2bbc3e7` | 黄色 |
| 文案 | `be0f8c2e-7054-490f-84c1-f95212c07ef2` | 紫色 |
| 发布 | `b4fa7209-3d42-4cdb-98c0-ee2742dd647a` | 绿色 |
| 后评估 | `072feefc-4d30-4522-af7d-ba6448ec960f` | 蓝色 |

**使用场景**：
- 小红书发布上报时，自动添加「发布」标签
- 创建灵感 Issue 时添加「灵感」标签
- 支持多个 label，用逗号分隔 ID

## Prompt 模板（内容事业部）

这些模板是 `api-draw` 的画图风格模板，已同步为 Linear Documents。

| 模板名 | 说明 |
|--------|------|
| 手绘白板 | 手绘风格白板图 |
| 人物语录 | 名人名言配图 |
| 学霸笔记 | 笔记风格 |
| 思维导图 | 思维导图 |
| 技术对比 | 技术方案对比 |
| 信息图表 | 信息可视化 |
| 时间线 | 时间轴 |
| 知识卡片 | 知识点卡片 |
| 对话框 | 对话场景 |
| 数据可视化 | 数据图表 |
| 代码展示 | 代码高亮 |
| 金句 | 金句配图 |

## 实现说明

使用 `~/.claude/skills/api-linear/linear-cli.js` 脚本执行操作。

**关键实现细节**：
- 通过文件传递 JSON payload（`curl -d @file`），正确处理 markdown 换行符
- Linear API 的 `attachmentCreate` 需要 `title` + `url`，不能直接传 `documentId`
- 链接 Document 时，先查询 Document 获取其 title 和 url，再创建 attachment

## 示例

```bash
# 创建内容事业部 Issue
node ~/.claude/skills/api-linear/linear-cli.js create \
  --team content \
  --title "【0204-16】小红书：AI 深度调研" \
  --description "sessionId: xxx\n\n## 发布信息\n- 标题: xxx"

# 更新状态
node ~/.claude/skills/api-linear/linear-cli.js update --id P-123 --state in_progress

# 追加内容
node ~/.claude/skills/api-linear/linear-cli.js update --id P-123 --append "## 2024-02-04 进展\n- 完成了 xxx"

# 搜索
node ~/.claude/skills/api-linear/linear-cli.js search --session abc-123-def

# 链接 prompt 模板到 Issue
node ~/.claude/skills/api-linear/linear-cli.js link-doc --id C-11 --prompt "手绘白板"

# 列出所有可用模板
node ~/.claude/skills/api-linear/linear-cli.js list-prompts

# 创建 Document 关联到 Issue
node ~/.claude/skills/api-linear/linear-cli.js doc-create \
  --title "调研报告：DuckDB vs PostgreSQL" \
  --content "## 核心发现\n1. DuckDB 在 OLAP 场景下快 10x..." \
  --issue R-5

# 从文件创建 Document
node ~/.claude/skills/api-linear/linear-cli.js doc-create \
  --title "Session 总结" \
  --content-file /tmp/session-summary.md \
  --issue P-123

# 更新 Document 内容
node ~/.claude/skills/api-linear/linear-cli.js doc-update \
  --id <doc-id> \
  --content "完整替换的新内容..."

# 追加内容到 Document
node ~/.claude/skills/api-linear/linear-cli.js doc-update \
  --id <doc-id> \
  --append "## 追加的新章节\n- 新发现..."
```
