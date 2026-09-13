---
baseline_commit: 9072ac70
---

# Story 9.3: Frontend: Skill Assignment Dashboard Landing Page

Status: done

## Story

As an **HR Admin**,
I want to land on an org-wide dashboard when I log in,
so that I can get a temperature check before diving into individual assignments (FR-31, FR-32 display, UX-DR44).

## Scope Notes (read before starting)

1. **Frontend-only. Both backend endpoints already exist and are done.** `GET /api/dashboard/stats` (Story 9.1) and `GET /api/dashboard/segmentation` (Story 9.2) are both shipped, tested, and merged — confirmed directly against `backend/app/dashboard/router.py`. This story is pure UI: fetch both, render them. Do not add, modify, or duplicate any backend endpoint/schema/service code.

2. **Exact response shapes to consume (`backend/app/dashboard/schemas.py`) — copy these field names verbatim into new frontend types, do not rename or reshape them:**
   ```python
   class DashboardStatsResponse(BaseModel):
       total_employees: int
       total_skills_assigned: int
       total_completed: int
       completed_count: int
       in_progress_count: int
       not_started_count: int
       overall_percent: int

   class NeedsAttentionEntry(BaseModel):
       employee_id: uuid.UUID
       employee_name: str
       assignment_id: uuid.UUID
       skill_id: uuid.UUID
       skill_name: str

   class EmployeeSegmentationResponse(BaseModel):
       on_track_count: int
       in_progress_count: int
       needs_attention_count: int
       needs_attention: list[NeedsAttentionEntry]
   ```
   FastAPI serializes these as-is (snake_case, no aliasing) — this codebase has no camelCase transform layer anywhere in `lib/api/`, matching `types/dashboard.ts`'s existing `AssignmentRow` (`assignment_id`, `employee_name`, etc.). Keep the new frontend types snake_case to match.

3. **Routes to call, both already live, both HR-Admin-gated (401/403 handled identically to every other page in this app — no new client-side role check; this app has none anywhere, e.g. `/skills`/`/employees`/`/hr/dashboard` all rely on `RequireAuth` + backend 403, never a frontend role branch):**
   - `GET /api/dashboard/stats` → `DashboardStatsResponse`
   - `GET /api/dashboard/segmentation` → `EmployeeSegmentationResponse`
   Add both as new functions on the existing `dashboardApi` object in `frontend/src/lib/api/dashboardApi.ts` (mirror `getDashboard`'s exact shape: `apiClient.get<T>(url)` then `return response.data`) — do not create a new API-client file.

4. **New route: `/dashboard` (exact URL from the UX spec, §"Page Basics" → URL Route), NOT `/hr/dashboard`.** `/hr/dashboard` is the existing full-grid route (`Dashboard.tsx` → `DashboardPage`) and must be left completely untouched — this story does not modify it, its route, or any of its files.

5. **Critical scope boundary — do NOT touch `HrAppShell.tsx`'s nav wiring.** `epics.md`'s own "Recommended build order" note for Epic 9 is explicit: *"Story 9.5 (nav shell) last, since it repoints 'Dashboard' to Story 9.3's page, which must exist first."* Story 9.5's own AC also explicitly claims sole ownership: *"this is the one behavior change to an already-shipped nav entry this story [9.5] makes."* Story 9.3's own AC1 text ("click Dashboard in the left nav... lands on the new page") describes the **end state after 9.5 ships**, not this story's own scope — this story only needs to build the page and make it reachable at `/dashboard`. Verify AC1 in this story's tests via direct navigation to `/dashboard`, not via clicking the existing "Dashboard" nav link (which correctly still points to `/hr/dashboard` until Story 9.5 ships). Do not add a "Skill Assignments" 4th nav link either — also Story 9.5's job. This is a deliberate, documented scope decision, not a gap — do not "helpfully" wire the nav here; that would collide with Story 9.5's own explicit claim to that change and create merge/authorship confusion.

6. **Reuse `HrAppShell` as-is for the page chrome (nav sidebar + top bar), same as every other HR page (`EmployeesPage.tsx`, `SkillsPage.tsx`, `Dashboard.tsx`).** Do not build a new shell.

7. **Single self-contained page file, mirroring `EmployeesPage.tsx`'s shape (not `Dashboard.tsx`/`DashboardPage.tsx`'s split-into-a-ref-exposing-child-component shape — this page needs no imperative handle, no child modals to coordinate).** New file: `frontend/src/pages/hr/SkillAssignmentDashboard.tsx`. Fetch both endpoints in parallel on mount (`Promise.all`), track loading/error/loaded state with a `requestIdRef` race-guard exactly like `EmployeesPage.tsx`'s `refetch` (a slow/stale response must never clobber a newer one).

8. **Error message extraction: use this codebase's established `extractErrorMessage(err, fallback)` helper pattern** (duplicated locally per-file today — copied verbatim in `EmployeesPage.tsx`/`SkillsPage.tsx`/several `features/admin/*` files, not shared — follow that same precedent, do not introduce a new shared utility for this one story):
   ```ts
   function extractErrorMessage(err: unknown, fallback: string): string {
     if (err && typeof err === 'object' && 'response' in err) {
       const response = (err as { response?: { data?: { message?: string } } }).response;
       if (response?.data?.message) return response.data.message;
     }
     return fallback;
   }
   ```

