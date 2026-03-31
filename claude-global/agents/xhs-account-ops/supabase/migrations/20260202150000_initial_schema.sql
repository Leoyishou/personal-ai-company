-- XHS Content Management System Schema
-- 小红书内容管理系统数据模型

-- 1. 系列表 (Series) - 内容聚合容器
CREATE TABLE IF NOT EXISTS xhs_series (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    content_template JSONB DEFAULT '{}',
    research_template JSONB DEFAULT '{}',
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed')),
    idea_count INTEGER DEFAULT 0,
    published_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 灵感表 (Ideas) - 内容创作起点
CREATE TABLE IF NOT EXISTS xhs_ideas (
    id TEXT PRIMARY KEY,
    series_id TEXT REFERENCES xhs_series(id) ON DELETE SET NULL,
    subject TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'researched', 'in_production', 'ready', 'published', 'abandoned')),
    priority INTEGER DEFAULT 0,
    source TEXT,
    source_url TEXT,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 调研表 (Research) - 灵感深度调研
CREATE TABLE IF NOT EXISTS xhs_research (
    id TEXT PRIMARY KEY,
    idea_id TEXT NOT NULL REFERENCES xhs_ideas(id) ON DELETE CASCADE,
    research_type TEXT DEFAULT 'general',
    content JSONB NOT NULL DEFAULT '{}',
    sources TEXT[] DEFAULT '{}',
    key_findings TEXT[] DEFAULT '{}',
    researcher TEXT,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'completed', 'outdated')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. 文案表 (Copies) - 文字内容
CREATE TABLE IF NOT EXISTS xhs_copies (
    id TEXT PRIMARY KEY,
    idea_id TEXT NOT NULL REFERENCES xhs_ideas(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    char_count INTEGER GENERATED ALWAYS AS (length(body)) STORED,
    version INTEGER DEFAULT 1,
    is_valid BOOLEAN DEFAULT true,
    validation_errors JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. 图片表 (Images) - 图片素材
CREATE TABLE IF NOT EXISTS xhs_images (
    id TEXT PRIMARY KEY,
    idea_id TEXT NOT NULL REFERENCES xhs_ideas(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    url TEXT,
    style TEXT,
    role TEXT DEFAULT 'detail' CHECK (role IN ('cover', 'detail', 'background')),
    dimensions JSONB DEFAULT '{}',
    generation_prompt TEXT,
    source_type TEXT DEFAULT 'generated' CHECK (source_type IN ('generated', 'uploaded', 'screenshot', 'processed')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. 发布表 (Publications) - 发布记录（不可变快照）
CREATE TABLE IF NOT EXISTS xhs_publications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idea_id TEXT NOT NULL REFERENCES xhs_ideas(id) ON DELETE RESTRICT,
    copy_id TEXT REFERENCES xhs_copies(id) ON DELETE SET NULL,
    platform TEXT NOT NULL DEFAULT 'xiaohongshu',
    post_id TEXT,
    post_url TEXT,
    published_at TIMESTAMPTZ NOT NULL,
    snapshot JSONB NOT NULL DEFAULT '{}',
    publisher TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. 评估表 (Evaluations) - 发布后追踪
CREATE TABLE IF NOT EXISTS xhs_evaluations (
    id TEXT PRIMARY KEY,
    publication_id UUID NOT NULL REFERENCES xhs_publications(id) ON DELETE CASCADE,
    metrics JSONB NOT NULL DEFAULT '{
        "D0": null,
        "D1": null,
        "D7": null,
        "D30": null
    }',
    tracking_status JSONB NOT NULL DEFAULT '{
        "D1_done": false,
        "D7_done": false,
        "D30_done": false
    }',
    engagement_score NUMERIC,
    grade TEXT CHECK (grade IN ('A', 'B', 'C', 'D', 'F')),
    result JSONB,
    learnings TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_ideas_series ON xhs_ideas(series_id);
CREATE INDEX IF NOT EXISTS idx_ideas_status ON xhs_ideas(status);
CREATE INDEX IF NOT EXISTS idx_research_idea ON xhs_research(idea_id);
CREATE INDEX IF NOT EXISTS idx_copies_idea ON xhs_copies(idea_id);
CREATE INDEX IF NOT EXISTS idx_images_idea ON xhs_images(idea_id);
CREATE INDEX IF NOT EXISTS idx_publications_idea ON xhs_publications(idea_id);
CREATE INDEX IF NOT EXISTS idx_publications_platform ON xhs_publications(platform);
CREATE INDEX IF NOT EXISTS idx_evaluations_publication ON xhs_evaluations(publication_id);

-- 触发器：自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE OR REPLACE TRIGGER update_xhs_series_updated_at
    BEFORE UPDATE ON xhs_series
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE TRIGGER update_xhs_ideas_updated_at
    BEFORE UPDATE ON xhs_ideas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE TRIGGER update_xhs_research_updated_at
    BEFORE UPDATE ON xhs_research
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE TRIGGER update_xhs_copies_updated_at
    BEFORE UPDATE ON xhs_copies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE TRIGGER update_xhs_evaluations_updated_at
    BEFORE UPDATE ON xhs_evaluations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 注释
COMMENT ON TABLE xhs_series IS '系列 - 内容聚合容器，如「B站UP主介绍」系列';
COMMENT ON TABLE xhs_ideas IS '灵感 - 内容创作的起点';
COMMENT ON TABLE xhs_research IS '调研 - 对灵感的深度调研结果';
COMMENT ON TABLE xhs_copies IS '文案 - 标题+正文';
COMMENT ON TABLE xhs_images IS '图片 - AI生成或上传的图片素材';
COMMENT ON TABLE xhs_publications IS '发布 - 不可变的发布快照';
COMMENT ON TABLE xhs_evaluations IS '评估 - D0/D1/D7/D30 追踪';
