# 产品事业部 - 代码杠杆

> 将 idea 变为产品，找到愿意付费的用户

## 一、核心信息

| 字段 | 值 |
|------|-----|
| Linear Team | P (产品事业部) |
| Initiative | 代码杠杆 |
| 启动命令 | `cd ~/usr/pac/product-bu && claude --dangerously-skip-permissions` |

## 二、产品项目（Linear Project）

| 项目 | 说明 | 状态 |
|------|------|------|
| Viva | 英语学习 App（词汇 + 听力） | active |
| Vocab Highlighter | 浏览器生词高亮（已合并到 Viva 插件端） | merged |
| CC Mission Control | Claude Code Dashboard | planning |
| 投资 Dashboard | 持仓追踪工具 | idea |
| 知识库产品 | Obsidian 笔记变现 | idea |
| ModelHop | Chrome 插件 | active |

## 三、工作流状态

```
Backlog --> Todo --> In Progress --> In Review --> 待人工测试 --> 待发布 --> Done
```

## 四、目录结构

```
product-bu/
├── .claude/               # Claude Code 项目配置
├── hooks/                 # 项目级 hooks
├── viva/                  # Viva 英语学习 App
├── ModelHop/              # Chrome 插件
├── VoiceType/             # 语音输入工具
├── dejavu/                # 其他项目
├── docs/                  # 文档
└── inbox/                 # 临时项目
```

## 五、Git 规范

- **Branch**: `{type}/{issue-key}-{short-description}` (如 `feat/P-15-viva-splash-screen`)
- **Commit**: `{type}({scope}): {description} [{issue-key}]`
- **Worktree**: `~/usr/projects/worktrees/{project}/{issue-key}`

## 六、自动化

### 6.1 Session 结束自动上报

全局 `SessionEnd` hook --> PMO Agent --> 创建 Linear Issue

### 6.2 状态流转

| 操作 | Linear 更新 |
|------|------------|
| 创建 branch | In Progress |
| 创建 PR | In Review |
| PR 合并 + GUI 标签 | 待人工测试 |
| PR 合并 - GUI 标签 | 待发布 |
| 部署成功 | Done |

## 七、测试标签

涉及 UI 交互的 Issue 必须标记「需人工测试」，AI 无法验证视觉/交互。

## 八、常用 Skills

| Skill | 用途 |
|-------|------|
| `deploy` | 统一部署（Vercel/TestFlight） |
| `api-deploy-testflight` | iOS TestFlight |
| `api-deploy-static` | 静态网站 |
| `tdd` | 测试驱动开发 |
| `build-fix` | 构建失败修复 |
