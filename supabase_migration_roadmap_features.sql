-- ============================================
-- Chat Wallet - Roadmap Features Migration
-- Features: Scheduled Tasks, Bridging, Insights
-- ============================================

-- ============================================
-- 1. SCHEDULED TASKS
-- ============================================

-- Main scheduled tasks table
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,

    -- Task definition
    task_type VARCHAR(50) NOT NULL,  -- 'transfer', 'swap', 'gift_card', 'bridge'
    task_params JSONB NOT NULL,       -- Action-specific parameters
    description TEXT,                  -- Human-readable description

    -- Schedule configuration
    schedule_type VARCHAR(20) NOT NULL,  -- 'once', 'recurring', 'conditional'
    cron_expression VARCHAR(100),         -- For recurring: "0 9 * * 1" (Mon 9am)
    timezone VARCHAR(50) DEFAULT 'UTC',
    next_run_at TIMESTAMPTZ,

    -- Conditional triggers (optional)
    condition_type VARCHAR(50),           -- 'balance_below', 'balance_above', 'price_below'
    condition_value DECIMAL,
    condition_asset VARCHAR(20),
    condition_check_interval INTEGER DEFAULT 3600,  -- Seconds between checks

    -- Execution tracking
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'paused', 'completed', 'failed', 'cancelled'
    last_run_at TIMESTAMPTZ,
    last_result JSONB,
    run_count INTEGER DEFAULT 0,
    max_runs INTEGER,                      -- NULL = unlimited
    consecutive_failures INTEGER DEFAULT 0,

    -- Notifications
    notify_on_success BOOLEAN DEFAULT true,
    notify_on_failure BOOLEAN DEFAULT true,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Execution history for scheduled tasks
CREATE TABLE IF NOT EXISTS scheduled_task_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES scheduled_tasks(id) ON DELETE CASCADE NOT NULL,

    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL,  -- 'success', 'failed', 'skipped'
    result JSONB,
    error_message TEXT,
    tx_hash VARCHAR(100),

    -- Execution context
    triggered_by VARCHAR(50) DEFAULT 'scheduler',  -- 'scheduler', 'manual', 'condition'
    execution_time_ms INTEGER
);

-- Indexes for scheduled tasks
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_next_run
    ON scheduled_tasks(next_run_at)
    WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_user
    ON scheduled_tasks(user_id);

CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_conditional
    ON scheduled_tasks(condition_type, status)
    WHERE condition_type IS NOT NULL AND status = 'active';

CREATE INDEX IF NOT EXISTS idx_task_runs_task
    ON scheduled_task_runs(task_id, started_at DESC);


-- ============================================
-- 2. CROSS-CHAIN BRIDGING
-- ============================================

-- Bridge transactions
CREATE TABLE IF NOT EXISTS bridge_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,

    -- Bridge details
    bridge_provider VARCHAR(50) NOT NULL,  -- 'cctp', 'stargate', 'debridge', 'across'
    from_chain VARCHAR(50) NOT NULL,
    to_chain VARCHAR(50) NOT NULL,
    amount DECIMAL NOT NULL,
    currency VARCHAR(20) DEFAULT 'USDC',

    -- Addresses
    source_address VARCHAR(100) NOT NULL,
    destination_address VARCHAR(100) NOT NULL,

    -- Transaction tracking
    source_tx_hash VARCHAR(100),
    destination_tx_hash VARCHAR(100),
    message_hash VARCHAR(100),        -- For CCTP attestation lookup
    attestation TEXT,                 -- CCTP attestation data

    -- Status tracking
    status VARCHAR(20) DEFAULT 'initiated',
    -- Statuses: 'initiated', 'source_confirmed', 'attesting', 'attestation_ready',
    --           'completing', 'completed', 'failed'
    status_message TEXT,
    estimated_completion TIMESTAMPTZ,

    -- Fees breakdown
    bridge_fee DECIMAL,
    gas_fee_source DECIMAL,
    gas_fee_dest DECIMAL,
    total_fee DECIMAL,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Index for pending bridges (for status polling)
CREATE INDEX IF NOT EXISTS idx_bridge_pending
    ON bridge_transactions(status, updated_at)
    WHERE status NOT IN ('completed', 'failed');

CREATE INDEX IF NOT EXISTS idx_bridge_user
    ON bridge_transactions(user_id, created_at DESC);


-- ============================================
-- 3. CONTEXT AWARENESS & INSIGHTS
-- ============================================

-- Spending categories (auto-detected from transactions)
CREATE TABLE IF NOT EXISTS spending_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    tx_id UUID REFERENCES transactions(id) ON DELETE CASCADE,
    tx_hash VARCHAR(100),

    -- Categorization
    category VARCHAR(50) NOT NULL,     -- 'entertainment', 'food', 'subscription', 'transfer', 'defi', 'shopping', 'travel', 'other'
    subcategory VARCHAR(50),           -- More specific: 'netflix', 'starbucks', 'aave_deposit'
    merchant_name VARCHAR(100),
    merchant_logo_url TEXT,

    -- Transaction details
    amount DECIMAL NOT NULL,
    currency VARCHAR(20) DEFAULT 'USD',
    is_recurring BOOLEAN DEFAULT false,

    -- Confidence of categorization
    confidence DECIMAL DEFAULT 1.0,    -- 0.0 to 1.0
    manually_set BOOLEAN DEFAULT false,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User alert configurations
