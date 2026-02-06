# Workstream: Revenue Officer

> **Owner**: Revenue Officer session
> **Status**: Awaiting session start
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

## Context to Read First

1. `docs/COMMAND_CENTER.md` - Project overview
2. `docs/STRATEGIC_DIRECTION.md` - Revenue targets (Q2: $5K/mo, Q4: $50K/mo)
3. `docs/EXECUTIVE_REVIEW_2026-01.md` - CEO gave C+ on economics ("unsustainable")
4. `docs/BUSINESS_OVERVIEW.txt` - Current fee structure ($0.005 + 0.2%)
5. `docs/VISION_2026.md` - Revenue metrics and ARPU targets

## Current Revenue Model (Problematic)
| Stream | Rate | Issue |
|--------|------|-------|
| Transaction fees | $0.005 + 0.2% (cap $3) | Too low - $10 send = $0.025 fee |
| Yield spread | 70% platform / 30% user | Reversed in some docs. Needs clarification. |
| Gift card affiliate | ~5-10% | Not tracked, not implemented |
| Premium tier | None | No recurring revenue |
| Agent marketplace | 20% platform cut | Phase 3, no timeline to revenue |

## Current Cost Structure (Estimated)
| Cost | Per-unit | Monthly (1K users) |
|------|----------|-------------------|
| LLM (Claude Sonnet) | ~$0.012/message | ~$600 (5 msg/user/day) |
| Infrastructure | - | ~$200-500 |
| RPC calls | ~$0.0001/call | ~$50 |
| Gas (meta-tx relayer) | ~$0.01-0.05/tx | ~$500 |

**Problem**: At 1,000 users doing 5 messages/day and 1 tx/day, monthly LLM cost alone ($600) likely exceeds transaction fee revenue.

---

## Sprint 0 Tasks

### 1. Unit Economics Deep Dive
- [ ] Calculate true cost-per-user (LLM + infra + gas + support)
- [ ] Calculate true revenue-per-user at current pricing
- [ ] Identify the breakeven point (users needed, volume needed)
- [ ] Model scenarios: 100 users, 1K users, 10K users, 100K users

### 2. Pricing Strategy Review
- [ ] Benchmark against competitors (Coinbase, Venmo, Wise, Revolut fees)
- [ ] Evaluate fee increase options ($0.01 + 0.5% vs current $0.005 + 0.2%)
- [ ] Model premium tier economics ($5/mo, $9/mo, $19/mo options)
- [ ] Evaluate yield split options (current: ambiguous 70/30. What's fair AND profitable?)
- [ ] Analyze gift card affiliate revenue potential

### 3. LLM Cost Optimization
- [ ] Read the codebase to understand current LLM usage patterns
- [ ] Model the impact of routing 70% of queries to Haiku (cheaper model)
- [ ] Evaluate caching strategies (common queries, balance checks)
- [ ] Calculate cost savings from model routing
- [ ] Explore free/cheap alternatives for simple operations (no LLM needed for balance checks)

### 4. Revenue Stream Analysis
- [ ] Rank all potential revenue streams by: revenue potential, implementation effort, time to revenue
- [ ] Model a revenue roadmap: what earns first, what earns most, what's the long game?
- [ ] Specifically evaluate:
  - Transaction fees (adjustable)
  - Yield spread (immediate potential with Aave)
  - Premium subscriptions (recurring, predictable)
  - Agent marketplace (20% cut, but needs ecosystem)
  - API access fees (B2B, developers)
  - White-label / licensing

### 5. Financial Projections
- [ ] Build a 12-month projection model (conservative, moderate, aggressive)
- [ ] Identify the path to $5K MRR (what's needed?)
- [ ] Identify the path to $50K MRR (what's needed?)
- [ ] Define key financial milestones
- [ ] Model fundraising scenarios (how long does runway last at different burn rates?)

---

## Findings

_Write your analysis here._

### Unit Economics

### Pricing Benchmarks

### Revenue Streams Ranked

---

## Recommendations

### Immediate (This Week)

### Short-term (This Month)

### Medium-term (This Quarter)

---

## Urgent Flags

_Flag anything that is an existential financial risk._

---
