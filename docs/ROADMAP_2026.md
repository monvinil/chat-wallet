# USDChat Implementation Roadmap 2026
## Detailed Technical Todo Lists by Category

---

> **Reference:** This roadmap implements the strategy defined in STRATEGIC_DIRECTION.md
> **Last Updated:** February 2026

---

# Overview: Implementation Phases

```
Phase 0: SECURITY (Week 1-2)        ████████░░ CRITICAL - Blocks everything
Phase 1: API FOUNDATION (Week 2-4)  ████░░░░░░ Unblocks mobile, agents, scale
Phase 2: x402 & PAYMENTS (Week 4-6) ██░░░░░░░░ Circle partnership proof
Phase 3: AGENT PROTOCOL (Week 6-10) ░░░░░░░░░░ The moat
Phase 4: MARKETPLACE (Week 10-14)   ░░░░░░░░░░ Network effects
Phase 5: SCALE (Week 14+)           ░░░░░░░░░░ Mobile, growth, optimization
```

---

# PHASE 0: SECURITY HARDENING
## Timeline: Week 1-2 (IMMEDIATE)
## Status: CRITICAL — Blocks Circle partnership

### 0.1 Cookie Key Removal
**Priority:** P0 — CRITICAL
**Files:** `session_manager.py`, `app.py`

- [ ] Remove `chat_wallet_key` from browser cookies
- [ ] Implement session-based key storage (memory only)
- [ ] Add password re-entry on unlock
- [ ] Test: Verify key not in document.cookie
- [ ] Test: Verify key cleared on logout

**Implementation Notes:**
```python
# REMOVE this pattern:
st.session_state.cookies['chat_wallet_key'] = encrypted_key

# REPLACE with:
# Key stays in st.session_state only, never persisted
st.session_state._wallet_key = encrypted_key  # Memory only
```

### 0.2 Auto-Lock Implementation
**Priority:** P0 — CRITICAL
**Files:** `session_manager.py`, `components/sidebar.py`

- [ ] Add `last_activity_timestamp` to session state
- [ ] Create `check_idle_timeout()` function (5 min default)
- [ ] Call timeout check on every page load
- [ ] Clear sensitive data on timeout
- [ ] Show "Session locked" UI with unlock form
- [ ] Add user setting for timeout duration (5/15/30 min)

**Implementation:**
```python
def check_idle_timeout():
    timeout_minutes = get_user_setting('idle_timeout', default=5)
    last_activity = st.session_state.get('last_activity')

    if last_activity and (now() - last_activity) > timedelta(minutes=timeout_minutes):
        clear_sensitive_session_data()
        st.session_state.wallet_locked = True
        return True
    return False
```

### 0.3 Session State Audit
**Priority:** P0 — HIGH
**Files:** All files using `st.session_state`

- [ ] Audit all session state keys for sensitive data
- [ ] Document which keys contain sensitive data
- [ ] Ensure sensitive keys cleared on logout/lock
- [ ] Add `clear_sensitive_session_data()` function
- [ ] Test: Verify no keys leak after logout

**Sensitive keys to track:**
```python
SENSITIVE_SESSION_KEYS = [
    '_wallet_key',
    'decrypted_private_key',
    'mnemonic',
    'seed_phrase',
    # Add all found during audit
]
```

### 0.4 RLS Policy Implementation
**Priority:** P1 — HIGH
**Files:** `supabase_client.py`, Supabase dashboard

- [ ] Create RLS policies for all tables
- [ ] Remove service key usage where possible
- [ ] Test: Verify user can only access own data
- [ ] Test: Verify cross-user data access fails
- [ ] Document remaining service key uses

**SQL to create:**
```sql
-- users table
CREATE POLICY "Users can read own data" ON users
FOR SELECT USING (auth.uid() = id);

-- wallets table
CREATE POLICY "Users can access own wallets" ON wallets
FOR ALL USING (auth.uid() = user_id);

-- transactions table
CREATE POLICY "Users can access own transactions" ON transactions
FOR ALL USING (auth.uid() = user_id);

-- scheduled_tasks table
CREATE POLICY "Users can access own tasks" ON scheduled_tasks
FOR ALL USING (auth.uid() = user_id);

-- settings table
CREATE POLICY "Users can access own settings" ON user_settings
FOR ALL USING (auth.uid() = user_id);
```

