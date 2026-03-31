# AI Company 部门架构说明

## 概述

AI Company 是一个由多个专业 AI 部门组成的虚拟公司，每个部门都有专属的 AI Agent，配备了特定的技能和工具，能够协同完成复杂的任务。

## 核心通用能力

所有部门共享的基础能力：

### 🌐 WebFetchPlus
- Twitter/X 内容获取（推文、用户、时间线）
- 社交媒体下载（抖音、B站、小红书）
- 智能网页抓取（自动识别URL类型）
- 批量处理能力

### 🔍 Research
- 8种调研模式（技术、市场、竞品、人物等）
- 专业分析框架（SWOT、Porter五力、PEST）
- 结构化报告生成
- 4种调研深度控制

## 部门列表

### 🕵️ Intelligence Department (情报部)
**文件**: `intelligence-department.md`
**模型**: sonnet
**核心职责**: 信息收集、竞争情报、市场洞察、威胁监测

**专属能力**:
- 全网监测和追踪
- 竞争对手动态分析
- 威胁情报预警
- 多源信息交叉验证

---

### 🔬 Research Department (战投部)
**文件**: `research-department.md`
**模型**: opus
**核心职责**: 深度调研、竞品分析、行业研究、投资分析

**专属能力**:
- 技术评估和调研
- 投资机会分析
- 用户痛点挖掘
- 富途交易记录查询

---

### 📱 Product Department (产品部)
**文件**: `product-department.md`
**模型**: sonnet
**核心职责**: 产品规划、用户研究、功能设计、产品迭代

**专属能力**:
- 用户需求分析
- 竞品功能对比
- 产品路线图制定
- MVP定义

---

### 💻 Dev Department (开发部)
**文件**: `dev-department.md`
**模型**: sonnet
**核心职责**: 软件开发、系统架构、代码实现、技术支持

**专属能力**:
- 全栈开发
- 系统架构设计
- API集成
- 性能优化

---

### 🎨 Content & PR Department (内容与公关部)
**文件**: `content-pr-department.md`
**模型**: sonnet
**核心职责**: 内容创作、品牌传播、社交媒体运营、公关危机

**专属能力**:
- 多平台内容创作
- 社交媒体运营
- 品牌舆情监测
- 危机公关处理

---

### 🚀 Operations Department (运营部)
**文件**: `ops-department.md`
**模型**: sonnet
**核心职责**: 运营管理、数据分析、用户增长、流程优化

**专属能力**:
- 数据运营分析
- 用户增长策略
- 运营自动化
- 流程优化

---

### 💼 Business Unit (商务部)
**文件**: `business-unit.md`
**模型**: sonnet
**核心职责**: 商业拓展、合作洽谈、收入增长、客户管理

**专属能力**:
- 商机挖掘
- 客户背景调研
- 竞争定价分析
- 渠道管理

## 部门协作模式

### 情报驱动决策流程
```
Intelligence (情报收集) → Research (深度分析) → 各业务部门 (执行决策)
```

### 产品开发流程
```
Product (需求定义) → Research (技术调研) → Dev (开发实现) → Operations (上线运营)
```

### 市场推广流程
```
Intelligence (市场洞察) → Content&PR (内容创作) → Operations (推广执行) → Business (商业变现)
```

## 调用方式

### 通过Task工具调用特定部门
```python
# 调用情报部
Task(subagent_type="intelligence-department", prompt="分析这个链接的内容")

# 调用战投部
Task(subagent_type="research-department", prompt="深度调研AI行业")

# 调用产品部
Task(subagent_type="product-department", prompt="分析竞品功能")
```

### 部门技能使用示例
```python
# 情报部使用WebFetchPlus
Skill(skill: "webfetch-plus", args: "https://x.com/elonmusk/status/xxx")

# 战投部使用Research
Skill(skill: "research", args: "OpenAI --mode tech --depth deep")

# 内容部使用社交媒体发布
Skill(skill: "social-media-publish", args: "发布内容")
```

## 配置更新

所有部门配置文件都在 `~/.claude/agents/departments/` 目录下，可以通过编辑对应的 `.md` 文件来更新部门能力。

## 未来扩展

1. **新部门添加**:
   - Legal (法务部)
   - HR (人力资源部)
   - Finance (财务部)

2. **能力增强**:
   - AI决策支持系统
   - 自动化工作流
   - 跨部门数据共享平台

3. **集成更多工具**:
   - 项目管理工具
   - CRM系统
   - 数据分析平台

## 注意事项

1. 部门间信息共享需要通过明确的接口
2. 敏感信息处理需要遵守隐私规范
3. 各部门AI模型可根据任务复杂度调整
4. 定期更新部门能力以适应新需求