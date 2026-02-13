# PMO - 项目管理办公室

> Personal AI Company 的管理中枢，自动追踪 Session 活动并归类到 Linear

## 一、架构

```
SessionEnd Hook (全局)
    |
    v
pmo-session-end.js          # 结构化提取 session 摘要
    |
    v
spawn PMO Agent              # claude --dangerously-skip-permissions --print
    |                         # cwd: ~/usr/pac/pmo（读取 CLAUDE.md + BU 规则）
    v
Linear API                   # 创建/更新 Issue + Document
```

## 二、目录结构

```
pmo/
├── CLAUDE.md              # PMO Agent prompt（事业部规则、Team ID、处理流程）
├── README.md              # 本文件
├── pmo-session-end.js     # SessionEnd Hook（结构化摘要提取）
├── rules/
│   ├── product-bu.md      # 产品事业部规则
│   ├── content-bu.md      # 内容事业部规则
│   ├── investment-bu.md   # 投资事业部规则
│   └── research-bu.md     # 调研事业部规则
├── agent.md               # PMO Agent 定义（备用）
├── hooks/                 # 专用 Hook（如有）
└── lib/                   # 工具库（如有）
```

## 三、Session 摘要提取策略

`pmo-session-end.js` 采用分层提取，用户优先：

| 层级 | 扫描范围 | 提取内容 | 用途 |
|------|---------|---------|------|
| 意图层 | 全量用户消息 | 每条最多 500 字 | 理解 session 在做什么 |
| 行为层 | 全量 tool_use | 工具名称去重 | 判断标签（api-draw=做图） |
| 产出层 | 全量 Write/Edit | 文件路径 | 证明有实际产出 |
| 结果层 | 仅最后一条 assistant | 最多 1500 字 | 通常是总结/收尾 |

总摘要上限 4000 字符，传给 PMO Agent 分析。

## 四、事业部与 Linear 映射

| 事业部 | Team Key | cwd 关键词 | Initiative |
|--------|----------|-----------|------------|
| 产品 | P | `product-bu` | 代码杠杆 |
| 内容 | C | `content-bu` | 媒体杠杆 |
| 投资 | I | `investment-bu` | 资本杠杆 |
| 调研 | R | `research-bu` | 信息杠杆 |
| PMO | PMO | `pmo` | - |

## 五、PMO Agent 判断流程

```
收到结构化摘要
    |
    +--> 是否有实际产出？（工具调用 > 0 或文件产出 > 0）
    |       |
    |       No --> 跳过（纯聊天/咨询）
    |       |
    |       Yes
    |       v
    +--> 根据 cwd 判断事业部
    |       v
    +--> 匹配 Project（关键词匹配 projects.json）
    |       v
    +--> 根据工具名称推断 Labels
    |       v
    +--> 创建 Issue + Document
```

## 六、依赖

| 依赖 | 说明 |
|------|------|
| `LINEAR_API_KEY` | `~/.claude/secrets.env` |
| `linear-cli.js` | `~/.claude/skills/api-linear/linear-cli.js` |
| `projects.json` | `~/.claude/knowledge/projects.json` |
| Pro 订阅 | PMO Agent 移除 API key，使用 Pro 认证 |

## 七、触发配置

全局 `~/.claude/settings.json` 中的 `SessionEnd` hook：

```json
{
  "SessionEnd": [{
    "matcher": "",
    "hooks": [{
      "type": "command",
      "command": "node /Users/liuyishou/usr/pac/pmo/pmo-session-end.js",
      "timeout": 30
    }]
  }]
}
```
