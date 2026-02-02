# USDChat Roadmap 2026
## Strategic Pivot: Money Maker First, Agent Marketplace Second

---

> **MAJOR UPDATE (February 2026)**
> - Pivoting from Streamlit to Next.js + shadcn/ui
> - Prioritizing retail "money maker" features over agent marketplace
> - Agent infrastructure stays (already built), but ships after user traction
>
> **Rationale:** A wallet that makes people $50/month has users. An agent marketplace with no agents has none.

---

# The New Stack

## Frontend Migration: Streamlit → Next.js

**Why the change:**
| Streamlit | Next.js |
|-----------|---------|
| Full page reload on every input | Real-time updates |
| No proper auth/RBAC | Industry-standard auth |
| ~15% of fintech apps use it | ~70% of fintech apps use React |
| Limited mobile experience | PWA with native-like feel |
| Python-only ecosystem | Full JS/TS ecosystem |

**New Frontend Stack:**
```
Next.js 14 (App Router)
├── shadcn/ui (component library)
├── Tailwind CSS (styling)
├── TanStack Query (data fetching)
├── Zustand (state management)
├── next-pwa (PWA support)
└── Recharts (analytics/charts)
```

**Backend (Unchanged):**
```
FastAPI ✅ (already built)
├── JWT auth ✅
├── Rate limiting ✅
├── Wallet endpoints ✅
├── Transaction endpoints ✅
└── Agent endpoints ✅
```

