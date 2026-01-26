"""
Chat Interface Component
V12 Design: "Liquid Silver" - Floating Void Aesthetic
"""

import streamlit as st
from chain_utils import ChainUtils


# --- VISUAL: FLOATING DATA ---
def render_fashion_card(label, value, tag=None):
    """Minimalist data point floating in space."""
    st.markdown(f"""
    <div style="padding: 12px 0;">
        <div style="font-family: 'JetBrains Mono'; font-size: 10px; color: #444; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.1em;">{label}</div>
        <div style="font-family: 'Inter'; font-size: 18px; font-weight: 400; color: white; letter-spacing: -0.02em;">
            {value} {f'<span style="font-size: 12px; color: #444; margin-left: 4px;">{tag}</span>' if tag else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)


# --- HEADER: MAGAZINE ---
def render_header():
    """Magazine-style minimal header."""
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("""
        <div style="margin-top: 30px;">
            <h1 style="font-size: 28px; margin: 0; font-weight: 300; letter-spacing: -0.04em;">CHAT02</h1>
            <p style="font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 300; color: #666; margin: 8px 0 0 0; letter-spacing: -0.01em;">
                Fuel your AI chats with real money. Go from 0 to something with USDC.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div style="text-align: right; margin-top: 40px;">
            <span style="font-family: 'JetBrains Mono'; font-size: 10px; color: #fff; background: rgba(255,255,255,0.1); padding: 4px 10px; border-radius: 10px;">ONLINE</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)


# --- THE PULSE DECK ---
def render_pulse_deck():
    """
    Hybrid action + reward strip. V12 Liquid Silver aesthetic.
    Priority: Urgent Task → Scheduled → Perks
    """

    # === GLASS WHITE / SILVER PALETTE ===
    HOLO_WHITE = "#ffffff"
    SILVER_GLOW = "rgba(255,255,255,0.5)"
    GLASS_BG = "rgba(255,255,255,0.05)"
    MUTED = "#666"

    # === DATA SOURCES (mock - replace with real queries) ===
    # TODO: Pull from pending_approvals table
    active_tasks = []  # e.g., [{"type": "urgent", "label": "APPROVAL", "value": "Send $500", "action": "Sign"}]

    # TODO: Pull from scheduled_payments table
    scheduled = []  # e.g., [{"label": "TOMORROW", "value": "Netflix $15.99", "action": "View"}]

    # TODO: Pull from user spending + perks config
    perks = [
        {"brand": "Spotify", "progress": 75, "target": 100, "reward": "1 Mo Free"},
        {"brand": "Pro", "progress": 2, "target": 5, "reward": "Unlock"},
    ]

    # === SLOT BUILDER ===
    slots = []

    # Slot 1: Priority (Urgent > Scheduled > Stat fallback)
    if active_tasks:
        t = active_tasks[0]
        slots.append({
            "mode": "task",
            "urgent": t["type"] == "urgent",
            "title": t["label"],
            "main": t["value"],
            "cta": t["action"]
        })
    elif scheduled:
        s = scheduled[0]
        slots.append({
            "mode": "scheduled",
            "title": s["label"],
            "main": s["value"],
            "cta": s["action"]
        })
    else:
        # Fallback: spending stat
        slots.append({
            "mode": "stat",
            "title": "THIS MONTH",
            "main": "$0.00",
            "sub": "spent"
        })

    # Slots 2-3: Perks
    for p in perks[:2]:
        pct = int((p["progress"] / p["target"]) * 100)
        slots.append({
            "mode": "perk",
            "title": p["brand"].upper(),
            "main": f"{p['progress']}/{p['target']}",
            "reward": p["reward"],
            "pct": pct,
            "complete": pct >= 100
        })

    # === RENDER ===
    cols = st.columns(len(slots))

    for i, slot in enumerate(slots):
        with cols[i]:
            _render_pulse_card(slot, HOLO_WHITE, SILVER_GLOW, GLASS_BG, MUTED)


