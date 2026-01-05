-- Migration: Add user settings and OAuth connections
-- Run this in Supabase SQL Editor

-- User settings table
CREATE TABLE IF NOT EXISTS user_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- LLM Configuration
    llm_provider TEXT DEFAULT 'anthropic',  -- anthropic, openai, etc.
    llm_model TEXT DEFAULT 'claude-sonnet-4-20250514',
    llm_api_key_encrypted TEXT,  -- Encrypted API key

    -- Spending limits
    daily_spend_limit DECIMAL(10, 2) DEFAULT 100.00,
    require_approval_above DECIMAL(10, 2) DEFAULT 50.00,

    -- Permissions
    allow_recurring_payments BOOLEAN DEFAULT false,
    allow_account_access BOOLEAN DEFAULT false,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id)
);

-- OAuth connections table
CREATE TABLE IF NOT EXISTS user_oauth_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    provider TEXT NOT NULL,  -- gmail, google, amazon, etc.
    provider_user_id TEXT,  -- User ID from the provider

    -- Encrypted tokens
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,

    -- Token metadata
    scopes TEXT[],  -- Array of granted scopes
    expires_at TIMESTAMPTZ,

    -- Status
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, provider)
);

-- Approval history table (for recurring/multi-step tasks)
CREATE TABLE IF NOT EXISTS approval_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Task details
    task_type TEXT NOT NULL,  -- 'single', 'recurring', 'multi_step'
    task_description TEXT,

    -- Approval details
    approved BOOLEAN DEFAULT false,
    approved_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,  -- For recurring approvals

    -- Spending
    estimated_cost DECIMAL(10, 2),
    actual_cost DECIMAL(10, 2),

    -- Execution
    status TEXT DEFAULT 'pending',  -- pending, approved, executing, completed, failed
    result JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);
CREATE INDEX IF NOT EXISTS idx_oauth_connections_user_id ON user_oauth_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_oauth_connections_provider ON user_oauth_connections(provider);
CREATE INDEX IF NOT EXISTS idx_approval_history_user_id ON approval_history(user_id);
CREATE INDEX IF NOT EXISTS idx_approval_history_status ON approval_history(status);

-- RLS Policies
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_oauth_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE approval_history ENABLE ROW LEVEL SECURITY;

-- User settings policies
CREATE POLICY "Users can view own settings"
    ON user_settings FOR SELECT
    USING (user_id::text = auth.uid()::text);

CREATE POLICY "Users can update own settings"
    ON user_settings FOR UPDATE
    USING (user_id::text = auth.uid()::text);

CREATE POLICY "Users can insert own settings"
    ON user_settings FOR INSERT
    WITH CHECK (user_id::text = auth.uid()::text);

-- OAuth connections policies
CREATE POLICY "Users can view own connections"
    ON user_oauth_connections FOR SELECT
    USING (user_id::text = auth.uid()::text);

CREATE POLICY "Users can manage own connections"
    ON user_oauth_connections FOR ALL
    USING (user_id::text = auth.uid()::text);

-- Approval history policies
CREATE POLICY "Users can view own approvals"
    ON approval_history FOR SELECT
    USING (user_id::text = auth.uid()::text);

CREATE POLICY "Users can insert own approvals"
    ON approval_history FOR INSERT
    WITH CHECK (user_id::text = auth.uid()::text);

-- Functions for encryption helpers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers
CREATE TRIGGER update_user_settings_updated_at
    BEFORE UPDATE ON user_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_oauth_connections_updated_at
    BEFORE UPDATE ON user_oauth_connections
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_approval_history_updated_at
    BEFORE UPDATE ON approval_history
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE user_settings IS 'User preferences including LLM configuration and spending limits';
COMMENT ON TABLE user_oauth_connections IS 'OAuth tokens for connected accounts (Gmail, Google, etc.)';
COMMENT ON TABLE approval_history IS 'History of user approvals for tasks and spending';

COMMENT ON COLUMN user_settings.llm_api_key_encrypted IS 'Encrypted user API key for LLM provider';
COMMENT ON COLUMN user_oauth_connections.access_token_encrypted IS 'Encrypted OAuth access token';
COMMENT ON COLUMN user_oauth_connections.refresh_token_encrypted IS 'Encrypted OAuth refresh token';
