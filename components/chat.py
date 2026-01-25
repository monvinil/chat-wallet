"""
Chat Interface Component
V8 Design: "The Drop" (Fashion/Tech)
High-end streetwear aesthetic with volt accents.
"""

import streamlit as st
from chain_utils import ChainUtils


# --- HELPER: FASHION-TECH CARD ---
def render_fashion_card(label, value, tag=None):
    """
    Renders a card that looks like a product spec sheet.
    """
    st.markdown(f"""
    <div style="
        background: #0A0A0A;
        border: 1px solid #1F1F1F;
        border-radius: 4px;
        padding: 20px;
        height: 100%;
        position: relative;
        transition: border 0.2s;
    ">
        <div style="font-family: 'JetBrains Mono'; font-size: 9px; color: #525252; margin-bottom: 8px; letter-spacing: 0.1em;">{label.upper()}</div>
        <div style="font-family: 'Inter'; font-size: 16px; font-weight: 600; color: white; letter-spacing: -0.02em;">{value}</div>
        {f'<div style="position: absolute; top: 10px; right: 10px; background: #1F1F1F; color: #999; font-size: 9px; padding: 2px 6px; border-radius: 2px; font-family: JetBrains Mono;">{tag}</div>' if tag else ''}
    </div>
    """, unsafe_allow_html=True)


# --- HEADER: THE "BRAND" HEADER ---
def render_header():
    """
    Big, bold, unapologetic branding.
    """
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("""
        <div style="margin-top: 10px;">
            <h1 style="font-size: 40px; line-height: 0.9; margin: 0; letter-spacing: -0.05em; font-weight: 800;">
                CHAT<br><span style="color: #333;">WALLET</span>
            </h1>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div style="text-align: right; font-family: 'JetBrains Mono'; font-size: 10px; color: #525252; margin-top: 10px;">
            BUILD_V8.0<br>
            SECURE_ENCLAVE<br>
            <span style="color: #ccff00;">● SYSTEM_READY</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)


# --- CALLBACKS FOR ACTION BUTTONS ---
def _on_deposit_click():
    st.session_state.show_deposit_modal = True


def _on_quick_action(prompt: str):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state._quick_action_triggered = True


# --- ACTIONS: THE CONTROL STRIP ---
def render_action_deck():
    """
    A single row of high-contrast buttons.
    Uses on_click callbacks to avoid double-render from explicit st.rerun().
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.button("DEPOSIT / IN", key="quick_deposit", type="primary",
                  use_container_width=True, on_click=_on_deposit_click)

    with col2:
        st.button("SEND / OUT", key="quick_send", use_container_width=True,
                  on_click=_on_quick_action, args=("I want to send money",))

    with col3:
        st.button("GIFT / BUY", key="quick_giftcard", use_container_width=True,
                  on_click=_on_quick_action, args=("Show me gift cards",))

    with col4:
        st.button("BILL / PAY", key="quick_bill", use_container_width=True,
                  on_click=_on_quick_action, args=("Help me pay a bill",))


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
                        st.button(label, key=f"mod_{tab_idx}_{i}", use_container_width=True,
                                  on_click=_on_quick_action, args=(prompt,))
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
    """
    Main chat interface with V8 streetwear styling.
    """
    # 1. HEADER
    render_header()

    # 2. HANDLE PRE-LOGIN STATE
    if not st.session_state.wallet_address:
        st.markdown("""
        <div style="
            border-top: 1px solid #333;
            border-bottom: 1px solid #333;
            padding: 40px 0;
            margin: 20px 0;
            text-align: center;
        ">
            <div style="font-family: 'Inter'; font-weight: 600; color: white; font-size: 18px; letter-spacing: -0.03em;">AUTHENTICATION REQUIRED</div>
            <div style="color: #525252; font-size: 12px; margin-top: 8px; font-family: 'JetBrains Mono';">PLEASE INITIALIZE SESSION TO PROCEED</div>
        </div>
        """, unsafe_allow_html=True)
        render_modules_preview()
        st.chat_input("WAITING...", disabled=True, key="preview_input")
        return

    # 3. HANDLE LOCKED STATE
    if st.session_state.get("wallet_locked", False) and st.session_state.get("wallet_encrypted"):
        st.warning("SESSION LOCKED")
        st.caption("Unlock in sidebar to continue.")
        st.chat_input("LOCKED", disabled=True, key="locked_input")
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

    # Show free tier status
    if llm_config.get("using_free_tier"):
        remaining = llm_config.get("remaining_messages", 0)
        if remaining <= 10:
            st.warning(f"{remaining} free messages left. Add your API key in Settings.")
        else:
            st.caption(f"{remaining} free messages remaining")

    # 5. ACTION STRIP
    render_action_deck()

    # 6. CHAT SECTION
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Welcome state (if no messages yet)
    if not st.session_state.messages:
        wallet_short = ChainUtils.format_address(st.session_state.wallet_address) if st.session_state.wallet_address else "..."
        st.markdown(f"""
        <div style="display: flex; gap: 30px; border-bottom: 1px solid #1A1A1A; padding-bottom: 20px; margin-bottom: 20px;">
            <div>
                <div style="font-family: 'JetBrains Mono'; font-size: 9px; color: #525252; letter-spacing: 0.1em;">ID</div>
                <div style="color: white; font-size: 12px; font-family: 'JetBrains Mono';">{wallet_short}</div>
            </div>
            <div>
                <div style="font-family: 'JetBrains Mono'; font-size: 9px; color: #525252; letter-spacing: 0.1em;">NET</div>
                <div style="color: white; font-size: 12px; font-family: 'JetBrains Mono';">BASE_MAIN</div>
            </div>
            <div>
                <div style="font-family: 'JetBrains Mono'; font-size: 9px; color: #525252; letter-spacing: 0.1em;">STATUS</div>
                <div style="color: #ccff00; font-size: 12px; font-family: 'JetBrains Mono';">ACTIVE</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        # Show modules when no messages
        render_modules()

    # Render chat history with editorial styling
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                # AI = Clean typography
                st.markdown(f"<div style='color: #F0F0F0; font-family: Inter; font-weight: 400; font-size: 15px; line-height: 1.6;'>{msg['content']}</div>", unsafe_allow_html=True)
            else:
                # User = Volt, uppercase, right-aligned feel
                st.markdown(f"<div style='color: #ccff00; font-family: JetBrains Mono; font-size: 13px; letter-spacing: 0.05em;'>{msg['content'].upper()}</div>", unsafe_allow_html=True)

    # 7. HANDLE INPUT LOGIC
    prompt = None
    if st.session_state.get("_quick_action_triggered"):
        st.session_state._quick_action_triggered = False
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            prompt = st.session_state.messages[-1]["content"]

    # 8. INPUT FIELD
    if not prompt:
        prompt = st.chat_input("TYPE COMMAND...")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(f"<div style='color: #ccff00; font-family: JetBrains Mono; font-size: 13px; letter-spacing: 0.05em;'>{prompt.upper()}</div>", unsafe_allow_html=True)

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

                st.markdown(f"<div style='color: #F0F0F0; font-family: Inter; font-weight: 400; font-size: 15px; line-height: 1.6;'>{response}</div>", unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": response})

                if message_success and llm_config.get("using_free_tier"):
                    FreeTier.increment_usage(user_id)
