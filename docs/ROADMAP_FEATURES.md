# Chat Wallet - Roadmap Features

## Overview

Three major features to transform from "chatbot with tools" to "AI financial autopilot":

1. **Scheduled Actions** - Recurring/scheduled transactions and automations
2. **Cross-Chain Bridging** - Stargate/deBridge integration for USDC movement
3. **Context Awareness** - Spending insights, alerts, and proactive advice

---

## 1. Scheduled Actions

### Purpose
Enable users to set financial intentions that execute automatically:
- "Send $100 to savings every Friday"
- "DCA $50 into ETH every Monday"
- "Pay Netflix when bill arrives"
- "Top up phone when balance < $10"

### Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   User Chat     │────▶│  Schedule Tool   │────▶│   Supabase DB   │
│   "Schedule X"  │     │  (LangChain)     │     │  scheduled_tasks│
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Notification   │◀────│  Task Executor   │◀────│  Cron Worker    │
│  (Email/Push)   │     │  (Background)    │     │  (Every minute) │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### Database Schema

```sql
-- Scheduled tasks table
CREATE TABLE scheduled_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) NOT NULL,

    -- Task definition
    task_type VARCHAR(50) NOT NULL,  -- 'transfer', 'swap', 'gift_card', 'bridge'
    task_params JSONB NOT NULL,       -- Action-specific parameters

    -- Schedule configuration
    schedule_type VARCHAR(20) NOT NULL,  -- 'once', 'recurring', 'conditional'
    cron_expression VARCHAR(100),         -- For recurring: "0 9 * * 1" (Mon 9am)
    next_run_at TIMESTAMPTZ,

    -- Conditional triggers (optional)
    condition_type VARCHAR(50),           -- 'balance_below', 'balance_above', 'price_below'
    condition_value DECIMAL,
    condition_asset VARCHAR(20),

    -- Execution tracking
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'paused', 'completed', 'failed'
    last_run_at TIMESTAMPTZ,
    last_result JSONB,
    run_count INTEGER DEFAULT 0,
    max_runs INTEGER,                      -- NULL = unlimited

    -- Metadata
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Execution history
CREATE TABLE scheduled_task_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES scheduled_tasks(id) NOT NULL,

    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL,  -- 'success', 'failed', 'skipped'
    result JSONB,
    error_message TEXT,
    tx_hash VARCHAR(100)
);

-- Indexes
CREATE INDEX idx_scheduled_tasks_next_run ON scheduled_tasks(next_run_at)
    WHERE status = 'active';
CREATE INDEX idx_scheduled_tasks_user ON scheduled_tasks(user_id);
```

### Task Types & Parameters

```python
# Transfer task
{
    "task_type": "transfer",
    "task_params": {
        "to_address": "0x...",
        "amount": 100.00,
        "currency": "USDC",
        "network": "base"
    }
}

# Swap task
{
    "task_type": "swap",
    "task_params": {
        "from_currency": "USDC",
        "to_currency": "ETH",
        "amount": 50.00,
        "slippage_percent": 0.5
    }
}

# Gift card task
{
    "task_type": "gift_card",
    "task_params": {
        "product_id": "netflix-us",
        "amount": 15.99,
        "email": "user@example.com"
    }
}

# Bridge task
{
    "task_type": "bridge",
    "task_params": {
        "from_network": "arbitrum",
        "to_network": "base",
        "amount": 500.00,
        "currency": "USDC"
    }
}
```

### LangChain Tools

```python
# scheduler_tools.py

@tool
def create_scheduled_task(
    description: str,
    task_type: str,
    task_params: dict,
    schedule: str,  # "once:2024-01-15T09:00:00" or "recurring:weekly:monday:9am" or "when:balance_below:50"
) -> str:
    """
    Create a scheduled or conditional task.

    Args:
        description: Human-readable description ("Send $100 to mom every Friday")
        task_type: One of 'transfer', 'swap', 'gift_card', 'bridge'
        task_params: Parameters specific to the task type
        schedule: When to execute - can be:
            - "once:DATETIME" for one-time
            - "recurring:daily|weekly|monthly:DAY:TIME" for recurring
            - "when:CONDITION:VALUE" for conditional

    Returns:
        Confirmation with task ID and next run time
    """

@tool
def list_scheduled_tasks() -> str:
    """List all active scheduled tasks for the current user."""

@tool
def cancel_scheduled_task(task_id: str) -> str:
    """Cancel/delete a scheduled task."""

@tool
def pause_scheduled_task(task_id: str) -> str:
    """Temporarily pause a scheduled task."""
```

### Background Worker

