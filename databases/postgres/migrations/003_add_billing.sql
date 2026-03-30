-- Billing tables
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    public_key VARCHAR(64) UNIQUE NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    permissions JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_public_key ON api_keys(public_key);

CREATE TABLE billing_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    record_type VARCHAR(50),
    amount DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    credits_amount DECIMAL(10, 2),
    credits_balance_after DECIMAL(15, 2),
    job_id UUID,
    stripe_payment_intent_id VARCHAR(100),
    stripe_invoice_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_billing_user_id ON billing_records(user_id);
CREATE INDEX idx_billing_created_at ON billing_records(created_at);

CREATE TABLE stored_credentials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100),
    credential_type VARCHAR(50),
    encrypted_data TEXT NOT NULL,
    iv VARCHAR(32),
    domain VARCHAR(255),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_credentials_user_id ON stored_credentials(user_id);