"""
Cached CSS styles for Chat Wallet
Module-level constant - loaded once at import time for performance.
"""

# V22 Design System: "Cinematic Atmosphere" - Deep Zinc, Spotlight, Glass Inputs
MAIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    /* V22 Atmosphere Palette */
    --bg-deep: #09090b;
    --bg-surface: #18181b;
    --text-primary: #f4f4f5;
    --text-secondary: #a1a1aa;
    --border-glass: rgba(255, 255, 255, 0.08);
    --border-hairline: rgba(255, 255, 255, 0.06);
    --font-sans: 'Inter', sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
}

/* 1. THE ATMOSPHERE BACKGROUND */
.stApp {
    background-color: var(--bg-deep);
}

html, body, [class*="css"] {
    font-family: var(--font-sans);
    color: var(--text-primary);
}

/* 2. TYPOGRAPHY */
h1, h2, h3 {
    font-family: 'Inter', sans-serif;
    font-weight: 500 !important;
    letter-spacing: -0.04em !important;
    color: white !important;
}

/* 3. GLASS INPUTS */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stChatInput > div > div > textarea,
.stNumberInput > div > div > input {
    background-color: rgba(255,255,255,0.03) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: 12px !important;
    color: white !important;
    font-family: 'Inter', sans-serif;
    font-size: 15px !important;
    padding: 12px 16px !important;
    transition: all 0.2s ease;
}

.stTextInput > div > div > input:hover,
.stTextArea > div > div > textarea:hover,
.stChatInput > div > div > textarea:hover {
    background-color: rgba(255,255,255,0.05) !important;
    border-color: rgba(255,255,255,0.15) !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stChatInput > div > div > textarea:focus {
    border-color: rgba(255,255,255,0.3) !important;
    box-shadow: 0 0 15px rgba(255,255,255,0.05) !important;
}

.stTextInput > div > div > input::placeholder,
.stChatInput > div > div > textarea::placeholder {
    color: #555 !important;
}

/* Chat input wrapper - remove inner rectangle */
.stChatInput,
.stChatInput *,
.stChatInput div,
[data-testid="stChatInput"],
[data-testid="stChatInput"] *,
[data-testid="stChatInputContainer"],
[data-testid="stChatInputContainer"] * {
    background: transparent !important;
    background-color: transparent !important;
}

/* Only the actual textarea gets the glass style */
.stChatInput textarea,
[data-testid="stChatInput"] textarea {
    background-color: rgba(255,255,255,0.03) !important;
    border: 1px solid var(--border-glass) !important;
}

/* 4. REFINED BUTTONS */
.stButton > button {
    background: transparent !important;
    border: 1px solid var(--border-glass) !important;
    color: var(--text-secondary) !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif;
    font-weight: 500 !important;
    font-size: 13px !important;
    padding: 8px 20px !important;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    background: rgba(255,255,255,0.05) !important;
    color: white !important;
    border-color: rgba(255,255,255,0.2) !important;
    transform: translateY(-1px);
}

/* Primary Action Buttons */
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"],
button[kind="primary"] {
    background: white !important;
    color: black !important;
    border: none !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 12px rgba(255,255,255,0.15);
}

.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="baseButton-primary"]:hover {
    box-shadow: 0 6px 20px rgba(255,255,255,0.25);
    transform: translateY(-1px);
}

.stButton > button[kind="primary"] p,
.stButton > button[kind="primary"] span {
    color: black !important;
}

.stButton > button:disabled {
    opacity: 0.25 !important;
    transform: none !important;
}

/* Form submit buttons */
[data-testid="stFormSubmitButton"] > button,
.stFormSubmitButton > button {
    background: white !important;
    color: black !important;
    border: none !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif;
    font-size: 13px !important;
    padding: 8px 20px !important;
    box-shadow: 0 4px 12px rgba(255,255,255,0.15);
}

[data-testid="stFormSubmitButton"] > button:hover,
.stFormSubmitButton > button:hover {
    box-shadow: 0 6px 20px rgba(255,255,255,0.25);
    transform: translateY(-1px);
}

[data-testid="stFormSubmitButton"] > button p,
[data-testid="stFormSubmitButton"] > button span,
.stFormSubmitButton > button p,
.stFormSubmitButton > button span {
    color: black !important;
}

/* 5. SIDEBAR */
[data-testid="stSidebar"] {
    background-color: #050505 !important;
    border-right: 1px solid var(--border-glass);
}

[data-testid="stSidebar"] > div:first-child {
    background: transparent !important;
}

/* Remove all focus outlines and highlights */
[data-testid="stSidebar"] input:focus,
[data-testid="stSidebar"] button:focus,
[data-testid="stForm"] input:focus,
[data-testid="stForm"] button:focus,
input:focus, button:focus, textarea:focus {
    outline: none !important;
    box-shadow: none !important;
}

*:focus {
    outline: none !important;
}

/* Remove Streamlit's input wrapper highlights */
[data-baseweb="input"],
[data-baseweb="input"]:focus-within,
[data-baseweb="base-input"],
[data-testid="stForm"] [data-baseweb="input"] {
    border-color: var(--border-glass) !important;
    box-shadow: none !important;
    background: rgba(255,255,255,0.03) !important;
    transition: none !important;
}

