# 小红书账号运营系统 - 架构设计

## 一、核心理念

**一个账号，多个内容系列，统一的生命周期管理**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         小红书账号运营系统                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐           │
│   │ B站UP主  │   │ AI工具   │   │ 读书笔记  │   │ 日常分享  │  ...      │
│   │ 系列     │   │ 推荐系列  │   │ 系列     │   │ 系列     │           │
│   └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘           │
│        │              │              │              │                   │
│        └──────────────┴──────────────┴──────────────┘                   │
│                              │                                          │
│                    ┌─────────▼─────────┐                               │
│                    │   统一内容队列    │                               │
│                    │   (content-queue) │                               │
│                    └─────────┬─────────┘                               │
│                              │                                          │
│                    ┌─────────▼─────────┐                               │
│                    │   发布 & 归档     │                               │
│                    │   (published)     │                               │
│                    └─────────┬─────────┘                               │
│                              │                                          │
│                    ┌─────────▼─────────┐                               │
│                    │   数据追踪        │                               │
│                    │   D1 / D7 / D30   │                               │
│                    └─────────┬─────────┘                               │
│                              │                                          │
│                    ┌─────────▼─────────┐                               │
│                    │   复盘 & 优化     │                               │
│                    │   (analytics)     │                               │
│                    └───────────────────┘                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 二、目录结构

```
~/.claude/agents/xhs-account-ops/
├── config.json                 # 全局配置
├── dashboard.html              # 可视化面板
├── ARCHITECTURE.md             # 本文档
│
├── series/                     # 【新】系列定义
│   ├── _template.json          # 系列模板
│   ├── bilibili-up.json        # B站UP主系列配置
│   ├── ai-tools.json           # AI工具推荐系列
│   └── reading-notes.json      # 读书笔记系列
│
├── research/                   # 调研素材库
│   └── {series-id}/            # 按系列分组
│       ├── index.json          # 选题索引
│       └── {subject}.json      # 单个选题调研
│
├── content-queue/              # 待发布队列（跨系列）
│   └── {id}.json               # 单条待发内容
│
├── published/                  # 已发布内容（跨系列）
│   └── {YYYYMM}/               # 按月归档
│       └── {date}_{id}.json    # 发布记录
│
└── analytics/                  # 数据分析
    ├── tracking/               # 数据追踪记录
    │   └── {post_id}.json      # 单条笔记的追踪数据
    ├── reports/                # 复盘报告
    │   ├── weekly/             # 周报
    │   └── monthly/            # 月报
    └── insights.json           # 累积洞察（什么类型表现好）
```

## 三、数据结构

### 3.1 series/{series-id}.json - 系列定义

```json
{
  "id": "bilibili-up",
  "name": "B站UP主介绍",
  "description": "挖掘UP主老粉才知道的梗，制作反差型内容",
  "status": "active",           // active | paused | archived
  "created_at": "2026-02-02",

  "content_template": {
    "style": "反差揭秘",
    "image_count": 2,
    "cover_style": "线刻肖像",
    "second_image_style": "手绘白板"
  },

  "research_template": {
    "dimensions": ["人设反差", "经典语录", "老粉梗", "隐藏技能"],
    "search_keywords": ["{name} 名场面", "{name} 梗 老粉", "{name} 反差"]
  },

  "performance": {
    "total_published": 1,
    "avg_likes": 0,
    "avg_comments": 0,
    "avg_collects": 0,
    "best_post": null,
    "worst_post": null
  }
}
```

### 3.2 content-queue/{id}.json - 待发内容（增强版）

```json
{
  "id": "uuid-xxx",
  "series_id": "bilibili-up",
  "subject": "影视飓风",
  "status": "ready",              // draft | ready | scheduled | publishing

  "scheduled_at": null,           // 定时发布时间
  "priority": 1,                  // 发布优先级

  "content": {
    "title": "xxx",
    "body": "xxx",
    "tags": [],
    "images": []
  },

  "research_ref": "research/bilibili-up/yingshijufeng.json",
  "created_at": "2026-02-02",
  "updated_at": "2026-02-02",

  "checklist": {
    "title_under_20": true,
    "body_under_1000": true,
    "images_ready": true,
    "tags_added": true
  }
}
```

### 3.3 published/{YYYYMM}/{date}_{id}.json - 发布记录（增强版）

