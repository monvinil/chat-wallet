-- Migration: Add encrypted wallet backup for account recovery
-- Run this after the initial schema

-- Add encrypted wallet storage to wallets table
ALTER TABLE wallets
ADD COLUMN IF NOT EXISTS wallet_data_encrypted TEXT,
ADD COLUMN IF NOT EXISTS backup_method TEXT DEFAULT 'password';  -- 'password', 'recovery_phrase', etc.

-- Update comment
COMMENT ON COLUMN wallets.wallet_data_encrypted IS 'Encrypted private key for wallet recovery (AES-256)';
COMMENT ON COLUMN wallets.backup_method IS 'Method used to encrypt wallet (password, recovery phrase, etc.)';

-- Add wallet_address column to users for primary wallet
ALTER TABLE users
ADD COLUMN IF NOT EXISTS primary_wallet_address TEXT;

COMMENT ON COLUMN users.primary_wallet_address IS 'User''s primary wallet address for quick lookup';
