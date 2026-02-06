# COMMAND CENTER - USDChat

> **Last updated**: 2026-02-06
> **Architect session**: active
> **Sprint**: Sprint 0 → Sprint 1 transition

---

## How This Document Works

This is the **single source of truth** for all parallel Claude Code sessions working on USDChat. Each session operates as a specialized role. You are one of them.

**Your protocol:**
1. Read this entire document to understand the project
2. Find your role in the [Role Registry](#role-registry) below
3. Read your workstream file at `docs/workstreams/{your-role}.md`
4. Execute your tasks autonomously - you have full freedom within your mandate
5. Write all findings, recommendations, and changes back to your workstream file
6. If you make code changes, commit with prefix: `[role-name] description`
7. Push to branch: `claude/project-analysis-fwmFh` (see Git Protocol below)
8. If you need to flag something urgent to the architect, write it to the `## Urgent Flags` section of your workstream file

**You do NOT need to:**
- Wait for approval from other roles (unless your workstream says otherwise)
- Coordinate timing with other sessions
- Limit your output - be thorough

**You MUST:**
- Stay within your role's mandate (don't do other roles' work)
- Write everything down (other sessions can't see your thinking)
- Be specific and actionable (no vague recommendations)
- Reference file paths and line numbers when discussing code
- Update your workstream file before your session ends

---

## Git Protocol (CRITICAL - Read This)

All sessions share one branch: `claude/project-analysis-fwmFh`

**Before writing:**
```bash
git fetch origin claude/project-analysis-fwmFh
git pull origin claude/project-analysis-fwmFh --rebase
```

**After writing:**
```bash
git add docs/workstreams/YOUR-FILE.md
git commit -m "[role-name] Sprint 0: description of findings"
git push -u origin claude/project-analysis-fwmFh
```

**If push fails (merge conflict):**
```bash
git pull origin claude/project-analysis-fwmFh --rebase
# resolve conflicts (keep both changes)
git push -u origin claude/project-analysis-fwmFh
```

**If push fails with 403 / permission error**, retry up to 4 times with 2s delay between attempts. If it still fails, save your workstream file content and report the error in your session output.

**Rules:**
- Each role only modifies its own workstream file (no cross-file edits except architect)
- Always pull before push (avoids conflicts)
- Commit messages must start with `[role-name]` prefix
- The architect is the only role that edits `COMMAND_CENTER.md`
- All other docs (`docs/*.md`) are read-only for roles (flag changes needed to architect via your workstream file)

---

## Project State (What Exists Today)

### One-Liner
USDChat is a wallet for people who want to make money with AI. It connects USDC to LLMs and ships pre-built money-making mechanisms (yield, DCA, automated trading, agent payments) so users earn from day one.

> **NOTE TO ALL ROLES**: The "AI project launchpad" framing in older docs was aspirational positioning written by a previous AI assistant. It does not reflect the current code. Ground your analysis in what the code actually does, not what the docs describe. The founder's vision: **a competitive wallet with built-in ways for people to make money using AI**.

### Tech Stack
| Layer | Technology | Location |
|-------|-----------|----------|
| Frontend (legacy) | Streamlit | `app.py`, `components/` |
| Frontend (new) | Next.js 14 + shadcn/ui + Tailwind | `web/` |
| Backend | FastAPI + Pydantic | `api/` |
| Database | Supabase (PostgreSQL + RLS) | `migrations/` |
| AI | Claude 3.5 Sonnet via LangChain | root Python modules |
| Blockchain | Web3.py (EVM) + Solana SDK | `chain_utils.py`, `*_client.py` |
| Agent SDK | Python package | `sdk/usdchat_agent/` |
| Scheduler | Background worker | `scheduler_executor.py` |
| Infra | Docker Compose | `docker-compose.yml` |

### What's Built (Phase 1 - COMPLETE)
- Non-custodial HD wallet (BIP39/44, EVM + Solana)
- FastAPI backend with JWT auth, rate limiting
- Full Next.js frontend: wallet dashboard, yield UI, DCA scheduler, earnings dashboard, send/receive, transaction history
- Agent Protocol: SDK + 8-table DB schema + API endpoints
- Aave yield integration (backend)
- CCTP cross-chain bridging (backend)
- Bitrefill gift card integration (backend, needs API key)
- Email automation via Gmail OAuth
- Security hardening (memory-only keys, auto-lock, RLS)
- Docker Compose orchestration

### What's NOT Built Yet
- PWA / service worker / push notifications (Phase 2)
- Agent marketplace UI (Phase 3)
- x402 micropayments (blocked on Circle credentials)
- Mobile-native app
- E2E tests against real backend
- Production deployment
- Fiat on/off ramp

### Infrastructure
- **Hosting**: Railway (synced from git, live)
- **Database**: Supabase (live, schema applied)
- **Circle**: Warm relationship - founder is close friends with Arc (Circle's chain) leadership
- **Deployment**: Railway auto-deploys from git pushes

### Remaining Blockers (Require Founder Action)
| Blocker | Impact | Status |
|---------|--------|--------|
| Circle API credentials | Blocks x402, CCTP production | Warm relationship, in progress |
| Bitrefill API key | Blocks gift card purchases | Pending |
| Production RPC keys (Alchemy/Infura) | Blocks reliable mainnet access | Pending |

### Key Numbers
- 50 commits, 1 contributor ("blue"), 6 days of intense development (Jan 27 - Feb 2)
- 42 Python modules at root level
- 115 files changed in last 5 commits alone (~24K lines added)
- Revenue model: $0.005 + 0.2% per transaction (CEO review says "too low")
- Yield split: 70% platform / 30% user (strategic doc says this, exec review questions sustainability)

---

## Honest Competitive Assessment

### Strengths
1. **Unique intersection**: AI + self-custody + multi-chain + commerce. No direct competitor does all four.
2. **Working MVP**: Wallet creation, sends, yield, DCA, earnings dashboard all functional.
3. **Agent Protocol foundation**: SDK, DB schema, API ready for marketplace.
4. **2FA email loop**: Genuine differentiator - AI reads verification emails to complete purchases autonomously.

### Weaknesses (Why We're Not Competitive Yet)
1. **No users, no revenue, no deployment** - product exists only in dev environment.
2. **Streamlit legacy** - 42 root Python files, 1,227-line `app.py`, architectural debt.
3. **Security gaps** - exec review flagged cookie-stored keys (now fixed), but no security audit.
4. **Unit economics don't work** - LLM costs (~$0.012/tx) exceed transaction fees ($0.005 + 0.2%).
5. **No mobile** - 2026 fintech without mobile is dead on arrival.
6. **Solo developer** - no team, no advisors, no funding.
7. **Missing integrations** - Circle, Bitrefill, production RPC all blocked on API keys.
8. **No go-to-market** - great vision docs but no launch plan, no community, no distribution.

### Competitive Landscape (Feb 2026)
| Competitor | Threat Level | What They Have | What They Lack |
|-----------|-------------|----------------|----------------|
| Coinbase Wallet + AI features | HIGH | Brand, users, fiat ramp | AI depth, agent marketplace |
| MetaMask + Snaps ecosystem | HIGH | Distribution, plugins | AI, simplicity |
| Phantom | MEDIUM | Beautiful UX, Solana | Multi-chain AI, automation |
| ChatGPT + finance plugins | HIGH | Distribution, AI | Wallet, self-custody |
| New AI-native wallets (2026) | UNKNOWN | Fresh, funded | Unproven |

### What Would Make Us Competitive
1. **Ship to production** with working yield + DCA (proves the core thesis)
2. **PWA with push notifications** (daily earnings notification = retention hook)
3. **Agent marketplace with 10+ agents** (creates moat via network effects)
4. **Fix unit economics** (Haiku for simple queries, yield revenue, premium tier)
5. **Community** (Discord, Twitter, creator onboarding)

---

## Role Registry

### Roles and Their Mandates

| # | Role | Workstream File | Mandate |
|---|------|----------------|---------|
| 1 | **Lead Architect** | `workstreams/architect.md` | System design, code construction, technical decisions, integration. The builder. |
| 2 | **Lead Designer** | `workstreams/designer.md` | UX/UI audit, design system, interaction patterns, accessibility, mobile-first design. |
| 3 | **PMF Analyst** | `workstreams/pmf-analyst.md` | Product-market fit, user segments, competitive positioning, feature prioritization, metrics. |
| 4 | **Security Auditor** | `workstreams/security-auditor.md` | Full security audit: code, architecture, crypto, API, supply chain. Threat modeling. |
| 5 | **R&D Lab** | `workstreams/rd-lab.md` | 2026 trends scan, emerging tech, integration opportunities, "what's possible" research. Has web search. |
| 6 | **Revenue Officer** | `workstreams/revenue-officer.md` | Revenue model, unit economics, pricing strategy, monetization roadmap, financial projections. |
| 7 | **Compliance Officer** | `workstreams/compliance.md` | Regulatory landscape, licensing needs, geo-restrictions, privacy law, terms of service. |
| 8 | **Workflow Reviewer** | `workstreams/workflow-reviewer.md` | Code quality, dev workflow, CI/CD, testing strategy, deployment pipeline, DX for contributors. |
| 9 | **DevOps Lead** | `workstreams/devops.md` | Infrastructure, deployment, monitoring, scaling, cost optimization, reliability. |
| 10 | **Growth Strategist** | `workstreams/growth.md` | Distribution, user acquisition, viral loops, partnerships, community building, launch strategy. |

### Role Interaction Rules
- Each role **writes to its own workstream file only** (except the architect who maintains this COMMAND_CENTER)
- Roles reference each other's findings by reading other workstream files
- The architect synthesizes cross-role findings into actionable decisions
- No role blocks another - work in parallel, flag conflicts in your workstream file
- If two roles disagree, the architect resolves it

---

## Active Sprint: Sprint 0 - Strategic Foundation

### Sprint Goal
Every role produces their initial assessment and actionable recommendations. The architect uses these to build Sprint 1 (the first construction sprint).

### Per-Role Sprint 0 Deliverables

| Role | Deliverable | Output |
|------|------------|--------|
| Architect | System design review, dependency map, construction plan | `workstreams/architect.md` |
| Designer | Full UX audit, design system spec, mobile-first wireframes | `workstreams/designer.md` |
| PMF Analyst | Market map, user segment analysis, feature priority matrix | `workstreams/pmf-analyst.md` |
| Security Auditor | Threat model, vulnerability report, remediation priorities | `workstreams/security-auditor.md` |
| R&D Lab | 2026 trends report, integration opportunities, tech radar | `workstreams/rd-lab.md` |
| Revenue Officer | Unit economics model, pricing recommendations, revenue roadmap | `workstreams/revenue-officer.md` |
| Compliance | Regulatory risk matrix, licensing requirements, geo-strategy | `workstreams/compliance.md` |
| Workflow Reviewer | Code quality report, CI/CD plan, testing strategy | `workstreams/workflow-reviewer.md` |
| DevOps Lead | Infrastructure plan, deployment strategy, cost projections | `workstreams/devops.md` |
| Growth Strategist | GTM plan, channel strategy, community blueprint, launch plan | `workstreams/growth.md` |

---

## Architecture Decisions Log

| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| 2026-02 | Next.js 14 replaces Streamlit | PWA support, React ecosystem, mobile-first | ACTIVE |
| 2026-02 | Base is primary chain | Cheapest gas, Circle native, Coinbase ecosystem | ACTIVE |
| 2026-02 | Self-custody only (no custodial) | Regulatory advantage, user trust | ACTIVE |
| 2026-02 | LangChain + Claude for AI | Structured tool calling, best reasoning | ACTIVE |
| **2026-02-06** | **North star: Monthly Active Treasuries (MAT)** | WAC requires marketplace that doesn't exist. MAT = wallets >$100 + >1 tx/mo + yield | **REPLACES WAC** |
| **2026-02-06** | **Positioning: "The Autopilot for Your USDC"** | "AI launchpad" was aspirational vapor. Autopilot matches what code does | **REPLACES LAUNCHPAD** |
| **2026-02-06** | **Pricing: $0.01 + 0.5% (cap $5)** | Old pricing ($0.005+0.2%) loses money. Breakeven at $8 vs $22 | **REPLACES OLD FEES** |
| **2026-02-06** | **Model routing: Haiku 70% / Sonnet 30%** | LLM costs drop from $0.012 to $0.003/msg | **NEW** |
| **2026-02-06** | **Yield is the business** | 70/30 platform/user split at $3M AUM = $8,750/mo | **NEW** |
| **2026-02-06** | **Target segment: crypto-native freelancers** | Quantifiable pain (3-5% Wise fees), natural yield loop | **NEW** |
| **2026-02-06** | **Kill: Community Vaults, meme coins, card issuance, AI characters** | Securities law, regulatory risk, no users to support | **NEW** |

---

## Key Documents Index

| Priority | Document | Purpose |
|----------|----------|---------|
| 1 | `docs/RECONSTRUCTED_ARCHITECTURE.md` | **Architect's code-grounded plan (Sprint 1 source of truth)** |
| 2 | `docs/COMMAND_CENTER.md` | This file - coordination hub |
| 3 | `docs/workstreams/*.md` | All 9 Sprint 0 role outputs |
| 4 | `docs/CONTEXT_FOR_AI.md` | Quick project context |
| 5 | `docs/STRATEGIC_DIRECTION.md` | Strategy (partially outdated - see decisions log) |
| 6 | `docs/SECURITY_TODO.md` | Security issues |

---

## Sprint 0 Complete - Cross-Role Synthesis

### What All 9 Roles Agree On

1. **DO NOT LAUNCH YET** — API send is fake, JWT has hardcoded fallback, charts show random data
2. **YIELD IS THE BUSINESS** — not transaction fees. $8,750/mo at $3M AUM via 70/30 split
3. **POSITIONING: "Autopilot for USDC"** — not "AI launchpad" (code doesn't support that claim)
4. **TARGET: Crypto-native freelancers** — quantifiable pain, natural yield retention loop
5. **KILL: Community Vaults, meme coins, AI characters, card issuance, Streamlit**
6. **BUILD: Yield activation, model routing, pricing fix, OFAC screening, push notifications**

### Urgent Risk (Compliance)
Server-side encrypted key storage may classify USDChat as custodian under FinCEN. Must audit `wallet_manager.py`, `meta_tx.py`, `scheduler_executor.py` and verify keys are NEVER accessible server-side. This is a launch blocker.

---

## Sprint 1: Make It Real (Architect's Construction Plan)

### Goal: Fix every broken thing → ship to production → get first 10 real users

### Week 1: Fix Hard Blockers (No new features — just make existing code honest)

| # | Task | Owner | Files | Hours |
|---|------|-------|-------|-------|
| 1 | **Remove JWT hardcoded fallback** — fail on startup if not set | Architect | `api/config.py:36` | 1h |
| 2 | **Fix API send endpoint** — wire real transaction signing or disable | Architect | `api/routes/transactions.py:297-321` | 4-8h |
| 3 | **Replace mock earnings data** — connect to real hooks | Architect | `web/` earn page components | 2h |
| 4 | **Fix pricing** — $0.01 + 0.5% cap $5 | Architect | `config.py:111-114` | 1h |
| 5 | **PBKDF2 → 600K iterations** | Architect | `utils/encryption.py` | 2h |
| 6 | **Audit key storage** — verify non-custodial architecture | Security | `wallet_manager.py`, `meta_tx.py`, `scheduler_executor.py` | 4h |
| 7 | **OFAC SDN screening** (free list) | Compliance | New middleware | 8h |
| 8 | **Geo-block NY + WA + sanctioned countries** | Compliance | New middleware | 4h |

### Week 2: Production Deployment

| # | Task | Owner | Files | Hours |
|---|------|-------|-------|-------|
| 9 | **Production Dockerfiles** — multi-stage, non-root, real builds | DevOps | `Dockerfile.api`, `web/Dockerfile` | 4h |
| 10 | **Restrict CORS** — actual domains only | DevOps | `api/main.py` | 1h |
| 11 | **Create .dockerignore** | DevOps | New files | 30m |
| 12 | **Deploy to Railway/Vercel/Fly.io** | DevOps | Infrastructure | 4h |
| 13 | **Merge designer's 17 UX fixes** | Architect | From `claude/ux-ui-audit-FPOzz` | 2h |
| 14 | **Fix dead navigation links** — /settings, /import, /notifications | Designer | `web/app/` | 4h |
| 15 | **Model routing** — Haiku for simple, Sonnet for complex | Architect | `app.py` or new `model_router.py` | 4h |

### Week 3: First Users

| # | Task | Owner | Files | Hours |
|---|------|-------|-------|-------|
| 16 | **PWA config** — service worker, manifest, install prompt | Architect | `web/next.config.ts`, `web/public/` | 4h |
| 17 | **Push notifications** — "You earned $X today" | Architect | New notification service | 8h |
| 18 | **ToS + Privacy Policy** pages | Compliance | `web/app/` legal pages | 8h |
| 19 | **Yield risk disclosure** — user acknowledgment before first deposit | Compliance + Designer | `web/` modal | 2h |
| 20 | **Pin all dependencies** | Workflow | `requirements.txt`, `package.json` | 2h |
| 21 | **CI/CD pipeline** (merge workflow reviewer's config) | Workflow | `.github/workflows/ci.yml` | 2h |

### Founder Actions (Parallel — No Code Needed)

| Action | Urgency | Impact |
|--------|---------|--------|
| Alchemy free-tier signup | This week | Reliable RPC |
| Domain name purchase | This week | Professional URL for deployment |
| Twitter/X account creation | This week | Growth channel |
| Discord server setup | This week | Community |
| Circle API credentials request | This month | x402, CCTP |
| Legal opinion on meta-tx relayer | This month | $3-5K, needed for compliance |

---

## Session Branch Registry

| Role | Branch | Status |
|------|--------|--------|
| Architect | `claude/project-analysis-fwmFh` | Active (main branch) |
| Designer | `claude/ux-ui-audit-FPOzz` | Sprint 0 complete — 17 fixes to merge |
| PMF Analyst | `claude/pmf-analysis-usdchat-QG4Cj` | Sprint 0 complete |
| Security Auditor | `claude/security-audit-usdchat-EyCQM` | Sprint 0 complete |
| R&D Lab | `claude/rd-tech-landscape-scan-uwLrf` | Sprint 0 complete |
| Revenue Officer | `claude/fix-project-economics-vUdyi` | Sprint 0 complete |
| Compliance | `claude/review-compliance-docs-hj9xG` | Sprint 0 complete |
| Workflow Reviewer | `claude/audit-production-readiness-XiEcI` | Sprint 0 complete |
| DevOps | `claude/setup-production-deployment-sQo0k` | Sprint 0 complete |
| Growth | `claude/usdchat-growth-strategy-MCFqq` | Sprint 0 complete |

---