def _render_pulse_card(slot: dict, accent: str, glow: str, glass_bg: str, muted: str):
    """Render individual pulse card based on mode."""

    mode = slot["mode"]
    is_urgent = slot.get("urgent", False)
    is_complete = slot.get("complete", False)

    # Dynamic styling - Glass White for active states
    if mode == "task" and is_urgent:
        border = f"1px solid rgba(255,255,255,0.2)"
        bg = glass_bg
        title_color = accent
    elif is_complete:
        border = f"1px solid rgba(255,255,255,0.3)"
        bg = "rgba(255,255,255,0.08)"
        title_color = accent
    else:
        border = "1px solid rgba(255,255,255,0.06)"
        bg = "rgba(255,255,255,0.02)"
        title_color = muted

    # Build card HTML
    if mode == "perk":
        # Perk card with progress bar
        reward_badge = f'''
            <span style="font-family: Inter; font-size: 9px; background: {'rgba(255,255,255,0.9)' if is_complete else 'rgba(255,255,255,0.1)'};
                         color: {'#000' if is_complete else '#888'}; padding: 2px 6px; border-radius: 4px; font-weight: 500;">
                {'CLAIM' if is_complete else slot['reward']}
            </span>
        '''
        # Silver glow progress bar
        progress_bar = f'''
            <div style="width: 100%; height: 2px; background: rgba(255,255,255,0.08); margin-top: 10px; border-radius: 2px; overflow: hidden;">
                <div style="width: {slot['pct']}%; height: 100%; background: rgba(255,255,255,0.6); border-radius: 2px;
                            {'box-shadow: 0 0 10px ' + glow + ', 0 0 20px rgba(255,255,255,0.2);' if slot['pct'] > 50 else ''}"></div>
            </div>
        '''
        bottom_section = progress_bar

    elif mode == "task":
        reward_badge = ""
        bottom_section = f'''
            <div style="font-family: JetBrains Mono; font-size: 10px; color: {accent}; text-align: right; margin-top: 6px; opacity: 0.8;">
                {slot['cta']} →
            </div>
        '''

    elif mode == "scheduled":
        reward_badge = ""
        bottom_section = f'''
            <div style="font-family: JetBrains Mono; font-size: 10px; color: {muted}; text-align: right; margin-top: 6px;">
                {slot['cta']} →
            </div>
        '''

    else:  # stat
        reward_badge = ""
        bottom_section = f'''
            <div style="font-family: JetBrains Mono; font-size: 10px; color: {muted}; margin-top: 6px;">
                {slot.get('sub', '')}
            </div>
        '''

    st.markdown(f"""
    <div style="
        border: {border};
        background: {bg};
        border-radius: 12px;
        padding: 14px;
        height: 88px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    ">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <span style="font-family: JetBrains Mono; font-size: 9px; color: {title_color}; letter-spacing: 0.05em;">
                {slot['title']}
            </span>
            {reward_badge}
        </div>

        <div style="font-family: Inter; font-size: 15px; font-weight: 500; color: white;
                    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            {slot['main']}
        </div>

        {bottom_section}
    </div>
    """, unsafe_allow_html=True)


# Legacy alias for compatibility
def render_action_deck():
    """Deprecated: Use render_pulse_deck instead."""
    render_pulse_deck()


