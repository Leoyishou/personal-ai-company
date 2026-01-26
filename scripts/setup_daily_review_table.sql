-- 每日复盘表
-- 在 Supabase Dashboard SQL Editor 中执行一次

CREATE TABLE IF NOT EXISTS daily_personal_reviews (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  review_date DATE UNIQUE NOT NULL,

  -- 统计数据
  total_pages INT,
  total_domains INT,
  total_duration_minutes INT,
  agent_sessions INT,
  agent_messages INT,

  -- OKR 分析
  okr_alignment JSONB,  -- {"O1": 15, "O2": 0, "O7": 35, "unaligned": 20}
  time_distribution JSONB,  -- 各类活动时间分布

  -- AI 生成内容
  one_line_summary TEXT,
  insights JSONB,  -- [{title: "", content: ""}, ...]
  tomorrow_suggestions JSONB,  -- ["suggestion1", "suggestion2"]

  -- 原始报告
  raw_report TEXT,

  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_daily_personal_reviews_date ON daily_personal_reviews(review_date DESC);

-- RLS (Row Level Security) - 可选
-- ALTER TABLE daily_personal_reviews ENABLE ROW LEVEL SECURITY;
