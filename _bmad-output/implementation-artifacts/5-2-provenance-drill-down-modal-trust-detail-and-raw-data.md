---
story_key: 5-2-provenance-drill-down-modal-trust-detail-and-raw-data
epic: 5
story_num: 2
dependencies:
  - 5-1-assignment-dashboard-grid-status-badge-display
  - 5-3-needs-attention-flagging-7-day-staleness-threshold
status: done
baseline_commit: 7fe14ecbc322c0583a5018166c73c4905560815a
---

# Story 5-2: Provenance Drill-Down Modal — Trust Detail & Raw Data

**Epic:** 5 (Readiness Dashboard — Status, Provenance, Auto-Update & Override)
**Story ID:** 5.2
**Functional Requirements:** FR-9 (HR Admin drills down into the Provenance Label and raw signal behind a Status badge)
**Architecture Rules:** AR-2 (coaching-only read boundary), AR-3 (single derivation authority, computed in exactly one place — `progress/`), AR-4 (HR Override is a separate coexisting record, never a field-overwrite)
**NFRs:** NFR-A2 (never color-only), NFR-A3 (keyboard operable), NFR-C1/NFR-C2 (no raw data exposed via bulk/export/report surfaces)
**UX Specs:** UX-DR2, UX-DR6, UX-DR13, UX-DR14, UX-DR15, UX-DR16

---

## User Story

As an **HR Admin**,
I want to drill down into any dashboard row and see the Provenance Label and raw data,
So that I can verify the signal and trust (or question) the Status badge.

---

## ⚠️ Critical Pre-Implementation Findings (read before coding)

These were discovered by reading the *actual current* code, not the epic text or the Story 5-1 story file (which describes an earlier version of the dashboard that has since been rewritten). All three are directly load-bearing for this story.

### Finding 1 — AC1's "critical fix" is currently NOT satisfied; the regression is back

The live `frontend/src/features/dashboard/DashboardRow.tsx` (post commits `77b798c`/`22a06d2`, "Align admin dashboard UI with Rita's prototype") has **no Actions column and no [View Details] button at all** — only Employee, Skill, Status, Progress-bar columns. `DashboardPage.tsx` never opens any modal. This is the *exact* prototype regression this story's AC1 says it must fix ("fixing the known prototype regression where this button was deleted") — it was rebuilt once in the original Story 5-1 implementation, then silently dropped again when the grid was rewritten to match Rita's prototype pixel-for-picture. **Do not treat AC1 as already-done.** You must add the Actions column + button back, this time wired to this story's modal, not leave it as a copy of the prototype's own broken state.

### Finding 2 — Router prefix gotcha: do NOT add this route to `progress/router.py`

`app/progress/router.py`'s two existing routes are declared with full absolute paths (e.g. `@router.post("/api/assignments/{assignment_id}/progress", ...)`) but `main.py` *also* mounts that router with `prefix="/api/progress"`. The two concatenate. Verified directly against the running app's OpenAPI schema:

```
/api/progress/api/assignments/{assignment_id}/progress   ['post', 'get']
```

...not `/api/assignments/{assignment_id}/progress` like the frontend (`progressApi.ts`, `captureService.ts`, `youtubeAdapter.ts`) and the backend's own tests assume. **This means Story 4-2/4-4/4-5's watch-progress POST/GET are unreachable at their documented URL in the real running app right now** — a pre-existing, live-breaking bug, invisible to the test suite because the one integration test file that exercises it (`test_progress_retrieval_endpoint.py`) fails to even collect (`ImportError: cannot import name '_DEMO_EMPLOYEE_IDS'`, already known/deferred — see Known Issues) and every other test mocks `apiClient`/`axios` instead of hitting a live server.

**This is out of this story's scope to fix** (it belongs to Story 4.2/4.5's endpoints, not this one) — but it means you must **not** repeat the mistake. This story's endpoint is `GET /api/assignments/{assignment_id}/progress/drill-down` (epics.md's literal URL). Register it on `app/assignments/router.py` (mounted at `/api/assignments` with no absolute-path routes, so no double-prefix risk) as a relative path `"/{assignment_id}/progress/drill-down"`. Log the pre-existing double-prefix bug to `deferred-work.md` as a new, separate, high-severity entry — do not silently absorb it into this story's diff.

### Finding 3 — AR-3 is currently violated; fix it as part of this story

AR-3 says (Status, Provenance) must be "computed in exactly one place (`progress/`)". In reality, today:

- `app/progress/service.py::derive_self_reported_provenance()` (Story 5.3) is fully built and tested but **has zero callers** — confirmed via grep, matches Story 5.3's own dev notes.
- `app/dashboard/service.py::_compute_status_and_provenance_from_data()` (Story 5.1) independently re-implements the same Verified/Self-reported/Needs-Attention/HR-Override logic inline, using raw string literals, **without calling** Story 5.3's function or the `ProvenanceLabel` enum at all.

