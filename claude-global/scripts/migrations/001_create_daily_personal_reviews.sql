-- Migration: Create daily_personal_reviews table
-- Run this in Supabase SQL Editor: https://supabase.com/dashboard/project/ebgmmkaxuhawfrwryzia/sql

-- Daily Personal Reviews table for storing AI-generated insights
CREATE TABLE IF NOT EXISTS daily_personal_reviews (
  id SERIAL PRIMARY KEY,
  review_date DATE NOT NULL UNIQUE,

  -- OKR alignment scores (0.0 - 1.0)
  okr_alignment JSONB NOT NULL DEFAULT '{}',
  dominant_okr VARCHAR(10),

  -- Time distribution
  time_distribution JSONB DEFAULT '{}',

  -- Summary
  one_line_summary TEXT,

  -- Insights array
  insights JSONB DEFAULT '[]',

  -- Tomorrow actions
  tomorrow_actions JSONB DEFAULT '[]',

  -- Knowledge delta
  knowledge_delta JSONB DEFAULT '{}',

  -- Source data references
  browsing_count INTEGER DEFAULT 0,
  agent_session_count INTEGER DEFAULT 0,
  odyssey_files_changed INTEGER DEFAULT 0,

  -- Full AI response for reference
  ai_raw_response JSONB,

  -- Notion page URL
  notion_url TEXT,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for date queries
CREATE INDEX IF NOT EXISTS idx_daily_personal_reviews_date ON daily_personal_reviews(review_date DESC);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_daily_personal_reviews_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS daily_personal_reviews_updated_at ON daily_personal_reviews;
CREATE TRIGGER daily_personal_reviews_updated_at
  BEFORE UPDATE ON daily_personal_reviews
  FOR EACH ROW
  EXECUTE FUNCTION update_daily_personal_reviews_timestamp();

-- Add comment
COMMENT ON TABLE daily_personal_reviews IS 'AI-generated daily personal insights based on browsing, agent, and odyssey data';

-- Enable RLS (optional, for public access via anon key)
ALTER TABLE daily_personal_reviews ENABLE ROW LEVEL SECURITY;

-- Allow public read/write for now (can be restricted later)
CREATE POLICY "Allow all" ON daily_personal_reviews FOR ALL USING (true) WITH CHECK (true);