# --- MODULES: FULL CAPABILITY LIBRARY ---
def render_modules():
    """
    Render full capability library with all categories.
    """
    st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)

    # Full categories with (label, prompt, is_live)
    categories = {
        "Send & Pay": [
            ("Send USDC", "Help me send USDC to someone", True),
            ("Pay Bills", "Help me pay a bill with crypto", True),
            ("Phone Top-up", "I need to add minutes to my phone", True),
            ("Schedule", "I want to set up a recurring payment", True),
        ],
        "Earn": [
            ("Earn Yield", "Lend idle USDC on Aave, earn ~4% APY", False),
            ("Swap to ETH", "Swap USDC to ETH at best rates", False),
            ("Stack Sats", "Buy Bitcoin directly, no exchange needed", False),
        ],
        "Tools": [
            ("Get Domain", "I want to register a domain", True),
            ("VPN", "I want a Mullvad VPN subscription", True),
            ("eSIM", "I need an international eSIM", False),
            ("Alerts", "Set up balance alerts and spending notifications", False),
        ],
        "Shopping": [
            ("Amazon", "I want to buy an Amazon gift card", True),
            ("Target", "Show me Target gift cards", True),
            ("Walmart", "I want a Walmart gift card", True),
            ("Best Buy", "Show me Best Buy gift cards", True),
            ("Sephora", "Get a Sephora gift card", True),
        ],
        "Food": [
            ("DoorDash", "I want a DoorDash gift card", True),
            ("Uber Eats", "I want Uber Eats gift card credits", True),
            ("Starbucks", "Get me a Starbucks gift card", True),
            ("Chipotle", "I want a Chipotle gift card", True),
            ("Grubhub", "Show me Grubhub gift cards", True),
        ],
        "Streaming": [
            ("Netflix", "I want a Netflix gift card", True),
            ("Spotify", "Get me a Spotify gift card", True),
            ("Disney+", "I want a Disney+ gift card", False),
            ("Hulu", "Show me Hulu gift cards", False),
            ("Apple TV+", "I want an Apple TV+ subscription", False),
        ],
        "Gaming": [
            ("PlayStation", "Show me PlayStation gift cards", True),
            ("Xbox", "I want an Xbox gift card", True),
            ("Steam", "Get me a Steam gift card", True),
            ("Nintendo", "I want a Nintendo eShop card", True),
            ("Roblox", "Show me Roblox gift cards", True),
        ],
    }

    tabs = st.tabs(list(categories.keys()))

    for tab_idx, (category_name, items) in enumerate(categories.items()):
        with tabs[tab_idx]:
            cols = st.columns(min(len(items), 4))
            for i, (label, prompt, is_live) in enumerate(items):
                col_idx = i % 4
                with cols[col_idx]:
                    if is_live:
                        if st.button(label, key=f"mod_{tab_idx}_{i}", use_container_width=True):
                            st.session_state.messages.append({"role": "user", "content": prompt})
                            st.session_state._quick_action_triggered = True
                            st.rerun()
                    else:
                        st.button(label, key=f"mod_{tab_idx}_{i}", disabled=True,
                                  use_container_width=True, help=prompt)


def render_modules_preview():
    """
    Render capability preview for pre-login users (all disabled).
    """
    categories = {
        "Send & Pay": ["Send USDC", "Pay Bills", "Phone Top-up", "Schedule"],
        "Earn": ["Earn Yield", "Swap to ETH", "Stack Sats"],
        "Tools": ["Get Domain", "VPN", "eSIM", "Alerts"],
        "Shopping": ["Amazon", "Target", "Walmart", "Best Buy", "Sephora"],
        "Food": ["DoorDash", "Uber Eats", "Starbucks", "Chipotle", "Grubhub"],
        "Streaming": ["Netflix", "Spotify", "Disney+", "Hulu", "Apple TV+"],
        "Gaming": ["PlayStation", "Xbox", "Steam", "Nintendo", "Roblox"],
    }

    tabs = st.tabs(list(categories.keys()))

    for tab_idx, (category_name, items) in enumerate(categories.items()):
        with tabs[tab_idx]:
            cols = st.columns(min(len(items), 4))
            for i, label in enumerate(items):
                col_idx = i % 4
                with cols[col_idx]:
                    st.button(label, key=f"prev_{tab_idx}_{i}", disabled=True,
                              use_container_width=True, help="Sign up to use")


