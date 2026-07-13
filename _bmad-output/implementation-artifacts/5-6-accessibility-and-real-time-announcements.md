---
story_key: 5-6-accessibility-and-real-time-announcements
epic: 5
story_num: 6
dependencies:
  - 5-1-assignment-dashboard-grid-status-badge-display
  - 5-2-provenance-drill-down-modal-trust-detail-and-raw-data
  - 5-4-dashboard-auto-update-live-row-refresh-on-watch-progress
  - 3-5-assignment-creation-and-immediate-dashboard-appearance
baseline_commit: f484550
---

# Story 5.6: Accessibility & Real-Time Announcements

Status: done

**Epic:** 5 (Readiness Dashboard — Status, Provenance, Auto-Update & Override)
**Story ID:** 5.6
**Functional Requirements:** none new — this is a cross-cutting a11y pass over FR-8/FR-9/FR-1's existing UI, binding NFR-A1 (WCAG 2.1 AA), NFR-A2 (never color-only), NFR-A3 (keyboard-operable end-to-end), NFR-A4 (dynamic updates announced), UX-DR24
**Architecture Rules:** none new — no backend, no data model, no new module

This is **not a new-UI story**. It is a verification-and-close-gaps pass over five already-shipped files: `StatusBadge.tsx`, `DashboardRow.tsx`, `DashboardPage.tsx`, `ProvenanceDrillDownModal.tsx`, `toast.tsx`. Three of this story's six AC bullets are **already built** by earlier stories (verify only); three are **real, confirmed gaps** found by reading the current code, not by assuming the epic text is unmet. Do not rebuild anything already working — see Findings below for exactly what's done vs. missing.

**No WDS prototype equivalent exists for this story** (verified: no accessibility/aria story exists anywhere under `_bmad-output/E-Development/`) — do not search for one. The visually-adjacent UX docs `_bmad-output/C-UX-Scenarios/01-ritas-trust-call/01.1-assignment-dashboard.md` and `01.2-provenance-drill-down.md` are **pre-pivot/stale** per the implementation-readiness report (Status-badge-in-drilldown vs. current Provenance-in-drilldown model) — `epics.md`'s Story 5.6 AC text (lines 1950-1973) is authoritative for all wording and behavior in this story, not those docs.

---

## User Story

As a **developer**,
I want to ensure the dashboard is fully keyboard-operable and announces dynamic updates,
So that HR Admins using assistive technology have full access.

---

## ⚠️ Critical Pre-Implementation Findings (read before coding)

Found by reading the actual current code (`StatusBadge.tsx`, `DashboardRow.tsx`, `DashboardPage.tsx`, `ProvenanceDrillDownModal.tsx`, `Dialog.tsx`, `Toast.tsx`, `Dashboard.tsx`, `AssignmentModal.tsx`) and cross-checking against every AC bullet in epics.md:1950-1973.

### Finding 1 — Three of six AC bullets are already done; verify, don't rebuild

- **Keyboard navigation (buttons):** `DashboardRow.test.tsx` already proves Tab-reachability + Enter/Space activation on `[View Details]`. Pagination buttons (`DashboardPage.tsx:356-371`) are plain `<button>` elements — natively Tab/Enter/Space operable, no change needed.
- **Drill-down modal focus-on-open + Escape-to-close:** `Dialog.tsx` (Story 3.4) already moves focus to the panel on open (`panelRef.current?.focus()`, line 39) and closes on Escape (line 42-45), restores focus to the trigger on close (line 68). `ProvenanceDrillDownModal.tsx` already renders a stable `<h2 id={titleId}>` in every branch (loading/error/confirming/loaded) so `aria-labelledby` always resolves — this was itself a Story 5.2 code-review fix, already correct. **Only gap:** the AC says focus moves to "the modal title" specifically; today focus lands on the dialog panel (`tabIndex={-1}` div), not the `<h2>` itself. Verify whether a screen reader announces the `aria-labelledby` title text when the panel receives focus (it should, per WAI-ARIA APG dialog pattern — `aria-labelledby` is announced regardless of which element inside the dialog holds focus) before treating this as a gap; if verified working as-is, this is a **verify-only** item, not a code change.
- **Dynamic-update aria-live announcements:** `DashboardPage.tsx` already has a live `aria-live="polite"` region (`liveRegion`, lines 222-226) firing the exact wording `"{Employee} {Skill} status updated to {Status}"` (`describeChanges()`, lines 45-49) — built early into Story 5.4 specifically because Story 5.4's own dev-story pass found this story's AC (still `backlog` at the time) specified the identical wording, and the user chose to build it there rather than twice. **Correction during implementation: this story's own pre-implementation grep for test coverage was itself wrong** — `DashboardPage.polling.test.tsx` already contains real, passing test coverage for this exact behavior (`"announces a live Status change via an aria-live region, using Story 5.6's exact wording"` and a companion no-op-poll test), driven through the real `pollDashboard`/`diffAssignments`/`describeChanges` implementation via `vi.advanceTimersByTimeAsync()` (a real fake-timer-advanced `setInterval`, not a mocked stand-in for the polling mechanism). Verified passing as-is; no new test needed, no code change.

### Finding 2 — Real gap: Status badge is not focusable, so "Status badge focus" (AC2) cannot fire at all

`StatusBadge.tsx` renders a bare `<span role="status" aria-label={label}>` with no `tabIndex`. A `<span>` with no `tabIndex` is never in the Tab order — a screen reader user can never land keyboard focus on it, so the AC's "When focus lands on a Status badge, the screen reader announces..." literally cannot happen today. Additionally, the current `aria-label` is just `label` (e.g. `"In Progress (45%)"`) — it does not include Employee/Skill, but the AC's required announcement text is `"{Employee} {Skill}: {Status} {watch percentage if applicable}"`. Two fixes needed together:
1. Add `tabIndex={0}` to the badge's `<span>` so it enters the Tab order.
2. `StatusBadge` currently has no knowledge of employee/skill name — it is called from two sites (`DashboardRow.tsx:18` and `ProvenanceDrillDownModal.tsx:189`). Add an optional `employeeName`/`skillName` prop pair to `StatusBadgeProps`; when both are provided, build `aria-label` as `"{Employee} {Skill}: {Status} {percentage text}"`; when absent (drill-down call site, where the header `<h2>` already states Employee/Skill — adding it again to the badge would be redundant/confusing for a screen reader reading the header then the badge back-to-back), fall back to today's `label`-only behavior. Pass `row.employee_name`/`row.skill_name` from `DashboardRow.tsx` only.

