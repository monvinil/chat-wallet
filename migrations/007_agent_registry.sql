-- ============================================
-- Agent Registry Migration
-- Foundation for the Agent Marketplace (THE MOAT)
-- February 2026
-- ============================================

-- ============================================
-- 1. AGENTS TABLE - Core Registry
-- ============================================

CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Creator info
    creator_id UUID REFERENCES users(id) ON DELETE SET NULL,
    creator_address VARCHAR(100) NOT NULL,

    -- Agent identity
    slug VARCHAR(100) UNIQUE NOT NULL,           -- URL-friendly identifier: "crypto-news-bot"
    name VARCHAR(200) NOT NULL,
    description TEXT,
    avatar_url TEXT,
    banner_url TEXT,

    -- Categorization
    category VARCHAR(50) NOT NULL,               -- 'trading', 'content', 'service', 'character', 'yield', 'utility'
    tags TEXT[] DEFAULT '{}',                    -- ['defi', 'news', 'automation']

    -- Technical
    agent_type VARCHAR(50) NOT NULL DEFAULT 'external',  -- 'internal' (platform-built), 'external' (community)
    runtime VARCHAR(50) DEFAULT 'python',        -- 'python', 'typescript', 'docker'
    endpoint_url TEXT,                           -- For external agents: webhook/API endpoint
    sdk_version VARCHAR(20),                     -- Agent SDK version used
    source_code_url TEXT,                        -- GitHub link (optional, for verified agents)

    -- Monetization
    pricing_model VARCHAR(50) DEFAULT 'free',    -- 'free', 'per_request', 'subscription', 'tips_only'
    price_per_request DECIMAL,                   -- In USDC (for per_request model)
    subscription_price_monthly DECIMAL,          -- In USDC (for subscription model)
    min_tip DECIMAL DEFAULT 0.01,                -- Minimum tip amount
    accepts_tips BOOLEAN DEFAULT true,

    -- Revenue split (defaults, can be customized)
    creator_share_percent DECIMAL DEFAULT 70,    -- Creator gets 70%
    platform_share_percent DECIMAL DEFAULT 20,   -- Platform gets 20%
    referrer_share_percent DECIMAL DEFAULT 10,   -- Referrer gets 10%

    -- Vault (agent's wallet for earnings)
    vault_address VARCHAR(100),                  -- Agent's dedicated wallet address
    vault_chain VARCHAR(50) DEFAULT 'base',

    -- Status & verification
    status VARCHAR(30) DEFAULT 'draft',          -- 'draft', 'pending_review', 'active', 'suspended', 'archived'
    is_verified BOOLEAN DEFAULT false,           -- Platform-verified (security audit passed)
    is_featured BOOLEAN DEFAULT false,           -- Featured on marketplace
    verification_level VARCHAR(20) DEFAULT 'none', -- 'none', 'basic', 'full', 'audited'

    -- Capabilities (what the agent can do)
    capabilities JSONB DEFAULT '[]',             -- ['accept_payments', 'make_payments', 'access_yield', 'trade']
    required_permissions JSONB DEFAULT '[]',     -- Permissions needed from user

    -- Rate limits
    requests_per_minute INTEGER DEFAULT 60,
    requests_per_day INTEGER DEFAULT 10000,

    -- Statistics (denormalized for fast access)
    total_users INTEGER DEFAULT 0,
    total_requests INTEGER DEFAULT 0,
    total_revenue_usdc DECIMAL DEFAULT 0,
    average_rating DECIMAL DEFAULT 0,
    rating_count INTEGER DEFAULT 0,

    -- Metadata
    metadata JSONB DEFAULT '{}',                 -- Flexible additional data
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    published_at TIMESTAMPTZ,
    last_active_at TIMESTAMPTZ
);

-- Indexes for agents
CREATE INDEX IF NOT EXISTS idx_agents_creator ON agents(creator_id);
CREATE INDEX IF NOT EXISTS idx_agents_slug ON agents(slug);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_agents_category ON agents(category, status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_agents_featured ON agents(is_featured, total_users DESC) WHERE status = 'active' AND is_featured = true;
CREATE INDEX IF NOT EXISTS idx_agents_popular ON agents(total_users DESC, average_rating DESC) WHERE status = 'active';


-- ============================================
-- 2. AGENT VERSIONS - Track deployments
-- ============================================

CREATE TABLE IF NOT EXISTS agent_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE NOT NULL,

    version VARCHAR(50) NOT NULL,                -- Semantic version: "1.0.0"
    changelog TEXT,

    -- Deployment info
    endpoint_url TEXT,
    config_hash VARCHAR(100),                    -- Hash of agent config for integrity

    -- Status
    status VARCHAR(20) DEFAULT 'active',         -- 'active', 'deprecated', 'rollback'
    is_current BOOLEAN DEFAULT false,

    -- Metrics for this version
    total_requests INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER,

    deployed_at TIMESTAMPTZ DEFAULT NOW(),
    deprecated_at TIMESTAMPTZ,

    UNIQUE(agent_id, version)
);

