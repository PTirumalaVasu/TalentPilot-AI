# Implementation Steps for Story 7-1: `employees/` Module Foundation — Schema Migration & Credential Reconciliation

**Story Key:** 7-1-employees-module-foundation-schema-migration-and-credential-reconciliation
**Epic:** 7 (Employee Roster Management) — **first story**
**Status:** ✅ DONE
**Completed Date:** 2026-09-11

---

## Overview

Story 7.1 is Epic 7's foundational story: before any Employee CRUD endpoint can be built (Stories 7.2–7.7), the codebase needed a real owning module for the `employees` table, a schema extended with the new profile fields Employee Roster Management requires, and — the hardest part — an actual decision about where Employee login credentials live. The PRD's own addendum had flagged an existing-but-unused `Account` model in `backend/app/auth/models.py` as a likely target, but left the decision open (AR-24, PRD Open Question 18).

The work mirrored Story 6.1's exact precedent (`Skill`'s extraction into its own `skills/` module) almost step for step: physically relocate the `Employee` ORM class out of `assignments/models.py` into a new `employees/` module, register it back via whole-module imports in both directions, extend the table with 11 new columns via a migration, and add unit/schema tests.

The one genuine discovery — found only by reading the actual seed code rather than trusting its own comments — resolved AR-24 unambiguously: `core/seeds.py::create_default_accounts()` already seeds `Account` rows using the *same UUIDs* as the corresponding `Employee` rows. That match is not accidental; it is the codebase's own half-finished intent to use `Account` as the real credential store. But a second, more consequential discovery followed close behind: an independent review subagent, running the story-creation workflow's own quality-gate checklist, verified by direct `bcrypt.checkpw()` execution that the seeded `password_hash` values — despite a comment claiming `# bcrypt("demo123")` — **do not actually validate against `"demo123"`**. They were shape-valid placeholders, not real hashes. Had this shipped unnoticed, Employee login would have silently broken the instant a future story wired `authenticate()` to read from `Account`. The story was rewritten around that finding before a single line of implementation code was written.

---

## Agents Invoked

### 1. **Independent Story Quality Review Subagent**

**Purpose:** Fresh-context adversarial review of the newly-drafted story file, per `bmad-create-story`'s own `checklist.md` process — verify every technical claim against the actual source rather than trusting the previous draft's assertions.

**When Invoked:** Immediately after the first draft of the story file was written, before any implementation began
**Model Capability:** Sonnet 5 (session model), background subagent with no memory of the drafting session
**Input:** The draft story file plus direct access to re-read `backend/app/auth/models.py`, `auth/repository.py`, and `core/seeds.py::create_default_accounts`

**Key Findings Identified:**
- **The critical one:** the draft's claim that the seeded `Account.password_hash` values were "real bcrypt hashes of `demo123`, already computed and stored" was **false** — verified by directly executing `bcrypt.checkpw(b"demo123", stored_hash)`, which returned `False`. The stored value has valid bcrypt *shape* only (`$2b$12$...`), not a working hash — and the seed code's own comment two lines above it ("For now, use a simple mock hash") was the honest tell the first draft had missed in favor of a more confident-sounding comment elsewhere in the same function.
- The story as drafted would have shipped with a false "nothing left to do here" assumption about Open Question 17's credential half, blocking nothing today but silently breaking Employee login the moment any future story wired `authenticate()` to `Account`.

**Output:** A single decisive finding that reshaped the story before implementation: a new Scope Note (4), a new Acceptance Criterion, a new Task (4a — re-seed real hashes), a corrected Dev Note ("Why bcrypt, not argon2"), and a permanent regression-guard test requirement pinning the exact bad hash value so it could never silently reappear. The main session independently re-verified the same `bcrypt.checkpw()` call before accepting the finding.

---

### 2. **Code Review Agent (`code-review` skill)**

**Purpose:** Adversarial review of the finished implementation's diff, run after the story reached `review` status.

**When Invoked:** User request: "code-review", immediately after Story 7.1's implementation was marked `review`
**Model Capability:** Sonnet 5 (session model), forked background execution
**Input:** The working-tree diff (`git diff HEAD` plus new untracked files) covering the entire `employees/` module, the migration, and every modified `assignments/`/`auth/`/`core/` file and test

