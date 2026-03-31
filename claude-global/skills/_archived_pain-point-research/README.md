# Pain Point Research - Reddit 深度调研工具

基于 Reddit 深度挖掘用户真实痛点和需求，支持产品调研、舆情分析、投资情绪、技术趋势等多场景。

## 功能特点

- **多场景支持**：痛点挖掘、舆情分析、投资情绪、技术趋势
- **多维度搜索**：情绪触发、渴望搜索、痛点验证等搜索模式
- **情绪强度评分**：1-10分量化情绪的强度
- **用户原话提取**：保留真实表达，可直接用于内容创作
- **预设调研模板**：11种预设场景开箱即用

## 适用场景

### 产品/内容类
| 场景 | 描述 | 输出 |
|-----|------|------|
| YouTube选题 | 找到高情绪共鸣的内容选题 | 选题列表+标题公式+金句库 |
| AI产品机会 | 发现现有工具的痛点和缺口 | 痛点列表+产品方向+验证数据 |
| 竞品分析 | 分析竞品用户的流失原因 | 流失原因+替代需求+差异化方向 |

### 舆情/市场类
| 场景 | 描述 | 输出 |
|-----|------|------|
| 品牌舆情 | 监控品牌/产品的社区讨论 | 正负比例+关键观点+风险提示 |
| 热点追踪 | 了解社区对特定事件的反应 | 观点汇总+情绪趋势+争议焦点 |

### 投资/金融类
| 场景 | 描述 | 输出 |
|-----|------|------|
| 股票情绪 | 分析散户对特定股票的情绪 | 多空比例+关键事件+风险点 |
| 加密货币 | 追踪加密货币社区情绪 | 情绪指标+热点话题+预警信号 |
| 中概股 | 调研中概股相关讨论 | 观点汇总+风险分析+趋势判断 |

### 技术/趋势类
| 场景 | 描述 | 输出 |
|-----|------|------|
| 技术对比 | 收集技术方案的社区评价 | 优缺点对比+使用场景+迁移趋势 |
| 框架调研 | 评估前端/后端框架选型 | 采用趋势+痛点+学习曲线 |

## 快速开始

### 1. 使用预设模板

```bash
cd /Users/liuyishou/.claude/skills/pain-point-research

# 查看所有可用的预设场景
python research_templates.py

# 生成特定场景的调研计划
python research_templates.py youtube_职场      # 职场新人痛点
python research_templates.py ai_product        # AI产品机会
python research_templates.py notion_competitor # Notion竞品分析
python research_templates.py sentiment_openai  # OpenAI舆情
python research_templates.py sentiment_tesla   # Tesla舆情
python research_templates.py investment_nvda   # NVIDIA投资情绪
python research_templates.py investment_btc    # 比特币情绪
python research_templates.py investment_china  # 中概股调研
python research_templates.py tech_rust_go      # Rust vs Go对比
python research_templates.py tech_framework    # 前端框架调研
python research_templates.py hot_deepseek      # DeepSeek热点
```

### 2. 自定义调研

```bash
# 格式：custom:类型:话题1,话题2:subreddit分类
python research_templates.py "custom:sentiment:Cursor,Windsurf:ai"
python research_templates.py "custom:investment:AAPL,MSFT:finance"
python research_templates.py "custom:pain:remote work,WFH:career"
```

### 3. 在 Claude Code 中使用

直接告诉 Claude 你想调研什么：

```
# 痛点调研
帮我调研一下20-30岁职场新人的痛点，我想做YouTube内容
调研一下Notion用户的痛点，我想做替代产品

# 舆情分析
帮我看看Reddit上对OpenAI的舆情怎么样
调研一下Tesla最近在社区的口碑

# 投资情绪
Reddit上对NVIDIA的情绪怎么样
帮我看看比特币社区最近的情绪

# 技术调研
调研一下Rust和Go的社区评价
帮我看看Next.js和Remix的对比讨论
```

Claude 会自动：
1. 识别调研类型
2. 选择合适的搜索模板和subreddit
3. 并行执行多维度搜索
4. 生成结构化报告

## 预设场景详解

### 痛点/产品类

