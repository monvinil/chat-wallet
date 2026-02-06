# Workstream: Workflow Reviewer

> **Owner**: Workflow Reviewer session
> **Status**: Sprint 0 COMPLETE
> **Last updated**: 2026-02-06
> **Branch**: `claude/project-analysis-fwmFh`

---

## Mandate

Answer: **"Is this codebase ready for production, and what needs to change to get there?"**

**Verdict: NOT production-ready.** There are 5 critical blockers, 12 major issues, and numerous minor quality items. Estimated effort to reach MVP production: 2-3 weeks of focused work.

---

## Sprint 0 Tasks

### 1. Code Quality Audit

- [x] Review Python code quality (root modules - are they well-structured?)
- [x] Review TypeScript code quality (`web/` - is it consistent?)
- [x] Identify code smells, dead code, and duplication
- [x] Check for hardcoded values, magic numbers, configuration drift
- [x] Evaluate error handling patterns
- [x] Check type safety (Python type hints, TypeScript strict mode)
- [x] Review import organization and circular dependency risks

### 2. Testing Assessment

- [x] What tests exist currently? (`tests/` directory)
- [x] What's the test coverage? (run tests if possible)
- [x] What critical paths have ZERO tests?
- [x] Propose a testing strategy:
  - Unit tests (what to test)
  - Integration tests (API endpoints)
  - E2E tests (user flows)
  - Contract tests (blockchain interactions)
- [x] Estimate effort to reach 60% coverage on critical paths

### 3. CI/CD Pipeline Design

- [x] Propose a GitHub Actions workflow:
  - Lint (Python: ruff/black, TypeScript: eslint)
  - Type check (mypy, tsc)
  - Test (pytest, jest/vitest)
  - Build (Docker images)
  - Deploy (staging, production)
- [x] Define branch strategy (main, develop, feature branches)
- [x] Define PR requirements (reviews, checks, coverage)

### 4. Dependency Audit

- [x] Are Python dependencies pinned? (exact versions in requirements.txt)
- [x] Are Node dependencies locked? (package-lock.json exists?)
- [x] Any known vulnerabilities? (npm audit, pip-audit)
- [x] Any unnecessary dependencies? (bloat)
- [x] Any dangerously outdated dependencies?

### 5. Developer Experience

- [x] How easy is it to set up the project from scratch? (follow QUICKSTART.md)
- [x] Are environment variables documented?
- [x] Is the `sdk/` package installable and usable?
- [x] Is there API documentation (OpenAPI/Swagger)?
- [x] What's the inner development loop? (change code -> see result speed)

### 6. Code Organization Recommendations

- [x] Evaluate the 42 root-level Python files - propose a reorganization
- [x] Evaluate the monolith `app.py` (1,227 lines) - propose a split strategy
- [x] Evaluate shared code between Streamlit and FastAPI - should they share?
- [x] Propose a migration path from current structure to recommended structure

---

## Findings

### CRITICAL Issues (Block Production Deployment)

#### C1. Insecure JWT Secret Default
- **File**: `api/config.py:36`
- **Issue**: JWT secret has a hardcoded default: `"CHANGE-THIS-IN-PRODUCTION-use-secrets-token-hex-32"`. The docker-compose also uses `JWT_SECRET_KEY:-your-dev-secret-key-change-in-prod`.
- **Risk**: If deployed without setting env var, all JWTs are signed with a known key. Any attacker can forge authentication tokens.
- **Fix**: Remove the default. Raise an error on startup if `JWT_SECRET_KEY` is not set. Add a startup validator.

#### C2. Transaction Execution is Mocked
- **File**: `api/routes/transactions.py:297-321`
- **Issue**: The `/api/v1/transactions/send` endpoint returns a **mock transaction hash** and does not actually execute any blockchain transaction. Comment on line 301: `"Transaction execution requested but signing not implemented in API yet"`.
- **Risk**: Users see fake confirmations. This is the core functionality of a wallet.
- **Fix**: Implement the signing integration. The Streamlit `direct_tx.py` has working signing code - it needs to be adapted for the API layer.

#### C3. In-Memory Preview Store (No Persistence)
- **File**: `api/routes/transactions.py:47`
- **Issue**: `_preview_store: Dict[str, Dict[str, Any]] = {}` - transaction previews are stored in-memory. If the API restarts, all pending previews are lost.
- **Risk**: In production with multiple workers (uvicorn with `--workers N`), each worker has its own store. Users can create a preview on worker A and try to execute on worker B (404).
- **Fix**: Use Redis or database for preview storage.

