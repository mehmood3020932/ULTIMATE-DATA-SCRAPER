-- Jobs and related tables
CREATE TABLE scraping_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    target_url TEXT NOT NULL,
    instructions TEXT,
    schema_definition JSONB,
    config JSONB DEFAULT '{}',
    credentials_id UUID,
    pages_scraped INTEGER DEFAULT 0,
    pages_total INTEGER,
    items_extracted INTEGER DEFAULT 0,
    credits_consumed DECIMAL(10, 4) DEFAULT 0,
    result_data JSONB,
    result_file_url VARCHAR(500),
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    estimated_duration_seconds INTEGER,
    agents_used JSONB DEFAULT '[]',
    llm_calls_made INTEGER DEFAULT 0,
    confidence_score DECIMAL(3, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_jobs_user_id ON scraping_jobs(user_id);
CREATE INDEX idx_jobs_status ON scraping_jobs(status);
CREATE INDEX idx_jobs_created_at ON scraping_jobs(created_at);

-- Job events
CREATE TABLE job_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES scraping_jobs(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'info',
    message TEXT,
    metadata JSONB,
    agent_name VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_events_job_id ON job_events(job_id);
CREATE INDEX idx_events_created_at ON job_events(created_at);