### 0.5 Input Validation Hardening
**Priority:** P1 — MEDIUM
**Files:** All tool functions, `direct_tx.py`, `aave_client.py`

- [ ] Validate all addresses (checksum, format)
- [ ] Validate all amounts (positive, within limits)
- [ ] Sanitize all user inputs before DB storage
- [ ] Add rate limiting to sensitive operations
- [ ] Test: Injection attempts blocked

---

# PHASE 1: API FOUNDATION
## Timeline: Week 2-4
## Status: REQUIRED — Unblocks everything else

### 1.1 FastAPI Setup
**Priority:** P0 — CRITICAL
**New Files:** `api/`, `api/main.py`, `api/routes/`

- [ ] Create `api/` directory structure
- [ ] Set up FastAPI application
- [ ] Configure CORS for Streamlit + future clients
- [ ] Add API key authentication middleware
- [ ] Add rate limiting middleware
- [ ] Create health check endpoint
- [ ] Create OpenAPI documentation

**Directory structure:**
```
api/
├── __init__.py
├── main.py              # FastAPI app
├── config.py            # API configuration
├── middleware/
│   ├── auth.py          # Authentication
│   ├── rate_limit.py    # Rate limiting
│   └── logging.py       # Request logging
├── routes/
│   ├── wallet.py        # Wallet operations
│   ├── transactions.py  # Send/receive
│   ├── yield_farming.py # Aave operations
│   ├── agents.py        # Agent management
│   └── x402.py          # Micropayments
├── schemas/
│   ├── wallet.py        # Pydantic models
│   ├── transaction.py
│   └── agent.py
└── services/
    └── # Reuse existing managers
```

### 1.2 Wallet API Endpoints
**Priority:** P0 — CRITICAL
**Files:** `api/routes/wallet.py`

- [ ] `GET /api/v1/wallet/balance` — Get all balances
- [ ] `GET /api/v1/wallet/balance/{chain}` — Get chain balance
- [ ] `GET /api/v1/wallet/address/{chain}` — Get deposit address
- [ ] `POST /api/v1/wallet/create` — Create new wallet
- [ ] `POST /api/v1/wallet/import` — Import from mnemonic
- [ ] `GET /api/v1/wallet/export` — Export mnemonic (auth required)

**Schema:**
```python
class BalanceResponse(BaseModel):
    chain: str
    balance: Decimal
    token: str = "USDC"
    usd_value: Decimal
    updated_at: datetime

class WalletBalances(BaseModel):
    total_usd: Decimal
    balances: List[BalanceResponse]
```

### 1.3 Transaction API Endpoints
**Priority:** P0 — CRITICAL
**Files:** `api/routes/transactions.py`

- [ ] `POST /api/v1/tx/preview` — Preview transaction
- [ ] `POST /api/v1/tx/send` — Execute send
- [ ] `GET /api/v1/tx/status/{tx_hash}` — Check status
- [ ] `GET /api/v1/tx/history` — Transaction history
- [ ] `POST /api/v1/tx/bridge` — Cross-chain bridge

**Schema:**
```python
class TransactionPreview(BaseModel):
    to_address: str
    amount: Decimal
    chain: str
    fee: Decimal
    total: Decimal
    estimated_time: int  # seconds

class TransactionRequest(BaseModel):
    to_address: str
    amount: Decimal
    chain: str = "base"
    user_confirmed: bool = False

class TransactionResponse(BaseModel):
    tx_hash: str
    status: str
    explorer_url: str
```

### 1.4 Yield API Endpoints
**Priority:** P1 — HIGH
**Files:** `api/routes/yield_farming.py`

- [ ] `GET /api/v1/yield/status` — Current yield positions
- [ ] `GET /api/v1/yield/rates` — Available APY rates
- [ ] `POST /api/v1/yield/deposit` — Deposit to yield
- [ ] `POST /api/v1/yield/withdraw` — Withdraw from yield
- [ ] `GET /api/v1/yield/earnings` — Historical earnings

### 1.5 Refactor Streamlit to Use API
**Priority:** P1 — HIGH
**Files:** `app.py`, `components/chat.py`, `components/sidebar.py`

- [ ] Create `api_client.py` for internal API calls
- [ ] Replace direct manager calls with API calls
- [ ] Maintain backward compatibility during transition
- [ ] Test: All existing features work via API
- [ ] Remove direct database calls from Streamlit

