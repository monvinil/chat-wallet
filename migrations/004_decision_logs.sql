-- Migration: Add decision_logs table for AI training data
-- Run this in Supabase SQL Editor

-- Decision Logs table (captures AI decisions for future fine-tuning)
CREATE TABLE IF NOT EXISTS decision_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    session_id VARCHAR(100),

    -- The interaction
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    tool_calls JSONB,  -- [{tool: "send_usdc", input: {...}, output_preview: "..."}]

    -- Context (anonymized)
    user_context JSONB,  -- {balance_bucket: "100-500", has_yield: true, ...}

    -- Outcome tracking
    outcome VARCHAR(20) DEFAULT 'success',  -- 'success', 'failure', 'cancelled', 'corrected'
    user_feedback VARCHAR(20),  -- 'positive', 'negative', 'corrected'
    correction_message TEXT,  -- If user corrected the AI

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- For efficient training data export
    exported_at TIMESTAMPTZ,
    export_batch VARCHAR(50)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_decision_logs_user ON decision_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_decision_logs_created ON decision_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_decision_logs_outcome ON decision_logs(outcome);
CREATE INDEX IF NOT EXISTS idx_decision_logs_unexported ON decision_logs(exported_at) WHERE exported_at IS NULL;

-- Row Level Security
ALTER TABLE decision_logs ENABLE ROW LEVEL SECURITY;

-- Users can view their own logs
CREATE POLICY "Users can view own decision logs" ON decision_logs
    FOR SELECT USING (auth.uid() = user_id);

-- Users can insert logs (anonymous allowed - user_id can be null)
CREATE POLICY "Anyone can insert decision logs" ON decision_logs
    FOR INSERT WITH CHECK (true);

-- Service role has full access (for training export)
CREATE POLICY "Service role full access decision logs" ON decision_logs
    FOR ALL USING (auth.role() = 'service_role');

-- Add auto_lock_minutes to user_settings if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_settings'
        AND column_name = 'auto_lock_minutes'
    ) THEN
        ALTER TABLE user_settings ADD COLUMN auto_lock_minutes INTEGER DEFAULT 15;
    END IF;
END $$;