#### C4. No .dockerignore Files
- **Files**: Root directory, `web/` directory
- **Issue**: No `.dockerignore` exists anywhere. `COPY . .` in both Dockerfiles copies `.env` files (with secrets), `.git/`, `node_modules/`, `__pycache__/`, test data, etc.
- **Risk**: Secrets baked into Docker images. Images are bloated (100MB+ unnecessary).
- **Fix**: Create `.dockerignore` files excluding `.env*`, `.git`, `node_modules`, `__pycache__`, `*.pyc`, `.next`, etc. **STATUS: FIXED in this commit.**

#### C5. Docker Runs as Root
- **File**: `Dockerfile.api` (entire file)
- **Issue**: No `USER` directive. Container runs as root.
- **Risk**: If the container is compromised, attacker has root access.
- **Fix**: Add `RUN adduser --disabled-password appuser` and `USER appuser`.

---

### MAJOR Issues (High Risk / Significant Problems)

#### M1. Python Dependencies Not Pinned
- **File**: `requirements.txt`
- **Issue**: All 30+ dependencies use `>=` (minimum version) instead of `==` (exact version). Examples: `web3>=6.0.0`, `fastapi>=0.109.0`, `langchain>=1.2.0`.
- **Risk**: Builds are non-reproducible. A new release of any package can break production. LangChain is especially volatile (breaking changes between minor versions).
- **Fix**: Pin all deps with `pip freeze > requirements.txt` from a known-working environment. Use `pip-compile` (pip-tools) for dependency locking.

#### M2. Streamlit Dependency Leakage into API
- **Files**: `wallet_manager.py:9` (`import streamlit as st`), `direct_tx.py:12`, `supabase_client.py:7`, `config.py`, and 15+ other root modules.
- **Issue**: Core business logic (wallet management, transactions, Supabase client) imports Streamlit for `st.error()`, `st.session_state`, `st.cache_resource`. The FastAPI routes import from these modules via `sys.path` hacks.
- **Risk**: Streamlit is a 200MB dependency being loaded into the API server. Session state calls fail in non-Streamlit context. Tests require mocking Streamlit (`tests/test_wallet_manager.py:11`: `sys.modules['streamlit'] = MagicMock()`).
- **Fix**: Refactor core logic to be framework-agnostic. Create a shared `core/` package with no Streamlit imports. UI error handling should be at the view layer only.

#### M3. sys.path Manipulation in API Routes
- **Files**: `api/routes/wallet.py:20`, `api/routes/transactions.py:19`, `api/main.py:20`
- **Issue**: Every API file does `sys.path.insert(0, ...)` to import root-level modules. This is fragile and causes import ordering issues.
- **Fix**: Make the project installable (`pyproject.toml`) or use a proper package structure with `__init__.py` files.

#### M4. 42 Root-Level Python Files (No Package Structure)
- **Files**: All `*.py` in root
- **Issue**: Business logic sprawled across 42 files at root level with no package organization. Related files aren't grouped: `aave_client.py`, `yield_tools.py`, `balance_service.py`, `chain_utils.py` are all related but scattered.
- **Risk**: Import confusion, difficulty navigating, impossible to test in isolation.
- **Fix**: Reorganize into packages: `core/wallet/`, `core/blockchain/`, `core/yield/`, `core/scheduler/`, `integrations/bitrefill/`, `integrations/circle/`, etc.

#### M5. Test Coverage is Near-Zero
- **Files**: `tests/test_wallet_manager.py`, `tests/test_meta_tx.py`
- **Issue**: Only 2 test files exist covering password hashing, wallet encryption/creation, and meta-transaction signing. That's ~30 test cases for an entire financial application.
- **Coverage gaps** (ZERO tests):
  - API endpoints (all routes)
  - Authentication/JWT flow
  - Transaction execution
  - Balance queries
  - Yield/Aave operations
  - Scheduler/DCA execution
  - Supabase client operations
  - CCTP bridging
  - Rate limiting
  - Error handling paths
- **Risk**: Any code change can silently break critical financial flows.
- **Effort to 60% coverage on critical paths**: ~40-60 hours (1-2 dev weeks).