Sources:
- [Fintech App Development 2026](https://trio.dev/fintech-app-development/)
- [Streamlit Limitations for Production](https://plotly.com/blog/best-streamlit-alternatives-production-data-apps/)
- [shadcn/ui vs Radix](https://saasindie.com/blog/shadcn-vs-radix-themes-comparison)

---

# Phase Overview

```
COMPLETED ████████████████████████████████
├── Security hardening ✅
├── FastAPI backend ✅
├── Agent SDK + DB schema ✅
└── Agent API endpoints ✅

PHASE 1: MONEY MAKER MVP ████████░░░░░░░░░░ (Current Focus)
├── Next.js scaffold + API connection
├── One-click yield (Aave)
├── Auto-DCA scheduling
└── Earnings dashboard

PHASE 2: PWA + RETENTION ████░░░░░░░░░░░░░░
├── PWA configuration
├── Push notifications
├── Daily earnings emails
└── Mobile-optimized UI

PHASE 3: AGENT MARKETPLACE ░░░░░░░░░░░░░░░░ (After User Traction)
├── Agent discovery UI
├── x402 integration (needs Circle)
└── Creator onboarding
```

---

# PHASE 1: MONEY MAKER MVP
## Goal: Users deposit, see daily earnings, return daily

### 1.1 Next.js Project Scaffold
**Priority:** P0 - CRITICAL
**Creates:** `/web` directory

```
web/
├── app/
│   ├── layout.tsx         # Root layout with providers
│   ├── page.tsx           # Landing/dashboard
│   ├── (auth)/
│   │   ├── login/
│   │   └── signup/
│   ├── (dashboard)/
│   │   ├── wallet/
│   │   ├── earn/
│   │   ├── send/
│   │   └── history/
│   └── api/               # BFF routes if needed
├── components/
│   ├── ui/                # shadcn components
│   ├── wallet/
│   ├── earn/
│   └── common/
├── lib/
│   ├── api.ts             # FastAPI client
│   ├── auth.ts            # Auth utilities
│   └── hooks/             # Custom hooks
├── public/
│   └── manifest.json      # PWA manifest
├── tailwind.config.ts
├── next.config.ts
└── package.json
```

**Tasks:**
- [ ] Initialize Next.js 14 with App Router
- [ ] Install shadcn/ui, Tailwind, dependencies
- [ ] Create API client connecting to FastAPI
- [ ] Implement JWT auth flow (login, signup, token refresh)
- [ ] Create base layout with navigation
- [ ] Build wallet overview page (balance display)

### 1.2 Yield UI (Start Earning)
**Priority:** P0 - CRITICAL
**Backend:** `aave_client.py` (already exists)

**The UX:**
```
┌─────────────────────────────────────┐
│  Your USDC is earning 0%            │
│                                     │
│  ┌─────────────────────────────┐    │
│  │  Start Earning              │    │
│  │  8.2% APY on Aave           │    │
│  │                             │    │
│  │  Your balance: $1,247.00    │    │
│  │                             │    │
│  │  ┌─────────────────────┐    │    │
│  │  │  Enable Yield  →    │    │    │
│  │  └─────────────────────┘    │    │
│  └─────────────────────────────┘    │
│                                     │
│  Projected monthly: +$8.51          │
│  Projected yearly: +$102.25         │
└─────────────────────────────────────┘
```

**Tasks:**
- [ ] Create `/api/v1/yield/deposit` endpoint (wire to aave_client)
- [ ] Create `/api/v1/yield/withdraw` endpoint
- [ ] Create `/api/v1/yield/status` endpoint
- [ ] Build "Start Earning" card component
- [ ] Build yield toggle (on/off)
- [ ] Show projected earnings calculator
- [ ] Add confirmation modal with fee breakdown

### 1.3 Auto-DCA Setup
**Priority:** P0 - CRITICAL
**Backend:** `scheduler_manager.py` (exists), `scheduled_tasks` table (exists)

**The UX:**
```
┌─────────────────────────────────────┐
│  Auto-Invest                        │
│                                     │
│  Buy ETH automatically              │
│                                     │
│  Amount:  [$50      ▼]              │
│  Every:   [Week     ▼]              │
│  From:    USDC balance              │
│                                     │
│  ┌─────────────────────────────┐    │
│  │  Start Auto-Invest  →       │    │
│  └─────────────────────────────┘    │
│                                     │
│  Next purchase: Monday, Feb 10      │
└─────────────────────────────────────┘
```

**Tasks:**
- [ ] Create `/api/v1/scheduler/create` endpoint
- [ ] Create `/api/v1/scheduler/list` endpoint
- [ ] Create `/api/v1/scheduler/cancel` endpoint
- [ ] Deploy scheduler executor (cron job or edge function)
- [ ] Build DCA setup form component
- [ ] Build active schedules list
- [ ] Add next execution preview

### 1.4 Earnings Dashboard
**Priority:** P0 - CRITICAL
**The Core Return Behavior Driver**

**The UX:**
```
┌─────────────────────────────────────┐
│  Today's Earnings                   │
│                                     │
│     +$0.47                          │
│     ━━━━━━━━━━━━━━━━━━━━            │
│                                     │
│  This Week    This Month   All Time │
│  +$3.29       +$14.21      +$47.83  │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ [Earnings Chart - 30 days] │    │
│  └─────────────────────────────┘    │
│                                     │
│  Breakdown:                         │
│  • Yield (Aave)      +$0.35        │
│  • DCA gains         +$0.12        │
└─────────────────────────────────────┘
```

**Tasks:**
- [ ] Create `/api/v1/earnings/summary` endpoint
- [ ] Create `/api/v1/earnings/history` endpoint
- [ ] Build earnings summary cards
- [ ] Build 30-day earnings chart (Recharts)
- [ ] Build earnings breakdown by source
- [ ] Add daily/weekly/monthly/all-time toggles

### 1.5 Transaction Flow (Send/Receive)
**Priority:** P1 - HIGH
**Backend:** Already exists via API

**Tasks:**
- [ ] Build send form with address validation
- [ ] Build transaction preview modal
- [ ] Build transaction confirmation flow
- [ ] Build receive page with QR code
- [ ] Build transaction history list
- [ ] Add transaction status polling

---

# PHASE 2: PWA + RETENTION
## Goal: Mobile-like experience, daily return triggers

### 2.1 PWA Configuration
**Priority:** P0 - CRITICAL

**Tasks:**
- [ ] Configure `next-pwa` in next.config.ts
- [ ] Create `manifest.json` with app icons
- [ ] Set up service worker for offline support
- [ ] Add install prompt banner
- [ ] Configure app shortcuts (quick send, view earnings)

### 2.2 Push Notifications
**Priority:** P0 - CRITICAL
**The Daily Return Trigger**

**Notification Types:**
1. Daily earnings: "You earned $0.47 today"
2. DCA executed: "Bought 0.02 ETH for $50"
3. Price alerts: "ETH up 5% today"
4. Large deposits/withdrawals: "Received $500 USDC"

**Tasks:**
- [ ] Set up web push with Firebase or OneSignal
- [ ] Create notification preferences UI
- [ ] Build daily earnings notification (6 PM local time)
- [ ] Build transaction notification triggers
- [ ] Add notification history in-app

### 2.3 Email Notifications
**Priority:** P1 - HIGH

**Tasks:**
- [ ] Set up email service (Resend or SendGrid)
- [ ] Design email templates
- [ ] Weekly earnings summary email
- [ ] Transaction confirmation emails
- [ ] Security alert emails

### 2.4 Mobile UI Polish
**Priority:** P1 - HIGH

**Tasks:**
- [ ] Mobile-first navigation (bottom tabs)
- [ ] Touch-optimized buttons and inputs
- [ ] Swipe gestures for common actions
- [ ] Pull-to-refresh on balances
- [ ] Haptic feedback on transactions

---

# PHASE 3: AGENT MARKETPLACE
## Goal: Leverage user base for agent distribution
## Timing: After Phase 2 proves retention

### 3.1 Agent Discovery UI
**Priority:** P1 - HIGH
**Backend:** Already built (api/routes/agents.py)

**Tasks:**
- [ ] Build agent marketplace page
- [ ] Build agent cards with stats
- [ ] Build category filters
- [ ] Build search functionality
- [ ] Build agent detail page
- [ ] Build "Use this agent" flow

### 3.2 x402 Integration
**Priority:** P0 - CRITICAL
**Blocked on:** Circle API credentials

**Tasks:**
- [ ] Implement x402 payment request generation
- [ ] Implement payment verification
- [ ] Create payment confirmation UI
- [ ] Handle 402 responses in agent chat
- [ ] Track micropayments in agent_earnings

### 3.3 Agent Chat Interface
**Priority:** P1 - HIGH

**Tasks:**
- [ ] Build chat UI for agent interaction
- [ ] Handle streaming responses
- [ ] Show payment prompts inline
- [ ] Display agent capabilities
- [ ] Track conversation history

### 3.4 Creator Onboarding
**Priority:** P1 - HIGH

**Tasks:**
- [ ] Build "Create Agent" wizard
- [ ] Build agent configuration form
- [ ] Build capability selection
- [ ] Build pricing configuration
- [ ] Build agent testing sandbox
- [ ] Build publish/review flow

---

# Technical Debt to Address

| Item | Priority | Effort |
|------|----------|--------|
| Pin dependency versions | P0 | Low |
| Add integration tests | P1 | High |
| Deduplicate balance cache logic | P2 | Low |
| Abstract Supabase queries | P2 | Medium |
| Add structured logging (JSON) | P2 | Low |
| RPC connection pooling | P2 | Medium |

---

# What's Done vs What's Needed

## ✅ Completed
- Security hardening (memory-only keys, auto-lock)
- FastAPI backend (wallet, transactions, agents)
- Agent SDK (`sdk/usdchat_agent/`)
- Agent database schema (8 tables)
- Agent API endpoints (full CRUD)
- CCTP bridging code (not tested mainnet)
- Aave yield backend (needs UI wiring)
- Scheduler database (needs executor deployment)

## 🚧 Blocked on You
- Circle API credentials (x402)
- Bitrefill API key (gift cards)

## 📋 Next Up (No Blockers)
1. Next.js scaffold + API integration
2. Yield UI (one-click Aave)
3. Scheduler executor deployment
4. Earnings dashboard

---

# Success Metrics

## Phase 1 Success (Money Maker MVP)
- [ ] User can deposit USDC
- [ ] User can enable yield with one click
- [ ] User sees daily earnings
- [ ] User can set up auto-DCA

## Phase 2 Success (Retention)
- [ ] PWA installable on mobile
- [ ] Daily push notification of earnings
- [ ] 30%+ users return within 7 days

## Phase 3 Success (Marketplace)
- [ ] 10+ agents published
- [ ] 100+ agent interactions
- [ ] $100+ in agent payments

---

*Last Updated: February 2026*
*Strategic Pivot: Retail money maker → Agent marketplace*
