"""
Chat Interface Component
V7 Design: "The Construct"
Industrial high-fidelity aesthetic with terminal-like precision.
"""

import streamlit as st
from chain_utils import ChainUtils


# --- HELPER: INDUSTRIAL CARD ---
def render_industrial_card(title, value, subtext=None, accent=False):
    """
    Renders a card that looks like a machine part / label.
    """
    border_color = "#bef264" if accent else "rgba(255,255,255,0.08)"
    bg_color = "rgba(190, 242, 100, 0.05)" if accent else "#18181b"
    text_color = "#bef264" if accent else "#f4f4f5"

    st.markdown(f"""
    <div style="
        background: {bg_color};
        border: 1px solid {border_color};
        border-radius: 4px;
        padding: 16px;
        height: 100%;
        transition: all 0.2s;
        position: relative;
    ">
        <div style="position: absolute; top: 6px; right: 6px; width: 4px; height: 4px; border-radius: 50%; background: #3f3f46;"></div>

        <div style="font-family: 'JetBrains Mono'; font-size: 10px; color: #71717a; text-transform: uppercase; margin-bottom: 8px;">{title}</div>
        <div style="font-family: 'Inter'; font-size: 18px; font-weight: 600; color: {text_color}; letter-spacing: -0.02em;">{value}</div>
        {f'<div style="font-size: 11px; color: #a1a1aa; margin-top: 4px; font-family: JetBrains Mono;">{subtext}</div>' if subtext else ''}
    </div>
    """, unsafe_allow_html=True)


# --- HEADER: SYSTEM STATUS ---
def render_header():
    """
    A technical header with system diagnostics.
    """
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown("""
        <div style="margin-top: -10px;">
            <div style="font-family: 'JetBrains Mono'; font-size: 10px; color: #bef264; margin-bottom: 4px;">/// SECURE CHANNEL ESTABLISHED</div>
            <h1 style="font-size: 24px; font-weight: 600; margin: 0; letter-spacing: -0.02em;">Command Center</h1>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        # Tech indicator
        st.markdown("""
        <div style="display: flex; justify-content: flex-end; align-items: center; height: 100%;">
            <div style="padding: 4px 8px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; font-family: 'JetBrains Mono'; font-size: 10px; color: #71717a;">
                V7.0.1
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("---")


# --- QUICK ACTIONS: CONTROL DECK ---
def render_action_deck():
    """
    Render quick actions as industrial operation buttons.
    """
    st.markdown("<div style='font-family: \"JetBrains Mono\"; font-size: 10px; color: #52525b; margin-bottom: 10px;'>OPERATIONS</div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("↓ INTAKE", key="dock_deposit", type="primary", use_container_width=True):
            st.session_state.show_deposit_modal = True
            st.rerun()

    with col2:
        if st.button("↗ TRANSFER", key="dock_send", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "I want to send money"})
            st.session_state._quick_action_triggered = True
            st.rerun()

    with col3:
        if st.button("🎁 ACQUIRE", key="dock_card", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Show me gift cards"})
            st.session_state._quick_action_triggered = True
            st.rerun()

    with col4:
        if st.button("⚡ SETTLE", key="dock_bill", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Help me pay a bill"})
            st.session_state._quick_action_triggered = True
            st.rerun()


# --- MODULES: TECHNICAL SPECS ---
def render_modules():
    """
    Render capability modules with industrial card styling.
    """
    st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)

    tabs = st.tabs(["ASSETS", "LIFESTYLE", "SECURITY"])

    with tabs[0]:  # Assets
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Send USDC", key="mod_send", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "Help me send USDC to someone"})
                st.session_state._quick_action_triggered = True
                st.rerun()
        with c2:
            if st.button("Schedule", key="mod_schedule", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "I want to set up a recurring payment"})
                st.session_state._quick_action_triggered = True
                st.rerun()
        with c3:
            if st.button("Pay Bills", key="mod_bills", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "Help me pay a bill with crypto"})
                st.session_state._quick_action_triggered = True
                st.rerun()

    with tabs[1]:  # Lifestyle
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Amazon", key="mod_amazon", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "I want to buy an Amazon gift card"})
                st.session_state._quick_action_triggered = True
                st.rerun()
        with c2:
            if st.button("Uber", key="mod_uber", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "I want Uber Eats gift card credits"})
                st.session_state._quick_action_triggered = True
                st.rerun()
        with c3:
            if st.button("Starbucks", key="mod_starbucks", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "Get me a Starbucks gift card"})
                st.session_state._quick_action_triggered = True
                st.rerun()

    with tabs[2]:  # Security
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("VPN", key="mod_vpn", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "I want a Mullvad VPN subscription"})
                st.session_state._quick_action_triggered = True
                st.rerun()
        with c2:
            if st.button("Domain", key="mod_domain", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "I want to register a domain"})
                st.session_state._quick_action_triggered = True
                st.rerun()
        with c3:
            st.button("Alerts", key="mod_alerts", use_container_width=True, disabled=True)


