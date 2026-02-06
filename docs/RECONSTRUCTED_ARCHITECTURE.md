# Reconstructed Architecture - USDChat

> **Author**: Lead Architect
> **Date**: 2026-02-06
> **Basis**: Code audit (not docs). Grounded in what actually works.

---

## The Product (Founder's Vision)

**"A wallet for people who want to make money with AI."**

Not a launchpad. Not an agent marketplace (yet). A wallet with built-in, pre-created money-making mechanisms that work from day one.

The moat is not the wallet. The moat is the **money-making features that are hard to replicate** - AI-powered yield optimization, automated DCA, trading strategies, and eventually an ecosystem of money-making agents.

---

## What We Actually Have (Code Audit, Feb 2026)

### Working (Can ship today)
1. **Wallet** - BIP39/44, EVM+Solana, encrypted, self-custodial
2. **Yield** - Aave V3 deposits/withdrawals, real APY, real transactions
3. **Transfers** - Direct USDC sends, gasless meta-transactions
4. **Scheduler** - Cron-based task engine (Supabase-backed, transfers only)
5. **Balance Ledger** - Double-spend prevention, atomic operations
6. **Email Automation** - IMAP, verification code extraction
7. **AI Agent** - LangChain + Claude, 7 tool categories wired up

### Broken / Incomplete (Must fix before launch)
1. **API send endpoint** - Returns fake tx_hash (transactions.py:301)
2. **Bridge completion** - Can burn USDC but can't claim on destination
3. **DCA execution** - Mocked with hardcoded prices

### Scaffolding (Exists architecturally, not functional)
1. **Gift cards** - Needs Bitrefill API key
2. **Merchant payments** - Empty adapters, missing imports
3. **Agent marketplace** - DB + API exist, execution returns placeholder
4. **x402 payments** - Framework exists, verification always fails

---

## Reconstructed Architecture

### Principle: Ship what works, fix what's broken, build what earns

```
WHAT EARNS MONEY (Priority Order)
│
├── 1. YIELD ENGINE (Works today)
│   ├── Aave V3 on Base/Arbitrum ─── DONE
│   ├── Multi-protocol routing (Morpho, Compound) ─── BUILD
│   ├── Auto-compound ─── BUILD
│   └── Yield optimization AI (pick best risk/return) ─── BUILD
│
├── 2. DCA ENGINE (Scheduler works, execution doesn't)
│   ├── Fix: Integrate real DEX swap (Uniswap on Base) ─── FIX
│   ├── Fix: Real price feeds (Chainlink or API) ─── FIX
│   ├── Add: Multiple DCA strategies (value avg, momentum) ─── BUILD
│   └── Add: Performance tracking vs benchmarks ─── BUILD
│
├── 3. TRADING STRATEGIES (Not built)
│   ├── Simple: RSI-based buy/sell ─── BUILD
│   ├── Medium: Grid trading, mean reversion ─── BUILD
│   ├── Advanced: AI-analyzed market signals ─── BUILD
│   └── Infrastructure: DEX integration, position tracking ─── BUILD
│
├── 4. COMMERCE (Needs API keys)
│   ├── Gift card arbitrage/cashback ─── NEEDS BITREFILL KEY
│   └── Merchant deals aggregation ─── LATER
│
└── 5. AGENT MARKETPLACE (Phase 2+)
    ├── Fix: Agent execution (actually call agents) ─── FIX
    ├── Fix: Payment verification (x402) ─── NEEDS CIRCLE
    └── Pre-built agents: yield optimizer, DCA bot, news trader ─── BUILD
```

### System Architecture (What to build)

```
┌─────────────────────────────────────────────────┐
│                 NEXT.JS FRONTEND                 │
│  Dashboard │ Yield │ DCA │ Strategies │ Agents   │
│  PWA │ Push Notifications │ Mobile-first         │
└──────────────────────┬──────────────────────────┘
                       │ JWT Auth
┌──────────────────────┴──────────────────────────┐
│                  FASTAPI BACKEND                 │
│                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │  Wallet   │ │  Yield   │ │  Strategy Engine │ │
│  │  Service  │ │  Engine  │ │  (DCA, Trading)  │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │  Bridge   │ │ Commerce │ │  Agent Runtime   │ │
│  │  Service  │ │ Service  │ │  (Marketplace)   │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
│  ┌──────────────────────────────────────────────┐│
│  │  AI Layer (LangChain + Model Router)         ││
│  │  Haiku (70% simple) │ Sonnet (30% complex)   ││
│  └──────────────────────────────────────────────┘│
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────┐
│                  DATA + CHAIN                    │
│  Supabase (users, ledger, tasks, agents)         │
│  Base/Arbitrum/Solana (via Alchemy RPC)          │
│  Aave/Uniswap/DEX (yield + swaps)               │
│  Circle CCTP (bridging)                          │
└─────────────────────────────────────────────────┘
```

---

## Sprint 1: Make It Real (Construction Plan)

