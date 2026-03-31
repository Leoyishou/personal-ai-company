# Linear GitHub Integration 配置指南

## 一、在 Linear 中配置 GitHub Integration

### 1.1 连接 GitHub

1. 打开 Linear → Settings → Integrations → GitHub
2. 点击 "Connect GitHub"
3. 选择要连接的 GitHub 账号和仓库

### 1.2 配置自动化规则

在 Linear Settings → Team Settings → Workflow → Automations 中添加：

**规则 1：Branch 创建 → In Progress**
```
When: A branch is created that references an issue
Then: Move issue to "In Progress"
```

**规则 2：PR 创建 → In Review**
```
When: A pull request is created that references an issue
Then: Move issue to "In Review"
```

**规则 3：PR 合并 → 待发布/待人工测试**
```
When: A pull request is merged that references an issue
Then:
  - If issue has label "需人工测试" or "GUI测试" → Move to "待人工测试"
  - Else → Move to "待发布"
```

### 1.3 Issue 链接方式

Linear 自动识别以下格式：

1. **Branch 名称**：`feat/P-15-description` → 自动关联 P-15
2. **Commit Message**：`feat: xxx [P-15]` 或 `Fixes LIN-15`
3. **PR Title/Body**：包含 `P-15` 或 `Fixes LIN-15`

## 二、GitHub 仓库配置

### 2.1 Branch Protection Rules

在 GitHub 仓库 Settings → Branches 中配置：

```
Branch name pattern: main
- Require pull request reviews before merging
- Require status checks to pass before merging
- Include administrators
```

### 2.2 Webhook（可选，高级）

如果需要更复杂的自动化，可以配置 Webhook：

```
Payload URL: https://api.linear.app/webhooks/github
Content type: application/json
Events:
  - Pull requests
  - Pushes
  - Branch or tag creation
```

## 三、验证配置

1. 创建一个测试 Issue（如 P-99）
2. 创建 branch `feat/P-99-test`
3. 检查 Linear 中 P-99 是否自动变为 "In Progress"
4. 创建 PR
5. 检查 Linear 中 P-99 是否自动变为 "In Review"