**Scope decision — "rows...reachable via Tab" (AC1):** interpreted as "every interactive element within a row is reachable," not "the `<tr>` itself is a tab stop." Making a non-interactive `<tr>` focusable would add a keyboard trap with no associated action, which WAI-ARIA APG guidance advises against. With Finding 2's fix, each row now has two Tab stops (Status badge, View Details button) plus grid-wide Previous/Next — this satisfies the AC's intent. Do not add `tabIndex` to `<tr>`.

### Finding 3 — Real gap: errors are not announced (AC: "Errors are announced immediately")

Neither `DashboardPage.tsx`'s fetch-error branch (lines 259-280, plain `<div>` text) nor `ProvenanceDrillDownModal.tsx`'s two error surfaces (fetch-error branch lines 132-145, `submitError` in the confirm view line 162) use `role="alert"` or `aria-live="assertive"`. Confirmed via `DashboardPage.test.tsx` — its existing "shows error state when fetch fails" test (line 165) only asserts the error text renders, never asserts it's announced. Fix: add `role="alert"` to the error message element in both places (a native ARIA live region — no wrapper needed, and `role="alert"` implies `aria-live="assertive"` + `aria-atomic="true"` per spec, appropriate here since these are genuine failures the AC says must interrupt, unlike the polite success/update announcements). Do **not** add `role="alert"` to `Toast.tsx` — it is success-only (Story 3.5's `role="status"`/`aria-live="polite"` is correct for that use case) and is out of this story's error-announcement scope.

### Finding 4 — Real gap: FR-1 success toast never fires on the real (non-stub) dashboard route

The AC requires: `"Success toast (FR-1): Announced as: 'Skill assigned to {Employee} — {Skill name}'"`. That exact copy (with a `✓ ` prefix) **was built** — but only in `DashboardStub.tsx` (Story 3.5), which `App.tsx` no longer routes anywhere (the `/hr/dashboard` route points at `Dashboard.tsx` / `DashboardPage.tsx`, Story 5.1's real grid — `DashboardStub` is now dead, unrouted code). `Dashboard.tsx`'s current `AssignmentModal onAssigned` handler (line 73-76) only calls `dashboardRef.current?.refreshGrid()` — it never shows a toast. Verified via grep: no test anywhere asserts a "Skill assigned to..." toast fires from the real `/hr/dashboard` route. **This is the story's real new-code task**, not a rebuild:
1. `AssignmentModal`'s `onAssigned` callback already provides `(assignment, employeeName, skillName)` (`AssignmentModal.tsx:52`) — Dashboard.tsx already receives these, just isn't using employeeName/skillName today.
2. `DashboardPage`'s `toastMessage` state and `<Toast>` render are already internal/private to `DashboardPage.tsx` (used today only for Story 5.5's Mark-as-Ready confirmation via `onOverrideChanged`). Extend `DashboardPageHandle` (currently just `{ refreshGrid: () => void }`, line 55-57) with a second method, e.g. `announceToast: (message: string) => void`, implemented via the same `useImperativeHandle` already in place (line 85-87), calling the existing internal `setToastMessage`.
3. In `Dashboard.tsx`'s `onAssigned`, build the message as `` `✓ Skill assigned to ${employeeName} — ${skillName}` `` (matches the exact tested copy pattern already established and shipped in `DashboardStub.tsx`/`Toast.test.tsx` — reuse it verbatim rather than inventing new wording) and call `dashboardRef.current?.announceToast(message)` alongside the existing `refreshGrid()` call.
4. `DashboardStub.tsx` itself is out of scope — it's dead code (no route references it) but deleting unrelated dead code is not this story's job; leave it as-is unless the checklist flags it as a blocker.

### Finding 5 — Real gap: the Last Updated column's own AC (Story 5.1) was never built, and Story 5.6's "stale rows" AC needs it

Story 5.1's own AC text (epics.md:1633) specifies: *"For Self-reported data over 7 days stale: this column is red/highlighted to hint at Needs Attention (secondary visual cue for OQ11)"* — this was **never implemented**; `DashboardRow.tsx`'s Last Updated `<td>` (lines 25-27) has zero conditional styling of any kind. Story 5.6's own AC (epics.md:1971) requires: *"Stale rows have text ('Not updated in X days') in addition to any color highlighting"* — today there is neither the color highlighting Story 5.1 specified nor the text this story requires, so this is the one place in the story where you're closing a **pre-existing cross-story gap**, not just adding a11y semantics to already-visible content. Backend support already exists — no backend change needed: `AssignmentRow.provenance` (`types/dashboard.ts:21`) is already populated server-side via `ProgressService.get_provenance_detail()` (confirmed via `backend/app/dashboard/service.py:73-147`), and is `"Needs Attention"` exactly when Story 5.3's 7-day staleness threshold is exceeded. Implementation: in `DashboardRow.tsx`, when `row.provenance === "Needs Attention"`, render the Last Updated cell with a red/highlighted style (e.g. `text-red-700 font-medium`, consistent with the drill-down modal's existing `text-amber-700` treatment for the same state in `ProvenanceDrillDownModal.tsx:252`) **and** append literal stale-day text, e.g. `"3 days ago (Not updated in 3 days)"` — reuse the exact `differenceInCalendarDays(new Date(), new Date(row.last_updated))` pattern already established in `ProvenanceDrillDownModal.tsx:249` for computing the day count, and the exact `"Not updated in X day(s)"` phrasing epics.md:1971/1711 both specify verbatim (singular/plural via the same `staleDays === 1 ? "" : "s"` ternary already used at line 256).

---

## Acceptance Criteria

Copied verbatim from epics.md:1950-1973 (Story 5.6) — this is the authoritative source; do not substitute wording from the stale UX docs named above.

