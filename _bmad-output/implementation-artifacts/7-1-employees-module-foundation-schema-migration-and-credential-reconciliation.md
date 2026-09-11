---
baseline_commit: 75638a224527b04d91d6769bea7e55d5ef706975
---

# Story 7.1: `employees/` Module Foundation — Schema Migration & Credential Reconciliation

Status: done

## Story

As a **developer**,
I want to establish `employees/` as the sole owning module for the `employees` table, extend its schema with Employee Roster Management's new profile fields, and resolve where Employee login credentials actually live,
So that Stories 7.2–7.7 (Create/View/Edit/Delete-Archive/Regenerate/Nav) each build on a stable schema and a real (not mock, not plaintext) credential mechanism, instead of discovering this mid-implementation (AR-24, resolving PRD Open Question 18).

## Scope Notes (read before starting)

1. **This mirrors Story 6.1's exact pattern** (`skills/` module extraction from `assignments/models.py`) — same AD-1 single-owner-module rationale, same "physically relocate, register via whole-module import" mechanism. Read Story 6.1's Dev Notes (`6-1-skills-module-foundation-data-model-migration-embeddings.md`) before starting if anything below is unclear; this story is deliberately the same shape.
2. **`Employee` currently lives in `assignments/models.py`**, not its own module — it has real relationships (`assignments`, `assignments_created`, `assignments_deleted`, `overrides_created`, `overrides_reversed`) that must keep resolving correctly after relocation, exactly the same cross-module relationship-registration concern Story 6.1's code review caught for `Skill`. Don't skip that lesson here.
3. **A critical discovery that changes AR-24's resolution — read this before writing any migration:** `backend/app/auth/models.py::Account` (currently unused — `authenticate()` in `auth/repository.py` still reads the plaintext `_MOCK_ACCOUNTS` dict) is **not actually a green field**. `core/seeds.py::create_default_accounts()` already seeds `Account` rows using `id=RITA_ID`, `id=CASEY_ID`, `id=MORGAN_ID`, etc. — **the exact same UUIDs as the corresponding `Employee` rows** (`core/seed_ids.py`). This is deliberate, half-finished work: the codebase already commits to `Account.id == Employee.id` as the identity link (by convention, not yet by a declared FK), precisely because `auth/repository.py`'s own comment states `CurrentUser.user_id` must resolve to a real Employee UUID (Story 3.1's assignments code does `uuid.UUID(current_user.user_id)` and expects it to be a real employee). **Resolution: extend/formalize `Account` as the real EMPLOYEE-role credential store — do not add a `password_hash` column directly to `Employee`.** Add an explicit FK (`accounts.id` → `employees.id`) making the existing implicit convention a declared constraint, rather than inventing a second, competing credential-storage shape.
4. **The seeded `password_hash` values are NOT valid — verify before trusting them.** `create_default_accounts()`'s inline comment says `# bcrypt("demo123")`, but the stored value (`$2b$12$Ej1cKPsyxQqFWK/8PHT0d.c0yoIbR1Z2r.uV5XvDWMmr.B8xN3RBG`, identical across all 5 rows) **fails `bcrypt.checkpw(b"demo123", stored)`** — confirmed by direct execution during this story's authoring. It's a placeholder with valid bcrypt *shape* only (matches the code's own honest comment a few lines up: `# In a real app, passwords would be hashed with bcrypt or similar / For now, use a simple mock hash`), not a real, usable hash. This story must re-seed real hashes (Task 4a below) — do not carry forward the false assumption that Open Question 17's credential half is already solved.
5. **This story does NOT wire `authenticate()` to actually use `Account` for login** — that's a real, currently-unassigned gap across Epic 7 as authored (see Dev Notes below), not this story's own scope (epics.md scopes 7.1 to "no new API endpoints... schema and credential-storage decision only"). Flagged prominently, not silently left for someone to discover.

## Acceptance Criteria

**Given** the existing `employees` table (`id`, `name`, `email`, `role`, `group`, `created_at` only — `backend/app/assignments/models.py::Employee`)
**When** this story's migration runs
**Then** the table gains: `employee_code` (string, unique, not null — but see the seed-data note below for how the 5 existing rows get a value), `phone`, `experience`, `technologies`, `position`, `project`, `manager_name`, `location`, `department` (all nullable strings), `updated_at` (timestamp), and `archived_at` (nullable timestamp — null means active, non-null means archived, per FR-27)

