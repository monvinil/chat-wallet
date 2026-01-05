-- Migration: Add encrypted wallet backup for cloud recovery
-- Run this in your Supabase SQL Editor after the initial schema

-- Add encrypted wallet storage to wallets table
ALTER TABLE wallets
ADD COLUMN IF NOT EXISTS wallet_data_encrypted TEXT,
ADD COLUMN IF NOT EXISTS encryption_salt TEXT,
ADD COLUMN IF NOT EXISTS backup_method TEXT DEFAULT 'password';  -- 'password', 'recovery_phrase', etc.

-- Create index for faster user wallet lookups
CREATE INDEX IF NOT EXISTS idx_wallets_user_id ON wallets(user_id);

-- Update comments
COMMENT ON COLUMN wallets.wallet_data_encrypted IS 'Fernet-encrypted wallet data (private key, mnemonic) for cloud backup';
COMMENT ON COLUMN wallets.encryption_salt IS 'Salt used for password-based key derivation (hex encoded)';
COMMENT ON COLUMN wallets.backup_method IS 'Method used to encrypt wallet (password, recovery phrase, etc.)';

-- Add wallet_address column to users for primary wallet
ALTER TABLE users
ADD COLUMN IF NOT EXISTS primary_wallet_address TEXT;

COMMENT ON COLUMN users.primary_wallet_address IS 'User''s primary wallet address for quick lookup';