/* Remove form container highlight */
[data-testid="stForm"] {
    border: none !important;
    background: transparent !important;
}

[data-testid="stForm"] > div {
    border: none !important;
    box-shadow: none !important;
}

/* 6. CHAT BUBBLES */
[data-testid="stChatMessage"] {
    background: transparent !important;
    padding: 12px 0 !important;
    border: none !important;
}

[data-testid="stChatMessage"] [data-testid="stImage"] {
    display: none;
}

/* 7. TABS */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border: none !important;
    background: transparent;
}

.stTabs [data-baseweb="tab"] {
    height: 40px;
    border-radius: 8px;
    border: none !important;
    background: transparent;
    color: #666;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: 500;
    padding: 0 16px;
    transition: all 0.2s ease;
}

.stTabs [data-baseweb="tab"]:hover {
    color: #999;
    background: transparent;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: transparent;
    color: white;
}

/* 8. LAYOUT - Comfortable Width for Cards + Chat */
.block-container {
    padding-top: 2rem;
    max-width: 1100px;
}

/* 8. CODE BLOCKS - V12 Minimal */
code {
    background: transparent !important;
    color: #888 !important;
    padding: 0 !important;
    border-radius: 0 !important;
    font-size: 11px !important;
    font-family: var(--font-mono) !important;
    border: none !important;
}

pre {
    background: transparent !important;
    border: none !important;
    border-bottom: 1px solid var(--border-hairline) !important;
    border-radius: 0 !important;
    padding: 12px 0 !important;
    margin: 0 !important;
}

/* st.code widget - minimal with inline copy button */
[data-testid="stCode"] {
    background: transparent !important;
}

[data-testid="stCode"] > div {
    background: transparent !important;
    border: none !important;
    border-bottom: 1px solid var(--border-hairline) !important;
    border-radius: 0 !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
}

[data-testid="stCode"] pre {
    background: transparent !important;
    border: none !important;
    padding: 12px 0 !important;
    margin: 0 !important;
    flex: 1 !important;
    min-width: 0 !important;
}

[data-testid="stCode"] code {
    background: transparent !important;
    color: #888 !important;
    font-size: 11px !important;
    word-break: break-all !important;
    white-space: pre-wrap !important;
}

/* Copy button - inline at end */
[data-testid="stCode"] button {
    flex-shrink: 0 !important;
    background: transparent !important;
    border: none !important;
    color: #444 !important;
    opacity: 0.4;
    transition: opacity 0.2s ease;
    padding: 8px !important;
    margin: 0 !important;
}

[data-testid="stCode"] button:hover {
    opacity: 1;
    color: white !important;
    background: transparent !important;
}

