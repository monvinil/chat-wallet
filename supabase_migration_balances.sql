-- Migration: Add internal balance tracking for gasless transactions
-- Run this after the initial schema

-- User balances table (internal accounting)
CREATE TABLE IF NOT EXISTS user_balances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    chain TEXT NOT NULL,
    currency TEXT NOT NULL,
    deposited DECIMAL(20, 8) DEFAULT 0,
    spent DECIMAL(20, 8) DEFAULT 0,
    reserved DECIMAL(20, 8) DEFAULT 0,  -- For pending transactions
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, chain, currency)
);

-- Computed available balance
CREATE OR REPLACE VIEW user_available_balance AS
SELECT
    user_id,
    chain,
    currency,
    (deposited - spent - reserved) as available,
    deposited,
    spent,
    reserved
FROM user_balances;

-- Update transaction table to track internal vs on-chain
ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS is_meta_tx BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS gas_paid_by_relayer DECIMAL(20, 8) DEFAULT 0,
ADD COLUMN IF NOT EXISTS user_signature TEXT;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_user_balances_user_id ON user_balances(user_id);
CREATE INDEX IF NOT EXISTS idx_user_balances_chain ON user_balances(chain);

-- RLS Policies
ALTER TABLE user_balances ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own balances"
    ON user_balances FOR SELECT
    USING (user_id::text = auth.uid()::text);

CREATE POLICY "Users can update own balances"
    ON user_balances FOR UPDATE
    USING (user_id::text = auth.uid()::text);

-- Grant access
GRANT SELECT ON user_available_balance TO authenticated;

-- Comments
COMMENT ON TABLE user_balances IS 'Internal balance tracking for gasless transactions';
COMMENT ON COLUMN user_balances.deposited IS 'Total USDC deposited by user';
COMMENT ON COLUMN user_balances.spent IS 'Total USDC spent (including gas + fees)';
COMMENT ON COLUMN user_balances.reserved IS 'USDC reserved for pending transactions';
COMMENT ON COLUMN transactions.is_meta_tx IS 'True if this is a gasless meta-transaction';
COMMENT ON COLUMN transactions.gas_paid_by_relayer IS 'Gas cost paid by relayer in USD';
