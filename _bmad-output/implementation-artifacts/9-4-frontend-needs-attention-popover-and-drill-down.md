---
baseline_commit: c89bab2f
---

# Story 9.4: Frontend: Needs Attention Popover & Drill-Down

Status: done

## Story

As an **HR Admin**,
I want to click straight through to whoever needs attention,
so that the pie chart is something I can act on, not just something I read (FR-33, UX-DR45, UX-DR46).

## Scope Notes (read before starting)

1. **Frontend-only. Zero backend changes.** `EmployeeSegmentationResponse.needs_attention` (Story 9.2) already returns everything this popover needs — `employee_id`, `employee_name`, `assignment_id`, `skill_id`, `skill_name` per flagged Assignment. Story 9.3 fetched this field but never read it (its own Review Findings logged this as a deferred, non-actionable item — "Story 9.4 will use it"). This story is the payoff: read `segmentation.needs_attention`, render it, link it. Do not add, modify, or call any new backend endpoint.

2. **One popover row per flagged *Assignment*, not deduplicated per Employee.** `needs_attention_count` (the pie segment's number) is the count of *distinct flagged Employees*; `needs_attention` (the array) is one row per flagged *Assignment* and can be longer than `needs_attention_count` if an Employee has more than one flagged Assignment (`types/dashboard.ts`'s own doc comment on `EmployeeSegmentationResponse` says this explicitly — do not conflate the two, and do not de-duplicate the list down to one row per employee, since each row must carry its own `assignment_id` to link to the correct drill-down). Row format is literally `"{Employee name} — {Skill name}"` per the UX spec's Content section — iterate `segmentation.needs_attention` directly.

3. **The drill-down destination is the existing per-assignment Provenance Drill-Down modal (`ProvenanceDrillDownModal.tsx`, Story 5-2/FR-9), reached at `/hr/dashboard`, not a new view.** Read `frontend/src/features/dashboard/DashboardPage.tsx` and `frontend/src/pages/hr/Dashboard.tsx` before touching either — `DashboardPage` already owns `selectedAssignmentId` state and renders `<ProvenanceDrillDownModal assignmentId={selectedAssignmentId} open={...} onClose={handleCloseDrillDown} .../>`, fetching drill-down detail directly from `assignmentId` via `dashboardApi.getDrillDown` (independent of whether that assignment's row is currently loaded/visible in the paginated grid — confirmed by reading `ProvenanceDrillDownModal.tsx`'s `fetchDetail`). There is currently **no way to deep-link into this modal from outside `/hr/dashboard`** — that plumbing does not exist yet and must be added by this story (see Task 2). This is wiring an existing view, not building a new one — epics.md's own AC1 text is explicit that this must reuse "the same per-Employee view FR-9 already provides."

4. **New deep-link mechanism: `/hr/dashboard?assignmentId={id}` opens the modal on load.**
   - `Dashboard.tsx`: read `assignmentId` via `useSearchParams()` (react-router-dom v7, already a project dependency, no new package). Pass it to `DashboardPage` as a new optional prop.
   - `DashboardPage.tsx`: add `initialAssignmentId?: string | null` to `DashboardPageProps`. On mount only (empty-deps `useEffect`), if truthy, call the existing `setSelectedAssignmentId(initialAssignmentId)` — reuse the existing state variable and existing `<ProvenanceDrillDownModal>` render, do not add a second modal instance or duplicate its wiring.
   - Add an optional `onInitialAssignmentConsumed?: () => void` prop, invoked from the existing `handleCloseDrillDown()` (alongside its existing `setSelectedAssignmentId(null)`), so `Dashboard.tsx` can strip the now-stale `assignmentId` query param from the URL on close (`searchParams.delete(...)` + `setSearchParams(..., { replace: true })`). This keeps the URL clean after the modal closes; it is a no-op when the modal was opened the normal way (clicking "View Details"), since there is no query param to strip then.
   - Do **not** attempt to auto-expand the target Employee's accordion row in the grid behind the modal — the modal itself renders full drill-down detail independent of the grid/pagination state (Scope Note 3), so this isn't needed to satisfy any AC, and the target row may not even be on the grid's current page. Out of scope; do not build it.