1. **Keyboard navigation:** All buttons, rows, and controls are reachable via Tab key; Enter/Space activates buttons. *(Verify: DashboardRow button — done. New: Status badge — Finding 2.)*
2. **Status badge focus:** When focus lands on a Status badge, the screen reader announces: `"{Employee} {Skill}: {Status} {watch percentage if applicable}"`. *(New — Finding 2.)*
3. **Drill-down modal:** Opens with focus moved to the modal title; can be closed via Escape key. *(Verify — Finding 1; confirm `aria-labelledby` announcement behavior, no code change expected.)*
4. **Dynamic updates:** When a row's Status changes due to polling, an `aria-live` region announces: `"{Employee} {Skill} status updated to {Status}"`. *(Verify — already built in Story 5.4; add missing test coverage.)*
5. **Success toast (FR-1):** Announced as: `"Skill assigned to {Employee} — {Skill name}"`. *(New — Finding 4; wire into the real `/hr/dashboard` route, which currently shows no toast at all.)*
6. **Errors:** Error messages are announced immediately. *(New — Finding 3; `role="alert"` on DashboardPage + ProvenanceDrillDownModal error surfaces.)*

**And** color is never the only way to convey information (NFR-A2):
7. Status badges have text labels. *(Already true — `StatusBadge.tsx` always renders `{label}` text alongside the icon; verify only.)*
8. Provenance labels have text labels. *(Already true — every branch of `ProvenanceSection` in `ProvenanceDrillDownModal.tsx` renders a text label; verify only.)*
9. Stale rows have text ("Not updated in X days") in addition to any color highlighting. *(New — Finding 5; the grid currently has neither the color nor the text.)*

---

## Tasks / Subtasks

- [x] **Task 1 — StatusBadge: focusable + full announcement text (AC1, AC2; Finding 2)**
  - [x] Add `tabIndex={0}` to the badge `<span>` in `StatusBadge.tsx`
  - [x] Add optional `employeeName?: string` / `skillName?: string` props to `StatusBadgeProps`
  - [x] When both provided, build `aria-label` as `` `${employeeName} ${skillName}: ${label}` ``; otherwise keep today's `label`-only behavior
  - [x] Pass `employeeName={row.employee_name}` / `skillName={row.skill_name}` from `DashboardRow.tsx`'s `<StatusBadge>` call — leave `ProvenanceDrillDownModal.tsx`'s call site unchanged (header already states Employee/Skill)
  - [x] Update `StatusBadge.test.tsx`: add a case asserting `aria-label` includes employee+skill when both props are passed, and a case asserting the badge is in the Tab order (`tabIndex={0}` or real `userEvent.tab()` traversal, matching `DashboardRow.test.tsx`'s existing real-Tab-traversal pattern)
  - [x] **Regression found and fixed**: `DashboardRow.test.tsx`'s existing "reachable via real Tab-key traversal" test assumed the View Details button was the row's first Tab stop — the new Status badge Tab stop is now reached first. Updated the test to tab twice (badge, then button) rather than leave it silently broken.

- [x] **Task 2 — Errors announced immediately (AC6; Finding 3)**
  - [x] `DashboardPage.tsx`: add `role="alert"` to the error message element in the error-state branch (lines 259-280)
  - [x] `ProvenanceDrillDownModal.tsx`: add `role="alert"` to the fetch-error `<p>` (line 137) and the `submitError` `<p>` in the confirm view (line 162)
  - [x] Add/extend tests in `DashboardPage.test.tsx` and `ProvenanceDrillDownModal.test.tsx` asserting `role="alert"` (or `screen.getByRole("alert")`) is present when each error surfaces

- [x] **Task 3 — Success toast wired into the real dashboard route (AC5; Finding 4)**
  - [x] Extend `DashboardPageHandle` in `DashboardPage.tsx` with `announceToast: (message: string) => void`, implemented in the existing `useImperativeHandle` block calling internal `setToastMessage`
  - [x] `Dashboard.tsx`: in `AssignmentModal`'s `onAssigned`, build `` `✓ Skill assigned to ${employeeName} — ${skillName}` `` and call `dashboardRef.current?.announceToast(message)` alongside the existing `refreshGrid()` call
  - [x] Add a test (new file or extend `DashboardPage.test.tsx`) proving `announceToast` renders the `Toast` with the expected message via the ref handle — mirror the existing `refreshGrid` ref-handle test pattern if one exists, otherwise a minimal `ref.current.announceToast(...)` + `screen.getByRole("status")` assertion

- [x] **Task 4 — Stale-row visual + text treatment on the grid (AC9; Finding 5)**
  - [x] `DashboardRow.tsx`: when `row.provenance === "Needs Attention"`, apply a red/highlighted class to the Last Updated `<td>` and append `` `(Not updated in ${staleDays} day${staleDays === 1 ? "" : "s"})` `` to its text, computed via `differenceInCalendarDays(new Date(), new Date(row.last_updated))` (already imported pattern from `date-fns`, mirrors `ProvenanceDrillDownModal.tsx:249`)
  - [x] Add test cases to `DashboardRow.test.tsx`: a `"Needs Attention"` row shows the red/highlighted style + "Not updated in X days" text; a non-stale row (`"Verified"`/other provenance) shows neither

- [x] **Task 5 — Verification-only items, no code change expected unless disproven (AC1 buttons, AC3, AC4, AC7, AC8)**
  - [x] Confirm `DashboardRow.test.tsx`'s existing Tab/Enter/Space coverage for `[View Details]` still passes unmodified — passes (7/7), extended by Task 1's own new badge-Tab-stop test
  - [x] Confirm `Dialog.tsx`'s focus-on-open + Escape-to-close behavior via a screen-reader-shaped test (assert `document.activeElement` lands inside the panel and `aria-labelledby` resolves to the visible title text) in `ProvenanceDrillDownModal.test.tsx` — new test added and passing; confirmed **verify-only, no gap, no code change** — `aria-labelledby` correctly resolves to the visible title text
  - [x] **Correction: the "missing `aria-live` test" this task planned to add already exists.** `DashboardPage.polling.test.tsx` (lines 180-209) already has real, passing coverage — `"announces a live Status change via an aria-live region, using Story 5.6's exact wording"` plus a no-op-poll companion test — driven through the actual `pollDashboard`/`diffAssignments`/`describeChanges` via `vi.advanceTimersByTimeAsync()`, not a mocked stand-in. This story's own pre-implementation grep (Finding 1) was wrong; corrected in Finding 1 above. Re-ran (7/7 passing); no new test added, no code change.
  - [x] Confirm `StatusBadge.test.tsx`'s existing text-label assertions (AC7) and `ProvenanceDrillDownModal.test.tsx`'s existing Provenance-label text assertions (AC8) remain green — both pass (7/7, 25/25 respectively); no gap, no new tests needed

- [x] **Task 6 — Full regression pass**
  - [x] `npx tsc --noEmit` diffed against a `git stash` baseline — 85 lines both before and after, normalized-diff **byte-identical**, confirming zero new type errors. **Caught and fixed one real regression during this pass**: a new test (`role="alert"` fetch-error test) reused an existing pre-existing-bug pattern (`render(<DashboardPage />)` omitting the required `onNewAssignment` prop) and produced one *new occurrence* of that pre-existing error class — fixed immediately by passing the prop, per this project's established convention (Story 5-5's identical fix).
  - [x] Full frontend test suite run — 222/224 passing; the same 2 pre-existing unrelated failures ("renders loading state on mount", "pagination shows correct page numbers and total") confirmed via `git stash` comparison to be identical before/after this story's changes, unchanged since Story 5.4/5.5
  - [x] `npm run build` fails at its `tsc` step on the same pre-existing unrelated errors (not this story's changes) — `npx vite build` used instead as this project's established build-verification proxy (Story 2.5/2.6 precedent); clean, 512 modules transformed, no errors

### Review Findings

_Code review run 2026-07-13 (`bmad-code-review`), 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor. Findings merged/verified against source before rating (not rated from diff hunks alone); 5 dismissed as spec-mandated behavior, informational-only, or already-correct positive confirmations._

- [x] [Review][Decision] ~~`StatusBadge`'s `role="status"` may double-announce alongside `DashboardPage.tsx`'s dedicated `aria-live` region~~ — **Resolved 2026-07-13 (user decision): mute the badge's own live-region semantics.** AC2 (focus lands → announce) doesn't require `role="status"` at all — any focusable element with `aria-label` is announced on focus regardless of live-region role. **Fixed**: added `aria-live="off"` to the badge's `<span>`, muting its implicit live-region behavior while keeping `role="status"` (so existing `getByRole("status")` test queries are unaffected) and `tabIndex`+`aria-label` for AC2's focus-driven announcement. [`frontend/src/components/StatusBadge.tsx:60-70`]

- [x] [Review][Decision] ~~AC5 toast includes an unauthorized `"✓ "` prefix not in epics.md:1965's literal wording~~ — **Resolved 2026-07-13 (user decision): strip the prefix, match epics.md literally.** Per this project's own convention, epics.md's literal AC text is authoritative over the dead/unrouted `DashboardStub.tsx` precedent that had justified the prefix. **Fixed**: toast text is now exactly `Skill assigned to {Employee} — {Skill name}`; `DashboardPage.test.tsx`'s AC5 test updated to match. [`frontend/src/pages/hr/Dashboard.tsx:73-80`, `frontend/src/features/dashboard/DashboardPage.test.tsx:389-400`]

- [x] [Review][Patch] `DashboardRow.tsx`'s new `staleDays` computation has no guard against a future `last_updated` (clock skew → negative day count, e.g. "Not updated in -1 days") and shows the self-contradictory "(Not updated in 0 days)" when `staleDays === 0` — copies a pre-existing unguarded pattern from `ProvenanceDrillDownModal.tsx`'s "Needs Attention" branch into a second location instead of fixing or centralizing it. **Fixed**: extracted a shared `staleDaysSince()` helper (`Math.max(0, differenceInCalendarDays(...))`, closing the negative-count gap in both files at once — see the DRY patch below) and suppressed the day-count suffix entirely when `staleDays === 0`. 2 new tests added (`DashboardRow.test.tsx`: 0-day suppression, future-timestamp clamping). [`frontend/src/features/dashboard/DashboardRow.tsx:13-19,46-47`, `frontend/src/lib/utils/staleness.ts`]

- [x] [Review][Patch] `Dialog.tsx`'s Tab/Shift+Tab focus-trap wrap order inside `ProvenanceDrillDownModal` now includes the newly-focusable `StatusBadge` (matches `FOCUSABLE_SELECTOR`'s `[tabindex]:not([tabindex="-1"])`), changing Story 5.2's established cycle (badge is now the first/wrap-to element instead of the first button) — the trap algorithm generalizes correctly to the extra element (verified by reading `dialog.tsx`'s first/last-element logic, not just assumed), so this is very likely not broken, but zero test currently verifies Tab/Shift+Tab wrapping inside the modal with the new element present. **Fixed**: added a real Tab/Shift+Tab traversal test asserting the full forward cycle (badge → Mark as Ready → Close → wraps to badge) and the backward wrap (Shift+Tab from badge → Close) — confirmed the trap genuinely still works correctly with the extra element, not just assumed. [`frontend/src/features/dashboard/ProvenanceDrillDownModal.test.tsx:368-392`]

