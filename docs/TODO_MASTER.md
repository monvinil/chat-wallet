# USDChat Master TODO
## Created: January 2026 | Last Session Context

---

# Context & Reasoning

## What This Document Is
A persistent todo list with context, so future sessions can pick up where we left off. Includes reasoning for priorities and dependencies.

## Core Product Vision (Refined)
**One-liner:** USDChat is an AI wallet. Chat to manage your money, earn on idle funds, spend anywhere.

**Three Horizons:**
1. **AI Wallet (NOW)** — Chat interface, send/receive USDC, gift cards, merchants
2. **Financial Autopilot (NEXT)** — Yield on idle funds, recurring payments, auto-routing
3. **AI Projects That Earn (FUTURE)** — Characters with wallets, trading bots, monetized agents

**Primary User:** Remote workers / freelancers who get paid in crypto or want to.

---

# A) Functionality

## P0 — Ship This Quarter

### 1. Wire Yield UI to Aave Client
**Status:** Not started
**Files:** `aave_client.py` (backend ready), `components/chat.py` (Earn modules)
**What:** Connect "Start Earning" module to actually deposit USDC to Aave
**Why:** Core Horizon 2 feature. Backend exists, just needs UI wiring.
**Dependency:** None

### 2. Deploy Scheduler Executor
**Status:** Not started
**Files:** `scheduler_manager.py`, `migrations/003_scheduled_tasks.sql` (done)
**What:** Cron job that checks `scheduled_tasks` table and executes due tasks
**Why:** Recurring payments won't work without this
**Dependency:** Needs deployment environment (Supabase Edge Functions or external cron)

### 3. Activate Real Bitrefill API
**Status:** Not started (currently mock mode)
**Files:** `bitrefill_api.py`
**What:** Switch from mock responses to real API calls
**Why:** Gift cards are a key spending use case
**Dependency:** Needs real Bitrefill API key in `.env`

### 4. Circle Programmable Wallets SDK
**Status:** Not started
**What:** Integrate Circle's embedded wallet SDK for smoother onboarding
**Why:** Better fiat→USDC flow, cleaner wallet creation
**Dependency:** Circle developer account, API keys
**Docs:** https://developers.circle.com/w3s/programmable-wallets

### 5. Email Verification Flow
**Status:** Not started
**What:** Send verification email on signup, require confirmation
**Why:** Security baseline, reduces spam accounts
**Dependency:** Email service (Supabase has built-in, or use Resend/SendGrid)

---

## P1 — Next Quarter

### 6. Multi-Step AI Agent
**Status:** Not started
**What:** Agent can chain actions: "Send $50 to Alice then buy a VPN"
**Why:** Power user delight, feels like real AI assistant
**Technical:** LangChain tool sequencing, state management between calls
**Dependency:** Current tools work, just needs orchestration layer

### 7. x402 Micropayments
**Status:** Not started
**What:** Implement Circle's x402 protocol for AI-to-AI payments
**Why:** Foundation for Horizon 3 (AI projects that earn)
**Docs:** https://developers.circle.com/stablecoins/x402

### 8. Hyperliquid Integration
**Status:** Not started
**What:** API integration for perpetual trading
**Why:** Horizon 3 — trading bots
**Dependency:** Hyperliquid API key, user needs to connect their account

### 9. Polymarket Integration
**Status:** Not started
**What:** API for prediction market bets
**Why:** Horizon 3 — trading bots
**Dependency:** Polymarket API access

### 10. Income Routing Engine
**Status:** Not started
**What:** Auto-split incoming deposits to buckets (spending/earning/tax)
**Why:** Horizon 2 — financial autopilot
**Technical:** Rules engine that triggers on deposit detection

---

# B) PMF (Product-Market Fit)

### 11. Define User Journey
**Status:** ✅ Done
**What:** Document Day 1, Day 7, Day 30 experience for freelancer persona
**Why:** Know what "success" looks like, align features to journey
**Output:** Added to VISION_2026.md as Part V-B

### 12. Add Analytics Events
**Status:** Not started
**What:** Track activation, first deposit, first send, yield enabled, retention
**Why:** Can't improve what you don't measure
**Technical:** PostHog, Mixpanel, or simple Supabase event logging

### 13. In-App Feedback Button
**Status:** Not started
**What:** Simple "Send feedback" that logs to Supabase + optional email
**Why:** Direct user voice
**Technical:** Quick to build, high value

### 14. Onboarding A/B Tests
**Status:** Not started
**What:** Test different hooks for first deposit conversion
**Why:** Deposit is the key activation metric
**Dependency:** Needs analytics first

### 15. Document Revenue Model
**Status:** Partially done (fee structure in config.py)
**What:** Explicit documentation of all revenue streams
**Current:** 0.2% + $0.005 flat fee, $3 cap (in `config.py`)
**Missing:** Yield split percentage, premium tier details

