---
name: perplexity-research
description: 基于 Perplexity (通过 OpenRouter) 进行网络深度调研和实时搜索。支持快速搜索 (sonar-pro-search) 和深度研究 (sonar-deep-research) 两种模式，灵活切换。
allowed-tools: Bash(python:*), Read, Write, Glob
model: sonnet
---

# Perplexity 调研工具

通过 OpenRouter 调用 Perplexity 模型，进行实时网络搜索和深度调研分析。

## 模型说明

| 模型 | ID | 适用场景 | 特点 |
|-----|-----|---------|-----|
| **快速搜索** | `perplexity/sonar-pro-search` | 简单问题、事实查询、快速验证 | 响应快、成本低 |
| **深度研究** | `perplexity/sonar-deep-research` | 复杂调研、多角度分析、综合报告 | 更全面、带引用 |

## 快速开始

### 基础用法

```bash
cd /Users/liuyishou/.claude/skills/perplexity-research/scripts

# 快速搜索（默认）
python perplexity_research.py --query "2024年AI领域最重要的突破是什么"

# 深度研究
python perplexity_research.py --query "分析 Claude 和 GPT-4o 的技术差异" --deep

# 指定语言
python perplexity_research.py --query "What is MCP in Claude" --lang en
```

### 保存结果

```bash
# 保存为 Markdown
python perplexity_research.py --query "..." --output report.md

# 保存完整 JSON 响应
python perplexity_research.py --query "..." --output-json response.json
```

## 使用场景

### 1. 事实核查
```bash
python perplexity_research.py --query "DeepSeek R1的参数规模是多少"
```

### 2. 技术调研
```bash
python perplexity_research.py --query "2024年最流行的向量数据库对比" --deep
```

### 3. 市场分析
```bash
python perplexity_research.py --query "AI编程助手市场格局分析" --deep --lang zh
```

### 4. 竞品研究
```bash
python perplexity_research.py --query "Cursor vs Windsurf vs Claude Code 功能对比" --deep
```

### 5. 趋势追踪
```bash
python perplexity_research.py --query "2024年生成式AI的主要趋势"
```

## 参数说明

| 参数 | 说明 | 默认值 |
|-----|------|-------|
| `--query` | 调研问题（必填） | - |
| `--deep` | 使用深度研究模式 | False (使用快速搜索) |
| `--model` | 手动指定模型 | 自动选择 |
| `--lang` | 输出语言 (zh/en) | zh |
| `--output` | 保存结果到 Markdown 文件 | - |
| `--output-json` | 保存完整 JSON 响应 | - |
| `--temperature` | 采样温度 | 0.2 |
| `--max-tokens` | 最大输出 token | 4096 |

## 工作流建议

### Step 1: 确定调研类型

询问用户：
- **问题类型**：事实查询 / 对比分析 / 深度调研
- **输出语言**：中文 / 英文
- **深度要求**：快速回答 / 详细报告

### Step 2: 选择模式

| 场景 | 推荐模式 | 原因 |
|-----|---------|-----|
| 简单事实查询 | 快速搜索 | 响应快、够用 |
| 数据验证 | 快速搜索 | 效率优先 |
| 技术对比 | 深度研究 | 需要多角度 |
| 市场分析 | 深度研究 | 需要综合 |
| 投资调研 | 深度研究 | 需要引用 |

### Step 3: 执行调研

```bash
cd /Users/liuyishou/.claude/skills/perplexity-research/scripts

# 根据场景选择
python perplexity_research.py --query "..." [--deep] [--lang zh]
```

### Step 4: 整理输出

根据用户需求格式化结果：
- 直接输出回答
- 整理为结构化报告
- 提取关键信息

## 输出格式

### 默认输出
直接输出模型回答，包含引用来源（如有）

### Markdown 报告
```markdown
# 调研报告: [问题]

## 摘要
[核心发现]

## 详细分析
[模型回答]

## 来源
[引用列表]

---
模型: perplexity/sonar-deep-research
时间: 2024-01-26
```

## 与其他调研 skill 的区别

| Skill | 数据源 | 适用场景 |
|-------|-------|---------|
| **perplexity-research** | 全网实时搜索 | 事实查询、技术调研、市场分析 |
| research-by-reddit | Reddit 社区 | 用户痛点、舆情、情绪分析 |
| pain-point-research | Reddit 深度 | 产品机会、竞品分析 |

## 依赖

```bash
pip install requests python-dotenv
```

## 环境配置

需要 `OPENROUTER_API_KEY`，已在全局 CLAUDE.md 中配置。

## 使用示例

### 示例1: 快速问答
```
用户：DeepSeek R1 是什么时候发布的？

Claude：
[调用 perplexity/sonar-pro-search]
DeepSeek R1 于 2024 年 11 月发布...
```

### 示例2: 深度调研
```
用户：帮我调研一下 AI 编程助手的市场现状

Claude：
[调用 perplexity/sonar-deep-research]
生成《AI 编程助手市场调研报告》
```

### 示例3: 技术对比
```
用户：Claude MCP 和 OpenAI Function Calling 有什么区别

Claude：
[调用 perplexity/sonar-deep-research --deep]
生成技术对比分析...
```

## 注意事项

1. **实时性**：Perplexity 可搜索最新网页，适合时效性强的问题
2. **引用来源**：深度研究模式会返回引用，便于验证
3. **成本考虑**：深度研究成本较高，简单问题用快速搜索即可
4. **语言支持**：中英文都支持，可通过 --lang 指定输出语言