**Key Findings Identified:** None survived scrutiny — reported as a clean pass (`[]`). The agent specifically checked and ruled out three plausible failure modes rather than skimming past them:
- The three-way circular whole-module import (`assignments.models` ↔ `employees.models` ↔ `skills.models`) — verified safe via Python's `sys.modules` caching plus SQLAlchemy's lazy string-based relationship resolution, matching an already-working, previously-reviewed pattern from Story 6.1.
- Migration ordering — confirmed the `employee_code` backfill → `NOT NULL`/`UNIQUE` constraint → `accounts.id` FK sequence requires `employees` rows to pre-date `accounts` rows, and confirmed `seed_employees()` does in fact run before `create_default_accounts()`.
- No leftover imports of `Employee` from the old `app.assignments.models` location anywhere in app code; the placeholder-bcrypt-hash data-fix in the migration is scoped to the exact known placeholder string, not a blanket rewrite.

**Output:** Zero findings. Story approved for `done` status without any follow-up patches.

---

## Skills Invoked

### 1. **`/bmad-create-story` (story creation)**

**Purpose:** Ground Story 7.1 in the real epics/PRD/architecture text and the actual current source code, then produce a comprehensive story file for implementation.

**When Invoked:** Explicit user instruction: "bmad-create-story for Story 7.1."
**Workflow Steps Executed:**
1. Loaded Epic 7's Story 7.1 text from `epics.md`, the PRD's addendum ("Employee Roster Management — Architecture Handoff Notes"), and Story 6.1's own story file as the direct pattern precedent.
2. Read `backend/app/assignments/models.py::Employee` in full (confirming exactly 5 existing relationships that must keep resolving after relocation), `backend/app/auth/models.py::Account`, `auth/repository.py::_MOCK_ACCOUNTS`/`find_account`, and `core/seeds.py::create_default_accounts()` — the exhaustive analysis step that surfaced the `Account.id == Employee.id` UUID-matching discovery resolving AR-24.
3. Wrote the story with 5 Scope Notes covering: the Story 6.1 mirror-pattern instruction, the relationship-preservation requirement, the AR-24 resolution and its evidence, the (at that point still believed) real seeded hashes, and the explicit "this story does not wire `authenticate()`" scope boundary.
4. Dispatched the independent quality review subagent (above), which found the seeded-hash claim was false — triggered a full rewrite of Scope Note 4, a new AC, Task 4a, the "Why bcrypt" Dev Note, and the Change Log before the story was considered ready.
5. Set Status to `ready-for-dev`; `sprint-status.yaml`'s `7-1-...` entry updated from `backlog` to `ready-for-dev`.

**Output File:** `_bmad-output/implementation-artifacts/7-1-employees-module-foundation-schema-migration-and-credential-reconciliation.md`
**Sprint Status:** `7-1-...`: `backlog` → `ready-for-dev`

---

### 2. **`/bmad-dev-story` (implementation)**

**Purpose:** Execute the story's 8 tasks end-to-end, TDD-style, without pausing for milestone check-ins.

**When Invoked:** User instruction: "continue" (following story creation)
**Workflow Steps Executed:**

