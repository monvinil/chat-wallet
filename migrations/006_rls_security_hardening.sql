-- Migration: RLS Security Hardening
-- Run this in Supabase SQL Editor
-- Fixes the service key bypass issues by implementing proper RLS policies

-- ============================================================================
-- USERS TABLE
-- ============================================================================

-- Ensure RLS is enabled
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Users can view their own record
CREATE POLICY IF NOT EXISTS "Users can view own record" ON users
    FOR SELECT USING (auth.uid() = id);

-- Users can update their own record (except sensitive fields)
CREATE POLICY IF NOT EXISTS "Users can update own record" ON users
    FOR UPDATE USING (auth.uid() = id)
    WITH CHECK (
        auth.uid() = id AND
        -- Prevent users from modifying these fields
        (OLD.email = NEW.email) AND
        (OLD.created_at = NEW.created_at)
    );

-- Only service role can insert (for account creation)
CREATE POLICY IF NOT EXISTS "Service role can insert users" ON users
    FOR INSERT WITH CHECK (auth.role() = 'service_role');

-- Service role has full access
CREATE POLICY IF NOT EXISTS "Service role full access users" ON users
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- WALLETS TABLE
-- ============================================================================

ALTER TABLE wallets ENABLE ROW LEVEL SECURITY;

-- Users can view their own wallets
DROP POLICY IF EXISTS "Users can view own wallets" ON wallets;
CREATE POLICY "Users can view own wallets" ON wallets
    FOR SELECT USING (auth.uid() = user_id);

-- Users can insert their own wallets
DROP POLICY IF EXISTS "Users can insert own wallets" ON wallets;
CREATE POLICY "Users can insert own wallets" ON wallets
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can update their own wallets
DROP POLICY IF EXISTS "Users can update own wallets" ON wallets;
CREATE POLICY "Users can update own wallets" ON wallets
    FOR UPDATE USING (auth.uid() = user_id);

-- Users can delete their own wallets
DROP POLICY IF EXISTS "Users can delete own wallets" ON wallets;
CREATE POLICY "Users can delete own wallets" ON wallets
    FOR DELETE USING (auth.uid() = user_id);

-- Service role for admin operations
DROP POLICY IF EXISTS "Service role wallets" ON wallets;
CREATE POLICY "Service role wallets" ON wallets
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- USER_SETTINGS TABLE
-- ============================================================================

ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;

-- Users can view their own settings
DROP POLICY IF EXISTS "Users can view own settings" ON user_settings;
CREATE POLICY "Users can view own settings" ON user_settings
    FOR SELECT USING (auth.uid() = user_id);

-- Users can insert their own settings
DROP POLICY IF EXISTS "Users can insert own settings" ON user_settings;
CREATE POLICY "Users can insert own settings" ON user_settings
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can update their own settings
DROP POLICY IF EXISTS "Users can update own settings" ON user_settings;
CREATE POLICY "Users can update own settings" ON user_settings
    FOR UPDATE USING (auth.uid() = user_id);

-- Service role for admin/background operations
DROP POLICY IF EXISTS "Service role settings" ON user_settings;
CREATE POLICY "Service role settings" ON user_settings
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- TRANSACTIONS TABLE
-- ============================================================================

ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- Users can view their own transactions
DROP POLICY IF EXISTS "Users can view own transactions" ON transactions;
CREATE POLICY "Users can view own transactions" ON transactions
    FOR SELECT USING (auth.uid() = user_id);

-- Only service role can insert transactions (from backend)
DROP POLICY IF EXISTS "Service role insert transactions" ON transactions;
CREATE POLICY "Service role insert transactions" ON transactions
    FOR INSERT WITH CHECK (auth.role() = 'service_role');

-- Only service role can update transactions
DROP POLICY IF EXISTS "Service role update transactions" ON transactions;
CREATE POLICY "Service role update transactions" ON transactions
    FOR UPDATE USING (auth.role() = 'service_role');

-- ============================================================================
-- OAUTH_CONNECTIONS TABLE
-- ============================================================================

