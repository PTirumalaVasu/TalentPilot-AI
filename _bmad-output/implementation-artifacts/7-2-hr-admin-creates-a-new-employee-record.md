---
baseline_commit: 75638a224527b04d91d6769bea7e55d5ef706975
---

# Story 7.2: HR Admin Creates a New Employee Record

Status: done

## Story

As an **HR Admin**,
I want to create a new Employee record with a working login,
So that I can onboard a new hire myself without waiting on engineering (FR-24).

## Scope Notes (read before starting)

1. **This is the first story to mount `employees/router.py`.** Story 7.1 left it as a documented, unmounted stub. Mount it in `app/main.py` at `/api/admin/employees` — mirrors `skills_router`'s `/api/admin/skills` prefix exactly (both are HR-Admin-only mutation modules, same convention).
2. **Password generation + hashing already has a home.** `employees/service.py::hash_password` (bcrypt) was added by Story 7.1 — call it, don't reimplement. You still need to add the *plaintext generation* step (nothing in Story 7.1 generates passwords, only hashes/verifies them).
3. **Creating an Employee means creating TWO rows in one transaction**: the `Employee` row (profile data) and an `Account` row (`id` = the same UUID as the new `Employee.id`, `password_hash` = the generated password's hash, `role` = `"EMPLOYEE"`, `email` = same email). This is the AR-24 pattern Story 7.1 formalized — `Account.id` must always equal the corresponding `Employee.id` (enforced by the `accounts_id_fkey` FK migration 011 added). Both inserts must succeed or neither should (one DB transaction, one `flush()` — `core/db.py::get_db` commits once at the end of the request, per its documented convention, so you do not call `commit()` yourself).
4. **`authenticate()` still does NOT read `Account`** (Story 7.1's deliberately-deferred gap, `auth/service.py::authenticate` / `auth/repository.py::_MOCK_ACCOUNTS`). This story does **not** fix that — a newly-created Employee gets a real, correctly-hashed password stored in `accounts.password_hash`, but cannot actually log in with it until a future story wires `authenticate()` to check `Account` first. Do not treat this as an AC of this story; do not attempt to fix it here (out of scope, flagged in epics.md and PRD Open Question 9 as a separate gap). If asked "why can't the new employee log in," the answer is: this story's job is provisioning the credential correctly, not wiring the login path.
5. **Duplicate checks are two different case-sensitivities by design, per the AC text itself:** `employee_code` collision is checked as an *exact* match (case-sensitive) — matches the plain DB `UNIQUE` constraint `uq_employees_employee_code` (migration 011), no functional index needed. `email` collision is checked *case-insensitively* — the AC explicitly says "matching FR-20's Skill-name dedup pattern," which is `skills/repository.py::get_skill_by_name_ci` + migration `006`'s functional `UNIQUE INDEX ... (lower(name))` DB-level backstop. Add the equivalent for `employees.email` (a new migration `012`) rather than relying on the pre-check alone — the existing `employees.email` unique constraint is case-sensitive, so two different-case emails would otherwise both pass the pre-check and both insert successfully at the DB level, silently violating the AC. Mirror migration `006` exactly (see References).
6. **Duplicate checks cover archived rows too** — do not filter by `archived_at`. The `Employee`/`Account` models don't yet have any query in this codebase that filters on `archived_at` (Story 7.5 adds the first one, for the roster's default view) — for this story's dedup check, query all rows unconditionally.
7. **The Assignment Flow's employee picker needs no changes.** `assignments/repository.py::list_employees` already does an unscoped `select(Employee)` with no `archived_at` filter — a newly-created Employee is immediately visible there with zero additional work (AC4). This only works because Story 7.5 (archive) hasn't added an `archived_at` filter yet; not this story's concern.

## Acceptance Criteria

**AC1 — Create with only the 3 required fields:**
**Given** an HR Admin submits a new Employee with Employee ID/Code, Name, and Email (the only required fields)
**When** the request is valid and neither the ID/Code nor Email collides with an existing record (active or archived — Email checked case-insensitively, matching FR-20's Skill-name dedup pattern)
**Then** the record is created, a password is generated server-side, hashed via `employees.service.hash_password`, and stored in a new `Account` row (`Account.id == Employee.id`, `role="EMPLOYEE"`) — and the plaintext password is returned **exactly once** in this response, never persisted in plaintext, never retrievable via any other endpoint.

**AC2 — Duplicate ID or Email rejected, not overwritten:**
**Given** an HR Admin submits an Employee ID/Code or Email that already exists (active or archived)
**When** the request is validated
**Then** it is rejected with `409` and a message identifying which field collided (`employee_code` vs `email` — do not use one ambiguous "ID or email" message at the API layer; that ambiguity belongs to the UI copy layer, not the API contract) — never a silent overwrite.

**AC3 — Optional fields default to null:**
**Given** an HR Admin omits any of the 8 optional fields (Phone, Experience, Technologies, Position, Project, Manager Name, Location, Department)
**When** the record is created
**Then** creation succeeds with those fields `null` — no field beyond ID/Code, Name, Email is required.

**AC4 — Immediately assignable:**
**And** the new Employee is immediately selectable in the Skill Assignment Flow's employee picker (§4.1/FR-1) — no separate publish/activation step (already true via `assignments/repository.py::list_employees`'s existing unscoped query — verify with a test, don't just assume).

## Tasks / Subtasks

- [x] **Task 1: Migration 012 — case-insensitive unique index on `employees.email`** (AC2)
  - [x] `backend/alembic/versions/012_add_employees_email_ci_unique_index.py`, mirroring `006_add_skills_name_ci_unique_index.py` exactly: `CREATE UNIQUE INDEX ix_employees_email_lower ON employees (lower(email))`; `downgrade()` drops it.
  - [x] Applied via `alembic upgrade head` against the local dev DB (port 5433); verified via direct `pg_indexes` query that the functional unique index exists (`CREATE UNIQUE INDEX ix_employees_email_lower ON public.employees USING btree (lower((email)::text))`).

- [x] **Task 2: Schemas** (`backend/app/employees/schemas.py`)
  - [x] `CreateEmployeeRequest`: `employee_code`/`name` required + non-blank (`_reject_blank` validator), `email: EmailStr` required, 8 optional fields all `str | None = None` with `max_length` matching each DB column. `model_config = ConfigDict(extra="forbid")`.
  - [x] `EmployeeResponse`: all `Employee` columns (no password field — that lives on `Account`). `model_config = ConfigDict(from_attributes=True)`.
  - [x] `EmployeeCreatedResponse(EmployeeResponse)`: adds `generated_password: str` — extends rather than wraps, so `EmployeeResponse.model_validate(employee).model_dump()` unpacks directly into it alongside the plaintext.
  - [x] `email-validator==2.3.0` added explicitly to `backend/requirements.txt` and `backend/requirements-prod.txt`; installed into the local venv and verified importable.

- [x] **Task 3: Repository** (`backend/app/employees/repository.py`)
  - [x] `get_employee_by_code(db, employee_code) -> Employee | None` — exact match, no `archived_at` filter.
  - [x] `get_employee_by_email_ci(db, email) -> Employee | None` — `func.lower(Employee.email) == func.lower(email)`, no `archived_at` filter.
  - [x] `create_employee_with_account(db, employee_data, password_hash) -> Employee` — `Employee(**employee_data)` → `add`/`flush`/`refresh` to get the generated `id`, then `Account(id=employee.id, email=employee.email, password_hash=password_hash, role="EMPLOYEE")` → `add`/`flush`. Both writes in one function so no caller can leave either row orphaned.
  - [x] `Account` imported from `app.auth.models` — documented in the function's own docstring as the deliberate, AR-24-sanctioned AD-1 exception this story establishes (no prior precedent existed for a cross-module *write* to `accounts`; flagged plainly rather than hidden).

- [x] **Task 4: Password generation** (`backend/app/employees/service.py`)
  - [x] `generate_password() -> str`: 12 chars via `secrets.choice` over the documented ambiguity-excluding alphabet, matching the validated UX prototype exactly.

- [x] **Task 5: Service** (`backend/app/employees/service.py`)
  - [x] `create_employee_service`: `require_hr_admin` gate first, then exact `employee_code` check → `EMPLOYEE_CODE_CONFLICT` 409, then case-insensitive `email` check → `EMPLOYEE_EMAIL_CONFLICT` 409, then generate+hash password, then `create_employee_with_account`, wrapped in `try/except IntegrityError` (rollback, re-query both fields, raise whichever actually collided, or re-raise if neither does). Returns `EmployeeCreatedResponse` with the plaintext attached — the only place in the codebase it ever exists.

- [x] **Task 6: Router** (`backend/app/employees/router.py`)
  - [x] `router = APIRouter(dependencies=[Depends(get_current_user)])`, `POST ""` → `create_employee_route`, `response_model=EmployeeCreatedResponse`, `status_code=201`.
  - [x] Mounted in `backend/app/main.py`: `app.include_router(employees_router, prefix="/api/admin/employees", tags=["employees"])`, placed directly after `skills_router`'s mount line.

- [x] **Task 7: Tests**
  - [x] `backend/tests/test_employees_service.py` extended: 4 new tests for `generate_password()` (length, alphabet membership, ambiguous-character exclusion, 20-call uniqueness).
  - [x] New `backend/tests/test_employees_router.py` (11 tests): AC1 (201, `Account` row created with matching `id`, password verifies via `verify_password`), AC2 (duplicate `employee_code` → 409 `EMPLOYEE_CODE_CONFLICT`; duplicate email including different-case → 409 `EMPLOYEE_EMAIL_CONFLICT`), AC3 (all 8 optional fields null when omitted), AC4 (new employee found via `assignments.repository.list_employees` directly), 403 for an EMPLOYEE session, 401 unauthenticated, 422 for missing required field / blank name / invalid email / unknown field.
  - [x] Full regression run: **656 passed, 2 skipped, 0 failed** (up from the 641-passed baseline — the +15 delta is exactly the 4 new service tests + 11 new router tests; zero pre-existing tests broke). `app.main` also verified to import cleanly with the new router mounted (15 routes registered).

## Dev Notes

### Why a new migration for email case-insensitivity, when Story 7.1 already touched this table

Story 7.1's migration 011 added `employees.email`'s *columns* but didn't touch its case-sensitivity — that column has carried a plain (case-sensitive) `UNIQUE` constraint since Story 1.x, long before Epic 7. This story is the first to need case-insensitive email dedup (Story 7.1 never created Employees, only migrated the schema), so it's the right place to add the functional index — exactly mirroring how Story 6.2 (Skill creation, not Skill's original migration) added migration 006's `lower(name)` index only once Skill creation actually needed dedup. Don't be tempted to skip this and rely on the pre-check alone — Story 6.2's own code review caught that exact gap; don't repeat it.

### The `Account` write is new — no existing module has ever written to `auth`'s table before

Every existing FK to `employees.id` in this codebase (`AdminApiKey.admin_id`, `Assignment.employee_id`, etc.) is a *read* relationship — nothing outside `auth/` has ever inserted an `Account` row. This story is the first. It's a deliberate, AR-24-sanctioned exception to strict AD-1 module ownership (the alternative — routing every Employee-creation request through `auth/service.py` — would be backwards, since `auth/` doesn't own the Employee-creation workflow or its validation rules). State this plainly in code comments at the import site; don't let it look like an accidental boundary violation to a future reader.

### `EmailStr` requires `email-validator` — installed but undeclared (verified during story authoring)

Pydantic's `EmailStr` type needs the `email-validator` package installed, or it raises an `ImportError` at import time, not a validation-time error. Verified during story authoring: `email-validator==2.3.0` **is** already installed in `backend/.venv` (a transitive pull, likely via a FastAPI extra) but is **not** listed in `requirements.txt` or `requirements-prod.txt` — the identical class of gap Story 7.1 found with `bcrypt`. Add `email-validator==2.3.0` explicitly to both requirements files as part of this story (Task 2) rather than leaving it an undeclared transitive dependency a second time.

### Password generation does not need to satisfy any complexity/strength policy

No AC or PRD FR specifies a password complexity requirement — the 12-character, ambiguity-excluding alphabet from the validated UX prototype is the full spec. Do not add complexity rules (uppercase+digit+symbol requirements, etc.) that no requirement asked for — this is exactly the kind of unrequested scope creep the project's own conventions (and this session's standing guidance) call out to avoid.

## Dev Agent Record

### Debug Log

- Confirmed `email-validator==2.3.0` was already installed in `backend/.venv` (transitive) but undeclared in either requirements file, exactly matching Story 7.1's `bcrypt` finding pattern — added it explicitly to both before writing any code that imports `EmailStr`.
- Migration 012 applied cleanly against the local dev DB (port 5433) on the first attempt; verified the resulting index definition directly via `pg_indexes` (`CREATE UNIQUE INDEX ix_employees_email_lower ON public.employees USING btree (lower((email)::text))`) rather than trusting the migration script alone.
- All 20 new tests (4 service + 11 router, plus 5 pre-existing service tests re-run) passed on the first run with no red-phase failures needing a fix — the story's detailed Dev Notes/Scope Notes (mirroring `skills/`'s exact patterns for dedup, conflict responses, and the request/response schema split) meant the implementation matched the tests' expectations on the first pass.
- Full regression suite: 656 passed, 2 skipped, 0 failed — a clean +15 over the 641-passed baseline (4 new service tests + 11 new router tests), confirming zero pre-existing tests were affected by the new unique index or the two new endpoints/tables touched.
- `app.main` verified to still import cleanly with `employees_router` mounted (15 total routes registered) — checks for the circular-import risk any new cross-module wiring could introduce.

