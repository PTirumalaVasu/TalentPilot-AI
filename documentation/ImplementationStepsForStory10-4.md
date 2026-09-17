# Implementation Steps for Story 10-4: Employee Experience Distribution Panel

**Story Key:** 10-4-employee-experience-distribution-widget
**Epic:** 10 (Post-MVP Admin & Roster Refinements) — 4 of 16 stories, epic remains in-progress
**Status:** ✅ DONE (code-reviewed; not yet committed to git)
**Completed Date:** 2026-09-17

---

## Overview

Story 10.4 implements FR-36: a headcount-by-years-of-experience panel on the Employees page, with a click-through that filters the same roster grid down to a selected experience bucket. The panel is deliberately separate from FR-32's existing Employee Segmentation pie chart on the Skill Assignment Dashboard page (readiness status vs. tenure are unrelated axes) — this story never touches that chart or that page.

**Process deviation from Stories 10.1–10.3, done deliberately at the user's explicit direction, not by oversight:** the user's opening request was `start implementation for both API and UI for the story 10-4-employee-experience-distribution-widget if required refer the UX desing`. `sprint-status.yaml` listed the story as `backlog` — "Story files not yet authored." Unlike Story 10.3 (which ran `bmad-create-story` then `bmad-dev-story` before any code was written), this session implemented directly from `epics.md`'s already-fully-authored Story 10.4 AC text (lines 3016–3042) and the locked `05.1-Employees-Tab.html` mockup, without invoking either of those two skills. The story markdown file (this doc's sibling, `_bmad-output/implementation-artifacts/10-4-employee-experience-distribution-widget.md`) was authored **retroactively**, after implementation and live verification were already complete, in response to the user's own explicit follow-up ("Only remaining decision: author the retroactive Story 10.4 document and move sprint-status.yaml to review, if desired") — again by direct file authoring, not by running `bmad-create-story`. Only `bmad-code-review` ran as a formally invoked BMad skill in this story's full lifecycle. This is flagged here specifically so a future reader comparing this story's process to 10.1–10.3's doesn't mistake the difference for an inconsistency or a corner cut — it was a conscious, user-directed choice each time.

