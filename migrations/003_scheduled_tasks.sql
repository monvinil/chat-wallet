-- Migration: Add scheduled tasks and task runs tables
-- Run this in Supabase SQL Editor

-- Scheduled Tasks table
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    task_type VARCHAR(50) NOT NULL,  -- 'transfer', 'gift_card', 'swap', 'bridge'
    task_params JSONB NOT NULL,
    description TEXT,
    schedule_type VARCHAR(20) NOT NULL,  -- 'once', 'recurring', 'conditional'
    cron_expression VARCHAR(100),
    next_run_at TIMESTAMPTZ,
    condition_type VARCHAR(50),  -- 'balance_below', 'balance_above', 'price_below', 'price_above'
    condition_value DECIMAL,
    condition_asset VARCHAR(20),
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'paused', 'completed', 'failed'
    run_count INTEGER DEFAULT 0,
    max_runs INTEGER,
    consecutive_failures INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_run_at TIMESTAMPTZ
);

-- Task Runs table (execution history)
CREATE TABLE IF NOT EXISTS task_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES scheduled_tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL,  -- 'success', 'failed', 'skipped'
    result JSONB,
    error_message TEXT,
    tx_hash VARCHAR(100),
    execution_time_ms INTEGER,
    triggered_by VARCHAR(50) DEFAULT 'scheduler'  -- 'scheduler', 'manual', 'condition'
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_user_status ON scheduled_tasks(user_id, status);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_next_run ON scheduled_tasks(next_run_at) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_conditional ON scheduled_tasks(schedule_type) WHERE schedule_type = 'conditional';
CREATE INDEX IF NOT EXISTS idx_task_runs_task ON task_runs(task_id);
CREATE INDEX IF NOT EXISTS idx_task_runs_user ON task_runs(user_id);

-- Row Level Security
ALTER TABLE scheduled_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_runs ENABLE ROW LEVEL SECURITY;

-- Policies: Users can only see/modify their own tasks
CREATE POLICY "Users can view own tasks" ON scheduled_tasks
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own tasks" ON scheduled_tasks
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own tasks" ON scheduled_tasks
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own tasks" ON scheduled_tasks
    FOR DELETE USING (auth.uid() = user_id);

-- Service role can access all (for background executor)
CREATE POLICY "Service role full access tasks" ON scheduled_tasks
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access runs" ON task_runs
    FOR ALL USING (auth.role() = 'service_role');

-- Users can view their task runs
CREATE POLICY "Users can view own task runs" ON task_runs
    FOR SELECT USING (auth.uid() = user_id);
