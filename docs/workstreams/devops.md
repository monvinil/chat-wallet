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

### Current Infrastructure Gaps

| Gap | Severity | Impact |
|-----|----------|--------|
| **No production deployment** | Critical | Product cannot be used |
| **No .dockerignore** | High | Docker images include `.env`, `.git`, `__pycache__` (bloated + secrets leak) |
| **Dockerfile.api runs as root** | High | Container breakout = host compromise |
| **web/Dockerfile doesn't build for prod** | High | `RUN npm run build` is commented out, CMD runs `npm run dev` |
| **No multi-stage Docker builds** | Medium | Images ~1.2GB instead of ~200MB |
| **No CI/CD pipeline** | High | Manual deployment = human error |
| **No secret management** | High | `.env` files with plaintext secrets |
| **No monitoring/alerting** | High | Blind to errors, no incident response |
| **CORS allows wildcards** | Medium | `cors_allow_methods: ["*"]`, `cors_allow_headers: ["*"]` |
| **JWT secret has fallback default** | Critical | `api/config.py:36` falls back to hardcoded string |
| **No rate limiting per user** | Medium | `slowapi` uses IP-based limiting only — easily bypassed |
| **Health check uses `curl`** | Low | Requires curl in slim image; `wget` or Python check better |
| **Streamlit `@st.cache_resource`** | Low | `supabase_client.py:44` uses Streamlit cache in API context — works but fragile |
| **No connection pooling** | Medium | Supabase SDK handles this, but no explicit pool config |
| **Public RPCs in production** | High | Rate limited, unreliable, no SLA |

### Docker Review Details

**Dockerfile.api Issues:**
1. `python:3.11-slim` is fine for base
2. Installs `gcc` but doesn't clean apt cache properly (apt lists removed, good)
3. **No multi-stage build**: dev dependencies in production image
4. **Runs as root**: no `USER` directive
5. **COPY . .** includes everything (no .dockerignore)
6. **HEALTHCHECK uses `curl`**: not installed in slim image by default — this check silently fails
7. No `PYTHONDONTWRITEBYTECODE=1` or `PYTHONUNBUFFERED=1`

**web/Dockerfile Issues:**
1. `node:20-alpine` is good
2. **`npm run build` is commented out** — no production build
3. **CMD runs `npm run dev`** — dev server with hot-reload in production
4. **HEALTHCHECK uses `wget`**: works on alpine, but checks `/` which may redirect
5. No multi-stage build (node_modules in final image)
6. No `.dockerignore` for web directory

**docker-compose.yml Issues:**
1. Mounts source volumes (`.:/app`) — fine for dev, disaster for prod
2. Runs `--debug` mode by default
3. JWT secret has fallback default
4. No restart policies
5. No resource limits
6. No networking isolation

---

## Deployment Recommendation

### Architecture: Vercel (Frontend) + Fly.io (API + Scheduler)

After evaluating 5 platforms across cost, DX, scalability, and reliability, the recommended stack is:

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCTION ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Users ──→ Vercel Edge Network ──→ Next.js Frontend (SSR)  │
│              │                        │                     │
│              │                    API calls                  │
│              │                        │                      │
│              │                        ▼                      │
│              │              Fly.io (iad region)              │
│              │              ┌──────────────┐                │
│              │              │  API Server  │ ←── FastAPI    │
│              │              │  (shared-2x) │     uvicorn    │
│              │              └──────────────┘                │
│              │              ┌──────────────┐                │
│              │              │  Scheduler   │ ←── worker     │
│              │              │  (shared-1x) │     mode       │
│              │              └──────────────┘                │
│              │                    │                          │
│              │                    ▼                          │
│              │         ┌────────────────────┐               │
│              │         │   Supabase (hosted)│               │
│              │         │  PostgreSQL + Auth │               │
│              │         └────────────────────┘               │
│              │                    │                          │
│              │                    ▼                          │
│              │         ┌────────────────────┐               │
│              │         │  Alchemy/Infura    │               │
│              │         │  (RPC endpoints)   │               │
│              │         └────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

