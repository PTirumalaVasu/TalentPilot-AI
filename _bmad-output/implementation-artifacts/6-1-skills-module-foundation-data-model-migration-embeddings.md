---
baseline_commit: 4e99d275
---

# Story 6.1: `skills/` Module Foundation — Data Model, Migration & Embeddings

Status: done

## Story

As a **developer**,
I want to establish `skills/` as the sole owning module for the `skills` table, migrating it out of `assignments/`,
So that Skill CRUD (FR-20/21/22) has a real architectural home instead of the narrow, documented exceptions that existed before this epic (AD-11, resolving PRD Open Question 16).

## Scope Notes (read before starting)

1. **Migration 004 (`ever_assigned` column + backfill) and migration 005 (`admin_api_keys` table) already existed on this branch before this story started** — committed ad hoc (`4e99d275`, "Migration done for the Skill tab"), outside the formal `bmad-create-story`/`bmad-dev-story` flow, alongside a column-only `ever_assigned` addition to `assignments/models.py::Skill`. Verified live against the running Docker Postgres (`alembic_version` = `005`, `skills.ever_assigned boolean not null default false` present) before starting — migration/backfill work is **not** redone here. This story's real scope is the module relocation, scaffolding, and embedding-write helper the epic's own AC text calls for.
2. **`admin_api_keys` (migration 005, `AdminApiKey` model) is Story 6.5's table, untouched by this story** except for one incidental fix: `test_schema_definition.py::test_all_tables_defined` was pinned at 7 expected tables and had been silently broken by migration 005 landing without a matching test update. Fixed opportunistically (one-line, in a file this story already touches for its own Skill-import fix) — logged in Dev Notes below, not scope creep on Story 6.5's actual CRUD/credential work.
3. **The epic's AC text says "content/ no longer imports Skill or queries the skills table directly," not just "list_all_skills() is replaced."** Taken literally: `content/repository.py::get_skill_embedding()` (Story 2.4) was a second direct `Skill`/`skills`-table read, whose own docstring rationale ("no `skills/` module/service exists yet") became false the moment this story creates one. Both `list_all_skills` and `get_skill_embedding` were relocated to `skills/repository.py` + `skills/service.py`; `content/` now depends on `skills.service` exclusively (matches the architecture spine's AD-8 diagram: `Content -. depends on .-> Skills`).
4. **`assignments/repository.py::list_skills()`** (a third, narrower pre-existing direct `Skill` read, for the assignment modal's Step 2 combobox) was **not** migrated — it isn't named in this story's ACs (which scope only the `content/repository.py` replacement), and this story's own "Out of Scope" note limits it to "schema, migration, module scaffolding, and the embedding-write helper only," not a sweep of every module's `Skill` consumption. Left as a flagged, documented exception (see that file's own docstring and import comment) for a future story to route through a real `skills.service` call — not Story 6.2/6.3 specifically (those are `skills/`'s own CRUD endpoints, not a refactor of `assignments/`'s read side; corrected 2026-09-09 code review, which caught this file's earlier wording misattributing which story would close it).

## Acceptance Criteria

**Given** the `Skill` ORM model currently lives in `assignments/models.py` (Story 1.7), with `content/repository.py::list_all_skills()` reading it directly as a documented narrow AD-1 exception (Story 2.3, scope note 2)
**When** I create the `skills/` module (`app/skills/{router.py, service.py, repository.py, models.py, schemas.py}`, per the paradigm table)
**Then**:
- `Skill` moves to `skills/models.py`; `assignments/models.py` no longer defines it (imports it from `skills/models.py` only for the FK relationship on `Assignment.skill_id`, never for writes)
- The `skills` table gains one new column: `ever_assigned` (boolean, not null, default `false`) — the AD-11 lock flag
- A new Alembic migration applies this column addition without data loss to existing seeded Skill rows (all default to `ever_assigned = false`, correct since no Skill row can retroactively know whether it's "ever been assigned" without a backfill query — this migration includes a one-time backfill: `UPDATE skills SET ever_assigned = true WHERE id IN (SELECT DISTINCT skill_id FROM assignments)`, so pre-existing seeded/assigned Skills aren't incorrectly editable post-migration)

**Given** `content/repository.py::list_all_skills()` (Story 2.3's documented exception)
**When** this story lands
**Then** it's replaced with a call to `skills.service.list_all_skills()` (the new module's Service API) — `content/` no longer imports `Skill` or queries the `skills` table directly; the exception documented in Story 2.3's scope note 2 is retired

**Given** `skills/service.py`
**When** a Skill's name (and description, if present) changes — on create (Story 6.2) or rename (Story 6.3)
**Then** it calls `core/embedding.py::embed_text()` on `f"{name}: {description or ''}"` (same truncation convention as `content/`'s `_build_embedding_text`, Story 2.3) and stores the resulting vector in `skills.embedding` — mirrors `content/`'s existing embedding-on-write pattern, never computed inline in the router

**Out of Scope (this story):** the CRUD endpoints themselves (Stories 6.2/6.3) — this story is schema, migration, module scaffolding, and the embedding-write helper only.

## Tasks / Subtasks

- [x] Task 1: Verify pre-existing migration 004/005 state (no AC — baseline check)
  - [x] Confirm live DB `alembic_version` = `005` and `skills.ever_assigned` column present via `docker exec ... psql \d skills`
  - [x] Confirm `admin_api_keys` table exists (Story 6.5, unrelated but co-located in `assignments/models.py`)
- [x] Task 2: Create `skills/` module scaffolding (AC1)
  - [x] `app/skills/__init__.py`, `models.py`, `repository.py`, `service.py`, `schemas.py`, `router.py`
  - [x] `router.py`/`schemas.py` are documented stubs (no CRUD endpoints yet — Story 6.2/6.3); not mounted in `main.py`
- [x] Task 3: Relocate `Skill` ORM model (AC1)
  - [x] Move `class Skill` from `assignments/models.py` to `skills/models.py` (same columns, same `ever_assigned`)
  - [x] `assignments/models.py` imports `Skill` back only for the FK relationship registration, with an explicit "never for writes" comment
  - [x] Fix the `AdminApiKey` docstring's now-stale "alongside Skill/ContentCatalog" claim (one-line, same file already being edited)
- [x] Task 4: Retire `content/`'s Skill exceptions (AC2)
  - [x] Move `list_all_skills()` and `get_skill_embedding()` from `content/repository.py` to `skills/repository.py`, wrapped by `skills/service.py`
  - [x] `content/service.py`'s `run_ingestion_job` and `match_content_for_skill` call `skills_service.list_all_skills()` / `skills_service.get_skill_embedding()` instead of `repository.*`
  - [x] `content/repository.py` no longer imports `Skill`
- [x] Task 5: Embedding-write helper (AC3)
  - [x] `skills/service.py::_build_embedding_text(name, description)` — same 1000-char truncation convention as `content/service.py`'s helper, independently defined (AD-8: `skills/` must not depend on `content/`)
- [x] Task 6: Update every import site affected by the `Skill` relocation (code review, 2026-09-09: none of these actually raised `ImportError` if left untouched — `assignments/models.py`'s original `from app.skills.models import Skill` kept `Skill` importable from the old path too, closed by a separate patch below — these sites were updated for AD-1-compliance cleanliness, not because they were forced to)
  - [x] App code: `assignments/repository.py`, `content/repository.py`, `content/service.py`, `core/seeds.py`
  - [x] Tests: `conftest.py`, `test_antiflow_validation.py`, `test_content_discovery.py`, `test_content_ingestion.py`, `test_content_matching.py`, `test_content_repository.py`, `test_content_service.py`, `test_position_retrieval.py`, `test_schema_definition.py`, `test_seed_skill_data_quality.py`
- [x] Task 7: Tests (new + moved)
  - [x] `tests/test_skills_repository.py` — `list_all_skills`, `get_skill_embedding`, `ever_assigned` default-false (moved/adapted from `test_content_ingestion.py`/`test_content_matching.py` + new)
  - [x] `tests/test_skills_service.py` — `_build_embedding_text` truncation/None-description, Service API smoke tests
  - [x] `test_schema_definition.py`: `ever_assigned` column coverage added; `test_all_tables_defined` fixed to expect 8 tables (pre-existing gap, see Scope Note 2)
- [x] Task 8: Full regression pass — 384 passed, 2 skipped, 3 pre-existing unrelated failures (see Dev Notes)

### Review Findings

`bmad-code-review` (2026-09-09, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor). 1 decision-needed (resolved), 9 patches, 2 deferred, 3 dismissed.

- [x] [Review][Decision] AC3's "embedding-write helper" only builds text — it never calls `embed_text()` or writes to `skill.embedding` — Acceptance Auditor flagged this as a literal AC3 gap: the AC's Then-clause names both "calls `embed_text()`" and "stores the resulting vector in `skills.embedding`" as behavior of `skills/service.py`, but `_build_embedding_text()` (what this story ships) only does the text-truncation half. **Decision (user, 2026-09-09): leave as-is.** The text-builder is the complete "embedding-write helper" this story owns — matches `content/service.py`'s own established inline-composition convention exactly (it composes `embed_text(_build_embedding_text(...))` inline at each write site — `manual_seed_content`, `ingest_content_for_skill` — never in a separate wrapper). Story 6.2 (create)/6.3 (rename) will each call `embed_text(_build_embedding_text(...))` inline the same way when they build the actual write paths. Not a gap — dismissed as consistent with precedent.

- [x] [Review][Patch] Old import path `from app.assignments.models import Skill` still works, undermining the AD-1 enforcement boundary this story exists to establish [backend/app/assignments/models.py:30] — Blind Hunter: `assignments/models.py` doing `from app.skills.models import Skill` re-binds `Skill` in its own namespace, so nothing stops future code from importing it the old way. Fix: switch to a whole-module `import app.skills.models` (registers the class for relationship resolution without exposing the name) — verified zero remaining call sites anywhere in the codebase depend on `from app.assignments.models import Skill` before applying.
- [x] [Review][Patch] Import-ordering fragility: `skills/models.py`'s `content_items`/`assignments` relationships only resolve if `app.assignments.models` happens to already be imported somewhere in the process [backend/app/skills/models.py] — independently found by both Edge Case Hunter and Blind Hunter. Today every real entry point (app boot via `main.py`, test suite via `conftest.py`) transitively imports both modules together, so it doesn't currently misfire, but a future isolated import (a standalone script, a narrower test, Story 6.2's router mounted before other routers) could hit an unresolved-relationship `InvalidRequestError`. Fix: add a mirroring whole-module `import app.assignments.models` to `skills/models.py`, the same safe circular-registration idiom already used in the other direction.
- [x] [Review][Patch] `_build_embedding_text` doesn't actually mirror `content/service.py`'s "identical" helper — the latter logs via `logger.debug` on truncation, `skills/service.py`'s version logs nothing [backend/app/skills/service.py:18-27] — Blind Hunter + Acceptance Auditor both caught this divergence from the Dev Notes' "mirrors... exactly" claim. Fix: add the same truncation-logging line content/service.py's version has.
- [x] [Review][Patch] No automated guard verifies the actual architectural invariant this story establishes — that `content/` never again directly imports `Skill` or queries the `skills` table [backend/app/content/repository.py, backend/app/content/service.py] — Blind Hunter: AD-1/AD-8 compliance is asserted only in prose (Dev Notes, docstrings), with no regression test to catch a future re-introduction. This codebase already has a precedent for exactly this shape of check (`test_content_ad7_regression_guard.py`, a static grep-based guard). Fix: add an equivalent static guard test for this invariant.
- [x] [Review][Patch] New schema test's name/docstring promise "default false" coverage it never asserts [backend/tests/test_schema_definition.py, `test_skills_ever_assigned_column_is_a_non_nullable_boolean_defaulting_false`] — Edge Case Hunter + Acceptance Auditor both caught this: the test only checks `nullable`/`type`, never `.default`/`.server_default`. Not a functional gap (`test_skills_repository.py::test_new_skill_defaults_ever_assigned_to_false` already exercises the real runtime default), but the schema-level test under-asserts relative to its own name. Fix: add `default`/`server_default` assertions.
- [x] [Review][Patch] `assignments/repository.py::list_skills()`'s own docstring carries no AD-1/exception language — only the import-block comment above it does [backend/app/assignments/repository.py:60-62] — Acceptance Auditor: a future reader of `list_skills()` in isolation (the actual flagged function) gets no signal it's a documented exception. Fix: add a brief note to the function's own docstring, not just the import comment.
- [x] [Review][Patch] Story file Scope Note 4's rationale ("scope creep into Story 6.2/6.3 territory") misattributes which story would actually own migrating `list_skills()` [this file, Scope Note 4] — Acceptance Auditor: 6.2/6.3 are `skills/`'s own CRUD endpoints, not a refactor of `assignments/`'s consumption of `Skill`; the conclusion (leave it alone) is still correct under AC2's literal text, but the stated reason could mislead a future reader about which story closes this gap. Fix: reword to reference "a future story" rather than naming 6.2/6.3 specifically.
- [x] [Review][Patch] Story file's Architecture Compliance section oversells the AD-1 claim then immediately contradicts it [this file, "Architecture Compliance"] — Blind Hunter: opens with "only `skills/repository.py` queries it directly," then the very next clause concedes `assignments/repository.py::list_skills()` is a live, unmigrated exception. Fix: reword to state the known exception upfront rather than assert-then-walk-back.
- [x] [Review][Patch] Story file Task 6's "~10 broken import sites" framing overstates what happened [this file, Task 6] — Blind Hunter: none of those sites would have raised `ImportError` if left untouched, since the old `from app.assignments.models import Skill` path kept working (see the decision above about closing that path) — they were changed for AD-1-compliance cleanliness, not because they were forced to. Fix: reword. Note this framing becomes literally accurate once the "old import path still works" patch above is applied (after that fix, those sites genuinely would break if reverted).

- [x] [Review][Defer] `test_all_tables_defined`'s hardcoded exact-table-count set is a brittle pattern that will likely collide with Story 6.5 (`org_api_credentials`) and 6.8 (`content_catalog` changes) [backend/tests/test_schema_definition.py] — deferred, pre-existing test design (not introduced by this story; this story only bumped the count 7→8 to fix an already-broken assertion). Fixing the anti-pattern itself (e.g. deriving the count from migration history, or dropping the exact-count assertion) is out of this story's scope — flagged for whoever picks up 6.5/6.8 to watch for a merge collision on this exact set.
- [x] [Review][Defer] Tests run against a single shared, stateful dev Postgres instance with accumulated cross-session row state, rather than an isolated test DB/schema [backend/tests/test_skills_repository.py, test_skills_service.py, and every other live-DB test file] — deferred, pre-existing systemic issue already extensively tracked elsewhere in this ledger (the conftest.py `drop_all()` landmine, the cross-file asyncpg pool-corruption pattern) since Story 1.7/the Epic 4 retro; this story's 3 confirmed-pre-existing failures are a symptom of the same root cause, not a new instance.

**Dismissed** (noise, false positive, or already handled elsewhere): new test files' module-level engines never `.dispose()`d (matches this codebase's own established convention in `test_content_matching.py`/`test_content_discovery.py`/`test_seed_skill_data_quality.py`, not a deviation); the regression-baseline "confirmed via `git stash`" claim being unverifiable prose (matches this project's own documentation convention used by essentially every prior story, not fixable by a code patch); `skills/models.py`'s docstring naming a future `skills.service.mark_ever_assigned()` API as "premature" (verified against `ARCHITECTURE-SPINE.md` AD-11 point 3, which already locks this exact function name/call pattern — not invented by the developer, matches this codebase's established forward-reference-guidance precedent).

## Dev Notes

### Why the migration/backfill work isn't repeated here

A prior, out-of-process commit (`4e99d275`) already wrote and applied migrations 004/005. Rewriting them would either duplicate work or (worse) create a second competing migration touching the same column. Verified directly against the live container rather than trusting the commit message:

```
docker exec talentpilot-db psql -U talentpilot -d talentpilot -c "\d skills"
 ever_assigned | boolean | not null | false
docker exec talentpilot-db psql -U talentpilot -d talentpilot -c "select version_num from alembic_version;"
 005
```

This story's real, previously-undone work was the module relocation the epic AC actually asks for — `ever_assigned` living on the right table was never the hard part; `Skill` having a real owning module was.

### "content/ no longer imports Skill or queries the skills table directly" was read as a blanket statement, not just about `list_all_skills`

The AC's Given/When/Then is framed around `list_all_skills()`, but its own Then-clause states the destination condition in absolute terms. `get_skill_embedding()` (added later, Story 2.4) was the same class of violation under a different docstring rationale ("no `skills/` module/service exists yet, Story 3.2 is still backlog") — a rationale this story's own existence falsifies. Moving both, rather than only the one named function, was judged to be what actually satisfies the AC's stated end-state rather than a narrower literal reading that would leave a second identical exception standing one story after the first was supposedly retired.

### `assignments/repository.py::list_skills()` was deliberately left alone

This is a third pre-existing direct `Skill` read (HR assignment modal's Step 2 combobox, Story 3.4), structurally the same shape as the two `content/` exceptions just retired. It is not named anywhere in this story's ACs, and this story's own "Out of Scope" note limits it to "schema, migration, module scaffolding, and the embedding-write helper only" — a sweep of every other module's `Skill` consumption isn't part of that. Flagged in-place, now in both the import comment *and* the function's own docstring (code review, 2026-09-09, found the docstring alone carried no exception language, only the import block did) for a future story to route through a real `skills.service` call instead — not Story 6.2/6.3 specifically, which are `skills/`'s own CRUD endpoints, not a refactor of `assignments/`'s read side.

### Embedding-write helper is a helper, not the create/rename logic

AD-11 point 4 and this story's third AC describe behavior that only becomes end-to-end reachable once Story 6.2 (create) and Story 6.3 (rename) exist. What this story owns is the shared implementation those two stories must both call into — `_build_embedding_text()` — so neither re-derives its own truncation logic (the exact "never duplicated elsewhere" AD-11 warns about). Unit-tested standalone (truncation at 1000 chars, `None` description handling) rather than through an endpoint that doesn't exist yet, mirroring `content/service.py`'s identical helper and its own test file's pattern (`test_content_ingestion.py::test_build_embedding_text_*`).

### A live-DB async test-loop trap, caught while writing `test_skills_service.py`

`test_skills_repository.py` uses a blanket `pytestmark = pytest.mark.asyncio(loop_scope="module")` (the established Story 2.4/3.1 private-engine pattern) — safe there because every test in the file is async. `test_skills_service.py` mixes sync tests (`_build_embedding_text`, no DB) with async ones (DB-backed), and a blanket module-level mark warns pytest-asyncio when it lands on a sync function. Removing the mark entirely (to silence the warning) instead broke the async tests: without `loop_scope="module"`, each async test runs on its own function-scoped event loop while still sharing one module-level `_engine`/pooled asyncpg connection created at import time — asyncpg binds a connection to whichever loop first used it, so every test after the first failed with `InterfaceError: cannot perform operation: another operation is in progress`. Fixed by applying `@pytest.mark.asyncio(loop_scope="module")` per-test on only the async functions, leaving the sync ones undecorated — both the warning and the real bug are gone. Worth remembering for any future skills/content test file that mixes sync helper-function tests with live-DB async tests.

### Regression baseline: 3 pre-existing failures, confirmed unrelated via `git stash`

Full suite: 384 passed, 2 skipped, 3 failed (`test_assignments_repository.py::test_find_existing_assignment_returns_empty_when_no_match`, `test_content_discovery.py::test_assignment_with_no_qualifying_content_has_null_content`, `test_content_router.py::test_content_match_returns_null_when_no_content_matches_the_skill`), all a `ForeignKeyViolationError` against a real, already-existing `content_catalog`/`assignments` row pair in the shared dev database (accumulated live-testing state from earlier sessions, not something this story's tests created). Confirmed pre-existing, not a regression, by `git stash`-ing every change from this story and re-running the same 3 files against the untouched baseline — byte-for-byte identical failures, same FK/row IDs. Restored via `git stash pop` before continuing.

### Environment note

This machine's Python is 3.12.10 (matches the architecture spine's target exactly, unlike an earlier session's 3.14.0 workaround-pins note) — a fresh `backend/.venv` was created and `requirements.txt` installed as-pinned with no version substitutions needed.

## Project Structure Notes

New files:
- `backend/app/skills/__init__.py`
- `backend/app/skills/models.py` — `Skill` ORM (relocated from `assignments/models.py`)
- `backend/app/skills/repository.py` — `list_all_skills`, `get_skill_embedding` (relocated from `content/repository.py`)
- `backend/app/skills/service.py` — Service API wrappers + `_build_embedding_text` helper
- `backend/app/skills/schemas.py` — stub (Story 6.2/6.3 add real schemas)
- `backend/app/skills/router.py` — stub, unmounted (Story 6.2 adds the first route + `main.py` wiring)
- `backend/tests/test_skills_repository.py`
- `backend/tests/test_skills_service.py`
- `backend/tests/test_content_ad1_skills_regression_guard.py` — added in code review (2026-09-09), static guard against `content/` re-acquiring direct `Skill` access

Modified files:
- `backend/app/assignments/models.py` — `Skill` class removed; registers `app.skills.models` via a whole-module import (code review: switched from `from ... import Skill`, which left the pre-Story-6.1 import path silently working); `AdminApiKey` docstring corrected
- `backend/app/skills/models.py` — code review: added a mirroring whole-module `import app.assignments.models` to close a cross-module relationship-resolution ordering fragility
- `backend/app/skills/service.py` — code review: added truncation logging to `_build_embedding_text` to genuinely match `content/`'s pattern
- `backend/app/assignments/repository.py` — `Skill` import repointed to `app.skills.models`; `list_skills()` flagged as a documented, out-of-scope exception (code review: exception language added to the function's own docstring, not just the import comment)
- `backend/app/content/repository.py` — `list_all_skills`/`get_skill_embedding` removed, no more `Skill` import
- `backend/app/content/service.py` — calls `skills_service.list_all_skills`/`get_skill_embedding` instead of `repository.*`
- `backend/app/core/seeds.py` — `Skill` import repointed to `app.skills.models`
- `backend/tests/conftest.py`, `test_antiflow_validation.py`, `test_content_discovery.py`, `test_content_ingestion.py`, `test_content_matching.py`, `test_content_repository.py`, `test_content_service.py`, `test_position_retrieval.py`, `test_seed_skill_data_quality.py` — `Skill` import repointed to `app.skills.models`
- `backend/tests/test_schema_definition.py` — `Skill` import repointed; `ever_assigned` column + non-nullable/default-false coverage added (code review: strengthened to also assert `default`/`server_default`, not just `nullable`/`type`); `test_all_tables_defined` fixed to expect 8 tables (pre-existing `admin_api_keys` gap)

No changes to:
- `backend/alembic/versions/004_add_skills_ever_assigned.py`, `005_add_admin_api_keys.py` (pre-existing, verified live)
- `backend/app/main.py` (skills router not mounted — no endpoints yet)

## Architecture Compliance

- **AD-1 — Single-owner data modules**: `skills` now has a real owning module. One known, pre-existing exception remains outside it — `assignments/repository.py::list_skills()`, flagged in place and left for a future story (out of this story's own scope) — but both of `content/`'s former direct-access exceptions are retired, and no new direct access was introduced anywhere else.
- **AD-8 — Module dependency direction**: `content/` now depends on `skills/`'s Service API (`Content -. depends on .-> Skills`, matching the spine's diagram exactly); `skills/` depends on nothing feature-specific in return.
- **AD-11 — `skills/` sole ownership + local lock flag**: module created, `Skill` relocated, `ever_assigned` present (migration pre-existing, verified live), embedding-write helper in place for Story 6.2/6.3 to call.

## References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 6.1] — full AC text
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#AD-11] — sole-ownership + local-flag rule
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#AD-1, #AD-8] — single-owner + dependency-direction rules
- [Source: _bmad-output/C-UX-Scenarios/04-ritas-content-curation/04.1-skills-content-sourcing/04.1-skills-content-sourcing.md] — confirms no additional Skill fields are UX-required beyond name/description/lock
- [Source: backend/app/content/service.py, repository.py] — the embedding-write and single-owner patterns this story mirrors
- [Source: backend/alembic/versions/004_add_skills_ever_assigned.py, 005_add_admin_api_keys.py] — pre-existing migrations verified live

## Completion Checklist

- [x] `skills/` module created (router, service, repository, models, schemas)
- [x] `Skill` ORM relocated out of `assignments/models.py`
- [x] `ever_assigned` column present (pre-existing migration, verified live — not re-created)
- [x] `content/`'s `list_all_skills`/`get_skill_embedding` exceptions retired, routed through `skills.service`
- [x] Embedding-write helper (`_build_embedding_text`) implemented and unit-tested
- [x] All broken import sites (app + tests) updated
- [x] New/moved tests passing (`test_skills_repository.py`, `test_skills_service.py`)
- [x] Full regression suite run — zero regressions (3 pre-existing failures confirmed via `git stash` baseline comparison)
- [x] `app.main` imports cleanly (no circular-import issue from the new cross-module import)
- [x] Code review complete: 1 decision-needed resolved, 9 patches applied, 2 deferred, 3 dismissed
- [x] Sprint status updated to `done`

## Dev Agent Record

### Test Results

Pre-review:
```
tests/test_skills_repository.py .....                                    [ 5 passed]
tests/test_skills_service.py .....                                       [ 5 passed]
tests/test_schema_definition.py ................                        [16 passed]

Full suite: 384 passed, 2 skipped, 3 failed in 55.51s
  FAILED test_assignments_repository.py::test_find_existing_assignment_returns_empty_when_no_match
  FAILED test_content_discovery.py::test_assignment_with_no_qualifying_content_has_null_content
  FAILED test_content_router.py::test_content_match_returns_null_when_no_content_matches_the_skill
  (all 3 confirmed pre-existing via git stash against baseline commit 4e99d275 — identical
  FK-violation errors against the same real content_catalog/assignments row IDs)
```

Post-review (after all 9 patches, including 2 new tests in test_content_ad1_skills_regression_guard.py):
```
Full suite: 386 passed, 2 skipped, 3 failed in 94.90s
  (same 3 pre-existing failures as above, unchanged)
```

## Change Log

- 2026-09-08: Story 6.1 implemented (`bmad-agent-dev`, direct TDD implementation). `skills/` module created; `Skill` ORM relocated from `assignments/models.py`; `content/`'s `list_all_skills`/`get_skill_embedding` exceptions retired in favor of `skills.service`; embedding-write helper (`_build_embedding_text`) added; import sites updated across app + test code for AD-1 compliance; `test_all_tables_defined` fixed (pre-existing `admin_api_keys` gap, found while touching that file). Migrations 004/005 (already present from an earlier ad hoc commit, `4e99d275`) verified live, not redone. Full suite: 384 passed, 2 skipped, 3 pre-existing failures confirmed unrelated via `git stash` baseline comparison. Status → `review`.
- 2026-09-09: `bmad-code-review` (3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor). 1 decision-needed (AC3's embedding-write helper scope — resolved: leave as-is, matches `content/`'s inline-composition precedent), 9 patches applied, 2 deferred (`deferred-work.md`), 3 dismissed. Patches: closed the old `from app.assignments.models import Skill` import path (was still silently working, undermining the relocation's own point) via a whole-module `import app.skills.models`; closed a real cross-module import-ordering fragility (independently found by both Edge Case Hunter and Blind Hunter) by adding the mirroring `import app.assignments.models` to `skills/models.py`, verified safe in all 3 import orders including a previously-broken skills-only case; added truncation logging to `_build_embedding_text` to genuinely match `content/`'s pattern; added a new static regression-guard test (`test_content_ad1_skills_regression_guard.py`, mirroring the existing AD-7 guard) verifying `content/` never re-acquires direct `Skill` access; strengthened the under-asserting `ever_assigned` schema test to actually check `default`/`server_default`; added AD-1 exception language to `list_skills()`'s own docstring, not just the import comment above it; corrected 3 documentation-wording issues in this story file (Scope Note 4's story misattribution, the Architecture Compliance section's assert-then-contradict framing, Task 6's overstated "broken import sites" claim — the latter is now literally accurate, since the old-import-path patch closed the gap that made it previously false). Full regression re-verified: `app.main` imports cleanly, 386 passed (2 new) / 2 skipped / same 3 pre-existing failures. Status → `done`.
