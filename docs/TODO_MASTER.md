# USDChat Master TODO
## February 2026 — Aligned with Strategic Direction

---

> **IMPORTANT:** This TODO is subordinate to STRATEGIC_DIRECTION.md
> All priorities flow from the strategic pillars defined there.
> See ROADMAP_2026.md for detailed implementation plans.
> See MANUAL_ACTIONS.md for tasks requiring human intervention.

---

# Current Focus: Phase 1 — API Integration & x402

**Status:** IN PROGRESS
**Blocks:** Agent marketplace, mobile app, x402 micropayments

---

# P0 — CRITICAL (Completed ✅)

## Security Fixes — DONE

### 1. Remove Cookie-Stored Wallet Key
**Status:** ✅ COMPLETE
**Files:** `session_manager.py`, `wallet_manager.py`

- [x] Remove `chat_wallet_key` from cookies (was already deprecated)
- [x] Implement memory-only key storage
- [x] Add password re-entry on unlock
- [x] Verified key not stored in cookies

### 2. Implement Auto-Lock
**Status:** ✅ COMPLETE
**Files:** `wallet_manager.py`, `rate_limiter.py`

- [x] Add `last_activity_timestamp` via `_last_wallet_activity`
- [x] Create `should_auto_lock()` and `check_auto_lock()` (15 min default)
- [x] Clear sensitive data on timeout
- [x] User settings support for custom timeout

### 3. Session State Audit
**Status:** ✅ COMPLETE
**Files:** `wallet_manager.py`, `session_manager.py`

- [x] Audit all session keys
- [x] Document sensitive keys in `SENSITIVE_SESSION_KEYS`
- [x] Fixed `wallet_data` leak in logout/lock flows
- [x] `lock_wallet()` now clears all sensitive keys

---

## Manual Actions Required (Parallel Track)

**Owner:** Founder (cannot be automated)
**Details:** See MANUAL_ACTIONS.md

- [ ] Circle Developer Account setup
- [ ] Circle API credentials
- [ ] Bitrefill API credentials
- [ ] Alchemy/Infura RPC keys

---

# P1 — HIGH (Current Sprint)

## API Foundation — DONE ✅

### 4. FastAPI Setup
**Status:** ✅ COMPLETE
**Files:** `api/` directory

- [x] Create directory structure (`api/`, `api/routes/`, `api/schemas/`, `api/middleware/`)
- [x] Set up FastAPI app (`api/main.py`)
- [x] Configure CORS
- [x] Add JWT auth middleware (`api/middleware/auth.py`)
- [x] Add rate limiting (slowapi)

### 5. Wallet API Endpoints
**Status:** ✅ COMPLETE
**Files:** `api/routes/wallet.py`

- [x] GET /balance (auth required)
- [x] GET /address/{chain}
- [x] POST /create
- [x] POST /login
- [x] POST /import
- [x] POST /refresh (token refresh)

### 6. Transaction API Endpoints
**Status:** ✅ COMPLETE
**Files:** `api/routes/transactions.py`

- [x] POST /preview
- [x] POST /send
- [x] GET /status/{hash}
- [x] GET /history
- [x] POST /bridge/preview (CCTP)

### 7. RLS Policies
**Status:** [ ] Not Started
**Files:** Supabase dashboard
**Details:** See ROADMAP_2026.md Section 0.4

- [ ] Create policies for all tables
- [ ] Remove unnecessary service key usage
- [ ] Test cross-user access blocked

## Streamlit → API Integration

### 8. Migrate Streamlit to API Client
**Status:** [ ] Not Started
**Files:** `app.py`, `components/*.py`

- [ ] Create API client wrapper
- [ ] Replace direct wallet_manager calls with API
- [ ] Replace direct chain_utils calls with API
- [ ] Test full flow through API layer

---

# P2 — MEDIUM (Week 3-4)

## x402 & Payments

### 8. x402 Protocol Implementation
**Status:** [ ] Not Started
**Details:** See ROADMAP_2026.md Section 2.1
**Dependency:** Circle API credentials

- [ ] Study x402 spec
- [ ] Implement payment request generation
- [ ] Implement payment verification
- [ ] Create HTTP 402 handler

### 9. Payment Links
**Status:** [ ] Not Started
**Details:** See ROADMAP_2026.md Section 2.4

- [ ] Create shareable links
- [ ] Generate QR codes
- [ ] Track usage
- [ ] Webhooks on payment

### 10. Revenue Split System
**Status:** [ ] Not Started
**Details:** See ROADMAP_2026.md Section 2.5

- [ ] Define split ratios (70/20/10)
- [ ] Implement auto-split
- [ ] Track all revenue streams

---

# P3 — COMPLETED (Agent Protocol)

## Agent Protocol — DONE ✅

### 11. Agent Registry Database
**Status:** ✅ COMPLETE
**Files:** `migrations/007_agent_registry.sql`

- [x] Create `agents` table (with slug, pricing, capabilities, stats)
- [x] Create `agent_earnings` table (with auto-split tracking)
- [x] Create `agent_subscriptions` table
- [x] Create `agent_requests` table (usage logging)
- [x] Create `agent_reviews` table
- [x] Create `agent_capabilities` table (built-in caps)
- [x] Create `user_agent_permissions` table
- [x] Add RLS policies for all tables
- [x] Add triggers for rating/revenue updates

