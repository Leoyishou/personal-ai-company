# PMO 项目归类规则 - 产品事业部

## 一、核心概念

### 1.1 Session 与 Issue 的关系

```
1 个本地 Session = 1 或 n 个 Linear Issue
```

- 每个 Issue 的 description 必须包含 `sessionId: <session_id>`
- 同一 Session 可能产出多个 Issue（如：做完设计又写代码）

### 1.2 事业部信息

| 字段 | 值 |
|------|-----|
| Team ID | `fcaf8084-612e-43e2-b4e4-fe81ae523627` |
| Key | P |
| 说明 | 面向用户的产品 |

## 二、Project = 用户产品

- `Viva` - 英语学习 App
- `Vocab Highlighter` - 浏览器插件
- `投资 Dashboard` - 持仓追踪工具

**IMPORTANT**: 每个产品项目必须绑定对应的 GitHub 仓库作为 Resource Link。

```graphql
# 添加 GitHub 链接到项目
mutation {
  entityExternalLinkCreate(input: {
    url: "https://github.com/Leoyishou/<repo-name>",
    label: "GitHub",
    projectId: "<project-id>"
  }) { success }
}
```

## 三、Labels

### 3.1 工作类型

| Label | 说明 |
|-------|------|
| 产品思路 | 需求分析、功能规划 |
| 设计 | UI/UX 设计、原型图 |
| 前端 | 前端开发 |
| 后端 | 后端开发 |
| 测试 | 测试 |
| 发布 | 构建、部署上线 |
| 上架 | App Store / Play Store 元数据填写、截图上传、提交审核 |

### 3.2 端类型（可选）

| Label | 说明 |
|-------|------|
| App端 | iOS/Android App |
| 插件端 | 浏览器插件（Vocab Highlighter）|
| Web端 | Web 应用 |

**可多选**：一个 Issue 可以同时有 `前端` + `App端` + `发布`

## 四、Issue 创建规范

### 4.1 必填字段

```graphql
issueCreate(input: {
  title: "任务标题",
  teamId: "fcaf8084-612e-43e2-b4e4-fe81ae523627",
  projectId: "项目ID",
  description: "sessionId: xxx\n\n任务描述",
  labelIds: ["label1", "label2"]
})
```

### 4.2 Description 模板（轻量摘要）

```markdown
sessionId: <session_id>

## 摘要
<一句话描述做什么>

## Git 信息
- Branch: `feat/P-xx-description`
- PR: （待创建）
```

### 4.3 Document: 实施计划/技术决策

通过 `doc-create --issue P-xx` 创建，详细内容独立存放：

```markdown
## 任务描述
<具体要做什么>

## 技术方案
<选型、架构决策>

## 测试要求
- [ ] 自动化测试
- [ ] GUI 测试（如需人工）

## 相关链接
- 本地目录: file:///path/to/project
- Worktree: `~/usr/projects/worktrees/{project}/P-xx`
- GitHub: https://github.com/xxx
```

## 五、触发与归类

### 5.1 触发时机

PMO Classify Hook 在以下操作时自动触发：
- 代码改动（Write/Edit）→ 产品事业部

### 5.2 归类流程

1. **匹配 Project**：根据关键词匹配已有 Project
2. **选择 Labels**：根据具体工作内容打 Label
3. **创建 Issue**：提交到产品事业部 Team

### 5.3 Project 匹配规则

**匹配逻辑**：
1. 从 Session 上下文提取关键词（cwd 路径、用户消息、工具调用参数）
2. 与已有 Project 的 keywords 匹配
3. 计算匹配度：高（>0.8）、中（0.5-0.8）、低（<0.5）

**匹配结果处理**：

| 匹配度 | 行为 |
|--------|------|
| 高 | 自动关联，静默处理 |
| 中 | 用 AskUserQuestion 确认 |
| 低/无 | 用 AskUserQuestion 让用户选择或新建 |

## 六、项目名单

**数据源**：`~/.claude/knowledge/projects.json`

| ID | 项目名 | Linear Project ID | 关键词 |
|----|--------|-------------------|--------|
| 2 | Viva | `50deb7b2-f67b-4dd4-b7e9-7809dd4229c0` | viva, 英语, 词汇, vocab, 听力, 学习app |
| 3 | Vocab Highlighter | - | highlighter, 高亮, 插件, 浏览器 |
| 1 | CC Mission Control | - | dashboard, 任务流, pmo, 可视化 |
| 4 | 投资 Dashboard | - | 投资, 持仓, 股票, portfolio, 收益 |
| 5 | 知识库产品 | - | 知识库, obsidian, 笔记, 变现 |

## 七、工作流状态

### 7.1 状态流转

```
Backlog → Todo → In Progress → In Review → 待人工测试 → 待发布 → Done
                      ↓              ↓           ↓
                  Canceled       Canceled    Canceled
```

