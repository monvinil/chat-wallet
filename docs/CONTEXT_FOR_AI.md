# Context for AI Assistants
## Read This First When Starting a New Session

---

> **CRITICAL: If you're an AI assistant and context was lost, READ THIS DOCUMENT FIRST.**
> This provides essential context about the project, its direction, and current state.

---

# Quick Summary

**Project:** USDChat
**What it is:** AI project launchpad with money rails (NOT just a wallet)
**Tech Stack:** Python/Streamlit + FastAPI (API layer added Feb 2026)
**Key Partner:** Circle (USDC infrastructure)
**Primary Goal:** Let people turn AI ideas into money-making agents
**North Star:** Weekly Active Creators (WAC)

---

# The Vision (One Paragraph)

USDChat enables anyone to create AI agents that can earn money. The wallet functionality is just plumbing — the real value is the ecosystem of community-created agents that can accept payments, run trades, and monetize autonomously. We're building on Circle's infrastructure (CCTP for bridging, x402 for micropayments) to create network effects where more creators attract more users attract more creators.

---

# Critical Documents (Read Order)

1. **STRATEGIC_DIRECTION.md** — Primary strategy and building direction
2. **ROADMAP_2026.md** — Detailed implementation plan with todos
3. **MANUAL_ACTIONS.md** — Tasks requiring human action (API keys, etc.)
4. **This file** — Quick context for new sessions

---

# Current State (February 2026)

## What Works
- Wallet creation (BIP39/44, EVM + Solana)
- Send/receive USDC
- Gift card purchases (mocked - needs real API key)
- AI chat with LangChain tools
- Yield farming backend (Aave - ready, needs UI wiring)
- CCTP bridging code (ready, not tested mainnet)
- **NEW: FastAPI layer with wallet/transaction endpoints**
- **Security: Cookie wallet key deprecated (memory-only)**
- **Security: Auto-lock on idle (15 min default)**

## What's In Progress
- [ ] Streamlit → API client integration
- [ ] x402 micropayments implementation (blocked on Circle credentials)

## What's Done (Recently)
- [x] Agent registry database schema (`migrations/007_agent_registry.sql`)
- [x] Agent SDK (`sdk/usdchat_agent/`)
- [x] Agent API endpoints (`/api/v1/agents/*`)

## What's Still Missing
- [ ] Scheduler executor deployment
- [ ] Circle credentials (user action required)
- [ ] Bitrefill API key (user action required)

## Immediate Priorities
1. ~~Security fixes~~ ✅ Done
2. ~~API layer (FastAPI)~~ ✅ Complete
3. ~~Agent registry~~ ✅ Schema + SDK + API done
4. x402 prototype (needs Circle credentials)
5. Streamlit → API migration

---

# Architecture

## Current State
```
┌─────────────────────────────────────────────────────────────────────┐
│                    Streamlit App (app.py)                           │
│                    - Chat interface                                 │
│                    - UI components                                  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FastAPI (api/main.py)                            │
│                    - /api/v1/wallet/*                               │
│                    - /api/v1/transactions/*                         │
│                    - /api/v1/agents/*  ← NEW                        │
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
│session_mgr   │       │ Agent API    │       │supabase      │
└──────────────┘       └──────────────┘       └──────────────┘
```

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
1. Complete strategic analysis and reframing
2. Security hardening:
   - Cookie wallet key deprecated
   - Auto-lock implemented (via rate_limiter.py)
   - Session state audit (wallet_data leak fixed)
3. FastAPI foundation created:
   - Wallet endpoints (create, login, import, balance, address)
   - Transaction endpoints (preview, send, history, status)
   - JWT authentication middleware
   - Rate limiting
4. Documentation restructured
5. North star changed from TVL to Weekly Active Creators
6. **Agent Protocol implemented:**
   - Database schema (`migrations/007_agent_registry.sql`)
   - Agent SDK with capabilities and x402 payment decorators
   - Full CRUD API for agents
   - Subscription and review system
   - Creator earnings dashboard

## Key Decisions
| Decision | Rationale |
|----------|-----------|
| Weekly Active Creators as north star | Avoids TVL/valuation trap |
| API layer before mobile | Unblocks everything |
| x402 prioritized | Enables agent economy |
| Community agents over internal integrations | Network effects |
| Agent SDK as Python package | Easy for creators to build |
| 70/20/10 revenue split | Industry standard, fair to creators |

---

# How To Continue Work

1. **Check TODO_MASTER.md** for current task list
2. **Check MANUAL_ACTIONS.md** for pending human tasks
3. **API is ready** — Full endpoints for wallet, transactions, and agents
4. **Agent SDK ready** — Creators can start building agents
5. **Next steps:**
   - Run `migrations/007_agent_registry.sql` in Supabase
   - x402 prototype (needs Circle credentials)
   - Streamlit → API client migration

---

# Questions to Ask User

If starting fresh:
1. "What's the current status on Circle credentials?"
2. "Should I continue with x402 implementation or focus elsewhere?"
3. "Any specific features you want prioritized?"

---

*Last Updated: February 2026*
*Session: Agent Protocol implemented (schema, SDK, API)*
