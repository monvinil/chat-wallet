"""
Chat Interface Component
V6 Design: "Obsidian Standard"
Linear/Stripe fintech aesthetic with minimal, professional styling.
"""

import streamlit as st
from chain_utils import ChainUtils


# --- VISUAL COMPONENT: HUD HEADER ---
def render_hud_header():
    """
    Renders the 'Dynamic Island' style status header.
    Moves the 'Status' logic to a visual indicator in the top right.
    """
    # Layout: Title on Left, Status Pill on Right
    c1, c2 = st.columns([3, 1])

    with c1:
        st.markdown("""
            <div style="margin-top: -10px;">
                <h1 style="font-size: 24px; font-weight: 600; margin-bottom: 0; letter-spacing: -0.02em; color: #EDEDEF;">Chat Wallet</h1>
                <div style="font-family: 'Inter', sans-serif; font-size: 11px; color: #5C6370; letter-spacing: 0;">
                    AI-powered • Non-custodial
                </div>
            </div>
        """, unsafe_allow_html=True)

    with c2:
        # The "System Status" Pill
        # Visual check for connection
        is_connected = bool(st.session_state.wallet_address)
        status_color = "#3ECF8E" if is_connected else "#EF4444"  # Green or Red
        status_text = "Online" if is_connected else "Offline"

        st.markdown(f"""
        <div style="
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 8px;
            padding: 8px 0px;
        ">
            <span style="font-family: 'Inter', sans-serif; font-size: 11px; color: {status_color}; letter-spacing: 0;">
                {status_text}
            </span>
            <div style="width: 6px; height: 6px; background: {status_color}; border-radius: 50%;"></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")


# --- VISUAL COMPONENT: QUICK ACTION DECK ---
def render_quick_actions():
    """
    Render quick actions as a grid of action tiles.
    """
    st.markdown("<div style='font-family: \"Inter\", sans-serif; font-size: 11px; font-weight: 500; color: #5C6370; margin-bottom: 10px;'>Quick Actions</div>", unsafe_allow_html=True)

    # Using 4 columns for a tighter, more professional grid look
    # These rely on the CSS injected in App.py to look like "Glass Tiles"
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Primary Action - Deposit (Highlighted via type="primary")
        if st.button("↓ DEPOSIT", key="quick_deposit", type="primary", use_container_width=True):
            st.session_state.show_deposit_modal = True
            st.rerun()

    with col2:
        if st.button("↗ SEND", key="quick_send", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "I want to send money"})
            st.session_state._quick_action_triggered = True
            st.rerun()

    with col3:
        if st.button("🎁 PERKS", key="quick_giftcard", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Show me gift cards"})
            st.session_state._quick_action_triggered = True
            st.rerun()

    with col4:
        if st.button("⚡ BILLS", key="quick_bill", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Help me pay a bill"})
            st.session_state._quick_action_triggered = True
            st.rerun()


# --- VISUAL COMPONENT: SUGGESTED MODULES ---
def render_suggested_actions():
    """
    Render capability library with thematic tabs.
    """
    st.markdown("<div style='margin-top: 24px; font-family: \"Inter\", sans-serif; font-size: 11px; font-weight: 500; color: #5C6370; margin-bottom: 10px;'>Modules</div>", unsafe_allow_html=True)

    categories = {
        "FINANCE": [
            ("Send USDC", "Help me send USDC to someone", True),
            ("Pay Bills", "Help me pay a bill with crypto", True),
            ("Phone Top-up", "I need to add minutes to my phone", True),
            ("Schedule", "I want to set up a recurring payment", True),
        ],
        "LIFESTYLE": [
            ("Amazon", "I want to buy an Amazon gift card", True),
            ("Uber", "I want Uber Eats gift card credits", True),
            ("Coffee", "Get me a Starbucks gift card", True),
            ("Streaming", "Get me a Spotify gift card", True),
        ],
        "TOOLS": [
            ("VPN", "I want a Mullvad VPN subscription", True),
            ("Domain", "I want to register a domain", True),
            ("Alerts", "Set up balance alerts", False),
        ]
    }

    tabs = st.tabs(list(categories.keys()))

    for tab_idx, (category_name, items) in enumerate(categories.items()):
        with tabs[tab_idx]:
            # Auto-distribute grid
            cols = st.columns(min(len(items), 4))
            for i, (label, prompt, is_live) in enumerate(items):
                col_idx = i % 4
                with cols[col_idx]:
                    # These buttons will pick up the 'Glass Tile' CSS automatically
                    if st.button(label, key=f"cap_{tab_idx}_{i}", use_container_width=True, disabled=not is_live):
                        st.session_state.messages.append({"role": "user", "content": prompt})
                        st.session_state._quick_action_triggered = True
                        st.rerun()


def render_suggested_actions_preview():
    """
    Render capability preview for pre-login users.
    Same visual style, just disabled.
    """
    st.markdown("<div style='margin-top: 24px; font-family: \"Inter\", sans-serif; font-size: 11px; font-weight: 500; color: #5C6370; margin-bottom: 10px;'>Preview</div>", unsafe_allow_html=True)

    categories = {
        "FINANCE": ["Send USDC", "Pay Bills", "Schedule"],
        "LIFESTYLE": ["Amazon", "Uber", "Coffee"],
        "TOOLS": ["VPN", "Domain", "Alerts"]
    }

    tabs = st.tabs(list(categories.keys()))

    for tab_idx, (category_name, items) in enumerate(categories.items()):
        with tabs[tab_idx]:
            cols = st.columns(len(items))
            for i, label in enumerate(items):
                with cols[i]:
                    st.button(label, key=f"preview_{tab_idx}_{i}", disabled=True, use_container_width=True)


# --- MAIN INTERFACE ---
def chat_interface(create_agent_func):
    """
    Main chat interface
    """
    # 1. RENDER HUD (New Location: Always top, pinned feeling)
    render_hud_header()

    # 2. HANDLE PRE-LOGIN STATE
    if not st.session_state.wallet_address:
        st.markdown("""
        <div style="
            background: #121315;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            text-align: center;
        ">
            <div style="font-family: 'Inter', sans-serif; color: #EDEDEF; font-size: 16px; font-weight: 500; margin-bottom: 8px;">Your money, your words.</div>
            <div style="color: #8A8F98; font-size: 13px; line-height: 1.6;">
                AI-powered wallet that turns conversation into action.<br>
                Sign in to get started.
            </div>
        </div>
        """, unsafe_allow_html=True)

        render_suggested_actions_preview()
        st.chat_input("Initialize session...", disabled=True, key="preview_input")
        return

    # 3. HANDLE LOCKED STATE
    if st.session_state.get("wallet_locked", False) and st.session_state.get("wallet_encrypted"):
        st.warning("SESSION LOCKED")
        st.caption("Please unlock your keystore in the sidebar to continue.")
        st.chat_input("Locked...", disabled=True, key="locked_input")
        return

    # 4. ONBOARDING & API CHECKS (Keep existing logic)
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

    # 5. RENDER QUICK ACTIONS (Below HUD)
    render_quick_actions()

    # 6. RENDER MODULES (Grouped with quick actions as "Command Palette")
    render_suggested_actions()

    # 7. CHAT SECTION
    st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)

    # Welcome state (if no messages yet)
    if not st.session_state.messages:
        wallet_short = ChainUtils.format_address(st.session_state.wallet_address) if st.session_state.wallet_address else "..."
        st.markdown(f"""
        <div style="
            background: #121315;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0 20px 0;
            font-family: 'Inter', sans-serif;
        ">
            <div style="color: #5C6370; font-size: 11px; font-weight: 500; margin-bottom: 8px;">Session Active</div>
            <div style="color: #EDEDEF; font-size: 13px;">Connected: <span style="color: #5E6AD2;">{wallet_short}</span></div>
            <div style="margin-top: 16px; display: flex; gap: 8px; flex-wrap: wrap;">
                <span style="background: rgba(62, 207, 142, 0.1); color: #3ECF8E; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 500;">Ready</span>
                <span style="background: rgba(255,255,255,0.05); color: #8A8F98; padding: 4px 8px; border-radius: 4px; font-size: 11px;">Base Sepolia</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Render chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 8. HANDLE INPUT LOGIC
    prompt = None
    if st.session_state.get("_quick_action_triggered"):
        st.session_state._quick_action_triggered = False
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            prompt = st.session_state.messages[-1]["content"]

    # 9. INPUT FIELD
    if not prompt:
        prompt = st.chat_input("Enter command...")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

    # 10. PROCESS MESSAGE
    if prompt:
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                message_success = False
                try:
                    # Agent initialization logic...
                    if not st.session_state.get("agent"):
                        try:
                            agent = create_agent_func()
                            if agent:
                                st.session_state.agent = agent
                        except Exception:
                            pass

                    if not st.session_state.get("agent"):
                        # Handle missing agent...
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

                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

                if message_success and llm_config.get("using_free_tier"):
                    FreeTier.increment_usage(user_id)