```python
# scheduler_worker.py

async def run_scheduler():
    """Main scheduler loop - runs every minute"""
    while True:
        # Get tasks due to run
        due_tasks = get_due_tasks()  # WHERE next_run_at <= NOW() AND status = 'active'

        for task in due_tasks:
            try:
                # Execute based on task type
                result = await execute_task(task)

                # Log execution
                log_task_run(task.id, 'success', result)

                # Update next run time (for recurring)
                update_next_run(task)

                # Notify user (optional)
                if task.notify_on_complete:
                    send_notification(task.user_id, result)

            except Exception as e:
                log_task_run(task.id, 'failed', error=str(e))

                # Maybe pause after N failures
                if task.consecutive_failures >= 3:
                    pause_task(task.id)

        await asyncio.sleep(60)  # Check every minute
```

### Example User Flows

```
User: "Send $100 to 0x1234... every Friday at 9am"
AI: I'll set up a recurring transfer for you.
    - Amount: $100 USDC
    - To: 0x1234...5678
    - Schedule: Every Friday at 9:00 AM
    - First transfer: This Friday, Jan 19

    Confirm? (yes/no)

User: "yes"
AI: Scheduled! Task ID: sched_abc123
    I'll send you a confirmation after each transfer.
    You can say "show my scheduled tasks" to manage them.
```

```
User: "Buy $25 of ETH whenever my USDC balance goes above $500"
AI: I'll set up a conditional swap:
    - Trigger: When USDC balance > $500
    - Action: Swap $25 USDC → ETH
    - Frequency: Check every hour, max once per day

    Confirm?
```

---

## 2. Cross-Chain Bridging

### Purpose
Abstract away multi-chain complexity:
- "Bridge my USDC from Arbitrum to Base"
- "Move all my funds to the cheapest network"
- Auto-optimize for gas costs

### Integration Options

| Bridge | Pros | Cons |
|--------|------|------|
| **Stargate V2** | Fast, USDC native, unified liquidity | Complex SDK |
| **deBridge** | Wide chain support, good API | Newer, less battle-tested |
| **Circle CCTP** | Native USDC burn/mint, most secure | Limited chains |
| **Across Protocol** | Fast, good UX | Requires ETH for fees |

**Recommendation: Start with Circle CCTP for USDC (most secure), add Stargate for speed**

### Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   User Chat     │────▶│   Bridge Tool    │────▶│  Bridge Router  │
│  "Bridge to X"  │     │   (LangChain)    │     │  (Best path)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                          │
                              ┌────────────────┬──────────┴──────────┐
                              ▼                ▼                     ▼
                        ┌──────────┐    ┌──────────┐          ┌──────────┐
                        │  CCTP    │    │ Stargate │          │ deBridge │
                        │  (Slow)  │    │  (Fast)  │          │ (Backup) │
                        └──────────┘    └──────────┘          └──────────┘
```

### Database Schema

```sql
-- Bridge transactions
CREATE TABLE bridge_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) NOT NULL,

    -- Bridge details
    bridge_provider VARCHAR(50) NOT NULL,  -- 'cctp', 'stargate', 'debridge'
    from_chain VARCHAR(50) NOT NULL,
    to_chain VARCHAR(50) NOT NULL,
    amount DECIMAL NOT NULL,
    currency VARCHAR(20) DEFAULT 'USDC',

    -- Transaction hashes
    source_tx_hash VARCHAR(100),
    destination_tx_hash VARCHAR(100),

    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'confirming', 'completed', 'failed'
    estimated_completion TIMESTAMPTZ,

    -- Fees
    bridge_fee DECIMAL,
    gas_fee_source DECIMAL,
    gas_fee_dest DECIMAL,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
```

### LangChain Tools

```python
# bridge_tools.py

@tool
def get_bridge_quote(
    from_chain: str,
    to_chain: str,
    amount: float,
    currency: str = "USDC"
) -> str:
    """
    Get quotes from available bridges for cross-chain transfer.

    Returns comparison of speed, fees, and recommended option.
    """

@tool
def bridge_usdc(
    from_chain: str,
    to_chain: str,
    amount: float,
    speed: str = "normal",  # 'fast' (Stargate) or 'normal' (CCTP)
    user_approved: bool = False
) -> str:
    """
    Bridge USDC between chains.

    Args:
        from_chain: Source chain ('base', 'arbitrum', 'polygon', 'ethereum')
        to_chain: Destination chain
        amount: Amount in USDC
        speed: 'fast' (~2min, higher fee) or 'normal' (~15min, lower fee)
        user_approved: Must be True to execute

    Returns:
        Bridge transaction status and tracking info
    """