---

# C) UX/UI

### 16. Pulse Deck: Balance Card Actionable
**Status:** Not started
**What:** "Tap to earn" triggers yield deposit flow
**Why:** Promise without payoff is bad UX
**Files:** `components/chat.py` (render_pulse_deck)

### 17. Pulse Deck: Perk Progress Text
**Status:** Not started
**What:** Show "25 more to unlock" instead of just "75/100"
**Why:** Urgency, progress visibility, retention psychology
**Files:** `components/chat.py` (_render_pulse_card_html)

### 18. Pulse Deck: AI Card Last Action
**Status:** Not started
**What:** Show last AI action ("Sent $50 · 2h ago") on YOUR AI card
**Why:** Proof the AI is working, trust building
**Technical:** Query recent decision_logs or chat history
**Files:** `components/chat.py` (render_pulse_deck)

### 19. Mobile Responsive Pass
**Status:** Partially done
**What:** Test and fix cards, modules, chat on mobile viewports
**Why:** Many users will be mobile-first
**Files:** `components/chat.py` (CSS media queries exist, need testing)

### 20. Onboarding Polish
**Status:** Not started
**What:** First-run experience improvements
**Why:** First 30 seconds determine conversion
**Files:** `onboarding.py`

---

# D) From Discussion (Recommendations)

### 21. AI Confirmation for Large Amounts
**Status:** Not started
**What:** Transactions >$100 require explicit confirmation step
**Why:** Safety, trust, prevents expensive mistakes
**Technical:** Already have preview system, just add threshold logic
**Files:** `transaction_tools.py`, `components/chat.py`

### 22. Chained Tool Calls
**Status:** Not started
**What:** Support sequential tool execution in one message
**Why:** "Pay rent and buy groceries" should work
**Technical:** LangChain agent already supports this, may need prompt tuning

### 23. Perks → Real Spend Tracking
**Status:** Not started
**What:** Connect perk progress to actual gift card purchases
**Why:** Currently mock data (75/100 hardcoded)
**Technical:** Query transactions table for gift card purchases by brand
**Files:** `components/chat.py` (render_pulse_deck)

### 24. Streak/Retention Card
**Status:** Not started
**What:** "Active 5 days · $12.40 earned this week"
**Why:** Personal investment, retention psychology
**Technical:** Track daily active sessions, sum yield earnings

### 25. AI Character Monetization Flow
**Status:** Not started (Horizon 3)
**What:** Payment links, tips, subscriptions for AI characters
**Why:** Foundation for "AI projects that earn"
**Dependency:** x402 micropayments, character creation flow

---

# Priority Stack (Recommended Order)

## Immediate (This Week)
1. ~~**Wire yield UI**~~ — ✅ Done (backend + UI connected)
2. ~~**Pulse Deck improvements**~~ — ✅ Done (actionable cards, progress text, AI action)
3. ~~**Document user journey**~~ — ✅ Done (Day 1/7/30/90 in VISION_2026.md)

## Next Sprint
4. **Scheduler executor** — Recurring payments live
5. **Analytics events** — Start measuring
6. **Real Bitrefill** — Gift cards end-to-end (needs API key)

## Following Sprint
7. **Circle SDK exploration** — Smoother onboarding
8. **Multi-step agent** — Power user delight
9. **Mobile responsive** — Expand reach

## Horizon 3 Prep (Q3)
10. **Hyperliquid/Polymarket APIs**
11. **x402 micropayments**
12. **Character monetization**

---

# Dependencies / Needs From User

| Item | What's Needed |
|------|---------------|
| Real Bitrefill | API key in `.env` as `BITREFILL_API_KEY` |
| Circle SDK | Circle developer account, API credentials |
| Email verification | Email service config (Supabase built-in or external) |
| Hyperliquid | API key, user authentication flow |
| Polymarket | API access |
| Analytics | PostHog/Mixpanel project or Supabase event table |

---

# What's Already Done (This Session)

1. ✅ VISION_2026.md revised — Horizon 3 reframed as "AI projects that earn"
2. ✅ Language cleanup — "Treasury" → "Balance" throughout
3. ✅ Pulse Deck: TREASURY → BALANCE label change
4. ✅ Decision logger wired to chat
5. ✅ RPC fallback system added
6. ✅ Auto-lock functionality added
7. ✅ Balance caching added
8. ✅ Supabase migrations created (003, 004)
9. ✅ Pulse Deck: Balance card triggers yield deposit flow
10. ✅ Pulse Deck: Perk progress shows "X more → reward"
11. ✅ Pulse Deck: AI card displays last agent action
12. ✅ User journey documented (Day 1/7/30/90 for freelancer persona)

---

*Last updated: January 2026*
*Session: VISION review + PMF discussion + TODO creation*