CREATE INDEX IF NOT EXISTS idx_agent_versions_current ON agent_versions(agent_id, is_current) WHERE is_current = true;


-- ============================================
-- 3. AGENT EARNINGS - Revenue Tracking
-- ============================================

CREATE TABLE IF NOT EXISTS agent_earnings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE NOT NULL,

    -- Transaction reference
    tx_hash VARCHAR(100),
    payment_type VARCHAR(50) NOT NULL,           -- 'request', 'subscription', 'tip', 'yield'

    -- Amounts
    gross_amount DECIMAL NOT NULL,               -- Total payment received
    currency VARCHAR(20) DEFAULT 'USDC',

    -- Revenue split
    creator_amount DECIMAL NOT NULL,
    platform_amount DECIMAL NOT NULL,
    referrer_amount DECIMAL DEFAULT 0,
    referrer_id UUID REFERENCES users(id),

    -- Payer info
    payer_id UUID REFERENCES users(id),
    payer_address VARCHAR(100),

    -- Status
    status VARCHAR(20) DEFAULT 'pending',        -- 'pending', 'confirmed', 'distributed', 'failed'
    distributed_at TIMESTAMPTZ,

    -- Metadata
    request_id UUID,                             -- Reference to the agent request that triggered this
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_earnings_agent ON agent_earnings(agent_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_earnings_creator ON agent_earnings(agent_id, status) WHERE status = 'confirmed';
CREATE INDEX IF NOT EXISTS idx_agent_earnings_pending ON agent_earnings(status) WHERE status = 'pending';


-- ============================================
-- 4. AGENT SUBSCRIPTIONS - User subscriptions
-- ============================================

CREATE TABLE IF NOT EXISTS agent_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,

    -- Subscription details
    plan_type VARCHAR(50) DEFAULT 'monthly',     -- 'monthly', 'yearly', 'lifetime'
    price_usdc DECIMAL NOT NULL,

    -- Status
    status VARCHAR(20) DEFAULT 'active',         -- 'active', 'cancelled', 'expired', 'paused'

    -- Dates
    started_at TIMESTAMPTZ DEFAULT NOW(),
    current_period_start TIMESTAMPTZ DEFAULT NOW(),
    current_period_end TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,

    -- Payment tracking
    last_payment_at TIMESTAMPTZ,
    last_payment_tx VARCHAR(100),
    payment_failures INTEGER DEFAULT 0,

    -- Auto-renew
    auto_renew BOOLEAN DEFAULT true,

    UNIQUE(agent_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_agent_subscriptions_user ON agent_subscriptions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_agent_subscriptions_agent ON agent_subscriptions(agent_id, status);
CREATE INDEX IF NOT EXISTS idx_agent_subscriptions_renewal ON agent_subscriptions(current_period_end, auto_renew)
    WHERE status = 'active' AND auto_renew = true;


-- ============================================
-- 5. AGENT REQUESTS - Usage Tracking
-- ============================================

CREATE TABLE IF NOT EXISTS agent_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Request details
    request_type VARCHAR(50) NOT NULL,           -- 'message', 'action', 'query'
    input_hash VARCHAR(100),                     -- Hash of input for deduplication

    -- Response
    response_status VARCHAR(20),                 -- 'success', 'error', 'timeout', 'rate_limited'
    response_time_ms INTEGER,
    error_code VARCHAR(50),

    -- Payment (if applicable)
    was_paid BOOLEAN DEFAULT false,
    payment_amount DECIMAL,
    payment_tx VARCHAR(100),

    -- x402 tracking
    x402_request_id VARCHAR(100),
    x402_payment_verified BOOLEAN,

    -- Metadata
    ip_hash VARCHAR(100),                        -- Hashed IP for rate limiting
    user_agent VARCHAR(500),
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Partitioned index for time-series queries
CREATE INDEX IF NOT EXISTS idx_agent_requests_agent_time ON agent_requests(agent_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_requests_user ON agent_requests(user_id, created_at DESC) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_agent_requests_x402 ON agent_requests(x402_request_id) WHERE x402_request_id IS NOT NULL;


-- ============================================
-- 6. AGENT REVIEWS - Ratings & Reviews
-- ============================================

CREATE TABLE IF NOT EXISTS agent_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,

    -- Review content
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(200),
    body TEXT,

    -- Verification
    is_verified_user BOOLEAN DEFAULT false,      -- User actually used the agent
    usage_count INTEGER DEFAULT 0,               -- How many times user used agent before review

    -- Moderation
    status VARCHAR(20) DEFAULT 'published',      -- 'pending', 'published', 'flagged', 'removed'
    flagged_reason TEXT,

    -- Helpfulness
    helpful_count INTEGER DEFAULT 0,
    not_helpful_count INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(agent_id, user_id)  -- One review per user per agent
);

CREATE INDEX IF NOT EXISTS idx_agent_reviews_agent ON agent_reviews(agent_id, status, created_at DESC) WHERE status = 'published';
CREATE INDEX IF NOT EXISTS idx_agent_reviews_rating ON agent_reviews(agent_id, rating) WHERE status = 'published';


-- ============================================
-- 7. AGENT CAPABILITIES - Permission System
-- ============================================

CREATE TABLE IF NOT EXISTS agent_capabilities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Capability definition
    name VARCHAR(100) UNIQUE NOT NULL,           -- 'accept_payments', 'make_payments', 'yield_access'
    display_name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Risk level
    risk_level VARCHAR(20) DEFAULT 'low',        -- 'low', 'medium', 'high', 'critical'
    requires_verification BOOLEAN DEFAULT false,

    -- Limits
    daily_limit_usdc DECIMAL,                    -- Max daily usage in USDC
    per_request_limit_usdc DECIMAL,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed default capabilities
INSERT INTO agent_capabilities (name, display_name, description, risk_level, requires_verification)
VALUES
    ('accept_payments', 'Accept Payments', 'Agent can receive payments via x402 or direct transfer', 'low', false),
    ('make_payments', 'Make Payments', 'Agent can send payments on user behalf', 'high', true),
    ('yield_access', 'Yield Strategies', 'Agent can deposit/withdraw from yield protocols', 'high', true),
    ('trade', 'Trading', 'Agent can execute trades on DEXs or perp platforms', 'critical', true),
    ('read_balance', 'Read Balance', 'Agent can view user wallet balance', 'low', false),
    ('read_history', 'Read History', 'Agent can view user transaction history', 'medium', false),
    ('notifications', 'Send Notifications', 'Agent can send notifications to user', 'low', false),
    ('schedule_tasks', 'Schedule Tasks', 'Agent can create scheduled tasks', 'medium', false)
ON CONFLICT (name) DO NOTHING;


-- ============================================
-- 8. USER AGENT PERMISSIONS - Per-user grants
-- ============================================

CREATE TABLE IF NOT EXISTS user_agent_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE NOT NULL,

    -- Granted capabilities
    capabilities TEXT[] DEFAULT '{}',            -- ['accept_payments', 'read_balance']

    -- Limits (override defaults)
    daily_limit_usdc DECIMAL,
    per_request_limit_usdc DECIMAL,

    -- Status
    status VARCHAR(20) DEFAULT 'active',         -- 'active', 'revoked', 'expired'

    -- Tracking
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    revoked_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,

    UNIQUE(user_id, agent_id)
);

CREATE INDEX IF NOT EXISTS idx_user_agent_permissions_user ON user_agent_permissions(user_id, status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_user_agent_permissions_agent ON user_agent_permissions(agent_id, status) WHERE status = 'active';


-- ============================================
-- 9. AGENT WEBHOOKS - Event notifications
-- ============================================

CREATE TABLE IF NOT EXISTS agent_webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE NOT NULL,

    -- Webhook config
    url TEXT NOT NULL,
    secret VARCHAR(100),                         -- For signature verification

    -- Events to subscribe
    events TEXT[] DEFAULT '{}',                  -- ['payment_received', 'subscription_started', 'request']

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Health tracking
    last_called_at TIMESTAMPTZ,
    last_success_at TIMESTAMPTZ,
    consecutive_failures INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================
-- 10. ROW LEVEL SECURITY
-- ============================================

ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_earnings ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_agent_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_webhooks ENABLE ROW LEVEL SECURITY;

-- Agents: Public read for active, owner can manage
CREATE POLICY agents_read_active ON agents
    FOR SELECT USING (status = 'active' OR creator_id = auth.uid());

CREATE POLICY agents_manage_own ON agents
    FOR ALL USING (creator_id = auth.uid());

-- Agent versions: Same as agents
CREATE POLICY agent_versions_policy ON agent_versions
    FOR ALL USING (agent_id IN (SELECT id FROM agents WHERE creator_id = auth.uid() OR status = 'active'));

-- Earnings: Creator can see their agent earnings
CREATE POLICY agent_earnings_creator ON agent_earnings
    FOR SELECT USING (agent_id IN (SELECT id FROM agents WHERE creator_id = auth.uid()));

-- Subscriptions: Users see their own
CREATE POLICY agent_subscriptions_user ON agent_subscriptions
    FOR ALL USING (user_id = auth.uid());

-- Requests: Users see their own
CREATE POLICY agent_requests_user ON agent_requests
    FOR SELECT USING (user_id = auth.uid());

-- Reviews: Public read, users manage their own
CREATE POLICY agent_reviews_read ON agent_reviews
    FOR SELECT USING (status = 'published' OR user_id = auth.uid());

CREATE POLICY agent_reviews_manage ON agent_reviews
    FOR ALL USING (user_id = auth.uid());

-- Permissions: Users manage their own
CREATE POLICY user_agent_permissions_policy ON user_agent_permissions
    FOR ALL USING (user_id = auth.uid());

-- Webhooks: Agent owner manages
CREATE POLICY agent_webhooks_policy ON agent_webhooks
    FOR ALL USING (agent_id IN (SELECT id FROM agents WHERE creator_id = auth.uid()));


-- ============================================
-- 11. TRIGGERS
-- ============================================

-- Update agent stats on earnings
CREATE OR REPLACE FUNCTION update_agent_revenue()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'confirmed' AND (OLD.status IS NULL OR OLD.status != 'confirmed') THEN
        UPDATE agents
        SET total_revenue_usdc = total_revenue_usdc + NEW.gross_amount
        WHERE id = NEW.agent_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_agent_revenue
    AFTER INSERT OR UPDATE ON agent_earnings
    FOR EACH ROW EXECUTE FUNCTION update_agent_revenue();

-- Update agent rating on review
CREATE OR REPLACE FUNCTION update_agent_rating()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE agents
    SET
        average_rating = (SELECT AVG(rating) FROM agent_reviews WHERE agent_id = NEW.agent_id AND status = 'published'),
        rating_count = (SELECT COUNT(*) FROM agent_reviews WHERE agent_id = NEW.agent_id AND status = 'published')
    WHERE id = NEW.agent_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_agent_rating
    AFTER INSERT OR UPDATE OR DELETE ON agent_reviews
    FOR EACH ROW EXECUTE FUNCTION update_agent_rating();

-- Update timestamps
CREATE TRIGGER update_agents_updated_at
    BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_reviews_updated_at
    BEFORE UPDATE ON agent_reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================
-- 12. VIEWS
-- ============================================

-- Agent leaderboard view
CREATE OR REPLACE VIEW agent_leaderboard AS
SELECT
    a.id,
    a.slug,
    a.name,
    a.category,
    a.avatar_url,
    a.pricing_model,
    a.total_users,
    a.total_revenue_usdc,
    a.average_rating,
    a.rating_count,
    a.is_verified,
    a.is_featured,
    u.email as creator_email,
    a.created_at
FROM agents a
LEFT JOIN users u ON a.creator_id = u.id
WHERE a.status = 'active'
ORDER BY a.total_users DESC, a.average_rating DESC;

-- Creator earnings summary
CREATE OR REPLACE VIEW creator_earnings_summary AS
SELECT
    a.creator_id,
    COUNT(DISTINCT a.id) as agent_count,
    SUM(a.total_revenue_usdc) as total_revenue,
    SUM(ae.creator_amount) as total_creator_earnings,
    COUNT(DISTINCT ae.payer_id) as unique_payers
FROM agents a
LEFT JOIN agent_earnings ae ON a.id = ae.agent_id AND ae.status = 'confirmed'
WHERE a.creator_id IS NOT NULL
GROUP BY a.creator_id;


-- ============================================
-- COMMENTS
-- ============================================

COMMENT ON TABLE agents IS 'Core agent registry - community-created AI agents that can earn money';
COMMENT ON TABLE agent_earnings IS 'Revenue tracking per agent with automatic 70/20/10 split';
COMMENT ON TABLE agent_subscriptions IS 'User subscriptions to paid agents';
COMMENT ON TABLE agent_capabilities IS 'Permission system - what agents can do';
COMMENT ON TABLE user_agent_permissions IS 'Per-user permission grants to agents';
COMMENT ON COLUMN agents.slug IS 'URL-friendly unique identifier, e.g., crypto-news-bot';
COMMENT ON COLUMN agents.capabilities IS 'JSON array of capability names the agent requires';
COMMENT ON COLUMN agents.vault_address IS 'Agent dedicated wallet for receiving earnings';
