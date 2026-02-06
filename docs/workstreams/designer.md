# Lead Designer Workstream - UX/UI Audit
**Date:** February 2026
**Branch:** claude/ux-ui-audit-FPOzz
**Status:** Complete

---

## Executive Summary

Comprehensive UX/UI audit of the Next.js frontend (`web/`). Reviewed every page, component, layout, hook, API layer, and configuration file. The frontend is well-structured with a clean architecture (shadcn/ui + TanStack Query + Zustand), but has several issues ranging from broken navigation links to accessibility violations and hardcoded mock data.

**Total Issues Found: 34**
- **CRITICAL (5):** Broken routes, non-functional UI elements
- **HIGH (9):** Accessibility violations, UX inconsistencies
- **MEDIUM (12):** Missing features, polish items
- **LOW (8):** Code quality, minor improvements

---

## 1. CRITICAL Issues

### C1. Dead Links - /import, /settings, /notifications routes do not exist
**Files:** `web/app/(auth)/signup/page.tsx:165`, `web/components/common/header.tsx:20-28`, `web/components/common/sidebar.tsx:50`
**Impact:** Users click these links and get a 404 page.

- **Signup page** links to `/import` ("Have a recovery phrase? Import wallet") but no `/import` route exists
- **Header** links to `/notifications` and `/settings` but no routes exist
- **Sidebar** links to `/settings` but no route exists

**Fix applied:** Removed dead links. Import wallet link removed from signup. Settings/notifications links replaced with placeholder toast messages until those pages are built.

### C2. Chart Tooltip Uses Wrong Color Format
**File:** `web/app/(dashboard)/earn/page.tsx:155-159`
**Impact:** Chart tooltips may render with broken background colors.

The tooltip uses `hsl(var(--card))` but the CSS variables use OKLCH color space, not HSL. This produces invalid CSS color values.

**Fix applied:** Changed tooltip styling to use CSS class-based approach that inherits from the theme properly.

### C3. Hardcoded Mock Chart Data on Earn Page
**File:** `web/app/(dashboard)/earn/page.tsx:54-57`
**Impact:** Users see fake randomly-generated data instead of real earnings history.

```typescript
const mockChartData = Array.from({ length: 30 }, (_, i) => ({
  date: ...,
  earnings: Math.random() * 0.5 + 0.2, // RANDOM fake data
}));
```

**Fix applied:** Chart now uses real `useEarningsHistory()` hook data when available, falling back to an empty state message when no data exists.

### C4. History Page "Load More" Button is Non-Functional
**File:** `web/app/(dashboard)/history/page.tsx:141-143`
**Impact:** Button renders but clicking it does nothing - no pagination state management.

**Fix applied:** Implemented cursor-based pagination with proper state management.

### C5. Signup Mnemonic Dialog Cannot Be Dismissed
**File:** `web/app/(auth)/signup/page.tsx:174`
**Impact:** If something goes wrong, the user is stuck in a modal with no escape. The `onOpenChange={() => {}}` prevents any dismissal, and pointerDownOutside is also prevented.

**Assessment:** This is intentional for security (user MUST save their mnemonic). However, there should be a visible explanation of why the dialog can't be dismissed. **Fix applied:** Added visible text explaining the modal is non-dismissable.

---

## 2. HIGH Priority Issues

### H1. Accessibility: userScalable: false in Viewport
**File:** `web/app/layout.tsx:31`
**Impact:** Prevents users from zooming on mobile. WCAG 2.1 SC 1.4.4 violation.

```typescript
userScalable: false, // Blocks accessibility zoom
```

**Fix applied:** Changed to `userScalable: true` and removed `maximumScale: 1`.

### H2. Accessibility: Native Checkbox Instead of Accessible Component
**File:** `web/app/(auth)/signup/page.tsx:218-220`
**Impact:** Plain `<input type="checkbox">` without proper styling or keyboard accessibility.