```json
{
  "id": "20260202_fengge",
  "series_id": "bilibili-up",
  "subject": "峰哥亡命天涯",

  "published_at": "2026-02-02T15:30:00+08:00",
  "post_id": "xhs_post_id",
  "post_url": "https://www.xiaohongshu.com/...",

  "content": { /* 发布时的内容快照 */ },

  "metrics": {
    "D0": { "likes": 0, "comments": 0, "collects": 0, "views": 0, "recorded_at": "..." },
    "D1": { "likes": 10, "comments": 2, "collects": 5, "views": 200, "recorded_at": "..." },
    "D7": null,
    "D30": null
  },

  "evaluation": {
    "score": null,                // A/B/C/D/F 评级
    "vs_series_avg": null,        // 对比系列平均值
    "learnings": null,            // 复盘总结
    "tags": []                    // 标签：爆款/平稳/扑街
  }
}
```

### 3.4 analytics/insights.json - 累积洞察

```json
{
  "updated_at": "2026-02-02",

  "series_ranking": [
    { "series_id": "bilibili-up", "avg_engagement": 120, "post_count": 1 }
  ],

  "best_practices": [
    {
      "insight": "反差类内容评论率高于平均 50%",
      "evidence": ["post_id_1", "post_id_2"],
      "confidence": "high"
    }
  ],

  "time_analysis": {
    "best_publish_hour": 20,      // 晚8点
    "best_publish_day": "saturday"
  },

  "tag_performance": {
    "B站宝藏UP主": { "avg_likes": 100, "usage_count": 1 },
    "反差感": { "avg_likes": 100, "usage_count": 1 }
  }
}
```

## 四、后评估机制

### 4.1 数据追踪时间点

| 时间点 | 触发方式 | 追踪内容 |
|--------|----------|----------|
| D0 | 发布后立即 | 初始数据（通常为0） |
| D1 | 发布后24h | 首日表现，判断是否起量 |
| D7 | 发布后7天 | 稳定期数据，判断长尾 |
| D30 | 发布后30天 | 最终数据，用于归档评分 |

### 4.2 评分规则

```
评分 = 加权得分 / 系列平均值

加权公式：
  互动分 = likes × 1 + comments × 3 + collects × 2

评级标准（相对系列平均）：
  A: > 200%  (爆款)
  B: 120-200% (优秀)
  C: 80-120% (正常)
  D: 50-80%  (低于预期)
  F: < 50%   (扑街)
```

### 4.3 自动复盘报告

**周报模板**：

```markdown
# 小红书周报 2026-W05

## 本周数据
- 发布: 3 条
- 总互动: 150 (点赞 100 / 评论 20 / 收藏 30)
- 平均互动: 50

## 最佳表现
- 【标题】- 互动 80，高于平均 60%
- 原因分析：反差点击中目标受众

## 待改进
- 【标题】- 互动 20，低于平均 60%
- 原因分析：选题太小众

## 下周计划
- 继续 B站UP主系列（剩余 5 个）
- 尝试 AI工具系列首发
```

## 五、工作流

### 5.1 新建系列

```
1. 创建 series/{series-id}.json
2. 创建 research/{series-id}/index.json
3. Dashboard 自动识别新系列
```

### 5.2 内容生产流程

```
选题调研 → 入队 → 审核 → 发布 → 追踪 → 复盘
   │         │       │       │       │       │
   ▼         ▼       ▼       ▼       ▼       ▼
research/  queue/  checklist  published/  tracking/  reports/
```

### 5.3 定时任务（可选）

| 任务 | 频率 | 内容 |
|------|------|------|
| 数据追踪 | 每日 | 检查需要追踪 D1/D7/D30 的笔记 |
| 周报生成 | 每周日 | 汇总本周数据，生成报告 |
| 月报生成 | 每月1日 | 汇总上月数据，更新 insights |

## 六、Dashboard 功能升级

### 6.1 首页概览

- 全账号数据：总发布/总互动/粉丝变化
- 系列卡片：每个活跃系列的进度和表现
- 待办事项：需要追踪的笔记、待发布内容

### 6.2 系列详情页

- 选题看板（Kanban）
- 系列表现趋势图
- 最佳/最差内容对比

### 6.3 数据分析页

- 时间维度：按周/月查看表现
- 内容维度：哪类内容表现好
- 标签分析：哪些标签带来流量

### 6.4 复盘页

- 周报/月报列表
- 累积洞察展示
- 最佳实践库

## 七、下一步

1. **迁移现有数据** - 将 bilibili-up 迁移到新结构
2. **升级 Dashboard** - 支持多系列切换
3. **实现数据追踪** - 定时获取小红书数据
4. **实现自动复盘** - 生成周报/月报
