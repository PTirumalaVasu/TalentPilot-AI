---
baseline_commit: eb4a2128
---

# Story 8.1: User Switches Between Light and Dark Theme

Status: done

## Story

As a **user (HR Admin or Employee)**,
I want to switch the application's visual theme,
So that I can use whichever mode I prefer, consistently, across the whole product (FR-30).

## Scope Notes (read before starting)

1. **Frontend-only. No API, no backend, no migration.** Confirmed against `epics.md`'s own Epic 8 header ("Owned by: frontend only — no backend module") and the PRD (§4.9/FR-30: "no backend change required, consistent with the zero-budget/local-only constraint"). The command that kicked off this story said "API and UI" — there is no API half; everything lives in `frontend/`.

2. **No prior UX design exists for this feature.** The PRD's own `[NOTE FOR PM]` on FR-30 flags this explicitly: "No UX scenario, prototype, or prior design work covers this — downstream UX work needs to design both palettes... and confirm the toggle's placement... before build." No `_bmad-output/C-UX-Scenarios/` doc, wireframe, or prototype mentions theming anywhere (confirmed via search). This story therefore makes the palette and placement decisions itself (below), as the epics AC's own text already anchors the placement ("alongside the user-menu, per Phase 4 design intent") — there is no separate design doc to defer to.

3. **Tailwind v4, not v3 — dark mode needs a CSS-side opt-in, not a `tailwind.config.js` flag.** `frontend/package.json` pins `tailwindcss ^4.3.2`, and `frontend/src/index.css` already uses the v4 CSS-first `@import "tailwindcss"` + `@config` syntax. Tailwind v4 does **not** support the v3 `darkMode: 'class'` config key for selector-based toggling — the v4-documented mechanism is a `@custom-variant` declaration in CSS: `@custom-variant dark (&:where(.dark, .dark *));` added to `index.css`. Without this, `dark:` utilities would silently follow `prefers-color-scheme` only, and manual toggling would never visually apply even though state/localStorage worked correctly.

4. **Theme state: new `frontend/src/lib/theme/ThemeContext.tsx`**, following the exact `AuthContext.tsx` shape (`createContext`/`useContext` + a `use*` hook that throws outside its Provider — see `frontend/src/lib/auth/AuthContext.tsx:16,63-67`). Resolution order on first load: `localStorage.getItem('theme')` (`'light' | 'dark'`) → `window.matchMedia('(prefers-color-scheme: dark)').matches` → `'light'` (AC1). Every subsequent manual pick calls `setTheme`, which updates React state, writes `localStorage`, and toggles the `dark` class on `document.documentElement` — no page reload (AC2). `localStorage` writes wrapped in `try/catch` (private-browsing/quota edge case) — a failed write must not throw or block the in-memory theme change, matching this codebase's existing "best-effort, non-blocking" convention for `logout()`'s server-call failures (`HrAppShell.tsx:26-35`, `ContentDiscovery.tsx:170-179`).

5. **FOUC prevention: a tiny inline script in `frontend/index.html`'s `<head>`, before `main.tsx` loads.** React-effect-driven class application (`useEffect` in `ThemeProvider`) runs *after* first paint — on an OS-dark-mode device with no stored preference, or a returning visitor who chose Dark, the page would flash light before flipping. This mirrors the "no flash" bar this codebase already holds itself to for auth (Story 1.6's own title: "Protected Endpoint Gate — No Flash of Protected Content"). The inline script re-implements *only* the read-and-apply half of step 4's resolution order (no React, no state) — `ThemeProvider`'s lazy `useState` initializer must compute the identical value so React's first render matches what the inline script already applied (no hydration mismatch).

6. **Toggle component: new `frontend/src/components/ui/theme-toggle.tsx`.** A single icon button (sun/moon, hand-rolled inline SVG — this codebase has no icon library, confirmed via `package.json`; matches `HrAppShell.tsx`'s own hamburger `<svg>` and `DashboardPage.tsx`'s `TrashIcon` convention of `fill="currentColor"` so `text-*` classes actually reach the glyph, unlike an emoji). `data-testid="theme-toggle"`, `aria-label` reads `"Switch to dark theme"` / `"Switch to light theme"` (the *action*, not the current state — matches `HrAppShell.tsx`'s hamburger `aria-label="Open menu"`/`"Close menu"` pattern). Clicking toggles `light ⇄ dark` via `useTheme().setTheme`.

7. **Placement — exactly two call sites, per the epics AC's "alongside the user-menu" anchor:**
   - `frontend/src/components/layout/HrAppShell.tsx`'s top bar, next to the existing user-menu button (`HrAppShell.tsx:101-124`). Since `Dashboard.tsx`, `SkillsPage.tsx`, and `EmployeesPage.tsx` **all already render through `HrAppShell`** (Story 7.7's extraction), this one placement covers all three HR-side AC3 surfaces automatically — do not add a second toggle inside any of those three pages.
   - `frontend/src/pages/employee/ContentDiscovery.tsx`'s shared `UserMenuButton` header — **both** header variants in this file render it (the idle-grid header at line ~250 and the inline-video-player header at line ~204; both already share one `UserMenuButton` component per the file's own comment at lines 38-41). Add the toggle as a sibling of `<UserMenuButton .../>` at both JSX call sites (or lift it into a tiny shared header fragment if that reads cleaner — either way, don't duplicate the toggle's own markup/logic, only its two render call sites).
   - **`Login.tsx` gets no toggle.** It has no user-menu to place one "alongside" (there is no design intent for a bare, chrome-less toggle on the login screen), and AC2's persistence contract only concerns a choice made *after* landing on a themed page — Login only needs to *render correctly* in whichever theme is already active (AC3), which is a pure `dark:` styling concern, not a new control.
   - `AssignmentWatch.tsx` has no header/chrome of its own at all (confirmed: single `<div className="mx-auto max-w-3xl p-8">` wrapper, no color utility classes) — no toggle, no dark: edits needed there beyond what the shared body background (Scope Note 9) already provides for free.