def render_modules_preview():
    """
    Render capability preview for pre-login users (disabled).
    """
    tabs = st.tabs(["ASSETS", "LIFESTYLE", "SECURITY"])

    with tabs[0]:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.button("Send USDC", key="prev_send", disabled=True, use_container_width=True)
        with c2:
            st.button("Schedule", key="prev_schedule", disabled=True, use_container_width=True)
        with c3:
            st.button("Pay Bills", key="prev_bills", disabled=True, use_container_width=True)

    with tabs[1]:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.button("Amazon", key="prev_amazon", disabled=True, use_container_width=True)
        with c2:
            st.button("Uber", key="prev_uber", disabled=True, use_container_width=True)
        with c3:
            st.button("Starbucks", key="prev_starbucks", disabled=True, use_container_width=True)

    with tabs[2]:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.button("VPN", key="prev_vpn", disabled=True, use_container_width=True)
        with c2:
            st.button("Domain", key="prev_domain", disabled=True, use_container_width=True)
        with c3:
            st.button("Alerts", key="prev_alerts", disabled=True, use_container_width=True)


# --- MAIN INTERFACE ---
def chat_interface(create_agent_func):
    """
    Main chat interface with V7 industrial styling.
    """
    # 1. HEADER
    render_header()

    # 2. HANDLE PRE-LOGIN STATE
    if not st.session_state.wallet_address:
        st.markdown("""
        <div style="background: #121212; border: 1px dashed #3f3f46; border-radius: 4px; padding: 30px; text-align: center; margin-bottom: 20px;">
            <div style="font-family: 'JetBrains Mono'; font-size: 12px; color: #bef264; margin-bottom: 10px;">SYSTEM STANDBY</div>
            <div style="color: #a1a1aa; font-size: 14px;">Awaiting user authentication to initialize neural wallet agent.</div>
        </div>
        """, unsafe_allow_html=True)
        render_modules_preview()
        st.chat_input("AUTHENTICATE TO PROCEED...", disabled=True, key="preview_input")
        return

    # 3. HANDLE LOCKED STATE
    if st.session_state.get("wallet_locked", False) and st.session_state.get("wallet_encrypted"):
        st.warning("ENCRYPTION ACTIVE")
        st.caption("Unlock keystore in sidebar to continue.")
        st.chat_input("LOCKED", disabled=True, key="locked_input")
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

    # 5. OPERATIONS DECK
    render_action_deck()

    # 6. CHAT SECTION
    st.markdown("<div style='margin-top: 20px; border-top: 1px solid rgba(255,255,255,0.05);'></div>", unsafe_allow_html=True)

    # Welcome state (if no messages yet)
    if not st.session_state.messages:
        wallet_short = ChainUtils.format_address(st.session_state.wallet_address) if st.session_state.wallet_address else "..."
        st.markdown(f"""
        <div style="margin-top: 20px; font-family: 'JetBrains Mono'; font-size: 11px; color: #52525b;">
            > CONNECTED: {wallet_short}<br>
            > NETWORK: BASE-SEPOLIA<br>
            > AGENT: READY<br>
            > WAITING FOR INPUT...<span style="animation: blink 1s infinite;">_</span>
        </div>
        """, unsafe_allow_html=True)
        # Show modules when no messages
        render_modules()

    # Render chat history with terminal styling
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                st.markdown(f"<div style='font-family: \"JetBrains Mono\"; font-size: 11px; color: #71717a; margin-bottom: 4px;'>OUTPUT //</div>", unsafe_allow_html=True)
                st.markdown(msg["content"])
            else:
                st.markdown(f"<div style='font-family: \"JetBrains Mono\"; font-size: 11px; color: #52525b; margin-bottom: 4px;'>INPUT //</div>", unsafe_allow_html=True)
                st.markdown(f"<span style='color: #bef264;'>{msg['content']}</span>", unsafe_allow_html=True)

    # 7. HANDLE INPUT LOGIC
    prompt = None
    if st.session_state.get("_quick_action_triggered"):
        st.session_state._quick_action_triggered = False
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            prompt = st.session_state.messages[-1]["content"]

    # 8. INPUT FIELD
    if not prompt:
        prompt = st.chat_input("ENTER COMMAND...")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(f"<div style='font-family: \"JetBrains Mono\"; font-size: 11px; color: #52525b; margin-bottom: 4px;'>INPUT //</div>", unsafe_allow_html=True)
                st.markdown(f"<span style='color: #bef264;'>{prompt}</span>", unsafe_allow_html=True)

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

                st.markdown(f"<div style='font-family: \"JetBrains Mono\"; font-size: 11px; color: #71717a; margin-bottom: 4px;'>OUTPUT //</div>", unsafe_allow_html=True)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

                if message_success and llm_config.get("using_free_tier"):
                    FreeTier.increment_usage(user_id)