@tool
def check_bridge_status(bridge_id: str) -> str:
    """Check status of a pending bridge transaction."""

@tool
def suggest_optimal_chain() -> str:
    """
    Analyze user's balances and suggest optimal chain based on:
    - Where they have funds
    - Gas costs on each chain
    - Their typical usage patterns
    """
```

### Circle CCTP Integration

```python
# cctp_bridge.py

from web3 import Web3

# CCTP Contract addresses (mainnet)
CCTP_CONTRACTS = {
    "ethereum": {
        "token_messenger": "0xBd3fa81B58Ba92a82136038B25aDec7066af3155",
        "message_transmitter": "0x0a992d191DEeC32aFe36203Ad87D7d289a738F81"
    },
    "base": {
        "token_messenger": "0x1682Ae6375C4E4A97e4B583BC394c861A46D8962",
        "message_transmitter": "0xAD09780d193884d503182aD4588450C416D6F9D4"
    },
    # ... other chains
}

class CCTPBridge:
    def __init__(self, source_chain: str, dest_chain: str):
        self.source = source_chain
        self.dest = dest_chain

    async def initiate_bridge(self, amount: int, recipient: str, private_key: str) -> dict:
        """
        1. Approve USDC spend to TokenMessenger
        2. Call depositForBurn on source chain
        3. Wait for attestation from Circle
        4. Call receiveMessage on destination
        """

    async def get_attestation(self, message_hash: str) -> str:
        """Fetch attestation from Circle's attestation service"""
        # https://iris-api.circle.com/attestations/{message_hash}

    async def complete_bridge(self, message: bytes, attestation: str) -> str:
        """Submit attestation to destination chain to receive funds"""
```

---

## 3. Context Awareness & Insights

### Purpose
Transform AI from reactive to proactive:
- Spending summaries and trends
- Low balance alerts
- Subscription tracking
- Personalized recommendations

### Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Transaction    │────▶│  Analytics       │────▶│   Insights DB   │
│  History        │     │  Processor       │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                          │
┌─────────────────┐     ┌──────────────────┐              │
│   User Chat     │◀────│  Insights Tool   │◀─────────────┘
│                 │     │  (LangChain)     │
└─────────────────┘     └──────────────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │  Alert System    │───▶ Email/Push
                        │  (Background)    │
                        └──────────────────┘
```

### Database Schema

```sql
-- Spending categories (auto-detected)
CREATE TABLE spending_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) NOT NULL,
    tx_hash VARCHAR(100) NOT NULL,

    category VARCHAR(50),      -- 'entertainment', 'food', 'subscription', 'transfer', 'defi'
    subcategory VARCHAR(50),   -- 'netflix', 'starbucks', 'aave_deposit'
    merchant_name VARCHAR(100),

    amount DECIMAL NOT NULL,
    currency VARCHAR(20),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User alerts configuration
CREATE TABLE user_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) NOT NULL,

    alert_type VARCHAR(50) NOT NULL,  -- 'low_balance', 'large_tx', 'weekly_summary'
    threshold DECIMAL,                 -- For balance alerts
    is_enabled BOOLEAN DEFAULT true,

    -- Delivery preferences
    notify_email BOOLEAN DEFAULT true,
    notify_push BOOLEAN DEFAULT false,

    last_triggered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Spending summaries (pre-computed)
CREATE TABLE spending_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) NOT NULL,

    period_type VARCHAR(20) NOT NULL,  -- 'daily', 'weekly', 'monthly'
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    total_spent DECIMAL,
    total_received DECIMAL,

    -- Category breakdown
    by_category JSONB,  -- {"entertainment": 45.00, "food": 120.00, ...}

    -- Comparisons
    vs_previous_period DECIMAL,  -- Percentage change

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, period_type, period_start)
);
```

### LangChain Tools

```python
# insights_tools.py

@tool
def get_spending_summary(period: str = "week") -> str:
    """
    Get spending summary for the current user.

    Args:
        period: 'day', 'week', 'month', or 'year'

    Returns:
        Breakdown by category, comparison to previous period,
        and notable transactions.
    """

@tool
def get_spending_by_category(category: str = None) -> str:
    """
    Get detailed spending for a specific category or all categories.

    Categories: entertainment, food, subscriptions, transfers, defi, shopping
    """

@tool
def set_balance_alert(threshold: float, above_or_below: str = "below") -> str:
    """
    Set an alert when balance crosses a threshold.

    Args:
        threshold: Dollar amount
        above_or_below: 'below' for low balance alert, 'above' for large balance
    """

@tool
def get_subscriptions() -> str:
    """
    Detect and list recurring payments that look like subscriptions.
    Shows: name, amount, frequency, next expected date.
    """

@tool
def get_financial_health() -> str:
    """
    Overall financial health check:
    - Current balances across chains
    - Monthly burn rate
    - Subscription commitments
    - Savings rate (if any transfers to savings detected)
    """
```

