# Context for AI Assistants
## Read This First When Starting a New Session

---

> **CRITICAL: If you're an AI assistant and context was lost, READ THIS DOCUMENT FIRST.**
> This provides essential context about the project, its direction, and current state.

---

# Quick Summary

**Project:** USDChat
**What it is:** Retail money-maker wallet (yield + DCA) with future agent marketplace
**Tech Stack:** Next.js 14 + shadcn/ui (frontend) + FastAPI (backend)
**Key Partner:** Circle (USDC infrastructure)
**Primary Goal:** Help users earn passive income on their USDC
**North Star:** Daily Active Users checking earnings
**Strategic Pivot:** Money maker features first, agent marketplace second

---

# The Vision (One Paragraph)

USDChat makes your USDC work for you. One-click yield on Aave, automated DCA into ETH/BTC, and a beautiful earnings dashboard that brings you back every day. The agent marketplace (already built in backend) ships after we have users — because a wallet that makes people $50/month has users, an agent marketplace with no agents has none. We're building on Circle's infrastructure (CCTP for bridging, x402 for micropayments) for the future agent economy.

---

# Critical Documents (Read Order)

1. **STRATEGIC_DIRECTION.md** — Primary strategy and building direction
2. **ROADMAP_2026.md** — Detailed implementation plan with todos
3. **MANUAL_ACTIONS.md** — Tasks requiring human action (API keys, etc.)
4. **This file** — Quick context for new sessions

---

# Current State (February 2026)

## Strategic Pivot
- **OLD:** Agent marketplace first, wallet features second
- **NEW:** Money maker features first, agent marketplace second
- **Rationale:** A wallet that makes people $50/month has users. An agent marketplace with no agents has none.

## Frontend Migration
- **FROM:** Streamlit (full page reloads, limited mobile, 15% of fintech)
- **TO:** Next.js 14 + shadcn/ui + Tailwind (real-time, PWA, 70% of fintech)

## What's Done (Backend Ready)
- [x] Wallet creation (BIP39/44, EVM + Solana)
- [x] FastAPI layer (wallet, transactions, agents)
- [x] Agent protocol (database, SDK, API) - ships Phase 3
- [x] Security hardening (memory-only keys, auto-lock)
- [x] Yield backend (Aave - needs UI)
- [x] Scheduler backend (needs executor deploy)

## Phase 1 Complete
- [x] Next.js 14 scaffold with App Router (`/web` directory)
- [x] shadcn/ui components (15+ UI components)
- [x] TanStack Query + Zustand for state management
- [x] JWT auth flow (login, signup, token refresh)
- [x] Yield API + UI (Aave deposit/withdraw)
- [x] Scheduler API + UI (DCA schedules CRUD)
- [x] Earnings API + UI (30-day chart, summary)
- [x] All frontend pages (wallet, earn, send, receive, history)
- [x] Docker Compose for local development

## What's Remaining for Production
- [ ] End-to-end testing with real backend
- [ ] Deploy scheduler executor as background worker

## What's Still Missing
- [ ] Circle credentials (blocks x402 - Phase 3)
- [ ] Bitrefill API key (gift cards)
- [ ] RPC keys for production

## Immediate Priorities
1. **Phase 1: Money Maker MVP** ✅ COMPLETE
   - Next.js + shadcn/ui scaffold
   - Yield UI, DCA, earnings dashboard
2. **Phase 2: PWA + Retention** ← NEXT
   - Push notifications, mobile polish
3. **Phase 3: Agent Marketplace**
   - After user traction proven

---

# Architecture

## Target State (Next.js + FastAPI)
```
┌─────────────────────────────────────────────────────────────────────┐
│                    Next.js 14 App (/web)                            │
│                    - App Router                                     │
│                    - shadcn/ui components                           │
│                    - TanStack Query (data fetching)                 │
│                    - Zustand (state management)                     │
│                    - PWA with next-pwa                              │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FastAPI (api/main.py)                            │
│                    - /api/v1/wallet/*                               │
│                    - /api/v1/transactions/*                         │
│                    - /api/v1/agents/* (Phase 3)                     │
│                    - /api/v1/yield/* ✅                             │
│                    - /api/v1/scheduler/* ✅                         │
│                    - /api/v1/earnings/* ✅                          │
│                    - JWT auth, rate limiting                        │
└─────────────────────────────────────────────────────────────────────┘
                                  │
        ┌───────────────────────┬┴──────────────────────┐
        ▼                       ▼                       ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│    Wallet    │       │    Agent     │       │   Shared     │
│   Services   │       │   Services   │       │   Services   │
│              │       │              │       │              │
│wallet_manager│       │ Agent SDK    │       │chain_utils   │
│aave_client   │       │ Agent API    │       │supabase      │
│scheduler_mgr │       │              │       │              │
└──────────────┘       └──────────────┘       └──────────────┘
```