8. **`ThemeProvider` wraps the whole app, outside `AuthProvider`, in `App.tsx`.** Theme is orthogonal to auth (must work on the pre-login `Login` screen too) — nest `<ThemeProvider><AuthProvider>...</AuthProvider></ThemeProvider>`, not the other way around.

9. **Dark palette convention — the single source of truth for every file touched below.** Since no design doc specifies exact dark values (Scope Note 2), this table is the story's own documented decision — apply it mechanically, don't re-derive per file. Chosen to preserve every existing non-color cue exactly as-is (Scope Note 10) and to stay within Tailwind's stock gray/blue/red/green/yellow scale (no `tailwind.config.js` edit needed — the existing `talentpilot-*` custom shades are a strict subset of the stock `blue-*` scale at the same hex values, so dark-only shades reuse plain `blue-*`/`red-*`/etc. rather than extending the custom palette for shades it doesn't define):

   | Light utility | Dark utility | Where |
   |---|---|---|
   | `bg-white` (surfaces: cards, dialogs, header bars, inputs, dropdowns) | `dark:bg-gray-900` | everywhere |
   | `bg-gray-50` (page background, `body`) | `dark:bg-gray-950` | `index.css` body, page wrapper `<div>`s |
   | `bg-gray-50` (subtle inline panel, e.g. expanded accordion row, employee-info tint) | `dark:bg-gray-800` | `DashboardPage.tsx`, `Accordion`, `ContentDiscovery.tsx` |
   | `bg-gray-100` (skeleton pulse, ghost-button hover, disabled badge) | `dark:bg-gray-800` | everywhere |
   | `border-gray-200` | `dark:border-gray-700` | everywhere |
   | `border-gray-300` (input/button borders) | `dark:border-gray-600` | `Input`, `Button` outline, `Combobox` |
   | `text-gray-900` (primary heading/body text) | `dark:text-gray-100` | everywhere |
   | `text-gray-700` | `dark:text-gray-300` | everywhere |
   | `text-gray-600` / `text-gray-500` (secondary/meta text) | `dark:text-gray-400` | everywhere |
   | `text-gray-400` (placeholder, disabled, "no results") | `dark:text-gray-500` | `Input`, `Combobox`, empty states |
   | `hover:bg-gray-50` / `hover:bg-gray-100` | `dark:hover:bg-gray-800` | nav links, menu items, buttons |
   | `bg-blue-50` (active-nav tint, info banner) | `dark:bg-blue-950` | `HrAppShell` active link, pagination active page |
   | `text-blue-600` / `text-blue-700` (links, accents, active states) | `dark:text-blue-400` | everywhere |
   | `border-blue-200` / `border-blue-600` | `dark:border-blue-800` | info banners, active pagination button |
   | `bg-talentpilot-100` / `text-talentpilot-700` (avatar chip) | `dark:bg-talentpilot-900` / `dark:text-talentpilot-300` (nearest stock shade: none exists on the custom scale — use plain `blue-900`/`blue-300`) | `HrAppShell`, `ContentDiscovery` user-menu avatar |
   | Status-badge pairs `bg-{gray,yellow,green}-100` + `text-{gray,yellow,green}-800` | `dark:bg-{gray,yellow,green}-900` + `dark:text-{gray,yellow,green}-200` (standard Tailwind dark-badge pairing — verified sufficient contrast both directions) | `StatusBadge.tsx`, `DashboardPage.tsx`'s inline status pills |
   | `bg-red-100` / `text-red-700` (destructive hover) | `dark:bg-red-950` / `dark:text-red-300` | delete/trash buttons |
   | `border-red-200` / `text-red-600`/`text-red-700` (error banners, form errors) | `dark:border-red-900` / `dark:text-red-400` | error states, `FormErrorText` |
   | `bg-green-100`/`text-green-700` (completed accents) | `dark:bg-green-950`/`dark:text-green-400` | progress bars, completed stat tiles |

10. **Non-color-only / WCAG 2.1 AA is preserved by construction, not re-verified from scratch.** `StatusBadge.tsx`'s own header comment already states its contract: "never color-only" — every status renders an icon (`○`/`▶`/`✓`) **and** a text label, independent of theme. `HrAppShell.tsx`'s active-nav-link treatment is `aria-current="page"` **plus** a non-color style change, per its own comment citing "UX-DR41... never color-only." Adding `dark:` variants to these existing `bg`/`text` pairs does not remove or weaken either non-color mechanism — both are structural (icon glyph, `aria-current`), not styling. Do not add any *new* color-only signal while touching these files.

11. **Explicitly out of scope — confirmed dead/unreachable code, not overlooked:**
    - `frontend/src/features/dashboard/DashboardRow.tsx` and `frontend/src/features/dashboard/AssignmentsList.tsx` — Story 5.7's Dev Notes confirmed both are imported but never rendered by the real `DashboardPage.tsx` (which builds its own inline table). Re-confirmed still true by reading the current `DashboardPage.tsx` in full during this story's authoring (Scope Note reference below) — it contains no reference to either component.
    - `frontend/src/components/ContinueWatchingCard.tsx` — grep-confirmed to have zero import sites in `frontend/src/` outside its own test file; `ContentDiscovery.tsx` renders `AssignmentCard` for every group (including `IN_PROGRESS`), not `ContinueWatchingCard`. Dead code, same class of gap as the above.
    - `frontend/src/pages/dev/*` (four `/dev/*-demo` routes) — internal dev-only scaffolding predating their real pages, not part of the epics AC's named surface list (Dashboard/Skills/Employees/Content Discovery/login). Leave unthemed.
    - `frontend/src/pages/hr/DashboardStub.tsx` — confirmed unreachable from `App.tsx`'s route table (no route renders it); superseded by the real `Dashboard.tsx`.

