---
story_key: 5-5-hr-override-manual-readiness-confirmation
epic: 5
story_num: 5
dependencies:
  - 5-1-assignment-dashboard-grid-status-badge-display
  - 5-2-provenance-drill-down-modal-trust-detail-and-raw-data
baseline_commit: 4ae858d
---

# Story 5.5: HR Override — Manual Readiness Confirmation

Status: review

**Epic:** 5 (Readiness Dashboard — Status, Provenance, Auto-Update & Override)
**Story ID:** 5.5
**Functional Requirements:** FR-12 (HR Admin manually overrides an assignment's readiness status)
**Architecture Rules:** AD-4 (HR Override is a separate, coexisting record — never a field-overwrite), AR-4, AD-1 (single-owner data modules), AD-6 (server-side role/identity gate)
**NFRs:** NFR-A2 (Provenance never color-only), NFR-C1/C2 (coaching-only boundaries)
**Data Model:** Table 7 `assignment_overrides` (epics.md:520-533) — **already exists** in the DB (created in `001_initial_schema.py`, read side built by Story 5.2). This story builds the **write path only**.

This story is a **shared backend endpoint + a Mark-as-Ready frontend flow**. It does **not** build the "[Reverse Override]" button UI — that's Story 5.5b's job (still `backlog`). It does build the backend's `unset` action, because the data model, AR-4's "second validated write path," and Story 5.5b's own AC all describe **one** `POST /override` endpoint handling both actions — building only half of it now would mean re-touching this same endpoint in 5.5b for no reason.

---

## User Story

As an **HR Admin**,
I want to manually mark an Assignment as Ready (e.g., because I verified competency in a conversation),
So that I can use the dashboard even when auto-captured data doesn't reflect my assessment.

---

## ⚠️ Critical Pre-Implementation Findings (read before coding)

Found by reading the actual current code — `progress/service.py`, `progress/repository.py`, `assignments/schemas.py`, `dashboard/service.py`, `ProvenanceDrillDownModal.tsx` — not just the epic text.

### Finding 1 — The read side is already 100% done; this story is write-path only

Story 5.2 already built everything needed to **display** an HR Override: `AssignmentOverride` model (`assignments/models.py:122-143`), the table (`001_initial_schema.py:128-146`), `ProgressRepository.get_active_override_for_assignment()` / `get_active_overrides_for_assignments()` (`progress/repository.py:289-373`), and `ProgressService.get_provenance_detail()` (`progress/service.py:356-445`) — which `dashboard/service.py` (grid) and `get_drill_down_service` (modal) both already call. **Do not touch `dashboard/service.py`, `dashboard/router.py`, or `dashboard/repository.py` at all** — the moment a row's `active` override flag flips, the existing grid/drill-down read path already derives and displays it correctly (verified by reading `dashboard/service.py:122-147`). If you find yourself editing those files, stop — you've misread the scope.

### Finding 2 — `ProvenanceLabel.HR_OVERRIDE` should NOT be added despite what its own docstring says

`assignments/schemas.py:35-39`'s `ProvenanceLabel` docstring reads: *"HR_OVERRIDE (Story 5.5, AssignmentOverride-backed case) is intentionally not yet a member here... add HR_OVERRIDE when Story 5.5 builds the create/reverse mutation path."* Reading the actual consumers shows this is stale advice: nothing anywhere compares against a `ProvenanceLabel.HR_OVERRIDE` enum value — the real merge point is the plain string constant `PROVENANCE_HR_OVERRIDE = "HR Override"` in `progress/service.py:47`, already wired into `DrillDownResponse.provenance`'s `Literal[...]` (`assignments/schemas.py:181`) and the frontend's `ProvenanceType` union (`types/dashboard.ts:6-11`). Adding an actual enum member with the same literal value `"HR Override"` would risk nothing today (it doesn't collide with `AssignmentStatus`'s members), but it's dead weight no code path reads — and this exact class of "docstring says do X, the working code doesn't need X" mistake is what caused the real `NOT_STARTED` cross-type equality bug Story 5.3's review caught (same file, same enum family, see the `CAUTION` block right above it). **Do not add the enum member.** Leave the docstring as-is (harmless staleness, not a build blocker).

### Finding 3 — A real, already-logged bug you're now unblocking: the `||` vs `??` reason display

`deferred-work.md` (Story 5-2 review) already flags: `ProvenanceDrillDownModal.tsx:199`'s `{data.override_reason || "No reason provided"}` uses `||` not `??` — a non-null-but-whitespace-only reason would render a blank line. It was unreachable before (no create-override endpoint existed to submit one). **Fix both halves this story**: backend trims `reason` and coerces empty/whitespace-only to `None` before persisting (so a real whitespace-only reason can't even reach the DB), **and** the frontend fallback becomes `??` (defense in depth, in case a pre-existing row somehow has a blank string).

### Finding 4 — Mutual-exclusivity of the two Action buttons is a real, already-written AC, not a new invention

