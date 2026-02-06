# Security Audit Report - USDChat Wallet

**Auditor:** Claude Security Auditor
**Date:** 2026-02-06
**Scope:** Full security audit of all files handling private keys, encryption, authentication, transactions, and user data
**Risk Context:** Self-custodial crypto wallet - security failures mean users lose money

---

## Executive Summary

USDChat is a self-custodial multi-chain wallet (EVM + Solana) with a Streamlit frontend, FastAPI backend, and Supabase database. The codebase demonstrates security awareness (PBKDF2+Fernet encryption, bcrypt password hashing, RLS policies, spending limits, auto-lock), but several critical and high-severity issues were found that could lead to **account takeover, fund theft, or bypass of financial controls**.

**10 critical/high findings** were identified. **8 have been directly fixed** in this audit.

---

## Findings Summary

| # | Severity | Status | File | Finding |
|---|----------|--------|------|---------|
| 1 | **CRITICAL** | **FIXED** | `api/config.py:36` | Hardcoded JWT secret default allows token forgery |
| 2 | **CRITICAL** | **FIXED** | `scheduler_executor.py:532` | Scheduler HTTP auth bypass when secret is empty |
| 3 | **CRITICAL** | **FIXED** | `scheduler_executor.py:532` | Non-constant-time auth comparison (timing attack) |
| 4 | **HIGH** | **FIXED** | `api/routes/transactions.py:450` | IDOR: Any user can query any transaction by hash |
| 5 | **HIGH** | **FIXED** | `wallet_manager.py:305` | lock_wallet doesn't clear all SENSITIVE_SESSION_KEYS |
| 6 | **HIGH** | **FIXED** | `utils/encryption.py` | Missing `decrypt_with_key` method breaks scheduled execution |
| 7 | **HIGH** | **FIXED** | `meta_tx.py:131`, `supabase_client.py:65` | print() leaks error details to stdout |
| 8 | **HIGH** | **FIXED** | `transaction_relayer.py:75,98,249` | Bare except clauses mask errors silently |
| 9 | **HIGH** | **FIXED** | `.env.example` | Missing SETTINGS_ENCRYPTION_KEY, RELAYER_PRIVATE_KEY |
| 10 | **HIGH** | **FIXED** | `scheduler_executor.py:182` | Error message leaks decryption failure details |
| 11 | **HIGH** | OPEN | `session_manager.py:72` | Session cookie lacks HttpOnly flag (XSS risk) |
| 12 | **HIGH** | OPEN | `spending_limits.py:21-57` | Daily limits tracked in session state only (bypassable) |
| 13 | **HIGH** | OPEN | `utils/encryption.py:169-179` | SettingsEncryption silently uses random key when env var missing |
| 14 | **MEDIUM** | OPEN | `api/config.py:29` | CORS wildcard `https://*.streamlit.app` too permissive |
| 15 | **MEDIUM** | OPEN | `direct_tx.py:258` | Float precision loss in financial calculations |
| 16 | **MEDIUM** | OPEN | `meta_tx.py:46` | Default nonce=0, weak replay protection |
| 17 | **MEDIUM** | OPEN | Wallet creation | No password complexity requirements |
| 18 | **MEDIUM** | OPEN | `utils/encryption.py:28` | PBKDF2 iterations (100k) below OWASP recommendation (600k) |
| 19 | **LOW** | OPEN | `api/routes/transactions.py:47` | In-memory preview store unbounded (DoS) |
| 20 | **LOW** | OPEN | `transaction_relayer.py:51-53` | Temporary relayer account created if env var missing |

---

## Detailed Findings

### FINDING 1: Hardcoded JWT Secret Default [CRITICAL] [FIXED]

