# USDChat Master TODO
## February 2026 — Strategic Pivot: Money Maker First

---

> **STRATEGIC PIVOT (February 2026)**
> Prioritizing retail "money maker" features over agent marketplace.
> A wallet that makes people $50/month has users. An agent marketplace with no agents has none.
> Frontend migrating: Streamlit → Next.js 14 + shadcn/ui

---

# Current Focus: Phase 1 — Money Maker MVP

**Status:** COMPLETE
**Goal:** Users deposit, see daily earnings, return daily
**Frontend:** Next.js 14 + shadcn/ui (replacing Streamlit)

---

# Phase 1: Money Maker MVP

## 1.1 Next.js Project Scaffold
**Priority:** P0 - CRITICAL
**Status:** [x] COMPLETE
**Creates:** `/web` directory

**Tasks:**
- [x] Initialize Next.js 14 with App Router
- [x] Install shadcn/ui, Tailwind CSS
- [x] Install TanStack Query, Zustand
- [x] Create API client connecting to FastAPI (`lib/api/client.ts`)
- [x] Implement JWT auth flow (login, signup, token refresh)
- [x] Create base layout with navigation
- [x] Build wallet overview page (balance display)

**Directory Structure:**
```
web/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── (auth)/login/
│   ├── (auth)/signup/
│   └── (dashboard)/wallet/
├── components/ui/
├── lib/api.ts
└── package.json
```

## 1.2 Yield UI (Start Earning)
**Priority:** P0 - CRITICAL
**Status:** [x] COMPLETE
**Backend:** `aave_client.py` + `api/routes/yield_routes.py`

**Tasks:**
- [x] Create `/api/v1/yield/deposit` endpoint (wire to aave_client)
- [x] Create `/api/v1/yield/withdraw` endpoint
- [x] Create `/api/v1/yield/status` endpoint
- [x] Build "Start Earning" card component
- [x] Build yield toggle (on/off)
- [x] Show projected earnings calculator
- [x] Add confirmation modal with fee breakdown

## 1.3 Auto-DCA Setup
**Priority:** P0 - CRITICAL
**Status:** [x] COMPLETE
**Backend:** `scheduler_executor.py` + `api/routes/scheduler_routes.py`

**Tasks:**
- [x] Create `/api/v1/scheduler/create` endpoint
- [x] Create `/api/v1/scheduler/list` endpoint
- [x] Create `/api/v1/scheduler/cancel` endpoint
- [x] Add DCA support to scheduler executor
- [x] Build DCA setup form component
- [x] Build active schedules list
- [x] Add next execution preview

## 1.4 Earnings Dashboard
**Priority:** P0 - CRITICAL
**Status:** [x] COMPLETE
**The Core Return Behavior Driver**

**Tasks:**
- [x] Create `/api/v1/earnings/summary` endpoint
- [x] Create `/api/v1/earnings/history` endpoint
- [x] Build earnings summary cards (today/week/month/all-time)
- [x] Build 30-day earnings chart (Recharts)
- [x] Build earnings breakdown by source
- [x] Add daily/weekly/monthly/all-time toggles

## 1.5 Transaction Flow (Send/Receive)
**Priority:** P1 - HIGH
**Status:** [x] COMPLETE
**Backend:** Already exists via API

**Tasks:**
- [x] Build send form with address validation
- [x] Build transaction preview modal
- [x] Build transaction confirmation flow
- [x] Build receive page with QR code
- [x] Build transaction history list
- [ ] Add transaction status polling (enhancement)

---

# Phase 2: PWA + Retention

## 2.1 PWA Configuration
**Priority:** P0 - CRITICAL (after Phase 1)
**Status:** [ ] Not Started

**Tasks:**
- [ ] Configure `next-pwa` in next.config.ts
- [ ] Create `manifest.json` with app icons
- [ ] Set up service worker for offline support
- [ ] Add install prompt banner
- [ ] Configure app shortcuts (quick send, view earnings)

## 2.2 Push Notifications
**Priority:** P0 - CRITICAL (after Phase 1)
**Status:** [ ] Not Started
**The Daily Return Trigger**

**Tasks:**
- [ ] Set up web push (Firebase or OneSignal)
- [ ] Create notification preferences UI
- [ ] Build daily earnings notification (6 PM local time)
- [ ] Build transaction notification triggers
- [ ] Add notification history in-app

## 2.3 Email Notifications
**Priority:** P1 - HIGH (after Phase 1)
**Status:** [ ] Not Started

**Tasks:**
- [ ] Set up email service (Resend or SendGrid)
- [ ] Design email templates
- [ ] Weekly earnings summary email
- [ ] Transaction confirmation emails
- [ ] Security alert emails