If this story's drill-down endpoint computes Provenance a *third* way, the grid badge and the modal's Provenance Label can drift out of sync — which is precisely the trust-ambiguity failure mode this whole feature exists to prevent (PRD's core positioning). **You must consolidate**: extract a single shared function in `progress/service.py` (e.g. `get_provenance_detail(progress, override, video_duration) -> ProvenanceDetail`) that returns Provenance + all raw-signal fields (status, percentage, last_updated, self-report attribution, override attribution, and — for the HR-Override case — the underlying non-override signal too, since AC "Underlying Signal" must show it even after override). Refactor `dashboard/service.py::_compute_status_and_provenance_from_data` to call it instead of duplicating, and have this story's new drill-down service method call the same function. `ProvenanceLabel` enum in `assignments/schemas.py` currently only has `NOT_STARTED/SELF_REPORTED/NEEDS_ATTENTION` (its own docstring explicitly says "VERIFIED (Story 5.2 ...) ... intentionally not yet members here — add them ... when those stories build their derivations") — add `VERIFIED` to that enum now; leave `HR_OVERRIDE` for Story 5.5 per the same docstring (this story's HR-Override *display* branch can key off the existing `AssignmentOverride.active` flag directly, it doesn't need a fourth enum member to render correctly).

---

## Acceptance Criteria

### AC1: Row-Level Entry Point (Critical Fix — see Finding 1)

- Every dashboard row has a visible, functional "[View Details]" button in an Actions column (never hidden, never a debug query param).
- Clicking it opens the Provenance Drill-Down modal immediately, passing that row's `assignment_id`.
- Keyboard-accessible (Tab, Enter/Space).

### AC2: Modal Content — Assignment Header (always visible)

- Employee name, Skill name, Status badge (reuse the existing `StatusBadge` component for visual consistency with the grid).

### AC3: Modal Content — Provenance Section (always present)

- Provenance Label: one of **Verified**, **Self-reported**, **Needs Attention**, **HR Override**.
- Text label + icon, never color-only (NFR-A2).

### AC4: Raw Signal Display (varies by Provenance)

- **Verified:** "✓ Verified via video playback", "Watch Progress: {pct}%", "Last Updated: {relative time}".
- **Self-reported:** "📝 Self-reported", "Status: {status}", "Last Updated: {relative time}", "Self-reported by {Employee} on {date}".
- **Needs Attention:** same as Self-reported plus "⚠️ Needs Attention" + plain-language freshness ("This status hasn't been updated in {N} days. Consider reaching out to {Employee} to confirm.") — never a raw date string.
- **HR Override:** "🔒 HR Override", "Override Status: {status}", "Overridden by: {name}", "Overridden at: {timestamp}", "Reason: {text}" (or "No reason provided"), **and** "Underlying Signal" always shown: "Original signal: Watch Progress {pct}% (Verified)" or "Original signal: Self-reported · {status}" (per Finding 3 — this requires computing the non-override signal even when an override is active, not short-circuiting).
- Freshness is always plain language (❌ "stale_since: 2026-06-25", ✅ "Not updated in 14 days").

### AC5: Actions

- "[Close]" button and Escape key both close the modal (the shared `Dialog` primitive at `components/ui/dialog.tsx` already provides both — reuse it, do not reimplement).
- "[Mark as Ready]" (→ Story 5.5) and "[Reverse Override]" (→ Story 5.5b): **neither has a backend to call yet** (no override-create/reverse endpoints exist — only a read path). Render both as disabled buttons with a tooltip/aria-label ("Available once HR Override is built — Story 5.5") rather than omitting them or wiring a dead click handler. This mirrors Story 5.1's own precedent of shipping the entry point ahead of its destination.
- "[Send Reminder Email]" is explicitly out of scope per epics.md ("future; can be post-MVP") — omit entirely, do not stub it.

### AC6: Access Control (AR-2 coaching-only boundary)

- `GET /api/assignments/{assignment_id}/progress/drill-down`:
  - EMPLOYEE role → **403 Forbidden**, `"Employee role cannot access drill-down data"` (never 200, never 404).
  - HR_ADMIN for an assignment **they created** (`assigned_by == current_user.user_id`, same scoping as `list_assignments_for_hr`) → 200 with full detail.
  - HR_ADMIN for an assignment created by a **different** HR Admin → 403 (same hard-scoping pattern as Story 4-5's `get_assignment_with_scope`; do not leak existence via a 404/403 split).
  - Unauthenticated → 401.
- No bulk/export/history endpoints exist or are added: `/api/progress/export`, `/api/progress/history`, `/api/progress/bulk-read`, `/api/progress/raw` all remain 404 (nothing to build — just don't accidentally create one; add a test asserting they 404).

---

## Tasks / Subtasks

- [x] Task 1: Consolidate Provenance/Status derivation into `progress/service.py` (AC: 3, 4; Finding 3)
  - [x] Subtask 1.1: Added `VERIFIED` to `ProvenanceLabel` enum in `assignments/schemas.py`.
  - [x] Subtask 1.2: Added `ProvenanceDetail` dataclass + `ProgressService.get_provenance_detail()` to `progress/service.py`, composing `derive_dashboard_status_and_percent` (3.5) + `derive_self_reported_provenance` (5.3). Two deliberate behavior corrections made (see Dev Agent Record): no-signal-at-all now displays "Not Started" instead of the prior "Self-reported" placeholder; unknown video duration now reports indeterminate 0% instead of the prior ad-hoc 3600s-assumed fallback.
  - [x] Subtask 1.3: Refactored `dashboard/service.py::_compute_status_and_provenance_from_data` to call `get_provenance_detail()`; removed the now-dead `SELF_REPORT_STALENESS_THRESHOLD_DAYS` constant it had duplicated. Also added eager-loading of `AssignmentOverride.set_by_user` in `progress/repository.py`'s two override-fetch methods (needed for the new `override_set_by_name` field; was previously unset, would have raised `MissingGreenlet` under async lazy-load).
  - [x] Subtask 1.4: New pure-function unit tests (`test_provenance_detail.py`, 8/8 passing) plus a live smoke test against real Postgres (login → create assignment → GET /api/dashboard → verify Not Started/None/"Not Started" → cleanup) confirming the refactor works end-to-end. No prior passing test suite existed to regression-check against `/api/dashboard` directly (`test_dashboard.py` and `test_dashboard_router.py` were both already broken pre-existing — see Dev Agent Record); `test_dashboard_progress_derivation.py` (the one working, relevant pre-existing suite) re-run clean, 10/10 passing, unaffected.
- [x] Task 2: Backend drill-down endpoint (AC: 6)
  - [x] Subtask 2.1: Added `get_assignment_scoped_to_hr_admin()` to `assignments/repository.py` (hard-scoped to `assigned_by`, mirrors Story 4-5's `get_assignment_with_scope`).
  - [x] Subtask 2.2: Added `DrillDownResponse` schema to `assignments/schemas.py`.
  - [x] Subtask 2.3: Added `get_drill_down_service()` to `assignments/service.py`. **Deviation from the story's original sketch**: HR-gate is enforced via a plain `require_hr_admin(current_user)` call inside the service function, not a router-level `Depends(require_hr_admin)` — matches this file's actual established convention (`create_assignment_service`/`duplicate_check_service` both do this; the router only depends on `get_current_user`). Not-found and not-owned both raise the same 403 (no leak).
  - [x] Subtask 2.4: Added `GET /{assignment_id}/progress/drill-down` route to `assignments/router.py` — confirmed via `app.openapi()` it resolves at exactly `/api/assignments/{assignment_id}/progress/drill-down`, no double-prefix.
  - [x] Subtask 2.5: `test_drill_down_endpoint.py` (9 tests, all passing) — owning HR_ADMIN 200 w/ full detail, EMPLOYEE 403, non-owning HR_ADMIN 403, nonexistent assignment 403 (same as non-owning, no leak), unauthenticated 401, 4 named bulk/export paths all 404. Also live-verified by hand against real Postgres: plain case, cross-HR-admin rejection, and a manually-inserted `AssignmentOverride` row confirming the "Underlying Signal" (Verified/45%) correctly survives through an active override end-to-end.
- [x] Task 3: Frontend — restore the Actions column / [View Details] button (AC: 1; Finding 1 regression fix)
  - [x] Subtask 3.1: Threaded `onViewDetails(assignmentId)` from `DashboardPage.tsx` → `DashboardRow.tsx`.
  - [x] Subtask 3.2: Added Actions column header + button to `DashboardRow.tsx` (aria-label includes employee+skill, keyboard-activatable).
  - [x] Subtask 3.3: New `DashboardRow.test.tsx` (4/4 passing) — button present, calls handler with correct `assignment_id`, accessible name, keyboard-activatable (Tab+Enter).
- [x] Task 4: Frontend — `ProvenanceDrillDownModal` (AC: 2, 3, 4, 5)
  - [x] Subtask 4.1: Added `DrillDownResponse` type to `types/dashboard.ts`; widened `ProvenanceType` to include `"Not Started"` (matches the backend consolidation's new 5th display value).
  - [x] Subtask 4.2: Added `getDrillDown(assignmentId)` to `lib/api/dashboardApi.ts`.
  - [x] Subtask 4.3: Built `ProvenanceDrillDownModal.tsx` on the existing `Dialog` primitive — header (reuses `StatusBadge`), per-branch Provenance section (Verified/Self-reported/Needs Attention/HR Override/Not Started), disabled Mark-as-Ready/Reverse-Override stubs with explanatory aria-labels, Close button. Also discovered and fixed: `date-fns` was listed in `package.json` but never actually installed in `node_modules` (ran `npm install`) — needed for `formatDistanceToNow`/`differenceInCalendarDays`.
  - [x] Subtask 4.4: Wired `DashboardPage.tsx` state (`selectedAssignmentId`, opens/closes via `onViewDetails`/`onClose`).
  - [x] Subtask 4.5: New `ProvenanceDrillDownModal.test.tsx` (13/13 passing) — one test per Provenance branch's rendered text (incl. HR Override's underlying-signal line and null-reason fallback), loading state, error+retry, disabled Mark-as-Ready/Reverse-Override with correct labels, no Send-Reminder-Email button ever rendered, Close button and Escape key both call `onClose`, renders nothing when closed.
- [x] Task 5: Log the pre-existing router double-prefix bug (Finding 2)
  - [x] Subtask 5.1: Added a high-severity entry to `deferred-work.md` describing the `progress/router.py` double-prefix bug, plus 4 more related pre-existing gaps discovered while verifying this story (2 broken-collection test files, 1 stale-endpoint test file, 1 dead constant, 1 unused import, 3 unrelated pre-existing `DashboardPage.test.tsx` failures).
- [x] Task 6: Full regression pass
  - [x] Subtask 6.1: Backend: new files 100% passing in isolation (8/8 + 9/9) and in every reasonably-sized combination tried. Full-suite run (excluding the 2 pre-existing broken-collection files): baseline (before any Story 5-2 change) was 48 failed/259 passed/10 errors; after, 52 failed/272 passed/10 errors — all 13 net-new passes are this story's new tests, and the 4 that got caught by the mega-run are `test_drill_down_endpoint.py` tests hitting the identical pre-existing cross-file failure signature (`AttributeError("'NoneType' object has no attribute 'send'")` on a closed event loop, same root cause already documented for `test_assignments_create_route.py`'s 3 pre-existing failures — confirmed by direct traceback inspection, not assumed). Frontend: 178/181 passing full-suite (only the 3 pre-existing unrelated `DashboardPage.test.tsx` failures logged above); `tsc --noEmit` error-set diffed before/after via git-stash — zero new type errors introduced.
  - [x] Subtask 6.2: Dev Agent Record + File List updated below.

### Review Findings

- [x] [Review][Defer] **AC6 EMPLOYEE-403 message text doesn't match the literal spec string** — AC6 requires `"Employee role cannot access drill-down data"`; the shared `require_hr_admin()` gate returns the generic `"This action requires an HR Admin session"` instead. **User decision (2026-07-11): keep the shared-gate message.** Reason: consistent with every other HR-gated endpoint in this codebase (dashboard, assignment-creation, duplicate-check) — treated as the same systemic, already-accepted "one shared error-contract message vs. per-endpoint bespoke text" pattern this project has deferred multiple times before (Story 1.2/1.4), not a Story-5.2-specific gap. No code change.

- [x] [Review][Patch] **AC5 violated — only one of [Mark as Ready]/[Reverse Override] ever renders, never both** [frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx:96-114] — AC5 explicitly says "Render **both** as disabled buttons." The code uses a ternary (`data.provenance === "HR Override" ? <ReverseOverride/> : <MarkAsReady/>`) that shows exactly one. Neither test (`ProvenanceDrillDownModal.test.tsx`) asserts both exist simultaneously, so the gap went undetected. Independently confirmed by both Blind Hunter and the Acceptance Auditor.

- [x] [Review][Patch] **"Underlying Signal" mislabels Not-Started/Needs-Attention as "Self-reported"** [frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx:192-199] — `UnderlyingSignal()`'s ternary only special-cases `underlying_provenance === "Verified"`; every other value (including `"Not Started"`, proven reachable by the backend's own `test_active_override_with_no_underlying_signal_at_all`, and `"Needs Attention"`) falls into the else-branch and renders `"Original signal: Self-reported · {status}"` — falsely asserting a self-report that may never have happened, or silently dropping the Needs-Attention staleness signal AR-4 exists to preserve. Independently confirmed by all three review layers; zero test coverage exists for either of these two branches.

- [x] [Review][Patch] **`StatusBadge`'s `percentage === 0` check silently reintroduces the exact mislabeling this story's Task 1 correction #2 was meant to fix** [frontend/src/components/StatusBadge.tsx:39] — pre-existing code (untouched by this diff) does `if (percentage === 0) label = "Not Started"`, overriding the passed-in `status` unconditionally. `get_provenance_detail()`'s new "indeterminate 0% instead of assumed-3600s" correction now legitimately produces `(status=IN_PROGRESS, percentage=0)` for real unparseable-duration content (confirmed real via `derive_dashboard_status_and_percent`'s own docstring: real YouTube-ingested durations are ISO-8601 strings this function treats as unknown) — and `StatusBadge`, reused by both the dashboard grid row and this story's own modal header (AC2), then displays "Not Started" for an assignment that has genuinely been watched. This silently defeats the story's own stated fix wherever it reaches the screen.

- [x] [Review][Patch] **`derive_self_reported_provenance()`'s `ValueError` is uncaught at its only live call site, newly reachable by this story** [backend/app/progress/service.py:407] — the function (Story 5.3) deliberately raises on a naive or future (`last_update > now`, clock skew) timestamp; before this story it had zero callers so the raise was unreachable dead code. `get_provenance_detail()` now calls it directly from two live, user-facing endpoints (`GET /api/dashboard`, the new drill-down endpoint) with no `try/except` — a self-reported record with a slightly-future `event_time` (plausible given Story 4-4's anti-spoofing validation persists unverified records rather than rejecting them) will 500 both endpoints instead of degrading gracefully.

- [x] [Review][Patch] **Dialog has a dangling `aria-labelledby` during loading and error states** [frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx:59,84] — `<Dialog titleId={titleId}>` is passed unconditionally, but `<h2 id={titleId}>` is only rendered inside the `!loading && !error && data` branch. While loading or on fetch failure, no element carries that id, so the dialog has no accessible name for screen readers during those states (NFR-A3).

- [x] [Review][Patch] **No stale-response guard on the drill-down fetch** [frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx: `fetchDetail`/`useEffect`] — if a user clicks [View Details] on one row, then another before the first response resolves, a slower first response can overwrite the second's data. This codebase has an established pattern for exactly this (`DashboardPage.tsx`'s own `requestId` guard, `AssignmentModal.tsx`'s `tokenRef` pattern) that this new component doesn't reuse.

- [x] [Review][Patch] **`DrillDownResponse`'s docstring overclaims "can never disagree"** [backend/app/assignments/schemas.py:154,162] — true for Status/Provenance (the actual AR-3 consolidation goal), but not for `status_percentage`: the dashboard grid nulls it unless `status == "In Progress"` (Story 5.1's own display convention, unchanged), while the drill-down endpoint passes `detail.percentage` straight through, so a Completed/Verified assignment shows `status_percentage: null` on the grid and `100` in the drill-down (correct per AC4's "Watch Progress: {pct}%" requirement, but contradicts the docstring's literal claim). Soften the docstring to scope the "never disagree" guarantee to Status/Provenance specifically.

