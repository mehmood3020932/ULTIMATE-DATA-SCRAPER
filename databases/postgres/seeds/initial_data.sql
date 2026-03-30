-- Initial seed data

-- Insert default subscription plans
INSERT INTO subscription_plans (id, name, price_monthly, credits_included, features) VALUES
('free', 'Free', 0, 100, '["Basic scraping", "Standard support"]'),
('starter', 'Starter', 49, 1000, '["Advanced AI", "Priority queue", "Email support"]'),
('professional', 'Professional', 199, 5000, '["All AI models", "API access", "Priority support"]'),
('enterprise', 'Enterprise', NULL, NULL, '["Unlimited", "Dedicated infrastructure", "SLA"]');

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_jobs_user_status ON scraping_jobs(user_id, status);
CREATE INDEX IF NOT EXISTS idx_billing_user_type ON billing_records(user_id, record_type);