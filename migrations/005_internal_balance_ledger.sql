-- Migration: Internal Balance Ledger for Financial Integrity
-- Run this in Supabase SQL Editor
-- This provides double-spend protection and transaction tracking

-- ============================================================================
-- BALANCES TABLE
-- Tracks user balances per chain/token (source of truth, not blockchain queries)
-- ============================================================================
CREATE TABLE IF NOT EXISTS balances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    chain VARCHAR(30) NOT NULL,           -- 'base-mainnet', 'arbitrum-mainnet', 'solana-mainnet', etc.
    token VARCHAR(20) NOT NULL,           -- 'USDC', 'ETH', 'SOL', 'aUSDC', etc.

    -- Balance tracking (all in token's native decimals, stored as decimal for precision)
    available_balance DECIMAL(24,6) NOT NULL DEFAULT 0,   -- Spendable balance
    pending_in DECIMAL(24,6) NOT NULL DEFAULT 0,          -- Incoming (unconfirmed deposits)
    pending_out DECIMAL(24,6) NOT NULL DEFAULT 0,         -- Outgoing (unconfirmed sends)
    locked_balance DECIMAL(24,6) NOT NULL DEFAULT 0,      -- Locked (in yield, scheduled, etc.)

    -- Computed total: available + pending_in - pending_out + locked
    -- Constraint: available_balance >= 0 at all times

    -- Metadata
    last_sync_at TIMESTAMPTZ,             -- Last blockchain sync timestamp
    last_sync_block BIGINT,               -- Last synced block number
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint: one balance record per user/chain/token
    CONSTRAINT balances_unique UNIQUE (user_id, chain, token),

    -- Prevent negative available balance
    CONSTRAINT positive_available CHECK (available_balance >= 0),
    CONSTRAINT positive_pending_in CHECK (pending_in >= 0),
    CONSTRAINT positive_pending_out CHECK (pending_out >= 0),
    CONSTRAINT positive_locked CHECK (locked_balance >= 0)
);

-- ============================================================================
-- LEDGER ENTRIES TABLE
-- Immutable transaction log (append-only, never update/delete)
-- ============================================================================
CREATE TABLE IF NOT EXISTS ledger_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Transaction identification
    idempotency_key VARCHAR(100),         -- Client-provided key for duplicate prevention
    tx_hash VARCHAR(100),                 -- Blockchain transaction hash (if applicable)

    -- Entry details
    entry_type VARCHAR(30) NOT NULL,      -- 'deposit', 'withdrawal', 'send', 'receive', 'yield_deposit', 'yield_withdraw', 'fee', 'adjustment'
    chain VARCHAR(30) NOT NULL,
    token VARCHAR(20) NOT NULL,

    -- Amount (positive = credit, negative = debit)
    amount DECIMAL(24,6) NOT NULL,
    fee_amount DECIMAL(24,6) DEFAULT 0,

    -- Balance snapshot (for audit trail)
    balance_before DECIMAL(24,6),
    balance_after DECIMAL(24,6),

    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 'pending', 'confirming', 'confirmed', 'failed', 'reversed'
    confirmations INTEGER DEFAULT 0,
    required_confirmations INTEGER DEFAULT 1,

    -- Counterparty info
    counterparty_address VARCHAR(100),    -- To/from address
    counterparty_user_id UUID,            -- If internal transfer between users

    -- Metadata
    description TEXT,
    metadata JSONB,                        -- Additional data (gift card details, yield protocol, etc.)

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    confirmed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Prevent duplicate idempotency keys per user
    CONSTRAINT unique_idempotency UNIQUE (user_id, idempotency_key)
);

-- ============================================================================
-- PENDING TRANSACTIONS TABLE
-- Tracks transactions waiting for blockchain confirmation
-- ============================================================================
CREATE TABLE IF NOT EXISTS pending_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ledger_entry_id UUID REFERENCES ledger_entries(id) ON DELETE CASCADE,

    -- Transaction details
    tx_hash VARCHAR(100) NOT NULL,
    chain VARCHAR(30) NOT NULL,
    tx_type VARCHAR(30) NOT NULL,         -- 'send', 'deposit', 'yield_deposit', etc.

    -- Amount reserved from balance
    amount DECIMAL(24,6) NOT NULL,
    fee_amount DECIMAL(24,6) DEFAULT 0,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 'pending', 'confirming', 'confirmed', 'failed', 'dropped'
    confirmations INTEGER DEFAULT 0,
    first_seen_block BIGINT,
    confirmed_block BIGINT,

    -- Retry tracking
    retry_count INTEGER DEFAULT 0,
    last_check_at TIMESTAMPTZ,

    -- Expiry (for dropped transactions)
    expires_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_pending_tx UNIQUE (chain, tx_hash)
);