## Legacy (Streamlit - Being Replaced)
The Streamlit app (`app.py`) remains for reference but is being replaced by the Next.js frontend.

## API Endpoints Available

### Core Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/ready` | GET | Readiness check |

### Wallet Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/wallet/create` | POST | Create new wallet |
| `/api/v1/wallet/login` | POST | Login to wallet |
| `/api/v1/wallet/import` | POST | Import wallet |
| `/api/v1/wallet/balance` | GET | Get balances (auth required) |
| `/api/v1/wallet/address/{chain}` | GET | Get deposit address |
| `/api/v1/wallet/refresh` | POST | Refresh JWT token |

### Transaction Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/transactions/preview` | POST | Preview transaction |
| `/api/v1/transactions/send` | POST | Execute transaction |
| `/api/v1/transactions/history` | GET | Transaction history |
| `/api/v1/transactions/status/{hash}` | GET | Transaction status |

### Agent Endpoints (NEW)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/agents/` | GET | List/search agents |
| `/api/v1/agents/` | POST | Create agent (auth) |
| `/api/v1/agents/featured` | GET | Get featured agents |
| `/api/v1/agents/categories` | GET | Get agent categories |
| `/api/v1/agents/capabilities` | GET | Get available capabilities |
| `/api/v1/agents/{slug}` | GET | Get agent details |
| `/api/v1/agents/{slug}` | PATCH | Update agent (auth, owner) |
| `/api/v1/agents/{slug}` | DELETE | Archive agent (auth, owner) |
| `/api/v1/agents/{slug}/publish` | POST | Publish agent (auth, owner) |
| `/api/v1/agents/{slug}/message` | POST | Send message to agent |
| `/api/v1/agents/{slug}/subscribe` | POST | Subscribe to agent (auth) |
| `/api/v1/agents/{slug}/subscription` | GET | Get subscription status (auth) |
| `/api/v1/agents/{slug}/reviews` | GET | Get agent reviews |
| `/api/v1/agents/{slug}/reviews` | POST | Create/update review (auth) |
| `/api/v1/agents/my/agents` | GET | Get creator's agents (auth) |
| `/api/v1/agents/my/earnings` | GET | Get creator earnings (auth) |

### Yield Endpoints (Phase 1)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/yield/status` | GET | Get yield status (APY, deposited, earned) |
| `/api/v1/yield/deposit` | POST | Deposit USDC into Aave (auth) |
| `/api/v1/yield/withdraw` | POST | Withdraw from Aave (auth) |

### Scheduler Endpoints (Phase 1)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/scheduler/create` | POST | Create DCA schedule (auth) |
| `/api/v1/scheduler/list` | GET | List all schedules (auth) |
| `/api/v1/scheduler/{id}/cancel` | POST | Cancel a schedule (auth) |
| `/api/v1/scheduler/{id}/pause` | POST | Pause a schedule (auth) |
| `/api/v1/scheduler/{id}/resume` | POST | Resume a schedule (auth) |

### Earnings Endpoints (Phase 1)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/earnings/summary` | GET | Get earnings summary (auth) |
| `/api/v1/earnings/history` | GET | Get earnings history for charts (auth) |

## Running the API
```bash
# Install new dependencies
pip install -r requirements.txt

# Run API server (debug mode)
python run_api.py --debug

# Run API server (production)
python run_api.py --port 8000
```

---

# Key Concepts

## Agent Protocol (IMPLEMENTED)
Community creates agents using our SDK (`sdk/usdchat_agent/`). Agents can:
- Accept payments (x402 micropayments)
- Pay other agents
- Run trading strategies
- Charge subscriptions (monthly/yearly)

Revenue split: Creator 70% / Platform 20% / Referrer 10%

### Agent SDK Structure
```
sdk/usdchat_agent/
├── __init__.py      # Main exports
├── agent.py         # Base Agent class
├── capabilities.py  # Capability system (@capability decorator)
├── payments.py      # x402 payment helpers (@x402_payment decorator)
├── types.py         # AgentContext, UserInfo, etc.
├── exceptions.py    # PaymentRequiredError, CapabilityDeniedError
└── examples/
    ├── crypto_news_agent.py    # Per-request pricing example
    └── trading_bot_agent.py    # Subscription + capabilities example
```

### Agent Database Tables
- `agents` - Core registry (name, slug, pricing, capabilities, stats)
- `agent_versions` - Deployment versioning
- `agent_earnings` - Revenue tracking with auto-split
- `agent_subscriptions` - User subscriptions
- `agent_requests` - Usage logging
- `agent_reviews` - Ratings and reviews
- `agent_capabilities` - Built-in capability definitions
- `user_agent_permissions` - Per-user permission grants