#### M6. ETH Price Hardcoded for Gas Estimation
- **File**: `direct_tx.py:168`
- **Issue**: `gas_cost_usd = gas_cost_eth * 2000` - ETH price is hardcoded at $2000 for fee estimation.
- **Risk**: If ETH is $4000, users see fees at half the actual cost. If $1000, fees appear doubled.
- **Fix**: Use a price oracle (CoinGecko API, Chainlink, etc.) with caching.

#### M7. No HTTPS/TLS Configuration
- **Files**: `docker-compose.yml`, `Dockerfile.api`
- **Issue**: No TLS termination configured. API runs on plain HTTP (port 8000).
- **Risk**: JWT tokens and wallet data transmitted in cleartext on production.
- **Fix**: Add nginx/caddy reverse proxy with TLS, or deploy behind a cloud load balancer with TLS.

#### M8. CORS Configuration Too Permissive
- **File**: `api/config.py:33-34`
- **Issue**: `cors_allow_methods: List[str] = ["*"]` and `cors_allow_headers: List[str] = ["*"]`.
- **Risk**: Allows all methods and headers. Should be restricted to actual needed methods (GET, POST, OPTIONS) and headers (Authorization, Content-Type).
- **Fix**: Whitelist specific methods and headers.

#### M9. Docker Compose Not Production-Ready
- **File**: `docker-compose.yml`
- **Issues**:
  - Line 18: `volumes: - .:/app` mounts entire source code into container (dev only)
  - Line 19: `command: python run_api.py --debug` forces debug mode
  - Line 16: `DEBUG=true` hardcoded
  - No resource limits (memory, CPU)
  - No restart policies
  - No network isolation between services
- **Fix**: Create separate `docker-compose.prod.yml` without volume mounts, with debug off, with restart policies and resource limits.

#### M10. Web Dockerfile Not Production-Ready
- **File**: `web/Dockerfile`
- **Issue**: Line 14 comments out `RUN npm run build`. Line 24 runs `npm run dev` (development server with HMR, not optimized).
- **Risk**: Development server in production = slow, no optimizations, verbose error output.
- **Fix**: Multi-stage build: build stage compiles Next.js, production stage runs `next start`.

#### M11. No Token Blacklisting/Revocation
- **File**: `api/middleware/auth.py`
- **Issue**: JWTs are stateless with no revocation mechanism. If a token is compromised, there's no way to invalidate it until expiry (24 hours for access, 30 days for refresh).
- **Risk**: Compromised tokens remain valid for extended periods.
- **Fix**: Implement token blacklist (Redis) or switch to shorter-lived tokens with more frequent refresh.

#### M12. Multiple TODO/Unimplemented Sections
- **Files**: Multiple
  - `scheduler_executor.py:236`: `# TODO: Implement actual Bitrefill purchase`
  - `scheduler_executor.py:263`: `# TODO: Implement price oracle`
  - `scheduler_executor.py:301`: `# TODO: Implement actual DEX swap`
  - `api/routes/agents.py:483`: `# TODO: Implement payment verification`
  - `api/routes/agents.py:498`: `# TODO: Actually call the agent endpoint`
  - `sdk/usdchat_agent/payments.py:160`: `# TODO: Implement actual verification`
- **Risk**: Users may trigger unimplemented code paths that silently fail or return wrong data.

---

### Code Quality Issues

#### Python Code Quality
- **Type hints**: Present in most files (good), but not enforced by mypy. No mypy config exists.
- **Docstrings**: Good coverage in API routes and middleware. Sparse in root-level utility modules.
- **Error handling**: Inconsistent. Some modules raise exceptions, some return None, some call `st.error()`. API routes use proper HTTPException.
- **Import organization**: Broken by `sys.path.insert()` hacks. Circular dependency risk between `config.py`, `chain_utils.py`, and `wallet_manager.py`.
- **Magic numbers**: `direct_tx.py:168` (ETH=$2000), `direct_tx.py:144` (gas buffer 1.2x), `config.py:112-114` (fee structure), `api/config.py:38` (24h token expiry). Fee structure should be in config/env vars.

#### TypeScript Code Quality
- **Strict mode**: ON (`tsconfig.json:7` - `"strict": true`) - excellent
- **ESLint**: 0 errors, 19 warnings (all unused imports + 1 `<img>` tag)
- **No console.log**: Clean - no debug logging left in production code
- **API client**: Well-structured with token refresh handling and race condition prevention (`client.ts:130-135`)
- **State management**: Zustand with persistence - clean pattern
- **Type safety**: Good - types defined in `lib/api/types.ts`, used consistently
- **XSS**: No `dangerouslySetInnerHTML` found. React JSX auto-escaping provides protection.
- **Accessibility**: Basic semantic HTML present but no ARIA labels or screen reader support audited.

