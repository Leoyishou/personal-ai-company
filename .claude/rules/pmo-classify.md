# PMO 项目归类规则

## 一、核心概念

### 1.1 Session 与 Issue 的关系

```
1 个本地 Session = 1 或 n 个 Linear Issue
```

- 每个 Issue 的 description 必须包含 `sessionId: <session_id>`
- 同一 Session 可能产出多个 Issue（如：做完设计又写代码）

### 1.2 两个事业部（Team）

| 事业部 | Team ID | Key | 说明 |
|--------|---------|-----|------|
| 产品事业部 | `<YOUR_PRODUCT_TEAM_ID>` | P | 面向用户的产品 |
| 内容事业部 | `<YOUR_CONTENT_TEAM_ID>` | C | 社媒发布内容 |

## 二、产品事业部 (P-)

### 2.1 Project = 一个用户产品

- `Viva` - 英语学习 App
- `Vocab Highlighter` - 浏览器插件
- `投资 Dashboard` - 持仓追踪工具

**IMPORTANT**: 每个产品项目必须绑定对应的 GitHub 仓库作为 Resource Link。

```graphql
# 添加 GitHub 链接到项目
mutation {
  entityExternalLinkCreate(input: {
    url: "https://github.com/<your-username>/<repo-name>",
    label: "GitHub",
    projectId: "<project-id>"
  }) { success }
}
```

### 2.2 Labels（工作类型）

| Label | 说明 |
|-------|------|
| 产品思路 | 需求分析、功能规划 |
| 设计 | UI/UX 设计、原型图 |
| 前端 | 前端开发 |
| 后端 | 后端开发 |
| 测试 | 测试 |
| 发布 | 部署上线 |

### 2.3 Labels（端类型，可选）

| Label | 说明 |
|-------|------|
| App端 | iOS/Android App |
| 插件端 | 浏览器插件（Vocab Highlighter）|
| Web端 | Web 应用 |

**可多选**：一个 Issue 可以同时有 `前端` + `App端` + `发布`

## 三、内容事业部 (C-)

### 3.1 Project = 内容系列

内容事业部的 Project 对应一个**内容系列**：
- `n张图系列` - 图文科普
- `人物语录系列` - 名人名言配图
- `技术科普系列` - 编程/AI 科普
- `小红书封面系统` - 工具类项目

**Issue = 系列中的一期内容**，如：
- `[n张图] DuckDB vs PostgreSQL`
- `[人物语录] 马斯克论第一性原理`

### 3.2 Labels（流程阶段）

| Label | 说明 |
|-------|------|
| 灵感 | 选题、素材收集 |
| 做图 | 封面图、配图制作 |
| 文案 | 文案撰写 |
| 发布 | 发布到平台 |
| 后评估 | 数据复盘、优化 |

**可多选**：一个 Issue 可以同时有 `做图` + `文案` 标签

### 3.3 内容事业部 Description 模板

```markdown
sessionId: <session_id>

## 内容描述
<这期内容讲什么>

## 创作素材
- 风格文档: `~/.claude/skills/api-draw/templates/<风格名>.md`
- AI 画图 Prompt:
  ```
  <实际使用的 prompt>
  ```
- 参考素材: <如有链接或描述>

## 产出物

### 图片
| 序号 | 文件 | 说明 |
|------|------|------|
| 1 | `file:///path/to/image1.png` | 封面 |
| 2 | `file:///path/to/image2.png` | 内容图 |

### 文案
<完整文案内容>