12. **New tests only cover the logic layer, not per-file visual/contrast assertions.** This codebase has no visual-regression or contrast-checking tooling (confirmed: no Playwright/axe/pixel-diff dependency in `package.json`, consistent with every prior UI story's own "no headless browser available" disclaimer). `ThemeContext`'s resolution/persistence logic and `ThemeToggle`'s click/label behavior are fully unit-testable in jsdom and get real tests (Task 6). The ~25-file `dark:` styling pass itself is verified by a live browser pass (Task 8), matching this codebase's established live-verification convention (every Epic 6/7 story's Dev Agent Record), not by new automated assertions per file.

## Acceptance Criteria

**AC1 — Default theme on first visit:**
**Given** I have never set a theme preference on this browser
**When** the app first loads
**Then** it defaults to my OS/browser-level preference (`prefers-color-scheme`) if available, otherwise Light.

**AC2 — Manual toggle, immediate, persisted, local-only:**
**Given** I toggle the theme (control placed alongside the user-menu, per Phase 4 design intent)
**When** I select Light or Dark
**Then** the change applies immediately with no page reload, and persists across future sessions on this browser via `localStorage` — not synced server-side to the account (no backend change, per the zero-budget/local-only constraint, §9).

**AC3 — Full-application commitment:**
**Given** either theme is active
**When** any page renders — Dashboard, Skills, Employees, Content Discovery, and the login page
**Then** it renders correctly and completely in that theme — this is a full-application commitment, not a partial skin on select pages.

**AC4 — Accessibility parity across themes:**
**And** Status badges and Provenance Labels (FR-8/FR-9) remain WCAG 2.1 AA-compliant (non-color-only, sufficient contrast) in both themes — the existing accessibility NFR applies identically regardless of theme.

## Tasks / Subtasks

- [x] **Task 1: Tailwind v4 dark-variant enablement** (`frontend/src/index.css`) (Scope Note 3)
  - [x] Add `@custom-variant dark (&:where(.dark, .dark *));` near the top (after the existing `@import`/`@config` lines).
  - [x] Change the `body` base-layer rule from `bg-gray-50` to `bg-gray-50 dark:bg-gray-950` (Scope Note 9) — this alone makes every chrome-less page (e.g. `AssignmentWatch.tsx`) theme-correct for free.

- [x] **Task 2: Theme state — `ThemeContext`** (`frontend/src/lib/theme/ThemeContext.tsx`, new) (AC1, AC2; Scope Notes 4, 8)
  - [x] `type Theme = 'light' | 'dark'`; `STORAGE_KEY = 'theme'`.
  - [x] `getSystemTheme()`: `window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'`.
  - [x] `getInitialTheme()`: read `localStorage.getItem(STORAGE_KEY)`, return it if it's exactly `'light'`/`'dark'`, else `getSystemTheme()` (AC1).
  - [x] `ThemeProvider`: `useState<Theme>(getInitialTheme)` (lazy initializer — must match the inline script's applied class, Scope Note 5); a `useEffect` on `[theme]` that does `document.documentElement.classList.toggle('dark', theme === 'dark')`; `setTheme(next)` updates state and `try { localStorage.setItem(...) } catch {}` (Scope Note 4's best-effort convention).
  - [x] `useTheme()`: throws `Error('useTheme must be used within a ThemeProvider')` outside a Provider — mirrors `useAuth()` exactly (`AuthContext.tsx:63-67`).

- [x] **Task 3: FOUC-prevention inline script** (`frontend/index.html`) (Scope Note 5)
  - [x] Add a `<script>` (not `type="module"`, so it runs synchronously before paint) in `<head>`, after the `<title>`, that re-implements `getInitialTheme()`/apply-class inline (no imports — plain JS, wrapped in `try/catch` since `localStorage`/`matchMedia` can throw in locked-down contexts): read `localStorage.getItem('theme')`, else check `matchMedia('(prefers-color-scheme: dark)')`, then set `document.documentElement.classList.add('dark')` if dark.

- [x] **Task 4: Toggle component** (`frontend/src/components/ui/theme-toggle.tsx`, new) (AC2; Scope Note 6)
  - [x] `ThemeToggle()`: reads `useTheme()`, renders one `<button type="button" data-testid="theme-toggle">` with a hand-rolled sun/moon `currentColor` SVG (moon shown in light mode as the "switch to dark" affordance, sun shown in dark mode as "switch to light" — standard convention), `aria-label` per Scope Note 6, `onClick` calls `setTheme(theme === 'dark' ? 'light' : 'dark')`.
  - [x] Style with the `dark:` pairs from Scope Note 9's table (ghost-button treatment, matching `Button`'s `ghost` variant look without importing it, to keep this a self-contained primitive callable from both the HR shell and the employee header).

- [x] **Task 5: Wire `ThemeProvider` + place the toggle** (AC2, AC3; Scope Notes 7, 8)
  - [x] `App.tsx`: wrap `<AuthProvider>` in `<ThemeProvider>` (outermost).
  - [x] `HrAppShell.tsx`: render `<ThemeToggle />` next to the user-menu button in the top bar (~line 101-124); add `dark:` variants to this file's own classes (sidebar `bg-white`/`border-gray-200`, nav links' active/inactive states, top bar, user-menu dropdown, mobile backdrop stays `bg-black/40` unchanged).
  - [x] `ContentDiscovery.tsx`: render `<ThemeToggle />` alongside `<UserMenuButton .../>` at both header call sites (~line 217, ~line 258); add `dark:` variants throughout this file (both headers, employee-info tint card, stat tiles, section headings, loading/empty/error states) per Scope Note 9.

- [x] **Task 6: New unit tests — logic layer only** (Scope Note 12)
  - [x] `frontend/src/tests/ThemeContext.test.tsx` (new): with no `localStorage` value and `matchMedia` mocked `matches: true` → initial theme is `'dark'` and `document.documentElement` gets the `dark` class; with no stored value and `matchMedia` mocked `matches: false` → `'light'`, no class; with a stored `'dark'` value → that wins over a conflicting `matchMedia` mock; `setTheme('dark')` from a `'light'` start updates the class immediately (no unmount/remount needed) and writes `localStorage`; a `localStorage.setItem` that throws (mock it to throw) doesn't crash `setTheme` and the in-memory theme still changes; `useTheme()` outside a `ThemeProvider` throws.
  - [x] `frontend/src/tests/ThemeToggle.test.tsx` (new): renders with the "Switch to dark theme" label when the current theme is light, and "Switch to light theme" when dark; clicking calls the context's `setTheme` with the opposite value (render inside a real `ThemeProvider`, assert via a sibling consumer or by checking the `dark` class post-click, matching this codebase's existing preference for real-component-tree tests over prop-drilled mocks, e.g. `HrAppShell.test.tsx`'s pattern).