### Testing Gaps

| Critical Path | Test Coverage | Risk |
|--------------|---------------|------|
| Wallet creation/import | Partial (tests exist) | Medium |
| Password hashing/verification | Covered | Low |
| Meta-transaction signing | Covered | Low |
| API authentication (JWT) | NONE | **Critical** |
| API endpoints (all routes) | NONE | **Critical** |
| Transaction execution | NONE | **Critical** |
| Balance queries (blockchain) | NONE | High |
| Yield/Aave operations | NONE | High |
| Scheduler/DCA execution | NONE | High |
| Supabase CRUD operations | NONE | High |
| Rate limiting | NONE | Medium |
| Frontend components | NONE | Medium |
| SDK functionality | NONE | Low (not yet used) |

**Tests could not be run** during this audit because Python dependencies failed to install completely (cffi/cryptography build issues in the CI-like environment). This is itself a finding about reproducibility.

### Dependency Issues

#### Python (`requirements.txt`)
| Issue | Severity | Details |
|-------|----------|---------|
| No version pinning | Major | All 30+ packages use `>=`, builds non-reproducible |
| Streamlit in API | Major | 200MB+ unnecessary dependency for API server |
| langchain pinning | High | LangChain has frequent breaking changes between minor versions |
| No pip-audit | Minor | No automated vulnerability scanning |
| No lock file | Major | No `requirements.lock` or `pip-compile` output |

#### Node.js (`web/package.json`)
| Issue | Severity | Details |
|-------|----------|---------|
| package-lock.json missing from repo | Major | Was not committed (generated by `npm install` during audit). **STATUS: FIXED in this commit.** |
| Deps use `^` ranges | Minor | Standard practice for Node, but `npm ci` with lock file needed |
| npm audit shows 0 vulnerabilities | Good | Clean bill of health |
| Next.js 16.1.6 | Good | Current version |
| React 19.2.3 | Good | Current version |

### DX Issues

| Area | Rating | Notes |
|------|--------|-------|
| Setup docs | B | QUICKSTART.md exists, covers basics, but missing troubleshooting |
| .env.example | A | Comprehensive, well-documented |
| API docs | B | OpenAPI/Swagger available in debug mode (`/docs`), disabled in prod |
| Inner dev loop | C | Requires 2-3 terminals (API, web, optional scheduler). No `make dev` |
| SDK installability | D | `setup.py` with empty `install_requires`, no README.md in sdk/ |
| Error messages | B | Consistent API error format, Streamlit errors are user-friendly |
| Code navigation | D | 42 root files make finding code difficult |
| Onboarding time | C+ | ~30 min to get running if deps install cleanly |

---

## Recommendations

### Immediate (Before Production - MUST DO)

1. **Fix JWT secret** - Remove default, fail on startup if not set (~1 hour)
2. **Create `.dockerignore`** files to exclude `.env`, `.git`, etc. (~30 min) **DONE**
3. **Add non-root user to Dockerfiles** (~30 min)
4. **Pin Python dependencies** with exact versions (~2 hours)
5. **Commit `package-lock.json`** to the web directory (~5 min) **DONE**
6. **Create production Docker Compose** with debug off, no volume mounts (~2 hours)
7. **Fix web Dockerfile** to build for production (multi-stage) (~1 hour)
8. **Implement real transaction signing** in API or clearly disable/warn (~4-8 hours)
9. **Replace in-memory preview store** with Redis/DB (~4 hours)
10. **Restrict CORS** to actual production domains (~30 min)

### Short-term (First Month)

1. **Refactor root modules into packages** - Eliminate 42 root files (~2-3 days)
2. **Remove Streamlit dependency from core logic** - Create framework-agnostic core (~3-5 days)
3. **Add API endpoint tests** with pytest + httpx TestClient (~3-5 days)
4. **Add ETH price oracle** for gas estimation (~4 hours)
5. **Implement token revocation** (Redis blacklist) (~4 hours)
6. **Set up CI/CD pipeline** (see below) (~4 hours) **DONE - `.github/workflows/ci.yml` committed**
7. **Fix all TODO items** or add proper error responses (~2 days)
8. **Add structured logging** (~4 hours)

