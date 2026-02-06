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

Decisions made by the architect that all roles must respect:

| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| 2026-02 | Next.js 14 replaces Streamlit | PWA support, React ecosystem, mobile-first | ACTIVE |
| 2026-02 | Base is primary chain | Cheapest gas, Circle native, Coinbase ecosystem | ACTIVE |
| 2026-02 | Self-custody only (no custodial) | Regulatory advantage, user trust | ACTIVE |
| 2026-02 | Agent marketplace is the moat | Network effects > feature list | ACTIVE |
| 2026-02 | Weekly Active Creators is north star | Avoids TVL trap, measures real engagement | ACTIVE |
| 2026-02 | 70/20/10 revenue split (creator/platform/referrer) | Fair to creators, sustainable for platform | ACTIVE |
| 2026-02 | LangChain + Claude for AI | Structured tool calling, best reasoning | ACTIVE |

---

## Key Documents Index

Read in this order for full context:

| Priority | Document | Purpose |
|----------|----------|---------|
| 1 | `docs/CONTEXT_FOR_AI.md` | Quick project context (architecture, endpoints, current state) |
| 2 | `docs/STRATEGIC_DIRECTION.md` | Authoritative strategy (pillars, metrics, what we don't do) |
| 3 | `docs/VISION_2026.md` | Full product vision (three horizons, user journeys, competitive landscape) |
| 4 | `docs/ROADMAP_2026.md` | Implementation plan (Phase 1-3, technical debt, success metrics) |
| 5 | `docs/TODO_MASTER.md` | Current task tracking |
| 6 | `docs/EXECUTIVE_REVIEW_2026-01.md` | Honest critique (CTO B-, PM B, Design A-, CEO C+, VC B-) |
| 7 | `docs/SECURITY_TODO.md` | Security issues and fixes |
| 8 | `docs/AI_MONEY_INTEGRATION_ANALYSIS.md` | What AI can/can't automate with money |
| 9 | `docs/ROADMAP_FEATURES.md` | Feature specs (scheduler, bridging, insights) |
| 10 | `docs/CIRCLE_INTEGRATION_PLAN.md` | Circle partnership technical plan |

---

## Coordination Notes

> This section is for cross-role observations. Any role can add a note here by editing this file.
> Format: `[ROLE] [DATE] note`

_No notes yet. Roles will add notes as they work._

---

## Sprint Backlog (Architect Maintains)

> This is populated after Sprint 0 assessments are complete.

_Pending Sprint 0 completion._

---
