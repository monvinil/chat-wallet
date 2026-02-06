# Workstream: DevOps Lead

> **Owner**: DevOps session
> **Status**: Sprint 0 COMPLETE
> **Last updated**: 2026-02-06

---

## Mandate

You are the DevOps lead. You own:
- Deployment strategy (where and how to host)
- Infrastructure architecture (containers, orchestration, CDN)
- Monitoring and observability (logs, metrics, alerts)
- Cost optimization (infrastructure spend projections)
- Scaling strategy (what breaks at 100, 1K, 10K users?)
- Reliability (uptime, failover, disaster recovery)
- Secret management

Your job is to answer: **"How do we go from 'works on my machine' to 'production-grade service'?"**

---

## Context to Read First

1. `docs/COMMAND_CENTER.md` - Project overview
2. `docs/QUICKSTART.md` - Current dev/deployment setup
3. `docs/SCHEDULER_DEPLOYMENT.md` - Scheduler worker deployment options
4. `docker-compose.yml` - Current Docker setup
5. `Dockerfile.api` - API container
6. `web/Dockerfile` - Frontend container
7. `.env.example` - Environment variables

## Current Infrastructure State
- **Not deployed to production** — everything runs locally
- Docker Compose orchestrates: API (port 8000), Web (port 3000), optional Scheduler
- Supabase is the only external service (hosted)
- Public RPC endpoints (no production reliability)
- No monitoring, no logging, no alerts
- No CI/CD pipeline
- No secret management (`.env` files)

---

## Sprint 0 Task Completion

### 1. Deployment Architecture Design — COMPLETE

- [x] Recommend hosting platform for each component
- [x] Evaluate cost at different scales (0, 100, 1K, 10K users)
- [x] Design the deployment pipeline (push to branch → staging → production)
- [x] Define environment strategy (dev, staging, production)

### 2. Infrastructure Configuration — COMPLETE

- [x] Review `docker-compose.yml` for production readiness
- [x] Review `Dockerfile.api` for security and optimization
- [x] Review `web/Dockerfile` for production optimization
- [x] Design health check endpoints
- [x] Create `docker-compose.production.yml`
- [x] Create `.dockerignore`

### 3. Monitoring & Observability — COMPLETE

- [x] Propose logging strategy
- [x] Propose metrics to track
- [x] Propose alerting rules
- [x] Evaluate tools and budget

### 4. Scaling Analysis — COMPLETE

- [x] Identify bottlenecks at 100, 1K, 10K users
- [x] Propose scaling solutions
- [x] Evaluate Redis needs

### 5. Security & Secrets — COMPLETE

- [x] Propose secret management solution
- [x] Review existing secrets handling
- [x] Propose key rotation strategy
- [x] HTTPS/TLS and DDoS protection

### 6. Cost Projections — COMPLETE

- [x] Model monthly costs at scale
- [x] Compare hosting platforms
- [x] Project RPC and Supabase costs

---

## Findings

### Hosting Platform Research

Evaluated 5 platforms (February 2026 pricing):

| Platform | Best For | Free Tier | Starter Cost | 10K Users |
|----------|----------|-----------|-------------|-----------|
| **Vercel** | Next.js frontend | Yes (non-commercial only) | $20/mo Pro | $20/mo |
| **Fly.io** | Always-on Python API | No (pay-as-you-go) | ~$6/mo | $25-130/mo |
| **Railway** | Quick Python deploys | $5 trial credit | $20/mo Pro | $40-60/mo |
| **Render** | All-in-one simplicity | Yes (30-60s cold starts) | $7/service/mo | $75/mo |
| **AWS Fargate** | Enterprise scale | None for Fargate | $34-40/mo | $50-80/mo |

**Key findings:**
- Fly.io has the lowest raw compute cost: shared-cpu-2x (512MB) = $4.04/mo
- Railway Pro ($20/mo) includes $20 usage credit but pricing is unpredictable
- Render free tier has crippling 30-60s cold starts — unusable for an API
- AWS ALB alone costs $16-22/mo — not justified below 50K users
- Vercel Hobby plan is non-commercial — must use Pro ($20/mo) for a startup

