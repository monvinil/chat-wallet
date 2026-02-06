# Workstream: Lead Architect

> **Owner**: Architect session (primary builder)
> **Status**: Active
> **Last updated**: 2026-02-06

---

## Mandate

You are the system architect and primary builder. You own:
- All technical design decisions
- Code construction and integration
- Dependency management and build system
- Cross-role conflict resolution
- Sprint planning (after Sprint 0 assessments arrive)

You are the only role that edits `COMMAND_CENTER.md`. You synthesize findings from all other roles into construction decisions.

---

## Current Assessment

### Architecture Health
- **42 root-level Python files** - needs modularization (services/, tools/, integrations/)
- **`app.py` at 1,227 lines** - Streamlit monolith, will be deprecated but still runs
- **Next.js frontend** is clean (proper app router, components, lib structure)
- **FastAPI backend** is well-structured (routes, schemas, middleware)
- **Agent SDK** is minimal but correct foundation
- **No tests** running against real backend
- **No CI/CD pipeline**

### Dependency Map
```
Production Critical Path:
  Circle API Key ──► x402 payments ──► Agent marketplace revenue
  Bitrefill Key ──► Gift card purchases ──► Commerce layer
  RPC Keys ──► Reliable mainnet ──► Production deployment

Phase 2 (No Blockers):
  Next.js PWA config ──► Service worker ──► Push notifications ──► Retention

Phase 3 (Needs Circle):
  x402 ──► Agent payments ──► Creator onboarding ──► Marketplace
```

### Technical Debt Priority
1. Pin dependency versions in `requirements.txt` and `web/package.json`
2. Modularize root Python files into proper packages
3. Integration tests (at minimum: wallet create, send, yield deposit)
4. Structured JSON logging
5. RPC connection pooling and failover

---

## Sprint 0 Tasks

- [x] Full codebase analysis
- [x] Create coordination system (COMMAND_CENTER + workstreams)
- [ ] Review all other role outputs when they arrive
- [ ] Resolve cross-role conflicts
- [ ] Plan Sprint 1 construction tasks

## Construction Queue (Post Sprint 0)

_To be populated after reviewing all role assessments._

Likely priorities:
1. Production deployment pipeline (Vercel + Railway/Fly.io)
2. PWA configuration (next-pwa, service worker, manifest)
3. Push notification system
4. Fix unit economics in code (model routing: Haiku for simple, Sonnet for complex)
5. E2E test suite
6. Root module reorganization

---

## Architecture Notes

### Proposed Module Reorganization
```
chat-wallet/
├── api/                    # FastAPI backend (keep as-is, well-structured)
├── web/                    # Next.js frontend (keep as-is)
├── sdk/                    # Agent SDK (keep as-is)
├── services/               # NEW: extracted from root modules
│   ├── wallet/             # wallet_manager.py, balance_service.py
│   ├── blockchain/         # chain_utils.py, direct_tx.py, meta_tx.py, transaction_relayer.py
│   ├── defi/               # aave_client.py, yield_tools.py
│   ├── commerce/           # bitrefill_client.py, merchant_tools.py, bill_payment_helper.py
│   ├── bridge/             # cctp_client.py, bridge_tools.py
│   ├── email/              # email_manager.py, email_tools.py, gmail_oauth.py
│   ├── scheduler/          # scheduler_manager.py, scheduler_executor.py, scheduler_tools.py
│   └── ai/                 # agent setup, LangChain tools, model routing
├── migrations/
├── tests/
├── docs/
├── components/             # Streamlit (deprecated, keep for now)
├── utils/
├── config.py
├── app.py                  # Streamlit entry (deprecated)
└── run_api.py              # API entry
```

### Model Routing Strategy (Fix Unit Economics)
```
User message → Classify complexity (fast, cheap classifier)
  ├── Simple (balance check, send, status) → Haiku ($0.001/msg)
  ├── Medium (scheduling, yield questions) → Sonnet ($0.008/msg)
  └── Complex (strategy, multi-step) → Sonnet ($0.008/msg)

Target: 70% Haiku, 30% Sonnet = avg $0.003/msg (down from $0.012)
```

---

## Urgent Flags

_None currently._

---

## Notes from Other Roles

_Space for architect to track important findings from other workstreams._

---