## 发布记录
| 平台 | 时间 | 链接 |
|------|------|------|
| 小红书 | 2026-02-03 | https://... |
| X | - | - |
| B站 | - | - |
```

**字段说明**：
- **风格文档**：画图风格的 prompt 模板，存放在 `~/.claude/skills/api-draw/templates/`
- **AI 画图 Prompt**：本次实际使用的完整 prompt
- **产出物**：最终生成的图片（本地路径或 CDN 链接）
- **发布记录**：多平台发布后回填链接

## 四、Issue 创建规范

### 4.1 必填字段

```graphql
issueCreate(input: {
  title: "任务标题",
  teamId: "事业部ID",        # 产品/内容
  projectId: "项目ID",       # 可选，关联产品
  description: "sessionId: xxx\n\n任务描述",
  labelIds: ["label1", "label2"]  # 工作类型
})
```

### 4.2 Description 模板

```markdown
sessionId: <session_id>

## 任务描述
<具体要做什么>

## 相关链接
- 本地目录: file:///path/to/project
- GitHub: https://github.com/xxx
```

## 五、触发与归类

### 5.1 触发时机

PMO Classify Hook 在以下操作时自动触发：
- 代码改动（Write/Edit）→ 产品事业部
- 图片生成（api-draw）→ 可能是内容事业部
- 社媒发布（social-media/xiaohongshu/x-post）→ 内容事业部
- 视频制作（video）→ 内容事业部

### 5.2 归类流程

1. **判断事业部**：根据操作类型判断产品/内容
2. **匹配 Project**：根据关键词匹配已有 Project（见第六节名单）
3. **选择 Labels**：根据具体工作内容打 Label
4. **创建 Issue**：提交到对应 Team

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

**AskUserQuestion 格式**：

```
question: "这个任务属于哪个项目？"
header: "项目归类"
options:
  - { label: "Viva (推荐)", description: "匹配到关键词: 英语, 词汇" }
  - { label: "CC Mission Control", description: "" }
  - { label: "新建项目", description: "创建新的产品项目" }
multiSelect: false
```

**新建 Project 流程**：
1. 用户选择"新建项目"后，追问项目名称
2. 调用 Linear API 创建 Project
3. 更新 `~/.claude/knowledge/projects.json`
4. 将 Issue 关联到新 Project

## 六、项目名单

**数据源**：`~/.claude/knowledge/projects.json`

### 产品事业部（用户产品）

| ID | 项目名 | Linear Project ID | 关键词 |
|----|--------|-------------------|--------|
| 2 | Viva | `<VIVA_PROJECT_ID>` | viva, 英语, 词汇, vocab, 听力, 学习app |
| 3 | Vocab Highlighter | - | highlighter, 高亮, 插件, 浏览器 |
| 1 | CC Mission Control | - | dashboard, 任务流, pmo, 可视化 |
| 4 | 投资 Dashboard | - | 投资, 持仓, 股票, portfolio, 收益 |
| 5 | 知识库产品 | - | 知识库, obsidian, 笔记, 变现 |

### 内容事业部（内容系列）

| ID | 项目名 | Linear Project ID | 关键词 | 说明 |
|----|--------|-------------------|--------|------|
| 10 | n张图系列 | `<PROJECT_ID>` | n张图, 图文, 对比, 科普 | |
| 11 | 人物语录系列 | `<PROJECT_ID>` | 语录, 名言, 人物, quote | |
| 12 | 技术科普系列 | `<PROJECT_ID>` | 技术, 科普, 编程, AI | |
| 13 | 随机探索系列 | - | 探索, 随机, 杂谈 | **兜底**：不属于其他系列时用 |
| 6 | 小红书封面系统 | - | 小红书, 封面, xhs, 模板 | 工具类 |

## 七、工作流状态

### 7.1 产品事业部状态流转

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

### 8.5 Description 模板更新

```markdown
sessionId: <session_id>

## 任务描述
<具体要做什么>

## Git 信息
- Branch: `feat/P-xx-description`
- Worktree: `~/usr/projects/worktrees/{project}/P-xx`
- PR: （待创建）

## 测试要求
- [ ] 自动化测试
- [ ] GUI 测试（如需人工）

## 相关链接
- 本地目录: file:///path/to/project
- GitHub: https://github.com/xxx
```

### 8.6 Session 总结模板

Session 结束时，根据事业部生成对应的总结，追加到 Issue description。

#### 产品事业部总结

```markdown
## Session 总结