**Fix applied:** Replaced with the shadcn/ui Checkbox component with proper `aria-describedby`.

### H3. Accessibility: Copy Button Missing aria-label
**Files:** `web/app/(dashboard)/wallet/page.tsx:52-63`, `web/app/(dashboard)/receive/page.tsx:89-100`
**Impact:** Screen readers announce "button" with no context for copy address buttons.

**Fix applied:** Added `aria-label="Copy address to clipboard"` to all copy buttons.

### H4. Accessibility: Form Inputs Missing autocomplete Attributes
**Files:** `web/app/(auth)/login/page.tsx`, `web/app/(auth)/signup/page.tsx`
**Impact:** Browsers cannot auto-fill credentials. WCAG 1.3.5 violation.

**Fix applied:** Added `autoComplete="email"`, `autoComplete="current-password"`, `autoComplete="new-password"` as appropriate.

### H5. Missing "Receive" in Navigation
**Files:** `web/components/common/sidebar.tsx:18-23`, `web/components/common/bottom-nav.tsx:6-11`
**Impact:** The Receive page exists at `/receive` but is not in the navigation. Users can only reach it via the wallet page CTA button.

**Fix applied:** Added Receive to both sidebar and bottom nav (5 items in nav now). Updated bottom nav to use `grid-cols-5`.

### H6. No Error Boundary for Dashboard Pages
**Files:** All `(dashboard)/*` pages
**Impact:** If any page throws a runtime error, users see a blank white screen with no recovery path.

**Assessment:** Recommend adding Next.js `error.tsx` boundary. Deferred to Phase 2.

### H7. Send Page Only Validates EVM Addresses
**File:** `web/app/(dashboard)/send/page.tsx:85-87`
**Impact:** Only validates `0x` + 40 hex chars. Solana addresses (which exist in the system per `User.solana_address`) would be rejected.

**Assessment:** Acceptable for Phase 1 since only EVM chains are in the chain selector. Flag for when Solana is added.

### H8. No Loading/Error Feedback on Send Preview Failure
**File:** `web/app/(dashboard)/send/page.tsx:181-187`
**Impact:** Error message renders below the button but may be missed. No toast notification for preview failures.

**Fix applied:** Added toast notification on preview error.

### H9. DCA Frequency Text Parsing Bug
**File:** `web/app/(dashboard)/earn/page.tsx:341`
**Impact:** `'daily'.replace('ly', '')` produces `'dai'` not `'day'`. "You'll buy $50 of ETH every dai."

**Fix applied:** Replaced with a proper frequency label map.

---

## 3. MEDIUM Priority Issues

### M1. Bottom Nav Safe Area CSS Class Invalid
**File:** `web/components/common/bottom-nav.tsx:22`
**Impact:** `h-safe-area-inset-bottom` is not a standard Tailwind class. No safe area padding on notched iPhones.

**Fix applied:** Changed to `pb-[env(safe-area-inset-bottom)]`.

### M2. No Dark Mode Toggle
**Files:** `web/app/globals.css`, `web/components/providers/index.tsx`
**Impact:** `next-themes` is installed as a dependency but not configured. Users have no way to switch themes.

**Assessment:** Wire up `ThemeProvider` from `next-themes` and add a toggle in sidebar/settings. Deferred to dedicated theme task.

### M3. PWA Icons Don't Exist
**File:** `web/public/manifest.json:11-22`
**Impact:** Manifest references `/icons/icon-192.png`, `/icons/icon-512.png`, `/icons/earnings.png`, `/icons/send.png` - none of these exist in the public folder.

**Assessment:** Need to generate proper PWA icons. Deferred to Phase 2 PWA task.

### M4. Font Configuration Mismatch
**File:** `web/app/layout.tsx:6-9`, `web/app/globals.css:9-10`
**Impact:** Layout loads Inter font with `--font-inter` variable, but CSS references `--font-geist-sans` and `--font-geist-mono` which are never defined. Fonts will fall back to system fonts.

