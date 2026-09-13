---
baseline_commit: 0b0b7e42
---

# Story 9.2: Backend: Employee Segmentation Endpoint

Status: done

## Story

As an **HR Admin**,
I want each Employee classified as On Track / In Progress / Needs Attention,
So that I can immediately see who actually needs my attention without scanning the full grid myself (FR-32, AR-27, AR-28).

## Scope Notes (read before starting)

1. **Backend-only. One new endpoint on the existing `dashboard/` module. No new table.** Confirmed against `epics.md`'s Story 9.2 scope and AR-26 ("read-composition owned by `dashboard/`, no new table"). The pie-chart UI and Needs Attention popover that consume this endpoint are Stories 9.3/9.4 — do not build any UI here (user decision this session: 9.2 ships backend-only, ahead of 9.3).

2. **New route: `GET /api/dashboard/segmentation`**, added as a third route inside the existing `backend/app/dashboard/router.py`, mirroring `/stats`'s exact shape byte-for-byte: `@router.get("/segmentation", response_model=EmployeeSegmentationResponse)`, `Depends(require_hr_admin)` + `Depends(get_db)`, no query params (single computed aggregate, not paginated). No new router file, no new `app.include_router(...)` — the existing mount (`backend/app/main.py:49`) already covers it.

3. **Reuse Story 9.1's exact read-composition pattern — do not re-derive Status/Provenance independently.** `DashboardService.get_dashboard_stats` (`backend/app/dashboard/service.py:117-194`) is the direct precedent:
   - `all_assignments = await list_assignments_for_dashboard(session)` (`assignments/repository.py:191-218` — eager-loads `employee`/`skill`/`content`/`progress`, filters only `Assignment.active`).
   - Archived-Employee exclusion happens in the **service**, not the repository (the query has no `Employee.archived_at` awareness): `assignments = [a for a in all_assignments if a.employee is not None and a.employee.archived_at is None]` (`service.py:139`).
   - Overrides are batch-loaded via the existing `DashboardService._batch_load_overrides` helper (`service.py:206-214`) — progress is already eager-loaded by the query, so no `_batch_load_progress` step (that helper is only needed by `get_dashboard_assignments`, whose query doesn't eager-load progress).
   - Per-assignment Status/Provenance comes from the existing `DashboardService._compute_status_and_provenance_from_data(assignment, progress, override, video_duration=video_duration)` helper (`service.py:216-242`), which delegates to `ProgressService.get_provenance_detail` (AD-3 authority) — **never reimplement this derivation**. It returns `(status_str, provenance_str, percentage, last_updated)` where `status_str` is one of `"Not Started"/"In Progress"/"Completed"` and `provenance_str` includes the literal `"Needs Attention"` value you need to detect.
   - `video_duration = ProgressRepository.get_video_duration(assignment)` — **do not** add the `match_content_for_skill` re-embed fallback that `get_dashboard_assignments` uses; that fallback can trigger a write (Content re-embedding), which Story 9.1's own code review found violates a GET endpoint's read-only guarantee (`service.py:156-168`'s comment explains why `get_dashboard_stats` deliberately omits it). This new endpoint must stay equally side-effect-free.

4. **New in-memory grouping this story actually introduces: by Employee, not by Assignment.** Story 9.1 iterates the flat assignment list once for org-wide counts. This story additionally needs to **group the same filtered assignment list by `assignment.employee_id`** before classifying, since segmentation is a per-Employee bucket, not a per-Assignment one. No existing helper does this grouping — write it fresh in the new service method. An Employee who has zero entries in the filtered assignment list (either genuinely zero active Assignments, or archived) is automatically excluded from the segmentation response simply by not appearing in any group — no separate exclusion check needed (this satisfies the AC's "excluded entirely, not silently defaulted" requirement for free, as a consequence of reusing the same filtered list Story 9.1 already builds).

5. **Classification priority order (exact, from epics.md — implement in this order, not as independent conditions):**
   1. **Needs Attention** — the Employee has at least one Assignment whose derived `provenance_str == "Needs Attention"`. Overrides everything else regardless of completion rate.
   2. **On Track** — no Needs Attention assignments, and `completed_count / total_count >= ON_TRACK_THRESHOLD` for that Employee's own Assignments (`completed_count` = Assignments where `status_str == "Completed"`; `total_count` = length of that Employee's filtered Assignment group).
   3. **In Progress** — everything else (explicit catch-all, including Employees at 0% complete / all Not Started — epics.md/PRD both confirm there is deliberately no 4th "Not Started" segment).

6. **`ON_TRACK_THRESHOLD` — new named constant (AR-28).** Follow the exact precedent already established by `NEEDS_ATTENTION_STALENESS_DAYS` in `backend/app/progress/service.py:22-27` (a plain module-level constant, not a `Settings`/`.env` field — "this threshold has no legitimate per-environment override case"). Place `ON_TRACK_THRESHOLD = 0.8` in **`backend/app/dashboard/service.py`** (not `progress/service.py`) — this is a dashboard-only segmentation concept, not part of `progress/`'s AD-3 per-Assignment Status/Provenance derivation authority, so it belongs with the module that owns this read composition (AR-26). Comment must explicitly point at **PRD Open Question 20** and state the value is a PM-drafted default, not user-confirmed (copy the exact framing from `addendum.md`: *"the item most likely to change once a real HR Admin sees the pie chart"*). Reference it from exactly one call site in the new segmentation logic — never inline `0.8` a second time anywhere.

7. **Needs Attention list — one entry per flagged Assignment, not one per Employee.** The AC requires "for each flagged Employee, their id/name and the specific flagged Skill/Assignment." An Employee can have more than one Needs-Attention Assignment; collapsing to a single representative skill per employee would silently drop data the frontend might need later (Story 9.4's popover is UX-DR45's "name + flagged Skill" — singular in the UX copy, but that's a popover *rendering* choice, not a reason for this backend to lose data). **Design decision for this story:** emit one `NeedsAttentionEntry` row per flagged Assignment (each carrying `employee_id`/`employee_name`/`assignment_id`/`skill_id`/`skill_name`); `needs_attention_count` in the response is the **count of distinct flagged Employees** (matching the pie chart's segment count), not the row count of the list (which can be ≥ that number). Document this distinction clearly in the schema docstring so Story 9.3/9.4 don't misread one for the other.

8. **Response schema — follow the existing plain-`BaseModel` pattern in `backend/app/dashboard/schemas.py`.** `DashboardStatsResponse` (no `from_attributes`, pure computed aggregate) is the direct precedent — new schemas `NeedsAttentionEntry` and `EmployeeSegmentationResponse` should match that same style, not `AssignmentRowResponse`'s ORM-passthrough style.

9. **AR-27 query-plan check — required before marking this story done, not assumed fine.** This is the first per-Employee-aggregation read in the project. Since this story reuses the *identical* `list_assignments_for_dashboard` query Story 9.1 already introduced (no new SQL query — only a new in-memory groupby over the same already-fetched rows), there is no new query plan to analyze beyond what 9.1's own review already flagged and deferred (`deferred-work.md`: "loads the entire org-wide active-assignment list into memory with no pagination/cap"). **Still required for this story:** record the actual current roster/assignment row counts from the live dev DB in Dev Notes (e.g. `SELECT COUNT(*) FROM employees WHERE archived_at IS NULL`, `SELECT COUNT(*) FROM assignments WHERE active = true`) so "fine at pilot scale" is a measured fact, not an assumption — and confirm no N+1 query pattern was introduced by the new per-Employee grouping (it must be pure in-memory list/dict work over data already fetched in one query + one batch-load, not a query-per-employee loop).

10. **Existing tests to extend, not replace or duplicate the setup of:** `backend/tests/test_dashboard.py` (service-layer, `db_session` fixture) and `backend/tests/test_dashboard_router.py` (HTTP-level — `_client()`, `_login()`, `_cleanup_assignment(s)_for()` helpers, seeded IDs from `app.core.seed_ids` (`RITA_ID`=HR Admin, `CASEY_ID`/`MORGAN_ID`=Employees) and `app.core.seeds` (`SKILL_DATA_VIZ_ID`, `SKILL_SALESFORCE_ID`), delta-snapshot pattern via a `_get_segmentation(client)` helper mirroring `_get_stats`). This is a **shared, ever-growing dev DB** — assert on deltas between before/after snapshots, never absolute counts. Note the added wrinkle for this story: because bucket membership (not just a count) is being asserted per-Employee, tests must use dedicated per-test Employees/skills (via `_cleanup_assignments_for`) so a seeded Employee's *other*, unrelated Assignments from other tests can't flip their bucket unexpectedly.

11. **Simulating "Needs Attention" in tests:** mirror however the existing `test_progress*.py`/`test_dashboard_router.py` suite already forces a stale Self-reported entry past `NEEDS_ATTENTION_STALENESS_DAYS` (7 days) to get a genuine `"Needs Attention"` provenance — grep `NEEDS_ATTENTION_STALENESS_DAYS` usage in the existing test suite for the established pattern (likely a direct DB insert with a backdated `SkillProgress`/self-report timestamp) rather than inventing a new one.

## Acceptance Criteria

**AC1 — Classification priority order:**
**Given** an active Employee with at least one active Assignment
**When** segmentation is computed
**Then** it is classified using this exact priority order: **Needs Attention** if any of their Assignments carries the "Needs Attention" Provenance Label (FR-10's existing 7-day staleness rule) — overriding everything else; else **On Track** if their completion rate (Completed Assignments ÷ their total active Assignments) is ≥ `ON_TRACK_THRESHOLD`; else **In Progress**.

**AC2 — Named threshold constant:**
**Given** `ON_TRACK_THRESHOLD`
**When** it is implemented
**Then** it exists as exactly one named config constant (AR-28) — not duplicated or inlined at more than one call site — defaulted to 0.8 per the PRD's own PM-drafted default, with a comment pointing at PRD Open Question 20 as still-unconfirmed.

**AC3 — Zero-assignment exclusion:**
**Given** an active Employee with zero active Assignments
**When** segmentation runs
**Then** that Employee is excluded entirely from the segmentation response (not counted toward any of the three buckets, and not silently defaulted into one).

**AC4 — Needs Attention detail payload:**
**Given** the "Needs Attention" bucket
**When** its response is built
**Then** it includes, for each flagged Employee, their id/name and the specific flagged Skill/Assignment — the frontend's popover (Story 9.4) needs this to render without a second round-trip.

**AC5 — First full-roster aggregation read, query-plan check required:**
**And** this is the first "compute something for every Employee, every page load" read in this project (AR-27) — a query-plan check against the actual roster size is recorded in this story's Dev Notes before being marked done, not assumed fine.

**AC6 — Role gate (implicit, matching every other HR-only endpoint in this module — FR-14, mirrors Story 9.1's AC5):**
**Given** the endpoint is called by a non-HR-Admin or unauthenticated session
**When** the request is evaluated
**Then** it is refused with the same 401/403 access-denied response FR-14 already defines for every other HR-only endpoint (`/api/dashboard/stats` is the exact same-module precedent).

## Tasks / Subtasks

- [x] **Task 1: Response schemas** (AC2, AC4) — `backend/app/dashboard/schemas.py`
  - [x] Added `NeedsAttentionEntry(BaseModel)`: `employee_id: uuid.UUID`, `employee_name: str`, `assignment_id: uuid.UUID`, `skill_id: uuid.UUID`, `skill_name: str`.
  - [x] Added `EmployeeSegmentationResponse(BaseModel)`: `on_track_count: int`, `in_progress_count: int`, `needs_attention_count: int` (distinct-Employee count — docstring states this explicitly), `needs_attention: list[NeedsAttentionEntry]` (one row per flagged Assignment).

- [x] **Task 2: `ON_TRACK_THRESHOLD` constant** (AC2, Scope Note 6) — `backend/app/dashboard/service.py`
  - [x] `ON_TRACK_THRESHOLD = 0.8` as a module-level constant, comment referencing PRD Open Question 20, mirroring `NEEDS_ATTENTION_STALENESS_DAYS`'s comment style/precedent in `progress/service.py:22-27`.

- [x] **Task 3: `DashboardService.get_employee_segmentation(session)`** (AC1, AC3, AC4, AC5, Scope Notes 3-4, 7)
  - [x] Reuses `list_assignments_for_dashboard` + the same archived-Employee filter Story 9.1 uses.
  - [x] Batch-loads overrides via the existing `_batch_load_overrides` helper (no new `_batch_load_progress` step).
  - [x] Groups filtered `assignments` by `assignment.employee_id` (new grouping logic, plain in-memory `dict`).
  - [x] For each Employee group, computes per-Assignment `(status_str, provenance_str, ...)` via the existing `_compute_status_and_provenance_from_data` helper (same no-side-effect `video_duration` resolution as `get_dashboard_stats`).
  - [x] Classifies each Employee per the AC1 priority order; collects `NeedsAttentionEntry` rows for every flagged Assignment when the bucket is Needs Attention.
  - [x] Returns `EmployeeSegmentationResponse` with the three bucket counts and the needs-attention list.

- [x] **Task 4: Router endpoint** (AC4, AC6) — `backend/app/dashboard/router.py`
  - [x] `@router.get("/segmentation", response_model=EmployeeSegmentationResponse)`, `Depends(require_hr_admin)` + `Depends(get_db)`, no query params — mirrors `/stats`'s docstring style.

- [x] **Task 5: AR-27 query-plan check** (AC5, Scope Note 9)
  - [x] Ran `SELECT COUNT(*) FROM employees WHERE archived_at IS NULL` (= 5) and `SELECT COUNT(*) FROM assignments WHERE active = true` (= 6) against the live dev DB.
  - [x] Confirmed by code inspection: `get_employee_segmentation` issues exactly one `list_assignments_for_dashboard` query + one `_batch_load_overrides` batch query, identical to Story 9.1's `get_dashboard_stats` — the per-Employee grouping is pure in-memory `dict`/`list` work over the already-fetched rows, zero additional SQL, no query-per-employee loop.
  - [x] Conclusion recorded below in Dev Notes.

- [x] **Task 6: Tests** (all ACs)
  - [x] `backend/tests/test_dashboard.py`: structural service-level test (`test_employee_segmentation_service_returns_response_structure`).
  - [x] `backend/tests/test_dashboard_router.py`: added `_get_segmentation(client)` helper plus `_create_throwaway_employee`/`_delete_employee_hard`/`_set_override_completed`/`_insert_stale_self_reported_progress` helpers, and 7 new tests: auth 401/403 gate; On Track (100% complete via HR Override); In Progress catch-all (0% complete, Not Started); Needs Attention overriding an otherwise-qualifying 80% completion rate (priority rule, not additive); zero-active-Assignments exclusion; archived-Employee exclusion (mirrors Story 9.1's lifecycle test).

- [x] **Task 7: Regression check**
  - [x] Full backend suite (`pytest -q`): 714 passed, 2 skipped (same 2 pre-existing skips as Story 9.1's baseline) — 706 → 714 is exactly the +8 new tests (1 structural + 7 router), zero regressions.

### Review Findings

_(`bmad-code-review`, 2026-09-13, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor. Findings verified against the actual code/schema before rating, not taken from the diff hunk alone.)_

- [x] [Review][Patch] No test proves the one real behavioral interaction between Needs Attention and HR Override: an Employee whose only flagged Assignment is then HR-Overridden must fall out of the Needs Attention bucket (since `get_provenance_detail` reports `"HR Override"`, never `"Needs Attention"`, once an override is active). The story's Dev Notes claim this was "confirmed safe via direct code reading" but no test exercises the combination. [backend/tests/test_dashboard_router.py] **Fixed:** added `test_employee_segmentation_override_clears_needs_attention_flag`.
- [x] [Review][Patch] `ON_TRACK_THRESHOLD`'s boundary is never tested in isolation — every existing test sits at 100%, 0%, or exactly 80% while simultaneously triggering the Needs Attention override (which masks whether the `>=` comparison itself is exercised cleanly). Need one test at a ratio just below threshold (e.g. 3/4 = 75%, no Needs Attention flags) landing In Progress, and one just at/above threshold with no override involved (e.g. 4/5 = 80%, natural completions only) landing On Track. [backend/tests/test_dashboard_router.py] **Fixed:** added `test_employee_segmentation_on_track_boundary_without_override` and `test_employee_segmentation_below_threshold_lands_in_progress`.
- [x] [Review][Patch] No test asserts the endpoint's read-only/no-side-effect guarantee — the whole point of deliberately omitting the `match_content_for_skill` fallback (Scope Note 3) is that this GET must never trigger a Content re-embed write, but nothing catches a future regression that reintroduces that call. [backend/tests/test_dashboard_router.py] **Fixed:** added `test_employee_segmentation_never_triggers_content_reembed_write` (mocks `app.dashboard.service.match_content_for_skill`, asserts never called).
- [x] [Review][Patch] `by_employee: dict = {}` is untyped, inconsistent with this same file's precedent of precise type hints elsewhere (e.g. `dict[UUID, SkillProgress]`). [backend/app/dashboard/service.py] **Fixed:** typed as `dict[UUID, list[Assignment]]` (added `Assignment` to the existing `app.assignments.models` import).
- [x] [Review][Defer] Unbounded `needs_attention` list growth with no cap/pagination — extends Story 9.1's already-deferred AR-27 "no pagination/cap" debt to a list-shaped payload specifically. Real at scale, non-urgent at current pilot scale (5 Employees), and a capping/truncation strategy is better decided alongside Story 9.3/9.4 (the actual consumers) than unilaterally in this backend-only story.
- [x] [Review][Defer] Cross-endpoint consistency between `/stats` and `/segmentation` (two independent reads of the same mutable data, no shared snapshot/transaction) — extends Story 9.1's own already-deferred single-endpoint consistency gap to a second endpoint that must now visually agree with the first on the landing page. Low practical impact at this project's pilot scale (coaching-only data, AR-15 local-only target).
- [x] [Review][Defer] `get_dashboard_stats` and `get_employee_segmentation` independently re-run the identical expensive `list_assignments_for_dashboard` + override-batch-load read with no shared helper — real duplication/maintenance cost (the archived-Employee filter logic is now copy-pasted in two places), but consolidating is an architectural call better made once Story 9.3 reveals actual call patterns, not a mechanical fix.

Dismissed as non-issues after verification: a claimed float-rounding risk at the exact 0.8 threshold was verified false — empirically confirmed every fraction mathematically equal to 0.8 (4/5, 8/10, 16/20, 40/50, 12/15) rounds to the identical IEEE-754 double as the literal `0.8`, so no boundary misclassification is possible for this specific threshold value; claimed `None`-name crashes for `employee_name`/`skill_name` were verified false — both `Employee.name` and `Skill.name` are `nullable=False` at the DB level; a claimed duplicate-row risk from query "fan-out" was verified false — `list_assignments_for_dashboard` uses `selectinload`, not `joinedload`, so no join-based duplication is possible; the `"Unknown"` fallback for `employee`/`skill` was verified unreachable in practice — both FKs are `nullable=False` with default RESTRICT delete behavior, and the fallback is copied verbatim from the existing, already-accepted `get_dashboard_assignments` pattern; the status/provenance literal-string comparison "fragility" matches this same file's own pre-existing `get_dashboard_stats` convention, not a new regression; `needs_attention_count != len(needs_attention)` being a "footgun" was already explicitly reasoned through and documented on both the field and the class as a deliberate design decision (Scope Note 7); the `sprint-status.yaml` `last_updated` line being overwritten rather than appended was verified to match that field's own established convention (a "latest status" snapshot, not a log — only `action_items` is documented as append-only), with the full historical narrative correctly preserved separately in `project-context.md`; test-helper duplication (`_delete_employee_hard` as a third cleanup variant) matches this same test file's precedent, already dismissed in Story 9.1's own review as consistent with an accepted pattern; `needs_attention` list ordering was confirmed already deterministic today (dict insertion order following the underlying query's `ORDER BY assigned_at DESC`), just not contractually documented — cosmetic only; a claimed docstring-wording mismatch between `/stats` and `/segmentation` was self-assessed by the Acceptance Auditor as cosmetic, not a Scope-Note-2 violation; a claimed AC5 evidence gap (the query-plan check "isn't in the diff") was confirmed to be a diff-scope artifact only — the untracked story file itself (excluded from `git diff HEAD`) already contains the actual live-DB counts and Task 5 checkboxes, so the required check was genuinely performed, just not visible in the reviewed diff until this file is added to git.

## Dev Notes

### AR-27 query-plan conclusion

Current dev DB: 5 active Employees, 6 active Assignments (queried directly, not assumed). `get_employee_segmentation` adds no new SQL query beyond what Story 9.1's `get_dashboard_stats` already introduced and whose no-pagination/no-cap concern is already tracked in `deferred-work.md` — this story's only new cost is an in-memory `dict` groupby over the same already-fetched rows (O(n) over the assignment list, no additional round-trips). At current pilot scale this is trivially fine; no new deferred-work entry needed since the underlying query's scaling concern is already tracked under Story 9.1's entry and applies identically here (same query, same caller-side fan-out risk).

### Design decisions carried through from story authoring (confirmed during implementation, no deviation)

- `ON_TRACK_THRESHOLD` lives in `dashboard/service.py`, not `progress/service.py` — segmentation is a dashboard-owned aggregation (AR-26), not part of `progress/`'s AD-3 per-Assignment derivation authority.
- `needs_attention` is one entry per flagged Assignment (not deduplicated per Employee); `needs_attention_count` is the distinct-Employee count, computed separately (`needs_attention_employee_count`) rather than derived from `len(needs_attention_entries)`, so the two can never accidentally be conflated by a future edit.
- An Employee with zero active Assignments needs no explicit exclusion check — they simply never get a key in the `by_employee` dict, since that dict is built only from the already-filtered `assignments` list. Verified by `test_employee_segmentation_excludes_employee_with_zero_active_assignments`.
- Real, non-obvious test-design finding during implementation: the seeded demo Employees (Casey/Morgan/Rita) could **not** be reused for bucket-membership assertions the way earlier dashboard tests reuse them for count-delta assertions, because segmentation bucket membership is a function of an Employee's *entire* active-Assignment set, not just the row(s) a given test creates — a seeded Employee's other, unrelated Assignments (from other tests sharing this dev DB) would make their resulting bucket unpredictable. Solved by creating a dedicated throwaway Employee per test scenario (same pattern Story 9.1's archived-Employee test already established for a different reason), then asserting on before/after count deltas around that Employee's fully-controlled Assignment set.
- HR Override (`POST /api/assignments/{id}/override`) was used to force "Completed" status in tests without needing to fabricate exact watch-percentage/duration data — confirmed via `get_provenance_detail` (`progress/service.py:407-420`) that an active override's `status` counts as `AssignmentStatus.COMPLETED` for completion-rate purposes while its `provenance` becomes `"HR Override"` (never `"Needs Attention"`), so this doesn't interfere with the priority-override test's genuine (non-overridden) Needs Attention assignment.

## Architecture Compliance

- AR-26: read-composition owned by `dashboard/`, no new table. ✅ (`get_employee_segmentation` reads only; no writes, no new model/migration.)
- AR-27: first per-Employee, full-active-roster aggregation read — query-plan check recorded above (Task 5); no new SQL query introduced, in-memory-only new work. ✅
- AR-28: `ON_TRACK_THRESHOLD` implemented as exactly one named module-level constant (`dashboard/service.py`), referenced from exactly one call site. ✅
- AR-8 (module dependency direction): `dashboard` depends on `assignments`/`progress`, never the reverse — no new dependency direction introduced. ✅
- AD-3: Status/Provenance derivation stays solely in `progress/` — this story calls into it via the existing `_compute_status_and_provenance_from_data`/`get_provenance_detail` chain, never reimplements it. ✅

## Architecture Compliance

- AR-26: read-composition owned by `dashboard/`, no new table.
- AR-27: first per-Employee, full-active-roster aggregation read — query-plan check recorded in Dev Notes per Task 5 before this story is marked done.
- AR-28: `ON_TRACK_THRESHOLD` implemented as exactly one named module-level constant (Task 2), never inlined elsewhere.
- AR-8 (module dependency direction): `dashboard` depends on `assignments`/`employees`/`progress`, never the reverse — this story adds no new dependency direction, only new read calls along existing-allowed directions.
- AD-3: Status/Provenance derivation stays solely in `progress/` — this story calls into it via the existing `_compute_status_and_provenance_from_data`/`get_provenance_detail` chain, never reimplements it.

## References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 9.2] — full AC text, Epic 9 scope, AR-27/AR-28
- [Source: _bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md#FR-32] — Employee Segmentation priority order, 80% threshold assumption, Open Question 20
- [Source: _bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/addendum.md] — "80% On-Track threshold is a literal constant" framing to mirror in the code comment
- [Source: _bmad-output/planning-artifacts/epics.md#UX-DR45/UX-DR46] — Needs Attention popover shape (name + flagged Skill) that this endpoint's response must support without a second round-trip
- [Source: _bmad-output/implementation-artifacts/9-1-backend-org-wide-stats-and-assignment-progress-endpoint.md] — direct sibling story; read-composition pattern, dead-code trap already resolved, archived-Employee exclusion precedent, AR-27 deferral already logged for the shared query
- [Source: backend/app/dashboard/service.py:117-242] — `get_dashboard_stats`, `_batch_load_overrides`, `_compute_status_and_provenance_from_data` — the exact pattern to extend
- [Source: backend/app/dashboard/schemas.py] — `DashboardStatsResponse` plain-`BaseModel` pattern to mirror
- [Source: backend/app/dashboard/router.py:57-74] — `/stats` endpoint, the exact shape to mirror for `/segmentation`
- [Source: backend/app/progress/service.py:22-27] — `NEEDS_ATTENTION_STALENESS_DAYS` constant precedent for `ON_TRACK_THRESHOLD`'s placement/comment style
- [Source: backend/app/assignments/repository.py:191-218] — `list_assignments_for_dashboard`
- [Source: backend/app/employees/repository.py:23-33] — `count_active_employees` (module-ownership precedent, not directly reused here since segmentation only needs Employees who already appear in the assignment list)
- [Source: backend/tests/test_dashboard_router.py] — `_client`, `_login`, `_cleanup_assignment(s)_for`, `_get_stats`, seeded IDs — fixtures/helpers to extend
- [Source: _bmad-output/implementation-artifacts/deferred-work.md] — existing AR-27 deferral entry from Story 9.1, to be referenced rather than duplicated

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5

### Debug Log References

- `pytest tests/test_dashboard.py tests/test_dashboard_router.py -v`: initial run of the new tests confirmed RED (`AttributeError: type object 'DashboardService' has no attribute 'get_employee_segmentation'` for the structural test; `404` for all 7 router tests, since `/api/dashboard/segmentation` didn't exist yet) before any implementation code was written. After implementing schemas/constant/service/router: 24/24 passed (17 pre-existing + 7 new router tests + the 1 new structural test — note the file already had 10 pre-existing tests before Story 9.1/9.2 additions).
- One test-only fix during GREEN: `test_employee_segmentation_needs_attention_overrides_high_completion` initially asserted `skill_name == "Communication"`, but the seeded skill's actual name is `"Communication Skills"` (`app/core/seeds.py:90`) — corrected the assertion to the real seeded value rather than changing production code.
- Full suite: `pytest -q` → 714 passed, 2 skipped (same 2 pre-existing skips as Story 9.1's last-recorded baseline of 706 passed/2 skipped), 111s. 706 → 714 = exactly the 8 new tests added. Zero regressions.
- AR-27 query-plan check: `SELECT COUNT(*) FROM employees WHERE archived_at IS NULL` → 5; `SELECT COUNT(*) FROM assignments WHERE active = true` → 6 (run directly against the live dev DB via a throwaway script using `app.core.db.engine`).

### Completion Notes List

- New `NeedsAttentionEntry`/`EmployeeSegmentationResponse` schemas (`dashboard/schemas.py`), `DashboardService.get_employee_segmentation` + `ON_TRACK_THRESHOLD` constant (`dashboard/service.py`), and `GET /api/dashboard/segmentation` (`dashboard/router.py`) — all following Story 9.1's exact dashboard-module conventions (auth deps, response-model style, read-composition-only, no new SQL query beyond the existing org-wide read + override batch-load).
- True TDD: wrote the structural service test and all 7 router tests first, confirmed every one failed for the expected reason (missing attribute / 404), then implemented schemas → constant → service → router until all 8 passed, with zero changes needed to the tests' logic (only the one seeded-skill-name assertion fix above).
- Real test-design problem found and solved during implementation, not anticipated in the story's Scope Notes at the same level of specificity: bucket-membership assertions can't reuse the seeded demo Employees (Casey/Morgan/Rita) the way Story 9.1's count-delta tests do, because segmentation looks at an Employee's *entire* active-Assignment set — their other Assignments from unrelated tests in this shared dev DB would make the bucket unpredictable. Solved with a dedicated-throwaway-Employee-per-test-scenario pattern (extending, not duplicating, Story 9.1's own archived-Employee-test precedent).
- HR Override was used as a lightweight way to force Completed status in tests (avoiding the need to fabricate exact watch-position/video-duration data) — confirmed safe via direct code reading of `get_provenance_detail`'s override branch (an active override's provenance is always `"HR Override"`, never `"Needs Attention"`, so it can't accidentally interfere with the genuine-Needs-Attention priority test).
- AR-27's query-plan check was completed as scoped in the story: no new SQL query is introduced by this endpoint (verified by code inspection — one `list_assignments_for_dashboard` call + one `_batch_load_overrides` call, identical to `get_dashboard_stats`), and current live-DB roster/assignment counts (5 Employees, 6 Assignments) were recorded to make "fine at pilot scale" a measured fact rather than an assumption.

### File List

**Modified:**
- `backend/app/dashboard/schemas.py` — added `NeedsAttentionEntry`, `EmployeeSegmentationResponse`
- `backend/app/dashboard/service.py` — added `ON_TRACK_THRESHOLD` constant and `DashboardService.get_employee_segmentation`; added `Assignment` to the existing `app.assignments.models` import and typed `by_employee` as `dict[UUID, list[Assignment]]` (review patch)
- `backend/app/dashboard/router.py` — added `GET /api/dashboard/segmentation`
- `backend/tests/test_dashboard.py` — added `test_employee_segmentation_service_returns_response_structure`
- `backend/tests/test_dashboard_router.py` — added imports (`SKILL_COMMUNICATION_ID`, `SKILL_PYTHON_ID`, `SKILL_SQL_ID`, `timedelta`, `unittest.mock`), 5 new helpers (`_get_segmentation`, `_create_throwaway_employee`, `_delete_employee_hard`, `_set_override_completed`, `_insert_stale_self_reported_progress`), and 11 new tests: the original 7 (`test_employee_segmentation_requires_authentication`, `test_employee_segmentation_forbidden_for_employee_role`, `test_employee_segmentation_on_track_employee`, `test_employee_segmentation_in_progress_catchall_for_zero_percent`, `test_employee_segmentation_needs_attention_overrides_high_completion`, `test_employee_segmentation_excludes_employee_with_zero_active_assignments`, `test_employee_segmentation_excludes_archived_employee`) plus 4 added during code review (`test_employee_segmentation_on_track_boundary_without_override`, `test_employee_segmentation_below_threshold_lands_in_progress`, `test_employee_segmentation_override_clears_needs_attention_flag`, `test_employee_segmentation_never_triggers_content_reembed_write`)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — story/epic status tracking
- `_bmad-output/implementation-artifacts/deferred-work.md` — 3 findings deferred from this story's code review

**No changes to:**
- Any frontend file (`frontend/`) — this story is backend-only, confirmed in Scope Note 1 and via `AskUserQuestion` at kickoff
- `assignments/repository.py::list_assignments_for_dashboard` / `employees/repository.py::count_active_employees` — reused as-is, not modified

## Change Log

- 2026-09-13: Story created (`bmad-create-story`), for Epic 9 / Story 9.2, per explicit user request to implement this story next (backend-only scope confirmed via `AskUserQuestion` — UI/pie-chart consumption deferred to Story 9.3, which this story does not touch). Analyzed Story 9.1's implementation directly (its file, plus live `backend/app/dashboard/service.py`, `schemas.py`, `router.py`, `progress/service.py`, `assignments/repository.py`, `employees/repository.py`, and `test_dashboard_router.py`) to extract the exact read-composition pattern, constant-placement precedent (`NEEDS_ATTENTION_STALENESS_DAYS`), and test fixtures to reuse — no new pattern needed to be invented beyond the per-Employee grouping step and the `ON_TRACK_THRESHOLD` constant itself. Key judgment calls made during story authoring and documented above for the dev agent to confirm or revise: (1) `ON_TRACK_THRESHOLD` placed in `dashboard/service.py`, not `progress/service.py`, since segmentation is a dashboard-owned aggregation, not part of `progress/`'s AD-3 per-Assignment derivation authority; (2) the Needs Attention list is one row per flagged Assignment (not per Employee) to avoid silently dropping data, with `needs_attention_count` explicitly documented as the distinct-Employee count rather than the row count; (3) AR-27's required query-plan check is scoped to confirming no new SQL query pattern is introduced (this story reuses Story 9.1's exact org-wide read), plus recording actual current roster/assignment counts from the live dev DB — not a full index/EXPLAIN audit, since the underlying query itself was already flagged and deferred by Story 9.1's own code review.
- 2026-09-13: Implementation complete (`bmad-dev-story`/Amelia, same session), full red-green-refactor cycle. Wrote the structural service test and all 7 router tests first and confirmed each failed for the expected reason before writing any production code. Implemented `NeedsAttentionEntry`/`EmployeeSegmentationResponse` schemas, `ON_TRACK_THRESHOLD` constant, `DashboardService.get_employee_segmentation`, and `GET /api/dashboard/segmentation`, all directly mirroring Story 9.1's established patterns — no new SQL query introduced (AR-27 confirmed by code inspection: one existing org-wide read + one existing override batch-load, same as `get_dashboard_stats`; only new work is an in-memory per-Employee groupby). All 3 classification buckets tested individually, including the priority-override case (an 80%-complete Employee with one genuine stale Needs Attention assignment correctly lands in Needs Attention, not On Track) and zero-Assignment/archived-Employee exclusion. One test-only fix during GREEN (a wrong assumed seeded skill name, corrected to the real value). Full regression: 714 passed/2 skipped (706 → 714 = exactly the 8 new tests), zero regressions. Status → `review`.
- 2026-09-13: Code review (`bmad-code-review`, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor, run against the uncommitted diff with this story file as spec context). 0 decision-needed, 4 patches applied, 3 deferred (`deferred-work.md`), 11 dismissed as non-issues after verification. **Most consequential findings**: (1) the story's own Dev Notes claimed the Needs-Attention/HR-Override interaction was "confirmed safe via direct code reading," but nothing tested it — fixed by adding `test_employee_segmentation_override_clears_needs_attention_flag`, which proves a genuinely stale Assignment that then gets HR-Overridden correctly clears the Employee's Needs Attention flag; (2) `ON_TRACK_THRESHOLD`'s `>=` comparison itself was never actually exercised — every prior test sat at 0%, 100%, or a threshold-boundary case masked by a simultaneous Needs Attention override — fixed with two new boundary tests (natural 80% with zero overrides → On Track; 75% → In Progress); (3) the endpoint's read-only/no-side-effect guarantee (the reason `match_content_for_skill`'s fallback is deliberately omitted) had no regression test — fixed by mocking that function and asserting it's never called. A 4th, minor patch: `by_employee: dict = {}` was untyped — fixed to `dict[UUID, list[Assignment]]`. Several claimed defects were investigated and verified false rather than dismissed on faith: an alleged float-rounding risk at the exact 0.8 threshold was empirically disproven (every fraction mathematically equal to 0.8 rounds to the identical IEEE-754 double); alleged `None`-name crash risks were disproven against the actual schema (`Employee.name`/`Skill.name` are both `nullable=False`); an alleged join-fan-out duplicate-row risk was disproven (`selectinload`, not `joinedload`, is used). 3 real-but-non-urgent findings were deferred (unbounded `needs_attention` list growth; cross-endpoint `/stats`↔`/segmentation` consistency; duplicated expensive-read pattern between the two dashboard endpoints) — all extend already-accepted Story 9.1 deferrals rather than introducing new categories of debt. Full regression re-verified: 718 passed/2 skipped (714 + 4 new patch tests), zero regressions. Status → `done`.
