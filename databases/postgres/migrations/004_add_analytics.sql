-- Analytics tables
CREATE TABLE llm_usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES scraping_jobs(id),
    provider VARCHAR(50),
    model VARCHAR(100),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    cost_usd DECIMAL(10, 6),
    latency_ms INTEGER,
    success BOOLEAN,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_llm_logs_job_id ON llm_usage_logs(job_id);
CREATE INDEX idx_llm_logs_created_at ON llm_usage_logs(created_at);

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON scraping_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();