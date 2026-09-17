---
baseline_commit: f97d27f6
---

# Story 10.4: Employee Experience Distribution Panel

Status: done

## Story

As an **HR Admin**,
I want to see headcount broken down by years of experience with a click-through to the matching Employees,
So that I can understand the roster's experience mix at a glance, separate from readiness status (FR-36).

## Acceptance Criteria

1. **Given** `employees.experience` (currently free text, e.g. "5+ yrs")
   **When** this story's migration runs
   **Then** it adds a numeric `experience_years` field (nullable) alongside the existing free-text `experience` field, which is unaffected — exact input UX for capturing it (a new numeric input alongside the free-text field vs. replacing it) is a Story 10.4 implementation decision, not specified further here

2. **Given** the active roster's `experience_years` values
   **When** the Experience Distribution panel loads (new `GET /api/dashboard/experience-distribution` or equivalent read-composition endpoint, owned by `dashboard/` per AR-26's existing "no new table" pattern)
   **Then** it returns counts for exactly 7 contiguous, exhaustive buckets — **0–4, 5–7, 8–9, 10–11, 12–14, 15–19, 20+** years — confirmed 2026-09-15, and excludes any Employee with a null `experience_years` from every bucket rather than guessing

3. **Given** this panel and FR-32's existing Employee Segmentation pie chart (On Track/In Progress/Needs Attention, Story 9.2/9.3)
   **When** both are visible
   **Then** they render as visually and semantically distinct panels with distinct names/headings — this FR does not modify FR-32's chart in any way

4. **Given** an HR Admin clicks a bucket's count
   **When** the click is handled
   **Then** it shows the list of Employees in that bucket, paginated at **15 per page**, matching FR-25's existing roster pagination convention

5. **And** any chart rendering of this panel follows the same non-color-only rule as FR-32's pie chart (§8/NFR-A2)

## Tasks / Subtasks

- [x] Task 1: `experience_years` column, migration, and CRUD plumbing (AC: 1)
  - [x] `backend/alembic/versions/016_add_employee_experience_years.py` — new nullable `Integer` column on `employees`, no backfill (no reliable source to derive it from the free-text `experience` column; every pre-existing row starts null)
  - [x] `backend/app/employees/models.py` — `experience_years = Column(Integer, nullable=True)`, independent of the existing `experience` column
  - [x] `backend/app/employees/schemas.py` — `experience_years: int | None = Field(default=None, ge=0)` added to `CreateEmployeeRequest`, `UpdateEmployeeRequest`, and `EmployeeResponse`
  - [x] `backend/app/employees/service.py` — `experience_years` passed through in both `create_employee_service`'s and `update_employee_service`'s `employee_data` dicts
  - [x] `backend/app/core/seeds.py` — demo Employees (Casey/Morgan/Jordan/Sam) given `experience_years` 3/6/9/13 so a fresh seed demos the panel non-trivially (Sails Admin left null on purpose — excluded from every bucket like any Employee with no value set)
  - [x] Input UX decision (AC1's open point): a second, independent numeric input alongside the existing free-text "Experience" field in both `CreateEmployeeModal.tsx` and `EditEmployeeModal.tsx` — not a replacement, matching the locked mockup's `create-emp-experience-years` field

- [x] Task 2: `GET /api/dashboard/experience-distribution` (AC: 2, 3, 5)
  - [x] `backend/app/employees/repository.py::list_active_employee_experience_years` — raw `experience_years` values for active (`archived_at IS NULL`), non-null rows only (AD-1: `dashboard/` never queries `employees` directly)
  - [x] `backend/app/dashboard/service.py::EXPERIENCE_BUCKETS` — the 7 fixed `(label, min_years, max_years)` tuples locked 2026-09-15, mirroring `ON_TRACK_THRESHOLD`'s existing fixed-constant precedent; `max_years=None` marks the open-ended "20+ yrs" bucket
  - [x] `backend/app/dashboard/service.py::get_experience_distribution` — fetches the raw values once, buckets them in Python (mirrors `get_employee_segmentation`'s existing fetch-then-groupby shape rather than 7 range-COUNT queries)
  - [x] `backend/app/dashboard/schemas.py` — `ExperienceBucketResponse` (`label`, `min_years`, `max_years`, `count`) and `ExperienceDistributionResponse` (`buckets: list[...]`) — a separate response shape from `EmployeeSegmentationResponse`, satisfying AC3's "distinct panel" requirement at the contract level too
  - [x] `backend/app/dashboard/router.py` — `GET /api/dashboard/experience-distribution`, HR_ADMIN-gated identically to the sibling `/stats`/`/segmentation` routes (AD-6)
  - [x] AC5 (non-color-only): satisfied structurally — every bucket renders as a text label + count, never color alone

- [x] Task 3: Employees page — Experience Distribution chip bar + click-through (AC: 2, 3, 4)
  - [x] `frontend/src/types/dashboard.ts` / `frontend/src/lib/api/dashboardApi.ts` — `ExperienceBucket`/`ExperienceDistributionResponse` types and `dashboardApi.getExperienceDistribution()`
  - [x] `frontend/src/pages/hr/EmployeesPage.tsx` — new "Experience:" chip row (one pill per bucket, `"{label} ({count})"`, `aria-pressed`) rendered above the roster grid, fetched alongside `listEmployees()` in the existing `refetch()`; distinct heading/labeling from any Employee Segmentation chart (AC3 — this page has none to collide with; Story 9.2/9.3's segmentation chart lives on the separate Skill Assignment Dashboard page)
  - [x] Click-through (AC4) reuses the roster's own already-fetched list and existing 15/page client-side pagination (FR-25 convention, Story 7.3 Scope Note 2) instead of a second paginated endpoint — clicking a bucket sets a `activeBucketLabel` filter that narrows the same `filtered` roster list by `[min_years, max_years]` (looked up from the API response, not a second hardcoded copy of the boundaries); clicking the active bucket again, or "Clear filter", clears it
  - [x] Bucket counts are computed server-side over the *full* active roster regardless of the page's own search/Department/Position/archived-toggle state (Dev Notes: a bucket count must not shrink just because an unrelated filter is also active) — confirmed by fetching distribution independently of the `filtered` memo
  - [x] Extended Story 10.2 AC6's existing self-row-exclusion rule: the acting HR Admin's own row now also drops out of the unfiltered view while a bucket filter is active, matching the AC6 text's own forward-reference ("...or Experience-bucket filter (FR-36/Story 10.4) active") already added to epics.md during Story 10.2

- [x] Task 4: Tests (AC: 1, 2, 4)
  - [x] `backend/tests/test_employees_router.py` — `experience_years` round-trips on create/update; omitted-on-create defaults to null; negative value rejected 422 (`ge=0`)
  - [x] `backend/tests/test_dashboard_router.py` — auth/role gates; exact 7 bucket labels/boundaries; a new Employee's `experience_years` moves the correct (and only the correct) bucket's count; the open-ended 20+ bucket; a null `experience_years` moves no bucket; an archived Employee (via real Assignment history + DELETE, not a hard-delete) is excluded
  - [x] `frontend/src/tests/EmployeesPage.test.tsx` — `dashboardApi` mocked; chip bar renders labels/counts; clicking a bucket filters the grid and shows "Clear filter"; a null-`experience_years` row is excluded from an active bucket filter; the acting admin's own row drops out under a bucket filter and returns after "Clear filter"
  - [x] `frontend/src/tests/EmployeesPage.test.tsx` / `EditEmployeeModal.test.tsx` — `makeEmployee()` fixtures extended with `experience_years` (new required field on `EmployeeResponse`)
  - [x] Full regression: backend 732 passed/2 skipped (0 new failures); frontend 437 passed, 41 files; `tsc --noEmit` unchanged at the documented 73-error baseline (0 new errors, none in touched files)

- [x] Task 5: Live verification (AC: 2, 3, 4)
  - [x] Docker's `talentpilot-api`/`talentpilot-ui` images predate this change (not volume-mounted) — stopped them and ran local dev servers instead (`uvicorn` on :8000 against the existing `.venv`, Vite on :5173) against the same Postgres container, migrated to head (016)
  - [x] Verified via Playwright (installed ad hoc into a scratch dir, not added to the project): chip bar renders correct per-bucket counts (0–4:1, 5–7:1, 8–9:1, 12–14:1 for the seeded Casey/Morgan/Jordan/Sam); clicking "8–9 yrs" filters the grid to Jordan only and hides Sails Admin's own row; "Clear filter" restores all 5; creating a new Employee with 17 years live-bumps the "15–19 yrs" count; the Edit modal round-trips an existing Employee's `experience_years` independent of the free-text field
  - [x] One environment finding: the dev Postgres DB predates this story's seed change (`seed_employees` is insert-once/skip-if-exists), so Casey/Morgan/Jordan/Sam's new `experience_years` values needed a one-time manual SQL backfill against that existing DB — a genuinely fresh database gets them automatically from the updated `core/seeds.py`; no code defect, just an idempotent-seed characteristic already established by prior stories (e.g. Story 10.1's identical finding, resolved there via a data migration instead since that story's gap affected every existing DB, not just the local dev one)

### Review Findings

- [x] [Review][Patch] Archived employee slips into an active bucket filter's results despite being excluded from that bucket's own count [frontend/src/pages/hr/EmployeesPage.tsx:313-318]
- [x] [Review][Patch] `experience_years` has no upper bound — an oversized value passes Pydantic and crashes at the DB layer with an unhandled `NumericValueOutOfRangeError`, surfacing as a generic 500 instead of a clean 422 [backend/app/employees/schemas.py]
- [x] [Review][Patch] Fractional `experience_years` input (e.g. `3.5`) gives no client-side signal before hitting the server's already-correct 422 rejection [frontend/src/features/admin/CreateEmployeeModal.tsx, EditEmployeeModal.tsx]
- [x] [Review][Patch] Experience Distribution fetch failure is a fully silent `catch {}` — no `console.error` for debuggability [frontend/src/pages/hr/EmployeesPage.tsx:208-215]
- [x] [Review][Patch] No boundary-value tests at the bucket edges the whole feature's correctness depends on [backend/tests/test_dashboard_router.py]
- [x] [Review][Patch] Bucket `data-testid`s are built from raw server label text (Unicode dashes/spaces) — brittle to any future relabeling [frontend/src/pages/hr/EmployeesPage.tsx, frontend/src/tests/EmployeesPage.test.tsx]
- [x] [Review][Patch] `refetch()` awaits the roster and distribution fetches sequentially instead of via `Promise.all` [frontend/src/pages/hr/EmployeesPage.tsx:197-215]
- [x] [Review][Patch] New `EmployeesPage.test.tsx` bucket tests only ever mock a single-bucket distribution array, never the real 7-bucket set [frontend/src/tests/EmployeesPage.test.tsx]
- [x] [Review][Defer] `CreateEmployeeModal.tsx` has no test file at all (pre-existing gap; this story added untested `experience_years` logic to it) [frontend/src/features/admin/CreateEmployeeModal.tsx] — deferred, pre-existing: no test suite existed for this component before this story; building one from scratch is out of proportion to a review patch

## Dev Notes

**Bucket boundaries have exactly one source of truth.** `EXPERIENCE_BUCKETS` (`dashboard/service.py`) is the only place the 7 ranges are declared; the frontend never hardcodes a second copy — it filters the roster using the `min_years`/`max_years` the API already returned for the clicked bucket. This avoids the two ever silently drifting apart (e.g. a future boundary tweak in one place and not the other).

**No new paginated endpoint for the click-through (AC4).** The Employees page already fetches its full active+archived roster once and does all search/filter/pagination client-side (Story 7.3 Scope Note 2, `EmployeesPage.tsx`). A bucket click is just one more client-side filter criterion over that same list, reusing the existing 15/page pagination verbatim — "matching FR-25's existing roster pagination convention" is satisfied literally, not by parallel-building a second grid.

**No new grid column.** The locked mockup (`05.1-Employees-Tab.html`) happens to also show an "Experience" column, but that reflects an earlier, pre-Story-10.2 draft of that file — the real, shipped `EmployeesPage.tsx` grid (Story 10.2, done) has a fixed column set (ID, Name, Position, Project, Location, Technologies, Days in Talent Pool, Email, Status, Actions) that this story does not touch, per CLAUDE.md's own guidance that these mockups can visually diverge from the real app and are a design reference, not a literal spec. Neither AC1 nor AC4 asks for a new column.

**Panel location (AC3).** This story's panel lives on the Employees page only, matching the locked mockup (`05.1-Employees-Tab.html`) and distinct from FR-32/Story 9.2's Employee Segmentation pie chart on the separate Skill Assignment Dashboard page — the two never appear on the same page in this story's scope. `epics.md`'s Story 10.11 (`10-11-...`, still backlog) is the one that later moves an Experience Distribution presentation onto the Dashboard page in place of the segmentation chart; that is explicitly out of this story's scope and reuses this story's endpoint/bucket data rather than re-deriving it.

**Architecture compliance (`ARCHITECTURE-SPINE.md`).** AR-26 (dashboard/ read-composition, no new table): satisfied — `dashboard/` owns no table and reads `employees/`'s data only through `employees/repository.py::list_active_employee_experience_years`, mirroring the existing `count_active_employees` cross-module read precedent used by `get_dashboard_stats`. AD-1 (module table ownership): satisfied — only `employees/repository.py` queries the `employees` table. AD-6 (server-side role gate): satisfied — the new route requires `require_hr_admin`, identical to its `/stats`/`/segmentation` siblings.

**Testing standard.** Backend: pytest against the real app/DB (matches `test_dashboard_router.py`'s existing live-DB pattern, throwaway Employees per test to avoid polluting shared seeded-roster assertions). Frontend: vitest with `dashboardApi` mocked (avoids real network calls from every `EmployeesPage` test, not just the ones that care about this panel).

### Project Structure Notes

Backend: `backend/alembic/versions/016_add_employee_experience_years.py` (new), `backend/app/employees/{models,schemas,service,repository}.py`, `backend/app/dashboard/{schemas,service,router}.py`, `backend/app/core/seeds.py`, `backend/tests/{test_employees_router,test_dashboard_router}.py`.
Frontend: `frontend/src/types/dashboard.ts`, `frontend/src/lib/api/{dashboardApi,employeesApi}.ts`, `frontend/src/features/admin/{CreateEmployeeModal,EditEmployeeModal}.tsx`, `frontend/src/pages/hr/EmployeesPage.tsx`, `frontend/src/tests/{EmployeesPage,EditEmployeeModal}.test.tsx`.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story 10.4` (lines 3016-3042)] — canonical AC text this story implements.
- [Source: `_bmad-output/planning-artifacts/epics.md#Story 10.2` line 2987, `[ADDED 2026-09-15]`] — the already-shipped forward-reference to this story's bucket filter needing to trigger the same self-row-exclusion rule as search/Department/Position.
- [Source: `_bmad-output/planning-artifacts/epics.md#Story 10.11` (lines 3172-3190)] — confirms this story's panel/endpoint is reused, not reimplemented, by the later Dashboard-page presentation change; confirms this story's scope is Employees-page-only.
- [Source: `_bmad-output/E-Development/01-Ritas-Trust-Call-Prototype/05.1-Employees-Tab.html` lines 207-222, 452-461, 640-677] — locked mockup reference for the compact quick-filter chip-bar presentation (not a stat-card panel), the 7 fixed bucket ranges, and the click-filters-the-same-list interaction (superseded by Story 10.2's real grid for column layout, per CLAUDE.md's mockup-drift note).
- [Source: `_bmad-output/E-Development/01-Ritas-Trust-Call-Prototype/06.1-Skill-Assignment-Dashboard.html` lines 240-258, 433-434] — confirms the ring+legend Dashboard-page presentation is Story 10.11's scope, not this story's.
- [Source: `_bmad-output/implementation-artifacts/sprint-change-proposal-2026-09-15.md`] — Epic 10's origin; FR-36/Story 10.4 build order (after 10-2/10-3, independent of 10-5..10-9).
- [Source: `CLAUDE.md`#Invariants, #Current status] — AR-26/AD-1/AD-6 compliance; the mockups-vs-real-app drift note that justified not adding an Experience grid column.

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (claude-sonnet-5)

### Debug Log References

- `alembic upgrade head` against the local dev Postgres (docker `talentpilot-db`, localhost:5433): `015 -> 016` applied cleanly.
- `pytest tests/test_employees_router.py tests/test_dashboard_router.py tests/test_employees_service.py -q`: 92 passed.
- `pytest -q` (full backend suite): 732 passed, 2 skipped, 0 failed.
- `npx tsc --noEmit -p .`: 73 errors, identical to the pre-existing baseline (verified via `git stash`/re-check), 0 new, none in any file this story touched.
- `npx vitest run`: 437 passed, 41 files, 0 failed.
- Live Playwright verification (ad hoc, scratch dir, removed after use) against local `uvicorn`/`vite` dev servers: chip counts, bucket click-through filtering, self-row exclusion, Clear filter, and the Create/Edit modal's new field all confirmed working via screenshots and DOM assertions.

### Completion Notes List

- All 5 ACs implemented and verified: `experience_years` migration/CRUD (AC1); `GET /api/dashboard/experience-distribution` with the 7 locked buckets, null-exclusion (AC2); a visually/semantically distinct Employees-page-only panel that does not touch FR-32's chart (AC3); click-through reusing the roster's own existing 15/page pagination rather than a new endpoint (AC4); text-plus-count rendering satisfying the non-color-only rule (AC5).
- Scope decision (documented in Dev Notes): did not add an "Experience" grid column even though the locked mockup shows one — that mockup predates Story 10.2's real, shipped column set and neither AC asks for a new column; adding one would have been an unrequested visual change.
- Real environment finding, not a code defect: the shared dev Postgres DB already had seeded demo Employees from before this story (idempotent seeding skips if rows exist), so the new `core/seeds.py` `experience_years` values needed a one-time manual backfill against that specific DB to demo/verify live — a fresh database picks them up automatically.
- No formal story file existed for 10-4 before this session (`sprint-status.yaml` had it at `backlog`, "Story files not yet authored"); this file was authored retroactively, immediately after implementation, at the user's explicit request, rather than via the normal `bmad-create-story` → `bmad-dev-story` sequencing.
- Full regression green: backend 732/732 passed (2 pre-existing skips), frontend 437/437 passed (41 files), `tsc --noEmit` unchanged at the documented 73-error baseline. No `bmad-code-review` pass has run yet — Status is `review`, not `done`.

### File List

- `backend/alembic/versions/016_add_employee_experience_years.py`
- `backend/app/employees/models.py`
- `backend/app/employees/schemas.py`
- `backend/app/employees/service.py`
- `backend/app/employees/repository.py`
- `backend/app/dashboard/schemas.py`
- `backend/app/dashboard/service.py`
- `backend/app/dashboard/router.py`
- `backend/app/core/seeds.py`
- `backend/tests/test_employees_router.py`
- `backend/tests/test_dashboard_router.py`
- `frontend/src/types/dashboard.ts`
- `frontend/src/lib/api/dashboardApi.ts`
- `frontend/src/lib/api/employeesApi.ts`
- `frontend/src/features/admin/CreateEmployeeModal.tsx`
- `frontend/src/features/admin/EditEmployeeModal.tsx`
- `frontend/src/pages/hr/EmployeesPage.tsx`
- `frontend/src/tests/EmployeesPage.test.tsx`
- `frontend/src/tests/EditEmployeeModal.test.tsx`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `_bmad-output/implementation-artifacts/deferred-work.md`

## Change Log

- 2026-09-17: Implemented directly from `epics.md`'s existing Story 10.4 AC text and the locked `05.1-Employees-Tab.html` mockup, at the user's explicit request to start API + UI development for Story 10.4 referencing the UX design — no `bmad-create-story` pass ran first (story was still `backlog`, unauthored). Backend: `experience_years` migration/model/schema/service, new `GET /api/dashboard/experience-distribution` (7 fixed buckets, AR-26 read-composition). Frontend: Employees-page "Experience:" chip bar reusing the roster's existing client-side pagination for click-through, extending Story 10.2 AC6's self-row-exclusion to this new filter; new numeric input in Create/Edit Employee modals. Full regression green (backend 732 passed/2 skipped, frontend 437 passed). Live-verified via Playwright against local dev servers (Docker's `talentpilot-api`/`talentpilot-ui` images were stale, not rebuilt as part of this story). Status set directly to `review` (skipping `in-progress`, since implementation was already complete when this story file was authored).
- 2026-09-17: Story file authored retroactively (this document) at the user's explicit request, immediately after implementation and verification, to bring the work under normal tracking. `sprint-status.yaml`'s `10-4-employee-experience-distribution-widget` entry updated `backlog -> review`.
- 2026-09-17: Code-reviewed via `bmad-code-review` (3-layer adversarial review — Blind Hunter, Edge Case Hunter, Acceptance Auditor). All 3 layers independently converged on the same real bug: an archived Employee matching the active bucket filter rendered in the grid despite being excluded from that bucket's own server-computed count (reachable via "Show archived" + a bucket click). 0 decision-needed, 8 patches applied, 1 deferred, 3 dismissed after verification against this codebase's own established conventions (no `CheckConstraint`s anywhere in this schema; Python-side bucketing matches `get_employee_segmentation`'s existing precedent). Patches: bucket filter now always excludes archived rows regardless of the toggle (with a new regression test); added `MAX_EXPERIENCE_YEARS` upper bound (verified via a live DB insert that an unbounded value crashed with an unhandled `NumericValueOutOfRangeError`, a generic 500, before this fix); `step={1}` added to both numeric inputs; the distribution-fetch failure now logs via `console.error` instead of being fully silent; added a boundary-value test covering both edges of two adjacent bucket pairs (4/5, 19/20); bucket `data-testid`s switched from raw label text to a stable index; `refetch()` now fires the roster and distribution fetches concurrently via `Promise.allSettled` instead of sequentially; frontend tests switched from partial bucket-array mocks to the real 7-bucket canonical set. Deferred: `CreateEmployeeModal.tsx` has no test file at all (pre-existing gap predating this story). Full regression re-verified: backend 734 passed/2 skipped (732 + 2 new), frontend 438 passed (437 + 1 new), `tsc --noEmit` unchanged at the 73-error baseline. Status -> `done`.
