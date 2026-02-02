# Manual Actions Required
## Tasks That Need Human Intervention

---

> **Purpose:** This document tracks all tasks that require YOUR direct action.
> These cannot be automated or done by AI assistants.
> **Last Updated:** February 2026

---

# Critical Priority (This Week)

## 1. Circle Developer Account & Credentials

**Status:** [ ] Not Started  [ ] In Progress  [ ] Complete

**Why Critical:** Blocks x402 implementation, CCTP production, and partnership credibility.

### Actions Required:

- [ ] **Create Circle Developer Account**
  - URL: https://console.circle.com
  - Sign up with company email
  - Complete business verification if required

- [ ] **Get API Credentials**
  - [ ] API Key (for attestation API)
  - [ ] Entity ID (for Programmable Wallets)
  - [ ] Entity Secret (for signing operations)

- [ ] **Set Up Environments**
  - [ ] Sandbox environment for testing
  - [ ] Note down sandbox credentials
  - [ ] Request production access when ready

- [ ] **Add to Environment Variables**
  ```bash
  # Add to .env
  CIRCLE_API_KEY=your-api-key
  CIRCLE_ENTITY_ID=your-entity-id
  CIRCLE_ENTITY_SECRET=your-entity-secret
  CIRCLE_API_URL=https://api.circle.com/v1
  CIRCLE_ATTESTATION_URL=https://iris-api.circle.com/attestations
  ```

### Circle Partnership Discussion Points:
- [ ] Schedule follow-up call with Circle contact
- [ ] Discuss x402 early access
- [ ] Discuss Programmable Wallets subsidy
- [ ] Discuss co-marketing opportunities
- [ ] Discuss integration bounty/grant

---

## 2. Bitrefill API Credentials

**Status:** [ ] Not Started  [ ] In Progress  [ ] Complete

**Why Critical:** Gift card purchases are currently mocked. Real API needed for core functionality.

### Actions Required:

- [ ] **Create Bitrefill Partner Account**
  - URL: https://www.bitrefill.com/partner
  - Apply for API access
  - May require business verification

- [ ] **Get API Credentials**
  - [ ] API Key
  - [ ] API Secret

- [ ] **Add to Environment Variables**
  ```bash
  # Add to .env
  BITREFILL_API_KEY=your-api-key
  BITREFILL_API_SECRET=your-api-secret
  ```

- [ ] **Test in Sandbox**
  - Verify test purchases work
  - Confirm webhook setup

---

## 3. RPC Provider Upgrade

**Status:** [ ] Not Started  [ ] In Progress  [ ] Complete

**Why Critical:** Public RPC endpoints will rate-limit under load. Fundraising blocker.

### Actions Required:

- [ ] **Alchemy Account**
  - URL: https://www.alchemy.com
  - Create account
  - Get API keys for: Base, Arbitrum, Ethereum
  - Free tier is sufficient initially

- [ ] **Infura Account (Backup)**
  - URL: https://www.infura.io
  - Create account
  - Get API keys
  - Set as fallback

- [ ] **Add to Environment Variables**
  ```bash
  # Add to .env
  ALCHEMY_API_KEY=your-alchemy-key
  INFURA_API_KEY=your-infura-key
  ```

- [ ] **Update RPC Configuration**
  - AI can help update `config.py` once keys are available

---

# High Priority (Next 2 Weeks)

## 4. Supabase Production Setup

**Status:** [ ] Not Started  [ ] In Progress  [ ] Complete

**Why:** Current setup may be development tier. Production needs proper config.

### Actions Required:

- [ ] **Upgrade to Pro Tier** (if not already)
  - ~$25/month
  - Removes row limits
  - Better performance

- [ ] **Configure Production**
  - [ ] Enable Point-in-Time Recovery
  - [ ] Set up database backups
  - [ ] Configure connection pooling
  - [ ] Set up monitoring alerts

- [ ] **Security Checklist**
  - [ ] Review and enable RLS on all tables
  - [ ] Rotate anon key if exposed
  - [ ] Review service key usage
  - [ ] Enable MFA on Supabase account

---

## 5. Email Service Setup

**Status:** [ ] Not Started  [ ] In Progress  [ ] Complete

**Why:** Email verification and notifications require email service.

### Actions Required:

**Option A: Use Supabase Built-in (Simpler)**
- [ ] Configure Supabase Auth emails
- [ ] Customize email templates
- [ ] Set up custom SMTP (optional)