### Medium-term (First Quarter)

1. **Reach 60% test coverage** on critical paths (~40-60 hours)
2. **Add E2E tests** against test backend (Playwright or Cypress) (~2 weeks)
3. **Add frontend tests** with vitest (~1 week)
4. **Implement health check endpoints** with dependency status (~4 hours)
5. **Add database migrations tooling** (Alembic or Supabase CLI) (~1 day)
6. **SDK documentation and tests** (~1 week)
7. **Security audit** (pen test, dependency scan) (~1 week)

---

## Proposed CI/CD Pipeline

**Implemented**: `.github/workflows/ci.yml` committed with this workstream.

### Pipeline Stages

```
Push/PR -> Lint (Python ruff/black + TypeScript eslint)
        -> Type Check (mypy + tsc --noEmit)
        -> Test (pytest with coverage + vitest when added)
        -> Build (Next.js production build)
        -> Security Scan (pip-audit + npm audit)
        -> Docker Build (API + Web images, on push only)
```

### Branch Strategy
```
main          - Production releases (protected, require PR)
develop       - Integration branch for features
feature/*     - Individual feature branches
hotfix/*      - Emergency production fixes
```

### PR Requirements
- All CI checks must pass (lint, type-check, test, build)
- At least 1 code review approval
- No decrease in test coverage
- Branch must be up-to-date with base

### Concurrency
- Cancels in-progress runs for same branch (saves CI minutes)
- Runs on push to main/develop and all PRs

---

## Code Organization Recommendation

### Current Structure (42 root files - problematic):
```
chat-wallet/
├── aave_client.py          # Yield
├── analytics.py            # Analytics
├── app.py                  # Streamlit (1227 lines!)
├── balance_service.py      # Balance queries
├── bill_payment_helper.py  # Payments
├── bitrefill_client.py     # Gift cards
├── bridge_tools.py         # CCTP
├── cctp_client.py          # CCTP
├── chain_utils.py          # Blockchain
├── circle_client.py        # Circle
├── config.py               # Config
├── decision_logger.py      # Logging
├── design_system.py        # Streamlit UI
├── direct_tx.py            # Transactions
├── email_manager.py        # Email
├── email_tools.py          # Email
├── free_tier.py            # Pricing
├── gmail_oauth.py          # OAuth
├── merchant_adapters.py    # Commerce
├── merchant_tools.py       # Commerce
├── meta_tx.py              # Meta-transactions
├── onboarding.py           # UI
├── patch_streamlit.py      # Hacks
├── quick_start.py          # UI
├── rate_limiter.py         # Rate limiting
├── run_api.py              # API entry
├── scheduler_executor.py   # DCA
├── scheduler_manager.py    # DCA
├── scheduler_tools.py      # DCA
├── session_manager.py      # Sessions
├── settings_manager.py     # Settings
├── settings_ui.py          # UI
├── showcase_agents.py      # Agent demos
├── spending_limits.py      # Limits
├── styles.py               # Streamlit CSS
├── supabase_client.py      # Database
├── transaction_relayer.py  # Relay
├── universal_crypto_payment.py  # Payments
├── wallet_manager.py       # Wallets
└── yield_tools.py          # Yield
```

### Recommended Structure:
```
chat-wallet/
├── core/                        # Framework-agnostic business logic
│   ├── __init__.py
│   ├── config.py                # Shared configuration
│   ├── wallet/
│   │   ├── __init__.py
│   │   ├── manager.py           # Wallet creation/import
│   │   ├── encryption.py        # Wallet encryption
│   │   └── session.py           # Session management
│   ├── blockchain/
│   │   ├── __init__.py
│   │   ├── evm.py               # EVM chain operations
│   │   ├── solana.py            # Solana operations
│   │   ├── balance.py           # Balance queries
│   │   ├── direct_tx.py         # Direct transactions
│   │   └── meta_tx.py           # Meta-transactions
│   ├── yield_/
│   │   ├── __init__.py
│   │   ├── aave.py              # Aave client
│   │   └── tools.py             # Yield LangChain tools
│   ├── scheduler/
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   ├── executor.py
│   │   └── tools.py
│   ├── commerce/
│   │   ├── __init__.py
│   │   ├── bitrefill.py
│   │   ├── merchants.py
│   │   └── payments.py
│   ├── bridge/
│   │   ├── __init__.py
│   │   └── cctp.py
│   └── database/
│       ├── __init__.py
│       └── supabase.py
├── api/                         # FastAPI (unchanged, well-organized)
├── web/                         # Next.js (unchanged, well-organized)
├── streamlit_app/               # Streamlit legacy UI
│   ├── app.py
│   ├── components/
│   └── styles/
├── sdk/                         # Agent SDK
├── tests/                       # All tests
│   ├── core/
│   ├── api/
│   └── sdk/
├── migrations/
├── docs/
└── docker/                      # Docker configs
    ├── Dockerfile.api
    ├── Dockerfile.web
    ├── docker-compose.yml
    └── docker-compose.prod.yml
```

