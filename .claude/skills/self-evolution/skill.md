# self-evolution - 自我迭代

基于官方文档进行最佳实践级别的自我优化。

## 触发词

- "自我迭代"
- "自我优化"
- "升级配置"
- "学习新功能"

## 官方文档位置

`/Users/liuyishou/.claude/claude-code-docs/`

包含：
- settings.md - 配置选项
- hooks.md / hooks-guide.md - Hook 机制
- skills.md - Skill 定义
- sub-agents.md - Subagent 创建
- mcp.md - MCP 服务器
- best-practices.md - 最佳实践
- plugins.md - 插件系统
- changelog.md - 更新日志

## 执行流程

### Step 1: 确定优化方向

用户可能指定方向，或让我自行诊断：

| 优化方向 | 查阅文档 |
|----------|----------|
| Hook 优化 | hooks.md, hooks-guide.md |
| Skill 优化 | skills.md |
| Subagent 优化 | sub-agents.md |
| 配置优化 | settings.md |
| MCP 扩展 | mcp.md |
| 新功能探索 | changelog.md, best-practices.md |

### Step 2: 审计当前配置

检查现有配置状态：

```bash
# 配置文件
cat ~/.claude/settings.json
cat ~/.claude.json | head -200

# Skills
ls -la ~/.claude/skills/

# Subagents
ls -la ~/.claude/agents/

# Hooks
ls -la ~/.claude/hooks/
```

### Step 3: 查阅官方文档

根据优化方向，读取对应的官方文档：

```bash
# 示例：读取 best-practices
cat /Users/liuyishou/.claude/claude-code-docs/best-practices.md
```

### Step 4: 对比分析

将当前配置与官方最佳实践对比：
- 缺失的推荐配置
- 可以改进的 Hook
- 未使用的新功能
- Skill/Subagent 的优化空间

### Step 5: 生成优化方案

输出结构化的优化建议：

```markdown
## 优化报告

### 发现的问题
1. xxx 配置缺失
2. xxx Hook 可以优化

### 推荐改进
1. 添加 xxx 配置
2. 创建 xxx Subagent

### 执行计划
- [ ] 步骤 1
- [ ] 步骤 2
```

### Step 6: 执行优化（需用户确认）

在用户确认后执行具体的配置修改。

## 自动诊断清单

当用户没有指定方向时，自动检查：

1. **settings.json 完整性**
   - 是否有推荐的 permission 配置
   - Hook 是否覆盖关键事件

2. **Skill 健康度**
   - skill.md 格式是否规范
   - 是否有重复/冗余的 skill

3. **Subagent 规范性**
   - frontmatter 是否完整
   - description 是否足够清晰供自动委派

4. **新功能检查**
   - 对比 changelog.md 看是否有未使用的新功能

## 注意事项

- 修改配置前必须备份
- 重大改动需用户确认
- 记录每次优化的变更日志