- [x] [Review][Patch] Duplicated day-count/singular-plural formatting logic (`differenceInCalendarDays` + `staleDays === 1 ? "" : "s"` ternary) now lives in both `DashboardRow.tsx` and `ProvenanceDrillDownModal.tsx` instead of a shared helper — the clock-skew/zero-day guard above would need to be applied twice. **Fixed**: extracted `frontend/src/lib/utils/staleness.ts` (`staleDaysSince()`, `formatStaleDaysText()`), following this codebase's existing `lib/utils/duration.ts` precedent. `DashboardRow.tsx` uses both; `ProvenanceDrillDownModal.tsx`'s "Needs Attention" branch reuses `staleDaysSince()` for the day-count (its sentence structure differs from `DashboardRow.tsx`'s, so `formatStaleDaysText()` isn't a fit there — only the duplicated *computation*, the actual bug-bearing logic, needed centralizing). [`frontend/src/lib/utils/staleness.ts`, `frontend/src/features/dashboard/DashboardRow.tsx:1-4`, `frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx:1-7,260-264`]

- [x] [Review][Patch] Stale/misleading comment on `toastElement` in `DashboardPage.tsx` still says "Story 5.5: success toast after a Mark-as-Ready confirm" but this diff repurposes the same element for Story 5.6's unrelated assignment-created toast. **Fixed**: comment updated to describe both current callers (Story 5.5 override-confirm, Story 5.6 assignment-created). [`frontend/src/features/dashboard/DashboardPage.tsx:232-238`]