### Why This Stack

| Decision | Rationale |
|----------|-----------|
| **Vercel for frontend** | Best-in-class Next.js hosting. Automatic edge caching, image optimization, zero-config deploys. $20/mo Pro plan handles 10K+ users easily. |
| **Fly.io for API** | Cheapest always-on compute ($4.04/mo for 512MB). Global edge network when needed. Simple Docker deploys. Health checks and auto-restart built in. |
| **Fly.io for scheduler** | Same platform as API = shared secrets, same deploy pipeline. $2.02/mo for 256MB shared instance. |
| **NOT Railway** | Railway Pro ($20/mo) includes $20 credit but usage-based pricing makes costs unpredictable. Fly.io's fixed pricing is better for budgeting. |
| **NOT Render** | Free tier has 30-60s cold starts (kills UX). Starter tier ($7/service) costs more than Fly.io for equivalent resources. |
| **NOT AWS** | ALB alone costs $16-22/mo. Operational complexity (VPC, IAM, ECR) not justified at this scale. Revisit at 50K+ users. |
| **Supabase stays hosted** | Already integrated. Free tier handles 500MB DB + 50K monthly auth. Only external dependency. |

### Environment Strategy

| Environment | Purpose | Infrastructure |
|-------------|---------|----------------|
| **Development** | Local coding | `docker-compose.yml` (existing) or bare metal |
| **Staging** | Pre-production validation | Fly.io separate app (`usdchat-staging`), Vercel preview deploys |
| **Production** | Live users | Fly.io `usdchat-api` + `usdchat-scheduler`, Vercel production |

### Deployment Pipeline

```
Developer pushes to GitHub
    │
    ├── Push to `main` ──→ Vercel auto-deploy (frontend)
    │                  ──→ GitHub Actions: test → build → fly deploy (API)
    │                  ──→ GitHub Actions: fly deploy (scheduler)
    │
    └── Push to PR ──→ Vercel preview deploy (frontend)
                   ──→ GitHub Actions: test only (backend)
```

---

## Scaling Analysis

### What Breaks at 100 Users

| Component | Status | Notes |
|-----------|--------|-------|
| Frontend (Vercel) | OK | Edge CDN handles this trivially |
| API (Fly.io shared-2x) | OK | ~10 req/sec is well within capacity |
| Scheduler | OK | Processes 50 tasks/batch, 1-min intervals |
| Supabase (free) | OK | 500MB DB, 50K auth requests |
| Public RPCs | **WARNING** | May hit rate limits with 100 concurrent users doing balance checks |

**Action needed**: Get Alchemy free tier (300M compute units/mo) before launch.

### What Breaks at 1,000 Users

| Component | Status | Fix |
|-----------|--------|-----|
| API | **Stress** | Scale to 2x shared-cpu-4x replicas ($16/mo) |
| Supabase (free) | **Exceeded** | Upgrade to Pro ($25/mo) — need connection pooling |
| RPC | **Breaks** | Alchemy Growth tier ($49/mo) or multiple free-tier keys |
| Scheduler | **Queue growth** | Reduce interval to 30s or add second worker |
| Rate limiting | **Bypass risk** | Add per-user rate limiting (JWT-based) |

**Action needed**: Redis (Upstash free tier) for rate limiting + caching.

### What Breaks at 10,000 Users

| Component | Status | Fix | Cost |
|-----------|--------|-----|------|
| API | **Needs scaling** | 3-4x performance-1x replicas behind Fly proxy | ~$130/mo |
| Supabase | **Connection limits** | Pro plan + PgBouncer pooling | $25/mo |
| RPC | **Expensive** | Alchemy Scale ($199/mo) or self-hosted RPC node | $199/mo |
| Scheduler | **Throughput** | Multiple workers + task sharding | ~$10/mo |
| Frontend | OK | Vercel Pro handles this | $20/mo |
| Monitoring | **Required** | Sentry Pro + Grafana Cloud | ~$30/mo |

**Total at 10K**: ~$400-500/mo (see cost model below)