### 1.6 Authentication System
**Priority:** P0 — CRITICAL
**Files:** `api/middleware/auth.py`

- [ ] JWT token generation on login
- [ ] Token validation middleware
- [ ] Refresh token flow
- [ ] API key generation for agents
- [ ] Scoped permissions (read, write, admin)

---

# PHASE 2: x402 & PAYMENT INFRASTRUCTURE
## Timeline: Week 4-6
## Status: CRITICAL — Proves Circle partnership value

### 2.1 x402 Protocol Implementation
**Priority:** P0 — CRITICAL
**New Files:** `api/routes/x402.py`, `x402/`

- [ ] Study Circle x402 specification
- [ ] Implement payment request generation
- [ ] Implement payment verification
- [ ] Create HTTP 402 response handler
- [ ] Test with mock payments
- [ ] Integrate with agent system

**Core implementation:**
```python
# x402/handler.py
class X402Handler:
    def create_payment_request(
        self,
        amount: Decimal,
        recipient: str,
        description: str,
        ttl_seconds: int = 300
    ) -> PaymentRequest:
        """Generate x402 payment request"""

    def verify_payment(
        self,
        payment_header: str,
        expected_amount: Decimal
    ) -> PaymentVerification:
        """Verify x-payment header"""

    def generate_402_response(
        self,
        request: PaymentRequest
    ) -> Response:
        """Generate HTTP 402 response with payment details"""
```

### 2.2 x402 API Endpoints
**Priority:** P0 — CRITICAL
**Files:** `api/routes/x402.py`

- [ ] `POST /api/v1/x402/request` — Create payment request
- [ ] `POST /api/v1/x402/verify` — Verify payment
- [ ] `GET /api/v1/x402/status/{payment_id}` — Check payment status
- [ ] `POST /api/v1/x402/pay` — Execute payment (wallet side)

### 2.3 CCTP Enhancement
**Priority:** P1 — HIGH
**Files:** `cctp_client.py`, `api/routes/bridge.py`

- [ ] Add attestation polling with exponential backoff
- [ ] Add bridge status webhooks
- [ ] Create bridge progress UI
- [ ] Add estimated completion time
- [ ] Handle bridge failures gracefully
- [ ] Test mainnet bridges (small amounts)

### 2.4 Payment Links
**Priority:** P1 — HIGH
**New Files:** `api/routes/payment_links.py`

- [ ] Create shareable payment links
- [ ] Support fixed and variable amounts
- [ ] Generate QR codes for links
- [ ] Track payment link usage
- [ ] Webhook on payment received

**Schema:**
```python
class PaymentLink(BaseModel):
    id: str
    recipient: str
    amount: Optional[Decimal]  # None = any amount
    currency: str = "USDC"
    description: str
    url: str
    qr_code: str  # Base64 encoded
    created_at: datetime
    expires_at: Optional[datetime]
```

### 2.5 Revenue Split System
**Priority:** P1 — HIGH
**New Files:** `services/revenue_split.py`

- [ ] Define split ratios (70/20/10)
- [ ] Implement automatic split on payment
- [ ] Track platform revenue
- [ ] Track creator revenue
- [ ] Track referrer revenue
- [ ] Create payout system for creators

---

# PHASE 3: AGENT PROTOCOL
## Timeline: Week 6-10
## Status: THE MOAT

### 3.1 Agent Registry Database
**Priority:** P0 — CRITICAL
**Files:** Supabase migrations

- [ ] Create `agents` table
- [ ] Create `agent_versions` table
- [ ] Create `agent_deployments` table
- [ ] Create `agent_earnings` table
- [ ] Create `agent_reviews` table
- [ ] Add RLS policies for all tables

