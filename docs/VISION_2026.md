# USDChat: The Money Operating System
## Internal Strategy Document — January 2026

---

# Part I: Mission & Vision

## The One-Liner
**USDChat is an AI wallet. Chat to manage your money, earn on idle funds, spend anywhere.**

## Mission Statement
Give everyone an AI that handles their money — from everyday payments to passive earnings to projects that run while you sleep. Built on USDC for instant, global, 24/7 settlement.

## Vision: Three Horizons

### Horizon 1: AI Wallet (NOW)
A self-custodial wallet where users manage USDC through natural conversation.
- "Send $50 to Alice"
- "Buy a Mullvad VPN subscription"
- "What's my balance across all chains?"

**Status:** MVP complete. Functional on Base, Arbitrum, Solana.

### Horizon 2: Financial Autopilot (NEXT)
Your money works while you don't. Idle balance earns yield, bills pay themselves, savings grow automatically.
- Idle funds earn ~4% APY (Aave, Compound)
- Recurring payments run on schedule
- Income auto-routes to savings vs spending
- Set aside % for taxes automatically

**Status:** Architecture defined. Yield integration ready.

### Horizon 3: AI Projects That Earn (FUTURE)
Connect money to your AI creations. Your AI character, bot, or agent can accept payments, run trades, or sell on your behalf.
- AI characters that accept tips or charge for access
- Trading bots on Hyperliquid, Polymarket, Pump.fun
- AI agents that sell digital goods or services

**Status:** Foundation ready (chat + wallet). Monetization rails in progress.

---

## Why This Matters

### The Macro Thesis
1. **Stablecoins won.** USDC is becoming core financial infrastructure (Visa settlement, Circle x402, GENIUS Act regulation)
2. **AI agents are coming.** Agentic AI can plan, reason, and execute multi-step financial workflows
3. **Self-custody is the future.** Regulatory clarity favors non-custodial (you control keys, no money transmitter license)
4. **24/7 settlement unlocks new models.** Businesses that couldn't exist with banking hours can now run autonomously

### The Opportunity
No one has built the operating system that combines:
- Programmable money (USDC rails)
- AI decision-making (agentic treasury)
- Self-custody (regulatory advantage)
- Multi-chain coverage (EVM + Solana)

**USDChat sits at this intersection.**

---

# Part II: Functional Architecture

## Core Capabilities Matrix

| Layer | Function | Status | Priority |
|-------|----------|--------|----------|
| **Foundation** | | | |
| Wallet Core | HD key derivation, multi-chain (EVM + Solana) | ✅ Done | — |
| Self-Custody | User controls keys, encrypted locally | ✅ Done | — |
| Chat Interface | Natural language → structured actions | ✅ Done | — |
| **Transactions** | | | |
| Send USDC | Gasless meta-transactions | ✅ Done | — |
| Receive USDC | QR codes, address display | ✅ Done | — |
| Cross-Chain | Bridge between networks | ⏳ Planned | P2 |
| Swap | USDC ↔ other tokens | ⏳ Planned | P2 |
| **Yield/Savings** | | | |
| Passive Yield | Auto-deposit to Aave/Compound | 🔧 Ready | P0 |
| Vault Selection | Route to best risk-adjusted yield | ⏳ Planned | P1 |
| Liquidity Tiers | Instant/Flex/Committed buckets | ⏳ Planned | P1 |
| **Spending** | | | |
| Gift Cards | 1000+ merchants via Bitrefill | ✅ Done | — |
| Direct Crypto Merchants | Porkbun, Mullvad, Travala | ✅ Done | — |
| Card Issuance | Virtual/physical USDC cards | ⏳ Research | P3 |
| **Automation** | | | |
| Recurring Payments | Scheduled sends/purchases | 🔧 Partial | P0 |
| Income Routing | Auto-categorize inflows | ⏳ Planned | P1 |
| Tax Reserve | Set aside % of income | ⏳ Planned | P2 |
| Bill Detection | Scan email for invoices | 🔧 Partial | P1 |
| **Business** | | | |
| Business Accounts | Separate from personal | ⏳ Planned | P2 |
| Supplier Payments | Webhook-triggered payouts | ⏳ Planned | P2 |
| Invoice Collection | Payment pages/links | ⏳ Planned | P2 |
| P&L Tracking | Auto-categorize flows | ⏳ Planned | P3 |

---