### Do We Need Redis?

**Yes, but not yet.** Use Upstash (serverless Redis) when needed:

| Need | When | Why |
|------|------|-----|
| Per-user rate limiting | 500+ users | Current IP-based slowapi is easily bypassed by NAT/proxy |
| Balance caching | Now | 60s cache in `chain_utils.py` is in-memory per-process; multi-worker = redundant RPC calls |
| Session store | 1K+ users | JWT is stateless but revocation needs a blocklist |

**Recommendation**: Add Upstash free tier (10K commands/day) at 500 users. Cost: $0 → $10/mo at scale.

---

## Monitoring & Observability

### Logging Strategy

**Current**: `utils/logger.py` — Python logging to stdout. No structured format.

**Recommended**: Structured JSON logging with correlation IDs.

```
Stage 1 (Launch): Fly.io built-in log aggregation (free, 7-day retention)
Stage 2 (500+ users): Add Axiom or Logtail ($0 free tier, 500MB/mo ingest)
Stage 3 (5K+ users): Grafana Cloud or Datadog ($23/mo for 5GB/day ingest)
```

### Metrics to Track

| Metric | Source | Alert Threshold |
|--------|--------|----------------|
| API response time (p50, p95, p99) | Fly.io metrics | p95 > 2s |
| Error rate (5xx) | Sentry / logs | > 1% of requests |
| Scheduler task success rate | Custom metric | < 95% success |
| RPC call latency | Custom metric | p95 > 5s |
| RPC error rate | Custom metric | > 5% errors |
| Failed transactions | DB query | Any failure |
| Active users (DAU/WAU) | Supabase auth | N/A (business metric) |
| DB connection count | Supabase dashboard | > 80% of limit |

### Alerting Rules

| Alert | Channel | Condition |
|-------|---------|-----------|
| API down | Slack/PagerDuty | Health check fails 3x consecutive |
| High error rate | Slack | 5xx > 5% for 5 minutes |
| Scheduler stopped | Slack | No task runs for 10 minutes |
| Failed transaction | Slack | Any send/yield/DCA failure |
| DB near capacity | Email | Storage > 80% |
| RPC degraded | Slack | Error rate > 10% for 5 minutes |

### Tool Recommendations

| Tool | Purpose | Cost | When |
|------|---------|------|------|
| **Sentry** (free tier) | Error tracking + alerting | $0 (5K events/mo) | Launch |
| **Fly.io metrics** | Infrastructure metrics | $0 (included) | Launch |
| **UptimeRobot** (free) | External uptime monitoring | $0 (50 monitors) | Launch |
| **Axiom** (free tier) | Log aggregation | $0 (500MB/mo) | 500+ users |
| **Grafana Cloud** (free) | Dashboards + metrics | $0 (10K series) | 1K+ users |
| **BetterStack** | Incident management | $0 (free tier) | 1K+ users |

**Total monitoring cost at launch: $0/mo**

---

## Security & Secrets

### Secret Inventory

| Secret | Location | Risk Level |
|--------|----------|------------|
| `SUPABASE_URL` | `.env` | Low (public info) |
| `SUPABASE_ANON_KEY` | `.env` | Low (public, RLS-protected) |
| `SUPABASE_SERVICE_KEY` | `.env` | **CRITICAL** (bypasses all RLS) |
| `JWT_SECRET_KEY` | `.env` / hardcoded fallback | **CRITICAL** (forges auth tokens) |
| `SCHEDULER_ENCRYPTION_SECRET` | `.env` | **CRITICAL** (decrypts user private keys) |
| `TASK_EXECUTOR_SECRET` | `.env` | Medium (scheduler HTTP auth) |
| `ALCHEMY_API_KEY` | `.env` (optional) | Medium (rate limit abuse) |
| `CIRCLE_API_KEY` | `.env` (optional) | High (financial API) |
| `OPENAI_API_KEY` | `.env` (optional) | Medium (cost abuse) |

### Secret Management Strategy

