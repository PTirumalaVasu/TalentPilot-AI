---
baseline_commit: f1b4604b
---

# Story 9.1: Backend: Org-Wide Stats & Assignment Progress Endpoint

Status: done

## Story

As an **HR Admin**,
I want org-wide assignment stats and progress computed for me,
So that I can see the health of the whole org at a glance without opening the full grid (FR-31, part of FR-32).

## Scope Notes (read before starting)

1. **Backend-only. One new endpoint on the existing `dashboard/` module. No new table.** Confirmed against `epics.md`'s own Story 9.1 scope and AR-26 ("read-composition owned by `dashboard/`, no new table"). Frontend consumption of this endpoint is Story 9.3, not this story — do not build any UI here.

2. **New route: `GET /api/dashboard/stats`**, added as a second route inside the existing `backend/app/dashboard/router.py`. No new router file and no new `app.include_router(...)` line — the existing mount (`backend/app/main.py:49`, `app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])`) already covers it; a `@router.get("/stats", ...)` decorator inside the existing file is all that's needed.

3. **Reuse the existing endpoint's exact auth/session pattern — do not reinvent it.** `backend/app/dashboard/router.py`'s current (and only) endpoint is:
   ```python
   router = APIRouter(tags=["dashboard"], dependencies=[Depends(get_current_user)])

   @router.get("", response_model=DashboardResponse)
   async def get_dashboard(
       current_user: Annotated[CurrentUser, Depends(require_hr_admin)],
       session: Annotated[AsyncSession, Depends(get_db)],
       page: int = Query(1, ge=1),
       page_size: int = Query(50, ge=1, le=500),
   ) -> DashboardResponse:
   ```
   The new `/stats` endpoint takes no `page`/`page_size` params (this is a single aggregate object, not a paginated list) but otherwise uses the identical `Depends(require_hr_admin)` + `Depends(get_db)` shape.

4. **Real gap found in the codebase, not assumed — verify before reusing:** `backend/app/assignments/repository.py::list_assignments_for_dashboard` (line 191) is exactly the query shape this story needs — org-wide, `Assignment.active.is_(True))`-filtered, unpaginated, eager-loading `employee`/`skill`/`content`/`progress`. **But it is currently dead code.** Its only caller, `backend/app/assignments/service.py::list_assignment_rows_for_dashboard_service` (line 330), is itself never called from any router or test (confirmed via project-wide grep — zero call sites beyond its own definition and a repository docstring reference). It predates and was superseded by the current paginated `DashboardService.get_dashboard_assignments`/`list_assignments_for_hr` path (that function's own docstring says as much: *"Still not the final Epic 5 grid..."*). The query is well-formed and safe to resurrect for this story, but confirm it still behaves correctly against the current schema before relying on it — don't assume dead code is still exactly correct just because it reads that way.

5. **Critical correctness trap: `list_assignments_for_dashboard` does NOT eager-load `AssignmentOverride` rows.** The existing live `GET /api/dashboard` endpoint separately batch-loads overrides (`DashboardService._batch_load_overrides` → `ProgressRepository.get_active_overrides_for_assignments`) and folds them into each row's Status/Provenance via `ProgressService.get_provenance_detail` (the full AD-3 authority, which short-circuits Status to the override's value when one is active). **Do not classify this story's Completed/In Progress/Not Started counts using the narrower `ProgressService.derive_dashboard_status_and_percent` alone** — an Assignment with an active HR Override must count as whatever the override says (typically Completed) even if its raw watch-% disagrees. Batch-load overrides the same way `DashboardService._batch_load_overrides` already does, and call `get_provenance_detail` per assignment (or at minimum its `.status` field) for the breakdown — not the bare percent-derivation function.
   **Do NOT also add a `_batch_load_progress`-equivalent step.** `Assignment.progress` is a `uselist=False` relationship, and the resurrected `list_assignments_for_dashboard` query already does `selectinload(Assignment.progress)` (`assignments/repository.py:213`) — `assignment.progress` is directly available on each row. The live `/api/dashboard` endpoint only needs a separate progress-batch-load because *its* query (`list_assignments_for_hr`) doesn't eager-load progress — that's a difference between the two queries, not something to copy reflexively. Overrides are the only thing genuinely missing here.

