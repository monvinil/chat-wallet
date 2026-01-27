-- Migration: Add sessions table for persistent login
-- Run this in your Supabase SQL Editor

-- Sessions table for persistent login across page refreshes
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token TEXT NOT NULL UNIQUE,
    email TEXT,
    wallet_address TEXT,
    solana_address TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_user_session UNIQUE (user_id)
);

-- Add solana_address column if it doesn't exist (for existing tables)
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS solana_address TEXT;

-- Index for fast session token lookup
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);

-- Index for cleanup of expired sessions
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);

-- Comments
COMMENT ON TABLE sessions IS 'Persistent user sessions for cookie-based authentication';
COMMENT ON COLUMN sessions.session_token IS 'Secure random token stored in browser cookie';
COMMENT ON COLUMN sessions.expires_at IS 'Session expiration timestamp (default 30 days)';

-- Optional: Auto-cleanup expired sessions (run periodically)
-- DELETE FROM sessions WHERE expires_at < NOW();
