---
name: research
shortname: research
description: 深度调研工具，支持多信息源并发搜索、多任务类型策略。可指定信息源（reddit/twitter/perplexity/v2ex）或任务类型（痛点挖掘/舆情分析/投资情绪/技术调研）。
version: 5.0.0
author: Claude
allowed-tools: Bash(python:*), Read, Write, Glob, WebSearch, WebFetch
model: sonnet
tags: [research, analysis, reddit, twitter, perplexity, pain-point, sentiment, investment]
---

# Research - 深度调研工具

## 架构概览

本 skill 采用**策略模式**设计，支持灵活的信息源调度和任务类型切换：

```
┌─────────────────────────────────────────────────────────────┐
│                     Research Skill                          │
├─────────────────────────────────────────────────────────────┤
│  SourceStrategy（信息源策略）  │  TaskTypeStrategy（任务类型策略）│
│  - 默认：全部并发              │  - 默认：通用 SOP              │
│  - 指定：仅用指定信息源        │  - 指定：特定任务流程          │
└─────────────────────────────────────────────────────────────┘
```

---

## 一、信息源策略（SourceStrategy）

### 1.1 可用信息源

| ID | 信息源 | 工具 | 特点 | 适用场景 |
|----|-------|------|------|---------|
| `perplexity` | Perplexity | `perplexity_research.py` | 全网搜索、带引用 | 综合调研、事实查询 |
| `twitter` | Grok X/Twitter | `grok_x_search.py` | 实时数据（默认最近7天） | 舆情、KOL观点、实时事件 |
| `reddit` | Reddit | `analyze_reddit.py` | 深度讨论、真实反馈 | 用户痛点、产品评价 |
| `v2ex` | V2EX | `v2ex_search.py` | 中文技术社区 | 技术调研、中文用户反馈 |
| `web` | WebSearch/WebFetch | 内置工具 | 通用搜索、官方来源 | 补充搜索、一手资料 |

### 1.2 调度规则

**默认行为**：不指定信息源时，**全部并发**执行

**指定信息源**：用户明确提及时，**仅使用指定信息源**

| 用户输入 | 调度行为 |
|---------|---------|
| "调研 XX" | 全部信息源并发 |
| "Reddit 上怎么看 XX" | 仅使用 Reddit |
| "Twitter/X 上的讨论" | 仅使用 Grok X/Twitter |
| "用 Perplexity 查一下" | 仅使用 Perplexity |
| "V2EX 上的评价" | 仅使用 V2EX |
| "Reddit 和 Twitter" | 并发 Reddit + Twitter |

### 1.3 信息源使用示例

**注意**：搜索能力已统一到 `api-fetch` skill，以下路径为软链接。

```bash
# 统一入口（推荐）
cd ~/.claude/skills/api-fetch/search

# Perplexity 全网搜索
python perplexity.py --query "主题" --deep

# Grok X/Twitter 搜索（默认最近7天）
python twitter.py --query "主题"

# Reddit 搜索
python reddit.py --query "主题" --search-subreddit all --limit 12 --include-comments

# V2EX 中文社区搜索
python v2ex.py --query "主题" --size 10
```

**向后兼容**：旧路径 `~/.claude/skills/research/scripts/sources/` 仍可使用（软链接）。

---

## 二、任务类型策略（TaskTypeStrategy）

### 2.1 可用任务类型

| ID | 任务类型 | 触发词 | 核心指标 | 报告模板 |
|----|---------|-------|---------|---------|
| `general` | 通用调研 | "调研"、"分析" | 事实/观点分离 | 通用 SOP 报告 |
| `pain_point` | 痛点挖掘 | "痛点"、"需求"、"用户声音" | 情绪强度、频率 | 痛点调研报告 |
| `sentiment` | 舆情分析 | "舆情"、"口碑"、"评价" | 正负比例、趋势 | 舆情分析报告 |
| `investment` | 投资情绪 | "投资"、"股票"、"情绪" | 多空比例、催化剂 | 投资情绪报告 |
| `tech` | 技术调研 | "技术"、"框架"、"选型" | 采用趋势、迁移方向 | 技术趋势报告 |

### 2.2 调度规则