9. **Page States (UX spec §"Page States", exact copy):**
   - **Loading:** skeleton cards/ring/chart in place; nav/top bar stay interactive (they're outside this component, inside `HrAppShell`, so this is automatic).
   - **Empty:** triggers when `total_employees === 0 OR total_skills_assigned === 0` (matches epics.md Story 9.3's 3rd AC: "zero active Employees or zero active Assignments"). Content area replaced with: `"Nothing to show yet — assign a Skill to get started."` + a `+ New Assignment` link/button to the Skill Assignment Flow route (check `App.tsx`/`AssignmentModal.tsx` usage elsewhere for the existing assignment-creation entry point — reuse it, don't build a new one; if the flow is only reachable via a modal opened from `/hr/dashboard` today with no standalone route, link to `/hr/dashboard` as the closest existing equivalent and note this in Dev Notes rather than inventing a new route).
   - **Error:** either request failing → content area replaced with `"Couldn't load dashboard data."` + a `Retry` button that re-runs both fetches.
   - **Loaded:** full page — stats row, Progress Ring, Segmentation pie, all populated from real response data, never hardcoded (epics.md AC1's explicit requirement).

10. **Visual hierarchy is a hard AC (epics.md Story 9.3, 2nd AC / UX-DR44) — Segmentation card must be visibly larger than the Progress Ring card, with a larger heading.** Use the UX spec's own **typography token table** (§"Typography Tokens") as the source of truth, not the Phase-5 prototype HTML's slightly different class choices (`06.1-Skill-Assignment-Dashboard.html` uses `text-lg`/`text-xl` for the two headings; the written Phase-4 spec's token table says `heading-md`/20px for Progress and `heading-lg`/24px for Segmentation — a real discrepancy between the two artifacts, noticed during story authoring). Follow the written spec (the canonical Phase 4 deliverable): Progress heading = `text-xl font-bold` (20px/700), Segmentation heading = `text-2xl font-bold` (24px/700), page H1 = `text-3xl font-black` (30px/900, both artifacts agree here). Layout: `grid-cols-1 lg:grid-cols-[1fr_1.5fr]` for the Progress/Segmentation row (matches the spec's 450px:680px ≈ 1:1.51 ratio); stats row `grid-cols-1 md:grid-cols-3`.

11. **Progress Ring and Segmentation Pie: use a CSS `conic-gradient` on a rounded div, not a charting library** (this codebase has zero chart/graphing dependencies in `package.json` — do not add one for this story). The Phase-5 prototype (`06.1-Skill-Assignment-Dashboard.html`, JS section) already has a working, directly-portable `conicGradient(stops)` helper — port its logic into a small TS helper (e.g. inline in the new page file; this is the only place it's used, so no shared util needed). Ring center shows `{overall_percent}%` as text (already guarded server-side against zero-assignment division, per Story 9.1 Task 10). Segment colors — match this app's existing Tailwind palette (not the prototype's unused `talentpilot-*` custom color, which only exists in the standalone prototype's own Tailwind config, never in this app's real `tailwind.config`): Completed `#1d4ed8` (blue-700), In Progress `#93c5fd` (blue-300), Not Started `#e5e7eb` (gray-200) for the ring; On Track `#16a34a` (green-600), In Progress `#f59e0b` (amber-500), Needs Attention `#dc2626` (red-600) for the pie — same hex values the prototype already validated, just mapped onto colors this app's other components already use elsewhere (`StatusBadge.tsx`, `EmployeesPage.tsx`'s green/gray badges). These chart-fill colors are not theme-reactive (same hex in light/dark mode) — recomputing the gradient on theme change is out of scope; only surrounding text/card chrome need `dark:` classes, matching every other themed component since Story 8.1.

12. **The "Needs Attention" segment/legend row in THIS story is display-only — no button, no click handler, no popover, no "Click to see who" hint, regardless of count.** That entire interactive layer (UX-DR45/UX-DR46, the popover, the hint text, the `aria-label`) is Story 9.4's job, not this one — epics.md's own Story 9.3 ACs never mention clicking or a popover at all; Story 9.4's ACs own that behavior explicitly. Render it as a plain legend row identical in shape to On Track/In Progress (colored dot + `"Needs Attention — {N}"` text) every time. Do not build a `<button>`, `aria-expanded`, or any popover markup here — that would preempt Story 9.4's own component and create merge conflict/rework.

13. **Accessibility (epics.md Story 9.3's last AC + UX spec §"Accessibility Requirements"):** every stat, ring segment, and pie segment must show as **text + numbers**, never color-only (NFR-A2). This is naturally satisfied by rendering legend text (`"Completed — {N}"`, etc.) alongside every colored dot — do not rely on color alone anywhere. Loading/empty/error states should be reachable by assistive tech the same way `EmployeesPage.tsx`/`DashboardPage.tsx` already handle theirs (plain text content, no `aria-live` requirement here since — unlike `DashboardPage.tsx`'s poll-driven live region — this page has no background polling per the UX spec's own "Real-Time Updates Architecture" section: *"For POC: No polling needed... no requirement exists for it to auto-refresh."*). Do not add polling.

14. **Route registration in `frontend/src/App.tsx`:** add `<Route path="/dashboard" element={<RequireAuth><SkillAssignmentDashboard /></RequireAuth>} />`, same `RequireAuth`-wrapping pattern as every other protected route in this file. Import path: `@/pages/hr/SkillAssignmentDashboard`.

15. **Do not touch `DashboardStub.tsx`, `AssignmentsList.tsx`, or `DashboardRow.tsx`.** All three are confirmed dead/unreachable code (Story 5.7's Change Log, re-confirmed by Story 8.1's retro) — out of scope, do not delete or modify them in this story either.

## Acceptance Criteria

**AC1 — Landing page renders real data (FR-31, FR-32, NFR-L6):**
**Given** I log in as HR Admin, or click "Dashboard" in the left nav
**When** the page loads
**Then** I land on the new Skill Assignment Dashboard (not the full grid) within the NFR-L6 2-second budget, showing Total Employees/Total Skills Assigned/Total Completed, the Assignment Progress ring, and the Employee Segmentation pie chart — all populated from Stories 9.1/9.2's endpoints, never hardcoded.
*(This story verifies AC1 via direct navigation to `/dashboard` — see Scope Note 5 for why the nav-click path itself is Story 9.5's scope, not this one's.)*

**AC2 — Visual hierarchy (UX-DR44):**
**Given** the page's visual hierarchy
**When** it renders
**Then** the Employee Segmentation pie chart is visually larger (card width and heading size) than the Assignment Progress ring — the three stats and the ring are secondary/supporting, not competing for primary attention.

**AC3 — Three-state discipline (FR-4, FR-8 precedent):**
**Given** the page while data is loading, or if it fails to load, or if there is genuinely nothing to show (zero active Employees or zero active Assignments)
**When** each of those conditions applies
**Then** a distinct Loading / Error (with Retry) / Empty (with a link into the Skill Assignment Flow) state renders.

**AC4 — Text/number labeling, never color-only (NFR-A2):**
**And** every stat, the ring segments, and the pie segments are labeled with text/numbers, never color-only.

## Tasks / Subtasks

- [x] **Task 1: Frontend types** (AC1) — `frontend/src/types/dashboard.ts`
  - [x] Add `DashboardStatsResponse`, `NeedsAttentionEntry`, `EmployeeSegmentationResponse` interfaces, field-for-field identical to the backend Pydantic schemas (Scope Note 2).

- [x] **Task 2: API client methods** (AC1) — `frontend/src/lib/api/dashboardApi.ts`
  - [x] Add `getDashboardStats()` → `GET /api/dashboard/stats`.
  - [x] Add `getEmployeeSegmentation()` → `GET /api/dashboard/segmentation`.
  - [x] Export both from the existing `dashboardApi` object.

- [x] **Task 3: `SkillAssignmentDashboard` page component** (AC1, AC2, AC3, AC4) — new `frontend/src/pages/hr/SkillAssignmentDashboard.tsx`
  - [x] Wrap content in `HrAppShell` (Scope Note 6).
  - [x] Parallel-fetch both endpoints on mount via `Promise.all`, with a `requestIdRef` race-guard (Scope Note 7).
  - [x] Implement Loading / Error+Retry / Empty+CTA / Loaded states (Scope Note 9).
  - [x] Loaded state: stats row (3 cards), Progress Ring card (secondary, smaller heading), Segmentation card (primary, larger heading + larger card) — layout/typography per Scope Note 10.
  - [x] Render Ring/Pie via a local `conicGradient` helper (Scope Note 11); Needs Attention legend row is plain text always, no interactivity (Scope Note 12).
  - [x] Footer: `"App v0.1.0"` (matches every other HR page's existing footer convention, e.g. `DashboardPage.tsx`'s identical line).
  - [x] Empty-state CTA resolved: links to `/hr/dashboard` (confirmed via grep — `AssignmentModal` has no standalone route anywhere in this codebase, only opened from `Dashboard.tsx`/dead `DashboardStub.tsx`; per Dev Notes, `/hr/dashboard` is the closest existing entry point).

- [x] **Task 4: Route registration** (AC1) — `frontend/src/App.tsx`
  - [x] Add `/dashboard` route, `RequireAuth`-wrapped, per Scope Note 14. Left `/hr/dashboard` and every existing route untouched (diff-verified).

- [x] **Task 5: Tests** (all ACs) — new `frontend/src/tests/SkillAssignmentDashboard.test.tsx`
  - [x] Mock `dashboardApi.getDashboardStats`/`getEmployeeSegmentation` (module mock, mirroring `EmployeesPage.test.tsx`'s `vi.mock('@/lib/api/employeesApi', ...)` pattern).
  - [x] Loaded state: asserts all 3 stat values, ring `{percent}%` label + 3 legend rows with counts, pie's 3 legend rows with counts, Needs Attention rendered as non-interactive text (no `role="button"`, no popover) regardless of count.
  - [x] Loading state renders before data resolves.
  - [x] Empty state: `total_employees: 0` (and separately `total_skills_assigned: 0`) → empty copy + CTA link, no ring/chart rendered.
  - [x] Error state: a rejected fetch → error copy + Retry button; clicking Retry re-invokes both API functions.
  - [x] Visual-hierarchy assertion: Segmentation heading has `text-2xl`, Progress heading has `text-xl` (not `text-2xl`) — per Scope Note 10's token choice.
  - [x] **Race-guard subtask dropped, not skipped silently:** investigated during implementation and found not independently testable through this component's real UI — the only second-fetch trigger is the Retry button, which is only reachable after the first request has already settled (rejected), so a same-instance stale-over-fresh race can't actually occur here (unlike `EmployeesPage`'s filter-driven re-fetch, which also has no such test either — confirmed by grep, this codebase doesn't test this pattern anywhere despite several components sharing it). Writing a "passing" test that doesn't genuinely exercise the guard would be a false-confidence test, not real coverage — omitted rather than faked, per the "no lying/cheating about completion" rule. The `requestIdRef` guard itself is still implemented, matching this codebase's established defensive convention.

- [x] **Task 6: Regression check**
  - [x] Frontend: `vitest run` → 411 passed (404 pre-existing + 7 new), 0 failed, zero regressions. `tsc --noEmit` → 31 pre-existing errors, unchanged, none in new/modified files. `vite build` → clean, 537 modules (536 + 1 new page).
  - [x] Live-verified via Playwright (Chromium installed ad hoc, removed after use) against rebuilt Docker containers (both `frontend` and `backend` images were stale relative to HEAD and needed rebuilding before `/api/dashboard/segmentation` responded — see Debug Log): real HR Admin login → `/dashboard` renders live data (5 Employees, 6 Assignments, correct ring/pie percentages) in both light and dark theme; a non-HR-Admin (Employee) session hitting `/dashboard` cleanly shows the Error state with the backend's actual 403 message via Retry, not a crash — confirming the "no frontend role gate, rely on backend + generic error branch" decision (Scope Note 3) works end-to-end.

### Review Findings

_(`bmad-code-review`, 2026-09-13, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor, run against the uncommitted diff with this story file as spec context.)_

- [x] [Review][Patch] Empty state drops the Stats row entirely, contradicting the UX spec's explicit instruction. `06.1-skill-assignment-dashboard.md`'s own Page States table (line 216) reads "**Stats show zeros**; ring/pie chart area replaced with: 'Nothing to show yet...'" — i.e. only the ring/pie region should be swapped for the empty-state message, not the whole content area. This story's own Scope Note 9 paraphrased that as merely "Content area replaced with...", silently dropping the "stats show zeros" clause, and the implementation (`SkillAssignmentDashboard.tsx`, Empty branch) follows that paraphrase rather than the cited source. No test caught this since none asserted on stat-card presence/absence in the empty branch. [frontend/src/pages/hr/SkillAssignmentDashboard.tsx] **Fixed:** restructured so the stats row renders unconditionally whenever `stats`/`segmentation` have loaded, with the Empty message and the Progress/Segmentation grid as mutually-exclusive siblings beneath it (not nested inside one another) — `dashboard-state-loaded`'s testid now denotes specifically the non-empty ring/pie grid, `dashboard-state-empty` the swapped-in message, matching the spec's literal state model. New test assertion added confirming the stats row (with zero values) renders alongside the Empty message and that the ring/segmentation cards do not.
- [x] [Review][Patch] No test exercises `extractErrorMessage`'s real `.response.data.message` extraction path — the only error-state test uses a bare `Error('network down')` with no `.response`, so it only ever exercises the fallback-string branch, not the "shows the backend's real message" behavior the Completion Notes claim was live-verified. [frontend/src/tests/SkillAssignmentDashboard.test.tsx] **Fixed:** added a test rejecting with the exact `{ response: { data: { message: ... } } }` shape this app's centralized error envelope (`backend/app/core/errors.py`) actually returns, asserting the real message renders.
- [x] [Review][Patch] The six chart-fill hex colors (`#1d4ed8`, `#93c5fd`, `#e5e7eb`, `#16a34a`, `#f59e0b`, `#dc2626`) are duplicated as inline string literals across the ring/pie/legend JSX with no single source of truth — a future consistency change (e.g. Story 9.4 reusing "Needs Attention red" in its popover) has nothing to import from. [frontend/src/pages/hr/SkillAssignmentDashboard.tsx] **Fixed:** extracted to a single `CHART_COLORS` module-level constant, referenced from every ring/pie/legend call site.

Full regression re-verified after patches: frontend 412/412 (404 baseline + 8 tests, up from 7 — one new test added by the patches), `tsc --noEmit` unchanged at 31 pre-existing errors, `vite build` clean. Live-re-verified against a rebuilt Docker frontend: the Loaded state still renders identically (5 Employees, 6 Assignments, correct ring/pie percentages).
- [x] [Review/Defer] `EmployeeSegmentationResponse.needs_attention` (the full flagged-Assignment list) is fetched on every page load but entirely unused here — only `needs_attention_count` is read. This is an unavoidable consequence of Story 9.2's existing single-endpoint response shape (this story cannot add a leaner backend response without violating its own no-backend-changes scope), and directly extends Story 9.2's own already-logged `deferred-work.md` entry about the list's unbounded growth. Not actionable within this story. — deferred, pre-existing
- [x] [Review/Dismiss — verified false] `extractErrorMessage` was flagged as possibly assuming the wrong envelope key (`message` vs. a more conventional `detail`) with no test locking in the real 403 path. Verified directly against `backend/app/core/errors.py:43,63` — the centralized `http_exception_handler` wraps every raised exception (including plain `HTTPException.detail`) into `_error_body(...)`, which always emits the text under `"message"`. Also independently confirmed live: a real Employee-role Playwright session hitting `/dashboard` rendered the exact backend text "This action requires an HR Admin session" via this exact code path.
- Dismissed as non-issues after verification, each matching an established, already-accepted codebase-wide pattern rather than a defect this story introduced: `extractErrorMessage` silently falling back to the generic message when `response.data.message` is empty/non-string (verbatim copy of the pattern already used identically in `EmployeesPage.tsx`/`SkillsPage.tsx`/several `features/admin/*` files, per this story's own Scope Note 8); no unmount-guard around the `Promise.all` fetch (matches `EmployeesPage.tsx`'s identical `requestIdRef`-only pattern, no `isMounted` flag there either); no fetch timeout for an indefinitely-pending request (no page in this codebase has one); `conicGradient`/`isEmpty` having no defensive handling for negative/NaN/undefined backend fields (this codebase never runtime-validates API responses against a schema anywhere — trusts the FastAPI `response_model` contract everywhere else too); `overall_percent` rendered without client-side rounding/clamping (the backend, per Story 9.1 Scope Note 10, already computes `round(...)` server-side — re-rounding client-side would be redundant, and AC1 explicitly requires never re-deriving values independently); no test exercises `App.tsx`'s actual route-to-component wiring (no page in this codebase has such a test — confirmed, no `App.test.tsx` exists); the heading-size test asserting Tailwind class names rather than computed pixel size (matches this codebase's own established test-assertion style elsewhere, e.g. `ThemeToggle.test.tsx`/`StatusBadge.test.tsx`); no automated test for the "no frontend role gate" decision (no HR-only page in this codebase tests backend role-enforcement from the frontend test suite; verified live instead, matching this codebase's live-verification convention for cross-cutting auth behavior); the `dashboardApi` test mock being untyped against the real module's full shape (identical to `EmployeesPage.test.tsx`'s own `vi.mock` convention); the Empty-state CTA linking to `/hr/dashboard` rather than a direct assignment-creation flow (already a documented, reasoned decision in this story's own Dev Notes/Completion Notes — no standalone assignment-creation route exists anywhere in this codebase, confirmed by grep); two "Dashboard"-titled pages existing simultaneously with no distinguishing affordance (the deliberate, documented 9.3/9.5 interim-sequencing scope boundary, not an oversight); the tracking-doc narrative appearing in `sprint-status.yaml`/`project-context.md`/this story file (matches this project's own established documentation convention for every prior story, e.g. Stories 9.1/9.2's identical triple-narrative shape); a claimed extra `act()`-warning risk from the loading-state test's unresolved promise (re-ran that test in isolation — only the pre-existing, unrelated `AuthProvider` warning appeared, no additional warning); no disabled/pending affordance on the Retry button during an in-flight request (the `requestIdRef` guard already prevents any stale-data correctness issue from a double-click; matches `DashboardPage.tsx`'s own Retry button, which has the same gap).

## Dev Notes

### Both consumed endpoints are already done — this is the first purely-frontend story to touch the `dashboard/` domain since Story 8.1

Stories 9.1 (`GET /api/dashboard/stats`) and 9.2 (`GET /api/dashboard/segmentation`) are both `done`, fully tested (718 backend tests passing as of Story 9.2), and require zero changes here. Do not re-derive Status/Provenance/segmentation logic on the frontend — every number this page shows comes directly from these two responses, verbatim (AC1's explicit "never hardcoded" / "never re-derived independently" requirement, inherited from the backend stories' own AD-3 discipline).

### The 9.3/9.5 nav-wiring scope boundary (read Scope Note 5 first)

This is the most important judgment call in this story. `epics.md`'s Story 9.3 AC1 text literally describes the fully-wired end state (nav click → new page), but the same document's Story 9.5 AC and its own "Recommended build order" note both explicitly assign that specific wiring change to Story 9.5, "last, since it repoints 'Dashboard' to Story 9.3's page, which must exist first." Building the page at a real, directly-navigable `/dashboard` route (not a `/dev/*` throwaway route, since the UX spec itself specifies `/dashboard` as this page's real URL) satisfies "must exist first" while leaving Story 9.5's one claimed behavior change untouched. If a future reviewer flags AC1 as "not fully met" because clicking the nav's Dashboard link doesn't yet reach this page, point back to this note and Story 9.5's own explicit scope claim — this is an epics.md-internal sequencing decision, not an implementation gap.

### Typography discrepancy between the Phase 4 spec and the Phase 5 prototype

Noticed during story authoring, not previously documented: `06.1-skill-assignment-dashboard.md`'s own "Typography Tokens" table specifies `heading-md`(20px) for the Progress heading and `heading-lg`(24px) for the Segmentation heading, but the later-built prototype HTML (`06.1-Skill-Assignment-Dashboard.html`) uses `text-lg`(18px)/`text-xl`(20px) instead — one size smaller at each step. Follow the written spec (Scope Note 10) since it's the canonical Phase 4 UX deliverable and the prototype is a downstream illustrative artifact, not itself a spec revision.

### Empty-state CTA target is not fully resolved — verify at implementation time

The UX spec's Empty-state CTA is `"+ New Assignment"` linking to "the Skill Assignment Flow (03.1)". In this real codebase (unlike the prototype's standalone `03.1-Skill-Assignment-Flow.html` page), assignment creation is `AssignmentModal.tsx`, a modal opened from within `Dashboard.tsx`/`DashboardStub.tsx` — there is no standalone routed page for it. Before implementing, grep `App.tsx`/`AssignmentModal.tsx` usage to confirm whether any route opens it directly; if none does, the pragmatic choice is a link to `/hr/dashboard` (the existing entry point that already has the "+ New Assignment" button wired) rather than inventing a new modal-triggering mechanism on this page — document whichever choice is made here in Completion Notes.

### Previous story's pattern to lean on

`EmployeesPage.tsx` is the closest existing precedent for this story's overall shape: a single self-contained page component wrapped in `HrAppShell`, `useCallback`-wrapped fetch with a `requestIdRef` guard, a locally-duplicated `extractErrorMessage` helper, module-mocked in its test file. Follow it directly rather than `DashboardPage.tsx`'s more complex ref-handle/poll/modal-coordination shape, which this page doesn't need (no polling per Scope Note 13, no child modals to coordinate).

### Project-context.md entry required before this story can be marked done

Per the Epic 8 retrospective's action item (a recurring gap flagged across Stories 6.6-7.3, 7.7, and again 8.1): this story must get its own `project-context.md` entry summarizing what was built, mirroring the existing Story 9.1/9.2 entries, before/alongside marking it done.

## Architecture Compliance

- AR-26: read-composition owned by `dashboard/` (backend, already satisfied by Stories 9.1/9.2 — this story adds no backend code).
- AR-8 (module dependency direction): unaffected — this story only adds frontend read calls to already-existing, already-allowed endpoints.
- FR-29 (nav shell): explicitly NOT amended by this story (Scope Note 5) — Story 9.5's job.

## References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 9.3] — full AC text, Epic 9 scope, build-order note
- [Source: _bmad-output/planning-artifacts/epics.md#Story 9.5] — the nav-repoint story this one must not preempt
- [Source: _bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md#FR-31/FR-32] — org-wide stats/segmentation requirements
- [Source: _bmad-output/C-UX-Scenarios/06-ritas-pulse-check/06.1-skill-assignment-dashboard/06.1-skill-assignment-dashboard.md] — full UX design spec: layout, object IDs, states, typography tokens, accessibility requirements
- [Source: _bmad-output/E-Development/01-Ritas-Trust-Call-Prototype/06.1-Skill-Assignment-Dashboard.html] — directly portable `conicGradient`/`computeAssignmentStatus` reference implementation (illustrative prototype, not spec-authoritative where it conflicts with the .md above — see Dev Notes)
- [Source: _bmad-output/implementation-artifacts/9-1-backend-org-wide-stats-and-assignment-progress-endpoint.md] — `DashboardStatsResponse` contract, done
- [Source: _bmad-output/implementation-artifacts/9-2-backend-employee-segmentation-endpoint.md] — `EmployeeSegmentationResponse` contract, done
- [Source: backend/app/dashboard/schemas.py] — exact response schemas to mirror in `types/dashboard.ts`
- [Source: backend/app/dashboard/router.py] — exact route paths (`/api/dashboard/stats`, `/api/dashboard/segmentation`)
- [Source: frontend/src/pages/hr/EmployeesPage.tsx] — page-shape precedent (fetch/error/race-guard pattern) to follow
- [Source: frontend/src/features/dashboard/DashboardPage.tsx] — existing loading/error/empty three-state precedent, footer text convention
- [Source: frontend/src/components/layout/HrAppShell.tsx] — shared nav shell to reuse unmodified; `NAV_LINKS` is Story 9.5's to change, not this story's
- [Source: frontend/src/App.tsx] — existing route registration pattern
- [Source: frontend/src/lib/api/client.ts] — shared `apiClient` axios instance
- [Source: frontend/src/types/dashboard.ts] — existing snake_case type convention to extend

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5

### Debug Log References

- `npx vitest run src/tests/SkillAssignmentDashboard.test.tsx` → 7/7 passed on first green run (TDD: wrote the page component and tests together, iterating red→green per state branch — loading, loaded, Needs-Attention-non-interactive, visual-hierarchy, both empty variants, error+retry).
- `npx vitest run` (full suite) → 411 passed (404 pre-existing + 7 new), 0 failed. Baseline of 404 confirmed against Story 8.1's last-recorded frontend count (no frontend changes landed in Stories 9.1/9.2, both backend-only).
- `npx tsc --noEmit` → 73 lines / 31 `error TS` occurrences, identical to the long-standing documented baseline; none in `SkillAssignmentDashboard.tsx`, `dashboardApi.ts`, `types/dashboard.ts`, or `App.tsx`.
- `npx vite build` → clean, 537 modules (536 baseline + 1 new page component), no new warnings beyond the pre-existing >500kB chunk-size notice.
- **Real deployment gap found and fixed during live verification, not anticipated in Scope Notes:** both `talentpilot-ui` and `talentpilot-api` Docker images were stale relative to HEAD — `docker ps` showed `talentpilot-api` "healthy" but a live `curl` to `/api/dashboard/segmentation` (with a valid session cookie) returned 404, even though Stories 9.1/9.2 are marked `done` in `sprint-status.yaml` and the route exists in the checked-out `backend/app/dashboard/router.py`. Root cause: the running containers were built from an older image predating those commits' inclusion in the image layer, not a code defect. Fixed by `docker compose build backend frontend && docker compose up -d backend frontend`; re-verified `/api/dashboard/segmentation` returns 200 with real data afterward. This is an environment/ops finding, not a story-code fix — no source file changed because of it — but it's recorded here since it would otherwise look like a false "story 9.2 regression."
- Playwright (Chromium, installed ad hoc via a throwaway `npm install playwright` + `npx playwright install chromium` outside the repo, removed after use) against the rebuilt containers: (1) HR Admin (`rita@sails.example.com`) login → direct navigation to `/dashboard` → Loaded state with real live data (5 Employees, 6 Assignments, Assignment Progress 0% with a genuine partial ring, Employee Segmentation 0 On Track / 2 In Progress / 0 Needs Attention) in both light and dark theme (toggled via `[data-testid="theme-toggle"]`), screenshots captured; (2) Employee (`casey@sails.example.com`) session → `/dashboard` → clean Error state showing the backend's real 403 message ("This action requires an HR Admin session") with a Retry button, no crash, no frontend role-check code needed.

### Completion Notes List

- Both endpoints this page consumes (`GET /api/dashboard/stats`, `GET /api/dashboard/segmentation`) were already shipped by Stories 9.1/9.2 — this story added zero backend code, exactly as scoped.
- New types (`DashboardStatsResponse`, `NeedsAttentionEntry`, `EmployeeSegmentationResponse`) added to `types/dashboard.ts`, field-for-field matching the live backend Pydantic schemas (verified by reading `backend/app/dashboard/schemas.py` directly, not assumed from the story files' prose).
- `dashboardApi.getDashboardStats`/`getEmployeeSegmentation` added to the existing `dashboardApi` object, mirroring `getDashboard`'s exact `apiClient.get<T>(url)` shape.
- New self-contained page `frontend/src/pages/hr/SkillAssignmentDashboard.tsx`, modeled directly on `EmployeesPage.tsx`'s fetch/error/race-guard shape (not `DashboardPage.tsx`'s more complex ref-handle/poll/modal shape, which this page doesn't need). Implements all four UX-spec page states (Loading/Error+Retry/Empty+CTA/Loaded), a locally-scoped `conicGradient` helper ported from the Phase-5 prototype for the Progress Ring and Segmentation Pie (no chart library added), and renders the Needs Attention legend row as permanently non-interactive plain text (Story 9.4's job to add the click/popover layer).
- **Deliberate scope boundary held, not just noted:** did not touch `HrAppShell.tsx`'s `NAV_LINKS` or the existing "Dashboard" nav link's target — confirmed via `git diff` that only the 5 files below changed. The new `/dashboard` route is reachable only by direct navigation until Story 9.5 repoints the nav, exactly as this story's own Scope Note 5/Dev Notes documented as the intended sequencing.
- **Typography discrepancy resolved as planned:** used the UX spec's written typography-token table (`text-xl`/20px for Progress, `text-2xl`/24px for Segmentation) over the Phase-5 prototype HTML's slightly smaller classes, per this story's own Dev Notes reasoning.
- **Empty-state CTA question resolved during implementation:** grepped every `AssignmentModal` usage in the codebase — it's opened only from `Dashboard.tsx` (live, at `/hr/dashboard`) and the confirmed-dead `DashboardStub.tsx`; no standalone route exists. Linked the Empty-state CTA to `/hr/dashboard` per the story's own documented fallback plan.
- **Race-guard test subtask deliberately not completed as originally scoped** — see Task 5's own note. Investigated rather than skipped silently: this page's only second-fetch trigger (Retry) is unreachable until the first request has already settled, so the classic stale-response race this guard defends against cannot actually be exercised through the real UI. The `requestIdRef` guard code itself was still implemented (matches `EmployeesPage.tsx`'s established convention), just not independently unit-tested, since doing so would have required simulating an unrealistic internal state rather than testing real behavior.
- **Real deployment gap found (see Debug Log):** both Docker images were stale relative to `HEAD`, silently masking Story 9.2's already-shipped `/segmentation` endpoint during initial live verification. Fixed by rebuilding both images; not a code change, recorded for traceability since it could otherwise be mistaken for a regression in this story's own testing.
- Zero regressions: full frontend suite 411/411 passing (404 baseline + 7 new), `tsc --noEmit` unchanged at the 31-error baseline, `vite build` clean.

### File List

**Modified:**
- `frontend/src/types/dashboard.ts` — added `DashboardStatsResponse`, `NeedsAttentionEntry`, `EmployeeSegmentationResponse`
- `frontend/src/lib/api/dashboardApi.ts` — added `getDashboardStats`, `getEmployeeSegmentation`, exported both
- `frontend/src/App.tsx` — added `/dashboard` route (`RequireAuth`-wrapped)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — story/epic status tracking
- `_bmad-output/project-context.md` — Story 9.3 entry (required before this story can be marked done, per the Epic 8 retro's blocking gate)

**Added:**
- `frontend/src/pages/hr/SkillAssignmentDashboard.tsx` — new Skill Assignment Dashboard landing page (post-review: Empty state restructured to keep the stats row visible; chart colors extracted to `CHART_COLORS`)
- `frontend/src/tests/SkillAssignmentDashboard.test.tsx` — 8 tests (7 original + 1 added by code review: real-backend-error-message extraction; the Empty-state test was also strengthened to assert the stats row/ring/segmentation presence)

**No changes to:**
- Any backend file (`backend/`) — both consumed endpoints already existed (Stories 9.1/9.2), confirmed via direct code read
- `frontend/src/components/layout/HrAppShell.tsx` — nav wiring is Story 9.5's scope, deliberately untouched here
- `frontend/src/pages/hr/Dashboard.tsx`, `frontend/src/features/dashboard/DashboardPage.tsx`, `/hr/dashboard` route — the existing full-grid page, untouched
- `frontend/src/pages/hr/DashboardStub.tsx`, `frontend/src/features/dashboard/AssignmentsList.tsx`, `frontend/src/features/dashboard/DashboardRow.tsx` — confirmed dead code, out of scope

## Change Log

- 2026-09-13: Story created (`bmad-create-story`), at user's explicit request to start API + UI development for Story 9.3, referencing the UX design. Analyzed epics.md's Epic 9 (Stories 9.1-9.5), the full UX design spec (`06.1-skill-assignment-dashboard.md`) and its companion Phase-5 prototype HTML, both already-done backend stories' contracts (9.1/9.2, verified directly against the live `backend/app/dashboard/schemas.py`/`router.py`), and the current frontend's routing/nav/page-shape conventions (`App.tsx`, `HrAppShell.tsx`, `EmployeesPage.tsx`, `DashboardPage.tsx`). Confirmed this story is frontend-only — both consumed endpoints already exist and are `done`. Found and resolved two real judgment calls before they could become implementation disasters: (1) a genuine scope tension where this story's own epics.md AC1 text describes a fully-wired nav-click path that epics.md's own Story 9.5 AC and build-order note explicitly assign to a later story — resolved by scoping this story to a real `/dashboard` route reachable by direct navigation, deliberately not touching `HrAppShell.tsx`'s nav wiring; (2) a real drift between the UX spec's own written typography-token table (20px/24px headings) and its companion prototype HTML (18px/20px) — resolved in favor of the written spec as the canonical artifact. Also flagged an unresolved question for the dev agent to settle during implementation: the Empty-state CTA's exact link target, since this codebase's real assignment-creation flow is a modal, not the prototype's standalone routed page.
- 2026-09-13: Implementation complete (`bmad-dev-story`/Amelia, same session as creation). All 6 tasks done: new types/API-client methods (zero backend changes needed), new `SkillAssignmentDashboard.tsx` page (Loading/Error/Empty/Loaded states, conic-gradient Progress Ring + Segmentation Pie, Needs Attention rendered display-only), new `/dashboard` route. Resolved both open questions from story creation (Empty-state CTA → `/hr/dashboard`; typography → written spec's tokens). 7 new tests, all passing; one originally-scoped test subtask (stale-response race guard) deliberately dropped after investigation showed it wasn't genuinely testable through this page's real UI, rather than faked — documented in Task 5 and Completion Notes. Zero regressions: 411/411 frontend tests (404 + 7 new), `tsc --noEmit` unchanged at 31 pre-existing errors, `vite build` clean. **Real, unanticipated finding during live verification:** both `talentpilot-api` and `talentpilot-ui` Docker containers were running stale images that predated Stories 9.1/9.2's and this story's own commits — `/api/dashboard/segmentation` 404'd against the live "healthy" backend container despite the route existing in the checked-out code, until both images were rebuilt. Live-verified end-to-end afterward via Playwright (installed ad hoc, removed after use): real HR Admin login renders live org data correctly in both light/dark theme; a non-HR-Admin session hitting `/dashboard` cleanly shows the Error state with the backend's real 403 message, confirming the deliberate no-frontend-role-gate decision. Status → `review`.
- 2026-09-13: Code review (`bmad-code-review`, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor, run against the uncommitted diff with this story file as spec context). 0 decision-needed, 3 patches applied, 1 deferred (`deferred-work.md`), ~14 dismissed as noise/already-accepted patterns after verification (not waved off — e.g. the `extractErrorMessage` "assumes wrong envelope key" concern was checked directly against `backend/app/core/errors.py` and confirmed false; several others matched this codebase's own established conventions elsewhere, verified by grep/read, not assumed). **Most consequential finding** (Acceptance Auditor): the Empty state was dropping the entire stats row, contradicting the UX spec's own literal "Stats show zeros" instruction — this story's own Scope Note 9 had silently paraphrased that clause away. Fixed by restructuring so the stats row renders unconditionally alongside either the Empty message or the Progress/Segmentation grid (now mutually-exclusive siblings, not nested). Two other patches: added a test locking in `extractErrorMessage`'s real `.response.data.message` extraction path (previously only the generic-fallback path was tested, despite Completion Notes claiming the real-message path was live-verified); extracted the six chart-fill hex colors to a single `CHART_COLORS` constant. One real, non-actionable finding deferred: `EmployeeSegmentationResponse.needs_attention`'s full list is fetched but unused by this story (extends Story 9.2's own already-logged unbounded-list deferral; not fixable without a backend change, out of this story's scope). Full regression re-verified: frontend 412/412 (404 baseline + 8 tests, +1 from the patch), `tsc --noEmit` unchanged at 31 pre-existing errors, `vite build` clean. Live-re-verified against a rebuilt Docker frontend: Loaded state unchanged and correct. Status → `done`.
