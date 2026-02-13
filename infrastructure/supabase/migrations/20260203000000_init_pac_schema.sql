-- PAC (Personal AI Company) Schema
-- 公司统一数据存储

-- 创建 pac schema
CREATE SCHEMA IF NOT EXISTS pac;

-- 产物索引表
CREATE TABLE pac.bu_artifacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bu TEXT NOT NULL CHECK (bu IN ('product', 'content', 'investment')),
  type TEXT NOT NULL,
  linear_issue_id TEXT,
  session_id TEXT,
  storage_url TEXT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 产物类型索引
CREATE INDEX idx_bu_artifacts_bu ON pac.bu_artifacts(bu);
CREATE INDEX idx_bu_artifacts_type ON pac.bu_artifacts(type);
CREATE INDEX idx_bu_artifacts_linear_issue ON pac.bu_artifacts(linear_issue_id);
CREATE INDEX idx_bu_artifacts_session ON pac.bu_artifacts(session_id);

-- 内容发布记录表
CREATE TABLE pac.content_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  platform TEXT NOT NULL CHECK (platform IN ('xhs', 'bilibili', 'x', 'douyin', 'youtube')),
  post_url TEXT,
  title TEXT,
  content TEXT,
  images TEXT[],
  linear_issue_id TEXT,
  session_id TEXT,
  published_at TIMESTAMPTZ,
  -- 数据追踪
  views INT DEFAULT 0,
  likes INT DEFAULT 0,
  comments INT DEFAULT 0,
  shares INT DEFAULT 0,
  tracked_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 发布记录索引
CREATE INDEX idx_content_posts_platform ON pac.content_posts(platform);
CREATE INDEX idx_content_posts_linear_issue ON pac.content_posts(linear_issue_id);
CREATE INDEX idx_content_posts_published_at ON pac.content_posts(published_at);

-- 投资交易记录表
CREATE TABLE pac.investment_trades (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol TEXT NOT NULL,
  market TEXT NOT NULL CHECK (market IN ('us', 'hk', 'crypto', 'other')),
  direction TEXT NOT NULL CHECK (direction IN ('buy', 'sell')),
  quantity DECIMAL,
  price DECIMAL,
  amount DECIMAL,
  linear_issue_id TEXT,
  session_id TEXT,
  traded_at TIMESTAMPTZ,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 交易记录索引
CREATE INDEX idx_investment_trades_symbol ON pac.investment_trades(symbol);
CREATE INDEX idx_investment_trades_market ON pac.investment_trades(market);
CREATE INDEX idx_investment_trades_traded_at ON pac.investment_trades(traded_at);

-- 启用 RLS
ALTER TABLE pac.bu_artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE pac.content_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE pac.investment_trades ENABLE ROW LEVEL SECURITY;

-- 允许匿名访问（本地开发）
CREATE POLICY "Allow all for anon" ON pac.bu_artifacts FOR ALL USING (true);
CREATE POLICY "Allow all for anon" ON pac.content_posts FOR ALL USING (true);
CREATE POLICY "Allow all for anon" ON pac.investment_trades FOR ALL USING (true);

-- Storage Buckets 创建（通过 SQL 函数）
-- 注意：Storage buckets 需要通过 API 或 Studio 创建
COMMENT ON SCHEMA pac IS 'Personal AI Company 统一数据存储';
