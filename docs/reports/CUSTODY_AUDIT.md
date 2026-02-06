# Custody Audit Report
## Lead Architect — February 6, 2026

---

> **SEVERITY: CRITICAL — Must be resolved before any user-facing launch.**

---

# Executive Summary

USDChat's interactive wallet operations (user-initiated sends, deposits, withdrawals) are **non-custodial** — the private key is decrypted in the user's browser session and never stored server-side in plaintext. This is the correct architecture.

However, two components create **custodial liability**:

1. **`scheduler_executor.py`** — Stores encrypted private keys in the database with a server-side decryption key. The server can access user funds without the user being present.
2. **`transaction_relayer.py`** — The relayer executes USDC transfers from its own address, meaning it must hold user funds.

Both of these would classify USDChat as a **custodian** under US (FinCEN), EU (MiCA), and most other jurisdictions.

**Current risk: LOW** (stealth, no users). **Pre-launch risk: CRITICAL.**

---

# Detailed Findings

## Finding 1: scheduler_executor.py — Server-Side Key Storage

**File:** `scheduler_executor.py`
**Lines:** 127-191
**Severity:** CRITICAL

### How It Works

1. User enables "auto-execute" for scheduled payments in settings
2. User's private key is encrypted with `SCHEDULER_ENCRYPTION_SECRET` (env var) and stored in `user_settings.scheduled_tx_private_key_encrypted` (Supabase database)
3. When a scheduled task is due, the executor:
   - Reads the encrypted key from DB (line 159)
   - Decrypts it using the server-side secret (line 177)
   - Uses the plaintext key to sign and broadcast transactions (lines 186-191)

### Why This Is Custodial

Under FinCEN's 2019 guidance on virtual assets:
> "A person that has independent control over value belonging to another person is a money transmitter."

The server holds `SCHEDULER_ENCRYPTION_SECRET`, the database holds `scheduled_tx_private_key_encrypted`. Together, the server has **independent control** over user funds.

Under EU MiCA (effective 2024):
> "Custody and administration of crypto-assets" requires a license if a service stores cryptographic keys that provide access to another person's crypto-assets.

### Evidence

```python
# scheduler_executor.py:159
encrypted_key = settings.data.get("scheduled_tx_private_key_encrypted")

# scheduler_executor.py:173-178
scheduler_secret = os.getenv("SCHEDULER_ENCRYPTION_SECRET")
private_key = PasswordEncryption.decrypt_with_key(
    encrypted_key, scheduler_secret
)

# scheduler_executor.py:186-191
executor = DirectTransactionExecutor(chain)
result = executor.execute_transfer(
    private_key=private_key,  # Decrypted user key!
    to_address=to_address,
    amount_usdc=float(amount),
    user_id=user_id
)
```

### Recommended Fix

**Option A (Simplest — Recommended for MVP):** Pending Approval Model
- Scheduler marks tasks as "ready" instead of executing them
- User sees pending tasks on next login and batch-approves them
- User's key stays in browser session, never stored server-side
- Trade-off: Tasks don't execute in real-time

**Option B:** Smart Contract Allowance
- User approves a smart contract to spend up to X USDC
- Scheduler calls the contract (no private key needed, only contract interaction)
- Contract enforces spending limits, recipient whitelist
- Trade-off: Requires deploying and auditing a smart contract

**Option C:** Circle Programmable Wallets
- Delegate signing to Circle's MPC infrastructure
- Circle handles custody compliance
- Trade-off: Dependency on Circle; Circle becomes the custodian

**Option D:** Session Key Pattern (ERC-4337)
- User generates a temporary session key with limited permissions
- Session key can only execute pre-approved transaction types
- Key expires after a set period
- Trade-off: Complexity; needs account abstraction infrastructure

---

## Finding 2: transaction_relayer.py — Relayer Holds Funds

**File:** `transaction_relayer.py`
**Lines:** 152-227
**Severity:** HIGH

### How It Works

1. User signs an EIP-712 meta-transaction message (off-chain)
2. Relayer validates the signature
3. Relayer calls `usdc.functions.transfer()` from `self.relayer_address` (line 183)
4. This means the relayer wallet must hold the USDC being transferred