/* 9. DIVIDERS & MISC */
hr {
    border-color: var(--border-hairline) !important;
    margin: 2rem 0 !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* 10. EXPANDERS */
.streamlit-expanderHeader {
    font-family: var(--font-mono) !important;
    font-size: 10px !important;
    color: #666 !important;
    background: transparent !important;
    border: none !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

details {
    background: transparent !important;
    border: 1px solid var(--border-hairline) !important;
    border-radius: 0 !important;
}

details:hover {
    border-color: rgba(255,255,255,0.15) !important;
}

/* 11. ALERTS */
.stAlert {
    border-radius: 0 !important;
    border: 1px solid var(--border-hairline) !important;
    background: rgba(255,255,255,0.02) !important;
}

/* 12. SELECT/NUMBER INPUTS */
.stSelectbox > div > div,
.stNumberInput > div > div > input {
    background: transparent !important;
    border: none !important;
    border-bottom: 1px solid #333 !important;
    border-radius: 0 !important;
    color: var(--text-primary) !important;
    font-family: var(--font-mono) !important;
}

.stSelectbox > div > div:hover,
.stNumberInput > div > div > input:hover {
    border-bottom-color: #666 !important;
}

/* 13. CAPTIONS */
.stCaption, [data-testid="stCaptionContainer"] p {
    color: #555 !important;
    font-size: 11px !important;
    font-family: var(--font-mono) !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* 14. LINK BUTTONS */
.stLinkButton > a {
    border-radius: 20px !important;
    font-weight: 500 !important;
    border: 1px solid var(--border-hairline) !important;
    background: transparent !important;
    color: #888 !important;
    font-size: 10px !important;
    font-family: var(--font-mono) !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

.stLinkButton > a:hover {
    background-color: rgba(255,255,255,0.05) !important;
    color: white !important;
    border-color: white !important;
}

/* 15. SCROLLBAR */
::-webkit-scrollbar {
    width: 3px;
    height: 3px;
}

::-webkit-scrollbar-track {
    background: transparent;
}

::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.1);
    border-radius: 0;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(255,255,255,0.2);
}

/* 16. METRIC CARDS */
[data-testid="stMetric"] {
    background: transparent;
    border: none;
    padding: 0;
}

[data-testid="stMetricValue"] {
    font-family: var(--font-sans) !important;
    font-weight: 300;
    color: var(--text-primary) !important;
}

[data-testid="stMetricLabel"] {
    font-family: var(--font-mono) !important;
    font-size: 9px !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #555 !important;
}

/* 17. REMOVE DEFAULT PADDING */
.block-container {
    padding-top: 2rem;
}

/* 18. CHECKBOX & RADIO - VOID */
.stCheckbox label span,
.stRadio label span {
    color: #888 !important;
    font-size: 13px !important;
    font-family: var(--font-sans) !important;
}

.stCheckbox [data-testid="stCheckbox"],
.stRadio [data-testid="stRadio"] {
    background: transparent !important;
}

/* 19. TOAST - MINIMAL */
[data-testid="stToast"] {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid var(--border-hairline) !important;
    border-radius: 0 !important;
    color: #888 !important;
    font-family: var(--font-mono) !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* 20. SPINNER - SUBTLE */
.stSpinner > div {
    border-color: rgba(255,255,255,0.1) rgba(255,255,255,0.1) rgba(255,255,255,0.1) white !important;
}

/* 21. NUMBER INPUT LABEL HIDE */
.stNumberInput > label {
    font-family: var(--font-mono) !important;
    font-size: 10px !important;
    color: #555 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* 22. ALERT ICON MINIMAL */
.stAlert [data-testid="stIcon"] {
    display: none;
}

.stAlert [data-testid="stMarkdownContainer"] p {
    color: #888 !important;
    font-family: var(--font-sans) !important;
    font-size: 13px !important;
}

/* ========================================
   MOBILE OPTIMIZATION: < 768px
   ======================================== */
@media (max-width: 768px) {
    /* 1. BUTTONS - 48px touch target minimum */
    .stButton > button {
        padding: 14px 20px !important;
        font-size: 12px !important;
        min-height: 48px !important;
    }

    .stButton > button[kind="primary"]:hover {
        transform: none !important; /* No scale on touch */
    }

    /* 2. INPUTS - 48px height, 16px font prevents iOS zoom */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {
        font-size: 16px !important;
        padding: 14px 0 !important;
        min-height: 48px !important;
    }

    .stChatInput > div > div > textarea {
        font-size: 16px !important;
        min-height: 48px !important;
    }

    /* 3. TABS - Better touch targets */
    .stTabs [data-baseweb="tab-list"] {
        gap: 16px !important;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 12px !important;
        padding: 12px 8px !important;
    }

    /* 4. CHAT - Reduce excess spacing */
    [data-testid="stChatMessage"] {
        padding: 0.75rem 0 !important;
    }

    /* 5. CODE BLOCKS - Readable on small screens */
    code, [data-testid="stCode"] code {
        font-size: 12px !important;
    }

    /* 6. EXPANDERS - Better headers */
    .streamlit-expanderHeader {
        font-size: 11px !important;
        padding: 12px 0 !important;
    }

    /* 7. SELECT/RADIO - Larger targets */
    .stSelectbox > div > div {
        font-size: 14px !important;
        min-height: 48px !important;
    }

    .stCheckbox label span,
    .stRadio label span {
        font-size: 14px !important;
    }

    /* 8. SPACING - Reduce excessive margins + iOS safe areas */
    .block-container {
        padding: 1rem 1rem !important;
        padding-bottom: calc(1rem + env(safe-area-inset-bottom, 0px)) !important;
    }

    /* iOS safe area for chat input at bottom */
    .stChatInput {
        padding-bottom: env(safe-area-inset-bottom, 0px) !important;
    }

    /* 9. ALERTS - Readable on narrow screens */
    .stAlert [data-testid="stMarkdownContainer"] p {
        font-size: 13px !important;
    }

    /* 10. HEADERS - Scale down */
    h1 { font-size: 22px !important; }
    h2 { font-size: 18px !important; }
    h3 { font-size: 16px !important; }

    /* 11. SIDEBAR - Proper drawer behavior on mobile */
    [data-testid="stSidebar"] {
        min-width: 85vw !important;
        max-width: 85vw !important;
        width: 85vw !important;
    }

    [data-testid="stSidebar"] > div {
        padding: 1rem !important;
    }

    /* Ensure sidebar collapse button is visible and touchable */
    [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"] {
        min-width: 48px !important;
        min-height: 48px !important;
        z-index: 999999 !important;
    }

    /* Fix sidebar overlay - ensure it doesn't block main content when collapsed */
    [data-testid="stSidebar"][aria-expanded="false"] {
        transform: translateX(-100%) !important;
        pointer-events: none !important;
    }

    /* Main content should be fully accessible */
    [data-testid="stAppViewBlockContainer"],
    .main .block-container {
        pointer-events: auto !important;
    }
}

/* EXTRA SMALL SCREENS: < 480px (iPhone SE, older phones) */
@media (max-width: 480px) {
    h1 { font-size: 20px !important; }

    .stButton > button {
        padding: 12px 16px !important;
        font-size: 11px !important;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 11px !important;
        padding: 10px 6px !important;
    }

    code, [data-testid="stCode"] code {
        font-size: 11px !important;
    }

    .block-container {
        padding: 0.75rem 0.75rem !important;
    }
}
</style>
"""