## Vault System
Every wallet is a vault. Every agent has a vault.
Idle funds earn yield. Platform takes 20% of yield.

## Circle Integration
- **CCTP:** Cross-chain USDC bridging
- **x402:** HTTP 402 micropayments for agents
- **Programmable Wallets:** Optional easy onboarding

**Status:** Waiting on Circle credentials (see MANUAL_ACTIONS.md)

---

# Code Structure

## Key Files
| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit entry |
| `api/main.py` | FastAPI application |
| `api/routes/wallet.py` | Wallet API endpoints |
| `api/routes/transactions.py` | Transaction API endpoints |
| `api/routes/agents.py` | Agent API endpoints (NEW) |
| `api/schemas/agent.py` | Agent request/response schemas (NEW) |
| `api/middleware/auth.py` | JWT authentication |
| `sdk/usdchat_agent/` | Agent SDK package (NEW) |
| `wallet_manager.py` | Key derivation, encryption |
| `session_manager.py` | Session handling (security hardened) |
| `rate_limiter.py` | Auto-lock, rate limiting |
| `components/chat.py` | Chat interface |

## Database
- Supabase (PostgreSQL)
- Key tables: `users`, `wallets`, `transactions`, `scheduled_tasks`, `sessions`
- Agent tables: `agents`, `agent_earnings`, `agent_subscriptions`, `agent_requests`, `agent_reviews` (NEW)

## Environment Variables Needed
See MANUAL_ACTIONS.md for full list. Critical:
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`
- `CIRCLE_API_KEY` (pending)
- `BITREFILL_API_KEY` (pending)
- `JWT_SECRET_KEY` (for API auth)

---

# What NOT To Do

1. **Don't commit API keys** — All secrets in `.env`
2. **Don't use service key everywhere** — Prefer RLS policies
3. **Don't store sensitive data in cookies** — ✅ Fixed (memory only now)
4. **Don't over-engineer** — Ship fast, iterate

---

# Communication Style

The founder prefers:
- Direct, honest assessments
- Technical depth when needed
- Strategic thinking alongside tactical
- No fluff, no excessive praise
- Action-oriented recommendations
- **Quality over speed** (explicitly stated)
- Modern libraries over generic solutions

---

# Recent Session Context

## Work Done (February 2026)
1. **Strategic Pivot:** Money maker first, agent marketplace second
2. **Frontend Decision:** Streamlit → Next.js 14 + shadcn/ui
3. Security hardening:
   - Cookie wallet key deprecated
   - Auto-lock implemented (via rate_limiter.py)
   - Session state audit (wallet_data leak fixed)
4. FastAPI foundation created (complete)
5. Agent Protocol implemented (backend ready, UI in Phase 3):
   - Database schema (`migrations/007_agent_registry.sql`)
   - Agent SDK (`sdk/usdchat_agent/`)
   - Full CRUD API (`api/routes/agents.py`)
6. **Roadmap rewritten** for strategic pivot
7. **TODO updated** to reflect Phase 1-3 approach

## Key Decisions
| Decision | Rationale |
|----------|-----------|
| Money maker first | Cold-start problem: no agents → no users |
| Next.js 14 + shadcn/ui | 70% of fintech uses React; PWA support |
| Daily earnings as north star | Return behavior driver |
| Agent marketplace Phase 3 | Backend ready, wait for user base |
| 70/20/10 revenue split | Industry standard, fair to creators |

---

# How To Continue Work

1. **Check TODO_MASTER.md** for current task list (Phase 1-3 structure)
2. **Check ROADMAP_2026.md** for detailed implementation plans
3. **Check MANUAL_ACTIONS.md** for pending human tasks

## Phase 2 Next Steps (PWA + Retention)
1. Configure `next-pwa` in `web/next.config.ts`
2. Set up push notifications (Firebase or OneSignal)
3. Build daily earnings notification (6 PM local time)
4. Email service integration (Resend or SendGrid)
5. Mobile UI polish (pull-to-refresh, haptic feedback)

## What's Already Done
- FastAPI backend (wallet, transactions, agents)
- Agent database schema (run in Supabase)
- Agent SDK (sdk/usdchat_agent/)
- Security hardening

## Blocked Items (User Action Required)
- Circle credentials → x402 (Phase 3)
- Bitrefill API key → Gift cards

---

# Questions to Ask User

If starting fresh:
1. "Phase 1 is complete. Ready to start Phase 2 (PWA + notifications)?"
2. "Preference for push notifications: Firebase Cloud Messaging or OneSignal?"
3. "Preference for email service: Resend or SendGrid?"
4. "What's the status on Circle/Bitrefill credentials?"

---

*Last Updated: February 2026*
*Session: Strategic pivot to Money Maker first, Next.js + shadcn/ui*