## 2.4 Mobile UI Polish
**Priority:** P1 - HIGH (after Phase 1)
**Status:** [ ] Not Started

**Tasks:**
- [ ] Mobile-first navigation (bottom tabs)
- [ ] Touch-optimized buttons and inputs
- [ ] Swipe gestures for common actions
- [ ] Pull-to-refresh on balances
- [ ] Haptic feedback on transactions

---

# Phase 3: Agent Marketplace (After User Traction)

## 3.1 Agent Discovery UI
**Priority:** P1 - HIGH (after Phase 2)
**Status:** [ ] Not Started
**Backend:** Already built (api/routes/agents.py)

**Tasks:**
- [ ] Build agent marketplace page
- [ ] Build agent cards with stats
- [ ] Build category filters
- [ ] Build search functionality
- [ ] Build agent detail page
- [ ] Build "Use this agent" flow

## 3.2 x402 Integration
**Priority:** P0 - CRITICAL (when reached)
**Status:** [ ] Blocked on Circle credentials

**Tasks:**
- [ ] Implement x402 payment request generation
- [ ] Implement payment verification
- [ ] Create payment confirmation UI
- [ ] Handle 402 responses in agent chat
- [ ] Track micropayments in agent_earnings

## 3.3 Agent Chat Interface
**Priority:** P1 - HIGH (after Phase 2)
**Status:** [ ] Not Started

**Tasks:**
- [ ] Build chat UI for agent interaction
- [ ] Handle streaming responses
- [ ] Show payment prompts inline
- [ ] Display agent capabilities
- [ ] Track conversation history

## 3.4 Creator Onboarding
**Priority:** P1 - HIGH (after Phase 2)
**Status:** [ ] Not Started

**Tasks:**
- [ ] Build "Create Agent" wizard
- [ ] Build agent configuration form
- [ ] Build capability selection
- [ ] Build pricing configuration
- [ ] Build agent testing sandbox
- [ ] Build publish/review flow

---

# Completed (Infrastructure Ready)

## Security Fixes — DONE
- [x] Cookie wallet key deprecated (memory-only)
- [x] Auto-lock on idle (15 min default)
- [x] Session state audit, fixed wallet_data leak
- [x] SENSITIVE_SESSION_KEYS documented

## FastAPI Backend — DONE
- [x] JWT auth middleware
- [x] Wallet endpoints (create, login, import, balance, address, refresh)
- [x] Transaction endpoints (preview, send, history, status)
- [x] Rate limiting with slowapi
- [x] Pydantic schemas for validation

## Agent Protocol — DONE (Backend Ready)
- [x] Database schema (8 tables) - `migrations/007_agent_registry.sql`
- [x] Agent SDK package - `sdk/usdchat_agent/`
- [x] Agent API endpoints - `api/routes/agents.py`
- [x] Example agents (crypto_news, trading_bot)

---

# Manual Actions Required (Parallel Track)

**Owner:** Founder (cannot be automated)
**Details:** See MANUAL_ACTIONS.md

| Item | Status | Blocks |
|------|--------|--------|
| Circle API credentials | [ ] Pending | x402 micropayments |
| Bitrefill API key | [ ] Pending | Gift card purchases |
| RPC keys (Alchemy/Infura) | [ ] Pending | Production reliability |

---

# Technical Debt (Address When Convenient)

| Item | Priority | Effort |
|------|----------|--------|
| Pin dependency versions | P0 | Low |
| Add integration tests | P1 | High |
| Deduplicate balance cache logic | P2 | Low |
| Abstract Supabase queries | P2 | Medium |
| Add structured logging (JSON) | P2 | Low |
| RPC connection pooling | P2 | Medium |
| RLS policies for all tables | P1 | Medium |

---

# Dependencies Map

```
Phase 1: Money Maker MVP
    │
    ├──► Next.js Scaffold ──► All Frontend
    │
    ├──► Yield API ──► Yield UI
    │
    └──► Scheduler Deploy ──► Auto-DCA

Phase 2: PWA + Retention
    │
    ├──► Phase 1 Complete
    │
    └──► Push Service Setup ──► Notifications

Phase 3: Agent Marketplace
    │
    ├──► Phase 2 Complete (user base)
    │
    └──► Circle Credentials ──► x402 Payments
```

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

# Quick Reference

| Document | Purpose |
|----------|---------|
| STRATEGIC_DIRECTION.md | Why we're building what |
| ROADMAP_2026.md | How we're building it (detailed) |
| MANUAL_ACTIONS.md | What you need to do |
| CONTEXT_FOR_AI.md | Quick context for AI sessions |
| This file | What's being worked on now |

---

*Last Updated: February 2026*
*Strategic Pivot: Money Maker First → Agent Marketplace Second*