**File:** `api/config.py:36`
**Was:**
```python
jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "CHANGE-THIS-IN-PRODUCTION-use-secrets-token-hex-32")
```
**Risk:** If JWT_SECRET_KEY env var is not set, the default string is used. Anyone who knows this default (it's in the source code) can forge valid JWT tokens and take over any account.

**Fix applied:** Removed insecure default. If env var is missing, generates an ephemeral random key and emits a RuntimeWarning. All tokens are invalidated on restart, making it obvious the env var is needed.

---

### FINDING 2: Scheduler HTTP Auth Bypass [CRITICAL] [FIXED]

**File:** `scheduler_executor.py:532`
**Was:**
```python
if executor_secret and auth_header != f"Bearer {executor_secret}":
```
**Risk:** When `TASK_EXECUTOR_SECRET` is empty/unset, the `if executor_secret` check is False, so the entire auth block is skipped. Anyone can POST to `/execute` and trigger scheduled task execution (including transfers).

**Fix applied:** Server now refuses to start in HTTP mode if TASK_EXECUTOR_SECRET is not set.

---

### FINDING 3: Timing Attack on Scheduler Auth [CRITICAL] [FIXED]

**File:** `scheduler_executor.py:532`
**Was:** `auth_header != f"Bearer {executor_secret}"` (standard string comparison)
**Risk:** Standard `!=` comparison leaks token length and character values through timing side-channels.

**Fix applied:** Replaced with `hmac.compare_digest()` for constant-time comparison.

---

### FINDING 4: IDOR on Transaction Status [HIGH] [FIXED]

**File:** `api/routes/transactions.py:450`
**Was:**
```python
result = supabase.table("transactions").select("*").eq("tx_hash", tx_hash).single().execute()
```
**Risk:** Any authenticated user can query any transaction by hash, leaking other users' transaction details (amounts, addresses, timestamps).

**Fix applied:** Added `.eq("user_id", user_id)` filter to restrict results to the authenticated user's transactions only.

---

### FINDING 5: Incomplete Sensitive Data Cleanup on Lock [HIGH] [FIXED]

**File:** `wallet_manager.py:305`
**Was:** `lock_wallet()` hardcoded `["wallet_key", "wallet_data", "_pending_seed_phrase"]`, missing `_export_key_step` which is defined in `SENSITIVE_SESSION_KEYS` at the module level.
**Risk:** The `_export_key_step` state could persist after wallet lock, potentially allowing unauthorized key export flow continuation.

**Fix applied:** Changed `lock_wallet()` to iterate over `SENSITIVE_SESSION_KEYS` constant instead of a hardcoded list.

---

### FINDING 6: Missing `decrypt_with_key` Method [HIGH] [FIXED]

**File:** `scheduler_executor.py:177` calls `PasswordEncryption.decrypt_with_key()` which didn't exist in `utils/encryption.py`
**Risk:** All scheduled transaction auto-execution was broken. This is a functional bug with security implications - scheduled transfers would always fail, and the error message could leak decryption details.

**Fix applied:** Added both `encrypt_with_key()` and `decrypt_with_key()` methods to `PasswordEncryption` class using PBKDF2 derivation from the scheduler secret with a per-encryption random salt stored alongside the ciphertext.

---

### FINDING 7: Information Leakage via print() [HIGH] [FIXED]

**Files:** `meta_tx.py:131`, `supabase_client.py:65`
**Was:** `print(f"Signature verification failed: {e}")` and `print(f"Supabase connection failed: {e}")`
**Risk:** Error details written to stdout can be captured in container logs, CI/CD output, or console. Exception messages may contain sensitive context (connection strings, key material, internal state).

**Fix applied:** Replaced with `logger.warning()` / `logger.error()` using `{type(e).__name__}` to log only the error class, not the full message.

---

### FINDING 8: Bare Except Clauses [HIGH] [FIXED]

**File:** `transaction_relayer.py:75,98,249`
**Was:** `except:` (catches SystemExit, KeyboardInterrupt, etc.)
**Risk:** Swallows ALL exceptions including critical ones like MemoryError, SystemExit. Can mask real problems and make debugging impossible.

**Fix applied:** Changed all bare `except:` to `except Exception:`.

---

### FINDING 9: Missing Critical Env Vars in .env.example [HIGH] [FIXED]

**File:** `.env.example`
**Risk:** `SETTINGS_ENCRYPTION_KEY` and `RELAYER_PRIVATE_KEY` were not documented in `.env.example`, increasing the likelihood of production deployments without these critical configuration values.

**Fix applied:** Added `SETTINGS_ENCRYPTION_KEY` and `RELAYER_PRIVATE_KEY` sections with generation instructions.

---

### FINDING 10: Error Message Leaks Decryption Details [HIGH] [FIXED]

**File:** `scheduler_executor.py:182`
**Was:** `return {"success": False, "error": f"Failed to decrypt key: {e}"}`
**Risk:** The exception `e` could contain information about the encryption scheme, key format, or internal state. This error is returned in JSON and could be exposed via API or logged.

**Fix applied:** Changed to generic error message "Failed to decrypt execution key" and log the error type server-side only.

---

### FINDING 11: Session Cookie Lacks HttpOnly Flag [HIGH] [OPEN]

**File:** `session_manager.py:72`
**Current:**
```python
document.cookie = "{name}={value};" + expires + ";path=/;SameSite=Lax;Secure";
```
**Risk:** Without HttpOnly, the session token is accessible to JavaScript. Any XSS vulnerability in the app or third-party Streamlit components could steal session tokens.

**Remediation:** This is an architectural limitation of Streamlit (cookies must be set client-side via JS). **Recommended:** Deploy behind a reverse proxy (nginx/Cloudflare) that sets the session cookie server-side with HttpOnly flag. Alternatively, migrate to a framework that supports server-side cookie management.

---

### FINDING 12: Spending Limits Bypass via Session State [HIGH] [OPEN]

**File:** `spending_limits.py:21-57`
**Risk:** Daily spending is tracked in `st.session_state` which is per-browser-tab and resets on page refresh. A user (or attacker with session access) can bypass daily limits by:
1. Opening a new browser tab
2. Refreshing the page
3. Using the API directly (no limit enforcement on API endpoints)

**Remediation:** Move daily spend tracking to the database (Supabase). Use the `ledger_entries` table to compute actual daily spend from confirmed transactions. Enforce limits on both Streamlit and API paths.

---

### FINDING 13: SettingsEncryption Silent Fallback [HIGH] [OPEN]

**File:** `utils/encryption.py:169-179`
**Risk:** When `SETTINGS_ENCRYPTION_KEY` is not set, a random key is generated per process. This means:
1. All previously encrypted settings become undecryptable after restart
2. Settings encrypted in one process can't be decrypted in another
3. No warning is logged server-side (only shown in Streamlit UI)

**Remediation:** Log a CRITICAL-level warning and refuse to encrypt/decrypt if the key is not set in production (check for a `PRODUCTION` or `ENVIRONMENT` env var).

---

### FINDING 14: Overly Permissive CORS [MEDIUM] [OPEN]

**File:** `api/config.py:29`
**Current:** `"https://*.streamlit.app"` in CORS origins
**Risk:** Any Streamlit Cloud app can make credentialed cross-origin requests to the API. An attacker could deploy a malicious Streamlit app that makes API calls on behalf of authenticated users.

**Remediation:** Replace with the specific Streamlit app URL(s) for this project. Use environment variable for CORS origins so they can be configured per deployment.

---

### FINDING 15: Float Precision in Financial Calculations [MEDIUM] [OPEN]

**File:** `direct_tx.py:258`
**Current:** `int(amount_usdc * 1e6)` - float multiplication
**Risk:** IEEE 754 floating-point arithmetic can lose precision. Example: `0.1 * 1e6 = 99999.99999999999` which truncates to `99999` instead of `100000`. This could result in users sending slightly incorrect amounts.

**Remediation:** Use `Decimal` throughout: `int(Decimal(str(amount_usdc)) * Decimal('1000000'))`

---

### FINDING 16: Weak Replay Protection in Meta-Transactions [MEDIUM] [OPEN]

**File:** `meta_tx.py:46`
**Risk:** Default nonce is 0 and is passed as a parameter. The relayer must track nonces server-side to prevent replay. If the relayer's nonce tracking fails (e.g., database outage), meta-transactions could be replayed.

**Remediation:** Use on-chain nonce tracking via the smart contract, or at minimum ensure the `BalanceService.check_and_record_nonce()` is always called before relayer execution.

---

### FINDING 17: No Password Complexity Requirements [MEDIUM] [OPEN]

**File:** Wallet creation flow (wallet_manager.py, api/routes/wallet.py)
**Risk:** No minimum password length or complexity checks. Users can set single-character passwords. Weak passwords make wallet encryption trivially brute-forceable.

**Remediation:** Add minimum password requirements: 8+ characters minimum, ideally with zxcvbn-style strength estimation. Enforce in both Streamlit and API wallet creation paths.

---

### FINDING 18: PBKDF2 Iteration Count Below OWASP Recommendation [MEDIUM] [OPEN]

**File:** `utils/encryption.py:28`
**Current:** `PASSWORD_HASH_ITERATIONS = 100000`
**Risk:** OWASP recommends 600,000 iterations for PBKDF2-SHA256 as of 2023. 100,000 iterations provides roughly 6x less resistance to brute-force attacks. For a wallet where the encrypted data contains private keys worth real money, this matters.

**Remediation:** Increase to 600,000 iterations. Note: This is a breaking change for existing encrypted wallets. Implement a migration strategy: detect old iteration count, re-encrypt on successful unlock.

---

### FINDING 19: Unbounded In-Memory Preview Store [LOW] [OPEN]

**File:** `api/routes/transactions.py:47`
**Risk:** `_preview_store` is an unbounded dictionary. An attacker could create millions of previews to exhaust server memory. Cleanup only runs when new previews are created.

**Remediation:** Add a maximum size limit (e.g., 10,000 entries). Use a TTL cache library or Redis. Run cleanup on a timer, not just on new preview creation.

---

### FINDING 20: Temporary Relayer Account in Production [LOW] [OPEN]

**File:** `transaction_relayer.py:51-53`
**Risk:** When `RELAYER_PRIVATE_KEY` is not set, a temporary account is created. This account has no funds, so all relayer transactions will fail. Not a direct theft vector, but could cause user confusion and operational issues.

**Remediation:** Log a CRITICAL warning when using temporary relayer. Refuse to process transactions if relayer balance is below a minimum threshold.

---

## Positive Security Observations

The following security measures are well-implemented:

1. **Password hashing:** bcrypt with 12 rounds + legacy SHA-256 support with constant-time comparison (hmac.compare_digest)
2. **Wallet encryption:** PBKDF2-SHA256 + Fernet (AES-128-CBC) with random salts
3. **Session token generation:** `secrets.token_urlsafe(32)` - cryptographically secure
4. **Auto-lock:** 15-minute inactivity timeout with configurable duration
5. **Cookie sanitization:** Regex validation on cookie names/values prevents XSS injection
6. **RLS policies:** Database-level row-level security (migration 006)
7. **Balance ledger:** Atomic operations with idempotency keys and double-spend protection
8. **Deprecated wallet key cookie:** `save_wallet_key()` intentionally does nothing
9. **Rate limiting:** slowapi on sensitive endpoints (login: 10/min, create: 5/min, send: 10/min)
10. **Error handling:** Generic error messages to users, detailed logging server-side (mostly)
11. **Nonce tracking:** `check_and_record_nonce()` for replay protection
12. **Spending limits:** Per-transaction approval thresholds (though session-state tracking is bypassable)

---

## Recommendations (Priority Order)

### Immediate (Before Production)
1. Set all required environment variables (JWT_SECRET_KEY, SETTINGS_ENCRYPTION_KEY, TASK_EXECUTOR_SECRET, SCHEDULER_ENCRYPTION_SECRET)
2. Deploy behind a reverse proxy with HttpOnly cookie support
3. Move spending limit tracking from session state to database
4. Add password complexity requirements (minimum 8 characters)
5. Restrict CORS origins to specific deployment URLs

### Short-term (Next Sprint)
6. Increase PBKDF2 iterations to 600,000 with migration strategy
7. Use Decimal throughout for all financial calculations
8. Add bounds to in-memory preview store
9. Implement server-side nonce tracking for meta-transactions
10. Add CRITICAL log warnings for SettingsEncryption fallback key

### Medium-term
11. Implement rate limiting on the Streamlit frontend (session-based)
12. Add CSP (Content Security Policy) headers
13. Implement token blacklisting for JWT revocation
14. Consider switching to Circle Programmable Wallets for scheduled execution
15. Add penetration testing with tools like OWASP ZAP

---

## Files Audited

| File | Lines | Verdict |
|------|-------|---------|
| `wallet_manager.py` | 488 | Fixed: lock_wallet cleanup |
| `utils/encryption.py` | 222 | Fixed: Added decrypt_with_key; NOTE: iteration count low |
| `direct_tx.py` | 338 | Float precision issue (open) |
| `meta_tx.py` | 156 | Fixed: print→logger; Replay protection weak (open) |
| `transaction_relayer.py` | 251 | Fixed: bare excepts |
| `api/middleware/auth.py` | 238 | Clean - well structured |
| `session_manager.py` | 427 | HttpOnly limitation documented |
| `supabase_client.py` | 450 | Fixed: print→logger |
| `scheduler_executor.py` | 633 | Fixed: auth bypass, timing attack, error leakage |
| `config.py` | 287 | Clean |
| `api/config.py` | 68→78 | Fixed: JWT secret default |
| `settings_manager.py` | 534 | Clean |
| `spending_limits.py` | 165 | Session-state bypass (open) |
| `balance_service.py` | 695 | Clean - well designed |
| `api/routes/transactions.py` | 480 | Fixed: IDOR |
| `api/routes/wallet.py` | 526 | Clean |
| `api/routes/scheduler_routes.py` | 383 | Clean |
| `api/main.py` | 136 | Clean |
| `.env.example` | 60→70 | Fixed: added missing vars |
