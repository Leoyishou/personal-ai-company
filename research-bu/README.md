# 调研事业部 - 信息杠杆

> 深度调研变为决策优势，服务其他三个事业部

## 一、核心信息

| 字段 | 值 |
|------|-----|
| Linear Team | R (调研事业部) |
| Initiative | 信息杠杆 |
| 启动命令 | `cd ~/usr/pac/research-bu && claude --dangerously-skip-permissions` |

## 二、调研类型（Linear Project）

| 项目 | 说明 | 协同 BU |
|------|------|---------|
| 技术调研 | 框架选型、方案评估 | 产品 |
| 市场调研 | 用户痛点、竞品分析 | 产品/内容 |
| 投资调研 | 行业研究、财报解读 | 投资 |
| 舆情分析 | 社媒情绪、热点追踪 | 内容 |
| 人物/公司 | 背景调查、深度分析 | 投资/内容 |

## 三、标签

### 调研阶段

选题 --> 采集 --> 分析 --> 报告 --> 应用

### 信息来源（可多选）

Reddit / Twitter/X / 小红书 / Perplexity / 一手数据

## 四、目录结构

```
research-bu/
├── inbox/                 # 临时项目
└── output/                # 调研报告产出
```

报告同时存储到：`~/usr/odyssey/0 收集箱/research/【MMDD】主题_调研报告.md`

## 五、跨 BU 协同

调研是其他 BU 的"智囊团"：

```
技术调研 --> 产品 BU 采用方案
市场调研 --> 产品方向 / 内容选题
投资调研 --> 投资决策
舆情分析 --> 内容选题
```

调研 Issue 完成后，如有可执行建议，在目标 BU 创建关联 Issue。

## 六、常用 Skills

| Skill | 用途 |
|-------|------|
| `research` | 多源并发调研 |
| `research-by-reddit` | Reddit 专项调研 |
| `api-fetch` | 网页抓取 |
| `api-openrouter` | 多模型分析 |
| `concept-tree` | 知识结构树 |
| `notebooklm` | NotebookLM 文档查询 |