### Completion Notes

- Implemented `POST /api/admin/employees` (Story 7.2, FR-24): the first Employee-creation path in the codebase, and the first code to actually exercise the `Account` credential mechanism Story 7.1 built.
- Confirmed a real gap during implementation (already anticipated in the story's Dev Notes): `employees.email` only carried a case-sensitive unique constraint. Added migration 012 (case-insensitive functional unique index), mirroring migration 006's identical fix for `skills.name` — this closes a concurrent-request race the same way Story 6.2's code review originally found and fixed.
- `create_employee_with_account` (repository) performs the Employee + Account writes as one function so no caller can leave either row orphaned — documented in its own docstring as the deliberate, AR-24-sanctioned AD-1 exception this story establishes (first-ever cross-module write from `employees/` into `auth/`'s owned `accounts` table).
- Duplicate detection matches the AC's literal wording precisely: `employee_code` is exact-match (case-sensitive, backed by the pre-existing plain unique constraint), `email` is case-insensitive (backed by the new migration 012 index) — verified via a dedicated test that a different-case email collision is caught.
- `generate_password()` mirrors the already-validated UX prototype's alphabet and length exactly (12 chars, ambiguous characters excluded), but uses `secrets.choice` instead of `Math.random()` since this is a real credential, not a UI mock.
- As documented in Scope Note 4, `authenticate()` still does not read `Account` — a newly-created Employee's password is correctly generated, hashed, and stored, but cannot yet be used to log in until a future story wires that path. This is out of scope here by design, not an oversight.

### Test Results

```
656 passed, 2 skipped in 96.54s
```

No new regressions relative to baseline commit `75638a22` (which already included Story 7.1's 641-passed state). The 2 skipped tests are pre-existing skips unrelated to this story. The +15 delta over the 641-passed baseline is exactly accounted for by this story's new tests (4 in `test_employees_service.py`, 11 in the new `test_employees_router.py`).

## File List

New files:
- `backend/alembic/versions/012_add_employees_email_ci_unique_index.py`
- `backend/tests/test_employees_router.py`

Modified files:
- `backend/app/employees/schemas.py` — `CreateEmployeeRequest`, `EmployeeResponse`, `EmployeeCreatedResponse` added
- `backend/app/employees/repository.py` — `get_employee_by_code`, `get_employee_by_email_ci`, `get_employee_by_code_or_email_ci` (code review: combined dedup query), `create_employee_with_account` added; post-review, `Account` construction delegated to `auth_repository.create_account` instead of being inlined
- `backend/app/employees/service.py` — `generate_password`, `_code_conflict`/`_email_conflict` helpers, `create_employee_service` added; post-review: bcrypt hashing offloaded via `asyncio.to_thread`, duplicate pre-check/backstop switched to the combined query, `IntegrityError` backstop extended to also check `accounts` via `auth_repository.get_account_by_email_ci`
- `backend/app/employees/router.py` — `POST ""` → `create_employee_route` added (first mounted endpoint for this module)
- `backend/app/main.py` — `employees_router` imported and mounted at `/api/admin/employees`
- `backend/app/auth/repository.py` — code review: added `get_account_by_email_ci` and `create_account` (the new sole write path into `accounts` from another module)
- `backend/requirements.txt`, `backend/requirements-prod.txt` — added `email-validator==2.3.0`
- `backend/tests/test_employees_service.py` — 4 new tests for `generate_password()`
- `backend/tests/test_employees_router.py` — code review: 1 new regression test (`test_create_employee_account_side_email_conflict_returns_409_not_500`)

No changes to:
- `backend/app/auth/repository.py::authenticate()` / `_MOCK_ACCOUNTS` — explicitly out of scope (Scope Note 4)
- `backend/app/assignments/repository.py::list_employees` — AC4 verified via a new test, no code change needed

## Architecture Compliance

- **AD-1 exception, deliberate and AR-24-sanctioned**: `employees/repository.py` triggers a write to `auth`'s `accounts` table (Task 3). This is the one designed exception this epic's architecture creates — not a violation to fix, but also not a precedent to casually extend to unrelated future cross-module writes without the same explicit reasoning. Post-code-review, the actual `Account` row construction was moved into a new `auth.repository.create_account` function so `auth/` remains the single place that knows `Account`'s column shape — `employees/` only decides *when* to call it.
- **AR-24**: this story is the first to actually exercise the `Account` credential path Story 7.1 built. `authenticate()` still doesn't read it — do not close that gap here (Scope Note 4).

## Senior Developer Review (AI)

**Outcome:** Changes Requested → all 4 findings patched
**Reviewed:** 2026-09-11 (`code-review` skill, forked background execution)

### Action Items

- [x] **[Med]** `create_employee_service` ran `hash_password()` (bcrypt, ~100-300ms) synchronously inside the async request handler, blocking the entire single-process event loop on every create — offloaded via `asyncio.to_thread`, mirroring `main.py`'s existing `asyncio.to_thread(load_embedding_model)` precedent. (`backend/app/employees/service.py`)
- [x] **[Med]** The `IntegrityError` backstop only re-checked `employees`, so a failure on the *Account* insert specifically (not the Employee insert) — e.g. a stale `accounts.email` left over from a hypothetical future Employee-edit story letting the two tables' emails drift apart — fell through to a raw, unattributed 500 instead of a clean 409. Added `auth_repository.get_account_by_email_ci` and a check against it in the backstop; added a regression test (`test_create_employee_account_side_email_conflict_returns_409_not_500`) that manufactures exactly this desync and asserts a 409, not a 500. (`backend/app/employees/service.py`, `backend/app/auth/repository.py`, `backend/tests/test_employees_router.py`)
- [x] **[Low]** Two sequential duplicate-check queries (`employee_code` then `email`) on every create request — combined into one `get_employee_by_code_or_email_ci` query (single round-trip, `OR`-based `WHERE`), used both for the pre-check and the post-rollback backstop re-check. (`backend/app/employees/repository.py`, `backend/app/employees/service.py`)
- [x] **[Low]** `Account(...)` was constructed inline in `employees/repository.py`, duplicating knowledge of a table `auth/` is documented to own — a future required-column change would need remembering in two modules. Added `auth.repository.create_account`; `employees/repository.py::create_employee_with_account` now calls it instead of constructing the row itself. (`backend/app/auth/repository.py`, `backend/app/employees/repository.py`)

All 4 patches verified together: full regression **657 passed, 2 skipped, 0 failed** (656-passed post-implementation baseline + 1 new regression test), `app.main` still imports cleanly (15 routes).

## References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 7.2] — full AC text
- [Source: _bmad-output/implementation-artifacts/7-1-employees-module-foundation-schema-migration-and-credential-reconciliation.md] — the module scaffold, migration 011, and `hash_password`/`verify_password` this story builds directly on top of
- [Source: backend/app/skills/service.py::create_skill_service, backend/app/skills/repository.py::get_skill_by_name_ci, backend/alembic/versions/006_add_skills_name_ci_unique_index.py] — the exact dedup + functional-index pattern this story's AC text explicitly says to mirror
- [Source: backend/app/employees/service.py] — existing `hash_password`/`verify_password` (Story 7.1)
- [Source: backend/app/auth/models.py::Account] — the row this story creates
- [Source: backend/app/assignments/repository.py::list_employees] — confirms AC4 needs no code change, only a test
- [Source: _bmad-output/C-UX-Scenarios/05-ritas-roster-management/05.2-create-employee/05.2-create-employee.md] — field list, required/optional split, duplicate-notice copy (UI layer; API error codes in this story are more granular per AC2's explicit wording)
- [Source: _bmad-output/E-Development/05-Ritas-Roster-Management-Prototype/05.1-Employees-Tab.html] — `generatePassword()` (lines ~474-477), the validated password alphabet/length this story's `generate_password()` mirrors
- [Source: _bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md#FR-24] — full FR text and Open Question 9 cross-reference

## Completion Checklist

- [x] `email-validator==2.3.0` declared explicitly in both requirements files
- [x] Migration 012 applied: case-insensitive unique index on `employees.email`
- [x] `CreateEmployeeRequest`/`EmployeeResponse`/`EmployeeCreatedResponse` schemas added
- [x] `get_employee_by_code`/`get_employee_by_email_ci`/`create_employee_with_account` repository functions added
- [x] `generate_password()` added (12-char, `secrets.choice`, documented alphabet)
- [x] `create_employee_service` added: HR-Admin-gated, both duplicate checks (exact + case-insensitive), IntegrityError race backstop, single-transaction Employee+Account write
- [x] `POST /api/admin/employees` mounted and working
- [x] All 4 ACs covered by passing tests, including the AC4 "immediately assignable" check
- [x] Full regression suite run, zero new regressions vs. baseline
- [x] Sprint status updated to `review` (then `done` after code review)

## Change Log

- 2026-09-11: Story created (`bmad-create-story`), building directly on Story 7.1's just-completed module foundation. Identified that the AC's "checked case-insensitively for Email" line requires a new migration (012) — Story 7.1's migration 011 never added this, since it only migrated schema, not create-time behavior. Flagged the `Account` cross-module write as a deliberate, AR-24-sanctioned AD-1 exception rather than an oversight, and confirmed AC4 needs no code change via `assignments/repository.py::list_employees`'s existing unscoped query. Status → `ready-for-dev`.
- 2026-09-11: Implementation complete (`bmad-dev-story`). All 7 tasks done: migration 012 applied and verified, `email-validator` declared, `employees/` module's schemas/repository/service/router filled in (first real endpoint for this module), `POST /api/admin/employees` mounted in `main.py`, and 15 new tests added (4 service + 11 router) covering all 4 ACs plus auth/validation edge cases. Full regression: 656 passed, 2 skipped, 0 failed — zero regressions against the 641-passed baseline. Status → `review`.
- 2026-09-11: Code review (`code-review` skill) found 4 issues, all patched: (1) bcrypt hashing blocked the async event loop synchronously — offloaded via `asyncio.to_thread`; (2) the `IntegrityError` backstop only checked `employees`, misattributing an `accounts`-side failure as a raw 500 — added an `accounts` check plus a regression test proving the fix; (3) two sequential duplicate-check queries combined into one; (4) inline `Account` construction in `employees/repository.py` replaced with a call to a new `auth.repository.create_account`, centralizing `Account`'s column shape in the module that owns it. Full regression re-verified: 657 passed, 2 skipped, 0 failed. Status → `done`.
