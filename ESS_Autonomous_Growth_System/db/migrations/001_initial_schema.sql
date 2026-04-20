-- ESS Autonomous Growth System - Database Schema
-- PostgreSQL 16

-- Content Groups (clusters of related content)
CREATE TABLE IF NOT EXISTS content_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    cluster VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Content Versions (tracks every version of a page)
CREATE TABLE IF NOT EXISTS content_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_group_id UUID REFERENCES content_groups(id),
    title VARCHAR(500) NOT NULL,
    slug VARCHAR(500) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    content TEXT,
    meta_description TEXT,
    meta_title VARCHAR(200),
    schema_markup JSONB,
    status VARCHAR(50) DEFAULT 'draft',
    wordpress_post_id INTEGER,
    wordpress_url TEXT,
    language VARCHAR(10) DEFAULT 'en',
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Translations (paired EN/ES pages)
CREATE TABLE IF NOT EXISTS translations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_content_id UUID REFERENCES content_versions(id),
    translated_content_id UUID REFERENCES content_versions(id),
    source_language VARCHAR(10) DEFAULT 'en',
    target_language VARCHAR(10) DEFAULT 'es',
    status VARCHAR(50) DEFAULT 'pending',
    synced BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Keywords
CREATE TABLE IF NOT EXISTS keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keyword VARCHAR(500) NOT NULL,
    search_volume INTEGER,
    difficulty INTEGER,
    cpc DECIMAL(10,2),
    trend VARCHAR(50),
    language VARCHAR(10) DEFAULT 'en',
    last_checked TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Keyword Clusters
CREATE TABLE IF NOT EXISTS keyword_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    keywords JSONB,
    authority_score INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Opportunities
CREATE TABLE IF NOT EXISTS opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keyword VARCHAR(500) NOT NULL,
    score INTEGER NOT NULL,
    score_breakdown JSONB,
    content_type VARCHAR(50),
    priority VARCHAR(20),
    status VARCHAR(50) DEFAULT 'discovered',
    cluster VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Briefs (content briefs generated from opportunities)
CREATE TABLE IF NOT EXISTS briefs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID REFERENCES opportunities(id),
    title VARCHAR(500),
    outline JSONB,
    target_keywords JSONB,
    internal_link_targets JSONB,
    word_count_target INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tasks (queue items for automation)
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_type VARCHAR(100) NOT NULL,
    payload JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    queue_state VARCHAR(50) DEFAULT 'brief',
    priority INTEGER DEFAULT 5,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Automation Runs
CREATE TABLE IF NOT EXISTS automation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    automation_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'running',
    tasks_completed INTEGER DEFAULT 0,
    tasks_total INTEGER DEFAULT 0,
    results JSONB,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_log TEXT
);

-- Internal Links
CREATE TABLE IF NOT EXISTS internal_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_content_id UUID REFERENCES content_versions(id),
    target_content_id UUID REFERENCES content_versions(id),
    anchor_text VARCHAR(500),
    link_type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'suggested',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Snapshots (before/after page state)
CREATE TABLE IF NOT EXISTS snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID REFERENCES content_versions(id),
    snapshot_data JSONB NOT NULL,
    snapshot_type VARCHAR(50) DEFAULT 'before',
    reason TEXT,
    automation_id UUID REFERENCES automation_runs(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Diffs
CREATE TABLE IF NOT EXISTS diffs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    before_snapshot_id UUID REFERENCES snapshots(id),
    after_snapshot_id UUID REFERENCES snapshots(id),
    diff_data JSONB NOT NULL,
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Reports
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_type VARCHAR(50) NOT NULL,
    period_start DATE,
    period_end DATE,
    data JSONB,
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Leads
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_content_id UUID REFERENCES content_versions(id),
    source_url TEXT,
    lead_type VARCHAR(50),
    contact_info JSONB,
    status VARCHAR(50) DEFAULT 'new',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Revenue
CREATE TABLE IF NOT EXISTS revenue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id),
    opportunity_value DECIMAL(12,2),
    closed_value DECIMAL(12,2),
    status VARCHAR(50) DEFAULT 'pipeline',
    closed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ranking Data
CREATE TABLE IF NOT EXISTS ranking_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keyword_id UUID REFERENCES keywords(id),
    content_id UUID REFERENCES content_versions(id),
    position INTEGER,
    url TEXT,
    search_volume INTEGER,
    tracked_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_content_versions_slug ON content_versions(slug);
CREATE INDEX idx_content_versions_status ON content_versions(status);
CREATE INDEX idx_content_versions_language ON content_versions(language);
CREATE INDEX idx_keywords_keyword ON keywords(keyword);
CREATE INDEX idx_opportunities_score ON opportunities(score DESC);
CREATE INDEX idx_opportunities_status ON opportunities(status);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_queue_state ON tasks(queue_state);
CREATE INDEX idx_ranking_data_tracked ON ranking_data(tracked_at DESC);
CREATE INDEX idx_leads_source ON leads(source_content_id);