**Assessment:** Either switch to Geist font or update CSS to use `--font-inter`. Minor visual impact since system fonts work fine.

### M5. Wallet Page Shows "Enable Yield" CTA Even When Yield is Active
**File:** `web/app/(dashboard)/wallet/page.tsx:178-194`
**Impact:** The CTA card at the bottom always shows regardless of yield status. Redundant for users who already enabled yield.

**Fix applied:** Conditionally hide the CTA when yield is already enabled.

### M6. No Confirmation Before Destructive Actions
**File:** `web/app/(dashboard)/earn/page.tsx:408-415`
**Impact:** Cancel DCA schedule button has no confirmation. One accidental tap deletes the schedule.

**Fix applied:** Added confirmation dialog before cancelling schedules.

### M7. Transaction History Has No Filter/Search
**File:** `web/app/(dashboard)/history/page.tsx`
**Impact:** As transactions grow, users have no way to find specific transactions.

**Assessment:** Add filter tabs (All/Sent/Received) and search. Deferred to Phase 2.

### M8. Earn Page Doesn't Show Withdraw Option When Yield is Active
**File:** `web/app/(dashboard)/earn/page.tsx:193-219`
**Impact:** Users can deposit into yield but there's no UI to withdraw.

**Assessment:** Add withdraw button to the yield active state. Deferred (needs password dialog similar to deposit).

### M9. No Skeleton/Loading State for Chain Selector on Send Page
**File:** `web/app/(dashboard)/send/page.tsx:100-116`
**Impact:** Chain selector renders immediately with no loading state, which is fine, but the balance display can flash.

**Assessment:** Minor - acceptable as-is.

### M10. Redundant Balance Fetching
**Files:** `web/app/(dashboard)/wallet/page.tsx`, `web/app/(dashboard)/earn/page.tsx`, `web/app/(dashboard)/send/page.tsx`
**Impact:** Each page calls `useWalletBalances()` independently. TanStack Query deduplicates these, but the `refetchInterval: 30s` means background polling on all mounted pages.

**Assessment:** This is handled correctly by TanStack Query's built-in deduplication. No action needed.

### M11. Copy to Clipboard Has No Fallback
**Files:** `web/app/(auth)/signup/page.tsx:56`, `web/app/(dashboard)/wallet/page.tsx:24`, `web/app/(dashboard)/receive/page.tsx:29`
**Impact:** `navigator.clipboard.writeText()` can fail in non-HTTPS contexts or older browsers. No try/catch.

**Fix applied:** Wrapped clipboard calls in try/catch with error toast fallback.

### M12. QR Code Alt Text is Generic
**File:** `web/app/(dashboard)/receive/page.tsx:71`
**Impact:** `alt="QR Code"` doesn't convey what it encodes. Screen reader users get no useful info.

**Fix applied:** Changed to `alt="QR code for your {chain} deposit address"`.

---

## 4. LOW Priority Issues

### L1. Inconsistent Page Heading Patterns
**Files:** Various dashboard pages
**Impact:** Some pages use `CardTitle` inside a card for the page heading (Send, Receive, Wallet), while History uses a standalone `<h1>`.

**Assessment:** Standardize to use `<h1>` for page titles across all pages. Low priority cosmetic.

### L2. Unused Imports
**Files:**
- `web/app/(dashboard)/wallet/page.tsx:4` - `ExternalLink` imported but unused
- `web/app/(dashboard)/earn/page.tsx:9` - `ChevronRight` imported but unused
- `web/app/(dashboard)/earn/page.tsx:10` - `Info` imported but unused

**Fix applied:** Removed unused imports.

### L3. ReactQueryDevtools in Production
**File:** `web/components/providers/query-provider.tsx:37`
**Impact:** DevTools bundle ships to production. Small performance/bundle size impact.

