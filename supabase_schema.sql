-- Chat Wallet Database Schema for Supabase
-- Run this in your Supabase SQL Editor after creating the project

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    auth_provider TEXT DEFAULT 'google',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Wallets table (stores addresses only, NOT private keys!)
CREATE TABLE wallets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    chain TEXT NOT NULL,
    address TEXT NOT NULL,
    is_mock BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, chain)
);

-- Transactions table
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    wallet_id UUID REFERENCES wallets(id) ON DELETE SET NULL,
    tx_hash TEXT,
    chain TEXT NOT NULL,
    type TEXT NOT NULL, -- 'deposit', 'withdrawal', 'swap', 'gift_card_purchase'
    amount DECIMAL(20, 8) NOT NULL,
    currency TEXT NOT NULL,
    fee_charged DECIMAL(20, 8) DEFAULT 0,
    status TEXT DEFAULT 'pending', -- 'pending', 'confirmed', 'failed'
    metadata JSONB, -- Additional data (product info, etc.)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for better query performance
CREATE INDEX idx_wallets_user_id ON wallets(user_id);
CREATE INDEX idx_wallets_chain ON wallets(chain);
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_created_at ON transactions(created_at DESC);

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to users table
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to transactions table
CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) Policies
-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE wallets ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users can view own profile"
    ON users FOR SELECT
    USING (auth.uid()::text = id::text);

CREATE POLICY "Users can view own wallets"
    ON wallets FOR SELECT
    USING (user_id::text = auth.uid()::text);

CREATE POLICY "Users can insert own wallets"
    ON wallets FOR INSERT
    WITH CHECK (user_id::text = auth.uid()::text);

CREATE POLICY "Users can view own transactions"
    ON transactions FOR SELECT
    USING (user_id::text = auth.uid()::text);

CREATE POLICY "Users can insert own transactions"
    ON transactions FOR INSERT
    WITH CHECK (user_id::text = auth.uid()::text);

-- View for aggregated balances (optional - for future analytics)
CREATE VIEW user_balance_summary AS
SELECT
    user_id,
    chain,
    currency,
    SUM(CASE WHEN type IN ('deposit', 'swap_in') THEN amount ELSE -amount END) as net_balance
FROM transactions
WHERE status = 'confirmed'
GROUP BY user_id, chain, currency;

-- Grant access to authenticated users
GRANT SELECT ON user_balance_summary TO authenticated;

-- Comments for documentation
COMMENT ON TABLE users IS 'User accounts authenticated via OAuth';
COMMENT ON TABLE wallets IS 'User wallet addresses per chain (NO PRIVATE KEYS!)';
COMMENT ON TABLE transactions IS 'Transaction history for all user operations';
COMMENT ON COLUMN wallets.is_mock IS 'True if this is a mocked address (not real blockchain)';
COMMENT ON COLUMN transactions.metadata IS 'Additional transaction data in JSON format';
