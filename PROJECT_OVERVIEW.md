# USDChat — Project Overview
## Central Coordination Document for All Sessions
### Lead Architect: Claude | Last Updated: February 2026

---

> **ALL AGENTS: READ THIS FIRST.**
> This is the single source of truth. If it conflicts with other docs, this wins.
> Sections marked with [FOUNDER CONFIRMED] reflect direct founder input.

---

# 1. What Is USDChat

**Domain:** usd.chat
**Twitter/X:** x.com/usdchat
**Stage:** Stealth — no live users yet
**Stack:** Next.js 16 + FastAPI + Supabase + Web3.py

USDChat is a self-custodial USDC wallet that helps users earn passive income and (in later phases) deploy AI agents that generate revenue. The wallet is the plumbing. The moat is the ecosystem of money-making AI agents and the network effects of creators + users + yield.

**One-liner:** Turn AI ideas into money. Create agents that earn while you sleep.

---

# 2. Founder Decisions & Corrections

These override any earlier assumptions in other documents.

## 2.1 Pricing [OPEN — Needs Analysis]

The previous session proposed changing fees from `$0.005 + 0.2% (cap $3)` to `$0.01 + 0.5% (cap $5)`.

**Founder response:** "Depends on the chain of ops; percent vs fixed cost would determine a lot there."

**Current fee structure** (in `config.py:112-114`):
```
FEE_FLAT = 0.005    # $0.005
FEE_PERCENTAGE = 0.002  # 0.2%
FEE_MAX = 3.0       # $3 cap
```

**Action needed:** Revenue model officer should analyze fee structure against:
- Actual gas costs per chain (Base is cheap, Ethereum is expensive)
- Competitor pricing (MetaMask 0.875%, Phantom 0.85%)
- Unit economics at various user counts (100, 1K, 10K, 100K)
- Whether flat fee, percentage, or hybrid is optimal per chain

## 2.2 Yield Revenue & Custody Implications [FOUNDER CONFIRMED — Concerned]

**Founder response:** "I agree on yield there as a profitable model but wouldn't it mean custody? Wouldn't that require a whole set of docs on top vs a wallet company?"

**Architect analysis:** Yield via Aave is NOT custodial IF the user signs the deposit transaction. The `aave_client.py` `deposit()` method (line 312) takes a private key as a parameter — the user's key never leaves the client session. The user deposits directly to Aave's smart contract. USDChat never holds the funds.

**However:** If USDChat auto-deposits user funds (e.g., from the scheduler), that WOULD be custodial. See Section 5 (Custody Audit).

**Revenue split mechanism:** The 70/30 split (platform 70%, user 30%) needs to be implemented carefully:
- Option A: User deposits full amount to Aave, platform takes cut on withdrawal (fee, not custody)
- Option B: Smart contract splits yield automatically (non-custodial, needs contract deployment)
- Option C: Server handles split (CUSTODIAL — avoid)

**Recommendation:** Option A for MVP, Option B long-term. Document this clearly for compliance.

## 2.3 Feature Scope [FOUNDER CONFIRMED — Corrections]

Previous session proposed killing: Community Vaults, meme coins, AI characters, card issuance.

**Founder corrections:**

| Feature | Previous Decision | Founder Input | Revised Status |
|---------|------------------|---------------|----------------|
| **Community Vaults** | Kill | "Many functional DeFi protocols do this as smart contracts" | KEEP — but only as smart contract wrappers (non-custodial). Research Yearn/Beefy model. |
| **Meme coins / PumpFun** | Kill (securities risk) | "How is it a legal issue if the UI is a wrapper with a wallet?" | KEEP IN SCOPE — but as a UI pass-through only. USDChat provides the interface; user interacts directly with PumpFun contracts. No order book, no matching. |
| **AI Characters** | Kill | "Was about 3rd party integration for AI influencers that make money through socials — connecting LLM ideas to capital and tools" | REFRAME — This is the core "Idea → Money" pipeline. Not us creating characters, but enabling creators to build AI agents that earn revenue. This IS the agent marketplace vision. |
| **Card Issuance** | Kill | "Was never my idea" | CONFIRMED KILL |

## 2.4 External Assets [FOUNDER CONFIRMED]

| Asset | Status |
|-------|--------|
| Domain: usd.chat | Active |
| Twitter/X: x.com/usdchat | Active (stealth) |
| Alchemy account | Founder can set up now if blocking |
| Discord | Not created |

---

# 3. Architecture

## 3.1 Current State