**Assessment:** Wrap in `process.env.NODE_ENV === 'development'` check. Note: React Query DevTools already lazy-loads and tree-shakes in production, so impact is minimal.

### L4. Send Page Chain Options Duplicated
**Files:** `web/app/(dashboard)/send/page.tsx:28-32`, `web/app/(dashboard)/receive/page.tsx:14-18`
**Impact:** Chain list is defined twice. Adding a new chain requires editing both files.

**Assessment:** Extract to a shared constants file. Low priority.

### L5. Auth Store Persists Mnemonic Risk
**File:** `web/lib/stores/auth.ts:138`
**Impact:** The `partialize` correctly excludes `mnemonic` from localStorage. Verified - this is handled correctly.

### L6. No Retry Logic on API Client for Network Errors
**File:** `web/lib/api/client.ts`
**Impact:** Single fetch attempt with no retry. TanStack Query handles retries at the query level, so this is acceptable.

### L7. Toaster Position May Conflict with Bottom Nav
**File:** `web/components/providers/index.tsx:15`
**Impact:** Toast position is `top-center`, which is fine. No conflict with bottom nav.

### L8. Missing TypeScript Strict Null Checks on Optional Chaining
**Files:** Various pages
**Impact:** Many places use `||` fallback (e.g., `balances?.total_usdc_formatted || '$0.00'`) which would show `$0.00` if the value is an empty string. Prefer `??` nullish coalescing.

**Assessment:** Very minor. `||` is acceptable since empty string balance would be invalid anyway.

---

## 5. Design System Analysis