CREATE TABLE IF NOT EXISTS user_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,

    -- Alert definition
    alert_type VARCHAR(50) NOT NULL,  -- 'low_balance', 'high_balance', 'large_tx', 'weekly_summary', 'price_alert'
    alert_name VARCHAR(100),

    -- Thresholds (depending on alert type)
    threshold_value DECIMAL,
    threshold_currency VARCHAR(20) DEFAULT 'USD',
    threshold_chain VARCHAR(50),       -- NULL = total across all chains
    comparison VARCHAR(10),            -- 'below', 'above', 'equals'

    -- For price alerts
    asset VARCHAR(20),                 -- 'ETH', 'BTC'
    target_price DECIMAL,

    -- Status
    is_enabled BOOLEAN DEFAULT true,
    cooldown_minutes INTEGER DEFAULT 60,  -- Min time between triggers

    -- Delivery preferences
    notify_email BOOLEAN DEFAULT true,
    notify_push BOOLEAN DEFAULT false,
    notify_in_app BOOLEAN DEFAULT true,

    -- Tracking
    last_triggered_at TIMESTAMPTZ,
    trigger_count INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Pre-computed spending summaries
CREATE TABLE IF NOT EXISTS spending_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,

    -- Period
    period_type VARCHAR(20) NOT NULL,  -- 'daily', 'weekly', 'monthly'
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- Totals
    total_spent DECIMAL DEFAULT 0,
    total_received DECIMAL DEFAULT 0,
    net_flow DECIMAL DEFAULT 0,        -- received - spent
    transaction_count INTEGER DEFAULT 0,

    -- Category breakdown
    by_category JSONB DEFAULT '{}',    -- {"entertainment": 45.00, "food": 120.00}
    by_chain JSONB DEFAULT '{}',       -- {"base": 100.00, "arbitrum": 50.00}

    -- Top items
    top_merchants JSONB DEFAULT '[]',  -- [{"name": "Amazon", "amount": 150.00}, ...]
    largest_transaction JSONB,          -- {amount, merchant, date}

    -- Comparisons
    vs_previous_period_percent DECIMAL,  -- e.g., +15.5 means 15.5% more than previous
    vs_average_percent DECIMAL,          -- vs user's historical average

    -- Insights (AI-generated)
    insights JSONB DEFAULT '[]',       -- ["You spent 20% more on food this week", ...]

    computed_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, period_type, period_start)
);

-- Detected subscriptions
CREATE TABLE IF NOT EXISTS detected_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,

    -- Subscription details
    merchant_name VARCHAR(100) NOT NULL,
    merchant_id VARCHAR(100),          -- Bitrefill product ID if applicable
    amount DECIMAL NOT NULL,
    currency VARCHAR(20) DEFAULT 'USD',

    -- Frequency detection
    frequency VARCHAR(20) NOT NULL,    -- 'weekly', 'monthly', 'yearly'
    day_of_month INTEGER,              -- 1-31 for monthly
    day_of_week INTEGER,               -- 0-6 for weekly

    -- Tracking
    last_charge_date DATE,
    next_expected_date DATE,
    charge_count INTEGER DEFAULT 0,

    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'cancelled', 'paused'
    confidence DECIMAL DEFAULT 0.8,

    -- User preferences
    is_hidden BOOLEAN DEFAULT false,
    custom_name VARCHAR(100),
    auto_pay_enabled BOOLEAN DEFAULT false,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for insights
CREATE INDEX IF NOT EXISTS idx_spending_categories_user
    ON spending_categories(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_spending_categories_category
    ON spending_categories(user_id, category);

CREATE INDEX IF NOT EXISTS idx_user_alerts_active
    ON user_alerts(user_id, is_enabled)
    WHERE is_enabled = true;

CREATE INDEX IF NOT EXISTS idx_spending_summaries_lookup
    ON spending_summaries(user_id, period_type, period_start DESC);

CREATE INDEX IF NOT EXISTS idx_detected_subscriptions_user
    ON detected_subscriptions(user_id, status)
    WHERE status = 'active';


-- ============================================
-- 4. HELPER FUNCTIONS
-- ============================================

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to tables with updated_at
DROP TRIGGER IF EXISTS update_scheduled_tasks_updated_at ON scheduled_tasks;
CREATE TRIGGER update_scheduled_tasks_updated_at
    BEFORE UPDATE ON scheduled_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_bridge_transactions_updated_at ON bridge_transactions;
CREATE TRIGGER update_bridge_transactions_updated_at
    BEFORE UPDATE ON bridge_transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_alerts_updated_at ON user_alerts;
CREATE TRIGGER update_user_alerts_updated_at
    BEFORE UPDATE ON user_alerts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================
-- 5. ROW LEVEL SECURITY
-- ============================================

-- Enable RLS on new tables
ALTER TABLE scheduled_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE scheduled_task_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE bridge_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE spending_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE spending_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE detected_subscriptions ENABLE ROW LEVEL SECURITY;

-- Policies (users can only see their own data)
CREATE POLICY scheduled_tasks_user_policy ON scheduled_tasks
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY scheduled_task_runs_user_policy ON scheduled_task_runs
    FOR ALL USING (task_id IN (SELECT id FROM scheduled_tasks WHERE user_id = auth.uid()));

CREATE POLICY bridge_transactions_user_policy ON bridge_transactions
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY spending_categories_user_policy ON spending_categories
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY user_alerts_user_policy ON user_alerts
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY spending_summaries_user_policy ON spending_summaries
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY detected_subscriptions_user_policy ON detected_subscriptions
    FOR ALL USING (user_id = auth.uid());


-- ============================================
-- 6. SAMPLE DATA / DEFAULTS
-- ============================================

-- Default alert types users can enable
COMMENT ON TABLE user_alerts IS 'User-configurable alerts. Types: low_balance, high_balance, large_tx, weekly_summary, price_alert';

-- Category taxonomy
COMMENT ON TABLE spending_categories IS 'Categories: entertainment, food, subscription, transfer, defi, shopping, travel, utilities, other';
