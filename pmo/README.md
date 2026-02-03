# PMO Agent - 项目管理自动化

> 自动追踪 Session 活动，归类到 Linear 项目

## 目录结构

```
pmo/
├── agent.md              # PMO Agent 定义
├── rules/
│   ├── product-bu.md     # 产品事业部规则
│   └── content-bu.md     # 内容事业部规则
└── hooks/
    ├── classify.js       # 实时分类（PostToolUse）
    ├── xhs-mcp-tracker.js  # 小红书 MCP 发布追踪
    └── session-end.js    # Session 结束总结
```

## 触发机制

| Hook | 时机 | 触发条件 | 作用 |
|------|------|----------|------|
| classify.js | PostToolUse | Write/Edit/Skill | 实时判断事业部归属 |
| xhs-mcp-tracker.js | PostToolUse | 小红书 MCP publish | 创建内容 Issue，回填链接 |
| session-end.js | SessionEnd | 所有 Session | 总结并上报 Linear |

## 事业部判断

根据 `cwd`（当前工作目录）判断：
- `product-bu` → 产品事业部（Team: P）
- `content-bu` → 内容事业部（Team: C）

## 依赖

- `LINEAR_API_KEY`：`~/.claude/secrets.env`
- 小红书 MCP：`http://localhost:18060/mcp`