### Current Infrastructure Gaps

| Gap | Severity | Impact |
|-----|----------|--------|
| **No production deployment** | Critical | Product cannot be used by anyone |
| **No `.dockerignore`** | High | Docker images include `.env`, `.git`, `__pycache__` — bloated images + secrets leak |
| **`Dockerfile.api` runs as root** | High | Container breakout = full host compromise |
| **`web/Dockerfile` doesn't build for prod** | High | `RUN npm run build` is commented out; CMD runs `npm run dev` |
| **No multi-stage Docker builds** | Medium | Images ~1.2GB instead of ~200MB |
| **No CI/CD pipeline** | High | Manual deployment = human error, no test gate |
| **No secret management** | High | `.env` files with plaintext secrets, no rotation |
| **No monitoring/alerting** | High | Blind to errors, outages, failed transactions |
| **CORS allows wildcards** | Medium | `cors_allow_methods: ["*"]`, `cors_allow_headers: ["*"]` in `api/config.py` |
| **JWT secret has fallback default** | Critical | `api/config.py:36` falls back to hardcoded string — anyone can forge tokens |
| **No rate limiting per user** | Medium | `slowapi` uses IP-based limiting only — easily bypassed via NAT/proxy |
| **Health check uses `curl`** | Low | `curl` not installed in `python:3.11-slim` — health check silently fails |
| **Public RPCs in production** | High | Rate limited, unreliable, no SLA — will fail under load |
| **No connection pooling config** | Medium | Supabase SDK handles pooling, but no explicit configuration |

### Docker Review Details

**Dockerfile.api (current) — 6 issues found:**
1. `python:3.11-slim` base is fine
2. Installs `gcc` but no multi-stage build — compiler stays in production image
3. **No `.dockerignore`** — `COPY . .` copies `.env`, `.git`, `__pycache__`, `node_modules`
4. **Runs as root** — no `USER` directive
5. **HEALTHCHECK uses `curl`** — not installed in slim image, check silently fails
6. No `PYTHONDONTWRITEBYTECODE=1` or `PYTHONUNBUFFERED=1`

**web/Dockerfile (current) — 4 issues found:**
1. `node:20-alpine` base is good
2. **`npm run build` is commented out** — image has no production build
3. **CMD runs `npm run dev`** — development server with hot-reload in production
4. No multi-stage build — all devDependencies in final image

**docker-compose.yml (current) — 5 issues found:**
1. Mounts source volumes (`.:/app`) — fine for dev, disaster for prod (overwrites built code)
2. Runs API in `--debug` mode
3. JWT secret has fallback default in environment
4. No restart policies
5. No resource limits (can OOM the host)

### Deployment Recommendation

