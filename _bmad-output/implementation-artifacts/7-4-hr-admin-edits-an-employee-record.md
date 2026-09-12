---
baseline_commit: 1c8f45b7da343ec4b4eaefe483753526d6f9f396
---

# Story 7.4: HR Admin Edits an Employee Record

Status: done

## Story

As an **HR Admin**,
I want to edit an Employee's profile fields,
So that I can keep the roster accurate as people change roles, teams, or contact details (FR-26).

## Scope Notes (read before starting)

1. **No PATCH/PUT route exists anywhere in this codebase to mirror exactly.** `employees/router.py` currently has only `GET ""` (Story 7.3) and `POST ""` (Story 7.2). `skills/router.py` has no edit route at all (Skills are identity-locked once assigned, FR-21/22 — the opposite of this story's "no lock" requirement). This story is greenfield on route naming: `PATCH /api/admin/employees/{employee_id}`, mounted on the already-existing `employees_router` (no new `main.py` mount needed). The request body is a **full replace of every editable field** (not JSON-merge-patch partial semantics) — the Edit panel always loads and submits the complete field set, so there is no "field omitted vs. field cleared to null" ambiguity to design around.

2. **`employee_code` is immutable — reject it structurally, don't just ignore it.** `UpdateEmployeeRequest` (new schema) must **not** include `employee_code` as a field at all, and must set `model_config = ConfigDict(extra="forbid")` (matching `CreateEmployeeRequest`) so a client that mistakenly sends `employee_code` gets a clean `422`, not a silently-dropped value. Read [Source: backend/app/employees/schemas.py] before writing this — `CreateEmployeeRequest`'s exact field list/validators (`_reject_blank` on `name`, `max_length` per column) is the template; `UpdateEmployeeRequest` is that same shape minus `employee_code`.

3. **`EmployeeResponse` needs no changes.** It already carries every field (including `updated_at`, which auto-bumps via the model's existing `onupdate=func.now()` — Story 7.1) the edit response needs. Reuse it as-is for `PATCH`'s `response_model`, exactly like Story 7.2's docstring in `schemas.py` already anticipated ("Story 7.3 (view/list), 7.4 (edit), and 7.6 (regenerate password) extend this file").

4. **Email-edit must reuse Story 7.2's exact dual-table conflict-check shape, extended with a self-exclusion.** [Source: backend/app/employees/service.py::create_employee_service] checks `employees` (case-insensitive, active+archived) then, in the `IntegrityError` backstop, `accounts` too — because `employees/repository.py::create_employee_with_account` (Story 7.1/AR-24) keeps `Account.id == Employee.id` and `Account.email` in sync with `Employee.email` at creation time. This story is the first to ever change an existing Employee's email after creation, so it must **also update `Account.email`** to keep the two tables from drifting (Story 7.2's own code-review comment explicitly named this exact future story: *"a future Employee-edit story letting the two tables' emails drift apart, FR-26's own `[ASSUMPTION]`"*). No `update_account_email`-shaped function exists yet in `auth/repository.py` — add one, following `create_account`'s established pattern (Story 7.2 code review: centralize the write in `auth/`, called from `employees/service.py`, per the AD-1-exception reasoning already documented on `create_employee_with_account`). Every conflict check in this story (pre-check AND the `IntegrityError` backstop) must **exclude the Employee's own row/Account** from the collision, or editing an Employee without changing their email would spuriously 409 against themselves.

5. **Login is unaffected by an email edit — do not imply otherwise in tests or UI copy.** `auth/service.py::authenticate()` still reads only `_MOCK_ACCOUNTS` (a hardcoded plaintext dict), never the real `Account` table — this gap predates this story and is out of scope to fix here (flagged in Story 7.1/7.3's carried-forward notes). Updating `Account.email` keeps the two tables consistent for whenever a future story wires `authenticate()` to read `Account` for real, but has **no observable effect on login today**. PRD FR-26's own `[ASSUMPTION]` ("an existing session is not silently invalidated by an Email edit") is trivially true right now for the wrong reason (nothing reads the edited value yet) — don't write a test that claims to verify session behavior post-email-edit; there is nothing real to verify.

6. **No lock, unlike Skills.** The AC's "regardless of the Employee's Assignment history" is satisfied by construction — the update service never queries `assignments`/`assignment_overrides` at all (unlike `skills/service.py::update_skill_service`'s explicit `ever_assigned` lock check, FR-21/22). Do not add an assignment-history check "for safety" — that would be inventing a requirement the AC explicitly rules out.

7. **Concurrent edits: last-write-wins, no optimistic lock.** Matches this PRD's existing no-optimistic-locking precedent everywhere else (explicit `[ASSUMPTION]` in both `epics.md` Story 7.4 and PRD FR-26). Do not add a version column, `If-Match` header, or timestamp-conflict check — none is in scope.

8. **Frontend: reuse `NewSkillModal.tsx` + `Dialog`/`Label`/`Input`/`FormErrorText`, not a new pattern.** [Source: frontend/src/features/admin/NewSkillModal.tsx] is the concrete, working analog for the new `EditEmployeeModal.tsx`: same `Dialog` primitive (focus trap, Escape/backdrop-close, `aria-modal`), same `requestIdRef` staleness guard invalidating in-flight requests across open/close transitions, same `conflictErr.response?.status === 409` branching idiom, same `extractErrorMessage()` helper (already duplicated per-page/modal in this codebase — not a new pattern to introduce). Read that file in full before starting.

9. **List-refresh: reuse `EmployeesPage.tsx`'s existing `refetch()`.** No React Query or other cache-invalidation library exists anywhere in this codebase (confirmed in Story 7.3). The path of least resistance and most consistent with precedent is: on a successful save, call the page's already-wired `refetch()` (full re-fetch of the roster) and close the modal. This satisfies "the roster reflects the change without a full page reload" (AC3) — a re-fetch is not a page reload.

10. **Only the Edit row/card action button changes behavior.** [Source: frontend/src/pages/hr/EmployeesPage.tsx::RowActions] currently wires all three action buttons (Edit, Regenerate Password, Delete/Archive) to one shared `onUnavailable` toast stub. This story replaces **only** the Edit button's handler with one that opens `EditEmployeeModal` for that row's Employee — Regenerate Password and Delete/Archive stay wired to the stub exactly as-is (Stories 7.6/7.5's scope, not this one). Don't touch their `aria-label`s or markup beyond wiring the one new handler through.

11. **UX prototype's Edit modal is a 3-field simplified mock — do not under-scope to match it.** `_bmad-output/E-Development/05-Ritas-Roster-Management-Prototype/05.1-Employees-Tab.html`'s `#edit-employee-modal` only has Name/Position/Department inputs. The markdown UX spec (`05.1-employees-roster.md`'s `edit-employee-fields` row) is authoritative and lists the full 10-field editable set (Name, Email, Phone, Experience, Technologies, Position, Project, Manager Name, Location, Department) — build all 10, not the prototype's 3.

## Acceptance Criteria

**AC1 — Edit panel loads with ID/Code read-only, everything else editable, no lock:**
**Given** I open an existing Employee for editing
**When** the Edit panel loads
**Then** Employee ID/Code renders as a read-only field (UX-DR39) and every other field (Name, Email, Phone, Experience, Technologies, Position, Project, Manager Name, Location, Department — Story 7.2's field set) is editable, regardless of the Employee's Assignment history — no lock, unlike a Skill's identity-lock (FR-21/22).

**AC2 — Duplicate-email rejection on save:**
**Given** I change the Email to one already used by another active or archived Employee
**When** I save
**Then** the save is rejected with the same 409 pattern as Story 7.2's creation check (`EMPLOYEE_EMAIL_CONFLICT`, matched case-insensitively) — and saving with the Employee's **own unchanged** email never spuriously conflicts with itself.

**AC3 — Successful save updates the roster live:**
**Given** I save a valid edit
**When** the request succeeds
**Then** the roster (Story 7.3's list) reflects the change without a full page reload, and no confirmation/lock step is required.

**AC4 — Concurrent edits, last-write-wins:**
**And** if two HR Admins edit the same Employee concurrently, the last write wins with no conflict error (documented `[ASSUMPTION]`, matching this PRD's existing no-optimistic-locking precedent elsewhere).

## Tasks / Subtasks

- [x] **Task 1: Schema** (`backend/app/employees/schemas.py`)
  - [x] `UpdateEmployeeRequest(BaseModel)`: identical field set to `CreateEmployeeRequest` **minus `employee_code`**, same `max_length`s per column, same `_reject_blank` validator reused on `name`, `model_config = ConfigDict(extra="forbid")` (Scope Note 2). No new response schema — `EmployeeResponse` is reused as-is (Scope Note 3).

- [x] **Task 2: Repository** (`backend/app/employees/repository.py`)
  - [x] `get_employee_by_id(db, employee_id: UUID) -> Employee | None` — plain PK lookup, no `archived_at` filter (an archived Employee can still be edited — nothing in the AC restricts editing to active-only, unlike Story 7.6's regenerate-password). Note: `assignments/repository.py::get_employee_by_id` already exists (used by `/api/auth/me`) with the identical signature/behavior — this is a deliberate, AD-1-consistent duplication (each module owns its own reads of `employees`, not a shared cross-module helper), not an oversight; don't import the assignments-module version instead.
  - [x] `get_employee_by_email_ci_excluding_id(db, email: str, exclude_id: UUID) -> Employee | None` — same shape as `get_employee_by_email_ci` but adds `Employee.id != exclude_id` so an Employee's own unchanged email never self-conflicts (Scope Note 4/AC2).
  - [x] `update_employee(db, employee: Employee, data: dict) -> Employee` — `setattr` each field from `data` onto `employee`, `await db.flush()`, `await db.refresh(employee)`. `updated_at` bumps automatically via the model's existing `onupdate=func.now()` (Story 7.1) — no explicit set needed.

- [x] **Task 3: Auth repository — new cross-module write** (`backend/app/auth/repository.py`)
  - [x] `get_account_by_email_ci_excluding_id(db, email: str, exclude_id: UUID) -> Account | None` — same self-exclusion shape as Task 2's employee-side lookup, for the `IntegrityError` backstop's accounts-side re-check (Scope Note 4).
  - [x] `update_account_email(db, *, id: UUID, email: str) -> None` — the sole write path for changing an existing `accounts.email` value, following `create_account`'s established centralization pattern (Story 7.2 code review) so `Account`'s column shape stays known in exactly one place.

- [x] **Task 4: Service** (`backend/app/employees/service.py`)
  - [x] `_not_found(employee_id) -> AppException`: `404`, error_code `EMPLOYEE_NOT_FOUND`.
  - [x] `update_employee_service(db, *, current_user, employee_id: UUID, request: UpdateEmployeeRequest) -> EmployeeResponse`:
    - `require_hr_admin(current_user)` first (matches every other service method in this module).
    - `employee = await repository.get_employee_by_id(db, employee_id)`; if `None`, raise `_not_found(employee_id)`.
    - If `request.email.lower() != employee.email.lower()`: check `repository.get_employee_by_email_ci_excluding_id(db, request.email, employee.id)`; if a match is found, raise `_email_conflict(request.email)` (reuse the existing Story 7.2 helper, no new error code).
    - Apply the update: build a `dict` of all `UpdateEmployeeRequest` fields, call `repository.update_employee(db, employee, data)`.
    - If the email changed, also call `auth_repository.update_account_email(db, id=employee.id, email=request.email)` (Scope Note 4) — inside the same service call, same transaction, so a failure rolls back both.
    - Wrap the flush in a `try/except IntegrityError` backstop mirroring `create_employee_service`'s exact shape: on rollback, re-check both `employees` (excluding self) and `accounts` (excluding self, Task 3) before re-raising a `_email_conflict`, else re-raise the original error.
    - Return `EmployeeResponse.model_validate(employee)`.

- [x] **Task 5: Router** (`backend/app/employees/router.py`)
  - [x] `PATCH "/{employee_id}"` → `update_employee_route`, `response_model=EmployeeResponse`, path param typed `UUID`. Same `Depends(get_current_user)` + `Depends(get_db)` shape as the existing two routes.

- [x] **Task 6: Backend tests** (`backend/tests/test_employees_router.py`, extend existing file — same private-engine/`_login`/`_delete_employee_by_code` conventions, no new test file)
  - [x] AC1: create an employee, `PATCH` every editable field to new values, assert `200` and every field reflects the new value; assert `employee_code` in the response is unchanged even though the response body's `employee_code` was never part of the request.
  - [x] AC1/no-lock: `PATCH` succeeds for an employee regardless of Assignment history — cover via a code-reading assertion in Dev Notes if a real Assignment fixture is too heavy to stand up cheaply here; if a lightweight existing Assignment-creation helper already exists in `test_assignments_*` fixtures, prefer a real end-to-end check over an inference.
  - [x] Sending `employee_code` in the request body → `422` (Scope Note 2, `extra="forbid"`).
  - [x] AC2: create two employees, `PATCH` the second one's email to the first's (any case) → `409`, `code == "EMPLOYEE_EMAIL_CONFLICT"`.
  - [x] AC2/self-exclusion: `PATCH` an employee with every field identical to its current values (including its own current email) → `200`, not `409`.
  - [x] AC2/account sync: `PATCH` an employee's email to a new value, then directly query `Account` by `id` and assert `Account.email` now matches the new value (Scope Note 4).
  - [x] 404: `PATCH` a random non-existent UUID → `404`, `code == "EMPLOYEE_NOT_FOUND"`.
  - [x] Role gate: EMPLOYEE session → `403`; unauthenticated → `401` (same pattern as every other route in this router).
  - [x] Archived employee: `PATCH` an employee whose `archived_at` is set (directly via the private session, no archive endpoint exists yet) still succeeds — nothing in the AC restricts editing to active-only.
  - [x] AC4: two sequential `PATCH` requests against the same employee (simulating two HR Admins editing concurrently, no interleaving needed since there's no lock to race) — assert the second request's values are what persists, with no conflict error from either call.
  - [x] Full regression run; record before/after counts in the Dev Agent Record.

- [x] **Task 7: Frontend API client** (`frontend/src/lib/api/employeesApi.ts`, extend existing file)
  - [x] `UpdateEmployeeRequest` TS interface mirroring the backend schema (all `CreateEmployeeRequest` fields minus `employee_code`).
  - [x] `updateEmployee(id: string, payload: UpdateEmployeeRequest): Promise<EmployeeResponse>` → `PATCH /api/admin/employees/${id}`.

- [x] **Task 8: Edit modal** (`frontend/src/features/admin/EditEmployeeModal.tsx`, new file — mirrors `NewSkillModal.tsx` structure directly, Scope Note 8)
  - [x] Props: `open: boolean`, `employee: EmployeeResponse | null`, `onClose: () => void`, `onSaved: (updated: EmployeeResponse) => void`.
  - [x] `useEffect([open, employee])`: on open, seed all form fields from `employee`'s current values; reset `error`/`submitting` (mirrors `NewSkillModal`'s reset-on-open effect).
  - [x] `employee_code` rendered as a disabled/read-only `Input` (or plain text), labeled, `data-testid="edit-employee-id-readonly"` (UX-DR39/AC1) — never submitted in the request body.
  - [x] All 10 remaining fields as `Label`+`Input` pairs (Name, Email required; the other 8 optional, `null`-when-empty on submit) — `data-testid`s following the existing `new-skill-*` naming convention, e.g. `edit-employee-name-input`, `edit-employee-email-input`, etc.
  - [x] `requestIdRef` staleness guard identical to `NewSkillModal`'s (Scope Note 8).
  - [x] Submit handler: call `updateEmployee(employee.id, payload)`; on success, `onSaved(updated)` then `onClose()`; on `409`, show an inline notice `data-testid="edit-employee-duplicate-notice"` reading "An employee with this email already exists." (verbatim, per the UX spec's `edit-employee-duplicate-notice` object); on any other error, `FormErrorText` via the same `extractErrorMessage()` helper pattern.
  - [x] Header: `data-testid="edit-employee-header-title"` reading `Edit {employee.name}`; close button `data-testid="edit-employee-btn-close"`; save button `data-testid="edit-employee-btn-save"` reading "Save changes".

- [x] **Task 9: Wire into `EmployeesPage.tsx`** (extend existing file, Scope Notes 9/10)
  - [x] New state: `const [editingEmployee, setEditingEmployee] = useState<EmployeeResponse | null>(null)`.
  - [x] `RowActions`: add an `onEdit: (employee: EmployeeResponse) => void` prop, wire **only** the Edit button's `onClick` to `() => onEdit(employee)` — Regenerate Password and Delete/Archive stay on `onUnavailable` exactly as today.
  - [x] Render `<EditEmployeeModal open={editingEmployee !== null} employee={editingEmployee} onClose={() => setEditingEmployee(null)} onSaved={handleEmployeeSaved} />` near the existing `<Toast .../>`.
  - [x] `handleEmployeeSaved(updated: EmployeeResponse)`: call `void refetch()` (Scope Note 9) and `setEditingEmployee(null)`.

- [x] **Task 10: Frontend tests**
  - [x] `frontend/src/tests/EmployeesPage.test.tsx` (extend): clicking a row's Edit button opens the modal pre-filled with that employee's current values; a successful save closes the modal and the roster reflects the new value (mock `updateEmployee`/re-mock `listEmployees` for the post-save `refetch()`); Regenerate Password/Delete-Archive buttons are unaffected (still show the "not available yet" toast).
  - [x] `frontend/src/tests/EditEmployeeModal.test.tsx` (new file — note: colocated under `frontend/src/tests/`, NOT next to the component in `features/admin/`; matches where `NewSkillModal.test.tsx`/`DeleteSkillModal.test.tsx` actually live, confirmed by reading those files' real location, not assumed from their component's folder): Employee ID/Code renders read-only and is never part of the submitted payload; all 10 other fields are editable and submit their edited values; a `409` response shows the duplicate-email notice and does not close the modal; a non-409 error shows a generic message; Escape/backdrop-click/`onClose` all work via the shared `Dialog` primitive (already covered by `Dialog`'s own tests if any exist — don't duplicate, just confirm this modal renders through `Dialog` correctly).
  - [x] AC4 (concurrent edits, last-write-wins): not independently meaningful to test on the frontend beyond the backend's Task 6 coverage — no frontend-side locking/conflict UI exists to verify. Skip a dedicated frontend test for this AC.
  - [x] `tsc --noEmit` and `vite build` clean; record before/after in the Dev Agent Record.

### Review Findings

_(`bmad-code-review`, 2026-09-11, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor. Blind Hunter empirically reproduced two real bugs against the live dev DB rather than reasoning about them; Acceptance Auditor found no AC violations but caught real documentation-accuracy issues.)_

- [x] [Review][Patch] `update_employee_service`'s `IntegrityError` backstop accesses `employee.id` (an attribute on an ORM object whose attributes were just expired by `await db.rollback()`) instead of the already-available `employee_id` function parameter — on a genuine concurrent-write race this crashes with `sqlalchemy.exc.MissingGreenlet` (reproduced live) instead of returning the intended clean `409`. This is a regression against an established, documented pattern in this exact codebase (`content/service.py`'s and `skills/service.py`'s own `IntegrityError` backstops both deliberately use a plain id parameter post-rollback for this exact reason). [`backend/app/employees/service.py:231,234-236`]
- [x] [Review][Patch] A case-only email edit (e.g. `Jane@x.com` → `jane@x.com`) updates `Employee.email` but never syncs `Account.email`, since the sync is gated on `email_changed` (a case-insensitive comparison) while the raw-cased value is always written — violating Scope Note 4's explicit anti-drift requirement. Reproduced live and independently flagged by all three review layers. [`backend/app/employees/service.py:203-225`]
- [x] [Review][Patch] This story file's own Task 4 subtasks (`_not_found`, `update_employee_service`) are left unchecked despite being fully implemented and covered by passing tests — a documentation inconsistency, not a code defect. [`_bmad-output/implementation-artifacts/7-4-hr-admin-edits-an-employee-record.md:80-88`]
- [x] [Review][Patch] Dev Agent Record's frontend test-count arithmetic is wrong: it states "343-passed baseline + 21 new tests," but Story 7.3's own recorded baseline was 355 (not 343), and the actual new-test count is 9 (7 in `EditEmployeeModal.test.tsx` + 2 in `EmployeesPage.test.tsx`, plus 1 rewritten) — not 21, which was the file's post-change total mislabeled as a new-test count. The final `364 passed` figure itself is correct (355 + 9 = 364, independently verified). [`_bmad-output/implementation-artifacts/7-4-hr-admin-edits-an-employee-record.md:180,199`]

- [x] [Review][Defer] `auth/repository.py::update_account_email` calls `db.get(Account, id)` with no `None` check — if no `Account` row exists for the given id, this crashes with a raw `AttributeError` (500) instead of a clean error. [`backend/app/auth/repository.py:51-61`] — deferred, currently unreachable: AR-24 guarantees every `Employee` gets a paired `Account` atomically at creation (`create_employee_with_account`), and no delete/archive path exists yet (Story 7.5) that could orphan one.
- [x] [Review][Defer] `UpdateEmployeeRequest`'s 8 optional string fields have no `_reject_blank`/strip validator (only `name` does), so a whitespace-only value passes validation and stores verbatim. [`backend/app/employees/schemas.py`] — deferred, pre-existing (mirrors `CreateEmployeeRequest`'s identical gap from Story 7.2, not introduced or worsened by this story).
- [x] [Review][Defer] Name/Email carry no visual or `aria-required` marker distinguishing them as required from the other 8 optional fields. [`frontend/src/features/admin/EditEmployeeModal.tsx`] — deferred, pre-existing (mirrors `NewSkillModal.tsx`'s identical gap, which also marks its one required field with nothing but a disabled-Save fallback).
- [x] [Review][Defer] The duplicate-email notice has no `aria-describedby`/`role="alert"` association with the Email input for screen-reader users. [`frontend/src/features/admin/EditEmployeeModal.tsx`] — deferred, pre-existing (mirrors `NewSkillModal.tsx`'s identical duplicate-notice pattern verbatim).

Dismissed as false positives / no real consequence: a claim that a `422` from an invalid `EmailStr` reaches the frontend in FastAPI's raw `{"detail": [...]}` shape — verified false by reading `core/errors.py`: `register_exception_handlers`'s `validation_exception_handler` already normalizes every `RequestValidationError` codebase-wide into the standard `{status, code, message, timestamp}` envelope, so `extractErrorMessage` reads a real (if generic) message, not a silent fallback; a claim that `test_update_employee_concurrent_edits_last_write_wins` isn't "truly concurrent" — matches this story's own Scope Note 7 ("no interleaving needed since there's no lock to race"), a deliberate authoring-time decision, and this codebase's universal precedent of never testing genuine concurrent races for any last-write-wins claim; a claim that only one field (`employee_code`) is tested for the `extra="forbid"` 422 — `extra="forbid"` is a single uniform Pydantic model-level setting, not per-field, so one representative test is standard, sufficient practice matching Story 7.2's own precedent; a claim that a successful save should show a success toast — AC3 explicitly states "no confirmation ... step is required," so its absence is spec-compliant by design, not a regression.

## Dev Notes

### Route naming and body shape — a deliberate, documented choice, not a guess

No existing endpoint in this codebase edits an existing resource's fields in place with a full-replace body (Skills are permanently locked once assigned, so `skills/` never needed one). `PATCH /api/admin/employees/{employee_id}` was chosen over `PUT` purely as REST convention (editing a subset of a resource's fields, even though this particular body happens to require every editable field present) — there is no functional difference here since the body always contains the complete editable-field set either way. Do not read "PATCH" as license to accept a partial body with `exclude_unset` semantics; the Edit modal always submits the full form.

### Why `employee_code` must be a schema-level omission, not a request-time no-op

`CreateEmployeeRequest` uses `extra="forbid"`. Reusing that same setting on `UpdateEmployeeRequest` (which simply never declares an `employee_code` field) means a client bug that includes it fails fast and loud with a `422`, rather than an update service that silently accepts-and-ignores an `employee_code` key that happened to be present in the JSON body. This matches the AC's "renders as a read-only field" intent at the API boundary, not just the UI layer.

### The email/Account-sync gap this story closes (and the one it deliberately doesn't)

Story 7.2's code review flagged, by name, that a future Employee-edit story would need to keep `employees.email` and `accounts.email` from drifting apart once editing existed — this is that story. What it does **not** do: make `auth/service.py::authenticate()` actually read the `Account` table (it still only reads `_MOCK_ACCOUNTS`, unchanged since Story 1.4). So this story's `Account.email` sync is forward-looking correctness (keeping the two tables consistent for whenever a later story wires real login to `Account`), not something with any observable effect on login today. Say so plainly in the Dev Agent Record rather than letting a future reader assume email-edit-affects-login was verified end-to-end here.

### Self-exclusion is the one genuinely new wrinkle vs. Story 7.2's conflict-check shape

Story 7.2's create-time check never needed a self-exclusion (there was no existing row to exclude). Every conflict check this story adds — both the pre-check and the `IntegrityError` backstop, on both `employees` and `accounts` — must exclude the Employee/Account being edited by `id`, or the most common case (an HR Admin re-saves a form without touching the Email field) would 409 against itself. Test this explicitly (Task 6, AC2/self-exclusion) rather than assuming it falls out for free.

## Architecture Compliance

- **AD-1**: all new `employees` table writes/reads stay in `employees/repository.py`. The one new `accounts` table write (`update_account_email`) is a deliberate, documented exception mirroring `create_account`'s existing precedent (Story 7.2 code review) — not a new pattern, the second and last planned use of the same exception `create_employee_with_account`'s docstring already calls out ("not a precedent to casually extend").
- **AD-6/FR-14**: `PATCH /api/admin/employees/{employee_id}` is HR_ADMIN-only via `require_hr_admin`, matching every other `/api/admin/*` mutation endpoint in this codebase.
- **AR-24**: this story is the first to touch the credential-storage decision Story 7.1 made (extending `Account`) after its initial creation-time write — extending it here (email sync) rather than introducing a second, competing mechanism.

## References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 7.4] — full AC text
- [Source: _bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md#FR-26] — full FR text, consequences, and the three `[ASSUMPTION]` items (email/session, concurrent edits, Manager Name as unmaintained free text)
- [Source: _bmad-output/C-UX-Scenarios/05-ritas-roster-management/05.1-employees-roster/05.1-employees-roster.md] — Edit Employee Panel object IDs, field list, interaction flow, UX-DR39
- [Source: _bmad-output/E-Development/05-Ritas-Roster-Management-Prototype/05.1-Employees-Tab.html] — reference prototype's simplified 3-field Edit modal (not authoritative for field scope, Scope Note 11)
- [Source: _bmad-output/implementation-artifacts/7-1-employees-module-foundation-schema-migration-and-credential-reconciliation.md] — schema (`employee_code` immutability, `updated_at` auto-bump), AR-24 credential decision
- [Source: _bmad-output/implementation-artifacts/7-2-hr-admin-creates-a-new-employee-record.md] — `CreateEmployeeRequest`/`EmployeeResponse` shapes, the 409 dual-table conflict-check pattern this story extends, and its own code review's explicit forward-reference to this story
- [Source: _bmad-output/implementation-artifacts/7-3-hr-admin-views-the-employee-roster.md] — `EmployeesPage.tsx`'s fetch-once-then-filter shape, `refetch()`, `RowActions` stub wiring this story partially replaces
- [Source: backend/app/employees/schemas.py, service.py, repository.py, router.py, models.py] — current module state, read in full during story authoring
- [Source: backend/app/auth/repository.py] — `create_account`/`get_account_by_email_ci` pattern this story's new `update_account_email`/`get_account_by_email_ci_excluding_id` extend
- [Source: frontend/src/features/admin/NewSkillModal.tsx, frontend/src/components/ui/dialog.tsx] — the modal pattern `EditEmployeeModal.tsx` mirrors
- [Source: frontend/src/pages/hr/EmployeesPage.tsx, frontend/src/lib/api/employeesApi.ts] — current page/API-client state this story extends
- [Source: backend/tests/test_employees_router.py] — private-engine/`_login`/`_delete_employee_by_code` test conventions to follow

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5

### Debug Log References

- Red phase confirmed before writing any implementation: all 11 new `test_update_employee_*` tests in `test_employees_router.py` failed with `404 Not Found` (no `PATCH /{employee_id}` route existed yet) before Tasks 1-5 landed.
- All 11 new backend tests passed on the first implementation attempt (no red→green iteration needed beyond the initial red confirmation). Full backend regression: **673 passed, 2 skipped, 0 failed** (662-passed post-Story-7.3 baseline + 11 new), zero regressions.
- 9 new frontend tests (7 in `EditEmployeeModal.test.tsx`, all new + 2 new tests added to `EmployeesPage.test.tsx`), plus 1 pre-existing `EmployeesPage.test.tsx` test rewritten (it asserted Edit showed the stub toast, no longer true), all passed on the first run. Full frontend regression: **364 passed, 0 failed** (355-passed post-Story-7.3 baseline + 9 new — corrected during code review; the record originally stated "343-passed baseline + 21 new tests," which was wrong on both numbers, though the final 364 total was already correct). `tsc --noEmit`: 73 pre-existing errors, byte-identical before/after (confirmed via `git stash -u` against the pre-story baseline — the 73 count is higher than Story 7.3's recorded 31 because `project-context.md`'s update log has a gap across Stories 6.6-7.3, see the note added there; none of the 73 touch any file this story modified). `vite build`: clean, 531 modules (up from 530 pre-story, for the new `EditEmployeeModal.tsx`).
- **Live-verified end-to-end against the real Docker backend, not just tests**: rebuilt `talentpilot-ai-backend` and recreated `talentpilot-api` (no volume mount, same requirement as every migration/schema-touching story since 6.1). Via `curl` as Rita: created a test Employee, `PATCH`ed every editable field including email (`200`, `updated_at` genuinely bumped), confirmed `employee_code` in the body → `422`, confirmed a random UUID → `404 EMPLOYEE_NOT_FOUND`; as Casey (EMPLOYEE) → `403 FORBIDDEN_NOT_HR_ADMIN`; unauthenticated → `401`. Cleaned up the test row directly in the dev DB afterward.
- **Live browser verification via an ad hoc Playwright/Chromium smoke test** (disposable `playwright-core` install against the pre-existing local Chromium cache, uninstalled after use — `package-lock.json`'s resulting metadata churn was reverted via `git checkout`, no net lockfile change retained, same pattern as Story 7.3's precedent) against `vite` dev server (proxying `/api` to the rebuilt Docker backend) logged in as the real seeded Rita account: roster loads with Edit buttons present → clicking Edit opens the modal with Employee ID/Code disabled → edited Name + Department, saved → modal closed and the roster showed the new name with no navigation/reload → reverted the seeded employee back to its original name+department so the demo dataset wasn't left mutated → Regenerate Password still shows the "not available yet" toast (confirming Story 7.4 left it untouched, per Scope Note 10). All 8 checks passed. Console errors observed were the same benign pre-existing pattern already documented in Story 7.3's Dev Agent Record (a `401` from the login page's own pre-login session-check, one unrelated `404`) — not introduced by this story.

### Completion Notes List

- Implemented `PATCH /api/admin/employees/{employee_id}` (Story 7.4, FR-26): `UpdateEmployeeRequest` (Story 7.2's field set minus the immutable `employee_code`, `extra="forbid"`), `update_employee_service` (HR-Admin-gated, 404-on-missing, self-excluding email-conflict pre-check + `IntegrityError` backstop across both `employees` and `accounts`, `Account.email` sync on an email change), and the route itself — all following the exact patterns Story 7.2's `create_employee_service`/`schemas.py` already established.
- The one genuinely new backend wrinkle vs. Story 7.2 (flagged during story authoring, confirmed true during implementation): every conflict check needed a **self-exclusion** (`get_employee_by_email_ci_excluding_id`, `get_account_by_email_ci_excluding_id`) — Story 7.2's create-time check never needed one, since there was no prior row to exclude. Verified explicitly via `test_update_employee_unchanged_email_does_not_conflict`.
- `auth/repository.py` gained `update_account_email` and `get_account_by_email_ci_excluding_id` — the cross-module write Story 7.2's own code review anticipated by name as this story's future job, keeping `Employee.email`/`Account.email` from drifting apart. Confirmed and documented (Scope Note 5, and again here): `auth/service.py::authenticate()` still only reads the hardcoded `_MOCK_ACCOUNTS` dict, so this sync has **no observable effect on login today** — it's forward-looking correctness for whenever a later story wires real login to `Account`.
- No lock: the update service never queries `assignments`/`assignment_overrides` at all, satisfying AC1's "no lock, unlike Skills" by construction. Verified end-to-end (not just by absence of code) via `test_update_employee_succeeds_regardless_of_assignment_history`, which creates a real Assignment against the test Employee before editing it.
- Frontend: `EditEmployeeModal.tsx` mirrors `NewSkillModal.tsx`'s `Dialog`/`requestIdRef`/409-branching pattern directly (Scope Note 8) — Employee ID/Code renders as a disabled `Input` (UX-DR39), all 10 other Story-7.2 fields are editable, optional fields collapse to `null` on submit when blank. Wired into `EmployeesPage.tsx`'s existing (previously fully-stubbed) `RowActions` — only the Edit button's handler changed; Regenerate Password and Delete/Archive remain on the "not available yet" toast exactly as Story 7.3 left them (Scope Note 10), confirmed both by a unit test and the live browser check.
- A successful save calls `EmployeesPage.tsx`'s pre-existing `refetch()` (Scope Note 9) rather than patching local state or reloading the page — satisfies AC3 and matches Story 7.3's already-established precedent (no React Query/cache library exists anywhere in this codebase).
- **One pre-existing test needed rewriting, not just extending**: Story 7.3's `EmployeesPage.test.tsx` had a test asserting the Edit button showed the "not available yet" toast — now false, since Edit opens the real modal. Split into two tests: one confirming Regenerate Password/Delete-Archive still show the stub toast, one confirming Edit now opens the modal pre-filled with the row's data.
- AC4 (concurrent edits, last-write-wins): covered on the backend via two sequential `PATCH` requests against the same Employee, asserting the second's values persist with no conflict error. Deliberately not given a dedicated frontend test (Scope Note/Task 10) — there is no frontend-side locking/conflict UI to verify.

### Test Results

```
Backend:  675 passed, 2 skipped, 0 failed  (662-passed post-Story-7.3 baseline + 11 new implementation tests + 2 new code-review regression tests)
Frontend: 364 passed, 0 failed  (355-passed post-Story-7.3 baseline + 9 new tests across EditEmployeeModal.test.tsx and EmployeesPage.test.tsx, net of 1 rewritten pre-existing test)
tsc --noEmit: 73 pre-existing errors, unchanged (verified via git-stash baseline diff; none touch a file this story modified)
vite build: clean, 531 modules (up from 530 pre-story)
```

Live-verified end-to-end: `curl` against the rebuilt Docker backend (200/422/404/403/401 all confirmed with the exact expected bodies/codes) and an ad hoc Playwright/Chromium smoke test against the real dev server + Docker backend (8/8 checks passed, including a real edit-save-roster-updates-live round trip with no page reload).

### Code Review Patches (2026-09-11)

4 patch findings from `bmad-code-review` applied (see Review Findings above):
- **Real bug fixed**: the `IntegrityError` backstop's re-check calls now use the `employee_id` function parameter instead of `employee.id` — reading an ORM attribute after `await db.rollback()` (which expires the session's objects) raised `sqlalchemy.exc.MissingGreenlet` on a genuine concurrent-write race, crashing with a raw 500 instead of the intended clean `409`. Blind Hunter reproduced this live before the fix; `test_update_employee_account_side_email_conflict_returns_409_not_500` (new) deterministically reaches this exact path (same desync technique as Story 7.2's own account-side-conflict test) and asserts a clean `409`, plus that the failed transaction fully rolled back rather than leaving Employee B half-updated.
- **Real bug fixed**: a case-only email edit (e.g. `Jane@x.com` → `jane@x.com`) now correctly syncs `Account.email` — the sync condition changed from a case-insensitive comparison (which a case-only change never trips) to a raw comparison captured *before* `repository.update_employee` mutates `employee.email` in place. `test_update_employee_case_only_email_change_still_syncs_account_email` (new) covers this exactly.
- Story file's Task 4 subtask checkboxes corrected (`_not_found`/`update_employee_service` were implemented and tested but left unchecked).
- Dev Agent Record's frontend test-count arithmetic corrected (had used a stale "343-passed" baseline instead of Story 7.3's actual recorded 355; actual new-test count is 9, not 21 — the final 364 total was already right).

4 items deferred (`deferred-work.md`): `update_account_email`'s unguarded `db.get()` (currently unreachable — every Employee has a paired Account by construction, no delete path exists yet); no blank/whitespace validator on `UpdateEmployeeRequest`'s 8 optional fields (mirrors `CreateEmployeeRequest`'s pre-existing gap); no required-field marker on Name/Email in the modal (mirrors `NewSkillModal`'s pre-existing gap); no `aria-describedby` on the duplicate-email notice (mirrors `NewSkillModal`'s pre-existing gap).

Re-verified after patches: backend 675 passed / 2 skipped / 0 failed (673 + 2 new regression tests). Frontend unchanged (the two patches were backend-only + documentation).

**Both fixes also re-verified live** against a rebuilt Docker backend, not just the test suite: a case-only email `PATCH` now shows `Account.email` genuinely updated (`psql` query against `talentpilot-db` confirmed), and the same account-side-desync technique that previously crashed with `MissingGreenlet` (confirmed by Blind Hunter pre-fix) now returns a clean `409 EMPLOYEE_EMAIL_CONFLICT`. Test rows cleaned up afterward.

### File List

New files:
- `frontend/src/features/admin/EditEmployeeModal.tsx` — the Edit panel (read-only Employee ID/Code, all 10 editable fields, 409-duplicate-email notice, `requestIdRef` staleness guard)
- `frontend/src/tests/EditEmployeeModal.test.tsx` — 7 tests covering AC1 (pre-fill, read-only ID), AC2 (409 notice), submit payload shape, reset-on-reopen, close behavior

Modified files:
- `backend/app/employees/schemas.py` — `UpdateEmployeeRequest` added
- `backend/app/employees/repository.py` — `get_employee_by_id`, `get_employee_by_email_ci_excluding_id`, `update_employee` added
- `backend/app/employees/service.py` — `_not_found`, `update_employee_service` added; code review: `IntegrityError` backstop now uses `employee_id` instead of the post-rollback-expired `employee.id`; email-sync condition changed to a pre-mutation raw comparison so case-only edits sync `Account.email` too
- `backend/app/employees/router.py` — `PATCH "/{employee_id}"` → `update_employee_route` added
- `backend/app/auth/repository.py` — `get_account_by_email_ci_excluding_id`, `update_account_email` added
- `backend/tests/test_employees_router.py` — 13 new `test_update_employee_*` tests: 11 at implementation covering all 4 ACs plus 404/403/401/archived-employee/extra-forbid cases, + 2 code-review regression tests (case-only email sync, account-side `IntegrityError` backstop)
- `frontend/src/lib/api/employeesApi.ts` — `UpdateEmployeeRequest` interface, `updateEmployee()` added
- `frontend/src/pages/hr/EmployeesPage.tsx` — `editingEmployee` state, `handleEmployeeSaved`, `RowActions`'s `onEdit` prop wired only to the Edit button, `EditEmployeeModal` rendered
- `frontend/src/tests/EmployeesPage.test.tsx` — 1 pre-existing test rewritten (Edit no longer shows the stub toast) + 2 new Story 7.4 tests (modal opens pre-filled; successful save updates the roster live)

No changes to:
- `backend/app/employees/models.py` — Story 7.1's schema already has everything this story needs (`updated_at`'s `onupdate=func.now()` already bumps automatically)
- `backend/app/auth/models.py`, `backend/app/auth/service.py` — `authenticate()` deliberately untouched (Scope Note 5); no schema change needed on `Account`
- `backend/app/main.py` — `employees_router` already mounted (Story 7.2)

## Completion Checklist

- [x] `UpdateEmployeeRequest` schema added (no `employee_code`, `extra="forbid"`)
- [x] `get_employee_by_id`, `get_employee_by_email_ci_excluding_id`, `update_employee` added to `employees/repository.py`
- [x] `get_account_by_email_ci_excluding_id`, `update_account_email` added to `auth/repository.py`
- [x] `update_employee_service` added: HR-Admin-gated, 404-on-missing, self-excluding 409 conflict check, `IntegrityError` backstop, `Account.email` sync
- [x] `PATCH /api/admin/employees/{employee_id}` added and working
- [x] `EditEmployeeModal.tsx` implements read-only Employee ID/Code, all 10 editable fields, 409-duplicate-email notice
- [x] `EmployeesPage.tsx`'s Edit row/card action opens the modal; Regenerate Password/Delete-Archive untouched
- [x] Successful save refetches the roster without a full page reload (AC3)
- [x] All 4 ACs covered by passing backend + frontend tests, including the self-exclusion and Account-sync cases
- [x] Full backend + frontend regression run, zero new regressions
- [x] `tsc --noEmit` / `vite build` clean
- [x] Live-verified end-to-end: `curl` against a rebuilt Docker backend, and an ad hoc Playwright smoke test in a real browser
- [x] Sprint status updated to `review` (then `done` after code review)

## Change Log

- 2026-09-11: Story created (`bmad-create-story`), building on Story 7.1 (schema/`Account` credential decision), Story 7.2 (`CreateEmployeeRequest`/`EmployeeResponse`/409 conflict pattern, and its own code review's explicit forward-reference to this exact story), and Story 7.3 (`EmployeesPage.tsx`/`refetch()`/`RowActions` stubs). Verified current code directly (schemas.py, service.py, repository.py, router.py, models.py, auth/repository.py, EmployeesPage.tsx, employeesApi.ts, NewSkillModal.tsx, dialog.tsx, test_employees_router.py) rather than relying solely on prior story docs. Identified the one genuinely new backend wrinkle (self-exclusion on the email-conflict check, absent from Story 7.2 since there was no prior row to exclude) and the one cross-module addition (`auth/repository.py::update_account_email`, anticipated by name in Story 7.2's own code review). A fresh-context validation pass caught and fixed a wrong test-file location and a missing AC4 test task before implementation began. Status → `ready-for-dev`.
- 2026-09-11: Implementation complete (`bmad-agent-dev`/Amelia, direct TDD, red-green confirmed). Backend: `UpdateEmployeeRequest`/`update_employee_service`/`PATCH "/{employee_id}"` added, plus the self-excluding conflict-check repository functions and `auth/repository.py::update_account_email` (11 new tests, all green on first run); full regression 673 passed/2 skipped/0 failed. Frontend: `EditEmployeeModal.tsx` added (mirrors `NewSkillModal.tsx`), wired into `EmployeesPage.tsx`'s previously-fully-stubbed Edit action (9 new + 1 rewritten test, all green); full regression 364 passed/0 failed; `tsc --noEmit` byte-identical to the pre-existing baseline (73 errors, none in touched files); `vite build` clean (531 modules). Live-verified end-to-end: `curl` against a rebuilt Docker backend confirmed the exact 200/422/404/403/401 behaviors, and an ad hoc Playwright/Chromium smoke test against the real dev server confirmed the full edit→save→roster-updates-live flow in an actual browser, then reverted the seeded demo employee back to its original values. Status → `review`.
- 2026-09-11: Code review (`bmad-code-review`, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor). Blind Hunter empirically reproduced two real bugs against the live dev DB rather than reasoning about them: (1) the `IntegrityError` backstop crashed with `sqlalchemy.exc.MissingGreenlet` on a genuine concurrent-write race, because it read `employee.id` after `db.rollback()` had expired the ORM object's attributes — a regression against an established, documented pattern this exact codebase already follows in `content/service.py` and `skills/service.py`; (2) a case-only email edit (e.g. `Jane@x.com` → `jane@x.com`) never synced `Account.email`, since the sync was gated on a case-insensitive comparison while the raw-cased value was always written to `Employee.email` — independently flagged by all three review layers, violating Scope Note 4's explicit anti-drift requirement. Both fixed (2 new regression tests added, one reproducing the account-side `IntegrityError` deterministically via the same desync technique as Story 7.2's own test, one covering the case-only email fix), plus 2 documentation-accuracy patches (Task 4 checkboxes, corrected frontend test-count arithmetic). 4 items deferred to `deferred-work.md` (an unguarded `db.get()` in `update_account_email`, currently unreachable; no blank-string validator on 8 optional fields, pre-existing; no required-field marker and no `aria-describedby` on the duplicate notice, both pre-existing `NewSkillModal` patterns). 4 findings dismissed as false positives or as matching deliberate, already-documented design choices (a factually-wrong claim about 422 error-body shape; a "not truly concurrent" critique that matches Scope Note 7's own stated design; a misunderstanding of `extra="forbid"`'s uniform model-level scope; a "missing success toast" critique that AC3 explicitly rules out). Full regression re-verified after patches: backend 675 passed/2 skipped/0 failed (673 + 2 new), frontend unchanged at 364 passed/0 failed (patches were backend-only + documentation). Status → `done`.
