---
name: pain-point-research
description: 基于Reddit深度挖掘用户真实痛点和需求。适用于YouTube选题调研、AI产品机会发现、市场需求验证、竞品用户反馈分析、舆情监控、投资调研、技术趋势分析等场景。自动生成多维度搜索、情绪强度评分、结构化报告。
allowed-tools: Bash(python:*), Read, Write, Glob, Grep
model: sonnet
---

# Reddit 深度调研工具

基于 Reddit API 进行多场景深度调研，支持痛点挖掘、舆情分析、投资调研、趋势追踪等。

## 适用场景

### 产品/内容类
1. **YouTube/自媒体选题** - 找到高情绪共鸣、高需求的内容选题
2. **产品机会发现** - 挖掘用户对现有工具的不满和未被满足的需求
3. **竞品用户分析** - 了解竞品用户的真实痛点和流失原因

### 市场/舆情类
4. **舆情监控** - 追踪特定话题/品牌/事件的社区讨论和情绪变化
5. **品牌口碑分析** - 分析用户对品牌/产品的真实评价
6. **热点事件追踪** - 了解社区对特定事件的反应和观点

### 投资/金融类
7. **投资情绪分析** - 分析散户对特定股票/加密货币/资产的情绪
8. **行业趋势调研** - 追踪特定行业的发展动态和用户关注点
9. **消费趋势分析** - 了解消费者对特定品类的态度变化

### 技术/趋势类
10. **技术选型调研** - 收集社区对不同技术方案的真实评价
11. **新兴趋势发现** - 发现正在兴起的技术/产品/概念
12. **开源项目口碑** - 分析开发者对开源项目的评价

## 核心搜索模板

### 1. 痛点挖掘类

```python
PAIN_TEMPLATES = {
    "emotion_trigger": [
        "tired of {topic}",
        "frustrated with {topic}",
        "why does {topic} suck",
        "anyone else hate {topic}",
        "sick of {topic}",
    ],
    "desire_seeking": [
        "wish there was {topic}",
        "how do I {topic}",
        "what actually works for {topic}",
        "best way to {topic}",
    ],
    "pain_validation": [
        "anyone else struggling with {topic}",
        "feeling stuck with {topic}",
        "can't figure out {topic}",
    ],
}
```

### 2. 舆情/口碑类

```python
SENTIMENT_TEMPLATES = {
    "positive": [
        "{topic} is amazing",
        "love {topic}",
        "{topic} changed my life",
        "finally {topic} works",
    ],
    "negative": [
        "{topic} is terrible",
        "hate {topic}",
        "{topic} ruined",
        "never using {topic} again",
    ],
    "neutral_discussion": [
        "thoughts on {topic}",
        "what do you think about {topic}",
        "{topic} discussion",
        "honest opinion {topic}",
    ],
}
```

### 3. 投资/金融类

```python
INVESTMENT_TEMPLATES = {
    "bullish": [
        "{ticker} to the moon",
        "buying more {ticker}",
        "{ticker} undervalued",
        "long {ticker}",
    ],
    "bearish": [
        "{ticker} overvalued",
        "selling {ticker}",
        "{ticker} crash",
        "short {ticker}",
    ],
    "analysis": [
        "{ticker} DD",  # Due Diligence
        "{ticker} analysis",
        "{ticker} fundamentals",
        "is {ticker} worth buying",
    ],
    "sentiment": [
        "what happened to {ticker}",
        "{ticker} news",
        "why is {ticker} down",
        "why is {ticker} up",
    ],
}
```

### 4. 技术趋势类

```python
TECH_TEMPLATES = {
    "comparison": [
        "{tech1} vs {tech2}",
        "{tech} alternatives",
        "switching from {tech}",
        "migrating to {tech}",
    ],
    "experience": [
        "{tech} in production",
        "{tech} real world",
        "using {tech} for",
        "{tech} experience",
    ],
    "learning": [
        "learning {tech}",
        "{tech} worth learning",
        "{tech} roadmap",
        "how long to learn {tech}",
    ],
}
```

## Subreddit 分类

### 投资/金融
```python
FINANCE_SUBREDDITS = [
    "wallstreetbets", "stocks", "investing", "options",
    "cryptocurrency", "Bitcoin", "ethereum", "CryptoMarkets",
    "personalfinance", "financialindependence", "Fire",
    "Bogleheads", "dividends", "ValueInvesting",
    # 中概股/亚洲市场
    "ChinaStocks", "Sino",
]
```

### 科技/编程
```python
TECH_SUBREDDITS = [
    "programming", "webdev", "learnprogramming",
    "MachineLearning", "artificial", "LocalLLaMA",
    "devops", "sysadmin", "kubernetes",
    "reactjs", "node", "golang", "rust",
    "technology", "gadgets", "hardware",
]
```

### 职场/生活
```python
CAREER_SUBREDDITS = [
    "careerguidance", "jobs", "careeradvice",
    "cscareerquestions", "ExperiencedDevs",
    "antiwork", "workreform", "overemployed",
    "Entrepreneur", "startups", "smallbusiness",
]
```

### 消费/生活方式
```python
CONSUMER_SUBREDDITS = [
    "BuyItForLife", "Frugal", "deals",
    "homeautomation", "smarthome",
    "cars", "electricvehicles",
    "Apple", "Android", "GooglePixel",
]
```

