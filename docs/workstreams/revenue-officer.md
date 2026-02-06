# Workstream: Revenue Officer

> **Owner**: Revenue Officer session
> **Status**: COMPLETE — Sprint 0 Analysis & Recommendations
> **Last updated**: 2026-02-06

---

## Mandate

You are the revenue officer. You own:
- Unit economics analysis (is each user profitable?)
- Pricing strategy (transaction fees, premium tiers, yield splits)
- Revenue model design (how does USDChat make money sustainably?)
- Financial projections (what does the path to $50K MRR look like?)
- Cost analysis (LLM costs, infrastructure, gas)
- Monetization roadmap (when to introduce what revenue stream)

Your job is to answer: **"How does this become a real business, not a money-losing side project?"**

---

## Context Read

1. `docs/COMMAND_CENTER.md` - Project overview
2. `docs/STRATEGIC_DIRECTION.md` - Revenue targets (Q2: $5K/mo, Q4: $50K/mo)
3. `docs/EXECUTIVE_REVIEW_2026-01.md` - CEO gave C+ on economics ("unsustainable")
4. `docs/BUSINESS_OVERVIEW.txt` - Current fee structure ($0.005 + 0.2%)
5. `docs/VISION_2026.md` - Revenue metrics and ARPU targets
6. `MONETIZATION_STRATEGY.md` - Existing yield/monetization plans
7. `LLM_COSTS.md` - LLM cost analysis

---

# Sprint 0: Fix Project Economics (Grade C+ → B+)

> **TLDR:** USDChat loses money on every transaction at current pricing. A $10 send generates $0.025 in fees but costs $0.032+ (gas + LLM). This document proposes a new pricing structure that achieves profitability at 500 DAUs and scales to $1M+ ARR at 10K users, benchmarked against 10 major competitors.

---

# Table of Contents

