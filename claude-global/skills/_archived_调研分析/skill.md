---
name: 调研&分析
shortname: 🔍 调研
description: 多信息源并发调研，区分事实与观点，Fact-check 后输出洞见。
version: 4.0.0
author: Claude
allowed-tools: Bash(python:*), Read, Write, Glob, WebSearch, WebFetch
model: sonnet
tags: [research, analysis, fact-check, insight, perplexity, grok, reddit, v2ex]
---

# 调研&分析

## 核心流程

```
信息源并发搜索 → 资料整合 → 事实/观点分离 → Fact-check → Insight
```

---

## 一、信息源并发搜索

**原则：能并发就并发，充分利用所有可用信息源。**

### 1.1 可用信息源

| 信息源 | 工具 | 特点 | 适用场景 |
|-------|------|------|---------|
| **Perplexity** | `perplexity_research.py` | 全网搜索、带引用 | 综合调研、事实查询 |
| **Grok X搜索** | `grok_x_search.py` | Twitter/X 实时数据（默认最近7天） | 舆情、KOL观点、实时事件 |
| **V2EX** | `v2ex_search.py` | 中文技术社区、开发者讨论 | 技术调研、中文用户反馈、工具评测 |
| **Reddit** | `research-by-reddit` skill | 深度讨论、真实反馈 | 用户痛点、产品评价 |
| **WebFetch** | 内置工具 | 抓取指定网页 | 官方来源、一手资料 |
| **WebSearch** | 内置工具 | 通用搜索 | 补充搜索 |

### 1.2 并发搜索示例

```bash
# 同时调用多个信息源（在 Claude 中并行执行）
cd ~/.claude/skills/调研\&分析/scripts

# Perplexity 全网搜索
python perplexity_research.py --query "主题" --deep &

# Grok Twitter 搜索（不传日期默认搜索最近7天）
python grok_x_search.py --query "主题" &

# V2EX 中文技术社区搜索
python v2ex_search.py --query "主题" --size 10 &

# 等待所有搜索完成
wait
```

### 1.3 信息源选择策略

| 调研类型 | 推荐信息源组合 |
|---------|---------------|
| **产品调研** | Perplexity + Reddit + V2EX + 官网 WebFetch |
| **舆情监测** | Grok X搜索 + Reddit + V2EX |
| **技术调研** | Perplexity + V2EX + GitHub + 官方文档 |
| **人物调研** | Perplexity + Grok X搜索 |
| **市场调研** | Perplexity + Reddit + 行业报告 |
| **投资调研** | Perplexity + Grok X搜索 + 财报 |
| **开发工具评测** | V2EX + Reddit + Grok X搜索 |

---

## 二、资料整合

### 2.1 整合原则

1. **去重** - 相同信息只保留最权威来源
2. **分类** - 按主题/维度组织
3. **标注来源** - 每条信息标明出处
4. **时间排序** - 注明信息时间，优先最新

### 2.2 整合模板

```markdown
## 原始资料汇总

### 来源：Perplexity
- [信息1] (来源URL, 时间)
- [信息2] (来源URL, 时间)

### 来源：Twitter/X
- [@用户] "推文内容" (时间, 互动数)
- [@用户] "推文内容" (时间, 互动数)

### 来源：Reddit
- [r/subreddit] 帖子标题 (upvotes, 评论数)
  - 热门评论摘要

### 来源：官方渠道
- [官网] 信息内容 (URL)
- [公告] 信息内容 (时间)
```

---

## 三、事实 vs 观点 分离

**关键环节：明确区分可验证的事实和主观观点。**

### 3.1 事实 (Facts)

可验证、客观的信息：

- 数字：融资金额、用户数、市场规模
- 日期：发布时间、里程碑事件
- 事件：收购、合作、产品发布
- 技术指标：性能数据、准确率
- 官方声明：公司公告、财报数据

### 3.2 观点 (Opinions)

主观判断、无法直接验证：

- 评价：好用/难用、值得/不值
- 预测：未来趋势、市场走向
- 比较：A比B好、X是最佳选择
- 情感：喜欢/讨厌、期待/失望
- 推荐：建议使用、不推荐

### 3.3 分离模板