#### Architecture: Vercel (Frontend) + Fly.io (API + Scheduler)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PRODUCTION ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Users ──→ Vercel Edge Network ──→ Next.js Frontend (SSR)          │
│              │                        │                             │
│              │                    API calls to:                     │
│              │               api.usdchat.com (Fly.io)              │
│              │                        │                             │
│              │                        ▼                             │
│              │              Fly.io (iad region)                     │
│              │              ┌───────────────────┐                  │
│              │              │  usdchat-api      │ ←── FastAPI      │
│              │              │  shared-cpu-2x    │     uvicorn      │
│              │              │  512MB RAM        │     2 workers    │
│              │              └───────────────────┘                  │
│              │              ┌───────────────────┐                  │
│              │              │  usdchat-scheduler│ ←── worker mode  │
│              │              │  shared-cpu-1x    │     60s interval │
│              │              │  256MB RAM        │                  │
│              │              └───────────────────┘                  │
│              │                    │         │                       │
│              │                    ▼         ▼                       │
│              │         ┌──────────────┐ ┌──────────────┐           │
│              │         │  Supabase    │ │  Alchemy     │           │
│              │         │  PostgreSQL  │ │  RPC         │           │
│              │         │  + Auth      │ │  (free tier) │           │
│              │         └──────────────┘ └──────────────┘           │
└─────────────────────────────────────────────────────────────────────┘
```

#### Why This Stack

| Decision | Rationale |
|----------|-----------|
| **Vercel for frontend** | Best-in-class Next.js hosting. Edge caching, image optimization, zero-config deploys from GitHub. $20/mo Pro handles 10K+ users. |
| **Fly.io for API** | Cheapest always-on compute ($4.04/mo for 512MB shared). Docker-native deploys. Auto-TLS. Health checks and auto-restart. |
| **Fly.io for scheduler** | Same platform = shared secrets, unified deploy pipeline. $2.02/mo for 256MB. Restart on crash built-in. |
| **NOT Railway** | Pro plan ($20/mo) has usage-based pricing that's unpredictable. Fly.io's fixed VM pricing is better for budgeting a startup. |
| **NOT Render** | Free tier has 30-60s cold starts (kills UX for a wallet API). Starter ($7/service) costs more than Fly.io for same resources. |
| **NOT AWS** | ALB alone costs $16-22/mo. IAM/VPC/ECR complexity not justified <50K users. Public IPv4 now $3.60/mo each. |
| **Supabase stays hosted** | Already integrated. Free tier: 500MB DB + 50K monthly auth requests. Only upgrade at ~5K users. |

#### Environment Strategy

| Environment | Purpose | Infrastructure |
|-------------|---------|----------------|
| **Development** | Local coding | `docker-compose.yml` (existing) or bare metal (`run_api.py --debug`) |
| **Staging** | Pre-production validation | Fly.io separate app (`usdchat-staging`), Vercel preview deploys (automatic on PR) |
| **Production** | Live users | Fly.io `usdchat-api` + `usdchat-scheduler`, Vercel production deploy |

#### Deployment Pipeline

```
Developer pushes to GitHub
    │
    ├── Push to feature branch (PR) ─→ Vercel preview deploy (frontend, automatic)
    │                                ─→ GitHub Actions: lint + test (backend)
    │
    └── Merge to `main` ──→ Vercel production deploy (frontend, automatic)
                          ──→ GitHub Actions: test → build → fly deploy (API)
                          ──→ GitHub Actions: fly deploy (scheduler)