### 12. Agent SDK
**Status:** ✅ COMPLETE
**Files:** `sdk/usdchat_agent/`

- [x] Define `Agent` base class
- [x] Capability declaration system (`@capability` decorator)
- [x] Payment integration helpers (`@x402_payment` decorator)
- [x] Type system (AgentContext, UserInfo, PaymentInfo)
- [x] Exception classes (PaymentRequiredError, CapabilityDeniedError)
- [x] Example agents (crypto_news_agent.py, trading_bot_agent.py)
- [x] Package setup (setup.py, README.md)

### 13. Agent API Endpoints
**Status:** ✅ COMPLETE
**Files:** `api/routes/agents.py`, `api/schemas/agent.py`

- [x] CRUD for agents (create, read, update, archive)
- [x] Publish endpoint (draft → pending_review → active)
- [x] Message endpoint with x402 payment handling
- [x] Subscription endpoints
- [x] Review endpoints
- [x] Creator dashboard (my/agents, my/earnings)
- [x] Discovery (list, featured, categories, search)

---

# Backlog (Deprioritized)

These items from the old TODO are now lower priority:

| Item | Old Priority | New Status | Reason |
|------|--------------|------------|--------|
| Pulse Deck improvements | P0 | DONE | Completed in previous session |
| Wire yield UI to Aave | P0 | P2 | API layer first |
| Deploy scheduler | P0 | P2 | API layer first |
| Real Bitrefill | P0 | P1 | Needs API key (manual action) |
| Mobile responsive | P1 | P3 | API/PWA first |
| Multi-step agent | P1 | P3 | Agent protocol first |
| Analytics events | P1 | P2 | After API |

---

# Completed (Recent)

## February 2026 — Agent Protocol Sprint
- [x] Agent: Database schema with 8 tables (migrations/007_agent_registry.sql)
- [x] Agent: SDK package (sdk/usdchat_agent/)
- [x] Agent: Base Agent class with config validation
- [x] Agent: @capability decorator for permissions
- [x] Agent: @x402_payment decorator for micropayments
- [x] Agent: Type system (AgentContext, PaymentInfo, etc.)
- [x] Agent: Exception classes (PaymentRequiredError)
- [x] Agent: Example agents (crypto_news, trading_bot)
- [x] API: Full agent CRUD endpoints
- [x] API: Agent discovery (list, featured, search, categories)
- [x] API: Agent subscriptions and reviews
- [x] API: Creator dashboard (my/agents, my/earnings)
- [x] Docs: CONTEXT_FOR_AI.md updated with agent info

## February 2026 — Security & API Sprint
- [x] Security: Cookie wallet key deprecated (memory-only)
- [x] Security: Auto-lock on idle (15 min default, configurable)
- [x] Security: Session state audit, fixed wallet_data leak
- [x] Security: SENSITIVE_SESSION_KEYS documented
- [x] API: FastAPI foundation with JWT auth
- [x] API: Wallet endpoints (create, login, import, balance, address, refresh)
- [x] API: Transaction endpoints (preview, send, history, status, bridge/preview)
- [x] API: Rate limiting with slowapi
- [x] API: Pydantic schemas for validation
- [x] Docs: STRATEGIC_DIRECTION.md (authoritative)
- [x] Docs: ROADMAP_2026.md (implementation plan)
- [x] Docs: MANUAL_ACTIONS.md (human tasks)
- [x] Docs: CONTEXT_FOR_AI.md (session continuity)
- [x] Docs: North star changed to Weekly Active Creators (WAC)

## Earlier
- [x] VISION_2026.md revised
- [x] Pulse Deck improvements (balance, perks, AI card)
- [x] User journey documented
- [x] RPC fallback system added
- [x] Balance caching added

---

# Dependencies Map

```
Manual Actions (API Keys)
    │
    ├──► Circle Credentials ──► x402 Implementation
    │
    ├──► Bitrefill API ──► Real Gift Cards
    │
    └──► RPC Keys ──► Production Reliability

Security Fixes
    │
    └──► API Layer
           │
           ├──► x402 Protocol
           │
           ├──► Agent Protocol
           │
           └──► Mobile App
```

---

# Weekly Check-In Template

Use this for status updates:

```markdown
## Week of [DATE]

### Completed
- [ ] List completed items

### In Progress
- [ ] List current work

### Blocked
- [ ] List blockers and why

### Next Week
- [ ] List planned work

### Manual Actions Status
- Circle credentials: [ ] Done [ ] Pending [ ] Blocked
- Bitrefill API: [ ] Done [ ] Pending [ ] Blocked
- RPC Keys: [ ] Done [ ] Pending [ ] Blocked
```

---

# Quick Reference

| Document | Purpose |
|----------|---------|
| STRATEGIC_DIRECTION.md | Why we're building what |
| ROADMAP_2026.md | How we're building it |
| MANUAL_ACTIONS.md | What you need to do |
| CONTEXT_FOR_AI.md | Quick context for AI sessions |
| This file | What's being worked on now |

---

*Last Updated: February 2026*
*Next Review: Weekly or when priorities change*