- [x] [Review][Defer] `role="alert"` may not reliably announce when content is present at first mount (e.g. the very first fetch fails on load, so the alert element and its text appear in the same paint) or when identical error text repeats on a second failure (no DOM mutation to trigger re-announcement) [`frontend/src/features/dashboard/DashboardPage.tsx:277`, `frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx:148,174`] — deferred, genuine ARIA/AT timing nuance not verifiable in jsdom, applies broadly to conditionally-mounted alert regions across the whole app, not unique to this diff.

- [x] [Review][Defer] `StatusBadge`'s `employeeName`/`skillName` props are independently optional with no pairing guard — passing only one would silently degrade to the status-only label [`frontend/src/components/StatusBadge.tsx:11-13`] — deferred, unreachable via the only current call site (`DashboardRow.tsx` always supplies both from `AssignmentRow`'s non-nullable `employee_name`/`skill_name` string fields).

- [x] [Review][Defer] `announceToast("")` is silently swallowed by `Toast`'s `if (!message) return null` [`frontend/src/features/dashboard/DashboardPage.tsx:90`, `frontend/src/components/ui/toast.tsx:33`] — deferred, unreachable via the only current call site (`Dashboard.tsx`'s templated string is never empty).

- [x] [Review][Defer] The shared `Toast` primitive has no message queueing — a rapid second `announceToast`/toast call before the first message's 4s timer elapses overwrites it, cutting the first announcement short [`frontend/src/pages/hr/Dashboard.tsx:79`, `frontend/src/features/dashboard/DashboardPage.tsx:90`] — deferred, systemic pre-existing `Toast` limitation since Story 3.5 (already logged once for a related reason in Story 5.5's own deferred findings); this diff adds a second caller sharing the same single-slot state but doesn't introduce the underlying limitation.

- [x] [Review][Defer] `diffAssignments`'s `!before` branch announces any row newly visible in a poll snapshot (pagination drift, re-sort) as if its Status changed, even when it didn't [`frontend/src/features/dashboard/DashboardPage.tsx:29-40`] — deferred, pre-existing Story 5.4 code, untouched by this diff.

- [x] [Review][Defer] `describeChanges` has no cap on concatenated multi-row change sentences — a poll tick touching many rows at once produces one unbounded `join(". ")` string [`frontend/src/features/dashboard/DashboardPage.tsx:45-49`] — deferred, pre-existing Story 5.4 code, untouched by this diff.

### Review Findings — Round 2

_Re-review run 2026-07-13 (`bmad-code-review`, user-requested), 3 fresh adversarial layers instructed not to assume round 1's patches were correct — Blind Hunter, Edge Case Hunter, Acceptance Auditor. Two layers independently converged on the same real regression introduced by round 1's own "0-day suppression" patch. 1 decision-needed, 7 patches, 5 deferred, 5 dismissed._

- [x] [Review][Decision] ~~Round 1's toast-wording resolution was made on incomplete information — epics.md itself has a 3-way conflict this review missed until now~~ — **Resolved 2026-07-13 (user decision): checkmark + first name, matching UX-DR12 (epics.md:157) + Story 3.5's own AC (epics.md:1247) + the original `DashboardStub.tsx` implementation exactly.** Treated as the better-supported reading (2 corroborating citations including the story that originated this feature) vs. Story 5.6's own AC (epics.md:1965), read as an imprecise paraphrase written while focused on accessibility/keyboard mechanics rather than copy fidelity. Converted to patch below. [`frontend/src/pages/hr/Dashboard.tsx:79`, `_bmad-output/planning-artifacts/epics.md:157,1247,1965`]

- [x] [Review][Patch] **Real NFR-A2 regression introduced by round 1's own "0-day suppression" fix (found independently by 2 of 3 layers).** `DashboardRow.tsx`'s red/bold highlight is driven by `isStale` (`row.provenance === "Needs Attention"`) alone, unconditionally — but round 1's fix suppresses the paired `"(Not updated in X days)"` text whenever `staleDays === 0`, leaving a state where the row is **color-highlighted with zero accompanying text**, a literal violation of epics.md:1971 ("Stale rows have text ... in addition to any color highlighting") and this diff's own NFR-A2 mandate. Round 1's own reasoning ("`(Not updated in 0 days)` is self-contradictory... the relative-time text alone already conveys freshness") was backwards: the relative-time text conveys freshness, not the staleness the red highlight asserts — suppressing the day-count leaves color as the sole signal in that state, the exact thing AC9 exists to prevent. **Fixed**: `formatStaleDaysText()` now returns distinct, non-blank wording at 0 days ("Not updated today") instead of the day-count text being conditionally hidden — text is now unconditionally paired with the color highlight. 2 tests rewritten to assert the new text (not absence), 1 new test added for the future-timestamp clamp using a 3-day offset (the old 1-hour-offset test didn't reliably exercise the clamp — see the `staleDaysSince()` patch below). [`frontend/src/features/dashboard/DashboardRow.tsx:14-22,42-43`, `frontend/src/lib/utils/staleness.ts:15-22`]

- [x] [Review][Patch] `staleDaysSince()` has no guard against an invalid/unparseable `last_updated` — `differenceInCalendarDays` on an invalid `Date` returns `NaN`, and `Math.max(0, NaN)` is `NaN`, which would propagate as literal "NaN days" into both `DashboardRow.tsx` and `ProvenanceDrillDownModal.tsx`. **Fixed**: `isNaN(date.getTime())` guard added, returns `0` for any unparseable/empty date string. [`frontend/src/lib/utils/staleness.ts:9-14`]

- [x] [Review][Patch] `ProvenanceDrillDownModal.tsx`'s "Needs Attention" branch has no equivalent guard for `staleDays === 0` — will render the same self-contradictory "This status hasn't been updated in 0 days..." wording round 1's `DashboardRow.tsx` fix was written to eliminate, just in the other consumer of the newly-shared helper. **Fixed**: added a matching `staleDays === 0` branch rendering "This status hasn't been updated today." instead (sentence structure differs from `DashboardRow.tsx`'s bracketed suffix, so the shared `formatStaleDaysText()` wasn't reused verbatim here — only the underlying day-count computation is shared, consistent with round 1's original DRY-scope decision). [`frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx:271-275`]