```markdown
## 事实清单

| 事实 | 来源 | 时间 | 待验证 |
|-----|------|------|-------|
| 融资 $4.5M | Crunchbase | 2024-12 | [ ] |
| 用户增长 50%/月 | 官方博客 | 2024-11 | [ ] |
| WER 5.9% | 论文 | 2016-10 | [x] |

## 观点汇总

### 正面观点
- "比 Apple 听写好用 10 倍" - @用户A (Twitter)
- "终于有好用的语音输入了" - Reddit r/productivity

### 负面观点
- "隐私担忧" - @用户B (Twitter)
- "定价太贵" - Reddit r/apps

### 中立/分析观点
- "技术上没有壁垒，竞争会很激烈" - 行业分析师
```

---

## 四、Fact-check

**对事实清单中的每一条进行验证。**

### 4.1 验证方法

| 数据类型 | 验证方法 | 可信来源 |
|---------|---------|---------|
| **融资数据** | 查 Crunchbase、官方公告 | 一手来源 |
| **技术指标** | 查官方文档、论文、基准测试 | 原始出处 |
| **市场数据** | 多份报告交叉对比 | Statista、Gartner 等 |
| **历史事件** | 多个新闻源确认 | 主流媒体 |
| **公司信息** | 官网、LinkedIn、SEC 文件 | 官方渠道 |

### 4.2 置信度标注

- `[✓]` **已验证** - 有一手来源确认
- `[⚠]` **待验证** - 仅有二手来源，或信息有条件限定
- `[?]` **推测** - 基于逻辑推断，无直接证据
- `[✗]` **存疑** - 发现矛盾信息，需进一步核实

### 4.3 Fact-check 记录模板

```markdown
## Fact-check 记录

| 数据点 | 原始值 | 验证结果 | 修正值 | 来源 | 置信度 |
|-------|-------|---------|-------|------|-------|
| 融资金额 | $4.5M | ✓ 确认 | - | Crunchbase | [✓] |
| 准确率 | 95% | ⚠ 条件限定 | 95%（仅干净音频） | 论文 | [⚠] |
| 发布时间 | 2024春 | ✓ 确认 | 2024-04 | Product Hunt | [✓] |
| 月增长率 | 50% | ? 无法验证 | - | 仅官方声称 | [?] |
```

---

## 五、Insight 输出

**基于验证后的事实 + 综合观点，给出独立判断。**

### 5.1 Insight 原则

1. **基于事实** - 每个结论都有已验证的事实支撑
2. **综合观点** - 考虑正反两面的观点
3. **独立判断** - 不只是复述，要有自己的分析
4. **可操作** - 给出具体的建议或下一步行动

### 5.2 输出结构

**IMPORTANT**: 报告开头必须包含「执行流程」区块，使用**简洁 ASCII 树形图**展示实际执行的步骤，并标注每个环节使用的**模型基座**。

````markdown
# [主题] 调研报告

---

## 执行流程

> 本次调研实际执行的 SOP 步骤记录

### 流程图

```
1. 信息源并发搜索
   ├─ ✓/✗ Perplexity (sonar-deep-research/OpenRouter) → [结果]
   ├─ ✓/✗ Grok X (grok-4-1-fast/xAI) → [结果]
   ├─ ✓/✗ V2EX (SOV2EX API) → [结果]
   ├─ ✓/✗ WebFetch → [结果]
   ├─ ✓/✗ WebSearch (Claude Search) → [结果]
   └─ ✓/✗ Reddit → [结果]
        ↓
2. 资料整合 [当前会话模型]
   → [具体执行内容]
        ↓
3. 事实/观点分离 [当前会话模型]
   → 事实: [列举]
   → 观点: [列举]
        ↓
4. Fact-check [当前会话模型]
   → [交叉验证方式]
   → 结果: X✓ Y⚠
        ↓
5. Insight 输出 [当前会话模型]
   → [核心产出]
```

### 信息源详情

| 信息源 | 状态 | 模型/API | 执行情况 |
|-------|:----:|---------|---------|
| Perplexity | ✓/✗ | `sonar-deep-research` (OpenRouter) | 说明 |
| Grok X/Twitter | ✓/✗ | `grok-4-1-fast` (xAI) | 说明 |
| V2EX | ✓/✗ | SOV2EX API | 说明 |
| WebFetch | ✓/✗ | - | 说明 |
| WebSearch | ✓/✗ | Claude Search | 说明 |
| Reddit | ✓/✗ | Reddit API | 说明 |