## How Money Flows

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MONEY IN                                     │
│  Deposits | Payments Received | Yield Earnings | Refunds            │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AI AUTO-ROUTING                                 │
│                                                                      │
│  Default rules (customizable):                                       │
│  • 10% → Tax savings (set aside automatically)                      │
│  • 20% → Spending (instant access)                                  │
│  • 70% → Earning (yield-bearing, same-day access)                   │
│                                                                      │
│  Smart overrides:                                                    │
│  • Bill due soon? → Keep funds liquid                               │
│  • Balance low? → Skip yield deposit                                │
│  • Unusual opportunity? → Alert you                                 │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      YOUR BALANCE                                    │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │  SPENDING    │  │   EARNING    │  │  TAX SAVINGS │               │
│  │              │  │              │  │              │               │
│  │  0% APY      │  │  3-5% APY    │  │  Set aside   │               │
│  │  Instant     │  │  Same-day    │  │  for taxes   │               │
│  │  access      │  │  withdrawal  │  │              │               │
│  │              │  │              │  │              │               │
│  │  Raw USDC    │  │  Aave/       │  │  Locked      │               │
│  │              │  │  Compound    │  │  until Q4    │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
│                                                                      │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         MONEY OUT                                    │
│                                                                      │
│  Sends | Bill Payments | Subscriptions | Purchases | Withdrawals    │
│                                                                      │
│  AI pulls from the right place:                                     │
│  • Coffee? → Spending balance                                       │
│  • Rent? → Move from Earning (scheduled ahead)                      │
│  • Emergency? → Unlock everything instantly                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Programmable Money Primitives

### 1. Yield Layer
| Provider | Type | APY | Risk | Liquidity | Integration |
|----------|------|-----|------|-----------|-------------|
| Aave V3 | Lending | 3-5% | Low | Instant | Ready |
| Compound | Lending | 3-5% | Low | Instant | Ready |
| Beefy | Auto-compound | 5-10% | Medium | Same-day | API available |
| Yearn | Vaults | 5-10% | Medium | Same-day | API available |
| Gauntlet | Curated | 6-12% | Medium | Varies | Partnership req |
| vaults.fyi | Aggregator | — | — | — | API available |

**Integration Priority:**
1. vaults.fyi API (yield discovery)
2. Beefy API (multi-chain auto-compound)
3. Aave direct (battle-tested fallback)

### 2. Settlement Layer
| Provider | Use Case | Settlement | Integration |
|----------|----------|------------|-------------|
| Circle Programmable Wallets | Embedded USDC payments | Instant | SDK |
| Circle x402 | AI/machine micropayments | Instant | HTTP 402 |
| Circle Payments Network | Cross-border B2B | Instant | Partnership |
| Visa USDC | Card rails settlement | Near-instant | Via issuers |

**Integration Priority:**
1. Circle Programmable Wallets SDK
2. x402 protocol for agent-to-agent payments

### 3. Spending Layer
| Provider | Type | Status |
|----------|------|--------|
| Bitrefill | Gift cards (1000+ brands) | ✅ Integrated |
| Direct merchants | Crypto-native (Porkbun, Mullvad) | ✅ Integrated |
| Card issuance | Virtual/physical cards | Research phase |

### 4. Automation Layer
| Capability | Description | Status |
|------------|-------------|--------|
| Recurring sends | Pay X to Y every month | Partial |
| Bill detection | Scan Gmail for invoices | Partial |
| Subscription management | Track and pay subscriptions | Planned |
| Webhook triggers | Pay supplier on order fulfillment | Planned |

---

# Part III: AI Projects That Earn

## The Thesis
You have an idea. You can describe it to AI. Now that AI can have a wallet.
**Your AI project can accept money, spend money, and make money — while you sleep.**

## How It Works

USDChat connects the two things people are already building with:
1. **AI chat** — Characters, bots, agents, assistants
2. **Money** — Payments, tips, subscriptions, trades

The result: AI projects that can monetize themselves.

## What You Can Build

| Project Type | How It Earns | Example |
|--------------|--------------|---------|
| **AI Character** | Tips, paid access, subscription | A fitness coach bot that charges $5/month |
| **Trading Bot** | Executes your strategy 24/7 | Perps on Hyperliquid, bets on Polymarket |
| **Content Agent** | Paywalled content, micropayments | AI that writes custom reports for $2 each |
| **Service Bot** | Per-task fees | AI that books appointments, finds deals |
| **Meme Coin Launcher** | Token creation + trading | Launch on Pump.fun, auto-manage liquidity |

## The Stack

