# Reddit 调研示例

## 示例 1：技术框架对比调研

**用户请求：**
```
帮我调研一下 Next.js 和 Remix 在实际项目中的使用体验，开发者更推荐哪个？
```

**调研过程：**

1. 执行搜索：
   - `site:reddit.com/r/reactjs nextjs vs remix`
   - `site:reddit.com/r/webdev nextjs remix production`
   - `site:reddit.com nextjs remix performance 2026`

2. 分析维度：
   - 性能表现
   - 开发体验
   - 部署难度
   - 社区支持
   - 适用场景

3. 生成报告包含：
   - 两个框架的优劣对比表
   - 不同使用场景的推荐
   - 迁移成本分析
   - 社区主流观点
   - 10+ 条参考讨论链接

---

## 示例 2：产品市场调研

**用户请求：**
```
我想了解 Notion 的用户痛点和竞品选择
```

**调研过程：**

1. 执行搜索：
   - `site:reddit.com/r/Notion problems issues`
   - `site:reddit.com notion alternatives 2026`
   - `site:reddit.com notion vs obsidian`
   - `site:reddit.com notion pricing expensive`

2. 提取信息：
   - 用户抱怨最多的 5 个问题
   - 最常被提及的 3 个替代品
   - 价格敏感度分析
   - 不同用户群体的需求差异

3. 报告输出：
   - 痛点优先级排序
   - 竞品对比矩阵
   - 用户留存/流失原因
   - 市场机会点

---

## 示例 3：趋势分析

**用户请求：**
```
调研 AI 编程助手在开发者中的接受度和使用情况
```

**调研过程：**

1. 执行搜索：
   - `site:reddit.com/r/programming AI coding assistant 2026`
   - `site:reddit.com github copilot cursor comparison`
   - `site:reddit.com/r/webdev AI tools productivity`
   - `site:reddit.com developers AI concerns`

2. 分析角度：
   - 采用率趋势
   - 主流工具对比
   - 开发者顾虑
   - 实际效果评价
   - 未来预期

3. 报告内容：
   - 时间线：观点演变
   - 分类：不同开发者群体的态度
   - 数据：提及频率、情感倾向
   - 预测：基于讨论的趋势判断

---

## 示例 4：问题解决方案调研

**用户请求：**
```
我想知道如何优化 React 应用的性能，社区有什么最佳实践？
```

**调研过程：**

1. 执行搜索：
   - `site:reddit.com/r/reactjs performance optimization`
   - `site:reddit.com react slow performance fix`
   - `site:reddit.com react best practices 2026`
   - `site:reddit.com react performance tools`

2. 整理方案：
   - 常见性能瓶颈
   - 推荐优化技术（memo、lazy loading 等）
   - 工具推荐（Profiler、Lighthouse 等）
   - 真实案例分享

3. 输出结构：
   - 问题诊断清单
   - 解决方案库（按难度和效果排序）
   - 工具对比表
   - 学习资源链接

---

## 示例 5：用户体验调研

**用户请求：**
```
调研机械键盘新手最关心什么，如何选购第一把键盘
```

**调研过程：**

1. 执行搜索：
   - `site:reddit.com/r/MechanicalKeyboards beginner first keyboard`
   - `site:reddit.com/r/MechanicalKeyboards buying guide 2026`
   - `site:reddit.com/r/MechanicalKeyboards budget recommendations`
   - `site:reddit.com mechanical keyboard mistakes avoid`

2. 用户画像：
   - 预算分布
   - 主要用途（办公/游戏/编程）
   - 关注要素（声音/手感/外观）
   - 常见误区

3. 报告呈现：
   - 新手决策流程图
   - 不同价位推荐矩阵
   - FAQ 汇总
   - 避坑指南

---

## 快速调用示例

在 Claude Code 中直接使用：

```bash
# 技术调研
帮我做一个关于 TypeScript 5.0 新特性接受度的 Reddit 调研

# 产品调研
基于 Reddit 调研一下 VSCode 插件开发者的痛点

# 市场调研
调研程序员对远程工作的真实看法（Reddit）

# 对比调研
在 Reddit 上调研 Docker vs Podman 的使用体验
```

---

## 自定义搜索策略示例

### 针对特定时间范围
```
site:reddit.com [主题] after:2025-01-01
site:reddit.com [主题] 2026
```

### 针对特定社区
```
site:reddit.com/r/programming
site:reddit.com/r/webdev
site:reddit.com/r/reactjs
```

### 组合搜索
```
site:reddit.com (nextjs OR remix) performance benchmark
site:reddit.com "best practices" typescript
```

---

## 报告质量检查清单

生成的报告应该满足：

- [ ] 有明确的执行摘要
- [ ] 核心发现基于多个来源
- [ ] 提供具体的数据支撑（而非主观判断）
- [ ] 包含至少 5 个有效来源链接
- [ ] 呈现不同的观点（正面、负面、中性）
- [ ] 标注调研的局限性
- [ ] 提供可执行的行动建议
- [ ] 格式清晰，易于阅读