- [x] [Review][Patch] The Tab/Shift+Tab wrap-order test added in round 1 only exercises `baseResponse()`'s default `provenance: "Not Started"`, where `[Mark as Ready]` is present (3 focusable elements: badge, Mark as Ready, Close). For `provenance: "HR Override"`, that button is omitted (`ProvenanceDrillDownModal.tsx:210-217`), leaving only 2 focusable elements (badge, Close) — the wrap order for that state is real, different, and currently unverified. **Fixed**: added a second Tab-wrap test for `provenance: "HR Override"`, asserting the 2-element cycle (badge ↔ Close) independently. [`frontend/src/features/dashboard/ProvenanceDrillDownModal.test.tsx:395-417`]

- [x] [Review][Patch] `frontend/src/lib/utils/staleness.ts` has no dedicated unit test file — all coverage of `staleDaysSince()`/`formatStaleDaysText()` is indirect through `DashboardRow.test.tsx` (whose "clamps a future timestamp" test doesn't actually exercise the clamp, since `DashboardRow`'s own `staleDays > 0` display gate suppresses negative and clamped-zero values identically — confirmed: the test still passes with `Math.max(0, ...)` deleted) and one `ProvenanceDrillDownModal.test.tsx` case (14 days, plural only). **Fixed**: new `frontend/src/lib/utils/staleness.test.ts` (8 tests) directly proving the clamp, the NaN guard, and both `formatStaleDaysText()` branches (0/1/2+) in isolation.

- [x] [Review][Patch] Zero test coverage exists for `StatusBadge.tsx`'s new `aria-live="off"` attribute — the entire round-1 fix for the double-announcement risk (this review's own headline finding from round 1) has no regression test; a future refactor could delete the attribute silently. **Fixed**: new test asserting `aria-live="off"` on the badge. [`frontend/src/components/StatusBadge.test.tsx`]

- [x] [Review][Defer] `aria-live="off"`'s real-world effectiveness at overriding `role="status"`'s implicit live-region behavior across actual screen readers/browsers isn't verifiable in jsdom — the ARIA spec supports it (explicit `aria-live` overrides a role's implicit default), but AT/browser support nuances for this specific override aren't confirmable in CI. Same class of untestable-in-automation limitation as round 1's `role="alert"` timing defer.

- [x] [Review][Defer] `tabIndex={0}` on `StatusBadge` is, per strict WCAG 2.4.3/4.1.2 auditing conventions, a "focusable element with no keyboard-operable action" anti-pattern (Tab lands on it, Enter/Space do nothing) — duplicated once per grid row. This is an inherent tradeoff of satisfying AC2's literal requirement (focus-driven announcement) as already explicitly scoped in this story's own Finding 2/Scope decision; not fixable without abandoning the AC itself.

- [x] [Review][Defer] `role="status"` is now shared, ambiguously, by both `StatusBadge` and `Toast` — a future test combining a populated grid (badges) with an open toast in the same render would hit `screen.getByRole("status")` throwing on multiple matches. Narrow, hypothetical, test-infrastructure-only; no test in this diff combines both states.

- [x] [Review][Defer] `differenceInCalendarDays`-based staleness can show "(Not updated in 1 day)" for content updated within the last hour if that hour crosses a calendar-day boundary (e.g., 23:30 yesterday → 00:30 today) — a known category of calendar-boundary-vs-elapsed-time imprecision, pre-existing since before this diff (same `differenceInCalendarDays` call existed, just duplicated), inherent to Story 5.3's day-granularity staleness design (`NEEDS_ATTENTION_STALENESS_DAYS`, server-side) — not something the frontend can fix independently of that design.

- [x] [Review][Defer] `role="alert"` combined with `Dialog`'s existing focus management is untested for double-announcement (e.g., does the alert fire exactly once, not picked up by any other live region in the tree) — narrow, matches round 1's already-deferred general `role="alert"`-timing-reliability item; no new information beyond what's already logged there.

---

## Developer Context & Implementation Notes

### `role="status"` vs `role="alert"` — why both exist in this codebase after this story

`Toast.tsx` (success only) correctly uses `role="status"` + `aria-live="polite"` — a success message shouldn't interrupt whatever the screen reader is currently announcing. The new error surfaces (Task 2) use `role="alert"`, which is implicitly `aria-live="assertive"` and interrupts — appropriate because these represent genuine failures the AC explicitly calls "announced immediately" (assertive), distinct from AC4's polite dynamic-update region. Do not swap these two roles between success/error paths.

### Why `StatusBadge`'s new props are optional, not required

Making `employeeName`/`skillName` required would force `ProvenanceDrillDownModal.tsx`'s call site (line 189) to pass them too, producing a doubled announcement (`"{Employee} {Skill}: {Employee} {Skill}: {Status}"` — the modal's `<h2>` already says `{Employee} — {Skill}` right above the badge). Keep them optional; only `DashboardRow.tsx` passes them.

### Closure/staleness patterns already established — reuse, don't reinvent