```
┌─────────────────────────────────────────────────────────────────────┐
│                    YOUR AI PROJECT                                   │
│                                                                      │
│  Built with: ChatGPT, Claude, custom agent, character.ai export     │
│  Personality, knowledge, rules — all defined by you                 │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    USDChat WALLET                                    │
│                                                                      │
│  • Accept payments (tips, subscriptions, per-use fees)              │
│  • Send payments (API costs, payouts, trades)                       │
│  • Earn on idle funds (auto-yield)                                  │
│  • Execute trades (Hyperliquid, Polymarket, DEXs)                   │
│  • Follow your rules (limits, approvals, alerts)                    │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    MONEY RAILS                                       │
│                                                                      │
│  Receive:              Trade:                Send:                  │
│  • x402 micropayments  • Hyperliquid perps   • USDC transfers       │
│  • Payment links       • Polymarket bets     • Gift card purchases  │
│  • QR codes            • Pump.fun tokens     • API payments         │
│  • Subscriptions       • DEX swaps           • Payouts              │
└─────────────────────────────────────────────────────────────────────┘
```

## Example: Trading Bot

**What you define:**
- Strategy: "Buy ETH when RSI < 30, sell when RSI > 70"
- Limits: "Max $100 per trade, max $500/day"
- Platform: Hyperliquid (perps) or Uniswap (spot)

**What USDChat handles:**
- Wallet with your USDC
- Execute trades based on your rules
- Track P&L automatically
- Alert you on big moves
- Earn yield on uninvested balance

**Your involvement:** Set rules once. Check in when you want.

## Example: Paid AI Character

**What you create:**
- Personality: A sarcastic personal finance advisor
- Knowledge: Trained on your notes, favorite books
- Access model: Free preview, $3/month for full access

**What USDChat handles:**
- Payment link / subscription management
- Accept USDC (or card via onramp)
- Deposit earnings to yield
- Pay out to your main wallet weekly

**Your involvement:** Create the character. Collect the earnings.

---

# Part IV: Technical Architecture

## Current Stack (MVP)

```
┌────────────────────────────────────────┐
│         Frontend (Streamlit)           │
│  Chat UI | Sidebar | Modals | Settings │
└───────────────────┬────────────────────┘
                    │
┌───────────────────┴────────────────────┐
│           Business Logic               │
│  WalletMgr | ChainUtils | SettingsMgr  │
│  BitrefillAPI | EmailMgr | LangChain   │
└───────────────────┬────────────────────┘
                    │
┌───────────────────┴────────────────────┐
│         External Services              │
│  Supabase | EVM RPCs | Solana RPC      │
│  Gemini/Claude/GPT | Bitrefill         │
└────────────────────────────────────────┘
```

## Target Architecture (Horizon 2-3)