**Stage 1 (Launch)**: Fly.io Secrets + Vercel Environment Variables
- `fly secrets set KEY=value` — encrypted at rest, injected as env vars
- Vercel dashboard → Settings → Environment Variables (encrypted, per-environment)
- **Remove hardcoded JWT fallback** in `api/config.py:36` — must fail if not set

**Stage 2 (1K+ users)**: Add 1Password/Doppler for team secret sharing
- Single source of truth for all secrets
- Audit trail for secret access
- Automatic rotation reminders

**Stage 3 (10K+ users)**: HashiCorp Vault or AWS Secrets Manager
- Dynamic secrets for database credentials
- Automatic key rotation
- Secret versioning

### Key Rotation Strategy

| Secret | Rotation Frequency | Method |
|--------|--------------------|--------|
| JWT_SECRET_KEY | Every 90 days | Deploy new key, old key valid for 24h (overlap) |
| SCHEDULER_ENCRYPTION_SECRET | Every 180 days | Re-encrypt all stored keys with new secret |
| SUPABASE_SERVICE_KEY | On compromise only | Regenerate in Supabase dashboard |
| RPC API keys | Every 90 days | Rotate in Alchemy/Infura dashboard |

### HTTPS/TLS

- **Vercel**: Automatic HTTPS via Let's Encrypt (included)
- **Fly.io**: Automatic TLS certificates for `*.fly.dev` domains and custom domains
- **Custom domain**: Add CNAME to Fly.io, TLS auto-provisioned
- **Force HTTPS**: Both platforms handle HTTP → HTTPS redirect automatically

### DDoS Protection

- **Vercel**: Built-in DDoS protection at edge (included in Pro)
- **Fly.io**: Anycast network absorbs volumetric attacks
- **Application layer**: `slowapi` rate limiting (needs per-user upgrade)
- **Additional**: Cloudflare free tier in front of API if needed ($0)

---

## Infrastructure Cost Model

### Recommended Stack Costs

| Component | 100 users | 1K users | 10K users |
|-----------|-----------|----------|-----------|
| **Vercel Pro** (frontend) | $20/mo | $20/mo | $20/mo |
| **Fly.io API** (shared-cpu-2x, 512MB) | $4/mo | $16/mo (2 replicas) | $130/mo (4x perf-1x) |
| **Fly.io Scheduler** (shared-cpu-1x, 256MB) | $2/mo | $4/mo | $10/mo (2 workers) |
| **Fly.io IPv4** | $2/mo | $2/mo | $2/mo |
| **Supabase** | $0/mo (free) | $25/mo (Pro) | $25/mo (Pro) |
| **Alchemy RPC** | $0/mo (free) | $0/mo (free) | $49/mo (Growth) |
| **Sentry** (error tracking) | $0/mo (free) | $0/mo (free) | $26/mo |
| **UptimeRobot** | $0/mo (free) | $0/mo (free) | $0/mo (free) |
| **Upstash Redis** | $0 | $0/mo (free) | $10/mo |
| **Domain** (annual) | $1/mo (~$12/yr) | $1/mo | $1/mo |
| | | | |
| **TOTAL** | **$29/mo** | **$68/mo** | **$273/mo** |

### Cost Comparison: Recommended vs Alternatives

| Scale | Vercel+Fly.io (rec.) | Vercel+Railway | All-Render | AWS Fargate |
|-------|---------------------|----------------|------------|-------------|
| 100 users | **$29/mo** | $45/mo | $21/mo* | $55/mo |
| 1K users | **$68/mo** | $90/mo | $94/mo | $85/mo |
| 10K users | **$273/mo** | $320/mo | $270/mo | $250/mo |

*\*Render $21/mo uses Starter instances which have 0.5 CPU — may be insufficient.*

### Supabase Pricing Detail

| Tier | Price | Database | Auth | Storage | Bandwidth |
|------|-------|----------|------|---------|-----------|
| Free | $0/mo | 500MB, 2 projects | 50K MAU | 1GB | 2GB |
| Pro | $25/mo | 8GB, unlimited | 100K MAU | 100GB | 250GB |
| Team | $599/mo | 16GB | 100K MAU | 100GB | 250GB |