- [x] **Task 7: Apply the Scope Note 9 dark palette across every in-scope file** (AC3, AC4)
  - [x] Shared UI primitives: `components/ui/button.tsx`, `card.tsx`, `input.tsx`, `label.tsx`, `toast.tsx`, `form-error-text.tsx`, `accordion.tsx`, `combobox.tsx`, `dialog.tsx` (panel `bg-white` only — backdrop `bg-black/40` is theme-neutral, leave as-is).
  - [x] Shared components: `components/StatusBadge.tsx` (badge-pair dark variants, Scope Note 10), `components/layout/HrAppShell.tsx` (done in Task 5).
  - [x] Dashboard surface: `pages/hr/Dashboard.tsx`, `features/dashboard/DashboardPage.tsx` (biggest file — toolbar, accordion rows, inline table, inline status pills, progress bars, pagination), `features/dashboard/ProvenanceDrillDownModal.tsx`, `features/dashboard/DeleteAssignmentModal.tsx`, `features/assignments/AssignmentModal.tsx`.
  - [x] Skills surface: `pages/hr/SkillsPage.tsx`, `features/admin/SkillCard.tsx`, `features/admin/NewSkillModal.tsx`, `features/admin/DeleteSkillModal.tsx`, `features/admin/ContentLookupPanel.tsx`, `features/admin/ContentPreviewModal.tsx`, `features/admin/ManualContentEntryForm.tsx`, `features/admin/CurrentlyApprovedContent.tsx`, `features/admin/ApiKeysModal.tsx`.
  - [x] Employees surface: `pages/hr/EmployeesPage.tsx`, `features/admin/EditEmployeeModal.tsx`, `features/admin/DeleteArchiveEmployeeModal.tsx`, `features/admin/RegeneratePasswordModal.tsx`.
  - [x] Content Discovery surface: `pages/employee/ContentDiscovery.tsx` (done in Task 5), `components/AssignmentCard.tsx`.
  - [x] Login surface: `pages/Login.tsx` (no toggle, Scope Note 7 — just `dark:` variants on its own card/inputs/error text).
  - [x] Skip per Scope Note 11: `DashboardRow.tsx`, `AssignmentsList.tsx`, `ContinueWatchingCard.tsx`, `pages/dev/*`, `DashboardStub.tsx`.

