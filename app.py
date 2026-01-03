"""
Chat-First Crypto Wallet MVP
"""

import os
import json
import streamlit as st
from typing import Optional
from datetime import datetime

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from cdp_langchain.agent_toolkits import CdpToolkit
from cdp_langchain.utils import CdpAgentkitWrapper

# ============================================================================
# CONFIG
# ============================================================================

NETWORK_ID = "base-sepolia"
SYSTEM_PROMPT = """You are a helpful crypto wallet assistant on Base Sepolia testnet. You can:
1. Check wallet balances (ETH, USDC)
2. Transfer assets to other addresses
3. Request testnet faucet funds
4. Swap between assets
5. Search and buy gift cards (simulated)
6. Read emails (simulated)

Always be clear about actions. Format results clearly.
Network: Base Sepolia (Testnet)
"""

# ============================================================================
# MOCK DATA
# ============================================================================

MOCK_GIFT_CARDS = [
    {"id": "gc_001", "name": "Amazon Gift Card", "price_usd": 10},
    {"id": "gc_002", "name": "Amazon Gift Card", "price_usd": 25},
    {"id": "gc_003", "name": "Uber Gift Card", "price_usd": 25},
    {"id": "gc_004", "name": "Spotify Premium", "price_usd": 10},
    {"id": "gc_005", "name": "Netflix Gift Card", "price_usd": 15},
    {"id": "gc_006", "name": "Steam Wallet", "price_usd": 20},
    {"id": "gc_007", "name": "DoorDash Credit", "price_usd": 25},
]

MOCK_EMAILS = [
    {"id": "1", "from": "billing@aws.amazon.com", "subject": "AWS Invoice December", "snippet": "Total: $127.43", "date": "2024-12-28"},
    {"id": "2", "from": "noreply@coinbase.com", "subject": "Deposit confirmed", "snippet": "0.5 ETH deposited", "date": "2024-12-27"},
    {"id": "3", "from": "support@bitrefill.com", "subject": "Gift card ready", "snippet": "Code: AXYZ-1234", "date": "2024-12-26"},
]

# ============================================================================
# TOOLS
# ============================================================================

@tool
def search_bitrefill(query: str) -> str:
    """Search for gift cards. Args: query - search term like 'amazon' or 'netflix'"""
    q = query.lower()
    results = [c for c in MOCK_GIFT_CARDS if q in c["name"].lower()] or MOCK_GIFT_CARDS[:3]
    return json.dumps({"status": "success", "results": results, "note": "[SIMULATED]"}, indent=2)

@tool
def buy_gift_card(product_id: str) -> str:
    """Buy a gift card. Args: product_id - e.g. 'gc_001'"""
    card = next((c for c in MOCK_GIFT_CARDS if c["id"] == product_id), None)
    if not card:
        return json.dumps({"status": "error", "message": "Product not found"})
    code = f"GIFT-{product_id.upper()}-{datetime.now().strftime('%H%M%S')}"
    if "purchases" not in st.session_state:
        st.session_state.purchases = []
    st.session_state.purchases.append({"product": card, "code": code})
    return json.dumps({"status": "success", "product": card["name"], "code": code, "note": "[SIMULATED]"}, indent=2)

@tool
def read_latest_emails(count: int = 3) -> str:
    """Read latest emails. Args: count - number of emails (max 10)"""
    return json.dumps({"status": "success", "emails": MOCK_EMAILS[:min(count, 10)], "note": "[SIMULATED]"}, indent=2)

@tool
def get_faucet_link() -> str:
    """Get Base Sepolia faucet links for free testnet ETH."""
    return json.dumps({
        "network": "Base Sepolia",
        "faucets": [
            {"name": "Coinbase Faucet", "url": "https://portal.cdp.coinbase.com/products/faucet"},
            {"name": "Alchemy Faucet", "url": "https://sepoliafaucet.com/"}
        ]
    }, indent=2)

# ============================================================================
# AGENT
# ============================================================================

def init_cdp_agent():
    if not os.getenv("CDP_API_KEY_NAME") or os.getenv("CDP_API_KEY_NAME") == "skip-for-now":
        return None, None
    try:
        cdp = CdpAgentkitWrapper(network_id=NETWORK_ID)
        toolkit = CdpToolkit.from_cdp_agentkit_wrapper(cdp)
        return cdp, toolkit.get_tools()
    except Exception as e:
        st.error(f"CDP init failed: {e}")
        return None, None

def create_agent():
    llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.3, max_tokens=4096)
    cdp, cdp_tools = init_cdp_agent()
    tools = [search_bitrefill, buy_gift_card, read_latest_emails, get_faucet_link] + (cdp_tools or [])
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True), cdp

# ============================================================================
# UI
# ============================================================================

def init_state():
    defaults = {"messages": [], "agent": None, "cdp": None, "gmail_connected": False, "purchases": [], "tool_outputs": []}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def sidebar():
    with st.sidebar:
        st.title("🔐 Wallet")
        st.markdown("**Network:** `Base Sepolia` 🧪")
        st.divider()
        if st.session_state.cdp:
            st.success("✅ Wallet Connected")
        else:
            st.warning("⚠️ CDP not configured (mock mode)")
        st.divider()
        st.subheader("📧 Email")
        if st.session_state.gmail_connected:
            st.success("Gmail Connected")
            if st.button("Disconnect"):
                st.session_state.gmail_connected = False
                st.rerun()
        else:
            if st.button("Connect Gmail", type="primary"):
                st.session_state.gmail_connected = True
                st.rerun()
        st.divider()
        if st.session_state.purchases:
            st.subheader("🎁 Purchases")
            for p in st.session_state.purchases[-3:]:
                st.code(f"{p['product']['name']}: {p['code']}")
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

def chat():
    st.title("💬 Chat-First Crypto Wallet")
    st.caption("Claude 3.5 Sonnet + Coinbase AgentKit")
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    if prompt := st.chat_input("Ask me anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    history = [HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"]) for m in st.session_state.messages[:-1]]
                    result = st.session_state.agent.invoke({"input": prompt, "chat_history": history})
                    response = result.get("output", "Sorry, I couldn't process that.")
                except Exception as e:
                    response = f"Error: {e}"
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

def main():
    st.set_page_config(page_title="Chat Crypto Wallet", page_icon="💰", layout="wide")
    init_state()
    
    if st.session_state.agent is None:
        with st.spinner("Starting AI Agent..."):
            try:
                st.session_state.agent, st.session_state.cdp = create_agent()
            except Exception as e:
                st.error(f"Failed to start: {e}")
                st.info("Check that ANTHROPIC_API_KEY is set in .env")
                st.stop()
    
    sidebar()
    chat()
    
    if not st.session_state.messages:
        welcome = """👋 **Welcome to your Chat-First Crypto Wallet!**

I can help you with:
- 💰 Check balances
- 💸 Transfer crypto
- 🎁 Buy gift cards (simulated)
- 📧 Read emails (simulated)

**Try:** "Search for Amazon gift cards" or "Read my emails"
"""
        st.session_state.messages.append({"role": "assistant", "content": welcome})
        st.rerun()

if __name__ == "__main__":
    main()