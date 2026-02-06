# Workstream: Lead Designer

> **Owner**: Designer session
> **Status**: Awaiting session start
> **Last updated**: 2026-02-06

---

## Mandate

You are the lead designer. You own:
- UX/UI quality across the entire product (Next.js frontend in `web/`)
- Design system consistency and documentation
- Accessibility (WCAG AA minimum)
- Mobile-first responsive design
- Interaction patterns and micro-interactions
- User flow optimization (onboarding, send money, earn yield, etc.)

You may **read** any code file. You may **edit** files in `web/` (components, styles, layouts). For changes outside `web/`, document them in this file for the architect to implement.

---

## Context to Read First

1. `docs/COMMAND_CENTER.md` - Project overview and your role
2. `docs/UI_REVIEW_2026-01.md` - Previous UI audit (28 issues found, 5 critical)
3. `docs/EXECUTIVE_REVIEW_2026-01.md` - Design got A- rating, see specific feedback
4. `docs/VISION_2026.md` Part V - User journey (Maya the freelancer)
5. `web/` directory - The actual Next.js frontend code

## Key Design Facts
- Design aesthetic: "V8 streetwear" - black/white, minimal, monospace accents
- Component library: shadcn/ui (Radix primitives + Tailwind)
- Typography: Inter (body) + JetBrains Mono (code/numbers)
- The Streamlit UI (`app.py`, `components/`, `styles.py`, `design_system.py`) is **legacy** - don't invest time there
- The Next.js UI (`web/`) is the future - focus all effort here

---

## Sprint 0 Tasks

### 1. Full UX Audit of Next.js Frontend
- [ ] Review every page in `web/app/` for consistency, usability, and mobile-readiness
- [ ] Catalog all components in `web/components/` - identify gaps and inconsistencies
- [ ] Check all user flows end-to-end (signup → wallet → earn → send → history)
- [ ] Evaluate mobile responsiveness (375px, 390px, 428px breakpoints)
- [ ] Test accessibility (color contrast, focus indicators, screen reader flow)

### 2. Design System Specification
- [ ] Document the current design tokens (colors, spacing, typography, shadows)
- [ ] Identify any token inconsistencies or hardcoded values
- [ ] Propose a complete design token set for the design system
- [ ] Recommend component patterns for common interactions (loading, errors, empty states, confirmations)

### 3. Critical UX Issues (from UI_REVIEW_2026-01.md)
These were identified but may not be fixed yet - verify and address:
- [ ] Hardcoded mock data in Pulse Deck
- [ ] Missing error states in balance display
- [ ] Color contrast WCAG failures (TEXT_GHOST #3f3f46 = 1.8:1 ratio)
- [ ] Transaction approval button has no loading feedback
- [ ] Fee estimation silent failure (shows $0 gas)
- [ ] Solana address truncation bug (assumes 42-char ETH addresses)
- [ ] QR code and address don't sync when switching chains

### 4. Mobile-First PWA Design
- [ ] Design the install prompt banner
- [ ] Design push notification templates (daily earnings, DCA executed, price alerts)
- [ ] Design bottom navigation for mobile (currently desktop-oriented)
- [ ] Design pull-to-refresh and swipe gestures
- [ ] Design offline state UI

### 5. Key User Flow Improvements
- [ ] Onboarding: time-to-first-transaction should be under 60 seconds
- [ ] Earnings dashboard: the "daily return" hook needs to be immediately compelling
- [ ] Send flow: reduce steps, add recent recipients, add contact book
- [ ] Yield activation: make it feel safe and reversible

---

## Findings

_Write your audit findings here as you work._

---

## Recommendations

_Write your design recommendations here._

---

## Proposed Changes

_List specific file changes with paths and descriptions._

---

## Urgent Flags

_Flag anything that blocks your work or needs immediate architect attention._

---
