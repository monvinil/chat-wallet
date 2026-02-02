"""
Example: Crypto News Agent

A simple agent that provides crypto news summaries for a small fee.
Demonstrates:
- Per-request pricing
- x402 micropayments
- Capability system
"""

import asyncio
from usdchat_agent import (
    Agent,
    AgentContext,
    AgentResponse,
    capability,
    x402_payment,
)


class CryptoNewsAgent(Agent):
    """
    An agent that provides crypto news summaries.

    Pricing: $0.01 per news request
    """

    def __init__(self):
        super().__init__(
            name="Crypto News Bot",
            description="Get the latest crypto news summarized by AI",
            category="content",
            tags=["crypto", "news", "ai"],
            pricing_model="per_request",
            price_per_request=0.01,
            accepts_tips=True,
            required_capabilities=["accept_payments"],
        )

    async def handle(self, message: str, context: AgentContext) -> AgentResponse:
        """Handle incoming requests."""

        # Parse the request
        message_lower = message.lower()

        if "bitcoin" in message_lower or "btc" in message_lower:
            return await self.get_bitcoin_news(context)
        elif "ethereum" in message_lower or "eth" in message_lower:
            return await self.get_ethereum_news(context)
        elif "solana" in message_lower or "sol" in message_lower:
            return await self.get_solana_news(context)
        else:
            return await self.get_general_news(context)

    @x402_payment(amount=0.01, description="Get Bitcoin news summary")
    async def get_bitcoin_news(self, context: AgentContext) -> AgentResponse:
        """Get Bitcoin-specific news."""
        # In a real agent, this would fetch from news APIs
        news = """
        **Bitcoin News Summary**

        1. Bitcoin ETFs see record inflows of $500M today
        2. MicroStrategy adds another 10,000 BTC to holdings
        3. Lightning Network capacity hits new ATH of 5,000 BTC

        *Powered by Crypto News Bot*
        """
        return AgentResponse(content=news.strip())

    @x402_payment(amount=0.01, description="Get Ethereum news summary")
    async def get_ethereum_news(self, context: AgentContext) -> AgentResponse:
        """Get Ethereum-specific news."""
        news = """
        **Ethereum News Summary**

        1. Ethereum L2s process 10x mainnet transactions
        2. Vitalik proposes new scaling solution
        3. Major DeFi protocol launches on Base

        *Powered by Crypto News Bot*
        """
        return AgentResponse(content=news.strip())

    @x402_payment(amount=0.01, description="Get Solana news summary")
    async def get_solana_news(self, context: AgentContext) -> AgentResponse:
        """Get Solana-specific news."""
        news = """
        **Solana News Summary**

        1. Solana processes 100M transactions this week
        2. New token launches break records on pump.fun
        3. Jupiter DEX volume exceeds Uniswap

        *Powered by Crypto News Bot*
        """
        return AgentResponse(content=news.strip())

    @x402_payment(amount=0.01, description="Get general crypto news")
    async def get_general_news(self, context: AgentContext) -> AgentResponse:
        """Get general crypto market news."""
        news = """
        **Crypto Market Summary**

        1. Total crypto market cap reaches $3T
        2. Stablecoin market hits new ATH at $200B
        3. Circle announces x402 micropayments protocol
        4. AI agents start earning on-chain

        *Powered by Crypto News Bot*
        """
        return AgentResponse(content=news.strip())


# Example usage
if __name__ == "__main__":
    agent = CryptoNewsAgent()
    print(f"Agent: {agent.config.name}")
    print(f"Pricing: {agent.config.pricing_model.value}")
    print(f"Price: ${agent.config.price_per_request} per request")
    print(f"Capabilities: {agent.config.required_capabilities}")