```
┌─────────────────────────────────────────────────────────────────────┐
│                       CLIENT LAYER                                   │
│                                                                      │
│   Web App          Mobile App         API/SDK           Agent API   │
│  (Streamlit →     (React Native      (for devs        (for AI      │
│   Next.js)         or Flutter)        building on)     agents)     │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────────────┐
│                       API GATEWAY                                    │
│                                                                      │
│  Auth | Rate Limiting | Routing | Webhooks | WebSockets             │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   WALLET     │    │   AUTOPILOT  │    │  AI PROJECTS │
│   SERVICE    │    │   SERVICE    │    │   SERVICE    │
│              │    │              │    │              │
│ • HD keys    │    │ • Yield mgmt │    │ • Characters │
│ • Sign txns  │    │ • Routing    │    │ • Trading    │
│ • Multi-chain│    │ • Scheduling │    │ • Payments   │
│ • Encryption │    │ • Tax reserve│    │ • Rules      │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BLOCKCHAIN LAYER                                  │
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  Base       │  │  Arbitrum   │  │  Solana     │  │  Ethereum   │ │
│  │  (primary)  │  │             │  │             │  │  (fallback) │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
│                                                                      │
│  Smart Contracts:                                                    │
│  • ERC-4626 vault adapters                                          │
│  • Meta-transaction relayer                                         │
│  • Payment splitter                                                 │
└─────────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────────────┐
│                    INTEGRATION LAYER                                 │
│                                                                      │
│  Yield:           Payments:         Commerce:         AI:           │
│  • vaults.fyi     • Circle SDK      • Printful        • Claude      │
│  • Beefy API      • x402            • Shopify         • GPT-4       │
│  • Aave direct    • Stripe          • Bitrefill       • Gemini      │
└─────────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────────────┐
│                    DATA LAYER                                        │
│                                                                      │
│  Supabase:                Redis:              Blob Storage:         │
│  • Users                  • Sessions          • Receipts            │
│  • Wallets                • Rate limits       • Invoices            │
│  • Transactions           • Cache             • Generated assets    │
│  • Schedules                                                        │
│  • Business configs                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Primary chain | Base | Cheapest gas, Circle native, Coinbase ecosystem |
| Vault standard | ERC-4626 | Universal interface, composable |
| Meta-transactions | Gelato/Biconomy | Gasless UX, battle-tested |
| Account abstraction | ERC-4337 | Future-proof, smart wallet features |
| AI framework | LangChain + tool calling | Structured actions, multi-model |
| Frontend (future) | Next.js | SSR, better mobile, API routes |
| Mobile | React Native | Code sharing, native performance |

---

# Part V: Go-to-Market

## Target Users (Segmented)

### Segment 1: Crypto-Native Individuals
**Profile:** Already holds USDC, uses DeFi occasionally, wants simpler UX
**Pain:** Managing multiple wallets, complex DeFi interfaces, gas fees
**Value prop:** "Chat to manage your money. Earn yield automatically."
**Acquisition:** Twitter/X, crypto podcasts, DeFi forums

### Segment 2: Remote Workers / Freelancers
**Profile:** Gets paid in crypto or wants to, pays for SaaS/tools
**Pain:** Converting crypto to pay bills, managing international payments
**Value prop:** "Get paid in USDC, pay everything with one wallet."
**Acquisition:** Indie Hackers, remote work communities, freelancer platforms

### Segment 3: Micro-Entrepreneurs
**Profile:** Side hustles, dropshipping, print-on-demand, affiliate marketing
**Pain:** Payment processing fees, cash flow management, manual operations
**Value prop:** "Automate your business finances. Treasury that runs itself."
**Acquisition:** E-commerce communities, YouTube business channels

### Segment 4: AI Creators
**Profile:** Building AI characters, bots, or agents. Wants to monetize their creations.
**Value prop:** "Give your AI a wallet. Let it accept tips, charge for access, or run trades."
**Acquisition:** Character.ai community, AI Twitter, Discord servers, YouTube tutorials

## PMF Signals to Track

| Signal | Metric | Target |
|--------|--------|--------|
| Activation | Wallet created + first deposit | >50% of signups |
| Engagement | Messages per user per week | >10 |
| Retention | Weekly active users | >40% at week 4 |
| Revenue | Avg revenue per user per month | >$1 |
| Referral | Organic signups from existing users | >20% |
| Yield adoption | % with yield enabled | >30% |

## Competitive Positioning

```
                        HIGH AUTOMATION
                              ▲
                              │
                              │    ┌─────────────┐
                              │    │             │
                              │    │  USDChat    │
                              │    │  (Target)   │
                              │    │             │
                              │    └─────────────┘
          ┌─────────────┐     │
          │ Traditional │     │
          │ Banks       │     │
          │ (Schwab,    │     │
          │  Fidelity)  │     │
          └─────────────┘     │
                              │
CUSTODIAL ◄───────────────────┼───────────────────► SELF-CUSTODY
                              │
          ┌─────────────┐     │     ┌─────────────┐
          │ Coinbase    │     │     │  MetaMask   │
          │ Wallet      │     │     │  Phantom    │
          │             │     │     │  Rabby      │
          └─────────────┘     │     └─────────────┘
                              │
                              │
                              ▼
                        LOW AUTOMATION
