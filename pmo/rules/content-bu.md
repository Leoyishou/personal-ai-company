# PMO 项目归类规则 - 内容事业部

## 一、核心概念

### 1.1 Session 与 Issue 的关系

```
1 个本地 Session = 1 或 n 个 Linear Issue
```

- 每个 Issue 的 description 必须包含 `sessionId: <session_id>`
- 同一 Session 可能产出多个 Issue（如：做完图又写文案）

### 1.2 事业部信息

| 字段 | 值 |
|------|-----|
| Team ID | `4bb065b8-982f-4a44-830d-8d88fe8c9828` |
| Key | C |
| 说明 | 社媒发布内容 |

## 二、Project = 内容系列

内容事业部的 Project 对应一个**内容系列**：
- `n张图系列` - 图文科普
- `人物语录系列` - 名人名言配图
- `技术科普系列` - 编程/AI 科普
- `小红书封面系统` - 工具类项目

**Issue = 系列中的一期内容**，如：
- `[n张图] DuckDB vs PostgreSQL`
- `[人物语录] 马斯克论第一性原理`

## 三、Labels（流程阶段）

| Label | Label ID | 说明 |
|-------|----------|------|
| 灵感 | `7be8f7f1-b476-4c27-87e4-e4b36fc2e6cb` | 选题、素材收集 |
| 做图 | `5a95aaa6-ce9a-4871-81ef-1dcce2bbc3e7` | 封面图、配图制作 |
| 文案 | `be0f8c2e-7054-490f-84c1-f95212c07ef2` | 文案撰写 |
| 发布 | `b4fa7209-3d42-4cdb-98c0-ee2742dd647a` | 发布到平台 |
| 后评估 | `072feefc-4d30-4522-af7d-ba6448ec960f` | 数据复盘、优化 |

**可多选**：一个 Issue 可以同时有 `做图` + `文案` 标签

## 四、Issue 创建规范

### 4.1 必填字段

```graphql
issueCreate(input: {
  title: "任务标题",
  teamId: "4bb065b8-982f-4a44-830d-8d88fe8c9828",
  projectId: "项目ID",
  description: "sessionId: xxx\n\n任务描述",
  labelIds: ["label1", "label2"]
})
```

### 4.2 Description 模板（轻量摘要）

```markdown
sessionId: <session_id>

## 摘要
<一句话描述这期内容>

## 创作信息
- 风格: <手绘白板/人物语录/...>
- 平台: <小红书/X/B站>
```

### 4.3 Document: 创作素材

通过 `doc-create --issue C-xx` 创建，详细内容独立存放：

```markdown
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

## 五、触发与归类

### 5.1 触发时机

PMO Classify Hook 在以下操作时自动触发：
- 图片生成（api-draw）→ 内容事业部
- 社媒发布（social-media/xiaohongshu/x-post）→ 内容事业部
- 视频制作（video）→ 内容事业部

### 5.2 归类流程

1. **匹配 Project**：根据关键词匹配已有内容系列
2. **选择 Labels**：根据当前阶段打 Label
3. **创建 Issue**：提交到内容事业部 Team

### 5.3 Project 匹配规则

**匹配逻辑**：
1. 从 Session 上下文提取关键词（用户消息、画图 prompt、发布内容）
2. 与已有 Project 的 keywords 匹配
3. 计算匹配度：高（>0.8）、中（0.5-0.8）、低（<0.5）

**匹配结果处理**：

| 匹配度 | 行为 |
|--------|------|
| 高 | 自动关联，静默处理 |
| 中 | 用 AskUserQuestion 确认 |
| 低/无 | 默认归入「随机探索系列」或让用户选择 |

## 六、项目名单

**数据源**：`~/.claude/knowledge/projects.json`

| ID | 项目名 | Linear Project ID | 关键词 | 说明 |
|----|--------|-------------------|--------|------|
| 10 | n张图系列 | `d6a1d29d-7bca-42c5-8779-71467fa97e5c` | n张图, 图文, 对比, 科普 | |
| 11 | 人物语录系列 | `3a246550-a979-416e-8810-1c094fcc810c` | 语录, 名言, 人物, quote | |
| 12 | 技术科普系列 | `b422ae73-64d5-42b1-9458-1992285877b2` | 技术, 科普, 编程, AI | |
| 13 | 随机探索系列 | - | 探索, 随机, 杂谈 | **兜底**：不属于其他系列时用 |
| 6 | 小红书封面系统 | - | 小红书, 封面, xhs, 模板 | 工具类 |

## 七、内容发布自动追踪

### 7.1 小红书发布追踪 Hook

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

### 7.2 Issue 自动生成格式

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

### 7.3 自动回填机制

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

### 7.4 依赖配置

- `LINEAR_API_KEY`：必须在 `~/.claude/secrets.env` 中配置
- 小红书 MCP 服务：必须运行在 `http://localhost:18060/mcp`

## 八、Session 总结模板

Session 结束时，通过 `doc-create --issue C-xx` 创建 Document（而非追加到 description）：

**Document 标题**：`Session 总结: <内容主题>`

```markdown
## 选题来源
- 灵感：<从哪来的 idea>
- 参考：<有无参考链接>

## 创作过程
- 风格：`手绘白板` / `人物语录` / ...
- 模板：`~/.claude/skills/api-draw/templates/xxx.md`
- 迭代次数：<生成了几版才满意>
- 关键调整：<什么改动让效果变好>

## 产出物
| 类型 | 文件 | 用途 |
|------|------|------|
| 封面 | `file://...` | 小红书 |
| 内容图 | `file://...` | 第 2 张 |

## 发布情况
| 平台 | 链接 | 数据（3日后回填） |
|------|------|-------------------|
| 小红书 | ... | 点赞/收藏/评论 |
| X | ... | ... |

## 经验沉淀
- 有效：<这个风格/文案/钩子效果好>
- 失败：<下次避免>
- 可复用：<这套 prompt 可以做成模板吗>
```

## 九、注意事项

- 不要过于频繁打断用户，连续操作时只在关键节点询问
- 如果用户明确说"跳过"或"不分类"，尊重选择
- 新 Project 需要用户确认后才在 Linear 创建
- Labels 可多选，反映实际工作内容
- 不属于明确系列的内容，默认归入「随机探索系列」