**At 10K users**: Pro tier ($25/mo) is sufficient. Database will be ~100MB-500MB.

### RPC Cost Projection

| Provider | Free Tier | Growth | Scale |
|----------|-----------|--------|-------|
| Alchemy | 300M CU/mo | $49/mo (400M CU) | $199/mo (1.5B CU) |
| Infura | 100K req/day | $50/mo | $225/mo |

**At 100 users**: ~50K RPC calls/day (balance checks, tx submissions). Alchemy free tier covers this.
**At 10K users**: ~500K RPC calls/day. Need Growth tier ($49/mo).

---

## Recommendations

### Before Launch (Blocking)

1. **[CRITICAL] Remove JWT secret fallback** — `api/config.py:36` must raise error if `JWT_SECRET_KEY` not set
2. **[CRITICAL] Create `.dockerignore`** — prevent secrets and dev files from entering images
3. **[CRITICAL] Production Dockerfiles** — multi-stage builds, non-root user, no dev dependencies
4. **[HIGH] Set up Fly.io apps** — `usdchat-api` and `usdchat-scheduler`
5. **[HIGH] Set up Vercel project** — connect GitHub repo, configure `web/` as root
6. **[HIGH] Get Alchemy free tier** — reliable RPC for mainnet operations
7. **[HIGH] Generate production secrets** — JWT key, scheduler encryption key
8. **[HIGH] Configure CORS** — replace wildcard with actual production domain
9. **[MEDIUM] Set up Sentry** — free tier error tracking from day 1
10. **[MEDIUM] Set up UptimeRobot** — external health monitoring

### First Month Post-Launch

1. Add structured JSON logging
2. Set up Axiom/Logtail for log aggregation
3. Add per-user rate limiting (JWT-based)
4. Set up staging environment on Fly.io
5. Add Upstash Redis for caching if RPC costs are high
6. Configure Cloudflare DNS (free CDN + DDoS protection)

### First Quarter

1. Implement proper secret rotation schedule
2. Add end-to-end tests in CI/CD
3. Set up Grafana dashboards for business metrics
4. Evaluate Supabase Pro upgrade timing
5. Add database backup verification (Supabase does daily backups on Pro)
6. Performance testing (load test API with k6 or similar)

---

## Urgent Flags

1. **`api/config.py:36`** — JWT secret has hardcoded fallback `"CHANGE-THIS-IN-PRODUCTION-use-secrets-token-hex-32"`. If `JWT_SECRET_KEY` env var is not set, the API silently uses this known string. Anyone can forge auth tokens. **Must be fixed before production.**

2. **`scheduler_executor.py`** handles `SCHEDULER_ENCRYPTION_SECRET` which can decrypt user private keys. This secret must never be exposed in logs, error messages, or environment variable dumps. The current code at line 177 decrypts keys in-memory — verify no logging of decrypted material.

3. **No `.dockerignore`** — current Docker builds will copy `.env`, `.git/`, `__pycache__/`, `node_modules/`, and potentially sensitive data into images. If images are ever pushed to a registry, secrets are exposed.

4. **Supabase service key** (`SUPABASE_SERVICE_KEY`) bypasses all Row Level Security. It's used by both the API and scheduler. If either is compromised, all user data is accessible. Consider principle-of-least-privilege: API should use anon key + JWT where possible.

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `docs/workstreams/devops.md` | This document — full Sprint 0 findings |
| `.dockerignore` | Prevent secrets/dev files in Docker images |
| `Dockerfile.api.production` | Production-optimized API container |
| `web/Dockerfile.production` | Production-optimized frontend container |
| `docker-compose.production.yml` | Production compose file |
| `fly.toml` | Fly.io API deployment config |
| `fly.scheduler.toml` | Fly.io scheduler deployment config |
| `web/vercel.json` | Vercel deployment config |
| `.github/workflows/deploy.yml` | CI/CD pipeline |
| `.github/workflows/test.yml` | Test pipeline for PRs |
