# Implementation Steps for Story 7-2: HR Admin Creates a New Employee Record

**Story Key:** 7-2-hr-admin-creates-a-new-employee-record
**Epic:** 7 (Employee Roster Management) — **second story**
**Status:** ✅ DONE
**Completed Date:** 2026-09-11

---

## Overview

Story 7.2 builds the first real Employee CRUD endpoint (`POST /api/admin/employees`, FR-24) directly on top of Story 7.1's foundation — the `employees/` module scaffold, the extended schema, and the `Account`-based credential mechanism resolved by AR-24. Creating an Employee means one transaction writing two rows: the `Employee` profile record and a matching `Account` row (`Account.id == Employee.id`) carrying a server-generated, bcrypt-hashed password — the first time anything in the codebase actually exercises the credential path Story 7.1 built but never used.

Two real gaps were found and closed during story creation, before any implementation code was written: `employees.email` only carried a case-sensitive unique constraint, but the acceptance criteria explicitly require case-insensitive duplicate detection (a new migration was needed, mirroring the identical fix Skills required in Story 6.2); and `email-validator` — required for Pydantic's `EmailStr` type — was installed in the venv but undeclared in either requirements file, the same class of gap Story 7.1 found with `bcrypt`.

Implementation went cleanly on the first pass — all 20 new tests passed without a red-phase failure needing a fix, and the full regression suite showed zero pre-existing breakage. The code review that followed found more: 4 real findings, two of them substantive (a blocking synchronous bcrypt call inside the async request handler, and an exception handler that would misattribute a rare but real failure mode as a raw 500 instead of a clean 409). All 4 were patched in the same session, with a new regression test specifically manufacturing the failure mode the second finding described.

---

## Agents Invoked

### 1. **Code Review Agent (`code-review` skill)**

**Purpose:** Adversarial review of the finished `POST /api/admin/employees` implementation.

**When Invoked:** User request: "code-review for Story7.2", after the story reached `review` status
**Model Capability:** Sonnet 5 (session model), forked background execution
**Input:** The complete `employees/service.py`/`repository.py`/`schemas.py`/`router.py` implementation, the new migration, and the story's own stated scope

**Key Findings Identified (4 items):**
- **[Med]** `create_employee_service` called `hash_password()` — bcrypt at its default cost factor, ~100–300ms — synchronously inside an `async def` route handler. On this single-process asyncio server, that blocks every other in-flight request (logins, dashboards, assignment reads) for the duration of every single Employee creation. The codebase already has a precedent for exactly this class of fix (`main.py`'s `await asyncio.to_thread(load_embedding_model)`), not applied here.
- **[Med]** The `IntegrityError` backstop only re-queried the `employees` table after a rollback. Since `create_employee_with_account` performs two separate flushes (Employee, then Account), a failure specifically on the *Account* insert — after the rollback undoes both — would leave both re-checks finding nothing, falling through to a bare `raise` and surfacing as an unhandled 500 instead of an attributable 409. Confirmed via direct code tracing that this branch had zero test coverage.
- **[Low]** Two sequential duplicate-check queries (`employee_code`, then `email`) on every create request — an avoidable extra round-trip.
- **[Low]** `Account(id=..., email=..., password_hash=..., role=...)` was constructed inline inside `employees/repository.py`, duplicating knowledge of a table `auth/` is documented to own — a future required-column change to `Account` would need remembering in two modules instead of one.

**Output:** 4 findings, JSON-formatted with file/line/failure-scenario detail for each. The main session independently re-traced the code for finding #2 (the narrower, more consequential one) before accepting it, confirming the exact conditions under which it could occur (a hypothetical future Employee-edit story letting `Account.email` and `Employee.email` drift apart) and that it was real, if currently narrow in scope.

---

## Skills Invoked

### 1. **`/bmad-create-story` (story creation)**

**Purpose:** Ground Story 7.2 in Story 7.1's just-completed foundation and the real current source of the module it extends (`skills/`'s create-endpoint pattern), then produce a comprehensive story file.