1. **Task 1 — Module scaffolding:** created `backend/app/employees/__init__.py`, `models.py`, `repository.py`, `service.py`, `schemas.py`, `router.py`. `repository.py`/`schemas.py`/`router.py` left as documented stubs (Stories 7.2–7.6 fill these in); `router.py` deliberately not mounted in `main.py` yet, since this story adds no endpoints.
2. **Task 2 — Model relocation:** moved `class Employee` out of `assignments/models.py` into `employees/models.py`, preserving all 5 relationships. Registered the class back into `assignments/models.py` via a whole-module `import app.employees.models` (not a `from ... import Employee` re-export) — deliberately using the correct form from the start, learning directly from Story 6.1's own code review finding that a one-way re-export defeats the point of a relocation.
3. **Task 3 — Migration 011:** added all 11 new columns (`employee_code`, `phone`, `experience`, `technologies`, `position`, `project`, `manager_name`, `location`, `department`, `updated_at`, `archived_at`), backfilled `employee_code` for the 5 existing seeded rows (`EMP-0001`–`EMP-0005`, ordered by `core/seed_ids.py`'s declared UUID constants rather than `created_at`, which isn't guaranteed distinct across one bulk insert), then applied the `NOT NULL`/`UNIQUE` constraint. Applied live via `alembic upgrade head` against the local dev Postgres and verified column/constraint state via direct SQL queries.
4. **Task 4 — AR-24 resolution:** added the `accounts_id_fkey` FK (`accounts.id` → `employees.id`) in the same migration, rewrote `Account`'s docstring to state its resolved role, and — after the review subagent's finding — added **Task 4a**: a one-time migration data-fix replacing the exact known-bad placeholder hash with a real `bcrypt.hashpw` output for any pre-existing `accounts` rows, plus updating `create_default_accounts()` to call the new `hash_password()` helper for any future fresh-DB seed run. Verified live with `bcrypt.checkpw(b"demo123", ...)` returning `True` for all 5 accounts afterward.
5. **Task 5 — Password hashing utility:** `employees/service.py::hash_password`/`verify_password` (bcrypt), unit-tested.
6. **Task 6 — Import site remediation:** an initial single-line regex search for `from app.assignments.models import Employee` found 9 call sites and fixed them. A **follow-up multi-line-import-aware search** (`grep -Pzo` across parenthesized import blocks) caught 2 more the first pass had missed (`conftest.py`, `test_schema_definition.py`) — both fixed the same way. `test_provenance_detail.py`'s 3 `Employee(...)` calls were checked and confirmed to be non-persisted in-memory objects, correctly left untouched rather than over-fixed.
7. **Task 7 — Schema tests:** 4 new tests added to `test_schema_definition.py` (`employee_code` required/unique, `department` distinct from `group`, `archived_at` nullable soft-delete, `accounts.id` FK) using the file's own established pure-ORM `class_mapper` style — an earlier draft had used a live-DB inspector pattern instead and was corrected to match convention. A new `test_employees_service.py` added 5 tests for the hashing helper, including a permanent regression guard pinning the exact bad placeholder hash the review subagent found.
8. **Task 8 — Full regression pass:** first run surfaced 5 failures — 4 were `NotNullViolationError`s from ad hoc `Employee(...)` test fixtures missing the new required `employee_code` (fixed by adding one to each), and the 5th (`test_assignments_repository.py::test_find_existing_assignment_returns_empty_when_no_match`) was a stray, unrelated pre-existing `Assignment` row left over in the shared dev database from an earlier session — confirmed pre-existing via the project's established `git stash push -u -- backend/` → re-run → `git stash pop` verification method, then cleaned up directly. Final suite: **641 passed, 2 skipped, 0 failed**. Rebuilt and restarted the `talentpilot-api` Docker container (no live volume mount in this compose file) and confirmed via live `curl` that both an HR_ADMIN and an EMPLOYEE mock login still succeed unchanged.
9. One self-caught implementation slip: an early draft of `employees/models.py` contained a leftover, nonsensical `Column(uuid.UUID if False else __import__("sqlalchemy").UUID(as_uuid=True), ...)` expression from mid-edit drafting — caught on re-read before running anything, fixed to a plain `Column(UUID(as_uuid=True), ...)`.
10. Filled in the story file's Dev Agent Record (Debug Log, Completion Notes, Test Results), File List, Completion Checklist, and a final Change Log entry; Status → `review`.

**Output File:** `_bmad-output/implementation-artifacts/7-1-employees-module-foundation-schema-migration-and-credential-reconciliation.md`
**Sprint Status:** `7-1-...`: `ready-for-dev` → `in-progress` → `review`

---

### 3. **`code-review` (final review)**

**Purpose:** Independent adversarial verification of the finished diff.

**When Invoked:** User request: "code-review"
**Workflow Steps Executed:** Reviewed the full working-tree diff against the story's own stated scope, specifically checking the three highest-risk areas by name (circular imports, migration ordering, leftover old-path imports) rather than a generic pass. See **Agents Invoked** above for detail.

**Output:** Zero findings. Status → `done`; `sprint-status.yaml`'s `7-1-...` entry updated from `review` to `done`.

---

## Files Created/Updated

### Backend — New Files

| File | Purpose |
|------|---------|
| `backend/app/employees/__init__.py` | Module init |
| `backend/app/employees/models.py` | `Employee` ORM, relocated from `assignments/models.py`, plus 11 new columns |
| `backend/app/employees/repository.py` | Documented stub (Stories 7.2–7.6 add real queries) |
| `backend/app/employees/service.py` | `hash_password`/`verify_password` (bcrypt) — the one non-stub file in this scaffold |
| `backend/app/employees/schemas.py` | Documented stub |
| `backend/app/employees/router.py` | Documented stub, deliberately unmounted |
| `backend/alembic/versions/011_add_employee_profile_fields.py` | The 11-column migration, `employee_code` backfill, `accounts_id_fkey`, and the placeholder-hash data-fix |
| `backend/tests/test_employees_service.py` | 5 tests for the hashing helper, including the bad-placeholder-hash regression guard |

### Backend — Modified Files