```
┌───────────────────────────────────────────────────────────────┐
│                    FRONTEND                                    │
│  Next.js 16 (/web)           │  Streamlit (LEGACY — sunset)  │
│  - App Router                │  - app.py (37KB)              │
│  - shadcn/ui + Tailwind      │  - Being replaced             │
│  - TanStack Query + Zustand  │                               │
└──────────────────────────────┴───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│                    FASTAPI BACKEND                            │
│  api/main.py — JWT Auth, Rate Limiting, CORS                 │
│  Routes: wallet, transactions, yield, scheduler, earnings,   │
│          agents, health                                      │
└──────────────────────────────┬───────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Wallet     │      │    DeFi      │      │   Agent      │
│   Layer      │      │   Layer      │      │   Layer      │
│              │      │              │      │              │
│wallet_manager│      │aave_client   │      │Agent SDK     │
│direct_tx     │      │yield_tools   │      │Agent API     │
│meta_tx       │      │scheduler_*   │      │Agent DB (8t) │
│chain_utils   │      │cctp_client   │      │              │
└──────────────┘      └──────────────┘      └──────────────┘
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               ▼
                    ┌──────────────────┐
                    │   Supabase       │
                    │   (PostgreSQL)   │
                    │   7 migrations   │
                    └──────────────────┘
```

## 3.2 Supported Chains

| Chain | Status | USDC Address |
|-------|--------|-------------|
| Base | Production | `0x8335...2913` |
| Arbitrum | Production | `0xaf88...5831` |
| Ethereum | Production | `0xa0b8...eb48` |
| Solana | Production | `EPjF...Dt1v` |
| Sepolia | Testnet | `0x1c7D...7238` |
| Arc | Testnet | `0x3600...0000` |

## 3.3 Key Files Quick Reference

| File | What It Does | Lines |
|------|-------------|-------|
| `config.py` | Fee structure, network configs, RPC fallback | 287 |
| `wallet_manager.py` | HD wallet creation, encryption, lock/unlock | 488 |
| `direct_tx.py` | Direct USDC transfers (user signs) | 338 |
| `meta_tx.py` | EIP-712 meta-transaction signing/verification | 156 |
| `transaction_relayer.py` | Gasless tx execution (relayer pays gas) | 251 |
| `scheduler_executor.py` | Background task runner (DCA, scheduled sends) | 633 |
| `aave_client.py` | Aave V3 deposit/withdraw/APY | ~350 |
| `api/main.py` | FastAPI app factory | - |
| `api/routes/agents.py` | Agent marketplace CRUD (28KB) | - |
| `sdk/usdchat_agent/` | Agent SDK package | - |

---

# 4. Phase Status

## Phase 1: Money Maker MVP — COMPLETE
- Next.js scaffold with App Router
- Yield UI (Aave one-click deposit)
- DCA scheduler
- Earnings dashboard (30-day chart)
- All frontend pages (wallet, earn, send, receive, history)
- JWT auth flow
- Docker Compose

## Phase 2: PWA + Retention — NEXT
- [ ] PWA configuration (next-pwa, service worker, manifest)
- [ ] Push notifications (daily earnings at 6 PM)
- [ ] Email notifications (weekly earnings summary)
- [ ] Mobile UI polish (bottom nav, swipe, haptic)

## Phase 3: Agent Marketplace — AFTER TRACTION
- [ ] Agent discovery UI
- [ ] x402 micropayments (blocked on Circle credentials)
- [ ] Agent chat interface
- [ ] Creator onboarding wizard
- [ ] PumpFun/DeFi pass-through integrations
- [ ] Community vault smart contracts

---

# 5. Custody Audit — CRITICAL FINDINGS

## Summary

| Component | Custodial? | Severity | Details |
|-----------|-----------|----------|---------|
| `meta_tx.py` | NO | Safe | Pure signing/verification utility. Private keys passed as parameters, never stored. |
| `wallet_manager.py` | NO | Safe | Keys encrypted with user's password, stored in browser session only. Server never has plaintext keys during normal operation. |
| `direct_tx.py` | NO (interactive) | Safe | Takes private key as parameter. In Streamlit flow, key comes from session state (user-decrypted). |
| `aave_client.py` | NO (interactive) | Safe | Same pattern — `deposit()` takes private key, signs tx, sends. User's key from session. |
| **`scheduler_executor.py`** | **YES** | **CRITICAL** | **Stores encrypted private key in DB, server holds decryption key. Can execute transactions without user presence.** |
| `transaction_relayer.py` | **PARTIAL** | **HIGH** | Relayer calls `transfer()` from its own address. If users deposit USDC to relayer, relayer holds funds = custodial. |

## scheduler_executor.py — Detailed Finding

**Location:** `scheduler_executor.py:159-191`

