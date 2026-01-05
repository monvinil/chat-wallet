-- Migration: Add password_hash column to users table
-- Run this in your Supabase SQL Editor

-- Add password_hash column if it doesn't exist
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT;

-- Add primary_wallet_address column if it doesn't exist
ALTER TABLE users ADD COLUMN IF NOT EXISTS primary_wallet_address TEXT;

-- Add wallet_address to wallets if using different column name
-- (the table uses 'address' but code might expect 'wallet_address')

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Comment for documentation
COMMENT ON COLUMN users.password_hash IS 'PBKDF2-SHA256 hashed password for login verification';
COMMENT ON COLUMN users.primary_wallet_address IS 'Primary wallet address associated with user';