### 舆情/新闻
```python
NEWS_SUBREDDITS = [
    "news", "worldnews", "politics",
    "technology", "business", "economics",
    "OutOfTheLoop", "explainlikeimfive",
]
```

## 调研流程

### Step 1: 确定调研类型

询问用户：
- **调研主题**：具体话题/品牌/股票/技术
- **调研类型**：痛点挖掘/舆情分析/投资情绪/技术调研
- **时间范围**：最近一周/一月/一年
- **深度要求**：快速概览/深度分析

### Step 2: 选择搜索策略

根据调研类型选择模板：

| 类型 | 模板 | 核心指标 |
|-----|------|---------|
| 痛点挖掘 | PAIN_TEMPLATES | 情绪强度、出现频率 |
| 舆情分析 | SENTIMENT_TEMPLATES | 正负比例、情绪趋势 |
| 投资调研 | INVESTMENT_TEMPLATES | 多空比例、关键事件 |
| 技术趋势 | TECH_TEMPLATES | 采用趋势、迁移方向 |

### Step 3: 执行多维度搜索

```bash
cd /Users/liuyishou/.claude/skills/research-by-reddit/scripts
export $(cat ../.env | grep -v '^#' | xargs)

# 并行执行多个搜索
python analyze_reddit.py \
  --query "{搜索词}" \
  --search-subreddit {subreddit} \
  --search-sort top \
  --time-filter month \
  --limit 12 \
  --include-comments \
  --comment-limit 8 \
  --analysis-language zh \
  --output-md {output}.md
```

### Step 4: 整合分析

根据调研类型生成不同格式的报告。

## 输出报告模板

### 模板A: 痛点调研报告

```markdown
# [主题] 痛点调研报告

## 核心发现
| 痛点 | 情绪强度 | 频率 | 产品机会 |
|-----|---------|-----|---------|

## 一级痛点（高需求+高情绪）
### 痛点1: [标题]
**Reddit原话：**
> "..."

**情绪强度：** X/10
**产品/内容机会：** ...

## 金句库
## 行动建议
```

### 模板B: 舆情分析报告

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

### 模板C: 投资情绪报告

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
## 信息来源质量评估
```

### 模板D: 技术趋势报告

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

## 预设调研场景

### 场景1: youtube_选题
YouTube/自媒体内容选题调研

### 场景2: ai_product
AI/SaaS产品机会发现

### 场景3: competitor_分析
竞品用户反馈分析

### 场景4: sentiment_品牌
品牌/产品舆情监控

### 场景5: investment_股票
股票/加密货币投资情绪

### 场景6: tech_趋势
技术选型/趋势调研

### 场景7: 自定义
用户自定义调研维度

## 使用示例

### 示例1: 舆情分析
```
用户：帮我看看Reddit上对OpenAI的舆情怎么样

Claude：
1. 确认调研类型：舆情分析
2. 选择相关subreddits：ChatGPT, OpenAI, artificial, LocalLLaMA
3. 使用SENTIMENT_TEMPLATES搜索
4. 生成《OpenAI舆情分析报告》
```

### 示例2: 投资情绪
```
用户：Reddit上对NVIDIA的情绪怎么样

Claude：
1. 确认调研类型：投资情绪
2. 选择相关subreddits：wallstreetbets, stocks, investing, nvda
3. 使用INVESTMENT_TEMPLATES搜索
4. 生成《NVDA投资情绪报告》
```

### 示例3: 技术调研
```
用户：调研一下Rust和Go的社区评价

Claude：
1. 确认调研类型：技术对比
2. 选择相关subreddits：rust, golang, programming
3. 使用TECH_TEMPLATES搜索
4. 生成《Rust vs Go 社区调研报告》
```

### 示例4: 热点事件
```
用户：Reddit上怎么看DeepSeek

Claude：
1. 确认调研类型：舆情+技术趋势
2. 选择相关subreddits：LocalLLaMA, MachineLearning, artificial
3. 混合使用SENTIMENT + TECH模板
4. 生成《DeepSeek社区反响报告》
```

## 情绪强度评分标准

| 分数 | 标准 |
|-----|------|
| 10 | score>500，评论充满强烈情绪，多人高度共鸣 |
| 8-9 | score>200，明确的情绪倾向，评论活跃 |
| 6-7 | score>100，有情绪但不极端 |
| 4-5 | score<100，存在但不强烈 |
| 1-3 | 低互动，可能是个例 |

## 依赖

本skill依赖 `research-by-reddit` skill的底层工具：

```
/Users/liuyishou/.claude/skills/research-by-reddit/scripts/analyze_reddit.py
/Users/liuyishou/.claude/skills/research-by-reddit/.env
```

需要配置：
- REDDIT_CLIENT_ID
- REDDIT_CLIENT_SECRET
- OPENROUTER_API_KEY

## 注意事项

1. **投资调研仅供参考**：Reddit情绪不代表投资建议，散户情绪常常是反向指标
2. **时效性**：舆情和投资情绪变化快，注意数据时效
3. **样本偏差**：Reddit用户不代表全部人群，主要是英语区年轻男性
4. **并行搜索**：多维度搜索应并行执行提高效率
5. **原话保留**：报告中必须包含用户原话