| File | Purpose |
|------|---------|
| `backend/app/assignments/models.py` | `Employee` class removed; registers `app.employees.models` (and `app.skills.models`) via whole-module imports |
| `backend/app/assignments/repository.py` | `Employee` import repointed to `app.employees.models` |
| `backend/app/auth/models.py` | `Account.id` gains an explicit FK to `employees.id`; docstring rewritten to state its resolved AR-24 role |
| `backend/app/core/seeds.py` | `Employee` import repointed; `seed_employees()` assigns `employee_code` to all 5 rows; `create_default_accounts()` calls `hash_password()` instead of a hardcoded placeholder |
| `backend/requirements.txt`, `backend/requirements-prod.txt` | Added `bcrypt==5.0.0` (previously an undeclared dependency) |
| `backend/tests/conftest.py` | `Employee` import repointed (multi-line import block, caught by the follow-up search) |
| `backend/tests/test_schema_definition.py` | `Employee` import repointed; 4 new schema tests added |
| `backend/tests/test_admin_api_keys_router.py`, `test_antiflow_validation.py`, `test_override_endpoint.py`, `test_position_retrieval.py`, `test_seed_employee_identity_alignment.py` | `Employee` import repointed |
| `backend/tests/test_admin_api_keys_router.py`, `test_override_endpoint.py` | Ad hoc `Employee(...)` fixtures gained a required `employee_code` |
| `backend/tests/test_db.py` | `Employee` import repointed; both ad hoc `Employee(...)` calls gained a required `employee_code` |

### Not Changed (by design)

- `backend/app/auth/repository.py::authenticate()` / `_MOCK_ACCOUNTS` — explicitly out of this story's scope; both HR_ADMIN and EMPLOYEE login verified unchanged via live `curl`
- `backend/app/main.py` — `employees` router not mounted; no endpoints exist yet
- `backend/tests/test_provenance_detail.py` — its 3 `Employee(...)` calls are non-persisted in-memory objects; verified passing unchanged, correctly left alone

### Documentation & Configuration Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/7-1-employees-module-foundation-schema-migration-and-credential-reconciliation.md` | Story file — ACs, 5 Scope Notes, Dev Notes, Dev Agent Record, Completion Checklist |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `7-1-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done` |
| `documentation/ImplementationStepsForStory7-1.md` | This file |

---

## Implementation Workflow Summary

### Phase 1: Story Creation
**Skill:** `/bmad-create-story`
- Exhaustive read of the actual current `auth/models.py`, `auth/repository.py`, and `core/seeds.py` source — not just the epics/PRD text — surfaced the `Account.id == Employee.id` UUID-matching discovery that resolves AR-24 unambiguously
- Independent quality review subagent caught a real, consequential factual error before any code was written: the seeded password hashes don't actually work
- Story rewritten around that finding: new Scope Note, new AC, new Task 4a, corrected Dev Note, regression-guard test requirement

### Phase 2: Implementation
**Skill:** `/bmad-dev-story`
- 8 tasks executed in strict sequence: module scaffolding → model relocation → schema migration → AR-24 FK + credential re-seed → hashing utility → import-site remediation (2 sites found only via a second, more careful search) → schema tests → full regression
- One self-caught syntax mistake fixed before it was ever run
- Full regression pass found and fixed 4 real (if narrow) test breaks plus 1 confirmed-unrelated pre-existing failure, verified via `git stash`
- Live Docker verification that neither HR_ADMIN nor EMPLOYEE login regressed
- Story marked `review`

### Phase 3: Code Review
**Skill:** `code-review`
- Single adversarial pass, specifically targeting the three highest-risk areas this kind of relocation-plus-migration story creates (circular imports, migration ordering, leftover old-path imports)
- Zero findings — all three risk areas verified safe rather than assumed safe
- Story marked `done`

---

## Test Coverage

### New/Extended Test Files (9 new tests from this story)

- `test_employees_service.py` — 5 new: bcrypt hash production, correct-password acceptance, incorrect-password rejection, salted non-determinism, and a permanent regression guard pinning the exact bad placeholder hash found during story creation
- `test_schema_definition.py` — 4 new: `employee_code` required/unique, `department` distinct from `group`, `archived_at` nullable soft-delete flag, `accounts.id` FK to `employees.id`

### Regression Verification

