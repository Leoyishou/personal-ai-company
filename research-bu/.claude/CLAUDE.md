# 调研事业部 (Research BU)

> 信息杠杆：深度调研，将信息不对称变为决策优势

## 模块化规则

@/Users/liuyishou/usr/pac/pmo/rules/research-bu.md

## 事业部 Skills

### 信息采集
- `research` - 多信息源并发深度调研
- `research-by-reddit` - Reddit 专题调研
- `api-fetch` - 统一搜索与抓取
- `little-crawler` - 小红书/知乎数据采集
- `api-pdf2markdown` - PDF/文档解析

### 分析工具
- `api-openrouter` - 多模型交叉验证
- `concept-tree` - 概念树/知识结构生成
- `notebooklm` - NotebookLM 文档问答
- `chat-to-supabase` - 数据库查询
- `lakehouse` - DuckDB OLAP 数据分析

### 浏览器自动化
- `browse-use` - 无头浏览器采集
- `playwright-cli` - 网页交互自动化

## 调研类型

| 类型 | 说明 | 典型场景 |
|------|------|----------|
| 技术调研 | 框架选型、方案评估、API 能力评测 | "Remotion vs Motion Canvas 对比" |
| 市场调研 | 用户痛点、竞品分析、市场规模 | "AI 英语学习 App 竞品" |
| 投资调研 | 行业研究、公司分析、财报解读 | "NVIDIA 2026 Q1 财报分析" |
| 舆情分析 | 社交媒体情绪、热点追踪 | "Claude Code 用户评价趋势" |
| 人物/公司 | 背景调查、能力评估 | "某 KOL 的内容矩阵分析" |

## 工作流

1. 明确调研目标 → 2. 多源信息采集 → 3. 交叉验证分析 → 4. 结构化报告 → 5. 决策建议

## 核心原则

- **多源验证**：同一事实至少 2 个独立来源
- **区分事实与观点**：报告中明确标注
- **量化优先**：能用数据说话的不用定性描述
- **可追溯**：所有结论附带来源链接

## 输出规范

调研报告存放在 `./output/YYYYMMDD-主题/` 目录下，包含：
- `report.md` - 主报告
- `sources/` - 原始数据和截图
- `data/` - 结构化数据（CSV/JSON）

## 新调研入口

新调研项目放入 `./inbox/`。