### Migration Path (Incremental):
1. Create `core/` package with `__init__.py` files
2. Move files one-by-one, updating imports (start with `config.py`, `wallet_manager.py`)
3. Remove `import streamlit` from core modules, replace with logging
4. Update API routes to import from `core.*`
5. Keep root-level files as thin shims during migration for backwards compatibility
6. Remove shims once all imports are updated

### app.py Split Strategy (1,227 lines):
The monolith `app.py` should be split into:
- `streamlit_app/app.py` - Main entry, routing, session init (~100 lines)
- `streamlit_app/pages/chat.py` - Chat interface
- `streamlit_app/pages/wallet.py` - Wallet management UI
- `streamlit_app/pages/settings.py` - Settings UI
- `streamlit_app/components/` - Reusable Streamlit components
- All business logic already extracted to `core/` (step 2 above)

---

## Testing Strategy Proposal

### Priority 1: API Integration Tests (Week 1)
```python
# tests/api/test_wallet_routes.py
- test_create_wallet_success
- test_create_wallet_duplicate_email
- test_login_success
- test_login_wrong_password
- test_login_nonexistent_user
- test_get_balances_authenticated
- test_get_balances_unauthenticated
- test_refresh_token

# tests/api/test_transaction_routes.py
- test_preview_transaction
- test_preview_invalid_chain
- test_execute_transaction_valid_preview
- test_execute_transaction_expired_preview
- test_execute_transaction_wrong_user

# tests/api/test_auth_middleware.py
- test_jwt_creation
- test_jwt_verification
- test_jwt_expiration
- test_jwt_invalid_token
- test_rate_limiting
```

### Priority 2: Core Business Logic (Week 2)
```python
# tests/core/test_wallet_manager.py (extend existing)
- test_solana_derivation
- test_wallet_import_mnemonic_12_words
- test_wallet_import_mnemonic_24_words
- test_wallet_import_private_key

# tests/core/test_transactions.py
- test_fee_calculation
- test_validate_transfer_insufficient_balance
- test_validate_transfer_success
- test_gas_estimation

# tests/core/test_config.py
- test_rpc_url_selection
- test_rpc_fallback
- test_network_configuration
```

### Priority 3: Frontend Tests (Week 3)
```typescript
// web/__tests__/
- api-client.test.ts (token management, request handling)
- auth-store.test.ts (login, logout, token refresh)
- Component smoke tests (renders without crashing)
```

---

## Urgent Flags

1. **JWT_SECRET_KEY has a guessable default** (`api/config.py:36`) - Any deployment without explicitly setting this env var is immediately compromised. All user tokens can be forged.

2. **Transaction send endpoint returns fake tx hashes** (`api/routes/transactions.py:297-321`) - The API endpoint that should send real USDC returns mock data. Users cannot actually send money through the API.

3. **No .dockerignore means secrets in Docker images** - If Docker images are pushed to a registry, `.env` files with API keys and secrets are included. **FIXED in this commit.**

4. **Scheduler has unimplemented TODOs in execution paths** (`scheduler_executor.py:236,263,301`) - Multiple `# TODO: Implement` comments in code paths that could be triggered by user-created schedules, leading to silent failures.

---

## Files Created/Modified in This Review

| File | Action | Purpose |
|------|--------|---------|
| `docs/workstreams/workflow-reviewer.md` | Modified | Complete audit findings |
| `.github/workflows/ci.yml` | Created | CI/CD pipeline |
| `.dockerignore` | Created | Prevent secrets in API Docker image |
| `web/.dockerignore` | Created | Prevent secrets in web Docker image |
| `web/package-lock.json` | Created | Lock frontend dependencies |

---