**默认行为**：不指定任务类型时，使用**通用 SOP 流程**

**指定任务类型**：用户明确提及时，使用**特定任务流程**

| 用户输入 | 任务类型 |
|---------|---------|
| "调研 XX" | `general` - 通用 SOP |
| "挖掘用户痛点" | `pain_point` - 痛点挖掘 |
| "舆情怎么样" | `sentiment` - 舆情分析 |
| "Reddit 对 NVDA 的情绪" | `investment` - 投资情绪 |
| "Rust vs Go 怎么选" | `tech` - 技术调研 |

---

## 三、通用 SOP 流程（TaskType: general）

```
信息源并发搜索 → 资料整合 → 事实/观点分离 → Fact-check → Insight → 数据可视化
```

### 3.1 资料整合

1. **去重** - 相同信息只保留最权威来源
2. **分类** - 按主题/维度组织
3. **标注来源** - 每条信息标明出处
4. **时间排序** - 注明信息时间，优先最新

### 3.2 事实 vs 观点 分离

**IMPORTANT**: 这是调研报告的核心输出，必须独立成章，每条 item 必须标注时间。

**事实 (Facts)** - 可验证、客观的信息：
- 数字：融资金额、用户数、市场规模
- 日期：发布时间、里程碑事件
- 事件：收购、合作、产品发布
- 技术指标：性能数据、准确率
- 官方声明：公司公告、财报数据

**观点 (Opinions)** - 主观判断、无法直接验证：
- 评价：好用/难用、值得/不值
- 预测：未来趋势、市场走向
- 比较：A比B好、X是最佳选择
- 情感：喜欢/讨厌、期待/失望
- 推荐：建议使用、不推荐

**输出格式要求**：

```markdown
## 事实清单

| # | 事实 | 时间 | 来源 | 置信度 |
|---|------|------|------|--------|
| 1 | Claude Code 发布 | 2024-10 | Anthropic 官方 | [✓] |
| 2 | 支持 MCP 协议 | 2024-11 | GitHub Release | [✓] |
| 3 | 月活用户 10 万+ | 2025-06 | 第三方估算 | [⚠] |

## 观点汇总

| # | 观点 | 时间 | 来源 | 倾向 |
|---|------|------|------|------|
| 1 | "写代码无敌，GPT 不是对手" | 2025-07 | V2EX @用户A | 正面 |
| 2 | "服从性不如 Cursor" | 2025-06 | V2EX @用户B | 负面 |
| 3 | "需要清晰需求才能发挥" | 2025-12 | Reddit u/xxx | 中立 |
```

**时间标注规则**：
- 精确到月：`2025-07`
- 无法确定月份时：`2025 年`
- 无法确定年份时：`日期不详`
- 时间范围：`2025-06 ~ 2025-12`

### 3.3 Fact-check

**置信度标注**：
- `[✓]` 已验证 - 有一手来源确认
- `[⚠]` 待验证 - 仅有二手来源，或信息有条件限定
- `[?]` 推测 - 基于逻辑推断，无直接证据
- `[✗]` 存疑 - 发现矛盾信息，需进一步核实

### 3.4 数据可视化（后置增强）

**触发条件**：当报告中包含大量可量化数据时，应添加 ASCII 可视化图表增强可读性。

**适用场景**：
- 数量对比（粉丝数、播放量、市场规模）
- 时间序列（月度/年度数据）
- 占比分布（市场份额、分区比例）
- 排名数据（TOP N 榜单）

**可视化模板**：

**1. 横向柱状图（数量对比）**
```
## 粉丝量排名（单位：万）

罗翔说刑法: ████████████████████████████████ 3200万
老番茄:     ████████████████████ 2000万
一数:       ████████████████████ 2000万
何同学:     ████████████ 1200万
影视飓风:   ████████ 800万
```

**2. 时间序列图（趋势变化）**
```
## 百大UP主首次入选人数变化

2022: ████████████████████████████████████████████████████████████ 60人
2023: ████████████████████████████████████████████ 45人
2024: ████████████████████████████████ 35人
2025: ████████████████████████████ 28人 (历史最低)
```