**Schema:**
```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID REFERENCES users(id) NOT NULL,

    -- Identity
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    category VARCHAR(50),  -- 'trading', 'character', 'content', 'service'

    -- Configuration
    capabilities JSONB,  -- List of capabilities
    pricing_model VARCHAR(50),  -- 'free', 'per_use', 'subscription', 'tips'
    price_amount DECIMAL,

    -- Vault
    vault_address VARCHAR(100),

    -- Status
    status VARCHAR(20) DEFAULT 'draft',  -- 'draft', 'pending_review', 'active', 'suspended'
    is_public BOOLEAN DEFAULT false,

    -- Stats
    total_users INTEGER DEFAULT 0,
    total_earnings DECIMAL DEFAULT 0,
    rating DECIMAL,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE agent_earnings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id) NOT NULL,
    user_id UUID REFERENCES users(id),  -- Who paid

    amount DECIMAL NOT NULL,
    currency VARCHAR(20) DEFAULT 'USDC',
    payment_type VARCHAR(50),  -- 'per_use', 'subscription', 'tip'

    -- Split tracking
    creator_share DECIMAL,
    platform_share DECIMAL,
    referrer_share DECIMAL,
    referrer_id UUID REFERENCES users(id),

    tx_hash VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.2 Agent Protocol SDK
**Priority:** P0 — CRITICAL
**New Files:** `sdk/`, `sdk/agent_protocol.py`

- [ ] Define `USDChatAgent` base class
- [ ] Define capability declaration system
- [ ] Define message handling interface
- [ ] Create payment integration helpers
- [ ] Create agent-to-agent payment helpers
- [ ] Document SDK usage

**Core interface:**
```python
# sdk/agent_protocol.py
from abc import ABC, abstractmethod
from typing import List, Optional
from decimal import Decimal

class AgentCapability:
    name: str
    description: str
    required_params: List[str]

class AgentResponse:
    message: str
    actions: List[dict]  # Actions to execute
    charge_amount: Optional[Decimal]

class USDChatAgent(ABC):
    """Base class for all USDChat agents"""

    def __init__(self, agent_id: str, vault_address: str):
        self.agent_id = agent_id
        self.vault = vault_address

    @abstractmethod
    def get_capabilities(self) -> List[AgentCapability]:
        """Declare what this agent can do"""
        pass

    @abstractmethod
    async def handle_message(
        self,
        user_id: str,
        message: str,
        context: dict
    ) -> AgentResponse:
        """Process user input"""
        pass

    async def charge_user(
        self,
        user_id: str,
        amount: Decimal,
        reason: str
    ) -> bool:
        """Charge user via x402"""
        # Implemented by SDK

    async def pay_agent(
        self,
        agent_id: str,
        amount: Decimal,
        reason: str
    ) -> bool:
        """Pay another agent"""
        # Implemented by SDK
