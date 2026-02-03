# 小红书内容运营 - 数据模型

## 核心实体

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            实体关系图                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────┐                                                         │
│   │  Series  │ (可选归属)                                               │
│   │  系列    │◄─────────────────┐                                      │
│   └──────────┘                  │                                      │
│                                 │                                      │
│   ┌──────────┐           ┌──────┴─────┐                               │
│   │  Idea    │           │   Idea     │                               │
│   │ 独立灵感  │           │  系列灵感   │                               │
│   └────┬─────┘           └──────┬─────┘                               │
│        │                        │                                      │
│        └────────────┬───────────┘                                      │
│                     │                                                  │
│                     ▼                                                  │
│              ┌──────────┐                                              │
│              │ Content  │ ◄─────┐                                     │
│              │ 内容草稿  │       │                                     │
│              └────┬─────┘       │                                     │
│                   │             │                                      │
│         ┌────────┼────────┐    │                                      │
│         │        │        │    │                                      │
│         ▼        ▼        ▼    │                                      │
│    ┌────────┐ ┌────┐ ┌────────┐│                                      │
│    │ Images │ │Copy│ │  Tags  ││                                      │
│    │  图片  │ │文案│ │  标签  ││                                      │
│    └────────┘ └────┘ └────────┘│                                      │
│                   │            │                                      │
│                   ▼            │                                      │
│            ┌───────────┐       │                                      │
│            │Publication│───────┘ (内容快照)                           │
│            │  发布记录  │                                              │
│            └─────┬─────┘                                              │
│                  │                                                     │
│                  ▼                                                     │
│            ┌───────────┐                                              │
│            │Evaluation │                                              │
│            │  后评估   │                                              │
│            └───────────┘                                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 一、Idea（灵感）

最基础的单元。一个灵感可以是：
- 属于某个系列的选题（如"影视飓风"属于"B站UP主系列"）
- 独立的单条灵感（如"今天看到一个有趣的事"）

```json
// ideas/{id}.json
{
  "id": "idea_20260202_001",
  "type": "series" | "standalone",     // 系列灵感 or 独立灵感

  // 如果是系列灵感
  "series_id": "bilibili-up",
  "series_subject": "影视飓风",

  // 灵感核心
  "hook": "圆通之子，凭亿近人",         // 一句话钩子
  "angle": "老板荒岛求生 vs 员工头等舱", // 切入角度
  "notes": "反差点很强，适合做封面",     // 备注

  // 调研素材（可选）
  "research": {
    "dimensions": {
      "人设反差": "表面草根创业，实际圆通总裁之子",
      "经典语录": "悲观者总是正确的，乐观者正在前行",
      "老粉梗": "凭亿近人、每年送iPhone",
      "隐藏技能": "帮截肢粉丝实现奔跑梦"
    },
    "sources": ["知乎", "B站", "微博"],
    "researched_at": "2026-02-02"
  },

  // 状态
  "status": "idea" | "researched" | "in_production" | "ready" | "published" | "archived",

  // 元数据
  "created_at": "2026-02-02T10:00:00+08:00",
  "updated_at": "2026-02-02T14:00:00+08:00",
  "created_by": "research-agent"
}
```

## 二、Series（系列）

系列是灵感的可选归属，用于批量生产同类内容。

```json
// series/{id}.json
{
  "id": "bilibili-up",
  "name": "B站UP主介绍",
  "description": "挖掘UP主老粉才知道的梗，制作反差型内容",
  "status": "active" | "paused" | "archived",

  // 内容模板
  "content_template": {
    "style": "反差揭秘",
    "image_styles": ["线刻肖像", "手绘白板"],
    "typical_tags": ["B站宝藏UP主", "反差感"]
  },

  // 调研模板
  "research_template": {
    "dimensions": ["人设反差", "经典语录", "老粉梗", "隐藏技能"],
    "search_patterns": ["{name} 名场面", "{name} 梗 老粉"]
  },

  // 统计（自动计算）
  "stats": {
    "idea_count": 7,
    "published_count": 1,
    "avg_engagement": 0
  },

  "created_at": "2026-02-02"
}
```

## 三、Content（内容草稿）

内容是灵感的具象化，包含实际要发布的图和文。

```json
// contents/{id}.json
{
  "id": "content_20260202_001",
  "idea_id": "idea_20260202_001",      // 关联灵感

  // 文案
  "copy": {
    "title": "三句不离下三路的峰哥，书单吓你一跳",
    "body": "你以为峰哥只会开车？...",
    "char_count": 320,                  // 自动计算
    "is_valid": true                    // 是否符合平台限制
  },

  // 图片
  "images": [
    {
      "id": "img_001",
      "path": "~/.claude/Nanobanana-draw-图片/xxx.jpg",
      "style": "线刻肖像",
      "role": "cover",                  // cover | detail | comparison
      "generated_at": "2026-02-02",
      "prompt": "将这张照片转换为黑白线刻..."
    },
    {
      "id": "img_002",
      "path": "~/.claude/Nanobanana-draw-图片/xxx.png",
      "style": "手绘白板",
      "role": "detail"
    }
  ],

  // 标签
  "tags": ["峰哥亡命天涯", "B站宝藏UP主", "反差感"],

  // 状态
  "status": "draft" | "ready" | "published",

  // 发布检查清单
  "checklist": {
    "title_length": { "pass": true, "value": 16, "limit": 20 },
    "body_length": { "pass": true, "value": 320, "limit": 1000 },
    "image_count": { "pass": true, "value": 2, "min": 1, "max": 9 },
    "tags_count": { "pass": true, "value": 3, "min": 1, "max": 10 }
  },

  "created_at": "2026-02-02T14:00:00+08:00",
  "updated_at": "2026-02-02T15:00:00+08:00"
}
```