#### youtube_职场
- **目标**：20-30岁职场新人痛点挖掘
- **搜索维度**：职业困境、效率问题、副业需求
- **Subreddits**：careerguidance, jobs, productivity, antiwork, sidehustle

#### ai_product
- **目标**：AI产品机会发现
- **搜索维度**：AI工具痛点、工作流需求、本地LLM
- **Subreddits**：ChatGPT, LocalLLaMA, SideProject, artificial

#### notion_competitor
- **目标**：Notion竞品分析
- **搜索维度**：性能痛点、迁移需求、定价敏感度
- **Subreddits**：Notion, ObsidianMD, productivity, PKMS

### 舆情/市场类

#### sentiment_openai
- **目标**：OpenAI/ChatGPT舆情监控
- **搜索维度**：正面评价、负面评价、争议话题
- **Subreddits**：ChatGPT, OpenAI, artificial, LocalLLaMA

#### sentiment_tesla
- **目标**：Tesla品牌舆情
- **搜索维度**：产品评价、CEO争议、竞品对比
- **Subreddits**：teslamotors, electricvehicles, technology, cars

### 投资/金融类

#### investment_nvda
- **目标**：NVIDIA投资情绪
- **搜索维度**：看多理由、看空观点、关键风险
- **Subreddits**：wallstreetbets, stocks, investing, nvidia

#### investment_btc
- **目标**：比特币投资情绪
- **搜索维度**：牛市信号、熊市担忧、监管动态
- **Subreddits**：Bitcoin, cryptocurrency, CryptoMarkets, ethtrader

#### investment_china
- **目标**：中概股调研
- **搜索维度**：政策风险、投资机会、退市担忧
- **Subreddits**：ChinaStocks, investing, stocks, Sino

### 技术/趋势类

#### tech_rust_go
- **目标**：Rust vs Go 技术对比
- **搜索维度**：性能对比、使用场景、学习曲线
- **Subreddits**：rust, golang, programming, ExperiencedDevs

#### tech_framework
- **目标**：前端框架调研
- **搜索维度**：React/Vue/Svelte对比、迁移趋势
- **Subreddits**：reactjs, vuejs, sveltejs, webdev

### 热点话题类

#### hot_deepseek
- **目标**：DeepSeek社区反响
- **搜索维度**：技术评价、使用体验、竞品对比
- **Subreddits**：LocalLLaMA, MachineLearning, artificial, China

## 输出报告格式

### 模板A: 痛点调研报告

```markdown
# [主题] 痛点调研报告

## 核心发现
| 痛点 | 情绪强度 | 频率 | 产品机会 |
|-----|---------|-----|---------|

## 一级痛点（高需求+高情绪）
### 痛点1: [标题]
**Reddit原话：**
> "直接引用用户原话..."

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
## 替代方案对比
## 是否值得采用
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

本 skill 依赖 `research-by-reddit` skill 的底层工具：

```
/Users/liuyishou/.claude/skills/research-by-reddit/scripts/analyze_reddit.py
/Users/liuyishou/.claude/skills/research-by-reddit/.env
```

需要配置的环境变量：
- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `OPENROUTER_API_KEY`

## 文件结构

```
pain-point-research/
├── SKILL.md              # Skill配置和完整使用说明
├── README.md             # 本文档
└── research_templates.py # 调研模板生成器
```

## 最佳实践

1. **并行搜索**：多个维度同时搜索，提高效率
2. **保留原话**：用户原话比总结更有说服力
3. **交叉验证**：同一观点在多个subreddit出现=高置信度
4. **情绪优先**：情绪强度高的内容往往更有价值
5. **注意时效**：舆情和投资情绪变化快，注意数据时效
6. **样本偏差**：Reddit用户主要是英语区年轻男性，不代表全部人群

## 注意事项

- **投资调研仅供参考**：Reddit情绪不代表投资建议，散户情绪常常是反向指标
- **舆情可能有偏**：Reddit社区有自己的文化和偏见
- **原话保留**：报告中必须包含用户原话以便验证

## 更新日志

- 2026-01-22: v2.0 - 扩展支持舆情分析、投资情绪、技术趋势等场景，新增8种预设模板
- 2026-01-22: v1.0 - 初始版本，支持YouTube选题、AI产品、竞品分析三种场景