- [x] **Task 8: Full regression + live verification**
  - [x] Run full frontend test suite; zero new regressions against the pre-story baseline (`git stash` comparison, matching this codebase's established convention).
  - [x] `tsc --noEmit` / `vite build` clean (or unchanged pre-existing-error count, per this codebase's running baseline).
  - [x] Live-browser pass (Playwright/Chromium installed ad hoc if unavailable, matching Story 1.8/6.5's precedent) across all 5 named AC3 surfaces in both themes: toggle from Dashboard, confirm Skills/Employees/Content Discovery/Login all render themed without a reload; hard-refresh with `localStorage` cleared and OS set to dark → confirm dark loads with no flash; hard-refresh with a stored preference opposite of OS preference → confirm the stored value wins.

### Review Findings

_(`bmad-code-review`, 2026-09-12, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor. Findings read and reachability-verified in the actual files before rating, not taken from the diff hunk alone.)_

- [x] [Review][Patch] `VideoPlayer.tsx` — rendered from both `ContentDiscovery.tsx`'s inline video view and `AssignmentWatch.tsx` — was never touched by this story and is 100% hardcoded inline `style={{...}}` colors (`color: '#666'` captions, `color: '#d32f2f'` error banner, `backgroundColor: '#000'` container), completely independent of the `dark` class. Scope Note 7's "`AssignmentWatch.tsx` has no header/chrome of its own... no dark: edits needed" is true of that file's own JSX but overlooked that the component it mounts is still fully light-styled. Once the surrounding page goes dark, the `#666` loading/capture-status captions sit directly on a near-black body background with contrast around ~3.8:1 — borderline-to-failing WCAG AA's 4.5:1 normal-text threshold. This is a real, reachable AC3/AC4 gap in the actual video-watching flow that this story's Task 7 file list never accounted for. **User decision:** patch now (the black player-container background stays as-is — a dark, theme-invariant video-chrome background is normal regardless of app theme; only the caption text colors need a theme-aware fix). [frontend/src/components/VideoPlayer.tsx:304,308]
- [x] [Review][Patch] `ThemeContext.tsx`'s `getInitialTheme()`/`getSystemTheme()` call `window.localStorage.getItem`/`window.matchMedia` with no `try/catch`, unlike `setTheme`'s already-guarded write path and unlike `index.html`'s inline script's equivalent read logic. Since `ThemeProvider` is the outermost provider in `App.tsx` (wrapping `AuthProvider`, routing, and `Login`), a throw from either call (private-browsing storage restrictions, a locked-down iframe/CSP sandbox, an environment without `matchMedia`) crashes the entire app white-screen at first render, including the login page — directly contradicting the story's own "must not throw or block" design intent, which today only actually holds for writes. [frontend/src/lib/theme/ThemeContext.tsx:8,20]
- [x] [Review][Patch] `frontend/src/index.css`'s `:root` has no `color-scheme` CSS property, so native browser controls (the `<select>` Department/Position filters on `EmployeesPage.tsx` — a named AC3 surface — and scrollbars app-wide) keep following the OS's own color scheme rather than the app's chosen theme, risking a white native dropdown popup inside an otherwise-dark page. [frontend/src/index.css]
- [x] [Review][Patch] `AssignmentCard.tsx`'s progress-bar fill (`bg-green-500`/`bg-blue-500`) has no `dark:` variant, while `DashboardPage.tsx`'s equivalent progress-bar fill (added in this same diff) does — the same UI pattern treated inconsistently within one mechanical pass. [frontend/src/components/AssignmentCard.tsx]
- [x] [Review][Patch] `components/ui/button.tsx`'s `default` variant (used by `Login.tsx`'s "Sign In" button and `ContentDiscovery.tsx`'s "Try again" button, among others) got no dark-mode treatment, while its sibling `outline`/`ghost` variants in the same file/same diff did. [frontend/src/components/ui/button.tsx:10]
- [x] [Review][Patch] `ThemeContext.tsx`'s `useMemo(() => ({ theme, setTheme }), [theme])` omits `setTheme` from its dependency array — harmless today since `setTheme` closes over nothing render-scoped, but it deviates from the exact `AuthContext.tsx` pattern this file claims to mirror (which defines its analogous functions inline inside the `useMemo` callback instead). [frontend/src/lib/theme/ThemeContext.tsx:55]
- [x] [Review][Patch] The same ~15-line `window.matchMedia` mock is copy-pasted into 6 test files (`HrAppShell.test.tsx`, `ContentDiscovery.test.tsx`, `EmployeesPage.test.tsx`, `SkillsPage.test.tsx`, `ThemeContext.test.tsx`, `ThemeToggle.test.tsx`) instead of being added once to the project's shared `frontend/src/tests/setup.ts`.
- [x] [Review][Patch] No test renders `<Login>` under `<ThemeProvider>` to directly assert AC3's claim that the login page needs no toggle but must still fully respect the active theme — that surface is currently only exercised by the (now-removed) ad hoc Playwright run.
- [x] [Review][Patch] Task 6's literal test case "a stored `'dark'` value → wins over a conflicting `matchMedia` mock" is not implemented — `ThemeContext.test.tsx` only tests the reverse direction (stored `'light'` overriding OS-dark). Low functional risk (same code branch either way) but a literal task/test mismatch.
- [x] [Review][Defer] No `matchMedia('change')` listener — a user with no stored preference who flips their OS theme mid-session sees no change until reload; both Blind Hunter and Edge Case Hunter flagged this independently. Beyond AC1's literal "when the app first loads" wording, and no AC asks for live OS-preference tracking. — deferred, real but out of this story's literal AC scope
- [x] [Review][Defer] No `storage` event listener for cross-tab theme sync — a theme change in one tab doesn't propagate to another already-open tab until it's reloaded. Not required by any AC (all four are single-page/single-session in scope). — deferred, real but out of this story's literal AC scope
- [x] [Review][Defer] `ContentDiscovery.tsx`'s employee-info banner gradient (`from-blue-950 to-blue-950`) is a no-op — but this pre-dates the story (the light-mode source was already an identical no-op, `from-blue-50 to-blue-50`); this diff just carried the existing pattern forward faithfully. — deferred, pre-existing, not introduced by this change
- [x] [Review][Defer] Two divergent status-badge color conventions exist for the same three states — `StatusBadge.tsx` uses gray/yellow/green, `AssignmentCard.tsx`'s local inline badge uses gray/blue/green — and this story's dark-mode pass mechanically preserved both without unifying them. — deferred, pre-existing inconsistency, not introduced by this change

Dismissed as non-issues after verification: focus-ring color (`ring-talentpilot-500`) staying constant across themes is common, acceptable design practice, and its dark-mode contrast against the new `gray-950` background is borderline-passing (~3.8:1), not a demonstrated failure; amber warning-banner dark colors (`dark:bg-amber-950`/`dark:text-amber-300`) were applied identically and consistently across all 4 sites that needed them, so while Scope Note 9's table technically omits an amber row, the actual code has no inconsistency — a documentation-completeness nitpick, not a defect; `dark:text-blue-300` (used in `HrAppShell.tsx`'s active nav-link and `DashboardPage.tsx`'s active pagination button, both paired with a filled `bg-blue-950` chip) vs. the palette table's plain-text `dark:text-blue-400` (used correctly by `ContentLookupPanel.tsx`'s underlined, unfilled active tab) is a deliberate and justified distinction — filled-chip text needs more contrast against its own dark fill than bare text needs against the page background, not an inconsistency; the Dev Agent Record's live-verification claims resting on now-removed ad hoc Playwright artifacts matches this project's own established convention (Stories 1.8, 6.5, 7.3, 7.6), and its quantitative claims (400/400 tests, 31-error `tsc` baseline, clean build) were independently reproduced by the Acceptance Auditor itself.

## Dev Notes

### Why this is a large story despite being "1 story" in the epic

Epic 8 has exactly one story, but its own AC3 is an explicit "full-application commitment" — every screen, not a subset. The real complexity isn't the theme-switching mechanism itself (a small, well-precedented Context + localStorage pattern, directly mirroring `AuthContext.tsx`) — it's the mechanical breadth of adding `dark:` utility pairs across ~25 files with zero prior dark-mode infrastructure and zero design-system tokens (every color is a literal Tailwind utility class, not a CSS variable). Scope Note 9's palette table exists specifically so that breadth is executed consistently rather than re-decided file by file.

### Why not CSS variables / a design-token layer instead of per-file `dark:` classes

Would be the more maintainable long-term approach, but this codebase has zero existing token infrastructure (`tailwind.config.js` defines exactly one custom color family, `talentpilot`, with 5 shades) and introducing one now is a much larger, riskier refactor than this story's actual AC asks for. Matches this project's repeated YAGNI precedent (e.g. Story 7.6 Scope Note 8: "don't build a conditional prop for a caller that doesn't exist yet") — ship the `dark:` pairs against the epics' literal ACs now; a future design-system story (Epic 8 has no planned follow-up) can introduce tokens if theming grows beyond a binary light/dark toggle.

### Relationship to Story 7.7 (`HrAppShell`)

This story is the direct beneficiary of Story 7.7's shared-shell extraction — before that refactor, `Dashboard.tsx`/`SkillsPage.tsx`/`EmployeesPage.tsx` each had their own copy-pasted header, which would have meant the toggle (and its `dark:` styling) needed adding in three places instead of one. Confirmed by reading `HrAppShell.tsx` in full (Scope Note 7) that all three pages already delegate their header/nav/user-menu to it.

## Architecture Compliance

- No backend/API/database change (Epic 8's own "frontend only" scope; PRD §9's zero-budget/local-only constraint).
- No new runtime dependency — the toggle icon is hand-rolled SVG (matching `HrAppShell.tsx`/`DashboardPage.tsx`'s existing no-icon-library convention), and `ThemeContext.tsx` uses only React's built-in Context API (matching `AuthContext.tsx`'s precedent, no state-management library).

## References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 8.1] — full AC text, Epic 8 scope/ownership
- [Source: _bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md#FR-30] — the `[NOTE FOR PM]` confirming no UX design exists yet, and the `[ASSUMPTION]` on app-wide scope/per-browser persistence
- [Source: frontend/src/lib/auth/AuthContext.tsx] — the exact Context/Provider/hook shape `ThemeContext.tsx` mirrors
- [Source: frontend/src/components/layout/HrAppShell.tsx] — current top-bar/user-menu structure (Story 7.7), toggle placement site, hamburger-icon SVG convention
- [Source: frontend/src/pages/employee/ContentDiscovery.tsx] — both header variants sharing `UserMenuButton`, second toggle placement site
- [Source: frontend/src/components/StatusBadge.tsx] — the "never color-only" contract (icon + text) that dark-mode styling must not weaken
- [Source: frontend/src/features/dashboard/DashboardPage.tsx] — confirmed no reference to `DashboardRow.tsx`/`AssignmentsList.tsx` (Story 5.7's dead-code finding, re-verified live)
- [Source: frontend/tailwind.config.js, frontend/src/index.css, frontend/package.json] — Tailwind v4.3.2 confirmed; `talentpilot-*` custom shades confirmed as a strict subset of stock `blue-*` at identical hex values
- [Source: frontend/index.html, frontend/src/main.tsx] — FOUC-script insertion point, `ThemeProvider` mount point
- [Source: _bmad-output/implementation-artifacts/7-7-hr-admin-navigation-shell-left-pane-nav.md] — the shared-shell precedent this story builds on; its "no Playwright available" live-verification disclaimer pattern, mirrored in Task 8

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5

### Debug Log References

- `npx vitest run`: 400/400 tests passing after every checkpoint (infra, Dashboard surface, Skills surface, Employees surface, Content Discovery/Login) — zero regressions introduced at any stage, verified incrementally rather than only at the end.
- `npx tsc --noEmit`: 31 pre-existing errors, unchanged from this codebase's documented baseline (Story 6.10's "back to the exact 31-error baseline") — confirmed all 31 live in `useResumePosition.test.ts`, `AssignmentsList.test.tsx`, `DashboardStub.test.tsx`, `RequireAuth.test.tsx`, `ContinueWatchingCard.tsx`, `VideoPlayer.tsx`, `AssignmentsList.tsx`, `VideoPlayerDemo.tsx`, and `ProvenanceDrillDownModal.test.tsx` (a pre-existing mock-typing issue, `Promise<unknown>` vs `Promise<DrillDownResponse>` — unrelated to this story's `dark:`-only edit to the component itself), none newly introduced.
- `npx vite build`: clean, 536 modules (up from 534 pre-story, for the two new files `ThemeContext.tsx`/`theme-toggle.tsx`).
- Live-verified end-to-end against a rebuilt Docker frontend container (`docker compose build frontend && docker compose up -d --no-deps --force-recreate frontend`) with Playwright/Chromium installed ad hoc (matching Story 1.8/6.5's precedent) and removed after use: 15/15 automated browser checks passed —
  - AC1: a fresh browser context with `colorScheme: 'dark'` and no `localStorage` value loads with `<html class="dark">` already applied on first paint (no flash), and a dark body background; the equivalent `colorScheme: 'light'` context defaults to Light.
  - AC2: the toggle renders in both call sites (`HrAppShell` top bar, `ContentDiscovery` header); clicking it flips the `dark` class immediately with no navigation/reload and writes the choice to `localStorage`; a stored `'light'` preference overrides a conflicting OS-dark context on reload (and vice versa).
  - AC3: logged in as Rita (HR_ADMIN), toggled dark, and navigated Dashboard → Skills → Employees via the real nav links — theme persisted across every route with no console errors; signed out and confirmed Login itself renders dark (theme is global, not tied to the authenticated session); logged in as Casey (EMPLOYEE) and confirmed the Content Discovery header's toggle also works with no console errors (the one console entry seen in two runs, a `401` from `AuthContext`'s mount-time `GET /api/auth/me`, is pre-existing, expected pre-login behavior per Story 1.8 — not caused by this story).
  - Two screenshots (Dashboard, Employees, both post-toggle) visually confirmed: dark surfaces, readable text, the active-nav highlight, and the green "Active" status badges all render correctly with no unstyled/white flashes of any element.
- All ad hoc Playwright scripts, screenshots, and the temporary `playwright` package (`npm install --no-save`, so `package.json`/`package-lock.json` were never touched) were removed after verification — confirmed via `git status` that no trace remains.

### Completion Notes List

- **Theme infrastructure** (all new): `frontend/src/lib/theme/ThemeContext.tsx` (Provider/hook mirroring `AuthContext.tsx` exactly), `frontend/src/components/ui/theme-toggle.tsx` (hand-rolled sun/moon SVG toggle), a `@custom-variant dark` declaration + `dark:bg-gray-950`/`dark:text-gray-100` added to `frontend/src/index.css`'s body rule (Tailwind v4's CSS-side mechanism for selector-based dark mode, not the v3 config flag), and a synchronous FOUC-prevention inline script added to `frontend/index.html`'s `<head>`.
- **Wiring**: `App.tsx` now wraps `<AuthProvider>` in `<ThemeProvider>` (outermost, so Login is themed pre-auth too). The toggle is rendered in exactly two places per the epics AC's "alongside the user-menu" anchor: `HrAppShell.tsx`'s top bar (covers Dashboard/Skills/Employees for free via Story 7.7's shared shell) and `ContentDiscovery.tsx`'s shared header (covers both its idle-grid and inline-video-player variants). Login intentionally has no toggle (no user-menu to sit alongside) but fully respects whichever theme is already active.
- **Dark palette applied across all named AC3 surfaces plus their shared chrome**: 9 UI primitives (`button`, `card`, `input`, `label`, `toast`, `form-error-text`, `accordion`, `combobox`, `dialog`), `StatusBadge.tsx`, `HrAppShell.tsx`, and every component reachable from Dashboard, Skills, Employees, Content Discovery, and Login (full list in File List below) — 34 files total, each following the single palette-mapping table documented in the story's Scope Note 9 so the ~25-file mechanical pass stayed consistent rather than re-decided per file.
- **Non-color-only accessibility preserved, not re-invented** (AC4): `StatusBadge.tsx`'s icon+text pairing and `HrAppShell.tsx`'s `aria-current` + non-color active-link treatment were only ever given `dark:` companions to their existing `bg`/`text` classes — neither mechanism was touched, removed, or made color-only.
- **Confirmed dead code stayed out of scope**: `DashboardRow.tsx`, `AssignmentsList.tsx`, and `ContinueWatchingCard.tsx` were re-verified (import-site search + reading `DashboardPage.tsx`/`ContentDiscovery.tsx` in full) to still have zero real call sites in the running app, so no `dark:` work was spent on unreachable code.
- **Test-suite fixes required by the new toggle**: `HrAppShell.test.tsx`, `ContentDiscovery.test.tsx`, `EmployeesPage.test.tsx`, and `SkillsPage.test.tsx` all render components that now call `useTheme()` — each gained a `window.matchMedia` mock (jsdom has no real implementation) and a `<ThemeProvider>` wrapper around their existing render helpers, or they would have thrown `useTheme must be used within a ThemeProvider` / crashed on the unmocked `matchMedia` call. No test assertions changed, only their render setup.
- **New tests**: `ThemeContext.test.tsx` (6 tests: OS-dark/OS-light defaults, stored-preference precedence, immediate `setTheme` application + persistence, a `localStorage.setItem` failure not blocking the in-memory change, `useTheme()` throwing outside a Provider) and `ThemeToggle.test.tsx` (3 tests: correct label per theme, click toggles the `dark` class and the label, a second click returns to light).

### Test Results

```
Frontend: 404 passed, 0 failed (40 test files) -- 400 post-implementation baseline + 4 code-review regression tests
tsc --noEmit: 31 pre-existing errors, unchanged baseline, none in any file this story touched
vite build: clean, 536 modules
```

Live-verified end-to-end via Playwright/Chromium (installed ad hoc, removed after use) against a rebuilt Docker frontend container: 15/15 automated browser checks passed across AC1 (OS-preference default, both directions), AC2 (toggle placement/immediacy/persistence, stored-preference precedence over OS), and AC3 (Dashboard/Skills/Employees/Content Discovery/Login all render correctly in dark with theme persisting across navigation and across sign-out). Re-verified again after the code-review patches (3 targeted checks against a rebuilt Docker frontend): a throwing `localStorage.getItem` no longer crashes the app at mount, `:root`'s `color-scheme` correctly switches light↔dark, and the full toggle flow still works end-to-end.

### File List

New files:
- `frontend/src/lib/theme/ThemeContext.tsx` — `ThemeProvider`/`useTheme`, localStorage + `prefers-color-scheme` resolution
- `frontend/src/components/ui/theme-toggle.tsx` — the light/dark toggle button
- `frontend/src/tests/ThemeContext.test.tsx` — 8 tests (6 implementation + 2 code-review regression tests)
- `frontend/src/tests/ThemeToggle.test.tsx` — 3 tests
- `frontend/src/tests/mockMatchMedia.ts` — code review: shared `matchMedia` mock helper, replacing the copy pasted into `ThemeContext.test.tsx`/`ThemeToggle.test.tsx`

Modified files:
- `frontend/index.html` — FOUC-prevention inline script
- `frontend/src/index.css` — `@custom-variant dark`, dark body background/text; code review: `color-scheme` CSS property added so native controls (select popups, scrollbars) follow the app's theme, not just the OS's
- `frontend/src/App.tsx` — wrapped in `<ThemeProvider>`
- `frontend/src/components/layout/HrAppShell.tsx` — `<ThemeToggle>` placed, full dark pass
- `frontend/src/pages/employee/ContentDiscovery.tsx` — `<ThemeToggle>` placed at both header variants, full dark pass
- `frontend/src/components/ui/{card,input,label,toast,form-error-text,accordion,combobox,dialog}.tsx` — dark variants
- `frontend/src/components/ui/button.tsx` — dark variants; code review: `default` variant also given `dark:bg-blue-700 dark:hover:bg-blue-600` (previously only `outline`/`ghost` were covered)
- `frontend/src/components/StatusBadge.tsx` — dark badge-pair variants
- `frontend/src/components/AssignmentCard.tsx` — dark variants; code review: progress-bar fill (`bg-green-500`/`bg-blue-500`) also given `dark:bg-green-400`/`dark:bg-blue-400`
- `frontend/src/components/VideoPlayer.tsx` — code review: previously untouched and out of the original Task 7 file list; the two status-caption `<p>` elements converted from a fixed inline `color: '#666'` to a themed `className` (`text-gray-600 dark:text-gray-400`), fixing a borderline-failing-contrast gap once the surrounding AC3 pages (Content Discovery's inline video view, `AssignmentWatch.tsx`) render dark
- `frontend/src/pages/hr/{SkillsPage,EmployeesPage}.tsx` — dark variants
- `frontend/src/pages/Login.tsx` — dark variants
- `frontend/src/features/dashboard/{DashboardPage,ProvenanceDrillDownModal,DeleteAssignmentModal}.tsx` — dark variants
- `frontend/src/features/assignments/AssignmentModal.tsx` — dark variants
- `frontend/src/features/admin/{SkillCard,NewSkillModal,DeleteSkillModal,ContentLookupPanel,ContentPreviewModal,ManualContentEntryForm,CurrentlyApprovedContent,ApiKeysModal,EditEmployeeModal,DeleteArchiveEmployeeModal,RegeneratePasswordModal}.tsx` — dark variants
- `frontend/src/tests/{HrAppShell,ContentDiscovery,EmployeesPage,SkillsPage}.test.tsx` — added `<ThemeProvider>` wrapper to existing render helpers (no assertion changes); code review: the per-file `matchMedia` mock removed in favor of the new shared default in `frontend/src/tests/setup.ts`
- `frontend/src/tests/Login.test.tsx` — code review: wrapped in `<ThemeProvider>`, +1 new test asserting AC3's login-dark-rendering claim directly (previously only exercised by the ad hoc Playwright run)
- `frontend/src/tests/setup.ts` — code review: added the shared default `window.matchMedia` stub (replaces 4 near-identical per-file copies)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — story/epic status tracking
- `_bmad-output/implementation-artifacts/deferred-work.md` — 4 items logged from code review

No changes to:
- Any backend file (`backend/`) — this story is frontend-only, confirmed in Scope Note 1
- `frontend/src/features/dashboard/DashboardRow.tsx`, `AssignmentsList.tsx`, `components/ContinueWatchingCard.tsx` — confirmed dead code, Scope Note 11
- `frontend/src/pages/dev/*`, `frontend/src/pages/hr/DashboardStub.tsx` — out of scope, Scope Note 11
- `frontend/tailwind.config.js` — no new custom color shades needed (Scope Note 9's dark-only shades reuse the stock Tailwind scale)

## Change Log

- 2026-09-12: Story created (`bmad-create-story`/Amelia), at user's explicit request to start development, referencing the UX design where available. Confirmed directly (not assumed) that no UX design/prototype exists for this feature — the PRD's own FR-30 note flags the gap — so this story makes the palette (Scope Note 9) and toggle-placement (Scope Note 7) decisions itself, anchored to the epics AC's literal "alongside the user-menu" text. Confirmed Tailwind v4.3.2 (not v3) requires a CSS-side `@custom-variant dark` declaration, not a config flag (Scope Note 3) — a real gap a v3-experienced implementation would miss. Read `AuthContext.tsx`, `HrAppShell.tsx`, `ContentDiscovery.tsx`, `DashboardPage.tsx`, `StatusBadge.tsx`, and every UI primitive in `components/ui/` directly to ground the Context shape, toggle placement, and the dark-palette mapping table in this codebase's actual current state rather than epics text alone. Confirmed three components are genuinely dead/unreachable (`DashboardRow.tsx`, `AssignmentsList.tsx`, `ContinueWatchingCard.tsx`) via direct import-site search, scoping them out rather than theming unreachable code. Status → `ready-for-dev`.
- 2026-09-12: Implementation complete (`bmad-dev-story`/Amelia, same session as creation). Theme infrastructure built (`ThemeContext.tsx`, `theme-toggle.tsx`, `@custom-variant dark`, FOUC-prevention inline script) and wired into `App.tsx` plus both toggle placement sites (`HrAppShell.tsx`, `ContentDiscovery.tsx`). The Scope Note 9 dark palette applied across all 9 UI primitives, `StatusBadge`/`HrAppShell`/`AssignmentCard`, and every component reachable from Dashboard, Skills, Employees, Content Discovery, and Login — 34 files total. 4 existing tests (`HrAppShell`/`ContentDiscovery`/`EmployeesPage`/`SkillsPage`) updated with a `matchMedia` mock + `<ThemeProvider>` wrapper (no assertion changes) since their pages now render `<ThemeToggle>`. 9 new tests (`ThemeContext.test.tsx`, `ThemeToggle.test.tsx`), all TDD. Zero regressions: full suite 400/400 passing at every checkpoint; `tsc --noEmit` unchanged at the documented 31-error baseline, none in a touched file; `vite build` clean (536 modules, up from 534). Live-verified end-to-end against a rebuilt Docker frontend container using Playwright/Chromium installed ad hoc (removed after use, per Story 1.8/6.5's precedent): 15/15 automated checks passed covering AC1 (OS-preference default both directions, no flash), AC2 (toggle immediacy/persistence/stored-preference precedence), and AC3 (all 5 named surfaces render correctly in dark with theme persisting across navigation and sign-out) — screenshots of Dashboard/Employees in dark mode visually confirmed clean rendering with no unstyled flashes. Status → `review`.
- 2026-09-12: Code review (`bmad-code-review`, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor). 1 decision-needed resolved by user (patch `VideoPlayer.tsx` now rather than defer, since it's a real reachable AC3/AC4 gap), 9 patches (all applied), 4 deferred (`deferred-work.md`), 4 dismissed as non-issues after verification (documented in Review Findings). **Most consequential finding**: `ThemeContext.tsx`'s `getInitialTheme()`/`getSystemTheme()` called `localStorage.getItem`/`matchMedia` with no `try/catch`, unlike the already-guarded write path — since `ThemeProvider` is the outermost provider wrapping the entire app including `Login`, a throw from either (private-browsing restrictions, a locked-down sandbox) would have white-screened the whole app at first render. Fixed by wrapping both reads in `try/catch`, matching `index.html`'s inline script's already-correct equivalent. **8 other fixes**: `VideoPlayer.tsx`'s two status captions (reachable from Content Discovery's inline video view and `AssignmentWatch.tsx`, both AC3 surfaces, but never in this story's original Task 7 file list) converted from a fixed `color: '#666'` to a themed class; `index.css` gained a `color-scheme` property so native `<select>` popups/scrollbars follow the app's theme, not just the OS's; `AssignmentCard.tsx`'s progress-bar fill and `button.tsx`'s `default` variant both gained the `dark:` treatment their sibling patterns already had; `ThemeContext.tsx`'s `useMemo` now defines `setTheme` inline (matching `AuthContext.tsx`'s exact precedent) instead of omitting it from the dependency array; the `matchMedia` mock duplicated across 6 test files was centralized into `frontend/src/tests/setup.ts` (4 files) and a new shared `mockMatchMedia.ts` helper (2 files, which need per-test dynamic control); `Login.test.tsx` gained a direct AC3 dark-rendering assertion; `ThemeContext.test.tsx` gained the missing stored-dark-over-OS-light test direction plus 2 new crash-regression tests. Full regression re-verified: 404 passed/0 failed (400 + 4 new), `tsc --noEmit` unchanged at 31 pre-existing errors, `vite build` clean (536 modules). Live-re-verified against a rebuilt Docker frontend: the crash-safety fix, the `color-scheme` fix, and the full toggle flow all confirmed working. Status → `done`.