**Given** the architecture handoff note that an existing-but-unused `Account` model already sits seeded but unwired
**When** this story decides where Employee credentials live (AR-24)
**Then** the decision and its rationale are documented in this story's Dev Notes before any endpoint story (7.2+) is built — resolved above (Scope Note 3): extend `Account`, formalize the `accounts.id == employees.id` link via a real FK, do not add a password column to `Employee`

**Given** the decision above
**When** a password needs to be stored (by a future story)
**Then** it is hashed via `bcrypt` (the library already imported/used elsewhere in this codebase's conventions — pick this rather than introducing `argon2` as a second scheme) — never plaintext, and never reusing Story 1.4's `_MOCK_ACCOUNTS` plaintext-dict pattern, which remains exactly as-is for HR_ADMIN login (out of this epic's scope per FR-24's note)

**Given** the 5 seeded `Account` rows' `password_hash` values are placeholders that do not actually validate against `"demo123"` (verified: `bcrypt.checkpw(b"demo123", stored)` returns `False` — see Scope Note 4)
**When** this story wires up the real `Account`↔`Employee` link
**Then** it re-seeds all 5 rows with a real `bcrypt.hashpw(b"demo123", bcrypt.gensalt())` output (via a migration data-fix or an updated `create_default_accounts()`) — this story does not ship with the false assumption that demo login already works against `Account`

**Given** the 5 already-shipped hardcoded demo employees (Rita, Casey, Morgan, Jordan, Sam) with live Assignment/Watch-Progress/Override history, and PRD Open Question 17 (no migration path defined for them once this epic becomes the roster's source of truth)
**When** this story's migration is planned
**Then** an explicit decision is made and documented in this story's Dev Notes: **resolved below (Dev Notes) — backfill `employee_code` values for the 5 existing rows as part of this migration** (`EMP-0001` through `EMP-0005`, ordered by `seed_ids.py`'s UUID constants, not `created_at` — see Dev Notes) so the new `NOT NULL UNIQUE` constraint doesn't break on existing data; their `Account` rows already exist (seeded) and already share the correct `id`, though their `password_hash` values need re-seeding with a real hash (see AC3/Task 4a) — no schema-level Open-Question-17 work is needed beyond the profile-column backfill, and null/empty defaults are acceptable there (Phone, Experience, etc. were never collected for these 5)

**And** this story adds no new API endpoints and no frontend changes — schema, module relocation, and credential-storage decision only, so Stories 7.2+ each build on a stable foundation

## Tasks / Subtasks

- [x] Task 1: Create `employees/` module scaffolding (mirrors Story 6.1's `skills/` pattern)
  - [x] `backend/app/employees/__init__.py`, `models.py`, `repository.py`, `service.py`, `schemas.py`, `router.py`
  - [x] `repository.py`/`schemas.py`/`router.py` are documented stubs (no real CRUD yet — Stories 7.2–7.6); `router.py` not mounted in `main.py`. `service.py` additionally carries the real Task 5 password-hashing helper (not a stub).
- [x] Task 2: Relocate `Employee` ORM model
  - [x] Moved `class Employee` from `assignments/models.py` to `employees/models.py`, including all 5 existing relationships (verified exactly 5 via direct source read, matching the story's own claim)
  - [x] `assignments/models.py` registers `Employee` (and `Skill`) via whole-module `import app.employees.models` / `import app.skills.models` — used the correct whole-module form from the start, no "old path still works" gap to fix in review this time
  - [x] `employees/models.py` mirrors back with `import app.assignments.models`
- [x] Task 3: Extend the `employees` table (new columns, AC1)
  - [x] Migration `011_add_employee_profile_fields.py`: all 11 new columns added, applied live against the dev Postgres (`alembic upgrade head`), verified via direct `information_schema.columns` query
  - [x] Backfilled `employee_code` for the 5 existing seeded rows (`EMP-0001`–`EMP-0005`, ordered by `seed_ids.py`'s UUID constants), verified live; `core/seeds.py::seed_employees` updated to assign the same codes for a fresh-DB seed run
- [x] Task 4: Formalize the `Account`↔`Employee` identity link (AR-24 resolution)
  - [x] `accounts_id_fkey` (accounts.id → employees.id) added in migration 011, verified live via `pg_constraint`
  - [x] `Account` model docstring updated to state its resolved role and the `id`-must-equal-`Employee.id` invariant
  - [x] **Task 4a:** Re-seeded all 5 `Account.password_hash` values with a real `bcrypt.hashpw` output (via the migration's own data-fix, scoped to exactly the known placeholder value) — verified live with `bcrypt.checkpw(b"demo123", ...)` returning `True` for all 5; `core/seeds.py::create_default_accounts` also updated to call the new `hash_password()` helper for any future fresh-DB seed run
  - [x] `auth/repository.py::authenticate()` and the login endpoint left untouched, as scoped — verified via live `curl` that both HR_ADMIN and EMPLOYEE login still work unchanged through `_MOCK_ACCOUNTS`
- [x] Task 5: Password hashing utility
  - [x] `employees/service.py::hash_password`/`verify_password` (bcrypt), unit-tested; `core/seeds.py` now calls `hash_password` instead of a hardcoded literal
- [x] Task 6: Update every import site affected by the `Employee` relocation
  - [x] App code: `assignments/models.py`, `assignments/repository.py`, `auth/models.py` (new FK-registration import), `core/seeds.py`
  - [x] Tests: 9 files found via a single-line regex search + **2 more found via a follow-up multi-line-import search** (`conftest.py`, `test_schema_definition.py`) that the first pass missed — all updated. `test_provenance_detail.py`'s 3 `Employee(...)` calls are pure in-memory objects never persisted (verified: file passes unchanged), correctly left alone rather than over-fixed.
- [x] Task 7: Schema tests
  - [x] `test_schema_definition.py`: added `test_employees_employee_code_is_required_and_unique`, `test_department_is_distinct_from_group`, `test_employees_archived_at_is_nullable_soft_delete_flag`, `test_accounts_id_references_employees` (all pure-ORM-metadata style, matching this file's established convention — an earlier draft used a live-DB inspector instead and was corrected to match the file's actual pattern)
  - [x] New `tests/test_employees_service.py` — 5 tests for `hash_password`/`verify_password`, including a permanent regression guard pinning the exact bad placeholder hash found during this story's authoring
- [x] Task 8: Full regression pass — 641 passed, 2 skipped, 0 failed (see Dev Agent Record for the full trace, including one confirmed-pre-existing failure found, `git stash`-verified, and cleaned up along the way)

## Dev Notes

### The `Account`/`Employee` UUID-matching discovery is the single most important finding in this story

`auth/repository.py`'s own comment states: *"user_id values are the same UUIDs as the real seeded Employee rows (core/seeds.py), not arbitrary names — Story 3.1's assignments code treats CurrentUser.user_id as a real Employee UUID."* `create_default_accounts()` was written honoring that exact constraint for `Account` rows too (`id=RITA_ID`, `id=CASEY_ID`, ...) — meaning whoever wrote that seed function already intended `Account` to become the real credential store, keyed by the same identity as `Employee`, not a separate user-identity space. This is what makes AR-24's resolution (extend `Account`, don't add a column to `Employee`) unambiguous. **What it does NOT mean:** that the credential data itself is production-ready — the `password_hash` values seeded alongside those matching IDs are placeholders that don't actually validate (see Task 4a). The identity-linking intent is real and load-bearing; the specific seeded secret values are not. Treat the ID-matching pattern as load-bearing context for every subsequent Epic 7 story — but re-verify, don't assume, any other seeded value you plan to depend on.

### The `authenticate()` rewire gap is real and currently unassigned — flagging it here so it isn't lost

Neither this story nor any other Epic 7 story (7.2 through 7.7, as currently written in `epics.md`) has an AC that says "modify `auth/repository.py::authenticate()` to check `Account` for EMPLOYEE-role logins." Story 7.2's AC covers *creating* an Employee (and its paired `Account` row, implicitly — see below), but never says the resulting credential is actually usable to log in. This is the same "auth-layer rewire is the riskiest part of this feature" risk the PRD's own post-review addendum flagged and it is *still* not concretely owned by any story after epic authoring and one implementation-readiness pass. **Recommendation for whoever picks up Story 7.2:** that story's real scope should include making `authenticate()` check `Account` (matched by email) for a role-appropriate result *before or in addition to* `_MOCK_ACCOUNTS`, not just insert rows nobody can log in with. If Story 7.2's own text isn't updated to say this explicitly before work starts, treat this paragraph as the binding guidance anyway — the same pattern Story 1.3 used for repository hard-scoping forward-guidance.

### Why `bcrypt`, not `argon2` — and why the seeded hashes need re-doing, not just reading

`epics.md`'s Story 7.1 text (as authored) offered a choice between `bcrypt` and `argon2`. The seed data in `create_default_accounts()` uses the `$2b$...` bcrypt format for all 5 rows, so `bcrypt` is the consistent choice — introducing `argon2` would mean two hashing schemes in one table with no algorithm-tag column to tell them apart. **However, the existing seeded hash values are not real** — `bcrypt.checkpw(b"demo123", stored)` returns `False` against the committed value, confirmed by direct execution. The code's own comment two lines above the hash (`# In a real app, passwords would be hashed with bcrypt or similar / For now, use a simple mock hash`) is the honest tell: this was always a placeholder, not a shortcut someone actually validated. Task 4a (re-seed with a real `bcrypt.hashpw` output) is not optional cleanup — without it, `Account`-backed Employee login is silently broken for all 5 demo accounts the moment a future story wires `authenticate()` to it.

### `employee_code` backfill approach

The new column is `NOT NULL UNIQUE`, but the 5 existing seeded Employees were never assigned a code (this concept didn't exist before this epic). Backfill with a deterministic scheme (`EMP-0001` etc.) ordered by the existing `seed_ids.py` UUID constants (`RITA_ID`, `CASEY_ID`, `MORGAN_ID`, `JORDAN_ID`, `SAM_ID`, in that declared order) — **not** by `created_at`, since all 5 rows are inserted in one `add_all`/flush and may share identical or near-identical `server_default=func.now()` timestamps, making `created_at` ordering non-deterministic in practice. Do this inside the same migration, before the constraint is added, so `alembic upgrade head` doesn't fail against the existing dev database. This is the full extent of Open Question 17's resolution needed at the schema layer — the harder half of Open Question 17 (do these 5 employees' *existing Assignment/Watch-Progress/Override history* need any migration) turns out to need **no schema change at all**, since that history already references `Employee.id`, which is untouched by this story's relocation or column additions.

### `department` vs. the existing `group` column — a deliberate decision, not an oversight

`addendum.md`'s Architecture Handoff Notes explicitly flag this as open: *"Whether `department` reuses the existing `group` column or is a distinct new column is an open implementation call, not decided in the PRD."* This story resolves it: **`department` is added as a new, distinct column — `group` is left untouched and unused by Employee Roster Management.** Reasoning: `group`'s original purpose and current usage elsewhere in the codebase were not established as "department" semantics anywhere in the PRD/UX work, and silently repurposing an existing column risks colliding with whatever `group` already means to other code paths that read it. A new column is the lower-risk choice given no evidence `group` was ever intended for this.

### Relationship-registration ordering (learn from Story 6.1's code review, don't repeat it)

Story 6.1 shipped `Skill`'s relocation with a one-way `from app.skills.models import Skill` re-export in `assignments/models.py`, which code review found still let old code import `Skill` the pre-relocation way — defeating the point of the relocation — and *separately* found the relationship resolution was fragile in the reverse-import-order case. Both problems are avoidable here by doing the whole-module-import-both-directions pattern from the start (Task 2 above), rather than shipping the naive version and fixing it in review a second time.

## File List

New files:
- `backend/app/employees/__init__.py`
- `backend/app/employees/models.py` — `Employee` ORM (relocated from `assignments/models.py`), plus 11 new columns
- `backend/app/employees/repository.py` — documented stub
- `backend/app/employees/service.py` — `hash_password`/`verify_password` (bcrypt)
- `backend/app/employees/schemas.py` — documented stub
- `backend/app/employees/router.py` — documented stub, unmounted
- `backend/alembic/versions/011_add_employee_profile_fields.py`
- `backend/tests/test_employees_service.py`

Modified files:
- `backend/app/assignments/models.py` — `Employee` class removed; registers `app.employees.models` (and, cleaned up in the same pass, `app.skills.models`) via whole-module imports
- `backend/app/assignments/repository.py` — `Employee` import repointed to `app.employees.models`
- `backend/app/auth/models.py` — `Account.id` gains an explicit FK to `employees.id`; class docstring rewritten to state its resolved AR-24 role
- `backend/app/core/seeds.py` — `Employee` import repointed; `seed_employees()` now assigns `employee_code` to all 5 rows; `create_default_accounts()` now calls `hash_password()` instead of a hardcoded placeholder hash
- `backend/requirements.txt`, `backend/requirements-prod.txt` — added `bcrypt==5.0.0` (already installed/imported by the seed data's own comment, but never declared — same class of gap Story 6.5 found for `cryptography`)
- `backend/tests/conftest.py` — `Employee` import repointed (multi-line import block, missed by the first single-line-regex pass)
- `backend/tests/test_schema_definition.py` — `Employee` import repointed (same multi-line-import miss); 4 new tests added
- `backend/tests/test_admin_api_keys_router.py`, `test_antiflow_validation.py`, `test_override_endpoint.py`, `test_position_retrieval.py`, `test_seed_employee_identity_alignment.py` — `Employee` import repointed
- `backend/tests/test_admin_api_keys_router.py`, `test_override_endpoint.py` — ad hoc `Employee(...)` fixture helpers gained a required `employee_code` (regression found via full-suite run, fixed same session)
- `backend/tests/test_db.py` — `Employee` import repointed; both ad hoc `Employee(...)` calls gained a required `employee_code` (same regression class)

No changes to:
- `backend/app/auth/repository.py::authenticate()` — explicitly out of scope, see Dev Notes forward-guidance
- `backend/app/auth/repository.py::_MOCK_ACCOUNTS` — HR_ADMIN and EMPLOYEE login both verified unchanged via live `curl`
- `backend/app/main.py` — `employees` router not mounted (no endpoints yet)
- `backend/tests/test_provenance_detail.py` — its 3 `Employee(...)` calls are non-persisted in-memory objects; verified the file passes unchanged, correctly left alone

## Dev Agent Record

### Debug Log

- `Employee` relocation: initial `models.py` draft contained a leftover nonsensical `Column(uuid.UUID if False else __import__("sqlalchemy").UUID(as_uuid=True), ...)` expression from mid-edit drafting — caught on re-read before running anything, replaced with a plain `Column(UUID(as_uuid=True), ...)` plus a proper `from sqlalchemy import UUID` import.
- Migration 011 applied via `alembic upgrade head` against the local `.venv` pointed at `localhost:5433` (the same exposed Postgres port the Docker `talentpilot-db` container publishes) — verified column/constraint state via direct `psql`/SQLAlchemy queries after applying, rather than trusting the migration script alone.
- `bcrypt` import worked in an ambient interpreter but raised `ModuleNotFoundError` inside the project's own `backend/.venv`, and was absent from both `requirements.txt` and `requirements-prod.txt` — added `bcrypt==5.0.0` to both files and `pip install`-ed it into the venv before continuing.
- Direct `bcrypt.checkpw(b"demo123", stored_hash)` against the seeded `accounts.password_hash` value returned `False` — confirms Scope Note 4 / Change Log entry 2's finding that the seeded hash is a shape-valid placeholder, not a real hash of `"demo123"`. Re-seeded via `hash_password("demo123")` in `create_default_accounts()`, and amended migration 011 with a one-time data-fix replacing the exact bad placeholder value for any pre-existing `accounts` rows (downgrade → re-upgrade cycle, since the migration hadn't been merged yet).
- Single-line regex search for `from app.assignments.models import Employee` found 9 call sites; a follow-up multi-line-aware search (`grep -Pzo` across parenthesized import blocks) found 2 more (`conftest.py`, `test_schema_definition.py`) the first pass missed — both fixed the same way (moved `Employee` to its own `from app.employees.models import Employee` line).
- First full regression run: 5 failed / 636 passed / 2 skipped. Triaged each:
  - `test_db.py` (2), `test_admin_api_keys_router.py` (1), `test_override_endpoint.py` (1): all `NotNullViolationError` on the new `employee_code` column from ad hoc `Employee(...)` test fixtures — fixed by adding a unique `employee_code` value to each.
  - `test_assignments_repository.py::test_find_existing_assignment_returns_empty_when_no_match`: unrelated — a stray pre-existing `Assignment` row in the shared dev DB (dated 2026-07-16, left over from an earlier session). Verified pre-existing/unrelated to this story via `git stash push -u -- backend/` → re-run (same failure against the reverted baseline) → `git stash pop`. Cleaned up by deleting the stray row directly.
- Re-ran full suite after fixes: **641 passed, 2 skipped, 0 failed** in 80.03s.
- Rebuilt and restarted the `talentpilot-api` Docker container (no live volume mount on this compose file, so the image needed rebuilding for the code changes to take effect) and confirmed via `curl` that both an HR_ADMIN and an EMPLOYEE mock login still succeed unchanged.

### Completion Notes

- **AR-24 resolved**: extended the existing-but-unused `Account` model (adding an explicit `accounts.id → employees.id` FK) rather than adding a password column directly to `Employee`. The deciding evidence was that `core/seeds.py::create_default_accounts` already seeds `Account.id` values equal to the matching `Employee`'s UUID for all 5 demo users — the schema was already implicitly designed this way, just never enforced or wired up.
- **Critical bug found and fixed during authoring, not implementation**: an independent story-review subagent caught that the seeded `Account.password_hash` values were not, in fact, valid bcrypt hashes of `"demo123"` as the seed code's own comment claimed — verified with a direct `bcrypt.checkpw()` call. Had this shipped unnoticed, Employee login would have silently broken the moment a future story wired `authenticate()` to read from `Account`. Fixed by adding a real `hash_password()` call to `create_default_accounts()` and a migration-level data-fix for any already-applied bad hash, plus a permanent regression-guard test pinning the exact bad hash value.
- Implemented the `employees/` module scaffold (models relocated with 11 new profile columns, service-layer bcrypt helpers, documented stubs for repository/schemas/router) mirroring Story 6.1's `skills/` extraction pattern, including the whole-module-both-directions import convention that story's code review established.
- `authenticate()` itself is explicitly **not** rewired to use `Account` by this story — that's flagged as a real, currently-unassigned gap for a future story (see Dev Notes) rather than silently left undiscovered.
- 11 total import call sites repointed from `app.assignments.models` to `app.employees.models` (9 found by an initial single-line regex, 2 more by a follow-up multi-line-import-aware search), plus 4 test files needed `employee_code` added to ad hoc `Employee(...)` fixtures to satisfy the new NOT NULL constraint.
- One unrelated, pre-existing test failure (a stray leftover DB row) was found and cleaned up along the way, verified via the project's established `git stash`-before/after methodology rather than assumed.

### Test Results

```
641 passed, 2 skipped in 80.03s
```

No new regressions relative to baseline commit `75638a22`. The 2 skipped tests are pre-existing skips unrelated to this story. One failure found mid-implementation (`test_assignments_repository.py::test_find_existing_assignment_returns_empty_when_no_match`) was confirmed pre-existing/unrelated via `git stash` and resolved by removing a stray leftover row from the shared dev database, not by changing test or app code.

## Architecture Compliance

- **AD-1 — Single-owner data modules**: `employees` gains a real owning module, mirroring AD-11's precedent for `skills/`. A new architectural decision this story establishes (not yet numbered in `ARCHITECTURE-SPINE.md`) is that `accounts` becomes jointly relevant to both `auth/` (module of record for the table) and `employees/` (the identity that `accounts.id` must always match) — flag for the architecture doc to catch up if a future pass formalizes AD numbering for Epic 7's decisions the way AD-10/AD-11 formalized Epic 6's.
- **AR-24 (epics.md)**: resolved — extend `Account`, do not add a password column to `Employee`. See Dev Notes.

## References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 7.1] — full AC text (as extended by the 2026-09-11 implementation readiness check with the Open Question 17 AC)
- [Source: _bmad-output/implementation-artifacts/6-1-skills-module-foundation-data-model-migration-embeddings.md] — the pattern this story mirrors
- [Source: backend/app/assignments/models.py] — current `Employee` definition and its relationships
- [Source: backend/app/auth/models.py] — current `Account` definition
- [Source: backend/app/auth/repository.py] — `_MOCK_ACCOUNTS`, and the comment establishing `user_id` must be a real Employee UUID
- [Source: backend/app/core/seeds.py::create_default_accounts] — the seeded `Account` rows already using matching Employee UUIDs and real bcrypt hashes — the key discovery resolving AR-24
- [Source: backend/app/core/seed_ids.py] — `RITA_ID`/`CASEY_ID`/etc. constants shared by both seed functions
- [Source: _bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/addendum.md#Employee Roster Management] — Architecture Handoff Notes this story resolves
- [Source: _bmad-output/planning-artifacts/implementation-readiness-report-2026-09-11.md] — the readiness check that added this story's Open Question 17 AC and flagged AR-24/Story-7.5 sizing concerns

## Completion Checklist

- [x] `employees/` module created (router, service, repository, models, schemas — all stubs except models.py)
- [x] `Employee` ORM relocated out of `assignments/models.py`, both-direction whole-module imports in place
- [x] Migration 011 applied: 9 new nullable columns + `employee_code` (NOT NULL UNIQUE, backfilled) + `updated_at` + `archived_at`
- [x] `accounts.id` → `employees.id` FK added and applied
- [x] `Account` docstring/model updated to state its resolved role
- [x] bcrypt hash/verify helper added and unit-tested
- [x] All import sites updated (app + tests), verified via repo-wide search, not assumed from this story's own list
- [x] Schema tests updated and passing
- [x] Full regression suite run, zero new regressions vs. current baseline
- [x] `app.main` imports cleanly (no circular-import issue from the new cross-module import)
- [x] Sprint status updated to `review` (then `done` after code review)

## Change Log

- 2026-09-11: Story created (`bmad-create-story`). Exhaustive analysis of `backend/app/auth/models.py`, `auth/repository.py`, and `core/seeds.py::create_default_accounts` found that `Account` rows are already seeded with `id` values matching the corresponding `Employee` UUIDs — resolving AR-24 unambiguously in favor of extending `Account` rather than adding a password column to `Employee`. Flagged a real, currently-unassigned gap: no Epic 7 story as authored actually wires `authenticate()` to use `Account` for Employee login — forward guidance recorded for Story 7.2. Status → `ready-for-dev`.
- 2026-09-11: Independent quality review (fresh-context subagent, per `checklist.md`) caught a factual error in the initial draft: the seeded `Account.password_hash` values were assumed to be real, working bcrypt hashes of `"demo123"` based on the seed code's own comment — verified by direct `bcrypt.checkpw()` execution that they are **not** (they fail validation; placeholder values with valid bcrypt shape only). Corrected throughout (Scope Notes, ACs, Dev Notes, Change Log) and added Task 4a (re-seed real hashes) so the story doesn't ship a false "nothing left to do here" assumption. Also added an explicit Dev Note resolving the `department`-vs-`group` column question the addendum had left open, and corrected the `employee_code` backfill ordering guidance (`seed_ids.py` UUID order, not `created_at`, which isn't guaranteed distinct across one bulk insert).
- 2026-09-11: Implementation complete (`bmad-dev-story`). All 8 tasks/subtasks done: `employees/` module scaffolded, `Employee` relocated with 11 new columns, migration 011 applied and verified live, `Account` FK added, bcrypt hash/verify helper added, all 11 import call sites repointed (9 + 2 found via a multi-line-import follow-up search), schema tests added, and a full regression pass fixed 4 `employee_code`-related test failures plus one confirmed-unrelated pre-existing stray-row failure (cleaned up via the project's `git stash` verification convention). Final suite: 641 passed, 2 skipped, 0 failed. Docker image rebuilt and both HR_ADMIN/EMPLOYEE mock logins verified unchanged via live `curl`. Status → `review`.