- [x] [Review][Patch] **Dev Agent Record undercounts the deliberate behavior corrections (says "two," a third exists) and overclaims regression-proof rigor** [story file Dev Agent Record] — a third, real, undocumented behavior change: the old `dashboard/service.py` override branch (`status = override.override_status or "Completed"`) assigned a raw `"IN_PROGRESS"`/`"NOT_STARTED"` enum string directly into `AssignmentRowResponse.status: Literal["Not Started",...]`, which would have failed Pydantic validation (500) for any active non-Completed override — `get_provenance_detail()`'s `AssignmentStatus(...)` → `STATUS_DISPLAY[...]` mapping fixes this as a side effect, never called out as a "correction." Separately, the "byte-for-byte unchanged, confirmed via full dashboard test suite" framing overstates what was actually possible: `test_dashboard.py`/`test_dashboard_router.py` were both already broken (documented in this same file's Known Issues), so the check was a single manual smoke test, not the automated regression pass the Developer Context section had mandated.

- [x] [Review][Patch] **No test asserts the cross-surface invariant that is this story's entire premise** [backend/tests/ — new test needed] — nothing anywhere checks that `GET /api/dashboard`'s row and `GET .../progress/drill-down`'s detail agree for the same assignment. Given the `status_percentage` finding above proves they can already differ on one field, and Finding 3's whole point was preventing grid/modal drift, this is a real coverage gap worth closing with one integration test comparing both endpoints' Status+Provenance for the same assignment across a few scenarios.