**The problem:**
1. User's private key is encrypted and stored in `user_settings.scheduled_tx_private_key_encrypted` (Supabase)
2. Server holds `SCHEDULER_ENCRYPTION_SECRET` environment variable
3. Server decrypts the key at line 177: `PasswordEncryption.decrypt_with_key(encrypted_key, scheduler_secret)`
4. Server uses the decrypted key to execute transfers at line 186-191

**Legal implication:** Under FinCEN guidance, SEC interpretations, and EU MiCA:
- If a service can unilaterally access user funds → custodian
- If a service stores private keys server-side (even encrypted) → custodian
- Custodians need: MSB registration (US), MiCA license (EU), state MTLs (US states)

**Current risk:** LOW (stealth, no users). **Pre-launch risk:** CRITICAL.

## transaction_relayer.py — Detailed Finding

**Location:** `transaction_relayer.py:152-227`

**The problem:**
- The relayer executes `transfer()` from `self.relayer_address` (line 191)
- This means the relayer wallet must hold the USDC that gets transferred
- If users deposit USDC to the relayer address, the relayer is custodial

**However:** The current meta-tx flow may not actually require users to deposit to the relayer. If user USDC stays in user wallet and the relayer only pays gas, that's a different (better) architecture. But the current `transfer()` call on line 183 sends USDC FROM the relayer, which IS custodial.

## Recommendations

### Immediate (before any users):

1. **scheduler_executor.py** — Remove server-side key storage entirely. Replace with:
   - **Option A:** Push notification approval (user approves each scheduled tx via mobile)
   - **Option B:** Smart contract allowance (user pre-approves a contract to spend up to X USDC on schedule)
   - **Option C:** Circle Programmable Wallets (delegated signing, Circle handles custody)
   - **Option D (simplest):** Make scheduled payments "pending" — executor queues them, user batch-approves on next login

2. **transaction_relayer.py** — Refactor to use proper ERC-2771 forwarder pattern or ERC-4337 account abstraction. The relayer should pay gas, not move USDC.

### Long-term:
- Move to ERC-4337 (Account Abstraction) for gas sponsorship
- Consider Circle Programmable Wallets for users who prefer hosted custody
- Keep self-custody as primary path (regulatory advantage)

---

# 6. Revenue Model — Current vs. Proposed

## Current (config.py)
```
Transaction fee: $0.005 + 0.2% (cap $3)
Yield revenue: 0 (not active)
Agent revenue: 0 (Phase 3)
Premium tier: None
```

## Open Questions [ACTION: Revenue Model Officer]

1. **Fee structure per chain:**
   - Base/Arbitrum gas costs: ~$0.001-0.01
   - Ethereum gas costs: ~$0.50-5.00
   - Should fees be chain-aware? (Higher on L1, lower on L2)

2. **Yield split implementation:**
   - If user deposits to Aave and platform takes 70% of yield, how is this enforced?
   - Smart contract split vs. fee-on-withdrawal vs. separate accounting
   - Legal: Is yield split a "fee" or "revenue sharing"? Different regulatory treatment.

3. **Competitor pricing:**
   - MetaMask: 0.875% swap fee
   - Phantom: 0.85% swap fee
   - Coinbase: 1% + spread
   - Our current: 0.2% + $0.005 — significantly cheaper

4. **Unit economics at scale:**
   - Need model at 1K, 10K, 100K users
   - Infrastructure costs vs. revenue per user
   - What's the breakeven DAU?

---

# 7. Agent Coordination

## How To Launch Parallel Sessions

Each session should:
1. Read this `PROJECT_OVERVIEW.md` first
2. Read their specific briefing below
3. Work on their branch
4. Leave notes in Section 9 (Agent Feedback)

## Active Agent Branches

| Role | Branch | Focus |
|------|--------|-------|
| UX/UI Audit | `claude/ux-ui-audit-FPOzz` | Next.js frontend quality, mobile UX |
| PMF Analysis | `claude/pmf-analysis-usdchat-QG4Cj` | Product-market fit for 2026 |
| Security Audit | `claude/security-audit-usdchat-EyCQM` | Code security, key management |
| R&D Landscape | `claude/rd-tech-landscape-scan-uwLrf` | 2026 tech trends, competitor analysis |
| Revenue Model | `claude/fix-project-economics-vUdyi` | Pricing, unit economics, yield model |
| Compliance | `claude/review-compliance-docs-hj9xG` | Regulatory requirements per jurisdiction |
| Production Readiness | `claude/audit-production-readiness-XiEcI` | Deployment, monitoring, reliability |
| Deployment Setup | `claude/setup-production-deployment-sQo0k` | Docker, CI/CD, infrastructure |
| Growth Strategy | `claude/usdchat-growth-strategy-MCFqq` | GTM, user acquisition, partnerships |