**3. 占比分布图（百分比）**
```
## 2025百大UP主分区分布

游戏区:  ██████████████████████ 22% (22位)
知识区:  █████████████████████ 21% (21位)
生活区:  ████████████████ 16% (16位)
影视区:  ██████████ 10% (10位)
其他:    ███████████████████████████████ 31% (31位)
```

**4. 对比矩阵（多维度）**
```
## 头部UP主特征对比

              粉丝量    更新频率    平均时长    连续百大
罗翔说刑法    ●●●●●    ●●○○○      ●●●○○      6年
老番茄        ●●●●○    ●●●○○      ●●●●○      8年
何同学        ●●●○○    ●○○○○      ●●●●●      回归
影视飓风      ●●○○○    ●●●●○      ●●●●●      3年

● = 高  ○ = 低
```

**绘制规则**：
1. **比例准确** - █ 数量与数值成正比，最大值对齐
2. **标签清晰** - 左侧标签对齐，右侧标注具体数值
3. **单位明确** - 图表标题注明单位
4. **降序排列** - 从大到小排列，便于比较
5. **适度简化** - 数据量过多时取 TOP 5-10

**输出位置**：
- 在报告的「执行摘要」或「深度分析」章节中穿插
- 紧跟相关数据表格之后
- 作为报告结尾的「数据一览」独立章节

### 3.5 通用报告模板

```markdown
# [主题] 调研报告

---

## 执行流程

### 流程图

```
1. 信息源并发搜索
   ├─ ✓/✗ Perplexity (sonar-deep-research/OpenRouter) → [结果]
   ├─ ✓/✗ Grok X (grok-4-1-fast/xAI) → [结果]
   ├─ ✓/✗ Reddit (Reddit API) → [结果]
   ├─ ✓/✗ V2EX (SOV2EX API) → [结果]
   └─ ✓/✗ WebSearch (Claude Search) → [结果]
        ↓
2. 资料整合 → 3. 事实/观点分离 → 4. Fact-check → 5. Insight → 6. 数据可视化
```

### 信息源详情

| 信息源 | 状态 | 模型/API | 执行情况 |
|-------|:----:|---------|---------|

---

## 执行摘要

[3-5 条核心发现]

---

## 事实清单

| # | 事实 | 时间 | 来源 | 置信度 |
|---|------|------|------|--------|
| 1 | [可验证的客观信息] | YYYY-MM | [来源] | [✓]/[⚠]/[?] |
| 2 | ... | ... | ... | ... |

**置信度说明**：
- `[✓]` 已验证 - 一手来源确认
- `[⚠]` 待验证 - 二手来源或有条件限定
- `[?]` 推测 - 基于逻辑推断

---

## 观点汇总

| # | 观点 | 时间 | 来源 | 倾向 |
|---|------|------|------|------|
| 1 | "[原话或摘要]" | YYYY-MM | [平台 @用户] | 正面/负面/中立 |
| 2 | ... | ... | ... | ... |

**观点分布**：正面 X 条 / 负面 Y 条 / 中立 Z 条

---

## 深度分析
## 洞见与建议
## 风险与不确定性

---

## 数据一览（可选，数据密集型报告必选）

[ASCII 可视化图表，展示报告中的关键量化数据]

## 附录
```

---

## 四、痛点挖掘流程（TaskType: pain_point）

### 4.1 搜索模板

```python
PAIN_TEMPLATES = {
    "emotion_trigger": [
        "tired of {topic}",
        "frustrated with {topic}",
        "why does {topic} suck",
        "anyone else hate {topic}",
    ],
    "desire_seeking": [
        "wish there was {topic}",
        "how do I {topic}",
        "what actually works for {topic}",
    ],
    "pain_validation": [
        "anyone else struggling with {topic}",
        "can't figure out {topic}",
    ],
}
```

### 4.2 情绪强度评分

| 分数 | 标准 |
|-----|------|
| 10 | score>500，评论充满强烈情绪，多人高度共鸣 |
| 8-9 | score>200，明确的情绪倾向，评论活跃 |
| 6-7 | score>100，有情绪但不极端 |
| 4-5 | score<100，存在但不强烈 |
| 1-3 | 低互动，可能是个例 |

### 4.3 痛点报告模板