`epics.md:1713-1717` (Story 5.2's own "Actions:" section, which predates the 5.5/5.5b split) is explicit: *"If Provenance ≠ HR Override: `[Mark as Ready]` button... If Provenance = HR Override: `[Reverse Override]` button"* — mutually exclusive, never both. Story 5.5b's own AC ("Reversal Button Visibility") re-specifies the `[Reverse Override]` half of this in detail — that's explicitly its job. **This story's job is only the `[Mark as Ready]` half**: render it (enabled) only when `data.provenance !== "HR Override"`; hide it entirely when an override is already active. **Do not touch `[Reverse Override]`'s visibility or `disabled` state** — leave it exactly as the current unconditional disabled stub (`ProvenanceDrillDownModal.tsx:129-136`); Story 5.5b owns making it conditional and enabled.

### Finding 5 — `get_drill_down_service` already crosses a module boundary; don't extend that pattern into new write code

`assignments/service.py::get_drill_down_service` (lines 139-179) calls `ProgressRepository.get_progress_for_assignment()` / `get_active_override_for_assignment()` directly — a read-only, already-flagged AD-1 boundary gap (`deferred-work.md`, Story 5-1 review: *"Ad-hoc Late Import... Refactor module imports to respect AD-1 boundaries (service-to-service, not service-to-repository cross-module)"*). That's pre-existing and out of this story's scope to fix. **But do not copy the pattern for the new mutation.** Add a proper `ProgressService.set_override(...)` method (service-to-service, matching AD-1's actual rule) and have `assignments/service.py`'s new function call *that* — not reach into `ProgressRepository` directly for the write. A write path reaching around the owning module's service is a worse violation than the existing read-side one.

---

## Acceptance Criteria

_Verbatim intent from epics.md lines 1791-1826 (Story 5.5), numbered for traceability. Story 5.5b's own AC (lines 1830-1941) documents the `[Reverse Override]` UI — out of this story's scope, but the backend `unset` action below must already satisfy its contract since it's the same endpoint._

1. **Given** an Assignment row with incomplete or stale data, **when** the HR Admin drills down and the Provenance is not already "HR Override", **then** a `[Mark as Ready]` button is visible (Finding 4). [epics.md:1799-1800]
2. **When** `[Mark as Ready]` is clicked, **then** a confirmation view opens: `"Mark {Employee} as Ready for {Skill}?"`, an optional "Reason" text field, and `[Confirm]`/`[Cancel]` buttons. [epics.md:1802-1804]
3. **On Confirm:** `POST /api/assignments/{assignment_id}/override` with `{ action: 'set', reason?: string }`. Backend creates a new `assignment_overrides` row (`assignment_id`, `set_by`, `set_at`, `reason`, `active=true`) — **no `skill_progress` row is modified** (AD-4: separate record, never a field-overwrite). [epics.md:1806-1810]
4. **Immediately** after Confirm succeeds: the Assignment's Status badge becomes **Completed**; the Provenance Label becomes **HR Override** (never **Verified**); the drill-down shows both the override and the underlying signal (watch % or self-report) — this is Finding 1's existing `get_provenance_detail()` derivation, triggered automatically once the override row exists; no new derivation code is needed, only a fresh read after the write. [epics.md:1812-1815]
5. **If** a fresh watch-position update arrives for this Assignment after the override: the underlying `skill_progress` updates normally; the drill-down shows both signals; the override is **not** replaced by the fresh signal — this is already true by construction (`get_provenance_detail` always computes the underlying signal first, then wraps it — `progress/service.py:370-373`); no new code required, just don't break it. [epics.md:1817-1820]
6. **Backend-only** (no UI this story, Finding 4): an HR Admin can reverse an override via the same endpoint — `POST /api/assignments/{assignment_id}/override { action: 'unset' }` — which sets `assignment_overrides.active = false` (plus `reversed_at`/`reversed_by`, per Table 7's schema, since this story owns "HR Override Data Model"). Status then reverts to the underlying signal. [epics.md:1822-1826]
7. **Access control:** an EMPLOYEE session calling the endpoint (either action) gets **403 Forbidden**; a non-owning HR Admin (didn't create the assignment) also gets **403** — same uniform 403 as Story 5.2's drill-down, no existence leak (AD-6, mirrors `get_assignment_scoped_to_hr_admin`'s pattern).
8. **Reason handling** (Finding 3): `reason` is optional; if provided, it is trimmed server-side and stored as `NULL` if empty/whitespace-only after trimming — never a blank string.
9. **At-most-one-active-override invariant:** if `action: 'set'` is called while an override is already active for that assignment, the existing active override is deactivated (same as a reversal, attributed to the acting HR Admin) before the new one is created — never two simultaneously-active override rows for one assignment.
10. **`unset` with no active override:** returns an error (404) rather than silently succeeding — there is nothing to reverse.

---

## Tasks / Subtasks

- [x] Task 1: Backend — repository methods (AC: 3, 6, 9; `progress/repository.py`, since `progress/` owns `assignment_overrides` per the paradigm table, `ARCHITECTURE-SPINE.md:31`)
  - [x] Subtask 1.1: `ProgressRepository.create_override(session, *, assignment_id, set_by, reason) -> AssignmentOverride` — inserts a new row (`override_status="COMPLETED"`, `active=True`; no status field in the request contract per AC3, so this is always the schema default — do not add a status parameter nobody can set).
  - [x] Subtask 1.2: `ProgressRepository.deactivate_override(session, override, *, reversed_by) -> None` — mutates the given `AssignmentOverride` in place: `active=False`, `reversed_at=now(timezone.utc)`, `reversed_by=reversed_by`; `session.flush()`. Reuse this same method for both the "deactivate the old one before creating a new one" case (AC9) and the `unset` action (AC6) — one method, two callers.
  - [x] Subtask 1.3: Reuse the existing `get_active_override_for_assignment` (already there, `progress/repository.py:289-312`) — do not duplicate it.

- [x] Task 2: Backend — service method (AC: 3, 4, 5, 6, 8, 9, 10; `progress/service.py`, Finding 5)
  - [x] Subtask 2.1: Add `ProgressService.set_override(session, *, assignment, current_user, action, reason, video_duration) -> ProvenanceDetail`:
    - `action == "set"`: fetch current active override (if any) via `get_active_override_for_assignment`; if present, `deactivate_override(..., reversed_by=<current_user's employee id>)` first (AC9); then `create_override(..., set_by=<current_user's employee id>, reason=<trimmed-or-None>)`.
    - `action == "unset"`: fetch current active override; if `None`, raise `AppException(status.HTTP_404_NOT_FOUND, error_code="NO_ACTIVE_OVERRIDE", message="No active override exists to reverse")` (AC10); else `deactivate_override(...)`.
    - Trim `reason` here (`reason.strip() or None` if not falsy already) — Finding 3, do this once, not in both the repository and the router.
    - After mutation: re-fetch progress (`ProgressRepository.get_progress_for_assignment`) and the (now-current) active override, then return `ProgressService.get_provenance_detail(assignment, progress, override, video_duration)` — reuses the existing single-derivation-authority function (AC4/AC5), does not recompute anything new.
    - `await session.commit()` at the end (matches `record_watch_progress`'s own commit-on-success convention, `progress/service.py:164`).
  - [x] Subtask 2.2: Extracting the HR Admin's own Employee UUID: use the same `uuid.UUID(current_user.user_id)` pattern already established in `assignments/repository.py::_parse_user_id` / `progress/service.py::get_resume_position` (`UUID(current_user.user_id)`) — do not invent a second parsing helper. Since `progress/service.py` doesn't currently import `assignments.repository._parse_user_id` (that's a private, underscore-prefixed helper — not meant for cross-module import), inline `uuid.UUID(current_user.user_id)` directly, matching `get_resume_position`'s own existing precedent one function above.

- [x] Task 3: Backend — request/response schema (AC: 3, 6, 8; `assignments/schemas.py`)
  - [x] Subtask 3.1: `SetOverrideRequest(BaseModel)`: `action: Literal["set", "unset"]`, `reason: str | None = None`. Add `model_config = ConfigDict(extra="forbid")` matching `CreateAssignmentRequest`'s established convention (`assignments/schemas.py:73-74`) — no client-supplied `override_status`, `set_by`, or `active` field (those are server-derived, AC3's "no status field in the request contract").
  - [x] Subtask 3.2: Reuse `DrillDownResponse` as the endpoint's response model — do not invent a new response shape. The whole point of routing the mutation through `get_provenance_detail()` (Task 2) is that the POST response and a subsequent GET `/progress/drill-down` are byte-identical for the same state (AR-3).

- [x] Task 4: Backend — service orchestration + endpoint (AC: 3, 4, 6, 7; `assignments/service.py`, `assignments/router.py`, Finding 5)
  - [x] Subtask 4.1: Add `set_override_service(session, *, current_user, assignment_id, request: SetOverrideRequest) -> DrillDownResponse` to `assignments/service.py`:
    - `require_hr_admin(current_user)` (AC7)
    - `assignment = await get_assignment_scoped_to_hr_admin(session, assignment_id=assignment_id, hr_admin_id=_parse_user_id(current_user))`; if `None`, raise the same uniform `403` `get_drill_down_service` already raises (AC7, no existence leak) — copy that exact pattern (`assignments/service.py:155-156`).
    - `video_duration = ProgressRepository.get_video_duration(assignment)`
    - `detail = await ProgressService.set_override(session, assignment=assignment, current_user=current_user, action=request.action, reason=request.reason, video_duration=video_duration)`
    - Build and return the `DrillDownResponse` from `detail` — **extract this construction into a small shared helper** (e.g. `_provenance_detail_to_drill_down_response(assignment, detail)`) reused by both `get_drill_down_service` and this new function, instead of duplicating the ~15-line `DrillDownResponse(...)` call. This is a pure refactor of existing code with zero behavior change — verify `get_drill_down_service`'s existing tests still pass unmodified after extracting it.
  - [x] Subtask 4.2: Add the route to `assignments/router.py` (**not** `progress/router.py` — same reasoning as the drill-down route, `assignments/router.py:94-97`, to avoid `progress/router.py`'s already-documented double-prefix bug):
    ```python
    @router.post("/{assignment_id}/override", response_model=DrillDownResponse)
    async def set_override_route(
        assignment_id: UUID,
        request: SetOverrideRequest,
        current_user: CurrentUser = Depends(get_current_user),
        session: AsyncSession = Depends(get_db),
    ) -> DrillDownResponse:
        return await set_override_service(session, current_user=current_user, assignment_id=assignment_id, request=request)
    ```

- [x] Task 5: Frontend — API client (AC: 3, 6; `frontend/src/lib/api/dashboardApi.ts`, matching `getDrillDown`'s placement precedent — both are `/api/assignments/...` backend routes consumed by the dashboard feature)
  - [x] Subtask 5.1: Add `setOverride(assignmentId: string, action: "set" | "unset", reason?: string): Promise<DrillDownResponse>` — `apiClient.post<DrillDownResponse>(\`/api/assignments/${assignmentId}/override\`, { action, reason })`.

- [x] Task 6: Frontend — enable `[Mark as Ready]` + confirmation flow (AC: 1, 2, 3, 4; `ProvenanceDrillDownModal.tsx`, Finding 3, Finding 4)
  - [x] Subtask 6.1: Add local state: `const [confirming, setConfirming] = useState(false)`, `const [reason, setReason] = useState("")`, `const [submitting, setSubmitting] = useState(false)`, `const [submitError, setSubmitError] = useState<string | null>(null)`. Reset all four in `fetchDetail`'s effect when `assignmentId`/`open` changes (mirror the existing `setData(null)` reset at line 46, so a re-opened modal for a different assignment doesn't leak stale confirm-view state).
  - [x] Subtask 6.2: Replace the disabled `[Mark as Ready]` button (lines 121-128) with: rendered only `{data.provenance !== "HR Override" && (...)}`, `disabled` removed, `onClick={() => setConfirming(true)}`.
  - [x] Subtask 6.3: Leave the `[Reverse Override]` button (lines 129-136) untouched — Finding 4, Story 5.5b's scope.
  - [x] Subtask 6.4: When `confirming` is true, render a confirmation view **in place of** the detail view (same `Dialog`, same pattern `AssignmentModal.tsx` already uses to switch between Step 1/2/3 within one Dialog instance — do not open a second/nested `Dialog`, which isn't designed for stacking two focus-traps/backdrops at once):
    - Heading: `Mark {data.employee_name} as Ready for {data.skill_name}?`
    - A `<textarea>` labelled "Reason (optional)" bound to `reason`
    - `[Cancel]`: `setConfirming(false); setReason(""); setSubmitError(null)` — no API call, per AC2's Cancel semantics (mirrors `AssignmentModal`'s `handleClose` no-side-effect convention).
    - `[Confirm]`: `setSubmitting(true)`, call `dashboardApi.setOverride(assignmentId, "set", reason.trim() || undefined)`, on success `setData(response)`, `setConfirming(false)`, `setReason("")`, call `onOverrideChanged?.(<success message>)` (Task 7); on failure `setSubmitError(...)`, stay in the confirm view (don't lose the typed reason).
  - [x] Subtask 6.5 (Finding 3, **corrected during implementation** — see Debug Log): the literal `??` swap suggested by Finding 3 was verified incorrect (it doesn't catch an empty-string `override_reason`, the exact case Finding 3 was trying to protect against). Implemented `{data.override_reason?.trim() || "No reason provided"}` instead, which correctly falls back for `null`, `""`, and whitespace-only values.

- [x] Task 7: Frontend — dashboard refresh + success toast (AC: 4; `DashboardPage.tsx`)
  - [x] Subtask 7.1: Add `const [toastMessage, setToastMessage] = useState<string | null>(null)` and render `<Toast message={toastMessage} onDismiss={() => setToastMessage(null)} />` (reuse the existing `components/ui/toast.tsx` primitive verbatim — Story 3.5 already established this pattern for assignment-creation success; do not build a second toast mechanism).
  - [x] Subtask 7.2: Add `onOverrideChanged={(message) => { setToastMessage(message); fetchDashboard(); }}` prop to the `<ProvenanceDrillDownModal>` element (line 331). Reusing `fetchDashboard()` (not the silent `pollDashboard()`) is correct here — this is a direct result of the HR Admin's own action in the same tab, not a background poll tick, so the brief loading-skeleton flash Finding 1 of Story 5.4 forbade for *polling* is fine and expected here (matches how `fetchDashboard` is already used after page-change).
  - [x] Subtask 7.3: `ProvenanceDrillDownModal`'s success message text: `"{employee_name} marked as Ready for {skill_name}."` — plain, declarative, matches this codebase's existing toast-copy tone (`Toast.tsx`'s only other consumer, Story 3.5's assignment-creation toast).

- [x] Task 8: Backend tests (`backend/tests/test_override_endpoint.py`, new file, mirrors `test_drill_down_endpoint.py`'s `_client`/`_login`/seed-constant/cleanup pattern exactly — real app + `ASGITransport` + real Postgres)
  - [x] Subtask 8.1: HR Admin sets an override on their own assignment → 200; response `provenance == "HR Override"`, `status == "COMPLETED"`, `underlying_provenance` populated (not null) even on a brand-new no-progress assignment (underlying = "Not Started").
  - [x] Subtask 8.2: A subsequent `GET /progress/drill-down` for the same assignment returns byte-identical `provenance`/`status`/override fields to the POST response (AR-3 cross-surface invariant, mirrors the existing `test_dashboard_grid_and_drill_down_agree_on_status_and_provenance_for_the_same_assignment` test's spirit).
  - [x] Subtask 8.3: `GET /api/dashboard` row for the same assignment shows `status == "Completed"`, `provenance == "HR Override"` immediately after the override, no polling wait (AC4; Finding 1 — proves the existing read path needed zero changes).
  - [x] Subtask 8.4: EMPLOYEE role → 403 `FORBIDDEN_NOT_HR_ADMIN` (both `action: 'set'` and `action: 'unset'`).
  - [x] Subtask 8.5: Non-owning HR Admin (different `assigned_by`) → 403, same uniform response as `test_non_owning_hr_admin_gets_403_not_a_leak`.
  - [x] Subtask 8.6: `action: 'unset'` with no active override → 404 `NO_ACTIVE_OVERRIDE` (AC10).
  - [x] Subtask 8.7: `action: 'set'` twice in a row (re-marking) → exactly one active `assignment_overrides` row afterward (query the table directly), the first row has `active=False`/`reversed_at`/`reversed_by` populated (AC9).
  - [x] Subtask 8.8: `reason: "   "` (whitespace-only) → stored/returned as `None`/no override_reason shown as blank (AC8, Finding 3). `reason: "  Verified in call  "` → trimmed to `"Verified in call"`.
  - [x] Subtask 8.9: A fresh `skill_progress` write arriving *after* an override still shows both override + underlying signal in a following drill-down GET (AC5 — should pass with zero new derivation code, since this is `get_provenance_detail`'s existing behavior; this test is regression insurance, not new logic).
  - [x] Subtask 8.10: Unauthenticated request → 401.

- [x] Task 9: Frontend tests (extend `ProvenanceDrillDownModal.test.tsx`)
  - [x] Subtask 9.1: `[Mark as Ready]` renders and is enabled when `provenance !== "HR Override"`; is absent entirely when `provenance === "HR Override"` (Finding 4).
  - [x] Subtask 9.2: Click `[Mark as Ready]` → confirm view renders with the exact employee/skill names and a Reason textarea.
  - [x] Subtask 9.3: `[Cancel]` in the confirm view → returns to the detail view, no API call made (assert the mock `setOverride` was never called).
  - [x] Subtask 9.4: `[Confirm]` → calls `dashboardApi.setOverride` with the trimmed reason (or `undefined` for an empty/whitespace-only reason), updates `data` from the response, closes the confirm view, and calls `onOverrideChanged` with the expected message string.
  - [x] Subtask 9.5: `[Confirm]` failure (rejected promise) → shows an error, stays in the confirm view, reason input is not cleared.
  - [x] Subtask 9.6: `override_reason: ""` (defensive case) renders "No reason provided", not a blank line (Finding 3, the corrected `.trim() || fallback` fix).
  - [x] Subtask 9.7 (`DashboardPage.test.tsx` or a small new test): `onOverrideChanged` triggers both a `Toast` render with the passed message and a `dashboardApi.getDashboard` re-fetch call.

- [x] Task 10: Full regression pass
  - [x] Subtask 10.1: Backend — run the new file plus `test_drill_down_endpoint.py`, `test_dashboard_router.py`, `test_provenance_detail.py` (files sharing import surface) in isolation per-file (known pre-existing cross-file asyncpg pool-corruption pattern, `deferred-work.md`, unfixed since Epic 4 — do not attempt to fix it in this story).
  - [x] Subtask 10.2: Frontend — `npm run test` full suite; `tsc --noEmit` diffed via `git stash` against baseline (matches Story 5.2/5.4's established verification method) — assert **zero new** type errors, not a clean full-build pass (pre-existing unrelated errors are documented in `deferred-work.md`, Story 2.6 entry).
  - [x] Subtask 10.3: Update Dev Agent Record + File List (below) with actual results.

---

## Developer Context & Implementation Notes

### Why the endpoint handles both `set` and `unset` now, even though 5.5b is `backlog`

AR-4 describes "Set/reverse flows through a `progress/` write method (a second validated write path alongside AD-5)" as **one** mechanism, not two. Table 7 (`assignment_overrides`) is captioned "Story 5.5 - HR Override Data Model" and includes `reversed_at`/`reversed_by` — fields only the `unset` path populates. Building only `set` now and bolting `unset` on in 5.5b would mean re-opening this same router/service/repository trio for no design reason, and `deferred-work.md`'s Story 5-2 note already anchors the `reason` validation fix to *"Story 5.5's override-creation validation."* Precedent: Story 3.4/3.6 split a shared mechanism (`handleClose()`) the same way — built once, a later story added dedicated test coverage and UI polish for one branch of it.

### `progress/service.py::set_override` — sketch

```python
@staticmethod
async def set_override(
    session: AsyncSession,
    *,
    assignment: Assignment,
    current_user: CurrentUser,
    action: Literal["set", "unset"],
    reason: str | None,
    video_duration: int | None,
) -> ProvenanceDetail:
    hr_admin_id = UUID(current_user.user_id)  # same pattern as get_resume_position's UUID(current_user.user_id)
    active_override = await ProgressRepository.get_active_override_for_assignment(session, assignment.id)

    if action == "unset":
        if active_override is None:
            raise AppException(status.HTTP_404_NOT_FOUND, error_code="NO_ACTIVE_OVERRIDE",
                                message="No active override exists to reverse")
        await ProgressRepository.deactivate_override(session, active_override, reversed_by=hr_admin_id)
        new_override = None
    else:  # "set"
        if active_override is not None:
            await ProgressRepository.deactivate_override(session, active_override, reversed_by=hr_admin_id)  # AC9
        trimmed_reason = reason.strip() or None if reason else None
        new_override = await ProgressRepository.create_override(
            session, assignment_id=assignment.id, set_by=hr_admin_id, reason=trimmed_reason
        )

    progress = await ProgressRepository.get_progress_for_assignment(session, assignment.id)
    await session.commit()
    return ProgressService.get_provenance_detail(assignment, progress, new_override, video_duration)
```

Note `new_override` must have `set_by_user` populated for `get_provenance_detail`'s `override.set_by_user.name` access (`progress/service.py:439`) — either eager-load it after `create_override`'s `flush()` (a cheap follow-up `refresh(new_override, ["set_by_user"])`) or accept that the HR Admin's own name is already known from `current_user` and skip the relationship load entirely for the immediate response. Prefer the latter if it avoids an extra query — but verify `get_provenance_detail` doesn't crash on a lazy-load attempt in an async context (SQLAlchemy's `MissingGreenlet` error, the exact bug Story 2.5 hit and fixed — see that story's Dev Agent Record) before shipping either approach untested.

### Frontend confirm-view sketch (`ProvenanceDrillDownModal.tsx`, replacing lines 119-144)

```tsx
{confirming ? (
  <div className="space-y-4">
    <h2 id={titleId} className="text-lg font-bold text-gray-900">
      Mark {data.employee_name} as Ready for {data.skill_name}?
    </h2>
    <label className="block text-sm text-gray-700">
      Reason (optional)
      <textarea
        value={reason}
        onChange={(e) => setReason(e.target.value)}
        className="mt-1 w-full rounded border border-gray-200 p-2 text-sm"
        rows={3}
      />
    </label>
    {submitError && <p className="text-red-600 text-sm">{submitError}</p>}
    <div className="flex items-center justify-end gap-2 pt-2 border-t border-gray-100">
      <button disabled={submitting} onClick={() => { setConfirming(false); setReason(""); setSubmitError(null); }}
              className="text-sm font-medium text-gray-600 hover:underline">
        Cancel
      </button>
      <button disabled={submitting} onClick={handleConfirmOverride}
              className="bg-blue-600 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50">
        Confirm
      </button>
    </div>
  </div>
) : (
  /* existing detail view, unchanged except Mark as Ready per Subtask 6.2 */
)}
```

Keep this inside the same `!loading && !error && data` render branch — do not add a fifth top-level branch to the component; `confirming` is a sub-state of the already-loaded view.

---

## Testing Strategy

**Backend:** integration-only (no unit test file for `set_override` in isolation) — matches the established precedent for `get_drill_down_service`/`create_assignment_service` (Story 3.4/5.2 never got a separate service-unit-test file; the real-DB integration test *is* the test). Real Postgres + `ASGITransport`, `_login()`/seed constants (`CASEY_ID`, `SKILL_DATA_VIZ_ID` from `core/seed_ids.py`/`core/seeds.py`) copied from `test_drill_down_endpoint.py`'s own preamble verbatim.

**Frontend:** extend `ProvenanceDrillDownModal.test.tsx` (already has an established `dashboardApi` mock + `data` fixture pattern per its existing test cases) — do not create a second test file for this modal, following the same "one file per component, add cases" convention `DashboardRow.test.tsx` used for Story 5.4's new column.

Do **not** add any test asserting `[Reverse Override]` becomes enabled or its confirmation flow — that's Story 5.5b's test surface, not this story's.

---

## Architecture Compliance Checklist

- **AD-1 (single-owner data modules):** `assignment_overrides` writes live only in `ProgressRepository` (Task 1); `assignments/service.py` calls `ProgressService.set_override()`, never `ProgressRepository` directly for this new mutation (Finding 5).
- **AD-4 (HR Override is a separate, coexisting record):** `create_override`/`deactivate_override` never touch `skill_progress` (AC3); `get_provenance_detail` already preserves the underlying signal through an active override (AC4/AC5, zero new code needed for this half).
- **AD-6 (server-side role/identity gate):** `require_hr_admin` + `get_assignment_scoped_to_hr_admin` hard-scope every call (AC7); no client-supplied `set_by`/`assignment.employee_id` is ever trusted, matching `record_watch_progress`'s "identity from the session, never the request body" rule (AD-5's sibling rule, same spirit).
- **AR-3 (single derivation authority):** the POST response is built from the same `get_provenance_detail()` call the GET drill-down and dashboard grid use — verified directly by Subtask 8.2's cross-surface test, not assumed.
- **No new backend table/migration:** `assignment_overrides` already exists (Finding 1) — if you find yourself writing an Alembic revision for this story, stop, you've misread the scope.

---

## Known Issues & Deferrals

- **Story 5.5b (backlog) still owns:** `[Reverse Override]`'s conditional visibility/enabling, its own confirmation modal, its own success toast copy ("Override removed. Status now based on video progress."), and the race-condition test between a reversal and a concurrent fresh watch-progress write (epics.md:1899-1909). This story's `unset` action must be **correct** (Task 8.6/8.7 test it) but has no UI trigger yet.
- **`get_drill_down_service`'s pre-existing direct `ProgressRepository` reads** (Finding 5) are not refactored by this story — only the new write path avoids extending that pattern. Fixing the existing read-side gap is still tracked in `deferred-work.md` (Story 5-1 review), unchanged by this story.
- **Backend transaction/snapshot race** (`dashboard/service.py`, `deferred-work.md`, Story 5-1/5-2/5-4 reviews all name it, still open) — this story's own write (`session.commit()` inside `set_override`) is a normal single-row write, not a new instance of that read-side race; do not conflate the two or feel obligated to fix the pre-existing item here.
- **`conftest.py` cross-file asyncpg pool corruption** (open since Epic 4 retro action item) — run new/touched test files in isolation per Subtask 10.1, same as every recent story.

---

## Success Criteria

1. `POST /api/assignments/{assignment_id}/override` exists (in `assignments/router.py`, not `progress/router.py`), handles both `action: 'set'` and `action: 'unset'`, returns the same `DrillDownResponse` shape as the existing GET drill-down endpoint.
2. HR Admin can mark an Assignment Ready from the drill-down modal; the dashboard grid and a subsequent drill-down GET both immediately show Status=Completed, Provenance=HR Override, with the underlying signal still visible (AC4/AC5) — zero changes to `dashboard/service.py`/`dashboard/router.py`/`dashboard/repository.py` (Finding 1).
3. `[Reverse Override]` remains exactly as disabled/stubbed as it is today — untouched by this story (Finding 4).
4. At most one active `assignment_overrides` row per assignment at all times (AC9); `unset` with nothing active is a clean 404, not a silent no-op (AC10).
5. `reason` is trimmed server-side, empty/whitespace becomes `NULL`, and the frontend's blank-reason fallback uses `??` not `||` (Finding 3, closes the `deferred-work.md` item).
6. Zero new type errors (`tsc --noEmit` diff); all new backend/frontend tests pass; pre-existing unrelated failures unchanged in count.

---

## Dev Notes

### Project Structure Notes

- Backend files expected to change: `backend/app/progress/repository.py` (new `create_override`/`deactivate_override`), `backend/app/progress/service.py` (new `set_override`), `backend/app/assignments/schemas.py` (new `SetOverrideRequest`), `backend/app/assignments/service.py` (new `set_override_service` + extracted `_provenance_detail_to_drill_down_response` helper), `backend/app/assignments/router.py` (new route).
- New backend test file: `backend/tests/test_override_endpoint.py`.
- No Alembic migration (table exists). No changes to `backend/app/dashboard/*` (Finding 1). No changes to `backend/app/progress/router.py`, `backend/app/progress/models.py`, or `backend/app/progress/schemas.py`.
- Frontend files expected to change: `frontend/src/lib/api/dashboardApi.ts` (new `setOverride`), `frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx` (confirm flow, `[Mark as Ready]` enabled, `??` fix), `frontend/src/features/dashboard/DashboardPage.tsx` (`Toast` + `onOverrideChanged` wiring).
- `ProvenanceDrillDownModal.test.tsx` gets new cases; no new frontend test file.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.5] (lines 1791-1828) — full AC text this story implements
- [Source: _bmad-output/planning-artifacts/epics.md] — FR-12 (line 61), AR-4 (line 116), Table 7 `assignment_overrides` (lines 520-533), Epic 5 binds list (line 1603), Story 5.2's "Actions:" mutual-exclusivity spec (lines 1713-1717), Story 5.5b's full AC (lines 1830-1941, out of scope but the `unset` contract must satisfy it)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md] — AD-1 (line 41-45), AD-3 (53-57), AD-4 (59-63), AD-6 (71-75), paradigm table (line 31: `progress/` owns `assignment_overrides`)
- [Source: backend/app/assignments/models.py:122-143] — existing `AssignmentOverride` model, all fields this story's repository methods populate
- [Source: backend/alembic/versions/001_initial_schema.py:128-146] — confirms the table already exists, no migration needed
- [Source: backend/app/progress/repository.py:289-373] — existing `get_active_override_for_assignment`/`get_active_overrides_for_assignments` to reuse, and the file/module this story's two new methods belong in
- [Source: backend/app/progress/service.py:47,356-445] — `PROVENANCE_HR_OVERRIDE` constant and `get_provenance_detail()`, the single derivation authority this story's mutation must feed into, not duplicate (Finding 1)
- [Source: backend/app/assignments/schemas.py:28-46,181] — `ProvenanceLabel`'s stale docstring (Finding 2) and `DrillDownResponse`'s existing `Literal["...", "HR Override"]` contract, reused as-is
- [Source: backend/app/assignments/service.py:139-179] — `get_drill_down_service`, the pattern to copy for scoping/403s (Task 4) and the pre-existing AD-1 boundary gap not to extend (Finding 5)
- [Source: backend/app/assignments/router.py:85-98] — `get_drill_down_route`'s doc-comment explaining why this router (not `progress/router.py`) is the correct home for the new route
- [Source: backend/tests/test_drill_down_endpoint.py] — exact test scaffolding (`_client`, `_login`, seed constants, cleanup helpers) to copy for the new test file
- [Source: frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx:119-149,177] — the two disabled stub buttons this story changes (only the first one), and the `||`/`??` bug site
- [Source: frontend/src/features/assignments/AssignmentModal.tsx] — the single-Dialog, multi-step-switch pattern to mirror for the confirm view (not a nested/stacked `Dialog`)
- [Source: frontend/src/components/ui/toast.tsx] — existing hand-rolled `Toast` primitive to reuse verbatim (Story 3.5 precedent), not rebuild
- [Source: frontend/src/features/dashboard/DashboardPage.tsx:70-84,331-335] — where the `Toast`/`onOverrideChanged` wiring attaches; existing `fetchDashboard`/`ProvenanceDrillDownModal` render site
- [Source: _bmad-output/implementation-artifacts/deferred-work.md] — Story 5-2 review's `||`/`??` reason-display item (explicitly anchored to "Story 5.5's override-creation validation"), Story 5-1 review's AD-1 boundary-gap item (Finding 5), the open cross-file pool-corruption item (Task 10)
- [Source: _bmad-output/implementation-artifacts/5-2-provenance-drill-down-modal-trust-detail-and-raw-data.md] — this story's direct predecessor; built everything Finding 1 relies on
- [Source: _bmad-output/implementation-artifacts/5-4-dashboard-auto-update-live-row-refresh-on-watch-progress.md] — `fetchDashboard`/`requestId` pattern this story reuses as-is (Subtask 7.2), not `pollDashboard`
- [Source: _bmad-output/project-context.md] — Epic 5 architecture-spine summary; confirms `progress/` is the sole derivation/mutation authority for Status/Provenance/override this story must route through, never bypass

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (claude-sonnet-5)

### Debug Log References

- **Finding 3's literal `??` suggestion was verified incorrect during implementation, not applied as-is (Subtask 6.5).** `||` and `??` only differ in how they treat an empty string `""`: `||` falls back for `""` (falsy), `??` does not (not nullish). Since Finding 3's stated goal was "defense in depth, in case a pre-existing row somehow has a blank string," swapping to `??` would have been a regression for that exact case (a blank `override_reason: ""` would render as a blank line under `??`, not the intended fallback). Verified by direct reasoning through both operators' semantics for a `string | null` field before shipping. Implemented `{data.override_reason?.trim() || "No reason provided"}` instead — correctly falls back for `null`, `""`, and whitespace-only values, and also trims real reasons for display. Added a dedicated test (`Finding 3: a defensive blank-string override_reason still shows 'No reason provided'`) proving this, since the original suggestion would have passed with `??` too shallowly (no test would have caught the empty-string gap if `??` had been used naively without checking the case that mattered).
- **Backend `set_override`'s `new_override` relationship-loading, decided per the story's own flagged open question:** rather than `session.refresh(new_override, ["set_by_user"])` (an unverified async-relationship-refresh pattern), re-fetched the just-created override via the already-tested `get_active_override_for_assignment` (which eager-loads `set_by_user` via `joinedload`) — reuses a known-correct code path instead of introducing a new one, per the story's own "verify before shipping" guidance (Story 2.5's `MissingGreenlet` precedent).
- **Full backend suite run (`pytest tests/`, excluding two pre-existing collection-broken files `test_dashboard.py`/`test_progress_retrieval_endpoint.py`, both already documented in project-context.md as stale-import gaps unrelated to this story): 278 passed / 60 failed / 10 errors on the first combined run.** Investigated rather than assumed: every failure/error traces to the already-documented cross-file asyncpg pool-corruption pattern (open since the Epic 4 retro action item) — confirmed by re-running the touched-surface files individually: `test_override_endpoint.py` (12/12), `test_drill_down_endpoint.py` + `test_provenance_detail.py` (19/19 combined), `test_assignments_router.py` (12/12), `test_assignment_cancel_no_orphan.py` (1/1) all pass 100% in isolation. `test_dashboard_router.py`'s 5 failures were verified via `git stash` to be byte-identical against the pristine baseline (a stale `/api/dashboard/assignments` 404, unrelated to this story). `test_protected_router_gate.py`'s 2 `assignments_router`/`dashboard_router` failures were likewise verified identical on baseline (a pre-existing router-construction-shape test, unrelated to adding a new route to an already-non-conforming router).
- **Frontend `tsc --noEmit` diffed via `git stash`:** baseline = 85 lines, first post-implementation pass = 86 lines (one genuinely new instance of the pre-existing `TS2741: Property 'onNewAssignment' is missing` error class, from my new `DashboardPage.test.tsx` test calling `<DashboardPage />` without the prop, matching every other test in that file). Fixed by passing `onNewAssignment={() => {}}` in the new test (harmless, makes the test itself more correct) rather than leaving the count elevated — re-diffed after the fix: 85 vs 85, and every line-diff confirmed to be a pure line-number shift of the same two pre-existing error codes (`TS2322`, `TS2741`), zero new error classes.
- **Frontend full suite:** 211 passed / 2 failed out of 213 (both pre-existing and unrelated: `renders loading state on mount`, `pagination shows correct page numbers and total`, both already documented since Story 5.4). Verified via `git stash` against baseline: identical 2 failures on 10 tests in `DashboardPage.test.tsx` pre-story vs. the same 2 failures on 11 tests post-story (my new test passes).
- `npx vite build` succeeds cleanly (practical build-verification proxy, matching Story 2.5/5.2/5.4's established precedent for this project's `tsc`-gated `npm run build` having pre-existing unrelated failures).

### Completion Notes List

- All 10 tasks complete. Backend: `ProgressRepository.create_override`/`deactivate_override` (progress/repository.py), `ProgressService.set_override` (progress/service.py, owns the mutation per AD-1/Finding 5), `SetOverrideRequest` schema (assignments/schemas.py), `set_override_service` + extracted `_provenance_detail_to_drill_down_response` shared helper (assignments/service.py), new `POST /api/assignments/{assignment_id}/override` route (assignments/router.py, not progress/router.py, per Finding 2/double-prefix precedent). Frontend: `dashboardApi.setOverride` client method, `ProvenanceDrillDownModal.tsx`'s Mark-as-Ready confirm flow (enabled/hidden per Finding 4, single-Dialog step-switch pattern per `AssignmentModal.tsx` precedent, `[Reverse Override]` left untouched), `DashboardPage.tsx`'s `Toast` + `onOverrideChanged` wiring.
- **Zero changes to `dashboard/service.py`/`dashboard/router.py`/`dashboard/repository.py`** — confirmed via `git status` and by the dashboard-grid-reflects-override test passing without any dashboard-module code change (Finding 1 verified true, not just assumed).
- **Finding 2 followed as specified:** no `ProvenanceLabel.HR_OVERRIDE` enum member was added; the stale docstring in `assignments/schemas.py` was left untouched (harmless staleness per the story's own guidance).
- **Finding 3 partially deviated from as written** (see Debug Log) — the underlying goal (a whitespace-only or blank reason never renders as a blank line) is satisfied, but via `.trim() || fallback` rather than the literally-suggested `??`, which would not have achieved that goal.
- **AC9's at-most-one-active-override invariant verified directly**, not just implemented: `test_re_marking_ready_leaves_exactly_one_active_override_row` queries `assignment_overrides` directly and asserts exactly one active + one inactive (with `reversed_at`/`reversed_by` populated) row after two consecutive `set` calls.
- **AC10 verified as a real 404, not a no-op:** `test_unset_with_no_active_override_returns_404` plus a second assertion inside `test_set_then_unset_deactivates_and_reverts_to_underlying_signal` (a second `unset` after the first succeeds must also 404).
- Test counts: backend `test_override_endpoint.py` 12/12 new, `test_drill_down_endpoint.py`/`test_provenance_detail.py` 19/19 unchanged (proves the extracted helper is behavior-preserving); frontend `ProvenanceDrillDownModal.test.tsx` 22/22 (3 pre-existing placeholder tests rewritten to match real Mark-as-Ready behavior, 7 new), `DashboardPage.test.tsx` 9/10 new-count passing (1 new test added, 2 pre-existing unrelated failures unchanged). Full frontend suite 211/213 passing. `tsc --noEmit` diff shows zero new error classes. `npx vite build` clean.

### File List

**Backend (modified):**
- `backend/app/progress/repository.py` — added `create_override`, `deactivate_override`
- `backend/app/progress/service.py` — added `set_override`; added `AppException` import
- `backend/app/assignments/schemas.py` — added `SetOverrideRequest`
- `backend/app/assignments/service.py` — added `set_override_service`; extracted `_provenance_detail_to_drill_down_response` (used by both `get_drill_down_service` and `set_override_service`); added `Assignment`, `SetOverrideRequest`, `ProvenanceDetail` imports
- `backend/app/assignments/router.py` — added `POST /{assignment_id}/override` route; added `SetOverrideRequest`, `set_override_service` imports

**Backend (new):**
- `backend/tests/test_override_endpoint.py` — 12 new integration tests

**Frontend (modified):**
- `frontend/src/lib/api/dashboardApi.ts` — added `setOverride`
- `frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx` — added `onOverrideChanged` prop, Mark-as-Ready confirm-view state/flow, enabled/conditional `[Mark as Ready]` button, `.trim() || fallback` reason-display fix
- `frontend/src/features/dashboard/ProvenanceDrillDownModal.test.tsx` — 3 stale placeholder tests rewritten, 7 new tests added, `setOverride` added to the mock
- `frontend/src/features/dashboard/DashboardPage.tsx` — added `Toast` import/state, `toastElement` rendered in all 4 branches, `onOverrideChanged` wiring on `ProvenanceDrillDownModal`
- `frontend/src/features/dashboard/DashboardPage.test.tsx` — added `getDrillDown`/`setOverride` to the mock, 1 new test

**Docs/tracking:**
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — status transitions (`ready-for-dev` → `in-progress` → `review`) and dated log entries
- `_bmad-output/project-context.md` — story-creation entry (prior session) plus this implementation-completion entry, per the project's mandatory Project Context Maintenance rule

## Change Log

| Date | Change |
|------|--------|
| 2026-07-12 | Story created via bmad-create-story. Scoped as a shared set/unset backend endpoint (owned by `progress/` per AD-1) plus a frontend Mark-as-Ready confirm flow only — `[Reverse Override]`'s UI is explicitly left to Story 5.5b. Read side (dashboard grid, drill-down modal) requires zero changes, already built by Story 5.2. |
| 2026-07-12 | Implemented all 10 tasks (bmad-dev-story). Backend: `POST /api/assignments/{assignment_id}/override` (set/unset actions), `ProgressService.set_override` (AD-1/Finding 5 compliant), `ProgressRepository.create_override`/`deactivate_override`, `SetOverrideRequest` schema, shared `_provenance_detail_to_drill_down_response` helper extracted from `get_drill_down_service`. Frontend: `dashboardApi.setOverride`, `ProvenanceDrillDownModal.tsx`'s Mark-as-Ready confirm flow (single-Dialog step-switch, `[Reverse Override]` untouched per Finding 4), `DashboardPage.tsx`'s `Toast`/refresh wiring. Corrected Finding 3's literal `??` suggestion during implementation (verified incorrect for the empty-string case; used `.trim() || fallback` instead — see Debug Log). 12 new backend tests (`test_override_endpoint.py`, 12/12 passing), 3 stale placeholder frontend tests rewritten + 7 new added to `ProvenanceDrillDownModal.test.tsx` (22/22), 1 new test in `DashboardPage.test.tsx`. Full regression: backend touched-surface files pass 100% in isolation (pre-existing cross-file pool-corruption pattern confirmed unrelated via `git stash`); frontend 211/213 passing (2 pre-existing unrelated failures, unchanged), `tsc --noEmit` diff shows zero new error classes, `vite build` clean. Zero changes to `dashboard/service.py`/`dashboard/router.py`/`dashboard/repository.py` (Finding 1 confirmed true). Status → review. |