-- Check if table exists first
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'oauth_connections') THEN
        ALTER TABLE oauth_connections ENABLE ROW LEVEL SECURITY;

        -- Users can view their own OAuth connections
        DROP POLICY IF EXISTS "Users can view own oauth" ON oauth_connections;
        CREATE POLICY "Users can view own oauth" ON oauth_connections
            FOR SELECT USING (auth.uid() = user_id);

        -- Users can insert their own OAuth connections
        DROP POLICY IF EXISTS "Users can insert own oauth" ON oauth_connections;
        CREATE POLICY "Users can insert own oauth" ON oauth_connections
            FOR INSERT WITH CHECK (auth.uid() = user_id);

        -- Users can update their own OAuth connections
        DROP POLICY IF EXISTS "Users can update own oauth" ON oauth_connections;
        CREATE POLICY "Users can update own oauth" ON oauth_connections
            FOR UPDATE USING (auth.uid() = user_id);

        -- Users can delete their own OAuth connections
        DROP POLICY IF EXISTS "Users can delete own oauth" ON oauth_connections;
        CREATE POLICY "Users can delete own oauth" ON oauth_connections
            FOR DELETE USING (auth.uid() = user_id);

        -- Service role for admin operations
        DROP POLICY IF EXISTS "Service role oauth" ON oauth_connections;
        CREATE POLICY "Service role oauth" ON oauth_connections
            FOR ALL USING (auth.role() = 'service_role');
    END IF;
END $$;

-- ============================================================================
-- SESSIONS TABLE
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'sessions') THEN
        ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

        -- Users can view their own sessions
        DROP POLICY IF EXISTS "Users can view own sessions" ON sessions;
        CREATE POLICY "Users can view own sessions" ON sessions
            FOR SELECT USING (auth.uid() = user_id);

        -- Only service role can manage sessions
        DROP POLICY IF EXISTS "Service role sessions" ON sessions;
        CREATE POLICY "Service role sessions" ON sessions
            FOR ALL USING (auth.role() = 'service_role');
    END IF;
END $$;

-- ============================================================================
-- ADD COLUMNS FOR AUTO-EXECUTION (if not exist)
-- ============================================================================

DO $$
BEGIN
    -- Add auto_execute_scheduled column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_settings'
        AND column_name = 'auto_execute_scheduled'
    ) THEN
        ALTER TABLE user_settings ADD COLUMN auto_execute_scheduled BOOLEAN DEFAULT FALSE;
    END IF;

    -- Add encrypted key storage for scheduled transactions
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_settings'
        AND column_name = 'scheduled_tx_private_key_encrypted'
    ) THEN
        ALTER TABLE user_settings ADD COLUMN scheduled_tx_private_key_encrypted TEXT;
    END IF;
END $$;

-- ============================================================================
-- CREATE HELPER FUNCTION FOR AUTHENTICATED USER ID
-- ============================================================================

-- This function can be used in application code to get the current user
CREATE OR REPLACE FUNCTION get_current_user_id()
RETURNS UUID AS $$
BEGIN
    RETURN auth.uid();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- AUDIT LOG TABLE (for sensitive operations)
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at DESC);

ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Only service role can access audit logs (for security)
CREATE POLICY "Service role audit logs" ON audit_logs
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- FUNCTION TO LOG AUDIT EVENTS
-- ============================================================================

CREATE OR REPLACE FUNCTION log_audit_event(
    p_user_id UUID,
    p_action VARCHAR(100),
    p_resource_type VARCHAR(50) DEFAULT NULL,
    p_resource_id UUID DEFAULT NULL,
    p_details JSONB DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_log_id UUID;
BEGIN
    INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
    VALUES (p_user_id, p_action, p_resource_type, p_resource_id, p_details)
    RETURNING id INTO v_log_id;

    RETURN v_log_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION log_audit_event TO service_role;

-- ============================================================================
-- VERIFICATION QUERIES
-- Run these to verify RLS is working correctly
-- ============================================================================

-- Check all tables have RLS enabled
-- SELECT tablename, rowsecurity
-- FROM pg_tables
-- WHERE schemaname = 'public'
-- AND tablename IN ('users', 'wallets', 'user_settings', 'transactions', 'balances', 'ledger_entries');

-- List all policies
-- SELECT tablename, policyname, cmd, qual
-- FROM pg_policies
-- WHERE schemaname = 'public'
-- ORDER BY tablename, policyname;
