# Security TODOs - Architectural Changes Required

## 1. Supabase RLS Bypass (Service Key Usage)

**Current Issue:**
Many operations use `get_supabase_client(use_service_key=True)` which bypasses Row Level Security (RLS) policies. This is a security risk because:
- Any bug in the application could allow unauthorized data access
- RLS is the last line of defense for data protection

**Affected Files:**
- `free_tier.py` - usage tracking
- `session_manager.py` - session management
- `settings_manager.py` - user settings
- `supabase_client.py` - transaction recording

**Recommended Fix:**
1. Create proper RLS policies that allow users to access only their own data
2. Use the anon key with RLS policies instead of service key
3. Only use service key for admin operations (if needed at all)

**Example RLS Policy:**
```sql
-- Allow users to read/write only their own settings
CREATE POLICY "Users can access own settings"
ON user_settings
FOR ALL
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);
```

## 2. Internal Balance Ledger

**Current Issue:**
`transaction_relayer.py:get_internal_balance()` returns blockchain balance instead of an internal ledger balance. This is incorrect because:
- User's internal balance should track deposits minus withdrawals
- Blockchain balance doesn't reflect pending or in-flight transactions
- Could allow double-spending in race conditions

**Recommended Fix:**
1. Create a `balances` table in Supabase:
```sql
CREATE TABLE balances (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    usdc_balance DECIMAL(18,6) DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

2. Create an `internal_transactions` table:
```sql
CREATE TABLE internal_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    type VARCHAR(20), -- 'deposit', 'withdrawal', 'transfer'
    amount DECIMAL(18,6),
    status VARCHAR(20), -- 'pending', 'confirmed', 'failed'
    created_at TIMESTAMP DEFAULT NOW()
);
```

3. Update `get_internal_balance()` to query the database instead of blockchain

## 3. Atomic Free Tier Increment (Enhancement)

**Current Status:** Partially fixed with rate limiting

**For Full Fix:**
Add this Supabase RPC function:
```sql
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
```

## 4. Nonce Persistence Table (Required for Replay Protection)

**Status:** Code updated to use database, table creation required

**Create this table in Supabase:**
```sql
CREATE TABLE used_nonces (
    wallet_address VARCHAR(42) NOT NULL,
    nonce BIGINT NOT NULL,
    used_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (wallet_address, nonce)
);

-- Index for efficient lookups
CREATE INDEX idx_used_nonces_wallet ON used_nonces(wallet_address);

-- Optional: Clean up old nonces (older than 30 days)
-- Run periodically via cron job or Supabase Edge Function
-- DELETE FROM used_nonces WHERE used_at < NOW() - INTERVAL '30 days';
```

## Priority

1. **High:** Internal Balance Ledger - Critical for financial integrity
2. **High:** Nonce Persistence Table - Required for replay protection
3. **Medium:** Supabase RLS - Important for defense in depth
4. **Low:** Atomic Increment - Rate limiting provides adequate protection
