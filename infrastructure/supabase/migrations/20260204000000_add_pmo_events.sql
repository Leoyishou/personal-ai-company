-- PMO 事件记录表
-- 记录所有 Agent session 的活动留痕

CREATE TABLE pac.pmo_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id TEXT NOT NULL,
  event_type TEXT NOT NULL CHECK (event_type IN ('session_end', 'tool_use', 'subagent_start', 'subagent_stop', 'publish')),
  bu TEXT CHECK (bu IN ('product', 'content', 'investment', 'pmo', 'unknown')),
  cwd TEXT,
  summary TEXT,
  decision TEXT CHECK (decision IN ('reported', 'skipped', 'pending')),
  linear_issue_id TEXT,
  transcript_path TEXT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_pmo_events_session ON pac.pmo_events(session_id);
CREATE INDEX idx_pmo_events_type ON pac.pmo_events(event_type);
CREATE INDEX idx_pmo_events_bu ON pac.pmo_events(bu);
CREATE INDEX idx_pmo_events_decision ON pac.pmo_events(decision);
CREATE INDEX idx_pmo_events_created_at ON pac.pmo_events(created_at);

-- RLS
ALTER TABLE pac.pmo_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all for anon" ON pac.pmo_events FOR ALL USING (true);

COMMENT ON TABLE pac.pmo_events IS 'PMO 事件留痕：记录所有 Agent session 的活动';

-- 授权 anon/authenticated 访问 pac schema
GRANT USAGE ON SCHEMA pac TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA pac TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA pac TO anon, authenticated;