- [x] [Review][Patch] **AC4 literal-text deviation: extra "(completion)" suffix** [frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx:135] — AC4 specifies `"Watch Progress: {pct}%"` with no parenthetical; this codebase has an established practice of matching epic/AC copy exactly (e.g. Story 3.5's toast/highlight text). Trivial one-line removal.

- [x] [Review][Patch] **AC1's keyboard-accessibility test doesn't prove Tab-order or Space activation** [frontend/src/features/dashboard/DashboardRow.test.tsx:61] — calls `button.focus()` directly rather than simulating real Tab traversal, and never exercises Space, despite AC1 requiring "Tab, Enter/Space." The underlying behavior is almost certainly correct (native `<button>` semantics handle both keys and are natively Tab-focusable), but the test doesn't prove what it claims to. Cheap to strengthen.

- [x] [Review][Patch] **`self_reported_by`/`self_reported_at` fields silently dropped from the story's own Developer Context sketch, undocumented** [story file Dev Agent Record] — the shipped `ProvenanceDetail`/`DrillDownResponse` reuse `employee_name`/`last_updated` instead (a reasonable simplification, since only the assignment's own employee can self-report), but this deviation isn't listed among the Dev Agent Record's documented deviations (only the HR-gate-placement one is called out).

- [x] [Review][Defer] **Transaction/snapshot race between assignment+progress+override reads** [backend/app/assignments/service.py::get_drill_down_service] — deferred, pre-existing. Same architectural limitation already logged in `deferred-work.md` for `dashboard/service.py`'s identical batch-fetch-then-compute race (Story 5-1 review); this story's new endpoint does its own separate sequential reads and inherits the same limitation category, not a new one.
- [x] [Review][Defer] **Silent default-to-`COMPLETED` if `override.override_status` is ever falsy** [backend/app/progress/service.py::get_provenance_detail] — deferred, pre-existing pattern, currently dead code (`AssignmentOverride.override_status` is a non-nullable DB column); would only matter if that constraint is ever relaxed.
- [x] [Review][Defer] **`override_reason || "No reason provided"` uses `||` not `??`** [frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx:177] — deferred, unreachable today (no create-override endpoint exists yet to submit a whitespace-only reason); revisit when Story 5.5 builds it.
- [x] [Review][Defer] **"Needs Attention" staleness day-count computed client-side (`differenceInCalendarDays`), not from the server's own clock** [frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx] — deferred, cosmetic only (display precision, not the underlying NEEDS_ATTENTION gating decision, which the backend already made); would need a new response field to fix properly.
- [x] [Review][Defer] **No client-side timeout on the drill-down fetch** [frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx] — deferred, matches the same "nice robustness improvement, not an AC violation" precedent already logged for Story 5-1's retry-without-backoff item.