### 遗留问题

- [ ] 待处理项

---

## 执行摘要
- 核心发现 (3-5 条)
- 关键结论
- 行动建议

## 事实基础
[经过 Fact-check 的关键事实，带置信度标注]

## 观点光谱
[正面/负面/中立观点的平衡呈现]

## 深度分析
[基于事实和观点的独立分析]

## 洞见与建议
[独立判断和具体建议]

## 风险与不确定性
[标注哪些结论置信度较低，需要持续关注]

## 附录
- Fact-check 记录
- 原始资料来源列表
````

### 5.3 模型标注规范

**必须标注的模型信息**：

| 环节 | 默认模型 | API |
|-----|---------|-----|
| Perplexity 搜索 | `perplexity/sonar-deep-research` | OpenRouter |
| Grok X/Twitter | `grok-4-1-fast` | xAI API |
| V2EX | - | SOV2EX API |
| WebFetch | - (无模型) | 直接抓取 |
| WebSearch | Claude Search | Anthropic 内置 |
| Reddit | - | Reddit API |
| 资料整合/分析/输出 | 当前会话模型 | Claude API |

**状态符号规范**：
- `✓` 成功执行
- `✗` 跳过/失败（需说明原因）

### 5.4 执行流程记录要点

**必须记录**:
1. **信息源使用情况** - 每个信息源是否调用、成功/失败原因
2. **SOP 步骤完成度** - 5 个核心步骤各自的执行状态
3. **遗留问题** - 未完成的部分和原因，便于后续补充

**状态标记**:
- `✓` 完成
- `⚠` 部分完成（说明缺失部分）
- `✗` 未执行（说明原因）

**价值**:
- 让用户了解调研的完整度和局限性
- 便于追溯和复现调研过程
- 帮助识别信息盲区

---

## 工具使用指南

### Perplexity 搜索

```bash
cd ~/.claude/skills/调研\&分析/scripts

# 快速搜索
python perplexity_research.py --query "问题"

# 深度研究（复杂调研用这个）
python perplexity_research.py --query "问题" --deep

# 保存报告
python perplexity_research.py --query "问题" --deep --output report.md
```

### Grok X/Twitter 搜索

```bash
cd ~/.claude/skills/调研\&分析/scripts

# 关键词搜索
python grok_x_search.py --query "AI agent"

# 搜索特定用户
python grok_x_search.py --query "AI" --users elonmusk,sama

# 限定时间范围
python grok_x_search.py --query "DeepSeek" --from 2025-01-01 --to 2025-01-29
```

### V2EX 搜索

```bash
cd ~/.claude/skills/调研\&分析/scripts

# 关键词搜索
python v2ex_search.py --query "Claude Code"

# 限定结果数量
python v2ex_search.py --query "AI" --size 20

# 按时间排序
python v2ex_search.py --query "GPT" --sort created

# 限定节点
python v2ex_search.py --query "效率" --node apple
```

### Reddit 搜索

使用 `research-by-reddit` 或 `pain-point-research` skill。

---

## 环境配置

### 必需的 API Keys

在 `~/.claude/secrets.env` 中配置：

```bash
# Perplexity (通过 OpenRouter)
OPENROUTER_API_KEY=sk-or-xxx

# Grok X搜索 (需要 X Premium)
XAI_API_KEY=xai-xxx
```

---

## 质量标准

### 信息质量
- **准确性** - 事实经过验证
- **时效性** - 标注信息时间
- **完整性** - 覆盖多个信息源
- **平衡性** - 呈现多方观点

### 分析质量
- **事实与观点分离** - 不混淆
- **置信度明确** - 该说不确定就说
- **逻辑清晰** - 结论有理有据
- **可操作** - 建议具体可执行

---

## 注意事项

1. **不要跳过 Fact-check** - 这是区分高质量调研和普通搜索的关键
2. **标注不确定性** - 宁可说不确定，也不要误导
3. **区分事实和观点** - 这是分析的基础
4. **多信息源交叉验证** - 单一来源不可靠
5. **保留原始来源** - 方便追溯和验证

---

## 输出配置

### 默认输出目录

```
/Users/liuyishou/usr/odyssey/0 收集箱/research/
```

所有调研报告保存到此目录，命名格式：`{主题}_调研报告.md`