Three scope decisions, made directly from the AC text and this repo's own established conventions rather than improvised mid-implementation, are worth calling out up front: (1) **no new "Experience" grid column was added**, even though the locked mockup shows one — that mockup predates Story 10.2's real, shipped column set (Project/Location/Technologies/Days in Talent Pool replacing Department), and neither AC1 nor AC4 asks for a new column, so adding one would have been an unrequested visual change (this is exactly the kind of mockup-vs-real-app drift `CLAUDE.md`'s own documentation map warns about); (2) **the click-through reuses the roster's own already-fetched list and existing 15/page client-side pagination** (Story 7.3's established FR-25 convention) instead of standing up a second paginated backend endpoint, since AC4's "matching FR-25's existing roster pagination convention" language points at reuse, not reinvention; (3) **the bucket boundaries have exactly one source of truth** — the backend's `EXPERIENCE_BUCKETS` constant — and the frontend filters using the `min_years`/`max_years` the API already returned for the clicked bucket rather than keeping a second hardcoded copy of the ranges.

---

## Agents Invoked

### 1. Blind Hunter (`bmad-review-adversarial-general` skill, background subagent)

**Purpose:** Open-ended adversarial critique of the finished diff — no spec context, no priors.

**When Invoked:** Part of `bmad-code-review`'s 3-parallel-layer step, once the story reached `review` status. Given the diff via a file path (1,049 diff lines across 19 files — large enough that this session wrote it to a scratchpad file and pointed the subagent at it, rather than embedding it inline in the prompt as Story 10.3's smaller diff allowed).

**Key Findings Identified:** The lead finding, later independently corroborated by both other layers: chip counts and the actual filtered table can disagree, because the `showArchived` exclusion check in `EmployeesPage.tsx`'s filter chain ran *after* (and independently of) the bucket-filter check, so an archived Employee matching the selected bucket's range could render in the table even though the server-computed chip count (active roster only) never included them. Also flagged: no upper bound on `experience_years` (only `ge=0`) risking an unhandled DB-level integer overflow on an implausibly large value; no boundary-value tests at the six real bucket edges; `refetch()` awaiting the roster and distribution fetches sequentially instead of concurrently; a fully silent `catch {}` on the distribution fetch with no logging; bucket `data-testid`s built from raw server label text (Unicode dashes/spaces) as a test-brittleness risk; no `step`/integer guard on the two new numeric inputs; a nitpick that `get_experience_distribution` buckets in Python rather than via a DB aggregate query; the new frontend tests only ever mocking a partial bucket array rather than the real 7-bucket set; no test for the (structurally impossible to fail, given 7 fixed buckets are always returned) zero-employee case; and that `CreateEmployeeModal.tsx` has no test file at all, so none of this story's new payload-construction logic there is exercised anywhere.

### 2. Edge Case Hunter (`bmad-review-edge-case-hunter` skill, background subagent)

**Purpose:** Method-driven walk of every branching path and boundary condition — orthogonal to Blind Hunter's attitude-driven pass.

**When Invoked:** Same trigger, launched in parallel with Blind Hunter and the Acceptance Auditor. Output as structured JSON (`location`, `trigger_condition`, `guard_snippet`, `potential_consequence`).

**Key Findings Identified:** Independently converged on the same archived-employee/active-bucket-filter inconsistency Blind Hunter found, plus the same no-upper-bound and fractional-input-with-no-step-guard concerns, each expressed as a concrete trigger condition with a suggested guard snippet (e.g. `le=80` on the Pydantic field, `Math.trunc(...)` on the frontend number coercion).

### 3. Acceptance Auditor (custom prompt, background subagent)

**Purpose:** Cross-check the diff against the story file's own 5 ACs for violations, deviations, and missing implementation — full `review_mode`, spec file (`10-4-employee-experience-distribution-widget.md`) read directly.

**When Invoked:** Same trigger, full review mode against the story file as spec.

**Key Findings Identified:** Framed the same archived/bucket-filter bug explicitly as an AC2-vs-AC4 spec violation — AC2 defines the panel's counts over "the active roster," so a click-through that can show an archived Employee under an active-only bucket count is a real, spec-level inconsistency, not just a stylistic nit; also flagged the fractional-input gap as a minor AC1 sub-deviation. Everything else was independently verified compliant: the 7 bucket labels/boundaries exactly match AC2's locked ranges and are contiguous/exhaustive/non-overlapping; null-`experience_years` and archived rows are correctly excluded at the repository layer; the panel never touches `EmployeeSegmentationResponse`/FR-32's chart (AC3); click-through correctly reuses the existing `PAGE_SIZE = 15` client-side pagination (AC4); text-plus-count rendering satisfies the non-color-only rule (AC5); AR-26/AD-1/AD-6 architecture invariants all hold.

---

## Skills Invoked

### 1. `bmad-agent-dev` (Amelia persona activation)

**Purpose:** Activate the Senior Software Engineer persona for implementation.

**When Invoked:** `start implementation for both API and UI for the story 10-4-employee-experience-distribution-widget if required refer the UX desing`.

### 2. `bmad-code-review` (3-layer adversarial review + patch application)

**Purpose:** Independent adversarial verification of the finished implementation, followed by resolving every finding.

**When Invoked:** Run explicitly via the `/code-review` (`bmad-code-review`) slash command, one turn after implementation was already complete and the story file had been authored. Auto-discovered as the sole `review`-status entry in `sprint-status.yaml`, matching the immediately preceding conversation's implementation work.

**Workflow Steps Executed:**
- Constructed the diff against uncommitted working-tree changes, scoped to Story 10.4's own File List (18 modified + 1 new file, 608 insertions / 11 deletions) — explicitly **excluding** `frontend/Dockerfile`'s unrelated, pre-existing change (a healthcheck-URL fix that predated this session and was already present in the initial `git status` at session start). Confirmed `HEAD` (`f97d27f6`) matched the story file's own `baseline_commit` frontmatter exactly before proceeding.
- Launched Blind Hunter, Edge Case Hunter, and the Acceptance Auditor as background subagents (the first sequentially due to an initial launch-order slip, the latter two in parallel), all three given the diff plus repo access to read full file context beyond the diff hunks.
- Normalized and deduplicated the raw findings — 12 from Blind Hunter, 5 from Edge Case Hunter, 2 from the Acceptance Auditor — down to a handful of unique findings, merging the archived/bucket-filter bug that all three layers independently converged on.
- **Read the actual current code and live-verified claims before rating severity**, per the workflow's own rule, rather than rating from the raw claims: confirmed the filter-chain bug by direct code inspection; confirmed Pydantic already rejects a fractional `experience_years` cleanly (422) by running it directly against the real schema in the venv; confirmed an unbounded large value actually crashes the DB by executing a live `INSERT` against the dev Postgres instance, reproducing a real `NumericValueOutOfRangeError`; confirmed this codebase has zero `CheckConstraint`s anywhere (`grep -rn "CheckConstraint"` across `app/`/`alembic/`) before dismissing the "no DB-level constraint" finding as consistent with an established, documented convention rather than a new gap.
- Triaged into: **0 decision-needed, 8 patch, 1 defer, 3 dismiss.**
- **All 8 patches applied** (user chose "apply every patch," no per-finding confirmation) — see Files Created/Updated below for the full list.
- **Deferred 1 finding** to `deferred-work.md`: `CreateEmployeeModal.tsx` has no test file at all (a pre-existing gap predating this story; building a whole new suite from scratch was judged out of proportion to a review patch).
- **Dismissed 3 findings after verification**: no DB `CHECK` constraint (consistent with this codebase's zero-`CheckConstraint`, Pydantic-is-the-real-guard convention per `CLAUDE.md`); Python-side bucketing instead of a DB aggregate query (matches `get_employee_segmentation`'s existing precedent, already justified in the story's own Dev Notes, pilot-scale); no zero-employee/all-buckets-zero test (no branching logic exists to protect, since 7 fixed buckets are always returned unconditionally).
- Re-ran the full regression suite after all patches — backend **734 passed / 2 skipped** (732 baseline + 2 net new), frontend **438 passed** (437 baseline + 1 net new), `tsc --noEmit` unchanged at the documented 73-error baseline.
- Story Status → `done`; `sprint-status.yaml` synced (`10-4-...`: `done`).

**Output:** Story file's "### Review Findings" subsection (8 checked-off patches, 1 checked-off deferral); Change Log entry; 1 new `deferred-work.md` entry; this implementation-steps document.

---

## Files Created/Updated

### Backend — Modified/New Files

| File | Purpose |
|------|---------|
| `backend/alembic/versions/016_add_employee_experience_years.py` | New migration — nullable `Integer` column on `employees`, no backfill (no reliable source to derive it from) |
| `backend/app/employees/models.py` | `experience_years = Column(Integer, nullable=True)` |
| `backend/app/employees/schemas.py` | `experience_years` added to Create/Update/Response schemas. Code-review patch: `MAX_EXPERIENCE_YEARS = 75` upper bound added (`le=`) after a live DB insert proved an unbounded value crashes with an unhandled `NumericValueOutOfRangeError` |
| `backend/app/employees/service.py` | `experience_years` passed through in both create/update `employee_data` dicts |
| `backend/app/employees/repository.py` | New `list_active_employee_experience_years` — active, non-null values only (AD-1: only this module queries `employees` directly) |
| `backend/app/dashboard/schemas.py` | New `ExperienceBucketResponse`/`ExperienceDistributionResponse` |
| `backend/app/dashboard/service.py` | New `EXPERIENCE_BUCKETS` constant (the 7 locked ranges) and `get_experience_distribution` |
| `backend/app/dashboard/router.py` | New `GET /api/dashboard/experience-distribution`, HR_ADMIN-gated identically to `/stats`/`/segmentation` |
| `backend/app/core/seeds.py` | Demo Employees (Casey/Morgan/Jordan/Sam) given `experience_years` 3/6/9/13 |
| `backend/tests/test_employees_router.py` | `experience_years` round-trip/omitted-defaults-null/negative-rejected tests. Code-review patch: 1 new test for the oversized-value rejection |
| `backend/tests/test_dashboard_router.py` | Auth/role gates, 7-bucket shape, counting, null/archived exclusion tests. Code-review patch: 1 new boundary-value test covering both edges of two adjacent bucket pairs (4/5, 19/20) |

### Frontend — Modified Files

| File | Purpose |
|------|---------|
| `frontend/src/types/dashboard.ts` | New `ExperienceBucket`/`ExperienceDistributionResponse` types |
| `frontend/src/lib/api/dashboardApi.ts` | New `getExperienceDistribution()` |
| `frontend/src/lib/api/employeesApi.ts` | `experience_years` added to `EmployeeResponse`/`CreateEmployeeRequest`/`UpdateEmployeeRequest` |
| `frontend/src/features/admin/CreateEmployeeModal.tsx` | New independent "Experience (years)" numeric input. Code-review patch: `step={1}` added |
| `frontend/src/features/admin/EditEmployeeModal.tsx` | Same new field, round-trips an existing value. Code-review patch: `step={1}` added |
| `frontend/src/pages/hr/EmployeesPage.tsx` | New "Experience:" chip bar, click-through filter reusing the roster's own pagination, extends Story 10.2 AC6's self-row-exclusion to this filter. Code-review patches: (1) bucket filter now always excludes archived rows regardless of the "Show archived" toggle — the actual bug fix; (2) `refetch()` fires the roster and distribution fetches concurrently via `Promise.allSettled` instead of sequentially; (3) the distribution-fetch failure now logs via `console.error`; (4) bucket `data-testid`s switched from raw label text to a stable index |
| `frontend/src/tests/EmployeesPage.test.tsx` | 4 new Story 10.4 tests (chip rendering/click-through, null-experience exclusion, self-row exclusion, `dashboardApi` mocked). Code-review patches: switched from partial bucket-array mocks to the real 7-bucket canonical set (`FULL_BUCKET_SET`); added 1 new regression test for the archived+bucket-filter fix; updated all `data-testid` references to the new index-based scheme |
| `frontend/src/tests/EditEmployeeModal.test.tsx` | `makeEmployee()` fixture extended with `experience_years` |

### Planning/Tracking — Modified Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `10-4-...`: `backlog` → `review` (retroactive story authoring) → `done` (code review) |
| `_bmad-output/implementation-artifacts/deferred-work.md` | 1 new entry logged from code review (`CreateEmployeeModal.tsx` has no test file at all) |

### Documentation Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/10-4-employee-experience-distribution-widget.md` | Story file — authored retroactively after implementation, 5 ACs, 5 Tasks, Dev Notes recording the scope decisions, Dev Agent Record, Review Findings section |
| `documentation/ImplementationStepsForStory10-4.md` | This file |

### Not Changed (by design)

- `backend/app/dashboard/router.py`'s sibling `/stats`/`/segmentation` routes, and `FR-32`'s `get_employee_segmentation` — AC3 explicitly requires the new panel not to modify the existing Employee Segmentation chart in any way; verified true throughout
- No new "Experience" grid column on `EmployeesPage.tsx` — the locked mockup shows one, but that reflects an earlier, pre-Story-10.2 draft; neither AC1 nor AC4 asks for it (see Overview)
- No second paginated backend endpoint for the click-through — AC4 reuses the roster's existing 15/page client-side pagination instead (see Overview)

---

## Implementation Workflow Summary

### Phase 1: Implementation (no `bmad-create-story`/`bmad-dev-story`)
**Execution:** Amelia persona, direct implementation
- Read `epics.md`'s already-authored Story 10.4 AC text and the locked `05.1-Employees-Tab.html` mockup directly, rather than running `bmad-create-story` first
- Backend: migration, model/schema/service plumbing, new `GET /api/dashboard/experience-distribution` endpoint, seed data
- Frontend: chip bar + click-through filter on `EmployeesPage.tsx`, new numeric inputs on both Employee modals
- Full regression: backend 732 passed/2 skipped, frontend 437 passed, `tsc --noEmit` unchanged at the 73-error baseline
- **Live-verified via Playwright** against local `uvicorn`/`vite` dev servers — Docker's `talentpilot-api`/`talentpilot-ui` images predated this change (not volume-mounted) and were stopped rather than rebuilt for this verification pass; the Postgres container was reused as-is, migrated to head. One environment-only finding: the shared dev DB's `seed_employees()` is insert-once/skip-if-exists, so the new seed `experience_years` values needed a one-time manual SQL backfill against that existing DB to demo/verify live (a genuinely fresh database gets them automatically)

### Phase 2: Retroactive Story Authoring (no `bmad-create-story`)
**Execution:** Amelia persona, direct file authoring, at the user's explicit follow-up request
- Story file written by hand, mirroring Story 10.3's established format exactly (Story, 5 ACs transcribed from `epics.md`, Tasks/Subtasks mapped to what had actually shipped, Dev Notes, References, Dev Agent Record, File List, Change Log)
- `sprint-status.yaml`'s `10-4-...` entry updated `backlog` → `review`, with the superseded prior `last_updated` entry preserved as a `#` comment rather than dropped

### Phase 3: Code Review + Patches
**Skill:** `bmad-code-review`
- 3 parallel-ish adversarial layers (Blind Hunter, Edge Case Hunter, Acceptance Auditor — the auditor given the story file directly as spec) against the uncommitted diff, scoped via an explicit file list to exclude the unrelated pre-existing `frontend/Dockerfile` change
- 19 raw findings deduplicated, with severities set only after live-reproducing the two most consequential claims (a real DB insert to confirm the overflow crash; a direct Pydantic call to confirm fractional rejection already works) rather than trusting the subagents' framing
- 0 decision-needed, 8 patched, 1 deferred, 3 dismissed after direct verification against this codebase's own established conventions
- The lead patched finding — archived Employees slipping into an active bucket filter's results — was independently corroborated by all three layers using three different methods (adversarial code reading, structured edge-case enumeration, and literal AC-text cross-check)
- Full regression re-verified after patches: backend 734/734 (2 new), frontend 438/438 (1 new)
- Story marked `done`

---

## Test Coverage

### New/Extended Test Files

- `backend/tests/test_employees_router.py` — 3 net new Story 10.4 tests (round-trip, negative rejection, plus 1 from code review for oversized-value rejection)
- `backend/tests/test_dashboard_router.py` — 7 net new Story 10.4 tests (auth/role gates, 7-bucket shape, counting, open-ended bucket, null exclusion, archived exclusion, plus 1 from code review for boundary-value edges)
- `frontend/src/tests/EmployeesPage.test.tsx` — 5 net new Story 10.4 tests (chip rendering/click-through against the real 7-bucket set, null-experience exclusion, self-row exclusion, plus 1 from code review regression-testing the archived+bucket-filter fix)
- `frontend/src/tests/EditEmployeeModal.test.tsx` — fixture extension only, no net-new test

### Regression Verification

- Backend: 732 baseline → 732 passed/2 skipped (post-implementation) → **734 passed/2 skipped** (post-review, 2 net new)
- Frontend: 437 baseline → 437 passed (post-implementation) → **438 passed** (post-review, 1 net new), 41 files throughout
- `tsc --noEmit`: 73 pre-existing errors at every checkpoint (verified via `git stash` against the baseline branch state), 0 new, none in this story's files

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **AC1: `experience_years` migration** | Nullable `Integer` column, independent of the existing free-text `experience` column | `backend/alembic/versions/016_...py`, `backend/app/employees/models.py` |
| **AC2: 7 fixed buckets, active-roster-only, null-excluded** | `EXPERIENCE_BUCKETS` constant + `get_experience_distribution`, reading only `employees/`'s active/non-null values via `list_active_employee_experience_years` (AD-1, AR-26) | `backend/app/dashboard/service.py`, `backend/app/employees/repository.py` |
| **AC3: visually/semantically distinct from FR-32's chart** | Separate response schema (`ExperienceDistributionResponse`), separate endpoint, confined to the Employees page only — never touches `EmployeeSegmentationResponse` | `backend/app/dashboard/schemas.py`, `frontend/src/pages/hr/EmployeesPage.tsx` |
| **AC4: click-through, 15/page, reusing FR-25's convention** | Bucket click sets a client-side filter over the already-fetched roster, narrowed by the API-returned `min_years`/`max_years` — no second paginated endpoint | `frontend/src/pages/hr/EmployeesPage.tsx` |
| **AC5: non-color-only rendering** | Every bucket renders as `"{label} ({count})"` text, never color alone | `frontend/src/pages/hr/EmployeesPage.tsx` |
| **Archived-roster consistency (found during code review, patched)** | Bucket filter now unconditionally excludes archived Employees, matching AC2's active-roster-only count definition regardless of the "Show archived" toggle | `frontend/src/pages/hr/EmployeesPage.tsx` |
| **Upper-bound validation (found during code review, patched)** | `MAX_EXPERIENCE_YEARS = 75` (`le=`) added after live-reproducing a real DB overflow crash on an unbounded value | `backend/app/employees/schemas.py` |

---

## Key Technical Achievements

✅ **Correctly discovered and honestly documented a process deviation** — no story file existed and neither `bmad-create-story` nor `bmad-dev-story` ran before implementation began, unlike Stories 10.1–10.3; flagged explicitly rather than silently glossed over, at both the point of deviation and again here
✅ **Verified the mockup-vs-real-app drift `CLAUDE.md` warns about, and made the correct call** — deliberately did not add an "Experience" grid column the locked mockup shows, since it predates Story 10.2's real shipped column set and no AC asks for it
✅ **Live-verified end-to-end against real local dev servers, not just the test suite** — including discovering and manually working around a real environment characteristic (the shared dev DB's insert-once seeding meaning the new seed values needed a one-time manual backfill to demo)
✅ **Code review's lead finding was independently corroborated by all three layers using three different methods** (adversarial code reading, structured edge-case JSON, and literal AC-text cross-check) — all converging on the same real archived-employee/bucket-filter inconsistency
✅ **Severities were set only after live-reproducing the underlying claims**, not from the subagents' own framing — a real DB `INSERT` proved the overflow crash; a direct Pydantic call proved the fractional-input rejection already worked correctly, downgrading that finding from "gap" to "UX polish"
✅ **Three findings were dismissed only after direct verification against this codebase's own established, documented conventions** (`grep -rn "CheckConstraint"` returning zero hits project-wide) — not waved away as noise by default
✅ **Zero regressions across every regression run in the session's final checkpoints** — backend 732 → 734, frontend 437 → 438, same 73 pre-existing `tsc` errors throughout

---

## Deferred Items (Not Story 10-4 Scope)

Formally deferred to `deferred-work.md`:

- **`CreateEmployeeModal.tsx` has no test file at all** [`frontend/src/features/admin/CreateEmployeeModal.tsx`] — a pre-existing gap predating this story (the component shipped without a test suite in Story 7.2's own frontend work); this story added new, currently-untested `experience_years` payload logic to that same untested file. Revisit when a `CreateEmployeeModal.test.tsx` is eventually created (mirroring `EditEmployeeModal.test.tsx`'s existing shape) — include a case for the empty-string-to-null conversion and a fractional-input case alongside the component's other untested behavior.

---

## Conclusion

Story 10-4 is **✅ DONE** after an implementation-then-retroactive-documentation-then-review-and-patch cycle, run across three turns in one continuous session:

- All 5 acceptance criteria satisfied — the Employees page now shows a 7-bucket Experience Distribution chip bar with a working click-through, entirely separate from FR-32's Employee Segmentation chart, verified by a 734-test backend and 438-test frontend regression pass, clean before and after the code-review patches, and confirmed live in a real browser via Playwright
- Unlike Stories 10.1–10.3, this story's process deliberately skipped `bmad-create-story`/`bmad-dev-story` at the user's direction, implementing straight from the already-authored `epics.md` AC text; the story file itself was authored retroactively, after the fact, at the user's explicit follow-up request — both points are documented here plainly rather than left implicit
- Code review surfaced a handful of findings, most stemming from one real bug (archived Employees slipping into an active bucket filter's results) independently found by all three review layers via three different methods; 0 requiring a human decision, 8 patched, 1 deferred as a pre-existing gap, 3 dismissed only after direct verification against this codebase's own conventions
- Zero regressions across every regression run in the session's final checkpoints (backend 732 → 734, frontend 437 → 438)
- **Not yet committed to git** — working tree still uncommitted as of this document, on top of `HEAD` at `f97d27f6` ("feat: Story 10.3 - Delete/Archive icon reflects the real action before the click")

**Epic 10 status:** in-progress — 4 of 16 stories (10.1, 10.2, 10.3, 10.4) done; next in the documented build order per the Sprint Change Proposal is any of 10.5 through 10.9.