## Session Launch Template

When starting a new parallel session, use this prompt:

```
You are a [ROLE] for USDChat (usd.chat), a self-custodial USDC wallet
with yield, DCA, and a future AI agent marketplace.

READ FIRST: PROJECT_OVERVIEW.md in the repo root.
THEN READ: docs/STRATEGIC_DIRECTION.md

Your branch: claude/[branch-name]

Your specific mission: [MISSION]

Leave your findings and recommendations as a report in
docs/reports/[ROLE]_REPORT.md

Key context:
- Stage: Stealth, no users yet
- Tech: Next.js 16 + FastAPI + Supabase
- Chains: Base, Arbitrum, Ethereum, Solana
- Phase 1 (yield/DCA/earnings) is complete
- Phase 2 (PWA/notifications) is next
- Phase 3 (agent marketplace) is after user traction
- CRITICAL: See custody audit in PROJECT_OVERVIEW.md Section 5

Constraints:
- Do NOT propose features outside current scope
- Focus on making existing features production-ready
- Flag any custody/regulatory concerns you find
- Be direct, no fluff
```

---

# 8. Roadmap Vision

## Q1 2026 (Now)
- [x] Phase 1 MVP complete
- [ ] Fix custody issues (scheduler, relayer)
- [ ] Production deployment (Alchemy RPC, proper hosting)
- [ ] End-to-end testing
- [ ] Pin dependency versions
- [ ] Security audit completion

## Q2 2026
- [ ] Phase 2: PWA + push notifications
- [ ] Soft launch (invite-only, 50-100 users)
- [ ] Circle API credentials → CCTP bridging
- [ ] Yield feature live with proper non-custodial implementation
- [ ] Begin agent marketplace UI (Phase 3 prep)

## Q3 2026
- [ ] Phase 3: Agent marketplace launch
- [ ] x402 micropayments live
- [ ] PumpFun/DeFi pass-through integrations
- [ ] Creator onboarding
- [ ] Target: 30 Weekly Active Creators

## Q4 2026
- [ ] Community vault smart contracts
- [ ] Multi-protocol yield (Compound, Morpho)
- [ ] Mobile-native features
- [ ] Target: 150 Weekly Active Creators, $500K/mo agent GMV

---

# 9. Agent Feedback & Notes

> Agents: Leave your notes, questions, and findings below.
> Format: `[DATE] [ROLE]: Note`

_No notes yet. Agents should append here after completing their reports._

---

# 10. Critical Blockers

| Blocker | Owner | Impact | Status |
|---------|-------|--------|--------|
| Custody issue in scheduler_executor.py | Architect | Cannot go live with server-side key storage | Audit complete, fix needed |
| Custody issue in transaction_relayer.py | Architect | Relayer pattern needs refactor | Audit complete, fix needed |
| Circle API credentials | Founder | Blocks x402, CCTP | Pending |
| Alchemy RPC key | Founder | Blocks reliable production RPC | Can set up now |
| Bitrefill API key | Founder | Blocks gift card feature | Pending |
| RLS policies incomplete | Security | Supabase service key overuse | Known, needs fix |

---

# 11. Decision Log

| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| 2026-02 | Money maker first, agents second | Cold-start: no agents → no users | LOCKED |
| 2026-02 | Streamlit → Next.js 16 | 70% fintech uses React; PWA support | LOCKED |
| 2026-02 | Self-custody only (primary) | Regulatory advantage; differentiator | LOCKED |
| 2026-02 | USDC only initially | Focus; Circle partnership | LOCKED |
| 2026-02 | No token launch | Product focus, not fundraising | LOCKED |
| 2026-02 | Kill card issuance | Founder: "Was never my idea" | LOCKED |
| 2026-02 | Keep PumpFun as pass-through | Non-custodial UI wrapper is legal | OPEN — needs compliance review |
| 2026-02 | Keep community vaults | Smart contract only (non-custodial) | OPEN — needs compliance review |
| 2026-02 | AI characters → Agent marketplace | Founder clarified: it's about enabling creators, not creating characters | LOCKED |
| 2026-02 | 70/20/10 agent revenue split | Industry standard | LOCKED |
| 2026-02 | WAC as north star metric | Avoids TVL trap | LOCKED |
| 2026-02 | Fee structure | OPEN — needs chain-specific analysis | OPEN |

---

*Document Owner: Lead Architect*
*Last Updated: February 6, 2026*
*Status: AUTHORITATIVE — All other docs defer to this one*