6. **Active-Employee count.** `Employee.archived_at` is nullable (`None` = active), already filtered this way in `assignments/repository.py:59`'s `list_employees` (`Employee.archived_at.is_(None)`). A dedicated `COUNT(*)`-style query is preferable to loading full Employee rows just to take `len()` — add a small new repository function if nothing suitable exists. **Module-ownership judgment call, not prescribed:** both `assignments/repository.py` (via `list_employees`) and `employees/repository.py` (the module that actually owns the `employees` table per AD-1) touch `Employee` today. Decide which module the new count function belongs in and document the reasoning in this story's Dev Notes — don't silently duplicate the query in a third place.

7. **Response schema — follow the existing pattern in `backend/app/dashboard/schemas.py`.** `AssignmentRowResponse`/`DashboardResponse` are plain `BaseModel`s (no `from_attributes`/ORM passthrough — this endpoint is a pure computed aggregate, same shape). New schema, e.g. `DashboardStatsResponse`, with: `total_employees: int`, `total_skills_assigned: int`, `total_completed: int`, `completed_count: int`, `in_progress_count: int`, `not_started_count: int`, `overall_percent: int`. (`total_skills_assigned` and `completed_count`/`total_completed` are the same underlying numbers used two ways — one for the top-line stat, one for the progress breakdown; don't compute them twice.)

8. **`dashboard/repository.py` is intentionally empty** ("Dashboard is a read-composition module that relies on assignments/ and progress/ repositories. No direct database access needed here" — its own existing comment). New counting/aggregation logic belongs in `assignments/repository.py` (and/or `employees/repository.py`, per Scope Note 6), called from a new `DashboardService` method — not a new query written directly inside `dashboard/`. If you conclude this convention genuinely needs to change for this story, say so explicitly in Dev Notes rather than silently breaking it.

9. **Existing tests to extend, not replace or duplicate the setup of:** `backend/tests/test_dashboard.py` (service-layer, `db_session: AsyncSession` fixture, hardcoded seeded Rita UUID) and `backend/tests/test_dashboard_router.py` (HTTP-level: `httpx.AsyncClient` + `ASGITransport(app=app)`, `pytest.mark.asyncio(loop_scope="module")`, its own `_engine`/`_session_factory`, a `_login()` helper posting to `/api/auth/login` for the session cookie, `_cleanup_assignment(s)_for` helpers, seeded IDs from `app.core.seed_ids`/`app.core.seeds`). New tests for `/stats` should reuse these exact fixtures/helpers.

10. **Overall % formula:** `round(completed_count / total_skills_assigned * 100)`, matching the exact wording in `epics.md`'s Story 9.1 AC. Guard the zero-assignments case explicitly (return 0, not a `ZeroDivisionError`) — this matters because Story 9.3's Empty state depends on this endpoint not crashing when the org genuinely has zero active Assignments yet.

## Acceptance Criteria

**AC1 — Org-wide stats:**
**Given** active (non-archived) Employees and active (non-soft-deleted) Assignments exist
**When** the dashboard's stats endpoint is called
**Then** it returns Total Employees, Total Skills Assigned, and Total Completed — all computed server-side from the single derivation authority (`progress/`, AD-3), never re-derived independently on the frontend.

**AC2 — Assignment Progress breakdown:**
**Given** the same active Assignment set
**When** the Assignment Progress breakdown is requested
**Then** Completed/In Progress/Not Started counts and Overall % (`completed/total * 100`, rounded) are returned, matching the exact Status values FR-8 already defines — not a parallel status computation.

**AC3 — Archived/soft-deleted exclusion:**
**Given** an archived Employee or a soft-deleted Assignment
**When** computing any of these counts
**Then** it is excluded, mirroring the existing archived/soft-delete exclusion rule already used by FR-25 (roster) and FR-4 (Content Discovery).

**AC4 — Read-only, no new table:**
**And** this endpoint is read-only, owned by `dashboard/` (AR-26), and adds no new table — reads across `assignments`/`employees`/`progress` exactly as the existing Readiness Dashboard already does (AD-8).

**AC5 — Role gate:**
**Given** the endpoint is called by a non-HR-Admin session
**When** the request is evaluated
**Then** it is refused with the same access-denied response FR-14 already defines for every other HR-only endpoint.

## Tasks / Subtasks

- [x] **Task 1: Response schema** (AC1, AC2) — `backend/app/dashboard/schemas.py`
  - [x] Add `DashboardStatsResponse(BaseModel)` with `total_employees`, `total_skills_assigned`, `total_completed`, `completed_count`, `in_progress_count`, `not_started_count`, `overall_percent` (all `int`).

- [x] **Task 2: Verify/resurrect the org-wide assignment query** (AC1, AC3, Scope Notes 4-5)
  - [x] Confirmed `assignments/repository.py::list_assignments_for_dashboard` still executes correctly against the current schema (verified via the router-level tests, which exercise it end-to-end against the live DB).
  - [x] Decision: call it directly from the new `DashboardService.get_dashboard_stats` method (no new repository function needed for the query itself) — documented in Dev Notes.
  - [x] Batch-load `AssignmentOverride` rows via `DashboardService._batch_load_overrides` (existing helper, reused as-is).

- [x] **Task 3: Active-Employee count** (AC1, AC3, Scope Note 6)
  - [x] Added `count_active_employees` to `employees/repository.py` (not `assignments/repository.py`) — decision documented in Dev Notes.

- [x] **Task 4: `DashboardService.get_dashboard_stats(session)`** (AC1, AC2, AC3, AC4, Scope Notes 5, 10)
  - [x] Composes Tasks 2+3's data via `ProgressService.get_provenance_detail` (through the existing `_compute_status_and_provenance_from_data` helper), aggregating Completed/In Progress/Not Started.
  - [x] `overall_percent` guards the zero-assignments case (returns 0).
  - [x] No new table, no writes.
  - [x] **Real gap caught during implementation, fixed before it became a bug:** AC3 requires archived-Employee assignments excluded from *every* count, not just `total_employees` — `list_assignments_for_dashboard` only filters `Assignment.active`, not `Employee.archived_at`. Fixed by filtering `assignment.employee.archived_at is None` in the service before aggregating, rather than widening the repository query's own WHERE clause.

- [x] **Task 5: Router endpoint** (AC1, AC5) — `backend/app/dashboard/router.py`
  - [x] `@router.get("/stats", response_model=DashboardStatsResponse)`, `Depends(require_hr_admin)` + `Depends(get_db)`, no query params.

- [x] **Task 6: Tests** (all ACs)
  - [x] `backend/tests/test_dashboard.py`: structural service-level test (`test_dashboard_stats_service_returns_response_structure`) — matches this file's existing convention of no absolute-value assertions against the shared/live dev DB.
  - [x] `backend/tests/test_dashboard_router.py`: 5 new tests + 1 helper — 401/403 role gate; mixed Not-Started/In-Progress/Completed delta assertions plus exact `overall_percent` arithmetic; HR Override counted as Completed; archived-Employee-and-their-Assignments excluded from every count (the AC3 gap above, caught by this very test failing before the fix).

- [x] **Task 7: Regression check**
  - [x] Full backend suite: 706 passed, 2 skipped (pre-existing, unrelated) — zero regressions.

### Review Findings

_(`bmad-code-review`, 2026-09-13, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor. Findings verified against the actual code before rating, not taken from the diff hunk alone.)_

- [x] [Review][Decision] The video-duration-resolution fallback (copied from `get_dashboard_assignments`) can trigger a real DB write as a side effect of this GET endpoint — `match_content_for_skill` → `reembed_content_for_skill` re-embeds Content rows when no match clears the threshold on the first pass, and `get_db`'s commit-on-success convention persists it. This directly contradicts AC4's "read-only" framing and this story's own "pure read composition" claim. Confirmed by reading `content/service.py::match_content_for_skill` directly — not a false positive. [backend/app/dashboard/service.py, backend/app/content/service.py:253-289] **Resolved by user: Option 2 — hardened this endpoint to drop the fallback entirely** (uses only `ProgressRepository.get_video_duration`, no `match_content_for_skill` call), so `/stats` is genuinely side-effect-free even though the sibling `GET /api/dashboard` endpoint still has this behavior. Consequence, documented inline: an assignment with partial watch progress but no resolvable duration classifies as Not Started here rather than a percentage-based status.
- [x] [Review][Patch] "In Progress" bucket never exercised by a genuine positive test — `test_dashboard_stats_reflects_mixed_status_counts`'s docstring claims a Not-Started/In-Progress/Completed trio is created, but the body only creates 2 assignments (not-started, completed); the `in_progress_count` assertion is a no-op delta of 0. AC2 requires the breakdown to be correct for all 3 buckets. [backend/tests/test_dashboard_router.py] **Fixed:** added a genuine 3rd assignment (MORGAN_ID, partial watch) so all 3 buckets get a real positive delta.
- [x] [Review][Patch] No test asserts `overall_percent`'s exact arithmetic against a known input/output — only bounds-checked (`0 <= overall_percent <= 100`), so a subtly wrong formula would pass every existing test. [backend/tests/test_dashboard_router.py] **Fixed:** added an exact `expected_percent = round(after["completed_count"] / after["total_skills_assigned"] * 100)` assertion.
- [x] [Review][Patch] This story's own Dev Agent Record/File List claims "6 new tests" in `test_dashboard_router.py` — actual count is 5 test functions + 1 non-test helper (`_get_stats`). [this story file] **Fixed:** corrected the count to "5 new tests + 1 helper" throughout this story file.
- [x] [Review][Patch] `test_dashboard_stats_hr_override_counts_as_completed` omits an `in_progress_count` delta assertion, unlike its sibling mixed-status test — inconsistent rigor across two tests covering the same AC2/AC3 surface. [backend/tests/test_dashboard_router.py] **Fixed:** added the missing `in_progress_count` delta assertion.
- [x] [Review][Patch] `DashboardStatsResponse.total_completed`/`completed_count` are permanently numerically identical (intentional per Scope Note 7 — one field per UI element, not an accidental duplication) but the schema itself carries no comment saying so, inviting a future reader to "fix" the redundancy. [backend/app/dashboard/schemas.py] **Fixed:** added a docstring explaining the intentional duplication and why both fields must stay.
- [x] [Review][Defer] `get_dashboard_stats` loads the entire org-wide active-assignment list into memory with no pagination/cap, unlike the paginated main dashboard grid — deferred, already flagged as AR-27 in `epics.md` ("query-plan/index check once real data volume is known"); logged in `deferred-work.md` for traceability.
- [x] [Review][Defer] No transactional/snapshot consistency across the 3 separate reads this endpoint composes (assignments, overrides, employee count) — a concurrent write between them could yield internally-inconsistent totals in one response. Low practical impact for a coaching-only, approximate landing-page stat at this project's pilot scale.
- [x] [Review][Defer] The HR-Override "always counts as Completed" assumption is only true because `SetOverrideRequest`'s current contract has no way to set any other `override_status` — protects against a hypothetical future schema change, not a present defect.

Dismissed as non-issues after verification: the router docstring's "identical auth to `GET /api/dashboard`" claim can't practically drift, since both endpoints share the literal same `require_hr_admin` dependency object, not just similar reimplemented logic; no caching/rate-limiting discussion is out of scope given this project's explicit local-only/pilot-scale target (AR-15, no production deployment exists); `list_assignments_for_dashboard`'s "wasted" eager-loads (`.skill`/`.content`/`ORDER BY`) match this story's own Scope Note 4, which explicitly directed reusing the existing function as-is rather than forking a leaner variant; the archived-employee test's raw `DELETE FROM accounts`/`employees` cleanup matches this same test file's pre-existing convention for other tables (`SkillProgress`/`Assignment` direct deletes), not a new or worse pattern.

## Dev Notes

### The dead-code trap this story must not repeat

`list_assignments_for_dashboard` + `list_assignment_rows_for_dashboard_service` are a fully-formed, correctly-shaped pair of functions for exactly this story's read pattern — and neither is called by anything live today. This is exactly the kind of "looks right, isn't actually exercised" trap this project's own architecture notes have flagged before (AD-3's whole reason for existing is centralizing derivation so it can't silently drift in two places). Resurrecting the query is fine; resurrecting the *derivation* logic in `list_assignment_rows_for_dashboard_service` (which uses the narrower percent-only function and a hand-rolled provenance string, not the current `get_provenance_detail` authority) would reintroduce exactly the kind of drift AD-3 exists to prevent. Use the query, not the derivation, from that dead pair.

### Module ownership for the new Employee count

**Decision:** `employees/repository.py::count_active_employees`. `employees/repository.py`'s own module docstring states "Only this module's own code may query the `employees` table directly (AD-1)" — a stricter, more current statement of the rule than `assignments/repository.py::list_employees`, which is an older, accepted exception. New code should follow the module's own documented rule rather than extend the older exception.

### AC3's archived-Employee exclusion applies to assignment counts too, not just total_employees

Caught while implementing Task 4, not assumed from the epics text alone: AC3 says archived Employees are excluded "from any of these counts" — that includes `total_skills_assigned`/`completed_count`/etc., not only `total_employees`. `list_assignments_for_dashboard` has no `Employee.archived_at` filter (it only knows about `Assignment.active`), so an archived Employee's still-`active` Assignments would otherwise still be counted. Fixed by filtering the fetched assignment list in `get_dashboard_stats` itself (`assignment.employee.archived_at is None`) rather than widening the shared repository query, since that query is dead-code-resurrected for this one caller and adding an employee-status opinion to it isn't this story's job. Verified by `test_dashboard_stats_excludes_archived_employee_and_their_assignments`, which failed on `total_skills_assigned` before this fix and passes after.

## Architecture Compliance

- AR-26: read-composition owned by `dashboard/`, no new table.
- AR-8 (module dependency direction): `dashboard` depends on `assignments`/`employees`/`progress`, never the reverse — this story adds no new dependency direction, only new read calls along existing-allowed directions.
- AD-3: Status/Provenance derivation stays solely in `progress/` — this story must call into it, never reimplement it.

## References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 9.1] — full AC text, Epic 9 scope
- [Source: _bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md#FR-31] — org-wide stats requirement
- [Source: _bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/addendum.md#Skill Assignment Dashboard — Architecture Handoff Notes] — read-composition framing, no-new-migration confirmation
- [Source: backend/app/dashboard/router.py] — existing endpoint's exact auth/session dependency pattern to mirror
- [Source: backend/app/dashboard/service.py] — `DashboardService.get_dashboard_assignments`, `_batch_load_progress`, `_batch_load_overrides` — the composition pattern and override-batching to reuse
- [Source: backend/app/dashboard/schemas.py] — `AssignmentRowResponse`/`DashboardResponse` pattern to mirror for the new `DashboardStatsResponse`
- [Source: backend/app/progress/service.py] — `ProgressService.derive_dashboard_status_and_percent`, `get_provenance_detail`, `NEEDS_ATTENTION_STALENESS_DAYS` constant precedent
- [Source: backend/app/assignments/repository.py:191-217] — `list_assignments_for_dashboard`, confirmed dead-but-well-formed; `list_employees` (line 59)'s `Employee.archived_at.is_(None)` filter
- [Source: backend/app/assignments/service.py:330-353] — `list_assignment_rows_for_dashboard_service`, confirmed dead code (zero call sites beyond its own definition)
- [Source: backend/app/main.py:49] — existing dashboard router mount
- [Source: backend/tests/test_dashboard.py, backend/tests/test_dashboard_router.py] — existing test fixtures/helpers to extend

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5

### Debug Log References

- `pytest tests/test_dashboard.py tests/test_dashboard_router.py -v`: 16/16 passed (10 pre-existing + 6 new) after fixing two test-only bugs found during this story: (1) the shared `_cleanup_assignment`/`_cleanup_assignments_for` helpers didn't delete `AssignmentOverride` rows before `Assignment`, which FK-violated once this story's tests became the first in this file to create an override; (2) the archived-Employee test's own cleanup tried to hard-delete the `Employee` row without first deleting its paired `Account` row (`Account.id == Employee.id`, AR-24), FK-violating on `accounts_id_fkey`. Both fixed in the test file itself, not the production code.
- Full suite: `pytest -q` → 706 passed, 2 skipped (pre-existing, unrelated to this story), 106s. Zero regressions.

### Completion Notes List

- New `DashboardStatsResponse` schema (`dashboard/schemas.py`), `DashboardService.get_dashboard_stats` (`dashboard/service.py`), and `GET /api/dashboard/stats` (`dashboard/router.py`) — all following the existing dashboard module's exact conventions (auth deps, response-model style, read-composition-only).
- Resurrected `assignments/repository.py::list_assignments_for_dashboard` (previously dead code, per this story's own Scope Note 4) as the org-wide read; did **not** resurrect its dead sibling `list_assignment_rows_for_dashboard_service`'s derivation logic, using `ProgressService.get_provenance_detail` (via the existing `_compute_status_and_provenance_from_data` helper) instead, per Dev Notes' AD-3 reasoning.
- New `employees/repository.py::count_active_employees` — a dedicated `COUNT` query, module-ownership decision documented in Dev Notes.
- **Real correctness gap found and fixed during implementation** (not by review): AC3 requires archived-Employee assignments excluded from every count, not just `total_employees` — the resurrected query doesn't know about `Employee.archived_at` at all. Fixed by filtering in the service layer; the fix is directly proven by `test_dashboard_stats_excludes_archived_employee_and_their_assignments`, which exercises the full create → verify-included → archive → verify-excluded lifecycle against the live DB.
- 5 new tests + 1 non-test helper (`_get_stats`), all passing, using the delta-snapshot pattern (before/after counts) required by this file's shared, ever-growing dev-DB convention rather than absolute-value assertions. The mixed-status test also asserts `overall_percent`'s exact formula, not just its bounds.
- Fixed 2 test-infrastructure FK-ordering bugs surfaced by this story's own new tests (see Debug Log References) — both in test cleanup helpers, zero production-code impact.

### File List

**Modified:**
- `backend/app/dashboard/schemas.py` — added `DashboardStatsResponse`
- `backend/app/dashboard/service.py` — added `DashboardService.get_dashboard_stats`
- `backend/app/dashboard/router.py` — added `GET /api/dashboard/stats`
- `backend/app/employees/repository.py` — added `count_active_employees`
- `backend/tests/test_dashboard.py` — added `test_dashboard_stats_service_returns_response_structure`
- `backend/tests/test_dashboard_router.py` — added 5 tests (`test_dashboard_stats_requires_authentication`, `test_dashboard_stats_forbidden_for_employee_role`, `test_dashboard_stats_reflects_mixed_status_counts`, `test_dashboard_stats_hr_override_counts_as_completed`, `test_dashboard_stats_excludes_archived_employee_and_their_assignments`) plus the `_get_stats` helper; fixed `_cleanup_assignment`/`_cleanup_assignments_for` to also delete `AssignmentOverride` rows
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — story/epic status tracking

**No changes to:**
- Any frontend file (`frontend/`) — this story is backend-only, confirmed in Scope Note 1
- `assignments/repository.py::list_assignments_for_dashboard`/`assignments/service.py::list_assignment_rows_for_dashboard_service` — the dead query was called as-is (not modified); the dead derivation function was left untouched and unused, not deleted (out of this story's scope)

## Change Log

- 2026-09-13: Story created (`bmad-create-story`), auto-discovered as the first backlog story in Epic 9. Used 4 parallel research subagents to exhaustively analyze `backend/app/dashboard/`, `backend/app/progress/`, `backend/app/assignments/`+`employees/`+the HR-admin auth gate, and recent git history before writing this story. Found and documented a real, non-obvious trap: `list_assignments_for_dashboard`/`list_assignment_rows_for_dashboard_service` are a fully-formed but completely dead code pair (superseded by the current paginated dashboard path, confirmed via zero live call sites) — the query is safe to resurrect, but its accompanying derivation logic is not (it predates the current `get_provenance_detail`/HR-Override-aware authority and would reintroduce exactly the kind of Status/Provenance drift AD-3 exists to prevent). Also flagged that the dead query doesn't eager-load `AssignmentOverride` rows, unlike the live dashboard endpoint's existing override-batching step — a real correctness gap for Total Completed if left unaddressed. Left the Employee-count module-ownership decision (assignments/ vs. employees/) genuinely open for the dev agent, since both modules currently touch `Employee` and this project's own AD-1 (single-owner modules) doesn't cleanly resolve it without a judgment call.
- 2026-09-13: Independent fresh-context quality review (checklist.md) run via a separate subagent that re-verified every technical claim directly against the code rather than trusting this file. Result: no critical issues — all function names/line numbers/dead-code claims/constants/schema shapes/test-fixture descriptions confirmed accurate, and no missed simpler employee-count query exists to reuse. One real gap fixed: Scope Note 5 now explicitly warns against also adding a `_batch_load_progress`-equivalent step, since the resurrected query already eager-loads `Assignment.progress` directly (unlike the live endpoint's `list_assignments_for_hr`, which is why *it* needs that extra batch step) — a dev agent pattern-matching "reuse the override-batching approach" could otherwise add an unneeded duplicate call. Status → `ready-for-dev`.
- 2026-09-13: Implementation complete (`bmad-dev-story`/Amelia, same session). All 7 tasks done: `DashboardStatsResponse` schema, `DashboardService.get_dashboard_stats` (resurrecting `list_assignments_for_dashboard`, batch-loading overrides via the existing helper, deriving Status through `get_provenance_detail` — never the bare percent-only function), `count_active_employees` (placed in `employees/repository.py` per AD-1, resolving Scope Note 6's open judgment call), and `GET /api/dashboard/stats`. **Real bug caught and fixed during implementation, not by review**: AC3's archived-Employee exclusion applies to every count, not just `total_employees` — the resurrected query has no `Employee.archived_at` awareness, so an archived Employee's still-active Assignments would otherwise inflate `total_skills_assigned`/`completed_count`. Fixed in the service layer; proven by a test that exercises the full create→verify→archive→verify lifecycle against the live DB. 5 new tests + 1 helper (delta-snapshot pattern, matching this file's live-shared-DB convention), plus 2 test-infrastructure FK-ordering bugs found and fixed in shared cleanup helpers (`AssignmentOverride` and `Account` rows weren't being deleted before their parent rows — both are test-only fixes, zero production impact). Full regression: 706 passed/2 skipped, zero regressions. Status → `review`.
- 2026-09-13: Code review (`bmad-code-review`, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor). 1 decision-needed resolved by user (Option 2: harden the endpoint — dropped the `match_content_for_skill` re-embed fallback entirely rather than accept the inherited write-on-read side effect, even though the sibling `GET /api/dashboard` endpoint still has it), 5 patches applied, 3 deferred (`deferred-work.md`), 4 dismissed as non-issues after verification. **Most consequential finding**: the video-duration fallback copied from the existing dashboard endpoint could trigger a real database write (Content re-embedding) from a GET call, directly contradicting AC4's read-only guarantee — confirmed by reading `content/service.py::match_content_for_skill` directly, not assumed. Fixed by removing the fallback for this endpoint specifically; an assignment with partial progress but unresolvable duration now classifies as Not Started here (documented trade-off) instead of pulling in a write. Other patches: the "In Progress" bucket is now genuinely exercised by a positive test case (the original test's docstring claimed one existed but it didn't — the assertion was a no-op); `overall_percent` now gets an exact-formula assertion, not just a bounds check; a documentation-only miscount ("6 new tests" vs. the actual 5 + 1 helper) corrected across the story file; the HR-Override test gained a missing `in_progress_count` assertion for parity with its sibling test; the schema gained a comment explaining `total_completed`/`completed_count`'s intentional duplication (per Scope Note 7) so a future reader doesn't "fix" it away. Full regression re-verified: 706 passed/2 skipped, identical to the pre-review baseline — zero regressions (patches strengthened assertions within the existing 5 test functions rather than adding new ones). Status → `done`.