- Full backend suite run after implementation: **641 passed, 2 skipped, 0 failed** — up from an initial run of 636 passed / 5 failed / 2 skipped, with every failure triaged individually rather than blanket-fixed
- 4 of the 5 initial failures were the same root cause (new `employee_code` NOT NULL constraint hitting ad hoc test fixtures) and fixed the same way
- The 5th was confirmed pre-existing and unrelated via `git stash push -u -- backend/` → re-run against the reverted baseline (same failure reproduced) → `git stash pop` — then cleaned up by deleting the stray row directly, matching this project's own established precedent for this exact situation
- Live-verified via `curl` against a rebuilt, restarted `talentpilot-api` Docker container: both an HR_ADMIN and an EMPLOYEE mock login succeed unchanged

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **AD-1: single-owner data modules** | `employees` gains a real owning module, mirroring AD-11's precedent for `skills/` | `employees/models.py`, `assignments/models.py` |
| **AR-24 (new, this story): Employee credential storage** | Resolved in favor of extending the existing-but-unused `Account` model (formalizing `accounts.id == employees.id` via a real FK) rather than adding a password column to `Employee` — the seed data already implicitly committed to this shape | `auth/models.py`, migration 011 |
| **Whole-module-import-both-directions (learned from Story 6.1's code review)** | `assignments/models.py` registers `Employee` via `import app.employees.models` (not a re-export); `employees/models.py` registers back via `import app.assignments.models` — done correctly from the start, avoiding a second review-and-fix cycle | `assignments/models.py`, `employees/models.py` |
| **bcrypt, not argon2, for password hashing** | Matches the format (`$2b$...`) already present in the seed data, avoiding two hashing schemes in one table with no algorithm-tag column | `employees/service.py` |

---

## Key Technical Achievements

✅ **Found and correctly resolved AR-24 by reading the actual seed code, not the planning documents** — the `Account.id == Employee.id` UUID match in `create_default_accounts()` was the deciding evidence, not a guess
✅ **An independent review subagent caught a real, consequential bug before any implementation code existed** — the seeded password hashes looked complete (correct bcrypt shape, a confident-sounding comment) but did not actually work; verified by directly executing `bcrypt.checkpw()` rather than trusting either the code's comment or the first draft's claim
✅ **Learned directly from Story 6.1's own code review finding instead of repeating it** — the whole-module-import-both-directions pattern was used from the very first draft of `employees/models.py`, with no naive-then-fixed cycle needed this time
✅ **A second, more careful search caught what the first one missed** — the initial single-line regex for the old import path found 9 of 11 real call sites; a deliberate follow-up multi-line-aware search found the remaining 2 before they could become a shipped gap
✅ **Correctly distinguished a real regression from a pre-existing, unrelated failure** — 4 of 5 initial test failures were genuinely caused by this story's new constraint and fixed; the 5th was proven pre-existing via `git stash` rather than assumed and blanket-patched
✅ **Zero findings on the final code review** — specifically because the review targeted the three highest-risk areas this exact kind of change creates (circular imports, migration ordering, leftover old-path imports) and verified each directly rather than skimming
✅ **This story deliberately ships incomplete on one axis, and says so plainly** — `authenticate()` still does not read `Account`; a new Employee's password will be correctly hashed and stored but unusable to log in until a future story wires that path, flagged prominently in Dev Notes rather than silently discovered later

---

## Deferred Items (Not Story 7-1 Scope)

Not logged to `deferred-work.md` (no code review findings this story), but explicitly flagged in the story's own Dev Notes as forward guidance for whoever picks up Story 7.2:

1. **`auth/repository.py::authenticate()` does not read `Account`.** No Epic 7 story, as currently authored, has an AC that says to wire this up. The story's Dev Notes recommend this become part of Story 7.2's real scope — inserting an Employee record with a hashed, unusable password is not the same as making that Employee able to log in.
2. **`ARCHITECTURE-SPINE.md` has not yet been updated to formally number this story's new architectural decision** (that `accounts` becomes jointly relevant to both `auth/` and `employees/`) the way AD-10/AD-11 formalized Epic 6's decisions — flagged for a future architecture-doc pass, not blocking.

---

## Conclusion

Story 7-1 is **✅ DONE** after a create-then-implement-then-review cycle that caught its single most consequential risk — a broken credential seed that would have silently defeated Employee login — before any implementation code was written, rather than during implementation or, worse, during a later story:

- All acceptance criteria satisfied, including the corrected AC covering the re-seeded password hashes
- AR-24 resolved with direct evidence from the actual seed code, not inference from planning documents
- Learned from and did not repeat Story 6.1's own code review finding (the whole-module-import pattern)
- A follow-up, more careful search caught 2 import sites a first-pass regex missed
- One real regression class (4 failures) fixed, one unrelated pre-existing failure correctly identified via `git stash` and cleaned up rather than misattributed
- Zero findings on the final adversarial code review, which specifically verified the three highest-risk areas this kind of change creates
- Live-verified via `curl` against a rebuilt Docker container that neither existing login path regressed
- One gap deliberately left open and clearly documented (`authenticate()` doesn't yet read `Account`) rather than silently discovered by a future story

**Epic 7 status:** Story 7.1 is `done`, the first of 7 stories. Story 7.2 (HR Admin Creates a New Employee Record) is already implemented and in `review` at the time of writing.