# --- MAIN INTERFACE ---
def chat_interface(create_agent_func):
    """Main chat interface with V12 liquid silver styling."""
    # 1. HEADER
    render_header()

    # 2. HANDLE PRE-LOGIN STATE
    if not st.session_state.wallet_address:
        st.markdown("""
        <div style="
            border-bottom: 1px solid rgba(255,255,255,0.08);
            padding: 60px 0;
            margin: 20px 0;
            text-align: center;
        ">
            <div style="font-family: 'Inter'; font-weight: 300; color: white; font-size: 20px; letter-spacing: -0.02em;">Authentication Required</div>
            <div style="color: #444; font-size: 12px; margin-top: 12px; font-family: 'JetBrains Mono'; letter-spacing: 0.05em;">INITIALIZE SESSION TO PROCEED</div>
        </div>
        """, unsafe_allow_html=True)
        render_modules_preview()
        st.chat_input("Waiting...", disabled=True, key="preview_input")
        return

    # 3. HANDLE LOCKED STATE
    if st.session_state.get("wallet_locked", False) and st.session_state.get("wallet_encrypted"):
        st.markdown("""
        <div style="color: #666; font-size: 14px; padding: 20px 0;">Session locked. Unlock in sidebar to continue.</div>
        """, unsafe_allow_html=True)
        st.chat_input("Locked", disabled=True, key="locked_input")
        return

    # 4. ONBOARDING & API CHECKS
    from onboarding import show_onboarding
    if not show_onboarding():
        return

    from api_key_setup import show_api_key_banner
    from settings_manager import SettingsManager
    from free_tier import FreeTier

    user_id = st.session_state.get("user_id")
    llm_config = SettingsManager.get_llm_config(user_id)
    has_api_key = bool(llm_config.get("api_key"))

    if not has_api_key:
        if FreeTier.is_available() and not FreeTier.has_quota(user_id):
            FreeTier.show_upgrade_prompt()
        else:
            show_api_key_banner()
        return

    # Force agent re-initialization if API key was just configured
    if has_api_key and st.session_state.get("_api_key_just_saved"):
        st.session_state.agent = None
        st.session_state._agent_initializing = False
        st.session_state._api_key_just_saved = False
        cache_key = f"_llm_config_{user_id}"
        if cache_key in st.session_state:
            del st.session_state[cache_key]

    # 5. PULSE DECK
    render_pulse_deck()

    # 6. CHAT SECTION - Hairline divider
    st.markdown("<div style='height: 40px; border-bottom: 1px solid rgba(255,255,255,0.05);'></div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Welcome state (if no messages yet)
    if not st.session_state.messages:
        wallet_short = ChainUtils.format_address(st.session_state.wallet_address) if st.session_state.wallet_address else "..."
        # Floating data points
        c1, c2, c3 = st.columns(3)
        with c1:
            render_fashion_card("Wallet", wallet_short)
        with c2:
            render_fashion_card("Network", "Arc")
        with c3:
            render_fashion_card("Status", "Active", "●")

        st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
        # Show modules when no messages
        render_modules()

    # Render chat history - pure text, minimal
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                # AI: Light gray, thin weight
                st.markdown(f"<div style='color: #ccc; font-family: Inter; font-weight: 300; font-size: 15px; line-height: 1.7;'>{msg['content']}</div>", unsafe_allow_html=True)
            else:
                # User: White, clean
                st.markdown(f"<div style='color: white; font-family: Inter; font-size: 15px; line-height: 1.6;'>{msg['content']}</div>", unsafe_allow_html=True)

    # 7. HANDLE INPUT LOGIC
    prompt = None
    if st.session_state.get("_quick_action_triggered"):
        st.session_state._quick_action_triggered = False
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            prompt = st.session_state.messages[-1]["content"]

    # 8. INPUT FIELD
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    if not prompt:
        prompt = st.chat_input("Input command...")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(f"<div style='color: white; font-family: Inter; font-size: 15px;'>{prompt}</div>", unsafe_allow_html=True)

    # 9. PROCESS MESSAGE
    if prompt:
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                message_success = False
                try:
                    # Agent initialization logic
                    if not st.session_state.get("agent"):
                        try:
                            agent = create_agent_func()
                            if agent:
                                st.session_state.agent = agent
                        except Exception:
                            pass

                    if not st.session_state.get("agent"):
                        # Handle missing agent
                        from api_key_setup import check_api_key_status
                        has_key, provider = check_api_key_status()
                        if not has_key:
                            response = "**System Offline:** API Key required in Settings."
                        else:
                            response = "**Initializing:** Please wait..."
                    else:
                        # Process with LangChain
                        from langchain_core.messages import HumanMessage, AIMessage
                        history = []
                        for m in st.session_state.messages[:-1]:
                            if m["role"] == "user":
                                history.append(HumanMessage(content=m["content"]))
                            else:
                                history.append(AIMessage(content=m["content"]))

                        result = st.session_state.agent.invoke({
                            "input": prompt,
                            "chat_history": history
                        })
                        response = result.get("output", "Error processing request.")
                        message_success = True

                except Exception as e:
                    response = f"**System Error:** {str(e)}"

                st.markdown(f"<div style='color: #ccc; font-family: Inter; font-weight: 300; font-size: 15px; line-height: 1.7;'>{response}</div>", unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": response})

                if message_success and llm_config.get("using_free_tier"):
                    FreeTier.increment_usage(user_id)
