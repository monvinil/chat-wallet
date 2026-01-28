"""
Showcase Agents - Pre-prompted money-making flows for demos
These demonstrate USDChat's core value prop: AI + Wallet + Identity Access
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ShowcaseAgent:
    """A pre-prompted agent flow for demos"""
    id: str
    name: str
    icon: str
    tagline: str
    description: str
    initial_prompt: str
    category: str  # earn, save, automate
    complexity: str  # easy, medium, hard
    demo_ready: bool  # False = coming soon


# === SHOWCASE AGENT DEFINITIONS ===

SHOWCASE_AGENTS: List[ShowcaseAgent] = [
    # === EARN CATEGORY ===
    ShowcaseAgent(
        id="yield-finder",
        name="Yield Finder",
        icon="📈",
        tagline="Find the best APY for your USDC",
        description="Scans DeFi protocols and finds the highest yield opportunities for your idle USDC. Compares Aave, Compound, and other major protocols.",
        initial_prompt="What's the best yield I can get on my USDC right now? Show me the top 3 options with their APY and risk levels.",
        category="earn",
        complexity="medium",
        demo_ready=False  # Needs DeFi integration
    ),
    ShowcaseAgent(
        id="airdrop-hunter",
        name="Airdrop Hunter",
        icon="🎯",
        tagline="Never miss a crypto airdrop",
        description="Monitors your wallet eligibility for upcoming airdrops. Alerts you when you qualify and can help claim.",
        initial_prompt="Check if my wallet is eligible for any upcoming airdrops. What actions can I take to qualify for more?",
        category="earn",
        complexity="medium",
        demo_ready=False  # Needs airdrop APIs
    ),
    ShowcaseAgent(
        id="dca-bot",
        name="DCA Bot",
        icon="🔄",
        tagline="Stack sats on autopilot",
        description="Dollar-cost average into BTC or ETH with scheduled purchases. Set it and forget it.",
        initial_prompt="Set up a weekly $10 Bitcoin purchase every Monday. Use the best available rate.",
        category="earn",
        complexity="easy",
        demo_ready=False  # Needs swap integration
    ),

    # === SAVE CATEGORY ===
    ShowcaseAgent(
        id="gift-card-saver",
        name="Gift Card Saver",
        icon="🎁",
        tagline="Buy gift cards with crypto",
        description="Purchase discounted gift cards for Amazon, Netflix, Uber, and 100+ brands. Pay with USDC.",
        initial_prompt="I want to buy a $50 Amazon gift card. Show me the options.",
        category="save",
        complexity="easy",
        demo_ready=True  # Works with Bitrefill
    ),
    ShowcaseAgent(
        id="cashback-stacker",
        name="Cashback Stacker",
        icon="💰",
        tagline="Stack cashback on every purchase",
        description="Routes your purchases through cashback portals and rebate programs to maximize savings.",
        initial_prompt="What cashback options are available for Amazon purchases? How can I stack discounts?",
        category="save",
        complexity="medium",
        demo_ready=False  # Needs cashback APIs
    ),
    ShowcaseAgent(
        id="subscription-auditor",
        name="Subscription Auditor",
        icon="📋",
        tagline="Find and cancel unused subscriptions",
        description="Scans your email for subscription receipts and identifies what you're paying for. Helps cancel what you don't use.",
        initial_prompt="Scan my recent emails for subscription receipts. What am I paying for monthly?",
        category="save",
        complexity="easy",
        demo_ready=True  # Works with email access
    ),

    # === AUTOMATE CATEGORY ===
    ShowcaseAgent(
        id="signup-agent",
        name="Signup Agent",
        icon="🤖",
        tagline="Claim new user bonuses automatically",
        description="Signs up for services, extracts 2FA codes from email, and claims new user promotions.",
        initial_prompt="Sign me up for [service] and claim any new user bonus. Use my connected email for verification.",
        category="automate",
        complexity="medium",
        demo_ready=True  # Works with email 2FA
    ),
    ShowcaseAgent(
        id="bill-payer",
        name="Bill Payer",
        icon="📄",
        tagline="Automate recurring payments",
        description="Set up scheduled payments for rent, utilities, or any recurring expense. Never miss a payment.",
        initial_prompt="Set up a monthly payment of $1000 to my landlord's wallet on the 1st of each month.",
        category="automate",
        complexity="easy",
        demo_ready=False  # Needs scheduler backend
    ),
    ShowcaseAgent(
        id="verification-assistant",
        name="Verification Assistant",
        icon="📧",
        tagline="Auto-complete 2FA flows",
        description="Reads verification codes from your email and completes 2FA authentication automatically.",
        initial_prompt="Get the latest verification code from my email.",
        category="automate",
        complexity="easy",
        demo_ready=True  # Works with email access
    ),
]


def get_showcase_agents(category: Optional[str] = None, demo_ready_only: bool = False) -> List[ShowcaseAgent]:
    """Get showcase agents, optionally filtered."""
    agents = SHOWCASE_AGENTS

    if category:
        agents = [a for a in agents if a.category == category]

    if demo_ready_only:
        agents = [a for a in agents if a.demo_ready]

    return agents


def get_agent_by_id(agent_id: str) -> Optional[ShowcaseAgent]:
    """Get a specific showcase agent by ID."""
    for agent in SHOWCASE_AGENTS:
        if agent.id == agent_id:
            return agent
    return None


def get_categories() -> List[Dict]:
    """Get agent categories with metadata."""
    return [
        {"id": "earn", "name": "Earn", "icon": "📈", "description": "Make money with your USDC"},
        {"id": "save", "name": "Save", "icon": "💰", "description": "Spend smarter, save more"},
        {"id": "automate", "name": "Automate", "icon": "🤖", "description": "AI handles the boring stuff"},
    ]


# === UI RENDERING ===

def render_showcase_grid(on_select_callback=None):
    """
    Render the showcase agents as a grid.
    Call from Streamlit context.
    """
    import streamlit as st
    from design_system import DS

    # Category tabs
    categories = get_categories()
    tabs = st.tabs([f"{c['icon']} {c['name']}" for c in categories])

    for tab_idx, category in enumerate(categories):
        with tabs[tab_idx]:
            agents = get_showcase_agents(category=category["id"])

            # Grid of agent cards
            cols = st.columns(2)
            for i, agent in enumerate(agents):
                with cols[i % 2]:
                    _render_agent_card(agent, on_select_callback)


def _render_agent_card(agent: ShowcaseAgent, on_select_callback=None):
    """Render a single agent card."""
    import streamlit as st
    from design_system import DS

    # Card styling
    opacity = "1" if agent.demo_ready else "0.5"
    cursor = "pointer" if agent.demo_ready else "not-allowed"
    badge = "" if agent.demo_ready else '<span style="font-size: 9px; color: #eab308; background: rgba(234,179,8,0.15); padding: 2px 6px; border-radius: 4px; margin-left: 8px;">SOON</span>'

    st.markdown(f"""
    <div style="
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        opacity: {opacity};
        cursor: {cursor};
        transition: all 0.2s ease;
    " class="hoverable">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
            <span style="font-size: 24px;">{agent.icon}</span>
            <div>
                <div style="font-family: {DS.typography.FONT_SANS}; font-size: 14px; color: {DS.colors.TEXT_PRIMARY}; font-weight: 500;">
                    {agent.name}{badge}
                </div>
                <div style="font-family: {DS.typography.FONT_MONO}; font-size: 11px; color: {DS.colors.TEXT_MUTED};">
                    {agent.tagline}
                </div>
            </div>
        </div>
        <div style="font-family: {DS.typography.FONT_SANS}; font-size: 12px; color: {DS.colors.TEXT_SECONDARY}; line-height: 1.5;">
            {agent.description}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if agent.demo_ready:
        if st.button(f"Try {agent.name}", key=f"agent_{agent.id}", use_container_width=True):
            if on_select_callback:
                on_select_callback(agent)
            else:
                # Default: add prompt to chat
                st.session_state.messages.append({"role": "user", "content": agent.initial_prompt})
                st.session_state._quick_action_triggered = True
                st.rerun()