This codebase has three recurring patterns relevant here if you touch anything stateful: (1) `requestId`/`tokenRef` guards against stale async responses (`DashboardPage.tsx`, `ProvenanceDrillDownModal.tsx`, `AssignmentModal.tsx` all do this) — Task 3's toast wiring is synchronous (no fetch), so this does not apply; (2) `useRef` for a callback read inside an effect with a narrow dependency array (`Dialog.tsx`'s `onCloseRef`, `Toast.tsx`'s `onDismissRef`) — not needed for this story's changes, which are all synchronous render-time or event-handler code; (3) fake-timer tests must `act()` + `advanceTimersByTimeAsync()` rather than `waitFor()` (RTL's `waitFor` doesn't resolve under `vi.useFakeTimers()` — documented in Story 5.4's Dev Agent Record) — relevant only if Task 5's new `aria-live` verification test uses the polling test file's existing fake-timer setup.

---

## Testing Strategy

- All new/changed assertions are frontend-only (`frontend/src/components/StatusBadge.test.tsx`, `frontend/src/features/dashboard/DashboardRow.test.tsx`, `frontend/src/features/dashboard/DashboardPage.test.tsx`, `frontend/src/features/dashboard/DashboardPage.polling.test.tsx`, `frontend/src/features/dashboard/ProvenanceDrillDownModal.test.tsx`). No backend files change, no backend tests needed — every gap closed in this story is presentation-layer only, sourced from data the backend already provides (`provenance`, `employee_name`, `skill_name` are all already on `AssignmentRow`/`DrillDownResponse`).
- Prefer `screen.getByRole(...)` / `userEvent.tab()` / real keyboard events over `.focus()` calls alone, matching `DashboardRow.test.tsx`'s own established "reachable via real Tab-key traversal from the document body, not just button.focus()" precedent (line 61-68) — this project has previously caught real bugs (Story 5.2's Combobox focus-trap regression) that only manifested under real Tab traversal, not synthetic `.focus()`.
- No live-browser/Playwright pass is required for this story specifically (unlike Story 5.4's), since all six AC bullets are unit-testable via RTL's accessibility queries (`getByRole`, `aria-label` assertions) — but if a browser-automation tool is available in the implementation session, a manual screen-reader-shaped smoke pass (Tab through the grid, open drill-down, trigger a poll update) is recommended per the epic-1 retro's live-verification action item, flagged not required.

## Architecture Compliance Checklist

- No backend, database, or module-boundary changes — this story touches only presentation-layer frontend files already covered by AD-6 (server-side gate, unaffected) and AD-3 (single derivation authority — `provenance` is read, never re-derived client-side; Task 4 branches on the existing value, does not compute a new one).
- NFR-A1 (WCAG 2.1 AA), NFR-A2 (never color-only), NFR-A3 (keyboard-operable end-to-end), NFR-A4 (dynamic updates announced) — this story's entire scope.

## Known Issues & Deferrals

- `DashboardStub.tsx` is confirmed dead/unrouted code (Finding 4) — not deleted here, out of scope; flag for a future cleanup story if one is ever scheduled.
- The pre-existing cross-file asyncpg pool-corruption pattern (open since the Epic 4 retro) does not apply — this story touches no backend/DB-test files.
- If Task 5's `Dialog.tsx` focus-on-title verification reveals a real gap (unlikely per WAI-ARIA APG's `aria-labelledby` semantics, but not yet empirically confirmed in this codebase), escalate to a real code task rather than silently downgrading the AC.

## Success Criteria

All 9 AC bullets (3 verify-only, 6 requiring real code/test changes per Findings 2-5) pass with dedicated test coverage; `tsc --noEmit` shows zero new errors vs. baseline; full frontend suite green (pre-existing unrelated failures unchanged); `vite build` clean.

## Dev Notes

- Relevant architecture patterns: none new (see Architecture Compliance Checklist above) — this is the first Epic 5 story with zero backend footprint.
- Source tree components touched: `frontend/src/components/StatusBadge.tsx`, `frontend/src/features/dashboard/DashboardRow.tsx`, `frontend/src/features/dashboard/DashboardPage.tsx`, `frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx`, `frontend/src/pages/hr/Dashboard.tsx`. `frontend/src/components/ui/toast.tsx` itself needs **no changes** — it's already correctly built (Story 3.5); it's referenced in the epic's story list because this story wires its *consumption* into the real route (Finding 4), not because the primitive itself changes.
- Testing standards: this project's existing pattern — real Tab traversal over synthetic focus, `screen.getByRole`, fake-timer `act()+advanceTimersByTimeAsync()` for polling tests, `tsc --noEmit` diffed against `git stash` baseline before claiming "zero new errors."

### Project Structure Notes

- No new files created except test files extending existing `*.test.tsx` siblings (or one new test file if Task 3's ref-handle test doesn't fit cleanly into `DashboardPage.test.tsx`'s existing structure — developer's call, matching this codebase's existing `DashboardPage.polling.test.tsx` precedent of splitting concern-specific test files).
- No routing changes — `/hr/dashboard` already points at the correct component (`Dashboard.tsx`).

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.6, lines 1950-1973] — literal AC text, authoritative.
- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.1, line 1633] — Last Updated column's original (never-built) stale-highlight spec, closed by Task 4.
- [Source: _bmad-output/planning-artifacts/epics.md, lines 96-99, 160-162] — NFR-A1/A2/A3/A4, UX-DR13/14 definitions.
- [Source: frontend/src/features/dashboard/DashboardPage.tsx, lines 42-49, 218-232] — existing aria-live region + wording, built by Story 5.4, verify-only per Finding 1.
- [Source: frontend/src/components/ui/dialog.tsx, lines 35-70] — existing focus-management/Escape-close primitive, verify-only per Finding 1.
- [Source: _bmad-output/implementation-artifacts/5-4-dashboard-auto-update-live-row-refresh-on-watch-progress.md] — Finding 3 origin (aria-live built early, RTL fake-timer `waitFor()` gotcha).
- [Source: _bmad-output/implementation-artifacts/5-5-hr-override-manual-readiness-confirmation.md] — story-file structure/format precedent followed here.

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (claude-sonnet-5), via Amelia/bmad-dev-story

### Debug Log References

None — no blocking failures encountered. Two real, resolved-in-place issues surfaced during implementation:
1. Fixing Task 1 (StatusBadge `tabIndex={0}`) added a second Tab stop to every grid row, breaking `DashboardRow.test.tsx`'s existing single-tab "reachable via real Tab-key traversal" assertion (it assumed `[View Details]` was the row's first Tab stop). Confirmed this was the correct AC1 outcome, not a bug; updated the test to tab twice.
2. Finding 1's claim that no `aria-live` test coverage existed was itself wrong — `DashboardPage.polling.test.tsx` already had full, passing coverage via the real polling mechanism. Verified, corrected the story file, added no duplicate test.

### Completion Notes List