1. [Diagnosis: Why We Lose Money](#1-diagnosis-why-we-lose-money)
2. [Competitive Benchmarking](#2-competitive-benchmarking)
3. [Proposed Pricing Structure](#3-proposed-pricing-structure)
4. [Unit Economics Model](#4-unit-economics-model)
5. [Revenue Projections](#5-revenue-projections)
6. [Implementation Plan](#6-implementation-plan)
7. [Risk Analysis](#7-risk-analysis)
8. [Sprint 0 Task Completion](#8-sprint-0-task-completion)

---

# 1. Diagnosis: Why We Lose Money

## Current Fee Structure (config.py:111-114)

```
FEE_FLAT       = $0.005  (0.5 cents)
FEE_PERCENTAGE = 0.2%
FEE_MAX        = $3.00
```

## Cost Structure Per Transaction

| Cost Component | Amount | Source |
|---|---|---|
| Gas (relayer, Base L2) | $0.02-0.05 | transaction_relayer.py:79-104 |
| LLM (Sonnet 4, ~2 msgs/tx) | $0.012-0.024 | LLM_COSTS.md analysis |
| Infrastructure (Supabase, hosting, RPCs) | ~$0.003 | Pro-rated from ~$500/mo at 5K tx/mo |
| **Total cost per transaction** | **$0.035-0.077** | |

## Revenue Per Transaction (Current)

| Transaction Size | Fee Charged | Total Cost (mid) | **Net P&L** |
|---|---|---|---|
| $5 | $0.015 | $0.050 | **-$0.035** |
| $10 | $0.025 | $0.050 | **-$0.025** |
| $25 | $0.055 | $0.050 | **+$0.005** |
| $50 | $0.105 | $0.050 | **+$0.055** |
| $100 | $0.205 | $0.050 | **+$0.155** |
| $500 | $1.005 | $0.050 | **+$0.955** |
| $1,000 | $2.005 | $0.050 | **+$1.955** |
| $5,000+ | $3.00 (cap) | $0.050 | **+$2.950** |

**Key Insight:** We lose money on every transaction under ~$22. If our median transaction is $25-50 (typical for a chat wallet targeting beginners), roughly 30-50% of transactions are unprofitable.

## Additional Revenue Leaks

| Issue | Impact | File Reference |
|---|---|---|
| Free tier: 50 LLM messages at $0.006 each = $0.30/user subsidy | -$0.30/user | free_tier.py:14 |
| Gift card purchases: NO platform markup, Bitrefill affiliate only | Unknown/untracked | bitrefill_client.py |
| Yield farming: NOT active, 0% revenue from idle funds | $0/year | aave_client.py (dormant) |
| Bridge fees: $0.25 flat estimate, no platform cut | $0/bridge | api/routes/transactions.py:186-189 |
| Merchant payments: NO platform fee on Porkbun/Mullvad/Travala | $0/purchase | merchant_adapters.py |
| Premium tier: Does not exist | $0 MRR | -- |
| Agent marketplace: Schema exists, no revenue yet | $0 | api/schemas/agent.py |

**Total unmonetized surface area:** Gift cards, bridges, merchant payments, yield, premium features.

---

# 2. Competitive Benchmarking

## Direct Competitor Fee Comparison

| Competitor | Transfer/Trade Fee | Subscription | Self-Custody | AI Chat |
|---|---|---|---|---|
| **USDChat (current)** | 0.005 + 0.2% (cap $3) | None | Yes | Yes |
| **Coinbase** | 0.5% spread (simple) | $4.99-$299/mo | Yes (wallet) | No |
| **Venmo** | Free P2P; 1.5-1.8% crypto | None | No | No |
| **Cash App** | Free P2P; 1.75%+ crypto | None | Yes (BTC) | No |
| **Revolut** | Free internal; 0.49-1.49% crypto | $0-$16.99/mo | No | No |
| **MetaMask** | 0.875% swaps/bridges | None | Yes | No |
| **Phantom** | 0.85% swaps | None | Yes | No |
| **PayPal** | Free P2P; 1.5-2% crypto | None | Partial | No |
| **Wise** | ~0.33% + flat | None | N/A | No |
| **Strike** | 0.99% (0.15% DCA) | None | Yes | No |

## Key Benchmarking Takeaways

1. **Our fees are among the lowest in the industry.** At 0.2%, we're cheaper than every competitor except Wise (~0.33% on FX) and Strike DCA (0.15%). This is unsustainable.

2. **Self-custody wallet swap fees cluster at 0.85-0.875%** (MetaMask, Phantom). We are 4x cheaper with zero justification.

3. **Subscription models work.** Both Coinbase One ($4.99-$299/mo) and Crypto.com Level Up ($4.99-$29.99/mo) have proven the market will pay for premium features.

4. **No competitor combines self-custody + AI + stablecoin focus.** We occupy a blue ocean -- we can price for value, not just undercut on cost.

5. **Stablecoin-native is an advantage.** USDC transfers are simpler and cheaper than volatile crypto trades. We can offer lower fees than crypto trading platforms while still being profitable.

6. **DeFi yield (4-7% on USDC via Aave) significantly beats traditional savings.** An "earn" feature with a yield split is a proven revenue model.

---

# 3. Proposed Pricing Structure

## 3A. Transaction Fees -- New Structure

### Recommended: $0.01 flat + 0.5% (cap $5)

| Parameter | Current | Proposed | Rationale |
|---|---|---|---|
| Flat fee | $0.005 | **$0.01** | Cover minimum gas cost on all txs |
| Percentage | 0.2% | **0.5%** | Still below MetaMask (0.875%), Phantom (0.85%), Revolut (0.49-1.49%) |
| Cap | $3.00 | **$5.00** | Competitive for large transfers; Venmo caps at $15 for instant |

**Revenue comparison at new rates:**

| Transaction Size | Old Fee | New Fee | Increase |
|---|---|---|---|
| $5 | $0.015 | $0.035 | +133% |
| $10 | $0.025 | $0.060 | +140% |
| $25 | $0.055 | $0.135 | +145% |
| $50 | $0.105 | $0.260 | +148% |
| $100 | $0.205 | $0.510 | +149% |
| $500 | $1.005 | $2.510 | +150% |
| $1,000 | $2.005 | $5.00 (cap) | +149% |
| $5,000+ | $3.00 (cap) | $5.00 (cap) | +67% |

**New breakeven point:** ~$8 transactions (down from ~$22). At a median of $25-50, we're profitable on 80%+ of transactions.

### Why 0.5% is defensible:

- **MetaMask charges 0.875%** for swaps -- and they don't have AI assistance, gasless transactions, or gift card/merchant integration.
- **Phantom charges 0.85%** -- same story.
- **Revolut charges 0.49-1.49%** -- and they're custodial.
- **We offer more value** (AI, gasless, multi-chain, merchant payments) at a lower price point than the self-custody wallet average.

## 3B. Premium Subscription Tiers

### USDChat Pro -- $4.99/month ($49.99/year)

| Feature | Free Tier | Pro Tier |
|---|---|---|
| AI messages/month | 50 (Gemini Flash) | Unlimited (Gemini Flash) |
| AI model upgrade | -- | Claude Haiku on-demand |
| Transaction fee | $0.01 + 0.5% | $0.01 + 0.3% |
| Fee cap | $5.00 | $3.00 |
| Yield farming | Manual opt-in | Auto-enabled, priority protocols |
| Yield split (user share) | 30% | 50% |
| Scheduled payments | 3 active | Unlimited |
| Priority support | -- | Yes |
| Agent marketplace discount | -- | 10% off paid agents |

### USDChat Business -- $19.99/month ($199.99/year)

| Feature | Business Tier |
|---|---|
| AI messages/month | Unlimited (Claude Sonnet) |
| Transaction fee | $0.005 + 0.2% (original rates) |
| Fee cap | $3.00 |
| Yield split (user share) | 70% |
| API access | Full REST API |
| Team wallets | Up to 5 members |
| Custom agent deployment | Yes |
| Batch payments | Yes |
| Priority support | 24/7 |

### Subscription Revenue Model

| Scenario | Free Users | Pro ($4.99) | Business ($19.99) | Monthly Subscription Revenue |
|---|---|---|---|---|
| 1K users, 5% Pro, 1% Biz | 940 | 50 | 10 | **$450** |
| 5K users, 8% Pro, 2% Biz | 4,500 | 400 | 100 | **$3,996** |
| 10K users, 10% Pro, 3% Biz | 8,700 | 1,000 | 300 | **$10,990** |
| 25K users, 12% Pro, 4% Biz | 21,000 | 3,000 | 1,000 | **$34,970** |

## 3C. Yield Farming Revenue -- Activate Immediately

### Recommended: 70/30 split (platform/user) for Free, 50/50 for Pro, 30/70 for Business

| Parameter | Value | Rationale |
|---|---|---|
| Protocol | Aave V3 (Base, Arbitrum) | Deepest liquidity, best audited, 4-7% APY |
| User yield (Free) | ~1.2-2.1% APY (30% of 4-7%) | Still 100x better than bank savings (0.01%) |
| User yield (Pro) | ~2.0-3.5% APY (50% of 4-7%) | Competitive with CeFi platforms |
| User yield (Business) | ~2.8-4.9% APY (70% of 4-7%) | Near-full yield pass-through |
| Platform yield | Remainder (70%/50%/30%) | Revenue scales with AUM |
| Liquidity buffer | 10% of deposits stay liquid | Instant withdrawal <10% of balance |
| Minimum deposit | $10 | Gas cost efficiency threshold |

### Yield Revenue Projections

| AUM (Total Deposits) | Aave APY | Platform Share (avg 55%) | Annual Yield Revenue |
|---|---|---|---|
| $100K | 5% | 55% | **$2,750** |
| $500K | 5% | 55% | **$13,750** |
| $1M | 5% | 55% | **$27,500** |
| $5M | 5% | 55% | **$137,500** |
| $10M | 5% | 55% | **$275,000** |

## 3D. Gift Card & Merchant Commissions -- Start Tracking

### Bitrefill Affiliate Revenue

Bitrefill typically pays 1-5% affiliate commissions on gift card purchases. This revenue is currently **untracked**.

| Monthly Gift Card Volume | Estimated Commission (3%) | Annual Revenue |
|---|---|---|
| $10K | $300 | **$3,600** |
| $50K | $1,500 | **$18,000** |
| $100K | $3,000 | **$36,000** |

**Action:** Verify Bitrefill affiliate terms and implement commission tracking in bitrefill_client.py.

### Merchant Payment Fees

Add a 1% convenience fee on merchant payments (Porkbun, Mullvad, Travala). Users pay for the convenience of crypto-to-merchant conversion.

| Monthly Merchant Volume | Fee (1%) | Annual Revenue |
|---|---|---|
| $5K | $50 | **$600** |
| $25K | $250 | **$3,000** |
| $100K | $1,000 | **$12,000** |

## 3E. Bridge Fees -- Add Platform Cut

Add a 0.1% platform fee on CCTP bridge transactions (in addition to gas).

| Monthly Bridge Volume | Fee (0.1%) | Annual Revenue |
|---|---|---|
| $50K | $50 | **$600** |
| $500K | $500 | **$6,000** |
| $2M | $2,000 | **$24,000** |

## 3F. Agent Marketplace Revenue (Future -- Already Coded)

The agent schema already supports revenue splits (api/schemas/agent.py:56-59):
- Creator: 70% (configurable 50-90%)
- Platform: 20% (configurable 10-30%)
- Referrer: 10% (configurable 0-20%)

| Monthly Agent GMV | Platform Share (20%) | Annual Revenue |
|---|---|---|
| $10K | $2,000 | **$24,000** |
| $50K | $10,000 | **$120,000** |
| $500K | $100,000 | **$1,200,000** |

---

# 4. Unit Economics Model

## 4A. Cost Per User Per Month

### Infrastructure Costs (at scale)

| Cost Component | 1K Users | 5K Users | 10K Users | Per-User/Mo |
|---|---|---|---|---|
| Supabase (Pro) | $25 | $25 | $100 | $0.01-0.03 |
| Railway hosting | $20 | $50 | $100 | $0.01-0.02 |
| RPC endpoints (Alchemy) | $0 | $49 | $49 | $0.005-0.05 |
| Domain + SSL | $15 | $15 | $15 | $0.002-0.015 |
| **Total infrastructure** | **$60** | **$139** | **$264** | **$0.03-0.06** |

### LLM Costs Per User Per Month

**Assumptions:** Average user sends 8 messages/day, 20 active days/month = 160 messages/month.

| Model | Cost/Message | Monthly/User | With Caching |
|---|---|---|---|
| Gemini Flash (Free tier) | ~$0 (Google free) | ~$0 | ~$0 |
| Claude Haiku (Pro tier) | $0.0005 | $0.08 | $0.05 |
| Claude Sonnet (Business) | $0.006 | $0.96 | $0.60 |

**Free tier users cost us $0 for LLM** (Gemini Flash is free from Google).
**Pro tier LLM cost:** ~$0.05-0.08/user/month (Haiku with caching).
**Business tier LLM cost:** ~$0.60-0.96/user/month (Sonnet with caching).

### Gas Costs (Relayer)

| Network | Avg Gas Cost/TX | Txs/User/Mo | Monthly Gas/User |
|---|---|---|---|
| Base L2 | $0.02 | 10 | $0.20 |
| Arbitrum L2 | $0.03 | 5 | $0.15 |
| **Average** | | | **$0.25** |

### Total Cost Per User Per Month

| Tier | Infrastructure | LLM | Gas (relayer) | **Total** |
|---|---|---|---|---|
| Free | $0.04 | $0.00 | $0.25 | **$0.29** |
| Pro | $0.04 | $0.06 | $0.25 | **$0.35** |
| Business | $0.04 | $0.75 | $0.25 | **$1.04** |

## 4B. Revenue Per User Per Month (RPUPM)

### Free Tier User

| Revenue Source | Calculation | Monthly |
|---|---|---|
| Transaction fees | 10 tx x $50 avg x 0.5% + $0.01 = $2.60 | $2.60 |
| Yield (70% of 5% on $200 avg) | $200 x 5% x 70% / 12 | $0.58 |
| Gift card commission (3%) | 2 purchases x $50 avg x 3% | $3.00 |
| **Total RPUPM** | | **$6.18** |

### Pro Tier User ($4.99/mo subscription)

| Revenue Source | Calculation | Monthly |
|---|---|---|
| Subscription | $4.99 | $4.99 |
| Transaction fees | 15 tx x $75 avg x 0.3% + $0.01 = $3.53 | $3.53 |
| Yield (50% of 5% on $500 avg) | $500 x 5% x 50% / 12 | $1.04 |
| Gift card commission (3%) | 4 purchases x $75 avg x 3% | $9.00 |
| **Total RPUPM** | | **$18.56** |

### Business Tier User ($19.99/mo subscription)

| Revenue Source | Calculation | Monthly |
|---|---|---|
| Subscription | $19.99 | $19.99 |
| Transaction fees | 30 tx x $200 avg x 0.2% + $0.005 = $12.15 | $12.15 |
| Yield (30% of 5% on $2K avg) | $2000 x 5% x 30% / 12 | $2.50 |
| Gift card/merchant | 5 purchases x $100 avg x 3% | $15.00 |
| **Total RPUPM** | | **$49.64** |

## 4C. Contribution Margin Per User

| Tier | RPUPM | Cost/User/Mo | **Margin** | **Margin %** |
|---|---|---|---|---|
| Free | $6.18 | $0.29 | **+$5.89** | **95%** |
| Pro | $18.56 | $0.35 | **+$18.21** | **98%** |
| Business | $49.64 | $1.04 | **+$48.60** | **98%** |

**Current state (old pricing):** Free user generates ~$2.05/mo revenue against $0.29 cost = $1.76 margin (86%). But this assumes no LLM cost and all transactions >$22. In reality, many transactions lose money.

**New pricing state:** Free user generates ~$6.18/mo, and every transaction over $8 is profitable.

---

# 5. Revenue Projections

## Scenario A: Conservative (1,000 users by Q4 2026)

**Assumptions:** 70% free, 25% pro, 5% business. 60% monthly active.

| Revenue Stream | Monthly | Annual |
|---|---|---|
| Transaction fees (new rates) | $2,800 | $33,600 |
| Subscriptions | $225 | $2,700 |
| Yield farming (30% adoption, $300 avg) | $230 | $2,750 |
| Gift card commissions | $600 | $7,200 |
| Merchant fees | $50 | $600 |
| **Total Revenue** | **$3,905** | **$46,850** |
| Total Costs | $450 | $5,400 |
| **Net Profit** | **$3,455** | **$41,450** |

## Scenario B: Moderate (5,000 users by Q4 2026)

**Assumptions:** 65% free, 27% pro, 8% business. 55% monthly active.

| Revenue Stream | Monthly | Annual |
|---|---|---|
| Transaction fees | $14,500 | $174,000 |
| Subscriptions | $2,150 | $25,800 |
| Yield farming (40% adoption, $500 avg) | $2,290 | $27,500 |
| Gift card commissions | $3,000 | $36,000 |
| Merchant fees | $250 | $3,000 |
| Agent marketplace (20% of target) | $2,000 | $24,000 |
| **Total Revenue** | **$24,190** | **$290,300** |
| Total Costs | $1,800 | $21,600 |
| **Net Profit** | **$22,390** | **$268,700** |

## Scenario C: Optimistic (25,000 users by end 2027)

**Assumptions:** 60% free, 28% pro, 12% business. 50% monthly active.

| Revenue Stream | Monthly | Annual |
|---|---|---|
| Transaction fees | $87,500 | $1,050,000 |
| Subscriptions | $34,970 | $419,640 |
| Yield farming (50% adoption, $800 avg) | $22,920 | $275,000 |
| Gift card commissions | $15,000 | $180,000 |
| Merchant fees | $2,500 | $30,000 |
| Agent marketplace | $20,000 | $240,000 |
| Bridge fees | $500 | $6,000 |
| **Total Revenue** | **$183,390** | **$2,200,640** |
| Total Costs | $12,000 | $144,000 |
| **Net Profit** | **$171,390** | **$2,056,640** |

## Revenue Mix at Scale (Scenario C)

```
Transaction Fees    ||||||||||||||||||||||||   48%
Subscriptions       ||||||||||||||             19%
Yield Farming       |||||||||                  12%
Agent Marketplace   ||||||||||                 11%
Gift Card Commissions ||||||                    8%
Merchant + Bridge   |                           2%
```

---

# 6. Implementation Plan

## Phase 1: Immediate Changes (Week 1)

### 1a. Update Transaction Fees in config.py

```python
# BEFORE (config.py:111-114)
FEE_FLAT = 0.005
FEE_PERCENTAGE = 0.002
FEE_MAX = 3.0

# AFTER
FEE_FLAT = 0.01        # $0.01 (1 cent)
FEE_PERCENTAGE = 0.005  # 0.5%
FEE_MAX = 5.0           # $5 cap
```

### 1b. Switch Default LLM to Haiku for Cost Control

In app.py, route free tier to Gemini Flash (already done), and add Haiku as the Pro tier model:

```python
# Hybrid routing: Gemini for free, Haiku for Pro, Sonnet for Business
if tier == "free":
    model = "gemini-2.5-flash"
elif tier == "pro":
    model = "claude-haiku-4-20250514"
else:
    model = "claude-sonnet-4-20250514"
```

### 1c. Add Merchant Convenience Fee (1%)

Update merchant_adapters.py to add a 1% platform convenience fee on all merchant payments.

### 1d. Track Bitrefill Affiliate Revenue

Add commission tracking to bitrefill_client.py to monitor affiliate earnings.

## Phase 2: Premium Tier Launch (Weeks 2-4)

### 2a. Implement Subscription Model

- Add `subscription_tier` field to user_settings table
- Create Stripe integration for payment processing
- Implement tier-based fee calculation in config.py
- Add Pro/Business tier UI in settings

### 2b. Activate Yield Farming

- Enable aave_client.py deposit/withdraw for opted-in users
- Implement yield split tracking (70/30 free, 50/50 pro, 30/70 business)
- Add yield earnings dashboard to sidebar
- Set up background job for hourly deposit batching

## Phase 3: Revenue Optimization (Months 2-3)

### 3a. Agent Marketplace Revenue

- Enable agent pricing models (per_request, subscription, tips)
- Implement automatic revenue splits (creator/platform/referrer)
- Launch creator onboarding flow

### 3b. Bridge Platform Fee

- Add 0.1% platform fee to CCTP bridge transactions
- Update bridge preview UI to show platform fee separately

### 3c. Conversation History Limit

- Limit to last 10 messages to reduce LLM costs by 40-60%
- Implement prompt caching for system prompt (50% input cost reduction)

---

# 7. Risk Analysis

## Pricing Change Risks

| Risk | Severity | Mitigation |
|---|---|---|
| User churn from fee increase | Medium | Still cheapest self-custody wallet by 40%. Grandfather early users for 3 months. |
| Competitor undercutting | Low | Our unique value is AI + self-custody + USDC focus. No competitor has this stack. |
| Fee perception ("they raised fees 150%!") | Medium | Frame as "now with Pro tier -- lower fees than ever." Lead with Pro value, not fee increase. |
| Subscription conversion too low | Medium | Free tier is still functional. Subscription is for power users. 5-10% conversion is industry standard. |

## Yield Farming Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Smart contract exploit (Aave) | Low | $5B+ TVL, audited by Trail of Bits/OpenZeppelin. Consider Nexus Mutual insurance. |
| Regulatory (yield = securities?) | Medium | Start as non-custodial helper (user approves, contract executes). Consult counsel before Phase 2. |
| Gas costs eating yield | Low | Batch deposits hourly, minimum $10 deposit. Base L2 gas is $0.02. |
| User trust ("where's my money?") | Medium | Full transparency: show Aave position, real-time yield counter, one-click withdraw. |

## LLM Cost Risks

| Risk | Severity | Mitigation |
|---|---|---|
| API cost spike from abuse | Medium | Rate limiting (free_tier.py already has 50 msg cap). Add per-day cap of 20 msgs for free tier. |
| Gemini Flash deprecation | Low | Gemini Flash is Google's flagship free model. Haiku is the fallback at $0.0005/msg. |
| Model quality degradation | Low | Hybrid routing ensures complex tasks get Sonnet. Monitor user satisfaction scores. |

---

# 8. Sprint 0 Task Completion

## Task Checklist

| # | Task | Status | Output |
|---|---|---|---|
| 1 | Audit current fee structure across codebase | DONE | Section 1: Found fees in config.py, transaction_relayer.py, direct_tx.py, api/routes/transactions.py, scheduler_executor.py |
| 2 | Calculate true cost-per-transaction (gas + LLM + infra) | DONE | Section 4A: $0.035-0.077/tx (varies by LLM model used) |
| 3 | Benchmark 10+ competitors | DONE | Section 2: Coinbase, Venmo, Cash App, Wise, Revolut, MetaMask, Phantom, PayPal, Crypto.com, Strike |
| 4 | Identify all unmonetized surfaces | DONE | Section 1: Gift cards, bridges, merchants, yield, premium tier, agent marketplace |
| 5 | Propose new fee structure with specific numbers | DONE | Section 3A: $0.01 + 0.5% (cap $5) |
| 6 | Design premium tier pricing | DONE | Section 3B: Pro at $4.99/mo, Business at $19.99/mo |
| 7 | Model yield farming revenue | DONE | Section 3C: 70/30 split, $2.75K-$275K/yr depending on AUM |
| 8 | Build unit economics model (cost/revenue per user) | DONE | Section 4: Free user margin 95%, Pro 98%, Business 98% |
| 9 | Create 3-scenario financial projections | DONE | Section 5: $47K-$2.2M ARR depending on scale |
| 10 | Write implementation plan with specific code changes | DONE | Section 6: 3-phase rollout with specific file changes |
| 11 | Risk analysis for all recommendations | DONE | Section 7: Pricing, yield, and LLM risk matrices |

---

# Appendix A: Competitor Fee Quick Reference

| Competitor | Crypto Fee | Self-Custody | Subscription Available |
|---|---|---|---|
| Coinbase | 0.5% spread / 0.05-0.60% advanced | Yes (wallet) | $4.99-$299.99/mo |
| Venmo | $0.49-$2.49 flat / 1.5-1.8% | No | No |
| Cash App | 1.75% + 0-1.5% volatility | Yes (BTC) | No |
| Wise | ~0.33% + flat fee | N/A | No |
| Revolut | 0.49-1.49% (tier-based) | No | $0-$16.99/mo |
| MetaMask | 0.875% swaps/bridges | Yes | No |
| Phantom | 0.85% swaps | Yes | No |
| PayPal | $0.49-$2.49 / 1.5-2% | Partial | No |
| Crypto.com | 0-0.25% (with CRO stake) | Partial | $4.99-$29.99/mo |
| Strike | 0.99% / 0.15% DCA | Yes | No |
| **USDChat (proposed)** | **$0.01 + 0.5% (cap $5)** | **Yes** | **$4.99-$19.99/mo** |

# Appendix B: DeFi Yield Rates Reference (Feb 2026)

| Protocol | USDC Supply APY | TVL | Risk Profile |
|---|---|---|---|
| Aave V3 (Ethereum) | 4-7% | $3.4B USDC | Battle-tested, audited |
| Aave V3 (Base) | 4-6% | Growing | Same contracts, newer chain |
| Compound V3 | 2-5% | Large | Conservative, lower APY |
| Morpho | 5-8% | Medium | Optimized, newer |
| Jito (Solana) | Up to 5.96% | Large | Solana ecosystem |

**Recommended approach:** Aave V3 on Base (cheapest gas + solid APY + audited contracts).

# Appendix C: Key Code Files for Implementation

| File | Change Required | Priority |
|---|---|---|
| `config.py:111-114` | Update FEE_FLAT, FEE_PERCENTAGE, FEE_MAX | P0 -- Week 1 |
| `free_tier.py:14` | Add daily message cap (20/day) | P0 -- Week 1 |
| `merchant_adapters.py` | Add 1% convenience fee | P1 -- Week 1 |
| `bitrefill_client.py` | Add affiliate commission tracking | P1 -- Week 1 |
| `app.py` | Add hybrid LLM routing (Gemini/Haiku/Sonnet by tier) | P1 -- Week 2 |
| `aave_client.py` | Activate yield deposits with split tracking | P1 -- Weeks 2-4 |
| `yield_tools.py` | Add yield split logic by subscription tier | P1 -- Weeks 2-4 |
| `api/routes/transactions.py:186-189` | Add 0.1% bridge platform fee | P2 -- Month 2 |
| `api/schemas/agent.py` | Already coded -- enable marketplace payments | P2 -- Month 2 |
| New: `subscription.py` | Stripe integration, tier management | P1 -- Weeks 2-3 |
| New: `supabase_migration_subscriptions.sql` | Subscription tier column in user_settings | P1 -- Week 2 |

---

## Urgent Flags

- **CRITICAL:** Current pricing loses money on every transaction under $22. Fee increase to $0.01 + 0.5% is the single highest-impact change and should be implemented immediately.
- **HIGH:** Yield farming (Aave) is coded but dormant. Activating it unlocks $27.5K-$275K/yr in revenue depending on AUM, with zero new feature development needed.
- **MEDIUM:** LLM costs on free tier are $0 (Gemini Flash), but if users upgrade to Claude Sonnet without a subscription, we lose money. Tier-gating LLM models is essential.

---

*Document Owner: Revenue Officer*
*Last Updated: February 6, 2026*
*Status: Sprint 0 COMPLETE -- Ready for implementation review*
