-- Performance optimization: Add composite indexes for common queries
-- Run this in Supabase SQL Editor to improve query performance

-- Transactions table indexes
CREATE INDEX IF NOT EXISTS idx_transactions_user_created
    ON transactions(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_transactions_status
    ON transactions(status)
    WHERE status = 'pending';

-- User settings indexes (already covered by unique constraint on user_id)

-- OAuth connections indexes
CREATE INDEX IF NOT EXISTS idx_oauth_user_provider
    ON user_oauth_connections(user_id, provider);

CREATE INDEX IF NOT EXISTS idx_oauth_active
    ON user_oauth_connections(is_active)
    WHERE is_active = true;

-- Approval history indexes
CREATE INDEX IF NOT EXISTS idx_approval_user_status
    ON approval_history(user_id, status);

CREATE INDEX IF NOT EXISTS idx_approval_pending
    ON approval_history(status, created_at DESC)
    WHERE status = 'pending';

-- Sessions table indexes
CREATE INDEX IF NOT EXISTS idx_sessions_token
    ON sessions(session_token);

CREATE INDEX IF NOT EXISTS idx_sessions_expires
    ON sessions(expires_at)
    WHERE expires_at > NOW();

-- Wallets table indexes
CREATE INDEX IF NOT EXISTS idx_wallets_user_chain
    ON wallets(user_id, chain);

-- Comment indexes for documentation
COMMENT ON INDEX idx_transactions_user_created IS 'Optimizes user transaction history queries';
COMMENT ON INDEX idx_transactions_status IS 'Partial index for pending transactions only';
COMMENT ON INDEX idx_oauth_user_provider IS 'Speeds up OAuth connection lookups';
COMMENT ON INDEX idx_approval_user_status IS 'Optimizes approval filtering by user and status';
COMMENT ON INDEX idx_sessions_token IS 'Fast session token lookups for authentication';
COMMENT ON INDEX idx_wallets_user_chain IS 'Optimizes multi-chain wallet queries';

-- Analyze tables to update query planner statistics
ANALYZE transactions;
ANALYZE user_oauth_connections;
ANALYZE approval_history;
ANALYZE sessions;
ANALYZE wallets;