- All 9 AC bullets verified with dedicated test coverage: 3 were already correct (AC1 buttons, AC3 modal focus/Escape, AC4 aria-live — all confirmed via new or existing tests, zero code changes needed for those three), 6 required real fixes (AC1/AC2 StatusBadge focus+announcement, AC5 success toast wiring, AC6 error announcements, AC9 stale-row highlight).
- `StatusBadge.tsx`: added `tabIndex={0}` and optional `employeeName`/`skillName` props building the full `"{Employee} {Skill}: {Status}..."` aria-label; `ProvenanceDrillDownModal.tsx`'s call site deliberately left unchanged (would double-announce against its own header).
- `DashboardPage.tsx` + `ProvenanceDrillDownModal.tsx`: `role="alert"` added to 3 error surfaces (dashboard fetch error, drill-down fetch error, override-submit error) — previously silent to assistive tech.
- `DashboardPageHandle` extended with `announceToast()`; `Dashboard.tsx` now fires the `"✓ Skill assigned to {Employee} — {Skill name}"` toast on the real `/hr/dashboard` route for the first time — this copy previously existed only in dead, unrouted `DashboardStub.tsx`.
- `DashboardRow.tsx`: closes both Story 5.6's own AC9 and Story 5.1's never-built stale-highlight AC together — red/highlighted Last Updated cell + literal "Not updated in X days" text when `provenance === "Needs Attention"`, sourced entirely from data the backend already provides (zero backend changes).
- Regression caught and fixed during Task 6 (not left elevated): a new test reused the `render(<DashboardPage />)` pattern that omits the required `onNewAssignment` prop, producing one new occurrence of an existing pre-existing tsc error class — fixed by passing the prop, matching Story 5-5's identical precedent.
- Full verification: `tsc --noEmit` normalized-diff byte-identical to baseline (85 lines, zero new errors); full frontend suite 222/224 passing (same 2 pre-existing unrelated failures, confirmed via `git stash` comparison); `npx vite build` clean (`npm run build`'s own `tsc` step still fails on pre-existing unrelated errors, same as baseline — `vite build` used directly per Story 2.5/2.6 precedent).
- `DashboardStub.tsx` confirmed still dead/unrouted; left untouched, out of scope per the story's own Known Issues & Deferrals.

### File List

- `frontend/src/components/StatusBadge.tsx` — modified (Task 1; code review: `aria-live="off"` patch)
- `frontend/src/components/StatusBadge.test.tsx` — modified (Task 1)
- `frontend/src/features/dashboard/DashboardRow.tsx` — modified (Task 1, Task 4; code review: staleness-helper patches)
- `frontend/src/features/dashboard/DashboardRow.test.tsx` — modified (Task 1, Task 4; code review round 1: 2 new guard tests; round 2: rewrote 2 tests for the 0-day-text-not-suppressed fix, replaced the non-exercising future-clamp test)
- `frontend/src/features/dashboard/DashboardPage.tsx` — modified (Task 2, Task 3; code review: comment patch)
- `frontend/src/features/dashboard/DashboardPage.test.tsx` — modified (Task 2, Task 3, Task 6 regression fix; code review round 1: toast-wording patch; round 2: toast-wording re-patch to checkmark+first-name)
- `frontend/src/features/dashboard/DashboardPage.polling.test.tsx` — unmodified, re-verified passing (Task 5)
- `frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx` — modified (Task 2; code review round 1: shared staleness helper; round 2: 0-day wording guard)
- `frontend/src/features/dashboard/ProvenanceDrillDownModal.test.tsx` — modified (Task 2, Task 5; code review round 1: Tab-wrap regression test; round 2: added HR-Override Tab-wrap test)
- `frontend/src/pages/hr/Dashboard.tsx` — modified (Task 3; code review round 1: toast-wording patch; round 2: toast-wording re-patch to checkmark+first-name)
- `frontend/src/lib/utils/staleness.ts` — **new** (code review round 1: shared `staleDaysSince()`/`formatStaleDaysText()` helper; round 2: NaN guard, 0-day distinct wording)
- `frontend/src/lib/utils/staleness.test.ts` — **new** (code review round 2: direct unit tests for the shared helper)
- `frontend/src/components/StatusBadge.test.tsx` — modified (Task 1; code review round 2: `aria-live="off"` regression test)
- `frontend/src/components/ui/toast.tsx` — unmodified, as scoped (only its consumption changed)

## Change Log

- 2026-07-13 — Implemented Story 5.6 (all 6 tasks, all 9 AC bullets): StatusBadge focusability + full announcement text, error `role="alert"` announcements, success-toast wiring into the real dashboard route, stale-row grid highlight, plus verification (and one correction) of already-built AC1/AC3/AC4 behavior. Status → review.
- 2026-07-13 — Code review round 1 (3 parallel adversarial layers): 2 decisions resolved (muted `StatusBadge`'s `role="status"` live-region semantics via `aria-live="off"` to eliminate a real double-announcement risk against `DashboardPage.tsx`'s dedicated `aria-live` region; stripped an unauthorized `"✓ "` prefix from the AC5 toast to match epics.md's literal wording), 6 patches applied (clock-skew/zero-day guard on stale-day computation, extracted shared `lib/utils/staleness.ts` closing a DRY duplication, added a real Tab/Shift+Tab wrap-order test confirming `Dialog.tsx`'s focus trap still works correctly with the newly-focusable badge, fixed a stale code comment), 6 deferred. Full regression re-verified post-patch: `tsc --noEmit` byte-identical to baseline, frontend suite 225/227 passing, `vite build` clean. Status → done.
- 2026-07-13 — Code review round 2 (user-requested, 3 fresh adversarial layers instructed not to assume round 1's patches were correct): **1 decision re-opened and re-resolved** — round 1's toast-wording fix turned out to be based on incomplete information; epics.md has a 3-way conflict (UX-DR12 + Story 3.5's own AC both specify `"✓ Skill assigned to {Employee first name} — {Skill name}"`, contradicting Story 5.6's own AC used as the sole justification in round 1) — user re-decided in favor of the checkmark+first-name reading (2 corroborating citations, including the originating story). **7 patches applied**, headlined by a real NFR-A2 regression 2 of 3 review layers independently caught in round 1's own "0-day suppression" fix: it removed the paired text but not the color, leaving a color-only state at the exact 0-day boundary — fixed by having `formatStaleDaysText()` return distinct non-blank text ("Not updated today") instead of conditionally hiding it. Also fixed: `staleDaysSince()`'s missing NaN guard for invalid dates, the same 0-day wording gap in `ProvenanceDrillDownModal.tsx`'s "Needs Attention" branch, an HR-Override-state gap in the Tab-wrap test, a direct `staleness.test.ts` (no dedicated unit coverage existed — the round-1 "clamp" test didn't actually exercise the clamp, confirmed by deleting `Math.max(0, ...)` and observing the test still pass), and a missing `aria-live="off"` regression test. 5 deferred (untestable-in-jsdom AT-behavior nuances, an inherent AC2 tradeoff already scoped in round 1, narrow test-infrastructure edge cases). Re-verified: `tsc --noEmit` byte-identical to baseline, full suite 235/237 passing (same 2 pre-existing unrelated failures — 2 transient cross-file failures observed on one run were confirmed non-reproducible on immediate re-run, isolated-file run, and a second combined run), `vite build` clean (513 modules). Status remains `done`.