**Option B: External Service (More Control)**
- [ ] Create Resend account (https://resend.com) OR
- [ ] Create SendGrid account (https://sendgrid.com)
- [ ] Verify sending domain
- [ ] Get API key
- [ ] Add to `.env`:
  ```bash
  EMAIL_SERVICE=resend  # or sendgrid
  EMAIL_API_KEY=your-api-key
  EMAIL_FROM=noreply@yourdomain.com
  ```

---

## 6. Domain & SSL

**Status:** [ ] Not Started  [ ] In Progress  [ ] Complete

**Why:** Production deployment needs proper domain.

### Actions Required:

- [ ] **Register/Confirm Domain**
  - Decide on production domain
  - Ensure DNS access

- [ ] **Configure DNS**
  - Point to hosting provider
  - Set up SSL certificate

- [ ] **Update Configuration**
  - Update allowed origins
  - Update OAuth callback URLs

---

# Medium Priority (Month 1)

## 7. Analytics Setup

**Status:** [ ] Not Started  [ ] In Progress  [ ] Complete

**Why:** Can't improve what you don't measure.

### Actions Required:

**Option A: PostHog (Recommended - Open Source)**
- [ ] Create PostHog account (https://posthog.com)
- [ ] Get project API key
- [ ] Add to `.env`:
  ```bash
  POSTHOG_API_KEY=your-key
  POSTHOG_HOST=https://app.posthog.com
  ```

**Option B: Mixpanel**
- [ ] Create Mixpanel account
- [ ] Get project token
- [ ] Add to `.env`

---

## 8. Error Tracking (Sentry)

**Status:** [ ] Not Started  [ ] In Progress  [ ] Complete

**Why:** Need visibility into production errors.

### Actions Required:

- [ ] Create Sentry account (https://sentry.io)
- [ ] Create Python project
- [ ] Get DSN
- [ ] Add to `.env`:
  ```bash
  SENTRY_DSN=your-dsn
  ```

---

## 9. Trading Platform APIs (For Agent Features)

**Status:** [ ] Not Started  [ ] In Progress  [ ] Complete

**Why:** Required for trading bot agents.

### Hyperliquid:
- [ ] Review API documentation
- [ ] Understand authentication requirements
- [ ] Note: May require user to connect their own account

### Polymarket:
- [ ] Review API access requirements
- [ ] Apply for API access if gated
- [ ] Understand rate limits

---

# Lower Priority (Month 2+)

## 10. Mobile App Store Accounts

**Status:** [ ] Not Started  [ ] In Progress  [ ] Complete

**Why:** Required for native mobile app (Phase 5).

### Apple Developer:
- [ ] Enroll in Apple Developer Program ($99/year)
- [ ] Complete identity verification

### Google Play:
- [ ] Create Google Play Developer account ($25 one-time)
- [ ] Complete verification

---

## 11. Legal & Compliance

**Status:** [ ] Not Started  [ ] In Progress  [ ] Complete

**Why:** Crypto + AI + money movement needs legal clarity.

### Actions Required:

- [ ] Consult crypto-friendly lawyer
- [ ] Review self-custody regulatory position
- [ ] Draft Terms of Service
- [ ] Draft Privacy Policy
- [ ] Consider geographic restrictions

---

## 12. Banking & Business Setup

**Status:** [ ] Not Started  [ ] In Progress  [ ] Complete

**Why:** Platform revenue needs business account.

### Actions Required:

- [ ] Form legal entity (if not done)
- [ ] Open business bank account
- [ ] Set up crypto-friendly banking (Mercury, Relay)
- [ ] Configure revenue collection

---

# Credential Checklist Summary

| Service | Status | Priority | Env Variable |
|---------|--------|----------|--------------|
| Circle API | [ ] | P0 | `CIRCLE_API_KEY` |
| Circle Entity | [ ] | P0 | `CIRCLE_ENTITY_ID`, `CIRCLE_ENTITY_SECRET` |
| Bitrefill | [ ] | P0 | `BITREFILL_API_KEY`, `BITREFILL_API_SECRET` |
| Alchemy | [ ] | P1 | `ALCHEMY_API_KEY` |
| Infura | [ ] | P2 | `INFURA_API_KEY` |
| Email Service | [ ] | P1 | `EMAIL_API_KEY` |
| PostHog/Analytics | [ ] | P1 | `POSTHOG_API_KEY` |
| Sentry | [ ] | P2 | `SENTRY_DSN` |
| Hyperliquid | [ ] | P2 | TBD |
| Polymarket | [ ] | P2 | TBD |

---

# Environment Template

Once you have credentials, your `.env` should include:

```bash
# ===========================================
# SUPABASE
# ===========================================
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# ===========================================
# CIRCLE (Critical)
# ===========================================
CIRCLE_API_KEY=
CIRCLE_ENTITY_ID=
CIRCLE_ENTITY_SECRET=
CIRCLE_API_URL=https://api.circle.com/v1
CIRCLE_ATTESTATION_URL=https://iris-api.circle.com/attestations

# ===========================================
# LLM PROVIDERS
# ===========================================
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GOOGLE_API_KEY=

# ===========================================
# RPC PROVIDERS
# ===========================================
ALCHEMY_API_KEY=
INFURA_API_KEY=

# ===========================================
# INTEGRATIONS
# ===========================================
BITREFILL_API_KEY=
BITREFILL_API_SECRET=

# ===========================================
# EMAIL
# ===========================================
EMAIL_SERVICE=resend
EMAIL_API_KEY=
EMAIL_FROM=noreply@usdchat.com

# ===========================================
# ANALYTICS & MONITORING
# ===========================================
POSTHOG_API_KEY=
SENTRY_DSN=

# ===========================================
# GMAIL OAUTH (existing)
# ===========================================
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

---

# Partnership Outreach Tracker

| Partner | Contact | Status | Next Action |
|---------|---------|--------|-------------|
| Circle | [Your contact] | In talks | Schedule x402 discussion |
| Bitrefill | TBD | Not started | Apply for partner program |
| Alchemy | TBD | Not started | Sign up for free tier |
| PostHog | TBD | Not started | Create account |

---

*Last Updated: February 2026*
*Review Weekly: Check off completed items, update statuses*
