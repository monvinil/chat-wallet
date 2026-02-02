"""
Example: Simple Trading Bot Agent

A trading agent that can execute basic trades on user's behalf.
Demonstrates:
- High-risk capabilities (trade, make_payments)
- Subscription pricing model
- User permission checks
"""

from usdchat_agent import (
    Agent,
    AgentContext,
    AgentResponse,
    capability,
    PaymentRequiredError,
)
from usdchat_agent.types import TransactionRequest, TransactionType, Chain
from usdchat_agent.capabilities import requires_capabilities


@requires_capabilities("trade", "read_balance")
class SimpleTradingBot(Agent):
    """
    A simple trading bot that can execute swaps.

    Requires subscription: $5/month
    Capabilities needed: trade, read_balance

    Note: This is a HIGH-RISK agent that requires user verification.
    """

    def __init__(self):
        super().__init__(
            name="Simple Swap Bot",
            description="Automated token swaps with configurable strategies",
            category="trading",
            tags=["trading", "swap", "automation", "defi"],
            pricing_model="subscription",
            subscription_price_monthly=5.0,
            accepts_tips=True,
            required_capabilities=["trade", "read_balance"],
        )

        # Trading strategies
        self.strategies = {
            "dca": self.execute_dca,
            "limit": self.execute_limit_order,
            "stop_loss": self.execute_stop_loss,
        }

    async def handle(self, message: str, context: AgentContext) -> AgentResponse:
        """Handle trading commands."""

        message_lower = message.lower().strip()

        # Parse command
        if message_lower.startswith("swap "):
            return await self.handle_swap(message, context)
        elif message_lower.startswith("dca "):
            return await self.handle_dca(message, context)
        elif message_lower == "balance":
            return await self.get_balance(context)
        elif message_lower == "help":
            return self.get_help()
        else:
            return AgentResponse(
                content="Unknown command. Type 'help' for available commands."
            )

    @capability("trade")
    async def handle_swap(self, message: str, context: AgentContext) -> AgentResponse:
        """
        Handle a swap command.
        Format: swap <amount> <from_token> to <to_token>
        Example: swap 100 USDC to ETH
        """
        try:
            parts = message.split()
            # swap 100 USDC to ETH
            amount = float(parts[1])
            from_token = parts[2].upper()
            to_token = parts[4].upper()

            # Create transaction request
            tx_request = TransactionRequest(
                type=TransactionType.SWAP,
                amount=amount,
                currency=from_token,
                from_token=from_token,
                to_token=to_token,
                chain=Chain.BASE,
                slippage_percent=0.5,
                description=f"Swap {amount} {from_token} to {to_token}",
            )

            # In a real implementation, this would call the platform API
            # to execute the swap
            return AgentResponse(
                content=f"Swap order created: {amount} {from_token} -> {to_token}\n"
                        f"Slippage: 0.5%\n"
                        f"Status: Pending execution\n\n"
                        f"Note: This is a demo - real execution requires platform integration.",
                metadata={"tx_request": tx_request.__dict__}
            )

        except (IndexError, ValueError) as e:
            return AgentResponse(
                content="Invalid swap format. Use: swap <amount> <from_token> to <to_token>\n"
                        "Example: swap 100 USDC to ETH"
            )

    @capability("trade")
    async def handle_dca(self, message: str, context: AgentContext) -> AgentResponse:
        """
        Handle DCA (Dollar Cost Average) setup.
        Format: dca <amount> <token> every <interval>
        Example: dca 50 USDC into ETH every day
        """
        return AgentResponse(
            content="DCA strategy configuration:\n\n"
                    "This would set up a recurring purchase.\n"
                    "In production, this creates a scheduled_task entry.\n\n"
                    "Note: Requires scheduler deployment to execute."
        )

    @capability("read_balance")
    async def get_balance(self, context: AgentContext) -> AgentResponse:
        """Get user's current balance."""
        # In production, this would call the platform API
        return AgentResponse(
            content=f"Balance for {context.user.wallet_address[:10]}...:\n\n"
                    f"This would show real balances via platform API.\n"
                    f"Capabilities granted: {context.user.granted_capabilities}"
        )

    def get_help(self) -> AgentResponse:
        """Return help message."""
        return AgentResponse(
            content="""
**Simple Swap Bot Commands**

**Trading:**
- `swap <amount> <from> to <to>` - Execute a token swap
  Example: `swap 100 USDC to ETH`

- `dca <amount> <token> into <token> every <interval>` - Set up DCA
  Example: `dca 50 USDC into ETH every day`

**Info:**
- `balance` - Check your current balance
- `help` - Show this help message

**Required Permissions:**
This bot requires the following permissions:
- `trade` - To execute swaps on your behalf
- `read_balance` - To check your balances

**Pricing:**
$5/month subscription
            """.strip()
        )

    async def execute_dca(self, *args, **kwargs):
        """Execute DCA strategy."""
        pass

    async def execute_limit_order(self, *args, **kwargs):
        """Execute limit order strategy."""
        pass

    async def execute_stop_loss(self, *args, **kwargs):
        """Execute stop loss strategy."""
        pass


# Example usage
if __name__ == "__main__":
    agent = SimpleTradingBot()
    print(f"Agent: {agent.config.name}")
    print(f"Pricing: {agent.config.pricing_model.value}")
    print(f"Monthly price: ${agent.config.subscription_price_monthly}")
    print(f"Required capabilities: {agent.config.required_capabilities}")
    print(f"\nThis agent requires HIGH-RISK permissions:")
    print("- trade: Can execute trades")
    print("- read_balance: Can view your balances")
