# Daily Review Skill

运营部核心技能：每日个人复盘，对齐 OKR 目标。

---

## 触发条件

- 定时触发：每晚 23:00 由 scheduler.py 自动执行
- 手动触发：CEO 指令 "今日复盘" / "daily review"

---

## 数据来源

### 1. Supabase 数据

```sql
-- 今日浏览记录
SELECT url, title, domain, duration_seconds, visit_time
FROM browsing_records
WHERE DATE(visit_time) = CURRENT_DATE;

-- 今日 Agent 会话
SELECT session_id, message_count, topics, summary
FROM agent_sessions
WHERE DATE(created_at) = CURRENT_DATE;
```

### 2. 本地 OKR (odyssey)

路径：`~/odyssey/4 复盘/2025/2025-2026 战略屋.md`

7 大目标：
- O1 健康
- O2 情绪和关系
- O3 心智成长
- O4 托福
- O5 第二大脑
- O6 智能化
- O7 投资研究

---

## 分析维度

### OKR 对齐度

将今日活动分类到 7 个 OKR：

```json
{
  "O6_智能化": {
    "percentage": 45,
    "activities": ["Supabase 开发", "Agent 调试"]
  },
  "O7_托福": {
    "percentage": 20,
    "activities": ["TPO 阅读"]
  },
  "无归属": {
    "percentage": 35,
    "activities": ["刷 Twitter", "随机浏览"]
  }
}
```

### 时间分配

```json
{
  "深度工作": "3h 20min",
  "碎片浏览": "2h 15min",
  "娱乐": "45min"
}
```

### 趋势对比

- 与昨天对比
- 与上周同期对比
- 连续趋势警告（如：连续 3 天无托福学习）

---

## 输出格式

### Telegram 通知（简报）

```
📊 今日复盘完成

2026-01-26

> 今天主要在优化 AI 公司基础设施，托福学习时间偏少

🎯 OKR 进展:
- O6 智能化: 65% ████████░░
- O7 托福: 15% ██░░░░░░░░
- ⚠️ 无归属: 20%

💡 关键洞察:
1. 技术债优先：连续 3 天在做基础设施
2. 深度时间不足：今天深度阅读 < 30min

📝 明日建议:
- 上午固定 1h 托福听力

详细报告已写入 Notion
```

### Supabase 存储

表：`daily_personal_reviews`

```json
{
  "review_date": "2026-01-26",
  "total_pages": 45,
  "total_domains": 12,
  "total_duration_minutes": 320,
  "okr_alignment": {...},
  "insights": [...],
  "tomorrow_suggestions": [...]
}
```

### Notion 报告

写入 Personal Review 数据库，包含完整分析。

---

## 配置

环境变量：

```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJxxx
NOTION_API_KEY=ntn_xxx
```

Notion 数据库 ID：`2f47f9bf-d164-81a2-886f-de01e398ac38`

---

## 使用示例

```
用户：今日复盘
CEO 助理：正在生成今日复盘报告...

[执行分析]

📊 今日复盘完成
...
```