### Analytics Processing

```python
# analytics_processor.py

class SpendingAnalyzer:

    # Category detection rules
    CATEGORY_RULES = {
        "entertainment": ["netflix", "spotify", "hulu", "disney", "playstation", "xbox", "steam"],
        "food": ["doordash", "ubereats", "grubhub", "starbucks", "dunkin"],
        "subscriptions": ["netflix", "spotify", "apple", "amazon prime", "youtube"],
        "shopping": ["amazon", "target", "walmart", "sephora"],
        "travel": ["uber", "lyft", "airbnb", "travala"],
        "defi": ["aave", "uniswap", "compound", "lido"],
    }

    def categorize_transaction(self, tx: dict) -> str:
        """Auto-categorize based on merchant/recipient"""

    def compute_weekly_summary(self, user_id: str) -> dict:
        """Generate weekly spending summary"""

    def detect_subscriptions(self, user_id: str) -> list:
        """Find recurring payments with similar amounts"""

    def calculate_burn_rate(self, user_id: str) -> float:
        """Average daily/monthly spending"""
```

### Alert System

```python
# alert_system.py

class AlertManager:

    async def check_balance_alerts(self):
        """Run every 5 minutes - check all low balance alerts"""
        alerts = get_active_alerts(alert_type='low_balance')

        for alert in alerts:
            balance = get_user_total_balance(alert.user_id)

            if balance < alert.threshold:
                if not recently_triggered(alert):
                    send_alert(
                        user_id=alert.user_id,
                        title="Low Balance Alert",
                        message=f"Your balance is ${balance:.2f}, below your ${alert.threshold:.2f} threshold."
                    )
                    mark_triggered(alert)

    async def send_weekly_summaries(self):
        """Run every Monday morning"""
        users = get_users_with_alert_enabled('weekly_summary')

        for user in users:
            summary = compute_weekly_summary(user.id)
            send_email(
                to=user.email,
                subject="Your Weekly Spending Summary",
                body=format_summary_email(summary)
            )
```

---

## Implementation Priority

### Phase 1: Foundation (Week 1-2)
1. Database migrations for all three features
2. Basic scheduled tasks (one-time transfers only)
3. Simple spending categorization

### Phase 2: Scheduling (Week 3-4)
1. Recurring task support
2. Conditional triggers
3. Background worker deployment
4. Task management UI in chat

### Phase 3: Bridging (Week 5-6)
1. Circle CCTP integration
2. Bridge status tracking
3. Chain optimization suggestions

### Phase 4: Insights (Week 7-8)
1. Full categorization engine
2. Alert system
3. Weekly summaries
4. Financial health tool

---

## Required Infrastructure

### New Dependencies
```
# requirements.txt additions
apscheduler>=3.10.0      # Scheduling
aiohttp>=3.9.0           # Async HTTP for bridge APIs
```

### Environment Variables
```
# Bridging
CCTP_ATTESTATION_API=https://iris-api.circle.com
STARGATE_API_KEY=...

# Alerts
SENDGRID_API_KEY=...     # For email alerts
PUSH_NOTIFICATION_KEY=...
```

### Supabase Edge Functions
For background tasks without a separate server:
- `scheduler-worker`: Runs every minute, executes due tasks
- `alert-checker`: Runs every 5 minutes, checks balance alerts
- `weekly-summary`: Runs Monday 9am, sends summaries

---

## Capability Library Updates

After implementation, update `render_suggested_actions()` in app.py:

```python
# New capabilities to mark as live
("📅", "Schedule Transfer", "Schedule a recurring transfer", True),
("🌉", "Bridge USDC", "Bridge my USDC to another chain", True),
("📊", "Spending Insights", "Show my spending summary", True),
("⏰", "Set Alert", "Alert me when balance is low", True),
```

---

## Security Considerations

### Scheduled Tasks
- Require re-authentication for high-value scheduled tasks
- Max amount limits per scheduled task
- Rate limiting on task creation
- Audit log for all executions

### Bridging
- Whitelist supported chains
- Maximum bridge amounts
- Confirmation required for large bridges
- Transaction simulation before execution

### Insights
- All data encrypted at rest
- No sharing of spending data
- User can delete all analytics data
- GDPR compliant data handling
