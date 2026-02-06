# Workstream: DevOps Lead

> **Owner**: DevOps session
> **Status**: Awaiting session start
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
- **Not deployed to production** - everything runs locally
- Docker Compose orchestrates: API (port 8000), Web (port 3000), optional Scheduler
- Supabase is the only external service (hosted)
- Public RPC endpoints (no production reliability)
- No monitoring, no logging, no alerts
- No CI/CD pipeline
- No secret management (`.env` files)

---

## Sprint 0 Tasks

### 1. Deployment Architecture Design
- [ ] Recommend hosting platform for each component:
  - Next.js frontend (Vercel? Cloudflare Pages? Self-hosted?)
  - FastAPI backend (Railway? Fly.io? Render? AWS ECS?)
  - Scheduler worker (same as backend? separate service?)
- [ ] Evaluate cost at different scales (0, 100, 1K, 10K users)
- [ ] Design the deployment pipeline (push to branch → staging → production)
- [ ] Define environment strategy (dev, staging, production)

### 2. Infrastructure Configuration
- [ ] Review `docker-compose.yml` for production readiness
- [ ] Review `Dockerfile.api` for security and optimization (multi-stage build? non-root?)
- [ ] Review `web/Dockerfile` for production optimization
- [ ] Design health check endpoints
- [ ] Propose a `docker-compose.production.yml` or equivalent

### 3. Monitoring & Observability
- [ ] Propose logging strategy (structured JSON, log aggregation)
- [ ] Propose metrics to track (request latency, error rates, blockchain call times)
- [ ] Propose alerting rules (downtime, error spikes, failed transactions)
- [ ] Evaluate tools: Grafana, Datadog, Sentry, LogTail, etc.
- [ ] Budget for monitoring (free tier vs paid)

### 4. Scaling Analysis
- [ ] What breaks first at 100 concurrent users? (RPC rate limits? DB connections? LLM quota?)
- [ ] What breaks at 1,000 users?
- [ ] What breaks at 10,000 users?
- [ ] Propose scaling solutions for each bottleneck
- [ ] Evaluate: Do we need Redis? (sessions, rate limiting, caching)

### 5. Security & Secrets
- [ ] Propose secret management solution (environment variables are not enough)
- [ ] Review what secrets exist and how they're handled
- [ ] Propose key rotation strategy
- [ ] HTTPS/TLS configuration
- [ ] DDoS protection needs

### 6. Cost Projections
- [ ] Model monthly infrastructure costs at different user scales
- [ ] Identify cost optimization opportunities
- [ ] Compare hosting platform pricing
- [ ] Project RPC costs (Alchemy/Infura pricing tiers)
- [ ] Include Supabase pricing at scale

---

## Findings

_Write your infrastructure findings here._

### Current Infrastructure Gaps

### Deployment Recommendation

### Scaling Bottlenecks

---

## Recommendations

### Before Launch (Blocking)

### First Month

### First Quarter

---

## Infrastructure Cost Model

| Component | 100 users | 1K users | 10K users |
|-----------|-----------|----------|-----------|
| Frontend hosting | | | |
| Backend hosting | | | |
| Database (Supabase) | | | |
| RPC provider | | | |
| Monitoring | | | |
| **Total/month** | | | |

---

## Urgent Flags

_Flag anything that would prevent production deployment._

---