### Color Palette
The app uses OKLCH color space, which is modern and provides perceptually uniform colors. However:
- The palette is entirely grayscale (neutral) with no brand color accent
- Green (#22c55e via Tailwind) is used for positive/earnings but isn't defined in the theme
- Yellow is used for warnings but inconsistently (sometimes as Tailwind class, sometimes inline)
- No semantic success/warning/info color tokens defined

### Typography
- Font: Inter (loaded from Google Fonts)
- CSS references Geist Sans/Mono variables that don't exist (font fallback)
- Good use of font sizing hierarchy (text-4xl for balances, text-2xl for headings)
- Monospace font used correctly for addresses and hashes

### Spacing & Layout
- Consistent use of `space-y-6` for page-level sections
- Good responsive breakpoints (md: for desktop/mobile split)
- Dashboard padding: `p-4 pb-20 md:p-6 md:pb-6` - pb-20 correctly accounts for bottom nav
- Cards use consistent padding via shadcn defaults

### Component Library
- shadcn/ui "new-york" style consistently used
- Good component coverage: Button, Card, Dialog, Input, Select, Tabs, Badge, etc.
- Missing components that could improve UX: AlertDialog (for confirmations), Tooltip, Progress (for loading states)

---

## 6. Mobile Responsiveness Audit

### Layout Behavior
- **Desktop (md+):** Sidebar (w-64) + main content. Correct.
- **Mobile (<md):** Header (h-16) + content + bottom nav (h-16). Correct.
- Sidebar hidden on mobile (`hidden md:flex`). Good.
- Header hidden on desktop (`md:hidden`). Good.

### Touch Targets
- Bottom nav items: Full grid cell (~25% width) - adequate
- Icon buttons (copy, settings): `size="icon"` = 36x36px. Slightly below 44px WCAG minimum. **Recommendation:** Increase to 44px minimum.
- Form submit buttons: Full width. Good.

### Scroll Behavior
- Content area: `overflow-auto` on main. Good.
- Bottom padding `pb-20` prevents content being hidden behind bottom nav. Good.
- No horizontal scroll issues detected in layout.

### Notch/Safe Area
- Bottom nav attempts safe area but uses invalid CSS class. **Fixed.**
- Status bar: `themeColor` correctly set for light/dark. Good.

---

## 7. Interaction Patterns Audit

### Form Submission
- Login/Signup: Good patterns with loading states, error display, validation
- Send flow: Good multi-step (form -> preview -> confirm -> success)
- Yield deposit: Good confirmation with password

### Feedback Mechanisms
- Toast notifications: Used consistently for success/error states
- Loading spinners: Skeleton and Loader2 used appropriately
- Error states: Displayed inline with destructive color

### Navigation
- Client-side routing via Next.js Link. Good.
- Auth redirects: Both layout-level guards and page-level redirects. Slightly redundant but safe.
- Back navigation: No explicit back buttons. Users rely on browser/OS back. Acceptable for Phase 1.

### Data Freshness
- Wallet balances: 30s refetch interval. Good.
- Yield status: 60s refetch. Good.
- Earnings: 5min refetch. Appropriate for slow-changing data.
- Transactions: No auto-refetch (on-demand only). Could benefit from `refetchOnWindowFocus`.

---

## 8. Security UX Audit

### Mnemonic Handling
- Displayed in a modal after signup. Good.
- Cannot dismiss without confirming backup. Good.
- Copied to clipboard with feedback. Acceptable (security trade-off vs usability).
- `clearMnemonic()` called after confirmation. Good.
- Not persisted to localStorage (excluded via `partialize`). **Verified.**

### Password Handling
- Required for yield deposit and transaction send. Good.
- Password visibility toggle on auth forms. Good.
- Password fields use `type="password"` correctly.
- No password strength indicator on signup. **Recommendation:** Add one for Phase 2.

### Token Management
- JWT stored in localStorage. Standard for SPAs (note: vulnerable to XSS but acceptable trade-off).
- Auto-refresh with 1-minute buffer before expiration. Good.
- Refresh deduplication to prevent race conditions. Good.
- Tokens cleared on logout. Good.

---

## 9. Fixes Applied (Sprint 0)

| # | Issue | Severity | Status |
|---|-------|----------|--------|
| C1 | Dead links (/import, /settings, /notifications) | CRITICAL | Fixed |
| C2 | Chart tooltip wrong color format | CRITICAL | Fixed |
| C3 | Mock chart data on earn page | CRITICAL | Fixed |
| C4 | Load More button non-functional | CRITICAL | Fixed |
| H1 | userScalable: false | HIGH | Fixed |
| H2 | Native checkbox on signup | HIGH | Fixed |
| H3 | Copy button missing aria-label | HIGH | Fixed |
| H4 | Form inputs missing autocomplete | HIGH | Fixed |
| H5 | Missing Receive in navigation | HIGH | Fixed |
| H8 | No toast on preview failure | HIGH | Fixed |
| H9 | DCA frequency text bug | HIGH | Fixed |
| M1 | Bottom nav safe area invalid | MEDIUM | Fixed |
| M5 | Yield CTA shows when active | MEDIUM | Fixed |
| M6 | No confirmation before cancel DCA | MEDIUM | Fixed |
| M11 | Clipboard no fallback | MEDIUM | Fixed |
| M12 | QR alt text generic | MEDIUM | Fixed |
| L2 | Unused imports | LOW | Fixed |

---

## 10. Recommendations for Future Sprints

### Sprint 1 (Next)
1. Add dark mode toggle (wire up next-themes)
2. Add transaction filter/search on history page
3. Add withdraw UI for yield
4. Build /settings page with profile, theme toggle, notification prefs
5. Add error.tsx boundary for dashboard route group

### Sprint 2
1. Build /import page for wallet recovery
2. Add password strength indicator on signup
3. Generate proper PWA icons
4. Fix font configuration (Inter vs Geist)
5. Add skeleton loading for all page transitions

### Sprint 3
1. Add pull-to-refresh on wallet/earnings
2. Add haptic feedback for key actions (if PWA supports)
3. Add transaction detail page (click to expand)
4. Add export transaction history (CSV)
5. Touch target size audit and fix (44px minimum)

---

*Generated from comprehensive UX/UI audit of web/ directory*
*Last Updated: February 2026*