| 状态 | 状态 ID | 说明 | 触发条件 |
|------|---------|------|----------|
| Backlog | `52220171-...` | 待规划 | 新建 Issue |
| Todo | `d430a64c-...` | 待开始 | 排入迭代 |
| In Progress | `53054e6e-...` | 开发中 | 创建 branch |
| In Review | `d8125aeb-...` | 代码审查 | 创建 PR |
| 待人工测试 | `db66771b-...` | 等待人工测试 | PR 合并 + 有 GUI 标签 |
| 待发布 | `177fe624-...` | 等待发布 | 测试通过 |
| Done | `05f950b5-...` | 已完成 | 发布成功 |

### 7.2 测试相关标签

| 标签 | 标签 ID | 说明 |
|------|---------|------|
| 需人工测试 | `b991ec74-...` | 包含 AI 无法验证的功能 |
| GUI测试 | `84771a94-...` | 涉及 UI 交互需人眼验证 |
| 自动化测试 | `8c6aff25-...` | 可由 CI 自动验证 |

### 7.3 测试流程判断

当 Issue 包含以下特征时，自动添加「需人工测试」标签：
- 标签包含 `App端` 或 `Web端`
- 涉及 UI 组件改动
- 涉及用户交互流程
- 涉及视觉样式调整

## 八、Git + Linear 集成

### 8.1 Branch 命名规范

```
{type}/{issue-key}-{short-description}
```

**示例**：
- `feat/P-15-viva-splash-screen`
- `fix/P-16-audio-background-play`
- `refactor/P-11-session-analysis`

**Type 类型**：
- `feat` - 新功能
- `fix` - Bug 修复
- `refactor` - 重构
- `docs` - 文档
- `test` - 测试
- `chore` - 杂项

### 8.2 Git Worktree 管理

**基础路径**：`~/usr/projects/worktrees`

**命名规范**：`{project}/{issue-key}`

**示例**：
```bash
# 为 Viva P-15 创建 worktree
cd ~/usr/projects/wip/viva
git worktree add ~/usr/projects/worktrees/viva/P-15 -b feat/P-15-viva-splash-screen
```

### 8.3 Commit Message 规范

```
{type}({scope}): {description} [{issue-key}]
```

**示例**：
- `feat(splash): add animated logo [P-15]`
- `fix(audio): enable background playback [P-16]`

Linear 会自动将 commit 关联到对应 Issue。

### 8.4 PR 与状态自动化

**GitHub Integration 自动触发**：

| 事件 | Linear 状态变更 |
|------|----------------|
| 创建 branch（含 issue key）| → In Progress |
| 创建 PR | → In Review |
| PR 合并 | → 待人工测试（如有 GUI 标签）或 待发布 |
| Release/Deploy | → Done |

**PR 模板**：
```markdown
## Summary
[{issue-key}] {description}

Fixes LIN-{issue-number}

## Test Plan
- [ ] 自动化测试通过
- [ ] GUI 测试项（如有）：
  - [ ] xxx 页面显示正常
  - [ ] xxx 交互流程正常

## Screenshots
（如涉及 UI 变更）
```

## 九、状态流转自动化

### 9.1 Claude Code 触发点

| 操作 | Linear 更新 |
|------|------------|
| 创建 branch 时 | 更新 Issue 状态为 In Progress |
| 创建 PR 时 | 更新 Issue 状态为 In Review |
| PR 合并时 | 判断标签，更新为「待人工测试」或「待发布」|
| `/deploy` 成功时 | 更新 Issue 状态为 Done |

### 9.2 判断是否需人工测试

```python
def needs_manual_test(issue):
    gui_labels = ['App端', 'Web端', '插件端', 'GUI测试', '需人工测试']
    return any(label in issue.labels for label in gui_labels)
```

## 十、Session 总结模板

Session 结束时，通过 `doc-create --issue P-xx` 创建 Document（而非追加到 description）：

**Document 标题**：`Session 总结: <功能主题>`

```markdown
## 完成内容
- 功能：<做了什么>
- 涉及文件：<主要改动的文件列表>
- 代码行数：+XX / -XX

## 技术决策
| 问题 | 方案 | 为什么 |
|------|------|--------|
| ... | ... | ... |

## 遗留问题
- [ ] TODO: ...
- [ ] 技术债：...

## 测试状态
- 单元测试：通过/未覆盖
- 集成测试：...
- 需人工验证：...
```

## 十一、注意事项

- 不要过于频繁打断用户，连续操作时只在关键节点询问
- 如果用户明确说"跳过"或"不分类"，尊重选择
- 新 Project 需要用户确认后才在 Linear 创建
- Labels 可多选，反映实际工作内容
- Branch 名称必须包含 Issue Key 以触发自动关联
- GUI 相关改动必须标记「需人工测试」，避免漏测