```

**Our position:** Self-custody (regulatory advantage) + High automation (differentiation)

## Deck Narrative (for fundraising)

### Slide 1: The Problem
Money doesn't work for you.
- Idle cash sits earning nothing
- Paying bills is manual and annoying
- No easy way to get paid internationally
- Can't connect money to your AI projects

### Slide 2: The Solution
USDChat: AI Wallet
- Chat to send, spend, and manage money
- Idle balance earns ~4% APY automatically
- Pay for anything — gift cards, domains, VPNs
- Connect your AI projects to real payments

### Slide 3: Why Now
- Stablecoins are becoming infrastructure (Visa, PayPal, Klarna)
- AI agents can now execute multi-step financial workflows
- Regulatory clarity (GENIUS Act) favors self-custody
- 24/7 settlement enables new business models

### Slide 4: Traction
- [X] users
- [X] transaction volume
- [X] yield TVL
- [X] AI messages processed

### Slide 5: Business Model
1. Transaction fees (0.2% avg)
2. Yield spread (70/30 split)
3. Premium tier ($9/mo)
4. Commerce revenue (future)

### Slide 6: Market Size
- Self-custody wallet market: $500M (2024)
- Stablecoin market cap: $150B+ (2026)
- AI-powered fintech: Emerging, high growth
- Our slice: AI × self-custody × automation = blue ocean

### Slide 7: Roadmap
- Q1 2026: Yield integration live, security hardened
- Q2 2026: Mobile app, recurring payments
- Q3 2026: Trading bots (Hyperliquid, Polymarket)
- Q4 2026: AI project monetization (characters, agents)

### Slide 8: Team
[Team bios]

### Slide 9: Ask
Raising $[X] for:
- Engineering (yield, mobile, commerce)
- Security audits
- Go-to-market

---

# Part VI: Roadmap

## 2026 Q1 (Now → March)

### Priority: Yield + Polish

| Item | Owner | Status |
|------|-------|--------|
| Fix security issues (cookie key removal, auto-lock) | Eng | P0 |
| Activate yield farming (Aave integration) | Eng | P0 |
| Persist scheduled payments to DB | Eng | P0 |
| vaults.fyi API integration | Eng | P1 |
| Beefy API integration | Eng | P1 |
| Email verification | Eng | P1 |
| Transaction receipts/confirmations | Eng | P1 |
| UI polish round (current work) | Design | P1 |

**Milestone:** Yield earning live, security hardened

## 2026 Q2 (April → June)

### Priority: Mobile + Automation

| Item | Owner | Status |
|------|-------|--------|
| React Native mobile app | Eng | P0 |
| Recurring payments (full implementation) | Eng | P0 |
| Income routing rules | Eng | P1 |
| Tax reserve automation | Eng | P1 |
| Bill detection from email | Eng | P2 |
| Premium tier launch | Product | P1 |

**Milestone:** Mobile app in app stores, recurring payments live

## 2026 Q3 (July → September)

### Priority: Trading Bots

| Item | Owner | Status |
|------|-------|--------|
| Hyperliquid integration | Eng | P0 |
| Polymarket integration | Eng | P0 |
| Trading rules engine | Eng | P1 |
| P&L tracking dashboard | Eng | P1 |
| Pump.fun integration | Eng | P2 |
| DEX swap integration | Eng | P2 |

**Milestone:** Users can run trading strategies through USDChat

## 2026 Q4 (October → December)

### Priority: AI Project Monetization

| Item | Owner | Status |
|------|-------|--------|
| AI character wallet linking | Eng | P0 |
| Payment links / tips | Eng | P0 |
| Subscription management | Eng | P1 |
| x402 micropayments | Eng | P1 |
| Character marketplace | Eng | P2 |
| Card issuance (research → pilot) | Eng | P2 |

**Milestone:** First AI characters earning money for their creators

---

# Part VII: Risk Register

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| Smart contract exploit (yield vaults) | Critical | Low | Insurance (Nexus), diversification, circuit breakers |
| Regulatory action (securities, MTL) | High | Medium | Non-custodial design, legal counsel, geo-blocking |
| User funds lost (key management) | Critical | Low | Local encryption, no cloud key storage, backup reminders |
| AI hallucination (wrong transaction) | High | Medium | Confirmation required, amount limits, undo window |
| Competition (Coinbase adds AI) | Medium | High | Speed, specialization, community, open source |
| Economic unsustainability | High | Medium | Yield integration, fee adjustment, premium tier |

---

# Part VIII: Success Metrics

## North Star
**Monthly Active Treasuries (MAT):** Wallets with >$100 and >1 transaction/month

## Layer 1: Growth
| Metric | Current | Q2 Target | Q4 Target |
|--------|---------|-----------|-----------|
| Registered users | — | 5,000 | 25,000 |
| MAT | — | 1,000 | 5,000 |
| Transaction volume (monthly) | — | $500K | $5M |

## Layer 2: Engagement
| Metric | Current | Q2 Target | Q4 Target |
|--------|---------|-----------|-----------|
| Messages per user/week | — | 15 | 20 |
| Yield adoption rate | 0% | 30% | 50% |
| Automation rate (scheduled/recurring) | — | 10% | 25% |

## Layer 3: Revenue
| Metric | Current | Q2 Target | Q4 Target |
|--------|---------|-----------|-----------|
| Monthly revenue | — | $5K | $50K |
| ARPU | — | $1 | $2 |
| Yield TVL | $0 | $1M | $10M |

## Layer 4: Retention
| Metric | Current | Q2 Target | Q4 Target |
|--------|---------|-----------|-----------|
| Week 1 retention | — | 60% | 70% |
| Week 4 retention | — | 35% | 45% |
| Month 3 retention | — | 25% | 35% |

---

# Part IX: Open Questions

## Strategic
1. **Build vs partner for card issuance?** (High cost to build, but high value)
2. **Open source the wallet?** (Community growth vs competitive moat)
3. **Geographic focus?** (US-first vs global-first, regulatory implications)

## Product
1. **Default yield on or off?** (Adoption vs trust)
2. **Business accounts: separate app or same?** (Simplicity vs complexity)
3. **Agent API: public or gated?** (Ecosystem vs quality control)

## Technical
1. **Account abstraction now or later?** (Future-proof vs shipping speed)
2. **Own relayer or third-party?** (Control vs complexity)
3. **Multi-tenant smart contracts or per-user?** (Gas efficiency vs isolation)

---

# Part X: Document Index

## Existing Docs
| Document | Purpose | Status |
|----------|---------|--------|
| BUSINESS_OVERVIEW.txt | High-level product description | Current |
| MONETIZATION_STRATEGY.md | Yield integration details | Current |
| EXECUTIVE_REVIEW_2026-01.md | Multi-stakeholder assessment | Current |
| ROADMAP_FEATURES.md | Feature backlog | Needs update |
| SECURITY_TODO.md | Security action items | Active |

## Future Docs Needed
| Document | Purpose | Priority |
|----------|---------|----------|
| API_SPECIFICATION.md | Public API documentation | P1 |
| YIELD_INTEGRATION.md | Technical yield implementation | P0 |
| COMMERCE_PLATFORM.md | Autonomous business architecture | P2 |
| MOBILE_APP.md | React Native architecture | P1 |
| COMPLIANCE_PLAYBOOK.md | Regulatory strategy by jurisdiction | P1 |
| SECURITY_ARCHITECTURE.md | Full security model | P0 |
| AGENT_SDK.md | SDK for AI agent developers | P2 |

---

# Appendix A: Competitive Intelligence

## Direct Competitors
| Product | Strengths | Weaknesses | Our Advantage |
|---------|-----------|------------|---------------|
| Coinbase Wallet | Brand, fiat on-ramp | No AI, no automation | AI-native, automation-first |
| MetaMask | Distribution, ecosystem | Complex UX, no AI | Simplicity, natural language |
| Phantom | Beautiful UX, Solana-native | Limited to Solana, no AI | Multi-chain, AI |
| Argent | Smart wallet, social recovery | Limited chains, no AI | Multi-chain, AI, commerce |
| Rainbow | Great mobile UX | No AI, limited features | AI, automation, yield |

## Adjacent Competitors
| Product | Overlap | Differentiation |
|---------|---------|-----------------|
| Robinhood | Simple investing | We're self-custody, crypto-native |
| Cash App | P2P payments | We're multi-chain, yield, automation |
| Mercury | Business banking | We're crypto-native, self-custody |
| Brex | Business finance | We're for individuals + micro-biz |

## Emerging Competitors
| Product | Threat Level | Response |
|---------|--------------|----------|
| ChatGPT + plugins | Medium | They don't have wallet, we do |
| Crypto wallets adding AI | High | Ship fast, specialize deep |
| Banks adding stablecoins | Low | Self-custody moat |

---

# Appendix B: Integration Priority Matrix

## Yield Integrations
| Integration | Effort | Impact | Priority |
|-------------|--------|--------|----------|
| vaults.fyi API | Low | High | P0 |
| Beefy API | Low | High | P0 |
| Aave direct | Medium | Medium | P1 |
| Yearn API | Medium | Medium | P2 |
| Gauntlet | High | High | P2 (partnership) |

## Payment Integrations
| Integration | Effort | Impact | Priority |
|-------------|--------|--------|----------|
| Circle Programmable Wallets | Medium | High | P1 |
| Circle x402 | Low | Medium | P2 |
| Stripe (fiat collection) | Medium | High | P1 |

## AI Project Integrations
| Integration | Effort | Impact | Priority |
|-------------|--------|--------|----------|
| Hyperliquid API | Medium | High | P0 |
| Polymarket API | Medium | High | P0 |
| Pump.fun API | Low | Medium | P1 |
| x402 micropayments | Medium | High | P1 |

---

*Document version: 1.1*
*Last updated: January 2026*
*Owner: Founding Team*
*Revision notes: Simplified language, focused Horizon 3 on AI projects that earn*