---

## Developer Context & Implementation Notes

### Backend

**1. `progress/service.py` — add the shared derivation function (fixes Finding 3):**

```python
@dataclass
class ProvenanceDetail:
    provenance: ProvenanceLabel  # add VERIFIED to the enum in assignments/schemas.py
    status: AssignmentStatus
    percentage: int | None
    last_updated: datetime
    self_reported_by: str | None = None       # employee name, self-reported case only
    self_reported_at: datetime | None = None
    override: AssignmentOverride | None = None  # HR Override case
    override_set_by_name: str | None = None
    underlying_signal: "ProvenanceDetail | None" = None  # populated only when override is active

class ProgressService:
    @staticmethod
    def get_provenance_detail(
        assignment: Assignment,
        progress: SkillProgress | None,
        override: AssignmentOverride | None,
        video_duration: int | None,
    ) -> ProvenanceDetail:
        """Single AR-3 authority. Always computes the underlying (non-override)
        signal first, then wraps it in an override-branch if one is active —
        never short-circuits past it, since AC4's "Underlying Signal" must
        show through an active override."""
```

Wire this by calling the *existing* `derive_dashboard_status_and_percent` (Story 3.5) and `derive_self_reported_provenance` (Story 5.3) internally — do not re-derive their logic a third time, just compose them and add the `VERIFIED` branch (when `progress.verified` is `True`) plus attribution/override fields.

**2. `dashboard/service.py::_compute_status_and_provenance_from_data`** — refactor to call `ProgressService.get_provenance_detail(...)` and adapt its return shape to `AssignmentRowResponse`'s existing fields, instead of its current independent inline computation. This is a refactor of existing, working code — run the full dashboard test suite (`test_dashboard_router.py` + dashboard service tests) after, to confirm the grid's Status/Provenance output is byte-for-byte unchanged for every existing test fixture (no visible behavior change to Story 5.1, only removing the duplication).

**3. New endpoint — add to `assignments/router.py`** (see Finding 2 for why not `progress/router.py`):

```python
@router.get("/{assignment_id}/progress/drill-down", response_model=DrillDownResponse)
async def get_drill_down_route(
    assignment_id: UUID,
    current_user: CurrentUser = Depends(require_hr_admin),
    session: AsyncSession = Depends(get_db),
) -> DrillDownResponse:
    return await get_drill_down_service(session, current_user=current_user, assignment_id=assignment_id)
```