-- ============================================================================
-- NONCES TABLE
-- Tracks used nonces for replay protection
-- ============================================================================
CREATE TABLE IF NOT EXISTS used_nonces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_address VARCHAR(100) NOT NULL,
    chain VARCHAR(30) NOT NULL,
    nonce BIGINT NOT NULL,
    tx_hash VARCHAR(100),
    used_at TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (wallet_address, chain, nonce)
);

-- Drop the default primary key and recreate as composite
ALTER TABLE used_nonces DROP CONSTRAINT IF EXISTS used_nonces_pkey;
ALTER TABLE used_nonces ADD PRIMARY KEY (wallet_address, chain, nonce);

-- ============================================================================
-- INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_balances_user ON balances(user_id);
CREATE INDEX IF NOT EXISTS idx_balances_chain_token ON balances(chain, token);

CREATE INDEX IF NOT EXISTS idx_ledger_user ON ledger_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_ledger_tx_hash ON ledger_entries(tx_hash) WHERE tx_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ledger_status ON ledger_entries(status) WHERE status IN ('pending', 'confirming');
CREATE INDEX IF NOT EXISTS idx_ledger_created ON ledger_entries(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ledger_idempotency ON ledger_entries(idempotency_key) WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_pending_tx_user ON pending_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_pending_tx_status ON pending_transactions(status) WHERE status IN ('pending', 'confirming');
CREATE INDEX IF NOT EXISTS idx_pending_tx_hash ON pending_transactions(tx_hash);

CREATE INDEX IF NOT EXISTS idx_nonces_wallet ON used_nonces(wallet_address, chain);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================
ALTER TABLE balances ENABLE ROW LEVEL SECURITY;
ALTER TABLE ledger_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE pending_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE used_nonces ENABLE ROW LEVEL SECURITY;

-- Users can view their own balances
CREATE POLICY "Users can view own balances" ON balances
    FOR SELECT USING (auth.uid() = user_id);

-- Users can view their own ledger entries
CREATE POLICY "Users can view own ledger" ON ledger_entries
    FOR SELECT USING (auth.uid() = user_id);

-- Users can view their own pending transactions
CREATE POLICY "Users can view own pending tx" ON pending_transactions
    FOR SELECT USING (auth.uid() = user_id);

-- Service role has full access (for balance updates, background jobs)
CREATE POLICY "Service role balances" ON balances
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role ledger" ON ledger_entries
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role pending_tx" ON pending_transactions
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role nonces" ON used_nonces
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function: Atomically reserve balance for a send operation
CREATE OR REPLACE FUNCTION reserve_balance(
    p_user_id UUID,
    p_chain VARCHAR(30),
    p_token VARCHAR(20),
    p_amount DECIMAL(24,6),
    p_fee DECIMAL(24,6) DEFAULT 0
) RETURNS BOOLEAN AS $$
DECLARE
    v_current_available DECIMAL(24,6);
    v_total_needed DECIMAL(24,6);
BEGIN
    v_total_needed := p_amount + p_fee;

    -- Lock the balance row for update
    SELECT available_balance INTO v_current_available
    FROM balances
    WHERE user_id = p_user_id AND chain = p_chain AND token = p_token
    FOR UPDATE;

    IF v_current_available IS NULL OR v_current_available < v_total_needed THEN
        RETURN FALSE;
    END IF;

    -- Reserve the balance (move to pending_out)
    UPDATE balances
    SET
        available_balance = available_balance - v_total_needed,
        pending_out = pending_out + v_total_needed,
        updated_at = NOW()
    WHERE user_id = p_user_id AND chain = p_chain AND token = p_token;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function: Confirm a pending send (remove from pending_out)
CREATE OR REPLACE FUNCTION confirm_send(
    p_user_id UUID,
    p_chain VARCHAR(30),
    p_token VARCHAR(20),
    p_amount DECIMAL(24,6),
    p_fee DECIMAL(24,6) DEFAULT 0
) RETURNS BOOLEAN AS $$
DECLARE
    v_total DECIMAL(24,6);
BEGIN
    v_total := p_amount + p_fee;

    UPDATE balances
    SET
        pending_out = pending_out - v_total,
        updated_at = NOW()
    WHERE user_id = p_user_id AND chain = p_chain AND token = p_token
    AND pending_out >= v_total;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function: Release reserved balance (failed transaction)
CREATE OR REPLACE FUNCTION release_reserved_balance(
    p_user_id UUID,
    p_chain VARCHAR(30),
    p_token VARCHAR(20),
    p_amount DECIMAL(24,6),
    p_fee DECIMAL(24,6) DEFAULT 0
) RETURNS BOOLEAN AS $$
DECLARE
    v_total DECIMAL(24,6);
BEGIN
    v_total := p_amount + p_fee;

    UPDATE balances
    SET
        available_balance = available_balance + v_total,
        pending_out = pending_out - v_total,
        updated_at = NOW()
    WHERE user_id = p_user_id AND chain = p_chain AND token = p_token
    AND pending_out >= v_total;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function: Credit balance (deposit confirmed)
CREATE OR REPLACE FUNCTION credit_balance(
    p_user_id UUID,
    p_chain VARCHAR(30),
    p_token VARCHAR(20),
    p_amount DECIMAL(24,6)
) RETURNS BOOLEAN AS $$
BEGIN
    -- Upsert balance (create if doesn't exist)
    INSERT INTO balances (user_id, chain, token, available_balance, updated_at)
    VALUES (p_user_id, p_chain, p_token, p_amount, NOW())
    ON CONFLICT (user_id, chain, token)
    DO UPDATE SET
        available_balance = balances.available_balance + p_amount,
        updated_at = NOW();

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function: Move balance to/from locked (for yield)
CREATE OR REPLACE FUNCTION lock_balance(
    p_user_id UUID,
    p_chain VARCHAR(30),
    p_token VARCHAR(20),
    p_amount DECIMAL(24,6)
) RETURNS BOOLEAN AS $$
DECLARE
    v_available DECIMAL(24,6);
BEGIN
    SELECT available_balance INTO v_available
    FROM balances
    WHERE user_id = p_user_id AND chain = p_chain AND token = p_token
    FOR UPDATE;

    IF v_available IS NULL OR v_available < p_amount THEN
        RETURN FALSE;
    END IF;

    UPDATE balances
    SET
        available_balance = available_balance - p_amount,
        locked_balance = locked_balance + p_amount,
        updated_at = NOW()
    WHERE user_id = p_user_id AND chain = p_chain AND token = p_token;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function: Unlock balance (withdraw from yield)
CREATE OR REPLACE FUNCTION unlock_balance(
    p_user_id UUID,
    p_chain VARCHAR(30),
    p_token VARCHAR(20),
    p_amount DECIMAL(24,6)
) RETURNS BOOLEAN AS $$
DECLARE
    v_locked DECIMAL(24,6);
BEGIN
    SELECT locked_balance INTO v_locked
    FROM balances
    WHERE user_id = p_user_id AND chain = p_chain AND token = p_token
    FOR UPDATE;

    IF v_locked IS NULL OR v_locked < p_amount THEN
        RETURN FALSE;
    END IF;

    UPDATE balances
    SET
        available_balance = available_balance + p_amount,
        locked_balance = locked_balance - p_amount,
        updated_at = NOW()
    WHERE user_id = p_user_id AND chain = p_chain AND token = p_token;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function: Atomic increment of free tier usage (prevents race conditions)
CREATE OR REPLACE FUNCTION increment_free_tier_usage(p_user_id UUID)
RETURNS VOID AS $$
BEGIN
    INSERT INTO user_settings (user_id, free_tier_messages_used, updated_at)
    VALUES (p_user_id, 1, NOW())
    ON CONFLICT (user_id)
    DO UPDATE SET
        free_tier_messages_used = COALESCE(user_settings.free_tier_messages_used, 0) + 1,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_balances_updated_at
    BEFORE UPDATE ON balances
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ledger_updated_at
    BEFORE UPDATE ON ledger_entries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pending_tx_updated_at
    BEFORE UPDATE ON pending_transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- CLEANUP FUNCTION
-- Run periodically to clean old data
-- ============================================================================
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
    -- Delete nonces older than 30 days
    DELETE FROM used_nonces WHERE used_at < NOW() - INTERVAL '30 days';

    -- Delete confirmed pending_transactions older than 7 days
    DELETE FROM pending_transactions
    WHERE status IN ('confirmed', 'failed', 'dropped')
    AND updated_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- GRANT PERMISSIONS TO SERVICE ROLE
-- ============================================================================
GRANT EXECUTE ON FUNCTION reserve_balance TO service_role;
GRANT EXECUTE ON FUNCTION confirm_send TO service_role;
GRANT EXECUTE ON FUNCTION release_reserved_balance TO service_role;
GRANT EXECUTE ON FUNCTION credit_balance TO service_role;
GRANT EXECUTE ON FUNCTION lock_balance TO service_role;
GRANT EXECUTE ON FUNCTION unlock_balance TO service_role;
GRANT EXECUTE ON FUNCTION increment_free_tier_usage TO service_role;
GRANT EXECUTE ON FUNCTION cleanup_old_data TO service_role;
