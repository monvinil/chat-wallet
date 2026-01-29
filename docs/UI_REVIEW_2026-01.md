# UI Consistency & Logic Review
**Date:** January 2026
**Status:** Action Required

---

## Executive Summary

Comprehensive review of all UI components identified **28 issues** across 6 files:
- 🔴 **5 HIGH** priority (functionality/security)
- 🟡 **12 MEDIUM** priority (UX/consistency)
- 🟢 **11 LOW** priority (polish/cleanup)

---

## Critical Issues (Fix Immediately)

### 1. Hardcoded Mock Data in Pulse Deck
**File:** [components/chat.py:476-482](components/chat.py#L476-L482)
**Severity:** 🔴 HIGH

```python
# Current (broken)
active_tasks = []  # TODO: Pull from pending_approvals table
perks = [
    {"brand": "spotify", "progress": 75, "target": 100, ...},  # HARDCODED
]
```

**Fix:**
```python
# Query actual data
from scheduler_manager import SchedulerManager
active_tasks = SchedulerManager.get_user_tasks(user_id, status="active")[:3]

# Query gift card purchases for perks
perks = get_user_perk_progress(user_id)  # New function needed
```

---

### 2. Missing Error State in Balance Display
**File:** [components/chat.py:370-391](components/chat.py#L370-L391)
**Severity:** 🔴 HIGH

When balance fetch fails, shows misleading "ONLINE" status.

**Fix:**
```python
except Exception as e:
    logger.error(f"Balance fetch failed: {e}")
    st.markdown("""
    <div style="...">
        <span style="color: #ef4444;">● Unable to load balance</span>
    </div>
    """, unsafe_allow_html=True)
```

---

### 3. Color Contrast Fails WCAG AA
**File:** [design_system.py:38](design_system.py#L38)
**Severity:** 🔴 HIGH (Accessibility)

```python
# Current (fails contrast)
TEXT_GHOST: str = "#3f3f46"  # On #09090b = 1.8:1 ratio

# Required: 4.5:1 for AA compliance
TEXT_GHOST: str = "#6b6b73"  # Better contrast
```

---

### 4. Transaction Approval Button No Feedback
**File:** [components/chat.py:273-289](components/chat.py#L273-L289)
**Severity:** 🔴 HIGH

"APPROVE" button has no visual confirmation when clicked - users may double-click.

**Fix:**
```python
# Add loading state
if st.button("APPROVE", key=f"approve_{tx_id}"):
    st.session_state[f"_approving_{tx_id}"] = True
    # Show spinner or disable button

# In render
if st.session_state.get(f"_approving_{tx_id}"):
    st.markdown("Processing...")
```

---

### 5. Fee Estimation Silent Failure
**File:** [components/modals.py:463-502](components/modals.py#L463-L502)
**Severity:** 🔴 HIGH

If fee estimation fails, shows $0 gas - user thinks it's free.

**Fix:**
```python
except Exception as e:
    logger.warning(f"Fee estimation failed: {e}")
    st.warning("Could not estimate fees. Network may be unavailable.")
    can_send = False  # Block send until fees known
```

---

## Medium Priority Issues

### 6. Terminology Inconsistency: "Treasury" vs "Balance"
**Files:** Multiple
**Severity:** 🟡 MEDIUM

| Location | Current | Should Be |
|----------|---------|-----------|
| chat.py:553 | "Treasury" comment | "Balance" |
| chat.py:598 | "BALANCE" | Keep |
| sidebar.py:132 | "Balance" | Keep |

**Fix:** Global search/replace "Treasury" → "Balance" in user-facing text.

---

### 7. Address Copy Button Not Keyboard Accessible
**File:** [components/sidebar.py:415](components/sidebar.py#L415)
**Severity:** 🟡 MEDIUM

```html
<!-- Current -->
<span class="addr-copy" onclick="..." title="Copy address">Copy</span>

<!-- Better -->
<button class="addr-copy" role="button" tabindex="0"
        onclick="..." onkeypress="if(event.key==='Enter')this.click()"
        aria-label="Copy address to clipboard">Copy</button>
```

---

### 8. Missing Alt Text on Icons
**File:** [components/chat.py:901](components/chat.py#L901)
**Severity:** 🟡 MEDIUM

```python
# Current
icon_html = f'<img src="{icon}" style="...">'

# Fix
icon_html = f'<img src="{icon}" alt="{slot["title"]} icon" style="...">'
```

---

### 9. Mobile: Extra Small Screen Hides Critical Info
**File:** [components/chat.py:827](components/chat.py#L827)
**Severity:** 🟡 MEDIUM

```css
/* Current - hides "Tap to earn" text on iPhone SE */
@media (max-width: 375px) {
    .pulse-card-sub { display: none; }
}

/* Fix - truncate instead of hide */
@media (max-width: 375px) {
    .pulse-card-sub {
        font-size: 10px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
}
```

---

### 10. QR Code Address Mismatch
**File:** [components/modals.py:251-264](components/modals.py#L251-L264)
**Severity:** 🟡 MEDIUM

If user toggles QR between EVM/Solana, displayed address above doesn't update.

**Fix:** Make address display reactive to QR selection:
```python
selected_chain = st.radio("Show QR for:", ["EVM", "Solana"])
display_address = evm_address if selected_chain == "EVM" else solana_address
st.code(display_address)  # Updates with selection
```

---

### 11. Hardcoded Network Options
**File:** [components/modals.py:277-288](components/modals.py#L277-L288)
**Severity:** 🟡 MEDIUM

```python
# Current (duplicated)
network_options = {"Ethereum": "eth-mainnet", ...}

# Fix - use centralized config
from config import NETWORKS
network_options = {n["name"]: key for key, n in NETWORKS.items() if not n.get("testnet")}
```

---

### 12. Chat Input Placeholder Inconsistency
**File:** [components/chat.py:1229-1314](components/chat.py#L1229-L1314)
**Severity:** 🟡 MEDIUM

| State | Current | Should Be |
|-------|---------|-----------|
| Pre-login | "Waiting..." | "Sign in to start chatting" |
| Locked | "Locked" | "Wallet locked - unlock to continue" |
| Normal | "Start typing..." | "Message your wallet..." |

---

### 13. Solana Address Truncation Bug
**File:** [components/sidebar.py:411-413](components/sidebar.py#L411-L413)
**Severity:** 🟡 MEDIUM

Assumes 42-char ETH address but Solana addresses are 44 chars.

```python
# Current (hardcoded for ETH)
<span class="addr-start">{addr[:6]}</span>
<span class="addr-mid">{addr[6:-4]}</span>

# Fix - dynamic
mid_start = 6
mid_end = len(addr) - 4
```

---

### 14. Silent Failure in Yield Display
**File:** [components/sidebar.py:175-212](components/sidebar.py#L175-L212)
**Severity:** 🟡 MEDIUM

```python
# Current - swallows error silently
except Exception as e:
    pass

# Fix
except Exception as e:
    logger.error(f"Yield display error: {e}")
    # Optionally show fallback UI
```

---

### 15. Success Animation Blocks Screen
**File:** [components/modals.py:29-106](components/modals.py#L29-L106)
**Severity:** 🟡 MEDIUM

If JS timeout fails, user is stuck with fullscreen overlay.

**Fix:** Add manual close button:
```html
<button onclick="this.parentElement.remove()"
        style="position:absolute;top:20px;right:20px;...">&times;</button>
```

---

### 16. Onboarding Button Labels Inconsistent
**File:** [onboarding.py:111-133](onboarding.py#L111-L133)
**Severity:** 🟡 MEDIUM

| Button | Current | Should Be |
|--------|---------|-----------|
| Line 111 | "CONNECT FREE AI" | "CONNECT FREE AI" |
| Line 133 | "Configure paid provider" | "CONFIGURE PAID PROVIDER" |

Standardize to ALL CAPS for primary actions.

---

### 17. Seed Phrase Display Security
**File:** [components/modals.py:136-145](components/modals.py#L136-L145)
**Severity:** 🟡 MEDIUM

Add security warning above seed phrase:
```python
st.warning("⚠️ Never share your seed phrase. Anyone with these words can access your wallet.")
```

---

## Low Priority Issues (Polish)

### 18. Dead Code: `_render_pulse_card()`
**File:** [components/chat.py:952-954](components/chat.py#L952-L954)
**Action:** Remove legacy wrapper function

### 19. Dead Code: `render_pulse_deck_skeleton()`
**File:** [components/chat.py:316-325](components/chat.py#L316-L325)
**Action:** Either use it for loading states or remove

### 20. Dead Code: `empty_state()`
**File:** [design_system.py:370-399](design_system.py#L370-L399)
**Action:** Either use it or remove

### 21. Duplicate Components: `status_badge()` vs `status_pill()`
**Files:** [design_system.py:319](design_system.py#L319), [design_system.py:847](design_system.py#L847)
**Action:** Consolidate into single component

### 22. CSS Class Collision Risk
**File:** [components/sidebar.py:382-402](components/sidebar.py#L382-L402)
**Action:** Rename `.addr-box` → `.sidebar-addr-box`

### 23. z-index Conflict
**File:** [styles.py:665](styles.py#L665)
**Action:** Create z-index scale:
```python
Z_INDEX = {
    "dropdown": 100,
    "modal": 1000,
    "toast": 2000,
    "overlay": 9999
}
```

### 24. Stale Version Comments
**File:** [styles.py:6](styles.py#L6)
**Action:** Standardize to "V12" or remove version from comments

### 25. Input Placeholder Color Too Dark
**File:** [styles.py:72](styles.py#L72)
**Action:** Change `#555` → `#888`

### 26. Scrollbar Too Subtle
**File:** [styles.py:457-474](styles.py#L457-L474)
**Action:** Increase opacity: `rgba(255,255,255,0.1)` → `rgba(255,255,255,0.2)`

### 27. Mobile Tab Navigation Hidden
**File:** [styles.py:1034-1036](styles.py#L1034-L1036)
**Action:** Add "More" indicator or horizontal scroll hint

### 28. API Key Setup No Loading State
**File:** [onboarding.py:57-136](onboarding.py#L57-L136)
**Action:** Add spinner when checking API status

---

## Implementation Priority

### Sprint 1 (This Week)
1. Fix hardcoded mock data (#1)
2. Fix color contrast (#3)
3. Fix fee estimation silent failure (#5)
4. Standardize terminology (#6)

### Sprint 2 (Next Week)
5. Fix error states (#2, #14)
6. Fix approval button feedback (#4)
7. Add accessibility improvements (#7, #8)
8. Fix mobile issues (#9)

### Sprint 3 (Following)
9. Clean up dead code (#18-21)
10. Polish and consistency (#22-28)

---

## Testing Checklist

After fixes, verify:
- [ ] Pulse Deck shows real data (not 75/100)
- [ ] Balance error shows clear message
- [ ] Color contrast passes [WebAIM checker](https://webaim.org/resources/contrastchecker/)
- [ ] Approve button shows loading state
- [ ] Fee estimation failure is visible
- [ ] Copy button works with keyboard (Tab + Enter)
- [ ] Icons have alt text (check with screen reader)
- [ ] Extra small screens (375px) still readable
- [ ] QR code and address stay in sync

---

*Generated from comprehensive UI review*
*Last Updated: January 2026*