```

### Scaling Bottlenecks

#### At 100 Users

| Component | Status | Notes |
|-----------|--------|-------|
| Frontend (Vercel) | OK | Edge CDN handles trivially |
| API (Fly.io shared-2x) | OK | ~10 req/sec well within capacity |
| Scheduler | OK | 50 tasks/batch, 1-min interval |
| Supabase (free) | OK | 500MB DB, 50K auth |
| Public RPCs | **WARNING** | May hit rate limits with 100 concurrent balance checks |

**Action needed**: Get Alchemy free tier (300M compute units/mo) before launch.

#### At 1,000 Users

| Component | Status | Fix | Added Cost |
|-----------|--------|-----|-----------|
| API | **Stress** | Scale to 2x shared-cpu-4x replicas | +$12/mo |
| Supabase (free) | **Exceeded** | Upgrade to Pro ($25/mo) for pooling + 8GB storage | +$25/mo |
| RPC | **Breaks** | Alchemy Growth tier or multiple free-tier keys | $0-49/mo |
| Scheduler | **Queue growth** | Reduce interval to 30s or add second worker | +$2/mo |
| Rate limiting | **Bypass risk** | Add per-user rate limiting (JWT-based, needs Redis) | +$0 (Upstash free) |

#### At 10,000 Users

| Component | Status | Fix | Cost |
|-----------|--------|-----|------|
| API | **Needs horizontal scaling** | 3-4x performance-1x replicas (dedicated CPU) | ~$130/mo |
| Supabase | **Connection limits** | Pro plan + PgBouncer connection pooling | $25/mo |
| RPC | **Expensive volume** | Alchemy Scale ($199/mo) or multi-provider failover | $49-199/mo |
| Scheduler | **Throughput limits** | Multiple workers + task sharding by user_id hash | ~$10/mo |
| Frontend | OK | Vercel Pro handles easily | $20/mo |
| Monitoring | **Required** | Sentry Pro + Grafana Cloud | ~$30/mo |

#### Do We Need Redis?

**Yes, but not yet.** Recommendation: Upstash (serverless Redis) when the need arises.

| Need | When to Add | Why |
|------|-------------|-----|
| Per-user rate limiting | 500+ users | `slowapi` is IP-based only — bypassed by NAT/proxy users |
| Balance caching | 500+ users | `chain_utils.py:34` has 60s in-memory cache, but it's per-process; multi-worker = redundant RPC calls |
| JWT revocation blocklist | 1K+ users | JWT is stateless; can't revoke tokens without a shared store |

**Upstash free tier**: 10K commands/day, 256MB. Sufficient up to ~2K users. Then $10/mo.

---

## Monitoring & Observability

### Logging Strategy

**Current state**: `utils/logger.py` — Python stdlib logging to stdout. No structured format, no correlation IDs.

**Recommended progression:**

| Stage | Tool | Cost | Retention |
|-------|------|------|-----------|
| Launch | Fly.io built-in logs | $0 | 7 days |
| 500+ users | Add Axiom or Logtail | $0 (free: 500MB/mo ingest) | 30 days |
| 5K+ users | Grafana Cloud or Datadog | $23/mo (5GB/day) | 90 days |

**Action item**: Add structured JSON logging format to `utils/logger.py` before launch — makes log aggregation tools useful from day one.

### Metrics to Track

| Metric | Source | Alert Threshold |
|--------|--------|----------------|
| API response time (p50, p95, p99) | Fly.io metrics / Sentry | p95 > 2s |
| Error rate (5xx responses) | Sentry | > 1% of requests for 5 min |
| Scheduler task success rate | Custom metric (DB query) | < 95% success |
| RPC call latency | Custom instrumentation | p95 > 5s |
| RPC error rate | Custom instrumentation | > 5% errors |
| Failed transactions (send/yield/DCA) | DB `task_runs` table | Any failure |
| Active users (DAU/WAU/MAU) | Supabase auth logs | N/A (business metric) |
| DB connection count | Supabase dashboard | > 80% of plan limit |
| Memory usage (API/scheduler) | Fly.io metrics | > 80% of allocation |

### Alerting Rules

| Alert | Channel | Condition |
|-------|---------|-----------|
| API down | Slack + PagerDuty | Health check (`/health`) fails 3x consecutive |
| High error rate | Slack | 5xx > 5% of requests for 5 minutes |
| Scheduler stopped | Slack | No task runs recorded for 10 minutes |
| Failed transaction | Slack | Any send/yield/DCA execution failure |
| Database near capacity | Email | Storage > 80% of plan limit |
| RPC degraded | Slack | RPC error rate > 10% for 5 minutes |
| SSL cert expiring | Email | < 14 days to expiry (backup — Fly auto-renews) |

### Tool Recommendations

| Tool | Purpose | Cost | When to Add |
|------|---------|------|-------------|
| **Sentry** (free tier) | Error tracking + performance | $0 (5K events/mo) | Launch |
| **Fly.io metrics** | Infrastructure CPU/memory/network | $0 (included) | Launch |
| **UptimeRobot** (free tier) | External uptime monitoring | $0 (50 monitors) | Launch |
| **Axiom** (free tier) | Log aggregation + search | $0 (500MB/mo) | 500+ users |
| **Grafana Cloud** (free tier) | Dashboards + custom metrics | $0 (10K series) | 1K+ users |
| **BetterStack** | Incident management + status page | $0 (free tier) | 1K+ users |

**Total monitoring cost at launch: $0/mo**

---

## Security & Secrets

### Secret Inventory

| Secret | Current Location | Risk Level | Notes |
|--------|-----------------|------------|-------|
| `SUPABASE_URL` | `.env` | Low | Publicly discoverable |
| `SUPABASE_ANON_KEY` | `.env` | Low | Public key, RLS-protected |
| `SUPABASE_SERVICE_KEY` | `.env` | **CRITICAL** | Bypasses ALL Row Level Security — full DB access |
| `JWT_SECRET_KEY` | `.env` + hardcoded fallback | **CRITICAL** | Forge any user's auth token. Fallback at `api/config.py:36` |
| `SCHEDULER_ENCRYPTION_SECRET` | `.env` | **CRITICAL** | Decrypts user private keys for auto-execution |
| `TASK_EXECUTOR_SECRET` | `.env` | Medium | HTTP endpoint auth for scheduler |
| `ALCHEMY_API_KEY` | `.env` (optional) | Medium | Rate limit abuse, cost |
| `CIRCLE_API_KEY` | `.env` (optional) | High | Financial API access |
| `OPENAI_API_KEY` | `.env` (optional) | Medium | Cost abuse |

### Secret Management Strategy

**Stage 1 — Launch**: Platform-native secrets
- **Fly.io**: `fly secrets set KEY=value` — encrypted at rest, injected as env vars at runtime. Never stored in code or CI logs.
- **Vercel**: Dashboard → Settings → Environment Variables — encrypted, can be scoped per-environment (production/preview/development).
- **CRITICAL FIX**: Remove hardcoded JWT fallback in `api/config.py:36`. The API must fail to start if `JWT_SECRET_KEY` is not set.

**Stage 2 — 1K+ users**: Team secret management
- Add [Doppler](https://doppler.com) or [1Password CLI](https://developer.1password.com/docs/cli/) for shared team access.
- Single source of truth for all secrets across environments.
- Audit trail for who accessed what.

**Stage 3 — 10K+ users**: Dynamic secrets
- HashiCorp Vault or AWS Secrets Manager for auto-rotating database credentials.
- Secret versioning and rollback capability.

### Key Rotation Strategy

| Secret | Rotation Frequency | Method |
|--------|--------------------|--------|
| `JWT_SECRET_KEY` | Every 90 days | Deploy new key; old key remains valid for 24h overlap window (accept both during transition) |
| `SCHEDULER_ENCRYPTION_SECRET` | Every 180 days | Re-encrypt all stored private keys with new secret in a migration script |
| `SUPABASE_SERVICE_KEY` | On compromise only | Regenerate in Supabase dashboard → redeploy all services |
| RPC API keys (Alchemy/Infura) | Every 90 days | Rotate in provider dashboard → update Fly.io secrets |

### HTTPS/TLS

| Component | TLS Provider | Custom Domain |
|-----------|-------------|---------------|
| Frontend (Vercel) | Automatic Let's Encrypt | CNAME `app.usdchat.com` → Vercel |
| API (Fly.io) | Automatic TLS for `*.fly.dev` and custom domains | CNAME `api.usdchat.com` → Fly.io |

Both platforms handle HTTP → HTTPS redirect automatically. No manual certificate management needed.

### DDoS Protection

| Layer | Protection | Cost |
|-------|------------|------|
| Edge (frontend) | Vercel built-in DDoS protection | Included in Pro |
| Network (API) | Fly.io Anycast network absorbs volumetric attacks | Included |
| Application | `slowapi` rate limiting (IP-based; upgrade to per-user at 500+ users) | $0 |
| Optional | Cloudflare free tier in front of API domain | $0 |

---

## Infrastructure Cost Model

### Recommended Stack (Vercel + Fly.io)

| Component | 100 users | 1K users | 10K users |
|-----------|-----------|----------|-----------|
| **Vercel Pro** (frontend) | $20/mo | $20/mo | $20/mo |
| **Fly.io API** (shared-cpu-2x, 512MB) | $4/mo | $16/mo (2 replicas, cpu-4x) | $130/mo (4x perf-1x) |
| **Fly.io Scheduler** (shared-cpu-1x, 256MB) | $2/mo | $4/mo | $10/mo (2 workers) |
| **Fly.io IPv4** (dedicated) | $2/mo | $2/mo | $2/mo |
| **Supabase** | $0 (free) | $25/mo (Pro) | $25/mo (Pro) |
| **Alchemy RPC** | $0 (free: 300M CU) | $0 (free) | $49/mo (Growth) |
| **Sentry** (error tracking) | $0 (free: 5K events) | $0 (free) | $26/mo (Team) |
| **UptimeRobot** (uptime monitoring) | $0 (free) | $0 (free) | $0 (free) |
| **Upstash Redis** (caching/rate-limit) | — | $0 (free: 10K cmd/day) | $10/mo |
| **Domain** (annual ÷ 12) | $1/mo | $1/mo | $1/mo |
| | | | |
| **TOTAL** | **$29/mo** | **$68/mo** | **$273/mo** |

### Alternative Stack Comparison

| Scale | Vercel+Fly.io (recommended) | Vercel+Railway | All-Render | AWS Fargate |
|-------|---------------------------|----------------|------------|-------------|
| 100 users | **$29/mo** | $45/mo | $21/mo* | $55/mo |
| 1K users | **$68/mo** | $90/mo | $94/mo | $85/mo |
| 10K users | **$273/mo** | $320/mo | $270/mo | $250/mo |

*\*Render $21/mo uses Starter instances (0.5 CPU) — may be insufficient for a FastAPI wallet API.*

### Supabase Pricing Detail

| Tier | Price | Database | Auth | Storage |
|------|-------|----------|------|---------|
| Free | $0/mo | 500MB, 2 projects max | 50K MAU | 1GB |
| Pro | $25/mo | 8GB, unlimited projects | 100K MAU | 100GB |
| Team | $599/mo | 16GB | 100K MAU | 100GB |

At 10K users, database size will be ~100-500MB. Pro tier ($25/mo) is sufficient through at least 50K users.

### RPC Cost Projection

| Provider | Free Tier | Growth | Scale |
|----------|-----------|--------|-------|
| **Alchemy** | 300M CU/mo | $49/mo (400M CU) | $199/mo (1.5B CU) |
| **Infura** | 100K req/day | $50/mo (unlimited Core) | $225/mo |

At 100 users: ~50K RPC calls/day (balance checks + tx submissions). Alchemy free tier covers this easily.
At 10K users: ~500K RPC calls/day. Growth tier ($49/mo) needed.

---

## Recommendations

### Before Launch (Blocking)

1. **[CRITICAL] Remove JWT secret fallback** — `api/config.py:36` must raise an error if `JWT_SECRET_KEY` is not set. Currently falls back to `"CHANGE-THIS-IN-PRODUCTION-use-secrets-token-hex-32"` which means anyone can forge auth tokens.
2. **[CRITICAL] Create `.dockerignore`** — prevent `.env`, `.git`, `__pycache__` from entering Docker images. **DONE: file created.**
3. **[CRITICAL] Use production Dockerfiles** — multi-stage builds, non-root user, no dev dependencies. **DONE: `Dockerfile.api.production` and `web/Dockerfile.production` created.**
4. **[HIGH] Set up Fly.io apps** — create `usdchat-api` and `usdchat-scheduler`, set secrets via `fly secrets set`.
5. **[HIGH] Set up Vercel project** — connect GitHub repo, configure `web/` as root directory.
6. **[HIGH] Get Alchemy free tier API key** — reliable RPC endpoint for mainnet. Public RPCs will fail under load.
7. **[HIGH] Generate production secrets** — `python -c "import secrets; print(secrets.token_urlsafe(32))"` for JWT key and scheduler encryption key.
8. **[HIGH] Configure CORS for production** — replace wildcard methods/headers in `api/config.py:26-33` with actual production domain.
9. **[MEDIUM] Set up Sentry** — free tier error tracking, 5K events/mo. Catch errors from day 1.
10. **[MEDIUM] Set up UptimeRobot** — free external monitoring on `/health` and `/ready` endpoints.

### First Month Post-Launch

1. Add structured JSON logging to `utils/logger.py` (format: `{"timestamp", "level", "message", "request_id", ...}`)
2. Set up Axiom or Logtail for centralized log search (free tier)
3. Add per-user rate limiting using JWT claims + Upstash Redis
4. Set up staging environment (`usdchat-staging` on Fly.io)
5. Configure Cloudflare DNS for CDN + additional DDoS layer (free tier)
6. Add Upstash Redis for balance caching if RPC costs rise

### First Quarter

1. Implement JWT key rotation (90-day cycle with 24h overlap)
2. Add end-to-end API tests in CI/CD pipeline
3. Set up Grafana dashboards for business + infrastructure metrics
4. Evaluate Supabase Pro upgrade timing based on actual usage
5. Performance/load testing with k6 (target: 100 concurrent users, p95 < 2s)
6. Add database backup verification (Supabase does daily backups on Pro, but verify restore works)
7. Document runbook for common incidents (API down, scheduler stuck, RPC degraded)

---

## Files Created

All infrastructure configs are on the `claude/setup-production-deployment-sQo0k` branch and will be merged:

| File | Purpose |
|------|---------|
| `.dockerignore` | Prevents secrets and dev files from entering Docker images |
| `Dockerfile.api.production` | Multi-stage build, non-root user, venv isolation, Python-based health check |
| `web/Dockerfile.production` | 3-stage build (deps → build → run), non-root user, production `npm start` |
| `docker-compose.production.yml` | Production compose with resource limits, health checks, restart policies |
| `fly.toml` | Fly.io API deployment: shared-cpu-2x, 512MB, auto-start/stop, health checks |
| `fly.scheduler.toml` | Fly.io scheduler worker: shared-cpu-1x, 256MB, background process |
| `web/vercel.json` | Vercel config with security headers (X-Frame-Options, X-Content-Type-Options, XSS-Protection) |
| `.github/workflows/test.yml` | CI: Python lint + test, Next.js lint + build, Docker build verification on PRs |
| `.github/workflows/deploy.yml` | CD: test gate → fly deploy API + scheduler on merge to main |

---

## Urgent Flags

### 1. JWT Secret Hardcoded Fallback (CRITICAL)
**File**: `api/config.py:36`
**Issue**: `jwt_secret_key` defaults to `"CHANGE-THIS-IN-PRODUCTION-use-secrets-token-hex-32"`. If `JWT_SECRET_KEY` env var is unset, the API silently uses this known string. Any attacker can forge authentication tokens for any user.
**Fix**: Change to `jwt_secret_key: str = os.environ["JWT_SECRET_KEY"]` (fail if not set) or add a startup validation check.

### 2. Scheduler Encryption Secret Exposure Risk (HIGH)
**File**: `scheduler_executor.py:177`
`SCHEDULER_ENCRYPTION_SECRET` can decrypt user private keys stored in the database. This is the most sensitive secret in the system. Verify:
- It is never logged (not even at DEBUG level)
- It is never included in error messages or stack traces
- The Fly.io secret store is the only place it exists

### 3. Docker Images Would Leak Secrets (CRITICAL — FIXED)
**Issue**: No `.dockerignore` existed. `COPY . .` in Dockerfiles would copy `.env` (with all secrets), `.git/` history, and potentially credentials into container images. If images were ever pushed to a registry, secrets are exposed permanently.
**Fix**: `.dockerignore` created — excludes `.env*`, `.git`, `__pycache__`, `node_modules`, docs, tests.

### 4. Supabase Service Key Over-Privileged (MEDIUM)
**File**: API routes use `SUPABASE_SERVICE_KEY` (bypasses ALL Row Level Security). Both API and scheduler have this key. If either service is compromised, attacker gets full read/write access to all user data.
**Recommendation**: API should use anon key + JWT auth for user-scoped operations where possible. Reserve service key for admin operations only. Audit which routes actually need the service key.

---