### 完成内容
- 功能：<做了什么>
- 涉及文件：<主要改动的文件列表>
- 代码行数：+XX / -XX

### 技术决策
| 问题 | 方案 | 为什么 |
|------|------|--------|
| ... | ... | ... |

### 遗留问题
- [ ] TODO: ...
- [ ] 技术债：...

### 测试状态
- 单元测试：通过/未覆盖
- 集成测试：...
- 需人工验证：...
```

#### 内容事业部总结

```markdown
## Session 总结

### 选题来源
- 灵感：<从哪来的 idea>
- 参考：<有无参考链接>

### 创作过程
- 风格：`手绘白板` / `人物语录` / ...
- 模板：`~/.claude/skills/api-draw/templates/xxx.md`
- 迭代次数：<生成了几版才满意>
- 关键调整：<什么改动让效果变好>

### 产出物
| 类型 | 文件 | 用途 |
|------|------|------|
| 封面 | `file://...` | 小红书 |
| 内容图 | `file://...` | 第 2 张 |

### 发布情况
| 平台 | 链接 | 数据（3日后回填） |
|------|------|-------------------|
| 小红书 | ... | 点赞/收藏/评论 |
| X | ... | ... |

### 经验沉淀
- 有效：<这个风格/文案/钩子效果好>
- 失败：<下次避免>
- 可复用：<这套 prompt 可以做成模板吗>
```

---

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

## 十、内容发布自动追踪

### 10.1 小红书发布追踪 Hook

**触发条件**：`PostToolUse` + `Bash` + 命令包含 `xhs_publish.py publish` + 输出包含"发布完成"

**Hook 路径**：`~/.claude/hooks/xhs-publish-tracker/index.js`

**自动化流程**：

```
小红书发布成功
    ↓
立即创建 Linear Issue（内容事业部）
    ↓
启动后台任务
    ↓
3分钟后自动搜索笔记
    ↓
回填笔记链接 + 初始数据到 Issue
```

### 10.2 Issue 自动生成格式

**标题格式**：`【MMdd-HH】小红书：{笔记标题}`

**Description 模板**：

```markdown
sessionId: <session_id>

## 发布信息
- **标题**: {笔记标题}
- **标签**: {标签列表}
- **发布时间**: {ISO时间}

## 笔记链接
⏳ 3分钟后自动回填...

## 数据追踪
| 时间 | 点赞 | 收藏 | 评论 |
|------|------|------|------|
| 发布时 | - | - | - |
```

### 10.3 自动回填机制

3分钟后，Hook 会：
1. 调用小红书 MCP 的 `search_feeds` 搜索笔记
2. 匹配作者为「转了码的刘公子」的笔记
3. 提取笔记 ID，生成链接：`https://www.xiaohongshu.com/explore/{note_id}`
4. 获取初始互动数据（点赞/收藏/评论）
5. 更新 Linear Issue 的 description

**回填后格式**：

```markdown
## 笔记链接
✅ https://www.xiaohongshu.com/explore/698162d1000000001a02aa1c

## 数据追踪
| 时间 | 点赞 | 收藏 | 评论 |
|------|------|------|------|
| 3分钟后 | 3 | 2 | 0 |
```

### 10.4 依赖配置

- `LINEAR_API_KEY`：必须在 `~/.claude/secrets.env` 中配置
- 小红书 MCP 服务：必须运行在 `http://localhost:18060/mcp`

---

## 十一、注意事项

- 不要过于频繁打断用户，连续操作时只在关键节点询问
- 如果用户明确说"跳过"或"不分类"，尊重选择
- 新 Project 需要用户确认后才在 Linear 创建
- Labels 可多选，反映实际工作内容
- Branch 名称必须包含 Issue Key 以触发自动关联
- GUI 相关改动必须标记「需人工测试」，避免漏测
