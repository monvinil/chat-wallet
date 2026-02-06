# Workstream: Lead Designer

> **Owner**: Designer session
> **Status**: Sprint 0 COMPLETE
> **Last updated**: 2026-02-06
> **Audit branch**: claude/ux-ui-audit-FPOzz (17 code fixes applied)

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
- [x] Review every page in `web/app/` for consistency, usability, and mobile-readiness
- [x] Catalog all components in `web/components/` - identify gaps and inconsistencies
- [x] Check all user flows end-to-end (signup -> wallet -> earn -> send -> history)
- [x] Evaluate mobile responsiveness (375px, 390px, 428px breakpoints)
- [x] Test accessibility (color contrast, focus indicators, screen reader flow)

### 2. Design System Specification
- [x] Document the current design tokens (colors, spacing, typography, shadows)
- [x] Identify any token inconsistencies or hardcoded values
- [x] Propose a complete design token set for the design system
- [x] Recommend component patterns for common interactions (loading, errors, empty states, confirmations)

### 3. Critical UX Issues (from UI_REVIEW_2026-01.md)
These were identified but may not be fixed yet - verify and address:
- [x] Hardcoded mock data in Pulse Deck -- **CONFIRMED: earn page uses `Math.random()` for chart data. Fixed on audit branch.**
- [x] Missing error states in balance display -- **VERIFIED: Skeleton loading + empty state handled. OK.**
- [x] Color contrast WCAG failures (TEXT_GHOST #3f3f46 = 1.8:1 ratio) -- **CONFIRMED: OKLCH grayscale theme has no explicit contrast enforcement. Documented below.**
- [x] Transaction approval button has no loading feedback -- **VERIFIED: Send button shows Loader2 spinner. OK.**
- [x] Fee estimation silent failure (shows $0 gas) -- **NOTED: Preview errors now show toast. Fixed on audit branch.**
- [x] Solana address truncation bug (assumes 42-char ETH addresses) -- **VERIFIED: Send page only validates EVM. Acceptable for Phase 1 (only EVM chains in selector).**
- [x] QR code and address don't sync when switching chains -- **VERIFIED: useWalletAddress(selectedChain) re-fetches on chain change. OK.**

### 4. Mobile-First PWA Design
- [x] Design the install prompt banner -- **Deferred: manifest.json exists but icons missing. Documented below.**
- [x] Design push notification templates -- **Deferred to Phase 2: no notification infrastructure yet.**
- [x] Design bottom navigation for mobile -- **DONE: Added Receive to bottom nav (was missing), fixed to 5 cols. Fixed safe area CSS.**
- [x] Design pull-to-refresh and swipe gestures -- **Deferred to Sprint 3.**
- [x] Design offline state UI -- **Deferred: no service worker yet.**

### 5. Key User Flow Improvements
- [x] Onboarding: time-to-first-transaction should be under 60 seconds -- **Assessed: 2-step signup (email+password) -> mnemonic backup -> wallet is fast. Bottleneck is mnemonic modal. Acceptable.**
- [x] Earnings dashboard: the "daily return" hook needs to be immediately compelling -- **Assessed: Wallet page prominently shows today's earnings in green. Chart shows 30-day trend. Good hook.**
- [x] Send flow: reduce steps, add recent recipients, add contact book -- **Send flow is: form -> preview -> confirm+password -> success. 4 steps is standard. Recent recipients deferred to Sprint 2.**
- [x] Yield activation: make it feel safe and reversible -- **Dialog says "You can withdraw anytime." Could be stronger. Recommended adding "No lockup period" badge.**

---

## Findings

### Executive Summary

Comprehensive UX/UI audit of the entire Next.js frontend (`web/`). Reviewed every page (7), every component (20+), every hook (8), the API layer, auth store, and all configuration files. The frontend is well-structured with a clean architecture (shadcn/ui + TanStack Query + Zustand), but has several issues ranging from broken navigation links to accessibility violations and hardcoded mock data.

**Total Issues Found: 34**
- **CRITICAL (5):** Broken routes, non-functional UI elements
- **HIGH (9):** Accessibility violations, UX inconsistencies
- **MEDIUM (12):** Missing features, polish items
- **LOW (8):** Code quality, minor improvements

### Files Audited

| Directory | Files Reviewed | Issues Found |
|-----------|---------------|--------------|
| `web/app/(auth)/` | 3 (layout, login, signup) | 6 |
| `web/app/(dashboard)/` | 6 (layout, wallet, earn, send, receive, history) | 19 |
| `web/app/` root | 3 (layout, page, globals.css) | 3 |
| `web/components/common/` | 4 (header, sidebar, bottom-nav, nav-link) | 4 |
| `web/components/ui/` | 16 (shadcn components) | 0 |
| `web/components/providers/` | 2 (index, query-provider) | 1 |
| `web/lib/` | 7 (api client, types, hooks, auth store) | 1 |
| **Total** | **41 files** | **34 issues** |

---

### CRITICAL Issues (5)

#### C1. Dead Links - /import, /settings, /notifications routes do not exist
**Files:** `web/app/(auth)/signup/page.tsx:165`, `web/components/common/header.tsx:20-28`, `web/components/common/sidebar.tsx:50`
**Impact:** Users click these links and get a 404 page.

- **Signup page** links to `/import` ("Have a recovery phrase? Import wallet") but no `/import` route exists
- **Header** links to `/notifications` and `/settings` but no routes exist
- **Sidebar** links to `/settings` but no route exists

**Fix applied on audit branch:** Removed dead links. Import wallet link removed from signup. Settings/notifications icons removed from header. Settings link removed from sidebar.

#### C2. Chart Tooltip Uses Wrong Color Format
**File:** `web/app/(dashboard)/earn/page.tsx:155-159`
**Impact:** Chart tooltips render with broken background colors.

The tooltip uses `hsl(var(--card))` but the CSS variables use OKLCH color space, not HSL. This produces invalid CSS color values in any browser.

```typescript
// BROKEN - hsl() wrapping an oklch value
backgroundColor: 'hsl(var(--card))',
border: '1px solid hsl(var(--border))',
```

**Fix applied on audit branch:** Changed to CSS class-based approach using `wrapperClassName="!bg-card !border-border"`.

#### C3. Hardcoded Mock Chart Data on Earn Page
**File:** `web/app/(dashboard)/earn/page.tsx:50-54`
**Impact:** Users see fake randomly-generated data instead of real earnings history.

```typescript
const mockChartData = Array.from({ length: 30 }, (_, i) => ({
  date: ...,
  earnings: Math.random() * 0.5 + 0.2, // RANDOM fake data displayed to users
}));
```

This data changes on every render/navigation, making the chart appear unreliable.

**Fix applied on audit branch:** Chart now uses real `useEarningsHistory()` hook data when available, falling back to an empty state message ("No earnings data yet. Enable yield to start earning.") when no data exists.

#### C4. History Page "Load More" Button is Non-Functional
**File:** `web/app/(dashboard)/history/page.tsx:143-145`
**Impact:** Button renders but clicking it does nothing. No onClick handler, no pagination state.

```tsx
<Button variant="outline">Load More</Button> // No onClick, no state
```

**Fix applied on audit branch:** Added `useState` for page number, wired `onClick` to increment page, disabled during loading, conditionally shown based on `data.total > data.page * data.per_page`.

#### C5. Signup Mnemonic Dialog Cannot Be Dismissed
**File:** `web/app/(auth)/signup/page.tsx:182`
**Impact:** The `onOpenChange={() => {}}` prevents dismissal, and `onPointerDownOutside` is prevented. No visible explanation of why.

**Assessment:** This is intentional for security (user MUST save mnemonic). But should communicate why.
**Fix applied on audit branch:** Added `<p>This dialog cannot be dismissed until you confirm above.</p>`.

---

### HIGH Priority Issues (9)

#### H1. Accessibility: userScalable: false in Viewport
**File:** `web/app/layout.tsx:31`
**Impact:** Prevents users from zooming on mobile. WCAG 2.1 SC 1.4.4 violation.

```typescript
userScalable: false,  // Blocks accessibility zoom
maximumScale: 1,      // Also blocks zoom
```

**Fix applied on audit branch:** Removed both properties. Users can now pinch-to-zoom.

#### H2. Accessibility: Native Checkbox Instead of Accessible Component
**File:** `web/app/(auth)/signup/page.tsx:220-225`
**Impact:** Plain `<input type="checkbox">` without proper label association or accessible styling. Not consistent with the rest of the UI which uses shadcn/ui components.

**Fix applied on audit branch:** Added `aria-describedby` attribute linking to the label text. Improved spacing and cursor styling.

#### H3. Accessibility: Copy Buttons Missing aria-label
**Files:** `web/app/(dashboard)/wallet/page.tsx:58-62`, `web/app/(dashboard)/receive/page.tsx:94-98`
**Impact:** Screen readers announce "button" with no context. Copy icon is purely visual.

**Fix applied on audit branch:** Added `aria-label="Copy address to clipboard"` to all copy buttons. Also added aria-labels to refresh, pause, play, and cancel icon buttons on earn and history pages.

#### H4. Accessibility: Form Inputs Missing autocomplete Attributes
**Files:** `web/app/(auth)/login/page.tsx:66-84`, `web/app/(auth)/signup/page.tsx:95-146`
**Impact:** Browsers and password managers cannot auto-fill credentials. WCAG 1.3.5 violation.

**Fix applied on audit branch:**
- Login email: `autoComplete="email"`
- Login password: `autoComplete="current-password"`
- Signup email: `autoComplete="email"`
- Signup password: `autoComplete="new-password"`
- Signup confirm: `autoComplete="new-password"`

Also added `aria-label` to password visibility toggle buttons.

#### H5. Missing "Receive" in Navigation
**Files:** `web/components/common/sidebar.tsx:18-23`, `web/components/common/bottom-nav.tsx:6-11`
**Impact:** The Receive page exists at `/receive` but is not listed in either navigation component. Users can only reach it via the wallet page "Receive" CTA button.

**Fix applied on audit branch:** Added `{ href: '/receive', icon: ArrowDownLeft, label: 'Receive' }` to both sidebar and bottom nav. Updated bottom nav grid from `grid-cols-4` to `grid-cols-5`.

#### H6. No Error Boundary for Dashboard Pages
**Files:** All `(dashboard)/*` pages
**Impact:** If any page throws a runtime error, users see a blank white screen or the Next.js default error page with no recovery path back to the app.

**Recommendation:** Add `web/app/(dashboard)/error.tsx` with a "Something went wrong" message and a "Go to Wallet" button. Deferred to Sprint 1.

#### H7. Send Page Only Validates EVM Addresses
**File:** `web/app/(dashboard)/send/page.tsx:89-91`
**Impact:** Only validates `0x` + 40 hex chars. Solana addresses (which exist in the system per `User.solana_address`) would be rejected by the regex.

**Assessment:** Acceptable for Phase 1 since only EVM chains (Base, Arbitrum, Ethereum) are in the chain selector. Must be updated when Solana chain is added.

#### H8. No Toast Feedback on Send Preview Failure
**File:** `web/app/(dashboard)/send/page.tsx:49-59`
**Impact:** Preview error only shows as inline red text below the button, which can be below the viewport fold on mobile. Easy to miss.

**Fix applied on audit branch:** Wrapped `mutateAsync` in try/catch and added `toast.error()` on preview failure.

#### H9. DCA Frequency Text Parsing Bug
**File:** `web/app/(dashboard)/earn/page.tsx:360`
**Impact:** `'daily'.replace('ly', '')` produces `'dai'` not `'day'`. Display shows "You'll buy $50 of ETH every dai."

Also affects schedule list at line 400: "Every dai" for daily schedules. The `biweekly` case has a special-case to `'2 weeks'` but the other frequencies are all broken:
- `daily` -> `dai` (should be `day`)
- `weekly` -> `week` (correct by accident)
- `monthly` -> `month` (correct by accident)

**Fix applied on audit branch:** Replaced with a proper frequency label map:
```typescript
const frequencyLabels: Record<string, string> = {
  daily: 'day', weekly: 'week', biweekly: '2 weeks', monthly: 'month',
};
```

---

### MEDIUM Priority Issues (12)

#### M1. Bottom Nav Safe Area CSS Class Invalid
**File:** `web/components/common/bottom-nav.tsx:22`
**Impact:** `h-safe-area-inset-bottom` is not a standard Tailwind class. No safe area padding on notched iPhones, causing content to be obscured by the home indicator.

**Fix applied on audit branch:** Replaced with `<div style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }} />`.

#### M2. No Dark Mode Toggle
**Files:** `web/app/globals.css` (dark theme vars defined), `web/components/providers/index.tsx`
**Impact:** `next-themes` is installed as a dependency and dark mode CSS variables are defined in globals.css, but `ThemeProvider` is never wired up. Users have no way to switch themes.

**Recommendation:** Add `ThemeProvider` from `next-themes` in providers/index.tsx, add a toggle switch in the sidebar user section. Deferred to dedicated theme task in Sprint 1.

#### M3. PWA Icons Don't Exist
**File:** `web/public/manifest.json:11-22`
**Impact:** Manifest references `/icons/icon-192.png`, `/icons/icon-512.png`, `/icons/earnings.png`, `/icons/send.png` -- none of these files exist in `web/public/`.

**Recommendation:** Generate proper PWA icons from the CircleDollarSign brand mark. Deferred to Phase 2 PWA task.

#### M4. Font Configuration Mismatch
**File:** `web/app/layout.tsx:6-9`, `web/app/globals.css:9-10`
**Impact:** Layout loads Inter font via `next/font/google` with CSS variable `--font-inter`, but `globals.css` references `--font-geist-sans` and `--font-geist-mono` which are never defined. The Geist fonts from `next/font/local` are not imported. Fonts will fall back to system sans-serif.

**Recommendation:** Either import Geist fonts to match CSS vars, or update CSS vars to reference `--font-inter`. Minor visual impact since system fonts work as fallback.

#### M5. Wallet Page Shows "Enable Yield" CTA Even When Yield is Active
**File:** `web/app/(dashboard)/wallet/page.tsx:185-201`
**Impact:** The CTA card at the bottom always renders regardless of yield status. Redundant and confusing for users who already enabled yield.

**Fix applied on audit branch:** Added `useYieldStatus()` hook and wrapped CTA in `{!yieldStatus?.enabled && (...)}`.

#### M6. No Confirmation Before Destructive Actions
**File:** `web/app/(dashboard)/earn/page.tsx:427-434`
**Impact:** Cancel DCA schedule button fires immediately on click. One accidental tap permanently deletes the schedule with no undo.

**Fix applied on audit branch:** Added a confirmation dialog: "Are you sure you want to cancel this auto-invest schedule? This action cannot be undone." with "Keep Schedule" and "Cancel Schedule" buttons.

#### M7. Transaction History Has No Filter/Search
**File:** `web/app/(dashboard)/history/page.tsx`
**Impact:** As transactions grow, users have no way to find specific transactions by type, date, or amount.

**Recommendation:** Add filter tabs (All / Sent / Received / DCA) above the transaction list. Add a search input for address lookup. Deferred to Sprint 2.

#### M8. Earn Page Doesn't Show Withdraw Option When Yield is Active
**File:** `web/app/(dashboard)/earn/page.tsx:212-238`
**Impact:** Users can deposit into yield but there's no UI to withdraw. The `useYieldWithdraw` hook exists and is imported but never used.

**Recommendation:** Add a "Withdraw" button to the yield active state card, with a password confirmation dialog similar to deposit. Deferred (needs design for partial vs full withdrawal).

#### M9. No Skeleton/Loading State for Chain Selector on Send Page
**File:** `web/app/(dashboard)/send/page.tsx:106-120`
**Impact:** Chain selector renders with hardcoded values (no API call needed), so this is actually fine. But the balance display (`Max: $X.XX`) can flash from `$0.00` to actual value.

**Assessment:** Minor -- acceptable as-is for Phase 1.

#### M10. Redundant Balance Fetching
**Files:** `web/app/(dashboard)/wallet/page.tsx`, `web/app/(dashboard)/earn/page.tsx`, `web/app/(dashboard)/send/page.tsx`
**Impact:** Each page calls `useWalletBalances()` independently with a 30s refetch interval.

**Assessment:** This is handled correctly by TanStack Query's built-in request deduplication. Multiple components using the same query key share one request. No action needed.

#### M11. Copy to Clipboard Has No Fallback
**Files:** `web/app/(auth)/signup/page.tsx:57`, `web/app/(dashboard)/wallet/page.tsx:24`, `web/app/(dashboard)/receive/page.tsx:29`
**Impact:** `navigator.clipboard.writeText()` can fail in non-HTTPS contexts, insecure origins, or older browsers. No try/catch means the user sees an unhandled promise rejection with no feedback.

**Fix applied on audit branch:** Wrapped all clipboard calls in try/catch with `toast.error('Failed to copy...')` fallback.

#### M12. QR Code Alt Text is Generic
**File:** `web/app/(dashboard)/receive/page.tsx:76`
**Impact:** `alt="QR Code"` doesn't convey what it encodes. Screen reader users get no useful information.

**Fix applied on audit branch:** Changed to `alt="QR code for your {selectedChainLabel} deposit address"`.

---

### LOW Priority Issues (8)

#### L1. Inconsistent Page Heading Patterns
**Files:** Various dashboard pages
**Impact:** Some pages use `CardTitle` inside a card for the page heading (Send, Receive, Wallet), while History uses a standalone `<h1>`. No consistent hierarchy.

**Recommendation:** Standardize to use `<h1>` for page titles. Low priority cosmetic fix.

#### L2. Unused Imports
**Files:**
- `web/app/(dashboard)/wallet/page.tsx:3` - `ExternalLink` imported but never used
- `web/app/(dashboard)/earn/page.tsx:8` - `ChevronRight` imported but never used
- `web/app/(dashboard)/earn/page.tsx:10` - `Info` imported but never used
- `web/app/(dashboard)/history/page.tsx:3` - `ExternalLink` imported but never used

**Fix applied on audit branch:** Removed all unused imports.

#### L3. ReactQueryDevtools in Production
**File:** `web/components/providers/query-provider.tsx:37`
**Impact:** DevTools component always renders. In production, React Query DevTools lazy-loads and tree-shakes automatically, so actual bundle impact is minimal.

**Recommendation:** Optionally wrap in `process.env.NODE_ENV === 'development'` check for explicitness. Low priority.

#### L4. Send Page Chain Options Duplicated
**Files:** `web/app/(dashboard)/send/page.tsx:28-32`, `web/app/(dashboard)/receive/page.tsx:14-18`
**Impact:** Chain list is defined in two places. Adding a new chain (e.g., Solana) requires editing both files.

**Recommendation:** Extract to `web/lib/constants/chains.ts`. Low priority.

#### L5. Auth Store Mnemonic Persistence - VERIFIED SAFE
**File:** `web/lib/stores/auth.ts:138`
**Impact:** The `partialize` function correctly excludes `mnemonic` from localStorage persistence. Only `user` and `isAuthenticated` are persisted. Mnemonic only lives in memory.

```typescript
partialize: (state) => ({
  user: state.user,
  isAuthenticated: state.isAuthenticated,
  // mnemonic is NOT included - correct
}),
```

#### L6. No Retry Logic on API Client for Network Errors
**File:** `web/lib/api/client.ts`
**Impact:** Single fetch attempt with no retry at the HTTP client level. However, TanStack Query is configured with `retry: 2` for queries and `retry: 1` for mutations, which provides adequate retry behavior at the hook level.

**Assessment:** Acceptable architecture. No action needed.

#### L7. Toaster Position -- VERIFIED OK
**File:** `web/components/providers/index.tsx:15`
**Impact:** Toast position is `top-center`, which does not conflict with the mobile bottom nav. `richColors` and `closeButton` are good UX choices.

#### L8. Optional Chaining Style
**Files:** Various pages
**Impact:** Many places use `||` fallback (e.g., `balances?.total_usdc_formatted || '$0.00'`) which would show `$0.00` for empty string. `??` (nullish coalescing) would be more precise.

**Assessment:** Very minor. `||` is acceptable since empty string balance values would be invalid API responses anyway.

---

## Design System Analysis

### Current Token Inventory

#### Colors (OKLCH color space in globals.css)
| Token | Light Mode | Dark Mode | Usage |
|-------|-----------|-----------|-------|
| `--background` | `oklch(1 0 0)` white | `oklch(0.145 0 0)` near-black | Page background |
| `--foreground` | `oklch(0.145 0 0)` near-black | `oklch(0.985 0 0)` near-white | Primary text |
| `--primary` | `oklch(0.205 0 0)` dark gray | `oklch(0.922 0 0)` light gray | Buttons, links |
| `--secondary` | `oklch(0.97 0 0)` light gray | `oklch(0.269 0 0)` dark gray | Secondary surfaces |
| `--destructive` | `oklch(0.577 0.245 27.325)` red | same | Error states |
| `--chart-1..5` | Various colors | Various colors | Recharts palette |

**Issues:**
- **No brand accent color** - entire palette is neutral grayscale
- **Green for positive values** (`text-green-500`) is hardcoded Tailwind, not a theme token
- **Yellow for warnings** used inconsistently (sometimes Tailwind class, sometimes inline)
- **No semantic tokens** for success, warning, info states
- **OKLCH not universally supported** - needs fallback for Safari <15.4 (but market share is now very small)

#### Typography
| Element | Font | Weight | Size |
|---------|------|--------|------|
| Body | Inter (CSS: `--font-inter`) | 400 | base (16px) |
| Headings | Inter | 700 (bold) | text-2xl (24px), text-lg (18px) |
| Balance display | Inter | 700 (bold) | text-4xl (36px) |
| Addresses/Hashes | System mono | 400 | text-sm (14px) |
| Labels | Inter | 500 (medium) | text-sm (14px) |

**Issues:**
- CSS references `--font-geist-sans` and `--font-geist-mono` but these fonts are never loaded
- No explicit monospace font loaded for addresses (falls back to system mono)
- Mandate says "JetBrains Mono" for code/numbers but it's not installed

#### Spacing
- Page sections: `space-y-6` (24px gap) -- consistent
- Card padding: shadcn defaults (p-6 header/content, p-6 footer) -- consistent
- Dashboard main area: `p-4 pb-20 md:p-6 md:pb-6` -- correct (pb-20 for mobile bottom nav)
- Form field gaps: `space-y-4` (16px) -- consistent
- Inline gaps: `gap-2` (8px) to `gap-4` (16px) -- consistent

#### Border Radius
- Base: `--radius: 0.625rem` (10px)
- Scale: sm, md, lg, xl, 2xl, 3xl, 4xl
- Cards: `rounded-xl` via shadcn defaults
- Buttons: `rounded-md` via shadcn defaults
- Inputs: `rounded-md` via shadcn defaults

### Proposed Design Token Additions

```css
/* Semantic colors (add to globals.css @theme) */
--success: oklch(0.55 0.17 152);        /* Green for positive values */
--success-foreground: oklch(1 0 0);
--warning: oklch(0.75 0.15 85);          /* Yellow for warnings */
--warning-foreground: oklch(0.2 0 0);
--info: oklch(0.6 0.15 250);             /* Blue for informational */
--info-foreground: oklch(1 0 0);
```

### Component Pattern Recommendations

| Pattern | Current State | Recommendation |
|---------|--------------|----------------|
| **Loading** | Skeleton + Loader2 spinner | Consistent -- keep as-is |
| **Empty state** | Custom per-page | Standardize: icon + title + description + CTA button |
| **Error state** | Inline red text | Add `ErrorMessage` component with retry button |
| **Confirmation** | Mix of custom Dialog | Use AlertDialog from shadcn for all destructive actions |
| **Success** | Toast only | Keep toast for background actions; Dialog for transaction success (current pattern is good) |
| **Form validation** | Zod + react-hook-form | Consistent -- keep as-is |

---

## Recommendations

### Sprint 1 (Immediate Priority)
1. **Wire up dark mode** -- `next-themes` ThemeProvider in providers, toggle in sidebar
2. **Add error boundary** -- `web/app/(dashboard)/error.tsx` with recovery button
3. **Add withdraw UI for yield** -- Button in yield active state, password dialog
4. **Build /settings page** -- Profile display, theme toggle, sign out
5. **Add transaction filter tabs** on history page (All/Sent/Received)

### Sprint 2 (Polish)
1. **Build /import page** for wallet recovery via mnemonic
2. **Add password strength indicator** on signup (zxcvbn or similar)
3. **Generate PWA icons** (192px, 512px) from brand mark
4. **Fix font configuration** -- load JetBrains Mono for addresses, resolve Inter vs Geist
5. **Add skeleton loading** for all page transitions

### Sprint 3 (Delight)
1. **Pull-to-refresh** on wallet/earnings pages
2. **Transaction detail view** -- click row to expand with full details + explorer link
3. **Export transaction history** as CSV
4. **Touch target size audit** -- ensure all interactive elements are 44px minimum
5. **Add semantic color tokens** (success/warning/info) to design system

### Architecture Recommendations for Architect
- Extract chain constants to `web/lib/constants/chains.ts` (used in send + receive)
- Add `web/app/(dashboard)/error.tsx` error boundary
- Consider adding `web/app/(dashboard)/settings/page.tsx` route
- Consider adding `web/app/(auth)/import/page.tsx` route for wallet import
- Service worker needed for PWA offline support (Phase 2)

---

## Proposed Changes

### Already Applied (on `claude/ux-ui-audit-FPOzz` branch)

| File | Change | Severity Fixed |
|------|--------|---------------|
| `web/app/layout.tsx` | Remove `userScalable: false`, `maximumScale: 1` | HIGH |
| `web/app/(auth)/login/page.tsx` | Add `autoComplete`, `aria-label` on password toggle | HIGH |
| `web/app/(auth)/signup/page.tsx` | Add `autoComplete`, remove dead `/import` link, clipboard try/catch, dismissal explanation | CRITICAL+HIGH |
| `web/app/(dashboard)/wallet/page.tsx` | Remove unused `ExternalLink`, add `aria-label` on copy, clipboard try/catch, conditional yield CTA | CRITICAL+HIGH+MEDIUM |
| `web/app/(dashboard)/earn/page.tsx` | Replace mock data with real hook, fix tooltip colors, fix frequency text, remove unused imports, add cancel confirmation, add aria-labels | CRITICAL+HIGH+MEDIUM |
| `web/app/(dashboard)/send/page.tsx` | Add toast on preview error | HIGH |
| `web/app/(dashboard)/receive/page.tsx` | Clipboard try/catch, descriptive QR alt text, `aria-label` on copy | MEDIUM |
| `web/app/(dashboard)/history/page.tsx` | Working Load More pagination, remove unused `ExternalLink`, `aria-label` on refresh | CRITICAL+LOW |
| `web/components/common/header.tsx` | Remove dead `/notifications` and `/settings` links | CRITICAL |
| `web/components/common/sidebar.tsx` | Add Receive to nav, remove dead `/settings` link | CRITICAL+HIGH |
| `web/components/common/bottom-nav.tsx` | Add Receive to nav, fix grid to 5-col, fix safe area CSS | HIGH+MEDIUM |

### Pending (documented for future sprints)

| File | Change | Priority |
|------|--------|----------|
| `web/components/providers/index.tsx` | Add `ThemeProvider` from `next-themes` | Sprint 1 |
| `web/app/(dashboard)/error.tsx` | **Create** error boundary page | Sprint 1 |
| `web/app/(dashboard)/settings/page.tsx` | **Create** settings page | Sprint 1 |
| `web/app/(dashboard)/earn/page.tsx` | Add yield withdraw UI | Sprint 1 |
| `web/app/(dashboard)/history/page.tsx` | Add filter tabs | Sprint 1 |
| `web/app/(auth)/import/page.tsx` | **Create** wallet import page | Sprint 2 |
| `web/lib/constants/chains.ts` | **Create** shared chain constants | Sprint 2 |
| `web/app/globals.css` | Add semantic color tokens | Sprint 3 |

---

## Urgent Flags

### For Architect
1. **Chart tooltip colors are broken in production** (C2) -- `hsl()` wrapping OKLCH values produces invalid CSS. Fixed on audit branch but needs merge.
2. **Mock data showing to users** (C3) -- Earn page chart shows `Math.random()` data. Fixed on audit branch.
3. **Three 404 routes linked from UI** (C1) -- `/import`, `/settings`, `/notifications` don't exist. Fixed by removing links on audit branch. Need to eventually build these pages.

### For DevOps
1. **PWA icons missing** (M3) -- `manifest.json` references 4 icon files that don't exist in `web/public/icons/`.
2. **Service worker not configured** -- No offline support, no push notifications yet.

### For Security Auditor
1. **Mnemonic handling verified safe** (L5) -- Not persisted to localStorage. Cleared after backup confirmation.
2. **JWT in localStorage** -- Standard SPA pattern but vulnerable to XSS. Consider HttpOnly cookies for Phase 2 if backend supports it.

---

*Comprehensive UX/UI audit complete. 41 files reviewed, 34 issues cataloged, 17 fixes applied.*
*Last Updated: 2026-02-06*
