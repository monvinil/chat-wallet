# Workstream: Security Auditor

> **Owner**: Security Auditor session
> **Status**: Awaiting session start
> **Last updated**: 2026-02-06

---

## Mandate

You are the lead security auditor. You own:
- Full security audit of the codebase (every file that handles keys, auth, transactions)
- Threat modeling (attack vectors specific to a crypto wallet)
- Vulnerability classification and remediation priorities
- Security architecture review
- Supply chain security (dependencies, build pipeline)
- Cryptographic implementation review

This is a **self-custodial crypto wallet**. Security failures mean **users lose money**. Your audit must be thorough and paranoid.

You may **read** any file. For code fixes, either implement them directly or document them precisely for the architect. Commit security fixes with prefix `[security]`.

---

## Context to Read First

1. `docs/COMMAND_CENTER.md` - Project overview
2. `docs/SECURITY_TODO.md` - Known security issues (4 flagged)
3. `docs/EXECUTIVE_REVIEW_2026-01.md` - CTO review flagged cookie key storage (since fixed)
4. Key files to audit:
   - `wallet_manager.py` - Key generation, storage, encryption
   - `utils/encryption.py` - Encryption utilities
   - `direct_tx.py` - Transaction signing and sending
   - `meta_tx.py` - Meta-transaction (gasless) implementation
   - `transaction_relayer.py` - Transaction relay with balance checks
   - `api/middleware/auth.py` - JWT authentication
   - `session_manager.py` - Session state management
   - `supabase_client.py` - Database access (RLS bypass concerns)
   - `scheduler_executor.py` - Background worker (handles encrypted keys)
   - `config.py` - Network configs, RPC endpoints
   - `rate_limiter.py` - Rate limiting implementation
   - `spending_limits.py` - Transaction limits

## Known Issues (from SECURITY_TODO.md)
1. **Supabase RLS bypass** - Service key used where anon key should suffice
2. **Internal balance returns blockchain balance** - Race condition / double-spend risk
3. **Atomic free tier increment** - Partially fixed with rate limiting
4. **Nonce persistence table** - Needed for replay protection

---

## Sprint 0 Tasks

### 1. Cryptographic Audit
- [ ] Review key derivation (BIP39/44 implementation)
- [ ] Review encryption at rest (PBKDF2 parameters, Fernet usage)
- [ ] Review key handling in memory (when are keys in memory? how long? wiped properly?)
- [ ] Review transaction signing flow (private key exposure surface)
- [ ] Check for hardcoded keys, seeds, or secrets in any file
- [ ] Review randomness sources (are they cryptographically secure?)

### 2. Authentication & Authorization Audit
- [ ] JWT implementation review (algorithm, expiry, refresh, revocation)
- [ ] Session management review (what's stored, where, how long)
- [ ] API endpoint authorization (can users access other users' data?)
- [ ] Rate limiting effectiveness (can it be bypassed?)
- [ ] CORS configuration review

### 3. Transaction Security Audit
- [ ] Transaction signing flow (can a malicious actor redirect funds?)
- [ ] Balance checking before send (race conditions?)
- [ ] Meta-transaction replay protection (nonce handling)
- [ ] Gas estimation manipulation (can user be tricked into overpaying?)
- [ ] Address validation (are all addresses validated before use?)

### 4. Data Security Audit
- [ ] Supabase RLS policy review (which tables lack RLS?)
- [ ] Service key usage audit (every instance of `use_service_key=True`)
- [ ] PII handling (what personal data is stored, where, encrypted?)
- [ ] Logging audit (are private keys, seeds, or passwords ever logged?)
- [ ] Environment variable handling (`.env` security)

### 5. Supply Chain & Infrastructure
- [ ] Dependency audit (`requirements.txt`, `package.json` - known vulnerabilities)
- [ ] Docker security (running as root? privileged containers?)
- [ ] API endpoint exposure (any debug endpoints in production?)
- [ ] Error message information leakage
- [ ] Input validation across all API endpoints

### 6. Threat Model
- [ ] Enumerate attack vectors specific to this product:
  - Wallet key theft
  - Transaction manipulation
  - Session hijacking
  - RLS bypass for data access
  - Scheduler abuse (unauthorized automated transactions)
  - AI prompt injection (tricking AI into sending funds)
  - Front-running / MEV exposure
  - Social engineering via AI interface
- [ ] Classify by severity and likelihood
- [ ] Propose mitigations for each

---

## Findings

_Write every finding here with severity, location (file:line), and remediation._

### Critical (P0)
_Findings that could lead to loss of funds._

### High (P1)
_Findings that could lead to unauthorized access or data exposure._

### Medium (P2)
_Findings that represent defense-in-depth gaps._

### Low (P3)
_Best practice recommendations._

---

## Remediation Plan

_Ordered list of fixes with effort estimates._

---

## Urgent Flags

_Flag anything that should stop a production launch._

---
