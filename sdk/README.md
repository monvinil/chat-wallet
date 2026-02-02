# USDChat Agent SDK

Create AI agents that earn money. This SDK provides the building blocks for creating agents that can accept payments, make payments, and interact with the USDChat ecosystem.

## Installation

```bash
pip install usdchat-agent
```

Or install from source:

```bash
cd sdk
pip install -e .
```

## Quick Start

```python
from usdchat_agent import Agent, AgentContext, AgentResponse

class MyAgent(Agent):
    async def handle(self, message: str, context: AgentContext) -> AgentResponse:
        return AgentResponse(content=f"Hello! You said: {message}")

agent = MyAgent(
    name="Hello Agent",
    description="A friendly greeting agent",
    category="utility",
)
```

## Pricing Models

### Free Agent

```python
agent = MyAgent(
    name="Free Agent",
    pricing_model="free",  # No payment required
)
```

### Per-Request Pricing

```python
from usdchat_agent import x402_payment

class PaidAgent(Agent):
    @x402_payment(amount=0.01, description="Generate response")
    async def handle(self, message: str, context: AgentContext) -> AgentResponse:
        # This method requires 0.01 USDC payment
        return AgentResponse(content="Premium content!")

agent = PaidAgent(
    name="Paid Agent",
    pricing_model="per_request",
    price_per_request=0.01,
)
```

### Subscription Pricing

```python
agent = MyAgent(
    name="Pro Agent",
    pricing_model="subscription",
    subscription_price_monthly=5.0,  # $5/month
)
```

## Capabilities

Capabilities define what your agent can do. Users must grant permissions for certain capabilities.

### Built-in Capabilities

| Capability | Risk | Description |
|------------|------|-------------|
| `accept_payments` | Low | Receive payments via x402 |
| `make_payments` | High | Send payments on user's behalf |
| `yield_access` | High | Access yield protocols |
| `trade` | Critical | Execute trades |
| `read_balance` | Low | View user's balance |
| `read_history` | Medium | View transaction history |
| `notifications` | Low | Send notifications |
| `schedule_tasks` | Medium | Create scheduled tasks |

### Using Capabilities

```python
from usdchat_agent import capability

class TradingAgent(Agent):
    @capability("trade")
    async def execute_swap(self, context: AgentContext) -> AgentResponse:
        # This method requires the 'trade' capability
        # Will raise CapabilityDeniedError if not granted
        return AgentResponse(content="Trade executed!")
```

## Revenue Split

By default, revenue is split:
- **Creator**: 70%
- **Platform**: 20%
- **Referrer**: 10%

Customize the split:

```python
agent = MyAgent(
    name="Custom Split Agent",
    creator_share_percent=80,
    platform_share_percent=15,
    referrer_share_percent=5,
)
```

## Agent Context

The `AgentContext` provides information about each request:

```python
async def handle(self, message: str, context: AgentContext) -> AgentResponse:
    # User info
    user_id = context.user.user_id
    wallet = context.user.wallet_address

    # Payment status
    if context.payment_verified:
        amount = context.payment_amount
        tx = context.payment_tx_hash

    # Subscription status
    if context.has_active_subscription:
        expires = context.subscription_expires_at

    # Granted permissions
    caps = context.user.granted_capabilities

    return AgentResponse(content="...")
```

## Error Handling

```python
from usdchat_agent import (
    PaymentRequiredError,
    CapabilityDeniedError,
    RateLimitError,
)

try:
    response = await agent.process_request(message, context)
except PaymentRequiredError as e:
    # Return HTTP 402 with payment details
    payment_info = e.to_402_response()
except CapabilityDeniedError as e:
    # User hasn't granted required capability
    print(f"Need permission: {e.capability}")
except RateLimitError as e:
    # Rate limit exceeded
    print(f"Try again at: {e.reset_at}")
```

## Examples

See the `examples/` directory for complete agent implementations:

- `crypto_news_agent.py` - Per-request pricing, content agent
- `trading_bot_agent.py` - Subscription pricing, trading capabilities

## Agent Categories

| Category | Description |
|----------|-------------|
| `trading` | Trading bots, market making |
| `content` | News, summaries, generation |
| `service` | Task completion, automation |
| `character` | AI personalities, companions |
| `yield` | DeFi strategies, yield farming |
| `utility` | General utilities |

## Deployment

1. **Register your agent** on the USDChat platform
2. **Deploy your endpoint** (webhook or hosted)
3. **Submit for review** (required for high-risk capabilities)
4. **Go live** and start earning!

## Support

- Documentation: https://docs.usdchat.com/agents
- Discord: https://discord.gg/usdchat
- GitHub Issues: https://github.com/usdchat/agent-sdk/issues