```

### 3.3 Agent API Endpoints
**Priority:** P0 — CRITICAL
**Files:** `api/routes/agents.py`

- [ ] `POST /api/v1/agents` — Create agent
- [ ] `GET /api/v1/agents` — List agents (with filters)
- [ ] `GET /api/v1/agents/{id}` — Get agent details
- [ ] `PUT /api/v1/agents/{id}` — Update agent
- [ ] `DELETE /api/v1/agents/{id}` — Delete agent
- [ ] `POST /api/v1/agents/{id}/deploy` — Deploy agent
- [ ] `POST /api/v1/agents/{id}/message` — Send message to agent
- [ ] `GET /api/v1/agents/{id}/earnings` — Get agent earnings
- [ ] `POST /api/v1/agents/{id}/withdraw` — Withdraw earnings

### 3.4 Agent Execution Runtime
**Priority:** P0 — CRITICAL
**New Files:** `services/agent_runtime.py`

- [ ] Sandboxed execution environment
- [ ] Rate limiting per agent
- [ ] Resource limits (CPU, memory, time)
- [ ] Logging and monitoring
- [ ] Error handling and recovery

### 3.5 Agent Templates
**Priority:** P1 — HIGH
**New Files:** `templates/agents/`

- [ ] Trading bot template
- [ ] AI character template
- [ ] Content agent template
- [ ] Service bot template
- [ ] Custom agent template

### 3.6 Agent Review System
**Priority:** P1 — HIGH
**Files:** `services/agent_review.py`

- [ ] Automated security checks
- [ ] Manual review queue
- [ ] Approval workflow
- [ ] Rejection with feedback
- [ ] Appeal process

---

# PHASE 4: MARKETPLACE
## Timeline: Week 10-14
## Status: NETWORK EFFECTS

### 4.1 Agent Discovery
**Priority:** P0 — CRITICAL
**New Files:** `api/routes/marketplace.py`

- [ ] `GET /api/v1/marketplace/featured` — Featured agents
- [ ] `GET /api/v1/marketplace/trending` — Trending agents
- [ ] `GET /api/v1/marketplace/search` — Search agents
- [ ] `GET /api/v1/marketplace/categories` — Browse by category
- [ ] `GET /api/v1/marketplace/new` — New agents

### 4.2 Marketplace UI
**Priority:** P0 — CRITICAL
**Files:** `components/marketplace.py`

- [ ] Agent cards with key stats
- [ ] Category filters
- [ ] Search functionality
- [ ] Sorting (trending, rating, earnings)
- [ ] Agent detail pages
- [ ] One-click deploy/use

### 4.3 Rating & Reviews
**Priority:** P1 — HIGH
**Files:** `api/routes/reviews.py`

- [ ] `POST /api/v1/agents/{id}/review` — Submit review
- [ ] `GET /api/v1/agents/{id}/reviews` — Get reviews
- [ ] Verified user badges
- [ ] Helpful votes on reviews
- [ ] Creator response capability

### 4.4 Creator Dashboard
**Priority:** P1 — HIGH
**Files:** `components/creator_dashboard.py`

- [ ] Agent performance metrics
- [ ] Earnings analytics
- [ ] User analytics
- [ ] Revenue withdrawals
- [ ] Agent management

### 4.5 Referral System
**Priority:** P1 — HIGH
**Files:** `services/referrals.py`

- [ ] Generate referral links
- [ ] Track referral conversions
- [ ] Calculate referral earnings
- [ ] Referral payouts
- [ ] Referral leaderboard

---

# PHASE 5: SCALE & POLISH
## Timeline: Week 14+
## Status: GROWTH

### 5.1 Mobile PWA
**Priority:** P0 — HIGH
**Files:** Configuration, CSS

- [ ] Service worker setup
- [ ] Offline capability
- [ ] Push notifications
- [ ] Install prompts
- [ ] Mobile-optimized UI
- [ ] Deep links

### 5.2 Mobile Native (Future)
**Priority:** P2 — MEDIUM
**New repo:** `usdchat-mobile`

- [ ] React Native setup
- [ ] API integration
- [ ] Biometric auth
- [ ] Push notifications
- [ ] App store submission

### 5.3 Analytics & Monitoring
**Priority:** P1 — HIGH
**Files:** `services/analytics.py`

- [ ] Event tracking (PostHog/Mixpanel)
- [ ] Error tracking (Sentry)
- [ ] Performance monitoring
- [ ] User funnel analysis
- [ ] A/B testing framework

### 5.4 Performance Optimization
**Priority:** P1 — MEDIUM
**Files:** Various

- [ ] Database query optimization
- [ ] Caching layer (Redis)
- [ ] CDN for static assets
- [ ] API response compression
- [ ] Connection pooling

### 5.5 Scheduler Deployment
**Priority:** P0 — CRITICAL (moved here but should be earlier)
**Files:** `scheduler_executor.py`

- [ ] Deploy as Supabase Edge Function
- [ ] Or deploy as separate worker process
- [ ] Add monitoring and alerting
- [ ] Add retry logic
- [ ] Add failure notifications

---

# Dependency Graph

```
PHASE 0: Security ──────────────────────────────────────┐
    │                                                    │
    ▼                                                    │
PHASE 1: API ───────────────────────────────────────────┤
    │                                                    │
    ├──────────────┬──────────────┐                     │
    ▼              ▼              ▼                     │
PHASE 2:       PHASE 3:      PHASE 5.5:                │
x402           Agents        Scheduler                  │
    │              │              │                     │
    └──────────────┴──────────────┘                     │
                   │                                     │
                   ▼                                     │
              PHASE 4:                                   │
              Marketplace                                │
                   │                                     │
                   ▼                                     │
              PHASE 5:                                   │
              Scale ◄───────────────────────────────────┘
```

---

# Timeline Summary

| Week | Phase | Key Deliverables |
|------|-------|------------------|
| 1-2 | Security | Cookie fix, auto-lock, RLS policies |
| 2-4 | API | FastAPI setup, wallet/tx endpoints |
| 4-6 | x402 | Micropayments, payment links |
| 6-10 | Agents | Protocol, SDK, runtime |
| 10-14 | Marketplace | Discovery, reviews, creator tools |
| 14+ | Scale | Mobile, analytics, optimization |

---

*Document Owner: Engineering Team*
*Last Updated: February 2026*
*Depends On: STRATEGIC_DIRECTION.md*