**When Invoked:** Explicit user instruction, immediately after Story 7.1's code review completed
**Workflow Steps Executed:**
1. Read Epic 7's Story 7.2 AC text from `epics.md`, the PRD's FR-24 section, and the UX scenario/prototype (`05.2-create-employee.md`, the working HTML mock's `generatePassword()` function) for the exact field list and password-generation shape to match.
2. Read `skills/router.py`, `skills/service.py`, `skills/repository.py`, and `skills/schemas.py` in full — the direct pattern precedent for a create-endpoint's dedup-check-then-insert-with-IntegrityError-backstop shape, including migration `006`'s case-insensitive functional index fix.
3. Read `employees/service.py` (Story 7.1's `hash_password`/`verify_password`), `auth/models.py::Account`, and `auth/service.py::require_hr_admin`/`get_current_user` to confirm exactly what already existed to build on.
4. **Found a real gap during authoring:** `employees.email` only had a case-sensitive unique constraint, but the AC's literal wording ("checked case-insensitively for Email, matching FR-20's Skill-name dedup pattern") requires the same fix Skills needed — added Task 1 for a new migration (012) before any code was written.
5. **Found a second gap:** verified directly (`pip show email-validator`) that `email-validator==2.3.0` was already installed in the venv but declared in neither requirements file — the same undeclared-dependency class Story 7.1 found with `bcrypt` — added as an explicit task rather than discovering it mid-implementation.
6. Wrote 7 Scope Notes covering: the router-mounting responsibility, reuse of Story 7.1's hashing helper, the two-writes-one-transaction requirement, the explicit `authenticate()`-still-not-wired scope boundary, the two-different-case-sensitivities-by-design distinction between `employee_code` and `email` dedup, the archived-rows-included dedup scope, and confirmation that the Assignment Flow's employee picker needs no code change.
7. Set Status to `ready-for-dev`; `sprint-status.yaml`'s `7-2-...` entry updated from `backlog` to `ready-for-dev`.

**Output File:** `_bmad-output/implementation-artifacts/7-2-hr-admin-creates-a-new-employee-record.md`
**Sprint Status:** `7-2-...`: `backlog` → `ready-for-dev`

---

### 2. **`/bmad-dev-story` (implementation)**

**Purpose:** Execute the story's 7 tasks in strict sequence.

**When Invoked:** User instruction: "proceed"
**Workflow Steps Executed:**

1. **Task 1 — Migration 012:** added a case-insensitive functional unique index on `employees.email` (`CREATE UNIQUE INDEX ix_employees_email_lower ON employees (lower(email))`), mirroring migration `006`'s identical fix for `skills.name`. Applied live via `alembic upgrade head` and verified directly via a `pg_indexes` query.
2. **Task 2 — Schemas:** `CreateEmployeeRequest` (3 required + non-blank fields, 8 optional, `EmailStr` for the login identity, `extra="forbid"`), `EmployeeResponse` (all Employee columns, never a password field), `EmployeeCreatedResponse` (extends `EmployeeResponse` with the one-time `generated_password`). `email-validator==2.3.0` added explicitly to both requirements files and installed into the venv.
3. **Task 3 — Repository:** `get_employee_by_code` (exact match), `get_employee_by_email_ci` (case-insensitive, mirroring `skills/repository.py::get_skill_by_name_ci`), and `create_employee_with_account` — a single function performing both the `Employee` insert and the `Account` insert so no caller could leave either row orphaned.
4. **Task 4 — Password generation:** `generate_password()` — 12 characters via `secrets.choice` (not `random`) over an alphabet excluding visually-ambiguous characters, matching the already-validated UX prototype's `generatePassword()` exactly.
5. **Task 5 — Service:** `create_employee_service` — `require_hr_admin` gate first, then the exact-match `employee_code` check, then the case-insensitive `email` check, then generate+hash the password, then the combined insert, wrapped in an `IntegrityError` race backstop mirroring `skills/service.py::create_skill_service`'s exact shape.
6. **Task 6 — Router:** `POST ""` → `create_employee_route`, `response_model=EmployeeCreatedResponse`, `status_code=201` — the first mounted endpoint for this module. Mounted in `main.py` at `/api/admin/employees`, directly after `skills_router`'s mount line.
7. **Task 7 — Tests:** 4 new tests extending `test_employees_service.py` (`generate_password()` length, alphabet membership, ambiguous-character exclusion, 20-call uniqueness) and a new `test_employees_router.py` with 11 tests covering all 4 ACs plus 403/401/422 edge cases. **All 20 new tests passed on the first run** — no red-phase failure needed fixing, credited to the story's detailed Scope Notes matching `skills/`'s exact patterns closely enough that the implementation matched the tests' expectations immediately.
8. Full regression: **656 passed, 2 skipped, 0 failed** — a clean +15 over the 641-passed baseline (4 service + 11 router tests), confirming zero pre-existing tests were affected by the new unique index or the two new tables touched by the new endpoint. `app.main` verified to still import cleanly with the new router mounted (15 routes).
9. Filled in the story file's Dev Agent Record, File List, Completion Checklist, and Change Log; Status → `review`.

**Output File:** `_bmad-output/implementation-artifacts/7-2-hr-admin-creates-a-new-employee-record.md`
**Sprint Status:** `7-2-...`: `ready-for-dev` → `in-progress` → `review`

---

### 3. **`code-review` (final review + patch application)**

**Purpose:** Independent adversarial verification of the finished implementation, followed by fixing everything the review found.

**When Invoked:** User request: "code-review for Story7.2"
**Workflow Steps Executed:**

- Ran the review (see **Agents Invoked** above) — 4 findings returned.
- Main session independently verified each finding against the actual code before acting: confirmed finding #2's exact trigger conditions by tracing `create_employee_with_account`'s two-flush structure and the backstop's re-check logic; confirmed finding #4 was a legitimate, if minor, architecture point rather than the codebase's own established precedent.
- Presented all 4 findings to the user, triaged by severity, with a recommendation to fix the two medium-severity ones. **User chose to fix all four.**

**Patches Applied (all TDD — implemented, then re-verified GREEN):**
1. **Blocking bcrypt call:** `create_employee_service` now calls `await asyncio.to_thread(hash_password, plaintext_password)` instead of calling it directly, mirroring `main.py`'s existing `asyncio.to_thread(load_embedding_model)` precedent. No new test needed — this is a scheduling change, not a behavior change; existing tests still cover correctness.
2. **`IntegrityError` misattribution:** added `auth.repository.get_account_by_email_ci` and a check against it in the backstop, after the `employees`-side re-checks and before the final bare `raise`. **New regression test** (`test_create_employee_account_side_email_conflict_returns_409_not_500`) manufactures the exact failure mode by creating Employee A normally, then directly mutating its paired `Account`'s email in the database to simulate a future edit-story's desync, then attempting to create Employee B with that now-stale email — asserting a clean 409 `EMPLOYEE_EMAIL_CONFLICT`, not a 500, and confirming no orphaned Employee B row was left behind.
3. **Redundant queries:** added `get_employee_by_code_or_email_ci` — a single `OR`-based query returning `(matched_by_code, matched_by_email)` — replacing both the pre-check and the post-rollback backstop's two separate queries.
4. **Inline `Account` construction:** added `auth.repository.create_account(db, *, id, email, password_hash, role)` as the new, sole write path into `accounts` from another module; `employees/repository.py::create_employee_with_account` now calls it instead of constructing the `Account` row itself. `employees/repository.py` no longer imports `Account` directly.

**Output:** All 4 patches applied; full regression re-verified at **657 passed, 2 skipped, 0 failed** (656-passed post-implementation baseline + 1 new regression test); `app.main` re-verified to import cleanly (15 routes). Story status → `done`; `sprint-status.yaml` updated to match.

**Documentation Generated:**
- A new "Senior Developer Review (AI)" section added directly to the story file, with all 4 action items marked `[x]` and their exact fix described
- File List and Change Log updated to reflect every file the patches touched
- Sprint status synced (`7-2-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done`)

---

## Files Created/Updated

### Backend — New Files

| File | Purpose |
|------|---------|
| `backend/alembic/versions/012_add_employees_email_ci_unique_index.py` | Case-insensitive functional unique index on `employees.email`, mirroring migration 006's identical fix for `skills.name` |
| `backend/tests/test_employees_router.py` | 12 tests (11 initial + 1 code-review regression test) for `POST /api/admin/employees` |

### Backend — Modified Files

| File | Purpose |
|------|---------|
| `backend/app/employees/schemas.py` | `CreateEmployeeRequest`, `EmployeeResponse`, `EmployeeCreatedResponse` added |
| `backend/app/employees/repository.py` | `get_employee_by_code`, `get_employee_by_email_ci`, `get_employee_by_code_or_email_ci` (code review), `create_employee_with_account` added; post-review, delegates `Account` construction to `auth_repository.create_account` instead of inlining it |
| `backend/app/employees/service.py` | `generate_password`, `_code_conflict`/`_email_conflict`, `create_employee_service` added; post-review: bcrypt hashing offloaded via `asyncio.to_thread`, duplicate checks switched to the combined query, `IntegrityError` backstop extended to also check `accounts` |
| `backend/app/employees/router.py` | `POST ""` → `create_employee_route` — first mounted endpoint for this module |
| `backend/app/main.py` | `employees_router` imported and mounted at `/api/admin/employees` |
| `backend/app/auth/repository.py` | Code review: added `get_account_by_email_ci` and `create_account` — the new sole write path into `accounts` from another module |
| `backend/requirements.txt`, `backend/requirements-prod.txt` | Added `email-validator==2.3.0` |
| `backend/tests/test_employees_service.py` | 4 new tests for `generate_password()` |

### Not Changed (by design)

- `backend/app/auth/repository.py::authenticate()` / `_MOCK_ACCOUNTS` — still doesn't read `Account`; a newly-created Employee's password is correctly generated, hashed, and stored, but not yet usable to log in (Story 7.1's deliberately-deferred gap, unaffected by this story)
- `backend/app/assignments/repository.py::list_employees` — AC4 ("immediately assignable") verified via a new test; no code change needed since this query was already unscoped

### Documentation & Configuration Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/7-2-hr-admin-creates-a-new-employee-record.md` | Story file — ACs, 7 Scope Notes, Dev Notes, Dev Agent Record, Senior Developer Review section |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `7-2-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done` |
| `documentation/ImplementationStepsForStory7-2.md` | This file |

---

## Implementation Workflow Summary

### Phase 1: Story Creation
**Skill:** `/bmad-create-story`
- Read `skills/`'s complete create-endpoint pattern (router/service/repository/schemas + migration 006) as the direct precedent this story's AC text explicitly cites
- Found two real gaps before writing any code: `employees.email`'s case-sensitivity mismatch against the AC's literal wording, and an undeclared `email-validator` dependency — both scoped as explicit tasks rather than discovered mid-implementation

### Phase 2: Implementation
**Skill:** `/bmad-dev-story`
- 7 tasks executed in sequence: migration → schemas → repository → password generation → service → router/mounting → tests
- All 20 new tests passed on the first run, with zero red-phase failures needing a fix
- Full regression: 656 passed, 2 skipped, 0 failed — a clean +15 over the 641-passed baseline
- Story marked `review`

### Phase 3: Code Review + Patches
**Skill:** `code-review`
- Single adversarial pass found 4 real findings — 2 medium (a blocking synchronous bcrypt call, and an exception-handling gap with zero test coverage), 2 low (a redundant query pair, and an architecture-boundary nit)
- User chose to fix all four rather than defer any
- One new regression test specifically manufactures the medium-severity exception-handling gap's exact failure mode and proves the fix
- Full regression re-verified: 657 passed, 2 skipped, 0 failed
- Story marked `done`

---

## Test Coverage

### New/Extended Test Files (21 tests total from this story, post-review)

- `test_employees_service.py` — 4 new: `generate_password()` length, alphabet membership, ambiguous-character exclusion, 20-call uniqueness
- `test_employees_router.py` — 12 new (11 initial + 1 code-review patch): AC1 (201, matching `Account` row, password verifies), AC2 (duplicate `employee_code` → 409; duplicate email including different-case → 409), AC3 (all 8 optional fields null when omitted), AC4 (immediately visible via `assignments.repository.list_employees`), 403 (EMPLOYEE session), 401 (unauthenticated), 422 (missing required field / blank name / invalid email / unknown field), and the code-review regression test for an `accounts`-side conflict

### Regression Verification

- Full backend suite run after implementation (656 passed, 2 skipped, 0 failed — exact +15 over the 641-passed baseline) and again after the 4 code-review patches (657 passed, 2 skipped, 0 failed — the +1 being the new regression test)
- Zero failures at either stage — no fixing-a-fix cycle needed
- `app.main` explicitly re-verified to import cleanly (15 routes) both after implementation and after the patches, checking for any circular-import risk the new `auth.repository.create_account`/`get_account_by_email_ci` cross-module calls could have introduced
- Migration 012 applied live and independently verified via a direct `pg_indexes` query rather than trusting the migration script alone

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **AR-24, first real use**: `Account` created alongside every new `Employee` | `create_employee_with_account` performs both inserts in one function/transaction, `Account.id` set equal to the new `Employee.id` | `employees/repository.py` |
| **AD-1 exception, deliberate and narrowed further by code review** | The cross-module write into `accounts` was initially inlined in `employees/repository.py`; code review centralized the actual row construction into `auth.repository.create_account`, so `employees/` only decides *when* to call it, not *how* the row is shaped | `auth/repository.py`, `employees/repository.py` |
| **Case-insensitive dedup matching FR-20's Skill-name pattern** | New migration 012, mirroring migration 006's identical `lower(email)`/`lower(name)` functional-index fix | `alembic/versions/012_...py`, `employees/repository.py` |
| **Blocking work must not run on the event loop (established by `main.py`'s existing precedent, applied here by code review)** | `hash_password()` now called via `await asyncio.to_thread(...)` inside the async request handler | `employees/service.py` |

---

## Key Technical Achievements

✅ **Found two real gaps during story creation, before any code was written** — the `employees.email` case-sensitivity mismatch against the AC's literal wording, and an undeclared `email-validator` dependency (verified directly with `pip show`, not assumed) — both scoped as explicit tasks rather than discovered mid-implementation
✅ **All 20 new tests passed on the first run** — a direct result of the story's Scope Notes matching `skills/`'s established create-endpoint pattern closely enough (dedup shape, conflict response shape, IntegrityError backstop shape) that the implementation and the tests agreed from the start
✅ **Code review found a real exception-handling gap with zero prior test coverage** — an `accounts`-side insert failure would have surfaced as an unattributed 500 instead of a clean 409, a scenario narrow enough (requires a future Employee-edit story to first let the two tables' emails drift apart) that it was easy to miss, but real and worth fixing now rather than discovering it in production after that future story ships
✅ **The regression test for that gap manufactures the exact failure condition directly**, rather than mocking the database layer — creating a real Employee, directly desyncing its paired `Account`'s email, then proving the API responds correctly, giving high confidence the fix actually works end-to-end
✅ **Correctly applied an existing codebase precedent instead of inventing a new one** — `asyncio.to_thread` for the blocking bcrypt call mirrors `main.py`'s own established pattern for the embedding-model load, rather than introducing a different offloading mechanism
✅ **Zero regressions across both full-suite runs** — 656 passed after implementation, 657 passed after all 4 patches, with the single test-count difference being exactly the one new regression test added

---

## Deferred Items (Not Story 7-2 Scope)

None from this story's code review — all 4 findings were fixed rather than deferred. Carried forward from Story 7.1 as still-open, unaffected by this story:

1. **`auth/repository.py::authenticate()` still does not read `Account`.** A newly-created Employee's password is correctly generated, hashed, and stored, but not yet usable to log in — remains a real, currently-unassigned gap for a future story.

---

## Conclusion

Story 7-2 is **✅ DONE** after a create-then-implement-then-review-and-patch cycle:

- All 4 acceptance criteria satisfied, verified by 12 dedicated router-level tests
- Two real gaps (case-insensitive email dedup, undeclared `email-validator`) found and closed during story creation rather than mid-implementation
- Clean first-pass implementation — 20 new tests, zero red-phase failures
- Code review found 4 real issues (2 medium, 2 low); all 4 patched in the same session rather than deferred, including a new regression test proving the more subtle exception-handling fix actually works
- Zero regressions across both the implementation and patch-verification regression runs
- One gap deliberately carried forward from Story 7.1 and clearly documented (`authenticate()` still doesn't read `Account`) rather than silently left for a future story to rediscover

**Epic 7 status:** Stories 7.1 and 7.2 are both `done`. Story 7.3 (HR Admin Views the Employee Roster) is next in the backlog.