### Why This Is Custodial

If users deposit USDC to the relayer address for it to execute transfers on their behalf, the relayer is holding user funds. This is custody.

### Evidence

```python
# transaction_relayer.py:183
transfer_fn = usdc_contract.functions.transfer(to_address, amount_wei)

# transaction_relayer.py:191-192
tx = transfer_fn.build_transaction({
    'from': self.relayer_address,  # Relayer sends, not user
    ...
})
```

The `transfer()` call moves USDC from the relayer to the recipient. The user's USDC must have been in the relayer wallet.

### Recommended Fix

**Option A (Recommended):** ERC-2771 Forwarder Pattern
- Deploy a Trusted Forwarder contract
- User signs meta-tx, relayer submits to forwarder
- Forwarder extracts user address from signature and calls USDC.transfer on behalf of user
- Relayer only pays gas, never holds USDC

**Option B:** ERC-4337 Account Abstraction
- User deploys a smart account
- Relayer bundles UserOperations and submits to EntryPoint
- Paymaster pays gas
- Industry standard, but higher implementation complexity

**Option C:** Abandon gasless for now
- Use `direct_tx.py` for all transactions (user pays gas)
- On Base/Arbitrum, gas is ~$0.001-0.01 — negligible
- Simplest path, minimal user friction on L2s

---

## Finding 3: wallet_manager.py — Correctly Non-Custodial

**File:** `wallet_manager.py`
**Severity:** SAFE (with caveats)

The wallet manager correctly:
- Generates keys client-side (line 111-121)
- Encrypts with user's password using PBKDF2 (line 33-44)
- Stores encrypted blob in browser session only (line 291-299)
- Requires user's password to decrypt (line 386-429)
- Auto-locks after inactivity (line 457-487)

**Caveat:** The encrypted wallet data blob is stored in `st.session_state`, which is server-side memory in Streamlit. If an attacker gains access to the server while a user has an active session, the encrypted blob and potentially the Fernet key could be extracted. This is inherent to Streamlit's architecture and one of the reasons for migrating to Next.js (where keys stay in browser localStorage, encrypted).

---

## Finding 4: aave_client.py / direct_tx.py — Non-Custodial When Interactive

**Files:** `aave_client.py`, `direct_tx.py`
**Severity:** SAFE (when called from UI)

Both files take `private_key` as a function parameter. When called from the interactive UI flow:
- User enters password → wallet decrypted in session → key passed to function → transaction signed → key discarded

When called from `scheduler_executor.py`: **CUSTODIAL** (see Finding 1).

---

# Risk Matrix

| Scenario | Custodial? | Regulatory Impact | Fix Priority |
|----------|-----------|-------------------|-------------|
| User sends USDC via UI | No | None | N/A |
| User deposits to Aave via UI | No | None | N/A |
| Scheduled payment executes while user offline | YES | MSB/MTL required | P0 |
| Gasless transfer via relayer | YES (if relayer holds funds) | MSB/MTL required | P1 |
| User views balance | No | None | N/A |
| DCA executes automatically | Partially (simulated currently) | When real: same as scheduled | P0 |

---

# Recommended Action Plan

## Phase 1: Before Beta (Q1 2026)
1. Remove `scheduled_tx_private_key_encrypted` from the database schema
2. Implement pending-approval model for scheduled tasks
3. Evaluate whether gasless txs are needed on L2 (Base gas is ~$0.001)
4. If gasless needed, deploy ERC-2771 forwarder or switch to ERC-4337

## Phase 2: Before Public Launch (Q2 2026)
1. Full security audit by external firm
2. Legal opinion on custody classification
3. Document non-custodial architecture for regulators
4. Implement session key pattern for recurring transactions (if needed)

## Phase 3: Scale
1. Offer Circle Programmable Wallets as optional custodial path
2. Maintain self-custody as primary (regulatory advantage)
3. Clear disclosure to users about custody model

---

*Report by: Lead Architect*
*Date: February 6, 2026*
*Status: FINDINGS CONFIRMED — Fixes required before launch*
