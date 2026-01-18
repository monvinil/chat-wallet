#!/usr/bin/env python3
"""
Test to understand stx CookieManager behavior
"""

import streamlit as st
import extra_streamlit_components as stx

st.title("Cookie Manager Test")

# Get cookie manager
if "cm" not in st.session_state:
    st.session_state.cm = stx.CookieManager(key="test_cookies")
    st.session_state.cm_created_at = st.session_state.get("run_count", 0)

cm = st.session_state.cm

# Track runs
run_count = st.session_state.get("run_count", 0) + 1
st.session_state.run_count = run_count

st.write(f"**Run count:** {run_count}")
st.write(f"**Cookie manager created at run:** {st.session_state.cm_created_at}")

# Try to get cookies
all_cookies = cm.get_all()
test_cookie = cm.get("test_cookie")

st.write(f"**All cookies:** {all_cookies}")
st.write(f"**test_cookie value:** {test_cookie}")

# Set a cookie
if st.button("Set test cookie"):
    cm.set("test_cookie", f"value_{run_count}", expires_at=None)
    st.success("Cookie set!")
    st.rerun()

# Check cookies after set
if st.button("Read cookies"):
    st.write(f"Current value: {cm.get('test_cookie')}")

# Force rerun
if st.button("Force rerun"):
    st.rerun()

# Show raw document.cookie via JS
st.markdown("---")
st.write("**Browser cookies (via JS):**")
st.components.v1.html("""
<script>
document.write("<pre>" + document.cookie + "</pre>");
</script>
""", height=100)