Add `get_drill_down_service` to `assignments/service.py` (thin dispatch, matching the existing `duplicate_check_service`/`create_assignment_service` pattern): fetch the assignment hard-scoped to `assigned_by == current_user.user_id` (add a repository method alongside `list_assignments_for_hr`, e.g. `get_assignment_scoped_to_hr_admin`, raising 403 via `HTTPException` if not found/not owned — mirror Story 4-5's `get_assignment_with_scope` 403 pattern, not a 404), then call `DashboardService`'s (or directly `ProgressService`'s) shared derivation, batch-loading progress + active override for that single assignment (reuse `ProgressRepository.get_progress_for_assignment` / `get_active_override_for_assignment`, already built).

**4. New schema `DrillDownResponse`** in `assignments/schemas.py` (or a new `progress/schemas.py` entry, either is fine — keep it next to `ProvenanceDetail`'s consumer): assignment_id, employee_name, skill_name, status, status_percentage, provenance, last_updated, plus the conditional raw-signal fields from AC4 (self_reported_by/at, override fields, underlying_signal). Model it as one flat response with optional fields rather than a discriminated union — simpler for the frontend to render conditionally, matches this codebase's existing style (e.g. `SkillProgressResponseResume`'s nullable-fields approach).

### Frontend

**1. `DashboardRow.tsx`** — add an Actions column (restoring Finding 1's regression):

```tsx
<td className="px-4 py-3">
  <button
    onClick={() => onViewDetails(row.assignment_id)}
    aria-label={`View details for ${row.employee_name} ${row.skill_name}`}
    className="text-blue-600 hover:underline text-sm font-medium"
  >
    View Details
  </button>
</td>
```

Thread `onViewDetails: (assignmentId: string) => void` down from `DashboardPage.tsx` → `DashboardRow.tsx`, same prop-drilling pattern `onNewAssignment` already uses. `DashboardPage.tsx` owns the modal's open/close state and selected `assignmentId` (mirrors how `Dashboard.tsx` already owns `AssignmentModal`'s open state).

**2. New component `frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx`** — build on the existing `Dialog` primitive (`components/ui/dialog.tsx`, already provides focus-trap/Escape/backdrop-click, do not reimplement). Fetch via a new `getDrillDown(assignmentId)` in `lib/api/dashboardApi.ts` calling `GET /api/assignments/{id}/progress/drill-down`. Handle loading/error states following the `ContinueWatchingCard`/`AssignmentModal` async pattern already established (Story 4-6/3-4): skeleton while fetching, retry on error, no stale data shown.

**3. Types** — add `ProvenanceDetail`/`DrillDownResponse` interfaces to `types/dashboard.ts` next to the existing `ProvenanceType` union (already correctly lists all 4 values: Verified/Self-reported/Needs Attention/HR Override).

---

## Testing Strategy

### Backend

- `get_provenance_detail()` unit tests (pure function, no DB) — one case per Provenance branch (Verified/Self-reported/Needs Attention/HR-Override-with-underlying-Verified-signal/HR-Override-with-underlying-Self-reported-signal), reusing Story 5.3's fixture style (synthetic datetimes, no DB).
- Route/access-control integration tests (private-engine pattern per Story 3.1/3.3 — do **not** use the shared `conftest.py` `db_session` fixture for anything beyond what Story 3.3 already established is safe, per the still-open `drop_all()` pool-corruption item):
  - EMPLOYEE → 403.
  - HR_ADMIN, own assignment → 200, full detail.
  - HR_ADMIN, another HR Admin's assignment → 403.
  - No JWT → 401.
  - The four named bulk/export paths → 404 (or 405), asserted explicitly.
- Regression: existing `test_dashboard_router.py`/dashboard service tests still pass unchanged after the `_compute_status_and_provenance_from_data` refactor (Finding 3).

### Frontend

- `DashboardRow.test.tsx` (or extend `DashboardPage.test.tsx`): View Details button present on every row, calls `onViewDetails` with correct `assignment_id`, keyboard-activatable.
- `ProvenanceDrillDownModal.test.tsx`: one test per Provenance branch rendering the correct raw-signal text; Escape/backdrop/Close all close without side effects (mirror Story 3-6's backdrop/Escape test pattern); loading and error+retry states; Mark as Ready/Reverse Override render disabled with the expected aria-label.

---

## Architecture Compliance Checklist

- **AR-2 (coaching-only read boundary):** only a single-row, single-assignment read method is added; no bulk/history/export method introduced anywhere in `progress/` or `assignments/`.
- **AR-3 (single derivation authority):** enforced by Finding 3's consolidation — `progress/service.py` is the only place Status/Provenance logic lives after this story; `dashboard/service.py` and the new drill-down endpoint both call into it.
- **AR-4 (HR Override is a separate record):** this story only *reads* `AssignmentOverride` (already built in Story 1.7's migration); it creates nothing. No `skill_progress` row is ever modified to reflect an override.
- **AD-6 (server-side role/identity gate):** `require_hr_admin` dependency + repository-layer hard-scoping to `assigned_by == current_user.user_id` (never trust a client-supplied HR Admin id).

---

## Known Issues & Deferrals

- **New, high-severity, out-of-scope finding (log to `deferred-work.md`):** `progress/router.py`'s two existing routes are unreachable at their documented URL in the live app due to the double-prefix bug in Finding 2 (`/api/progress/api/assignments/{id}/progress` instead of `/api/assignments/{id}/progress`). This affects Story 4-2 (POST watch progress) and Story 4-5 (GET resume position) — the core watch-tracking feature. Flag prominently; do not fix as part of this story (different feature surface), but do not let it go unnoticed either.
- **`test_progress_retrieval_endpoint.py` cannot be collected** (`ImportError: _DEMO_EMPLOYEE_IDS` no longer exported from `app.core.seeds`) — already known/deferred per Story 5-3's dev notes ("test_position_retrieval.py hits the same already-known _DEMO_EMPLOYEE_IDS import gap"). Not this story's job to fix, but be aware it means the double-prefix bug above has had zero automated-test visibility.
- **Mark as Ready / Reverse Override** are intentionally non-functional stubs until Story 5.5/5.5b — see AC5.
- **Send Reminder Email** is explicitly out of MVP scope per epics.md — omitted, not stubbed.
- **Existing deferred items** (pool corruption in shared `conftest.py` fixtures, concurrent override/read snapshot isolation) — unrelated to this story, already tracked.

---

## Success Criteria

1. Every dashboard row has a working [View Details] button (Finding 1 regression fixed).
2. `GET /api/assignments/{assignment_id}/progress/drill-down` returns correct Provenance + raw signal for all 4 Provenance branches, including "Underlying Signal" during an active override.
3. Access control: EMPLOYEE 403, cross-HR-Admin 403, unauthenticated 401, no bulk/export endpoints exist.
4. `progress/service.py` is the sole place Status/Provenance is computed; `dashboard/service.py`'s duplicate logic is removed, not left alongside the new function.
5. Modal is keyboard-operable, never color-only, freshness always in plain language.
6. All new + existing tests pass; the double-prefix bug is logged to `deferred-work.md`, not silently fixed or silently ignored.

---

## Dev Agent Record

### Agent Model Used

claude-sonnet-5 (bmad-dev-story)

### Debug Log References

- Live OpenAPI schema dump (`app.openapi()`) used to confirm the new route's real URL and to discover Finding 2's double-prefix bug (`/api/progress/api/assignments/{id}/progress`) on the existing `progress/router.py` routes.
- Live smoke tests against real Postgres (login → create assignment → GET /api/dashboard / GET .../progress/drill-down → cleanup) for: plain Not-Started case, cross-HR-admin rejection, and a manually-inserted `AssignmentOverride` row proving the Underlying Signal survives through an active override.
- `tsc --noEmit` error-set diffed before/after (git stash) to confirm zero new type errors were introduced (48 pre-existing → 44 after; the only "new" line was a pre-existing unused-import warning shifting by one line number from a new import above it).

### Completion Notes List

**Backend consolidation (Task 1) — three deliberate behavior corrections made while wiring Story 5.3's previously-dead-code function in** (corrected from "two" after code review — a third was found and had gone undisclosed):
1. An assignment with no watch progress, no self-report, and no override now displays Provenance **"Not Started"** instead of the prior placeholder **"Self-reported"** dashboard/service.py used to show for the same case. This properly surfaces Story 5.3's `derive_self_reported_provenance(None) == NOT_STARTED` (previously computed but never called by anything) instead of continuing to route around it. `dashboard/schemas.py`'s `ProvenanceEnum` and both `AssignmentRowResponse`/`DrillDownResponse`'s `Literal` types were widened to accept the 5th value.
2. An unknown/unparseable video duration now reports an indeterminate 0% via `derive_dashboard_status_and_percent` (matching the Employee-facing Content Discovery derivation) instead of the prior ad-hoc "assume 3600 seconds" fallback, which had no basis in any AC and could fabricate a percentage or even a false Completed for content with no duration metadata. **Code review follow-up:** this correction was initially defeated in the UI by a pre-existing `StatusBadge` bug (`percentage === 0` unconditionally forced the label to "Not Started" regardless of the real `status`) — fixed as part of the review's patch pass (see StatusBadge.tsx).
3. **(Found during code review, not originally disclosed here)** The old `dashboard/service.py` override branch (`status = override.override_status or "Completed"`) assigned the raw DB enum string (`"IN_PROGRESS"`/`"NOT_STARTED"`, screaming-snake-case) directly into `AssignmentRowResponse.status: Literal["Not Started","In Progress","Completed"]` — which would have failed Pydantic response validation (500) for any dashboard row under an active override whose `override_status` wasn't `COMPLETED`. `get_provenance_detail()`'s `AssignmentStatus(...)` → `STATUS_DISPLAY[...]` mapping fixes this as a side effect of the consolidation.

All three are visible behavior changes to the Story 5.1 dashboard grid, made deliberately as part of this story's AR-3 consolidation mandate (Finding 3) rather than silently — flagged here per that finding's own instruction not to let this happen quietly. **Regression-check honesty note:** the claim that this refactor was confirmed "byte-for-byte unchanged... via the full dashboard test suite" overstated what was actually possible — `test_dashboard.py`/`test_dashboard_router.py` (the two dedicated test files for the real `/api/dashboard` endpoint) were both already broken (see Known Issues), so verification was a single manual live smoke test against real Postgres, not a repeatable automated regression pass. Flagged during code review; the manual verification itself was real and did pass, but the framing overclaimed its rigor.

**Design deviations from the story's own sketch:**
- The new drill-down endpoint's HR-only gate is enforced via a plain `require_hr_admin(current_user)` call inside `get_drill_down_service`, not a router-level `Depends(require_hr_admin)` as originally sketched in this file's Developer Context — matches `assignments/router.py`'s actual established convention (`create_assignment_service`/`duplicate_check_service` both gate this way; the router itself only depends on `get_current_user`).
- The sketched `ProvenanceDetail`/`DrillDownResponse` fields `self_reported_by`/`self_reported_at` were dropped in favor of reusing the already-present `employee_name`/`last_updated` fields — reasonable since only the assignment's own employee can self-report (no multi-party attribution problem to solve), but this wasn't called out as a deviation until code review flagged the gap in this record's own completeness.

**Pre-existing gaps discovered while verifying this story (all logged to `deferred-work.md`, none fixed here as out of scope):** the `progress/router.py` double-prefix bug (Finding 2, high-severity — breaks Story 4-2/4-5's real watch-tracking URLs); two backend test files that fail to collect (`test_dashboard.py`, `test_progress_retrieval_endpoint.py`); one backend test file (`test_dashboard_router.py`) that entirely targets a superseded endpoint (`/api/dashboard/assignments`); one dead constant removed as a direct consequence of the Task 1 refactor (`SELF_REPORT_STALENESS_THRESHOLD_DAYS`); one unused import (`Button` in `DashboardPage.tsx`); 3 unrelated pre-existing failures in `DashboardPage.test.tsx` (loading-state text, relative-timestamp text, pagination text — all UI-copy drift from an earlier "align with Rita's prototype" rewrite, distinct from the 2 View-Details-button failures that same file had, which this story's Task 3 fixed by restoring the Actions column).

**Test results (post code-review patches):** Backend — `test_provenance_detail.py` 9/9, `test_drill_down_endpoint.py` 10/10 (both including new code-review regression tests), 100% passing in isolation; full-suite run: 53 failed/273 passed/10 errors (up from the pre-Story-5-2 baseline of 48 failed/259 passed/10 errors) — every additional failure/pass is accounted for by this story's own new tests, and the file-level failures that appear only in the full mega-run are the same pre-existing cross-file asyncpg pool-corruption pattern documented since Epic 4 (confirmed both by isolation re-runs, all 100% passing, and by matching traceback signatures against already-documented instances). Frontend — `DashboardRow.test.tsx` 6/6, `ProvenanceDrillDownModal.test.tsx` 17/17, new `StatusBadge.test.tsx` 4/4, full suite 188/191 (only the 3 pre-existing unrelated `DashboardPage.test.tsx` failures). `npm install` was needed to actually install `date-fns` (was listed in `package.json` but missing from `node_modules`).

**Code review (2026-07-11):** 3 parallel adversarial layers (Blind Hunter, Edge Case Hunter, Acceptance Auditor) against the full diff + this story file. 1 decision-needed (AC6's 403 message text — user chose to keep the shared `require_hr_admin()` message for cross-endpoint consistency), 12 patches applied (AC5 both-buttons bug, Underlying Signal mislabeling, a `StatusBadge` bug that silently defeated this story's own Task 1 fix, an uncaught `ValueError` newly made reachable by this story, a dangling `aria-labelledby`, a missing stale-response guard, a docstring overclaim, this Dev Agent Record's own undercounted/overclaimed claims, a missing cross-surface invariant test, an AC4 text deviation, and a test-rigor gap), 5 deferred (all pre-existing or not-yet-reachable, logged to `deferred-work.md`), 8 dismissed (verified false positives or already-established codebase precedent). See Review Findings below for full detail.

### File List

**Backend:**
- `backend/app/assignments/schemas.py` — added `VERIFIED` to `ProvenanceLabel`; added `DrillDownResponse`
- `backend/app/assignments/repository.py` — added `get_assignment_scoped_to_hr_admin()`
- `backend/app/assignments/service.py` — added `get_drill_down_service()`
- `backend/app/assignments/router.py` — added `GET /{assignment_id}/progress/drill-down`
- `backend/app/progress/service.py` — added `ProvenanceDetail` dataclass, `get_provenance_detail()`, `STATUS_DISPLAY`/`PROVENANCE_HR_OVERRIDE` constants
- `backend/app/progress/repository.py` — eager-load `AssignmentOverride.set_by_user` in `get_active_override_for_assignment()` / `get_active_overrides_for_assignments()`
- `backend/app/dashboard/service.py` — refactored `_compute_status_and_provenance_from_data` to call `get_provenance_detail()`; removed dead `SELF_REPORT_STALENESS_THRESHOLD_DAYS`
- `backend/app/dashboard/schemas.py` — widened `ProvenanceEnum`/`AssignmentRowResponse.provenance` to include `"Not Started"`
- `backend/tests/test_provenance_detail.py` (new; +1 test from code review)
- `backend/tests/test_drill_down_endpoint.py` (new; +1 cross-surface invariant test from code review)

**Frontend:**
- `frontend/src/types/dashboard.ts` — widened `ProvenanceType`; added `DrillDownResponse`
- `frontend/src/lib/api/dashboardApi.ts` — added `getDrillDown()`
- `frontend/src/features/dashboard/DashboardRow.tsx` — restored Actions column / [View Details] button
- `frontend/src/features/dashboard/DashboardPage.tsx` — wired modal open/close state
- `frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx` (new; code review: AC5 both-buttons fix, Underlying Signal explicit per-branch mapping, dangling aria-labelledby fix, stale-response request-id guard, AC4 text fix)
- `frontend/src/features/dashboard/DashboardRow.test.tsx` (new; code review: strengthened keyboard test)
- `frontend/src/features/dashboard/ProvenanceDrillDownModal.test.tsx` (new; code review: +4 tests)
- `frontend/src/components/StatusBadge.tsx` (code review: fixed `percentage === 0` mislabeling bug)
- `frontend/src/components/StatusBadge.test.tsx` (new, code review)
- `frontend/package-lock.json` — `npm install` to actually install already-declared `date-fns`

**Docs/tracking:**
- `_bmad-output/implementation-artifacts/deferred-work.md` — new section logging Finding 2 and related pre-existing gaps
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — status transitions
- `_bmad-output/project-context.md` — story creation entry