5. **New popover component: build it inline in `SkillAssignmentDashboard.tsx`, not as a new shared `src/components/ui/` primitive.** This codebase's own precedent for a first-and-only-use-site UI piece is to keep it local (see Story 9.3 Scope Note 11's `conicGradient` helper, kept in-file "since this is the only place it's used, so no shared util needed"). This is the first popover in the app; a modal primitive already exists (`components/ui/dialog.tsx`, Story 3.4) but is a full-screen centered overlay with a hard focus trap — wrong shape for a segment-anchored dropdown. The existing anchored-dropdown precedent to follow for *positioning* is `HrAppShell.tsx`'s user-menu (`<div className="relative">` wrapping the trigger, `<div className="absolute ... mt-2">` for the panel) — reuse that positioning pattern, but this popover needs its own Escape/outside-click handling, since the user-menu dropdown doesn't actually implement either (verified by reading `HrAppShell.tsx` — it only closes via re-clicking the trigger or clicking "Sign Out"; do not copy that gap into this story's popover, which has an explicit AC for both).

6. **Needs Attention segment interactivity is entirely count-gated — two structurally different renders, not one render with a disabled state (UX-DR46, epics.md AC2 and Story 9.3's own Scope Note 12, which this story now supersedes only for the interactive case).**
   - **`needs_attention_count === 0`:** keep rendering the exact same plain `LegendRow` Story 9.3 already built (colored dot + `"Needs Attention — 0"` text) — no `<button>`, no `role="button"`, no `aria-label`, no hint text, no popover markup mounted at all. This is a hard AC (epics.md Story 9.4 AC2): "no button role, no 'click to see who' hint, no popover markup at all — not merely a disabled-looking button."
   - **`needs_attention_count > 0`:** render a real `<button type="button">` in the same visual position (same dot + text, same row shape), plus a `"Click to see who"` hint (`dashboard-segmentation-hint`) next to it, `aria-haspopup="true"`, `aria-expanded={open}`, and `aria-label="Needs Attention, {N} employees, click to see who"` (exact copy from UX spec §Accessibility Requirements — interpolate the real count for `{N}`).
   - **On Track / In Progress rows are never interactive, regardless of count** — keep them as the existing plain `LegendRow` unconditionally (epics.md AC3's "deliberate asymmetry, not an oversight").

7. **Popover close behavior (epics.md AC4, UX spec §Accessibility Requirements) — all three paths must work:**
   - **Escape** while the popover is open: close it, then return keyboard focus to the trigger `<button>` (store a ref to it, call `.focus()` in the close handler — mirrors `Dialog.tsx`'s own `previouslyFocused.current?.focus()` pattern, but explicit here since the trigger is a specific known element, not "whatever was focused before").
   - **Click outside** the popover (and outside the trigger button): close it. No focus-restoration requirement is stated for this path in the AC (only "for Escape" is called out) — do not over-build.
   - **Click one of the popover's Employee links**: closes the popover. Since the link navigates to `/hr/dashboard` (a full route change), the whole `SkillAssignmentDashboard` page — popover included — unmounts on navigation; still explicitly close the popover state before/on click for a clean transition and so any test asserting on the popover's presence immediately after click passes deterministically rather than depending on router-unmount timing.
   - No focus trap requirement — this is a non-modal anchored popover, not a `Dialog`. "Tab cycles through employee links inside it" (UX spec) describes natural DOM tab order through the popover's own links, not an artificial wrap-around trap; do not port `Dialog.tsx`'s focus-trap `handleKeyDown` Tab-interception logic here, only its Escape-key idea.

8. **`useSearchParams` is new to this codebase (confirmed via grep — zero existing usage) but is a standard `react-router-dom` v7 hook already in `package.json`, not a new dependency.** Only `Dashboard.tsx` needs it; `DashboardPage.tsx` stays router-hook-free (accepts `initialAssignmentId` as a plain prop), so its existing test file (`DashboardPage.test.tsx`, which renders `<DashboardPage />` directly with no `<MemoryRouter>` wrapper) needs no new routing setup for its existing tests to keep passing.

9. **Route/nav-shell scope boundary unchanged from Story 9.3 — do not touch `HrAppShell.tsx`'s `NAV_LINKS` or add the 4th "Skill Assignments" link.** Still Story 9.5's job. This story only adds the popover to the already-shipped `/dashboard` page and the deep-link-opening capability to the already-shipped `/hr/dashboard` page.

10. **Reuse `CHART_COLORS.needsAttention` (`#dc2626`) from `SkillAssignmentDashboard.tsx`** for any popover chrome that needs the "Needs Attention red" accent (e.g. a left border or icon) — it's already a named export-adjacent module constant in that file (Story 9.3's code-review patch extracted it for exactly this future reuse). Do not reintroduce the hex as a new literal.

## Acceptance Criteria

**AC1 — Popover opens and lists flagged Employees (FR-33, UX-DR45):**
**Given** the Needs Attention segment shows a count greater than zero
**When** I click it
**Then** a popover opens listing exactly those flagged Employees (name + their flagged Skill, from Story 9.2's response), each a link into that Employee's existing Skill Progress drill-down (the same per-Employee view FR-9 already provides — not a new view built for this story).

**AC2 — Zero count is genuinely non-interactive (UX-DR46):**
**Given** the Needs Attention count is exactly zero
**When** the page renders
**Then** that segment is a genuinely non-interactive element — no button role, no "click to see who" hint, no popover markup at all — not merely a disabled-looking button.

**AC3 — On Track / In Progress stay inert (UX-DR45, deliberate asymmetry):**
**Given** the On Track or In Progress segments
**When** I click them
**Then** nothing happens — only Needs Attention is actionable, and this is deliberate, not an oversight to fix later.

**AC4 — Popover close behavior (FR-9's drill-down / user-menu close conventions):**
**Given** the popover is open
**When** I press Escape, click outside it, or click one of its Employee links
**Then** it closes and (for Escape) returns keyboard focus to the segment button.

**AC5 — Nav ownership boundary unchanged (not this story's job):**
**And** clicking "Skill Assignments" in the left nav (Story 9.5) reaches the full, unfiltered grid — this story's popover is the only way this page reaches a *single* Employee's view; the full grid is a separate, nav-level destination, not built by this story. *(Verified by omission: this story adds no nav-link code, confirmed via diff.)*

## Tasks / Subtasks

- [x] **Task 1: Needs Attention popover on the Skill Assignment Dashboard** (AC1, AC2, AC3) — `frontend/src/pages/hr/SkillAssignmentDashboard.tsx`
  - [x] Replace the always-plain `LegendRow` for Needs Attention (Story 9.3) with a count-gated branch (Scope Note 6): `needs_attention_count === 0` → identical plain `LegendRow`, unchanged; `> 0` → new local `NeedsAttentionControl`/popover markup.
  - [x] Track `open` state (`useState`) and a `containerRef`/`triggerRef` (`useRef<HTMLDivElement/HTMLButtonElement>`).
  - [x] Render the trigger as a real `<button type="button" aria-haspopup="true" aria-expanded={open} aria-label="Needs Attention, {N} employees, click to see who" data-testid="dashboard-segmentation-legend-needsattention">` (same visual dot+text as the plain row) plus a sibling hint `<span data-testid="dashboard-segmentation-hint">Click to see who</span>`, both only when count > 0.
  - [x] On click, toggle `open`.
  - [x] Render the popover panel (`data-testid="dashboard-needs-attention-popover"`) absolutely positioned relative to a `position: relative` wrapper around the trigger (Scope Note 5's positioning precedent), only when `open`. One `<Link data-testid="dashboard-needs-attention-popover-item">` per `segmentation.needs_attention` entry (Scope Note 2), text `"{employee_name} — {skill_name}"`, `to={`/hr/dashboard?assignmentId=${entry.assignment_id}`}`, `onClick` closes the popover.
  - [x] Escape-to-close + refocus trigger, click-outside-to-close (Scope Note 7) via a `useEffect` scoped to `open` (mirrors `Dialog.tsx`'s effect-lifecycle shape but without the Tab-trap).
  - [x] On Track / In Progress rows: no change — confirmed they remain the existing plain, always-non-interactive `LegendRow` (AC3), plus a new regression test clicking both and asserting no popover-like element appears.

- [x] **Task 2: Deep-link support on the full grid page** (AC1, AC4) — `frontend/src/pages/hr/Dashboard.tsx`, `frontend/src/features/dashboard/DashboardPage.tsx`
  - [x] `Dashboard.tsx`: read `assignmentId` from `useSearchParams()`; pass as `initialAssignmentId` to `DashboardPage`; pass `onInitialAssignmentConsumed` that strips the param via `setSearchParams(..., { replace: true })` (Scope Note 4).
  - [x] `DashboardPage.tsx`: added `initialAssignmentId`/`onInitialAssignmentConsumed` to `DashboardPageProps`; mount-only effect opens the existing `selectedAssignmentId` state/modal when `initialAssignmentId` is truthy; `handleCloseDrillDown()` also calls `onInitialAssignmentConsumed?.()`.
  - [x] No changes to `ProvenanceDrillDownModal.tsx` itself — it already fetches by `assignmentId` independent of grid/pagination state (Scope Note 3).
  - [x] **Real bug found and fixed during implementation, not anticipated in Scope Notes:** `ProvenanceDrillDownModal` was only ever rendered in `DashboardPage.tsx`'s final "grid loaded" return branch — the Loading/Error/Empty early-return branches each returned their own `<div>` without it. Since every mount starts in the Loading state (and the grid can legitimately be Empty), a deep-linked `initialAssignmentId` would silently fail to open the modal until the grid itself finished loading with ≥1 row — contradicting Scope Note 3's own claim that the modal is "independent of whether that assignment's row is currently loaded/visible." Fixed by hoisting a shared `drillDownModal` JSX const (alongside the existing `liveRegion`/`toastElement` shared consts) and rendering it in all four branches (Loading/Error/Empty/Loaded), replacing the old branch-local `<ProvenanceDrillDownModal>` instance in the Loaded branch. Live-verified via Playwright: the deep-linked modal now visibly opens over the Loading skeleton before the grid finishes fetching.

- [x] **Task 3: Tests** (all ACs) — extended `frontend/src/tests/SkillAssignmentDashboard.test.tsx`; extended `frontend/src/features/dashboard/DashboardPage.test.tsx`
  - [x] `SkillAssignmentDashboard.test.tsx`: count > 0 renders a real button with the exact `aria-label`, hint text present, `data-testid="dashboard-needs-attention-popover"` absent until clicked.
  - [x] Clicking the button opens the popover; it lists one `dashboard-needs-attention-popover-item` per `needs_attention` entry (not deduplicated — tested with 2 entries for the same employee, different `assignment_id`/`skill_name`, both rows present) with the exact `"{name} — {skill}"` text and correct `href`.
  - [x] Escape closes the popover and returns focus to the trigger button (asserted via `toHaveFocus()`).
  - [x] Clicking outside the popover (`userEvent.click(document.body)`) closes it.
  - [x] Clicking a popover item closes the popover; asserted its `href` resolves to `/hr/dashboard?assignmentId=<id>` (this test file has no existing router-aware navigation-assertion pattern to match, since Story 9.3's page has no internal routes of its own — asserting the rendered `<a href>` is the direct, sufficient check here; full cross-page navigation is covered by the Playwright live-verification instead).
  - [x] Renamed/re-scoped Story 9.3's old always-non-interactive test to `needs_attention_count === 0` only (the `> 0` case now legitimately renders a button) — still asserts no button/role/hint/popover markup for the zero case.
  - [x] On Track / In Progress: new regression test clicks both and asserts neither becomes a `<button>` and no popover-like element appears.
  - [x] `DashboardPage.test.tsx`: new `describe("Story 9.4: initialAssignmentId deep-link")` block — one test asserts the modal (`role="dialog"`) opens on mount from `initialAssignmentId` alone, without any `View Details` click; one test asserts `onInitialAssignmentConsumed` fires exactly once after closing it via Escape.

- [x] **Task 4: Regression check**
  - [x] `npx vitest run` → 420/420 passing (412 baseline + 8 new: 6 in `SkillAssignmentDashboard.test.tsx`, 2 in `DashboardPage.test.tsx`), 0 failed, 0 regressions.
  - [x] `npx tsc --noEmit` → 31 errors, byte-identical to the pre-existing baseline (confirmed by running it before starting this story); none in any file this story touched.
  - [x] `npx vite build` → clean, 537 modules (same module count as Story 9.3's baseline — no new modules added, since no new files were created).
  - [x] Live-verified: `talentpilot-ui` was 23h stale (unhealthy) — rebuilt and restarted per Story 9.3's own documented trap. Seeded one temporary self-reported `skill_progress` row backdated 10 days (`event_time`) on an existing assignment with no prior progress, to get one real "Needs Attention" flag without waiting out the 7-day threshold; reverted immediately after verification (`DELETE FROM skill_progress ...`), confirmed segmentation back to its pre-seed state via `curl`. Playwright (Chromium, installed ad hoc via `npm install --no-save playwright` + `npx playwright install chromium`, fully removed after use — `npm uninstall playwright` + `git checkout -- package-lock.json` to discard incidental lockfile metadata noise from a newer local npm version) against the rebuilt container, as HR Admin (`rita@sails.example.com`): clicked the Needs Attention segment on `/dashboard` → popover opened listing exactly the one flagged Employee/Skill with the correct `aria-label` ("Needs Attention, 1 employees, click to see who") → Escape closed it and refocused the trigger button (confirmed via `document.activeElement`) → reopened and clicked the employee link → landed on `/hr/dashboard?assignmentId=...` with the Provenance Drill-Down modal already open (visible over the grid's own Loading skeleton, proving Task 2's bug fix) showing "Casey the Continuer — Story 6.4 Live Verify Skill", "In Progress", "⚠️ Needs Attention", "Last Updated: 10 days ago" → closed the modal (Escape) → confirmed the URL cleaned back to `/hr/dashboard` with no stale `assignmentId` param. Screenshots captured. No console errors attributable to this story's code (one pre-existing, unrelated `401` on `/api/auth/me` observed during the login bootstrap sequence, not touched by this story).

### Review Findings

_(`bmad-code-review`, 2026-09-14, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor, run against the uncommitted diff with this story file as spec context.)_

- [x] [Review][Patch] `ProvenanceDrillDownModal` rendered at an inconsistent child position across `DashboardPage`'s four state branches — React remounts it on the Loading→Loaded transition, defeating this story's own deep-link fix. **Fixed:** `{drillDownModal}` moved to the same position (right after `{toastElement}`) in all four branches; the stale duplicate reference near `<DeleteAssignmentModal>` removed. New regression test added asserting `getDrillDown` is called exactly once across a real Loading→Loaded transition. [frontend/src/features/dashboard/DashboardPage.tsx]
- [x] [Review][Patch] Needs Attention popover panel had no `max-height`/`overflow-y-auto` and no cap on rendered rows — an employee with several flagged assignments, or an org with many flagged employees, could overflow the viewport with no way to reach the rest of the list. **Fixed:** added `max-h-80 overflow-y-auto` to the popover panel. [frontend/src/pages/hr/SkillAssignmentDashboard.tsx]
- [x] [Review][Patch] No programmatic association between the disclosure button and the popover it discloses — `aria-haspopup`/`aria-expanded` were present but the popover had no `id` and the trigger had no `aria-controls`. **Fixed:** added a `useId()`-derived id on the popover panel, referenced via `aria-controls` on the trigger (only while open). [frontend/src/pages/hr/SkillAssignmentDashboard.tsx]
- [x] [Review][Patch] `assignment_id` was interpolated into the popover link's query string via raw template literal with no encoding. Purely defensive (it's a UUID, never needs escaping in practice) but free to harden. **Fixed:** wrapped in `encodeURIComponent()`. [frontend/src/pages/hr/SkillAssignmentDashboard.tsx]
- [x] [Review/Defer] `onInitialAssignmentConsumed` fires unconditionally on every drill-down close (not just the deep-linked one) — harmless today only because the caller (`Dashboard.tsx`) re-guards with `if (!searchParams.has("assignmentId")) return`, not because the callback itself is scoped to the deep-linked case. [frontend/src/features/dashboard/DashboardPage.tsx] — deferred, no observable bug today.
- [x] [Review/Defer] The `initialAssignmentId` effect is intentionally mount-only — an in-place `?assignmentId=` change without a full remount (e.g. same-tab browser back/forward) is silently ignored. Already documented as a deliberate trade-off in this story's own Scope Note 4/Dev Notes, not a regression. [frontend/src/features/dashboard/DashboardPage.tsx] — deferred, by-design trade-off, revisit only if same-tab back/forward between two flagged assignments becomes a real need.
- Dismissed as non-issues after verification: the `aria-label`'s "1 employees" phrasing is the UX spec's own exact mandated copy (`06.1-skill-assignment-dashboard.md` §Accessibility Requirements), not a bug; the badge count (`needs_attention_count`) visibly differing from the popover's row count (`entries.length`) is Story 9.2's own explicit, spec-documented design (distinct-employee count vs. per-flagged-Assignment rows), re-confirmed correct by the Acceptance Auditor; the popover not closing on Tab/focusout is not one of AC4's three required close paths (Escape, outside-click, item-click) and would be scope creep; `handleViewDetails`/`handleDeleteClick` bypassing `onInitialAssignmentConsumed` is unreachable — `Dialog`'s full-screen `fixed inset-0` backdrop blocks all pointer interaction with the underlying grid while any drill-down modal is open, confirmed by reading `components/ui/dialog.tsx` directly; the `handleAssignmentDeleted` guard "never true for the deep-linked id" is pre-existing Story 5.7 behavior, unrelated to and unaffected by this story; an empty-string `?assignmentId=` is unreachable since the only real caller (the popover) always builds the link from a real UUID; `count > 0` with empty `entries` is unreachable by the backend's own construction (`needs_attention_count` is defined as the distinct-employee count *within* `needs_attention`, so `count > 0` implies `entries` is non-empty); the raw-template-literal vs. `URLSearchParams` URL-building style difference matches this codebase's existing convention (no `Link to` prop anywhere else in this codebase is built via `URLSearchParams`); a missing test for a deep-link to a since-deleted/404'd assignment targets `ProvenanceDrillDownModal`'s own pre-existing, independently-tested error handling, unmodified by this story. Two Blind Hunter findings (changelog entries reading as "unfilled template placeholders"; log entries "out of order") were verified false against the actual tracked files — both artifacts of this reviewer's own diff-construction step trimming long narrative comment lines to keep the review prompt short, not real file content; the real `sprint-status.yaml`/`project-context.md` entries are fully detailed and in this file's own established newest-first order, confirmed by direct read.

Full regression re-verified after patches: frontend 421/421 (412 baseline + 9 tests, up from 8 after the new regression test), `tsc --noEmit` unchanged at 31 pre-existing errors, `vite build` clean (537 modules).

## Dev Notes

### This story is small and almost entirely additive — no existing rendering logic changes except one conditional branch

Story 9.3 already built everything on `SkillAssignmentDashboard.tsx` except this one interactive layer, and deliberately left a seam for it (its own Scope Note 12 says as much). The stats row, Progress Ring, and On Track/In Progress legend rows are untouched by this story.

### Why the deep-link mechanism is the real engineering content here, not the popover markup itself

The popover's own AC (list entries, format, click-through) is straightforward given Story 9.2's response already has everything. The non-trivial part is that **no existing code lets any other page open `ProvenanceDrillDownModal` for a specific assignment** — it's entirely internal state to `DashboardPage.tsx`, only ever set by clicking a "View Details" button on an already-loaded, already-paginated grid row. `?assignmentId=` query-param support (Task 2) is the minimum wiring to satisfy AC1's "link into that Employee's existing Skill Progress drill-down" without building a second, parallel drill-down view (which epics.md explicitly forbids: "not a new view built for this story").

### The `needs_attention` array's per-Assignment (not per-Employee) granularity is easy to get wrong

`needs_attention_count` (used for the pie segment number and the button's `aria-label`) and `needs_attention.length` (used for the popover's row count) are **not guaranteed equal** — re-read `types/dashboard.ts`'s doc comment on `EmployeeSegmentationResponse` before writing the popover's render loop. Do not write `needs_attention.slice(0, needs_attention_count)` or any dedup logic; render every entry in the array, exactly as Scope Note 2 specifies.

### Project-context.md entry required before this story can be marked done

Per the Epic 8 retrospective's blocking action item (already applied to Stories 9.1/9.2/9.3): this story must get its own `project-context.md` entry before/alongside marking it done.

## Architecture Compliance

- AR-26: read-composition owned by `dashboard/` (backend) — unaffected; this story adds no backend code, only consumes Story 9.2's already-shipped field.
- FR-9: reused as-is (existing `ProvenanceDrillDownModal`/`getDrillDown` per-assignment drill-down) — not re-implemented or forked.
- FR-29 (nav shell): explicitly NOT touched by this story (Scope Note 9) — Story 9.5's job.

## References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 9.4] — full AC text, this story's exact scope
- [Source: _bmad-output/planning-artifacts/epics.md#Story 9.2] — `needs_attention` field's origin AC ("includes, for each flagged Employee, their id/name and the specific flagged Skill/Assignment — the frontend's popover (Story 9.4) needs this")
- [Source: _bmad-output/C-UX-Scenarios/06-ritas-pulse-check/06.1-skill-assignment-dashboard/06.1-skill-assignment-dashboard.md] — full UX design spec: popover object IDs, interactions table, accessibility requirements (exact `aria-label` copy), Page States table for the popover sub-states
- [Source: _bmad-output/implementation-artifacts/9-3-frontend-skill-assignment-dashboard-landing-page.md] — the page this story extends; its Scope Note 12 explicitly hands off this interactive layer; its Review Findings log the unused `needs_attention` field this story now consumes
- [Source: _bmad-output/implementation-artifacts/9-2-backend-employee-segmentation-endpoint.md] — `EmployeeSegmentationResponse`/`needs_attention` contract, done
- [Source: frontend/src/pages/hr/SkillAssignmentDashboard.tsx] — page to extend; `CHART_COLORS`, `LegendRow`, existing Needs Attention row to branch on
- [Source: frontend/src/features/dashboard/DashboardPage.tsx] — owns `selectedAssignmentId`/`ProvenanceDrillDownModal` wiring to extend with `initialAssignmentId`
- [Source: frontend/src/pages/hr/Dashboard.tsx] — route-level `/hr/dashboard` wrapper to add `useSearchParams` to
- [Source: frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx] — existing per-assignment drill-down modal, reused unmodified
- [Source: frontend/src/components/ui/dialog.tsx] — Escape/focus-restore precedent (positioning and Tab-trap NOT reused, see Scope Note 5/7)
- [Source: frontend/src/components/layout/HrAppShell.tsx] — anchored-dropdown positioning precedent (`relative`/`absolute`); confirmed it has no Escape/outside-click handling of its own, not a full precedent to copy
- [Source: frontend/src/types/dashboard.ts] — `NeedsAttentionEntry`/`EmployeeSegmentationResponse` types, already defined by Story 9.2/9.3
- [Source: frontend/src/tests/SkillAssignmentDashboard.test.tsx] — existing test file/mocking pattern to extend
- [Source: frontend/src/features/dashboard/DashboardPage.test.tsx] — existing test file/mocking pattern to extend

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5

### Debug Log References

- `npx tsc --noEmit` (before starting) → 31 `error TS` occurrences — confirmed as the exact baseline to preserve, not assumed from Story 9.3's record.
- `npx vitest run src/tests/SkillAssignmentDashboard.test.tsx` → 14/14 passed (8 baseline + 6 new/modified).
- `npx vitest run src/features/dashboard/DashboardPage.test.tsx` → 21/21 passed (19 baseline + 2 new).
- `npx vitest run` (full suite) → 420/420 passed (412 baseline + 8 new), 0 failed.
- `npx tsc --noEmit` (after) → 31 errors, unchanged; none in `SkillAssignmentDashboard.tsx`, `Dashboard.tsx`, `DashboardPage.tsx`, or either test file.
- `npx vite build` → clean, 537 modules (same as Story 9.3's baseline).
- `docker compose build frontend && docker compose up -d frontend` — `talentpilot-ui` was 23h stale/unhealthy at session start (predates this story, matches Story 9.3's already-documented trap); rebuilt and restarted.
- DB: `docker exec talentpilot-db psql ...` — seeded one temporary `skill_progress` row (`verified=false`, `event_time = now() - interval '10 days'`) on assignment `0d41046c-d793-4e8a-850c-775243b249bd` (Casey the Continuer / "Story 6.4 Live Verify Skill", which had no prior progress row) to produce one real Needs Attention flag without waiting out the 7-day threshold; deleted it immediately after verification and confirmed via `curl http://localhost:8000/api/dashboard/segmentation` that the response returned to its pre-seed state (`needs_attention_count: 0`).
- Playwright (Chromium, `npm install --no-save playwright` + `npx playwright install chromium`, both removed after use via `npm uninstall playwright`; `git checkout -- package-lock.json` discarded incidental lockfile metadata churn from a newer local npm version) against the rebuilt `talentpilot-ui` container: full flow verified end-to-end as HR Admin (`rita@sails.example.com`) — see Task 4 for the detailed step-by-step trace. Three screenshots captured locally (loaded state with the button+hint, popover open with the one listed entry, drill-down modal open at `/hr/dashboard?assignmentId=...` visible over the grid's Loading skeleton).

### Completion Notes List

- Zero backend changes, exactly as scoped — `EmployeeSegmentationResponse.needs_attention` (Story 9.2) already carried everything the popover needed; this story only reads a field Story 9.3 had fetched but never used.
- New local `NeedsAttentionControl` component in `SkillAssignmentDashboard.tsx`: count-gated between Story 9.3's original plain `LegendRow` (count === 0) and a new real `<button>` + anchored popover (count > 0), one `<Link>` per `needs_attention` entry (not deduplicated per Employee — deliberately, since each entry carries the specific `assignment_id` its link must target).
- **Real, unanticipated bug found and fixed during implementation (see Task 2's own note):** `ProvenanceDrillDownModal` was only rendered in `DashboardPage.tsx`'s final "grid loaded" branch, not in the Loading/Error/Empty early-return branches. Every deep-linked open starts in the Loading state, so without this fix the popover's own drill-down links would have silently failed to open the modal until the grid's own fetch resolved (and would have never opened at all against a genuinely empty grid). Fixed by hoisting a shared `drillDownModal` JSX const, rendered identically in all four branches — a small, low-risk change (one new const + replacing one existing inline `<ProvenanceDrillDownModal>` usage with a reference to it), not a restructuring of the branches themselves.
- `?assignmentId=` deep-link added to `/hr/dashboard` (`Dashboard.tsx` + `DashboardPage.tsx`), reusing the existing `selectedAssignmentId`/`ProvenanceDrillDownModal` wiring rather than building a second view — mount-only effect opens it once; `onInitialAssignmentConsumed` strips the query param on close via `useSearchParams`/`setSearchParams(..., { replace: true })`, live-verified to leave a clean `/hr/dashboard` URL after the admin closes the modal.
- All 5 ACs covered by automated tests (14 in `SkillAssignmentDashboard.test.tsx`, 2 in `DashboardPage.test.tsx`) plus a full live Playwright pass through the real popover → drill-down flow against seeded real data, reverted afterward to leave the shared dev DB unchanged.
- Zero regressions: 420/420 frontend tests (412 baseline + 8 new), `tsc --noEmit` unchanged at the 31-error baseline, `vite build` clean.

### File List

**Modified:**
- `frontend/src/pages/hr/SkillAssignmentDashboard.tsx` — added `NeedsAttentionControl` (button + anchored popover for count > 0; unchanged plain `LegendRow` for count === 0); replaced the old always-plain Needs Attention row usage
- `frontend/src/pages/hr/Dashboard.tsx` — added `useSearchParams`-based `?assignmentId=` deep-link read/strip, passed to `DashboardPage`
- `frontend/src/features/dashboard/DashboardPage.tsx` — added `initialAssignmentId`/`onInitialAssignmentConsumed` props; mount-only effect opens the drill-down modal from the deep-link; **bug fix:** hoisted `drillDownModal` as a shared const rendered in all four state branches (previously only in the Loaded branch)
- `frontend/src/tests/SkillAssignmentDashboard.test.tsx` — re-scoped Story 9.3's old always-non-interactive test to the `count === 0` case; added 6 new tests covering the button/popover/Escape/outside-click/item-click/On-Track-In-Progress-inert behavior
- `frontend/src/features/dashboard/DashboardPage.test.tsx` — added a new `describe` block with 2 tests covering `initialAssignmentId`-driven modal open and `onInitialAssignmentConsumed` on close
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — story/epic status tracking
- `_bmad-output/project-context.md` — Story 9.4 entry (required before this story can be marked done, per the Epic 8 retro's blocking gate)

**No changes to:**
- Any backend file (`backend/`) — this story is entirely frontend, consuming a field Story 9.2 already shipped
- `frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx` — reused unmodified, per Scope Note 3
- `frontend/src/components/layout/HrAppShell.tsx` — nav wiring is Story 9.5's scope, deliberately untouched
- `frontend/src/components/ui/dialog.tsx` — read as a close-behavior precedent only, not modified or reused directly (this popover is non-modal, built locally instead)

## Change Log

- 2026-09-14: Story created (`bmad-create-story`), at user's explicit request to start API + UI development for Story 9.4, referencing the UX design (`06.1-skill-assignment-dashboard.md`) and Story 9.3's shipped page/Dev Notes. Confirmed frontend-only — `EmployeeSegmentationResponse.needs_attention` (Story 9.2) already carries everything the popover needs; Story 9.3 fetched it but never read it, flagging that exact gap in its own Review Findings. Found and resolved the one real judgment call: there is currently no way to open `ProvenanceDrillDownModal` from outside `/hr/dashboard`'s own grid-row click, so satisfying AC1's "link into that Employee's existing... drill-down" requires adding `?assignmentId=` deep-link support to `Dashboard.tsx`/`DashboardPage.tsx` — scoped as reusing/wiring the existing FR-9 view, not building a new one, consistent with epics.md's explicit framing. Also resolved the `needs_attention_count` vs. `needs_attention.length` granularity distinction (one row per flagged Assignment, not per Employee) before it could become an implementation bug.
- 2026-09-14: Implementation complete (`bmad-dev-story`/Amelia, same session as creation). All 4 tasks done: `NeedsAttentionControl` (button + anchored popover, local to `SkillAssignmentDashboard.tsx`) for count > 0, unchanged plain row for count === 0; `?assignmentId=` deep-link wiring added to `Dashboard.tsx`/`DashboardPage.tsx`, reusing the existing `ProvenanceDrillDownModal` unmodified. **Real bug found and fixed, not anticipated at story-creation time:** the drill-down modal was only ever rendered in `DashboardPage.tsx`'s final "grid loaded" branch — every deep-linked open starts in the Loading state (and a genuinely empty grid never reaches that branch at all), so without a fix the popover's own links would have silently failed to open the modal on first navigation. Fixed by hoisting a shared `drillDownModal` const rendered in all four state branches. 8 new/modified tests, all passing; zero regressions (420/420 frontend, `tsc --noEmit` unchanged at 31 pre-existing errors, `vite build` clean, 537 modules). Live-verified end-to-end via Playwright (installed ad hoc, fully removed after use) against a freshly rebuilt `talentpilot-ui` container (found 23h stale at session start, matching Story 9.3's own documented trap): seeded one temporary stale self-reported progress row to produce a real Needs Attention flag, walked the full popover-open → Escape-close-and-refocus → outside-click-close → item-click → `/hr/dashboard?assignmentId=...` → drill-down-modal-open-over-the-Loading-skeleton → close-and-URL-cleanup flow with real data, then reverted the seeded row and confirmed the DB back to its original state. Status → `review`.
- 2026-09-14: Code review (`bmad-code-review`, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor, run against the uncommitted diff with this story file as spec context). 0 decision-needed, 4 patches applied, 2 deferred (`deferred-work.md`), 13 dismissed as non-issues after verification. **Most consequential finding** (Blind Hunter, independently corroborated by a new regression test): `drillDownModal` was rendered at an inconsistent child position across `DashboardPage.tsx`'s four state branches — right after `toastElement` in Loading/Error/Empty, but much later (near `DeleteAssignmentModal`) in the Loaded branch — so React's positional reconciliation unmounted and remounted `ProvenanceDrillDownModal` on the realistic Loading→Loaded transition every deep link goes through, discarding its already-fetched data and re-firing `getDrillDown`. This directly undermined this story's own earlier bug fix (Task 2) without any test catching it, since both original deep-link tests mocked an empty grid (`assignments: []`), which happens to keep the modal at a matching position across Loading→Empty. Fixed by rendering `drillDownModal` at the same position in all four branches; a new regression test asserts `getDrillDown` is called exactly once across a real Loading→Loaded transition with non-empty rows. Three other patches: added `max-h-80 overflow-y-auto` to the popover panel (previously unbounded, could overflow the viewport); added `aria-controls`/`id` association between the trigger button and the popover panel (previously `aria-haspopup`/`aria-expanded` existed with no programmatic link to what they controlled); wrapped the popover link's `assignment_id` in `encodeURIComponent()` (defensive hardening, low risk since it's a UUID). Two low-severity items deferred (`onInitialAssignmentConsumed` firing on every close, not just the deep-linked one; the mount-only deep-link effect silently ignoring in-place query-param changes) — both real but non-blocking, already safely guarded or documented as deliberate trade-offs. Two Blind Hunter findings (changelog entries reading as unfilled placeholders; log entries "out of order") were verified false — artifacts of the reviewer's own diff-construction step trimming long narrative lines to shorten the review prompt, not the real tracked-file content. Full regression re-verified: frontend 421/421 (412 baseline + 9 tests, up from 8), `tsc --noEmit` unchanged at 31 pre-existing errors, `vite build` clean. Status → `done`.
