-- Migration: Add API key usage tracking
-- Run this in Supabase SQL Editor

-- API key usage tracking table
CREATE TABLE IF NOT EXISTS api_key_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Request details
    provider TEXT NOT NULL,         -- anthropic, openai, google
    model TEXT NOT NULL,            -- claude-sonnet-4-20250514, gpt-4, etc.
    request_type TEXT DEFAULT 'chat', -- chat, tool_call, etc.

    -- Token usage
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,

    -- Cost estimate (USD)
    estimated_cost DECIMAL(10, 6) DEFAULT 0,

    -- Metadata
    success BOOLEAN DEFAULT true,
    error_message TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Daily aggregated usage (for faster queries)
CREATE TABLE IF NOT EXISTS api_key_usage_daily (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Aggregation date
    usage_date DATE NOT NULL,

    -- Provider info
    provider TEXT NOT NULL,
    model TEXT NOT NULL,

    -- Aggregated counts
    request_count INTEGER DEFAULT 0,
    total_input_tokens INTEGER DEFAULT 0,
    total_output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_estimated_cost DECIMAL(10, 6) DEFAULT 0,
    error_count INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, usage_date, provider, model)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_api_key_usage_user_id ON api_key_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_api_key_usage_created_at ON api_key_usage(created_at);
CREATE INDEX IF NOT EXISTS idx_api_key_usage_user_date ON api_key_usage(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_api_key_usage_daily_user ON api_key_usage_daily(user_id);
CREATE INDEX IF NOT EXISTS idx_api_key_usage_daily_date ON api_key_usage_daily(user_id, usage_date);

-- RLS Policies
ALTER TABLE api_key_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_key_usage_daily ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own usage"
    ON api_key_usage FOR SELECT
    USING (user_id::text = auth.uid()::text);

CREATE POLICY "Service can insert usage"
    ON api_key_usage FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Users can view own daily usage"
    ON api_key_usage_daily FOR SELECT
    USING (user_id::text = auth.uid()::text);

CREATE POLICY "Service can upsert daily usage"
    ON api_key_usage_daily FOR ALL
    USING (true);

-- Triggers for updated_at
CREATE TRIGGER update_api_key_usage_daily_updated_at
    BEFORE UPDATE ON api_key_usage_daily
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE api_key_usage IS 'Per-request API key usage tracking with token counts and costs';
COMMENT ON TABLE api_key_usage_daily IS 'Daily aggregated API usage for dashboard queries';
