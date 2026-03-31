# api-linear - Linear API 操作

Linear 项目管理 API 封装，供 PMO 系统调用。

## 配置

- **Workspace**: liugongzi
- **API Key**: `~/.claude/secrets.env` 中的 `LINEAR_API_KEY`
- **API Endpoint**: `https://api.linear.app/graphql`

### 快速链接

| 事业部 | URL |
|--------|-----|
| 产品事业部 | https://linear.app/liugongzi/team/P/all |
| 内容事业部 | https://linear.app/liugongzi/team/C/all |

## 数据映射

### Team（事业部）

| Team | ID | Key | 说明 |
|------|-----|-----|------|
| 产品事业部 | `fcaf8084-612e-43e2-b4e4-fe81ae523627` | P | 面向用户的产品（App、Web、API） |
| 内容事业部 | `4bb065b8-982f-4a44-830d-8d88fe8c9828` | C | 社媒内容（小红书、B站、X） |

**旧 Team（已弃用）**：
| Team | ID | Key |
|------|-----|-----|
| claude code | `3af46304-96f4-4741-814b-3dafc305c1c6` | CLA |
| Liugongzi | `d67458f3-a9de-4a96-b5d0-bc611c8f864d` | LIU |

### Labels

**产品事业部（工作类型）**：

| Label | ID |
|-------|-----|
| 产品思路 | `1ba8f8d3-a567-4b4c-9a66-7073c7830f9b` |
| 设计 | `5bde2dff-0b13-42d9-b0fb-c9481a6c4ca9` |
| 前端 | `cef79327-91d8-40e1-a179-e31ce1cbed45` |
| 后端 | `d2b97270-ad71-4421-af7b-f65e2c125226` |
| 测试 | `08529871-1a70-4724-a690-6790c10c40ef` |
| 发布 | `8a102b53-46c2-4f5a-af09-219dc3e27661` |

**内容事业部（流程阶段）**：

| Label | ID |
|-------|-----|
| 灵感 | `7be8f7f1-b476-4c27-87e4-e4b36fc2e6cb` |
| 做图 | `5a95aaa6-ce9a-4871-81ef-1dcce2bbc3e7` |
| 文案 | `be0f8c2e-7054-490f-84c1-f95212c07ef2` |
| 发布 | `b4fa7209-3d42-4cdb-98c0-ee2742dd647a` |
| 后评估 | `072feefc-4d30-4522-af7d-ba6448ec960f` |

**通用**：

| Label | ID |
|-------|-----|
| Feature | `bef74b1b-1bbc-45ed-822e-03d0ed371d9e` |
| Bug | `5654ba4b-2f92-45cf-8a5e-8742c85a3058` |
| Improvement | `268bd420-934e-4242-990e-8c45b91ac4df` |

### Project 配置

| PMO ID | 项目名 | Linear Project ID | 本地目录 | GitHub |
|--------|--------|-------------------|----------|--------|
| 2 | Viva | `50deb7b2-f67b-4dd4-b7e9-7809dd4229c0` | `/Users/liuyishou/usr/projects/wip/viva` | `liuysh2/viva` |
| - | 待补充 | - | - | - |

**项目属性**：
- `linear_project_id`: Linear 项目 ID
- `local_path`: 本地代码目录
- `github_repo`: GitHub 仓库（owner/repo 格式）
- `description`: 项目描述

## API 调用模板

### 创建 Issue

```bash
curl -s -X POST 'https://api.linear.app/graphql' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: $LINEAR_API_KEY' \
  -d '{"query": "mutation { issueCreate(input: { title: \"$TITLE\", teamId: \"$TEAM_ID\", projectId: \"$PROJECT_ID\", description: \"$DESC\" }) { success issue { id identifier title url } } }"}'
```

### 更新 Issue

```bash
curl -s -X POST 'https://api.linear.app/graphql' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: $LINEAR_API_KEY' \
  -d '{"query": "mutation { issueUpdate(id: \"$ISSUE_ID\", input: { title: \"$TITLE\", description: \"$DESC\", stateId: \"$STATE_ID\" }) { success issue { id identifier title url } } }"}'
```

### 查询 Issue

```bash
curl -s -X POST 'https://api.linear.app/graphql' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: $LINEAR_API_KEY' \
  -d '{"query": "{ issue(id: \"$ISSUE_ID\") { id identifier title description state { name } project { name } } }"}'
```

### 搜索 Issue

```bash
curl -s -X POST 'https://api.linear.app/graphql' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: $LINEAR_API_KEY' \
  -d '{"query": "{ issues(filter: { team: { id: { eq: \"$TEAM_ID\" } }, title: { contains: \"$KEYWORD\" } }) { nodes { id identifier title url } } }"}'
```

### 获取 Projects

```bash
curl -s -X POST 'https://api.linear.app/graphql' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: $LINEAR_API_KEY' \
  -d '{"query": "{ projects { nodes { id name } } }"}'
```

### 获取 Teams

```bash
curl -s -X POST 'https://api.linear.app/graphql' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: $LINEAR_API_KEY' \
  -d '{"query": "{ teams { nodes { id name key } } }"}'
```

### 创建 Project

```bash
curl -s -X POST 'https://api.linear.app/graphql' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: $LINEAR_API_KEY' \
  -d '{"query": "mutation { projectCreate(input: { name: \"$NAME\", teamIds: [\"$TEAM_ID\"] }) { success project { id name } } }"}'
```

### 添加 Attachment（外部链接）

用于内容事业部 Issue 关联小红书/B站链接：

```bash
curl -s -X POST 'https://api.linear.app/graphql' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: $LINEAR_API_KEY' \
  -d '{"query": "mutation { attachmentCreate(input: { issueId: \"$ISSUE_ID\", title: \"小红书笔记\", url: \"$XHS_URL\" }) { success attachment { id title url } } }"}'
```

## Issue Description 模板

### 产品事业部（代码改动）

```markdown
sessionId: {session_id}

## 一、代码分支

| 属性 | 值 |
|------|-----|
| Project | {project_name} |
| Worktree | `{worktree_path}` |
| Branch | `{branch_name}` |
| Base | `main` |

## 二、改动概要

{一句话描述本次改动的目标}

### 涉及文件

- `src/xxx.tsx` - 说明
- `src/yyy.ts` - 说明

### 改动统计

```
 N files changed, +X insertions, -Y deletions
```

## 三、技术决策

{记录关键的技术选型或设计决策}

## 四、相关链接

- Worktree: `file://{worktree_path}`
- GitHub Compare: {compare_url}
```

### 内容事业部（社媒内容）

```markdown
sessionId: {session_id}

## 一、内容信息

| 属性 | 值 |
|------|-----|
| 系列 | {series_name} |
| 平台 | 小红书 / B站 / X |
| 状态 | 灵感 / 做图 / 文案 / 已发布 |

## 二、内容概要

{主题和核心观点}

## 三、素材

- 封面图: `file://{cover_path}`
- 配图: {image_list}

## 四、发布链接

- 小红书: {xhs_url}
- B站: {bilibili_url}
```

## PMO 集成

PMO Hook 分类后，调用此 API 创建/更新 Linear issue。

## 使用场景

1. **Session 追踪**：PMO 分类后自动创建 Linear issue
2. **任务管理**：手动创建/更新 issue
3. **项目查询**：查看项目下的所有 issue