## 四、Publication（发布记录）

发布是一个不可变的事件记录。

```json
// publications/{YYYYMM}/{id}.json
{
  "id": "pub_20260202_001",
  "content_id": "content_20260202_001",
  "idea_id": "idea_20260202_001",
  "series_id": "bilibili-up",          // 冗余，方便查询

  // 发布信息
  "platform": "xiaohongshu",
  "post_id": "xhs_xxx",
  "post_url": "https://www.xiaohongshu.com/...",
  "published_at": "2026-02-02T15:30:00+08:00",

  // 内容快照（发布时的完整内容，不可变）
  "snapshot": {
    "title": "...",
    "body": "...",
    "tags": [...],
    "images": [...]
  },

  // 关联评估
  "evaluation_id": "eval_20260202_001"
}
```

## 五、Evaluation（后评估）

评估记录发布后的数据追踪和分析。

```json
// evaluations/{id}.json
{
  "id": "eval_20260202_001",
  "publication_id": "pub_20260202_001",

  // 数据追踪
  "metrics": {
    "D0": {
      "recorded_at": "2026-02-02T15:30:00+08:00",
      "likes": 0,
      "comments": 0,
      "collects": 0,
      "views": 0
    },
    "D1": {
      "recorded_at": "2026-02-03T15:30:00+08:00",
      "likes": 10,
      "comments": 2,
      "collects": 5,
      "views": 200
    },
    "D7": null,   // 待追踪
    "D30": null   // 待追踪
  },

  // 追踪状态
  "tracking_status": {
    "D1_due": "2026-02-03T15:30:00+08:00",
    "D1_done": true,
    "D7_due": "2026-02-09T15:30:00+08:00",
    "D7_done": false,
    "D30_due": "2026-03-04T15:30:00+08:00",
    "D30_done": false
  },

  // 评估结果（D7 后生成）
  "result": {
    "score": "B",                      // A/B/C/D/F
    "engagement_total": 17,            // likes + comments×3 + collects×2
    "vs_series_avg": 1.2,              // 相对系列平均的倍数
    "vs_account_avg": 1.0,             // 相对账号平均的倍数
    "tags": ["首发", "反差类"]          // 标签
  },

  // 复盘笔记（人工填写）
  "learnings": {
    "what_worked": "反差点击中目标受众，评论区讨论热烈",
    "what_failed": null,
    "next_action": "继续这个风格，下一个做影视飓风"
  }
}
```

## 六、目录结构

```
~/.claude/agents/xhs-account-ops/
├── config.json              # 全局配置
├── DATA_MODEL.md            # 本文档
├── ARCHITECTURE.md          # 系统架构
├── dashboard.html           # 可视化面板
│
├── series/                  # 系列定义
│   ├── bilibili-up.json
│   └── ai-tools.json
│
├── ideas/                   # 灵感库
│   ├── idea_20260202_001.json  (峰哥)
│   ├── idea_20260202_002.json  (影视飓风)
│   └── ...
│
├── contents/                # 内容草稿
│   ├── content_20260202_001.json
│   └── ...
│
├── publications/            # 发布记录（按月归档）
│   └── 202602/
│       └── pub_20260202_001.json
│
├── evaluations/             # 后评估
│   └── eval_20260202_001.json
│
└── analytics/               # 分析报告
    ├── weekly/
    ├── monthly/
    └── insights.json
```

## 七、状态流转

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          内容生命周期                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Idea                    Content              Publication   Evaluation  │
│  ────                    ───────              ───────────   ──────────  │
│                                                                         │
│  ┌────────┐                                                            │
│  │  idea  │ ── 记录灵感                                                │
│  └───┬────┘                                                            │
│      │ 调研                                                            │
│      ▼                                                                 │
│  ┌────────────┐                                                        │
│  │ researched │ ── 完成调研                                            │
│  └───┬────────┘                                                        │
│      │ 开始制作                                                        │
│      ▼                                                                 │
│  ┌───────────────┐    ┌────────┐                                      │
│  │ in_production │ ──►│ draft  │ ── 创建内容草稿                       │
│  └───────────────┘    └───┬────┘                                      │
│                           │ 完成制作                                   │
│                           ▼                                            │
│                       ┌────────┐                                       │
│                       │ ready  │ ── 待发布                             │
│                       └───┬────┘                                       │
│                           │ 发布                                       │
│                           ▼                                            │
│  ┌───────────┐       ┌────────────┐    ┌────────────┐                 │
│  │ published │ ◄──── │ published  │───►│ 创建评估   │                 │
│  └───────────┘       └────────────┘    └─────┬──────┘                 │
│       (Idea)            (Content)            │                         │
│                                              ▼                         │
│                                        ┌───────────┐                  │
│                                        │ tracking  │ ── D1/D7/D30     │
│                                        └─────┬─────┘                  │
│                                              │ 完成追踪                │
│                                              ▼                         │
│                                        ┌───────────┐                  │
│                                        │ evaluated │ ── 生成评分      │
│                                        └───────────┘                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 八、查询模式

### 按系列查看
```
series/bilibili-up.json
  → ideas/ where series_id = "bilibili-up"
    → contents/ where idea_id in ideas
      → publications/ where content_id in contents
        → evaluations/ where publication_id in publications
```

### 按状态查看
```
待调研：ideas/ where status = "idea"
待制作：ideas/ where status = "researched"
待发布：contents/ where status = "ready"
待追踪：evaluations/ where D7_done = false
```

### 按时间查看
```
本周发布：publications/202602/ where published_at in this_week
本月最佳：evaluations/ where result.score = "A"
```