```markdown
# [主题] 痛点调研报告

## 核心发现
| 痛点 | 情绪强度 | 频率 | 产品机会 |
|-----|---------|-----|---------|

## 一级痛点（高需求+高情绪）
### 痛点1: [标题]
**用户原话：**
> "..."

**情绪强度：** X/10
**产品/内容机会：** ...

## 金句库
## 行动建议
```

---

## 五、舆情分析流程（TaskType: sentiment）

### 5.1 搜索模板

```python
SENTIMENT_TEMPLATES = {
    "positive": ["{topic} is amazing", "love {topic}"],
    "negative": ["{topic} is terrible", "hate {topic}"],
    "neutral": ["thoughts on {topic}", "honest opinion {topic}"],
}
```

### 5.2 舆情报告模板

```markdown
# [话题/品牌] 舆情分析报告

## 情绪概览
- 正面情绪占比：X%
- 负面情绪占比：X%
- 中性讨论占比：X%

## 关键观点
### 正面评价
### 负面评价
### 争议焦点

## 典型用户声音
## 风险提示
## 建议行动
```

---

## 六、投资情绪流程（TaskType: investment）

### 6.1 搜索模板

```python
INVESTMENT_TEMPLATES = {
    "bullish": ["{ticker} to the moon", "buying more {ticker}"],
    "bearish": ["{ticker} overvalued", "selling {ticker}"],
    "analysis": ["{ticker} DD", "{ticker} analysis"],
}
```

### 6.2 推荐 Subreddits

```python
FINANCE_SUBREDDITS = [
    "wallstreetbets", "stocks", "investing", "options",
    "cryptocurrency", "Bitcoin", "ethereum",
    "personalfinance", "Bogleheads", "dividends",
]
```

### 6.3 投资情绪报告模板

```markdown
# [标的] 投资情绪分析

## 情绪指标
- 多空比例：X:Y
- 讨论热度：高/中/低
- 情绪趋势：上升/平稳/下降

## 社区观点
### 看多理由
### 看空理由
### 关键风险

## 近期催化剂
## 散户关注点

**免责声明**：本报告仅供参考，不构成投资建议。Reddit 散户情绪常为反向指标。
```

---

## 七、技术调研流程（TaskType: tech）

### 7.1 搜索模板

```python
TECH_TEMPLATES = {
    "comparison": ["{tech1} vs {tech2}", "{tech} alternatives"],
    "experience": ["{tech} in production", "{tech} real world"],
    "learning": ["learning {tech}", "{tech} worth learning"],
}
```

### 7.2 推荐 Subreddits

```python
TECH_SUBREDDITS = [
    "programming", "webdev", "learnprogramming",
    "MachineLearning", "LocalLLaMA",
    "devops", "kubernetes",
    "reactjs", "node", "golang", "rust",
]
```

### 7.3 技术调研报告模板

```markdown
# [技术/框架] 社区调研

## 采用趋势
- 讨论热度变化
- 新用户 vs 老用户比例

## 使用场景
### 推荐场景
### 不推荐场景

## 优缺点汇总
### 社区认可的优点
### 社区反映的问题

## 替代方案对比
## 学习曲线评估
## 是否值得采用
```

---

## 八、环境配置

### API Keys（`~/.claude/secrets.env`）

```bash
# Perplexity (通过 OpenRouter)
OPENROUTER_API_KEY=sk-or-xxx

# Grok X/Twitter (需要 X Premium)
XAI_API_KEY=xai-xxx

# Reddit
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx
```

---

## 九、质量标准

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

## 十、注意事项

1. **不要跳过 Fact-check** - 这是区分高质量调研和普通搜索的关键
2. **标注不确定性** - 宁可说不确定，也不要误导
3. **区分事实和观点** - 这是分析的基础
4. **多信息源交叉验证** - 单一来源不可靠
5. **保留原始来源** - 方便追溯和验证
6. **投资调研仅供参考** - Reddit 情绪不代表投资建议
7. **样本偏差** - Reddit 用户主要是英语区年轻男性，V2EX 主要是中文技术人群

---

## 输出配置

### 默认输出目录

```
/Users/liuyishou/usr/odyssey/0 收集箱/research/
```

所有调研报告保存到此目录，命名格式：`{主题}_调研报告.md`