### Goal: Fix everything broken → ship to Railway → get first real user

#### Week 1: Fix the Broken Core

| # | Task | Why | Files |
|---|------|-----|-------|
| 1 | **Fix API send endpoint** - wire real transaction signing | Users can't send money through the API | `api/routes/transactions.py` |
| 2 | **Fix DCA execution** - integrate Uniswap V3 on Base | DCA is core money-making feature | `scheduler_executor.py` + new `uniswap_client.py` |
| 3 | **Fix bridge completion** - store message bytes, implement claim | Users lose funds on incomplete bridge | `cctp_client.py`, `bridge_tools.py` |
| 4 | **Model routing** - Haiku for simple queries, Sonnet for complex | Fix unit economics ($0.012 → $0.003/msg) | `app.py` or new `model_router.py` |

#### Week 2: Ship to Production

| # | Task | Why | Files |
|---|------|-----|-------|
| 5 | **Railway deployment verification** | Must work end-to-end on Railway | Docker configs, env vars |
| 6 | **PWA config** (service worker, manifest, install prompt) | Mobile access, push notifications | `web/next.config.ts`, new `web/public/manifest.json` |
| 7 | **Push notifications** (daily earnings) | Retention hook - "You earned $0.47 today" | New notification service |
| 8 | **Alchemy RPC setup** (free tier) | Reliable mainnet access | `config.py` env vars |

#### Week 3: First Money-Making Features Beyond Yield

| # | Task | Why | Files |
|---|------|-----|-------|
| 9 | **Pre-built DCA strategies** (weekly ETH, monthly BTC, etc.) | Users pick a strategy, not configure from scratch | New `strategies/` module |
| 10 | **Yield comparison** (Aave vs Compound vs Morpho) | AI recommends best yield | Extend `aave_client.py` pattern |
| 11 | **Performance dashboard** (your DCA vs buy-and-hold) | Shows users they're making money | `web/` earnings page enhancement |
| 12 | **Share earnings** (social proof viral mechanic) | Growth via "I earned $X this month with USDChat" | `web/` share component |

---

## What NOT to Build (Kill List)

| Feature | Why Kill It |
|---------|------------|
| Streamlit UI maintenance | Next.js is the future, don't invest in legacy |
| Generic merchant adapters | Skeleton code with empty API keys, distraction |
| Business accounts | No users yet, premature complexity |
| Card issuance research | Way too early, regulatory nightmare |
| Income routing / tax reserve | No users have income flowing through yet |
| React Native mobile app | PWA first, native later if needed |

---

## Pre-Built Money-Making Mechanisms (The Product Differentiator)

These are what make USDChat competitive. Users don't configure strategies - they pick from pre-built, tested approaches:

### Tier 1: Passive (Set and Forget)
1. **Yield Optimizer** - AI routes idle USDC to best yield across protocols
2. **Auto-Compound** - Reinvest yield earnings automatically
3. **Smart Savings** - Rules-based allocation (X% to yield, Y% liquid)

### Tier 2: Automated (Strategy Execution)
4. **DCA Strategies** - Pre-configured (Weekly ETH, Monthly BTC, Custom)
5. **Value Averaging** - Buy more when prices drop, less when prices rise
6. **Rebalancing** - Maintain target allocations automatically

### Tier 3: Active (AI-Powered)
7. **Signal Trading** - AI analyzes market sentiment, executes trades
8. **Arbitrage Scanner** - Cross-chain/DEX price differences
9. **News Trader** - Reacts to market-moving events

### Tier 4: Ecosystem (Agent Marketplace)
10. **Community Strategies** - Users share and subscribe to each other's setups
11. **Agent Bots** - Third-party money-making agents (x402 payments)
12. **Copy Trading** - Follow top performers

**Note**: Tiers 1-2 can launch with current code + DEX integration. Tiers 3-4 require more infrastructure and are post-launch.

---

## Key Technical Decisions (Updated)

| Decision | Previous | Updated | Why |
|----------|----------|---------|-----|
| North star metric | Weekly Active Creators | **Daily Active Earners** | No creators exist yet. Users who check earnings = retention |
| Build priority | Agent marketplace | **Fix broken core + yield + DCA** | Can't sell a marketplace with no working features |
| AI model | Claude Sonnet only | **Haiku (70%) + Sonnet (30%)** | Fix unit economics |
| DEX integration | None | **Uniswap V3 on Base** | Required for real DCA execution |
| Frontend | Streamlit + Next.js | **Next.js only** | Stop maintaining two frontends |
| Positioning | "AI project launchpad" | **"Wallet that earns for you"** | Matches what code actually does |

---

## Dependencies on Founder

| Action | Impact | Urgency |
|--------|--------|---------|
| Alchemy free tier signup | Reliable RPC | This week |
| Circle API credentials | x402, CCTP production | This month |
| Bitrefill API key | Gift cards | This month |
| Domain name | Professional deployment | This week |

---
